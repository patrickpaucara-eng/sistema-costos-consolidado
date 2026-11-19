# -*- coding: utf-8 -*-
"""Motor espejo: interpreta la configuración del LIBRO (no de poc_config) con la misma semántica que motor.bas."""
import sys, os
from decimal import Decimal as D, ROUND_HALF_UP
from openpyxl import load_workbook

import math
def red(x, n):   # mismo redondeo que motor.bas: mitad hacia arriba, con tolerancia 1e-9
    f = 10 ** int(n); x = float(x)
    return math.floor(x * f + 0.5 + 1e-9) / f if x >= 0 else -math.floor(-x * f + 0.5 + 1e-9) / f
def norm(v):
    if v is None or v == "": return ""
    if isinstance(v, (int, float)): return repr(float(v))
    s = str(v).strip()
    try: return repr(float(s))
    except ValueError: return s
def num(v):
    if v is None or v == "": return 0.0
    return float(v)

def texto_num(x):   # OT-060: numero -> texto estable, igual que NumTexto de motor.bas: 9 decimales, sin ceros finales, punto decimal, sin exponente
    x = float(x)
    if abs(x) >= 1e15: raise Error("Número fuera de rango para CONCATENA")
    t = f"{x:.9f}".rstrip("0").rstrip(".")
    return "0" if t in ("", "-0") else t
def texto_valor(v):   # vacio -> "", numero -> texto_num, texto -> tal cual
    if v is None: return ""
    if isinstance(v, (int, float)) and not isinstance(v, bool): return texto_num(v)
    return str(v)

class Error(Exception): pass
PROF_MAX = 32   # OT-052: niveles máximos de operaciones anidadas (SI/PARACADA/operación); idéntico en motor.bas

def clave_cifrada(u, clave):
    """Igual que ClaveCifrada (motor.bas): huella SHA-256 de USUARIO:clave (UTF-8)."""
    import hashlib
    return "SHA256:" + hashlib.sha256(f"{str(u).upper()}:{clave}".encode("utf-8")).hexdigest()

def login(m, u, clave):
    """Espejo de Login (ui.bas)."""
    f = [r for r in m.T["USUARIO"]["r"] if str(r[0]) == str(u).upper()]
    return bool(f) and f[0][m.col("USUARIO", "USU_CLAVE")] == clave_cifrada(u, clave)

