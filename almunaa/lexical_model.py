from __future__ import annotations

import json
import math
import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .normalization import deobfuscate_text


TOKEN_RE = re.compile(r"[a-z\u0600-\u06ff]{2,}|[a-z0-9]{3,}", re.I)


def iter_jsonl(path: str | Path):
    with Path(path).open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                yield json.loads(line)


def tokens_for(text: str) -> set[str]:
    normalized = deobfuscate_text(text)
    tokens = {match.group(0).lower() for match in TOKEN_RE.finditer(normalized)}
    squashed = re.sub(r"[^a-z0-9]+", "", normalized)
    if 8 <= len(squashed):
        squashed = squashed[:400]
        tokens.update(f"char4:{squashed[idx:idx + 4]}" for idx in range(max(0, len(squashed) - 3)))
    return tokens


def _expected_label(record: dict[str, Any]) -> int | None:
    if "label" not in record:
        return None
    value = record["label"]
    if isinstance(value, int):
        return 1 if value == 1 else 0
    value_text = str(value).strip().lower()
    if value_text in {"1", "true", "malicious", "injection", "jailbreak", "unsafe"}:
        return 1
    if value_text in {"0", "false", "benign", "safe"}:
        return 0
    return None


def _record_text(record: dict[str, Any]) -> str:
    event = record.get("event")
    if isinstance(event, dict):
        return str(event.get("content") or "")
    return str(record.get("content") or record.get("text") or "")


