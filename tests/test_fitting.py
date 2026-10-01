import numpy as np
from dimuon.fitting import fit_resonance_window, composite_model
import pytest

def test_fit_resonance_window_synthetic_recovery():
    '''
        Generates synthetic signal and background data, fits it, and checks if the fitted parameters are close to the true values.
    '''
    
    np.random.seed(42)  # For reproducibility
    m_min, m_max = 2.5, 3.5  # GeV
    bin_edges = np.linspace(m_min, m_max, 51)  # 50 bins
    bin_centers = 0.5 * (bin_edges[:-1] + bin_edges[1:])
    bin_width = bin_edges[1] - bin_edges[0]
    
    # True Parameters
    S_true = 1000.0
    m0_true = 3.097
    sigma_true = 0.05
    B_true = 2000.0
    lambda_true = 0.4
    
    # Generate synthetic data
    expected_counts = composite_model(bin_centers, S_true, m0_true, sigma_true, B_true, lambda_true, m_min, bin_width)
    
    # Poisson fluctuations to simulate observed counts (poisson noise)
    noisy_counts = np.random.poisson(expected_counts).astype(float)
    initial_guesses = {"S": 800.0, "m0": 3.10, "sigma": 0.04, "B": 1500.0, "lambda_bg": 0.3}
    
    fit_res, _ = fit_resonance_window(
        bin_centers, 
        noisy_counts, 
        mass_window=(m_min, m_max), 
        initial_guesses=initial_guesses, 
        resonance_name="Synthetic_JPsi"
    )
    # Verify parameter recovery within 3-sigma uncertainties
    assert np.isclose(fit_res.fitted_mass, m0_true, atol=0.01)
    assert np.isclose(fit_res.resolution_sigma, sigma_true, atol=0.015)
    assert fit_res.significance > 10.0
    