# Verificación del recorrido HTML · Piloto 0.1

Se ejecutó el servicio real Python con almacenamiento Excel y se operó desde Chromium 156 en Linux. El piloto importó la [fixture Ola 1](../../../tests/fixtures/ola1/README.md), ejecutó dos compras T14 y un consumo T15, consultó el saldo en HTML y lo recuperó tras detener y reiniciar el proceso con el mismo directorio de datos.

## Datos y resultado

- Fuente histórica: `desarrollo/ola1@cac2501d9f712655dda466d216dc5bff2dd446a5`, ruta `kit/salida_b/Sistema_Costos.xlsx`.
- SHA-256 de la fixture antes y después: `43c9170c04b23e678de7abf7bab39f43c4251ea14695b351d884639ea972be40`.
- El espacio comenzó en versión 0 y quedó en versión 3. EXISTENCIA mostró CAJA4KG, almacén ALM1, empresa B, cantidad **400**, costo promedio **S/ 3,054** por unidad y valor **S/ 1.221,60** al céntimo. KARDEX mostró la misma versión.
- Comprobación a mano: `(2000 × 0,80 × 3,75 + 1000 × 0,85 × 3,72) / 3000 = 3,054`. El IGV recuperable queda fuera. Quedan `(3000 − 2600) × 3,054 = 1221,60`. El valor interno mostrado fue `1221.6000000000004`.
- Tras reiniciar, se volvió a elegir el espacio en el navegador y se obtuvo la misma fila y versión. La copia `libro.xlsx` conservó su SHA-256 entre el cierre y la reapertura.

Se verificaron además el rechazo de ruta local inexistente, la conservación del formulario ante JSON inválido, el reintento idéntico sin nuevo movimiento, el conflicto al cambiar el contenido con el mismo identificador y el usuario desconocido sin cambio de saldo o versión. La consulta de USUARIO devolvió 403. El servicio rechazó Host y Origin externos, un cuerpo de formato distinto de JSON y un cuerpo superior a 1 MiB. La página presentó literalmente un nombre con etiquetas HTML y mantuvo el documento sin desbordamiento horizontal a 393 px.

## Reproducir

Desde la raíz, con el [entorno instalado](../GUIA_PILOTO_EXCEL.md#preparar-el-entorno):

```sh
sha256sum -c tests/fixtures/ola1/SHA256SUMS
pilot_data_dir=$(mktemp -d)
.venv/bin/python -m reyna_local --data-dir "$pilot_data_dir" --port 0
```

Abrir la dirección local que imprime el servidor. Importar, por ruta absoluta, `tests/fixtures/ola1/Sistema_Costos.xlsx` y anotar el nombre del espacio. Ejecutar estas tres solicitudes con un identificador nuevo cada vez. Las tramas usan el modo de líneas separadas. La [guía del piloto](../GUIA_PILOTO_EXCEL.md#caso-comprobable-a-mano) documenta el mismo recorrido con tramas planas.

| Operación y usuario | Cabecera JSON | Líneas JSON |
|---|---|---|
| T14 · ALMACEN1 | `{"FECHA":20260310,"PER":"2026-03","EMP":"B","ALM":"ALM1","MON":"USD","IMP":"IGV"}` | `[{"REC":"CAJA4KG","CANT":2000,"CU_DOC":0.80}]` |
| T14 · ALMACEN1 | `{"FECHA":20260405,"PER":"2026-04","EMP":"B","ALM":"ALM1","MON":"USD","IMP":"IGV"}` | `[{"REC":"CAJA4KG","CANT":1000,"CU_DOC":0.85}]` |
| T15 · SUPERV1 | `{"FECHA":20260410,"PER":"2026-04","EMP":"B","OBJ":"OS-01","CEN":"LINEA1","ALM":"ALM1"}` | `[{"REC":"CAJA4KG","CANT":2600}]` |

Consultar EXISTENCIA y KARDEX. Repetir la última solicitud con el mismo identificador y sus mismos datos. Esperar versión 3. Cambiar la cantidad conservando el identificador y esperar conflicto. Detener con `Ctrl+C`, volver a ejecutar el servidor con el mismo `pilot_data_dir`, abrir la dirección anunciada y volver a seleccionar el espacio. EXISTENCIA debe mostrar los mismos 400, 3,054 y 1.221,60. La prueba automática de respaldo para **HTTP y reapertura del XLSX** está en [test_capacidad_inicial.py](../../../tests/test_capacidad_inicial.py).

```sh
.venv/bin/python -m unittest discover -s tests -p test_capacidad_inicial.py -k test_compra_consumo_saldo_y_reapertura -v
```

## Alcance

Compra y consumo por un operador local de confianza que usa códigos del libro de prueba. Esta evidencia cubre la primera entrega; la rama MVP Ola 3 agrega cierre técnico configurado, con alcance y resultado separados en [MVP_OLA3.md](MVP_OLA3.md). Siguen pendientes la verificación en Windows/Excel nativo, la autenticación empresarial, el aislamiento integral entre empresas y la conciliación del costo de orden y sus cuentas. El [registro de capacidades](../REGISTRO_CAPACIDADES.md) conserva el alcance por incremento.
