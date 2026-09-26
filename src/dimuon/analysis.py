from pathlib import Path
import numpy as np
import awkward as ak
import uproot
import matplotlib
matplotlib.use('Agg')  # Use a non-interactive backend for plotting
import matplotlib.pyplot as plt
from dimuon.selection import apply_baseline_selection, apply_pt_threshold
from dimuon.physics import calculate_invariant_mass

def run_chunked_analysis(
    file_path: str| Path,
    entry_start: int = 0,
    entry_stop: int = 10000,
    chunk_size : int = 1000,
    thresholds: list[float] | None = None,
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
    
    mass_bins = np.linspace(2, 120, 51) #generates a sequence of 51 numbers from 2 to 120, which will be used as the bin edges for the histogram
    
    #global accumulators, instead of storing all the data in memory, we will accumulate the counts in these dictionaries
    total_cutflow = {"initial": 0, "exactly_two_muons": 0, "opposite_charge": 0}
    scan_cutflow = {f"pt_min_{t}_GeV": 0 for t in thresholds} #initialize the scan cutflow dictionary with keys for each threshold and values set to 0
    histograms = {t: np.zeros(len(mass_bins)-1) for t in thresholds} #initialize histograms for each threshold with zeros
    branches = ["nMuon", "Muon_pt", "Muon_eta", "Muon_phi", "Muon_mass", "Muon_charge"]
    
    for data in uproot.iterate(
        f"{file_path}:Events",
        branches = branches,
        entry_start = entry_start,
        entry_stop = entry_stop,
        step_size = chunk_size,
        library = "ak",
    ):
        #import the masks
        two_muons_mask, opposite_charge_mask, chunk_cutflow = apply_baseline_selection(data["nMuon"], data["Muon_charge"])
        
        total_cutflow["initial"] += chunk_cutflow["initial"]
        total_cutflow["exactly_two_muons"] += chunk_cutflow["exactly_two_muons"]
        total_cutflow["opposite_charge"] += chunk_cutflow["opposite_charge"]
        
        
        #apply the masks to the data
        #two muons mask first, to drop the invalid events
        pt_two_muons = data["Muon_pt"][two_muons_mask]
        eta_two_muons = data["Muon_eta"][two_muons_mask]
        phi_two_muons = data["Muon_phi"][two_muons_mask]
        mass_two_muons = data["Muon_mass"][two_muons_mask]
        
        #opposite_charge mask next, to drop the invalid events
        pt_final = pt_two_muons[opposite_charge_mask]
        eta_final = eta_two_muons[opposite_charge_mask]
        phi_final = phi_two_muons[opposite_charge_mask]
        mass_final = mass_two_muons[opposite_charge_mask]

        for threshold in thresholds:
            pt_mask, passing_count = apply_pt_threshold(pt_final[:, 0], pt_final[:, 1], threshold)
            
            #+= instead of =, because we want to accumulate the counts across all chunks
            scan_cutflow[f"pt_min_{threshold}_GeV"] += passing_count
            
            pt1_threshold_cut = pt_final[:, 0][pt_mask]
            pt2_threshold_cut = pt_final[:, 1][pt_mask]
            eta1_threshold_cut = eta_final[:, 0][pt_mask]
            eta2_threshold_cut = eta_final[:, 1][pt_mask]
            phi1_threshold_cut = phi_final[:, 0][pt_mask]
            phi2_threshold_cut = phi_final[:, 1][pt_mask]
            m1_threshold_cut = mass_final[:, 0][pt_mask]
            m2_threshold_cut = mass_final[:, 1][pt_mask]
        
            #preparing the muons (that passed the pt threshold) for the mass calculation
            muon1 = [pt1_threshold_cut, eta1_threshold_cut, phi1_threshold_cut, m1_threshold_cut]
            muon2 = [pt2_threshold_cut, eta2_threshold_cut, phi2_threshold_cut, m2_threshold_cut]
            
            invariant_mass = calculate_invariant_mass(muon1, muon2)

            counts, _ = np.histogram(ak.to_numpy(invariant_mass), bins=mass_bins) 
            histograms[threshold] += counts  # Accumulate counts for this threshold
            
    # Headless plotting - no display 
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
    plt.xlabel("Invariant Mass (GeV)")
    plt.ylabel("No. Events")
    plt.title("Dimuon Invariant Mass Spectrum (Selection Sensitivity)")
    plt.legend()
    plt.grid(axis = 'y', alpha=0.75)
    
    plot_path = Path(output_plot_path) #cast to Path object for consistency
    plot_path.parent.mkdir(parents=True, exist_ok=True)  # Ensuring the output directory exists
    plt.savefig(plot_path)
    plt.close()

    final_cutflow = {"baseline":total_cutflow, "pt_scan": scan_cutflow}
    print("Full cutflow summary:", final_cutflow)

    return final_cutflow

if __name__ == "__main__":
    # Test the pipeline locally using the synthetic file first
    run_chunked_analysis("data/synthetic-demo.root")
    