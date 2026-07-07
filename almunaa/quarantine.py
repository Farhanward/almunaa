from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from .models import AgentEvent


DEFAULT_DIR = Path("quarantine")
SENSITIVE_FIELD = re.compile(r"(secret|token|password|passwd|api[_-]?key|private[_-]?key|authorization)", re.I)


def redact_text(text: str) -> str:
    value = text or ""
    value = re.sub(r"\b(?:sk|sk_live|sk_test|sk-ant|pplx|ghp|xoxb|AKIA)[A-Za-z0-9_\-]{12,}\b", "[REDACTED_API_KEY]", value)
    value = re.sub(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", "[REDACTED_EMAIL]", value, flags=re.I)
    value = re.sub(r"-----BEGIN [A-Z ]*PRIVATE KEY-----.*?-----END [A-Z ]*PRIVATE KEY-----", "[REDACTED_PRIVATE_KEY]", value, flags=re.S)
    return value


def redact_value(value: Any, key: str = "") -> Any:
    if SENSITIVE_FIELD.search(key):
        return "[REDACTED_FIELD]"
    if isinstance(value, dict):
        return {str(item_key): redact_value(item_value, str(item_key)) for item_key, item_value in value.items()}
    if isinstance(value, list):
        return [redact_value(item) for item in value]
    if isinstance(value, tuple):
        return [redact_value(item) for item in value]
    if isinstance(value, str):
        return redact_text(value)
    return value


def redacted_event(event: AgentEvent) -> dict[str, Any]:
    data = event.to_dict()
    data["content"] = redact_text(str(data.get("content", "")))
    tool = dict(data.get("tool") or {})
    for key, value in list(tool.items()):
        tool[key] = redact_value(value, key)
    data["tool"] = tool
    data["context"] = redact_value(data.get("context") or {})
    return data


def redacted_findings(findings: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return redact_value(findings)


def save_quarantine(incident_id: str, event: AgentEvent, findings: list[dict[str, Any]], root: Path = DEFAULT_DIR) -> str:
    root.mkdir(parents=True, exist_ok=True)
    path = root / f"{incident_id}.json"
    payload = {"incident_id": incident_id, "event": redacted_event(event), "findings": redacted_findings(findings)}
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return str(path.resolve())
