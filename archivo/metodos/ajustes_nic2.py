# -*- coding: utf-8 -*-
"""MÉTODO · AJUSTES_NIC2 — CÁSCARA (E-106): contrato listo, falta el cálculo. Reemplaza lo que hoy calcula la base.
Complete calcular() y CASOS siguiendo _plantilla_metodo.py; luego quite PENDIENTE y valide."""
PENDIENTE = True
FICHA = dict(nombre='AJUSTES_NIC2', version="0.0", vigente_desde="2026-01-01", eje='AJUSTE_CONTABLE', objetivo='CONTABLE',
    que_hace='Capacidad normal, ocio a gasto y rebaja al valor neto realizable', formula="(por definir)", fuente='NIC 2 §13, §28-33', supuestos="(por definir)", limites="(por definir)")
CONSUME = {'TARIFA': ['EMPRESA', 'PERIODO', 'TIPO'], '(sin MCD) EXISTENCIA': ['CENTRO', 'EMPRESA', 'RECURSO'], '(sin MCD) MOV_CIERRE': ['ALMACEN', 'EMPRESA', 'PERIODO', 'RECURSO', 'MCI_REF', 'TRANSACCION'], '(sin MCD) CTA_GASTO': ['CENTRO', 'CGA_CON', 'PERIODO']}   # OT-022: entidad MCD -> conceptos
DEPENDE_DE = {'LIQUIDACION_ORDENES': [('PRODUCTO', 'COSTO_UNITARIO')], 'REPARTO_ETAPAS': [('CENTRO', 'OCIO')]}
PARAMETROS = [dict(id="PER", etq="Periodo", tipo="texto"), dict(id="EMP", etq="Empresa", tipo="texto")]
ENTREGA = {'EXISTENCIA': ['REBAJA_VNR', 'VALOR_CONTABLE'], 'CENTRO': ['OCIO_A_GASTO']}
def calcular(hechos, parametros, previos):
    raise NotImplementedError("AJUSTES_NIC2: método pendiente (cáscara)")
CASOS = []
