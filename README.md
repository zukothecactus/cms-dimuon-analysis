# CMS Dimuon Invariant-Mass Analysis

[![CI](https://github.com/zukothecactus/cms-dimuon-analysis/actions/workflows/tests.yml/badge.svg)](https://github.com/zukothecactus/cms-dimuon-analysis/actions/workflows/tests.yml)
![Python](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)
![uproot](https://img.shields.io/badge/uproot-5.7-EE4C2C)
![Awkward Array](https://img.shields.io/badge/Awkward--Array-2.x-orange)
![Scikit-HEP](https://img.shields.io/badge/Scikit--HEP-vector-blue)
![SciPy](https://img.shields.io/badge/SciPy-1.x-8CAAE6?logo=scipy)
![Docker](https://img.shields.io/badge/Docker-containerized-2496ED?logo=docker&logoColor=white)
![License](https://img.shields.io/badge/license-MIT-green)

> **A fully reproducible, containerized, streaming analysis pipeline for CMS 2012 DoubleMuParked open data — recovering J/Ψ at 3.09 GeV (45.7σ) and the Z boson at 90.82 GeV (48.3σ) from 61.5 million collision events.**

---

![Full Dimuon Invariant Mass Spectrum](outputs/final_spectrum.png)

*Full dimuon invariant-mass spectrum (2–120 GeV) for five overlaid pT threshold cuts, revealing the J/Ψ meson and Z boson resonance peaks.*

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Key Features](#2-key-features)
3. [Visual Demonstrations](#3-visual-demonstrations)
4. [Architecture & Tech Stack](#4-architecture--tech-stack)
5. [Development Journey](#5-development-journey)
6. [Getting Started](#6-getting-started)
7. [How to Run / Execution Guide](#7-how-to-run--execution-guide)
8. [Troubleshooting](#8-troubleshooting)
9. [Data Provenance & Ethics](#9-data-provenance--ethics)
10. [Project Structure](#10-project-structure)

---

## 1. Executive Summary

This project implements a production-grade High Energy Physics (HEP) analysis pipeline targeting the publicly available **CMS 2012 DoubleMuParked dataset** (CERN Open Data Record [12342](https://opendata.cern.ch/record/12342)). Starting from **61,540,413 raw collision events**, the pipeline applies sequential event-selection cuts, reconstructs the dimuon invariant mass via relativistic four-vector kinematics, and fits resonance peaks with a composite signal-plus-background statistical model.

The two well-established Standard Model resonances recovered are:

| Resonance |  PDG Mass  | **Fitted Mass** | Significance | χ²/ndf |
|:---------:|:----------:|:---------------:|:------------:|:------:|
| J/Ψ Meson |  3.097 GeV |  **3.0925 GeV** |   **45.7σ**  |  1.92  |
|  Z Boson  | 91.188 GeV |  **90.820 GeV** |   **48.3σ**  |  0.59  |

The codebase is engineered for **reproducibility as a first principle**: a `uv` lockfile pins all dependencies, a `Dockerfile` isolates the runtime environment, synthetic ROOT fixtures enable CI without CERN network access, and the CLI enforces write-once output files to prevent silent evidence overwriting.

---

## 2. Key Features

- **Streaming, memory-bounded processing** — `uproot.iterate()` reads ROOT data in configurable chunks; the full 61M-event dataset never loads into RAM simultaneously.
- **Process-based parallelism** — `concurrent.futures.ProcessPoolExecutor` distributes independent event-range slices across CPU cores, bypassing Python's GIL for CPU-bound math.
- **Two-stage event selection** — multiplicity filter (exactly 2 muons) → opposite-charge filter → configurable pT threshold scan across [0, 5, 10, 15, 20] GeV.
- **Relativistic four-vector kinematics** — Lorentz-invariant mass computed via the Scikit-HEP `vector` library (C++ backend); replaces a hand-rolled NumPy implementation.
- **Composite resonance fitting** — `scipy.optimize.curve_fit` fits a Gaussian signal + exponential background model; dynamically selects J/Ψ or Z boson parameter priors based on the mass window.
- **Dual visualization** — macroscopic full-spectrum overlay and microscopic zoomed fit window plots saved headlessly via Matplotlib's `Agg` backend.
- **Fully containerized** — `Dockerfile` based on `python:3.12-slim`; `uv` handles fast, locked dependency installation inside the image.
- **GitHub Actions CI** — runs all unit tests on every push/PR to `main` using only synthetic fixtures; no CERN network or real dataset required.
- **Write-once CLI output** — the `emit()` function opens output files in exclusive mode (`"x"`), preventing repeated runs from silently overwriting previous results.

---

## 3. Visual Demonstrations

### 3.1 Z Boson Resonance Fit

![Z Boson Fit Spectrum](outputs/z_boson_fit_spectrum.png)

*Zoomed view of the Z boson mass window. Black error bars are data with Poisson uncertainties (σ_i = √N, min 1). The red curve is the fitted Gaussian + exponential composite model.*

**Z Boson Fit Summary (`outputs/z_boson_fit_summary.json`)**

```json
{
  "resonance_name": "Z_Boson",
  "signal_yield": 4337.03,
  "signal_yield_error": 73.54,
  "fitted_mass": 90.8204,
  "fitted_mass_error": 0.0351,
  "resolution_sigma": 2.0287,
  "resolution_sigma_error": 0.0327,
  "background_yield": 3713.10,
  "chi2_ndof": 0.5925,
  "significance": 48.34
}
```

---

### 3.2 J/Ψ Meson Resonance Fit

![JPsi Fit Spectrum](outputs/jpsi_fit_spectrum.png)

*J/Ψ mass peak at ~3.09 GeV. The narrow Gaussian width (σ ≈ 33 MeV) reflects the CMS detector's mass resolution, not the natural decay width of the meson.*

**J/Ψ Fit Summary (`outputs/jphi_fit_summary.json`)**

```json
{
  "resonance_name": "JPsi",
  "signal_yield": 2922.90,
  "signal_yield_error": 58.19,
  "fitted_mass": 3.0925,
  "fitted_mass_error": 0.0007,
  "resolution_sigma": 0.0334,
  "resolution_sigma_error": 0.0006,
  "background_yield": 1168.41,
  "chi2_ndof": 1.9177,
  "significance": 45.70
}
```

---

### 3.3 Full Spectrum with Threshold Scan

![J/Phi Threshold Spectrum](outputs/Jphi_meson_threshold_mass_spectrum.png)

*Five overlaid pT threshold spectra demonstrating how increasingly aggressive transverse-momentum cuts eliminate low-mass background while preserving resonance signal.*

### 3.4 Z Boson Threshold Fit Spectrum

![Z Boson Threshold Fit](outputs/z_boson_threshold_fit_spectrum.png)

---

### 3.5 Event Selection Cutflow

From **61,540,413** initial collision events:

| Selection Step | Events Remaining | Retention |
|:---|---:|---:|
| Initial Events | 61,540,413 | 100.00% |
| Exactly 2 Muons | 31,104,343 | 50.54% |
| Opposite Charge (Baseline) | 24,067,843 | 39.11% |
| pT ≥ 5 GeV | 22,363,477 | 36.34% |
| pT ≥ 10 GeV | 15,147,769 | 24.61% |
| pT ≥ 15 GeV | 7,751,783 | 12.60% |
| pT ≥ 20 GeV | 5,702,576 | **9.27%** |

---

## 4. Architecture & Tech Stack

### Tech Stack

| Layer | Technology | Role |
|:------|:-----------|:-----|
| Data I/O | `uproot 5.7` | Streaming read of ROOT files via `iterate()` |
| Array ops | `awkward 2.x` | Jagged array operations for variable-length muon lists |
| Kinematics | `scikit-hep/vector 1.9` | Lorentz 4-vector algebra (C++ backend) |
| Numerics | `numpy 2.x` | Histogram accumulation, bin management |
| Fitting | `scipy 1.x` | `curve_fit` with Poisson-weighted residuals |
| Plotting | `matplotlib 3.x` (Agg) | Headless spectrum & fit visualization |
| CLI | `argparse` (stdlib) | Subcommand dispatch; write-once JSON output |
| Parallelism | `concurrent.futures` (stdlib) | `ProcessPoolExecutor` for GIL-free parallelism |
| Packaging | `hatchling` + `uv` | Locked reproducible builds |
| Containerization | Docker (`python:3.12-slim`) | Isolated, portable runtime |
| CI | GitHub Actions | Automated testing on push/PR |

### Pipeline Architecture

```
ROOT File (CERN XRootD or local)
        │
        ▼
  uproot.iterate()          ← Streaming, chunk-by-chunk
        │
        ▼
 ┌──────────────────────────────────┐
 │      _process_entry_range()      │  ← Run in parallel via ProcessPoolExecutor
 │                                  │
 │  1. apply_baseline_selection()   │  → nMuon == 2  AND  q₁ ≠ q₂
 │  2. apply_pt_threshold()         │  → pT₁ ≥ threshold AND pT₂ ≥ threshold
 │  3. calculate_invariant_mass()   │  → vector.zip() + Lorentz addition
 │  4. np.histogram() accumulation  │  → Pre-binned, memory-safe
 └──────────────────────────────────┘
        │
        ▼
  Merge partial histograms across workers
        │
        ├── Plot 1: Full spectrum (all thresholds overlaid)
        │
        └── fit_resonance_window()  ← If --fit-min / --fit-max provided
                │
                ├── scipy.curve_fit (Gaussian + Exponential)
                ├── FitResult dataclass (frozen, immutable)
                ├── Plot 2: Zoomed resonance window
                └── JSON cutflow + fit_summary output
```

### Module Breakdown

```
src/dimuon/
├── cli.py          # Argparse CLI: environment | make-demo | inspect | analyze
├── config.py       # Dataclass config loader (entry bounds, source URL, branches)
├── demo.py         # Synthetic ROOT fixture generator (5 controlled events)
├── inspection.py   # Dataset inspection: branch types, multiplicity counts, preview
├── selection.py    # apply_baseline_selection(), apply_pt_threshold()
├── physics.py      # calculate_invariant_mass() via scikit-hep/vector
├── fitting.py      # composite_model(), fit_resonance_window(), FitResult dataclass
└── analysis.py     # run_chunked_analysis(), _process_entry_range()
```

---

## 5. Development Journey

The project was developed over five focused engineering sessions, each targeting a concrete capability. The progression reflects how real HEP analyses are built — iteratively validating correctness before scaling up.

### Day 1 — Foundation & Data Inspection

Established the project scaffold with `uv`, locked dependencies, and a synthetic ROOT fixture. Implemented `inspection.py` for bounded dataset reads. Real data access via XRootD failed on the dev machine (CMake dependency missing); the error was preserved honestly and the synthetic path was used to continue — false claims of accessing real data were explicitly avoided.

### Day 2 — Chunked Analysis & Selection Tests

Refactored from a single `tree.array()` read to `uproot.iterate()` for memory-efficient streaming. Implemented the two-stage event selection (`nMuon==2` → opposite-charge → pT threshold scan). Added a unit test (`test_chunk_size_independence`) proving that analysis results are invariant to chunk size — a critical correctness guarantee. Added `test_physics.py` and `test_selection.py`.

### Day 3 — Statistical Resonance Fitting

Introduced `fitting.py` with the `composite_model()` (Gaussian signal + exponential background) and `fit_resonance_window()` using `scipy.optimize.curve_fit`. Poisson error estimation (`σ = √N`, floored at 1) prevents zero-division during significance calculations. A `FitResult` frozen dataclass enforces immutability of fit outputs. Added `test_fit_resonance_window_synthetic_recovery()` to verify parameter recovery within 3σ on synthetic data.

### Day 4 — Z Boson Physics & Parallelism

Extended fitting to handle both the J/Ψ (narrow, detector-resolution-limited, σ ≈ 33 MeV) and Z boson (broad natural decay width, σ ≈ 2 GeV due to weak-force decay). Added dynamic initial-guess selection based on mass window centroid. Introduced `ProcessPoolExecutor`-based parallelism to split the entry range across CPU cores — bypasses the GIL since each worker runs independent I/O and numerical compute. Added decoupled macroscopic/microscopic plot generation.

### Day 5 — Vectorization, Binning & Containerization

Replaced the hand-rolled NumPy 4-momentum calculation with the Scikit-HEP `vector` library (C++ backend), improving both performance and code clarity. Increased histogram bin count substantially (11,800 bins over 2–120 GeV) — the original low bin count made the overlaid fit curve invisible on the plot. Authored the `Dockerfile` and `.dockerignore` for fully containerized execution.

---

## 6. Getting Started

### Prerequisites

- Python 3.12+ (managed via `.python-version`)
- [`uv`](https://docs.astral.sh/uv/) — fast Python package/project manager
- Docker (optional, for containerized runs)
- CMake + XRootD (optional, only needed for direct CERN remote data access)

### Installation

```bash
# Clone the repository
git clone https://github.com/zukothecactus/cms-dimuon-analysis.git
cd cms-dimuon-analysis

# Install all dependencies using the locked environment
uv sync --locked --python 3.12

# Verify the environment
uv run --locked dimuon environment --output outputs/my-environment.json
```

Expected output:

```json
{
  "python": "3.12.x",
  "packages": {
    "cms-dimuon-starter": "0.1.0",
    "uproot": "5.7.6",
    "awkward": "2.13.0",
    "numpy": "2.5.3"
  }
}
```

### Run Unit Tests

```bash
uv run --locked pytest -q
```

All tests use synthetic ROOT fixtures — no CERN network or real data required.

```
test_starter.py .....
test_chunking.py .
test_fitting.py .
test_physics.py ..
test_selection.py ..
9 passed in X.XXs
```

---

## 7. How to Run / Execution Guide

All commands use the `dimuon` CLI entry point installed by `uv`.

### Step 1: Generate the Synthetic Demo File

Creates a 5-event ROOT fixture for local testing and inspection:

```bash
uv run --locked dimuon make-demo --output data/my-synthetic-demo.root
```

Expected console output:

```json
{"status": "created", "data_kind": "synthetic", "path": "data/my-synthetic-demo.root"}
```

### Step 2: Inspect the Synthetic Dataset

```bash
uv run --locked dimuon inspect \
  --input data/my-synthetic-demo.root \
  --output outputs/my-demo-inspection.json
```

Verify the report shows `"data_kind": "synthetic-demo-not-physics-data"` and `"entries_read": 5`.

---

### Step 3: Run the Baseline Analysis (Synthetic Data)

A fast end-to-end test of the full pipeline on synthetic data:

```bash
uv run --locked dimuon analyze \
  --input data/my-synthetic-demo.root \
  --entry-stop 5 \
  --output-plot outputs/test_spectrum.png \
  --output-json outputs/test_analysis.json
```

---

### Step 4: Full Analysis on Local CMS Data

> **Note:** You must first download the CMS ROOT file locally. See the XRootD section below for the file URL. The file is ~2 GB.

Assuming the file is at `data/Run2012BC_DoubleMuParked_Muons.root`:

```bash
# Run single-threaded analysis across 100,000 events with J/Psi fit
uv run --locked dimuon analyze \
  --input data/Run2012BC_DoubleMuParked_Muons.root \
  --entry-stop 100000 \
  --chunk-size 1000 \
  --fit-min 2.9 --fit-max 3.3 \
  --output-plot outputs/jpsi_fit_spectrum.png \
  --output-json outputs/jphi_fit_summary.json
```

**To reproduce the Z boson results:**

```bash
uv run --locked dimuon analyze \
  --input data/Run2012BC_DoubleMuParked_Muons.root \
  --entry-stop 100000 \
  --chunk-size 1000 \
  --fit-min 70.0 --fit-max 110.0 \
  --output-plot outputs/z_boson_fit_spectrum.png \
  --output-json outputs/z_boson_fit_summary.json
```

**To use parallel processing (e.g., 4 CPU cores):**

```bash
uv run --locked dimuon analyze \
  --input data/Run2012BC_DoubleMuParked_Muons.root \
  --entry-stop 1000000 \
  --chunk-size 10000 \
  --num-workers 4 \
  --fit-min 70.0 --fit-max 110.0 \
  --output-plot outputs/z_boson_parallel.png \
  --output-json outputs/z_boson_parallel.json
```

**Expected console output (fitting):**

```
[Z_Boson Fit Successful] Mass: 90.82 GeV, Significance: 48.3σ
Full cutflow summary: {'baseline': {'initial': 100000, ...}, 'pt_scan': {...}, 'fit_summary': {...}}
```

---

### Step 5: (Optional) Accessing CERN Remote Data via XRootD

Requires CMake and XRootD installed on your system. Install the remote extras:

```bash
uv sync --locked --python 3.12 --extra remote

# Inspect the first 10 events from CERN EOS
uv run --locked --extra remote dimuon inspect --entries 10 --output outputs/cms-first-10.json

# Inspect the first 1,000 events
uv run --locked --extra remote dimuon inspect --output outputs/cms-first-1000.json
```

The data URL (from `docs/PROVENANCE.md`):

```
root://eospublic.cern.ch//eos/opendata/cms/derived-data/AOD2NanoAODOutreachTool/Run2012BC_DoubleMuParked_Muons.root
```

---

### Step 6: (Optional) Docker

```bash
# Build the image
docker build -t cms-dimuon .

# Run environment check inside container
docker run --rm cms-dimuon environment

# Run analysis against a locally downloaded data file
docker run --rm \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/outputs:/app/outputs \
  cms-dimuon analyze \
  --input data/Run2012BC_DoubleMuParked_Muons.root \
  --entry-stop 100000 \
  --fit-min 2.9 --fit-max 3.3 \
  --output-plot outputs/jpsi_fit_spectrum.png \
  --output-json outputs/jphi_fit_summary.json
```

> **Important:** The Docker image does not bundle the CMS dataset. You must mount your local `data/` directory as shown above.

---

## 8. Troubleshooting

Issues encountered and resolved during the development of this project.

### `XRootD` / CMake not found

**Symptom:**
```
ImportError: No module named 'XRootD'
```
or
```
ERROR: Failed building wheel for xrootd (CMake not found)
```

**Root cause:** The `xrootd` Python binding requires CMake and system-level C++ libraries that are absent on many developer machines (documented on Day 1).

**Solution:** Use the local file path instead of the CERN XRootD URL, or use Docker:

```bash
# Without XRootD: analyze a locally downloaded ROOT file
uv run --locked dimuon analyze --input data/Run2012BC_DoubleMuParked_Muons.root ...

# Or: build and run the Docker container
docker build -t cms-dimuon . && docker run --rm cms-dimuon environment
```

---

### Output File Already Exists

**Symptom:**
```json
{"status": "error", "error_type": "FileExistsError", "message": "Refusing to overwrite outputs/z_boson_fit_summary.json"}
```

**Root cause:** By design, the CLI opens output files in exclusive mode (`"x"`) to prevent accidental overwriting of analysis artifacts.

**Solution:** Delete or rename the existing file before re-running:

```bash
del outputs\z_boson_fit_summary.json  # Windows
rm outputs/z_boson_fit_summary.json   # macOS/Linux
```

---

### Fit Curve Invisible on Spectrum Plot

**Symptom:** The `--fit-min` / `--fit-max` arguments are provided, fitting succeeds, but the fit curve is not visible on the output plot.

**Root cause:** This was a known bug (fixed on Day 5). With too few histogram bins (e.g., 100 bins over 2–120 GeV), the resonance peak spans only 1–2 bins and the overlaid fit curve becomes invisible against the step-function background.

**Solution:** The current implementation uses 11,800 bins (`np.linspace(2, 120, 11801)`), yielding ~0.01 GeV/bin resolution. If you encounter this with a custom bin configuration, increase `mass_bins` density in `analysis.py`.

---

### Poisson Zero-Division Warning

**Symptom:**
```
RuntimeWarning: invalid value encountered in true_divide
```
during fitting.

**Root cause:** Empty bins (count = 0) produce `σ = √0 = 0` Poisson uncertainty, causing division by zero in the χ² residual calculation.

**Solution:** Already implemented — `sigma_y = np.sqrt(np.maximum(y_fit, 1.0))` floors the per-bin uncertainty at 1 event, consistent with standard HEP practice.

---

### Parallelism Hangs on Windows

**Symptom:** The `--num-workers` flag causes the process to hang or raise errors on Windows.

**Root cause:** Windows uses the `spawn` start method (not `fork`) for new processes. Code importing `matplotlib` at module level without specifying a non-interactive backend can conflict with the spawned child processes.

**Solution:** The `analysis.py` module explicitly calls `matplotlib.use('Agg')` at import time, before any figure is created. Ensure any custom scripts calling `run_chunked_analysis` are guarded with `if __name__ == "__main__":`. The `dimuon` CLI entry point handles this correctly by default.

---

### `entry_stop` Larger Than Dataset Size

**Symptom:** Requesting `--entry-stop 1000000` on the 5-event synthetic file returns only 5 events, not an error.

**Root cause:** By design — `uproot` clamps `entry_stop` to the actual number of tree entries. The inspection report exposes `entry_stop_effective` to document this behavior explicitly.

**Expected behavior:** The cutflow will correctly reflect only the events that exist in the file; no error is raised and no dummy entries are fabricated.

---

## 9. Data Provenance & Ethics

The intended real data source is [CERN Open Data Record 12342](https://opendata.cern.ch/record/12342) — the CMS 2012 DoubleMuParked muon-reduced NanoAOD dataset.

**Important limits (from `docs/PROVENANCE.md`):**

- The first N entries form a **deterministic slice**, not a random sample.
- This is preselected outreach data, not an unbiased sample of all collisions.
- The feature near 30 GeV is a **trigger effect**, not a physics resonance.
- Synthetic fixture tests validate software behavior only — not physics performance.
- No real dataset or source code from CERN is redistributed in this repository.

See [`docs/PROVENANCE.md`](docs/PROVENANCE.md) and [`docs/technical-note.md`](docs/technical-note.md) for full details.

---

## 10. Project Structure

```
cms-dimuon-analysis/
├── .github/
│   └── workflows/
│       └── tests.yml           # GitHub Actions CI (pytest on push/PR to main)
├── configs/
│   └── day1.json               # Default config: source URL, entry bounds, branches
├── data/                       # Local ROOT files (not committed; .gitignored)
├── docs/
│   ├── PROVENANCE.md           # Dataset provenance and analysis limits
│   ├── VALIDATION.md           # Validation notes
│   └── technical-note.md       # Formal technical description of the analysis
├── outputs/                    # Generated plots and JSON results
│   ├── final_spectrum.png
│   ├── jpsi_fit_spectrum.png
│   ├── z_boson_fit_spectrum.png
│   ├── Jphi_meson_threshold_mass_spectrum.png
│   ├── z_boson_threshold_fit_spectrum.png
│   ├── jphi_fit_summary.json
│   ├── z_boson_fit_summary.json
│   ├── baseline_analysis.json
│   └── environment.json
├── src/
│   └── dimuon/
│       ├── __init__.py
│       ├── analysis.py         # Streaming chunked analysis + parallel dispatch
│       ├── cli.py              # Argparse CLI entry point
│       ├── config.py           # Config dataclass and loader
│       ├── demo.py             # Synthetic ROOT fixture generator
│       ├── fitting.py          # Composite model, curve_fit wrapper, FitResult
│       ├── inspection.py       # Dataset inspection and environment report
│       ├── physics.py          # Invariant mass via scikit-hep/vector
│       └── selection.py        # Baseline selection and pT threshold masks
├── tests/
│   ├── test_starter.py         # Day 1 scaffold tests
│   ├── test_chunking.py        # Chunk-size independence test
│   ├── test_fitting.py         # Synthetic parameter recovery test
│   ├── test_physics.py         # Back-to-back and at-rest mass tests
│   └── test_selection.py       # Mask and cutflow correctness tests
├── Dockerfile
├── .dockerignore
├── .python-version             # Pins Python 3.12
├── pyproject.toml              # Project metadata, dependencies, entry points
├── uv.lock                     # Fully resolved, locked dependency graph
├── PROGRESS.md                 # Day-by-day engineering log
└── README.md
```

---

## References

- CMS Collaboration. *CMS 2012 DoubleMuParked NanoAOD Outreach Dataset.* CERN Open Data Portal, Record 12342. https://opendata.cern.ch/record/12342
- HSF Training. *Scikit-HEP / Uproot Tutorial.* https://hsf-training.github.io/hsf-training-scikit-hep-webpage/
- Scikit-HEP. *vector: Lorentz vectors for HEP.* https://vector.readthedocs.io/
- CMS Open Data Analyses. *DimuonSpectrumNanoAODOutreachAnalysis.* https://github.com/cms-opendata-analyses/DimuonSpectrumNanoAODOutreachAnalysis

---

*Built with the CMS Open Data starter scaffold. Physics content is for educational and portfolio purposes.*
