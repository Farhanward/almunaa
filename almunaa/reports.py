from __future__ import annotations

from typing import Any

from .models import ImmunityResult


def to_markdown(result: ImmunityResult) -> str:
    lines = [
        "# تقرير المناعة",
        "",
        f"- الإجراء: `{result.action}`",
        f"- الدرجة: `{result.score:.1f}/100`",
        f"- رقم الحادثة: `{result.incident_id}`",
    ]
    if result.quarantine_path:
        lines.append(f"- الحجر الصحي: `{result.quarantine_path}`")
    if result.ledger:
        lines.append(f"- سجل التدقيق: `{result.ledger.get('record_hash')}`")
    lines.extend(["", "## الملاحظات", ""])
    if not result.findings:
        lines.append("لا توجد مؤشرات خطر.")
    for finding in result.findings:
        evidence = f" — `{finding.evidence}`" if finding.evidence else ""
        lines.append(f"- **{finding.severity} / {finding.title}:** {finding.detail}{evidence}")
    lines.append("")
    return "\n".join(lines)


def _pct(value: float) -> str:
    return f"{value * 100:.2f}%"


def batch_to_markdown(report: dict[str, Any]) -> str:
    metrics = report.get("metrics", {})
    latency = report.get("latency_ms", {})
    memory = report.get("memory", {})
    collapse = report.get("collapse", {})
    confusion = report.get("confusion", {})
    lines = [
        "# تقرير اختبار المناعة الواسع",
        "",
        f"- الملف: `{report.get('input')}`",
        f"- السجلات المحمّلة: `{report.get('records_loaded')}`",
        f"- مرات التكرار: `{report.get('repeat')}`",
        f"- إجمالي الفحوص: `{report.get('processed')}`",
        f"- الأخطاء: `{report.get('errors')}`",
        f"- الزمن: `{report.get('elapsed_seconds')}s`",
        f"- الإنتاجية: `{report.get('throughput_per_second')}` فحص/ثانية",
        "",
        "## الجودة",
        "",
        f"- Accuracy: `{_pct(float(metrics.get('accuracy', 0)))}`",
        f"- Precision: `{_pct(float(metrics.get('precision', 0)))}`",
        f"- Recall: `{_pct(float(metrics.get('recall', 0)))}`",
        f"- Specificity: `{_pct(float(metrics.get('specificity', 0)))}`",
        f"- F1: `{_pct(float(metrics.get('f1', 0)))}`",
        f"- Confusion: `TP={confusion.get('tp', 0)} TN={confusion.get('tn', 0)} FP={confusion.get('fp', 0)} FN={confusion.get('fn', 0)}`",
        "",
        "## الضغط والانهيار",
        "",
        f"- الحالة: `{collapse.get('status')}`",
        f"- بلا استثناءات: `{collapse.get('no_exceptions')}`",
        f"- P99 أقل من 10ms: `{collapse.get('p99_under_10ms')}`",
        f"- P99 أقل من 25ms: `{collapse.get('p99_under_25ms')}`",
        f"- ذروة الذاكرة أقل من 128MB: `{collapse.get('peak_memory_under_128mb')}`",
        f"- Latency mean/p95/p99/max: `{latency.get('mean')} / {latency.get('p95')} / {latency.get('p99')} / {latency.get('max')}` ms",
        f"- Peak memory: `{memory.get('peak_mb')}` MB",
        "",
        "## توزيع القرارات",
        "",
    ]
    actions = report.get("actions") or {}
    if not actions:
        lines.append("لا توجد قرارات.")
    for action, count in actions.items():
        lines.append(f"- `{action}`: `{count}`")
    lines.extend(["", "## أكثر القواعد عملاً", ""])
    top_rules = report.get("top_rules") or {}
    if not top_rules:
        lines.append("لا توجد قواعد مفعلة.")
    for code, count in top_rules.items():
        lines.append(f"- `{code}`: `{count}`")
    error_samples = report.get("error_samples") or []
    if error_samples:
        lines.extend(["", "## عينات أخطاء", ""])
        for sample in error_samples:
            lines.append(f"- `{sample}`")
    lines.append("")
    return "\n".join(lines)
