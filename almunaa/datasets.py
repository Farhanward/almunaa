from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


HF_ROWS_URL = "https://datasets-server.huggingface.co/rows"
HF_SIZE_URL = "https://datasets-server.huggingface.co/size"
USER_AGENT = "almunaa-local-benchmark/0.2"


def _get_json(url: str, retries: int = 6) -> dict[str, Any]:
    request = Request(url, headers={"User-Agent": USER_AGENT})
    for attempt in range(retries):
        try:
            with urlopen(request, timeout=60) as response:
                return json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            if exc.code not in {429, 500, 502, 503, 504} or attempt == retries - 1:
                raise
            retry_after = exc.headers.get("Retry-After")
            delay = float(retry_after) if retry_after and retry_after.isdigit() else min(60.0, 2.0 * (attempt + 1))
            time.sleep(delay)
    raise RuntimeError("unreachable retry state")


def _dataset_url(endpoint: str, **params: Any) -> str:
    return f"{endpoint}?{urlencode(params)}"


def _line_count(path: Path) -> int:
    if not path.exists():
        return 0
    count = 0
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                count += 1
    return count


def fetch_neuralchemy_full(
    raw_out: str | Path,
    events_out: str | Path,
    page_size: int = 100,
    sleep_seconds: float = 0.0,
) -> dict[str, Any]:
    dataset = "neuralchemy/Prompt-injection-dataset"
    config = "full"
    splits = ("train", "validation", "test")
    raw_path = Path(raw_out)
    events_path = Path(events_out)
    raw_path.parent.mkdir(parents=True, exist_ok=True)
    events_path.parent.mkdir(parents=True, exist_ok=True)

    size_url = _dataset_url(HF_SIZE_URL, dataset=dataset, config=config)
    size_info = _get_json(size_url)
    split_sizes = {
        item["split"]: int(item["num_rows"])
        for item in size_info.get("size", {}).get("splits", [])
        if item.get("split") in splits
    }

    existing_raw = _line_count(raw_path)
    existing_events = _line_count(events_path)
    resume_rows = existing_raw if existing_raw == existing_events else 0
    mode = "a" if resume_rows else "w"
    total = resume_rows
    label_counts = {0: 0, 1: 0}
    category_counts: dict[str, int] = {}
    rows_to_skip = resume_rows
    with raw_path.open(mode, encoding="utf-8") as raw_handle, events_path.open(mode, encoding="utf-8") as event_handle:
        for split in splits:
            split_total = split_sizes.get(split, 0)
            split_skip = min(rows_to_skip, split_total)
            rows_to_skip -= split_skip
            start_offset = (split_skip // page_size) * page_size
            for offset in range(start_offset, split_total, page_size):
                url = _dataset_url(
                    HF_ROWS_URL,
                    dataset=dataset,
                    config=config,
                    split=split,
                    offset=offset,
                    length=min(page_size, split_total - offset),
                )
                page = _get_json(url)
                for row_data in page.get("rows", []):
                    row = dict(row_data.get("row") or {})
                    row_idx = int(row_data.get("row_idx", offset))
                    if row_idx < split_skip:
                        continue
                    label = int(row.get("label", 0))
                    category = str(row.get("category") or "")
                    text = str(row.get("text") or "")
                    source = str(row.get("source") or "")
                    raw_record = {
                        "dataset": dataset,
                        "config": config,
                        "split": split,
                        "row_idx": row_idx,
                        **row,
                    }
                    event_record = {
                        "dataset": dataset,
                        "config": config,
                        "split": split,
                        "row_idx": row_idx,
                        "label": label,
                        "expected_unsafe": label == 1,
                        "category": category,
                        "source": source,
                        "event": {
                            "kind": "input",
                            "agent": "dataset-neuralchemy",
                            "content": text,
                            "context": {
                                "dataset": "neuralchemy_prompt_injection",
                                "split": split,
                                "row_idx": row_idx,
                            },
                        },
                    }
                    raw_handle.write(json.dumps(raw_record, ensure_ascii=False) + "\n")
                    event_handle.write(json.dumps(event_record, ensure_ascii=False) + "\n")
                    total += 1
                    label_counts[label] = label_counts.get(label, 0) + 1
                    if category:
                        category_counts[category] = category_counts.get(category, 0) + 1
                if sleep_seconds:
                    time.sleep(sleep_seconds)

    final_rows = 0
    final_labels: dict[str, int] = {}
    final_categories: dict[str, int] = {}
    with events_path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            record = json.loads(line)
            final_rows += 1
            label_key = str(record.get("label", ""))
            final_labels[label_key] = final_labels.get(label_key, 0) + 1
            category_key = str(record.get("category") or "")
            if category_key:
                final_categories[category_key] = final_categories.get(category_key, 0) + 1

    return {
        "dataset": dataset,
        "config": config,
        "raw_out": str(raw_path.resolve()),
        "events_out": str(events_path.resolve()),
        "rows": final_rows,
        "resumed_from_rows": resume_rows,
        "new_rows": max(0, total - resume_rows),
        "labels": dict(sorted(final_labels.items())),
        "categories": dict(sorted(final_categories.items(), key=lambda item: item[1], reverse=True)[:25]),
    }
