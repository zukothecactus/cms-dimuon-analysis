# Starter Validation Record
## Checks

- Offline test suite: 25 tests passing after the final test additions.
- Ruff lint: passing.
- Locked installation: exercised with Python 3.12.
- Synthetic CLI workflow: created five artificial events; bounded inspection read all five and retained the synthetic label.
- (CMake needed - NOT YET DONE) Real remote read: ten entries successfully inspected from the configured public source.
- (CMake needed - NOT YET DONE) Real remote read: 1,000 entries successfully inspected with the six configured branches.
- (CMake needed - NOT YET DONE) Transport setup: the remote optional dependency group includes both XRootD and the fsspec-XRootD adapter;
- GitHub Actions: workflow supplied; no hosted GitHub run has been executed.
- Platform coverage: Linux validated; macOS and Windows execution not tested here.

The remote file is the one documented by [CERN Open Data record 12342](https://opendata.cern.ch/record/12342) and the [HSF Scikit-HEP tutorial](https://hsf-training.github.io/hsf-training-scikit-hep-webpage/aio/index.html). The following are observations from the actual bounded read, not published selection efficiencies or results copied from the source page.