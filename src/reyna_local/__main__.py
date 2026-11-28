"""Servidor local del piloto Excel/Python."""

import argparse
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import math
import re
from pathlib import Path
import signal
import sys
import traceback
from urllib.parse import parse_qs, unquote, urlsplit
import webbrowser

from .receipt_audit import audit_receipts
from .exportar import exportar, TIPOS
from .store import Problem, Store, load_data, content_bytes, metadata, TRANSACTIONS, TRANSACCIONES_E26, detectar_transacciones_e26
from .contrato import validar


INDEX = Path(__file__).parent / "web" / "index.html"
BODY_LIMIT = 1024 * 1024
SOCKET_TIMEOUT = 10
SECURITY_POLICY = (
    "default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; "
    "connect-src 'self'; base-uri 'none'; frame-ancestors 'none'; form-action 'self'"
)


class ReynaServer(ThreadingHTTPServer):
    daemon_threads = False

    def __init__(self, data_dir, port):
        self.store = Store(data_dir)
        self.index = INDEX.read_bytes()
        super().__init__(("127.0.0.1", port), ReynaHandler)
        actual_port = self.server_port
        self.hosts = {f"127.0.0.1:{actual_port}", f"localhost:{actual_port}"}
        if actual_port == 80:
            self.hosts.update({"127.0.0.1", "localhost"})


