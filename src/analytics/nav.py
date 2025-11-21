"""NAV (Net Asset Value) calculations and metrics."""

from dataclasses import dataclass
from datetime import date
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_

from ..database.models import (
    HoldingsTranche, CompanyStats, MarketPrice, DailySnapshot
)


@dataclass
class NAVMetrics:
    """NAV metrics data class."""
    total_btc: float
    btc_nav_usd: float
    bs_nav_usd: Optional[float]
    btc_per_share: Optional[float]
    bs_nav_per_share: Optional[float]
    premium_to_btc_nav: Optional[float]
    premium_to_bs_nav: Optional[float]
    btc_spot_price: float
    mstr_share_price: float
    market_cap_usd: float
    shares_outstanding: Optional[float]
    cash_usd: Optional[float]
    debt_usd_market: Optional[float]


def get_total_btc(session: Session, as_of_date: Optional[date] = None) -> float:
    """
    Get total BTC holdings as of a specific date.
    
    Args:
        session: Database session
        as_of_date: Date to query (defaults to latest)
        
    Returns:
        Total BTC holdings
    """
    if as_of_date is None:
        as_of_date = date.today()
    
    # Sum all tranches up to and including the as_of_date
    tranches = session.query(HoldingsTranche).filter(
        HoldingsTranche.as_of_date <= as_of_date
    ).all()
    
    if not tranches:
        return 0.0
    
    return sum(t.btc_acquired for t in tranches)


def get_btc_per_share(
    session: Session, 
    as_of_date: Optional[date] = None
) -> Optional[float]:
    """
    Calculate BTC per share.
    
    Args:
        session: Database session
        as_of_date: Date to query (defaults to latest)
        
    Returns:
        BTC per share or None if shares_outstanding not available
    """
    if as_of_date is None:
        as_of_date = date.today()
    
    total_btc = get_total_btc(session, as_of_date)
    
    # Get shares outstanding
    company_stat = session.query(CompanyStats).filter(
        CompanyStats.as_of_date <= as_of_date
    ).order_by(desc(CompanyStats.as_of_date)).first()
    
    if not company_stat or not company_stat.shares_outstanding:
        return None
    
    return total_btc / company_stat.shares_outstanding


def compute_nav_metrics(
    session: Session,
    as_of_date: Optional[date] = None
) -> Optional[NAVMetrics]:
    """
    Compute comprehensive NAV metrics.
    
    Args:
        session: Database session
        as_of_date: Date to query (defaults to latest)
        
    Returns:
        NAVMetrics dataclass or None if data is incomplete
    """
    if as_of_date is None:
        as_of_date = date.today()
    
    # Get total BTC
    total_btc = get_total_btc(session, as_of_date)
    if total_btc == 0:
        return None
    
    # Get BTC price
    btc_price_rec = session.query(MarketPrice).filter(
        and_(
            MarketPrice.as_of_date <= as_of_date,
            MarketPrice.asset == 'BTC'
        )
    ).order_by(desc(MarketPrice.as_of_date)).first()
    
    if not btc_price_rec:
        return None
    
    btc_spot_price = btc_price_rec.close_price
    
    # Get MSTR price
    mstr_price_rec = session.query(MarketPrice).filter(
        and_(
            MarketPrice.as_of_date <= as_of_date,
            MarketPrice.asset == 'MSTR'
        )
    ).order_by(desc(MarketPrice.as_of_date)).first()
    
    if not mstr_price_rec:
        return None
    
    mstr_share_price = mstr_price_rec.close_price
    
    # Get company stats
    company_stat = session.query(CompanyStats).filter(
        CompanyStats.as_of_date <= as_of_date
    ).order_by(desc(CompanyStats.as_of_date)).first()
    
    shares_outstanding = company_stat.shares_outstanding if company_stat else None
    cash_usd = company_stat.cash_usd if company_stat else None
    debt_usd_market = company_stat.debt_usd_market if company_stat else None
    
    # Calculate NAV values
    btc_nav_usd = total_btc * btc_spot_price
    
    # Balance sheet NAV (BTC value + cash - debt)
    bs_nav_usd = None
    if cash_usd is not None and debt_usd_market is not None:
        bs_nav_usd = btc_nav_usd + cash_usd - debt_usd_market
    
    # Market cap
    market_cap_usd = None
    if shares_outstanding:
        market_cap_usd = shares_outstanding * mstr_share_price
    
    # Per share metrics
    btc_per_share = None
    bs_nav_per_share = None
    if shares_outstanding:
        btc_per_share = total_btc / shares_outstanding
        if bs_nav_usd is not None:
            bs_nav_per_share = bs_nav_usd / shares_outstanding
    
    # Premium/discount calculations
    premium_to_btc_nav = None
    premium_to_bs_nav = None
    if market_cap_usd and btc_nav_usd > 0:
        premium_to_btc_nav = (market_cap_usd / btc_nav_usd) - 1.0
    if market_cap_usd and bs_nav_usd and bs_nav_usd > 0:
        premium_to_bs_nav = (market_cap_usd / bs_nav_usd) - 1.0
    
    return NAVMetrics(
        total_btc=total_btc,
        btc_nav_usd=btc_nav_usd,
        bs_nav_usd=bs_nav_usd,
        btc_per_share=btc_per_share,
        bs_nav_per_share=bs_nav_per_share,
        premium_to_btc_nav=premium_to_btc_nav,
        premium_to_bs_nav=premium_to_bs_nav,
        btc_spot_price=btc_spot_price,
        mstr_share_price=mstr_share_price,
        market_cap_usd=market_cap_usd or 0,
        shares_outstanding=shares_outstanding,
        cash_usd=cash_usd,
        debt_usd_market=debt_usd_market
    )
