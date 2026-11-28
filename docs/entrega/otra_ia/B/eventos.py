"""
eventos.py — B1 (Receptor de hechos) y B3 (Estado del plan) de la especificación MN 02.

Python 3.11 puro (sin dependencias).

Definiciones (Reyna, MCD §3.4; TECNIA 2016, pp. 84-85, según docs/diseno/METODO_PLANEAMIENTO.md):
  * evento  = transacción consumada: algo que YA ocurrió. No se edita ni se borra; una corrección
              es otro evento que dice a cuál corrige («corrige»: "E-0003").
  * ticket  = evento futuro con recursos comprometidos. Cambia de estado solo hacia adelante,
              según su máquina de estados (spec.TICKETS).

B1 valida cada hecho (campos, tipos, rangos y referencias) y lo rechaza con un mensaje en castellano;
nunca corrige en silencio (no convierte "10" en 10, ni «en curso» en «en ejecución»).
B3 guarda los tickets y deriva el estado REPRODUCIENDO todos los hechos válidos desde el estado base,
no encadenando deltas: así una corrección se aplica en el lugar del hecho que corrige y el orden
de llegada no cambia el resultado.

Uso:
    from eventos import EstadoPlan, PEDIDO, LLEGA_MATERIAL
    e = EstadoPlan(hoy="2026-01-10", recursos={"M1": 8}, materiales=["PVC"], recetas={...})
    r = e.registrar({"tipo": PEDIDO, "accion": "entra", "cliente": "C1", "producto": "P1",
                     "cantidad": 10, "fecha": "2026-01-20", "precio": 500})
    r["aceptado"], r["id"], r["tickets"], r["errores"], r["avisos"]
"""
from __future__ import annotations

import copy
import math
import re
from datetime import date, datetime, timedelta

# ----------------------------------------------------------------------------- nombres de spec.py
PEDIDO = "Pedido entra o se cancela"
LLEGA_MATERIAL = "Llega material"
PLANTA = "Se para / reinicia una planta"
COBRO_PAGO = "Se cobra o se paga"
NO_CONFORMIDAD = "No conformidad"
DATO_MAESTRO = "Cambia un dato maestro"
TIPOS_EVENTO = (PEDIDO, LLEGA_MATERIAL, PLANTA, COBRO_PAGO, NO_CONFORMIDAD, DATO_MAESTRO)

TICKET_DE_EVENTO = {PEDIDO: "OT", LLEGA_MATERIAL: "COMPRA", PLANTA: "OT", COBRO_PAGO: "FINANCIAMIENTO",
                    NO_CONFORMIDAD: "OT", DATO_MAESTRO: "—"}

# Máquinas de estado (spec.TICKETS). Solo hacia adelante. «cancelado» solo existe en OT y COMPRA.
MAQUINAS = {
    "OT": {"propuesto": {"comprometido", "cancelado"},
           "comprometido": {"en ejecución", "cancelado"},
           "en ejecución": {"terminado", "cancelado"},
           "terminado": set(), "cancelado": set()},
    "COMPRA": {"propuesto": {"comprometido", "cancelado"},
               "comprometido": {"recibido", "cancelado"},
               "recibido": set(), "cancelado": set()},
    "FINANCIAMIENTO": {"propuesto": {"tomado"}, "tomado": {"pagado"}, "pagado": set()},
    "INVERSIÓN": {"propuesto": {"aprobado"}, "aprobado": {"instalado"}, "instalado": {"en uso"}, "en uso": set()},
}
PREFIJO = {"OT": "OT", "COMPRA": "CO", "FINANCIAMIENTO": "FI", "INVERSIÓN": "IN"}
# atributos de cada ticket según spec.TICKETS (más los que trae el hecho que lo crea)
CAMPOS_TICKET = {
    "OT": ("producto", "cantidad", "fecha_entrega", "recurso", "inicio", "fin", "cliente", "precio", "origen"),
    "COMPRA": ("material", "cantidad", "proveedor", "fecha_pedido", "fecha_llegada"),
    "FINANCIAMIENTO": ("monto", "tasa", "fecha_toma", "fecha_pago"),
    "INVERSIÓN": ("activo", "costo", "fecha", "capacidad", "vida_util", "recurso"),
}
CAMPOS_MAESTRO = ("capacidad", "precio", "tasa", "plazo_proveedor")
# quién puede mover un ticket por fuera de un hecho (spec: B3 lee X.plan, C.carga; B9 lee U.gerente)
ORIGENES = ("plan", "gerente", "costos")

_RE_FECHA = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_RE_EVENTO = re.compile(r"^E-\d{4,}$")


class Rechazo(Exception):
    """Error de validación con uno o más mensajes en castellano."""
    def __init__(self, errores):
        self.errores = errores if isinstance(errores, list) else [errores]
        super().__init__("; ".join(self.errores))


