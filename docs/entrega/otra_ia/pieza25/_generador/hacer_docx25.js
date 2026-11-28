// Pieza 25 · MONOGRAFIA_1_textos.docx — textos para pegar en la monografía. Cifras desde hechos.json (calculadas, no tecleadas).
const fs = require("fs");
const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell, WidthType, ShadingType,
  AlignmentType, LevelFormat, HeadingLevel, BorderStyle, Footer, PageNumber, Header,
} = require("docx");
const H = JSON.parse(fs.readFileSync(process.argv[2], "utf8"));
const W = 9026, FONT = "Arial";
const n0 = (x) => Number(x).toLocaleString("en-US", { maximumFractionDigits: 2 });
const n2 = (x) => Number(x).toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 });

function runs(txt, o = {}) {
  const out = []; const re = /(\*\*[^*]+\*\*|~[^~]+~|`[^`]+`)/g; let last = 0, m;
  while ((m = re.exec(txt))) {
    if (m.index > last) out.push(new TextRun({ text: txt.slice(last, m.index), ...o }));
    const s = m[0];
    if (s.startsWith("`")) { out.push(new TextRun({ text: s.slice(1, -1), font: "Consolas", size: 20, ...o })); last = m.index + s.length; continue; }
    out.push(new TextRun({ text: s.slice(s.startsWith("**") ? 2 : 1, s.startsWith("**") ? -2 : -1), bold: s.startsWith("**") || o.bold, italics: s.startsWith("~") || o.italics, ...o }));
    last = m.index + s.length;
  }
  if (last < txt.length) out.push(new TextRun({ text: txt.slice(last), ...o }));
  return out;
}
const P = (t, o = {}) => new Paragraph({ children: runs(t, o.run || {}), spacing: { after: 120, line: 276 }, ...o.p });
const H1 = (t) => new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun(t)] });
const H2 = (t) => new Paragraph({ heading: HeadingLevel.HEADING_2, children: [new TextRun(t)] });
const H3 = (t) => new Paragraph({ heading: HeadingLevel.HEADING_3, children: [new TextRun(t)] });
const B = (t) => new Paragraph({ numbering: { reference: "v", level: 0 }, children: runs(t), spacing: { after: 60, line: 264 } });
const F = (t) => new Paragraph({ children: [new TextRun({ text: t, font: "Cambria Math", size: 21 })], indent: { left: 567 }, spacing: { after: 100 } });
const NOTA = (t) => new Paragraph({ children: runs(t, { size: 18, color: "5B6474", italics: true }), spacing: { after: 160 } });
const ESP = () => new Paragraph({ children: [], spacing: { after: 60 } });
const borde = { style: BorderStyle.SINGLE, size: 4, color: "C9CED6" };
function T(filas, anchos) {
  const tot = anchos.reduce((a, b) => a + b, 0); const esc = anchos.map((a) => Math.round((a * W) / tot));
  esc[esc.length - 1] += W - esc.reduce((a, b) => a + b, 0);
  return new Table({ width: { size: W, type: WidthType.DXA }, columnWidths: esc,
    rows: filas.map((f, i) => new TableRow({ tableHeader: i === 0, cantSplit: true, children: f.map((c, j) => new TableCell({
      width: { size: esc[j], type: WidthType.DXA }, borders: { top: borde, bottom: borde, left: borde, right: borde },
      shading: i === 0 ? { type: ShadingType.CLEAR, color: "auto", fill: "DCEAFB" } : undefined,
      margins: { top: 50, bottom: 50, left: 90, right: 90 },
      children: String(c).split("|").map((l) => new Paragraph({ children: runs(l, { size: 18, bold: i === 0 }), spacing: { after: 0, line: 240 } })) })) })) });
}
const R = H.julio.REB, M = H.julio.MPR, K = H.julio_kpi, L = H.lineas;
const c = [];

// ----------------------------------------------------------------------------------------------- portada
c.push(new Paragraph({ children: [new TextRun({ text: "Textos para la Monografía 1 · Sistema de costos ABC", bold: true, size: 34, font: FONT })], spacing: { after: 80 } }));
c.push(P("Secciones listas para pegar: **1. Marco teórico**, **2. Arquitectura del sistema** y **3. Límites del modelo**. Al final, «Fuentes» y una sección **Notas para el autor (no pegar)** con lo que quedó POR VERIFICAR.", { run: { color: "5B6474" } }));
c.push(P("Las cifras del caso SERVITEC (sintético) salieron de ejecutar calcular() del motor el 28/11/2026, no de copiarlas. Las rutas de archivo se refieren al repositorio del sistema.", { run: { color: "5B6474" } }));

