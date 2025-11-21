"""Calculate metrics like average cost, NAV ratio, etc."""

from typing import Dict, Optional
from dataclasses import dataclass


@dataclass
class Metrics:
    """Container for calculated metrics."""
    
    btc_holdings: float
    avg_cost_basis: float
    total_cost: float
    current_btc_price: float
    current_holdings_value: float
    unrealized_gain_loss: float
    unrealized_gain_loss_pct: float
    mstr_price: float
    mstr_market_cap: Optional[float]
    nav_ratio: Optional[float]
    premium_discount: Optional[float]  # Positive = premium, Negative = discount


class MetricsCalculator:
    """Calculate various metrics for MSTR Bitcoin holdings."""
    
    @staticmethod
    def calculate(
        btc_holdings: float,
        avg_cost_basis: float,
        current_btc_price: float,
        mstr_price: float,
        mstr_market_cap: Optional[float] = None,
        mstr_shares_outstanding: Optional[float] = None
    ) -> Metrics:
        """
        Calculate all metrics.
        
        Args:
            btc_holdings: Number of BTC held
            avg_cost_basis: Average cost per BTC
            current_btc_price: Current BTC price
            mstr_price: Current MSTR stock price
            mstr_market_cap: MSTR market cap (optional, will calculate if shares provided)
            mstr_shares_outstanding: Shares outstanding (optional, for market cap calc)
        
        Returns:
            Metrics object with all calculated values
        """
        # Calculate total cost
        total_cost = btc_holdings * avg_cost_basis
        
        # Calculate current holdings value
        current_holdings_value = btc_holdings * current_btc_price
        
        # Calculate unrealized gain/loss
        unrealized_gain_loss = current_holdings_value - total_cost
        unrealized_gain_loss_pct = (
            (unrealized_gain_loss / total_cost * 100) if total_cost > 0 else 0.0
        )
        
        # Calculate market cap if not provided
        if mstr_market_cap is None and mstr_shares_outstanding:
            mstr_market_cap = mstr_price * mstr_shares_outstanding
        
        # Calculate NAV ratio (market cap / BTC holdings value)
        nav_ratio = None
        premium_discount = None
        
        if mstr_market_cap and current_holdings_value > 0:
            nav_ratio = mstr_market_cap / current_holdings_value
            # Premium/Discount: (Market Cap - BTC Value) / BTC Value
            premium_discount = ((mstr_market_cap - current_holdings_value) / current_holdings_value) * 100
        
        return Metrics(
            btc_holdings=btc_holdings,
            avg_cost_basis=avg_cost_basis,
            total_cost=total_cost,
            current_btc_price=current_btc_price,
            current_holdings_value=current_holdings_value,
            unrealized_gain_loss=unrealized_gain_loss,
            unrealized_gain_loss_pct=unrealized_gain_loss_pct,
            mstr_price=mstr_price,
            mstr_market_cap=mstr_market_cap,
            nav_ratio=nav_ratio,
            premium_discount=premium_discount
        )
    
    @staticmethod
    def to_dict(metrics: Metrics) -> Dict:
        """Convert Metrics to dictionary."""
        return {
            "btc_holdings": metrics.btc_holdings,
            "avg_cost_basis": metrics.avg_cost_basis,
            "total_cost": metrics.total_cost,
            "current_btc_price": metrics.current_btc_price,
            "current_holdings_value": metrics.current_holdings_value,
            "unrealized_gain_loss": metrics.unrealized_gain_loss,
            "unrealized_gain_loss_pct": metrics.unrealized_gain_loss_pct,
            "mstr_price": metrics.mstr_price,
            "mstr_market_cap": metrics.mstr_market_cap,
            "nav_ratio": metrics.nav_ratio,
            "premium_discount": metrics.premium_discount
        }

