# Pieza 30 · oraculo_SERVITEC.xlsx

Es la verificación independiente del motor. Rehace **a mano, con fórmulas de Excel visibles**, el costo de julio de 2025 del caso sintético SERVITEC. Sigue las etapas de Oria y, en cada etapa, muestra la matriz de configuración (de REGLA_REPARTO) y la matriz de cálculo (de MEDIDA):

| Hoja | Qué hace |
|---|---|
| DATOS | Los únicos números tecleados: copiados del libro, cada uno con la hoja y fila de donde salió |
| P1_MATERIAL | Kardex a promedio ponderado. Cada orden: consumo real, estándar, exceso (pérdida) y material normal |
| P2_PERSONAL | MOD → actividades (HORAS_MOD) |
| P4A_INDIRECTOS | Alquiler, energía, supervisión y administración → centros |
| P4B_RECIPROCO | Mantenimiento ↔ calidad → taller. Presentación clásica (X) y efectiva (N = (I − P)⁻¹); las dos entregan 2,200 |
| P4D_TALLER | Taller → actividades (TALLER_ACT) |
| P4C_ACTIVIDADES | Actividades → órdenes; la capacidad práctica de PRU (200) separa el ocio: 20 % |
| P5_P7_GASTOS | Administración → órdenes. No hay reglas P6/P7: lo comprueba contándolas |
| RESULTADO | Costo por orden y por producto; controles de las cifras del dueño y de conservación |
| COMPARACION_MOTOR | Oráculo frente a calcular() del motor: 20 cifras por orden y elemento, 27 flechas por etapa y 3 controles |

## Resultado (28/11/2026)

| Orden | Oráculo | Motor | Diferencia |
|---|---|---|---|
| OT-SRV-REB-2025-07 | 22,975.00 | 22,975.00 | 0.00 |
| OT-SRV-MPR-2025-07 | 5,165.00 | 5,165.00 | 0.00 |

Desglose de REB: MD 6,174 (147 kg × 42) + MOD 9,600 + CIF 5,600 + adm. 1,000 + pérdida 126 (3 kg en exceso × 42) + ocio 475.
Desglose de MPR: MD 840 + MOD 1,920 + CIF 1,120 + adm. 1,000 + ocio 285.

**No hay diferencias en ninguna etapa.**

## Verificación automática

`python -I verificar_pieza30.py <repo> SERVITEC_sintetico.xlsx` (el archivo `motor_julio.py` debe estar en la misma carpeta). La verificación:
1. recalcula el libro con LibreOffice: 777 fórmulas, 0 errores;
2. exige que las hojas de cálculo sean fórmulas;
3. compara las 70 filas de DATOS con el libro;
4. vuelve a correr calcular();
5. reporta la diferencia por orden, por elemento y por etapa.

Se probó al revés: con una medida alterada (DES_OT de REB 200 → 210) y un número tecleado en RESULTADO, la verificación falló, nombró las dos alteraciones y ubicó la diferencia en la etapa P4C (actividad DES).

## Cómo se regenera

```
python -I motor_julio.py <repo>/src SERVITEC_sintetico.xlsx motor.json
python -I _generador/hacer_oraculo.py SERVITEC_sintetico.xlsx motor.json oraculo_SERVITEC.xlsx
```

## Límite

El oráculo está armado **para este caso**: dos centros de apoyo en recíproco, tres actividades y dos órdenes. Con otra empresa o con más centros, el método se repite igual, pero las hojas hay que ampliarlas.
