# -*- coding: utf-8 -*-
"""Resolución única de rutas del kit. La raíz es la carpeta padre de kit/.
REYNA_FUENTE manda si existe (entrega en zip: fuente/ queda junto al sistema)."""
import os

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FUENTE = os.environ.get("REYNA_FUENTE") or os.path.join(RAIZ, "fuente")
FUENTE_DIR = "fuente"
# OT-051 (T-166b): la FUENTE del DBD es DBD_Fuente.xlsx (lo único editable); DBD_Documento.xlsx se GENERA; la prosa humana vive en fuente/documental/.
DBD_FUENTE = os.path.join(FUENTE, "DBD_Fuente.xlsx")
DBD_DOCUMENTO = os.path.join(FUENTE, "DBD_Documento.xlsx")
DOCUMENTAL = os.path.join(FUENTE, "documental")
