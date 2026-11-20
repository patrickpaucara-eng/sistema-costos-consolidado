# Transferencia de sesión — Costos ORIA / Sistema de Costos Reyna

## 0. Instrucción de incorporación para Codex
Lee este documento íntegramente y úsalo como contexto inicial de dirección. Centraliza planificación, investigación, auditoría y futura implementación en Codex, sin exigir al usuario actuar de intermediario con ChatGPT. Esta ficha no es autorización de escritura ni una transcripción literal del historial. Distingue requisitos del usuario, propuestas pendientes y evidencias. Confirma las capacidades reales del entorno y presenta un plan breve antes de iniciar una auditoría completa. No interpretes la carga de este archivo como aprobación de cambios.

## 1. Mandato del usuario
- Repositorio privado: https://github.com/patrickpaucara-eng/sistema-costos-reyna ; rama principal main.
- Construir un sistema universal de costos e inteligencia de decisiones, adaptable a distintas industrias, con calidad comercial y rigor académico.
- Fundamento: metodología MCD y DBD de Tino Reyna Monteverde (UNI/FIIS). El proyecto ORIA del profesor es referencia, no una solución para copiar.
- Priorizar practicidad, facilidad de auditoría, rendimiento decente, simplicidad, funcionamiento sin Internet y mantenibilidad.
- El usuario inicialmente exigió Excel como BD; ahora considera insostenible esa solución y la duplicación Python/VBA. Está abierto a cambiar tecnología si la transición se justifica.
- Recuperar las fortalezas de ORIA, del proyecto de su equipo del año anterior y del trabajo de Claude; corregir fragilidades cuando aporte valor.
- El profesor tiene expectativas elevadas; la entrega debe aspirar a uso comercial, no solo demostración académica.
- El usuario tiene autoridad final. Preguntar cuando una incertidumbre material impida avanzar; evitar interrumpir por decisiones operativas reversibles.
- PROHIBIDO modificar el repositorio sin autorización expresa: no editar archivos versionados, crear ramas remotas, commits, PR, fusionar, borrar ni desplegar. Las autorizaciones futuras deben tener alcance explícito.

## 2. Estado conocido y procedencia
Claude desarrolló el sistema y declaró un 93 % de avance, no validado. La dispersión entre ramas impide al usuario auditarlo. ChatGPT y posteriormente Codex reportaron 292 ramas visibles; volver a fijar el inventario y los SHA al inicio de la auditoría.
README de main, leído mediante GitHub: prototipo dirigido por datos, caso palta Hass, v14 pendiente de aprobación. Base Reyna en kit/ (Excel + VBA, poc_config.py), eventos, cierres oficiales, consultas, MANT-PARM, seguridad, log, bitácora, reversa y re-arranque; motor de nueve operaciones de datos. Extensión E-080 en kit/algoritmos/ (Python): filtro con contrato, algoritmos con ficha, escenarios con memoria, tablero gerencial y decisión que retorna como evento.
Comando documentado: cd kit && python3 construir.py (opción --lo para LibreOffice). README declara base 363/363 en Python y LibreOffice, kardex=existencia, repositorio 38/38, metalmecánica 13/13. Son afirmaciones documentales, no resultados reproducidos por ChatGPT.
README de arq/documentos-finales coincidía con main al consultarlo. CLAUDE.md no apareció en la raíz de main. No se realizó auditoría integral ni modificación desde ChatGPT.

