# CMS Dimuon Analysis

## Day 0
- A Python package and command-line interface.
- A configurable, bounded ROOT-file reader with schema and multiplicity checks.
- An explicitly synthetic offline demo, generated locally rather than presented as CERN data.
- Tests and a GitHub Actions workflow that need no live CERN dataset.
- Provenance notes, a Day 1 walkthrough, and a clear separation between scaffold and future work.

## Quick start

You will need the "uv" package manager. If `uv` is not installed, consult the official [uv installation guide](https://docs.astral.sh/uv/getting-started/installation/).

```bash
uv sync --locked --python 3.12
uv run --locked pytest -q
uv run --locked dimuon environment --output outputs/environment.json
uv run --locked dimuon make-demo --output data/synthetic-demo.root
uv run --locked dimuon inspect --input data/synthetic-demo.root --output outputs/demo-inspection.json
```

The demo has five artificial events, so expect `entries_read: 5` and
`data_kind: "synthetic-demo-not-physics-data"`. This is only an offline plumbing check.

For a real-data read, install the optional XRootD transport and inspect ten entries first
(won't work if CMake is not installed):

```bash
uv sync --locked --python 3.12 --extra remote
uv run --locked --extra remote dimuon inspect --entries 10 --output outputs/cms-first-10.json
```

After the first ten entries work, use the bounded Day 1 configuration:

```bash
uv run --locked --extra remote dimuon inspect --config configs/day1.json --output outputs/cms-first-1000.json
```

Use `--extra remote` consistently on subsequent `uv run` commands when remote transport is needed. Uv may otherwise synchronise away an unrequested optional dependency.

Reports are never silently overwritten. On reruns, choose a new output filename or deliberately remove only the old generated file you intend to replace; the input dataset is never modified.

## What the data is

The configured source is the muon-reduced CMS 2012 DoubleMuParked data associated with [CERN Open Data record 12342](https://opendata.cern.ch/record/12342). The [HSF Scikit-HEP tutorial](https://hsf-training.github.io/hsf-training-scikit-hep-webpage/aio/index.html) demonstrates this file, its `Events` tree, muon branches, and bounded Uproot reads.

See `docs/PROVENANCE.md` for the exact input URL and caveats. No physics data is included in the archive.

## Code should be inspected in this order

1. `configs/day1.json`: what input, branches, and entry range are requested.
2. `src/dimuon/config.py`: why unbounded or malformed requests are rejected.
3. `src/dimuon/inspection.py`: where opening, reading, checking, and reporting happen.
4. `src/dimuon/demo.py`: why this fixture is synthetic and what cases it includes.
5. `tests/test_starter.py`: which behaviours are tested.
6. `src/dimuon/cli.py`: how commands map onto the small functions.

The inspector defaults to 1,000 entries and caps a requested inspection at 100,000. This is an intentional Day 1 guardrail, not a limitation on the eventual chunked analysis.

## Failure handling

If a command fails, it exits nonzero and prints JSON to stderr with `error_type` and `message`. That message and the environment is captured before changing packages at random:

```bash
uv run --locked --extra remote dimuon inspect --entries 10 --output outputs/cms-retry.json 2> outputs/cms-access-error.txt
```

The quick start creates `outputs/` first. If starting from scratch, run the environment command before using shell redirection into that directory.

- **Missing XRootD:** Run the remote-extra sync command above.
- **Network/timeout:** Remote storage access may be blocked on a particular network. The configured timeout is a transport timeout, not a guaranteed whole-process deadline; interrupt a hung attempt and record the failure.
- **Unsupported transport installation:** Use the offline sample today and resolve remote access separately; do not rename synthetic results as real data.
- **Existing output:** Choose a new output filename. This protection prevents an accidental rerun from overwriting your evidence.
- **Missing branch/tree:** Keep the error and inspect the actual schema. Do not silently substitute another dataset.

## Recording dependencies

`uv.lock` records the resolved environment; 
`pyproject.toml` records direct requirements. 
Run `uv sync --locked` for reproducible installation, and save `dimuon environment` output on your own machine because platform and interpreter details can differ from the builder's environment.

Matplotlib and physics-analysis modules are deliberately deferred. I'll add them when the day-by-day plan actually reaches plotting and selection, with tests and a short explanation of the change.


