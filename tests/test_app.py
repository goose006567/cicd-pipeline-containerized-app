import json
import os
import socket
import threading
from http.client import HTTPConnection

import pytest

from app import app as appmod


@pytest.fixture(scope="module")
def server():
    """Boot the real app on a random free port in a thread."""
    sock = socket.socket()
    sock.bind(("127.0.0.1", 0))
    port = sock.getsockname()[1]
    sock.close()
    httpd = appmod.HTTPServer(("127.0.0.1", port), appmod.Handler)
    t = threading.Thread(target=httpd.serve_forever, daemon=True)
    t.start()
    yield port
    httpd.shutdown()


def _get(port, path):
    conn = HTTPConnection("127.0.0.1", port, timeout=5)
    conn.request("GET", path)
    resp = conn.getresponse()
    body = json.loads(resp.read().decode())
    conn.close()
    return resp.status, body


def test_root(server):
    status, body = _get(server, "/")
    assert status == 200
    assert body["message"] == "hello"
    assert body["total_requests"] >= 1


def test_healthz(server):
    status, body = _get(server, "/healthz")
    assert status == 200
    assert body["status"] == "ok"


def test_version(server):
    status, body = _get(server, "/version")
    assert status == 200
    assert body["version"] == appmod.VERSION


def test_unknown_route_is_404(server):
    status, body = _get(server, "/nope")
    assert status == 404
    assert "error" in body


def test_request_counter_increments(server):
    before = _get(server, "/")[1]["total_requests"]
    after = _get(server, "/")[1]["total_requests"]
    assert after == before + 1
