"""Personal position analytics."""

from dataclasses import dataclass
from datetime import date
from typing import Optional
from sqlalchemy.orm import Session

from ..database.models import UserPosition
from .nav import get_btc_per_share, compute_nav_metrics


@dataclass
class PositionMetrics:
    """Personal position metrics."""
    label: str
    shares: float
    avg_entry_price: float
    current_price: float
    current_value: float
    cost_basis: float
    unrealized_pnl: float
    unrealized_pnl_pct: float
    implied_btc_exposure: Optional[float]
    btc_per_share: Optional[float]


def get_active_position(session: Session) -> Optional[UserPosition]:
    """
    Get the active user position.
    
    Args:
        session: Database session
        
    Returns:
        Active UserPosition or None
    """
    return session.query(UserPosition).filter(
        UserPosition.is_active.is_(True)
    ).first()


def get_position_by_id(session: Session, position_id: int) -> Optional[UserPosition]:
    """
    Get a specific user position by ID.
    
    Args:
        session: Database session
        position_id: Position ID
        
    Returns:
        UserPosition or None
    """
    return session.query(UserPosition).filter(
        UserPosition.id == position_id
    ).first()


def compute_position_metrics(
    session: Session,
    position_id: Optional[int] = None,
    as_of_date: Optional[date] = None
) -> Optional[PositionMetrics]:
    """
    Compute metrics for a personal position.
    
    Args:
        session: Database session
        position_id: Position ID (defaults to active position)
        as_of_date: Date to evaluate at (defaults to today)
        
    Returns:
        PositionMetrics or None if no position exists
    """
    if as_of_date is None:
        as_of_date = date.today()
    
    # Get position
    if position_id:
        position = get_position_by_id(session, position_id)
    else:
        position = get_active_position(session)
    
    if not position:
        return None
    
    # Get NAV metrics to get current MSTR price and BTC per share
    nav_metrics = compute_nav_metrics(session, as_of_date)
    
    if not nav_metrics:
        return None
    
    current_price = nav_metrics.mstr_share_price
    btc_per_share = nav_metrics.btc_per_share
    
    # Calculate position metrics
    current_value = position.shares * current_price
    cost_basis = position.shares * position.avg_entry_price
    unrealized_pnl = current_value - cost_basis
    unrealized_pnl_pct = (unrealized_pnl / cost_basis) * 100 if cost_basis > 0 else 0
    
    # Implied BTC exposure
    implied_btc_exposure = None
    if btc_per_share:
        implied_btc_exposure = position.shares * btc_per_share
    
    return PositionMetrics(
        label=position.label,
        shares=position.shares,
        avg_entry_price=position.avg_entry_price,
        current_price=current_price,
        current_value=current_value,
        cost_basis=cost_basis,
        unrealized_pnl=unrealized_pnl,
        unrealized_pnl_pct=unrealized_pnl_pct,
        implied_btc_exposure=implied_btc_exposure,
        btc_per_share=btc_per_share
    )
