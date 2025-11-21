"""Tranche-level analytics and performance tracking."""

from dataclasses import dataclass
from datetime import date
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_

from ..database.models import HoldingsTranche, MarketPrice


@dataclass
class TrancheSummary:
    """Summary of a single tranche."""
    id: int
    as_of_date: date
    btc_acquired: float
    usd_spent: float
    source_type: str
    implied_btc_price: float
    current_btc_price: float
    current_market_value: float
    unrealized_pnl_abs: float
    unrealized_pnl_pct: float
    age_days: int
    notes: Optional[str]


@dataclass
class PortfolioSummary:
    """Portfolio-level summary."""
    total_btc: float
    total_cost: float
    total_current_value: float
    total_unrealized_pnl: float
    total_unrealized_pnl_pct: float
    weighted_avg_cost: float
    tranches_count: int


@dataclass
class TrancheAnalysis:
    """Complete tranche analysis."""
    tranches: List[TrancheSummary]
    portfolio: PortfolioSummary


def get_tranche_summary(
    session: Session,
    as_of_date: Optional[date] = None
) -> Optional[TrancheAnalysis]:
    """
    Get comprehensive tranche-level summary.
    
    Args:
        session: Database session
        as_of_date: Date to evaluate at (defaults to today)
        
    Returns:
        TrancheAnalysis with individual tranches and portfolio summary
    """
    if as_of_date is None:
        as_of_date = date.today()
    
    # Get all tranches up to as_of_date
    tranches = session.query(HoldingsTranche).filter(
        HoldingsTranche.as_of_date <= as_of_date
    ).order_by(HoldingsTranche.as_of_date).all()
    
    if not tranches:
        return None
    
    # Get current BTC price
    btc_price_rec = session.query(MarketPrice).filter(
        and_(
            MarketPrice.as_of_date <= as_of_date,
            MarketPrice.asset == 'BTC'
        )
    ).order_by(desc(MarketPrice.as_of_date)).first()
    
    if not btc_price_rec:
        return None
    
    current_btc_price = btc_price_rec.close_price
    
    # Process each tranche
    tranche_summaries = []
    total_btc = 0.0
    total_cost = 0.0
    total_current_value = 0.0
    
    for tranche in tranches:
        current_value = tranche.btc_acquired * current_btc_price
        unrealized_pnl_abs = current_value - tranche.usd_spent
        unrealized_pnl_pct = (unrealized_pnl_abs / tranche.usd_spent) * 100 if tranche.usd_spent > 0 else 0
        age_days = (as_of_date - tranche.as_of_date).days
        
        tranche_summaries.append(TrancheSummary(
            id=tranche.id,
            as_of_date=tranche.as_of_date,
            btc_acquired=tranche.btc_acquired,
            usd_spent=tranche.usd_spent,
            source_type=tranche.source_type,
            implied_btc_price=tranche.implied_btc_price,
            current_btc_price=current_btc_price,
            current_market_value=current_value,
            unrealized_pnl_abs=unrealized_pnl_abs,
            unrealized_pnl_pct=unrealized_pnl_pct,
            age_days=age_days,
            notes=tranche.notes
        ))
        
        total_btc += tranche.btc_acquired
        total_cost += tranche.usd_spent
        total_current_value += current_value
    
    # Calculate portfolio summary
    total_unrealized_pnl = total_current_value - total_cost
    total_unrealized_pnl_pct = (total_unrealized_pnl / total_cost) * 100 if total_cost > 0 else 0
    weighted_avg_cost = total_cost / total_btc if total_btc > 0 else 0
    
    portfolio = PortfolioSummary(
        total_btc=total_btc,
        total_cost=total_cost,
        total_current_value=total_current_value,
        total_unrealized_pnl=total_unrealized_pnl,
        total_unrealized_pnl_pct=total_unrealized_pnl_pct,
        weighted_avg_cost=weighted_avg_cost,
        tranches_count=len(tranches)
    )
    
    return TrancheAnalysis(
        tranches=tranche_summaries,
        portfolio=portfolio
    )
