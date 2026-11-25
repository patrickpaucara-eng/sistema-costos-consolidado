"""Construye SERVITEC a partir del diseño manual; no modifica Frenosa."""
import calendar
import shutil
import sys
from pathlib import Path
from openpyxl import load_workbook

ROOT = Path(__file__).resolve().parents[2]
EMP = 'SRV'
FACTORES = (0.8, 0.9, 0.9, 1.0, 1.0, 1.1, 1.0, 1.1)


def generar(plantilla, salida):
    shutil.copyfile(plantilla, salida)
    w = load_workbook(salida)
    names = ['EMPRESA', 'PERIODO', 'OBJETO', 'RECURSO', 'EVENTO', 'LINEA', 'KARDEX', 'REGLA_REPARTO', 'CRITERIO', 'MEDIDA', 'CENTRO', 'ACTIVIDAD', 'VENTA', 'CLIENTE', 'COMPONENTE', 'ASIGNACION', 'EXISTENCIA', 'KARDEX_SALDO']
    for n in names:
        if w[n].max_row > 1:
            w[n].delete_rows(2, w[n].max_row - 1)
    def put(sheet, **row):
        cols = [c.value for c in w[sheet][1]]
        for col in cols:
            if col and col.endswith('_EMP') and col not in row: row[col] = EMP
        w[sheet].append([row.get(c) for c in cols])
    put('EMPRESA', EMP_COD=EMP, EMP_NOM='SERVITEC SAC', EMP_MON_FUN='PEN')
    types = {r[0] for r in w['TIPO_RECURSO'].iter_rows(min_row=2, values_only=True)}
    if 'MAT_DIR' not in types: put('TIPO_RECURSO', TRE_COD='MAT_DIR', TRE_ELE='MAT', TRE_CAP=0, TRE_INV='S')
    for code, desc, typ, unit in [('MAT_COBRE','Cobre','MAT_DIR','kg'),('MOD','Técnicos','PERS_DIR','S/'),('ALQ','Alquiler','INDIRECTO','S/'),('ENE','Energía','INDIRECTO','S/'),('SUP','Supervisión','INDIRECTO','S/'),('ADM01','Administración','INDIRECTO','S/')]:
        put('RECURSO', REC_COD=code, REC_DES=desc, REC_TRE=typ, REC_UNI=unit, REC_ACTIVO='S')
    for code, typ, order in [('CA_MANT','APR',1),('CA_CAL','APR',1),('CA_TALLER','PRO',2),('ADM_SRV','ADM',2),('ALM_SRV','ALM',0)]:
        put('CENTRO', CEN_COD=code, CEN_TIPO=typ, CEN_FUN='PRD' if typ in ('APR','PRO') else typ, CEN_ORD=order, CEN_ACTIVO='S')
    for code, desc in [('DES','Desarmado'),('BOB','Bobinado'),('PRU','Pruebas')]: put('ACTIVIDAD', ACT_COD=code, ACT_DES=desc, ACT_UNI='h', ACT_NIVEL='O')
    for product, qty in [('REB',14),('MPR',2)]: put('COMPONENTE', CMP_PRO=product, CMP_REC='MAT_COBRE', CMP_CAN_EST=qty, CMP_MERMA=5)
    put('ASIGNACION', ASI_TIPO='TRE', ASI_OBJ='MAT_DIR', ASI_PROP='INV', ASI_ALG='ALG-PROM', ASI_DESDE=19000101)
    put('CLIENTE', CLI_COD='CLIENTE', CLI_NOM='Mercado de prueba', CLI_CANAL='DIRECTO')
    rules = [('P1','MAT_COBRE','CONSUMO'),('P2','MOD','HORAS_MOD'),('P4A','ALQ','DIST_ALQ'),('P4A','ENE','DIST_ENE'),('P4A','SUP','DIST_SUP'),('P4A','ADM01','DIR_ADM'),('P4B','CA_MANT','MANT'),('P4B','CA_CAL','CAL'),('P4D','CA_TALLER','TALLER_ACT'),('P4C','DES','DES_OT'),('P4C','BOB','BOB_OT'),('P4C','PRU','PRU_OT'),('P5','ADM_SRV','ADM_OT')]
    for stage, origin, crit in rules:
        put('REGLA_REPARTO', RRE_ETAPA=stage, RRE_ORIGEN=origin, RRE_CRIT=crit, RRE_DESDE=19000101, RRE_FUENTE='Diseño SERVITEC')
        put('CRITERIO', CRI_COD=crit, CRI_DES=crit, CRI_UNI='h', CRI_ACTIVO='S')
    counter = 0
    def event(per, day, trx, obj=None):
        nonlocal counter
        counter += 1
        date = int(per.replace('-','') + f'{day:02d}')
        put('EVENTO', EVE_NUM=counter, EVE_TRX=trx, EVE_FEC=date, EVE_PER=per, EVE_OBJ=obj, EVE_MON='PEN', EVE_TC=1)
        return counter, date
    def material(per, day, qty, price=None, obj=None, excess=0, saldo=False):
        eid, date = event(per, day, 'T15' if obj else 'T14', obj)
        put('LINEA', LIN_EVE=eid, LIN_NUM=1, LIN_REC='MAT_COBRE', LIN_CAN=qty, LIN_CU_DOC=price, LIN_MTO=qty*price if price is not None else None, LIN_EXC=excess)
        put('KARDEX', KDX_EVE=eid, KDX_LIN=1, KDX_ALM='ALM_SRV', KDX_PER=per, KDX_FEC=date, KDX_TRX='T15' if obj else 'T14', KDX_CPB='SALDO' if saldo else 'COMPRA', KDX_REC='MAT_COBRE', KDX_CAN=-qty if obj else qty, KDX_VAL=qty*price if price is not None else None)
    def measure(per, crit, level, dest, qty): put('MEDIDA', MED_PER=per, MED_CRIT=crit, MED_NIVEL=level, MED_DEST=dest, MED_CAN=qty)
    for m, factor in enumerate(FACTORES, 1):
        per = f'2025-{m:02d}'; n = round(10 * factor)
        put('PERIODO', PER_COD=per, PER_INI=int(f'2025{m:02d}01'), PER_FIN=int(f'2025{m:02d}{calendar.monthrange(2025,m)[1]}'), PER_EST='A')
        for prod in ('REB','MPR'):
            oid = f'OT-SRV-{prod}-{per}'
            put('OBJETO', OBJ_NUM=oid, OBJ_PRO=prod, OBJ_CAN=n, OBJ_EST='T', OBJ_FEC_TER=int(f'2025{m:02d}{calendar.monthrange(2025,m)[1]}'))
            put('VENTA', VTA_EVE=m, VTA_LIN=1 if prod=='REB' else 2, VTA_PER=per, VTA_CLI='CLIENTE', VTA_REC=prod, VTA_CAN=n, VTA_ING=n*(3000 if prod=='REB' else 800), VTA_CANAL='DIRECTO')
        if m == 1: material(per, 1, 100, 40, saldo=True)
        qreb, qmpr = (150,20) if m == 7 else (14.7*n, 2*n)
        material(per, 5, 200 if m >= 7 else qreb+qmpr, 43 if m == 7 else 43.5 if m == 8 else 40)
        material(per, 10, qreb, obj=f'OT-SRV-REB-{per}', excess=3 if m == 7 else 0)
        material(per, 11, qmpr, obj=f'OT-SRV-MPR-{per}')
        for rec, amount in [('MOD',12000),('ALQ',3000),('ENE',1500),('SUP',2500),('ADM01',2000)]:
            eid, _ = event(per, 20, 'T17')
            put('LINEA', LIN_EVE=eid, LIN_NUM=1, LIN_REC=rec, LIN_CAN=1, LIN_CU_DOC=amount, LIN_MTO=amount)
        for crit, vals in [('DIST_ALQ',(20,10,70)),('DIST_ENE',(10,10,80)),('DIST_SUP',(20,20,60))]:
            for dest, val in zip(('CA_MANT','CA_CAL','CA_TALLER'), vals): measure(per,crit,'CEN',dest,val)
        for crit, vals in [('MANT',(('CA_CAL',20),('CA_TALLER',80))),('CAL',(('CA_MANT',10),('CA_TALLER',90))),('DIR_ADM',(('ADM_SRV',1),))]:
            for dest,val in vals: measure(per,crit,'CEN',dest,val)
        for act,val in [('DES',300),('BOB',500),('PRU',200)]: measure(per,'HORAS_MOD','ACT',act,val*factor)
        for act,val in [('DES',30),('BOB',50),('PRU',20)]: measure(per,'TALLER_ACT','ACT',act,val)
        for crit, weights in [('DES_OT',(200,100)),('BOB_OT',(500,0)),('PRU_OT',(100,60)),('ADM_OT',(1,1))]:
            for prod,val in zip(('REB','MPR'),weights):
                if val: measure(per,crit,'OBJ',f'OT-SRV-{prod}-{per}',val*(factor if crit != 'ADM_OT' else 1))
        measure(per,'PRU_OT','CAP','PRU',200)
    for user in w['USUARIO'].iter_rows(min_row=2):
        if user[0].value: user[3].value = EMP
    w.save(salida); w.close()
    return salida

if __name__ == '__main__':
    print(generar(Path(sys.argv[1]) if len(sys.argv)>1 else ROOT/'casos/plantilla_dbd.xlsx', Path(sys.argv[2]) if len(sys.argv)>2 else ROOT/'casos/libros/segundo.xlsx'))
