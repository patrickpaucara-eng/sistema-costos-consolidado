import sys,html; sys.path.insert(0,__import__('os').path.dirname(__import__('os').path.abspath(__file__)))
from spec import *
CORTO={'B0':'Parámetros y horizonte','B1':'Receptor de hechos','B2':'Lectura de costos','B3':'Estado del plan','B4':'Calculadora del plan','B5':'Caja y financiamiento','B6':'Catálogo de inversiones','B7':'Desviación y reprogramación','B8':'Estados y evaluación','B9':'Recomendación y aprendizaje'}
import validar as V
prod={}
for m in MODS:
    for o in m['out']: prod[o]=m['id']
dep={m['id']:set() for m in MODS}; edges=[]
for m in MODS:
    for i in m['inp']:
        p=prod.get(i)
        if p: edges.append((p,m['id'],i,(m['id'],i) in DELAYED))
        if p and (m['id'],i) not in DELAYED: dep[m['id']].add(p)
lvl={}
def L(u):
    if u in lvl: return lvl[u]
    lvl[u]=0 if not dep[u] else 1+max(L(v) for v in dep[u]); return lvl[u]
for u in dep: L(u)
cols={}
for m in MODS: cols.setdefault(lvl[m['id']],[]).append(m)
W,H=176,56; GX,GY=40,20
pos={}
nc=max(cols)+1; mx=max(len(v) for v in cols.values())
for c,ms in cols.items():
    for r,m in enumerate(ms): pos[m['id']]=(20+c*(W+GX),50+r*(H+GY)+ (mx-len(ms))*(H+GY)/2)
svgw=40+nc*(W+GX); svgh=70+mx*(H+GY)
ext_y={}
svg=[f'<svg viewBox="0 0 {svgw} {svgh+50}" role="img" aria-label="Flujo de datos de B"><defs><marker id="a" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto"><path d="M0,0L10,5L0,10z" fill="#8d95a3"/></marker></defs>']
for c in range(nc): svg.append(f'<text x="{20+c*(W+GX)}" y="26" class="s">PASO {c+1}</text>')
seen=set()
for a,b,i,d in edges:
    if a in ('B0','B2') or (a,b) in seen: continue
    seen.add((a,b)); xa,ya=pos[a]; xb,yb=pos[b]
    dl=any(x[0]==a and x[1]==b and x[3] for x in edges) and not any(x[0]==a and x[1]==b and not x[3] for x in edges)
    if xb>xa: x1,y1,x2,y2=xa+W,ya+H/2,xb,yb+H/2; mxp=(x1+x2)/2; p=f'M{x1} {y1} C{mxp} {y1} {mxp} {y2} {x2} {y2}'
    else: x1,y1,x2,y2=xa+W/2,ya+H,xb+W/2,yb+H; p=f'M{x1} {y1} C{x1} {svgh+30} {x2} {svgh+30} {x2} {y2}'
    svg.append(f'<path d="{p}" class="fl" {"stroke-dasharray=\"6 5\" stroke=\"#e0567a\"" if dl else ""} marker-end="url(#a)"/>')
col={'Definir':'#dceafb','Registrar':'#dceafb','(interno)':'#fff','Plan':'#ffe9b8','Caja':'#ffe9b8','Inversión':'#ffe9b8','Reportes':'#ffe9b8','Decidir':'#efe9fb'}
for m in MODS:
    x,y=pos[m['id']]; nm=html.escape(CORTO.get(m['id'],m['n'])); 
    if len(nm)>22: a=nm[:nm.rfind(" ",0,22)]; b=nm[len(a)+1:]
    else: a,b=nm,''
    svg.append(f'<g><rect x="{x}" y="{y}" width="{W}" height="{H}" rx="9" fill="{col[m["pantalla"]]}" stroke="#7d8796" stroke-width="1.6"/><text x="{x+8}" y="{y+19}" class="t">{m["id"]} · {a}</text><text x="{x+8}" y="{y+35}" class="t">{b}</text><text x="{x+8}" y="{y+48}" class="s">pantalla: {m["pantalla"]}</text></g>')
svg.append('</svg>')
import json
EV=[('📦','Pedido','OT'),('🚚','Llega material','COMPRA'),('🛑','Planta parada','OT'),('💵','Cobro / pago','FIN'),('⚠','Producto malo','OT'),('✎','Cambia un dato','—')]
TK=[('🏭','OT','OT',['propuesto','comprometido','en curso','terminado']),('🛒','Compra','COMPRA',['propuesto','comprometido','recibido']),('🏦','Financiamiento','FIN',['propuesto','tomado','pagado']),('🏗','Inversión','INV',['propuesto','aprobado','instalado','en uso'])]
RS=[('⏱','Horas ≤ capacidad'),('📦','Material ≤ stock'),('1️⃣','Una OT, un recurso'),('📅','Fecha de entrega'),('🔀','Secuencia'),('🕘','Ventanas'),('💵','Pagos ≤ caja'),('🛟','Caja mínima'),('🏗','Capacidad futura')]
PA=[('Horizonte n','12 meses'),('Periodo','semana'),('Multa por día tarde','1 % de la OT'),('Caja mínima','1 mes de fijos'),('Tasa de préstamo','1.5 % mes'),('Tasa de descuento','1.2 % mes'),('Umbral de desvío','10 %'),('Plazo proveedor','7 días'),('Calendario','L-S, 8 h'),('Impuesto renta','29.5 % (ley)')]
VC=['Todo dato tiene origen','Todo dato se usa','Un dato, un dueño','Sin círculos','Restricciones con datos','Eventos con ticket','Parámetros con vigencia','Caso inversión','Caso programación','Caso caja']
LIM=['Supuestos inventados','¿Rápido? sin medir','Falta enunciado Oria','¿Sistema o informe?']
data=dict(EV=EV,TK=TK,RS=RS,PA=PA,VC=[(t,o) for t,(o,_) in zip(VC,V.res)],LIM=LIM)
tpl=open(__import__('os').path.join(__import__('os').path.dirname(__file__),'vista.tpl'),encoding='utf-8').read()
out=tpl.replace('__FLUJO__',''.join(svg)).replace('__DATA__',json.dumps(data,ensure_ascii=False))
open('docs/diagramas/mapa-detalle-mn02.html','w',encoding='utf-8').write(out); print('ok')
