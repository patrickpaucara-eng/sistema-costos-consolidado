import json
from pathlib import Path
from reyna_local.exportar import exportar

ROOT = Path(__file__).resolve().parents[1]


def test_ocho_paginas_imprimibles_con_kpi_del_contrato(tmp_path):
    r = json.loads((ROOT / 'datos/resultados/frenosa_2010-12_REAL.json').read_text())
    result = exportar(r, 'presentacion', tmp_path)
    assert result.suffix == '.html'
    data = result.read_text(encoding='utf-8')
    assert data.count('<section>') == 8
    assert f"{r['kpi']['ventas']:,.2f}" in data
    assert '@media print' in data
    assert 'http://' not in data and 'https://' not in data
