"""OT-C33-1: cobertura de claves DBD para cada tabla con método CREAR."""
from collections import defaultdict
from pathlib import Path
import re

import pytest
from openpyxl import load_workbook

from reyna_local.motor_espejo import Error, Motor, claves_primarias_dbd
from reyna_local.store import Store, content_bytes, load_data


ROOT = Path(__file__).resolve().parents[1]
LIBROS = (
    ("Frenosa", ROOT / "casos/libros/frenosa.xlsx", "FRE"),
    ("SERVITEC", ROOT / "casos/libros/segundo.xlsx", "SRV"),
)


def _records(tables, name):
    table = tables.get(name) or {}
    headers = table.get("h") or []
    return [dict(zip(headers, row)) for row in table.get("r", []) if len(row) == len(headers)]


def _creadores(book):
    tables, _ = load_data(book.read_bytes())
    operations = defaultdict(list)
    for row in _records(tables, "OME"):
        operations[row.get("OME_OPN")].append(row.get("OME_MET"))
    methods = {row.get("MET_COD"): row for row in _records(tables, "MET")}
    mappings = _records(tables, "MCA")
    creators = {}
    for top in _records(tables, "TOP"):
        for code in operations.get(top.get("TOP_OPN"), []):
            method = methods.get(code) or {}
            if str(method.get("MET_TIPO") or "").strip().upper() != "CREAR":
                continue
            table = str(method.get("MET_TABLA") or "").strip()
            if table and table in tables:
                creators.setdefault(table, (code, [row for row in mappings if row.get("MCA_MET") == code]))
    primary = claves_primarias_dbd()
    found = []
    unkeyed = []
    for table, (method, maps) in sorted(creators.items()):
        explicit = tuple(dict.fromkeys(str(row["MCA_COL"]).strip() for row in maps
                                       if str(row.get("MCA_ROL") or "").strip().upper() == "K"))
        key_columns = explicit or tuple(primary.get(table, ()))
        if not key_columns:
            unkeyed.append((book.name, table))
            continue
        mapped = {str(row.get("MCA_COL") or "").strip() for row in maps}
        missing = [column for column in key_columns if column not in mapped]
        found.append({"book": book, "table": table, "method": method, "maps": maps,
                      "key_columns": key_columns, "missing": tuple(missing),
                      "key_source": "MCA-K" if explicit else "DBD-PK"})
    return found, unkeyed


CASES = []
NO_KEY_CREATORS = []
for book_name, book_path, company in LIBROS:
    cases, unkeyed = _creadores(book_path)
    for case in cases:
        case["book_name"] = book_name
        case["company"] = company
        CASES.append(case)
    NO_KEY_CREATORS.extend((book_name, table) for _, table in unkeyed)


def _motor(book):
    tables, _ = load_data(book.read_bytes())
    motor = Motor.__new__(Motor)
    motor.T = {name: {"h": data["h"], "r": [list(row) for row in data["r"]]}
               for name, data in tables.items()}
    motor.tr = {}
    motor.creados = []
    motor.val = lambda _origin, value: value
    return motor


def _crear_con_clave(case, motor, values):
    mappings = []
    for row in case["maps"]:
        mapping = [row.get(column) for column in
                   ("MCA_MET", "MCA_SEC", "MCA_COL", "MCA_ROL", "MCA_OPE", "MCA_ORI", "MCA_VAL")]
        column = str(mapping[2] or "").strip()
        if column in values:
            mapping[5], mapping[6] = "LIT", values[column]
        mappings.append(mapping)
    motor.m_CREAR(case["method"], case["table"], None, None, None, mappings)


def _case_id(case):
    return f"{case['book_name']}-{case['table']}"


@pytest.mark.parametrize("case", CASES, ids=_case_id)
def test_segunda_creacion_de_misma_clave_dbd_se_rechaza_sin_agregar_fila(case):
    assert not case["missing"], f"{case['table']} no asigna su clave DBD: {case['missing']}"
    motor = _motor(case["book"])
    before = len(motor.T[case["table"]]["r"])
    values = {column: f"C33-UNICA-{case['table']}-{index}" for index, column in enumerate(case["key_columns"])}

    _crear_con_clave(case, motor, values)
    after_first = [list(row) for row in motor.T[case["table"]]["r"]]
    assert len(after_first) == before + 1
    with pytest.raises(Error, match=rf"ya existe {re.escape(case['table'])}"):
        _crear_con_clave(case, motor, values)
    assert motor.T[case["table"]]["r"] == after_first


