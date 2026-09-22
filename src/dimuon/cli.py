"""Small Day 1 command line: environment, synthetic demo, bounded inspection."""

import argparse
import json
import sys
from dataclasses import replace
from pathlib import Path

from dimuon.config import load_config
from dimuon.demo import create_demo
from dimuon.inspection import environment_info, inspect_dataset


def emit(value: dict, output: str | None) -> None:
    text = json.dumps(value, indent=2, allow_nan=False)
    if output:
        path = Path(output)
        path.parent.mkdir(parents=True, exist_ok=True)
        # Exclusive mode: failed or repeated runs cannot silently overwrite evidence.
        with path.open("x", encoding="utf-8") as handle:
            handle.write(text + "\n")
    print(text)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Day 1 dimuon data-inspection scaffold")
    subparsers = parser.add_subparsers(dest="command", required=True)
    env = subparsers.add_parser("environment", help="Print versions, optionally save them")
    env.add_argument("--output")
    demo = subparsers.add_parser("make-demo", help="Create five SYNTHETIC events, not CERN data")
    demo.add_argument("--output", default="data/synthetic-demo.root")
    inspect = subparsers.add_parser("inspect", help="Read only the configured entry range")
    inspect.add_argument("--config", default="configs/day1.json")
    inspect.add_argument("--input", help="Override source; local ROOT files are allowed")
    inspect.add_argument("--entries", type=int, help="Read this many entries from configured start")
    inspect.add_argument("--output", help="Save a new JSON report, refusing existing files")
    args = parser.parse_args(argv)
    try:
        if args.command == "environment":
            emit(environment_info(), args.output)
        elif args.command == "make-demo":
            destination = create_demo(args.output)
            emit({"status": "created", "data_kind": "synthetic", "path": str(destination)}, None)
        else:
            # Check before expensive remote work.
            if args.output and Path(args.output).exists():
                raise FileExistsError(f"Refusing to overwrite {args.output}")
            config = load_config(args.config)
            if args.input is not None:
                config = replace(config, source=args.input)
            if args.entries is not None:
                config = replace(config, entry_stop=config.entry_start + args.entries)
            emit(inspect_dataset(config), args.output)
    except Exception as exc:
        # Preserve the exception type/message as machine-readable stderr.
        print(
            json.dumps({"status": "error", "error_type": type(exc).__name__, "message": str(exc)}),
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
