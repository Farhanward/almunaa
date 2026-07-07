from __future__ import annotations

import hashlib
import hmac
import json
import secrets
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


DEFAULT_LEDGER = Path("ledger") / "almunaa-ledger.jsonl"
DEFAULT_SECRET = Path("ledger") / ".almunaa-secret"


def canonical(data: Any) -> str:
    return json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def secret(path: Path) -> bytes:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        path.write_text(secrets.token_hex(32), encoding="utf-8")
    return path.read_text(encoding="utf-8").strip().encode("utf-8")


def last_hash(path: Path) -> tuple[int, str]:
    if not path.exists():
        return 0, "GENESIS"
    last = None
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            last = json.loads(line)
    if not last:
        return 0, "GENESIS"
    return int(last["index"]), str(last["record_hash"])


def append(payload: dict[str, Any], ledger_path: str | Path = DEFAULT_LEDGER) -> dict[str, Any]:
    path = Path(ledger_path)
    index, previous = last_hash(path)
    base = {
        "index": index + 1,
        "timestamp": datetime.now(UTC).isoformat(),
        "previous_hash": previous,
        "payload_hash": sha(canonical(payload)),
    }
    record_hash = sha(canonical(base))
    seal = hmac.new(secret(DEFAULT_SECRET), record_hash.encode("utf-8"), hashlib.sha256).hexdigest()
    record = {**base, "record_hash": record_hash, "seal": seal, "payload": payload}
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(canonical(record) + "\n")
    return {key: record[key] for key in ("index", "timestamp", "previous_hash", "payload_hash", "record_hash", "seal")}


def verify(ledger_path: str | Path = DEFAULT_LEDGER) -> dict[str, Any]:
    path = Path(ledger_path)
    if not path.exists():
        return {"ok": True, "records": 0, "message": "ledger file does not exist yet"}
    key = secret(DEFAULT_SECRET)
    previous = "GENESIS"
    count = 0
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        record = json.loads(line)
        base = {
            "index": record.get("index"),
            "timestamp": record.get("timestamp"),
            "previous_hash": record.get("previous_hash"),
            "payload_hash": record.get("payload_hash"),
        }
        if record.get("previous_hash") != previous:
            return {"ok": False, "line": line_number, "message": "broken hash chain"}
        if record.get("payload_hash") != sha(canonical(record.get("payload"))):
            return {"ok": False, "line": line_number, "message": "payload hash mismatch"}
        if record.get("record_hash") != sha(canonical(base)):
            return {"ok": False, "line": line_number, "message": "record hash mismatch"}
        expected = hmac.new(key, str(record.get("record_hash")).encode("utf-8"), hashlib.sha256).hexdigest()
        if record.get("seal") != expected:
            return {"ok": False, "line": line_number, "message": "seal mismatch"}
        previous = str(record.get("record_hash"))
        count += 1
    return {"ok": True, "records": count, "message": "ledger verified"}

