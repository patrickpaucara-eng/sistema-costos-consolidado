# -*- coding: utf-8 -*-
"""MÉTODO · COSTO_OBJETO_ORDENES — CÁSCARA (E-106): contrato listo, falta el cálculo. Reemplaza lo que hoy calcula la base.
Complete calcular() y CASOS siguiendo _plantilla_metodo.py; luego quite PENDIENTE y valide."""
PENDIENTE = True
FICHA = dict(nombre='COSTO_OBJETO_ORDENES', version="0.0", vigente_desde="2026-01-01", eje='ACUMULACION', objetivo='REAL',
    que_hace='Acumula material, personal e indirectos por orden y periodo', formula="(por definir)", fuente='Horngren cap. 4', supuestos="(por definir)", limites="(por definir)")
CONSUME = {'(sin MCD) CTA_OBJ_REC': ['OBJETO', 'RECURSO', 'PERIODO', 'CANTIDAD_REAL'], '(sin MCD) OBJETO': ['NUMERO', 'ESTADO']}   # OT-022: entidad MCD -> conceptos
DEPENDE_DE = {'PROMEDIO_MOVIL': [('SALIDA', 'MONTO')], 'PERSONAL_PLANILLA': [('OBJETO', 'COSTO_PERSONAL')], 'REPARTO_ETAPAS': [('OBJETO', 'CIF')], 'EXCESO_MERMAS': [('SALIDA', 'MONTO_PRODUCTO')]}
PARAMETROS = [dict(id="PER", etq="Periodo", tipo="texto"), dict(id="EMP", etq="Empresa", tipo="texto")]
ENTREGA = {'OBJETO': ['MD', 'MOD', 'CIF', 'COSTO_PERIODO']}
def calcular(hechos, parametros, previos):
    raise NotImplementedError("COSTO_OBJETO_ORDENES: método pendiente (cáscara)")
CASOS = []