class ReynaHandler(BaseHTTPRequestHandler):
    timeout = SOCKET_TIMEOUT

    def _send(self, status, body, content_type):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Content-Security-Policy", SECURITY_POLICY)
        if status == HTTPStatus.METHOD_NOT_ALLOWED:
            self.send_header("Allow", "GET, POST")
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(body)

    def _json(self, status, payload):
        body = json.dumps(payload, ensure_ascii=False, allow_nan=False).encode("utf-8")
        self._send(status, body, "application/json; charset=utf-8")

    def _check_peer(self):
        hosts = self.headers.get_all("Host", [])
        host = hosts[0].lower() if len(hosts) == 1 else None
        if host not in self.server.hosts:
            raise Problem(HTTPStatus.FORBIDDEN, "El servidor solo admite su dirección local.")
        origins = self.headers.get_all("Origin", [])
        origin_host = host.removesuffix(":80") if self.server.server_port == 80 else host
        if origins and origins != [f"http://{origin_host}"]:
            raise Problem(HTTPStatus.FORBIDDEN, "Abre la pantalla desde la misma dirección del servidor local.")

    def _raw_body(self, limite=20 * 1024 * 1024):
        lengths = self.headers.get_all("Content-Length", [])
        if self.headers.get("Transfer-Encoding") or len(lengths) != 1 or not lengths[0].isdigit():
            raise Problem(HTTPStatus.BAD_REQUEST, "Envía el archivo con su tamaño indicado.")
        n = int(lengths[0])
        if n > limite:
            raise Problem(HTTPStatus.REQUEST_ENTITY_TOO_LARGE, "El libro supera el límite de 20 MiB.")
        raw = self.rfile.read(n)
        if len(raw) != n:
            raise Problem(HTTPStatus.BAD_REQUEST, "El archivo recibido está incompleto.")
        return raw

    def _body(self):
        if self.headers.get("Transfer-Encoding"):
            raise Problem(HTTPStatus.BAD_REQUEST, "Envía un cuerpo JSON con tamaño indicado.")
        content_types = self.headers.get_all("Content-Type", [])
        if len(content_types) != 1 or self.headers.get_content_type() != "application/json":
            raise Problem(HTTPStatus.UNSUPPORTED_MEDIA_TYPE, "Envía los datos como application/json.")
        lengths = self.headers.get_all("Content-Length", [])
        if len(lengths) != 1 or not lengths[0].isascii() or not lengths[0].isdigit():
            raise Problem(HTTPStatus.BAD_REQUEST, "El tamaño del cuerpo JSON es obligatorio.")
        try:
            length = int(lengths[0])
        except ValueError:
            raise Problem(HTTPStatus.REQUEST_ENTITY_TOO_LARGE, "El cuerpo supera el límite de 1 MiB.") from None
        if length > BODY_LIMIT:
            raise Problem(HTTPStatus.REQUEST_ENTITY_TOO_LARGE, "El cuerpo supera el límite de 1 MiB.")
        try:
            raw = self.rfile.read(length)
        except TimeoutError:
            raise Problem(HTTPStatus.REQUEST_TIMEOUT, "Se agotó el tiempo de espera al recibir el cuerpo.") from None
        if len(raw) != length:
            raise Problem(HTTPStatus.BAD_REQUEST, "El cuerpo recibido está incompleto.")
        try:
            data = json.loads(
                raw.decode("utf-8"),
                parse_constant=self._invalid_json_constant,
                parse_float=self._finite_float,
            )
        except (ValueError, RecursionError):
            raise Problem(HTTPStatus.BAD_REQUEST, "El cuerpo debe ser JSON UTF-8 válido.") from None
        if not isinstance(data, dict):
            raise Problem(HTTPStatus.BAD_REQUEST, "El cuerpo debe ser un objeto JSON.")
        return data

    @staticmethod
    def _invalid_json_constant(value):
        raise ValueError(f"Constante JSON inválida: {value}")

    @staticmethod
    def _finite_float(value):
        number = float(value)
        if not math.isfinite(number):
            raise ValueError("Número JSON fuera de rango")
        return number

    @staticmethod
    def _pagination(query):
        try:
            params = parse_qs(query, keep_blank_values=True, max_num_fields=2)
            if set(params) - {"offset", "limit"} or any(len(values) != 1 for values in params.values()):
                raise ValueError
            offset = int(params.get("offset", ["0"])[0])
            limit = int(params.get("limit", ["100"])[0])
            if offset < 0 or not 1 <= limit <= 500:
                raise ValueError
        except ValueError:
            raise Problem(HTTPStatus.BAD_REQUEST, "Usa offset desde 0 y limit entre 1 y 500.") from None
        return offset, limit

    def _route(self):
        method = self.command
        try:
            target = urlsplit(self.path)
        except ValueError:
            raise Problem(HTTPStatus.BAD_REQUEST, "La dirección de la solicitud no es válida.") from None
        if target.scheme or target.netloc or target.fragment:
            raise Problem(HTTPStatus.BAD_REQUEST, "Usa una ruta del servidor local.")
        parts = target.path.split("/")
        store = self.server.store
        if target.path in {"/", "/index.html"} and method == "GET":
            self._send(HTTPStatus.OK, self.server.index, "text/html; charset=utf-8")
            return
        if target.path == "/api/laboratorio/crear" and method == "POST":
            from .laboratorio import crear
            self._json(HTTPStatus.CREATED, crear(store, self._body().get('original')))
            return
        if target.path == "/api/laboratorio/comparar" and method == "POST":
            from .laboratorio import comparar_espacios
            body = self._body()
            try:
                result = comparar_espacios(store, body.get('laboratorio'), body.get('periodo'), body.get('sintesis'))
            except ValueError as exc: raise Problem(422, str(exc)) from None
            self._json(HTTPStatus.OK, result)
            return
        if target.path == "/api/libros" and method == "GET":
            from .calculo_local import catalogo
            self._json(HTTPStatus.OK, {"libros": catalogo(store.root)})
            return
        if target.path == "/api/libros/versiones" and method == "GET":
            from .calculo_local import versiones
            s_ = parse_qs(target.query).get("id", [""])[0]
            if not re.fullmatch(r"[a-z0-9_]{1,60}", s_): raise Problem(400, "Elige una empresa válida.")
            self._json(HTTPStatus.OK, {"versiones": versiones(store.root, s_)})
            return
        if target.path == "/api/libros/restaurar" and method == "POST":
            from .calculo_local import restaurar
            q = parse_qs(target.query); s_ = q.get("id", [""])[0]; v_ = q.get("version", [""])[0]
            if not re.fullmatch(r"[a-z0-9_]{1,60}", s_) or not re.fullmatch(r"[a-z0-9_]{1,60}__\d{8}-\d{6}(?:-\d{6})?\.xlsx", v_):
                raise Problem(400, "Elige una versión válida.")
            self._body()
            try:
                self._json(HTTPStatus.OK, restaurar(store.root, s_, v_))
            except ValueError as exc:
                raise Problem(404, str(exc)) from None
            return
        if target.path.startswith("/api/cierres"):
            from . import cierre as CI
            from .calculo_local import calcular as _calc, ruta_libro
            q = {k: v[0] for k, v in parse_qs(target.query).items()}
            for k, patron in (("empresa", r"[a-z0-9_]{1,60}"), ("periodo", r"\d{4}-(0[1-9]|1[0-2])"), ("id", r"[a-z0-9_]+_\d{4}-\d{2}_v\d+")):
                if k in q and not re.fullmatch(patron, q[k]): raise Problem(400, "Parámetros inválidos.")
            try:
                if target.path == "/api/cierres" and method == "GET":
                    self._json(HTTPStatus.OK, {"cierres": CI.listar(store.root, q.get("empresa"))}); return
                if target.path == "/api/cierres/verificar" and method == "GET":
                    self._json(HTTPStatus.OK, CI.verificar(store.root, q["id"])); return
                if target.path == "/api/cierres/emitir" and method == "POST":
                    b = self._body()
                    self._json(HTTPStatus.CREATED, CI.emitir(store.root, q["empresa"], q["periodo"], str(b.get("usuario") or ""), _calc,
                                                             ruta_libro(store.root, q["empresa"]), str(b.get("motivo") or "")[:500])); return
                if target.path == "/api/cierres/accion" and method == "POST":
                    b = self._body(); emp = q["id"].rsplit("_", 2)[0]
                    self._json(HTTPStatus.OK, CI.accion(store.root, q["id"], str(b.get("accion") or ""), str(b.get("usuario") or ""),
                                                        str(b.get("comentario") or "")[:500], ruta_libro(store.root, emp))); return
            except (CI.Rechazo, ValueError) as exc:
                raise Problem(422, str(exc)) from None
            except KeyError:
                raise Problem(400, "Faltan parámetros.") from None
            raise Problem(HTTPStatus.NOT_FOUND, "La ruta no existe.")
        if target.path == "/api/libros/operar" and method == "POST":
            from .calculo_local import ruta_libro
            s_ = parse_qs(target.query).get("id", [""])[0]
            if not re.fullmatch(r"[a-z0-9_]{1,60}", s_) or s_.startswith("esp_"): raise Problem(400, "Elige un libro de empresa válido.")
            body = self._body()
            try:
                ruta = ruta_libro(store.root, s_)
            except ValueError as exc:
                raise Problem(404, str(exc)) from None
            nombre = str(body.get("name") or f"Operación {s_}")[:160]
            self._json(HTTPStatus.CREATED, store.create({"name": nombre, "workbook_path": str(ruta)}))
            return
        if target.path == "/api/libros" and method == "POST":
            from .calculo_local import registrar, YaExiste
            try:
                ficha, errores = registrar(store.root, self._raw_body(), reemplazar=parse_qs(target.query).get("reemplazar") == ["1"])
            except YaExiste as e:
                self._json(409, {"error": f"Ya existe un libro de «{e.ficha['nombre']}». ¿Reemplazarlo? La versión actual se guardará y podrás volver a ella.",
                                 "existe": e.ficha})
                return
            if errores:
                self._json(422, {"error": "El libro no cumple el formato DBD. Corrige estos puntos y vuelve a cargarlo.", "errores": errores})
            else:
                self._json(HTTPStatus.CREATED, ficha)
            return
        if target.path == "/api/suficiencia" and method == "GET":
            from .suficiencia import detectar_libro
            from .calculo_local import ruta_libro
            params = parse_qs(target.query, keep_blank_values=True)
            empresa = params.get('empresa', [''])[0]
            if set(params) != {'empresa'} or len(params['empresa']) != 1 or not re.fullmatch(r'[a-z0-9_]{1,60}', empresa):
                raise Problem(400, 'Empresa inválida.')
            try: resultado = detectar_libro(ruta_libro(store.root, empresa))
            except (ValueError, OSError) as exc: raise Problem(422, str(exc)) from None
            self._json(200, resultado)
            return
        if target.path == "/api/plantilla-nivel" and method == "GET":
            from .libro_dbd import plantilla_vacia
            from .suficiencia import ETIQUETAS
            from openpyxl import load_workbook
            import tempfile
            params = parse_qs(target.query, keep_blank_values=True)
            if set(params) != {'nivel'} or len(params['nivel']) != 1 or params['nivel'][0] not in tuple(map(str, range(5))):
                raise Problem(400, 'Nivel inválido.')
            nivel = int(params['nivel'][0])
            with tempfile.TemporaryDirectory() as temp:
                path = Path(plantilla_vacia(Path(temp) / 'plantilla.xlsx'))
                wb = load_workbook(path); ws = wb.create_sheet('NIVEL', 0)
                ws.append(['Guía de datos para el nivel', nivel])
                ws.append(['La plantilla conserva el formato DBD completo; esta guía no acredita el nivel.'])
                for i, etiqueta in enumerate(ETIQUETAS): ws.append([i, etiqueta, 'Requerido' if i <= nivel else 'Posterior'])
                wb.save(path); wb.close(); contenido = path.read_bytes()
            self.send_response(HTTPStatus.OK)
            self.send_header('Content-Type', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
            self.send_header('Content-Disposition', f'attachment; filename="plantilla_nivel_{nivel}.xlsx"')
            self.send_header('Content-Length', str(len(contenido))); self.end_headers(); self.wfile.write(contenido)
            return
        if target.path == "/api/plantilla" and method == "GET":
            from .libro_dbd import plantilla_vacia
            import tempfile as _t
            with _t.TemporaryDirectory() as d:
                contenido = Path(plantilla_vacia(Path(d) / "plantilla.xlsx")).read_bytes()
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
            self.send_header("Content-Disposition", 'attachment; filename="plantilla_dbd_reyna.xlsx"')
            self.send_header("Content-Length", str(len(contenido))); self.end_headers(); self.wfile.write(contenido)
            return
        if target.path == "/api/aprendizaje" and method == "GET":
            from .aprendizaje import leer_capa
            try:
                q = parse_qs(target.query, keep_blank_values=True, max_num_fields=1)
                if set(q) != {'empresa'} or len(q['empresa']) != 1 or not re.fullmatch(r'[a-z0-9_]{1,60}',q['empresa'][0]): raise ValueError('Empresa inválida.')
                data = leer_capa(q['empresa'][0],store.root)
            except (ValueError, OSError) as exc: raise Problem(422,str(exc)) from None
            self._json(200,{'empresa':q['empresa'][0],'calibraciones':data})
            return
        if target.path == "/api/aprendizaje/calibrar" and method == "POST":
            from datetime import date
            from .aprendizaje import calibrar, registrar
            from .calculo_local import ruta_libro
            from .libro_dbd import empresa as leer_empresa
            from .raiz import RAIZ
            body=self._body(); name=body.get('empresa')
            if not isinstance(name,str) or not re.fullmatch(r'[a-z0-9_]{1,60}',name): raise Problem(400,'Empresa inválida.')
            try:
                book=ruta_libro(store.root,name); code,_=leer_empresa(book); published={}
                for folder in (store.root/'resultados',RAIZ/'datos'/'resultados'):
                    for path in sorted(folder.glob(f'{name}_????-??_REAL.json')):
                        row=json.loads(path.read_text(encoding='utf-8')); period=row.get('periodo_actual')
                        if period not in published: published[period]=row
                candidates=calibrar(book,code,published)
                saved=registrar(store.root/'aprendizaje'/f'{name}.json',candidates,date.today().isoformat())
            except (ValueError, OSError, KeyError) as exc: raise Problem(422,str(exc)) from None
            self._json(200,{'empresa':name,'calibraciones':saved})
            return
        if target.path == "/api/aprendizaje/decidir" and method == "POST":
            from datetime import date
            from .aprendizaje import decidir
            body=self._body(); identifier=body.get('id'); decision=body.get('decision')
            if not isinstance(identifier,str) or not re.fullmatch(r'[0-9a-f]{64}',identifier) or decision not in ('APROBAR','RECHAZAR'):
                raise Problem(400,'Identificador o decisión inválidos.')
            try:
                matches=[]
                if (store.root/'aprendizaje').is_symlink(): raise ValueError('Directorio de aprendizaje inválido.')
                for path in (store.root/'aprendizaje').glob('*.json'):
                    if path.is_symlink(): continue
                    data=json.loads(path.read_text(encoding='utf-8'))
                    if any(x.get('id')==identifier for x in data): matches.append(path)
                if len(matches)!=1: raise ValueError('Calibración inexistente o ambigua.')
                result=decidir(matches[0],identifier,decision,date.today().isoformat(),actor=None)
            except (ValueError, OSError, KeyError, TypeError) as exc: raise Problem(422,str(exc)) from None
            self._json(200,result)
            return
        if target.path == "/api/familias/analizar" and method == "POST":
            from .familias import receta, pertenece, anova
            import math
            body = self._body()
            try:
                historia = body.get('historia')
                if not isinstance(historia, dict) or not historia or len(historia) > 100:
                    raise ValueError('Indica la historia por actividad o recurso.')
                def validar_historia(datos):
                    if not isinstance(datos, dict) or not datos or len(datos) > 100: raise ValueError('Historia inválida.')
                    for key, valores in datos.items():
                        if not isinstance(key, str) or not key or not isinstance(valores, list) or not 3 <= len(valores) <= 1000: raise ValueError('Cada historia requiere entre 3 y 1000 observaciones.')
                        if any(isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v) or v < 0 for v in valores): raise ValueError('Las observaciones deben ser números finitos no negativos.')
                validar_historia(historia)
                recetas = {k: receta(v) for k, v in historia.items()}
                salida = {'receta': recetas}
                componente = body.get('componente')
                if componente is not None:
                    if not isinstance(componente, dict) or set(componente) != set(recetas): raise ValueError('El componente debe incluir todos los inductores de la familia.')
                    if any(isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v) or v < 0 for v in componente.values()): raise ValueError('Cantidades inválidas.')
                    salida['pertenencia'] = pertenece(componente, recetas)
                otra = body.get('comparar')
                if otra is not None:
                    validar_historia(otra)
                    if set(otra) != set(historia): raise ValueError('Las familias deben tener los mismos inductores.')
                    resultados = {k: anova(historia[k], otra[k]) for k in historia}
                    if any(not math.isfinite(v['F']) for v in resultados.values()): raise ValueError('No se puede comparar con variación nula.')
                    salida['comparacion'] = resultados
                    salida['sugerir_fusion'] = all(x['mismo_efecto'] for x in resultados.values())
                self._json(200, salida)
            except (ValueError, TypeError, KeyError, ZeroDivisionError) as exc: raise Problem(422, str(exc)) from None
            return
        if target.path == "/api/pedido/familias" and method == "GET":
            from .calculo_local import ruta_libro
            from .recetas_pedido import leer_familias_de_libro
            q = parse_qs(target.query, keep_blank_values=True, max_num_fields=1)
            if set(q) - {"empresa"} or any(len(v) != 1 for v in q.values()):
                raise Problem(400, "Parámetros inválidos para consultar familias.")
            empresa = q.get("empresa", [""])[0]
            if not re.fullmatch(r"[a-z0-9_]{1,60}", empresa):
                raise Problem(400, "Elige una empresa válida.")
            try:
                from openpyxl import load_workbook
                libro = ruta_libro(store.root, empresa)
                wb = load_workbook(libro, read_only=True, data_only=True)
                try:
                    modelos = leer_familias_de_libro(wb)
                finally:
                    wb.close()
                familias = [{"codigo": codigo,
                             "parametros": [{**parametro,
                                             "derivable": bool((modelo.get("derivaciones") or {}).get(parametro["codigo"]))}
                                            for parametro in modelo["parametros"].values()],
                             "inductores": [{"codigo": ind} for ind in sorted(modelo["inductores"])]}
                            for codigo, modelo in sorted(modelos.items())]
            except (OSError, ValueError, KeyError):
                familias = []
            self._json(HTTPStatus.OK, {"familias": familias,
                                      "aviso": "Configura una hoja FAMILIA_PARAM para habilitar recetas." if not familias else ""})
            return
        if target.path in {"/api/cotizar", "/api/pedido/cotizar"} and method == "POST":
            from .calculo_local import ruta_libro
            from .cotizador import cotizar
            from .raiz import RAIZ
            import puerto_lectura as P
            es_pedido = target.path == "/api/pedido/cotizar"
            body = self._body()
            empresa = body.get('empresa')
            if not isinstance(empresa, str) or not re.fullmatch(r'[a-z0-9_]{1,60}', empresa):
                raise Problem(400, 'Elige una empresa válida.')
            try:
                libro = ruta_libro(store.root, empresa)
                data = P.leer(libro, ['PERIODO','MEDIDA','EMPRESA'])
                periods = {str(row['PER_COD']) for row in data['PERIODO'] if row.get('PER_COD')}
                closed = sorted(str(row['PER_COD']) for row in data['PERIODO'] if row.get('PER_COD') and str(row.get('PER_EST') or '').strip().upper() == 'C')
                folders = (store.root / 'resultados', RAIZ / 'datos' / 'resultados')
                provisional = not closed
                if closed:
                    per = closed[-1]
                else:
                    # Solo periodos existentes en el libro y con resultados REAL publicados.
                    calculados = sorted(p for p in periods if re.fullmatch(r'\d{4}-(0[1-9]|1[0-2])', p)
                                        and any((folder / f'{empresa}_{p}_REAL.json').is_file() for folder in folders))
                    if not calculados:
                        raise Problem(404, 'No hay un resultado REAL calculado para cotizar.')
                    per = calculados[-1]
                paths = [folder / f'{empresa}_{per}_REAL.json' for folder in folders]
                published = next((path for path in paths if path.is_file()), None)
                if published is None: raise Problem(404, 'No hay un resultado REAL publicado para el último periodo cerrado.')
                result = json.loads(published.read_text(encoding='utf-8'))
                if (validar(result) or result.get('periodo_actual') != per or result.get('sintesis') != 'REAL'
                        or len(data['EMPRESA']) != 1 or result['empresa'].get('codigo') != data['EMPRESA'][0].get('EMP_COD')):
                    raise ValueError('Resultado publicado incompatible con el periodo o la empresa.')
                if es_pedido:
                    from openpyxl import load_workbook
                    from .recetas_pedido import leer_familias_de_libro, resolver_parametros
                    from .pedido import cotizar_pedido
                    wb = load_workbook(libro, read_only=True, data_only=True)
                    try:
                        modelos = leer_familias_de_libro(wb)
                    finally:
                        wb.close()
                    familia = str(body.get('familia') or '')
                    if familia not in modelos:
                        raise ValueError('Elige una familia parametrizada en el libro.')
                    modelo = modelos[familia]
                    resueltos = resolver_parametros(modelo, body.get('parametros') or {},
                                                    body.get('parametros_tecnicos') or {})
                    if resueltos['faltantes']:
                        quote = {
                            'estado': 'PRELIMINAR', 'cotizacion_firme': False,
                            'producto': str(body.get('producto') or '').strip(),
                            'cliente': str(body.get('cliente') or '').strip(),
                            'fecha_requerida': str(body.get('fecha_requerida') or '').strip(),
                            'parametros_resueltos': resueltos['parametros'],
                            'origen_parametros': resueltos['origen'],
                            'faltantes': resueltos['faltantes'],
                            'avisos': ['Faltan datos para calcular el costo; completa la confirmación técnica.'],
                            'fundamento': {
                                'formula': 'El costo del pedido se calcula después de completar los parámetros requeridos.',
                                'supuesto': 'Solo se completan parámetros con una receta aprendida y dentro del rango declarado.',
                                'dato_usado': f"Familia {familia}; cantidad {body.get('cantidad')}; parámetros recibidos {body.get('parametros') or {}}.",
                                'limite': 'No se calculó el costo porque hay datos técnicos pendientes.',
                            },
                        }
                        self._json(HTTPStatus.OK, quote)
                        return
                    from .libro_dbd import empresa as leer_empresa
                    quote = cotizar_pedido(libro, leer_empresa(libro)[0], result, data['MEDIDA'],
                                           modelo, {**body, 'parametros': resueltos['parametros']})
                    quote['parametros_resueltos'] = resueltos['parametros']
                    quote['origen_parametros'] = resueltos['origen']
                    limites = body.get('umbral_firme', {})
                    if limites is None:
                        limites = {}
                    if not isinstance(limites, dict):
                        raise ValueError('Los límites de cotización firme deben ser un mapa.')
                    monto_maximo, ancho_maximo = limites.get('monto'), limites.get('ancho_pct')
                    motivos = []
                    if monto_maximo in (None, '') or ancho_maximo in (None, ''):
                        motivos.append('Define en Configuración el monto máximo y el ancho máximo del rango para autorizar una cotización firme.')
                    else:
                        if isinstance(monto_maximo, bool) or isinstance(ancho_maximo, bool):
                            raise ValueError('Los límites de cotización firme deben ser numéricos.')
                        try:
                            monto_maximo, ancho_maximo = float(monto_maximo), float(ancho_maximo)
                        except (TypeError, ValueError):
                            raise ValueError('Los límites de cotización firme deben ser numéricos.') from None
                        import math
                        if (not math.isfinite(monto_maximo) or monto_maximo < 0
                                or not math.isfinite(ancho_maximo) or ancho_maximo < 0):
                            raise ValueError('Los límites de cotización firme deben ser finitos y no negativos.')
                        if quote['costo_esperado'] > monto_maximo:
                            motivos.append('El monto supera el límite configurado; requiere confirmación técnica.')
                        rango = quote.get('rango_p05_p95')
                        if rango is None:
                            motivos.append('El rango P05–P95 no es estimable; la cotización queda preliminar.')
                        elif quote['costo_esperado'] > 0:
                            ancho = 100 * (rango['p95'] - rango['p05']) / quote['costo_esperado']
                            if ancho > ancho_maximo:
                                motivos.append(f'El ancho del rango ({ancho:.2f} %) supera el límite; requiere confirmación técnica.')
                    if quote.get('plazo', {}).get('estado') == 'NO_DISPONIBLE':
                        motivos.append('Falta información de capacidad o carga para confirmar la fecha de entrega.')
                    quote['estado'] = 'PRELIMINAR' if motivos else 'FIRME'
                    quote['cotizacion_firme'] = not motivos
                    quote['avisos'] = list(quote.get('avisos') or []) + motivos
                    quote['condicion_pago'] = str(body.get('condicion_pago') or '').strip()
                    if resueltos['origen']:
                        usados = ', '.join(f"{modelo['parametros'][codigo]['nombre']}={valor:g} ({resueltos['origen'][codigo]})"
                                           for codigo, valor in resueltos['parametros'].items())
                        quote['fundamento']['dato_usado'] += f" Parámetros: {usados}."
                elif body.get('familia') is not None:
                    import math
                    familia=body['familia']; unidades=body.get('unidades')
                    if not body.get('meses') or not isinstance(familia,dict) or not familia or len(familia)>100:
                        raise ValueError('La familia requiere cotización proyectada y receta válida.')
                    if isinstance(unidades,bool) or not isinstance(unidades,(int,float)) or not math.isfinite(unidades) or unidades<=0:
                        raise ValueError('Indica unidades positivas y finitas.')
                    for codigo, valores in familia.items():
                        if not isinstance(codigo,str) or not codigo or not isinstance(valores,dict): raise ValueError('Receta inválida.')
                        vs=[valores.get(k) for k in ('media','minimo','maximo')]
                        if any(isinstance(v,bool) or not isinstance(v,(int,float)) or not math.isfinite(v) for v in vs) or vs[0]<0 or vs[1]>vs[0] or vs[2]<vs[0]:
                            raise ValueError('Receta inválida.')
                if not es_pedido and body.get('meses'):
                    from .cotizador import cotizar_proyectado
                    from .libro_dbd import empresa as leer_empresa
                    quote = cotizar_proyectado(libro, leer_empresa(libro)[0], result, data['MEDIDA'], body.get('actividades') or {}, body.get('materiales') or {},
                                               body.get('precio_mercado'), body.get('margen_objetivo'), int(body['meses']), int(body.get('intervalo') or 3),
                                               body.get('curva') or 'pareja', body.get('contrato') or 'CERRADO', familia=body.get('familia'), unidades=body.get('unidades'))
                elif not es_pedido:
                    quote = cotizar(result, data['MEDIDA'], body.get('actividades'), body.get('materiales'), body.get('precio_mercado'), body.get('margen_objetivo'), producto=body.get('producto'), carpeta_aprendizaje=store.root, empresa_aprendizaje=empresa)
                if provisional:
                    quote['aviso'] = 'tasas provisionales: mes no cerrado'
                    quote['avisos'].append(quote['aviso'])
            except ValueError as exc: raise Problem(422, str(exc)) from None
            except (OSError, KeyError): raise Problem(422, 'No se pudo leer el libro o el resultado publicado.') from None
            self._json(200, quote)
            return
        if target.path == "/api/calcular" and method == "POST":
            try:
                params = parse_qs(target.query, keep_blank_values=True, max_num_fields=3)
                if not {"sintesis", "periodo"} <= set(params) <= {"sintesis", "periodo", "empresa"} or any(len(v) != 1 for v in params.values()):
                    raise ValueError
                sintesis, periodo = params["sintesis"][0], params["periodo"][0]
                empresa = params.get("empresa", [None])[0]
                if sintesis not in {"REAL", "CONTABLE"} or not re.fullmatch(r"\d{4}-(0[1-9]|1[0-2])", periodo):
                    raise ValueError
                if empresa is not None and not re.fullmatch(r"[a-z0-9_]{1,60}", empresa):
                    raise ValueError
                self._body()
            except ValueError:
                raise Problem(400, "Elige una síntesis y un periodo disponibles.") from None
            try:
                from .calculo_local import calcular
                resultado = calcular(store.root, periodo, sintesis, empresa)
            except ValueError as exc:
                import traceback; traceback.print_exc()
                raise Problem(422, f"No se pudo calcular el periodo: {exc}") from None
            except (OSError, KeyError, ImportError):
                import traceback; traceback.print_exc()          # queda en la consola del programa para diagnóstico
                raise Problem(422, "No se pudo calcular el periodo. Revisa que el periodo exista en el libro de la empresa.") from None
            self._json(HTTPStatus.OK, resultado)
            return
        if target.path == "/api/descargar" and method == "GET":
            params = parse_qs(target.query, keep_blank_values=True, max_num_fields=1)
            nombre = params.get("archivo", [""])[0]
            if set(params) != {"archivo"} or len(params["archivo"]) != 1 or not re.fullmatch(r"(?:resultados|analitica|proyeccion|html|codigo|entrada|sistema|informe|presentacion)-[0-9a-f]{32}\.(?:xlsx|html|docx)", nombre):
                raise Problem(400, "Elige un reporte válido.")
            try:
                contenido = (store.root / "exportaciones" / nombre).read_bytes()
            except OSError:
                raise Problem(404, "El reporte no está disponible.") from None
            self._send(HTTPStatus.OK, contenido, "application/octet-stream")
            return
        if target.path == "/api/trx-campos" and method == "GET":
            try:
                params = parse_qs(target.query, keep_blank_values=True, max_num_fields=2)
                if set(params) != {"id", "trx"} or any(len(v) != 1 for v in params.values()):
                    raise ValueError
                identifier, trx = params["id"][0], params["trx"][0]
                if trx not in TRANSACTIONS and trx not in TRANSACCIONES_E26:
                    raise ValueError
            except ValueError:
                raise Problem(400, "Elige un espacio y una transacción habilitada.") from None
            tables, _ = load_data(content_bytes(store.path(identifier)))
            info = metadata(tables)
            company = info.get("company_code")
            if info.get("id") != identifier or not company:
                raise Problem(409, "El espacio no tiene una empresa válida.")
            fields = []
            sensitive = {"USUARIO", "USUARIO_PERFIL", "PERFIL_TRX", "_ReynaMeta", "_ReynaRecibos"}
            configuration = tables["TRX_CAMPO"]
            names = ("TCA_TRX", "TCA_SEC", "TCA_VAR", "TCA_ETQ", "TCA_NIVEL", "TCA_LISTA")
            if any(configuration["h"].count(name) != 1 for name in names):
                raise Problem(422, "La configuración de campos del libro es incompatible.")
            positions = [configuration["h"].index(name) for name in names]
            for row in configuration["r"]:
                code, sequence, variable, label, level, reference = (row[index] for index in positions)
                if code != trx:
                    continue
                if level not in ("C", "L"):
                    continue
                options = []
                if reference:
                    if not isinstance(reference, str) or not re.fullmatch(r"[A-Z_]+\.[A-Z_]+", reference):
                        raise Problem(422, "La lista del campo no está configurada correctamente.")
                    name, column = reference.split(".")
                    if name.upper() in {x.upper() for x in sensitive} or any(x in column for x in ("CLAVE", "PASSWORD", "TOKEN")):
                        raise Problem(422, "La lista del campo no está disponible.")
                    tabla = tables.get(name)
                    if tabla is None or tabla['h'].count(column) != 1:
                        raise Problem(422, "La lista del campo no existe en el libro.")
                    ci = tabla['h'].index(column)
                    emp_cols = [i for i, col in enumerate(tabla['h']) if isinstance(col, str) and col.endswith('_EMP')]
                    if len(emp_cols) > 1:
                        raise Problem(422, "La lista tiene una empresa ambigua.")
                    for item in tabla['r']:
                        if name == 'EMPRESA' and item[ci] != company:
                            continue
                        if emp_cols and item[emp_cols[0]] not in (company, '*'):
                            continue
                        value = item[ci]
                        if value not in (None, '') and isinstance(value, (str, int, float)) and value not in options:
                            options.append(value)
                fields.append(dict(secuencia=sequence, variable=variable, etiqueta=label, nivel=level, lista=reference, valores=options))
            fields.sort(key=lambda field: int(field['secuencia']))
            from .correlativo_objeto import especificacion_creacion
            object_spec = especificacion_creacion(tables, trx)
            object_meta = None
            if object_spec:
                object_meta = {"variable": object_spec["variable"], "contexto": object_spec["producto"]["contexto"]}
                for field in fields:
                    if field["variable"] == object_spec["variable"]:
                        field["sistema_asignado"] = True
                        field["solo_lectura"] = True
            configured_transactions = list(TRANSACTIONS) + detectar_transacciones_e26(tables)
            object_transactions = [code for code in configured_transactions
                                   if especificacion_creacion(tables, code) is not None]
            self._json(200, {"transaccion": trx, "campos": fields,
                             "transacciones": [r[0] for r in tables.get("TRX", {}).get("r", []) if r and isinstance(r[0], str)],
                             "transacciones_objeto": object_transactions,
                             "objeto": object_meta})
            return
        if target.path == "/api/objeto-siguiente" and method == "POST":
            body = self._body()
            identifier, trx = body.get("id"), body.get("transaction")
            header, lines = body.get("header", {}), body.get("lines", [])
            if (not isinstance(identifier, str) or not re.fullmatch(r"[a-f0-9]{32}", identifier)
                    or not isinstance(trx, str) or not re.fullmatch(r"[A-Z0-9.]{1,8}", trx)
                    or not isinstance(header, dict) or not isinstance(lines, list)):
                raise Problem(400, "Indica un espacio, transacción y datos de formulario válidos.")
            self._json(200, store.sugerir_codigo_objeto(identifier, trx, header, lines))
            return
        if target.path == "/api/exportar" and method == "POST":
            try:
                params = parse_qs(target.query, keep_blank_values=True, max_num_fields=1)
                if set(params) != {"tipo"} or len(params["tipo"]) != 1 or params["tipo"][0] not in TIPOS:
                    raise ValueError("Elige un tipo de reporte válido.")
                body = self._body()
                granular = None
                if params["tipo"][0] == "proyeccion":
                    from .exportar import obtener_proyeccion
                    granular = obtener_proyeccion(body.get("resultados") or {}, store.root, body.get("empresa"))
                ruta = exportar(body.get("resultados"), params["tipo"][0], store.root / "exportaciones", proyeccion_granular=granular)
            except ValueError as exc:
                raise Problem(HTTPStatus.BAD_REQUEST, str(exc)) from None
            self._json(HTTPStatus.CREATED, {"ruta": str(ruta), "tipo": params["tipo"][0]})
            return
        if target.path == "/api/decidir" and method == "POST":
            from . import decidir as DEC
            body = self._body()
            try:
                empresa, periodo, caso = body.get("empresa"), body.get("periodo"), body.get("caso")
                if not (isinstance(empresa, str) and re.fullmatch(r"[a-z0-9_]{1,60}", empresa) and isinstance(periodo, str)
                        and re.fullmatch(r"\d{4}-(0[1-9]|1[0-2])", periodo)
                        and caso in ("tercerizar", "eliminar", "pedido", "recurso_escaso", "vender_procesar")):
                    raise ValueError("Parámetros inválidos.")
                nombre = f"{empresa}_{periodo}_REAL.json"
                archivo = next((x for x in (self.server.store.root / "resultados" / nombre, Path(__file__).resolve().parents[2] / "datos" / "resultados" / nombre) if x.is_file()), None)
                if archivo is None: raise ValueError("No hay resultado REAL calculado para ese periodo.")
                resultado = json.loads(archivo.read_text(encoding="utf-8"))
                if caso == "recurso_escaso":
                    criterio, destino = body.get("criterio"), body.get("destino")
                    if not (isinstance(criterio, str) and criterio and len(criterio) <= 100
                            and isinstance(destino, str) and destino and len(destino) <= 100):
                        raise ValueError("Elige un inductor y un recurso válidos.")
                    maximos = body.get("demanda_maxima") or {}
                    if not isinstance(maximos, dict): raise ValueError("Las demandas máximas deben enviarse por producto.")
                    out = DEC.asignar_recurso(resultado, criterio, destino, maximos)
                elif caso == "vender_procesar":
                    num = lambda k: float(body.get(k))
                    out = DEC.vender_o_procesar(num("precio_venta_actual"), num("precio_venta_procesado"), num("costo_procesamiento"))
                else:
                    producto = body.get("producto")
                    fila = next((f for f in resultado.get("decidir", {}).get("er_gerencial", {}).get("productos", []) if f["producto"] == producto), None)
                    if fila is None: raise ValueError("Producto sin datos en el panel Decidir.")
                    num = lambda k, d=0.0: float(body.get(k, d) or 0)
                    if caso == "tercerizar": out = DEC.producir_o_tercerizar(fila, num("unidades"), num("precio_compra"), num("costo_mantener"), num("costo_transicion"))
                    elif caso == "eliminar": out = DEC.eliminar_linea(fila)
                    else: out = DEC.pedido_especial(fila, num("unidades"), num("precio"), num("cf_incremental"), bool(body.get("capacidad_ociosa", True)), num("unidades_desplazadas"))
            except (ValueError, TypeError) as exc: raise Problem(422, str(exc)) from None
            self._json(200, out)
            return
        if target.path == "/api/resultados" and method == "GET":
            try:
                params = parse_qs(target.query, keep_blank_values=True, max_num_fields=3)
                if not {"sintesis", "periodo"} <= set(params) <= {"sintesis", "periodo", "empresa"} or any(len(x) != 1 for x in params.values()):
                    raise ValueError
                sintesis, periodo = params["sintesis"][0], params["periodo"][0]
                empresa = params.get("empresa", ["frenosa"])[0]
                if sintesis not in {"REAL", "CONTABLE"} or not re.fullmatch(r"\d{4}-(0[1-9]|1[0-2])", periodo):
                    raise ValueError
                if not re.fullmatch(r"[a-z0-9_]{1,60}", empresa):
                    raise ValueError
            except ValueError:
                raise Problem(400, "Elige una síntesis y un periodo válidos.") from None
            nombre = f"{empresa}_{periodo}_{sintesis}.json"
            candidatos = [self.server.store.root / "resultados" / nombre,
                          Path(__file__).resolve().parents[2] / "datos" / "resultados" / nombre,
                          INDEX.parent / nombre]
            archivo = next((p for p in candidatos if p.is_file()), None)
            if archivo is None:
                if empresa != "frenosa":                    # nunca mostrar el ejemplo de otra empresa como si fuera suyo
                    raise Problem(404, "No hay resultados calculados para esa empresa y periodo. Pulsa Calcular.")
                archivo = INDEX.parent / "resultados_ejemplo.json"
            try:
                resultado = json.loads(archivo.read_text(encoding="utf-8"))
                if validar(resultado):
                    raise ValueError
                if archivo.name != "resultados_ejemplo.json" and (resultado["periodo_actual"] != periodo or resultado["sintesis"] != sintesis):
                    raise ValueError
            except (OSError, ValueError, TypeError, KeyError):
                raise Problem(422, "Los resultados disponibles no se pueden mostrar. Revisa el archivo de resultados.") from None
            self._json(HTTPStatus.OK, resultado)
            return
        if target.path == "/api/precision" and method == "GET":
            from .calculo_local import ruta_libro
            from .proyeccion import precision
            from .libro_dbd import empresa as leer_empresa
            try:
                q = parse_qs(target.query, keep_blank_values=True, max_num_fields=1)
                company = q.get('empresa', ['frenosa'])[0]
                if set(q) - {'empresa'} or not re.fullmatch(r'[a-z0-9_]{1,60}', company): raise ValueError('Parámetros inválidos.')
                path = ruta_libro(store.root, company); result = precision(path, leer_empresa(path)[0])
            except (ValueError, KeyError) as exc: raise Problem(422, str(exc)) from None
            self._json(200, result)
            return
        if target.path == "/api/proyeccion" and method == "GET":
            from .calculo_local import ruta_libro
            from .proyeccion import proyectar_granular
            try:
                q = parse_qs(target.query, keep_blank_values=True, max_num_fields=2)
                if set(q) - {'empresa','meses'} or any(len(v) != 1 for v in q.values()): raise ValueError('Parámetros inválidos.')
                company = q.get('empresa',['frenosa'])[0]
                if not re.fullmatch(r'[a-z0-9_]{1,60}',company): raise ValueError('Empresa inválida.')
                months = int(q.get('meses',['6'])[0])
                from .libro_dbd import empresa as leer_empresa
                path = ruta_libro(store.root, company)
                result = proyectar_granular(path, leer_empresa(path)[0], months)
            except (ValueError, KeyError) as exc: raise Problem(422,str(exc)) from None
            self._json(200,result)
            return
        if target.path == "/api/periodos" and method == "GET":     # tarea 2.6: periodos por fecha libre
            from .periodos import desde_archivos, GRANOS
            from .calculo_local import ruta_libro
            q = {k: v[0] for k, v in parse_qs(target.query).items()}
            empresa, sintesis, grano = q.get("empresa", "frenosa"), q.get("sintesis", "REAL"), q.get("grano", "mes")
            if (not re.fullmatch(r"[a-z0-9_]{1,60}", empresa) or sintesis not in {"REAL", "CONTABLE"} or grano not in GRANOS
                    or not all(re.fullmatch(r"\d{4}-\d{2}-\d{2}", q.get(k, "")) for k in ("desde", "hasta"))):
                raise Problem(400, "Elige empresa, síntesis, grano y fechas válidas (AAAA-MM-DD).")
            try:
                libro = ruta_libro(self.server.store.root, empresa)
                out = desde_archivos(libro, [self.server.store.root / "resultados", Path(__file__).resolve().parents[2] / "datos" / "resultados"],
                                     empresa, sintesis, q["desde"], q["hasta"], grano)
            except ValueError as exc:
                raise Problem(400, str(exc)) from None
            self._json(HTTPStatus.OK, out)
            return
        if target.path == "/api/sello" and method == "POST":
            from .calculo_local import verificar_sello
            self._json(HTTPStatus.OK, verificar_sello(store.root, self._body().get("resultados") or {}))
            return
        if parts[:3] != ["", "api", "workspaces"]:
            raise Problem(HTTPStatus.NOT_FOUND, "La ruta no existe.")
        if len(parts) == 3 and method == "GET":
            self._json(HTTPStatus.OK, store.list())
        elif len(parts) == 3 and method == "POST":
            self._json(HTTPStatus.CREATED, store.create(self._body()))
        elif len(parts) == 4 and method == "GET" and parts[3]:
            self._json(HTTPStatus.OK, store.get(unquote(parts[3])))
        elif len(parts) == 5 and method == "POST" and parts[3] and parts[4] == "aceptar-cotizacion":
            status, payload = store.aceptar_cotizacion(unquote(parts[3]), self._body())
            self._json(status, payload)
        elif len(parts) == 5 and method == "POST" and parts[3] and parts[4] == "execute":
            status, payload = store.execute(unquote(parts[3]), self._body())
            self._json(status, payload)
        elif len(parts) == 5 and method == "POST" and parts[3] and parts[4] == "close-month":
            status, payload = store.close_month(unquote(parts[3]), self._body())
            self._json(status, payload)
        elif len(parts) == 5 and method == "GET" and parts[3] and parts[4] == "audit":
            self._json(HTTPStatus.OK, audit_receipts(store.path(unquote(parts[3]))))
        elif len(parts) == 6 and method == "GET" and parts[3] and parts[4] == "tables" and parts[5]:
            offset, limit = self._pagination(target.query)
            self._json(HTTPStatus.OK, store.table(unquote(parts[3]), unquote(parts[5]), offset, limit))
        else:
            raise Problem(HTTPStatus.NOT_FOUND, "La ruta no existe para este método.")

    def _handle(self):
        try:
            self._check_peer()
            if self.command not in {"GET", "POST"}:
                raise Problem(HTTPStatus.METHOD_NOT_ALLOWED, "Este servidor admite solicitudes GET y POST.")
            self._route()
        except Problem as error:
            self._reply_error(error.status, str(error))
        except (BrokenPipeError, ConnectionResetError, TimeoutError):
            self.close_connection = True
        except Exception:
            traceback.print_exc()
            self._reply_error(
                HTTPStatus.INTERNAL_SERVER_ERROR,
                "El servidor no pudo completar la operación. Comprueba el registro local.",
            )

    def _reply_error(self, status, message):
        try:
            self._json(status, {"error": message})
        except (BrokenPipeError, ConnectionResetError, TimeoutError):
            self.close_connection = True

    do_GET = do_POST = _handle
    do_HEAD = do_PUT = do_PATCH = do_DELETE = do_OPTIONS = do_TRACE = do_CONNECT = _handle


