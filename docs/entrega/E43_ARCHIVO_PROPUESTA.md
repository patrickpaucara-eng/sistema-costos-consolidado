# E43 · Código que no corre: qué archivar (propuesta de Claude, 28-nov — decide el dueño)
Método: se siguieron las importaciones desde el ejecutable (`reyna_local.__main__`) y se buscó cada módulo en `tests/`, `tools/` y `.github/`. «Archivar» = mover a `archivo/` (no borrar), quitarlo del EXE y anotarlo aquí; se recupera en un minuto si hace falta.

| Bloque | Qué es | ¿Lo usa algo? | Propuesta | Por qué |
|---|---|---|---|---|
| `src/analitica/` (10 módulos + `proveedores/`) | Analítica de la etapa anterior (hallazgos, mensajes, simulación, Monte Carlo, optimización) | Nada del sistema ni pruebas; solo `tools/windows/build.py` lo empaqueta | **ARCHIVAR** | Reemplazado por `analisis.py`, `aprendizaje.py`, `autonomia.py`, `proyeccion.py`. Pesa en el EXE y confunde al lector del código |
| `src/analitica2/` (11 módulos) | Segunda versión de la analítica (catálogo de evaluadores, dispersión, impactos) | Nada; solo el empaquetado | **ARCHIVAR** | Igual que arriba; nunca se conectó |
| `metodos/ajustes_nic2`, `cif_aplicado`, `costo_objeto_ordenes`, `exceso_mermas` | «Cáscaras»: contrato sin cálculo | Nada | **ARCHIVAR** | Prometen algo que no hacen; NIC 2, CIF aplicado y mermas ya están en `inventarios.py`, `normal.py` y el reparto |
| `metodos/personal_directo`, `costo_a_la_fecha`, `simular_cierre`, `publicar`, `correr_metodos` | Métodos sueltos del almacén de la etapa VBA | Nada | **ARCHIVAR** | Del flujo VBA/T25.4, congelado; el motor Python ya cubre personal por actividad y el sello |
| `metodos/puerta`, `probar_metodos`, `direccion_capas`, `validar_metodo`, `_plantilla_metodo`, `caso_excel` | Herramientas de verificación y plantilla de métodos | Herramientas | **CONSERVAR** | No son del sistema; sirven para verificarlo y agregar métodos |
| `casos/comun` | Utilidades de cargadores de casos | Nada | **CONSERVAR** | Lo usan los generadores de casos fuera del árbol de importación |
| `reyna_local/catalogo_dbd.py` | Inventario de encabezados DBD | `tests/test_c27_c_catalogo.py` | **CONSERVAR** | Tiene prueba; es pequeño |
| `reyna_local/tramos_cantidad.py` | Tramos de cantidad (C34-3) | Pruebas propias | **CONSERVAR** | Se conecta al Pedido en C37-4 |
| `reyna_local/intervalos_proyectados.py`, `comparar_laboratorio.py` | Marcados «preliminar» en su encabezado, pero SÍ corren | Sistema | **CONSERVAR**, quitar la palabra «preliminar» o completar | Están en uso |

**Efecto si apruebas todo «ARCHIVAR»:** ~25 módulos (≈2,000 líneas de analítica + 9 métodos) salen del sistema y del EXE; ninguna prueba ni pantalla cambia. Requiere editar `tools/windows/build.py` (línea 63: quitar `analitica` y `analitica2`) y correr la compuerta.

**Para Codex (si apruebas):** «Mueve a `archivo/` lo marcado ARCHIVAR en docs/entrega/E43_ARCHIVO_PROPUESTA.md, quita `analitica` y `analitica2` de `tools/windows/build.py`, corre la compuerta y abre el PR C40.»
