#!/usr/bin/env bash
set -euo pipefail
cd /workspace/work/ot001
case_ref=$1
repo_tree=$2
image=$3
tar -cf - "$repo_tree" wheels comprobar_valuacion.py | docker run --rm -i --network none --read-only --cap-drop=ALL --security-opt=no-new-privileges --user=65534:65534 --pids-limit=192 --memory=2g --cpus=2 --tmpfs /tmp:rw,nosuid,nodev,size=768m,mode=1777 "$image" env -i PATH=/usr/local/bin:/usr/bin:/bin HOME=/tmp TMPDIR=/tmp LC_ALL=C.UTF-8 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 sh -c '
set -eu
cd /tmp
tar --no-same-owner -xf -
python -m venv /tmp/audit-venv
export PATH=/tmp/audit-venv/bin:$PATH
python -m pip --disable-pip-version-check install --no-index --no-cache-dir --find-links=/tmp/wheels pytest==8.4.2 openpyxl==3.1.5
for wheel in /tmp/wheels/*.whl; do sha256sum "$wheel"; done
python -V
python -c "import socket; print(socket.if_nameindex()); assert [n for _,n in socket.if_nameindex()] == [\"lo\"]; s=socket.socket(); s.settimeout(1); assert s.connect_ex((\"1.1.1.1\",443)) != 0"
cd "$1"
if test -f .git/HEAD; then git read-tree HEAD; git status --porcelain; fi
set +e
if command -v soffice >/dev/null; then soffice --version; fi
if command -v git >/dev/null; then git --version; git rev-parse HEAD; fi
echo "=== pytest del árbol recibido ==="
python -m pytest -q -r a -p no:cacheprovider pruebas; echo "EXIT_PYTEST=$?"
echo "=== sonda de identidad por empresa ==="
python /tmp/comprobar_valuacion.py "$PWD"; echo "EXIT_SONDA=$?"
if test -x /usr/bin/python3 && test -d pruebas/I2b; then
 echo "=== simulación bajo Python de sistema ==="
 /usr/bin/python3 -V
 PYTHONPATH=/tmp/audit-venv/lib/python3.11/site-packages /usr/bin/python3 -m pytest -q -p no:cacheprovider pruebas/I2b/test_I2b_lecciones.py -k regresion_simulacion; echo "EXIT_SIM_PY_SISTEMA=$?"
fi
echo "=== construcción estricta desde DBD ==="
(cd kit && python construir.py --entrega); echo "EXIT_BUILD=$?"
echo "=== regeneración independiente en modo diseño ==="
(cd kit && python construir_desde_b.py); echo "EXIT_DBD_DISENO=$?"
if test -f kit/salida_b/informe_diseno.txt; then
 echo "=== informe de regeneración ==="
 cat kit/salida_b/informe_diseno.txt
fi
echo "=== regresión histórica directa ==="
(cd kit && python motor_espejo.py salida_b/Sistema_Costos.xlsx); echo "EXIT_HISTORIA=$?"
echo "=== oráculo ENVASE ==="
python informes/V41/integra_env.py; echo "EXIT_ORACULO=$?"
if command -v soffice >/dev/null; then
 echo "=== LibreOffice/UNO usando el adaptador del repositorio ==="
 (cd kit && mkdir -p salida && timeout -k 5 60 /usr/bin/python3 -u lo/probar_en_libreoffice.py salida_b/Sistema_Costos.xlsx); echo "EXIT_LO=$?"
fi
' sh "$repo_tree" > "PRUEBAS_$case_ref.log" 2>&1
