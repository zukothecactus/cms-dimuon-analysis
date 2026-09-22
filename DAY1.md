# CMS Dimuon Starter:

Read the [CERN analysis record](https://opendata.cern.ch/record/12342), then `README.md` and `docs/PROVENANCE.md`. Write your own three-sentence description in a notebook or private learning log:

Goal for today:
> Build a reproducible Python analysis of a documented slice of CMS open dimuon data.
> Validate the event selection and invariant-mass calculation, then compare how chosen momentum cuts change the observed spectrum.
> Build reliable analysis SW

### Synthetic-data access:

```bash
uv sync --locked --python 3.12
uv run --locked pytest -q
uv run --locked dimuon environment --output outputs/my-environment.json
uv run --locked dimuon make-demo --output data/my-synthetic-demo.root
uv run --locked dimuon inspect --input data/my-synthetic-demo.root --output outputs/my-demo-inspection.json
```

Expected synthetic facts: five events; multiplicities 0, 1, 2, and 3 occur 1, 1, 2, and 1 times respectively. The report says `synthetic-demo-not-physics-data`; 

### Real-data access:

I started with ten entries, not the full dataset. The data URL, `Events` tree, and bounded-read approach are documented in the [HSF tutorial](https://hsf-training.github.io/hsf-training-scikit-hep-webpage/aio/index.html).

```bash
uv sync --locked --python 3.12 --extra remote
uv run --locked --extra remote dimuon inspect --entries 10 --output outputs/my-cms-first-10.json
```

If that works (will not if CMake is not installed), inspect the first 1,000:

```bash
uv run --locked --extra remote dimuon inspect --output outputs/my-cms-first-1000.json
```

Read `entries_read`, `entry_start`, `entry_stop_effective`, `branch_types`, and the first three events. A “first 1,000 entries” request is not “1,000 selected dimuon pairs”; selection has not happened yet.

Since access failed, I kept the actual error and continued with the synthetic path. An access failure is acceptable on the 1st day; falsely claiming that the real sample was read is not.

Follow one command from `cli.py` into `config.py` and `inspection.py`, so that you can find the exact lines that enforce entry bounds and the exact lines that mark the synthetic fixture.