# CMS Dimuon Analysis: Reproducibility and Selection Sensitivity

An end-to-end physics analysis pipeline analyzing muon-reduced CMS 2012 DoubleMuParked data. This package reconstructs the invariant mass of dimuon systems, applies kinematic baseline selections, and performs statistical curve fitting on the J/Psi and Z boson resonance peaks.

## Architecture & Tools
- **Kinematics:** Scikit-HEP `vector` for optimized 4-momentum Lorentz calculations.
- **Data Streaming:** `uproot.iterate` combined with chunked parallel processing (`ProcessPoolExecutor`) for memory-safe scaling over large ROOT files.
- **Statistical Fitting:** `scipy.optimize` utilizing dynamically bounded composite models (Gaussian signal + exponential background) tailored to expected mass windows.
- **Automation:** Fully containerized environment using `uv` for deterministic dependency resolution, backed by GitHub Actions CI for continuous testing against synthetic fixtures.

## Quick start

You will need the `uv` package manager. If `uv` is not installed, consult the official [uv installation guide](https://docs.astral.sh/uv/getting-started/installation/).

```bash
uv sync --locked --python 3.12
uv run --locked pytest -q
uv run --locked dimuon environment --output outputs/environment.json
uv run --locked dimuon make-demo --output data/synthetic-demo.root
uv run --locked dimuon inspect --input data/synthetic-demo.root --output outputs/demo-inspection.json