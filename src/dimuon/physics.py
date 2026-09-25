import numpy as np
import awkward as ak

def calculate_invariant_mass(muon1, muon2):
    """Calculates the invariant mass of a system composed of two muons.
    
    Args:
        muon1 (array): pt, eta, phi, mass of muon1
        muon2 (array): pt, eta, phi, mass of muon2
    """
    pt1 = muon1[0]
    eta1 = muon1[1]
    phi1 = muon1[2]
    mass1 = muon1[3]

    pt2 = muon2[0]
    eta2 = muon2[1]
    phi2 = muon2[2]
    mass2 = muon2[3]
    
    # Cartesian momentum components for muon 1
    px1 = pt1 * np.cos(phi1)
    py1 = pt1 * np.sin(phi1)
    pz1 = pt1 * np.sinh(eta1)
    
    # total energy for muon 1
    E1 = np.sqrt(px1**2 + py1**2 + pz1**2 + mass1**2)
    
    
    # Cartesian momentum components for muon 2
    px2 = pt2 * np.cos(phi2)
    py2 = pt2 * np.sin(phi2)
    pz2 = pt2 * np.sinh(eta2)

    # total energy for muon 2
    E2 = np.sqrt(px2**2 + py2**2 + pz2**2 + mass2**2)

    # Total momentum components - for the parent system
    px = px1 + px2
    py = py1 + py2
    pz = pz1 + pz2

    # Total energy - for the parent system
    energy = E1 + E2
    
    # Invariant mass of the parent system
    invariant_mass_squared = energy**2 - px**2 - py**2 - pz**2
    
    #to protect against negative values due to numerical precision issues, we can use np.maximum to ensure that the argument of the square root is non-negative.
    invariant_mass_squared = np.maximum(invariant_mass_squared, 0)
    
    invariant_mass = np.sqrt(invariant_mass_squared)
    
    return invariant_mass