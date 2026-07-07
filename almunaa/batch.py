from __future__ import annotations

import json
import statistics
import time
import tracemalloc
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

from .core import scan_event
from .lexical_model import LexicalModel
from .models import AgentEvent


UNSAFE_ACTIONS = {"REVIEW", "QUARANTINE", "BLOCK"}


@dataclass
class BatchOptions:
    limit: int | None = None
    repeat: int = 1
    write_ledger: bool = False
    write_quarantine: bool = False
    model_path: str | Path | None = None
    split: str | None = None


def iter_jsonl(path: str | Path) -> Iterable[dict[str, Any]]:
    with Path(path).open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                yield json.loads(line)


def _event_from_record(record: dict[str, Any]) -> AgentEvent:
    if isinstance(record.get("event"), dict):
        return AgentEvent.from_dict(record["event"])
    return AgentEvent.from_dict(record)


def _expected_unsafe(record: dict[str, Any]) -> bool | None:
    for key in ("expected_unsafe", "unsafe", "malicious"):
        if key in record:
            return bool(record[key])
    if "label" in record:
        label = record["label"]
        if isinstance(label, bool):
            return label
        if isinstance(label, int):
            return label == 1
        label_text = str(label).strip().lower()
        if label_text in {"1", "true", "malicious", "injection", "jailbreak", "unsafe"}:
            return True
        if label_text in {"0", "false", "benign", "safe"}:
            return False
    return None


def percentile(values: list[float], pct: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    index = min(len(ordered) - 1, max(0, round((pct / 100.0) * (len(ordered) - 1))))
    return ordered[index]


def evaluate_jsonl(path: str | Path, options: BatchOptions | None = None) -> dict[str, Any]:
    opts = options or BatchOptions()
    base_records = [record for record in iter_jsonl(path) if not opts.split or record.get("split") == opts.split]
    if opts.limit is not None:
        base_records = base_records[: opts.limit]
    lexical_model = LexicalModel.load(opts.model_path) if opts.model_path else None

    started = time.perf_counter()
    tracemalloc.start()
    durations_ms: list[float] = []
    action_counts: Counter[str] = Counter()
    rule_counts: Counter[str] = Counter()
    category_counts: Counter[str] = Counter()
    errors: list[dict[str, Any]] = []
    tp = tn = fp = fn = unlabeled = 0
    total_chars = 0
    max_chars = 0
    processed = 0

    for round_idx in range(max(1, opts.repeat)):
        for row_idx, record in enumerate(base_records):
            processed += 1
            try:
                event = _event_from_record(record)
                text_len = len(event.scan_text())
                total_chars += text_len
                max_chars = max(max_chars, text_len)
                scan_started = time.perf_counter()
                result = scan_event(
                    event,
                    write_ledger=opts.write_ledger,
                    write_quarantine=opts.write_quarantine,
                    lexical_model=lexical_model,
                )
                durations_ms.append((time.perf_counter() - scan_started) * 1000)
                action_counts[result.action] += 1
                for finding in result.findings:
                    rule_counts[finding.code] += 1
                if isinstance(record.get("category"), str):
                    category_counts[record["category"]] += 1

                expected = _expected_unsafe(record)
                predicted = result.action in UNSAFE_ACTIONS
                if expected is None:
                    unlabeled += 1
                elif expected and predicted:
                    tp += 1
                elif expected and not predicted:
                    fn += 1
                elif not expected and predicted:
                    fp += 1
                else:
                    tn += 1
            except Exception as exc:  # Defensive batch mode: report bad rows, keep going.
                errors.append({"round": round_idx, "row": row_idx, "error": repr(exc)})

    current_bytes, peak_bytes = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    elapsed = time.perf_counter() - started
    labeled = tp + tn + fp + fn
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    specificity = tn / (tn + fp) if tn + fp else 0.0
    accuracy = (tp + tn) / labeled if labeled else 0.0
    f1 = (2 * precision * recall / (precision + recall)) if precision + recall else 0.0

    p99_under_10ms = percentile(durations_ms, 99) < 10 if durations_ms else True
    p99_under_25ms = percentile(durations_ms, 99) < 25 if durations_ms else True
    peak_memory_under_128mb = peak_bytes < 128 * 1024 * 1024
    no_exceptions = not errors
    collapse_status = "PASS" if (no_exceptions and p99_under_25ms and peak_memory_under_128mb) else "DEGRADED"

    return {
        "input": str(Path(path).resolve()),
        "records_loaded": len(base_records),
        "repeat": max(1, opts.repeat),
        "split": opts.split,
        "model_path": str(Path(opts.model_path).resolve()) if opts.model_path else None,
        "processed": processed,
        "errors": len(errors),
        "error_samples": errors[:10],
        "elapsed_seconds": round(elapsed, 4),
        "throughput_per_second": round(processed / elapsed, 2) if elapsed else 0.0,
        "latency_ms": {
            "mean": round(statistics.fmean(durations_ms), 4) if durations_ms else 0.0,
            "p50": round(percentile(durations_ms, 50), 4),
            "p95": round(percentile(durations_ms, 95), 4),
            "p99": round(percentile(durations_ms, 99), 4),
            "max": round(max(durations_ms), 4) if durations_ms else 0.0,
        },
        "memory": {
            "current_mb": round(current_bytes / (1024 * 1024), 3),
            "peak_mb": round(peak_bytes / (1024 * 1024), 3),
        },
        "input_chars": {
            "total": total_chars,
            "mean": round(total_chars / processed, 2) if processed else 0.0,
            "max": max_chars,
        },
        "actions": dict(action_counts),
        "top_rules": dict(rule_counts.most_common(25)),
        "categories": dict(category_counts.most_common(25)),
        "labeled": labeled,
        "unlabeled": unlabeled,
        "confusion": {"tp": tp, "tn": tn, "fp": fp, "fn": fn},
        "metrics": {
            "accuracy": round(accuracy, 4),
            "precision": round(precision, 4),
            "recall": round(recall, 4),
            "specificity": round(specificity, 4),
            "f1": round(f1, 4),
        },
        "collapse": {
            "status": collapse_status,
            "no_exceptions": no_exceptions,
            "p99_under_10ms": p99_under_10ms,
            "p99_under_25ms": p99_under_25ms,
            "peak_memory_under_128mb": peak_memory_under_128mb,
        },
    }
