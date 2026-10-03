from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path
import numpy as np
import awkward as ak
import uproot
import matplotlib
matplotlib.use('Agg')  # Use a non-interactive backend for plotting
import matplotlib.pyplot as plt
from dimuon.selection import apply_baseline_selection, apply_pt_threshold
from dimuon.physics import calculate_invariant_mass
from dimuon.fitting import fit_resonance_window

def _process_entry_range(
    file_path: str | Path,
    entry_start: int,
    entry_stop: int,
    chunk_size: int,
    thresholds: list[float],
    mass_bins: np.ndarray,
) -> tuple[dict, dict, dict]:
    """Process a bounded slice [entry_start, entry_stop) of a ROOT dataset."""
    branches = ["nMuon", "Muon_pt", "Muon_eta", "Muon_phi", "Muon_mass", "Muon_charge"]
    total_cutflow = {"initial": 0, "exactly_two_muons": 0, "opposite_charge": 0}
    scan_cutflow = {f"pt_min_{t}_GeV": 0 for t in thresholds}
    histograms = {t: np.zeros(len(mass_bins) - 1) for t in thresholds}

    #opening the ROOT file and call iterate directuly on the tree to enforce entry bounds (for multiprocessing)
    with uproot.open(file_path) as root_file:
        tree = root_file["Events"]
        
        for data in tree.iterate(
            branches,
            entry_start=entry_start,
            entry_stop=entry_stop,
            step_size=chunk_size,
            library="ak",
        ):
            two_muons_mask, opposite_charge_mask, chunk_cutflow = apply_baseline_selection(
                data["nMuon"], data["Muon_charge"]
            )

            total_cutflow["initial"] += chunk_cutflow["initial"]
            total_cutflow["exactly_two_muons"] += chunk_cutflow["exactly_two_muons"]
            total_cutflow["opposite_charge"] += chunk_cutflow["opposite_charge"]

            pt_two_muons = data["Muon_pt"][two_muons_mask]
            eta_two_muons = data["Muon_eta"][two_muons_mask]
            phi_two_muons = data["Muon_phi"][two_muons_mask]
            mass_two_muons = data["Muon_mass"][two_muons_mask]

            pt_final = pt_two_muons[opposite_charge_mask]
            eta_final = eta_two_muons[opposite_charge_mask]
            phi_final = phi_two_muons[opposite_charge_mask]
            mass_final = mass_two_muons[opposite_charge_mask]

            for threshold in thresholds:
                pt_mask, passing_count = apply_pt_threshold(pt_final[:, 0], pt_final[:, 1], threshold)
                scan_cutflow[f"pt_min_{threshold}_GeV"] += passing_count

                pt1_threshold_cut = pt_final[:, 0][pt_mask]
                pt2_threshold_cut = pt_final[:, 1][pt_mask]
                eta1_threshold_cut = eta_final[:, 0][pt_mask]
                eta2_threshold_cut = eta_final[:, 1][pt_mask]
                phi1_threshold_cut = phi_final[:, 0][pt_mask]
                phi2_threshold_cut = phi_final[:, 1][pt_mask]
                m1_threshold_cut = mass_final[:, 0][pt_mask]
                m2_threshold_cut = mass_final[:, 1][pt_mask]

                muon1 = [pt1_threshold_cut, eta1_threshold_cut, phi1_threshold_cut, m1_threshold_cut]
                muon2 = [pt2_threshold_cut, eta2_threshold_cut, phi2_threshold_cut, m2_threshold_cut]

                invariant_mass = calculate_invariant_mass(muon1, muon2)
                counts, _ = np.histogram(ak.to_numpy(invariant_mass), bins=mass_bins)
                histograms[threshold] += counts

    return total_cutflow, scan_cutflow, histograms

