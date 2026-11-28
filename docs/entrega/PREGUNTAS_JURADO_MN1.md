# 25 preguntas difíciles del jurado · Monografía 1 (sistema de costos ABC)

Respuestas cortas, basadas en lo que el sistema hace hoy. Estado al **28-nov-2026**: la orden de correcciones de la auditoría (OT-C38) **aún no está unida**; las respuestas 9, 10 y 11 dicen qué es cierto hoy y qué cambia cuando se una. Cifras de la última compuerta verde: **574 pruebas** (`python tools/verificar.py`). Si una cifra cambia en la corrida final, se actualiza aquí y en el informe de pruebas.

## A. Método

**1. ¿Por qué ABC y no un reparto con una sola base (por ejemplo, horas de mano de obra)?**
Porque los productos no consumen costos directamente: consumen actividades, y las actividades consumen recursos. El sistema acumula los costos indirectos en centros y actividades y los carga a cada orden según el inductor de cada actividad (Kaplan y Cooper, 1998; Oria, GE704W). Con una sola base, una orden que usa poco taller pagaría igual que una que lo usa mucho.

**2. ¿Qué metodología sigue y de quién es?**
El reparto por etapas P1–P7 es el ABC escalonado enseñado por W. Oria en GE704W. El diseño de datos y la forma de describir la operación (misión, funciones, eventos) siguen los libros MCD y DBD de Tino Reyna.

**3. ¿Qué son las «dos matrices de Oria»?**
La matriz de configuración (hoja `REGLA_REPARTO`: en qué etapa y con qué inductor se reparte cada origen) y la matriz de cálculo (hoja `MEDIDA`: cuánto inductor consumió cada destino en el mes). La regla siempre es la misma: monto del destino = monto del origen × medida del destino ÷ suma de medidas.

**4. ¿Escalonado o recíproco? ¿Por qué recíproco?**
En el escalonado el costo solo baja; el recíproco reconoce que dos centros de apoyo se prestan servicios entre sí y resuelve el sistema `N = (I − P)⁻¹`. Oria lo considera el método preferible y el dueño lo adoptó como regla el 23-nov. Si no hay servicios mutuos, da lo mismo que el escalonado.

**5. ¿SERVITEC demuestra que el recíproco funciona?**
No. SERVITEC tiene un solo centro productivo: todo el costo termina allí con cualquier método de reparto entre centros de apoyo, así que no distingue un método de otro. El recíproco y el escalonado se prueban con `tests/test_modelo3_oria.py`, que compara con cuentas hechas a mano.

**6. ¿Qué distingue costo del producto de gasto del periodo?**
La naturaleza del monto: NORMAL, PÉRDIDA (merma en exceso, rechazo sin reproceso) u OCIO (capacidad práctica no usada). En la síntesis CONTABLE solo MD, MOD y CIF normales quedan en la orden (NIC 2 §13 y §16); pérdida, ocio y gastos van al estado de resultados. La síntesis REAL carga todo a la orden para uso gerencial.

**7. Si REAL y CONTABLE cargan cosas distintas, ¿cuál es el resultado verdadero?**
Los dos. El resultado operativo del mes es el mismo en ambas (en SERVITEC julio: ventas 38,000, costo 28,140, margen 9,860); solo cambia qué parte se queda en la orden y qué parte se va al periodo.

## B. Confiabilidad de las cifras

**8. ¿Cómo sabe que el cálculo es correcto?**
Hay un oráculo independiente: `oraculo_SERVITEC.xlsx` rehace el costo de julio con fórmulas de Excel visibles, etapa por etapa, y se compara con el motor por orden, elemento y flecha. La diferencia es 0.00 en las dos órdenes (REB 22,975 y MPR 5,165). Además hay 574 pruebas automáticas y un recorrido de punta a punta por la API.

**9. ¿El motor puede perder costos sin avisar?**
Hoy sí, en cuatro casos que la auditoría independiente confirmó contra el motor real: un elemento de costo mal escrito se descarta (S1), una línea con monto pero sin costo unitario vale 0 (S2), una compra sin monto entra al kardex a 0 (S3) y un exceso de merma mayor que el consumo mueve costo a otra orden (S4). Cada caso tiene un control sin defecto que pasa, así que el escenario es válido. OT-C38 los convierte en rechazos con hoja, fila y valor; no están unidos todavía.

**10. ¿No hay un control de conservación?**
Sí: «suma de recursos = suma del costo de las órdenes». Pero la auditoría mostró que no detecta lo que se pierde antes de entrar al reparto (S6): con S1, S2 o S3 sigue dando OK. OT-C38-5 agrega un control independiente «registrado en el libro = entrado al reparto», por elemento.

**11. ¿Qué pasa si el libro de entrada trae datos malos?**
`validar()` rechaza con mensaje en castellano, hoja y fila, sin traza técnica, en cuatro de los ocho libros defectuosos probados (hoja borrada, celdas vacías, texto en un monto, archivo truncado). Tres defectos pasan hoy sin aviso: fechas al revés (04), código de orden duplicado (05, el más grave: el costo unitario de REB baja de 2,297.50 a 1,914.58) y criterio de reparto en cero (06; este lo frena `calcular()` con la regla I8, pero no al cargar). Estos tres no figuran en las líneas de OT-C38.

