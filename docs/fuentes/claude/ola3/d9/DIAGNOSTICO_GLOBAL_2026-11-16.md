# Deuda de diseño · Diagnóstico global (antes de pagar nada)

Fecha: 16-nov 04:40 UTC. Regla del dueño: mapa completo primero; después arreglos en paralelo por grupos que no se cruzan. Nada de esto entra a main sin visto bueno (cada arreglo que toca motor, estructura o cálculo).

## 1. Inventario [VERIFICADO en `fuente/DBD_Fuente.xlsx` y `informes/I0b/`]
| # | Deuda | Origen | Toca |
|---|---|---|---|
| D1 | UMBRAL → PARAMETRO | D-I0b-3 #1 | estructura + 5 servicios + 6 métodos (catálogo, dispersión, elemento, hallazgos, mensajes, autonomía) |
| D2 | DIARIO → LOG_TRX | D-I0b-3 #2 | estructura + servicios de registro |
| D3 | KARDEX y KARDEX_SALDO como derivadas de EXISTENCIA | D-I0b-3 #3 | clase de tabla + quien las escribe |
| D4 | CLIENTE y PROVEEDOR → ACTOR con rol | D-I0b-3 #4 | estructura + FK de VENTA/compras |
| D5 | TARIFA_CENTRO: predeterminada vs calculada | D-I0b-3 #5 | cálculo del cierre |
| D6 | OBJETO: avance a cuenta por periodo; costo real desde RESULTADO_METODO | D-I0b-3 #6 | cálculo |
| D7 | MOV_CIERRE como evento con líneas | D-I0b-3 #7 | motor del cierre |
| D8 | PLANILLA como evento, una línea por persona | D-I0b-3 #8 | motor |
| D9 | Cuentas CTA_* con un solo escritor + prueba de cuadre | D-I0b-1 | prueba (Obrera J, esta noche) |
| D10 | 62 tablas aún con alias «(sin MCD)» en DBD_4 | I-0b | metadatos (entidad), depende de MCD v3.2 |
| D11 | MCD v3.2 (P-1..P-7) con número E-### | D-I0b-2 | documento; habilita D10 |
| D12 | «La empresa gana al común» en PARAMETRO (comodín en la búsqueda) | I-5 (R-3) | motor (≈10 líneas VBA+espejo) |

## 2. Dependencias (quién bloquea a quién)
- **I-5 bloquea D1 y D12** (las tres tocan PARAMETRO/UMBRAL). Orden: I-5 → D12 → D1.
- D11 bloquea D10 (no se anota una entidad que el MCD aún no tiene).
- D4 se cruza con I-5 (CLIENTE y PROVEEDOR ya tienen empresa en la clave desde I-5): va después de I-5.
- D3, D9 son independientes. D5, D6, D7, D8 tocan el cálculo del cierre: uno por vez, con caso a mano.

## 3. Grupos que no se cruzan
| Grupo | Deudas | Riesgo | Cuándo |
|---|---|---|---|
| A · solo pruebas/documentos | D9 (cuadre), D11 (E-###), inventario D10 | ninguno (no cambia números) | **esta noche** (D9 Obrera J) |
| B · parámetros | D12 → D1 | bajo; necesita visto bueno (motor) | después de que I-5 entre a main |
| C · clase de tablas | D3, D2 | bajo-medio (quién escribe) | en paralelo a B |
| D · actores | D4 | medio (FK) | después de I-5 |
| E · cálculo del cierre | D5, D6, D7, D8 | alto (cambia cómo se calcula) | uno por incremento, con prueba del dueño en Excel; **después de la presentación** |

## 4. Para la presentación
«La deuda de diseño está inventariada (12 puntos), con dependencias y orden; lo que toca el cálculo no se cambia sin caso a mano y visto bueno. Nada se arregló a ciegas.»

## 5. Hallazgo de la noche (Obrera J, [VERIFICADO]) — cambia D9
Ninguna de las 7 cuentas cumple D-I0b-1: cada una tiene de 1 a 7 servicios escritores en línea (T15, T16, T17, T23.x…), y el cierre V4.1 publica RESULTADO_METODO sin escribir ninguna CTA_*. Por tanto D9 no es «una prueba»: es un **rediseño de quién escribe las cuentas** (grupo E, toca el cálculo). Queda con 14 pruebas xfail estrictas que lo describen; se decide después de la presentación. Detalle: `informes/DEUDA/escritores_cuentas.md`.

## 6. Hallazgo de la Obrera K (caso de 6 meses, [VERIFICADO]) — D13 rendimiento de la carga
La cadena de cálculo del mes tarda ~3.3 s, pero **la carga por el motor crece con el tamaño de las tablas**: 110 ms/línea en el mes 1 → 767 ms/línea en el mes 6 (5 → 34 min por mes en el espejo). Causa: cada búsqueda recorre la tabla completa. Correcciones probadas por K: tardío del mes 4 = S/ 932.45 a mano = sistema; puente DIF = 932.45; encadenamiento IFPP→IIPP dentro de 0.02; 0 errores en 15,846 eventos.
**D13:** índice por clave en Buscar/coincide (VBA y espejo, mismo resultado), con prueba de igualdad y medición antes/después. Prioridad alta antes de operar varios meses en Excel; para la demo de usuario se usa 1 mes.
