# -*- coding: utf-8 -*-
"""C41-1 (K1 de CONTRASTE_CLEIN, criterio del Prof. Oria): precisión con MAE, WAPE y sesgo, contra dos modelos ingenuos
con el mismo origen móvil. Serie inventada de 6 meses, dos productos; cuentas hechas a mano.

Reales:      M1   M2   M3   M4   M5   M6
  A         100  110  120  130  140  150
  B          50   50   50   50   50   50
Se evalúan M4, M5 y M6 (historia hasta t−1). Proyección del sistema: M4 A128 B52 · M5 A137 B49 · M6 A152 B50.
Ingenuo último valor: M4 A120 B50 · M5 A130 B50 · M6 A140 B50.
Ingenuo promedio de 3: M4 A(100+110+120)/3=110 B50 · M5 A120 B50 · M6 A130 B50.

Nivel producto (6 filas), error e = real − proyectado; Σ|real| = 130+140+150+50·3 = 570:
  sistema: e = 2, 3, −2 (A) y −2, 1, 0 (B) → Σ|e| = 10 → MAE 10/6 = 1.67; WAPE 10/570 = 1.75 %; sesgo 2/6 = 0.33
  último:  e = 10, 10, 10 y 0, 0, 0       → Σ|e| = 30 → MAE 5;   WAPE 30/570 = 5.26 %;  sesgo 5
  prom 3:  e = 20, 20, 20 y 0, 0, 0       → Σ|e| = 60 → MAE 10;  WAPE 60/570 = 10.53 %; sesgo 10
  gana el sistema por 5.26 − 1.75 = 3.51 puntos.
Nivel mes total: real 180, 190, 200 (Σ 570); sistema 180, 186, 202 → e 0, 4, −2 → MAE 2; WAPE 6/570 = 1.05 %; sesgo 2/3 = 0.67;
  último 170, 180, 190 → e 10 c/u → MAE 10; WAPE 5.26 %; sesgo 10. prom 3 160, 170, 180 → MAE 20; WAPE 10.53 %; sesgo 20.
  gana el sistema por 5.26 − 1.05 = 4.21 puntos.
Producto B solo: sistema Σ|e| = 3 → WAPE 3/150 = 2.00 %; los dos ingenuos aciertan (WAPE 0) → empate de ingenuos, el sistema pierde.
"""
from reyna_local.proyeccion import medir_contra_ingenuos

REALES = {f"2026-0{i}": {"A": a, "B": 50.0} for i, a in enumerate((100.0, 110.0, 120.0, 130.0, 140.0, 150.0), start=1)}
PROY = {"2026-04": {"A": 128.0, "B": 52.0}, "2026-05": {"A": 137.0, "B": 49.0}, "2026-06": {"A": 152.0, "B": 50.0}}


def _filas():
    return [{"periodo": m, "producto": p, "proyectado": v, "real": REALES[m][p]} for m, d in PROY.items() for p, v in d.items()]


def test_mae_wape_sesgo_y_ganador_calculados_a_mano():
    r = medir_contra_ingenuos(_filas(), REALES)
    pro = r["producto"]["modelos"]
    assert r["producto"]["comparables"] == 6 and r["producto"]["sin_historia"] == []
    assert (pro["sistema"]["mae"], pro["sistema"]["wape_pct"], pro["sistema"]["sesgo"]) == (1.67, 1.75, 0.33)
    assert (pro["ultimo_valor"]["mae"], pro["ultimo_valor"]["wape_pct"], pro["ultimo_valor"]["sesgo"]) == (5.0, 5.26, 5.0)
    assert (pro["promedio_3"]["mae"], pro["promedio_3"]["wape_pct"], pro["promedio_3"]["sesgo"]) == (10.0, 10.53, 10.0)
    g = r["producto"]["gana"]
    assert g["modelo"] == "sistema" and g["ventaja_puntos"] == 3.51 and g["sistema_gana"] is True
    mes = r["mes_total"]["modelos"]
    assert (mes["sistema"]["mae"], mes["sistema"]["wape_pct"], mes["sistema"]["sesgo"]) == (2.0, 1.05, 0.67)
    assert (mes["ultimo_valor"]["mae"], mes["ultimo_valor"]["wape_pct"], mes["ultimo_valor"]["sesgo"]) == (10.0, 5.26, 10.0)
    assert (mes["promedio_3"]["mae"], mes["promedio_3"]["wape_pct"], mes["promedio_3"]["sesgo"]) == (20.0, 10.53, 20.0)
    assert r["mes_total"]["gana"]["modelo"] == "sistema" and r["mes_total"]["gana"]["ventaja_puntos"] == 4.21
    b = r["por_cada_producto"]["B"]
    assert b["modelos"]["sistema"]["wape_pct"] == 2.0 and b["modelos"]["ultimo_valor"]["wape_pct"] == 0.0
    assert b["gana"]["modelo"] == "empate" and b["gana"]["ganadores"] == ["ultimo_valor", "promedio_3"]
    assert b["gana"]["sistema_gana"] is False and "no le gana" in b["gana"]["texto"]


def test_falta_de_historia_se_dice_con_texto_y_no_con_cero():
    filas = [{"periodo": "2026-02", "producto": "A", "proyectado": 105.0, "real": 110.0}]
    r = medir_contra_ingenuos(filas, REALES)
    assert filas[0]["ingenuo_ultimo"] == 100.0 and filas[0]["ingenuo_prom3"] is None
    assert "necesita 3" in filas[0]["motivo_ingenuo"]
    assert r["producto"]["comparables"] == 0 and r["producto"]["sin_historia"]
    assert r["producto"]["gana"]["modelo"] is None and r["producto"]["gana"]["texto"].startswith("No se puede decidir")
    assert r["producto"]["sistema_todas_las_filas"]["mae"] == 5.0        # el sistema se mide igual con todas sus filas


def test_wape_indefinido_si_la_suma_real_es_cero():
    reales = {f"2026-0{i}": {"A": 0.0} for i in range(1, 7)}
    filas = [{"periodo": m, "producto": "A", "proyectado": 3.0, "real": 0.0} for m in ("2026-04", "2026-05", "2026-06")]
    r = medir_contra_ingenuos(filas, reales)
    s = r["mes_total"]["modelos"]["sistema"]
    assert s["wape_pct"] is None and "suma de los costos reales es 0" in s["motivo"]
    assert s["mae"] == 3.0 and s["sesgo"] == -3.0                         # sobrestima: sesgo negativo
    assert r["mes_total"]["gana"]["modelo"] is None and "suma de los costos reales es 0" in r["mes_total"]["gana"]["texto"]
