from __future__ import annotations

import uuid
from pathlib import Path
from typing import Any

from .ledger import DEFAULT_LEDGER, append
from .models import AgentEvent, ImmunityResult, ThreatFinding
from .policy import scan_policy
from .quarantine import redacted_event, redacted_findings, save_quarantine


PENALTIES = {"low": 8, "medium": 18, "high": 38, "critical": 70}


def decide(score: float, findings: list[ThreatFinding]) -> str:
    severities = [finding.severity for finding in findings]
    if "critical" in severities:
        return "BLOCK"
    if "high" in severities:
        return "QUARANTINE"
    if score < 70 or "medium" in severities:
        return "REVIEW"
    return "ALLOW"


def scan_event(
    event: AgentEvent,
    ledger_path: str | Path | None = DEFAULT_LEDGER,
    write_ledger: bool = True,
    write_quarantine: bool = True,
    lexical_model: Any | None = None,
) -> ImmunityResult:
    findings = scan_policy(event)
    if lexical_model is not None:
        risk = float(lexical_model.score(event.scan_text()))
        threshold = float(getattr(lexical_model, "threshold", 0.5))
        if risk >= threshold:
            findings.append(
                ThreatFinding(
                    code="LEXICAL_MODEL_RISK",
                    layer="input",
                    severity="high",
                    title="تصنيف خطر من النموذج المحلي",
                    detail="رصد النموذج اللفظي المحلي نمطاً قريباً من حقن الأوامر أو jailbreak.",
                    evidence=f"risk={risk:.3f}, threshold={threshold:.3f}",
                )
            )
    penalty = sum(PENALTIES.get(finding.severity, 10) for finding in findings)
    score = max(0.0, 100.0 - penalty)
    action = decide(score, findings)
    incident_id = str(uuid.uuid4())
    quarantine_path = None

    if action in {"QUARANTINE", "BLOCK"} and write_quarantine:
        quarantine_path = save_quarantine(incident_id, event, [finding.to_dict() for finding in findings])

    result = ImmunityResult(
        action=action,
        score=score,
        findings=findings,
        event=event,
        incident_id=incident_id,
        quarantine_path=quarantine_path,
    )
    if write_ledger and ledger_path is not None:
        ledger_payload = result.to_dict()
        ledger_payload["event"] = redacted_event(event)
        ledger_payload["findings"] = redacted_findings(ledger_payload["findings"])
        result.ledger = append(ledger_payload, ledger_path=ledger_path)
    return result
