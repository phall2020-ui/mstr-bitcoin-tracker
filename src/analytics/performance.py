"""Performance analytics: returns, volatility, beta, drawdowns."""

from dataclasses import dataclass
from datetime import date, timedelta
from typing import Optional, List, Tuple
import pandas as pd
import numpy as np
from sqlalchemy.orm import Session
from sqlalchemy import and_

from ..database.models import MarketPrice

# Constants
MIN_DRAWDOWN_THRESHOLD = 0.05  # Only report drawdowns > 5%


@dataclass
class ReturnsMetrics:
    """Returns calculation results."""
    daily_returns: pd.Series
    cumulative_return: float
    annualized_return: float
    volatility: float
    sharpe_ratio: Optional[float]


@dataclass
class BetaMetrics:
    """Beta and correlation metrics."""
    beta: float
    correlation: float
    alpha: float
    r_squared: float
    rolling_beta_30d: Optional[pd.Series]
    rolling_beta_90d: Optional[pd.Series]


@dataclass
class DrawdownMetrics:
    """Drawdown analysis."""
    max_drawdown: float
    current_drawdown: float
    max_drawdown_start: Optional[date]
    max_drawdown_end: Optional[date]
    max_drawdown_duration_days: Optional[int]
    top_drawdowns: List[Tuple[date, date, float, int]]


def compute_returns(
    session: Session,
    asset: str,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    freq: str = "D"
) -> Optional[ReturnsMetrics]:
    """
    Compute returns metrics for an asset.
    
    Args:
        session: Database session
        asset: Asset symbol ('BTC', 'MSTR', etc.)
        start_date: Start date (defaults to 90 days ago)
        end_date: End date (defaults to today)
        freq: Frequency ('D' for daily)
        
    Returns:
        ReturnsMetrics or None if insufficient data
    """
    if end_date is None:
        end_date = date.today()
    if start_date is None:
        start_date = end_date - timedelta(days=90)
    
    # Get price data
    prices = session.query(MarketPrice).filter(
        and_(
            MarketPrice.asset == asset,
            MarketPrice.as_of_date >= start_date,
            MarketPrice.as_of_date <= end_date
        )
    ).order_by(MarketPrice.as_of_date).all()
    
    if len(prices) < 2:
        return None
    
    # Convert to pandas Series
    price_series = pd.Series(
        {p.as_of_date: p.close_price for p in prices}
    )
    
    # Calculate returns
    daily_returns = price_series.pct_change().dropna()
    
    if len(daily_returns) == 0:
        return None
    
    cumulative_return = (price_series.iloc[-1] / price_series.iloc[0]) - 1
    
    # Annualized metrics (assuming 252 trading days)
    n_days = len(daily_returns)
    annualized_return = (1 + daily_returns.mean()) ** 252 - 1
    volatility = daily_returns.std() * np.sqrt(252)
    
    # Sharpe ratio (assuming 0 risk-free rate for simplicity)
    sharpe_ratio = annualized_return / volatility if volatility > 0 else None
    
    return ReturnsMetrics(
        daily_returns=daily_returns,
        cumulative_return=cumulative_return,
        annualized_return=annualized_return,
        volatility=volatility,
        sharpe_ratio=sharpe_ratio
    )


