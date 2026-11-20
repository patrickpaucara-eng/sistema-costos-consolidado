# Sistema actual · cómo es el sistema hoy (16-nov-2026, después de I-0 … I-10, I-5, Ola 1 y Ola 1b)

Reemplaza a cualquier versión anterior de «sistema actual». [VERIFICADO] = contado en la base o en las pruebas hoy; [EN RAMA] = construido y probado, falta tu visto bueno para main.

## 1. Qué es, en una frase
Un sistema de costos en Excel cuyo **motor no sabe de costos**: lee del diccionario de datos (DBD, método Reyna) qué hace cada transacción, la ejecuta, la registra con bitácora y cierra periodos que ya no se reescriben. Un espejo en Python hace lo mismo y verifica cada número.

## 2. Tamaño [VERIFICADO]
| Pieza | Hoy |
|---|---|
| Tablas del modelo (DBD_4) | 103: 53 de hechos (parque), 34 catálogos, 7 maestros, 3 de seguridad, 2 de configuración, 2 históricas, 2 semilla |
| Transacciones | 47 (26 en línea, 21 por lote: cierre, estadísticas, alertas) |
| Servicios de datos (reglas como datos) | 544, agrupados en 266 operaciones |
| Métodos de costeo registrados | 15 (+ 25 módulos en `kit/metodos`) |
| Capa analítica | 20 módulos (hallazgos H-03…H-14, catálogo de propuestas, seguimiento, autonomía, riesgo) |
| Usuarios / perfiles de demostración | 12 / 12 |
| Pruebas | pytest 520 · historia 392 escenarios · caso O-1 66 valores contra Python independiente |

## 3. Cómo se usa (como usuario, sin ver código) [EN RAMA Ola 1b]
`instalar.bat` → abrir `Sistema_Costos.xlsm` → se abre sola la ventana:
- **SEGURIDAD** (ingreso con usuario y clave) · **DATA-ENTRY** (registrar una operación con su formulario) · **CARGA** (puerto de captura) · **ACT-BD** (cadena de cierre) · **CONSULTA** (hoja de costo con traza N1→N4) · **REPORTES** (kardex, diario) · **ESTADÍSTICAS** · **ALERTAS** · **ANÁLISIS** (decidir) · **APROBAR** (cambios de parámetros) · **MANT-PARM**.
- **OPERAR MES (nuevo):** Elegir `CARGA_MES.xlsx` → **Validar** (no graba; dice qué fila y por qué) → **Importar** (todo o nada; nunca duplica) → **Cerrar mes** (sigue CIERRE_PASO; ventas después de liquidar) → **Ver resultados**.
- Hojas protegidas: el usuario escribe solo en CARGA, MENU e INSTALAR.

## 4. Qué garantiza (lo que lo hace defendible)
| Garantía | Cómo |
|---|---|
| Cada número se puede rehacer | Python independiente: O-1 66/66 (CPT 242,072.45; IFPP 106,325.45; CV 242,063.14); caso del mes de usuario a mano (OS-01 S/ 28,321.87) |
| Excel = Python | Motor VBA y espejo idénticos (P19); paridad automática celda por celda en cada prueba del dueño (I-3, I-5: COINCIDE) |
| Nada se rompe al cambiar | 392 escenarios de regresión en cada cambio |
| Un periodo cerrado no se reescribe | Hecho tardío entra al mes abierto con referencia (I-3); puente publicado/recalculado |
| Quien propone no aprueba | Separación de funciones; la capa analítica propone, una persona decide (I-2) |
| Datos sucios no entran | Puerto estricto: rechaza con motivo, no corrige (I-6, Ola 1b) |
| Varias empresas en una base | La empresa es parte de la clave; el usuario no la escribe; no puede tocar otra empresa (I-5); parámetro propio o común (D12) [EN RAMA] |
| Una orden terminada no acepta consumos posteriores | R-80 como imposibilidad (I-10) |

## 5. Qué está en main y qué en ramas
| Estado | Incrementos |
|---|---|
| **main** | I-0, I-0b (alineación MCD↔DBD), I-1 (siembra de casos), I-2 (separación de funciones, seguimiento, autonomía), I-2b (riesgo), I-3+I-4 (tardío, claves compuestas), I-5 (varias empresas), I-6 (importador), I-8 (exportador), I-10 (R-80, costo a la fecha), herramientas (paquetes, volumen, paridad) |
| **`desarrollo/ola1`** (falta tu prueba y visto bueno) | D12 la empresa gana al común · D1 UMBRAL dentro de PARAMETRO · Ola 1b pantalla OPERAR MES + plantilla + guía + protección · **corrección de I-5**: 17 referencias a tablas de empresa ahora compuestas; coherencia del DBD 16 → 0 errores |
| **`desarrollo/deuda`** | Diagnóstico global (14 puntos), cuadre de cuentas (J), caso de 6 meses (K), diseño de protección con huella (OT-107) |
| **`desarrollo/I-9`** | Diseño de la capa predictiva (OT-106) |
| **Demo congelada** | `prototipo/v41-congelado` (3a28500) + zip entregado: intocable |

## 6. Límites conocidos (dichos antes de que pregunten)
| Límite | Estado |
|---|---|
| Excel: un usuario a la vez | Por diseño |
| La carga se vuelve lenta al crecer las tablas (110 → 767 ms/línea en 6 meses) | D13: índice en la búsqueda (planificado) |
| Las cuentas CTA_* tienen varios escritores (no cuadran por construcción con RESULTADO_METODO) | D9: rediseño en Ola 3 |
| El costo provisional de una venta no se reexpresa tras el cierre cuando el plan está en otra unidad | D14: Ola 3; por eso las ventas del mes de usuario van al cerrar |
| La compra no capitaliza el flete (NIC 2) | Ola 3 (visto en la comparación con Frenosa) |
| Reparto del indirecto mensual (no por tiempo dentro del mes) | Investigación futura |
| Datos sintéticos y casos del curso | Sin datos reales de empresa |

## 7. Qué sigue (PLAN_CIERRE_SISTEMA.md)
Ola 1 (cerrar con tu prueba) → Ola 2 estructura en paralelo → Ola 3 credibilidad del cierre (D9 primero) → Ola 4 integridad (huella) → Ola 5 predictiva + simulación en copia + consulta guiada → Ola 6 prueba global de 6 meses y v5.0. Avance ≈ 93 %.
