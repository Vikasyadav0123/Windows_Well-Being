import json
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path


class DashboardServer:
    def __init__(self, storage):
        self.storage = storage
        self._server = None
        self._port = 7331

    def start(self):
        storage = self.storage

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args):
                pass

            def do_GET(self):
                path = self.path.split("?")[0]
                if path == "/" or path == "/index.html":
                    self._serve_dashboard()
                elif path == "/api/today":
                    date = self._get_param("date")
                    self._serve_json(storage.get_day(date))
                elif path == "/api/week":
                    self._serve_json(storage.get_week())
                elif path == "/api/days":
                    self._serve_json(storage.list_days())
                else:
                    self.send_response(404)
                    self.end_headers()

            def _get_param(self, key):
                from urllib.parse import urlparse, parse_qs
                qs = parse_qs(urlparse(self.path).query)
                vals = qs.get(key, [None])
                return vals[0] if vals else None

            def _serve_json(self, data):
                body = json.dumps(data, ensure_ascii=False).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", len(body))
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(body)

            def _serve_dashboard(self):
                html_path = Path(__file__).parent / "dashboard.html"
                if html_path.exists():
                    with open(html_path, "rb") as f:
                        body = f.read()
                else:
                    body = b"<h1>dashboard.html not found</h1>"
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", len(body))
                self.end_headers()
                self.wfile.write(body)

        self._server = HTTPServer(("localhost", self._port), Handler)
        self._server.serve_forever()

    def stop(self):
        if self._server:
            self._server.shutdown()