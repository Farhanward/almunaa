from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


def _flatten_text(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, dict):
        parts: list[str] = []
        for key, item in value.items():
            parts.append(str(key))
            parts.extend(_flatten_text(item))
        return parts
    if isinstance(value, (list, tuple, set)):
        parts = []
        for item in value:
            parts.extend(_flatten_text(item))
        return parts
    return [str(value)]


@dataclass
class AgentEvent:
    kind: str
    content: str
    agent: str = "unknown"
    tool: dict[str, Any] = field(default_factory=dict)
    context: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AgentEvent":
        return cls(
            kind=str(data.get("kind") or "input"),
            content=str(data.get("content") or ""),
            agent=str(data.get("agent") or "unknown"),
            tool=dict(data.get("tool") or {}),
            context=dict(data.get("context") or {}),
        )

    def scan_text(self) -> str:
        tool_text = " ".join(_flatten_text(self.tool))
        context_text = " ".join(_flatten_text(self.context))
        return f"{self.content}\n{tool_text}\n{context_text}".strip()

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": self.kind,
            "content": self.content,
            "agent": self.agent,
            "tool": self.tool,
            "context": self.context,
        }


@dataclass
class ThreatFinding:
    code: str
    layer: str
    severity: str
    title: str
    detail: str
    evidence: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "code": self.code,
            "layer": self.layer,
            "severity": self.severity,
            "title": self.title,
            "detail": self.detail,
            "evidence": self.evidence,
        }


@dataclass
class ImmunityResult:
    action: str
    score: float
    findings: list[ThreatFinding]
    event: AgentEvent
    incident_id: str
    quarantine_path: str | None = None
    ledger: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "action": self.action,
            "score": round(self.score, 2),
            "incident_id": self.incident_id,
            "findings": [finding.to_dict() for finding in self.findings],
            "event": self.event.to_dict(),
            "quarantine_path": self.quarantine_path,
            "ledger": self.ledger,
        }
