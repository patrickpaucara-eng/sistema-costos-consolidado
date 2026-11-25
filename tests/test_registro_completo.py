# -*- coding: utf-8 -*-
"""E26 (decisión del dueño 25-nov): registro diario completo. Cada transacción adicional definida en el libro se ejecuta en una copia
de Frenosa con los maestros mínimos (persona, causa, proveedor, producto terminado) creados solo en la copia.
T09/T12/T13 (cotizar, reestimar, abrir OT) se prueban con el cotizador (C28)."""
import json, sys, threading
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError
from openpyxl import load_workbook
from reyna_local.__main__ import ReynaServer

ROOT = Path(__file__).resolve().parents[1]


def test_transacciones_adicionales_ejecutan(tmp_path):
    res = {}
    tmp=tmp_path
    b=load_workbook(str(ROOT / "casos/libros/frenosa.xlsx"))
    b["PERSONA"].append(["OP01","Operario 1","PLANTA_FRE","S","FRE"])
    b["CAUSA_INEF"].append(["C1","Fuera de medida","RECHAZO","S","PERDIDA"]); b["CAUSA_INEF"].append(["P1","Falla eléctrica","PARADA","N","PERDIDA"])
    b["PROVEEDOR"].append(["PRV1","Proveedor 1","FRE"]); b["PERFIL_TRX"].append(["COSTOS","T21"])
    b["RECURSO"].append(["SW50","Producto SW50 de prueba","PRODUCTO","kg",None,"S","FRE"]); b["PRODUCTO_PT"].append(["SW50","SW50",1,None,"FRE"]); b["ASIGNACION"].append(["TRE","PRODUCTO","INV","ALG-PROM",19000101,"FRE"]); b["EXISTENCIA"].append(["SW50","ALM_FRE",10,50,5,"FRE"]); lib=tmp/"f.xlsx"; b.save(lib)
    srv=ReynaServer(tmp/"e",0); threading.Thread(target=srv.serve_forever,daemon=True).start(); B=f"http://127.0.0.1:{srv.server_port}"
    def q(m,u,bd=None):
        try:
            with urlopen(Request(B+u,data=None if bd is None else json.dumps(bd).encode(),method=m,headers={"Content-Type":"application/json"}),timeout=60) as r: return r.status,json.load(r)
        except HTTPError as e: return e.code,json.load(e)
    _,sp=q("POST","/api/workspaces",{"name":"t","workbook_path":str(lib)}); w=sp["id"]; libro=tmp/"e"/w/"libro.xlsx"
    c={"FECHA":"20101228","PER":"2010-12","EMP":"FRE"}; OT="OT-FRENOSA-SW50-2010-12"; n=[0]
    def ex(t,u,h,l=()):
        n[0]+=1; s,r=q("POST",f"/api/workspaces/{w}/execute",{"transaction":t,"user":u,"request_id":f"x{n[0]}","header":h,"lines":list(l)}); res[t]=(s, r.get("error", ""))
        return s
    def ultimo(hoja):
        wb=load_workbook(libro,read_only=True); r=list(wb[hoja].values); wb.close(); return dict(zip(r[0],r[-1])) if len(r)>1 else {}
    ex("T18.2","SUPERV1",{**c,"CRIT":"KG_PRODUCIDOS","NIVEL":"OBJ"},[{"DEST":OT,"CANT":"10"}])
    ex("T18.3","SUPERV1",{**c,"OBJ":OT},[{"PERS":"OP01","MIN":"120"}])
    ex("T18.4","SUPERV1",{"FECHA":"20101228","CEN":"PLANTA_FRE","PRS":"OP01","OBJ":OT,"INI":"0800","FIN":"0900","CIN":"P1"})
    ex("T18.5","SUPERV1",{"FECHA":"20101228","PRS":"OP01","OBJ":OT,"MIN":"60","REC_PCT":"25","MOT":"CLIENTE"})
    ex("T18.6","SUPERV1",{"FECHA":"20101228","OBJ":OT,"REC":"MAT_SW50","CEN":"PLANTA_FRE","CAN_GEN":"2","CAN_REC":"0","CIN":"C1"})
    ex("T18.7","SUPERV1",{"FECHA":"20101228","OBJ":OT,"CAN":"5","CIN":"C1","REPROCESA":"N"})
    ex("T21","JCOSTOS",{**c,"PROV":"PRV1","TARDE":"1","RECH":"0","VARPRE":"0"})
    ex("T26","JCOSTOS",{**c,"CEN":"CA_MANT"},[{"DES":"PLANTA_FRE","CANT":"5"}])
    ex("T29.1","ALMACEN1",{**c,"ALM":"ALM_FRE"},[{"REC":"MAT_SW50","CANT":"100"}])
    ex("T20","COMERC1",{**c,"ALM":"ALM_FRE","CLI":"MERCADO","MON":"PEN"},[{"REC":"SW50","CANT":"2","PVU":"5"}]); ev=ultimo("EVENTO")["EVE_NUM"]
    ex("T20.1","COMERC1",{**c,"ALM":"ALM_FRE","EVE_ORI":ev,"CPB":"NC-1"},[{"REC":"SW50","CANT":"1"}])
    srv.shutdown(); srv.server_close()
    assert "T18.3" in sp["transactions"] and "T29.1" in sp["transactions"]
    fallas = {k: v for k, v in res.items() if v[0] != 200}
    assert not fallas, fallas
    assert set(res) >= {"T18.2", "T18.3", "T18.4", "T18.5", "T18.6", "T18.7", "T20.1", "T21", "T26", "T29.1"}