# ----------------------------------------------------------------------------- validadores
def _fecha(v, campo, err):
    if isinstance(v, datetime):
        if (v.hour, v.minute, v.second, v.microsecond) != (0, 0, 0, 0):
            err.append(f"«{campo}» trae hora ({v}); se espera solo la fecha.")
            return None
        return v.date()
    if isinstance(v, date):
        return v
    if isinstance(v, str) and _RE_FECHA.match(v.strip()):
        try:
            return date.fromisoformat(v.strip())
        except ValueError:
            err.append(f"«{campo}» = «{v}» no es una fecha que exista.")
            return None
    err.append(f"«{campo}» debe ser una fecha AAAA-MM-DD; llegó «{v}».")
    return None


def _numero(v, campo, err, minimo=None, estricto=False, maximo=None, entero=False):
    if isinstance(v, bool) or not isinstance(v, (int, float)):
        tipo = "texto" if isinstance(v, str) else type(v).__name__
        err.append(f"«{campo}» debe ser un número; llegó {tipo} «{v}».")
        return None
    if isinstance(v, float) and not math.isfinite(v):
        err.append(f"«{campo}» no es un número finito.")
        return None
    if entero and v != int(v):
        err.append(f"«{campo}» debe ser entero; llegó {v}.")
        return None
    if minimo is not None and (v <= minimo if estricto else v < minimo):
        err.append(f"«{campo}» debe ser {'mayor que' if estricto else 'mayor o igual a'} {minimo}; llegó {v}.")
        return None
    if maximo is not None and v >= maximo:
        err.append(f"«{campo}» debe ser menor que {maximo}; llegó {v}.")
        return None
    return v


def _texto(v, campo, err):
    if not isinstance(v, str) or not v.strip():
        err.append(f"«{campo}» debe ser un texto no vacío; llegó «{v}».")
        return None
    if v != v.strip():
        err.append(f"«{campo}» tiene espacios al inicio o al final («{v}»); corríjalo en el origen.")
        return None
    return v


def _opcion(v, campo, opciones, err):
    if v not in opciones:
        err.append(f"«{campo}» debe ser una de {sorted(opciones)}; llegó «{v}».")
        return None
    return v


# esquema: campo -> (obligatorio_en, validador). obligatorio_en: conjunto de acciones (o {"*"})
COMUNES = {"tipo", "documento", "corrige", "nota"}
ESQUEMA = {
    PEDIDO: {"accion": {"*"}, "cliente": {"entra"}, "producto": {"entra"}, "cantidad": {"entra"},
             "fecha": {"entra"}, "precio": {"entra"}, "ot": {"cancela"}},
    LLEGA_MATERIAL: {"proveedor": {"*"}, "material": {"*"}, "cantidad": {"*"}, "fecha": {"*"}, "compra": set()},
    PLANTA: {"accion": {"*"}, "recurso": {"*"}, "desde": {"para"}, "hasta": {"para"}, "fecha": {"reinicia"}},
    COBRO_PAGO: {"movimiento": {"*"}, "monto": {"*"}, "fecha": {"*"}, "cuenta": {"*"}, "ticket": set()},
    NO_CONFORMIDAD: {"ot": {"*"}, "cantidad_mala": {"*"}, "fecha": {"*"}},
    DATO_MAESTRO: {"campo": {"*"}, "objeto": {"*"}, "valor": {"*"}, "desde": {"*"}},
}
ACCIONES = {PEDIDO: ("accion", {"entra", "cancela"}), PLANTA: ("accion", {"para", "reinicia"}),
            COBRO_PAGO: ("movimiento", {"cobro", "pago"})}