**12. ¿Quién garantiza que las pantallas no recalculan?**
El diseño: pantallas y exportadores solo leen un resultado único (contrato JSON), validado contra `contrato.py` y sellado con SHA-256 del libro y del resultado. Si una cifra cambia después del sello, el estado pasa de VIGENTE a RESULTADO_ALTERADO.

**13. ¿Se puede falsificar un cierre aprobado?**
Hoy, en parte. La huella protege las cifras (una cifra alterada da ALTERADO), pero no cubre el estado ni el historial de aprobaciones (S7): se puede editar el JSON a «REVISADO» y la gerencia lo aprueba sin revisión de contabilidad. OT-C38-7 hace que la huella incluya estado e historial.

**14. ¿Qué tan rápido es y qué pasa con muchas órdenes?**
En la auditoría, 50 órdenes tardaron entre 2.8 y 3.6 s según la corrida y el trabajo creció en forma lineal (31 llamadas con 2 órdenes, 411 con 50; S9, severidad baja); es lo máximo que se midió. OT-C38-9 prevé medir con 100 a 400 órdenes y optimizar solo si 200 órdenes superan 30 s.

## C. Datos y arquitectura

**15. ¿Por qué un libro Excel como única entrada?**
Porque separa el sistema de cada ERP: cada empresa usa un adaptador que llena el formato DBD (como el de Frenosa) y el sistema valida el libro completo antes de aceptarlo. Python es el único motor de cálculo; Excel solo guarda datos y reglas, y el sistema no reemplaza al ERP.

**16. ¿Qué es un «evento» en el sistema?**
Una transacción consumada, como la define Reyna (MCD, §3.4): un hecho ocurrido, que no se edita ni se borra; un error se corrige con otro evento. El libro de SERVITEC define 47 transacciones: 26 en línea (las registra el usuario) y 21 por lote (las corre el cierre).

**17. ¿Los datos de SERVITEC son reales?**
No. SERVITEC es un caso sintético creado para probar el sistema; sus cifras prueban el método, no describen una empresa. El caso real es Frenosa (Cherres Juárez, 2010, PUCP), publicado.

**18. ¿Funciona sin internet?**
Sí. El ejecutable de Windows incluye Python, abre un servidor solo local en `127.0.0.1` y guarda los datos en `%LOCALAPPDATA%\ReynaCostos\datos`. El paquete trae `SHA256SUMS.txt` para comprobar los archivos. La prueba guiada está en `GUION_PRUEBA_DUENO.md`.

**19. ¿Por qué no hay base de datos relacional ni almacén de datos?**
Decisión del dueño para esta entrega: el libro DBD es la única entrada y el estado vive en archivos locales con escritura atómica y respaldo. SQLite queda para después de la entrega. No hay almacén de datos: el planeamiento (MN 02) solo leerá el contrato publicado de costos.

## D. Analítica y decisiones

**20. ¿Qué tan buena es la proyección?**
El sistema mide su propia precisión contra lo que ocurrió y la compara con dos modelos ingenuos (último valor real y promedio de los 3 últimos). Resultado honesto que informa el PR #60 (C41-1, todavía sin unir; cifras del PR, no re-medidas aquí): en el mes total el sistema **no le gana** al ingenuo: SERVITEC WAPE 4.59 % del sistema contra 1.43 % del último valor; Frenosa 6.09 % contra 4.50 %. Se declara en la monografía; la orden C41-5, también pendiente, hará que el método vigente sea el de menor error fuera de muestra.

**21. ¿Qué hace «Aprendizaje» y por qué no se descontrola?**
Recalibra estándares y umbrales solo si la mejora se comprueba fuera de muestra y el cambio es de 20 % o menos; si no, pide aprobación. Nunca toca el costo real.

**22. ¿Decidir optimiza con varias restricciones?**
No: resuelve una sola restricción, ordenando por margen unitario por unidad del recurso escaso. Con varias, exporta un modelo a Solver y su resultado solo vale dentro de su rango de sensibilidad. Si falta la capacidad (CAP) o una venta, la pantalla lo dice y pide el dato; no inventa.

**23. ¿En qué se equivoca la cotización?**
Tres límites declarados: el costo variable es lineal dentro de cada tramo de cantidad declarado; el rango P05–P95 suma intervalos suponiendo errores independientes (si los recursos suben juntos, el rango real es más ancho); y el plazo se da en días de capacidad, no en fechas, porque falta un calendario laboral aprobado.

**24. ¿Cuántos usuarios soporta?**
Uno a la vez. El código sugerido para una orden nueva no se reserva: si dos personas registran a la vez, la clave única rechaza la colisión y el segundo reintenta.

**25. ¿Qué no está hecho?**
Corregir los defectos de la auditoría (OT-C38), los tres defectos de carga de la pregunta 11, integrar los tramos de cantidad al Pedido (se cortó por la regla de recorte: el costo por tramos es por recurso y el Pedido valora por actividad, y unirlos exige evitar doble cómputo; el cálculo por recurso existe y está probado), el contrato de costos para planeamiento y la construcción de MN 02. Todo lo no hecho está declarado en el manual y en las pantallas.
