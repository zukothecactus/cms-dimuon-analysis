"""Small Day 1 command line: environment, synthetic demo, bounded inspection."""

import argparse
import json
import sys
from dataclasses import replace
from pathlib import Path

from dimuon.config import load_config
from dimuon.demo import create_demo
from dimuon.inspection import environment_info, inspect_dataset
from dimuon.analysis import run_chunked_analysis


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
    
    #
    analyze = subparsers.add_parser("analyze", help = "Run the chunked baseline selection and plot the mass spectrum")
    analyze.add_argument("--input", default = "data/synthetic-demo.root", help = "Path to the input ROOT file")
    analyze.add_argument("--entry-start", type=int, default=0, help = "Starting event index")
    analyze.add_argument("--entry-stop", type=int, default=10000, help = "Stopping event index")
    analyze.add_argument("--chunk-size", type=int, default=1000, help = "Size of each chunk")
    analyze.add_argument("--num-workers", type=int, default=1, help="Number of parallel processes")
    analyze.add_argument("--output-plot", default="outputs/threshold_mass_spectrum.png", help = "Path to save the output plot")
    analyze.add_argument("--output-json", default="outputs/baseline_analysis.json", help = "Path to save the cutflow JSON")
    analyze.add_argument("--fit-min", type=float, default=None, help="Fit window lower mass bound (GeV)")
    analyze.add_argument("--fit-max", type=float, default=None, help="Fit window upper mass bound (GeV)")
    args = parser.parse_args(argv)
    #business logic for the CLI commands
    try:
        if args.command == "environment":
            emit(environment_info(), args.output)
        elif args.command == "make-demo":
            destination = create_demo(args.output)
            emit({"status": "created", "data_kind": "synthetic", "path": str(destination)}, None)
        elif args.command == "analyze":
            fit_window = None
            if args.fit_min is not None and args.fit_max is not None:
                fit_window = (args.fit_min, args.fit_max)
            cutflow = run_chunked_analysis(
                file_path=args.input,
                entry_start=args.entry_start,
                entry_stop=args.entry_stop,
                chunk_size=args.chunk_size,
                num_workers=args.num_workers,
                fit_window=fit_window,
                output_plot_path=args.output_plot
            )
            emit({"status": "success", "cutflow": cutflow}, args.output_json)
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
