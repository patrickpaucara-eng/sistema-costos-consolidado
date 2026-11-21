# Etapa 1 · Frenosa julio 2010 por el ABC verificado

**Método:** REPARTO_ETAPAS (el mismo verificado contra Oria P10 a ±0.0001), sin código nuevo. Material por kardex (P1); mano de obra → actividades por minutos estándar (P2); otros recursos y soporte → actividades (P4A); actividades → órdenes con los pesos de producción y de soporte (P4C).
**Datos:** solo los cuadros del caso (Cherres Juárez 2010, PUCP), en `casos/frenosa/generar_julio.py`.

| Orden | MD | MOD | CIF | Total | C. unit. | Proyecto pasado | Dif. |
|---|---:|---:|---:|---:|---:|---:|---:|
| OT001 SW50 | 122,328.58 | 35,842.50 | 51,251.88 | 209,422.96 | 5.4860 | 209,149.73 | +273.23 |
| OT002 FRE9000 | 241,377.76 | 41,418.00 | 59,207.66 | 342,003.42 | 7.7659 | 341,687.69 | +315.73 |
| OT003 FRE9002 | 80,286.91 | 2,389.50 | 6,780.46 | 89,456.87 | 5.6593 | 89,438.66 | +18.21 |
| **Total** | 443,993.25 | 79,650.00 | 117,240.00 | **640,883.25** | | 640,276.08 | +607.17 |

## Inconsistencias del caso / proyecto pasado (encontradas)
1. **Mano de obra:** los porcentajes por actividad publicados (redondeados a entero) suman 99 %: el proyecto pasado repartió 78,855 de 79,650 → **perdió S/ 795**.
2. **Otros recursos:** los inductores del Cuadro 6 suman 99 % (Servicios, Instalaciones) y 101 % (Operacionales, No operacionales): el pasado **creó S/ 187.82** que no existen.
3. Nuestro reparto es proporcional (Σ medidas), así que **conserva el costo exacto**: total = suma de entradas = 640,883.25.
4. La mano de obra **no requiere un método nuevo**: con tolerancias y kg iguales para todas las actividades, el factor de distribución Fd es común y se cancela; el reparto es proporcional a los minutos estándar (Te × kg).

Prueba: `tests/test_frenosa_julio.py` (valores a mano).
