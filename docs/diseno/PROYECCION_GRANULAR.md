# Proyección granular y sensibilidad (tarea 2.4) — diseño

Reemplaza el «¿y si?» que editaba el pasado (decisión del dueño 23-nov). El costo proyectado sale del **mismo motor ABC**
corriendo un mes futuro construido con hechos proyectados. No es un atajo estadístico sobre el total.

## Idea en una línea
Clonar el último mes cerrado → escalarlo con factores granulares (volumen por producto, precio por recurso, precio de venta) →
correr `reparto_etapas.interno` → el resultado sale por orden y por producto, con la misma ruta del costo.

## Factores (por mes proyectado h = 1..H)
| Factor | Serie histórica | Uso |
|---|---|---|
| `vol[p]` volumen del producto p | OBJ_CAN por mes y producto | escala consumos, medidas OBJ y ventas de p |
| `pre[r]` precio del recurso r | MD: costo promedio de salida del kardex por mes; otros: LIN_CUD medio por mes | escala el costo unitario de sus líneas |
| `pv[p]` precio de venta de p | VTA_ING / VTA_CAN por mes | escala el ingreso |

Factor = pronóstico del mes h / valor del mes base. Pronóstico: `analisis.pronostico_puntual(y, H)` (mismo proveedor PRONÓSTICO,
modelo elegido fuera de muestra; con poca historia, INGENUO = factor 1). Parámetro `factores` permite fijarlos a mano (pruebas, «qué pasa si»).

## Reglas de escalado (sobre una copia de los hechos; el libro nunca se toca)
- Comportamiento del recurso = `REC_COMPORT` / `REC_PCT_VAR` de C18. Sin dato: MD variable, el resto fijo.
- Línea con orden: cantidad × (1 − v + v·vol[p]); línea sin orden (centro): cantidad × (1 − v + v·g), con
  g = Σ costo base de p × vol[p] / Σ costo base de p. Costo unitario × pre[r]. (v = 1 variable, 0 fijo, pct/100 mixto.)
- Salidas de MD: la valuación (VALUACION_PROMEDIO) del clon = valuación base × factor de cantidad × pre[r]. La merma en exceso no se proyecta.
- MEDIDA: nivel OBJ × vol[p]; ACT/CEN con criterio que no es porcentaje × g; criterios de porcentaje y nivel CAP sin cambio.
- Ventas: cantidad × vol[p]; ingreso × vol[p] × pv[p].
- Reglas de reparto: las vigentes por fecha (DESDE), como siempre.

## Bloques (costo escalonado, decisión 24-nov)
Tabla opcional `BLOQUE` (BLQ_REC, BLQ_DESDE, BLQ_CAP, BLQ_COSTO, BLQ_UNI): se define una vez por recurso y cambia solo por hecho real (nueva fila con fecha).
En la proyección, si el recurso tiene bloque vigente: monto = ⌈requerido / BLQ_CAP⌉ × BLQ_COSTO, requerido = Σ medida OBJ proyectada del criterio BLQ_UNI.
El monto se reparte entre las líneas del recurso en proporción a su monto base. El costo real nunca usa bloques.

## Sensibilidad
Mes 1: cada factor +10 % y −10 % por separado (los demás en su pronóstico) → Δ margen total. Orden por |Δ| mayor. Bajo demanda (no en cada publicación).

## Salida (fuera de la serie del contrato)
`proyeccion.proyectar_granular(libro, emp, meses=6, factores=None)` → `{base, meses:[{periodo, factores, productos:[{producto, cantidad, costo_total, ingreso, margen, elementos}], total}], sensibilidad:[{factor, mas, menos}], bloques:[{recurso, requerido, bloques, monto}]}`. API `GET /api/proyeccion`.

## Caso a mano MINI (prueba obligatoria)
Mes base: material M 100 kg × 10 (A 60 kg, B 40 kg) · MOD 1,000 fijo por horas (A 30 h, B 20 h) · IND 500 fijo por unidades (A 60, B 40).
Factores: vol A 1.5, B 1; precios 1.
- MD A 900 · B 400. MOD A 1,000 × 45/65 = 692.31 · B 307.69. IND A 500 × 90/130 = 346.15 · B 153.85.
- **A 1,938.46 · B 861.54** (total 2,800).
- Con bloque MOD (25 h por operario, 500 por operario): requerido 65 h → 3 operarios = 1,500 → MOD A 1,038.46 · B 461.54.
- Identidad: todos los factores 1 → mismos costos por producto que el mes base (al céntimo).
