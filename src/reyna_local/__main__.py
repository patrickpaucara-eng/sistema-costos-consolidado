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
from .store import Problem, Store
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
        if target.path == "/api/calcular" and method == "POST":
            try:
                params = parse_qs(target.query, keep_blank_values=True, max_num_fields=3)
                if not {"sintesis", "periodo"} <= set(params) <= {"sintesis", "periodo", "empresa"} or any(len(v) != 1 for v in params.values()):
                    raise ValueError
                sintesis, periodo = params["sintesis"][0], params["periodo"][0]
                empresa = params.get("empresa", [None])[0]
                if sintesis not in {"REAL", "CONTABLE", "ESTIMADO"} or not re.fullmatch(r"\d{4}-(0[1-9]|1[0-2])", periodo):
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
            if set(params) != {"archivo"} or len(params["archivo"]) != 1 or not re.fullmatch(r"(?:resultados|analitica|proyeccion|html|codigo|entrada|sistema)-[0-9a-f]{32}\.(?:xlsx|html|docx)", nombre):
                raise Problem(400, "Elige un reporte válido.")
            try:
                contenido = (store.root / "exportaciones" / nombre).read_bytes()
            except OSError:
                raise Problem(404, "El reporte no está disponible.") from None
            self._send(HTTPStatus.OK, contenido, "application/octet-stream")
            return
        if target.path == "/api/exportar" and method == "POST":
            try:
                params = parse_qs(target.query, keep_blank_values=True, max_num_fields=1)
                if set(params) != {"tipo"} or len(params["tipo"]) != 1 or params["tipo"][0] not in TIPOS:
                    raise ValueError("Elige un tipo de reporte válido.")
                body = self._body()
                ruta = exportar(body.get("resultados"), params["tipo"][0], store.root / "exportaciones")
            except ValueError as exc:
                raise Problem(HTTPStatus.BAD_REQUEST, str(exc)) from None
            self._json(HTTPStatus.CREATED, {"ruta": str(ruta), "tipo": params["tipo"][0]})
            return
        if target.path == "/api/resultados" and method == "GET":
            try:
                params = parse_qs(target.query, keep_blank_values=True, max_num_fields=3)
                if not {"sintesis", "periodo"} <= set(params) <= {"sintesis", "periodo", "empresa"} or any(len(x) != 1 for x in params.values()):
                    raise ValueError
                sintesis, periodo = params["sintesis"][0], params["periodo"][0]
                empresa = params.get("empresa", ["frenosa"])[0]
                if sintesis not in {"REAL", "CONTABLE", "ESTIMADO"} or not re.fullmatch(r"\d{4}-(0[1-9]|1[0-2])", periodo):
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
