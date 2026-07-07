from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .batch import BatchOptions, evaluate_jsonl
from .core import scan_event
from .datasets import fetch_neuralchemy_full
from .ledger import DEFAULT_LEDGER, verify
from .lexical_model import LexicalModel, train_lexical_model
from .models import AgentEvent
from .reports import batch_to_markdown, to_markdown


def load_event(path: Path) -> AgentEvent:
    return AgentEvent.from_dict(json.loads(path.read_text(encoding="utf-8")))


def scan_command(args: argparse.Namespace) -> int:
    event = load_event(Path(args.input))
    model = LexicalModel.load(args.model) if args.model else None
    result = scan_event(event, ledger_path=args.ledger, write_ledger=not args.no_ledger, lexical_model=model)
    payload = json.dumps(result.to_dict(), ensure_ascii=False, indent=2) if args.format == "json" else to_markdown(result)
    if args.out:
        out_path = Path(args.out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(payload, encoding="utf-8")
        print(str(out_path.resolve()))
    else:
        print(payload)
    return 2 if args.fail_on_block and result.action in {"BLOCK", "QUARANTINE"} else 0


def verify_command(args: argparse.Namespace) -> int:
    result = verify(args.ledger)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result.get("ok") else 1


def download_dataset_command(args: argparse.Namespace) -> int:
    if args.dataset != "neuralchemy-full":
        raise SystemExit(f"unknown dataset: {args.dataset}")
    result = fetch_neuralchemy_full(
        raw_out=args.raw_out,
        events_out=args.events_out,
        page_size=args.page_size,
        sleep_seconds=args.sleep,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


def batch_command(args: argparse.Namespace) -> int:
    report = evaluate_jsonl(
        args.input,
        BatchOptions(
            limit=args.limit,
            repeat=args.repeat,
            write_ledger=args.write_ledger,
            write_quarantine=args.write_quarantine,
            model_path=args.model,
            split=args.split,
        ),
    )
    payload = json.dumps(report, ensure_ascii=False, indent=2) if args.format == "json" else batch_to_markdown(report)
    if args.out:
        out_path = Path(args.out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(payload, encoding="utf-8")
        print(str(out_path.resolve()))
    else:
        print(payload)
    return 1 if report.get("errors") else 0


def train_model_command(args: argparse.Namespace) -> int:
    result = train_lexical_model(
        input_path=args.input,
        out_path=args.out,
        train_split=args.train_split,
        validation_split=args.validation_split,
        max_features=args.max_features,
        min_count=args.min_count,
        alpha=args.alpha,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(prog="almunaa", description="Local agent immunity gateway.")
    sub = root.add_subparsers(dest="command", required=True)
    scan = sub.add_parser("scan", help="Scan one agent event JSON file.")
    scan.add_argument("--input", required=True)
    scan.add_argument("--out")
    scan.add_argument("--format", choices=["json", "md"], default="json")
    scan.add_argument("--ledger", default=str(DEFAULT_LEDGER))
    scan.add_argument("--no-ledger", action="store_true")
    scan.add_argument("--fail-on-block", action="store_true")
    scan.add_argument("--model", help="Optional local lexical guard model JSON.")
    scan.set_defaults(func=scan_command)

    check = sub.add_parser("verify-ledger", help="Verify incident ledger.")
    check.add_argument("--ledger", default=str(DEFAULT_LEDGER))
    check.set_defaults(func=verify_command)

    dl = sub.add_parser("download-dataset", help="Download and convert an internet benchmark dataset.")
    dl.add_argument("--dataset", default="neuralchemy-full", choices=["neuralchemy-full"])
    dl.add_argument("--raw-out", default="data/external/neuralchemy_prompt_injection_full.jsonl")
    dl.add_argument("--events-out", default="data/benchmarks/neuralchemy_prompt_injection_full.events.jsonl")
    dl.add_argument("--page-size", type=int, default=100)
    dl.add_argument("--sleep", type=float, default=0.0)
    dl.set_defaults(func=download_dataset_command)

    batch = sub.add_parser("batch", help="Evaluate a JSONL file of agent events or labeled benchmark records.")
    batch.add_argument("--input", required=True)
    batch.add_argument("--out")
    batch.add_argument("--format", choices=["json", "md"], default="md")
    batch.add_argument("--limit", type=int)
    batch.add_argument("--repeat", type=int, default=1)
    batch.add_argument("--split")
    batch.add_argument("--model")
    batch.add_argument("--write-ledger", action="store_true")
    batch.add_argument("--write-quarantine", action="store_true")
    batch.set_defaults(func=batch_command)

    stress = sub.add_parser("stress", help="Run repeated batch scans to measure collapse behavior.")
    stress.add_argument("--input", required=True)
    stress.add_argument("--out")
    stress.add_argument("--format", choices=["json", "md"], default="md")
    stress.add_argument("--limit", type=int)
    stress.add_argument("--repeat", type=int, default=5)
    stress.add_argument("--split")
    stress.add_argument("--model")
    stress.add_argument("--write-ledger", action="store_true")
    stress.add_argument("--write-quarantine", action="store_true")
    stress.set_defaults(func=batch_command)

    train = sub.add_parser("train-model", help="Train a local lexical prompt-injection guard from labeled JSONL.")
    train.add_argument("--input", required=True)
    train.add_argument("--out", default="models/almunaa_lexical_guard.json")
    train.add_argument("--train-split", default="train")
    train.add_argument("--validation-split", default="validation")
    train.add_argument("--max-features", type=int, default=25000)
    train.add_argument("--min-count", type=int, default=2)
    train.add_argument("--alpha", type=float, default=0.5)
    train.set_defaults(func=train_model_command)

    serve = sub.add_parser("serve", help="Run the local HTTP immunity service.")
    serve.add_argument("--host")
    serve.add_argument("--port", type=int)
    serve.set_defaults(func=serve_command)

    version = sub.add_parser("version", help="Print service version.")
    version.set_defaults(func=version_command)
    return root


def serve_command(args: argparse.Namespace) -> int:
    from .service import run_server

    run_server(host=args.host, port=args.port)
    return 0


def version_command(args: argparse.Namespace) -> int:
    from .version import __version__

    print(json.dumps({"service": "almunaa", "version": __version__}, ensure_ascii=False))
    return 0


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    sys.exit(main())
