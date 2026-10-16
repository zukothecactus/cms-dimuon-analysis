# CMS Dimuon Analysis: Reproducibility and Selection Sensitivity

## Abstract

This project develops a fully reproducible analysis of the CMS 2012
DoubleMuParked dataset (CERN Open Data Record 12342) to quantify the
sensitivity of dimuon resonance reconstruction to event-selection thresholds.
The pipeline uses `uproot`, Scikit-HEP tools, and Docker to process the ROOT
data in an isolated and repeatable environment. Invariant-mass spectra are
constructed after sequential muon selections, and the J/Psi and Z boson
resonance peaks are extracted with bounded statistical models. The resulting
cut flow provides a quantitative description of the reduction from the
61,540,413 processed events to the selected samples used for resonance
measurement.

## 1. Introduction

The objective is to build a containerized physics pipeline that measures how
selection requirements affect the efficiency and statistical content of a
dimuon analysis. The study uses the CMS 2012 DoubleMuParked data sample from
CERN Open Data Record 12342. Starting from 61,540,413 events, the workflow
applies reproducible multiplicity, charge, and transverse-momentum
requirements before calculating dimuon invariant masses.

Reproducibility is treated as an analysis requirement rather than as a
post-processing convenience. The data transformation steps, software
dependencies, selection thresholds, fitting procedure, and generated
artifacts are specified in version-controlled project files. This design
allows the same analysis to be executed locally or in continuous integration
without changing the computational environment or relying on undocumented
interactive steps.

## 2. Software Architecture

The implementation is organized as a streaming analysis pipeline. ROOT
branches are read with `uproot.iterate`, which divides the input into bounded
chunks and avoids loading the full dataset into memory. Each chunk is
processed independently, and `ProcessPoolExecutor` provides multiprocessing
for the computationally independent event blocks. This combination supports
large-sample processing while keeping memory use bounded and making the
parallelization strategy explicit.

Muon four-vectors are represented with the Scikit-HEP `vector` library. The
library supplies the Lorentz-kinematic operations required to combine the two
selected muons and calculate their invariant mass. Statistical inference is
performed with the optimization routines in `scipy.optimize`. Docker isolates
the operating-system and Python dependency environment, so the execution
context is defined by the project configuration rather than by the host
machine.

## 3. Event Selection

The cut flow below records the number of events remaining after each
selection. The initial sample contains 61,540,413 processed events. At the
20 GeV threshold, 5,702,576 events remain, corresponding to a total
retention of 9.27%. Thus, the sequential selection removes 55,837,837 events
relative to the initial processed sample while retaining the events used for
the final high-threshold spectrum.

| Selection Step             | Events Remaining | Retention (%) |
| :------------------------: | :--------------: | :-----------: |
| Initial Processed Events   |    61,540,413    |    100.00%    |
| Exactly Two Muons          |    31,104,343    |     50.54%    |
| Opposite Charge (Baseline) |    24,067,843    |     39.11%    |
| pT >= 5 GeV                |    22,363,477    |     36.34%    |
| pT >= 10 GeV               |    15,147,769    |     24.61%    |
| pT >= 15 GeV               |     7,751,783    |     12.60%    |
| pT >= 20 GeV               |     5,702,576    |      9.27%    |

## 4. Kinematics & Statistical Fitting

For each event passing the selection, the two muon four-vectors are summed
and the dimuon invariant mass is calculated from the squared four-vector,
\[
m_{\mu\mu} = \sqrt{(p_{\mu^+} + p_{\mu^-})^2}.
\]
The resulting distribution contains the low-mass J/Psi resonance and the
high-mass Z boson resonance, together with a non-resonant continuum.

Each resonance is fitted with a dynamically bounded composite model consisting
of a Gaussian signal and an exponential background. The fitting procedure uses
`scipy.optimize` with parameter bounds defined for the relevant mass window.
The script automatically adapts the initial parameter guesses for the J/Psi
and Z boson windows, reducing dependence on manually tuned starting values
while keeping the optimization constrained to physically relevant regions.

The final fitted parameters are:

- J/Psi fitted mass: `3.092534538661731`
- J/Psi resolution sigma: `0.033376516500752615`
- J/Psi significance: `45.69649747990749`
- J/Psi chi2: `1.9176536418864862`
- Z boson fitted mass: `90.82041418973792`
- Z boson resolution sigma: `2.0286835151251075`
- Z boson significance: `48.33825065932062`
- Z boson chi2: `0.5924575649512132`

The final invariant-mass spectrum and fitted components are saved at
`../outputs/final_spectrum.png`.

The full invariant-mass spectrum and fitted components for the J/Phi meson are saved at
`../outputs/Jphi_meson_threshold_mass_spectrum.png`.

The resonance window (peak) for the J/Phi meson inside the full invariant mass spectrum is saved at 
`../outputs/Jphi_fit_spectrum.png`.

The full invariant-mass spectrum and fitted components for the Z boson are saved at
`../outputs/z_boson_threshold_fit_spectrum.png`.

The resonance window (peak) for the Z boson inside the full invariant mass spectrum is saved at 
`../outputs/z_boson_fit_spectrum.png`.


## 5. Reproducibility Integration

GitHub Actions continuous integration executes the test suite and verifies
the analysis workflow on every relevant repository change. Synthetic data
fixtures provide controlled ROOT inputs for testing selection, kinematic
calculation, and fitting behavior without requiring access to the CMS
remote-data service. These fixtures also make failure cases and expected
outputs available in a deterministic form.

The `uv` lockfile records the resolved Python dependency versions used by the
project. Docker supplies the corresponding isolated runtime environment, and
the CI workflow runs against the locked environment rather than resolving
dependencies during execution. Together, the lockfile, container definition,
synthetic fixtures, and version-controlled configuration guarantee
deterministic execution without relying on live remote data.
