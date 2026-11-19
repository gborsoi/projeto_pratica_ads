import os
from http import HTTPStatus
from pathlib import Path
from urllib.parse import quote

from app import ApplicationRequest, initialize_database


database_path = os.environ.get("MERCADO_DB")
if not database_path or not Path(database_path).is_absolute():
    raise RuntimeError("Defina MERCADO_DB com o caminho absoluto do banco da hospedagem.")

initialize_database()


class WSGIRequest(ApplicationRequest):
    allow_setup = False
    secure_cookies = True

    def __init__(self, environ, start_response):
        self.path = quote(environ["PATH_INFO"], safe="/")
        if environ.get("QUERY_STRING"):
            self.path += "?" + environ["QUERY_STRING"]
        self.headers = {
            "Cookie": environ.get("HTTP_COOKIE", ""),
            "Content-Length": environ.get("CONTENT_LENGTH") or "",
        }
        self.rfile = environ["wsgi.input"]
        self.start_response = start_response
        self.body = b""

    def send_application_response(self, status, headers, body):
        self.start_response(f"{status} {HTTPStatus(status).phrase}", headers)
        self.body = body


def application(environ, start_response):
    request = WSGIRequest(environ, start_response)
    method = environ["REQUEST_METHOD"]
    if method in ("GET", "HEAD"):
        request.do_GET()
    elif method == "POST":
        request.do_POST()
    else:
        request.send_application_response(405, [("Allow", "GET, HEAD, POST"), ("Content-Length", "0")], b"")
    return [b"" if method == "HEAD" else request.body]
