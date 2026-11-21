# Carpeta de MÉTODOS (todos los métodos de costeo, fuera de la base)

**Cómo se usa (sin programar):** doble clic en `correr_metodos.bat`, escriba el periodo y la empresa.
- Se abre un Excel con tres hojas:
  - **Estado:** cada método, si es compatible y si se usó;
  - **Resultados:** los valores calculados;
  - **Explicacion:** el paso a paso.
- Si responde S, los resultados quedan en la bandeja. En el sistema, «Procesar carga» los registra (puerto T25.4).

**Vigencia (Tino):** cada método tiene `vigente_desde`. Para un periodo se usa, por eje, la versión APROBADA con la mayor vigencia que no pase del inicio del periodo. Así un periodo pasado se recalcula con el método que regía entonces.

**Agregar un método:**
1. Copie `_plantilla_metodo.py` y complételo (`FORMATO_METODOS.md`).
2. Valídelo: `python -m metodos.validar_metodo metodos/<archivo>.py fuente/DBD_Fuente.xlsx`.
3. Regístrelo en `fuente/Datos_Iniciales.xlsx`, hoja `D_METODO_REGISTRADO`: nombre, versión, estado EN_PRUEBA, archivo, fuente, vigente desde, eje.
4. Pruébelo con `--incluir-en-prueba`.
5. Cuando esté validado, el estado pasa a APROBADO (pendiente 15: con doble control).

**Métodos de la carpeta:**
- compatibles: `valuacion.py` (PROMEDIO_MOVIL 1.0, EN_PRUEBA desde el 10-nov por ERR-1; el vigente de cada eje es su BASE_<EJE>, ver METODO_REGISTRADO), `personal_directo.py` (PERSONAL_PLANILLA 1.0, en prueba);
- cáscaras con contrato, falta el cálculo: exceso_mermas, reparto_etapas, costo_objeto_ordenes, liquidacion, ajustes_nic2, costo_ventas_gastos, cif_aplicado, proyeccion, diferencias.
