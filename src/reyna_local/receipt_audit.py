"""Verifica los recibos de una captura XLSX sin ejecutar operaciones."""

from contextlib import closing
from hashlib import sha256
from io import BytesIO
import json
from xml.etree.ElementTree import ParseError
from zipfile import BadZipFile, ZipFile

from defusedxml.common import DefusedXmlException
from openpyxl import load_workbook
from openpyxl.utils.exceptions import InvalidFileException

from .store import META, RECEIPTS, RECEIPT_HEADER, Problem, content_bytes, encode, inspect_zip, validate_execution


MAX_CONTROL_ROWS = 200_000
MAX_REPORTED_ISSUES = 100


def _version(value):
    return type(value) is int and value >= 0


def _normalized_text(value, limit):
    return isinstance(value, str) and 0 < len(value) <= limit and value.strip() == value and "\x00" not in value


def _json_object(value):
    if isinstance(value, str):
        try:
            obj = json.loads(value)
            if isinstance(obj, dict) and encode(obj) == value:
                return obj
        except (ValueError, RecursionError):
            pass
    return None


def _command_identity(command):
    if len(command) > 30_000:
        return None
    body = _json_object(command)
    if body is None:
        return None
    close_fields = {"operation", "user", "period"}
    if (set(body) in (close_fields, close_fields | {"result_hash"})
            and body["operation"] == "close_month"):
        # DBD_4 defines the provider fingerprint as exact text (length 20),
        # without requiring a particular digest algorithm or encoding.
        hash_ok = ("result_hash" not in body or
                   _normalized_text(body["result_hash"], 20))
        if (_normalized_text(body["user"], 100) and _normalized_text(body["period"], 40)
                and hash_ok):
            return {"operation": "close_month", "period": body["period"]}
    if set(body) == {"transaction", "user", "header", "lines"}:
        try:
            # El ID se guarda en otra columna y queda fuera del comando.
            txn, user, _, _, _ = validate_execution({**body, "request_id": "auditoria"})
        except (Problem, OverflowError):
            return None
        if txn == body["transaction"] and user == body["user"]:
            return {"transaction": txn}
    return None


def _step(step):
    if not isinstance(step, dict) or not isinstance(step.get("step"), (str, int, float)) or step["step"] == "":
        return False
    if step.get("result") == "OK":
        return set(step) == {"step", "result"}
    return (step.get("result") == "ERROR" and set(step) == {"step", "result", "error"}
            and isinstance(step["error"], str))


def _response_contract(response, identity, company_code):
    """Devuelve la validez del contrato y el incremento inferido, cuando es posible."""
    result = response.get("result")
    if identity is None or result not in ("OK", "ERROR"):
        return False, None
    fields = {"request_id", "result", "version", *identity}
    same_operation = all(response.get(field) == value for field, value in identity.items())
    if "transaction" in identity:
        if result == "ERROR":
            fields.add("error")
        valid = same_operation and set(response) == fields
        return valid and (result == "OK" or isinstance(response["error"], str)), int(result == "OK")

    fields.update({"company_code", "message", "steps"})
    steps = response.get("steps")
    if not isinstance(steps, list) or not steps or not all(_step(step) for step in steps):
        return False, None
    all_ok = all(step["result"] == "OK" for step in steps)
    if all_ok != (result == "OK"):
        return False, None
    valid = (same_operation and set(response) == fields and isinstance(response["message"], str)
             and isinstance(company_code, str) and response["company_code"] == company_code)
    return valid, len(steps) if all_ok else 0


def _control_rows(book, name, header, issue):
    if name not in book.sheetnames:
        issue("missing_control_sheet", name, None, "Falta la hoja de control.")
        return
    sheet = book[name]
    # La dimensión declarada puede omitir filas. Se leen también las filas con ID vacío.
    sheet.reset_dimensions()
    rows = iter(sheet.iter_rows(min_row=1, max_row=MAX_CONTROL_ROWS + 1, values_only=True))
    if next(rows, ()) != tuple(header):
        issue("invalid_control_header", name, 1, "La cabecera de control no corresponde al formato del piloto.")
        return
    for number, row in enumerate(rows, 2):
        if number > MAX_CONTROL_ROWS:
            issue("control_row_limit", name, number, "La hoja supera el límite de filas de control.")
            return
        if any(value is not None for value in row[len(header):]):
            issue("unexpected_control_cell", name, number, "Hay datos fuera de las columnas de control.")
        if any(value is not None for value in row):
            yield number, (row + (None,) * len(header))[:len(header)]


