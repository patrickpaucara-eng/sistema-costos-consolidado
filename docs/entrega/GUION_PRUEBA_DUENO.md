# Guion de prueba del ejecutable sin internet (15 min)

**Quién:** el dueño, en la PC de Windows donde se entregará. **Qué prueba:** que `ReynaCostos.exe` calcula SERVITEC sin conexión y que rechaza con un mensaje claro los libros defectuosos. Marca una casilla por paso. Si algo falla, anota qué viste al final (tabla de hallazgos).

**Antes de empezar (no cuenta en los 15 min)**
- Descarga `ReynaCostos-Windows-x64.zip` desde GitHub → Actions → «Paquete offline de Windows» (último run verde de `desarrollo/mono`). Cópialo a la PC junto con la carpeta `tests/datos/libros_hostiles/` del repo (los libros no vienen dentro del zip).
- Extrae el zip en una carpeta nueva. Desconecta Wi-Fi y cable de red (o activa modo avión). Deja el reloj a la vista.

**Resultado de referencia (SERVITEC, julio 2025, síntesis REAL):** OT-SRV-REB-2025-07 = **22,975**; OT-SRV-MPR-2025-07 = **5,165**; total del periodo = **28,140**; margen operativo = 9,860.

---

## Parte A · Arranque y cálculo correcto (6 min)

| # | Haz esto | Debe pasar | OK | FALLA |
|---|---|---|---|---|
| A1 | Doble clic en `ReynaCostos.exe`. Deja abierta la consola. | Se abre el navegador en `http://127.0.0.1:<puerto>`. Si no, copia la dirección de la consola y pégala. Arriba dice «Conectando…» y luego conectado. Sin internet. | ☐ | ☐ |
| A2 | Menú **Configuración → Cargar empresa**. Pulsa «Elegir libro .xlsx» y elige `00_control_sin_defecto.xlsx`. | El sistema valida el libro y lo acepta, sin mensajes de error ni texto de Python. | ☐ | ☐ |
| A3 | Pulsa «Operar la empresa elegida (crear espacio)». | Aparece confirmación de que se creó el espacio de operación. | ☐ | ☐ |
| A4 | En la barra superior elige la empresa (el espacio creado), periodo **2025-07**, síntesis **REAL**. Pulsa **Calcular**. | Termina sin error. El indicador «Sello» pasa a VIGENTE. | ☐ | ☐ |
| A5 | Menú **Pedido → Órdenes**. | REB = **22,975** y MPR = **5,165** (costo total de cada orden). | ☐ | ☐ |
| A6 | Cambia la síntesis a **CONTABLE** y vuelve a calcular. | El resultado operativo del mes es el mismo; cambia lo que se queda cargado en cada orden (pérdida y ocio salen al estado de resultados). | ☐ | ☐ |

## Parte B · Libros defectuosos (7 min)

Para cada libro: **Configuración → Cargar empresa → Elegir libro .xlsx**, elige el archivo y mira el mensaje. En ningún caso debe aparecer una traza de Python (líneas «Traceback…», rutas `.py`).

| # | Libro | Esperado | OK | FALLA |
|---|---|---|---|---|
| B1 | `01_hoja_obligatoria_borrada.xlsx` | Rechazo: «Falta la hoja CRITERIO. Inductores (unidad de medida).» | ☐ | ☐ |
| B2 | `03_texto_en_monto.xlsx` | Rechazo con hoja y fila: «Hoja VENTA, fila 14: el ingreso (VTA_ING) debe ser un número.» | ☐ | ☐ |
| B3 | `05_codigo_duplicado.xlsx` | **Hoy el sistema lo acepta y calcula mal sin avisar** (hallazgo conocido): REB sale con cantidad 12 y costo unitario 1,914.58 en vez de 2,297.50. Anota qué ves. Cuando se corrija, lo esperado es un rechazo: «Hoja OBJETO, fila 18: OBJ_NUM «OT-SRV-REB-2025-07» está repetido (ya está en la fila 14).» | ☐ | ☐ |
| B4 | `07_archivo_truncado.xlsx` | Rechazo: «El archivo no es un libro Excel (.xlsx) legible.» Sin traza. Después, el espacio que ya tenías (A3) sigue funcionando: vuelve a calcular 2025-07 y da 22,975 / 5,165. | ☐ | ☐ |

Para B3 marca OK si el comportamiento coincide con lo que dice la columna «Esperado» **para la versión que estás probando** (hoy: acepta y da 1,914.58; después de la corrección: rechaza). Si ves otra cosa, marca FALLA.

## Parte C · Cierre (2 min)

| # | Haz esto | Debe pasar | OK | FALLA |
|---|---|---|---|---|
| C1 | Sin haber reconectado la red, vuelve a **Calcular** 2025-07 con el espacio de A3. | Mismo resultado que A5. | ☐ | ☐ |
| C2 | En la consola pulsa **Ctrl+C**. | El servidor se cierra. Tus datos quedan en `%LOCALAPPDATA%\ReynaCostos\datos`. | ☐ | ☐ |

---

## Si algo falla
Anota: paso, qué esperabas, qué viste (copia el texto exacto del mensaje) y la hora. Si ves una traza de Python o el programa se cierra, guarda la consola completa. Eso es un hallazgo: se registra como `E<n>` en `docs/entrega/evidencias/ERRORES_E2E.md` y se corrige en lote, no en el momento.

## Qué cubre y qué no
- Cubre el cálculo de SERVITEC (caso sintético, creado para probar el sistema) y cuatro defectos de carga de los nueve libros de `libros_hostiles/`.
- No cubre Frenosa (caso real, no viaja con el paquete), ni los libros 02, 04, 06 y 08, que ya se verifican con `tests/datos/libros_hostiles/verificar_pieza24.py`.
- Los textos de los mensajes vienen de `tests/datos/libros_hostiles/LEEME.md`. Si el EXE los muestra con otras palabras pero dice lo mismo, es OK.

| Hallazgo (paso, qué viste) | Hora |
|---|---|
|  |  |
|  |  |