def validar_forma(ev: dict) -> tuple[dict, list[str]]:
    """B1, primera capa: forma del hecho (sin mirar el estado). Devuelve (hecho normalizado, errores).
    Normalizar = solo convertir fechas válidas a date; nada más se toca."""
    err: list[str] = []
    if not isinstance(ev, dict):
        return {}, ["El hecho debe ser un diccionario de campos."]
    tipo = ev.get("tipo")
    if tipo not in TIPOS_EVENTO:
        cerca = [t for t in TIPOS_EVENTO if isinstance(tipo, str) and tipo.lower() in t.lower()]
        sug = f" ¿Quiso decir «{cerca[0]}»?" if cerca else ""
        return {}, [f"Tipo de hecho desconocido: «{tipo}». Los válidos son: {', '.join(TIPOS_EVENTO)}.{sug}"]
    esquema = ESQUEMA[tipo]
    if "id" in ev:
        err.append("No envíe «id»: el sistema asigna el código del hecho (E-0001, …).")
    desconocidos = sorted(set(ev) - set(esquema) - COMUNES - {"id"})
    if desconocidos:
        err.append(f"Campos que no existen para «{tipo}»: {desconocidos}. Válidos: {sorted(esquema)}.")
    accion = "*"
    if tipo in ACCIONES:
        campo_acc, opciones = ACCIONES[tipo]
        accion = _opcion(ev.get(campo_acc), campo_acc, opciones, err) or "?"
    obligatorios = [c for c, en in esquema.items() if "*" in en or accion in en]
    faltan = [c for c in obligatorios if ev.get(c) in (None, "")]
    if faltan:
        err.append(f"Faltan campos obligatorios para «{tipo}»{'' if accion in '*?' else f' ({accion})'}: {faltan}.")
    sobran = [c for c, en in esquema.items() if en and "*" not in en and accion not in en and ev.get(c) is not None]
    if sobran and accion != "?":
        err.append(f"Con {ACCIONES[tipo][0]} = «{accion}» no corresponden los campos {sobran}.")
    h = {"tipo": tipo}
    for c in ("documento", "nota"):
        if ev.get(c) is not None:
            h[c] = _texto(ev[c], c, err)
    if ev.get("corrige") is not None:
        if not (isinstance(ev["corrige"], str) and _RE_EVENTO.match(ev["corrige"])):
            err.append(f"«corrige» debe ser el código de un hecho (E-0001); llegó «{ev['corrige']}».")
        h["corrige"] = ev["corrige"]
    for c in esquema:
        v = ev.get(c)
        if v is None or c in faltan:
            continue
        if c in ("fecha", "desde", "hasta"):
            h[c] = _fecha(v, c, err)
        elif c in ("cantidad", "cantidad_mala"):
            h[c] = _numero(v, c, err, minimo=0, estricto=True)
        elif c in ("precio", "monto"):
            h[c] = _numero(v, c, err, minimo=0, estricto=True)
        elif c == "valor":
            h[c] = v                      # se valida con el campo maestro
        elif c in ("accion", "movimiento"):
            h[c] = v
        elif c == "campo":
            h[c] = _opcion(v, c, set(CAMPOS_MAESTRO), err)
        else:
            h[c] = _texto(v, c, err)
    if tipo == DATO_MAESTRO and h.get("campo") and "valor" in h:
        campo = h["campo"]
        if campo == "tasa":
            val = _numero(h["valor"], "valor", err, minimo=0, maximo=1)
            if val is None and isinstance(h["valor"], (int, float)) and not isinstance(h["valor"], bool) and h["valor"] >= 1:
                err.append("La tasa se escribe como fracción por periodo (1.5 % = 0.015).")
        elif campo == "plazo_proveedor":
            val = _numero(h["valor"], "valor", err, minimo=0, entero=True)
        else:
            val = _numero(h["valor"], "valor", err, minimo=0)
        h["valor"] = val
    if tipo == PLANTA and h.get("desde") and h.get("hasta") and h["hasta"] < h["desde"]:
        err.append(f"Fecha al revés: «hasta» ({h['hasta']}) es anterior a «desde» ({h['desde']}).")
    return h, err


