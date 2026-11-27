"""C34-6: cuatro pedidos sintéticos con oráculos monetarios calculados a mano."""
from __future__ import annotations

from pathlib import Path

from openpyxl import Workbook, load_workbook

from reyna_local.pedido import cotizar_pedido
from reyna_local.recetas_pedido import guardar_familias_en_libro, leer_familias_de_libro


def _libro_y_receta(tmp_path, familia, definiciones, recetas):
    """Guarda la receta en un libro pequeño y la vuelve a leer como haría Pedido."""
    path = tmp_path / f"{familia.lower()}.xlsx"
    workbook = Workbook()
    modelos = {familia: {"familia": familia,
                         "parametros": {d["codigo"]: d for d in definiciones},
                         "inductores": recetas}}
    guardar_familias_en_libro(workbook, modelos)
    workbook.save(path)
    workbook.close()
    persisted = load_workbook(path, read_only=True, data_only=True)
    try:
        return path, leer_familias_de_libro(persisted)[familia]
    finally:
        persisted.close()


def _result(period, activity_rates=(), materials=()):
    activities = []
    measures = []
    rules = []
    drivers = []
    for code, cost, driver, usage in activity_rates:
        activities.append({"codigo": code, "nombre": code, "costo": cost})
        rules.append({"etapa": "P4C", "origen": code, "inductor": driver})
        drivers.append({"codigo": driver, "nombre": driver, "unidad": "h"})
        measures.append({"MED_PER": period, "MED_EMP": "SYN", "MED_CRIT": driver,
                         "MED_NIVEL": "OBJ", "MED_DEST": code, "MED_CAN": usage})
    kardex = [{"material": code, "costo_unitario": unit_cost, "movimiento": "ENTRADA", "fecha": period}
              for code, unit_cost in materials]
    return ({"periodo_actual": period, "sintesis": "REAL", "empresa": {"codigo": "SYN"},
             "actividades": activities, "kardex": kardex,
             "modelo": {"reglas": rules, "inductores": drivers}}, measures)


def _pedido(producto, cantidad, parametros, lote, preparacion=0, adicionales=()):
    return {"producto": producto, "cliente": "CLIENTE PRUEBA", "fecha_requerida": "2026-01-31",
            "cantidad": cantidad, "parametros": parametros, "precio_mercado": 5000,
            "margen_objetivo": 0.2, "contrato": "CERRADO", "unidades_por_lote": lote,
            "preparacion_por_lote": preparacion, "conceptos_adicionales": list(adicionales)}


def test_pedido_metalmecanica_valora_horas_de_soldadura(tmp_path):
    _, modelo = _libro_y_receta(tmp_path, "METAL",
        [{"codigo": "kg", "nombre": "Peso", "unidad": "kg", "minimo": 500, "maximo": 2000}],
        {"ACT_SOLD": {"base": 2, "coeficientes": {"kg": 0.005}, "n": 3}})
    resultado, medidas = _result("2026-01", [("ACT_SOLD", 6000, "DRV_SOLD", 300)])
    cotizacion = cotizar_pedido(None, "SYN", resultado, medidas, modelo,
        _pedido("EJE", 5, {"kg": 1200}, lote=5, preparacion=100))
    # A mano: (2 h + 0,005 × 1.200 kg) × 5 ejes × (S/ 6.000 / 300 h) + S/ 100 = S/ 900.
    assert cotizacion["costo_esperado"] == 900.00


def test_pedido_construccion_combina_cemento_transporte_y_contingencia(tmp_path):
    _, modelo = _libro_y_receta(tmp_path, "OBRA",
        [{"codigo": "m2", "nombre": "Área", "unidad": "m²", "minimo": 10, "maximo": 500}],
        {"MAT_CEM": {"base": 0, "coeficientes": {"m2": 0.2}, "n": 3}})
    resultado, medidas = _result("2026-01", materials=[("MAT_CEM", 8)])
    cotizacion = cotizar_pedido(None, "SYN", resultado, medidas, modelo,
        _pedido("MÓDULO", 5, {"m2": 100}, lote=5,
                adicionales=[{"concepto": "TRANSPORTE", "importe": 75},
                             {"concepto": "CONTINGENCIA", "porcentaje": 10}]))
    # A mano: 5 × 100 m² × 0,2 bolsas/m² × S/ 8 = S/ 800; +75 de transporte;
    # contingencia 10 % de (800 +75) =87,50; total S/ 962,50.
    assert cotizacion["costo_esperado"] == 962.50


def test_pedido_imprenta_suma_papel_impresion_y_preparacion(tmp_path):
    _, modelo = _libro_y_receta(tmp_path, "IMPRENTA",
        [{"codigo": "tiraje", "nombre": "Tiraje", "unidad": "hojas", "minimo": 100, "maximo": 5000}],
        {"MAT_PAPEL": {"base": 0, "coeficientes": {"tiraje": 1}, "n": 3},
         "ACT_IMP": {"base": 0, "coeficientes": {"tiraje": 0.0004}, "n": 3}})
    resultado, medidas = _result("2026-01", [("ACT_IMP", 3000, "DRV_IMP", 100)],
                                 [("MAT_PAPEL", 0.05)])
    cotizacion = cotizar_pedido(None, "SYN", resultado, medidas, modelo,
        _pedido("AFICHE", 1, {"tiraje": 1000}, lote=1, preparacion=40,
                adicionales=[{"concepto": "GASTOS_GENERALES", "importe": 8}]))
    # A mano: 1.000 hojas × S/ 0,05 =50; 0,4 h × S/30 =12; +40 de preparación +8 = S/110.
    assert cotizacion["costo_esperado"] == 110.00


def test_pedido_servicios_valora_horas_y_subcontrato(tmp_path):
    _, modelo = _libro_y_receta(tmp_path, "SERVICIO",
        [{"codigo": "duracion", "nombre": "Duración", "unidad": "h", "minimo": 0.5, "maximo": 8}],
        {"ACT_ATENCION": {"base": 0.5, "coeficientes": {"duracion": 0.5}, "n": 3}})
    resultado, medidas = _result("2026-01", [("ACT_ATENCION", 7000, "DRV_ATENCION", 200)])
    cotizacion = cotizar_pedido(None, "SYN", resultado, medidas, modelo,
        _pedido("CONSULTA", 4, {"duracion": 2}, lote=4,
                adicionales=[{"concepto": "SUBCONTRATO", "importe": 50}]))
    # A mano: 4 consultas × (0,5 +0,5×2) h × S/35/h =210; +S/50 de subcontrato = S/260.
    assert cotizacion["costo_esperado"] == 260.00
