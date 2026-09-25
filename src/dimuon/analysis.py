import awkward as ak
import uproot
import matplotlib.pyplot as plt
from dimuon.selection import apply_baseline_selection
from dimuon.physics import calculate_invariant_mass

def run_baseline_analysis(file_path):
    '''
    Read the dataset from given root file
    Apply baseline selection
    Calculate invariant mass for selected events
    Generate baseline spectrum plot
    
    '''
    tree = uproot.open(file_path)["Events"] # open the root file and access the "Events" tree
    branches = ["nMuon", "Muon_pt", "Muon_eta", "Muon_phi", "Muon_mass", "Muon_charge"]
    data = tree.arrays(branches) # read the specified branches into an awkward array
    
    #import the masks
    two_muons_mask, opposite_charge_mask, cutflow = apply_baseline_selection(data["nMuon"], data["Muon_charge"])
    
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
    
    #preparing the muons for the mass calculation
    muon1 = [pt_final[:, 0], eta_final[:, 0], phi_final[:, 0], mass_final[:, 0]]
    muon2 = [pt_final[:, 1], eta_final[:, 1], phi_final[:, 1], mass_final[:, 1]]
    
    invariant_mass = calculate_invariant_mass(muon1, muon2)
    
    # Generate the baseline spectrum plot
    plt.figure(figsize=(8, 6))
    plt.hist(invariant_mass, bins = 50, color="green", edgecolor="darkgreen", alpha=0.7)
    plt.xlabel("Invariant Mass (GeV)")
    plt.ylabel("No. Events")
    plt.title("Dimuon Invariant Mass Spectrum (Baseline Selection)")
    plt.grid(axis = 'y', alpha=0.75)
    plt.show()
    plt.savefig('outputs/baseline_mass_spectrum.png')
    print("Cutflow summary:", cutflow)
    
if __name__ == "__main__":
    # Test the pipeline locally using the synthetic file first
    run_baseline_analysis("data/synthetic-demo.root")
    