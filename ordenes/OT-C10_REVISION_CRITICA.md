# OT-C10 · Revisión crítica independiente (Codex · alto) — SOLO LECTURA Y PRUEBA
Rama `codex/ot-c10` desde `desarrollo/mono` (≥ `976eeac`). PR contra `desarrollo/mono` con UN archivo:
`docs/entrega/evidencias/OT-C10/REVISION.md`. **No modificar código, datos ni pruebas.** No unir.

Objetivo: que un revisor que no construyó el cálculo intente romperlo. Cada hallazgo con: qué probaste, qué esperabas,
qué obtuviste, archivo/línea y gravedad (BLOQUEA ENTREGA / CORREGIR / MENOR). Si algo está bien, dilo en una línea.

## A. Costos que cuadran (julio y diciembre 2010, REAL)
1. Recalcula a mano o con un script propio (sin importar `src/metodos` ni `resultados.py`) el MD de cada orden desde la hoja
   KARDEX de `casos/libros/frenosa.xlsx` con promedio ponderado móvil. Compara con `datos/resultados/frenosa_2010-07_REAL.json`.
2. Verifica que Σ costo de las órdenes = Σ recursos del periodo (hoja LINEA del periodo). Usa el panel `control` solo para comparar.
3. Toma 2 tramos de `trazas` (uno P4A y uno P4C) y recalcúlalos con MEDIDA: monto = origen × medida/total.

## B. CONTABLE vs NIC 2 / NIIF 18
4. En CONTABLE: admin, gasto_venta y financiero = 0 en cada objeto; el estado de resultados los presenta como gasto del periodo
   (financieros en FINANCIACION). REAL − CONTABLE por periodo = Σ GAD + GVT + GFI.

## C. ESTIMADO fuera de muestra
5. Demuestra que `estimacion` de 2010-12 no usa datos de diciembre (cambia el CU de diciembre en una copia y comprueba que el
   ESTIMADO no cambia). Revisa que la banda P05–P95 tenga sentido frente a la historia.

## D. Proyección y simulación
6. Reproducibilidad: dos cálculos seguidos dan las mismas p05/p50/p95 (semilla 2010). La p50 acompaña al determinístico (RA-17).

## E. Entrada única y sello
7. Intenta cargar por la API libros rotos (sin hoja, columna faltante, referencia rota, periodo mal escrito, entrada de kardex
   sin valor). Debe rechazar con mensaje en español. Intenta que acepte algo inválido.
8. Modifica el libro después de calcular: el sello debe decir LIBRO_MODIFICADO.

## F. Paquete
9. En una carpeta limpia: `python tools/entrega/armar.py --periodo 2010-12` y abre cada archivo (Excel con openpyxl, Word con
   python-docx, HTML con un navegador sin red). Lista lo que falte o esté roto.

Tiempo en `docs/entrega/tiempos/codex.csv`. Compuerta: `python tools/verificar.py` debe seguir VERDE (no cambiaste código).

## G. Lógica completa (agregada el 22-nov; base ≥ `83c3c9b`)
10. Flujo único: `/api/libros/operar?id=frenosa` → registra un T15 y un T14 en dólares por `/api/workspaces/<id>/execute` →
    recalcula el espacio (`esp_…`). Comprueba kardex, pérdidas por merma en exceso y conciliación EXISTENCIA motor = kardex.
11. Inventarios: cambia en una copia del libro cantidades vendidas, deja una orden abierta y una orden que termine el mes
    siguiente; verifica costo de ventas, producto terminado, en proceso y el ajuste D14 con aritmética propia.
12. Coproductos (T18 con dos productos): REAL por unidades, CONTABLE por valor de venta relativo; el costo conjunto se conserva.
13. Capacidad ociosa (MEDIDA nivel CAP), costeo normal (TARIFA_CENTRO PRED) y variaciones (TARIFA STD).
14. Costo de adquisición: flete del documento, T14.2 tardío (parte a inventario y parte a gasto), centro COM (REAL en inventario,
    CONTABLE gasto) y devolución al proveedor a costo directo.
15. Cierre y aprobación: intenta aprobar sin revisar, aprobar con el mismo usuario que emitió, alterar un paquete sellado, reabrir
    sin motivo. Todo debe rechazarse. Verifica que la v1 sigue existiendo tras emitir la v2.
16. Autonomía: aprueba noviembre y recalcula diciembre; recalcula a mano el ahorro realizado y el factor de efectividad.
