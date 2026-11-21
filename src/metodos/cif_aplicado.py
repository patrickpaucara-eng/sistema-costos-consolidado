# -*- coding: utf-8 -*-
"""MÉTODO · CIF_APLICADO — CÁSCARA (E-106): contrato listo, falta el cálculo. Reemplaza lo que hoy calcula la base.
Complete calcular() y CASOS siguiendo _plantilla_metodo.py; luego quite PENDIENTE y valide."""
PENDIENTE = True
FICHA = dict(nombre='CIF_APLICADO', version="0.0", vigente_desde="2026-01-01", eje='MEDIDA', objetivo='ESTIMADO',
    que_hace='Indirecto provisional con tasa predeterminada y su diferencia con el real', formula="(por definir)", fuente='Horngren cap. 4 (costeo normal)', supuestos="(por definir)", limites="(por definir)")
CONSUME = {'(sin MCD) CTA_OBJ_PER': ['EMPRESA', 'COP_IND', 'COP_IND_APL', 'MATERIAL', 'COP_MOD', 'OBJETO', 'PERIODO']}   # OT-022: entidad MCD -> conceptos
DEPENDE_DE = {}
PARAMETROS = [dict(id="PER", etq="Periodo", tipo="texto"), dict(id="EMP", etq="Empresa", tipo="texto")]
ENTREGA = {'OBJETO': ['CIF_APLICADO', 'SOBRE_SUB_APLICACION']}
def calcular(hechos, parametros, previos):
    raise NotImplementedError("CIF_APLICADO: método pendiente (cáscara)")
CASOS = []
