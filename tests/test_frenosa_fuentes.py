"""Comprueba que los CSV reproduzcan cada celda de las entradas textuales del JSONL."""
import collections
import csv
import io
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]


def test_csv_coinciden_con_entradas_mensuales_jsonl():
    expected = collections.defaultdict(list)
    headers = {}
    months = set()
    for line in (ROOT / 'docs/fuentes/originales/proyectoPasado.jsonl').read_text(encoding='utf-8').splitlines():
        item = json.loads(line)
        match = re.fullmatch(r'frenosa_datos_entrada_abc_2010_(\d\d)\.xlsx', item['archivo'])
        if not match:
            continue
        month = '2010-' + match.group(1)
        assert month not in months
        months.add(month)
        parts = re.split(r'^--- Hoja: (.*?) ---\s*$', item['contenido'], flags=re.M)
        for i in range(1, len(parts), 2):
            name = parts[i]
            if name in ('README', 'Reglas_Calculo', 'Diccionario', 'Fuentes', 'Modelos_Costeo'):
                continue
            rows = list(csv.reader(io.StringIO(parts[i + 1].strip()), delimiter='|'))
            header = rows[0][:]
            if name == 'Periodo':
                header[header.index('periodo')] = 'periodo_descripcion_fuente'
            if name in headers:
                assert headers[name] == header
            headers[name] = header
            expected[name].extend([month, *row] for row in rows[1:])
    assert months == {f'2010-{i:02}' for i in range(1, 13)}
    files = {p.stem for p in (ROOT / 'datos/frenosa').glob('*.csv')}
    assert files == set(expected)
    for name, rows in expected.items():
        with (ROOT / 'datos/frenosa' / (name + '.csv')).open(encoding='utf-8', newline='') as f:
            actual = list(csv.reader(f))
        assert actual[0] == ['periodo', *headers[name]]
        assert collections.Counter(map(tuple, actual[1:])) == collections.Counter(map(tuple, rows))
