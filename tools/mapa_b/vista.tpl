<!DOCTYPE html><html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Mapa visual · Sistema de planeamiento (MN 02) — SUPUESTOS</title>
<style>body{margin:0;background:#f7f6f2;color:#1d2433;font:14px/1.3 "Segoe UI",system-ui,sans-serif}.w{max-width:1200px;margin:0 auto;padding:14px}
h1{font-size:20px;margin:2px 0 4px}h2{font-size:15px;margin:22px 0 6px;color:#5b6474;letter-spacing:.5px}.sello{background:#e0567a;color:#fff;font-size:11px;font-weight:700;padding:2px 8px;border-radius:10px;vertical-align:middle}
svg{width:100%;height:auto;display:block;overflow:visible}svg text{font-family:"Segoe UI",system-ui,sans-serif;fill:#1d2433}.t{font-size:13px;font-weight:650}.s{font-size:11.5px;fill:#5b6474}.fl{fill:none;stroke:#8d95a3;stroke-width:2}
.mis{background:#fff;border-left:6px solid #7a5bd1;border-radius:8px;padding:8px 12px;font-size:15px;margin:6px 0}</style></head><body><div class="w">
<h1>Sistema de planeamiento · mapa visual (MN 02) <span class="sello">SUPUESTOS</span></h1>
<div class="mis">🎯 Entregar la <b>programación de los recursos comprometidos</b> para cumplir los objetivos · ⚡ tiempo real · 🔭 n periodos</div>
<h2>① CÓMO FLUYEN LOS DATOS</h2>__FLUJO__
<h2>② LO QUE PASA → LO QUE SE PLANEA</h2><svg viewBox="0 0 1200 350"><g id="ev"></g></svg>
<h2>③ LA CALCULADORA</h2><svg viewBox="0 0 1200 400"><g id="calc"></g></svg>
<h2>④ PARÁMETROS: NACEN SUPUESTOS, SE VAN MIDIENDO</h2><svg viewBox="0 0 1200 230"><g id="par"></g></svg>
<h2>⑤ VALIDACIÓN</h2><svg viewBox="0 0 1200 200"><g id="val"></g></svg>
</div><script>
const D=__DATA__,NS='http://www.w3.org/2000/svg';
const el=(p,t,a,x)=>{const e=document.createElementNS(NS,t);for(const k in a)e.setAttribute(k,a[k]);if(x!=null)e.textContent=x;p.appendChild(e);return e};
const def=el(document.querySelector('#ev').ownerSVGElement,'defs',{});const mk=el(def,'marker',{id:'b',viewBox:'0 0 10 10',refX:8,refY:5,markerWidth:7,markerHeight:7,orient:'auto'});el(mk,'path',{d:'M0,0L10,5L0,10z',fill:'#8d95a3'});
// eventos y tickets
const E=document.getElementById('ev');const ty={};
D.TK.forEach(([ic,n,k,st],i)=>{const y=20+i*78;ty[k]=y+26;el(E,'rect',{x:430,y,width:180,height:52,rx:12,fill:'#ffe9b8',stroke:'#c07a00','stroke-width':2});el(E,'text',{x:450,y:y+34,'font-size':22},ic);el(E,'text',{x:485,y:y+32,'font-size':15,'font-weight':700},n);
 st.forEach((s,j)=>{const x=670+j*140;el(E,'circle',{cx:x,cy:y+26,r:9,fill:j==st.length-1?'#2f9e6a':'#fff',stroke:'#7d8796','stroke-width':2});el(E,'text',{x,y:y+50,'text-anchor':'middle','font-size':12,fill:'#5b6474'},s);if(j<st.length-1)el(E,'path',{d:`M${x+11} ${y+26}H${x+127}`,stroke:'#c9ced6','stroke-width':2,'marker-end':'url(#b)'});});
 el(E,'path',{d:`M610 ${y+26}H656`,stroke:'#c9ced6','stroke-width':2});});
D.EV.forEach(([ic,n,k],i)=>{const y=12+i*52;el(E,'rect',{x:10,y,width:220,height:40,rx:20,fill:'#dceafb',stroke:'#5b86c4','stroke-width':1.5});el(E,'text',{x:28,y:y+27,'font-size':18},ic);el(E,'text',{x:58,y:y+26,'font-size':14,'font-weight':600},n);
 const ty2=k==='—'?332:ty[k];el(E,'path',{d:`M230 ${y+20}C330 ${y+20} 330 ${ty2} 428 ${ty2}`,fill:'none',stroke:k==='—'?'#e0567a':'#8d95a3','stroke-width':1.8,'stroke-dasharray':k==='—'?'5 4':'', 'marker-end':'url(#b)'});});
el(E,'text',{x:436,y:337,'font-size':12.5,fill:'#e0567a'},'✎ cambia un dato → cierra el valor viejo, abre el nuevo');
el(E,'text',{x:850,y:337,'font-size':12,fill:'#5b6474'},'azul = ya ocurrió (evento) · amarillo = futuro comprometido (ticket)');
// calculadora
const C=document.getElementById('calc');const cx=600,cy=200;
D.RS.forEach(([ic,n],i)=>{const a=-Math.PI/2+i*2*Math.PI/D.RS.length,x=cx+330*Math.cos(a),y=cy+160*Math.sin(a);el(C,'path',{d:`M${cx} ${cy}L${x} ${y}`,stroke:'#c9ced6','stroke-width':2});el(C,'rect',{x:x-95,y:y-20,width:190,height:40,rx:20,fill:'#fff',stroke:'#7d8796'});el(C,'text',{x:x-80,y:y+7,'font-size':17},ic);el(C,'text',{x:x-52,y:y+6,'font-size':13.5,'font-weight':600},n);});
el(C,'circle',{cx,cy,r:92,fill:'#ffe9b8',stroke:'#c07a00','stroke-width':3});
[['MAXIMIZAR',-30,13,'#c07a00'],['ingresos',-6,14],['− costos − multas',14,14],['− intereses',34,14],['(descontado a hoy)',56,11.5,'#5b6474']].forEach(([t,dy,fs,c])=>el(C,'text',{x:cx,y:cy+dy,'text-anchor':'middle','font-size':fs,'font-weight':dy<0?800:500,fill:c||'#1d2433'},t));
[['Decide',40,'#5b6474'],['🏭 cuánto y dónde',62],['🏦 cuánto prestar',84],['🏗 qué comprar',106]].forEach(([t,y,c])=>el(C,'text',{x:20,y,'font-size':13.5,fill:c||'#1d2433','font-weight':c?700:500},t));
[['Lee de costos',40,'#5b6474'],['💲 costo por actividad',62],['⏱ capacidad',84],['📋 receta',106]].forEach(([t,y,c])=>el(C,'text',{x:1180,y,'text-anchor':'end','font-size':13.5,fill:c||'#1d2433','font-weight':c?700:500},t));
// parámetros
const P=document.getElementById('par');D.PA.forEach(([n,v],i)=>{const x=10+(i%5)*238,y=10+Math.floor(i/5)*110;const ley=v.includes('ley');
 el(P,'rect',{x,y,width:222,height:96,rx:12,fill:'#fff',stroke:ley?'#2f9e6a':'#e39b12','stroke-width':2,'stroke-dasharray':ley?'':'6 4'});el(P,'text',{x:x+14,y:y+26,'font-size':13.5,'font-weight':700},n);
 el(P,'rect',{x:x+14,y:y+42,width:120,height:28,rx:14,fill:ley?'#dff3e9':'#fff3dc'});el(P,'text',{x:x+74,y:y+61,'text-anchor':'middle','font-size':13},v);
 if(!ley){el(P,'path',{d:`M${x+140} ${y+56}H${x+168}`,stroke:'#8d95a3','stroke-width':2,'marker-end':'url(#b)'});el(P,'text',{x:x+196,y:y+62,'text-anchor':'middle','font-size':18},'📏');el(P,'text',{x:x+14,y:y+88,'font-size':11,fill:'#5b6474'},'supuesto → medido');}else el(P,'text',{x:x+14,y:y+88,'font-size':11,fill:'#5b6474'},'dato legal');});
// validación
const V=document.getElementById('val');D.VC.forEach(([t,o],i)=>{const x=10+(i%5)*238,y=8+Math.floor(i/5)*54;el(V,'circle',{cx:x+18,cy:y+20,r:15,fill:o?'#2f9e6a':'#d6453d'});el(V,'text',{x:x+18,y:y+26,'text-anchor':'middle',fill:'#fff','font-size':16,'font-weight':800},o?'✔':'✘');el(V,'text',{x:x+42,y:y+25,'font-size':13.5},t);});
D.LIM.forEach((t,i)=>{const x=10+i*296,y=128;el(V,'rect',{x,y,width:282,height:40,rx:20,fill:'#fff',stroke:'#e0567a','stroke-dasharray':'6 4','stroke-width':2});el(V,'text',{x:x+20,y:y+26,'font-size':13.5,fill:'#a32117','font-weight':600},'? '+t);});
el(V,'text',{x:10,y:190,'font-size':12,fill:'#5b6474'},'verde = probado sobre la especificación · rojo punteado = lo que la prueba no puede asegurar');
</script></body></html>
