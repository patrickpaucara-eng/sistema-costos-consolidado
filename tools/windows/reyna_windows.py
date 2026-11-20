"""Punto de entrada del ejecutable portable."""

import argparse
import os
from pathlib import Path
import sys

from reyna_local.__main__ import main as serve


def main():
    parser = argparse.ArgumentParser(description="Abre el Sistema de Costos Reyna.")
    parser.add_argument("--no-browser", action="store_true", help="Solo muestra la dirección local en la consola.")
    args = parser.parse_args()

    local_appdata = os.environ.get("LOCALAPPDATA")
    if local_appdata:
        data_dir = Path(local_appdata) / "ReynaCostos" / "datos"
        print(f"Carpeta de datos: {data_dir}", flush=True)
        options = ["--data-dir", str(data_dir), "--port", "0"]
        if not args.no_browser:
            options.append("--open-browser")
        result = serve(options)
    else:
        print("Windows no indicó la carpeta de datos del usuario (LOCALAPPDATA).", file=sys.stderr)
        result = 1

    if result and not args.no_browser and sys.stdin is not None and sys.stdin.isatty():
        input("Presiona Entrar para cerrar.")
    return result


if __name__ == "__main__":
    raise SystemExit(main())
