# -*- coding: utf-8 -*-
"""B7a · Canal CARGA (§9.7 contratos 6 y 8). Python NO escribe en la base: arma tramas para la tabla CARGA
(CAR_TRX, CAR_USR, CAR_TRAMA; formato «VAR=valor;…», líneas separadas por |) y el motor las ejecuta. OT-083."""

_ESC = (("%", "%25"), (";", "%3B"), ("|", "%7C"), ("\n", "%0A"))   # ; y | separan variables y líneas de la trama


def _val(x):
    """Escapa con %XX lo que separa la trama (las claves compuestas llevan «|», p. ej. P4A|ABC1). El motor debe decodificarlo
    (OT-083_dudas.md n.º 2)."""
    s = "" if x is None else str(x)
    for c, e in _ESC:
        s = s.replace(c, e)
    return s


def trama_proponer(usuario, cambios, pca_paq, motivo="H-04"):
    """Una fila CARGA PROPONER por cada cambio; todas con el mismo PCA_PAQ (contrato 5).
    cambios = [{TABLA, CLAVE, COLUMNA, VALOR_NUEVO}]."""
    if not usuario or not pca_paq:
        raise ValueError("trama PROPONER: faltan usuario o PCA_PAQ")
    filas = []
    for c in cambios:
        partes = [("TABLA", c["TABLA"]), ("CLAVE", c["CLAVE"]), ("COL", c["COLUMNA"]), ("VALOR", c["VALOR_NUEVO"]),
                  ("MOTIVO", motivo), ("PCA_PAQ", pca_paq)]
        filas.append({"TRANSACCION": "PROPONER", "USUARIO": usuario, "TRAMA": ";".join(f"{k}={_val(v)}" for k, v in partes)})
    return filas


def trama_aprueba(usuario, pca_paq, decision="A", desde=None):
    """Fila CARGA APRUEBA-PARM que decide el paquete completo (A = aprobar, R = rechazar)."""
    if not usuario or not pca_paq:
        raise ValueError("trama APRUEBA-PARM: faltan usuario o PCA_PAQ")
    return [{"TRANSACCION": "APRUEBA-PARM", "USUARIO": usuario, "TRAMA": f"PCA_PAQ={_val(pca_paq)};DEC={_val(decision)}" + (f";DESDE={_val(desde)}" if desde else "")}]


def trama_seguim(usuario, filas):
    """I-2 (OT-098 V4): filas CARGA @SEGUIM desde filas EST_DECISION {EDE_REF, EDE_OBJ, EDE_PER, EDE_PRED, EDE_REAL, EDE_ERR,
    EDE_ESTADO, EDE_REGLA}. Valores vacíos viajan vacíos (solo válidos con ESTADO = PENDIENTE: lo decide el motor)."""
    if not usuario:
        raise ValueError("trama @SEGUIM: falta el usuario")
    out = []
    for f in filas:
        partes = [("REF", f.get("EDE_REF")), ("OBJ", f.get("EDE_OBJ")), ("PER", f.get("EDE_PER")), ("PRED", f.get("EDE_PRED")),
                  ("REAL", f.get("EDE_REAL")), ("ERR", f.get("EDE_ERR")), ("ESTADO", f.get("EDE_ESTADO") or f.get("ESTADO")),
                  ("REGLA", f.get("EDE_REGLA"))]
        out.append({"TRANSACCION": "@SEGUIM", "USUARIO": usuario, "TRAMA": ";".join(f"{k}={_val(v)}" for k, v in partes)})
    return out


def trama_nivel(usuario, cod, nivel):
    """I-2 (V7): fila CARGA @NIVEL que baja la autonomía de una entrada del catálogo PROPUESTA (AUT-01)."""
    if not usuario or not cod:
        raise ValueError("trama @NIVEL: faltan usuario o código")
    return [{"TRANSACCION": "@NIVEL", "USUARIO": usuario, "TRAMA": f"PRO={_val(cod)};NIVEL={_val(nivel)}"}]


