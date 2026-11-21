"""Contrato de RESULTADOS (motor/analítica → pantallas, dashboard, exportadores, informes).
El motor (Claude) produce un dict con esta forma; las pantallas y documentos (Codex) SOLO leen esto.
Así ambos trabajan en paralelo sin cruzarse. Cambiar el contrato requiere actualizar este archivo, el ejemplo y avisar."""
SINTESIS = {"REAL", "CONTABLE", "ESTIMADO"}
TIPOS_SERIE = {"HISTORICO", "ACTUAL", "PROYECTADO_DET", "PROYECTADO_EST"}
CATEGORIAS_NIIF18 = {"OPERACION", "INVERSION", "FINANCIACION", "IMPUESTOS"}
CAMPOS = {
    "empresa": dict, "periodo_actual": str, "sintesis": str, "moneda": str, "kpi": dict,
    "objetos": list, "actividades": list, "serie": list, "estado_resultados": list,
    "relevancia": list, "hallazgos": list, "propuestas": list, "escenarios": list,
}
KPI = ("ventas", "costo_total", "margen_operativo", "rentabilidad", "costo_unitario_prom")
OBJ = ("codigo", "producto", "cantidad", "md", "mod", "cif", "admin", "gasto_venta", "financiero",
       "costo_total", "costo_unitario", "ingreso", "margen")


def validar(r):
    e = []
    for k, t in CAMPOS.items():
        if not isinstance(r.get(k), t): e.append(f"falta o tipo incorrecto: {k}")
    if e: return e
    if r["sintesis"] not in SINTESIS: e.append("sintesis inválida")
    e += [f"kpi.{k}" for k in KPI if k not in r["kpi"]]
    for o in r["objetos"]:
        e += [f"objeto {o.get('codigo')}: falta {k}" for k in OBJ if k not in o]
        if all(k in o for k in OBJ):
            suma = sum(o[k] for k in ("md", "mod", "cif", "admin", "gasto_venta", "financiero"))
            if abs(suma - o["costo_total"]) > 0.01: e.append(f"objeto {o['codigo']}: elementos ≠ costo_total")
    for s in r["serie"]:
        if s.get("tipo") not in TIPOS_SERIE: e.append(f"serie {s.get('periodo')}: tipo inválido")
        if s.get("tipo") == "PROYECTADO_EST" and not all(k in s for k in ("p05", "p50", "p95")): e.append(f"serie {s.get('periodo')}: estocástico sin P05/P50/P95")
    for x in r["estado_resultados"]:
        if x.get("categoria") not in CATEGORIAS_NIIF18: e.append(f"estado_resultados: categoría inválida {x.get('categoria')}")
    if r["sintesis"] == "CONTABLE":
        if any(o["financiero"] for o in r["objetos"]): e.append("CONTABLE: gasto financiero en el costo del objeto (NIC 2 lo prohíbe)")
    return e
