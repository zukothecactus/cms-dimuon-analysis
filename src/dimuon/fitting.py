from dataclasses import dataclass
import numpy as np
from scipy.optimize import curve_fit

@dataclass(frozen = True)
class FitResult:
    #stores the fitted parameters and their statistical outputs
    resonance_name: str
    signal_yield: float
    signal_yield_error: float
    fitted_mass: float
    fitted_mass_error: float
    resolution_sigma: float
    resolution_sigma_error: float
    background_yield: float
    background_yield_error: float
    chi2_ndof: float #chi-squared per degree of freedom
    significance: float
    
def composite_model(
    m: np.ndarray,
    S: float,
    m0: float,
    sigma: float,
    B:float,
    lambda_bg: float,
    m_min: float,
    bin_width: float
) -> np.ndarray:
    signal = (S/(np.sqrt(2 * np.pi) * sigma)) * np.exp(-0.5 * ((m - m0) / sigma) ** 2) #signal component: Gaussian
    bkg = B * lambda_bg * np.exp(-lambda_bg * (m - m_min)) #background component: Exponential negative slope
    
    #overall distribution, distributed over the bin width to account for histogram binning
    return (signal + bkg) * bin_width

def fit_resonance_window(
    bin_centers: np.ndarray, #centers of the histogram bins (1,2,3,... instead of 0.5,1.5,2.5,...)
    bin_counts: np.ndarray, #counts in each histogram bin
    mass_window: tuple[float, float],
    initial_guesses: dict[str, float], #initial parameters dict with keys: S, m0, sigma, B, lambda_bg
    resonance_name: str = "Resonance" #Label for the particle resonance being fitted
) -> tuple[FitResult, np.ndarray]:
    '''
        Fit all events in the specified mass window
    '''
    m_min, m_max = mass_window
    mask = (bin_centers >= m_min) & (bin_centers <= m_max)
    
    #super inadequate data check: if there are fewer than 5 bins in the mass window, raise an error
    if(np.sum(mask)<5):
        raise ValueError(f"Insufficient histogram bins ({np.sum(mask)}) in mass window {mass_window}")
    
    m_fit = bin_centers[mask]
    y_fit = bin_counts[mask] #yield instead of counts
    bin_width = m_fit[1] - m_fit[0] if len(m_fit) > 1 else 1.0 #assumes uniform binning, defaults to 1.0 when the mass window is too narrow to have multiple bins
    
    p0 = [
        initial_guesses.get("S", 100.0),
        initial_guesses.get("m0", (m_min + m_max) / 2),
        initial_guesses.get("sigma", 0.1),
        initial_guesses.get("B", 200.0),
        initial_guesses.get("lambda_bg", 0.5),
    ]
    
    bounds = (
        [0.0, m_min, 0.001, 0.0, 0.0], #lower bounds for S, m0, sigma, B, lambda_bg
        [np.inf, m_max, (m_min + m_max) / 2, np.inf, 10.0] #upper bounds for S, m0, sigma, B, lambda_bg
    )
    
    #scipy curve fitting with wrapper lambda to fix m_min and bin_width
    def fit_func(m, S, m0, sigma, B, lambda_bg):
        return composite_model(m, S, m0, sigma, B, lambda_bg, m_min, bin_width)
    
    sigma_y = np.sqrt(np.maximum(y_fit, 1.0)) #Poisson uncertainty: sqrt(N), with a minimum of 1 to avoid zero uncertainty
    
    #curve fitting, returns optimal parameters and covariance matrix
    popt, pcov = curve_fit(
        fit_func,
        m_fit,
        y_fit,
        p0=p0,
        bounds=bounds,
        sigma=sigma_y,
        absolute_sigma=True,
    )
    
    perr = np.sqrt(np.diag(pcov)) #standard errors of the fitted parameters
    
    #extract fitted parameters and their errors
    S_fit, m0_fit, sigma_fit, B_fit, lambda_bg_fit = popt
    S_err, m0_err, sigma_err, B_err, _ = perr
    
    # Compute Chi-Squared/ Degrees of Freedom
    y_pred = fit_func(m_fit, *popt) #predicted values from the fit
    residuals = (y_fit - y_pred) / sigma_y #normalized residuals (fitted - predicted) / uncertainty
    chi2 = float(np.sum(residuals**2))
    ndof = int(len(m_fit) - len(popt)) #degrees of freedom: number of data points minus number of fitted parameters
    chi2_ndof = chi2/ndof if ndof>0 else chi2 #avoid division by zero
    
    # Compute significance: S / sqrt(S + B)
    denominator = np.sqrt(S_fit + B_fit) if (S_fit + B_fit) > 0 else 1.0
    significance = float(S_fit / denominator)
    
    fit_result = FitResult(
        resonance_name=resonance_name,
        signal_yield=float(S_fit),
        signal_yield_error=float(S_err),
        fitted_mass=float(m0_fit),
        fitted_mass_error=float(m0_err),
        resolution_sigma=float(sigma_fit),
        resolution_sigma_error=float(sigma_err),
        background_yield=float(B_fit),
        background_yield_error=float(B_err),
        chi2_ndof=float(chi2_ndof),
        significance=float(significance)
    )
    
    fit_curve = fit_func(m_fit, *popt) #fitted curve values for the mass window
    return fit_result, fit_curve