@dataclass
class LexicalModel:
    vocab: list[str]
    log_prior_safe: float
    log_prior_unsafe: float
    log_prob_safe: dict[str, float]
    log_prob_unsafe: dict[str, float]
    unknown_safe: float
    unknown_unsafe: float
    threshold: float
    metadata: dict[str, Any]

    def score(self, text: str) -> float:
        token_set = tokens_for(text)
        safe = self.log_prior_safe
        unsafe = self.log_prior_unsafe
        for token in token_set:
            safe += self.log_prob_safe.get(token, self.unknown_safe)
            unsafe += self.log_prob_unsafe.get(token, self.unknown_unsafe)
        max_log = max(safe, unsafe)
        safe_exp = math.exp(safe - max_log)
        unsafe_exp = math.exp(unsafe - max_log)
        return unsafe_exp / (safe_exp + unsafe_exp)

    def to_dict(self) -> dict[str, Any]:
        return {
            "vocab": self.vocab,
            "log_prior_safe": self.log_prior_safe,
            "log_prior_unsafe": self.log_prior_unsafe,
            "log_prob_safe": self.log_prob_safe,
            "log_prob_unsafe": self.log_prob_unsafe,
            "unknown_safe": self.unknown_safe,
            "unknown_unsafe": self.unknown_unsafe,
            "threshold": self.threshold,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "LexicalModel":
        return cls(
            vocab=list(data["vocab"]),
            log_prior_safe=float(data["log_prior_safe"]),
            log_prior_unsafe=float(data["log_prior_unsafe"]),
            log_prob_safe={str(key): float(value) for key, value in data["log_prob_safe"].items()},
            log_prob_unsafe={str(key): float(value) for key, value in data["log_prob_unsafe"].items()},
            unknown_safe=float(data["unknown_safe"]),
            unknown_unsafe=float(data["unknown_unsafe"]),
            threshold=float(data["threshold"]),
            metadata=dict(data.get("metadata") or {}),
        )

    @classmethod
    def load(cls, path: str | Path) -> "LexicalModel":
        return cls.from_dict(json.loads(Path(path).read_text(encoding="utf-8")))

    def save(self, path: str | Path) -> None:
        out_path = Path(path)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(self.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")


def _records_for_split(path: str | Path, split: str | None) -> list[dict[str, Any]]:
    records = []
    for record in iter_jsonl(path):
        if split and record.get("split") != split:
            continue
        if _expected_label(record) is not None:
            records.append(record)
    return records


def _metrics_for_scores(scored: list[tuple[float, int]], threshold: float) -> dict[str, float]:
    tp = tn = fp = fn = 0
    for score, label in scored:
        predicted = score >= threshold
        if label and predicted:
            tp += 1
        elif label and not predicted:
            fn += 1
        elif not label and predicted:
            fp += 1
        else:
            tn += 1
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    accuracy = (tp + tn) / max(1, tp + tn + fp + fn)
    f1 = (2 * precision * recall / (precision + recall)) if precision + recall else 0.0
    return {"accuracy": accuracy, "precision": precision, "recall": recall, "f1": f1, "tp": tp, "tn": tn, "fp": fp, "fn": fn}


def _best_threshold(scored: list[tuple[float, int]]) -> tuple[float, dict[str, float]]:
    best_threshold = 0.5
    best_metrics = _metrics_for_scores(scored, best_threshold)
    constrained_threshold = None
    constrained_metrics = None
    for idx in range(5, 96):
        threshold = idx / 100
        metrics = _metrics_for_scores(scored, threshold)
        if metrics["f1"] > best_metrics["f1"]:
            best_threshold = threshold
            best_metrics = metrics
        specificity = metrics["tn"] / (metrics["tn"] + metrics["fp"]) if metrics["tn"] + metrics["fp"] else 0.0
        if specificity >= 0.9 and (constrained_metrics is None or metrics["f1"] > constrained_metrics["f1"]):
            constrained_threshold = threshold
            constrained_metrics = metrics
    if constrained_threshold is not None and constrained_metrics is not None:
        return constrained_threshold, constrained_metrics
    return best_threshold, best_metrics


def train_lexical_model(
    input_path: str | Path,
    out_path: str | Path,
    train_split: str = "train",
    validation_split: str = "validation",
    max_features: int = 25000,
    min_count: int = 2,
    alpha: float = 0.5,
) -> dict[str, Any]:
    train_records = _records_for_split(input_path, train_split)
    if not train_records:
        raise ValueError(f"no labeled records found for split={train_split!r}")

    docs_by_label = {0: 0, 1: 0}
    token_counts = {0: Counter(), 1: Counter()}
    document_frequency = Counter()
    for record in train_records:
        label = int(_expected_label(record) or 0)
        docs_by_label[label] += 1
        token_set = tokens_for(_record_text(record))
        document_frequency.update(token_set)
        token_counts[label].update(token_set)

    vocab = [
        token
        for token, count in document_frequency.most_common(max_features)
        if count >= min_count
    ]
    vocab_set = set(vocab)
    totals = {
        label: sum(count for token, count in token_counts[label].items() if token in vocab_set)
        for label in (0, 1)
    }
    vocab_size = max(1, len(vocab))
    total_docs = docs_by_label[0] + docs_by_label[1]
    log_prior_safe = math.log((docs_by_label[0] + alpha) / (total_docs + 2 * alpha))
    log_prior_unsafe = math.log((docs_by_label[1] + alpha) / (total_docs + 2 * alpha))
    unknown_safe = math.log(alpha / (totals[0] + alpha * vocab_size))
    unknown_unsafe = math.log(alpha / (totals[1] + alpha * vocab_size))
    log_prob_safe = {
        token: math.log((token_counts[0].get(token, 0) + alpha) / (totals[0] + alpha * vocab_size))
        for token in vocab
    }
    log_prob_unsafe = {
        token: math.log((token_counts[1].get(token, 0) + alpha) / (totals[1] + alpha * vocab_size))
        for token in vocab
    }
    model = LexicalModel(
        vocab=vocab,
        log_prior_safe=log_prior_safe,
        log_prior_unsafe=log_prior_unsafe,
        log_prob_safe=log_prob_safe,
        log_prob_unsafe=log_prob_unsafe,
        unknown_safe=unknown_safe,
        unknown_unsafe=unknown_unsafe,
        threshold=0.5,
        metadata={
            "input": str(Path(input_path).resolve()),
            "train_split": train_split,
            "validation_split": validation_split,
            "train_records": len(train_records),
            "docs_by_label": docs_by_label,
            "max_features": max_features,
            "min_count": min_count,
            "alpha": alpha,
        },
    )

    validation_records = _records_for_split(input_path, validation_split)
    validation_metrics: dict[str, float] = {}
    if validation_records:
        scored = [(model.score(_record_text(record)), int(_expected_label(record) or 0)) for record in validation_records]
        threshold, validation_metrics = _best_threshold(scored)
        model.threshold = threshold
    model.metadata["validation_records"] = len(validation_records)
    model.metadata["validation_metrics"] = validation_metrics
    model.save(out_path)
    return {
        "model": str(Path(out_path).resolve()),
        "train_records": len(train_records),
        "validation_records": len(validation_records),
        "vocab_size": len(vocab),
        "threshold": model.threshold,
        "validation_metrics": validation_metrics,
    }