# ----------------------------------------------------------------------------- B3
class EstadoPlan:
    """B3: tickets y su estado actual (comprometido, ejecutado, pendiente), derivado de los hechos.

    Parámetros del estado base (lo que ya se sabía antes del primer hecho registrado aquí):
      hoy        fecha de corte (los hechos no pueden tener fecha posterior)
      recursos   {recurso: capacidad por día}           (C.capacidad)
      materiales lista o {material: stock inicial}
      recetas    {producto: {"horas": {recurso: h/u}, "material": {material: u/u}}}  (C.recetas)
      cuentas    lista o {cuenta: saldo inicial}
      parametros {"caja_minima": S/, "tasa": 0.015, ...}  valores iniciales (SUPUESTO) con vigencia desde «inicio»
      precios    {producto: precio}
      tickets    [{"tipo": "COMPRA", "estado": "comprometido", ...}]  tickets que ya existían (los numera el sistema)
    """

    def __init__(self, hoy, recursos=None, materiales=None, recetas=None, cuentas=None, parametros=None,
                 precios=None, tickets=None, inicio=None):
        err: list[str] = []
        hoy_d = _fecha(hoy, "hoy", err)
        inicio_d = _fecha(inicio, "inicio", err) if inicio is not None else hoy_d
        if err:
            raise Rechazo(err)
        self.hoy = hoy_d
        recursos = recursos or {}
        for r, c in recursos.items():
            _numero(c, f"capacidad de {r}", err, minimo=0)
        mats = materiales if isinstance(materiales, dict) else {m: 0 for m in (materiales or [])}
        for m, q in mats.items():
            _numero(q, f"stock inicial de {m}", err, minimo=0)
        ctas = cuentas if isinstance(cuentas, dict) else {c: 0 for c in (cuentas or [])}
        for c, s in ctas.items():
            _numero(s, f"saldo inicial de {c}", err)
        if err:
            raise Rechazo(err)
        maestros = {}
        for r, c in recursos.items():
            maestros[("capacidad", r)] = [{"valor": c, "desde": inicio_d, "hasta": None, "evento": "base"}]
        for p, v in (precios or {}).items():
            maestros[("precio", p)] = [{"valor": v, "desde": inicio_d, "hasta": None, "evento": "base"}]
        for k, v in (parametros or {}).items():
            maestros[(k, "general")] = [{"valor": v, "desde": inicio_d, "hasta": None, "evento": "base"}]
        self._base = {
            "tickets": {}, "stock": dict(mats), "caja": dict(ctas), "paradas": [], "maestros": maestros,
            "recursos": set(recursos), "materiales": set(mats), "cuentas": set(ctas),
            "recetas": copy.deepcopy(recetas) if recetas is not None else None,
            "parametros": dict(parametros or {}),
        }
        self._contador = {k: 0 for k in PREFIJO}
        for t in tickets or []:
            self._crear_base(t)
        self.eventos: list[dict] = []        # registro de hechos aceptados (nunca se borra)
        self.operaciones: list[dict] = []    # hechos + movimientos de plan/gerente/costos, en orden
        self.rechazados: list[dict] = []     # auditoría de lo que no entró
        self._estado = self._reproducir(self.operaciones)

    # ------------------------------------------------------------------ consultas
    @property
    def tickets(self) -> dict:
        return self._estado["tickets"]

    @property
    def stock(self) -> dict:
        return self._estado["stock"]

    @property
    def caja(self) -> dict:
        return self._estado["caja"]

    def ticket(self, tid):
        return self._estado["tickets"].get(tid)

    def evento(self, eid):
        return next((e for e in self.eventos if e["id"] == eid), None)

    def valor_vigente(self, campo, objeto="general", fecha=None):
        """Valor del dato maestro vigente en la fecha (B0). None si no hay."""
        f = fecha or self.hoy
        for v in self._estado["maestros"].get((campo, objeto), []):
            if v["desde"] <= f and (v["hasta"] is None or f <= v["hasta"]):
                return v["valor"]
        return None

    def capacidad(self, recurso, fecha):
        """Capacidad del recurso en una fecha: valor maestro vigente, 0 si hay parada ese día."""
        for p in self._estado["paradas"]:
            if p["recurso"] == recurso and p["desde"] <= fecha and (p["hasta"] is None or fecha <= p["hasta"]):
                return 0
        return self.valor_vigente("capacidad", recurso, fecha)

    def historial_maestro(self, campo, objeto="general"):
        return copy.deepcopy(self._estado["maestros"].get((campo, objeto), []))

    def vencidos(self):
        """Tickets cuya fecha ya pasó sin el hecho que los cumple (desviación de oportunidad, §6.2.3.4):
        p. ej. «el camión no llegó» = COMPRA comprometida con fecha de llegada vencida, sin recepción."""
        out = []
        for t in self.tickets.values():
            if t["tipo"] == "COMPRA" and t["estado"] == "comprometido" and t.get("fecha_llegada") \
                    and t["fecha_llegada"] < self.hoy:
                out.append({"ticket": t["id"], "esperado": t["fecha_llegada"], "falta": t["cantidad"] - t["recibido"]})
            if t["tipo"] == "OT" and t["estado"] in ("comprometido", "en ejecución") and t.get("fecha_entrega") \
                    and t["fecha_entrega"] < self.hoy:
                out.append({"ticket": t["id"], "esperado": t["fecha_entrega"], "falta": t["cantidad"]})
        return out

    # ------------------------------------------------------------------ B1 + B3: registrar un hecho
    def registrar(self, hecho: dict) -> dict:
        h, err = validar_forma(hecho)
        if err:
            return self._rechazar(hecho, err)
        if h.get("documento"):
            dup = next((e for e in self.eventos if e["tipo"] == h["tipo"] and e.get("documento") == h["documento"]
                        and not e.get("anulado_por") and e["id"] != h.get("corrige")), None)
            if dup:
                return self._rechazar(hecho, [f"El documento «{h['documento']}» ya está registrado en {dup['id']}. "
                                              "Si es una corrección, envíe «corrige»: \"" + dup["id"] + "\"."])
        for c in ("fecha",):
            if h.get(c) and h["tipo"] != PEDIDO and h[c] > self.hoy:
                return self._rechazar(hecho, [f"«{c}» ({h[c]}) es posterior a hoy ({self.hoy}): un hecho no puede "
                                              "haber ocurrido en el futuro."])
        if h["tipo"] == PLANTA and h.get("desde") and h["desde"] > self.hoy:
            return self._rechazar(hecho, [f"La parada empieza el {h['desde']}, después de hoy ({self.hoy}). Una parada "
                                          "futura es un ticket (mantenimiento programado), no un hecho."])
        if h["tipo"] == PEDIDO and h.get("accion") == "entra" and h["fecha"] < self.hoy:
            return self._rechazar(hecho, [f"La fecha de entrega ({h['fecha']}) es anterior a hoy ({self.hoy})."])

        nid = f"E-{len(self.eventos) + 1:04d}"
        h["id"] = nid
        h["registrado"] = self.hoy
        pos = len(self.operaciones)
        if h.get("corrige"):
            orig = self.evento(h["corrige"])
            if orig is None:
                return self._rechazar(hecho, [f"No existe el hecho {h['corrige']} que se quiere corregir."])
            if orig.get("anulado_por"):
                return self._rechazar(hecho, [f"{orig['id']} ya fue corregido por {orig['anulado_por']}; "
                                              f"corrija ese hecho."])
            if orig["tipo"] != h["tipo"]:
                return self._rechazar(hecho, [f"{orig['id']} es «{orig['tipo']}»; su corrección debe ser del "
                                              "mismo tipo."])
            for k in ("ot_creada", "reproceso_creado"):     # la corrección conserva los códigos asignados
                if k in orig:
                    h[k] = orig[k]
            pos = next(i for i, o in enumerate(self.operaciones) if o.get("id") == orig["id"])
        else:
            if h["tipo"] == PEDIDO and h["accion"] == "entra":
                h["ot_creada"] = self._nuevo_codigo("OT")
        ops = [o for o in self.operaciones]
        if h.get("corrige"):
            ops[pos] = {**h, "_op": "hecho"}
        else:
            ops.append({**h, "_op": "hecho"})
        try:
            nuevo = self._reproducir(ops, validar_contra=h["id"])
        except Rechazo as r:
            if h["tipo"] == PEDIDO and h.get("accion") == "entra" and not h.get("corrige"):
                self._contador["OT"] -= 1
            return self._rechazar(hecho, r.errores)
        # NC sobre OT terminada: el código del reproceso queda fijo en el hecho
        if "reproceso_creado" in nuevo["_ultimo"].get(h["id"], {}):
            h["reproceso_creado"] = nuevo["_ultimo"][h["id"]]["reproceso_creado"]
            ops[pos if h.get("corrige") else -1]["reproceso_creado"] = h["reproceso_creado"]
        efectos = nuevo["_ultimo"].get(h["id"], {})
        self.eventos.append(dict(h))
        if h.get("corrige"):
            self.evento(h["corrige"])["anulado_por"] = h["id"]
        self.operaciones = ops
        self._estado = nuevo
        return {"aceptado": True, "id": h["id"], "tipo": h["tipo"], "ticket_tipo": TICKET_DE_EVENTO[h["tipo"]],
                "tickets": efectos.get("tickets", []), "afectados": efectos.get("afectados", []),
                "avisos": efectos.get("avisos", []), "recalcular": efectos.get("recalcular", True),
                "corrige": h.get("corrige"), "errores": []}

    # ------------------------------------------------------------------ movimientos fuera de un hecho
    def crear_ticket(self, tipo, datos: dict, estado="propuesto", origen="plan") -> dict:
        """Ticket que propone el plan (B4) o aprueba el gerente (B9). Código asignado por el sistema."""
        err = []
        if tipo not in MAQUINAS:
            err.append(f"Tipo de ticket desconocido «{tipo}»; válidos: {list(MAQUINAS)}.")
        elif estado not in MAQUINAS[tipo]:
            err.append(f"«{estado}» no es un estado de {tipo}; válidos: {list(MAQUINAS[tipo])}.")
        if origen not in ORIGENES:
            err.append(f"Origen «{origen}» no válido; válidos: {ORIGENES}.")
        if err:
            return self._rechazar({"crear_ticket": tipo, **datos}, err)
        tid = self._nuevo_codigo(tipo)
        op = {"_op": "crear", "id_ticket": tid, "tipo_ticket": tipo, "datos": dict(datos), "estado": estado,
              "origen": origen, "fecha": self.hoy}
        return self._aplicar_op(op, tid)

    def mover(self, ticket_id, nuevo_estado, origen="gerente", nota=None) -> dict:
        """Cambio de estado decidido por el gerente (U.gerente) o informado por costos (C.carga)."""
        if origen not in ORIGENES:
            return self._rechazar({"mover": ticket_id}, [f"Origen «{origen}» no válido; válidos: {ORIGENES}."])
        op = {"_op": "mover", "id_ticket": ticket_id, "estado": nuevo_estado, "origen": origen, "fecha": self.hoy,
              "nota": nota}
        return self._aplicar_op(op, ticket_id)

    def avanzar(self, nueva_fecha):
        err = []
        f = _fecha(nueva_fecha, "hoy", err)
        if err:
            raise Rechazo(err)
        if f < self.hoy:
            raise Rechazo([f"No se puede retroceder la fecha de corte ({self.hoy} → {f})."])
        self.hoy = f

    # ------------------------------------------------------------------ internos
    def _nuevo_codigo(self, tipo):
        self._contador[tipo] += 1
        return f"{PREFIJO[tipo]}-{self._contador[tipo]:04d}"

    def _crear_base(self, t):
        err = []
        tipo = t.get("tipo")
        if tipo not in MAQUINAS:
            raise Rechazo([f"Ticket inicial con tipo desconocido «{tipo}»."])
        est = t.get("estado", "propuesto")
        if est not in MAQUINAS[tipo]:
            raise Rechazo([f"Ticket inicial {tipo} con estado «{est}» que no existe; válidos: {list(MAQUINAS[tipo])}."])
        desconocidos = set(t) - set(CAMPOS_TICKET[tipo]) - {"tipo", "estado"}
        if desconocidos:
            raise Rechazo([f"Ticket inicial {tipo} con campos que no existen: {sorted(desconocidos)}."])
        tid = self._nuevo_codigo(tipo)
        datos = {k: v for k, v in t.items() if k not in ("tipo", "estado")}
        for k in ("fecha_entrega", "fecha_pedido", "fecha_llegada", "fecha_toma", "fecha_pago", "fecha", "inicio", "fin"):
            if datos.get(k) is not None:
                datos[k] = _fecha(datos[k], k, err)
        if err:
            raise Rechazo(err)
        self._base["tickets"][tid] = {"id": tid, "tipo": tipo, "estado": est, **datos,
                                      "historial": [{"estado": est, "origen": "base", "fecha": None}]}
        if tipo == "COMPRA":
            self._base["tickets"][tid]["recibido"] = 0

    def _aplicar_op(self, op, tid):
        ops = self.operaciones + [op]
        try:
            nuevo = self._reproducir(ops)
        except Rechazo as r:
            return self._rechazar(op, r.errores)
        self.operaciones = ops
        self._estado = nuevo
        return {"aceptado": True, "id": tid, "estado": nuevo["tickets"][tid]["estado"], "errores": [], "avisos": []}

    def _rechazar(self, hecho, errores):
        self.rechazados.append({"hecho": hecho, "errores": list(errores), "fecha": self.hoy})
        return {"aceptado": False, "id": None, "errores": list(errores), "avisos": [], "tickets": [], "afectados": []}

    # ------------------------------------------------------------------ reproducción
    def _reproducir(self, ops, validar_contra=None) -> dict:
        s = copy.deepcopy(self._base)
        s["_ultimo"] = {}
        for op in ops:
            if op["_op"] == "hecho":
                ef = _APLICAR[op["tipo"]](self, s, op)
                s["_ultimo"][op["id"]] = ef
            elif op["_op"] == "crear":
                s["tickets"][op["id_ticket"]] = {"id": op["id_ticket"], "tipo": op["tipo_ticket"],
                                                 "estado": op["estado"], **op["datos"],
                                                 "historial": [{"estado": op["estado"], "origen": op["origen"],
                                                                "fecha": op["fecha"]}]}
                if op["tipo_ticket"] == "COMPRA":
                    s["tickets"][op["id_ticket"]].setdefault("recibido", 0)
            elif op["_op"] == "mover":
                _transicion(s, op["id_ticket"], op["estado"], op["origen"], op["fecha"])
        return s


