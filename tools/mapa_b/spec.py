# Especificación de B (MN 02). Todo valor marcado S es SUPUESTO declarado.
EXT = {  # lo que B lee de afuera
 'A.costo_actividad':'Costo por unidad de cada actividad (contrato publicado de costos)',
 'A.capacidad_practica':'Capacidad práctica por actividad y recurso (libro de costos)',
 'A.ordenes_abiertas':'Órdenes abiertas y su avance (libro de costos)',
 'A.precision':'Precisión medida de la proyección (costos)',
 'A.recetas':'Receta de familia: horas y material por unidad (costos, C34)',
 'N.hechos':'Hechos reales que llegan en el día (eventos)',
 'U.gerente':'Decisión del gerente (acepta o hace otra cosa)',
}
EVENTOS=[ # nombre, dato que trae, ticket que toca, qué recalcula
 ('Pedido entra o se cancela','cliente, producto, cantidad, fecha, precio','OT','agrega o quita la OT; recalcula programa y caja'),
 ('Llega material','proveedor, material, cantidad, fecha real','COMPRA','mueve el stock; libera OT que esperaban'),
 ('Se para / reinicia una planta','recurso, desde, hasta','OT','capacidad del recurso en esos días = 0; reprograma'),
 ('Se cobra o se paga','monto, fecha, cuenta','FINANCIAMIENTO','saldo de caja real; revisa caja mínima'),
 ('No conformidad','OT, cantidad mala','OT','reproceso: más horas y material en esa OT'),
 ('Cambia un dato maestro','capacidad, precio, tasa, plazo de proveedor','—','cierra el valor viejo y abre el nuevo con vigencia'),
]
# Cada línea de ticket (sea OT, compra, financiamiento o inversión) lleva SIEMPRE: recurso, cantidad, monto,
# fecha de devengo, fecha de caja, clase de concepto y estado (programado → comprometido → ejecutado).
# Con eso cualquier presupuesto es una SÍNTESIS (filtro + agrupación + reloj) definida como dato, no como código.
LINEA_TICKET=['recurso','cantidad','monto','fecha_devengo','fecha_caja','clase','estado','centro','titular']
CLASES=['INGRESO','EGRESO','INVERSION','FINANCIAMIENTO','APORTE','DIVIDENDO','IMPUESTO']
SINTESIS=[ # nombre, reloj, filtro de clases, agrupación  (catálogo editable: se pueden crear más sin programar)
 ('Presupuesto operativo','devengo',['INGRESO','EGRESO'],'centro y periodo'),
 ('Presupuesto de efectivo','caja','todas','periodo'),
 ('Presupuesto de inversiones','devengo',['INVERSION'],'proyecto y periodo'),
 ('Presupuesto financiero','caja',['FINANCIAMIENTO','APORTE','DIVIDENDO','IMPUESTO'],'periodo'),
 ('Control de ejecución','ambos','todas','línea: programado, comprometido, ejecutado, disponible'),
 ('Estados proyectados','devengo + caja','todas','cuenta'),
]
TICKETS=[
 ('OT (producir)','código, producto, cantidad, fecha entrega, recurso asignado, inicio, fin','propuesto → comprometido → en ejecución → terminado / cancelado'),
 ('COMPRA','material, cantidad, proveedor, fecha pedido, fecha llegada','propuesto → comprometido → recibido / cancelado'),
 ('FINANCIAMIENTO','monto, tasa efectiva del periodo, fecha toma, fecha pago','propuesto → tomado → pagado'),
 ('INVERSIÓN','activo, costo, fecha, capacidad que agrega, vida útil','propuesto → aprobado → instalado → en uso'),
]
# módulos de B: id, nombre, para qué, entradas (referencias), salidas (ids producidos)
MODS=[
 dict(id='B0',n='Parámetros y horizonte',para='Define cuántas unidades de tiempo mira el plan (n), el calendario y todos los parámetros con su vigencia.',
  inp=['U.gerente'],out=['P.horizonte','P.parametros'],pantalla='Definir'),
 dict(id='B1',n='Receptor de hechos',para='Recibe cada hecho real, lo valida y decide qué ticket toca.',
  inp=['N.hechos','P.parametros'],out=['H.hechos_validos'],pantalla='Registrar'),
 dict(id='B2',n='Lectura de costos',para='Lee del sistema de costos lo que el plan necesita; no copia ni recalcula.',
  inp=['A.costo_actividad','A.capacidad_practica','A.ordenes_abiertas','A.recetas','A.precision'],out=['C.costos','C.capacidad','C.carga','C.recetas'],pantalla='(interno)'),
 dict(id='B3',n='Estado del plan',para='Guarda los tickets y su estado actual: lo comprometido, lo ejecutado y lo pendiente.',
  inp=['H.hechos_validos','C.carga','X.plan'],out=['T.tickets','T.estado'],pantalla='Plan'),
 dict(id='B4',n='Calculadora del plan (investigación de operaciones)',para='Elige qué hacer, en qué recurso y cuándo, para maximizar la ganancia descontada respetando todas las restricciones.',
  inp=['T.estado','C.costos','C.capacidad','C.recetas','P.horizonte','P.parametros','F.caja_real','V.inversiones'],out=['X.plan','X.caja_plan','X.tardanzas'],pantalla='Plan'),
 dict(id='B5',n='Caja y financiamiento',para='Proyecta el saldo de caja día a día, exige la caja mínima y decide cuánto financiamiento tomar.',
  inp=['X.plan','H.hechos_validos','P.parametros'],out=['F.caja_real','F.flujo','F.deuda'],pantalla='Caja'),
 dict(id='B6',n='Catálogo de inversiones',para='Guarda cada inversión posible (costo, fecha, capacidad que agrega, vida útil) como opción para la calculadora; la calculadora decide si se compra.',
  inp=['P.parametros','C.costos'],out=['V.inversiones'],pantalla='Inversión'),
 dict(id='B7',n='Desviación y reprogramación',para='Compara lo programado con lo ejecutado; si se aleja más que el umbral, dispara un nuevo cálculo desde el estado de hoy.',
  inp=['T.estado','H.hechos_validos','P.parametros'],out=['D.desviacion','D.disparo'],pantalla='Plan'),
 dict(id='B8',n='Síntesis y evaluación',para='Genera cualquier presupuesto como síntesis del plan (catálogo SINTESIS: filtro de clases + agrupación + reloj devengo o caja), los estados proyectados y VAN, TIR y recuperación.',
  inp=['X.plan','F.flujo','F.deuda','C.costos','V.inversiones','P.parametros'],out=['E.estados','E.evaluacion'],pantalla='Reportes'),
 dict(id='B9',n='Recomendación y aprendizaje',para='Entrega la programación al gerente, registra qué decidió y mide cuánto acierta el sistema para ganar autonomía.',
  inp=['X.plan','T.tickets','D.desviacion','E.estados','U.gerente','A.precision'],out=['R.programa','R.aprendizaje'],pantalla='Decidir'),
]
# restricciones de la calculadora: id, texto, datos que necesita, parámetro
RESTR=[
 ('R1','Tiempo: horas usadas en cada recurso y periodo ≤ capacidad del recurso en ese periodo. Horas = horas por unidad × cantidad producida.',['C.capacidad','C.recetas'],'P.parametros'),
 ('R2','Materiales: lo consumido en un periodo ≤ stock inicial + lo que llega.',['T.estado','C.recetas'],'P.parametros'),
 ('R3','Asignación: cada OT se programa en un recurso por vez.',['T.estado'],None),
 ('R4','Fecha de entrega: tardanza = máx(0, fin − fecha comprometida).',['T.estado'],'P.parametros'),
 ('R5','Secuencia: una OT no puede ir después de otra incompatible (p. ej. pigmento negro).',['C.recetas'],'P.parametros'),
 ('R6','Ventanas: el proveedor entrega solo ciertos días; la planta o la luz no están ciertas horas.',['T.estado'],'P.parametros'),
 ('R7','Caja: lo que se paga en un periodo ≤ caja disponible + financiamiento tomado.',['F.caja_real'],'P.parametros'),
 ('R8','Caja mínima: el saldo de caja nunca baja del mínimo; si baja, se toma financiamiento.',['F.caja_real'],'P.parametros'),
 ('R9','Capacidad futura: si se compra un activo, la capacidad sube desde su fecha de instalación.',['V.inversiones'],None),
]
PARAMS=[ # nombre, unidad, valor inicial SUPUESTO, quién lo ajusta, regla de cierre
 ('Horizonte n','periodos',"12 meses (S)",'Gerente','Se cambia por decisión; no caduca'),
 ('Periodo base del plan','—',"semana (S); granular en días cercanos",'Gerente','Idem'),
 ('Penalización por tardanza','S/ por día y OT',"1 % del precio de la OT por día (S)",'Se ajusta con el costo real de las entregas tardías','Se cierra cuando el error medido supera 20 % durante 3 cierres'),
 ('Caja mínima','S/',"un mes de costos fijos (S)",'Gerente / finanzas','Se cierra al cambiar la política de liquidez'),
 ('Tasa efectiva de financiamiento','% por periodo',"1.5 % mensual (S)",'Cada contrato real con su banco','Se cierra al vencer la línea o cambiar la tasa'),
 ('Tasa de descuento (CPPC)','% por periodo',"1.2 % mensual (S)",'Finanzas','Se recalcula con estructura de capital real'),
 ('Umbral de desviación','% sobre lo programado',"10 % (S)",'Aprendizaje','Se ajusta para no reprogramar de más'),
 ('Plazo de proveedor','días',"7 días (S)",'Compras (hecho de recepción)','Se reemplaza con el promedio medido'),
 ('Calendario de planta','días y horas hábiles',"lunes a sábado, 8 h (S)",'Producción','Se cierra al cambiar turnos'),
 ('Impuesto a la renta','%',"29.5 % (vigencia legal)",'Finanzas (norma)','Cierra con la norma'),
]
SALIDAS=['R.programa','R.aprendizaje','E.estados','E.evaluacion','F.deuda','D.disparo','X.caja_plan','X.tardanzas']
DELAYED={('B3','X.plan'),('B4','F.caja_real')}
