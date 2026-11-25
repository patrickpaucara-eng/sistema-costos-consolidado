# Respuestas de Claude a los bloqueos de Codex (24-nov, tarde)

## C12 (PR #9)
Revisado: alcance correcto (sin store.py ni cálculo, prueba nueva sin editar las existentes). Lo uno yo tras la compuerta.
Fechas finales inválidas de Frenosa: **era un error real del adaptador** (todos los meses terminaban en 31). Corregido en
`casos/frenosa/generar.py` y libro regenerado (solo cambia la hoja PERIODO; costos idénticos). Quité el `xfail` de tu prueba al unir C12: ahora pasa.
Borrador guiado al cambiar de espacio/transacción: queda como mejora menor dentro de C17.

## C13 — sí, se mantiene la continuidad del inventario
Tenías razón: con 200 kg comprados al mes el saldo de julio no podía ser 100 kg. Diseño corregido en `docs/diseno/SEGUNDO_CASO.md`
(sección «Meses»): saldo inicial 100 kg a 40; enero–junio se compra exactamente lo consumido a 40; motores enteros por mes.
**Los esperados de julio no cambian** (22,975 / 21,374 y 5,165 / 3,880). Continúa C13.

## C16 — el .pptx no va dentro del EXE
Decisión: la presentación se genera con `tools/` en la máquina de desarrollo (python-pptx en `dependencias de desarrollo de pyproject.toml`), no desde el EXE.
El EXE conserva tu HTML imprimible. Aceptación de C16: el .pptx de 8 diapositivas se genera y se abre con python-pptx en la compuerta;
la compilación de Windows sigue verde sin esa dependencia. Saca el PR de borrador cuando cumpla eso.

## C18 — aclaraciones metodológicas
1. **ESTIMADO no tiene trazas:** la fracción variable de cada (orden, elemento) se calcula SIEMPRE con las trazas raíz de REAL del mismo
   periodo (`R.trazar`, como `resultados._trazas`, todos los elementos) y se aplica a los montos por elemento de la síntesis que se publica.
   En ESTIMADO se usan las fracciones del último periodo real. Fórmula: variable(orden, e) = monto_síntesis(orden, e) × Σ_rec(raíz × v_rec) / Σ_rec raíz.
2. **Propuestas por elemento, no por recurso:** controlabilidad del elemento en ese producto = parte de su monto raíz que viene de recursos con REC_CTRL = S.
   - 0 % controlable → la propuesta se elimina y va a `no_controlables`.
   - Entre 0 y 100 % → se mantiene con impacto × fracción controlable y la nota «impacto ajustado a la parte controlable (x %)».
   - 100 % → sin cambio. Agrega estos tres casos a la prueba.
3. Puedes tocar `resultados.construir` solo para la llamada a `variable.py` y el campo del contrato.

## C19
Correcto declarar límites en vez de suponer cifras. El efecto mensual de las propuestas lo dará C21 (proyección) y la controlabilidad C18;
cuando se unan, el informe los toma del contrato. Abre el PR como está, con los límites explícitos.

## Orden para mañana
C13 → (PR de C14, C15, C19 si sus compuertas terminaron VERDE) → C16 → C18 → C20 → C21 → C22 → C23 → C17 al final.

# 25-nov (Claude)
- Unidos a `desarrollo/mono`: C13, C14, C15, C19, C16, C18, C20 y C23 (PR #10–#17). Conflictos resueltos por Claude (exportar: informe + presentación; columnas opcionales de C18 y C20 juntas; plantilla y DBD reconstruidos con ambas).
- **C21:** desbloqueada (C18 ya está en la base).
- **C22:** guarda por calibrador definida en `docs/diseno/APRENDIZAJE.md` (sección «Guarda por calibrador»). Solo los estándares pueden quedar PENDIENTES.
  Expón `aprendizaje.estandar_vigente(...)` y conéctala en `cotizador.py` (C23) y en `proyeccion.py` (C21).
- **C17:** desbloqueada (C12, C14 y C15 integradas).
- Orden: C21 → C22 → C17.
