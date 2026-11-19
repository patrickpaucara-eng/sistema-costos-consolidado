"""Servidor local del piloto Excel/Python."""

import argparse
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import math
from pathlib import Path
import signal
import sys
import traceback
from urllib.parse import parse_qs, unquote, urlsplit

from .store import Problem, Store


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
            print(f"Piloto local disponible en http://127.0.0.1:{server.server_port}", flush=True)
            server.serve_forever()
    except KeyboardInterrupt:
        return 0
    finally:
        signal.signal(signal.SIGTERM, quit_handler)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