// ----------------------------------------------------------------------------------------------- 1
c.push(H1("1. Marco teórico"));
c.push(H2("1.1 Costeo basado en actividades"));
c.push(P("El costeo basado en actividades (ABC) parte de una idea simple: los productos no consumen costos de manera directa, sino actividades, y son las actividades las que consumen recursos. En lugar de repartir los costos indirectos con una sola base (horas de mano de obra, por ejemplo), el ABC los acumula primero en actividades y después los asigna a cada orden según cuánto usó de cada actividad, medido con un **inductor** (Kaplan y Cooper, 1998; Horngren, Datar y Rajan, 2012). En su versión por tiempo (TDABC), cada recurso necesita solo dos datos: cuánto cuesta una unidad de tiempo de su capacidad y cuánto tiempo toma cada actividad (Kaplan y Anderson, 2004)."));
c.push(P("El sistema adopta la metodología ABC enseñada por W. Oria en el curso GE704W (Oria, 2026), que organiza el reparto en etapas sucesivas, separa el costo normal de la pérdida y de la capacidad ociosa, y trata los servicios entre centros con los métodos escalonado y recíproco."));

c.push(H2("1.2 La metodología de W. Oria"));
c.push(H3("Elementos del costo"));
c.push(P("Cada monto viaja hasta la orden etiquetado con su elemento: material directo (MD), personal directo (MOD), servicios directos (SD), costos indirectos de fabricación (CIF), gastos de administración, de ventas y financieros. Además lleva su **naturaleza**: NORMAL, PÉRDIDA (merma en exceso, rechazo sin reproceso) u OCIO (capacidad práctica no usada). La naturaleza decide si el monto es costo del producto o gasto del periodo; el motor no lo decide, lo decide la síntesis (sección 2.4)."));
c.push(H3("Actividades e inductores"));
c.push(P("Una actividad es un conjunto de tareas con un resultado medible. Cada actividad tiene un **inductor único** (decisión del dueño del 24-nov): la unidad que mide cuánto de la actividad consume cada destino (horas, kilogramos, pruebas, porcentaje). Las actividades se clasifican por nivel: **estratégicas (E)**, **de apoyo (A)** y **operativas (O)**; solo las operativas llegan a la orden."));
c.push(H3("Modelos 1, 2 y 3"));
c.push(P("Oria presenta tres modelos de reparto, cada uno más detallado que el anterior. El sistema no los programa por separado: el modelo resulta de los **datos** (qué reglas de reparto se cargan), y los modelos 1 y 2 son casos particulares del 3 (decisión del 22-nov)."));
c.push(T([
  ["Modelo", "Ruta del costo", "Etapas que usa en el sistema"],
  ["1", "Elementos de costo → actividades → objetos de costo", "P4A a actividades, P4C"],
  ["2", "Elementos → centros → actividades → objetos", "P4A a centros, P4D, P4C"],
  ["3 (escalonado)", "Elementos → centros → actividades estratégicas → de apoyo → operativas → objetos", "P4A, P4D, P4E, P4C"],
], [18, 52, 30]));
c.push(NOTA("Fuente de las rutas: metodos/reparto_etapas.py (docstring), que cita «Modelos ABC de Oria (GE704W sem. 07)»."));
c.push(H3("Escalonado y recíproco"));
c.push(P("Cuando dos centros de apoyo se prestan servicios entre sí (mantenimiento atiende a calidad y calidad atiende a mantenimiento), hay dos formas de repartir. En el **escalonado** el costo solo baja: un centro entrega a los que están por debajo y nunca recibe de vuelta. En el **recíproco** se reconoce el servicio mutuo resolviendo un sistema de ecuaciones; Oria lo considera el método preferible y el dueño lo adoptó como regla el 23-nov. El sistema lo resuelve en forma exacta:"));
c.push(F("X = propio + Pᵀ·X   ⇒   N = (I − P)⁻¹,   efectivo(j, k) = Σᵢ N(j, i) · s(i, k)"));
c.push(P("donde P(j, i) es la parte del centro j que va al par i y s(i, k) la parte de i que va al destino final k. Si no hay servicios mutuos, el resultado coincide con el escalonado, que queda como caso particular. En SERVITEC, julio, mantenimiento entrega 20 % a calidad y 80 % al taller, y calidad entrega 10 % a mantenimiento y 90 % al taller: es un caso recíproco de la etapa P4B."));