class Motor:
    def __init__(self, ruta):
        wb = load_workbook(ruta)
        self.T = {}
        for ws in wb.worksheets:
            rows = list(ws.iter_rows(values_only=True))
            if not rows or not rows[0] or rows[0][0] is None: continue
            hdr = [h for h in rows[0] if h is not None]
            self.T[ws.title] = dict(h=hdr, r=[list(r[:len(hdr)]) for r in rows[1:] if r and r[0] not in (None, "")])
        self.usr = self.perfil = ""; self.pend = None
    def reiniciar(self):
        """Estado inicial de la prueba: vacía el parque y repone la semilla (hojas SEM_*), según TABLAS_LOGICAS."""
        for fila in self.T.get("TABLAS_LOGICAS", {"r": []})["r"]:
            nom, tipo = fila[0], fila[1]
            if tipo == "PARQUE": self.T[nom]["r"] = []
            elif tipo == "PARQUE-SEMILLA": self.T[nom]["r"] = [list(r) for r in self.T["SEM_" + nom]["r"]]
    # ---- acceso
    def col(self, t, c):
        try: return self.T[t]["h"].index(c)
        except ValueError: raise Error(f"Columna {c} no existe en {t}")
    def filas(self, t, c, v, orden=None):
        i = self.col(t, c); rs = [r for r in self.T[t]["r"] if norm(r[i]) == norm(v)]
        if orden: rs.sort(key=lambda r: num(r[self.col(t, orden)]))
        return rs
    def setc(self, t, row, c, v):
        i = self.col(t, c); self.undo.append((t, row, i, row[i])); row[i] = v
    # ---- trama
    def get(self, k):
        if k not in self.tr: raise Error(f"Variable no definida: {k}")
        return self.tr[k]
    def val(self, ori, v):
        if ori == "VAR": return self.get(v)
        if ori == "LIT": return v
        if ori == "VAROPC": return self.tr.get(v, "")
        if v == "#USR": return self.usr
        raise Error(f"Origen desconocido {ori} {v}")
    def plantilla(self, c):
        while "{" in c:
            a = c.index("{"); b = c.index("}"); c = c[:a] + str(self.get(c[a + 1:b])) + c[b + 1:]
        return c
    # ---- ejecución
    def ejecutar(self, trx, trama, usr, lineas=None):
        """Un evento = una transacción. lineas: lista de tramas de línea; las operaciones U corren solo en la 1.ª línea
        y lo que crean (p. ej. EVE_NUM) se hereda a las demás; si cualquier línea falla se revierte el evento completo."""
        self.recuperar()                                    # re-arranque: nada se aplica sobre un pendiente sin confirmar
        log = [len(self.T["LOG_TRX"]["r"]) + 1, trx, usr, "I", "", 0]          # registro log (DBD §4.2.4): I → O → A, o E
        self.T["LOG_TRX"]["r"].append(log)                                  # fuera de la reversa: sobrevive al error
        u = [r for r in self.T["USUARIO"]["r"] if r[0] == usr]
        if not u:
            log[3], log[4] = "E", "usuario no existe"; return "ERROR: usuario no existe"
        self.usr, self.perfil = usr, u[0][2]
        base = dict(trama); base["TRX"] = trx; base["USR"] = usr
        if "EMP" not in base and len(u[0]) > 3 and u[0][3]: base["EMP"] = u[0][3]          # EC-23: la empresa sale del usuario
        derivado = False
        if "PER" not in base and "FECHA" in base:                                          # EC-23: el periodo sale de la fecha
            pp = [r for r in self.T["PERIODO"]["r"] if norm(r[1]) == norm(base.get("EMP")) and num(r[2]) <= num(base["FECHA"]) <= num(r[3])]
            if pp: base["PER"] = pp[0][0]; derivado = True
        tardio = self._tardio(trx, base) if derivado else ""    # I-3: hecho tardío (L-2), solo si el periodo sale de la fecha
        par = [r for r in self.T.get("PARAMETRO", {"r": []})["r"] if r[0] == "TRAZA"]
        self.traza = str(trama.get("TRAZA", "")).upper() == "S" or (bool(par) and str(par[0][1]).upper() == "S")
        self.undo = []; self.creados = []; heredado = {}; self.prof = 0
        try:
            if not self.autorizado(usr, trx):
                raise Error(self.mensaje("MSG-SEG") + f" ({self.perfil} → {trx})")
            if not self.filas("TOP", "TOP_TRX", trx):          # I-2 (V7): una transacción sin pasos no existe; nunca «OK» vacío
                raise Error(f"transacción {trx} no existe")
            for k, lin in enumerate(lineas or [{}]):
                self.tr = dict(base); self.tr.update(lin); self.tr.update(heredado); self.tr["LIN_NUM"] = k + 1
                for r in self.filas("TOP", "TOP_TRX", trx, "TOP_SEC"):
                    niv = r[3] if len(r) > 3 else "L"
                    if niv == "U":
                        if k > 0: continue
                        antes = dict(self.tr); self.opn(r[2])
                        heredado.update({x: v for x, v in self.tr.items() if antes.get(x, object()) != v})
                    else: self.opn(r[2])
                self.alarmas(trx)                          # OT-072 (AL-1): tras el HECHO de la línea; solo escribe ALERTA, nunca lo bloquea
            log[3] = "O"                                   # listo para aplicar (DBD p. 26)
            if str(trama.get("MODO", "")).upper() == "PREVIA":
                self.bitacora(trx, usr, log[0])            # queda reconstruible aunque se pierda la memoria
                self.pend = (trx, usr, log); return "OK"   # espera Confirmar o Deshacer
            self.bitacora(trx, usr, log[0]); log[3] = "A"
            if tardio: log[4] = tardio                     # I-3 (H-2): el aviso queda en el log; el retorno sigue siendo «OK»
            return "OK"
        except Error as e:
            for _, row, i, old in reversed(self.undo): row[i] = old
            for t, row in reversed(self.creados): self.T[t]["r"].remove(row)
            log[3], log[4] = "E", str(e)
            return "ERROR: " + str(e)
    def _tardio(self, trx, base):
        """I-3 (OT-102): si la FECHA cae en un periodo CERRADO y la transacción está en TARDIO_TRX, el evento va al primer
        periodo abierto (EVE_PER) con EVE_PER_REF = periodo de la fecha; EVE_FEC conserva la fecha real. Devuelve el aviso."""
        per, emp = base.get("PER"), base.get("EMP")
        if per in (None, "") or emp in (None, ""): return ""
        pr = [r for r in self.T["PERIODO"]["r"] if norm(r[0]) == norm(per) and norm(r[1]) == norm(emp)]
        if not pr or str(pr[0][self.col("PERIODO", "PER_EST")]) != "C": return ""
        par = [r for r in self.T.get("PARAMETRO", {"r": []})["r"] if r[0] == "TARDIO_TRX"]
        if not par or trx not in [x.strip() for x in str(par[0][1]).split("|")]: return ""
        ab = sorted([r for r in self.T["PERIODO"]["r"] if norm(r[1]) == norm(emp) and str(r[self.col("PERIODO", "PER_EST")]) == "A"],
                    key=lambda r: num(r[self.col("PERIODO", "PER_INI")]))
        if not ab: return ""
        base["PER_REF"], base["PER"] = per, ab[0][0]
        return f"HECHO TARDÍO de {per}"
    def alarmas(self, trx):
        """OT-072 (AL-1, ESPEC_ETAPA2B §3): reglas de negocio de Tino, condiciones simples sobre variables de la PROPIA transacción.
        Corre DESPUÉS del hecho de la línea; su única acción es escribir en ALERTA (nunca modifica ni bloquea el hecho, I3).
        Evalúa a lo sumo ALARMAS_MAX_TRX reglas activas y vigentes (en el orden de la hoja); sin la tabla o sin el parámetro no evalúa nada.
        Una regla que no se puede evaluar (variable ausente de la trama, prefijo MVIG_, umbral inexistente o no numérico) se omite
        en silencio: la alarma nunca detiene el hecho. Igual que Alarmas de motor.bas (P19)."""
        if "REGLA_ALARMA" not in self.T or "ALERTA" not in self.T: return
        mx = [r[1] for r in self.T["PARAMETRO"]["r"] if r[0] == "ALARMAS_MAX_TRX"]
        if not mx or num(mx[0]) <= 0: return
        per, emp = self.tr.get("PER", ""), self.tr.get("EMP", "")
        if per in (None, "") or emp in (None, ""): return           # sin periodo y empresa no hay clave de ALERTA
        fecha = num(self.tr.get("FECHA", 0)); n = 0
        for r in self.filas("REGLA_ALARMA", "RAL_TRX", trx):                      # en el orden de la hoja (igual que VBA)
            h = dict(zip(self.T["REGLA_ALARMA"]["h"], r))
            if str(h["RAL_ACTIVA"]).upper() != "S" or num(h["RAL_DESDE"]) > fecha: continue
            if n >= num(mx[0]): break
            n += 1
            var = str(h["RAL_VAR"])
            if var[:5] == "MVIG_" or var not in self.tr: continue      # solo variables de su transacción (I4)
            um = self.umbral_parametro(h["RAL_PARM"], emp)                # D1 (Ola 1): el umbral vive en PARAMETRO (empresa, si no «*»)
            if um in (None, ""): continue
            a, b = self.tr[var], um
            try: a2, b2 = float(a), float(b)
            except (TypeError, ValueError): continue
            k = (a2 > b2) - (a2 < b2)
            if not {"EQ": k == 0, "NE": k != 0, "GT": k > 0, "GE": k >= 0, "LT": k < 0, "LE": k <= 0}.get(str(h["RAL_OPELOG"]), False): continue
            clave = [per, emp, h["RAL_COD"], self.tr.get("EVE_NUM", trx), self.tr.get("LIN_NUM", "")]
            fila = next((x for x in self.T["ALERTA"]["r"] if all(norm(x[i]) == norm(v) for i, v in enumerate(clave))), None)
            if fila is None:
                fila = [None] * len(self.T["ALERTA"]["h"]); fila[:5] = clave
                self.T["ALERTA"]["r"].append(fila); self.creados.append(("ALERTA", fila))
            self.setc("ALERTA", fila, "ALE_VAL", a2); self.setc("ALERTA", fila, "ALE_UMB", b2)
    def perfiles(self, usr):
        """Relación usuario-perfil (DBD §4.3.1): un usuario puede tener varios perfiles."""
        ps = [r[1] for r in self.T.get("USUARIO_PERFIL", {"r": []})["r"] if r[0] == usr]
        return ps or [r[2] for r in self.T["USUARIO"]["r"] if r[0] == usr]
    def autorizado(self, usr, op):
        ps = self.perfiles(usr)
        return any(r[0] in ps and r[1] == op for r in self.T["PERFIL_TRX"]["r"])
    def bitacora(self, trx, usr, lognum):
        """Bitácora de cambios (igual que motor.bas): una fila por celda modificada o creada, enlazada al log."""
        b = self.T["BITACORA"]["r"]
        # orden igual al de VBA: primero se crea la fila, después se modifica (la recuperación usa el valor anterior más antiguo)
        cambios = [(t, row, i, None) for t, row in self.creados if t not in ("BITACORA", "LOG_TRX", "TRAZA") for i, v in enumerate(row) if v not in (None, "")]
        cambios += [(t, row, i, old) for t, row, i, old in self.undo]
        sin = [r[1] for r in self.T["PARAMETRO"]["r"] if r[0] == "SIN_BITACORA"]
        sin = str(sin[0]) if sin else "|TRAZA|"
        n = 0
        for t, row, i, old in cambios:
            if t == "BITACORA" or f"|{t}|" in sin: continue    # traza y datos derivados: se reconstruyen, no son cambios del parque (EC-54)
            n += 1
            fila = next(k for k, x in enumerate(self.T[t]["r"]) if x is row) + 2
            b.append([len(b) + 1, trx, usr, t, fila, self.T[t]["h"][i], old, row[i], lognum])
        lg = [r for r in self.T["LOG_TRX"]["r"] if r[0] == lognum]
        if lg:
            while len(lg[0]) < 6: lg[0].append(0)
            lg[0][5] = n                                          # el log guarda cuántos cambios hizo la transacción
    def confirmar(self):
        """Arrepentimiento (DBD p. 26), confirmar: lo que estaba 'listo para aplicar' (log O) queda definitivo."""
        if not self.pend: return "ERROR: " + self.mensaje("MSG-SINPEND")
        trx, usr, log = self.pend; log[3] = "A"; self.pend = None
        return "OK"
    def deshacer(self):
        """Arrepentimiento, deshacer: se revierten todos los cambios de la transacción en espera."""
        if not self.pend: return "ERROR: " + self.mensaje("MSG-SINPEND")
        for _, row, i, old in reversed(self.undo): row[i] = old
        for t, row in reversed(self.creados): self.T[t]["r"].remove(row)
        self.pend[2][3], self.pend[2][4] = "R", "Deshecho por el usuario"; self.pend = None
        return "OK"
    def recuperar(self):
        """Re-arranque (espejo de RecuperarPendientes): toda transacción en O se revierte, desde la memoria o la bitácora."""
        if self.pend:
            for _, row, i, old in reversed(self.undo): row[i] = old
            for t, row in reversed(self.creados): self.T[t]["r"].remove(row)
            self.pend[2][3], self.pend[2][4] = "R", self.mensaje("MSG-REANUDA"); self.pend = None
        for log in self.T["LOG_TRX"]["r"]:
            if log[3] != "O": continue
            for b in reversed(self.T["BITACORA"]["r"]):
                if b[8] == log[0]:
                    fila = self.T[b[3]]["r"][b[4] - 2]; fila[self.col(b[3], b[5])] = b[6]
            for t in self.T.values():                          # filas creadas por la transacción: quedan vacías al final
                while t["r"] and all(v in (None, "") for v in t["r"][-1]): t["r"].pop()
            log[3], log[4] = "R", self.mensaje("MSG-REANUDA")
    def reiniciar(self):
        """Simula cerrar Excel con una transacción en espera: se pierde la memoria; se recupera con log y bitácora."""
        self.pend = None; self.undo = []; self.creados = []; self.recuperar(); return "OK"
    def importar_bandeja(self, ruta, usuario=""):
        """Espejo de ImportarBandeja (ui.bas): pasa las decisiones de la pantalla de análisis a la hoja CARGA y renombra el archivo.
        SEGURIDAD (E-097): responde quien procesa (usuario con sesión); el usuario del archivo queda como solicitante."""
        import os, datetime
        if not os.path.exists(ruta) or not usuario: return 0
        ncol = len(self.T["CARGA"]["h"]); isol = self.T["CARGA"]["h"].index("CAR_SOLICITA") if "CAR_SOLICITA" in self.T["CARGA"]["h"] else None
        c = self.T["CARGA"]["r"]; n = max([int(num(r[0])) for r in c] or [0]); k = 0
        for i, txt in enumerate(open(ruta, encoding="utf-8").read().splitlines()):
            p = txt.split("\t")
            if i == 0 or not txt.strip() or len(p) < 3: continue
            n += 1; k += 1; fila = [n, p[0], usuario, p[2], "", ""] + [""] * (ncol - 6)
            if isol is not None: fila[isol] = p[1]
            c.append(fila)
        os.rename(ruta, os.path.join(os.path.dirname(ruta), "bandeja_procesada_" + datetime.datetime.now().strftime("%Y%m%d_%H%M%S") + ".csv"))
        return k
    def procesar_carga(self):
        """Puerto de carga: cada fila de CARGA se ejecuta como transacción con su usuario de captura y deja su estado."""
        ok = err = 0
        for row in self.T["CARGA"]["r"]:
            if row[4] == "OK": continue          # ya registrada: no se duplica; las con ERROR se reintentan
            trx, usr, trama = row[1], row[2], row[3]
            partes = str(trama).split("|")
            if trx in ("@PROPONER", "PROPONER"):   # V4.1 §9.7 #6: canal de la capa analítica (formato de canal_carga incluido)
                tp = parse(partes[0]); out = self.proponer(tp["TABLA"], tp["CLAVE"], tp["COL"], tp["VALOR"], usr, tp.get("MOTIVO", ""), tp.get("PAQ", "") or tp.get("PCA_PAQ", ""), tp.get("PROP", "") or tp.get("PCA_PROP", ""))
            elif trx == "@INVPROC":                # V4.1 I-1 (OT-095): inventario final del cierre (K9) → INV_PROCESO
                out = self.invproc(parse(partes[0]), usr)
            elif trx == "@SEGUIM":                 # I-2: seguimiento de decisiones → EST_DECISION
                out = self.seguim(parse(partes[0]), usr)
            elif trx == "@NIVEL":                  # I-2: degradación AUT-01 → PROPUESTA.PRO_NIVEL
                out = self.nivel(parse(partes[0]), usr)
            elif trx in ("@RESOLVER", "APRUEBA-PARM"):
                tp = parse(partes[0]); num = tp.get("NUM")
                if num in (None, "") and tp.get("PCA_PAQ"):
                    pend = [r for r in self.T["PARAM_CAMBIO"]["r"] if r[10] == tp["PCA_PAQ"] and r[7] in ("P", "S")]   # I-3: también pospuestas
                    num = pend[0][0] if pend else None
                out = self.resolver(num, str(tp.get("DEC") or "A"), usr, tp.get("DESDE"), tp.get("MOTIVO", ""))
            else:
                out = self.ejecutar(trx, parse(partes[0]), usr, [parse(x) for x in partes[1:]] or None)
            row[4] = "OK" if out == "OK" else "ERROR"; row[5] = out
            ok, err = (ok + 1, err) if out == "OK" else (ok, err + 1)
        return "OK"
    # ---- gobierno de parámetros (doble control): un cambio es un evento con estados P → A / R
    def _perm(self, usr, op):
        u = [r for r in self.T["USUARIO"]["r"] if r[0] == usr]; perfil = u[0][2] if u else ""
        return perfil, self.autorizado(usr, op)
    def tipo_tabla(self, tabla):
        r = [x for x in self.T.get("TABLAS_LOGICAS", {"r": []})["r"] if x[0] == tabla]
        return r[0][1] if r else ""
    def validar_dato(self, tabla, fila, col, valor):
        """Gobierno de MANT-PARM (E-086): clase de la tabla (EC-12), rango del parámetro (EC-15), referencia (EC-16)."""
        if self.tipo_tabla(tabla) in ("HISTORICO", "PARQUE", "PARQUE-SEMILLA", "CONFIG"): return self.mensaje("MSG-SOLOLECT")
        if tabla == "PARAMETRO" and col == "PAR_VAL" and fila is not None:
            mn, mx = fila[self.col("PARAMETRO", "PAR_MIN")], fila[self.col("PARAMETRO", "PAR_MAX")]
            try:
                v = float(valor)
                if (mn not in (None, "") and v < float(mn)) or (mx not in (None, "") and v > float(mx)): return self.mensaje("MSG-RANGO")
            except (TypeError, ValueError): pass
        for r in self.T.get("DATO_REF", {"r": []})["r"]:
            if r[0] == tabla and r[1] == col and valor not in (None, ""):
                if not any(norm(x[self.col(r[2], r[3])]) == norm(valor) for x in self.T[r[2]]["r"]): return self.mensaje("MSG-REF") + f" ({col} = {valor})"
        return ""
    def _cols_clave(self, tabla):
        """I-4: columnas de la clave de una tabla con clave compuesta (parámetro CLAVE_COMPUESTA «TABLA:COL1,COL2|…», sacado del DBD)."""
        par = [r for r in self.T.get("PARAMETRO", {"r": []})["r"] if r[0] == "CLAVE_COMPUESTA"]
        for item in str(par[0][1] if par else "").split("|"):
            if ":" in item and item.split(":", 1)[0].strip() == tabla:
                return [c.strip() for c in item.split(":", 1)[1].split(",") if c.strip()]
        return []
    def filas_clave(self, tabla, clave):
        """Filas de `tabla` con esa clave. Clave compuesta «v1|v2»: debe traer todas sus partes y coincidir en todas."""
        cols = self._cols_clave(tabla)
        if len(cols) > 1:
            partes = str(clave).split("|")
            ie = next((i for i, c in enumerate(cols) if c.endswith("_EMP")), None)
            if ie is not None and len(partes) == len(cols) - 1: partes.insert(ie, "*")   # D12: clave sin empresa = fila común «*»
            if len(partes) != len(cols): return []
            idx = [self.col(tabla, c) for c in cols]
            return [r for r in self.T[tabla]["r"] if all(norm(r[i]) == norm(v) for i, v in zip(idx, partes))]
        return [r for r in self.T[tabla]["r"] if norm(r[0]) == norm(clave)]
    def completar_clave(self, tabla, clave, usr):
        """I-5: en una tabla «de cada empresa» el usuario no escribe la empresa: se completa con la suya (un usuario, una
        empresa). Si la escribe y no es la suya: rechazo MSG-EMP (aislamiento). Devuelve (clave, error)."""
        cols = self._cols_clave(tabla)
        ie = next((i for i, c in enumerate(cols) if c.endswith("_EMP")), None)
        if ie is None: return clave, ""
        u = [r for r in self.T["USUARIO"]["r"] if r[0] == usr]
        emp = str(u[0][self.col("USUARIO", "USU_EMP")] or "") if u else ""
        partes = str(clave).split("|")
        if len(partes) == len(cols) - 1:
            partes.insert(ie, emp)
            if not self.filas_clave(tabla, "|".join(partes)): return clave, ""   # D12: sin valor propio → clave sin empresa = el común «*»
        elif len(partes) == len(cols) and norm(partes[ie]) not in (norm(emp), "*"): return clave, self.mensaje("MSG-EMP")
        return "|".join(partes), ""
    def proponer(self, tabla, clave, col, valor, usr, motivo="", paq="", prop=""):
        self.recuperar()
        perfil, ok = self._perm(usr, "MANT-PARM")
        if not ok: return "ERROR: " + self.mensaje("MSG-SEG") + f" ({perfil} → MANT-PARM)"
        if str(motivo).strip() == "": return "ERROR: " + self.mensaje("MSG-MOTIVO")              # EC-14: todo cambio con su porqué
        ant = ""; fila = None
        if self.tipo_tabla(tabla) in ("HISTORICO", "PARQUE", "PARQUE-SEMILLA", "CONFIG"): return "ERROR: " + self.mensaje("MSG-SOLOLECT")   # I-4: antes de la clave
        if col != "(NUEVA)":
            clave, e = self.completar_clave(tabla, clave, usr)
            if e: return "ERROR: " + e
            filas = self.filas_clave(tabla, clave)
            if not filas: return "ERROR: " + self.mensaje("MSG-CLAVE")
            fila = filas[0]; ant = fila[self.col(tabla, col)]
            e = self.validar_dato(tabla, fila, col, valor)
        else:
            vs = str(valor).split("|"); e = ""
            for i, c in enumerate(self.T[tabla]["h"]):
                if not e and i < len(vs): e = self.validar_dato(tabla, None, c, parse(f"x={vs[i]}").get("x", vs[i]))
        if e: return "ERROR: " + e
        fila_pc = [len(self.T["PARAM_CAMBIO"]["r"]) + 1, tabla, clave, col, ant, valor, usr, "P", "", motivo, paq]
        if "PCA_PROP" in self.T["PARAM_CAMBIO"]["h"]:      # I-2: de qué entrada del catálogo PROPUESTA sale el cambio
            fila_pc += [None] * (len(self.T["PARAM_CAMBIO"]["h"]) - len(fila_pc))
            fila_pc[self.col("PARAM_CAMBIO", "PCA_PROP")] = prop or None
        elif prop:
            return "ERROR: la base no tiene PCA_PROP (falta la estructura de I-2)"
        self.T["PARAM_CAMBIO"]["r"].append(fila_pc)
        return "OK"
    def invproc(self, tp, usr):
        """@INVPROC (OT-095, espejo de InvProc de motor.bas): escribe o reemplaza la fila (PER, OBJ, ELE, EMP) de INV_PROCESO.
        Autorizado por PERFIL_TRX; el periodo debe existir y estar abierto (A = en cierre); deja BITACORA."""
        self.recuperar()
        perfil, ok = self._perm(usr, "@INVPROC")
        if not ok: return "ERROR: " + self.mensaje("MSG-SEG") + f" ({perfil} → @INVPROC)"
        per, obj, ele, emp, val = str(tp.get("PER")), str(tp.get("OBJ")), str(tp.get("ELE")), str(tp.get("EMP")), tp.get("VAL")
        pr = [r for r in self.T["PERIODO"]["r"] if str(r[0]) == per and str(r[1]) == emp]
        if not pr: return f"ERROR: periodo {per} de {emp} no existe"
        if str(pr[0][self.col("PERIODO", "PER_EST")]) != "A": return f"ERROR: periodo {per} de {emp} no está en cierre (estado {pr[0][self.col('PERIODO', 'PER_EST')]})"
        try: val = float(val)
        except (TypeError, ValueError): return f"ERROR: VAL no numérico ({val})"
        t = self.T["INV_PROCESO"]; c = {h: t["h"].index(h) for h in ("IPR_PER", "IPR_OBJ", "IPR_VAL", "IPR_EMP", "IPR_ELE")}
        fila = [r for r in t["r"] if str(r[c["IPR_PER"]]) == per and str(r[c["IPR_OBJ"]]) == obj and str(r[c["IPR_ELE"]]) == ele and str(r[c["IPR_EMP"]]) == emp]
        b = self.T["BITACORA"]["r"]
        if fila:
            r = fila[0]; ant = r[c["IPR_VAL"]]; r[c["IPR_VAL"]] = val
            b.append([len(b) + 1, "@INVPROC", usr, "INV_PROCESO", t["r"].index(r) + 2, "IPR_VAL", ant, val, 0])
        else:
            r = [None] * len(t["h"])
            r[c["IPR_PER"]], r[c["IPR_OBJ"]], r[c["IPR_VAL"]], r[c["IPR_EMP"]], r[c["IPR_ELE"]] = per, obj, val, emp, ele
            t["r"].append(r)
            for i, v in enumerate(r):
                if v not in (None, ""): b.append([len(b) + 1, "@INVPROC", usr, "INV_PROCESO", len(t["r"]) + 1, t["h"][i], None, v, 0])
        return "OK"
    def _bit(self, trx, usr, tabla, fila_idx, col, ant, nue):
        b = self.T["BITACORA"]["r"]; b.append([len(b) + 1, trx, usr, tabla, fila_idx + 2, col, ant, nue, 0])
    def seguim(self, tp, usr):
        """@SEGUIM (I-2, OT-098 I2-b; espejo de Seguim de motor.bas): escribe o reemplaza la fila EST_DECISION de REF (= PCA_NUM).
        Solo perfil autorizado (AUTONOMO); el PCA debe existir y estar en A; REAL y ERR vacíos solo si ESTADO = PENDIENTE."""
        self.recuperar()
        perfil, ok = self._perm(usr, "@SEGUIM")
        if not ok: return "ERROR: " + self.mensaje("MSG-SEG") + f" ({perfil} → @SEGUIM)"
        est = str(tp.get("ESTADO") or "")
        if est not in ("PENDIENTE", "MEDIDO", "SIN_MEDICION"): return f"ERROR: ESTADO {est!r} fuera de dominio (PENDIENTE, MEDIDO, SIN_MEDICION)"
        ref = tp.get("REF")
        pc = [r for r in self.T["PARAM_CAMBIO"]["r"] if norm(r[0]) == norm(ref)]
        if not pc: return f"ERROR: PCA_NUM {ref} no existe"
        if pc[0][7] != "A": return f"ERROR: PCA_NUM {ref} no está aprobado (estado {pc[0][7]})"
        vals = {}
        for k in ("PRED", "REAL", "ERR"):
            v = tp.get(k)
            if v in (None, ""):
                if k == "PRED" or est != "PENDIENTE": return f"ERROR: {k} vacío solo se admite con ESTADO = PENDIENTE" if k != "PRED" else "ERROR: PRED vacío"
                vals[k] = None
            else:
                try: vals[k] = float(v) if not isinstance(v, (int, float)) else v
                except (TypeError, ValueError): return f"ERROR: {k} no numérico ({v})"
        t = self.T["EST_DECISION"]; h = t["h"]
        nuevo = {"EDE_REF": ref, "EDE_OBJ": tp.get("OBJ"), "EDE_PER": tp.get("PER"), "EDE_PRED": vals["PRED"], "EDE_REAL": vals["REAL"],
                 "EDE_ERR": vals["ERR"], "EDE_ESTADO": est, "EDE_REGLA": tp.get("REGLA")}
        falta = [c for c in nuevo if c not in h]
        if falta: return f"ERROR: EST_DECISION sin {falta} (falta la estructura de I-2)"
        fila = [r for r in t["r"] if norm(r[h.index("EDE_REF")]) == norm(ref)]
        if fila:
            r = fila[0]
            for c, v in nuevo.items():
                if norm(r[h.index(c)]) != norm(v):
                    self._bit("@SEGUIM", usr, "EST_DECISION", t["r"].index(r), c, r[h.index(c)], v); r[h.index(c)] = v
        else:
            r = [None] * len(h)
            for c, v in nuevo.items(): r[h.index(c)] = v
            t["r"].append(r)
            for c, v in nuevo.items():
                if v not in (None, ""): self._bit("@SEGUIM", usr, "EST_DECISION", len(t["r"]) - 1, c, None, v)
        return "OK"
    def nivel(self, tp, usr):
        """@NIVEL (I-2, V7; espejo de BajarNivel de motor.bas): baja el PRO_NIVEL de una entrada de PROPUESTA (AUT-01).
        Solo baja la autonomía (más control humano = número mayor); subirla exige PROPONER y aprobación de otra persona."""
        self.recuperar()
        perfil, ok = self._perm(usr, "@NIVEL")
        if not ok: return "ERROR: " + self.mensaje("MSG-SEG") + f" ({perfil} → @NIVEL)"
        t = self.T.get("PROPUESTA")
        if not t: return "ERROR: la base no tiene PROPUESTA (falta la estructura de I-2)"
        f = [r for r in t["r"] if norm(r[0]) == norm(tp.get("PRO"))]
        if not f: return f"ERROR: PROPUESTA {tp.get('PRO')} no existe"
        try: n = int(float(tp.get("NIVEL")))
        except (TypeError, ValueError): return f"ERROR: NIVEL no numérico ({tp.get('NIVEL')})"
        i = self.col("PROPUESTA", "PRO_NIVEL"); ant = int(num(f[0][i]))
        if n not in (0, 1, 2): return f"ERROR: NIVEL {n} fuera de dominio (0, 1, 2)"
        if n <= ant: return f"ERROR: @NIVEL solo baja la autonomía ({ant} → {n} no permitido; use PROPONER)"
        f[0][i] = n; self._bit("@NIVEL AUT-01", usr, "PROPUESTA", t["r"].index(f[0]), "PRO_NIVEL", ant, n)
        return "OK"
    def _nivel1(self, x, usr):
        """V4.1 R-71: solo SISTEMA aprueba lo suyo, y solo el PAR_VAL de un parámetro con PAR_DUENO = SISTEMA y PAR_PROT = N."""
        if usr != "SISTEMA" or x[1] != "PARAMETRO" or x[3] != "PAR_VAL": return False
        f = self.filas_clave("PARAMETRO", x[2])               # D12: igual que EsNivel1 de motor.bas (FilaClave, clave compuesta)
        if not (bool(f) and f[0][self.col("PARAMETRO", "PAR_DUENO")] == "SISTEMA" and f[0][self.col("PARAMETRO", "PAR_PROT")] == "N"): return False
        if str(x[9] or "").upper().startswith("REVERSION"): return False        # I-2 (V8): una reversión la aprueba una persona
        h = self.T["PARAM_CAMBIO"]["h"]
        if "PCA_PROP" in h and len(x) > h.index("PCA_PROP") and x[h.index("PCA_PROP")] not in (None, ""):
            p = [r for r in self.T.get("PROPUESTA", {"r": []})["r"] if norm(r[0]) == norm(x[h.index("PCA_PROP")])]
            return bool(p) and num(p[0][self.col("PROPUESTA", "PRO_NIVEL")]) == 1    # I-2 (V8): solo entradas de nivel 1
        return True
    def resolver(self, num, dec, usr, desde=None, motivo=""):
        self.recuperar()
        dec = str(dec or "A").upper()
        if dec not in ("A", "R", "S"): return f"ERROR: decisión {dec} no válida (A, R o S)"
        if dec == "S" and str(motivo or "").strip() == "": return "ERROR: " + self.mensaje("MSG-MOTIVO")   # I-3 (L-8): posponer exige motivo
        perfil, ok = self._perm(usr, "APRUEBA-PARM")
        if not ok: return "ERROR: " + self.mensaje("MSG-SEG") + f" ({perfil} → APRUEBA-PARM)"
        p = [r for r in self.T["PARAM_CAMBIO"]["r"] if norm(r[0]) == norm(num)]
        if not p or p[0][7] not in ("P", "S"): return "ERROR: " + self.mensaje("MSG-PCA")
        p = p[0]
        grupo = [r for r in self.T["PARAM_CAMBIO"]["r"] if p[10] not in (None, "") and r[10] == p[10] and r[7] in ("P", "S")] or [p]   # EC-14: el paquete se decide junto
        if any(x[6] == usr and not self._nivel1(x, usr) for x in grupo): return "ERROR: " + self.mensaje("MSG-AUTOAPRUEBA")
        for x in grupo:
            if dec == "A":
                if x[3] == "(NUEVA)": self.T[x[1]]["r"].append([parse(f"x={v}")["x"] if v != "" else None for v in str(x[5]).split("|")])
                else:
                    fila = self.filas_clave(x[1], x[2])[0]; fila[self.col(x[1], x[3])] = x[5]
                    if x[1] == "PARAMETRO" and x[3] == "PAR_VAL" and desde not in (None, ""):   # R-72: vigencia = periodo siguiente
                        fila[self.col("PARAMETRO", "PAR_DESDE")] = int(desde)
            if x[6] == usr and self._nivel1(x, usr):                                     # ADR-05: toda acción de SISTEMA con motivo R-71
                b = self.T["BITACORA"]["r"]
                b.append([len(b) + 1, "APRUEBA-PARM", usr, x[1], x[2], x[3], x[4], x[5], "R-71" + (f" DESDE={desde}" if desde else "")][:len(self.T["BITACORA"]["h"])])
            x[7], x[8] = dec, usr
            h = self.T["PARAM_CAMBIO"]["h"]
            if "PCA_MOT_RES" in h and str(motivo or "").strip():                          # I-3 (H-3): motivo de la resolución
                x += [None] * (len(h) - len(x)); x[h.index("PCA_MOT_RES")] = motivo
        return "OK"
    def mantener_fila(self, tabla, fila, valores, usr):
        """MANT-PARM (espejo de MantenerFila): fila = índice 0-based o None para nueva; seguridad y reversa."""
        u = [r for r in self.T["USUARIO"]["r"] if r[0] == usr]; self.perfil = u[0][2] if u else ""
        if not self.autorizado(usr, "MANT-PARM"):
            return "ERROR: " + self.mensaje("MSG-SEG") + f" ({self.perfil} → MANT-PARM)"
        if str(valores[0]).strip() in ("", "None"): return "ERROR: " + self.mensaje("MSG-CLAVE")
        actual = self.T[tabla]["r"][fila] if fila is not None else None
        if tabla == "USUARIO":                                          # E-098: la clave nunca se guarda en claro
            valores = list(valores); j = self.col("USUARIO", "USU_CLAVE")
            if not str(valores[j]).startswith(("SHA256:", "(")): valores[j] = clave_cifrada(valores[0], valores[j])
        if tabla == "PARAMETRO" and actual is not None and str(actual[self.col("PARAMETRO", "PAR_PROT")]) == "S":
            return "ERROR: " + self.mensaje("MSG-PROTEGIDO")                                 # EC-15: protegido = solo por propuesta
        for i, c in enumerate(self.T[tabla]["h"]):
            e = self.validar_dato(tabla, actual, c, valores[i] if i < len(valores) else None)
            if e: return "ERROR: " + e
        if fila is None: self.T[tabla]["r"].append(list(valores))
        else: self.T[tabla]["r"][fila] = list(valores)
        return "OK"
    def opn(self, op):
        self.prof = getattr(self, "prof", 0) + 1                    # OT-052: profundidad de anidamiento (máx. PROF_MAX), igual que motor.bas
        try:
            if self.prof > PROF_MAX: raise Error(f"profundidad máxima de operaciones excedida (posible ciclo): {op}")
            ms = self.filas("OME", "OME_OPN", op, "OME_SEC")
            if not ms: raise Error(f"Operación sin métodos: {op}")
            for r in ms: self.met(r[2])
        finally: self.prof -= 1
    def ref(self, x):
        """OT-052: un nombre de operación o tabla con prefijo «VAR:» se toma de la variable en tiempo de ejecución."""
        x = "" if x is None else str(x)
        return str(self.get(x[4:])) if x[:4] == "VAR:" else x
    def met(self, cod):
        m = self.filas("MET", "MET_COD", cod)
        if not m: raise Error(f"Método no existe: {cod}")
        _, des, tipo, tabla, sub, obl, orden = m[0][:7]
        mca = self.filas("MCA", "MCA_MET", cod, "MCA_SEC")
        getattr(self, "m_" + tipo)(cod, tabla, sub, obl, orden, mca)
    def umbral_parametro(self, cod, emp):
        """D1: valor de PARAMETRO para un código de umbral; primero el de la empresa, si no hay, el común «*» (igual que UmbralParametro de motor.bas)."""
        ic, ie, iv = self.col("PARAMETRO", "PAR_COD"), self.col("PARAMETRO", "PAR_EMP"), self.col("PARAMETRO", "PAR_VAL")
        fs = [r for r in self.T["PARAMETRO"]["r"] if norm(r[ic]) == norm(cod)]
        f = [r for r in fs if norm(r[ie]) == norm(emp)] or [r for r in fs if norm(r[ie]) == "*"]
        return f[0][iv] if f else None
    def coincide(self, tabla, mca):
        """D12 (Ola 1): primero las filas exactas; si no hay ninguna, una clave *_EMP acepta la fila común «*»."""
        return self._coincide(tabla, mca, False) or self._coincide(tabla, mca, True)
    def _coincide(self, tabla, mca, comodin):
        res = []
        for row in self.T[tabla]["r"]:
            ok = True
            for _, _, c, rol, ope, ori, v in mca:
                if rol == "K":
                    cel = row[self.col(tabla, c)]
                    if norm(cel) != norm(self.val(ori, v)) and not (comodin and str(c).endswith("_EMP") and norm(cel) == "*"): ok = False; break
                if rol == "H" and num(row[self.col(tabla, c)]) > num(self.val(ori, v)): ok = False; break
            if ok: res.append(row)
        return res
    def destino(self, v):
        """OT-058 (E-200): nombre de variable destino de LEER. «VAR:x» o prefijo+«{VAR:x}» (p. ej. MVIG_{VAR:EJE_ACTUAL}) se resuelve
        en ejecución; el nombre construido debe empezar por «MVIG_» y no ser vacío. Sin esa forma, el nombre literal de siempre."""
        v = "" if v is None else str(v)
        if v[:4] != "VAR:" and "{VAR:" not in v: return v
        if v[:4] == "VAR:": n = str(self.get(v[4:]))
        else:
            n = v
            while "{VAR:" in n:
                a = n.index("{VAR:"); b = n.index("}", a); n = n[:a] + str(self.get(n[a + 5:b])) + n[b + 1:]
        if n.strip() == "" or n[:5] == "MVIG_" and n[5:].strip() == "": raise Error(f"Variable destino vacía: {v}")
        if n[:5] != "MVIG_": raise Error(f"Variable destino no permitida (debe empezar por MVIG_): {n}")
        return n
    def m_LEER(self, cod, tabla, sub, obl, orden, mca):
        rs = self.coincide(tabla, mca)
        if orden:
            desc = str(orden).startswith("-"); oc = self.col(tabla, str(orden).lstrip("-"))
            rs.sort(key=lambda r: num(r[oc]), reverse=desc)
        if not rs:
            if obl == "S": raise Error(f"No existe en {tabla} ({cod})")
            self.tr["HALLADA"] = "N"                       # OT-056 (R3): «hallada S/N» como parte del modo de acceso de LEER
            for x in mca:
                if x[3] == "V": self.tr[self.destino(x[6])] = ""
            return
        self.tr["HALLADA"] = "S"
        for x in mca:
            if x[3] == "V": self.tr[self.destino(x[6])] = rs[0][self.col(tabla, x[2])]
    def aplicar(self, tabla, row, mca):
        for x in mca:
            if x[3] != "V": continue
            c = self.plantilla(x[2]); i = self.col(tabla, c); v = self.val(x[5], x[6]); ope = x[4]
            if ope == "SUMA": nv = num(row[i]) + num(v)
            elif ope == "RESTA": nv = num(row[i]) - num(v)
            else: nv = v
            self.setc(tabla, row, c, nv)
    def m_CREAR(self, cod, tabla, sub, obl, orden, mca):
        row = [None] * len(self.T[tabla]["h"]); self.T[tabla]["r"].append(row); self.creados.append((tabla, row))
        for x in mca:
            i = self.col(tabla, x[2])
            if x[5] == "SIS" and x[6] == "#SIG":
                nv = max([num(r[i]) for r in self.T[tabla]["r"] if r is not row] + [0]) + 1; row[i] = nv; self.tr[x[2]] = nv
            else: row[i] = self.val(x[5], x[6])
    def m_ACTUALIZAR(self, cod, tabla, sub, obl, orden, mca):
        rs = self.coincide(tabla, mca)
        if not rs:
            if obl == "S": raise Error(f"No existe la fila a actualizar en {tabla} ({cod})")
            return
        self.aplicar(tabla, rs[0], mca)
    def m_ACUMULAR(self, cod, tabla, sub, obl, orden, mca):
        """OT-056: operador COMPUESTO configurado, una sola entrada: LEER (no obligatorio, R1) → FÓRMULA (valor nuevo =
        viejo ± dato; ASIGNA reemplaza sin convertir, R5; viejo = 0 si no hay fila) → CREAR (claves; sumas en 0) y ACTUALIZAR
        con los valores ya calculados (R2). Variables locales con prefijo propio (R6): la trama no se toca."""
        acu_fila = next(iter(self.coincide(tabla, mca)), None)                   # LEER interno
        acu_hallada = acu_fila is not None
        acu_val = {}                                                             # FÓRMULA: columna → valor nuevo, secuencial
        for x in mca:
            if x[3] != "V": continue
            c = self.plantilla(x[2]); v = self.val(x[5], x[6])
            if c in acu_val: viejo = acu_val[c]
            elif acu_hallada: viejo = acu_fila[self.col(tabla, c)]
            else: viejo = 0 if x[4] in ("SUMA", "RESTA") else None
            acu_val[c] = num(viejo) + num(v) if x[4] == "SUMA" else num(viejo) - num(v) if x[4] == "RESTA" else v
        if not acu_hallada:                                                      # CREAR: claves; sumas en 0; luego lo calculado
            acu_fila = [None] * len(self.T[tabla]["h"])
            for x in mca:
                c = self.plantilla(x[2]); i = self.col(tabla, c)
                if x[3] == "K": acu_fila[i] = self.val(x[5], x[6])
                elif x[4] in ("SUMA", "RESTA"): acu_fila[i] = 0
            self.T[tabla]["r"].append(acu_fila); self.creados.append((tabla, acu_fila))
        for c, v in acu_val.items(): self.setc(tabla, acu_fila, c, v)           # ACTUALIZAR con los valores ya calculados
    def trazar(self, met, var, v, det):
        row = [len(self.T["TRAZA"]["r"]) + 1, self.tr["TRX"], met, var, v, det, self.tr.get("OBJ", "")]
        self.T["TRAZA"]["r"].append(row); self.creados.append(("TRAZA", row))
    def m_FORMULA(self, cod, *_):
        acc = 0.0; det = ""; ini = True       # OT-060: acc puede ser TEXTO solo tras CONCATENA; ini = aun no hubo operacion
        for r in self.filas("FRM", "FRM_MET", cod, "FRM_SEC"):
            op, var, lit = r[2], r[3], r[4]
            if op == "ASIGNA":
                self.tr[var] = acc
                if getattr(self, "traza", False): self.trazar(cod, var, acc, det)
                det = ""; continue
            if op == "CONCATENA":   # texto acumulado & separador (solo con variable y si ya hay texto) & valor; unica operacion que pasa numeros a texto
                if not isinstance(acc, str): acc = "" if ini else texto_num(acc)
                t = texto_valor(self.get(var)) if var else texto_valor(lit)
                if var and acc != "": acc += texto_valor(lit)
                acc += t; ini = False
                if getattr(self, "traza", False): det += f"CONCATENA {var + '=' if var else ''}{t}; "
                continue
            if isinstance(acc, str) and op != "INICIA": raise Error(f"Operación {op} sobre texto acumulado en {cod}")
            x = num(self.get(var)) if var else num(lit)
            if getattr(self, "traza", False): det += f"{op} {var + '=' if var else ''}{x:g}; "
            ini = False
            if op == "INICIA": acc = x
            elif op == "SUMA": acc += x
            elif op == "RESTA": acc -= x
            elif op == "MULT": acc *= x
            elif op == "DIVIDE":
                if x == 0: raise Error(f"División entre cero en {cod}")
                acc /= x
            elif op == "MAX": acc = max(acc, x)
            elif op == "MIN": acc = min(acc, x)
            elif op == "RED": acc = red(acc, lit)
            elif op == "ASIGNA": self.tr[var] = acc
            else: raise Error(f"Operador desconocido {op}")
    def cond(self, cod):
        out = []
        for r in self.filas("CND", "CND_MET", cod):
            _, var, ope, var2, lit, msg = r[:6]
            a = self.get(var); b = self.get(var2) if var2 else lit
            try: a2, b2 = float(a), float(b); cmpab = (a2 > b2) - (a2 < b2)
            except (TypeError, ValueError): a2, b2 = norm(a), norm(b); cmpab = (a2 > b2) - (a2 < b2)
            ok = {"EQ": cmpab == 0, "NE": cmpab != 0, "GT": cmpab > 0, "GE": cmpab >= 0, "LT": cmpab < 0, "LE": cmpab <= 0}[ope]
            out.append((ok, msg))
        return out
    def m_VALIDA(self, cod, *_):
        for ok, msg in self.cond(cod):
            if not ok: raise Error(self.mensaje(msg))
    def mensaje(self, cod):
        for r in self.T.get("MENSAJE", {"r": []})["r"]:
            if r[0] == cod: return r[1]
        return cod
    def m_SI(self, cod, tabla, sub, *_):
        if all(ok for ok, _ in self.cond(cod)): self.opn(self.ref(sub))
    def m_PARACADA(self, cod, tabla, sub, obl, orden, mca):
        tabla = self.ref(tabla)
        if tabla not in self.T: raise Error(f"Tabla no existe: {tabla}")
        for row in list(self.coincide(tabla, mca)):
            for h, v in zip(self.T[tabla]["h"], row): self.tr[h] = v
            self.opn(self.ref(sub))                                  # la variable se lee tras cargar la fila (puede venir de ella)
    def m_ALGORITMO(self, cod, *_):
        alg = self.get("ALG")
        pasos = self.filas("PAL", "PAL_ALG", alg, "PAL_SEC")
        if not pasos: raise Error(f"Algoritmo sin pasos: {alg}")
        for p in pasos: self.met(p[2])

