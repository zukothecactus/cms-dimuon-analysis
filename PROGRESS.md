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


DAY 1:
'''Baseline selection

selection.py 
    - masks and cutflow are created
    - first filter is the 2 muon filter
    - second filter is the opposite charge filter
    - cutflow is the report consisting of the number of muons that passed each filter
    - apply_baseline_selection
        - the method that generates the report and returns the mask
        - takes 2 arguments
        - 1st argument:  all the events that have to be filtered
        - 2nd argument: all the charges that have to be filtered
        - the returning values are both masks and the cutflow report

'''
'''Physics

physics.py
    - the formula for calculating the invariant mass of two muons
    - calculate_invariant_mass(muon1, muon2)
        - method that calculates and returns the invariant mass
        - it takes 2 muons, that passed the selection proccess, and uses their Azumuthal angle, pseudorapidity, transversal momentum and mass, to calculate the invariant mass of the parent system

'''
''' Analysis and plotting

analysis.py
    run_baseline_analysis(file_path)
        - first we import the data from one of the root files
        - we get to the root file using the given path
        - we access the root "Events" tree, and separate the data into branches
        - after the application of both masks on the list of events, we drop the invalid ones, and prepare the left-over muons for the invariant mass calculations
        - at the end we generate the histogram and plot the data
        - the created plot is then exported to "outputs/baseline_mass_spectrum.png'
'''

DAY 2:
Chunked selection and testing

selection.py
    - threshold filter, since muons with lower GeV readings are considered noise
    apply_pt_threshold(pt1, pt2, threshold)
        -checks if both muons have a transverse momemtum above or at the threshold
        - creates a mask for the pairs
        - returns a mask and a count of muons

analysis.py
    - modified to work as a chunked analysis, instead of a baseline one
    - plotting is hidden in the background, since showing chunked plotting would use a lot or resources and time
    - uproot.iterate() instead of tree.array(), because of performance
    
    run_baseline_analysis(file_path) ---> run_chunked_analysis(...)
        - args:
            file_path: str| Path,
            entry_start: int = 0,
            entry_stop: int = 10000,
            chunk_size : int = 1000,
            thresholds: list[float] | None = None,
            output_plot_path: str | Path = "outputs/threshold_mass_spectrum.png"
        
        - instead of storing giant invariant mass arrays, that we plot at the end, we use predefined fixed mass bins and fill them as we go, to save memory, so that our computer doesnt crash because of the memory lack
        - to create these bins we use np.linspace, which creates a ranged sequence of evenly spaced numbers 
        - data count is accummulated in dictionaries, instead of being alll stored in memory
            - we have dictionaries for those events that passed the baseline_selection (2 muons and opposite charge), that passed the pt_threshold filter and a dictonary for the histograms for each of the threshold cases
        - as we do through the data that uproot.iterate obrains, we add the results to the dictionaries
            - as soon as we apply the baseline_selection, we append the results to the total_cutflow distionary
            - as soon as we apply the pt_threshold, we append the result to the scan_cutflow (*could have been named better ngl)
        - for each of the thresholds inside the list, we calculate the invariant mass for those that passed the pt_threshold filter, and count the invariant masses. After that we place them in the histogram distionary
        - instead of plotting a single plot, we create one for each of the thresholds, and we do it headless, so that it doesnt waste resouces
    
cli.py
    - updated our parser so that is can match the changes inside of analysis.py, for the analyze command

tests/test_chunking.py
    - testing if the number of events, which are processed, is independent of the chunk size
    test_chunk_size_independance(demo_data, tmp_path)

tests/test_physics.py
    - basic tests for the physics calculations
    test_calculate_invariant_mass_back_to_back()
    test_calculate_invariant_mass_at_rest()

tests/test_selection.py
    - basic tests for the selection process
    test_apply_baseline_selection_synthetic()
    test_apply_pt_threshold_synthetic()