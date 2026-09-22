# Dataset and scaffold provenance

## Intended real input

The analysis source is [CERN Open Data record 12342](https://opendata.cern.ch/record/12342), which documents an opposite-charge dimuon spectrum using muon-reduced CMS 2012 DoubleMuParked data. The source's reference analysis is [DimuonSpectrumNanoAODOutreachAnalysis](https://github.com/cms-opendata-analyses/DimuonSpectrumNanoAODOutreachAnalysis); the [HSF tutorial](https://hsf-training.github.io/hsf-training-scikit-hep-webpage/aio/index.html) documents the Uproot/Awkward reading path used for this learning project.

The documented data URL is:

```text
root://eospublic.cern.ch//eos/opendata/cms/derived-data/AOD2NanoAODOutreachTool/Run2012BC_DoubleMuParked_Muons.root
```

The documented tree is `Events`, and the inspection branches are `nMuon`, `Muon_pt`, `Muon_eta`, `Muon_phi`, `Muon_mass`, and `Muon_charge` ([HSF tutorial](https://hsf-training.github.io/hsf-training-scikit-hep-webpage/aio/index.html)). Units and physical meaning will explained later, not inferred merely from an array's storage type.

## Important limits

- The first N entries form a deterministic slice, not a random sample.
- This is preselected outreach data, not an unbiased sample of all collisions.
- The reference warns that the feature near 30 GeV is a trigger effect, not a resonance ([CERN record](https://opendata.cern.ch/record/12342)).
- Day 1 inspection counts are not physics selections, measured cross-sections, or discoveries.
- A local file with the same schema is labelled `unverified-input` unless it contains the synthetic marker. A matching schema alone is not proof of real-data provenance.
- No real dataset or source-code archive from CERN is redistributed here.

## Synthetic fixture

`dimuon make-demo` creates five artificial events with 0, 1, 2, 2, and 3 muons. The fixture includes an opposite-charge pair and a same-charge pair to support later exercises; its kinematics and arbitrary mass of 0.1 are not claimed to model real detector data or quote a precision muon mass.

Its ROOT metadata and inspection output explicitly mark it as synthetic. Synthetic tests only validate software behaviour, not physics performance ofc.