def _transicion(s, tid, nuevo, origen, fecha):
    t = s["tickets"].get(tid)
    if t is None:
        raise Rechazo([f"No existe el ticket {tid}."])
    maq = MAQUINAS[t["tipo"]]
    if nuevo not in maq:
        sug = " ¿Quiso decir «en ejecución»?" if nuevo == "en curso" else ""
        raise Rechazo([f"«{nuevo}» no es un estado de {t['tipo']}; válidos: {list(maq)}.{sug}"])
    if nuevo not in maq[t["estado"]]:
        permitidos = sorted(maq[t["estado"]]) or ["ninguno (estado final)"]
        raise Rechazo([f"Transición inválida en {tid} ({t['tipo']}): «{t['estado']}» → «{nuevo}». "
                       f"Desde «{t['estado']}» solo se puede pasar a: {', '.join(permitidos)}."])
    t["estado"] = nuevo
    t["historial"].append({"estado": nuevo, "origen": origen, "fecha": fecha})


def _ticket(s, tid, tipo):
    t = s["tickets"].get(tid)
    if t is None:
        raise Rechazo([f"No existe el ticket {tid}."])
    if t["tipo"] != tipo:
        raise Rechazo([f"{tid} es un ticket {t['tipo']}, no {tipo}."])
    return t