def test_catalogo_cubre_todas_las_tablas_creables_y_declara_claves():
    expected = set()
    for book_name, book_path, _company in LIBROS:
        tables, _ = load_data(book_path.read_bytes())
        cases, no_key = _creadores(book_path)
        expected.update((book_name, case["table"]) for case in cases)
        assert no_key == [(name, table) for name, table in NO_KEY_CREATORS if name == book_name]
        assert not no_key, f"Documentar sin inventar clave: {book_name}: {no_key}"
        assert all(not case["missing"] for case in cases), f"Faltan columnas de clave en {book_name}"
        assert "TRX" in tables
    assert expected == { (case["book_name"], case["table"]) for case in CASES }


@pytest.mark.parametrize("book_name,book,company", LIBROS, ids=lambda value: value if isinstance(value, str) else None)
def test_linea_acepta_mismo_evento_con_numero_distinto_y_rechaza_repetir_linea(book_name, book, company):
    case = next(case for case in CASES if case["book_name"] == book_name and case["table"] == "LINEA")
    assert case["key_columns"] == ("LIN_EVE", "LIN_NUM")
    motor = _motor(book)
    before = len(motor.T["LINEA"]["r"])
    _crear_con_clave(case, motor, {"LIN_EVE": "C33-EVENTO-COMUN", "LIN_NUM": 1})
    _crear_con_clave(case, motor, {"LIN_EVE": "C33-EVENTO-COMUN", "LIN_NUM": 2})
    after_two = [list(row) for row in motor.T["LINEA"]["r"]]
    assert len(after_two) == before + 2
    with pytest.raises(Error, match=r"ya existe LINEA"):
        _crear_con_clave(case, motor, {"LIN_EVE": "C33-EVENTO-COMUN", "LIN_NUM": 1})
    assert motor.T["LINEA"]["r"] == after_two


def _libro_con_estimaciones(path):
    workbook = load_workbook(LIBROS[0][1])
    sheet = workbook["ESTIMACION"]
    headers = [str(value) for value in next(sheet.iter_rows(min_row=1, max_row=1, values_only=True))]
    for number in (1, 2):
        values = {
            "EST_NUM": f"C33-COL-{number:03d}", "EST_EMP": "FRE", "EST_PER": "2010-12",
            "EST_CLI": "MERCADO", "EST_PRO": "SW50", "EST_CAN": 100,
            "EST_CST": 1234.5, "EST_ESTADO": "PENDIENTE", "EST_OBJ": None,
            "EST_VER": 1, "EST_ORIGEN": "C33-COL", "EST_PRECIO": 1000, "EST_RENT": 0.3,
        }
        sheet.append([values.get(header) for header in headers])
    workbook.save(path)
    workbook.close()


def test_dos_t13_con_misma_sugerencia_rechaza_colision_sin_escritura_parcial(tmp_path):
    workbook_path = tmp_path / "frenosa_colision.xlsx"
    _libro_con_estimaciones(workbook_path)
    store = Store(tmp_path / "espacios")
    space = store.create({"name": "C33-colision", "workbook_path": str(workbook_path)})
    identifier = space["id"]
    code = "OT-FRE-SW50-0001"

    def header(estimate):
        return {"FECHA": 20101228, "PER": "2010-12", "EMP": "FRE", "EST": estimate,
                "OBJ": code, "MONTO": 0, "REF": "C33-SESION", "ALG": "COSTO_PROYECTADO",
                "VER": 1, "HUELLA": "C33-COL"}

    first = header("C33-COL-001")
    second = header("C33-COL-002")
    suggestion_a = store.sugerir_codigo_objeto(identifier, "T13", first)
    suggestion_b = store.sugerir_codigo_objeto(identifier, "T13", second)
    assert suggestion_a["codigo"] == suggestion_b["codigo"] == code

    accepted, first_result = store.execute(identifier, {
        "transaction": "T13", "user": "JCOSTOS", "request_id": "C33-SESSION-A",
        "header": first, "lines": [],
    })
    assert accepted == 200, first_result
    raw_after_first = content_bytes(store.path(identifier))
    tables_after_first, _ = load_data(raw_after_first)
    business_tables = ("OBJETO", "ESTIMACION", "TARIFA", "EVENTO", "LINEA", "EXISTENCIA", "KARDEX")
    snapshot = {name: [list(row) for row in tables_after_first[name]["r"]]
                for name in business_tables if name in tables_after_first}

    rejected, second_result = store.execute(identifier, {
        "transaction": "T13", "user": "JCOSTOS", "request_id": "C33-SESSION-B",
        "header": second, "lines": [],
    })
    assert rejected == 422
    assert "ya existe OBJETO" in second_result["error"]
    assert code in second_result["error"]
    tables_after_second, _ = load_data(content_bytes(store.path(identifier)))
    assert {name: [list(row) for row in tables_after_second[name]["r"]]
            for name in snapshot} == snapshot
    assert second_result["version"] == first_result["version"]
