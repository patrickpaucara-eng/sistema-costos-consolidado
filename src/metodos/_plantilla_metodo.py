# -*- coding: utf-8 -*-
"""PLANTILLA DE MÉTODO DE COSTEO (formato compatible, E-105 + OT-022). Copie este archivo como metodos/<nombre>.py.
Reglas: (1) función PURA: no lee archivos, no escribe en la base, no imprime; recibe hechos y devuelve resultados.
(2) CONSUME por CONCEPTOS: {entidad MCD: [concepto]} (el traductor es metodos.semantica); (3) si faltan hechos,
lanza ValueError con el motivo: nunca inventa ni imputa en silencio. (4) reproducible: mismos hechos + parámetros =
mismo resultado (si usa azar, semilla fija como parámetro). (5) redondeo: 2 decimales, mitad hacia arriba (red())."""

FICHA = dict(
    nombre="MI_METODO",            # en MAYÚSCULAS, único; se registra en METODO_REGISTRADO
    version="0.1",                 # súbala cuando cambie la fórmula
    vigente_desde="2026-01-01",    # VIGENCIA (Tino): desde qué fecha rige esta versión; se usa la vigente al inicio del periodo
    eje="ACUMULACION",             # VALUACION | MEDIDA | REPARTO | ACUMULACION | ALCANCE | LIQUIDACION | AJUSTE_CONTABLE | ESTIMACION
    objetivo="REAL",               # REAL | CONTABLE | ESTIMADO
    que_hace="Qué calcula, en una frase.",
    formula="La fórmula exacta.",
    fuente="Autor (año), obra, capítulo / norma (NIC 2 §…).",
    supuestos="Lo que se asume.",
    limites="Cuándo NO usarlo.",
)

CONSUME = {                        # hechos que lee: {entidad MCD: [concepto]}   (OT-022)
    "OBJETO": ["NUMERO", "CANTIDAD", "AVANCE", "ESTADO"],
    "CTA_OBJ_REC": ["OBJETO", "RECURSO", "PERIODO", "CANTIDAD_REAL"],
}

DEPENDE_DE = {                     # resultados de OTROS métodos que necesita: {método: [(tipo, concepto)]}
    # "PROMEDIO_MOVIL": [("SALIDA", "MONTO")],
}

PARAMETROS = [                     # ajustes que el usuario puede cambiar
    dict(id="metodo_ue", etq="Unidades equivalentes", tipo="texto", opciones=["PROMEDIO", "PEPS"], defecto="PROMEDIO"),
]

ENTREGA = {                        # lo que devuelve: {tipo: [conceptos]}  (formato largo de RESULTADO_METODO)
    "OBJETO": ["UNIDADES_EQUIVALENTES", "COSTO_UNITARIO", "COSTO_TERMINADO", "COSTO_EN_PROCESO"],
}


def red(x, n=2):
    from decimal import Decimal as D, ROUND_HALF_UP
    return float(D(str(x)).quantize(D(1).scaleb(-n), rounding=ROUND_HALF_UP))


def calcular(hechos, parametros, previos):
    """hechos   = {entidad MCD: [ {concepto: valor}, ... ]}   (solo lo declarado en CONSUME, del periodo y empresa pedidos)
       parametros = {id: valor}                         previos = {método: [(tipo, clave, concepto, valor)]}
       devuelve  (resultados, explicacion)
         resultados  = [(tipo, clave, concepto, valor)]  con tipo y concepto de ENTREGA; clave = código del hecho (p. ej. "OE-03")
         explicacion = [frases paso a paso que permiten rehacer el número a mano]"""
    resultados, explicacion = [], []
    for o in hechos["OBJETO"]:
        if o["CANTIDAD"] in (None, ""):
            raise ValueError(f"{o['NUMERO']}: falta la cantidad del objeto")
        # ... su cálculo ...
        resultados.append(("OBJETO", o["NUMERO"], "COSTO_UNITARIO", red(0)))
    explicacion.append("Paso 1: ...")
    return resultados, explicacion


# Casos de verdad conocida (calculados a mano): los usa el validador. Al menos uno.
CASOS = [
    dict(nombre="Ejemplo mínimo",
         hechos={"OBJETO": [dict(NUMERO="X1", CANTIDAD=10, AVANCE=100, ESTADO="A")], "CTA_OBJ_REC": []},
         parametros={"metodo_ue": "PROMEDIO"}, previos={},
         espera=[("OBJETO", "X1", "COSTO_UNITARIO", 0.0)]),
]
