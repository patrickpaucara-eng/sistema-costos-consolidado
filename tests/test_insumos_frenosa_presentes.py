"""Las entradas de Frenosa necesarias para reproducir el cálculo deben distribuirse con el proyecto."""
from pathlib import Path


def test_supuestos_operativos_frenosa_estan_disponibles():
    raiz = Path(__file__).resolve().parents[1]
    assert (raiz / 'datos/frenosa_supuestos/Gastos_Operativos_SUPUESTOS.csv').is_file(), (
        'Falta el archivo de supuestos operativos requerido por el generador de Frenosa.'
    )
