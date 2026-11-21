"""Uso: python tools/codigo_a_word.py ruta-de-salida.docx"""
import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from reyna_local.codigo_fuente import generar_word

parser = argparse.ArgumentParser(description='Exporta código fuente del proyecto a Word.')
parser.add_argument('salida', type=Path)
args = parser.parse_args()
generar_word(args.salida, ROOT)
print(args.salida)
