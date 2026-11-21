"""Prueba el ejecutable desde una carpeta aislada usando solo loopback."""

from contextlib import contextmanager
from http.client import HTTPConnection
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import time


@contextmanager
def running(executable, directory, env, log):
    with log.open("wb") as output:
        process = subprocess.Popen(
            [str(executable), "--no-browser"], cwd=directory, env=env,
            stdout=output, stderr=subprocess.STDOUT,
        )
        try:
            deadline = time.monotonic() + 60
            while process.poll() is None and time.monotonic() < deadline:
                text = log.read_text(encoding="utf-8", errors="replace")
                match = re.search(r"Piloto local disponible en http://127\.0\.0\.1:(\d+)", text)
                if match:
                    yield int(match[1])
                    return
                time.sleep(0.1)
            raise RuntimeError("El ejecutable no anunció la dirección local.")
        except Exception:
            print(log.read_text(encoding="utf-8", errors="replace"), flush=True)
            raise
        finally:
            if process.poll() is None:
                if os.name == "nt":
                    # PyInstaller onefile ejecuta el servidor en un proceso hijo.
                    subprocess.run(["taskkill", "/PID", str(process.pid), "/T", "/F"],
                                   stdout=subprocess.DEVNULL, check=True, timeout=10)
                else:
                    process.terminate()
                process.wait(timeout=10)


def request(port, path, expected, data=None):
    client = HTTPConnection("127.0.0.1", port, timeout=10)
    try:
        if data is None:
            client.request("GET", path)
        else:
            client.request("POST", path, json.dumps(data), {"Content-Type": "application/json"})
        response = client.getresponse()
        body = response.read()
        if response.status != expected:
            raise RuntimeError(f"{path} devolvió HTTP {response.status}: {body[:500]!r}")
        return body
    finally:
        client.close()


def verify(executable, fixture, index, directory):
    directory.mkdir()
    isolated_exe = Path(shutil.copy2(executable, directory))
    workbook = Path(shutil.copy2(fixture, directory))
    local_appdata = directory / "Datos del usuario"
    data_dir = local_appdata / "ReynaCostos" / "datos"
    env = {key: value for key, value in os.environ.items() if not key.startswith("PYTHON")}
    env.update({
        "LOCALAPPDATA": str(local_appdata),
        "HTTP_PROXY": "http://127.0.0.1:1",
        "HTTPS_PROXY": "http://127.0.0.1:1",
        "ALL_PROXY": "http://127.0.0.1:1",
        "NO_PROXY": "",
        "PATH": "",
        "PYTHONIOENCODING": "utf-8",
    })

    with running(isolated_exe, directory, env, directory / "primer-arranque.log") as port:
        if request(port, "/", 200) != index.read_bytes():
            raise RuntimeError("La interfaz empaquetada difiere del HTML de origen.")
        if json.loads(request(port, "/api/workspaces", 200)) != {"workspaces": []}:
            raise RuntimeError("La carpeta de prueba debía empezar vacía.")
        workspace = json.loads(request(port, "/api/workspaces", 201, {
            "name": "Prueba del paquete",
            "workbook_path": str(workbook),
        }))
        stored = data_dir / workspace["id"] / "libro.xlsx"
        if not stored.is_file():
            raise RuntimeError(f"El libro no se guardó bajo LOCALAPPDATA: {stored}")

    # C04 debe estar integrado antes de construir el paquete de entrega.
    with running(isolated_exe, directory, env, directory / "calculo.log") as port:
        result = json.loads(request(port, "/api/calcular?sintesis=REAL&periodo=2010-07", 200, {}))
        if result.get("periodo_actual") != "2010-07" or result.get("kpi", {}).get("ventas") != 888730:
            raise RuntimeError("El cálculo de julio no coincide con el caso de referencia.")
        reporte = json.loads(request(port, "/api/exportar?tipo=html", 201, {"resultados": result}))
        html = Path(reporte["ruta"]).read_text(encoding="utf-8")
        if "<html" not in html.lower() or "http://" in html or "https://" in html:
            raise RuntimeError("El HTML generado no es autónomo.")

    with running(isolated_exe, directory, env, directory / "segundo-arranque.log") as port:
        workspaces = json.loads(request(port, "/api/workspaces", 200))["workspaces"]
        if [item["id"] for item in workspaces] != [workspace["id"]]:
            raise RuntimeError("El segundo arranque no recuperó el espacio importado.")

    print("Prueba local aprobada. HTML, API, importación, cálculo REAL, exportación y reapertura del libro.", flush=True)
