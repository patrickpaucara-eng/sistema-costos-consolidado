# Segundo caso · SERVITEC SAC (servicios: taller de reparación de motores) — diseño y esperados a mano

Propósito: demostrar «cualquier organización» (servicios, no manufactura), el **Modelo 2 de Oria** (EC → CA → AC → OC), el
**recíproco** entre centros de apoyo, **ocio** (capacidad) y **merma en exceso**, con datos propios (Frenosa no se toca).
Empresa `SRV`, moneda PEN, periodos 2025-01 a 2025-08 (8 meses: la banda estocástica es estimable). Adaptador en
`casos/segundo/generar.py` (mismo estilo que `casos/frenosa/generar.py`: escribe por nombre de columna sobre `casos/plantilla_dbd.xlsx`).

## Modelo (igual todos los meses)
| Pieza | Código | Datos |
|---|---|---|
| Objetos | `OT-SRV-REB-<per>` (rebobinado), `OT-SRV-MPR-<per>` (mantenimiento preventivo) | producto REB / MPR, cantidad = motores atendidos |
| Material | `MAT_COBRE` (MD, kg) | COMPONENTE: REB 14 kg/motor, MPR 2 kg/motor, merma normal 5 % |
| Mano de obra | `MOD` (PD) | planilla 6 técnicos × S/ 2,000 = 12,000/mes → P2 por horas a actividades |
| Indirectos | `ALQ` 3,000 · `ENE` 1,500 · `SUP` 2,500 (IND) | P4A a centros |
| Centros | `CA_MANT`, `CA_CAL` (APR) · `CA_TALLER` (PRO) · `ADM_SRV` (ADM) | |
| Actividades (nivel O) | `DES` desarmado · `BOB` bobinado · `PRU` pruebas | |
| Gasto adm. | `ADM01` 2,000 (tipo ADM) | P4A → ADM_SRV; P5 50/50 a las dos OT |

Reglas de reparto y medidas de **julio 2025** (los demás meses en la tabla del final):
- P4A ALQ por m²: MANT 20, CAL 10, TALLER 70 · ENE por kWh %: 10, 10, 80 · SUP por %: 20, 20, 60.
- P4B (recíproco): MANT → CAL 20 %, TALLER 80 % · CAL → MANT 10 %, TALLER 90 %.
- P4D TALLER → actividades %: DES 30, BOB 50, PRU 20.
- P2 MOD por horas: DES 300, BOB 500, PRU 200.
- P4C por horas a OT: DES (REB 200, MPR 100) · BOB (REB 500) · PRU (REB 100, MPR 60) con **capacidad PRU = 200 h** (MEDIDA nivel CAP).
- P5 ADM_SRV → OT por 1 : 1.
- Kardex cobre: saldo inicial 100 kg a S/ 40 (4,000); compra 05-jul 200 kg a S/ 43 (8,600) → promedio S/ 42.
  Consumos: REB 150 kg (10 motores; estándar 147 kg → **exceso 3 kg**, LIN_EXC = 3); MPR 20 kg (10 motores; estándar 21).
- Ventas julio: REB 10 × 3,000 = 30,000 · MPR 10 × 800 = 8,000.

## Esperados de julio 2025, calculados a mano
Centros: propio MANT 600+150+500 = 1,250 · CAL 300+150+500 = 950 · TALLER 2,100+1,200+1,500 = 4,800.
Recíproco: X_M = 1,250 + 0.1·X_C; X_C = 950 + 0.2·X_M → X_M = 1,345/0.98 = 1,372.448980; X_C = 1,224.489796.
TALLER recibe 0.8·X_M + 0.9·X_C = **2,200.00** → total 7,000 → DES 2,100 · BOB 3,500 · PRU 1,400 (CIF).
MOD: DES 3,600 · BOB 6,000 · PRU 2,400 (PD).
PRU usa 160 de 200 h → ocio 20 %: normal 3,040 (CIF 1,120 + PD 1,920); **ocio 760** (CIF 280 + PD 480), ambos 100 : 60.

| Orden | MD normal | Pérdida (MD) | PD | CIF | Ocio | Adm. | REAL (integral) | CONTABLE (inventario) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| OT-SRV-REB-2025-07 | 6,174 | 126 | 9,600 | 5,600 | 475 | 1,000 | **22,975** | **21,374** |
| OT-SRV-MPR-2025-07 | 840 | 0 | 1,920 | 1,120 | 285 | 1,000 | **5,165** | **3,880** |

Conservación: recursos 7,140 + 12,000 + 7,000 + 2,000 = 28,140 = 22,975 + 5,165 ✓.
CONTABLE: pérdida 126 y ocio 760 van al estado de resultados como gasto; resultado operativo igual en REAL y CONTABLE.

## Meses 2025-01 a 2025-08 (corregido 24-nov tras observación de Codex: continuidad del inventario)
El inventario es continuo: el saldo de cierre de un mes es el saldo inicial del siguiente. Para que julio abra con 100 kg a S/ 40:
- Saldo inicial 2025-01-01: **100 kg a S/ 40** (4,000), un solo registro SALDO.
- Enero a junio: cada mes se compra **exactamente lo que se consume, a S/ 40** (compra el día 05, consumos después) → el promedio
  sigue en 40 y el saldo de cierre vuelve a 100 kg. Así julio abre con 100 kg a 40, como exige la tabla de esperados.
- Julio: compra 200 kg a S/ 43 y consumos REB 150 / MPR 20, como arriba → cierra 130 kg a S/ 42.
- Agosto: compra 200 kg a S/ 43.50; consumos según la regla de abajo.

Motores por mes (enteros) y factor f (horas de P2 y P4C × f, ventas × f; capacidad PRU fija en 200 h):
| mes | 01 | 02 | 03 | 04 | 05 | 06 | 07 | 08 |
|---|---|---|---|---|---|---|---|---|
| f | 0.8 | 0.9 | 0.9 | 1.0 | 1.0 | 1.1 | 1.0 | 1.1 |
| motores REB y MPR (cada uno) | 8 | 9 | 9 | 10 | 10 | 11 | 10 | 11 |
Consumo de cobre fuera de julio = estándar con merma normal: REB 14.7 kg × motores, MPR 2 kg × motores (sin exceso). La merma en exceso solo existe en julio.
(PRU usa 160·f h ≤ 176 < 200: hay ocio todos los meses.)

## Aceptación (OT-C13)
`tests/test_segundo_caso.py`: el libro valida; julio da exactamente la tabla (±0.01) en REAL y CONTABLE; los 8 meses conservan;
la banda de 2025-08 es estimable; Frenosa no cambia.
