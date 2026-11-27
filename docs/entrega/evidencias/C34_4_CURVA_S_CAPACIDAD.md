# C34-4 · Curva S y plazo por capacidad

**Dependencia:** rama apilada sobre `codex/C34-3`; el PR incluye los commits previos aún no integrados.

## Curva S

`costo_por_intervalos` acepta la curva `s` y preserva `pareja`, `inicio` y `final`. Para seis intervalos se aplican los pesos `1-2-3-3-2-1` y se normalizan. Para otro número de intervalos se usa interpolación lineal entre esos puntos y luego se normaliza. Caso manual con 12 horas, tarifa 1 y seis intervalos: costos `[1,2,3,3,2,1]`, total 12. Para tres intervalos, pesos reescalados `[1,3,1]`, costos `[2,6,2]` sobre total 10.

## Capacidad y fecha más temprana

La función recibe carga nueva, capacidad práctica diaria y carga ya comprometida por actividad y día, en unidades iguales. Cada día se reserva primero la carga comprometida; la OT nueva usa el saldo. El plazo total es el máximo de días entre las actividades requeridas.

| Recurso | Carga nueva | Capacidad práctica | OT abierta comprometida | Libre | Días |
|---|---:|---:|---:|---:|---:|
| Soldadura | 85 h | 8 h/día | 2 h/día | 6 h/día | **15** |

Con fecha solicitada a 12 días, el estado es **3 días tarde**. Pruebas propias: `python -m unittest discover -s tests -p 'test_c34_4_curva_s_y_plazo.py' -v`.

## Ambigüedades registradas y límites

Las decisiones provisionales sobre discretización de la curva S, calendario y semántica de carga abierta están en `ordenes/RESPUESTAS_CODEX_24NOV.md`. El caso de aceptación se expresa en días de capacidad, sin convertirlo a fecha calendario. No hay integración que derive reservas diarias desde un libro operativo: no está definido si la medida de una OT abierta representa demanda restante, demanda total o consumo real. Hasta acordar esa semántica, el cotizador debe recibir compromisos explícitos y no inventarlos a partir del estado de la OT.

## Verificación integral de la rama

Las siete pruebas propias terminaron **7/7 OK**. `python tools/verificar.py` terminó **COMPUERTA: VERDE**: 555 pruebas, 1 advertencia y 26 subpruebas pasaron en 804,97 s; el contrato de resultados también pasó. No se editaron pruebas existentes ni los módulos excluidos.
