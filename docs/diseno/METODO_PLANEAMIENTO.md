# Sistema de planeamiento (B): cómo construirlo sin repetir los errores de costos

Estado: PROPUESTA (27-nov). No se construye antes del 9-dic. Presentación a Oria: 16-dic.

## 1. Qué es (definición del dueño, 27-nov)
Costos responde **si conviene** (casos de decisión de los apuntes). Planeamiento responde **cuándo y con qué**: compromete fechas y recursos, y absorbe lo que pasa en la realidad (el camión del proveedor que se cae, un proveedor nuevo cuya materia prima ahorra horas de máquina) para reordenar a cada área. Toma el costo ya calculado por el contrato publicado; no calcula costos. Horizonte corto (programación con fecha) y largo (presupuesto con valor del dinero en el tiempo). La meta es que su precisión supere a la del gerente; la autonomía se gana midiendo, no se declara.

## 2. Errores de costos que no se repiten (y la regla que los evita)
| Error en costos | Regla en planeamiento |
|---|---|
| Se programó antes de cerrar el modelo; se tocó la base muchas veces | Misión → eventos → banco de escenarios → DBD congelado → recién código. El DBD no cambia sin entrada en bitácora |
| «100 % funcional» con capacidades sin pantalla | Una capacidad está lista solo si se usa desde la pantalla con un caso a mano |
| El motor aceptaba claves repetidas; el usuario tecleaba códigos | Poka-yoke desde el día 1: el sistema asigna claves; el motor rechaza duplicados |
| Supuestos lineales y de pedido aislado descubiertos tarde | Cada método declara supuesto y límite en su ficha antes de construirse |
| Órdenes grandes que agotaban a Codex | Piezas de una sesión, casos a mano en la orden, una compuerta por rama |
| Hallazgos corregidos sobre la marcha | Recorrido completo, registro, corrección en lote |
| Mezclar entregas y fuentes | Fuente etiquetada: Reyna, Oria, Baldeón, propia |

## 3. El método, en términos de Tino (corregido 27-nov)
Corrección del dueño: «restricción, oportunidad, demanda, precio, dinero» NO son eventos. Para Tino, evento = transacción consumada (hecho que ocurrió, con condiciones, operaciones y secuencia; MCD libro, §3.4). Eso que se llamó «tipo de evento» es la **clasificación del efecto sobre el plan**, no el evento.

Modelo de planeamiento con las piezas de Tino:
- **Ticket = evento futuro con recursos comprometidos** (fecha, lote, operador, planta; TECNIA 2016, pp. 84-85). El plan es el conjunto de tickets; la capacidad es el saldo finito de tickets (cuenta control de existencias de tickets).
- **Evento ejecutado** = lo que de verdad ocurre y se registra: recepción de compra, pedido de cliente o su cancelación, parada de planta, cobro o falta de cobro, no conformidad, mantenimiento de maestro. Cada uno es una transacción del catálogo, con su TRX, condiciones y operaciones.
- **Desviación de oportunidad** = ticket programado contra evento ejecutado (§6.2.3.4). Que el camión no llegó no es un evento: es un ticket de recepción vencido sin evento ejecutado.
- **Reprogramación** = método disparado por esa desviación. Recalcula el plan desde el estado actual de las cuentas (no encadenando deltas), así el orden de aplicación deja de cambiar el resultado. Solo hay prioridad cuando dos tickets compiten por el mismo saldo; la regla es política del negocio («reservar mientras el disponible alcance»).
- **Clasificación del efecto** (capacidad, rendimiento, demanda, costo, caja): atributo de la regla de reprogramación, no entidad de evento. Útil para leer el plan, no para modelarlo.
- Una norma nueva (tasa de detracción) es **parámetro con vigencia**, no evento. Un error de capacidad cargada es una **transacción de mantenimiento** del maestro, que reprograma como cualquier otra.

## 4. Banco de escenarios antes del código (puerta G1)
Antes de construir, 15–20 escenarios escritos a mano con SERVITEC: situación → evento → plan antes → plan esperado después → número esperado. Ejemplo: «el proveedor de cobre no entrega 5 días» → restricción en cobre → la OT-0007 pasa del 12 al 17-ene, se avisa al cliente, caja de enero baja S/ X. Esos escenarios son las pruebas; el sistema está listo cuando los pasa todos.

## 5. Autonomía medida
Registro de decisión: recomendado / hecho / resultado. Precisión por tipo de decisión (mismo mecanismo que «precisión de la proyección» en costos). Bajo el umbral: solo recomienda. Sobre el umbral por N periodos: ejecuta y avisa. El umbral lo aprueba el dueño.

## 6. Mínimo para el 16-dic
Misión aprobada, eventos, DBD, banco de escenarios y un prototipo que reprograma 3 escenarios de punta a punta. Lo financiero (VAN, deuda, estados) entra en la versión de entrega final.
