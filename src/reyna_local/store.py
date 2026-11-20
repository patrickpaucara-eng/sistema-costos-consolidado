"""Persistencia atómica del piloto Excel con el intérprete Python de Ola 1."""
from contextlib import closing, contextmanager
from datetime import date, datetime, time as day_time, timezone
from hashlib import sha256
from io import BytesIO
import json
import math
from pathlib import Path
import os
import posixpath
import re
import shutil
from tempfile import NamedTemporaryFile
import time
from uuid import uuid4
from xml.dom import Node
from xml.etree.ElementTree import ParseError
from zipfile import BadZipFile, ZipFile

from defusedxml.common import DefusedXmlException
from defusedxml.minidom import parseString
from openpyxl import load_workbook
from openpyxl.utils import get_column_letter, column_index_from_string, range_boundaries
from openpyxl.utils.exceptions import InvalidFileException

from .motor_espejo import Motor

SOURCE_REVISION = "cac2501d9f712655dda466d216dc5bff2dd446a5"
ENGINE_SHA256 = "8c962583170cbb200c564bef8edfd95ae931602b82fa2f89f2bb48bcd9ce2a11"
# Explicit API capability boundary. The engine has more configured transactions,
# but these are the event operations currently covered by the active MVP scope.
TRANSACTIONS = ("T14", "T15", "T17", "T18", "T19", "T20")
PUBLIC = ("EVENTO", "LINEA", "EXISTENCIA", "KARDEX", "RECURSO", "PERIODO", "OBJETO", "CENTRO")
REQUIRED = {
    "USUARIO", "USUARIO_PERFIL", "PERFIL_TRX", "LOG_TRX", "BITACORA", "EMPRESA",
    "PARAMETRO", "TRX_CAMPO", "MENSAJE", "TRX", "TOP", "OME", "MET", "MCA",
    "FRM", "CND", "PAL", *PUBLIC,
}
MAX_XLSX = 16 * 1024 * 1024
MAX_XML = 80 * 1024 * 1024


class Problem(Exception):
    def __init__(self, status, message):
        self.status = status
        super().__init__(message)


def encode(data):
    return json.dumps(data, ensure_ascii=False, allow_nan=False, separators=(",", ":"), sort_keys=True)


def now():
    return datetime.now(timezone.utc).isoformat()


def text_field(obj, key, limit):
    value = obj.get(key)
    if not isinstance(value, str) or not value.strip() or len(value) > limit or "\x00" in value:
        raise Problem(400, f"Campo inválido: {key}.")
    return value.strip()


def validate_execution(body):
    txn = text_field(body, "transaction", 8)
    if txn not in TRANSACTIONS:
        raise Problem(400, "La transacción no está habilitada en el piloto.")
    user = text_field(body, "user", 100)
    key = text_field(body, "request_id", 160)
    header = body.get("header")
    lines = body.get("lines", [])
    if not isinstance(header, dict) or not isinstance(lines, list) or len(lines) > 250:
        raise Problem(400, "Se requiere cabecera y hasta 250 líneas.")
    for fields in [header, *lines]:
        if not isinstance(fields, dict) or len(fields) > 100:
            raise Problem(400, "La cabecera y las líneas deben contener campos con nombre.")
        for field, value in fields.items():
            if (not isinstance(field, str) or len(field) > 100 or isinstance(value, bool)
                    or value is None or not isinstance(value, (str, int, float))
                    or isinstance(value, str) and len(value) > 2048):
                raise Problem(400, "Valor de trama no admitido.")
            if isinstance(value, (int, float)) and (abs(value) > 1e20 or not math.isfinite(value)):
                raise Problem(400, "Valor numérico fuera del intervalo del piloto.")
    return txn, user, key, header, lines