c.push(H3("Las etapas P1–P7 y las dos matrices"));
c.push(P("El reparto sigue siempre el mismo mecanismo: **monto del destino = monto del origen × medida del destino ÷ suma de medidas**. Lo que cambia de una empresa a otra son dos matrices que se llenan en el libro: la **matriz de configuración** (hoja REGLA_REPARTO: en qué etapa y con qué inductor se reparte cada origen) y la **matriz de cálculo** (hoja MEDIDA: cuánto inductor consumió cada destino en el mes)."));
c.push(T([
  ["Etapa", "Origen → destino", "Base"],
  ["P1", "Material → orden", "Consumo real del kardex a promedio ponderado; la merma en exceso va aparte"],
  ["P2 / P3", "Personal y servicios directos → actividad u orden", "Minutos reales u otro inductor"],
  ["P4A", "Indirectos → centros (o actividades)", "m², kWh, porcentajes"],
  ["P4B", "Centros de apoyo ↔ entre sí → centros productivos", "Recíproco exacto entre pares"],
  ["P4D / P4E", "Centros → actividades; actividades E → A → O", "Escalonado entre niveles; recíproco dentro del mismo nivel"],
  ["P4C", "Actividades operativas → órdenes", "Inductor de la actividad; la capacidad práctica separa el ocio"],
  ["P5 – P7", "Administración, ventas y financieros → órdenes", "Inductor del gasto"],
], [14, 40, 46]));
c.push(NOTA(`El caso SERVITEC carga ${H.reglas_reparto_servitec} reglas de reparto en las etapas ${H.etapas_servitec.join(", ")}.`));

c.push(H2("1.3 El enfoque MCD/DBD de Tino Reyna"));
c.push(P("El sistema sigue los libros MCD y DBD de Tino Reyna como base metodológica (decisión vigente del dueño). Su aporte al diseño es separar **qué hace la organización** de **cómo se guardan los datos**, y describir la operación como transacciones con reglas explícitas, en lugar de pantallas con lógica escondida."));
c.push(H3("Misión"));
c.push(P("La misión aprobada (versión 2.1, decisión E-041, con el ajuste del dueño de que el presupuesto es otro sistema) es: «El área de Costos existe para **ENTREGAR** el costo de cada objeto de costo —de producción, de ventas y de administración—, real, planificado y proyectado, y sus diferencias, distinguiendo lo que es costo del producto de lo que es gasto del periodo conforme a la normativa vigente, para que la gerencia tome decisiones y la empresa cumpla sus obligaciones de información.»"));
c.push(P("Cada parte de la misión tiene su lugar en el sistema: el costo **real** sale del reparto por etapas; el **proyectado** pasa por el mismo motor; las **diferencias** las calcula el costeo normal; y la distinción **costo del producto / gasto del periodo** es la síntesis CONTABLE (NIC 2), frente a la REAL de uso gerencial (sección 2.4)."));
c.push(H3("Funciones"));
c.push(P("El ciclo de uso del sistema se organiza en cinco funciones: **Definir** (modelo de costeo, catálogos, parámetros), **Estimar** (cotizar un pedido y proyectar), **Registrar** (hechos de compra, consumo, gasto, producción y venta), **Entregar** (costo por orden, reportes, decisiones) y **Aprender** (comparar lo proyectado con lo real y recalibrar con guardas)."));
c.push(H3("Eventos"));
c.push(P("Para Reyna, un **evento** es una transacción consumada: un hecho que ya ocurrió, con sus condiciones, operaciones y secuencia (MCD, §3.4). No se edita ni se borra; un error se corrige con otro evento. En el sistema cada evento es una transacción del catálogo (hoja TRX)."));
c.push(P(`En el libro de SERVITEC el catálogo tiene **${H.trx_total} transacciones**: ${H.trx_online} en línea (las registra el usuario, por ejemplo T14 compra, T15 consumo en la orden, T18 resultado de la orden, T20 venta) y ${H.trx_batch} por lote (las corre el cierre, por ejemplo T23.1 distribuir centros de servicio, T23.3 liquidar órdenes terminadas, T23.5 valor neto realizable). Cada transacción declara sus campos (TRX_CAMPO), sus operaciones (TOP → OME) y los métodos y fórmulas que aplica (MET, MCA, FRM, CND); el motor no trae esas reglas escritas en el código, sino que las **lee del libro**.`));
c.push(P(`El libro es a la vez el modelo de datos: la hoja TABLAS_LOGICAS describe ${H.tablas_logicas} tablas lógicas y el libro completo tiene ${H.hojas_libro} hojas (catálogos, movimientos, cuentas de control, configuración del método y salidas).`));

