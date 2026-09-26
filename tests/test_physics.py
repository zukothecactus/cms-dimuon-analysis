import numpy as np
import pytest
from dimuon.physics import calculate_invariant_mass

'''
Validates relativistic 4-momentum math (back-to-back particle decays and rest-frame mass calculations).
'''


def test_calculate_invariant_mass_back_to_back():
    muon1 = [10.0, 0.0, 0.0, 0.105]  # pt, eta, phi, mass
    muon2 = [10.0, 0.0, np.pi, 0.105]  # pt, eta, phi, mass
    
    # Analytical total energy: 2 * sqrt(pT^2 + m^2)
    expected_energy = 2.0*np.sqrt(10.0**2 + 0.105**2)
    
    invariant_mass = calculate_invariant_mass(muon1, muon2)
    assert np.isclose(invariant_mass, expected_energy, rtol=1e-5)
    
def test_calculate_invariant_mass_at_rest():
    muon1 = [0.0, 0.0, 0.0, 0.105]  # pt, eta, phi, mass
    muon2 = [0.0, 0.0, 0.0, 0.105]  # pt, eta, phi, mass
    
    expected_mass = 2 * 0.105  # Total mass of the system
    
    invariant_mass = calculate_invariant_mass(muon1, muon2)
    assert np.isclose(invariant_mass, expected_mass, rtol=1e-5)