META = "_ReynaEspacio"
RECEIPTS = "_ReynaRecibos"
RECEIPT_HEADER = ["request_id", "digest", "status", "response", "command", "recorded_at"]
SHEET_NS = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
DOC_REL = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
PACKAGE_REL = "http://schemas.openxmlformats.org/package/2006/relationships"
CONTENT_NS = "http://schemas.openxmlformats.org/package/2006/content-types"
NS_DECL = "http://www.w3.org/2000/xmlns/"
ID = re.compile(r"[0-9a-f]{32}\Z")
WORKBOOK = "xl/workbook.xml"
RELS = "xl/_rels/workbook.xml.rels"
TYPES = "[Content_Types].xml"


def content_bytes(path):
    if not path.is_file():
        raise Problem(422, "Seleccione un archivo XLSX local existente.")
    with path.open("rb") as f:
        raw = f.read(MAX_XLSX + 1)
    if len(raw) > MAX_XLSX:
        raise Problem(413, "El libro supera el límite de 16 MiB del piloto.")
    return raw


def inspect_zip(archive):
    entries = archive.infolist()
    if len(entries) > 3000 or sum(entry.file_size for entry in entries) > MAX_XML:
        raise Problem(413, "El contenido del libro supera el límite de importación.")
    names = archive.namelist()
    if len(set(names)) != len(names) or any(n.lower().endswith("vbaproject.bin") for n in names):
        raise Problem(422, "Se requiere un XLSX libre de macros y de partes duplicadas.")
    if any(n.startswith("_xmlsignatures/") for n in names):
        raise Problem(422, "El piloto requiere una copia de trabajo sin firma de paquete.")


def load_data(raw, required=None):
    tables, positions = {}, {}
    try:
        with ZipFile(BytesIO(raw)) as z:
            inspect_zip(z)
        with closing(load_workbook(BytesIO(raw), read_only=True, keep_links=False)) as wb:
            total = 0
            for sheet in wb.worksheets:
                if required is not None and sheet.title not in required:
                    continue
                height, width = sheet.max_row, sheet.max_column
                if not height or not width or width > 1024 or height > 200000:
                    raise Problem(422, "Una hoja tiene dimensiones incompatibles.")
                total += height * width
                if total > 2_000_000:
                    raise Problem(413, "El libro supera dos millones de celdas de inspección.")
                values = iter(sheet.iter_rows(min_row=1, max_row=height, max_col=width, values_only=True))
                first = next(values, ())
                if not first or first[0] is None:
                    continue
                headers = [v for v in first if v is not None]
                if sheet.title in REQUIRED and (list(first[:len(headers)]) != headers
                        or not all(isinstance(v, str) for v in headers) or len(headers) != len(set(headers))):
                    raise Problem(422, f"Cabecera incompatible: {sheet.title}.")
                rows, numbers = [], []
                for index, row in enumerate(values, 2):
                    if row[0] not in (None, ""):
                        rows.append(list(row[:len(headers)]))
                        numbers.append(index)
                tables[sheet.title] = {"h": headers, "r": rows}
                positions[sheet.title] = numbers
    except (InvalidFileException, BadZipFile, OSError, ValueError, TypeError, IndexError, KeyError,
            ParseError, DefusedXmlException) as exc:
        raise Problem(422, "El XLSX no es legible o su estructura es incompatible.") from exc
    return tables, positions


def validate_model(tables):
    if REQUIRED.difference(tables):
        raise Problem(422, "Faltan tablas requeridas para el piloto.")
    if any(name.casefold() in (META.casefold(), RECEIPTS.casefold()) for name in tables):
        raise Problem(422, "El origen ya contiene hojas reservadas del piloto.")
    if tables["USUARIO"]["h"][:4] != ["USU_COD", "USU_CLAVE", "USU_PERFIL", "USU_EMP"]:
        raise Problem(422, "La estructura de usuarios resulta incompatible con el motor.")
    for txn in TRANSACTIONS:
        for table in ("TRX_CAMPO", "TOP"):
            if not any(r[0] == txn for r in tables[table]["r"]):
                raise Problem(422, f"El libro carece de la definición {txn} en {table}.")


