"""Monte Carlo simulation paths for BTC and MSTR."""

from dataclasses import dataclass
from typing import Tuple, Optional
import numpy as np
from scipy import stats

# Constants
MIN_DATA_POINTS = 10  # Minimum data points for beta estimation
DEFAULT_BETA = 1.5  # Default beta if insufficient data
DEFAULT_ALPHA = 0.0  # Default alpha
DEFAULT_RESIDUAL_SIGMA = 0.30  # Default residual volatility


@dataclass
class SimulationPaths:
    """Container for simulation path results."""
    btc_paths: np.ndarray  # Shape: (num_paths, horizon_days + 1)
    mstr_paths: Optional[np.ndarray]  # Shape: (num_paths, horizon_days + 1) or None
    initial_btc_price: float
    initial_mstr_price: Optional[float]
    num_paths: int
    horizon_days: int


def simulate_btc_paths(
    initial_price: float,
    horizon_days: int,
    num_paths: int,
    mu: float = 0.20,
    sigma: float = 0.80,
    dt: float = 1/252,
    seed: Optional[int] = None
) -> np.ndarray:
    """
    Simulate BTC price paths using Geometric Brownian Motion (GBM).
    
    dS/S = mu * dt + sigma * dW
    
    Args:
        initial_price: Starting BTC price
        horizon_days: Number of days to simulate
        num_paths: Number of simulation paths
        mu: Annual drift (expected return)
        sigma: Annual volatility
        dt: Time step (default 1/252 for daily with trading days)
        seed: Random seed for reproducibility
        
    Returns:
        Array of shape (num_paths, horizon_days + 1) with price paths
    """
    if seed is not None:
        np.random.seed(seed)
    
    # Generate random normal increments
    random_increments = np.random.standard_normal((num_paths, horizon_days))
    
    # Calculate log returns
    # S(t+dt) = S(t) * exp((mu - 0.5*sigma^2)*dt + sigma*sqrt(dt)*Z)
    drift = (mu - 0.5 * sigma ** 2) * dt
    diffusion = sigma * np.sqrt(dt)
    
    log_returns = drift + diffusion * random_increments
    
    # Initialize price paths
    paths = np.zeros((num_paths, horizon_days + 1))
    paths[:, 0] = initial_price
    
    # Build paths from log returns
    paths[:, 1:] = initial_price * np.exp(np.cumsum(log_returns, axis=1))
    
    return paths


def simulate_joint_btc_mstr_paths(
    initial_btc_price: float,
    initial_mstr_price: float,
    horizon_days: int,
    num_paths: int,
    btc_mu: float = 0.20,
    btc_sigma: float = 0.80,
    beta: float = 1.5,
    alpha: float = 0.0,
    residual_sigma: float = 0.30,
    dt: float = 1/252,
    seed: Optional[int] = None
) -> SimulationPaths:
    """
    Simulate joint BTC and MSTR paths using beta model.
    
    Model:
        r_BTC ~ GBM(mu_btc, sigma_btc)
        r_MSTR = alpha + beta * r_BTC + epsilon
        where epsilon ~ N(0, residual_sigma^2)
    
    Args:
        initial_btc_price: Starting BTC price
        initial_mstr_price: Starting MSTR price
        horizon_days: Number of days to simulate
        num_paths: Number of simulation paths
        btc_mu: BTC annual drift
        btc_sigma: BTC annual volatility
        beta: MSTR beta vs BTC
        alpha: MSTR alpha (excess return over beta*BTC)
        residual_sigma: Residual volatility of MSTR not explained by BTC
        dt: Time step
        seed: Random seed
        
    Returns:
        SimulationPaths with both BTC and MSTR paths
    """
    if seed is not None:
        np.random.seed(seed)
    
    # Simulate BTC paths
    btc_paths = simulate_btc_paths(
        initial_price=initial_btc_price,
        horizon_days=horizon_days,
        num_paths=num_paths,
        mu=btc_mu,
        sigma=btc_sigma,
        dt=dt,
        seed=seed
    )
    
    # Calculate BTC returns from paths
    btc_returns = np.diff(np.log(btc_paths), axis=1)
    
    # Generate residual (idiosyncratic) noise for MSTR
    np.random.seed(seed + 1 if seed else None)
    residual_noise = np.random.standard_normal((num_paths, horizon_days))
    residual_noise = residual_noise * residual_sigma * np.sqrt(dt)
    
    # Calculate MSTR returns using beta model
    # r_MSTR = alpha*dt + beta * r_BTC + epsilon
    mstr_returns = alpha * dt + beta * btc_returns + residual_noise
    
    # Build MSTR price paths from returns
    mstr_paths = np.zeros((num_paths, horizon_days + 1))
    mstr_paths[:, 0] = initial_mstr_price
    mstr_paths[:, 1:] = initial_mstr_price * np.exp(np.cumsum(mstr_returns, axis=1))
    
    return SimulationPaths(
        btc_paths=btc_paths,
        mstr_paths=mstr_paths,
        initial_btc_price=initial_btc_price,
        initial_mstr_price=initial_mstr_price,
        num_paths=num_paths,
        horizon_days=horizon_days
    )


def estimate_beta_parameters(
    btc_returns: np.ndarray,
    mstr_returns: np.ndarray
) -> Tuple[float, float, float]:
    """
    Estimate beta model parameters from historical returns.
    
    Fits: r_MSTR = alpha + beta * r_BTC + epsilon
    
    Args:
        btc_returns: Array of BTC returns
        mstr_returns: Array of MSTR returns (aligned with BTC)
        
    Returns:
        Tuple of (alpha, beta, residual_sigma)
    """
    # Ensure arrays are 1D and aligned
    btc_returns = btc_returns.flatten()
    mstr_returns = mstr_returns.flatten()
    
    # Remove NaN values
    mask = ~(np.isnan(btc_returns) | np.isnan(mstr_returns))
    btc_returns = btc_returns[mask]
    mstr_returns = mstr_returns[mask]
    
    if len(btc_returns) < MIN_DATA_POINTS:
        # Not enough data, return defaults
        return DEFAULT_ALPHA, DEFAULT_BETA, DEFAULT_RESIDUAL_SIGMA
    
    # Linear regression: mstr = alpha + beta * btc + epsilon
    slope, intercept, r_value, p_value, std_err = stats.linregress(btc_returns, mstr_returns)
    
    beta = slope
    alpha = intercept
    
    # Calculate residual standard deviation
    predicted = alpha + beta * btc_returns
    residuals = mstr_returns - predicted
    residual_sigma = np.std(residuals)
    
    return alpha, beta, residual_sigma