def compute_beta_vs_btc(
    session: Session,
    asset: str = "MSTR",
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    rolling_windows: bool = True
) -> Optional[BetaMetrics]:
    """
    Compute beta and correlation vs BTC.
    
    Args:
        session: Database session
        asset: Asset to analyze (default 'MSTR')
        start_date: Start date (defaults to 90 days ago)
        end_date: End date (defaults to today)
        rolling_windows: Whether to compute rolling beta
        
    Returns:
        BetaMetrics or None if insufficient data
    """
    if end_date is None:
        end_date = date.today()
    if start_date is None:
        start_date = end_date - timedelta(days=90)
    
    # Get BTC returns
    btc_metrics = compute_returns(session, 'BTC', start_date, end_date)
    if not btc_metrics:
        return None
    
    # Get asset returns
    asset_metrics = compute_returns(session, asset, start_date, end_date)
    if not asset_metrics:
        return None
    
    # Align the two series
    combined = pd.DataFrame({
        'btc': btc_metrics.daily_returns,
        'asset': asset_metrics.daily_returns
    }).dropna()
    
    if len(combined) < 10:
        return None
    
    # Calculate beta using regression
    # asset_return = alpha + beta * btc_return + epsilon
    btc_returns = combined['btc'].values
    asset_returns = combined['asset'].values
    
    # Simple linear regression
    covariance = np.cov(btc_returns, asset_returns)[0, 1]
    btc_variance = np.var(btc_returns)
    
    beta = covariance / btc_variance if btc_variance > 0 else 0
    correlation = np.corrcoef(btc_returns, asset_returns)[0, 1]
    
    # Calculate alpha (intercept)
    alpha = asset_returns.mean() - beta * btc_returns.mean()
    
    # R-squared
    ss_res = np.sum((asset_returns - (alpha + beta * btc_returns)) ** 2)
    ss_tot = np.sum((asset_returns - asset_returns.mean()) ** 2)
    r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0
    
    # Rolling beta calculations
    rolling_beta_30d = None
    rolling_beta_90d = None
    
    if rolling_windows and len(combined) >= 30:
        rolling_beta_30d = combined['btc'].rolling(30).cov(combined['asset']) / \
                           combined['btc'].rolling(30).var()
        
        if len(combined) >= 90:
            rolling_beta_90d = combined['btc'].rolling(90).cov(combined['asset']) / \
                               combined['btc'].rolling(90).var()
    
    return BetaMetrics(
        beta=beta,
        correlation=correlation,
        alpha=alpha * 252,  # Annualized alpha
        r_squared=r_squared,
        rolling_beta_30d=rolling_beta_30d,
        rolling_beta_90d=rolling_beta_90d
    )


def compute_drawdowns(
    session: Session,
    asset: str,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    top_n: int = 5
) -> Optional[DrawdownMetrics]:
    """
    Compute drawdown analysis.
    
    Args:
        session: Database session
        asset: Asset symbol
        start_date: Start date
        end_date: End date
        top_n: Number of top drawdowns to return
        
    Returns:
        DrawdownMetrics or None if insufficient data
    """
    if end_date is None:
        end_date = date.today()
    if start_date is None:
        start_date = end_date - timedelta(days=365)
    
    # Get price data
    prices = session.query(MarketPrice).filter(
        and_(
            MarketPrice.asset == asset,
            MarketPrice.as_of_date >= start_date,
            MarketPrice.as_of_date <= end_date
        )
    ).order_by(MarketPrice.as_of_date).all()
    
    if len(prices) < 2:
        return None
    
    # Convert to pandas Series
    price_series = pd.Series(
        {p.as_of_date: p.close_price for p in prices}
    )
    
    # Calculate running maximum and drawdown
    running_max = price_series.expanding().max()
    drawdown = (price_series - running_max) / running_max
    
    max_drawdown = drawdown.min()
    current_drawdown = drawdown.iloc[-1]
    
    # Find max drawdown period
    max_dd_end_idx = drawdown.idxmin()
    max_dd_end = max_dd_end_idx
    
    # Find start of max drawdown (last peak before the trough)
    prices_before_trough = price_series[:max_dd_end_idx]
    if len(prices_before_trough) > 0:
        max_dd_start = prices_before_trough.idxmax()
        max_dd_duration = (max_dd_end - max_dd_start).days
    else:
        max_dd_start = None
        max_dd_duration = None
    
    # Find top N drawdowns (simplified - just find local minima)
    top_drawdowns = []
    drawdown_values = drawdown.values
    drawdown_dates = list(drawdown.index)
    
    # Simple peak detection
    for i in range(1, len(drawdown_values) - 1):
        if drawdown_values[i] < drawdown_values[i-1] and drawdown_values[i] < drawdown_values[i+1]:
            # Local minimum found
            if drawdown_values[i] < -MIN_DRAWDOWN_THRESHOLD:  # Only significant drawdowns
                # Find the peak before
                peak_idx = i - 1
                while peak_idx > 0 and price_series.iloc[peak_idx] < price_series.iloc[peak_idx - 1]:
                    peak_idx -= 1
                
                peak_date = drawdown_dates[peak_idx]
                trough_date = drawdown_dates[i]
                dd_value = drawdown_values[i]
                duration = (trough_date - peak_date).days
                
                top_drawdowns.append((peak_date, trough_date, dd_value, duration))
    
    # Sort by magnitude and take top N
    top_drawdowns.sort(key=lambda x: x[2])
    top_drawdowns = top_drawdowns[:top_n]
    
    return DrawdownMetrics(
        max_drawdown=max_drawdown,
        current_drawdown=current_drawdown,
        max_drawdown_start=max_dd_start,
        max_drawdown_end=max_dd_end,
        max_drawdown_duration_days=max_dd_duration,
        top_drawdowns=top_drawdowns
    )
