#!/usr/bin/env bash
set -euo pipefail
cd /workspace/work/ot001
tar -cf - main/kit main/fuente main/informes/I5 ola1/kit/metodos ola1/kit/rutas.py ola1/fuente wheels comprobar_valuacion.py | docker run --rm -i --network none --read-only --cap-drop=ALL --security-opt=no-new-privileges --user=65534:65534 --pids-limit=64 --tmpfs /tmp:rw,nosuid,nodev,size=256m,mode=1777 python:3.11-slim env -i PATH=/usr/local/bin:/usr/bin:/bin HOME=/tmp sh -c '
set -eu
cd /tmp
tar --no-same-owner -xf -
python -m venv /tmp/audit
. /tmp/audit/bin/activate
python -m pip --disable-pip-version-check install --no-index --no-cache-dir --find-links=/tmp/wheels openpyxl==3.1.5
python comprobar_valuacion.py /tmp/main
python comprobar_valuacion.py /tmp/ola1
cd main
python -c "from zipfile import ZipFile; from pathlib import Path; z = ZipFile(\"informes/I5/PRUEBA_I5.zip\"); Path(\"/tmp/I5.xlsx\").write_bytes(z.read(\"PRUEBA_I5/Sistema_Costos.xlsx\"))"
python kit/instalador/comparar_paridad.py informes/I5/paridad_excel_dueno.csv /tmp/I5.xlsx --carga
'