def audit_receipts(path):
    """Audita un libro gestionado o su respaldo como capturas independientes."""
    issues = []
    issue_count = 0
    complete_receipts = True

    def issue(code, sheet, row, detail):
        nonlocal issue_count, complete_receipts
        if sheet == RECEIPTS and code in {"missing_control_sheet", "invalid_control_header", "control_row_limit"}:
            complete_receipts = False
        issue_count += 1
        if len(issues) < MAX_REPORTED_ISSUES:
            issues.append({"code": code, "sheet": sheet, "row": row, "detail": detail})

    try:
        raw = content_bytes(path)
        with ZipFile(BytesIO(raw)) as archive:
            inspect_zip(archive)
        with closing(load_workbook(BytesIO(raw), read_only=True, keep_links=False)) as book:
            versions = []
            company_code = None
            for row, (key, value) in _control_rows(book, META, ("key", "value"), issue):
                if key == "version":
                    versions.append((row, value))
                elif key == "company_code":
                    company_code = value
            workbook_version = None
            if len(versions) == 1 and _version(versions[0][1]):
                workbook_version = versions[0][1]
            else:
                issue("invalid_workbook_version", META, versions[-1][0] if versions else None,
                      "Debe existir una sola versión entera no negativa.")

            expected_version = 0
            receipt_count = 0
            ids = {}
            previous_row = 1
            for row, (request_id, digest, status, stored_response, command, recorded_at) in _control_rows(
                    book, RECEIPTS, RECEIPT_HEADER, issue):
                receipt_count += 1
                if row != previous_row + 1:
                    issue("receipt_gap", RECEIPTS, previous_row + 1, "Hay filas vacías entre los recibos.")
                previous_row = row
                if not _normalized_text(request_id, 160):
                    issue("invalid_request_id", RECEIPTS, row, "El identificador de solicitud no es válido.")
                elif request_id in ids:
                    issue("duplicate_request_id", RECEIPTS, row, f"El identificador ya aparece en la fila {ids[request_id]}.")
                else:
                    ids[request_id] = row
                if not isinstance(recorded_at, str) or not recorded_at:
                    issue("invalid_recorded_at", RECEIPTS, row, "Falta el texto de fecha de registro.")
                identity = None
                if isinstance(command, str):
                    if digest != sha256(command.encode("utf-8")).hexdigest():
                        issue("digest_mismatch", RECEIPTS, row, "La huella SHA-256 difiere del comando almacenado.")
                    identity = _command_identity(command)
                if identity is None:
                    issue("invalid_command", RECEIPTS, row, "El comando no tiene el formato canónico del piloto.")

                response = _json_object(stored_response)
                increment = None
                if response is not None:
                    valid, increment = _response_contract(response, identity, company_code)
                    if not valid:
                        issue("invalid_response", RECEIPTS, row, "La respuesta no concuerda con el contrato del comando.")
                    if "request_id" not in response or response["request_id"] != request_id:
                        issue("response_request_id_mismatch", RECEIPTS, row, "El identificador de respuesta difiere del recibo.")
                    result = response.get("result")
                    expected_status = {"OK": 200, "ERROR": 422}.get(result) if isinstance(result, str) else None
                    if type(status) is not int or status != expected_status:
                        issue("response_status_mismatch", RECEIPTS, row, "El estado HTTP no concuerda con el resultado.")
                else:
                    issue("invalid_response", RECEIPTS, row, "La respuesta no es un objeto JSON canónico.")

                if expected_version is not None:
                    expected_version = expected_version + increment if increment is not None else None
                if response is not None and (not _version(response.get("version"))
                        or (expected_version is not None and response["version"] != expected_version)):
                    issue("receipt_version_mismatch", RECEIPTS, row, "La versión de respuesta no concuerda con la secuencia.")

            if not complete_receipts:
                expected_version = None
            if workbook_version is not None and expected_version is not None and workbook_version != expected_version:
                issue("workbook_version_mismatch", META, versions[0][0], "La versión del libro no coincide con la acumulada.")
    except (InvalidFileException, BadZipFile, OSError, ValueError, TypeError, IndexError, KeyError,
            ParseError, DefusedXmlException) as exc:
        raise Problem(422, "No se pudo leer la captura XLSX para auditarla.") from exc

    return {"valid": not issue_count, "workbook_version": workbook_version, "expected_version": expected_version,
            "receipt_count": receipt_count, "issue_count": issue_count, "issues": issues}
