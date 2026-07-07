"""Almunaa agent immune system as a local HTTP service.

``POST /api/scan-event`` accepts an AgentEvent payload
(``{"kind", "agent", "content", "tool", "context"}``) and returns
``ALLOW/REVIEW/QUARANTINE/BLOCK`` with findings. By default nothing is
persisted; pass ``"record": true`` to write the incident ledger/quarantine.

The hybrid lexical guard loads once at startup (``ALMUNAA_MODEL``, default
``<project>/models/almunaa_lexical_guard.json``) and is applied to
latin-heavy texts, matching the benchmarked hybrid mode (F1≈98%).
"""

from __future__ import annotations

import os
from http.server import ThreadingHTTPServer
from pathlib import Path
from typing import Any

from .config import PROJECT_ROOT
from .core import scan_event
from .http_base import BaseServiceHandler, build_server
from .lexical_model import LexicalModel
from .models import AgentEvent

_MODEL: LexicalModel | None = None


def model_path() -> Path:
    raw = os.environ.get("ALMUNAA_MODEL", "").strip()
    return Path(raw) if raw else PROJECT_ROOT / "models" / "almunaa_lexical_guard.json"


def _should_use_model(text: str) -> bool:
    clean = text.strip()
    if len(clean) < 30:
        return False
    latin = sum(1 for char in clean.lower() if "a" <= char <= "z")
    return latin >= 12


def _scan_route(data: dict[str, Any]) -> tuple[int, dict[str, Any]]:
    content = str(data.get("content") or "")
    if not content.strip():
        return 400, {"ok": False, "error": "missing 'content'"}
    record = bool(data.get("record"))
    event = AgentEvent.from_dict({k: v for k, v in data.items() if k != "record"})
    model = _MODEL if _should_use_model(event.scan_text()) else None
    result = scan_event(event, write_ledger=record, write_quarantine=record, lexical_model=model)
    return 200, {"ok": True, **result.to_dict()}


class Handler(BaseServiceHandler):
    post_routes = {"/api/scan-event": staticmethod(_scan_route)}


def create_server(host: str | None = None, port: int | None = None) -> ThreadingHTTPServer:
    global _MODEL
    path = model_path()
    _MODEL = LexicalModel.load(path) if path.exists() else None
    return build_server(Handler, host=host, port=port)


def run_server(host: str | None = None, port: int | None = None) -> None:
    from .version import __version__

    server = create_server(host=host, port=port)
    print(f"almunaa service v{__version__}: http://{server.server_address[0]}:{server.server_address[1]}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
