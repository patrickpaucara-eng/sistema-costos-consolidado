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
def tbl(h,rows): return '<table><tr>'+''.join(f'<th>{x}</th>' for x in h)+'</tr>'+''.join('<tr>'+''.join(f'<td>{html.escape(str(c))}</td>' for c in r)+'</tr>' for r in rows)+'</table>'
mods=''.join(f'<details><summary><b>{m["id"]} · {html.escape(m["n"])}</b> — {html.escape(m["para"])}</summary><p><b>Entra:</b> '+'; '.join(html.escape(i+(" = "+EXT[i] if i in EXT else "")) for i in m['inp'])+f'</p><p><b>Sale:</b> '+', '.join(m['out'])+'</p></details>' for m in MODS)
ok=sum(1 for o,_ in V.res if o)
val=''.join(f'<li class="{"ok" if o else "bad"}">{"✔" if o else "✘"} {html.escape(t)}</li>' for o,t in V.res)
out=f'''<!DOCTYPE html><html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>Mapa a detalle del sistema de planeamiento (MN 02) — SUPUESTOS</title>
<style>
:root{{--papel:#f7f6f2;--tinta:#1d2433;--suave:#5b6474;--linea:#c9ced6}}
*{{box-sizing:border-box}}body{{margin:0;background:var(--papel);color:var(--tinta);font:15px/1.4 "Segoe UI",system-ui,sans-serif}}.w{{max-width:1240px;margin:0 auto;padding:16px}}
h1{{font-size:22px;margin:4px 0}}h2{{font-size:17px;margin:26px 0 6px}}p.n{{color:var(--suave);margin:4px 0 10px}}svg{{width:100%;height:auto;display:block;overflow:visible}}svg text{{font-family:"Segoe UI",system-ui,sans-serif;fill:var(--tinta)}}.t{{font-size:13px;font-weight:650}}.s{{font-size:11.5px;fill:var(--suave)}}.fl{{fill:none;stroke:#8d95a3;stroke-width:2}}
.sello{{background:#e0567a;color:#fff;font-size:11px;font-weight:700;padding:2px 8px;border-radius:10px;margin-left:8px;vertical-align:middle}}
table{{border-collapse:collapse;font-size:13px;background:#fff;width:100%;margin:6px 0}}td,th{{border:1px solid var(--linea);padding:4px 8px;text-align:left;vertical-align:top}}th{{background:#eef1f5}}
details{{background:#fff;border:1px solid var(--linea);border-radius:8px;padding:6px 10px;margin:5px 0}}summary{{cursor:pointer}}
.val li{{list-style:none;margin:4px 0;padding:5px 9px;border-radius:7px;background:#e8f5ee}}.val li.bad{{background:#fbe3e0}}.val{{padding:0}}
.cajas{{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:10px}}.cajas div{{background:#fff;border:1px solid var(--linea);border-radius:10px;padding:9px 11px;font-size:13.5px}}
.punt{{border:1.5px dashed #e0567a !important}}.leg{{font-size:12.5px;color:var(--suave)}}
</style></head><body><div class="w">
<h1>Mapa a detalle del sistema de planeamiento (MN 02)<span class="sello">SUPUESTOS — sin enunciado oficial de Oria</span></h1>
<p class="n">Misión propuesta: <b>entregar la programación de realización de los recursos comprometidos para el cumplimiento de los objetivos</b>. Se actualiza en tiempo real, con cada hecho que ocurre. Mira n periodos hacia adelante. La calculadora usa investigación de operaciones. Los parámetros arrancan como supuestos y se ajustan con la experiencia.</p>
<h2>1 · Cómo fluyen los datos entre los módulos de B</h2>
<p class="n">Cada flecha es un dato que pasa de un módulo a otro. Línea punteada roja = ese módulo usa lo que dejó la corrida anterior (así el plan puede corregirse sin dar vueltas en círculo).</p>
{''.join(svg)}
<p class="leg"><b>No se dibujan para no enredar:</b> B0 (parámetros) alimenta a todos los demás módulos, y B2 (costos) alimenta a B4, B6 y B8. Azul: entra o se define · Amarillo: cálculo y plan · Violeta: lo que ve el gerente · Blanco: interno. Los datos de costos entran por B2 (solo se leen).</p>
<h2>2 · Qué entra de afuera</h2>{tbl(['Dato','De dónde'],list(EXT.items()))}
<h2>3 · Los 6 eventos reales (transacciones consumadas)</h2><p class="n">Según Tino, un evento es algo que ya ocurrió. El plan es un conjunto de tickets (eventos futuros con recursos comprometidos). Restricción, oportunidad o urgencia no son eventos: son efectos de un evento sobre el plan.</p>
{tbl(['Evento','Qué dato trae','Ticket que toca','Qué recalcula'],EVENTOS)}
<h2>4 · Los 4 tipos de ticket</h2>{tbl(['Ticket','Campos','Estados'],TICKETS)}
<h2>5 · Qué hace la calculadora</h2>
<p class="n"><b>Decide:</b> cuánto producir de cada OT (X), en qué recurso y periodo (Y), cuánto financiamiento tomar (D) y qué inversión comprar (I). <b>Objetivo: maximizar</b> ingresos − costos − multas por tardanza − intereses, todo descontado a hoy. (Si se minimizara el costo, la mejor respuesta sería no producir.) El costo de cada actividad lo lee de costos.</p>
{tbl(['#','Restricción','Datos que necesita','Parámetro'],[(r[0],r[1],', '.join(r[2]),r[3] or '—') for r in RESTR])}
<p class="n">Corrección frente a la propuesta de Meta AI: Meta omitió R4, R5, R6 y escribió el tiempo sin multiplicar por la cantidad. Aquí van completas.</p>
<h2>6 · Parámetros (todos nacen como supuesto y se van cerrando)</h2>{tbl(['Parámetro','Unidad','Valor inicial','Quién lo ajusta','Cuándo se cierra el valor viejo'],PARAMS)}
<p class="n">«Cerrar» significa poner fecha de fin de vigencia y abrir el valor nuevo; nunca se borra. Así se sabe qué valor se usó en cada cálculo.</p>
<h2>7 · Detalle de cada módulo</h2>{mods}
<h2>8 · Validación ({ok} de {len(V.res)} pruebas en verde)</h2>
<p class="n">Se ejecutó sobre esta misma especificación antes de generar la página; los casos se calculan, no se escriben a mano.</p><ul class="val">{val}</ul>
<h2>9 · Lo que esta validación NO prueba</h2>
<div class="cajas">
<div class="punt"><b>Que los supuestos sean reales.</b> Penalización, caja mínima, tasas, n y calendario son inventados para poder calcular; deben reemplazarse con datos de una empresa.</div>
<div class="punt"><b>Que el modelo se resuelva rápido.</b> Con binarios y 50 OT puede ser lento. Hace falta un solucionador entero (hoy solo exportamos a Solver) y medir.</div>
<div class="punt"><b>Que coincida con Oria.</b> Se tomó del sílabo (semanas 13 a 15: presupuesto maestro, basado en actividades, financiero con CPPC, VAN, TIR y estados proyectados). Falta el enunciado oficial.</div>
<div class="punt"><b>Que sea el sistema que pide el curso.</b> No sabemos si la MN 02 exige un sistema o un informe; se pregunta a Oria el 16-dic.</div>
</div></div></body></html>'''
open('docs/diagramas/mapa-detalle-mn02.html','w',encoding='utf-8').write(out); print('ok',len(out),'niveles',nc)
