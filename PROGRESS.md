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


~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
DAY 1 

'''Baseline selection-----------------------------------------------------------------------

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
'''Physics------------------------------------------------------------------------------

physics.py
    - the formula for calculating the invariant mass of two muons
    - calculate_invariant_mass(muon1, muon2)
        - method that calculates and returns the invariant mass
        - it takes 2 muons, that passed the selection proccess, and uses their Azumuthal angle, pseudorapidity, transversal momentum and mass, to calculate the invariant mass of the parent system

'''
''' Analysis and plotting-------------------------------------------------------------

analysis.py
    run_baseline_analysis(file_path)
        - first we import the data from one of the root files
        - we get to the root file using the given path
        - we access the root "Events" tree, and separate the data into branches
        - after the application of both masks on the list of events, we drop the invalid ones, and prepare the left-over muons for the invariant mass calculations
        - at the end we generate the histogram and plot the data
        - the created plot is then exported to "outputs/baseline_mass_spectrum.png'
        - plt.stairs() was used to layer the varying Pt thresholds on top of each other, so we can visually assess how aggressive momoentum cuts eliminate low-mass background events
'''

~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
DAY 2:

Chunked selection and testing-----------------------------------------------------------------

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


~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Day 3
Resonance Peak Fitting ------------------------------------------------------------------------

src/dimuon/fitting.py
    class FitResult
        - immutable class (frozen = True) that is used for storing physical parameters, statistical uncertainties, goodness of fit metrics
        - physical parameters
            - signal_yield     - total number of signals
            - fitted_mass      - invariant mass at the peak (centered at a whole value ex. at bin 3)
            - resolution_sigma - Gaussian detector resolution parameter
            - background_yield - total estimated number of background signals (noise) within a mass window
        - every physical parameter has a property for it and its error
        - chi2_ndof        - Reduced chi-squared metric (per degree of freedom)
        - significance     - Signal significance ration (how significante is the peak / how far above the Poisson distribution)
    
    composite_model()
        - Method calculates the expected event counts per bin (interval)
        - Method that takes in parameter needed for both the signal and the background distribution
        - Parameters
            - S         - Signal yield normalization factor (number of events under the peak)
            - m0        - Central resonance mass peak
            - sigma     - Gaussian resolution width parameter (standard deviation of mass resolution)
            - B         - Background yield normalization factor (number of background signals (noise) within a mass window)
            - lambda_bg - Exponential background decay constant rate
            - m_min     - lower threshold of the active mass window
            - bin_width - Bin width used to convert continued densities into discrete bin count estimates (delta m)
        - Returns an array of expecten bin count yields corresponding to mass array m
            - the sum of signal and background distributions, multiplied by the bin_width
            - when you multiply the continuous composite (created by adding the 2 distributions) by bin_width, you get the expected event counts per bin

    fit_resonance_window()
        - Method that takes in the bin elements (centers, yields of each bin, and the mass window), initial parameter guesses and the name of the resonance being fitted
        - Based on the mass window, we create a mask so that only those events that fall into said bins, are taken into consideration
        - That mask is then used to obtain the array of bin_centers (masses) and the array of yields (event counts inside the bins)
        - bin_width is, at least one, but can be more, depending on the array of centers (masses)
            - aiming at uniform bin spacing
        - sigma_y - Poisson Error Estimation (Statistical uncertainty, per bin)
        - curve_fit is a method that returns the optimal parameters and covariace matrix
            - covariace matrix
                - diagonal elements store the variance of each individual variable (sigma_i**2)
                - non diagonal elements store the covariance between pairs of variables (if x increases, how is y effected aka. does increasing the S yield, cause the B yield to decrease)
        - perr is designed to take the errors for each variable (parameter) on the matrix diagonal 
        - chi**2 
            - It quantifies the difference between your observed (fitted) and predicted model, while taking into consideration the uncertainty of those measurements
            - its squared for 2 reasons:
                1. Positive and negative deviations dont cancel each other out
                2. Extreme outliers are heavily penalized
            - if its 0 then you have a perfect fit, where every single data point sits on the line
            - if its small, then the matching is well done
            - if its very large, our model fails to describe the underlying data
        - n Degrees of Freedom (ndof)
            - Number of points that dont fit onto the line, for which it can be checked if the fall onto the line
            - Fitted parameters are excluded
            - Number of histogram bins minus 5 fitted parameters(S, m0, sigma, B, lambda_bg)
        - Reduced Chi**2
            - Raw Chi**2 grows automatically, every time you add a data point, so to counter-balance that, it gets divided by ndof
            ~= 1 - good fit
            >> 1 - poor fit (over constrained)
            << 1 - over fit (overestimated errors)
        - We calculate the significance of the resonance mass peak, and with that, we have all the parameters contained inside of fitted data
        - fit_curve is a 1D NumPy array containing the predicted bin yield counts calculated by our fitted model across the mass window.
        - Our data and the fit_curve is evaluated at the sime exact bin centar points, sot the plotting becomes super straight forward (model is plotted directly on top of our histagram bins)
        
src/dimuon/cli.py
    - Analyze command has been expanded (it can now take two more arguments: fit_min (lower mass boundary) and fit_max (upper mass boundary))

src/dimuon/analysis.py
    - Expanded chunked analysis with fitting
    - Plotting the bins and fit curve accordingly

tests/test_fitting.py
    test_fit_resonance_window_synthetic_recovery()
        -  Generates synthetic signal and background data, fits it, and checks if the fitted parameters are close to the true values.
        

~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Day 4
Resonance Peak Fitting for Z bosons-----------------------------------------------------

src/dimuon/analysis.py
    - The parameters are passed for fitting, depending on the type of event
    - The type is determined by the mass window (fit_window)
    - Z bosons are much heavier than J/Phi mesons
    - Resonance width is also different
        - J/Phi s width is almost solely reliant on the detectors resolution (how accurate it is)
        - Z bozon decays as a result of a weak force and it has a large personal (natural) width of ~2,5GeV, hence the increase of the "sigma" parameter inside od our gaussian fit (signal distribution)
        - Fbkg is also a lot smaller than at the energy value of 3GeV
    
Process-Based Parallelism--------------------------------------------------------------

analysis.py

_process_entry_range()
    - Python's GLI prevents multiple threads from executiong CPU-bound math operations simultaneously, so to achieve parallelism, we used ProcessPoolExecutor
    - The main script calculates how many total events need to be processed and divideds them among workers
    - Each worker does the selection logic and returns its own cutflow dictionaried and mass histograms.
    - The results are summed up sequentially into a big dictionary by the main process
    - This way we avoid race conditions entirely
    - Since the boundaries needed to be set for uproot.iterate, to stop it from consumming the entirety of the ROOT file, we used the tree itself, and then iterated on it

run_chunked_analysis()
    - This is where we split the work (if the number of workers is not specified, the default is a sequentially operation)
    - Each worker calls the _process_entry_range() method on their slice and returns the results


Decoupled Visualization-----------------------------------------------------------------------

analysis.py()
    - Up to this point, only the general graph was plotted, and that is fine for the general gistribution
    - Focus also needed to be put on the resonance peaks themselves, for the analysis to be more thorough (easier to spot an error)
    - Macroscopic View
        - The main plot remains untouched, where you have the full invariant mass spectrum rendered
    - Microscopic Fit
        - The focus is exclusively on the resonance window
        - The plot overlays the theoretical composite model (signal + background) onto discrete data pints
    - Poisson Statistics
        - HEP error bars, capping the minimum uncertainty at 1. to prevent zero-division errors during siginificance calculations


    