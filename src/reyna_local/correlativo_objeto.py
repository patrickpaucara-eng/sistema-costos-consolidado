"""Sugerencias de correlativos para transacciones que crean objetos en el DBD."""


def _registros(tables, name):
    table = tables.get(name) or {}
    headers = table.get("h") or []
    if len(headers) != len(set(headers)):
        return []
    return [dict(zip(headers, row)) for row in table.get("r", []) if len(row) == len(headers)]


def especificacion_creacion(tables, transaction):
    """Descubre, por TOP→OME→MET/MCA, si la transacción crea OBJETO y qué variable lo identifica."""
    try:
        tops = [row for row in _registros(tables, "TOP") if row.get("TOP_TRX") == transaction]
        operations = _registros(tables, "OME")
        methods = {row.get("MET_COD"): row for row in _registros(tables, "MET")}
        mappings = _registros(tables, "MCA")
        form_fields = [row for row in _registros(tables, "TRX_CAMPO") if row.get("TCA_TRX") == transaction]
    except (TypeError, ValueError):
        return None
    if not tops:
        return None

    plan = []
    try:
        for top in sorted(tops, key=lambda row: int(row["TOP_SEC"])):
            opn = top["TOP_OPN"]
            for operation in sorted((row for row in operations if row.get("OME_OPN") == opn),
                                    key=lambda row: int(row["OME_SEC"])):
                method = methods.get(operation.get("OME_MET"))
                if method:
                    code = method["MET_COD"]
                    plan.append((method, [row for row in mappings if row.get("MCA_MET") == code]))
    except (KeyError, TypeError, ValueError):
        return None

    declared = {str(row.get("TCA_VAR")): str(row.get("TCA_NIVEL")) for row in form_fields}
    creators = [index for index, (method, _) in enumerate(plan)
                if str(method.get("MET_TIPO") or "").strip().upper() == "CREAR"
                and str(method.get("MET_TABLA") or "").strip().upper() == "OBJETO"]
    if not creators:
        return None

    specs = []
    for index in creators:
        _, create_map = plan[index]
        code_map = next((row for row in create_map
                         if row.get("MCA_COL") == "OBJ_NUM" and row.get("MCA_ORI") == "VAR"), None)
        product_map = next((row for row in create_map
                            if row.get("MCA_COL") == "OBJ_PRO" and row.get("MCA_ORI") == "VAR"), None)
        if not code_map or not code_map.get("MCA_VAL") or not product_map or not product_map.get("MCA_VAL"):
            return None
        product_variable = str(product_map["MCA_VAL"])
        product_source = None
        if declared.get(product_variable) == "C":
            product_source = {"tipo": "campo", "variable": product_variable, "contexto": [product_variable]}
        else:
            for method, method_map in reversed(plan[:index]):
                if (str(method.get("MET_TIPO") or "").strip().upper() != "LEER"
                        or not method.get("MET_TABLA")):
                    continue
                outputs = [row for row in method_map
                           if row.get("MCA_ROL") == "V" and row.get("MCA_OPE") == "LEE"
                           and row.get("MCA_ORI") == "VAR" and str(row.get("MCA_VAL")) == product_variable]
                keys = [row for row in method_map
                        if row.get("MCA_ROL") == "K" and row.get("MCA_ORI") == "VAR"]
                for output in outputs:
                    if not keys or any(declared.get(str(row.get("MCA_VAL"))) != "C" for row in keys):
                        continue
                    product_source = {
                        "tipo": "busqueda",
                        "tabla": method["MET_TABLA"],
                        "columna": output["MCA_COL"],
                        "claves": [{"columna": row["MCA_COL"], "variable": str(row["MCA_VAL"])} for row in keys],
                        "contexto": [str(row["MCA_VAL"]) for row in keys],
                    }
                    break
                if product_source:
                    break
        if product_source is None:
            return None
        specs.append({"variable": str(code_map["MCA_VAL"]), "nivel": declared.get(str(code_map["MCA_VAL"])),
                      "producto_variable": product_variable, "producto": product_source})

    first = specs[0]
    if any(spec != first for spec in specs[1:]):
        return None
    return first


def resolver_producto(tables, spec, header, lines, company):
    """Resuelve el producto desde el campo de la forma o desde una lectura DBD previa."""
    variable = spec["producto_variable"]
    value = header.get(variable)
    if value not in (None, ""):
        return str(value).strip() or None
    for line in lines or []:
        value = line.get(variable)
        if value not in (None, ""):
            candidates = {str(line.get(variable)).strip() for line in lines if line.get(variable) not in (None, "")}
            return candidates.pop() if len(candidates) == 1 else None

    source = spec["producto"]
    if source["tipo"] != "busqueda":
        return None
    key_values = {key["columna"]: header.get(key["variable"]) for key in source["claves"]}
    if any(value in (None, "") for value in key_values.values()):
        return None
    table = tables.get(source["tabla"])
    if not table or source["columna"] not in table["h"] or any(key not in table["h"] for key in key_values):
        return None
    indices = {name: table["h"].index(name) for name in (source["columna"], *key_values)}
    company_columns = [i for i, name in enumerate(table["h"]) if isinstance(name, str) and name.endswith("_EMP")]
    matches = []
    for row in table["r"]:
        if len(row) != len(table["h"]):
            continue
        if any(row[indices[column]] is None or str(row[indices[column]]) != str(value)
               for column, value in key_values.items()):
            continue
        if any(row[i] not in (None, "", company, "*") for i in company_columns):
            continue
        product = row[indices[source["columna"]]]
        if product not in (None, ""):
            matches.append(str(product).strip())
    return matches[0] if len(matches) == 1 else None


def siguiente_codigo(tables, company, product):
    """Devuelve el menor correlativo disponible con el mismo patrón de C32-1."""
    product = str(product or "").strip()
    company = str(company or "").strip()
    if not company or not product or "\x00" in product:
        return None
    prefix = f"OT-{company}-{product}-"
    if len(prefix) + 4 > 80:
        raise ValueError("El código generado supera el límite permitido.")
    table = tables.get("OBJETO") or {}
    if table.get("h", []).count("OBJ_NUM") != 1:
        raise ValueError("El libro no declara OBJ_NUM de forma única en OBJETO.")
    code_index = table["h"].index("OBJ_NUM")
    used = {str(row[code_index]) for row in table.get("r", []) if len(row) > code_index and row[code_index] not in (None, "")}
    number = next((n for n in range(1, 10000) if f"{prefix}{n:04d}" not in used), None)
    if number is None:
        raise ValueError("Se agotaron los códigos de orden para este producto.")
    return f"{prefix}{number:04d}"
