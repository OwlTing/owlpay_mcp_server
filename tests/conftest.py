"""Shared fixtures: a local fake upstream so tests never hit the network."""

import importlib
import socket
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest
from urllib3.util.retry import Retry

# ---- repo-specific settings -------------------------------------------------
SERVER_MODULE = "owlpay_mcp_server.server"
API_ATTR = "SEARCH_API"
SEARCH_FUNC = "search_owlpay_documentation_func"
TOOL_NAME = "search_owlpay_documentation"
# -----------------------------------------------------------------------------

UPSTREAM_BODY = "fake upstream documentation body"


@pytest.fixture
def server():
    return importlib.import_module(SERVER_MODULE)


@pytest.fixture
def search(server):
    return getattr(server, SEARCH_FUNC)


@pytest.fixture(autouse=True)
def _no_proxy(monkeypatch):
    """Make sure requests talks to 127.0.0.1 directly, not via an env proxy."""
    for name in ("HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY", "http_proxy", "https_proxy", "all_proxy"):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv("NO_PROXY", "*")


@pytest.fixture
def fast_retry(monkeypatch):
    """Skip Retry backoff sleeps without changing the configured Retry policy."""
    monkeypatch.setattr(Retry, "get_backoff_time", lambda self: 0)


class FakeUpstream:
    def __init__(self, statuses, delay=0):
        self.statuses = list(statuses)
        self.delay = delay
        self.requests = []
        upstream = self

        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):
                upstream.requests.append(self.path)
                idx = min(len(upstream.requests), len(upstream.statuses)) - 1
                status = upstream.statuses[idx]
                time.sleep(upstream.delay)
                body = (UPSTREAM_BODY if status == 200 else "upstream error").encode()
                self.send_response(status)
                self.send_header("Content-Type", "text/plain; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def log_message(self, *args):
                pass

        self.httpd = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.url = f"http://127.0.0.1:{self.httpd.server_address[1]}/search"
        self.thread = threading.Thread(target=self.httpd.serve_forever, daemon=True)
        self.thread.start()

    def close(self):
        self.httpd.shutdown()
        self.httpd.server_close()


@pytest.fixture
def upstream(monkeypatch, server):
    """Factory: upstream([503, 503, 200], delay=0) starts a fake server and points the API at it."""
    started = []

    def _start(statuses, delay=0):
        fake = FakeUpstream(statuses, delay)
        started.append(fake)
        monkeypatch.setattr(server, API_ATTR, fake.url)
        return fake

    yield _start
    for fake in started:
        fake.close()


@pytest.fixture
def closed_port_url():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(("127.0.0.1", 0))
    port = sock.getsockname()[1]
    sock.close()
    return f"http://127.0.0.1:{port}/search"
