# -*- coding: utf-8 -*-
"""CAT-01 · Fórmulas de impacto registradas (ESPEC_ANALITICA2 §7, D-5).
Firma: impacto(hallazgo, indice, hechos) -> {"tipo", "valor", "motivo"}; indice = {(tipo, clave, concepto): Decimal}."""
from decimal import Decimal as D


def _v(x):
    return None if x in (None, "") else D(str(x))


def contrafactual_familia(h, indice, hechos):
    return {"tipo": "CONTRAFACTUAL", "valor": None, "motivo": "CU de la familia (§9.4 V4.1)"}


def diferencia_total(h, indice, hechos):
    return {"tipo": "CONTRAFACTUAL", "valor": indice.get(("OBJETO", str(h["REFERENCIA"]), "DIFERENCIA")), "motivo": "ALG-08"}


def obj_can_x_desv(h, indice, hechos):
    return {"tipo": "CONTRAFACTUAL", "valor": None, "motivo": "OBJ_CAN × (CU − CU familia)"}


def elemento(h, indice, hechos):
    return {"tipo": "CONTRAFACTUAL", "valor": _v(h.get("IMPACTO")), "motivo": "ALG-13"}


def simulacion(h, indice, hechos):
    return {"tipo": "SIMULACION", "valor": None, "motivo": "capa 2 sobre una copia"}


def sin_impacto(h, indice, hechos):
    return {"tipo": "SIN_IMPACTO_MONETARIO", "valor": None, "motivo": "la regla no mueve dinero directamente"}


REGISTRO_IMPACTOS = {"CONTRAFACTUAL_FAMILIA": contrafactual_familia, "DIFERENCIA_TOTAL": diferencia_total,
                     "OBJ_CAN_X_DESV": obj_can_x_desv, "ELEMENTO": elemento, "SIMULACION": simulacion,
                     "SIN_IMPACTO": sin_impacto}