def operational_companies(tables):
    """Empresas asignadas a usuarios con permiso para transacciones del piloto."""
    companies = {str(row[0]) for row in tables["EMPRESA"]["r"] if row and row[0] not in (None, "")}
    allowed = {(row[0], row[1]) for row in tables["PERFIL_TRX"]["r"] if len(row) > 1}
    profiles = {}
    for row in tables["USUARIO_PERFIL"]["r"]:
        if len(row) > 1:
            profiles.setdefault(row[0], []).append(row[1])
    active = set()
    for user in tables["USUARIO"]["r"]:
        if len(user) < 4 or str(user[3]) not in companies:
            continue
        user_profiles = profiles.get(user[0]) or [user[2]]
        if any((profile, txn) in allowed for profile in user_profiles for txn in TRANSACTIONS):
            active.add(str(user[3]))
    return sorted(active)


def permitted_tables(tables):
    denied = set()
    for row in tables["PARAMETRO"]["r"]:
        if row[0] == "PUERTO_LECTURA_EXCLUIR":
            denied.update(str(row[1]).split("|"))
    return [name for name in PUBLIC if name not in denied]


def elements(parent, ns, name):
    return [n for n in parent.childNodes if n.nodeType == Node.ELEMENT_NODE and n.namespaceURI == ns and n.localName == name]


def element(doc, parent, ns, local, attrs=None):
    qualified = f"{parent.prefix}:{local}" if parent.prefix else local
    child = doc.createElementNS(ns, qualified)
    for key, value in (attrs or {}).items():
        child.setAttribute(key, str(value))
    parent.appendChild(child)
    return child


def package_add_sheets(archive, extra):
    workbook = parseString(archive.read(WORKBOOK))
    rels = parseString(archive.read(RELS))
    types = parseString(archive.read(TYPES))
    sheets = workbook.getElementsByTagNameNS(SHEET_NS, "sheets")[0]
    current = elements(sheets, SHEET_NS, "sheet")
    if {s.getAttribute("name").casefold() for s in current} & {name.casefold() for name in extra}:
        raise Problem(422, "Los nombres de hojas técnicas ya están ocupados.")
    sheet_id = max(int(s.getAttribute("sheetId")) for s in current)
    used = {r.getAttribute("Id") for r in elements(rels.documentElement, PACKAGE_REL, "Relationship")}
    rid = 0
    changes = {}
    for name, rows in extra.items():
        sheet_id += 1
        while f"rId{rid}" in used or rid == 0:
            rid += 1
        rel_id = f"rId{rid}"
        used.add(rel_id)
        part = f"xl/worksheets/reyna-{name}.xml"
        if part in archive.namelist():
            raise Problem(422, "El origen ya contiene una parte técnica del piloto.")
        sheet = element(workbook, sheets, SHEET_NS, "sheet",
                        {"name": name, "sheetId": sheet_id, "state": "veryHidden"})
        sheet.setAttributeNS(NS_DECL, "xmlns:r", DOC_REL)
        sheet.setAttributeNS(DOC_REL, "r:id", rel_id)
        element(rels, rels.documentElement, PACKAGE_REL, "Relationship",
                {"Id": rel_id, "Type": DOC_REL + "/worksheet", "Target": "/" + part})
        element(types, types.documentElement, CONTENT_NS, "Override",
                {"PartName": "/" + part, "ContentType": "application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"})
        empty = f'<worksheet xmlns="{SHEET_NS}"><dimension ref="A1"/><sheetData/></worksheet>'.encode()
        edits = [(i, j, v) for i, row in enumerate(rows, 1) for j, v in enumerate(row, 1)]
        changes[part] = patch_cells(empty, edits)
    changes.update({WORKBOOK: workbook.toxml("utf-8"), RELS: rels.toxml("utf-8"), TYPES: types.toxml("utf-8")})
    return changes