## 3. Fuentes y recuperación de conocimiento
El usuario transfirió conocimiento a Claude durante muchas conversaciones. Algunos Markdown quedaron desactualizados. No asumir que el archivo más reciente es correcto. Contrastar instrucciones explícitas, bibliografía, decisiones, commits, código y pruebas.
Materiales visibles en capturas del proyecto Claude, no recibidos como archivos originales en ChatGPT:
- carpeta claude (42 elementos)
- cleinOria.zip (26.8 MB)
- LIBRO COMPLETO DBD.pdf
- LIBRO COMPLETO MCD 2025 (2).pdf
- materialAcademicoOria2026.zip (13.6 MB)
- ProyectoCostosPasadoNOESDOCUM... (nombre incompleto; antecedente del equipo)
- TECNIA Vol.26-n1-Art. 5 y Art. 6
- Enterprise Integration Patterns
- The Data Warehouse Toolkit, 3rd Edition
- Building the Data Warehouse (aparente cuarta edición)
Claude mostraba 52 archivos y 90 % de capacidad de proyecto. El usuario se quedó sin créditos y no sabe exportar los materiales. No fingir acceso ni paralizar la auditoría Git por esta ausencia. Solicitar originales únicamente cuando sean necesarios. Priorizar libros MCD/DBD y proyectos antecedentes; bibliografía de integración y DW es complementaria.
En la captura del libro DBD se lee una introducción que distingue modelo arquitectónico, externo e interno, diseño lógico y físico, optimización y arquitectura del motor de BD. No se dispone del texto completo.
Documentos encontrados en main/docs/:
AUDITORIA_METODOS.md, DECISIONES_SEMANTICA.md, DISENO_F2_F3.md, DISPONIBILIDAD_PILOTO.md, ENMIENDA_MCD_v3.1.md, HISTORIAL_COORDINACION.md, MCD_v3_CONGELADO_2026-10-31.xlsx, arquitectura_objetivo.md, bitacora.md, caso_palta.md, centralizador.md, contrato_metodos.md, decisiones_validadas.md, dic_add.md, dic_g.md, diccionario.md, estrategia_solucion.md, flujo.mmd, funcional.md, guia_pruebas.md, mcd_congelado.md, objetivo.mmd, pendientes_tecnicos.md, principios.md.
No se ha comprobado su contenido completo ni vigencia.

## 4. Visión conceptual (propuesta, no arquitectura aprobada)
El usuario compartió un boceto manuscrito mezclado con apuntes académicos. Se distinguen órdenes de trabajo, procesos, estándar, ABC, presupuestos, punto de equilibrio, decisiones, captura de datos, base, contable, real, proyectado, analítica, gerente e IA. Algunas anotaciones no son legibles con certeza.
Interpretación propuesta por ChatGPT: captura de eventos e importación -> base integrada -> motor de costos -> información contable, real y proyectada -> analítica descriptiva (qué pasó), diagnóstica (por qué), predictiva (qué pasará), prescriptiva (qué hacer) -> gerente evalúa y decide -> retroalimentación mediante eventos.
Pasado: aprender de errores. Presente: controlar. Futuro: anticipar y evaluar alternativas.
La IA debe ser asistencia, no fuente oficial de cálculos. Núcleo determinista, reproducible y auditable; IA opcional para preservar funcionalidad offline. Analizar simulación, optimización y catálogo de decisiones según evidencia y valor. No imponer módulos ni confundir métodos de acumulación, valoración y asignación de costos: estudiar compatibilidad y semántica antes de diseñar.
Nombre SCID (Sistema de Costos e Inteligencia de Decisiones) fue sugerido, no aprobado.

## 5. Tecnología: hipótesis por evaluar
Candidato: SQLite como BD local, Python como único motor de reglas y costos, interfaz local por definir, Excel/CSV como importación/exportación y PDF si corresponde. El antecedente del equipo usaba Excel de importación y SQLite, según el usuario. Se busca evitar implementación duplicada en VBA y Python.
SQLite permite distribución sencilla y transacciones; solo un escritor simultáneo. Evitar compartir directamente el archivo por red. No asumir necesidad de servidor, PostgreSQL, frontend web, data warehouse separado ni microservicios.
Usuario no sabe aún si necesita uso individual o multiusuario. Propuesta provisional: comenzar individual/offline, diseñar límites de componentes que permitan evolución a servidor local cuando la evidencia lo justifique. Comparar costos de transición, instalación, respaldo, restauración, seguridad, trazabilidad, precisión monetaria y rendimiento representativo. Ningún stack está aprobado definitivamente.

## 6. Capacidades reportadas por Codex en su incorporación
- Acceso de lectura al repo privado, 292 ramas, consulta remota HEAD y lectura de main.
- Linux, terminal, Git, Python y red; /workspace sin checkout Git utilizable. Requiere copia temporal fijada a SHA.
- Prueba mínima de delegación realizada; hasta siete agentes concurrentes incluyendo orquestador, según su reporte.
- Subagentes pueden heredar o recibir modelo y esfuerzo explícitos según disponibilidad; probó gpt-6.2-sol con nivel bajo. Verificar opciones reales; no asumir modelos específicos adicionales.
- SQLite en memoria probado, servidor Docker responde, LibreOffice instalado. Compatibilidad real VBA pendiente; Excel nativo requiere entorno apropiado. Pruebas del proyecto y aislamiento de red pendientes.
- No acceso directo a este proyecto de ChatGPT. Usuario decidió evitar actuar de puente y centralizar todo en Codex.