// ----------------------------------------------------------------------------------------------- 2
c.push(H1("2. Arquitectura del sistema"));
c.push(P("La arquitectura tiene tres decisiones de fondo: **Python es el único motor de cálculo**, **el libro Excel con estructura DBD es la única entrada** (cada empresa usa un adaptador que llena ese formato) y **la interfaz es HTML local**, que solo lee un contrato de resultados y nunca recalcula costos."));
c.push(H2("2.1 Capas"));
c.push(T([
  ["Capa", "Qué hace", "Dónde (líneas)"],
  ["Entrada", "Valida el libro (hojas, columnas, referencias, rangos) con mensajes en castellano; calcula la huella SHA-256", `src/reyna_local/libro_dbd.py (${L["reyna_local/libro_dbd.py"]})`],
  ["Operación", "Registra transacciones según las reglas del libro (TRX, TOP, MET); recibos, respaldo y escritura atómica", `src/reyna_local/motor_espejo.py (${L["reyna_local/motor_espejo.py"]}), store.py (${L["reyna_local/store.py"]})`],
  ["Preparación", "Deriva el kardex a promedio ponderado y el costo de adquisición completo", `src/reyna_local/flujo.py (${L["reyna_local/flujo.py"]})`],
  ["Cálculo", "Reparto por etapas P1–P7 con escalonado y recíproco; naturalezas NORMAL / PÉRDIDA / OCIO", `src/metodos/reparto_etapas.py (${L["metodos/reparto_etapas.py"]})`],
  ["Contrato", "Arma el resultado único (objetos, actividades, serie, estado de resultados, propuestas…) y lo valida", `src/reyna_local/resultados.py (${L["reyna_local/resultados.py"]}), contrato.py (${L["reyna_local/contrato.py"]})`],
  ["Servicio", "Orquesta: valida → prepara → calcula → sella → guarda el JSON", `src/reyna_local/calculo_local.py (${L["reyna_local/calculo_local.py"]})`],
  ["Presentación", "Servidor local, pantallas HTML y exportadores Excel / Word / HTML", `src/reyna_local/__main__.py (${L["reyna_local/__main__.py"]}), exportar.py (${L["reyna_local/exportar.py"]}), web/index.html`],
  ["Analítica", "Decidir, proyección, propuestas, familias, aprendizaje; leen el contrato", `src/reyna_local/decidir.py (${L["reyna_local/decidir.py"]}) y otros`],
], [15, 48, 37]));
c.push(NOTA(`El paquete src/reyna_local tiene ${H.py_reyna_local} módulos y src/metodos ${H.py_metodos}.`));

