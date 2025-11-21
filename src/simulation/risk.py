"""Risk metrics: VaR, CVaR, and simulation risk analysis."""

from dataclasses import dataclass
from typing import Optional, Dict, Any
import numpy as np


@dataclass
class RiskMetrics:
    """Risk metrics from simulation results."""
    var_95: float  # Value at Risk at 95% confidence
    cvar_95: float  # Conditional VaR (Expected Shortfall) at 95%
    var_99: float  # VaR at 99%
    cvar_99: float  # CVaR at 99%
    mean_return: float
    median_return: float
    std_return: float
    percentiles: Dict[str, float]  # Various percentile returns


def compute_var_cvar(
    final_prices: np.ndarray,
    initial_price: float,
    alpha: float = 0.95
) -> tuple[float, float]:
    """
    Compute Value at Risk (VaR) and Conditional VaR (CVaR).
    
    VaR(alpha) = -percentile(returns, 1-alpha)
    CVaR(alpha) = -E[returns | returns <= -VaR(alpha)]
    
    Args:
        final_prices: Array of final prices from simulation paths
        initial_price: Initial price
        alpha: Confidence level (default 0.95 for 95%)
        
    Returns:
        Tuple of (VaR, CVaR) as returns (negative values indicate losses)
    """
    # Calculate returns
    returns = (final_prices - initial_price) / initial_price
    
    # VaR: (1-alpha) percentile of the return distribution
    # Negative sign convention: VaR is reported as a positive number for losses
    var = -np.percentile(returns, (1 - alpha) * 100)
    
    # CVaR: Average of returns worse than VaR
    threshold = -var
    worse_returns = returns[returns <= threshold]
    
    if len(worse_returns) > 0:
        cvar = -np.mean(worse_returns)
    else:
        cvar = var
    
    return var, cvar


def compute_risk_metrics(
    final_prices: np.ndarray,
    initial_price: float
) -> RiskMetrics:
    """
    Compute comprehensive risk metrics from simulation results.
    
    Args:
        final_prices: Array of final prices from simulation
        initial_price: Initial price
        
    Returns:
        RiskMetrics dataclass
    """
    # Calculate returns
    returns = (final_prices - initial_price) / initial_price
    
    # VaR and CVaR at different confidence levels
    var_95, cvar_95 = compute_var_cvar(final_prices, initial_price, alpha=0.95)
    var_99, cvar_99 = compute_var_cvar(final_prices, initial_price, alpha=0.99)
    
    # Basic statistics
    mean_return = np.mean(returns)
    median_return = np.median(returns)
    std_return = np.std(returns)
    
    # Percentiles
    percentiles = {
        "1": np.percentile(returns, 1),
        "5": np.percentile(returns, 5),
        "10": np.percentile(returns, 10),
        "25": np.percentile(returns, 25),
        "50": np.percentile(returns, 50),
        "75": np.percentile(returns, 75),
        "90": np.percentile(returns, 90),
        "95": np.percentile(returns, 95),
        "99": np.percentile(returns, 99)
    }
    
    return RiskMetrics(
        var_95=var_95,
        cvar_95=cvar_95,
        var_99=var_99,
        cvar_99=cvar_99,
        mean_return=mean_return,
        median_return=median_return,
        std_return=std_return,
        percentiles=percentiles
    )


def compute_portfolio_risk(
    btc_final_prices: np.ndarray,
    mstr_final_prices: np.ndarray,
    btc_initial_price: float,
    mstr_initial_price: float,
    mstr_shares: float
) -> RiskMetrics:
    """
    Compute risk metrics for a portfolio (personal MSTR position).
    
    Args:
        btc_final_prices: BTC final prices from simulation
        mstr_final_prices: MSTR final prices from simulation
        btc_initial_price: Initial BTC price
        mstr_initial_price: Initial MSTR price
        mstr_shares: Number of MSTR shares held
        
    Returns:
        RiskMetrics for the portfolio value
    """
    # Calculate portfolio values
    initial_value = mstr_shares * mstr_initial_price
    final_values = mstr_shares * mstr_final_prices
    
    return compute_risk_metrics(final_values, initial_value)


def create_risk_summary(
    btc_risk: RiskMetrics,
    mstr_risk: Optional[RiskMetrics] = None,
    portfolio_risk: Optional[RiskMetrics] = None
) -> Dict[str, Any]:
    """
    Create a comprehensive risk summary dictionary.
    
    Args:
        btc_risk: Risk metrics for BTC
        mstr_risk: Risk metrics for MSTR (optional)
        portfolio_risk: Risk metrics for portfolio (optional)
        
    Returns:
        Dictionary with structured risk summary
    """
    summary = {
        "btc": {
            "var_95": btc_risk.var_95,
            "cvar_95": btc_risk.cvar_95,
            "var_99": btc_risk.var_99,
            "cvar_99": btc_risk.cvar_99,
            "mean_return": btc_risk.mean_return,
            "median_return": btc_risk.median_return,
            "std_return": btc_risk.std_return,
            "percentiles": btc_risk.percentiles
        }
    }
    
    if mstr_risk:
        summary["mstr"] = {
            "var_95": mstr_risk.var_95,
            "cvar_95": mstr_risk.cvar_95,
            "var_99": mstr_risk.var_99,
            "cvar_99": mstr_risk.cvar_99,
            "mean_return": mstr_risk.mean_return,
            "median_return": mstr_risk.median_return,
            "std_return": mstr_risk.std_return,
            "percentiles": mstr_risk.percentiles
        }
    
    if portfolio_risk:
        summary["portfolio"] = {
            "var_95": portfolio_risk.var_95,
            "cvar_95": portfolio_risk.cvar_95,
            "var_99": portfolio_risk.var_99,
            "cvar_99": portfolio_risk.cvar_99,
            "mean_return": portfolio_risk.mean_return,
            "median_return": portfolio_risk.median_return,
            "std_return": portfolio_risk.std_return,
            "percentiles": portfolio_risk.percentiles
        }
    
    return summary
