# -*- coding: utf-8 -*-
"""MÉTODO · EXCESO_MERMAS — CÁSCARA (E-106): contrato listo, falta el cálculo. Reemplaza lo que hoy calcula la base.
Complete calcular() y CASOS siguiendo _plantilla_metodo.py; luego quite PENDIENTE y valide."""
PENDIENTE = True
FICHA = dict(nombre='EXCESO_MERMAS', version="0.0", vigente_desde="2026-01-01", eje='ALCANCE', objetivo='CONTABLE',
    que_hace='Separa del consumo lo normal (al producto) y el exceso o merma anormal (a gasto)', formula="(por definir)", fuente='NIC 2 §16(a)', supuestos="(por definir)", limites="(por definir)")
CONSUME = {'(sin MCD) LINEA': ['EVENTO', 'NUMERO', 'RECURSO', 'CANTIDAD', 'LIN_MTO'], '(sin MCD) CTA_OBJ_REC': ['OBJETO', 'RECURSO', 'PERIODO', 'COR_CAN_PERM', 'CANTIDAD_REAL']}   # OT-022: entidad MCD -> conceptos
DEPENDE_DE = {'PROMEDIO_MOVIL': [('SALIDA', 'MONTO')]}
PARAMETROS = [dict(id="PER", etq="Periodo", tipo="texto"), dict(id="EMP", etq="Empresa", tipo="texto")]
ENTREGA = {'SALIDA': ['MONTO_PRODUCTO', 'MONTO_GASTO']}
def calcular(hechos, parametros, previos):
    raise NotImplementedError("EXCESO_MERMAS: método pendiente (cáscara)")
CASOS = []
