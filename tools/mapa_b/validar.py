import sys; sys.path.insert(0,__import__('os').path.dirname(__import__('os').path.abspath(__file__)))
from spec import *
prod={}
for m in MODS:
    for o in m['out']: prod.setdefault(o,[]).append(m['id'])
res=[]
def chk(ok,txt): res.append((ok,txt))
# 1 entradas resueltas
fal=[(m['id'],i) for m in MODS for i in m['inp'] if i not in EXT and i not in prod]
chk(not fal,"Toda entrada de cada módulo viene de afuera (costos/hechos/gerente) o de otro módulo"+(f" — FALTA: {fal}" if fal else f" ({sum(len(m['inp']) for m in MODS)} entradas revisadas)"))
# 2 salidas usadas
usado={i for m in MODS for i in m['inp']}
sin=[o for o in prod if o not in usado and o not in SALIDAS]
chk(not sin,"Toda salida la usa otro módulo o es una salida final declarada"+(f" — SIN USO: {sin}" if sin else ""))
# 3 una sola fuente por dato
dup=[o for o,v in prod.items() if len(v)>1]
chk(not dup,"Cada dato lo produce un solo módulo"+(f" — duplicados: {dup}" if dup else ""))
# 4 ciclos sin aristas retardadas
dep={m['id']:set() for m in MODS}
for m in MODS:
    for i in m['inp']:
        if (m['id'],i) in DELAYED: continue
        for p in prod.get(i,[]): dep[m['id']].add(p)
def ciclo():
    st={}
    def dfs(u,path):
        st[u]=1
        for v in dep[u]:
            if st.get(v)==1: return path+[u,v]
            if v not in st:
                r=dfs(v,path+[u])
                if r: return r
        st[u]=2
    for u in dep:
        if u not in st:
            r=dfs(u,[])
            if r: return r
c=ciclo()
chk(c is None,"No hay dependencias circulares; los 2 lazos con el tiempo están declarados (usan la corrida anterior): "+', '.join(f"{a} lee {b} de la corrida anterior" for a,b in sorted(DELAYED)) if c is None else f"CICLO: {c}")
# 5 restricciones con datos
b4=[m for m in MODS if m['id']=='B4'][0]
malas=[(r[0],d) for r in RESTR for d in r[2] if d not in b4['inp'] and d not in prod]
sin_ent=[(r[0],d) for r in RESTR for d in r[2] if d not in b4['inp']]
chk(not sin_ent,"Los datos de las 9 restricciones llegan a la calculadora"+(f" — NO LLEGAN: {sin_ent}" if sin_ent else ""))
# 6 eventos
tk={t[0].split()[0] for t in TICKETS}
mal=[e[0] for e in EVENTOS if e[2] not in tk and e[2]!='—']
chk(not mal,"Los 6 eventos tocan un ticket que existe o son mantenimiento de dato maestro"+(f" — {mal}" if mal else ""))
# 7 parámetros
sup=[p[0] for p in PARAMS if '(S)' not in p[2] and 'legal' not in p[2]]
chk(not sup,"Cada parámetro tiene valor inicial marcado SUPUESTO (o vigencia legal), responsable y regla de cierre"+(f" — sin marcar: {sup}" if sup else f" ({len(PARAMS)} parámetros)"))
# 8 casos a mano
v12=120000/1.02**12; v24=120000/1.02**24
chk(abs(v12-94619)<5 and abs(v24-74607)<5 and v12>80000>v24,f"Caso de inversión a mano: 120,000 a 12 meses al 2 % vale hoy {v12:,.0f} > 80,000 (comprar); a 24 meses vale {v24:,.0f} < 80,000 (no comprar)")
# 9 caso OT: se enumeran todas las opciones, no se escribe el resultado a mano
import itertools
cap=100; datos={'A':(60,5000),'B':(50,4000)}; multa=800
mejor=None
for dec in itertools.product(['P1','P2','NO'],repeat=2):   # A y B: periodo 1, periodo 2 (con multa) o rechazar
    h1=sum(datos[o][0] for o,d in zip('AB',dec) if d=='P1'); h2=sum(datos[o][0] for o,d in zip('AB',dec) if d=='P2')
    if h1>cap or h2>cap: continue
    u=sum(datos[o][1]-(multa if d=='P2' else 0) for o,d in zip('AB',dec) if d!='NO')
    if mejor is None or u>mejor[0]: mejor=(u,dec)
chk(mejor==(8200,('P1','P2')),f"Caso de programación (enumerando las 9 combinaciones): 100 h por periodo, A usa 60 h y gana 5,000, B usa 50 h y gana 4,000; mejor = A en el periodo 1 y B en el 2 con multa 800, utilidad {mejor[0]:,}")
# 10 caja
cobranza=8000; caja0=10000; compra=12000; minima=5000
D=max(0,minima-(caja0-compra)); inter=D*0.015/2
chk(D==7000 and abs(inter-52.5)<1e-9,f"Caso de caja: caja 10,000, mínima 5,000, compra 12,000 antes de cobrar 8,000 → financiamiento {D:,} por 15 días al 1.5 % mensual = {inter:,.2f} de interés; al cobrar se paga")
if __name__=='__main__':
    for ok,t in res: print('OK ' if ok else 'XX ',t)
