"""Shared hardened HTTP handler base for the almunaa service."""

from __future__ import annotations

import hmac
import json
import logging
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Callable
from urllib.parse import urlparse

from .config import ServiceConfig, load_config
from .observability import Metrics, setup_logging
from .version import __version__

SERVICE_NAME = "almunaa"


class BaseServiceHandler(BaseHTTPRequestHandler):
    config: ServiceConfig | None = None
    metrics: Metrics | None = None
    logger: logging.Logger | None = None
    #: path -> callable(data dict) -> (status, payload dict). Set by build().
    post_routes: dict[str, Callable[[dict[str, Any]], tuple[int, dict[str, Any]]]] = {}
    get_routes: dict[str, Callable[[], tuple[int, dict[str, Any]]]] = {}

    def _send_json(self, status: int, payload: dict) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("X-Service-Version", __version__)
        self.end_headers()
        self.wfile.write(body)

    def _authorized(self) -> bool:
        key = self.config.api_key if self.config else ""
        if not key:
            return True
        provided = self.headers.get("X-API-Key", "")
        return hmac.compare_digest(provided.encode("utf-8"), key.encode("utf-8"))

    def _log_event(self, level: int, message: str, **event: object) -> None:
        if self.logger is not None:
            self.logger.log(level, message, extra={"event": event})

    def _drain_body(self, length: int, cap: int = 16_777_216) -> None:
        remaining = min(length, cap)
        while remaining > 0:
            chunk = self.rfile.read(min(65536, remaining))
            if not chunk:
                break
            remaining -= len(chunk)

    def do_GET(self) -> None:
        path = urlparse(self.path).path
        if path == "/api/health":
            payload = {
                "ok": True,
                "service": SERVICE_NAME,
                "version": __version__,
                "auth_required": bool(self.config and self.config.api_key),
            }
            if self.metrics is not None:
                payload["uptime_s"] = round(time.time() - self.metrics.started_at, 3)
            self._send_json(200, payload)
            return
        if not self._authorized():
            if self.metrics is not None:
                self.metrics.inc("http_unauthorized")
            self._send_json(401, {"ok": False, "error": "missing or invalid X-API-Key"})
            return
        if path == "/api/version":
            self._send_json(200, {"service": SERVICE_NAME, "version": __version__})
            return
        if path == "/api/metrics":
            self._send_json(200, self.metrics.snapshot() if self.metrics else {})
            return
        handler = self.get_routes.get(path)
        if handler is not None:
            try:
                status, payload = handler()
                self._send_json(status, payload)
            except Exception as exc:
                self._send_json(500, {"ok": False, "error": str(exc)})
            return
        self._send_json(404, {"ok": False, "error": "not found"})

    def do_POST(self) -> None:
        path = urlparse(self.path).path
        handler = self.post_routes.get(path)
        if handler is None:
            self._send_json(404, {"ok": False, "error": "not found"})
            return
        if not self._authorized():
            if self.metrics is not None:
                self.metrics.inc("http_unauthorized")
            self._send_json(401, {"ok": False, "error": "missing or invalid X-API-Key"})
            return
        max_body = self.config.max_body_bytes if self.config else 1_048_576
        length = int(self.headers.get("Content-Length", "0") or 0)
        if length > max_body:
            if self.metrics is not None:
                self.metrics.inc("http_payload_too_large")
            self._drain_body(length)
            self._send_json(413, {"ok": False, "error": f"body exceeds {max_body} bytes"})
            return
        started = time.perf_counter()
        try:
            raw = self.rfile.read(length).decode("utf-8") if length else "{}"
            data = json.loads(raw or "{}")
            if not isinstance(data, dict):
                raise ValueError("request body must be a JSON object")
            status, payload = handler(data)
            elapsed_ms = (time.perf_counter() - started) * 1000.0
            if self.metrics is not None:
                self.metrics.inc("http_requests_total")
                self.metrics.inc(f"endpoint{path.replace('/', '_')}")
                self.metrics.observe_ms(elapsed_ms)
            self._log_event(logging.INFO, "request", path=path, status=status, ms=round(elapsed_ms, 3))
            self._send_json(status, payload)
        except Exception as exc:
            elapsed_ms = (time.perf_counter() - started) * 1000.0
            if self.metrics is not None:
                self.metrics.inc("http_errors_total")
                self.metrics.observe_ms(elapsed_ms)
            self._log_event(logging.WARNING, "request_error", path=path, status=400, ms=round(elapsed_ms, 3), error=str(exc))
            self._send_json(400, {"ok": False, "error": str(exc)})

    def log_message(self, format: str, *args: object) -> None:
        return


def build_server(
    handler_cls: type[BaseServiceHandler],
    host: str | None = None,
    port: int | None = None,
    config: ServiceConfig | None = None,
) -> ThreadingHTTPServer:
    cfg = config or load_config()
    handler_cls.config = cfg
    handler_cls.metrics = Metrics(SERVICE_NAME, __version__)
    handler_cls.logger = setup_logging(f"{SERVICE_NAME}.service", cfg.log_dir, cfg.log_level)
    bind_host = host if host is not None else cfg.host
    bind_port = port if port is not None else cfg.port
    return ThreadingHTTPServer((bind_host, bind_port), handler_cls)