def _usa(s, ot, clave, valor):
    rec = (s["recetas"] or {}).get(ot.get("producto"), {})
    if clave == "recurso":
        return ot.get("recurso") == valor or (ot.get("recurso") is None and valor in rec.get("horas", {}))
    return valor in rec.get("material", {})


def _abiertas(s):
    return [t for t in s["tickets"].values() if t["tipo"] == "OT" and t["estado"] in ("comprometido", "en ejecución")]


# ----------------------------------------------------------------------------- efecto de cada hecho
def _ap_pedido(est, s, h):
    if h["accion"] == "entra":
        av = []
        if s["recetas"] is None:
            av.append("No hay catálogo de recetas cargado: la calculadora no podrá programar esta OT hasta tenerlo.")
        elif h["producto"] not in s["recetas"]:
            raise Rechazo([f"El producto «{h['producto']}» no tiene receta en el catálogo (C.recetas); "
                           "regístrela antes del pedido."])
        tid = h["ot_creada"]
        s["tickets"][tid] = {"id": tid, "tipo": "OT", "estado": "comprometido", "producto": h["producto"],
                             "cantidad": h["cantidad"], "fecha_entrega": h["fecha"], "recurso": None, "inicio": None,
                             "fin": None, "cliente": h["cliente"], "precio": h["precio"], "origen": h["id"],
                             "malas": 0, "reproceso": 0,
                             "historial": [{"estado": "comprometido", "origen": h["id"], "fecha": h["registrado"]}]}
        return {"tickets": [tid], "afectados": [tid], "avisos": av, "recalcular": True}
    t = _ticket(s, h["ot"], "OT")
    _transicion(s, t["id"], "cancelado", h["id"], h["registrado"])
    return {"tickets": [t["id"]], "afectados": [t["id"]], "avisos": [], "recalcular": True}