def _stop(_signum, _frame):
    raise KeyboardInterrupt


def main(argv=None):
    parser = argparse.ArgumentParser(description="Inicia el piloto Excel/Python en la máquina local.")
    parser.add_argument("--data-dir", type=Path, required=True, help="Carpeta de trabajo donde se guardan los espacios.")
    parser.add_argument("--port", type=int, default=8765, help="Puerto HTTP local. Usa 0 para elegir un puerto libre.")
    parser.add_argument("--open-browser", action="store_true", help="Abre la dirección local en el navegador predeterminado.")
    args = parser.parse_args(argv)
    if not 0 <= args.port <= 65535:
        parser.error("--port debe estar entre 0 y 65535.")
    try:
        server = ReynaServer(args.data_dir, args.port)
    except (OSError, Problem) as error:
        print(f"No se pudo iniciar el servidor local. {error}", file=sys.stderr)
        return 1
    quit_handler = signal.signal(signal.SIGTERM, _stop)
    try:
        with server:
            url = f"http://127.0.0.1:{server.server_port}"
            print(f"Piloto local disponible en {url}", flush=True)
            if args.open_browser:
                try:
                    opened = webbrowser.open(url)
                except (OSError, webbrowser.Error):
                    opened = False
                if not opened:
                    print("Abre la dirección indicada en tu navegador.", flush=True)
            server.serve_forever()
    except KeyboardInterrupt:
        return 0
    finally:
        signal.signal(signal.SIGTERM, quit_handler)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
