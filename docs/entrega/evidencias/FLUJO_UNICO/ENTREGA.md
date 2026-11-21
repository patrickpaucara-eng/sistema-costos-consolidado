# Flujo único: operar y costear el mismo libro (21-nov)
- **Plantilla única del DBD** (`casos/plantilla_dbd.xlsx`, D-6), construida por `tools/plantilla/construir_plantilla.py` a
  partir del modelo operativo (transacciones, usuarios, cierre) **sin datos de casos anteriores** (se verificó que no queda
  ningún dato del caso palta). Vocabulario de elementos del motor operativo (MAT, MOD, IND); el costeo lo traduce.
- **Adaptador Frenosa** escribe por nombre de columna (sirve para cualquier plantilla), completa claves de empresa (I-5),
  fecha de término de cada orden (R-80), lista de materiales (COMPONENTE: 1 kg por pieza), valuación ALG-PROM y existencias
  iniciales coherentes con el kardex. Cifras idénticas a las publicadas.
- **Espacio de operación = el mismo libro.** «Operar la empresa elegida» crea el espacio; el espacio aparece en «Empresa» y se
  costea tal como quedó después de sus transacciones.
- **Kardex derivado** (`src/reyna_local/flujo.py`): las transacciones del motor (T14, T15, T19, T20…) generan su movimiento de
  kardex según TRX_KARDEX; el costeo lo ve sin que nadie lo digite.
- **Merma en exceso**: el motor operativo separa al registrar el consumo lo que excede el estándar × unidades × (1 + merma
  normal). El costeo respeta esa separación: no entra a la orden y se presenta como pérdida anormal del periodo (NIC 2 §16 a),
  con su control de cuadre (salidas del kardex = material de las órdenes + pérdidas).
- Prueba: `tests/test_flujo_unico.py` (operar → consumo T15 de 1,000 kg en exceso → recalcular: la orden no cambia, la pérdida
  es S/ 3,605.84, el margen baja exactamente eso, el kardex muestra el movimiento). El humo del EXE ahora recorre este flujo.