def run_chunked_analysis(
    file_path: str| Path,
    entry_start: int = 0,
    entry_stop: int = 10000,
    chunk_size : int = 1000,
    num_workers: int = 1,
    thresholds: list[float] | None = None,
    mass_bins: np.ndarray | None = None,
    fit_window: tuple[float, float] | None = None,
    output_plot_path: str | Path = "outputs/threshold_mass_spectrum.png"
    ):
    '''
    Read the dataset from given root file
    Apply baseline selection
    Calculate invariant mass for selected events
    Generate mass spectrum plots for different pt thresholds
    
    '''
    
    if thresholds is None:
        thresholds = [0,5,10,15,20] #GeV
        
    
    #instead of using arrays and storing giant invariant mass arrays, that we plot at the end
    # we pre-define fixed mass bins and fill them as we go, to save memory, using uproot.iterate()
    
    if mass_bins is None:
        mass_bins = np.linspace(2, 120, 11801) #generates a sequence of 11801 numbers from 2 to 120, which will be used as the bin edges for the histogram
    
    bin_centers = 0.5*(mass_bins[:-1] + mass_bins[1:]) #calculate the bin centers from the bin edges
    
    #global accumulators, instead of storing all the data in memory, we will accumulate the counts in these dictionaries
    total_cutflow = {"initial": 0, "exactly_two_muons": 0, "opposite_charge": 0}
    scan_cutflow = {f"pt_min_{t}_GeV": 0 for t in thresholds} #initialize the scan cutflow dictionary with keys for each threshold and values set to 0
    histograms = {t: np.zeros(len(mass_bins)-1) for t in thresholds} #initialize histograms for each threshold with zeros

    #divide the entry range among workers
    total_entries = entry_stop - entry_start
    if num_workers>1 and total_entries > chunk_size:
        step = max(chunk_size, (total_entries + num_workers - 1) // num_workers)
        sub_ranges = []
        current = entry_start
        while current<entry_stop:
            nxt = min(current + step, entry_stop)
            sub_ranges.append((current, nxt))
            current = nxt
        
        with ProcessPoolExecutor(max_workers = min(num_workers, len(sub_ranges))) as executor:
            futures = [executor.submit(
                _process_entry_range,
                file_path,
                s_start,
                s_stop,
                chunk_size,
                thresholds, 
                mass_bins
                ) for s_start, s_stop in sub_ranges
            ]
            for future in as_completed(futures):
                p_cutflow, p_scan, p_histograms = future.result()
                for key in total_cutflow:
                    total_cutflow[key] += p_cutflow[key]
                for key in scan_cutflow:
                    scan_cutflow[key] += p_scan[key]
                for key in histograms:
                    histograms[key] += p_histograms[key]
    else:
        p_cutflow, p_scan, p_histograms = _process_entry_range(
            file_path, entry_start, entry_stop, chunk_size, thresholds, mass_bins
        )
        total_cutflow, scan_cutflow, histograms = p_cutflow, p_scan, p_histograms
    
    
    # Headless plotting - no display 
    # Plot 1 (Unclipped)
    plt.figure(figsize=(10, 6))
    for threshold in thresholds:
        counts = histograms[threshold]
        passing = scan_cutflow[f"pt_min_{threshold}_GeV"]  
        plt.stairs(
            counts,
            mass_bins,
            alpha = 0.5,
            fill=True,
            label=f"pt >= {threshold} GeV ({passing} events)"
        )      
        
    fit_summary = {}
    if fit_window is not None:
        try:
            primary_counts = histograms[thresholds[0]]  # Use the histogram for the lowest threshold for fitting
            center_mass = (fit_window[0] + fit_window[1]) / 2.0
            
            #dynamic resonance recognition, based on mass
            if center_mass > 60.0:
                initial_guess = {
                    "S": 1000.0, 
                    "m0": 91.2, 
                    "sigma": 2.5, 
                    "B": 200.0, 
                    "lambda_bg": 0.05
                }
                res_name = "Z_Boson"
            else:
                # Parameters adjusted for J/Psi
                initial_guess = {
                    "S": 500.0, 
                    "m0": center_mass, 
                    "sigma": 0.1, 
                    "B": 1000.0, 
                    "lambda_bg": 0.2
                }
                res_name = "JPsi"

            fit_result, fit_curve = fit_resonance_window(bin_centers, primary_counts, fit_window, initial_guess, resonance_name=res_name)
            m_mask = (bin_centers >= fit_window[0]) & (bin_centers <= fit_window[1])
            plt.plot(
                bin_centers[m_mask],
                fit_curve,
                "r--",
                linewidth=2,
                label=f"Fit ({res_name}): m0={fit_result.fitted_mass:.2f} GeV, \u03C3={fit_result.resolution_sigma:.2f}",
            )
            
            fit_summary = fit_result.__dict__  # Convert dataclass to dictionary for easier JSON serialization
            print(f"[{res_name} Fit Successful] Mass: {fit_result.fitted_mass:.2f} GeV, Significance: {fit_result.significance:.1f}\u03C3")
            
            #Plot 2 (Dedicated Zoomed Fit Plot)
            fit_plot_path = Path(output_plot_path).parent / f"{res_name.lower()}_fit_spectrum.png"
            plt.figure(figsize=(8, 6))
            m_centers = bin_centers[m_mask]
            m_counts = primary_counts[m_mask]
            m_errors = np.sqrt(np.maximum(m_counts, 1.0))

            plt.errorbar(
                m_centers,
                m_counts,
                yerr=m_errors,
                fmt="o",
                color="black",
                ecolor="black",
                capsize=2,
                label="Data"
            )
            plt.plot(
                m_centers,
                fit_curve,
                "r-",
                linewidth=2,
                label=f"Fit ({res_name}): m0={fit_result.fitted_mass:.2f} GeV, \u03C3={fit_result.resolution_sigma:.2f}"
            )
            plt.xlim(fit_window[0], fit_window[1])
            plt.xlabel("Invariant Mass (GeV)")
            plt.ylabel("Events / Bin")
            plt.title(f"{res_name} Mass Peak Fit Window")
            plt.legend()
            plt.grid(axis="y", alpha=0.75)
            fit_plot_path.parent.mkdir(parents=True, exist_ok=True)
            plt.savefig(fit_plot_path)
            plt.close()
            
        except Exception as e:
            print(f"Fitting skipped due to error: {e}")
            
    plt.xlabel("Invariant Mass (GeV)")
    plt.ylabel("No. Events")
    plt.title("Dimuon Invariant Mass Spectrum (Selection Sensitivity)")
    plt.legend()
    plt.grid(axis = 'y', alpha=0.75)
    
    plot_path = Path(output_plot_path) #cast to Path object for consistency
    plot_path.parent.mkdir(parents=True, exist_ok=True)  # Ensuring the output directory exists
    plt.savefig(plot_path)
    plt.close()

    final_cutflow = {"baseline":total_cutflow, "pt_scan": scan_cutflow, "fit_summary": fit_summary}
    print("Full cutflow summary:", final_cutflow)

    return final_cutflow

if __name__ == "__main__":
    # Test the pipeline locally using the synthetic file first
    run_chunked_analysis("data/synthetic-demo.root")
    