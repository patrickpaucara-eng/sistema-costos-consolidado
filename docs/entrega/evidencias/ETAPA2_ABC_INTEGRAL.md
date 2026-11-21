# Etapa 2 · ABC integral y síntesis REAL / CONTABLE (NIIF 18)

**Método:** el mismo REPARTO_ETAPAS, con una etapa nueva **P7 FIN → orden** (patrón de P5 ADM y P6 VTA). La regresión de Oria sigue exacta (P10 tradicional y ABC a ±0.0001; P05 corre).
**Gastos operativos y financieros:** el caso Frenosa no los publica → **supuestos académicos declarados** en `datos/frenosa_supuestos/Gastos_Operativos_SUPUESTOS.csv` (administración S/ 39,500; comisiones 3 % y despacho 1.5 % de ventas; intereses S/ 12,000 por mes), cada uno con su inductor ABC: kg producidos, ventas netas, kg vendidos, kg de material.

| Síntesis | Costo del objeto | Estado de resultados |
|---|---|---|
| **REAL** (gerencial) | MD + MOD + CIF + administración + ventas + financieros = **costo integral** (precio objetivo) | Mismas líneas |
| **CONTABLE** (NIC 2) | MD + MOD + CIF (administración, ventas y financieros **nunca** al inventario) | NIIF 18: **Operación** (ventas, costo de ventas, administración, ventas) · **Financiación** (financieros) |

Comprobaciones a mano (julio 2010): administración de FRE9000 = 39,500 × 44,039 / 98,020 = 17,746.79; ventas de FRE9000 = 26,661.90 × 453,602 / 888,730 + 13,330.95 × 44,039 / 98,020 = 19,597.47. El resultado operativo es el mismo en las dos síntesis; cambia el costo del objeto (barrera en `tests/test_frenosa_anual.py`).

## Inconsistencia adicional del proyecto pasado
El soporte de producción (mantenimiento, control de calidad, ingeniería) se cargó **dos veces**: dentro del costo de la orden y otra vez restado entre margen bruto y margen operativo. Por NIC 2 es costo de producción: va al costo de ventas una sola vez.