c.push(H2("2.2 Recorrido de un cálculo"));
c.push(P("Cuando el usuario pide el costo de un mes, `calculo_local.calcular()` hace, en este orden:"));
[
  "**Revisa** el libro con `libro_dbd.validar()`; si hay errores, se detiene y los muestra (nunca corrige en silencio).",
  "**Ordena** los hechos: `flujo.preparar()` deriva el kardex y el costo de adquisición.",
  "**Reparte** por etapas P1–P7 (`reparto_etapas`). Tres controles detienen el cálculo en lugar de imputar en silencio: I1 (cada etapa conserva el total), I8 (un origen con monto cuyo inductor suma cero) y R-52 (un origen con monto sin regla de reparto vigente).",
  "**Publica** el resultado: `resultados.construir()` arma el contrato, se valida contra `contrato.py` y se sella con la huella SHA-256 del libro y del propio resultado.",
  "**Muestra**: las pantallas y los exportadores leen ese JSON; si una cifra cambiara después del sello, el estado pasa de VIGENTE a RESULTADO_ALTERADO.",
].forEach((t) => c.push(B(t)));
c.push(H2("2.3 Ejemplo: SERVITEC, julio de 2025"));
c.push(P("El caso SERVITEC es **sintético**: fue creado para probar el sistema y no representa a una empresa real. Resultado de calcular() en síntesis REAL:"));
const fila = (nom, x) => [nom, n0(x.cantidad), n0(x.md), n0(x.mod), n0(x.cif), n0(x.admin), n0(x.perdida), n0(x.ocio), n0(x.costo_total), n2(x.costo_unitario)];
c.push(T([
  ["Orden", "Cant.", "MD", "MOD", "CIF", "Adm.", "Pérdida", "Ocio", "Costo total", "Unitario"],
  fila("OT-SRV-REB-2025-07", R), fila("OT-SRV-MPR-2025-07", M),
], [24, 7, 9, 9, 9, 8, 8, 7, 10, 9]));
c.push(NOTA(`Ventas del mes ${n0(K.ventas)}, costo total ${n0(K.costo_total)}, margen operativo ${n0(K.margen_operativo)}. El costo total de cada orden es la suma de sus elementos (control de conservación).`));
c.push(H2("2.4 Dos síntesis del mismo cálculo"));
c.push(P("**REAL** carga a la orden todo lo que consumió: MD, MOD, CIF, administración, ventas, financieros, pérdida y ocio (vista gerencial). **CONTABLE** carga solo MD, MOD y CIF normales, como pide la NIC 2 (§13: los costos fijos se asignan con la capacidad normal y lo no asignado es gasto; §16: las pérdidas anormales no son costo del inventario), y manda la pérdida, el ocio y los gastos al estado de resultados, presentado según las categorías de la NIIF 18. El resultado operativo del mes es el mismo en ambas; solo cambia qué se queda en la orden."));

// ----------------------------------------------------------------------------------------------- 3
c.push(H1("3. Límites del modelo"));
c.push(P("Estos límites están declarados en el manual y en las pantallas. Se listan con su consecuencia práctica y el lugar del código donde se ven."));
c.push(T([
  ["Límite", "Qué significa", "Consecuencia para el usuario", "Dónde se ve"],
  ["Costo variable lineal por tramo", "Dentro de cada tramo de cantidad declarado, el costo variable crece en línea recta; fuera de los tramos se proyecta lineal", "Economías o deseconomías de escala que no estén en un tramo declarado no aparecen en la cotización", "reyna_local/tramos_cantidad.py; pedido.py (supuesto de la receta)"],
  ["Plazo en días de capacidad", "El plazo de un pedido se calcula con la capacidad práctica y la carga comprometida, en días de capacidad", "No es una fecha de calendario: falta un calendario laboral aprobado (feriados, turnos)", "reyna_local/plazo_pedido.py; pedido.py (límite declarado)"],
  ["Rango P05–P95 con independencia", "El rango del costo de un pedido suma los intervalos de cada inductor suponiendo que sus errores son independientes", "Si los recursos se mueven juntos (por ejemplo, un alza general de precios), el rango real es más ancho", "reyna_local/pedido.py (límite declarado)"],
  ["Una restricción en Decidir", "Decidir resuelve una sola restricción (un recurso escaso, ordenando por margen por unidad del recurso)", "Con varias restricciones exporta un modelo a Solver; su resultado solo vale dentro de su rango de sensibilidad", "reyna_local/decidir.py; exportar.py (tipo «solver»)"],
  ["Un usuario a la vez", "El código sugerido para una orden nueva no se reserva", "Si dos personas registran a la vez, la clave única rechaza la colisión y el segundo debe reintentar", "reyna_local/correlativo_objeto.py; motor_espejo.py (clave duplicada)"],
  ["SERVITEC es sintético", "El segundo caso fue diseñado para probar el sistema; el otro caso (Frenosa) es real y publicado", "Las cifras de SERVITEC prueban el método, no describen una empresa ni sirven como referencia de mercado", "Manual descriptivo §6"],
], [18, 30, 30, 22]));
c.push(ESP());
c.push(P("Además, el modelo es determinista: el costo real sale de hechos registrados; la proyección y los rangos son estimaciones que se miden contra lo que después ocurre, y el sistema solo recalibra si la mejora se comprueba fuera de muestra."));

