# OT-C33-1 · cobertura de clave única y colisión de OT

## Alcance y método

La prueba recorre las secuencias TOP→OME→MET de los libros Frenosa y SERVITEC, encuentra cada destino de un método `CREAR` y consulta las columnas clave según el mismo contrato del motor: MCA con rol `K` cuando existe; en su ausencia, clave primaria de `fuente/DBD_Fuente.xlsx`, hoja `DBD_4_Modelo_Interno`. No se elige la primera columna por heurística.

En estos dos libros, los métodos de creación no declaran claves con MCA rol `K`; el motor usa la PK del DBD. Para cada destino, la prueba crea una fila con una clave declarada y repite esa misma clave: la segunda creación debe devolver `ya existe <tabla>` y no agregar una fila. `LINEA` se prueba con el mismo evento y números 1 y 2, que deben aceptarse; repetir la línea 1 debe rechazarse.

## Tablas cubiertas

| Tabla | Clave declarada en DBD |
|---|---|
| DESECHO | DSC_NUM |
| ESTIMACION | EST_NUM |
| EVENTO | EVE_NUM |
| HORA_EXTRA | HEX_NUM |
| LINEA | LIN_EVE + LIN_NUM |
| OBJETO | OBJ_NUM |
| PARADA | PDA_NUM |
| RECHAZO | RCZ_NUM |
| VENTA | VTA_EVE + VTA_LIN |

La misma cobertura se ejecutó contra los dos libros (`casos/libros/frenosa.xlsx` y `casos/libros/segundo.xlsx`, cuya empresa es SERVITEC). **No se encontró una tabla creable sin clave declarada**, por lo que no se inventó ninguna clave.

## Colisión de OT

Dos formularios de T13, con estimaciones distintas y solicitud/identificadores de sesión distintos, consultan el siguiente código antes de registrar; ambos reciben `OT-FRE-SW50-0001`. El primer registro es aceptado. El segundo devuelve HTTP/servicio 422 con `ya existe OBJETO ('OT-FRE-SW50-0001',)`. Se comparan `OBJETO`, `ESTIMACION`, `TARIFA`, `EVENTO`, `LINEA`, `EXISTENCIA` y `KARDEX` antes y después del rechazo: no hay escritura parcial ni incremento de versión.

## Resultado

Prueba propia: `tests/test_c33_1_claves_crear.py`.

```sh
PYTHONPATH=src python -m pytest -q tests/test_c33_1_claves_crear.py
```

Resultado focalizado: **22 pruebas aprobadas**. C33-1 solo añade pruebas y esta evidencia; no modifica `motor_espejo.py` ni otro módulo operativo. No se detectó una defensa faltante que requiera documentar bloqueo.

Compuerta completa (`python tools/verificar.py`): **526 pruebas aprobadas, 1 advertencia, 26 subpruebas aprobadas; contrato de resultados conforme; COMPUERTA: VERDE**.