def _tipar(t, numericos):
    """Los números de la trama decodificada llegan como texto: se convierten como lo haría ParseValor (punto decimal)."""
    out = dict(t)
    for k in numericos:
        v = out.get(k)
        if v not in (None, ""):
            try:
                out[k] = float(v) if "." in str(v) else int(v)
            except ValueError:
                pass
    return out


def _decodificar(trama):
    """«VAR=valor;…» → {VAR: valor} deshaciendo el escape %XX de _val."""
    out = {}
    for parte in str(trama).split(";"):
        if "=" in parte:
            k, v = parte.split("=", 1)
            for c, e in reversed(_ESC):
                v = v.replace(e, c)
            out[k.strip()] = v
    return out


def _ruta_base():
    import os
    raiz = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    for c in (os.environ.get("REYNA_BASE_V41") or "", os.path.join(raiz, "kit", "entrega", "Sistema_Costos", "Sistema_Costos.xlsx")):
        if c and os.path.exists(c):
            return c
    raise FileNotFoundError("canal_carga.ejecutar: falta la base generada (kit/construir.py) o REYNA_BASE_V41")


def trama_invproc(usuario, filas_k9):
    """OT-095: filas CARGA @INVPROC desde las filas K9 {IPR_PER, IPR_OBJ, IPR_ELE, IPR_VAL, IPR_EMP}."""
    if not usuario:
        raise ValueError("trama @INVPROC: falta el usuario")
    out = []
    for f in filas_k9:
        partes = [("PER", f["IPR_PER"]), ("OBJ", f["IPR_OBJ"]), ("ELE", f["IPR_ELE"]), ("VAL", f["IPR_VAL"]), ("EMP", f["IPR_EMP"])]
        out.append({"TRANSACCION": "@INVPROC", "USUARIO": usuario, "TRAMA": ";".join(f"{k}={_val(v)}" for k, v in partes)})
    return out


def ejecutar(filas, ruta=None, motor=None):
    """Ejecuta las filas CARGA con el espejo del motor (mismas reglas que ProcesarCarga de ui.bas: @PROPONER/@RESOLVER)
    sobre una copia en memoria de la base y devuelve CAR_RES por fila. APRUEBA-PARM decide el paquete por PCA_PAQ."""
    from motor_espejo import Motor
    m = motor or Motor(ruta or _ruta_base())
    res = []
    for f in filas:
        t = _decodificar(f.get("TRAMA", "")); usr = f.get("USUARIO", "")
        if f["TRANSACCION"] == "PROPONER":
            r = m.proponer(t.get("TABLA"), t.get("CLAVE"), t.get("COL"), t.get("VALOR"), usr, t.get("MOTIVO", ""), t.get("PCA_PAQ", ""), t.get("PCA_PROP", "") or t.get("PROP", ""))
        elif f["TRANSACCION"] == "APRUEBA-PARM":
            pend = [x for x in m.T["PARAM_CAMBIO"]["r"] if x[10] == t.get("PCA_PAQ") and x[7] == "P"]
            pend = pend or [x for x in m.T["PARAM_CAMBIO"]["r"] if x[10] == t.get("PCA_PAQ") and x[7] == "S"]     # I-3: también pospuestas
            r = m.resolver(pend[0][0], t.get("DEC", "A"), usr, t.get("DESDE"), t.get("MOTIVO", "")) if pend else "ERROR: " + m.mensaje("MSG-PCA")
        elif f["TRANSACCION"] == "@INVPROC":
            r = m.invproc(t, usr)
        elif f["TRANSACCION"] == "@SEGUIM":
            r = m.seguim(_tipar(t, ("REF", "PRED", "REAL", "ERR")), usr)
        elif f["TRANSACCION"] == "@NIVEL":
            r = m.nivel(t, usr)
        else:
            r = f"ERROR: transacción {f['TRANSACCION']} no admitida por el canal"
        res.append({"TRANSACCION": f["TRANSACCION"], "USUARIO": usr, "CAR_RES": r})
    return res
