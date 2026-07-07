"""Structured JSON logging and in-process metrics for almunaa."""

from __future__ import annotations

import json
import logging
import threading
import time
from collections import deque
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        event: dict[str, Any] = {
            "ts": self.formatTime(record, "%Y-%m-%dT%H:%M:%S%z"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        extra = getattr(record, "event", None)
        if isinstance(extra, dict):
            event.update(extra)
        if record.exc_info:
            event["exception"] = self.formatException(record.exc_info)
        return json.dumps(event, ensure_ascii=False)


def setup_logging(name: str, log_dir: Path, level: str = "INFO") -> logging.Logger:
    logger = logging.getLogger(name)
    if getattr(logger, "_svc_configured", False):
        return logger
    logger.setLevel(getattr(logging, level, logging.INFO))
    logger.propagate = False
    formatter = JsonFormatter()

    log_dir.mkdir(parents=True, exist_ok=True)
    file_handler = RotatingFileHandler(
        log_dir / f"{name}.jsonl", maxBytes=5_000_000, backupCount=3, encoding="utf-8"
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)

    logger._svc_configured = True  # type: ignore[attr-defined]
    return logger


def teardown_logging(logger: logging.Logger) -> None:
    for handler in list(logger.handlers):
        handler.close()
        logger.removeHandler(handler)
    logger._svc_configured = False  # type: ignore[attr-defined]


class Metrics:
    """Thread-safe counters + bounded latency reservoir with percentiles."""

    def __init__(self, service: str, version: str, reservoir_size: int = 4096) -> None:
        self.service = service
        self.version = version
        self.started_at = time.time()
        self._lock = threading.Lock()
        self._counters: dict[str, int] = {}
        self._latencies_ms: deque[float] = deque(maxlen=reservoir_size)

    def inc(self, name: str, amount: int = 1) -> None:
        with self._lock:
            self._counters[name] = self._counters.get(name, 0) + amount

    def observe_ms(self, duration_ms: float) -> None:
        with self._lock:
            self._latencies_ms.append(float(duration_ms))

    @staticmethod
    def _percentile(sorted_values: list[float], pct: float) -> float:
        if not sorted_values:
            return 0.0
        index = min(len(sorted_values) - 1, max(0, round(pct / 100.0 * (len(sorted_values) - 1))))
        return sorted_values[index]

    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            counters = dict(self._counters)
            latencies = sorted(self._latencies_ms)
        return {
            "service": self.service,
            "version": self.version,
            "uptime_s": round(time.time() - self.started_at, 3),
            "counters": counters,
            "latency_ms": {
                "samples": len(latencies),
                "p50": round(self._percentile(latencies, 50), 3),
                "p95": round(self._percentile(latencies, 95), 3),
                "p99": round(self._percentile(latencies, 99), 3),
                "max": round(latencies[-1], 3) if latencies else 0.0,
            },
        }