## 7. Gobierno multiagente
Configurar según capacidades confirmadas, no lanzar siete agentes por defecto. Orquestador alto para coordinación; Git/inventario bajo; documentación medio; metodología/ingeniería de costos alto o extra alto; arquitectura y BD alto; programación rutinaria medio; auditor independiente alto. Ajustar por complejidad y presupuesto de uso. Inicialmente hasta tres especialistas más orquestador para auditoría; ampliar solo si reduce trabajo real.
Evitar lecturas redundantes: hashes de commits, árboles y blobs, agrupación de ramas y caché de evidencias. No confundir mismo SHA con similitud funcional ni rama divergente con rama descartable.
Mantener un registro de fuentes, decisiones aprobadas, hipótesis, pendientes y entregables; actualizarlo por hitos. Antes de autorizar escritura, mantenerlo fuera del repo original en espacio de trabajo permitido y entregar copias descargables. No asumir persistencia entre sesiones cloud; comprobarla. Tras autorización evaluar AGENTS.md y configuración versionada de agentes, plan y arquitectura. No crear otro repo sin permiso.
No tocar main directamente durante futura implementación; ramas acotadas, integración revisada, pruebas obligatorias y auditor distinto del autor. No fusionar indiscriminadamente las 292 ramas.

## 8. Plan de trabajo propuesto
Fase 1 (OT-001): auditoría forense y recuperación del conocimiento. Pendiente autorización expresa en Codex.
1. Fijar fecha, refs y SHA de la línea base, inventario completo, agrupación de puntas idénticas, ancestros, integración, divergencias y cambios exclusivos. Registrar límites.
2. Reconstruir cronología y localizar versiones/componentes útiles; identificar divergencias documentación/código, duplicidades Python/VBA, referencias antecedentes y decisiones del usuario. No inferir que toda rama abandonada carece de valor.
3. Auditar arquitectura y lógica de negocio sin alterar archivos versionados; copias temporales locales solo si autorizadas. No ejecutar código no revisado con secretos o acceso innecesario a red.
4. Preparar entregables fuera del repositorio: INVENTARIO_RAMAS.csv, HISTORIAL_PROYECTO.md, CONOCIMIENTO_RECUPERADO.md, MAPA_ARQUITECTURA_ACTUAL.md, CONTRADICCIONES_Y_RIESGOS.md, INDICE_FUENTES.md, RESUMEN_EJECUTIVO.md. Cada hallazgo con rama/SHA/ruta/líneas, evidencia, impacto, certeza y limitaciones.
Fase 2: validar metodología con fuentes originales, comparar ORIA, antecedente y Claude. Matriz de requisitos trazables y criterios de aceptación antes de ponderar avance.
Fase 3: reproducir casos de referencia y pruebas por SHA, separar evidencia Linux/LibreOffice/Excel nativo. Medir integridad, cálculo, trazabilidad, rendimiento y recuperación. Distinguir aprobado, fallido, parcial, no probado y fuera de alcance; no convertir 93 % declarado en avance certificado.
Fase 4: propuesta conceptual y arquitectónica, alternativas, análisis de transición y clasificación conservar/corregir/rediseñar/descartar. Presentar al usuario para aprobación.
Fase 5: plan maestro incremental y migración únicamente con autorización, pruebas de equivalencia y rollback, revisión independiente y documentación.
Fase 6: validación integral y preparación para distribución comercial; no declarar certificación sin evidencia.

## 9. Primera respuesta esperada en Codex
Confirma lectura de esta ficha y capacidad de conservarla durante la sesión. Indica qué información ya tienes en tu sesión y qué falta. Propón un plan eficiente de OT-001 y solicita autorización para comenzar si no existe ya una autorización explícita. No pidas al usuario repetir información disponible. Centraliza la coordinación y entrega avances verificables, sin porcentajes arbitrarios.

## 10. Límites de esta transferencia
Esta ficha sintetiza la conversación de ChatGPT, no importa el estado interno ni el historial íntegro de Claude o Codex. No incluye bibliografía original ni código. Las hipótesis de arquitectura, nombre, organización y priorización son propuestas de ChatGPT, no acuerdos definitivos. No se ha alterado GitHub. El usuario podrá corregir esta ficha y sus restricciones prevalecen.
