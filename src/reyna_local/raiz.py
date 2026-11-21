"""Raíz de los recursos (casos, datos, fuente): la carpeta del repositorio o, en el EXE, la carpeta temporal de PyInstaller."""
import sys
from pathlib import Path

RAIZ = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parents[2]))
