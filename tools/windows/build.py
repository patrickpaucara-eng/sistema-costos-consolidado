"""Compila el ZIP portable en Windows x64 con CPython 3.12.10.

Ejecuta python tools/windows/build.py desde la raíz del repositorio.
"""

from hashlib import sha256
import os
from pathlib import Path
import shutil
import subprocess
import sys
import sysconfig
from tempfile import TemporaryDirectory
import venv
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo

from smoke import verify


TOOLS = Path(__file__).resolve().parent
ROOT = TOOLS.parents[1]
SOURCE = ROOT / "src" / "reyna_local"
INDEX = SOURCE / "web" / "index.html"
DESTINATION = ROOT / "dist" / "ReynaCostos-Windows-x64.zip"
PYTHON_VERSION = (3, 12, 10)
SOURCE_DATE_EPOCH = "1735689600"
ZIP_TIMESTAMP = (2025, 1, 1, 0, 0, 0)


def build(work):
    source = work / "source"
    source.mkdir()
    shutil.copy2(ROOT / "pyproject.toml", source)
    shutil.copytree(SOURCE, source / "src" / "reyna_local",
                    ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "*.pyo"))
    launcher = Path(shutil.copy2(TOOLS / "reyna_windows.py", work))

    environment = work / "venv"
    venv.EnvBuilder(with_pip=True).create(environment)
    python = environment / "Scripts" / "python.exe"
    env = {key: value for key, value in os.environ.items()
           if not key.startswith(("PYTHON", "PIP_"))}
    env.update({
        "PIP_CONFIG_FILE": os.devnull,
        "PYINSTALLER_CONFIG_DIR": str(work / "cache"),
        "PYTHONHASHSEED": "0",
        "SOURCE_DATE_EPOCH": SOURCE_DATE_EPOCH,
    })
    subprocess.run([
        python, "-m", "pip", "install", "--index-url", "https://pypi.org/simple",
        "--disable-pip-version-check", "--no-cache-dir", "--only-binary=:all:", "--no-deps",
        "--force-reinstall", "--require-hashes", "-r", TOOLS / "requirements-build.txt",
    ], cwd=work, env=env, check=True)
    subprocess.run([
        python, "-m", "pip", "install", "--no-index", "--no-build-isolation", "--no-deps", source,
    ], cwd=work, env=env, check=True)
    subprocess.run([python, "-m", "pip", "check"], cwd=work, env=env, check=True)

    output = work / "bin"
    assets = []
    for name in ("src", "casos", "fuente", "datos", "tools"):
        assets.extend(["--add-data", f"{ROOT / name}{os.pathsep}{name}"])
    for name in ("metodos", "analitica", "analitica2", "casos"):
        assets.extend(["--add-data", f"{ROOT / "src" / name}{os.pathsep}{name}"])
    hidden = []
    for module in ("reyna_local.resultados", "reyna_local.analisis", "puerto_lectura", "integra_env", "rutas", "metodos.reparto_etapas", "reyna_local.calculo_local", "reyna_local.flujo", "reyna_local.libro_dbd", "reyna_local.raiz", "defusedxml"):
        # C04 añade calculo_local; se incorpora al integrar esa orden.
        if module == "reyna_local.calculo_local" and not (SOURCE / "calculo_local.py").exists():
            continue
        hidden.extend(["--hidden-import", module])
    subprocess.run([
        python, "-m", "PyInstaller", "--noconfirm", "--clean", "--onefile", "--console", "--noupx",
        "--name", "ReynaCostos", "--collect-data", "reyna_local", "--paths", ROOT / "src", *assets, *hidden, "--distpath", output,
        "--workpath", work / "pyinstaller", "--specpath", work, launcher,
    ], cwd=work, env=env, check=True)
    return output / "ReynaCostos.exe"


def bundle(destination, files):
    destination.parent.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(dir=destination.parent) as staging:
        archive_path = Path(staging) / destination.name
        with ZipFile(archive_path, "w") as archive:
            sums = []
            for path in files:
                data = path.read_bytes()
                sums.append(f"{sha256(data).hexdigest()}  {path.name}\n")
                archive.writestr(ZipInfo(path.name, ZIP_TIMESTAMP), data, ZIP_DEFLATED)
            archive.writestr(ZipInfo("SHA256SUMS.txt", ZIP_TIMESTAMP), "".join(sums), ZIP_DEFLATED)
        archive_path.replace(destination)


def main():
    if (sys.implementation.name != "cpython" or sys.version_info[:3] != PYTHON_VERSION
            or sysconfig.get_platform() != "win-amd64"):
        raise SystemExit("Ejecuta este script en Windows x64 con CPython 3.12.10 de 64 bits.")
    with TemporaryDirectory(prefix="reyna-windows-") as temp:
        work = Path(temp)
        executable = build(work)
        verify(executable, ROOT / "tests" / "fixtures" / "ola1" / "Sistema_Costos.xlsx",
               INDEX, work / "prueba aislada")
        bundle(DESTINATION, [executable, INDEX, TOOLS / "INICIO.txt"])
    print(f"Paquete listo en {DESTINATION}")


if __name__ == "__main__":
    main()