// ----------------------------------------------------------------------------------------------- fuentes
c.push(H1("Fuentes"));
[
  "Horngren, C. T., Datar, S. M. y Rajan, M. V. (2012). ~Contabilidad de costos: un enfoque gerencial~ (14.ª ed.). Pearson. Capítulos de costeo por órdenes, ABC y asignación de costos de departamentos de apoyo.",
  "IASB. NIC 2 ~Inventarios~, §10–16. NIIF 18 ~Presentación e información a revelar en los estados financieros~ (2024).",
  "Kaplan, R. S. y Anderson, S. R. (2004). Time-Driven Activity-Based Costing. ~Harvard Business Review~, noviembre, 131–138.",
  "Kaplan, R. S. y Cooper, R. (1998). ~Cost & Effect~. Harvard Business School Press.",
  "Oria, W. (2026). Apuntes del curso GE704W, semana 07: modelos ABC. [Referencia completa POR VERIFICAR; citada así en el código del sistema.]",
  "Reyna, T. MCD (libro), §3.4: evento como transacción consumada. Reyna, T. DBD (libro). [Título completo, editorial y año POR VERIFICAR.]",
  "Repositorio del sistema: src/reyna_local, src/metodos; Manual descriptivo y Etapas del desarrollo (paquete MN 01).",
].forEach((t) => c.push(B(t)));

// ----------------------------------------------------------------------------------------------- notas
c.push(H1("Notas para el autor (no pegar)"));
[
  "**Misión**: se usa la versión 2.1 aprobada (E-041), con el ajuste del dueño del 28/11 (el presupuesto es otro sistema).",
  "**Referencias** de Oria (GE704W) y de los libros MCD/DBD de Reyna: completar título, año y editorial.",
  "**Claves duplicadas.** El manual dice que el motor rechaza claves repetidas; eso vale para lo que crean las transacciones. Un libro **importado** con una orden repetida en OBJETO se acepta hoy y cambia el costo unitario de REB de 2,297.50 a 1,914.58 (pieza 24, libro 05). Otro agente lo corrige antes del 9-dic. Si la corrección no entra, agregar este límite a la sección 3.",
  "**Cifras de pruebas** (562 pruebas en verde, recorrido 30/30) vienen de ETAPAS_DESARROLLO.md y no se volvieron a correr aquí: POR VERIFICAR con la corrida final (pieza 26).",
  "Este documento no copia texto de libros: las definiciones están escritas con palabras propias y citan su fuente.",
].forEach((t) => c.push(B(t)));

const doc = new Document({
  creator: "MN 01", title: "Textos para la Monografía 1",
  styles: { default: { document: { run: { font: FONT, size: 22 } } }, paragraphStyles: [
    { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true, run: { font: FONT, size: 28, bold: true, color: "1D2433" }, paragraph: { spacing: { before: 280, after: 120 }, keepNext: true, outlineLevel: 0 } },
    { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true, run: { font: FONT, size: 24, bold: true, color: "3B4658" }, paragraph: { spacing: { before: 200, after: 80 }, keepNext: true, outlineLevel: 1 } },
    { id: "Heading3", name: "Heading 3", basedOn: "Normal", next: "Normal", quickFormat: true, run: { font: FONT, size: 22, bold: true, color: "5B6474" }, paragraph: { spacing: { before: 140, after: 60 }, keepNext: true, outlineLevel: 2 } },
  ] },
  numbering: { config: [{ reference: "v", levels: [{ level: 0, format: LevelFormat.BULLET, text: "•", alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 400, hanging: 260 } } } }] }] },
  sections: [{ properties: { page: { size: { width: 11906, height: 16838 }, margin: { top: 1440, bottom: 1440, left: 1440, right: 1440 } } },
    headers: { default: new Header({ children: [new Paragraph({ alignment: AlignmentType.RIGHT, children: [new TextRun({ text: "MN 01 · Textos para la monografía · BORRADOR", size: 16, color: "8D95A3" })] })] }) },
    footers: { default: new Footer({ children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ children: ["Página ", PageNumber.CURRENT, " de ", PageNumber.TOTAL_PAGES], size: 16, color: "8D95A3" })] })] }) },
    children: c }],
});
Packer.toBuffer(doc).then((b) => { fs.writeFileSync(process.argv[3], b); console.log("ok"); });