def _ap_llegada(est, s, h):
    if s["materiales"] and h["material"] not in s["materiales"]:
        raise Rechazo([f"El material «{h['material']}» no está en el catálogo de materiales."])
    if h.get("compra"):
        c = _ticket(s, h["compra"], "COMPRA")
        dif = [f"{k}: ticket «{c.get(k)}», hecho «{h[k]}»" for k in ("material", "proveedor") if c.get(k) != h[k]]
        if dif:
            raise Rechazo([f"La llegada no coincide con {c['id']}: " + "; ".join(dif) + "."])
        if c["estado"] != "comprometido":
            raise Rechazo([f"{c['id']} está «{c['estado']}»; solo se recibe una COMPRA comprometida."])
    else:
        cand = [t for t in s["tickets"].values() if t["tipo"] == "COMPRA" and t["estado"] == "comprometido"
                and t.get("material") == h["material"] and t.get("proveedor") == h["proveedor"]]
        if not cand:
            raise Rechazo([f"No hay COMPRA comprometida de «{h['material']}» con «{h['proveedor']}». Registre la "
                           "compra (ticket) o indique «compra»."])
        if len(cand) > 1:
            raise Rechazo([f"Hay {len(cand)} compras comprometidas de «{h['material']}» con «{h['proveedor']}» "
                           f"({', '.join(t['id'] for t in cand)}); indique cuál en «compra»."])
        c = cand[0]
    pendiente = c["cantidad"] - c.get("recibido", 0)
    if h["cantidad"] > pendiente + 1e-9:
        raise Rechazo([f"Llegan {h['cantidad']} de «{h['material']}» pero a {c['id']} le faltan {pendiente}. "
                       "Un exceso se registra como otra compra."])
    c["recibido"] = c.get("recibido", 0) + h["cantidad"]
    s["stock"][h["material"]] = s["stock"].get(h["material"], 0) + h["cantidad"]
    av = []
    if abs(c["recibido"] - c["cantidad"]) <= 1e-9:
        c["fecha_llegada"] = h["fecha"]
        _transicion(s, c["id"], "recibido", h["id"], h["registrado"])
    else:
        av.append(f"Recepción parcial: {c['id']} sigue comprometida; faltan {c['cantidad'] - c['recibido']}.")
    liberadas = [t["id"] for t in _abiertas(s) if _usa(s, t, "material", h["material"])]
    return {"tickets": [c["id"]], "afectados": liberadas, "avisos": av, "recalcular": True}


def _ap_planta(est, s, h):
    if h["recurso"] not in s["recursos"]:
        raise Rechazo([f"El recurso «{h['recurso']}» no existe; recursos: {sorted(s['recursos'])}."])
    if h["accion"] == "para":
        for p in s["paradas"]:
            if p["recurso"] == h["recurso"] and not (h["hasta"] < p["desde"] or (p["hasta"] and h["desde"] > p["hasta"])):
                raise Rechazo([f"Ya hay una parada de {h['recurso']} del {p['desde']} al {p['hasta']} ({p['evento']}) "
                               "que se cruza con esta; si cambió, corrija ese hecho."])
        s["paradas"].append({"recurso": h["recurso"], "desde": h["desde"], "hasta": h["hasta"], "evento": h["id"]})
        d0, d1 = h["desde"], h["hasta"]
    else:
        act = [p for p in s["paradas"] if p["recurso"] == h["recurso"] and p["desde"] <= h["fecha"]
               and (p["hasta"] is None or h["fecha"] <= p["hasta"])]
        if not act:
            raise Rechazo([f"{h['recurso']} no está parado el {h['fecha']}: no hay nada que reiniciar."])
        p = act[0]
        if h["fecha"] == p["desde"]:
            raise Rechazo([f"El reinicio no puede ser el mismo día en que empezó la parada ({p['evento']}); "
                           "corrija ese hecho."])
        d0, d1 = h["fecha"], p["hasta"]
        p["hasta"] = h["fecha"] - timedelta(days=1)
        p["reiniciado_por"] = h["id"]
    afect = [t["id"] for t in _abiertas(s) if _usa(s, t, "recurso", h["recurso"])
             and (t.get("inicio") is None or not (t.get("fin") and t["fin"] < d0) and not (d1 and t["inicio"] > d1))]
    return {"tickets": afect, "afectados": afect, "avisos": [], "recalcular": True}


def _ap_caja(est, s, h):
    if s["cuentas"] and h["cuenta"] not in s["cuentas"]:
        raise Rechazo([f"La cuenta «{h['cuenta']}» no existe; cuentas: {sorted(s['cuentas'])}."])
    signo = 1 if h["movimiento"] == "cobro" else -1
    tk = []
    av = []
    if h.get("ticket"):
        f = _ticket(s, h["ticket"], "FINANCIAMIENTO")
        if h["movimiento"] == "cobro":
            if abs(h["monto"] - f["monto"]) > 1e-9:
                raise Rechazo([f"El desembolso ({h['monto']}) no es igual al monto de {f['id']} ({f['monto']})."])
            _transicion(s, f["id"], "tomado", h["id"], h["registrado"])
            f["fecha_toma"] = h["fecha"]
        else:
            if f["estado"] == "tomado" and h["monto"] < f["monto"] - 1e-9:
                raise Rechazo([f"El pago ({h['monto']}) es menor que el principal de {f['id']} ({f['monto']}); "
                               "un pago parcial no está previsto en el ticket."])
            _transicion(s, f["id"], "pagado", h["id"], h["registrado"])
            f["fecha_pago"] = h["fecha"]
            f["interes_pagado"] = round(h["monto"] - f["monto"], 10)
        tk = [f["id"]]
    s["caja"][h["cuenta"]] = s["caja"].get(h["cuenta"], 0) + signo * h["monto"]
    total = sum(s["caja"].values())
    minimo = _vigente(s, "caja_minima", "general", h["fecha"])
    if minimo is not None and total < minimo:
        av.append(f"Caja real {total:,.2f} por debajo de la caja mínima {minimo:,.2f} (R8): hay que financiar o "
                  "reprogramar.")
    return {"tickets": tk, "afectados": tk, "avisos": av, "recalcular": bool(av) or bool(tk)}


