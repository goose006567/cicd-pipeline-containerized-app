"""Zero-dependency containerized web app: /, /version, /healthz."""
import json
import os
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse

VERSION = os.environ.get("APP_VERSION", "1.0.0")
HOST = os.environ.get("HOST", "0.0.0.0")
PORT = int(os.environ.get("PORT", "8080"))
REQUESTS = 0
LOCK = threading.Lock()


def bump_requests():
    global REQUESTS
    with LOCK:
        REQUESTS += 1
        return REQUESTS


class Handler(BaseHTTPRequestHandler):
    def _json(self, code, payload):
        body = json.dumps(payload).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        path = urlparse(self.path).path
        total = bump_requests()
        if path == "/":
            self._json(200, {"message": "hello", "total_requests": total})
        elif path == "/healthz":
            self._json(200, {"status": "ok"})
        elif path == "/version":
            self._json(200, {"version": VERSION})
        else:
            self._json(404, {"error": "not found"})
        self.log_message("%s %s -> req#%d", self.command, path, total)


if __name__ == "__main__":
    print(f"[app] serving on {HOST}:{PORT} (version {VERSION})", flush=True)
    HTTPServer((HOST, PORT), Handler).serve_forever()
