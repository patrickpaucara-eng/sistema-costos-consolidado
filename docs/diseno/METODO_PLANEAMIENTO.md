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

## 3. El método: cada situación de la realidad es un EVENTO
Las «innumerables situaciones» no se programan una por una. Se reducen a pocos tipos de evento que cambian el plan de forma conocida:
| Tipo | Ejemplo | Qué cambia en el plan |
|---|---|---|
| Restricción nueva | se cayó el camión del proveedor; máquina parada | capacidad o disponibilidad de un recurso en unas fechas |
| Oportunidad | proveedor con mejor materia prima | tasa o rendimiento de un recurso (menos horas por unidad) |
| Demanda | pedido nuevo, cancelación, descuento | lo que hay que producir y cuándo |
| Precio | sube el insumo, cambia el tipo de cambio | costo esperado (se relee de costos) |
| Dinero | cliente no paga, crédito aprobado | caja y financiamiento |
Con cada evento el sistema **reprograma** (horizonte rodante): recalcula fechas, recursos comprometidos y caja, y emite a cada área su orden y a quien decide su recomendación con fundamento.

## 4. Banco de escenarios antes del código (puerta G1)
Antes de construir, 15–20 escenarios escritos a mano con SERVITEC: situación → evento → plan antes → plan esperado después → número esperado. Ejemplo: «el proveedor de cobre no entrega 5 días» → restricción en cobre → la OT-0007 pasa del 12 al 17-ene, se avisa al cliente, caja de enero baja S/ X. Esos escenarios son las pruebas; el sistema está listo cuando los pasa todos.

## 5. Autonomía medida
Registro de decisión: recomendado / hecho / resultado. Precisión por tipo de decisión (mismo mecanismo que «precisión de la proyección» en costos). Bajo el umbral: solo recomienda. Sobre el umbral por N periodos: ejecuta y avisa. El umbral lo aprueba el dueño.

## 6. Mínimo para el 16-dic
Misión aprobada, eventos, DBD, banco de escenarios y un prototipo que reprograma 3 escenarios de punta a punta. Lo financiero (VAN, deuda, estados) entra en la versión de entrega final.