def _ap_nc(est, s, h):
    t = _ticket(s, h["ot"], "OT")
    if t["estado"] not in ("en ejecución", "terminado"):
        raise Rechazo([f"{t['id']} está «{t['estado']}»: no puede haber producto malo de una OT que no se ha "
                       "empezado."])
    ya = t.get("malas", 0)
    if h["cantidad_mala"] > t["cantidad"] - ya + 1e-9:
        raise Rechazo([f"Cantidad mala ({h['cantidad_mala']}) mayor que lo que queda bueno de {t['id']} "
                       f"({t['cantidad'] - ya})."])
    t["malas"] = ya + h["cantidad_mala"]
    rec = (s["recetas"] or {}).get(t["producto"])
    av = []
    if rec:
        horas = {r: h_u * h["cantidad_mala"] for r, h_u in rec.get("horas", {}).items()}
        mat = {m: u * h["cantidad_mala"] for m, u in rec.get("material", {}).items()}
    else:
        horas = mat = None
        av.append(f"No hay receta de «{t['producto']}»: no se pueden calcular las horas y el material del "
                  "reproceso (no se asume 0).")
    if t["estado"] == "en ejecución":
        t["reproceso"] = t.get("reproceso", 0) + h["cantidad_mala"]
        return {"tickets": [t["id"]], "afectados": [t["id"]], "avisos": av, "recalcular": True,
                "reproceso": {"cantidad": h["cantidad_mala"], "horas": horas, "material": mat}}
    # OT terminada: no vuelve atrás; el reproceso es otra OT comprometida, sin precio (no es venta nueva)
    rid = h.get("reproceso_creado") or est._nuevo_codigo("OT")
    entrega = max(t["fecha_entrega"], h["registrado"]) if t.get("fecha_entrega") else h["registrado"]
    s["tickets"][rid] = {"id": rid, "tipo": "OT", "estado": "comprometido", "producto": t["producto"],
                         "cantidad": h["cantidad_mala"], "fecha_entrega": entrega, "recurso": None, "inicio": None,
                         "fin": None, "cliente": t.get("cliente"), "precio": 0, "origen": h["id"],
                         "reproceso_de": t["id"], "malas": 0, "reproceso": 0,
                         "historial": [{"estado": "comprometido", "origen": h["id"], "fecha": h["registrado"]}]}
    return {"tickets": [t["id"], rid], "afectados": [rid], "avisos": av, "recalcular": True,
            "reproceso_creado": rid, "reproceso": {"cantidad": h["cantidad_mala"], "horas": horas, "material": mat}}


def _vigente(s, campo, objeto, fecha):
    for v in s["maestros"].get((campo, objeto), []):
        if v["desde"] <= fecha and (v["hasta"] is None or fecha <= v["hasta"]):
            return v["valor"]
    return None


def _ap_maestro(est, s, h):
    campo, obj = h["campo"], h["objeto"]
    if campo == "capacidad" and obj not in s["recursos"]:
        raise Rechazo([f"«{obj}» no es un recurso; la capacidad se cambia por recurso: {sorted(s['recursos'])}."])
    if campo == "precio" and s["recetas"] is not None and obj not in s["recetas"]:
        raise Rechazo([f"«{obj}» no es un producto del catálogo de recetas."])
    if campo == "tasa" and obj != "general" and not obj.startswith("linea:"):
        raise Rechazo(["Para «tasa», «objeto» es «general» o «linea:<nombre de la línea de crédito>»."])
    hist = s["maestros"].setdefault((campo, obj), [])
    abierto = next((v for v in hist if v["hasta"] is None), None)
    if abierto and h["desde"] <= abierto["desde"]:
        raise Rechazo([f"Ya hay un valor de «{campo}» para «{obj}» vigente desde {abierto['desde']}; un cambio con "
                       f"fecha {h['desde']} reescribiría la historia. Si ese valor estaba mal, corrija el hecho "
                       f"{abierto['evento']}."])
    if abierto:
        abierto["hasta"] = h["desde"] - timedelta(days=1)
        abierto["cerrado_por"] = h["id"]
    hist.append({"valor": h["valor"], "desde": h["desde"], "hasta": None, "evento": h["id"]})
    return {"tickets": [], "afectados": [], "avisos": [], "recalcular": True}


_APLICAR = {PEDIDO: _ap_pedido, LLEGA_MATERIAL: _ap_llegada, PLANTA: _ap_planta, COBRO_PAGO: _ap_caja,
            NO_CONFORMIDAD: _ap_nc, DATO_MAESTRO: _ap_maestro}