_DES = (("%3B", ";"), ("%7C", "|"), ("%0A", "\n"), ("%25", "%"))     # I-4: inverso de canal_carga._val; %25 al final


def decodificar(v):
    for e, c in _DES:
        v = v.replace(e, c)
    return v


def parse(s):
    d = {}
    for par in str(s).split(";"):
        if "=" in par:
            k, v = par.split("=", 1); v = decodificar(v.strip())
            try: d[k.strip()] = float(v) if any(ch.isdigit() for ch in v) and v.replace(".", "", 1).replace("-", "", 1).isdigit() else v
            except ValueError: d[k.strip()] = v
    return d

def autoprueba(ruta):
    """Cada escenario se ejecuta y, en ese momento, se comprueban sus valores esperados (ESP_ESC = escenario)."""
    m = Motor(ruta); m.reiniciar()
    res = []
    for r in m.T["ESCENARIO"]["r"]:
        num_, grupo, trx, usr, trama, espera, desc = r[:7]
        partes = str(trama).split("|")
        tp = parse(partes[0]) if partes[0] else {}
        if trx == "@CARGA": out = m.procesar_carga()
        elif trx == "@PROPONER": out = m.proponer(tp["TABLA"], tp["CLAVE"], tp["COL"], tp["VALOR"], usr, tp.get("MOTIVO", ""), tp.get("PAQ", ""))
        elif trx == "@RESOLVER": out = m.resolver(tp["NUM"], tp["DEC"], usr)
        elif trx == "@CONFIRMAR": out = m.confirmar()
        elif trx == "@DESHACER": out = m.deshacer()
        elif trx == "@REINICIAR": out = m.reiniciar()
        else: out = m.ejecutar(trx, parse(partes[0]), usr, [parse(x) for x in partes[1:]] or None)
        ok = out == "OK" if espera == "OK" else (out.startswith("ERROR") and str(espera).split(":", 1)[-1].strip() in out)
        res.append(("ESCENARIO", num_, f"{trx} {desc}", espera, out, "PASA" if ok else "FALLA"))
        for e in m.T["ESPERADO"]["r"]:
            if norm(e[0]) != norm(num_): continue
            esc, tabla, filtro, colname, valor, desc2 = e[:6]
            cond = [x.split("=", 1) for x in str(filtro).split(";")]
            rows = [row for row in m.T[tabla]["r"] if all(norm(row[m.col(tabla, c)]) == norm(parse(f"{c}={v}")[c]) for c, v in cond)]
            got = rows[0][m.col(tabla, colname)] if rows else None
            try: float(valor); texto = False
            except (TypeError, ValueError): texto = True          # igual que VBA: un esperado no numérico se compara como texto
            if texto: ok = got is not None and norm(got) == norm(valor)
            else: ok = got is not None and got != "" and abs(num(got) - num(valor)) <= 0.005
            res.append(("VALOR", esc, f"{tabla}.{colname} [{filtro}] {desc2}", valor, got, "PASA" if ok else "FALLA"))
    return res, m

if __name__ == "__main__":
    ruta = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.abspath(__file__)), "salida", "PoC_Costos_Palta.xlsx")
    res, _ = autoprueba(ruta)
    for x in res: print(f"{x[5]:6s} {x[0]:9s} {str(x[1]):>3s}  {x[2][:80]:80s} esperado={x[3]} obtenido={x[4]}")
    f = sum(1 for x in res if x[5] == "FALLA")
    print(f"\nTOTAL: {len(res)} pruebas · {len(res) - f} PASA · {f} FALLA")
    sys.exit(1 if f else 0)