def sheet_parts(archive):
    wb = parseString(archive.read(WORKBOOK))
    rels = parseString(archive.read(RELS))
    targets = {r.getAttribute("Id"): r.getAttribute("Target") for r in
               elements(rels.documentElement, PACKAGE_REL, "Relationship")}
    paths = {}
    for s in wb.getElementsByTagNameNS(SHEET_NS, "sheet"):
        target = targets[s.getAttributeNS(DOC_REL, "id")]
        paths[s.getAttribute("name")] = posixpath.normpath(posixpath.join("xl", target)).lstrip("/")
    return paths


def set_value(doc, cell, value):
    if elements(cell, SHEET_NS, "f"):
        raise Problem(422, "La operación intentaría sobrescribir una fórmula del libro.")
    for name in ("v", "is"):
        for item in elements(cell, SHEET_NS, name):
            cell.removeChild(item)
    if cell.hasAttribute("t"):
        cell.removeAttribute("t")
    if value is None:
        return
    if isinstance(value, str):
        if len(value) > 32767 or re.search(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", value):
            raise Problem(422, "Un texto no es válido para una celda de Excel.")
        cell.setAttribute("t", "inlineStr")
        slot = element(doc, element(doc, cell, SHEET_NS, "is"), SHEET_NS, "t")
        slot.setAttribute("xml:space", "preserve")
    elif isinstance(value, bool):
        cell.setAttribute("t", "b")
        value = "1" if value else "0"
        slot = element(doc, cell, SHEET_NS, "v")
    elif isinstance(value, (int, float)) and math.isfinite(value):
        slot = element(doc, cell, SHEET_NS, "v")
    else:
        raise Problem(422, "El motor devolvió un valor de celda incompatible.")
    slot.appendChild(doc.createTextNode(str(value)))


def patch_cells(raw, edits):
    doc = parseString(raw)
    data = doc.getElementsByTagNameNS(SHEET_NS, "sheetData")[0]
    rows = {int(r.getAttribute("r")): r for r in elements(data, SHEET_NS, "row")}
    dimensions = doc.getElementsByTagNameNS(SHEET_NS, "dimension")
    max_column, max_row = 1, 1
    if dimensions:
        _, _, max_column, max_row = range_boundaries(dimensions[0].getAttribute("ref"))
    for number, column, value in edits:
        row = rows.get(number)
        if row is None:
            following = next((rows[n] for n in sorted(rows) if n > number), None)
            row = element(doc, data, SHEET_NS, "row", {"r": number})
            if following:
                data.insertBefore(row, following)
            rows[number] = row
        ref = f"{get_column_letter(column)}{number}"
        cells = elements(row, SHEET_NS, "c")
        cell = next((c for c in cells if c.getAttribute("r") == ref), None)
        if cell is None:
            following = next((c for c in cells if column_index_from_string(re.sub(r"[0-9]", "", c.getAttribute("r"))) > column), None)
            cell = element(doc, row, SHEET_NS, "c", {"r": ref})
            if following:
                row.insertBefore(cell, following)
        set_value(doc, cell, value)
        max_column, max_row = max(max_column, column), max(max_row, number)
    if dimensions:
        dimensions[0].setAttribute("ref", f"A1:{get_column_letter(max_column)}{max_row}")
    return doc.toxml("utf-8")


def write_archive(path, source, replacements):
    with ZipFile(BytesIO(source)) as old, ZipFile(path, "w") as new:
        new.comment = old.comment
        for entry in old.infolist():
            data = replacements.pop(entry.filename, None)
            new.writestr(entry, old.read(entry) if data is None else data)
        for name, data in replacements.items():
            new.writestr(name, data, compress_type=8)
    with ZipFile(path) as check:
        inspect_zip(check)
        if check.testzip() is not None:
            raise Problem(500, "No se pudo validar el libro temporal.")
    if path.stat().st_size > MAX_XLSX:
        raise Problem(413, "El resultado supera el tamaño máximo del piloto.")
    with path.open("rb+") as f:
        os.fsync(f.fileno())


def sync_dir(directory):
    if os.name == "posix":
        fd = os.open(directory, os.O_RDONLY)
        try:
            os.fsync(fd)
        finally:
            os.close(fd)


@contextmanager
def temporary(directory):
    with NamedTemporaryFile(dir=directory, prefix=".reyna-", suffix=".tmp", delete=False) as f:
        path = Path(f.name)
    try:
        yield path
    finally:
        path.unlink(missing_ok=True)


@contextmanager
def writer_lock(directory):
    with (directory / ".lock").open("a+b") as f:
        deadline = time.monotonic() + 10
        while True:
            try:
                if os.name == "nt":
                    import msvcrt
                    f.seek(0)
                    msvcrt.locking(f.fileno(), msvcrt.LK_NBLCK, 1)
                else:
                    import fcntl
                    fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
                break
            except OSError as exc:
                if time.monotonic() >= deadline:
                    raise Problem(423, "El espacio está ocupado. Reintente con el mismo identificador.") from exc
                time.sleep(0.05)
        try:
            yield
        finally:
            if os.name == "nt":
                f.seek(0)
                msvcrt.locking(f.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(f, fcntl.LOCK_UN)


def same_workbook(path, source):
    if any((path.parent / n).exists() for n in ("~$" + path.name, ".~lock." + path.name + "#")):
        raise Problem(409, "Cierre el libro en Office antes de registrar la operación.")
    if content_bytes(path) != source:
        raise Problem(409, "El libro cambió durante el registro. Revise los datos y reintente.")


def metadata(tables):
    if META not in tables or RECEIPTS not in tables:
        raise Problem(422, "El libro de trabajo perdió su información de control.")
    return dict(tables[META]["r"])


def summary(tables, path):
    info = metadata(tables)
    return {**info, "company_code": info.get("company_code"),
            "close_month_enabled": bool(info.get("close_month_enabled", 0)),
            "tables": permitted_tables(tables), "transactions": list(TRANSACTIONS),
            "workbook_path": str(path)}


def motor_changes(original, motor, positions):
    edits = {}
    for name, state in motor.T.items():
        old = original[name]["r"]
        new = state["r"]
        if old == new:
            continue
        physical = positions[name]
        next_row = (physical[-1] if physical else 1) + 1
        changed = []
        for i in range(max(len(new), len(old))):
            number = physical[i] if i < len(old) else next_row + i - len(old)
            previous = old[i] if i < len(old) else []
            current = new[i] if i < len(new) else []
            for j in range(max(len(previous), len(current))):
                before = previous[j] if j < len(previous) else None
                after = current[j] if j < len(current) else None
                if before != after:
                    changed.append((number, j + 1, after))
        edits[name] = changed
    return edits


class Store:
    def __init__(self, rootdirectory):
        self.root = Path(rootdirectory).resolve()
        self.root.mkdir(parents=True, exist_ok=True, mode=0o700)

    def path(self, identifier):
        if not isinstance(identifier, str) or not ID.fullmatch(identifier):
            raise Problem(404, "Espacio inexistente.")
        directory = self.root / identifier
        path = directory / "libro.xlsx"
        if directory.is_symlink() or path.is_symlink() or not path.is_file():
            raise Problem(404, "Espacio inexistente.")
        return path

    def create(self, body):
        name = text_field(body, "name", 160)
        source = Path(text_field(body, "workbook_path", 4096)).expanduser()
        if source.suffix.lower() != ".xlsx":
            raise Problem(422, "Seleccione un libro de configuración .xlsx.")
        raw = content_bytes(source)
        tables, _ = load_data(raw)
        validate_model(tables)
        companies = operational_companies(tables)
        if len(companies) != 1:
            raise Problem(422, "El piloto requiere un solo ámbito empresarial operativo por espacio. "
                               f"Empresas operativas detectadas: {', '.join(companies) or 'ninguna'}.")
        identifier = uuid4().hex
        info = {"id": identifier, "name": name, "version": 0, "created_at": now(),
                "workbook_sha256": sha256(raw).hexdigest(), "engine_sha256": ENGINE_SHA256,
                "engine_revision": SOURCE_REVISION, "company_code": companies[0],
                "close_month_enabled": int("CIERRE_PASO" in tables)}
        directory = self.root / identifier
        directory.mkdir(mode=0o700)
        path = directory / "libro.xlsx"
        try:
            extra = {META: [["key", "value"], *info.items()], RECEIPTS: [RECEIPT_HEADER]}
            with ZipFile(BytesIO(raw)) as z:
                replacements = package_add_sheets(z, extra)
            with temporary(directory) as temp:
                write_archive(temp, raw, replacements)
                os.replace(temp, path)
            sync_dir(directory)
            sync_dir(self.root)
        except BaseException:
            shutil.rmtree(directory)
            raise
        return {**info, "workbook_path": str(path), "tables": permitted_tables(tables), "transactions": list(TRANSACTIONS)}

    def list(self):
        result = [self.get(p.name) for p in self.root.iterdir()
                  if ID.fullmatch(p.name) and (p / "libro.xlsx").is_file()]
        return {"workspaces": sorted(result, key=lambda s: (s["created_at"], s["id"]))}

    def get(self, identifier):
        path = self.path(identifier)
        tables, _ = load_data(content_bytes(path), {META, RECEIPTS, "PARAMETRO"})
        return summary(tables, path)

    def table(self, identifier, name, offset=0, limit=100):
        if not isinstance(offset, int) or not isinstance(limit, int) or offset < 0 or not 1 <= limit <= 500:
            raise Problem(400, "Paginación inválida.")
        if name not in PUBLIC:
            raise Problem(403, "Tabla fuera del puerto de consulta.")
        path = self.path(identifier)
        tables, _ = load_data(content_bytes(path), {name, META, RECEIPTS, "PARAMETRO"})
        if name not in permitted_tables(tables):
            raise Problem(403, "La configuración del libro restringe esta tabla.")
        data = tables[name]
        visible = [[value.isoformat() if isinstance(value, (date, day_time)) else value for value in row]
                   for row in data["r"][offset:offset + limit]]
        return {"table": name, "columns": data["h"], "rows": visible,
                "total": len(data["r"]), "offset": offset, "limit": limit, "version": metadata(tables)["version"]}

    def execute(self, identifier, body):
        txn, user, key, header, lines = validate_execution(body)
        command = encode({"transaction": txn, "user": user, "header": header, "lines": lines})
        if len(command) > 30000:
            raise Problem(413, "La solicitud supera el espacio del recibo en Excel.")
        digest = sha256(command.encode()).hexdigest()
        path = self.path(identifier)
        with writer_lock(path.parent):
            raw = content_bytes(path)
            tables, positions = load_data(raw)
            info = metadata(tables)
            if info["id"] != identifier or info["engine_sha256"] != ENGINE_SHA256:
                raise Problem(409, "La identidad o versión del motor del espacio es incompatible.")
            company = info.get("company_code")
            if company is None:
                companies = operational_companies(tables)
                if len(companies) != 1:
                    raise Problem(409, "El espacio no tiene un único ámbito empresarial verificable. Reimpórtelo.")
                company = companies[0]
            for record in tables[RECEIPTS]["r"]:
                if record[0] == key:
                    if record[1] != digest:
                        raise Problem(409, "El identificador ya corresponde a otra operación.")
                    return record[2], json.loads(record[3])
            same_workbook(path, raw)
            declared = [r for r in tables["TRX_CAMPO"]["r"] if r[0] == txn]
            head_fields = {r[2] for r in declared if r[4] == "C"}
            line_fields = {r[2] for r in declared if r[4] == "L"}
            if set(header) - (head_fields if lines else head_fields | line_fields):
                raise Problem(400, "La cabecera contiene campos no declarados para la operación.")
            if any(set(item) - line_fields for item in lines):
                raise Problem(400, "Una línea contiene campos no declarados para la operación.")
            motor = Motor.__new__(Motor)
            # Las filas se copian porque el intérprete actualiza listas en el lugar.
            motor.T = {n: {"h": s["h"], "r": [list(r) for r in s["r"]]} for n, s in tables.items()
                       if n not in (META, RECEIPTS)}
            motor.usr = motor.perfil = ""
            motor.pend = None
            owner = next((r for r in tables["USUARIO"]["r"] if r[0] == user), None)
            if (owner is None or len(owner) < 4 or str(owner[3]) != company
                    or ("EMP" in header and str(header["EMP"]) != company)):
                outcome = "ERROR: Usuario o empresa no autorizados."
            else:
                try:
                    outcome = motor.ejecutar(txn, header, user, lines)
                except (ValueError, ArithmeticError, KeyError, IndexError, TypeError):
                    outcome = "ERROR: La operación contiene valores incompatibles con el libro."
            ok = outcome == "OK"
            status = 200 if ok else 422
            version = info["version"] + int(ok)
            response = {"result": "OK" if ok else "ERROR", "transaction": txn, "request_id": key, "version": version}
            if not ok:
                response["error"] = outcome
            edits = motor_changes(tables, motor, positions) if ok else {}
            if ok:
                version_row = next(n for n, row in zip(positions[META], tables[META]["r"]) if row[0] == "version")
                edits[META] = [(version_row, 2, version)]
            nr = (positions[RECEIPTS][-1] if positions[RECEIPTS] else 1) + 1
            record = (key, digest, status, encode(response), command, now())
            edits[RECEIPTS] = [(nr, j, val) for j, val in enumerate(record, 1)]
            with ZipFile(BytesIO(raw)) as z:
                parts = sheet_parts(z)
                patches = {parts[n]: patch_cells(z.read(parts[n]), cells) for n, cells in edits.items()}
            with temporary(path.parent) as temp, temporary(path.parent) as backup:
                write_archive(temp, raw, patches)
                with backup.open("wb") as f:
                    f.write(raw)
                    f.flush()
                    os.fsync(f.fileno())
                same_workbook(path, raw)
                os.replace(backup, path.parent / "respaldo.xlsx")
                sync_dir(path.parent)
                same_workbook(path, raw)
                os.replace(temp, path)
                sync_dir(path.parent)
            return status, response

    def close_month(self, identifier, body):
        """Ejecuta la cadena oficial en memoria y persiste una sola versión del libro."""
        user = text_field(body, "user", 100)
        key = text_field(body, "request_id", 160)
        period = text_field(body, "period", 40)
        command = encode({"operation": "close_month", "user": user, "period": period})
        digest = sha256(command.encode()).hexdigest()
        path = self.path(identifier)
        with writer_lock(path.parent):
            raw = content_bytes(path)
            tables, positions = load_data(raw)
            info = metadata(tables)
            if info["id"] != identifier or info["engine_sha256"] != ENGINE_SHA256:
                raise Problem(409, "La identidad o versión del motor del espacio es incompatible.")
            company = info.get("company_code")
            if company is None or not info.get("close_month_enabled"):
                raise Problem(422, "Este libro no tiene una cadena de cierre habilitada.")
            for record in tables[RECEIPTS]["r"]:
                if record[0] == key:
                    if record[1] != digest:
                        raise Problem(409, "El identificador ya corresponde a otra operación.")
                    return record[2], json.loads(record[3])
            same_workbook(path, raw)
            if len(command) > 30000:
                raise Problem(413, "La solicitud supera el espacio del recibo en Excel.")
            if not all(name in tables for name in ("CIERRE_PASO", "PERIODO", "CARGA")):
                raise Problem(422, "Faltan tablas para ejecutar el cierre de periodo.")
            periods = [r for r in tables["PERIODO"]["r"]
                       if str(r[0]) == period and str(r[1]) == company]
            if len(periods) != 1 or periods[0][4] != "A":
                raise Problem(422, "El periodo de la empresa no existe de forma única o no está abierto.")
            steps = sorted((r[0] for r in tables["CIERRE_PASO"]["r"]
                            if len(r) > 4 and r[4] in ("OFICIAL", "CIERRE")),
                           key=lambda code: next(float(r[1]) for r in tables["CIERRE_PASO"]["r"] if r[0] == code))
            if not steps:
                raise Problem(422, "La configuración no declara pasos oficiales de cierre.")
            motor = Motor.__new__(Motor)
            motor.T = {n: {"h": s["h"], "r": [list(r) for r in s["r"]]}
                       for n, s in tables.items() if n not in (META, RECEIPTS)}
            motor.usr = motor.perfil = ""
            motor.pend = None
            owner = next((r for r in tables["USUARIO"]["r"] if r[0] == user), None)
            outcomes = []
            if owner is None or len(owner) < 4 or str(owner[3]) != company:
                outcomes.append({"step": "validación", "result": "ERROR",
                                 "error": "El usuario no pertenece a la empresa del espacio."})
            else:
                carga = motor.T["CARGA"]
                start = len(carga["r"])
                for offset, step in enumerate(steps, 1):
                    row = [None] * len(carga["h"])
                    row[0] = start + offset
                    row[1] = step
                    row[2] = user
                    row[3] = f"PER={period};EMP={company}"
                    carga["r"].append(row)
                try:
                    motor.procesar_carga()
                    outcomes = [{"step": row[1], "result": "OK" if row[4] == "OK" and row[5] == "OK" else "ERROR",
                                 **({} if row[4] == "OK" and row[5] == "OK" else {"error": str(row[5])})}
                                for row in carga["r"][start:]]
                except Exception as error:
                    outcomes = [{"step": "cierre", "result": "ERROR",
                                 "error": f"La cadena de cierre no pudo completarse: {type(error).__name__}."}]
            ok = bool(outcomes) and all(item["result"] == "OK" for item in outcomes)
            version = info["version"] + (len(outcomes) if ok else 0)
            response = {"result": "OK" if ok else "ERROR", "operation": "close_month",
                        "period": period, "company_code": company, "request_id": key,
                        "version": version, "steps": outcomes,
                        "message": ("Cierre aplicado en una sola escritura del libro." if ok else
                                    "No se aplicaron cambios de negocio; el intento quedó registrado.")}
            status = 200 if ok else 422
            edits = motor_changes(tables, motor, positions) if ok else {}
            if ok:
                version_row = next(n for n, row in zip(positions[META], tables[META]["r"]) if row[0] == "version")
                edits[META] = [(version_row, 2, version)]
            nr = (positions[RECEIPTS][-1] if positions[RECEIPTS] else 1) + 1
            record = (key, digest, status, encode(response), command, now())
            edits[RECEIPTS] = [(nr, j, val) for j, val in enumerate(record, 1)]
            with ZipFile(BytesIO(raw)) as z:
                parts = sheet_parts(z)
                patches = {parts[n]: patch_cells(z.read(parts[n]), cells) for n, cells in edits.items()}
            with temporary(path.parent) as temp, temporary(path.parent) as backup:
                write_archive(temp, raw, patches)
                with backup.open("wb") as f:
                    f.write(raw)
                    f.flush()
                    os.fsync(f.fileno())
                same_workbook(path, raw)
                os.replace(backup, path.parent / "respaldo.xlsx")
                sync_dir(path.parent)
                same_workbook(path, raw)
                os.replace(temp, path)
                sync_dir(path.parent)
            return status, response
