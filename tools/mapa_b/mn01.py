import json
# datos cortos (≤4 palabras) por módulo: entradas [texto, fuente], salidas, decisión, semáforo, hallazgos cortos
D=[('Pedido','#3b7dd8',[
 ('cotizador','Cotizar pedido',[('Qué, cuánto, cuándo','decision'),('Familia y medidas','decision'),('Capacidad libre','repite'),('Lote, flete, margen…','supuesto'),('Actividades a mano','tecnico'),('Tasas del mes','calc')],['Costo ± rango','Precio sugerido','Plazo','Orden nueva'],'Aceptar o no',['bad','ok','bad','warn','bad'],['37 campos','Pide lo que ya sabe','Tramos sin conectar']),
 ('costos','Órdenes',[('Resultado','calc')],['Costo por orden','Margen'],'Qué orden pierde',['ok','ok','ok','warn','warn'],[]),
 ('ruta','Ruta de la orden',[('Orden','decision'),('Trazas','calc')],['Hoja de costos','Ruta del sol'],'Qué la encarece',['ok','warn','ok','na','bad'],['Cifra no reproducible'])]),
('Operación','#7a5bd1',[
 ('operar','Registrar movimiento',[('Transacción','decision'),('Cabecera JSON','tecnico'),('Líneas JSON','tecnico')],['Hecho nuevo'],'—',['warn','ok','bad','na','bad'],['Escribir JSON','Duplicado']),
 ('importar','Importar libro',[('Ruta del archivo','tecnico')],['Espacio nuevo'],'—',['ok','na','warn','na','warn'],['Duplicado']),
 ('cierre','Cierre y aprobación',[('Usuario','decision')],['Sello del mes'],'Aprobar el mes',['ok','ok','ok','ok','warn'],[])]),
('Costos','#2f9e6a',[
 ('portada','Inicio',[],['Accesos'],'—',['na','na','warn','na','warn'],['Sobra']),
 ('dashboard','Planta del costo',[('Resultado','calc')],['Indicadores','Mapa del costo'],'¿Va bien el mes?',['ok','ok','ok','warn','ok'],[]),
 ('periodos','Periodos',[('Rango','decision'),('Síntesis','repite')],['Serie'],'Tendencia',['warn','na','ok','warn','warn'],['Repite síntesis']),
 ('reportes','Reportes',[('Resultado','calc')],['Excel','HTML','Word'],'—',['ok','na','ok','na','warn'],[]),
 ('inventarios','Inventarios y pérdidas',[('Resultado','calc')],['Inventario','Pérdida','Ocio'],'Cuánto es ineficiencia',['ok','ok','ok','warn','warn'],[]),
 ('normal','Costeo normal',[('Tarifas','libro'),('Real','calc')],['Sobre/subaplicación','Variaciones'],'¿Tasa correcta?',['ok','ok','ok','warn','warn'],['Moneda y devoluciones sin pedido'])]),
('Futuro','#e39b12',[
 ('proyeccion','Futuro',[('Mes','decision'),('Historia','libro')],['Costo proyectado','Precisión'],'Anticipar',['ok','ok','ok','warn','ok'],[]),
 ('laboratorio','Laboratorio',[('Hechos de prueba','decision')],['Diferencias'],'Probar antes',['ok','na','warn','warn','warn'],['Preliminar']),
 ('familias','Familias',[('Familia','decision')],['Receta'],'Cotizar parecido',['ok','warn','warn','warn','warn'],['Dos mecanismos']),
 ('comparar','Comparar síntesis',[('Resultado','calc')],['Real vs contable'],'Explicar diferencia',['ok','ok','ok','warn','warn'],[]),
 ('decidir','Decidir',[('Caso, precio','decision'),('¿Capacidad ociosa?','repite'),('Demanda ×1.5','supuesto'),('Margen','calc')],['Mejor opción','Mezcla óptima'],'Elegir opción',['bad','ok','warn','ok','warn'],['Pide lo que ya sabe','Supuesto inventado','Repite pedido']),
 ('propuestas','Propuestas',[('Variaciones','calc')],['Propuesta'],'Aprobar mejora',['ok','ok','ok','ok','warn'],[])]),
('Aprendizaje','#d14f8a',[
 ('aprendido','Lo que aprendió',[('Errores medidos','calc')],['Calibraciones'],'Cuánto confiar',['ok','na','ok','warn','warn'],[]),
 ('analisis','Relevancia',[('Resultado','calc')],['Lo que pesa'],'Dónde mirar',['ok','ok','ok','ok','warn'],[])]),
('Configuración','#8a8f98',[
 ('modelo','Modelo de costeo',[('Reglas','libro')],['Etapas'],'—',['ok','ok','ok','na','warn'],[]),
 ('datos','Datos del libro',[('Libro','libro')],['Suficiencia'],'—',['ok','ok','ok','na','warn'],[]),
 ('cargar','Cargar empresa',[('Archivo','decision')],['Empresa'],'—',['ok','ok','ok','na','ok'],[]),
 ('espacios','Espacios',[('Igual a registrar','tecnico')],['Hecho'],'—',['warn','na','bad','na','bad'],['Duplicado']),
 ('consultar','Consultar tablas',[('Tabla','decision')],['Filas'],'—',['ok','na','warn','na','warn'],[]),
 ('control','Calidad y cuadre',[('Trazas','calc')],['OK / diferencia'],'¿Confiable?',['ok','ok','ok','ok','warn'],[]),
 ('simulacion','Simulación',[('Resultado','calc')],['Escenarios'],'—',['na','na','bad','na','bad'],['Sin enlace'])])]
data=[dict(d=d,c=c,m=[dict(id=a,n=b,i=i,o=o,dec=e,s=s,h=h) for a,b,i,o,e,s,h in ms]) for d,c,ms in D]
html=open('tools/mapa_b/mn01.tpl',encoding='utf-8').read().replace('__DATA__',json.dumps(data,ensure_ascii=False))
open('docs/diagramas/mapa-detalle-mn01.html','w',encoding='utf-8').write(html)
print('ok')
