"""Database operations for storing and retrieving historical records."""

from datetime import datetime, timedelta
from typing import List, Optional
from sqlalchemy import desc
from sqlalchemy.orm import Session
from .models import (
    SessionLocal, HoldingsRecord, PriceRecord, SimulationRecord, init_database
)


class DatabaseOperations:
    """Operations for database interactions."""
    
    def __init__(self):
        """Initialize database operations."""
        init_database()
        self.session = SessionLocal()
    
    def close(self):
        """Close the database session."""
        self.session.close()
    
    def add_holdings_record(
        self,
        btc_holdings: float,
        avg_cost_basis: float,
        total_cost: float,
        source: Optional[str] = None,
        notes: Optional[str] = None,
        timestamp: Optional[datetime] = None
    ) -> HoldingsRecord:
        """Add a new holdings record."""
        record = HoldingsRecord(
            timestamp=timestamp or datetime.utcnow(),
            btc_holdings=btc_holdings,
            avg_cost_basis=avg_cost_basis,
            total_cost=total_cost,
            source=source,
            notes=notes
        )
        self.session.add(record)
        self.session.commit()
        self.session.refresh(record)
        return record
    
    def add_price_record(
        self,
        btc_price_usd: float,
        mstr_price_usd: float,
        mstr_market_cap_usd: Optional[float] = None,
        mstr_shares_outstanding: Optional[float] = None,
        timestamp: Optional[datetime] = None
    ) -> PriceRecord:
        """Add a new price record."""
        record = PriceRecord(
            timestamp=timestamp or datetime.utcnow(),
            btc_price_usd=btc_price_usd,
            mstr_price_usd=mstr_price_usd,
            mstr_market_cap_usd=mstr_market_cap_usd,
            mstr_shares_outstanding=mstr_shares_outstanding
        )
        self.session.add(record)
        self.session.commit()
        self.session.refresh(record)
        return record
    
    def add_simulation_record(
        self,
        simulation_type: str,
        scenarios: int,
        days: int,
        initial_btc_price: float,
        mean_price: float,
        median_price: float,
        std_price: float,
        min_price: float,
        max_price: float,
        percentile_5: float,
        percentile_95: float,
        results_json: Optional[str] = None
    ) -> SimulationRecord:
        """Add a simulation record."""
        record = SimulationRecord(
            timestamp=datetime.utcnow(),
            simulation_type=simulation_type,
            scenarios=scenarios,
            days=days,
            initial_btc_price=initial_btc_price,
            mean_price=mean_price,
            median_price=median_price,
            std_price=std_price,
            min_price=min_price,
            max_price=max_price,
            percentile_5=percentile_5,
            percentile_95=percentile_95,
            results_json=results_json
        )
        self.session.add(record)
        self.session.commit()
        self.session.refresh(record)
        return record
    
    def get_latest_holdings(self) -> Optional[HoldingsRecord]:
        """Get the most recent holdings record."""
        return self.session.query(HoldingsRecord).order_by(
            desc(HoldingsRecord.timestamp)
        ).first()
    
    def get_latest_price(self) -> Optional[PriceRecord]:
        """Get the most recent price record."""
        return self.session.query(PriceRecord).order_by(
            desc(PriceRecord.timestamp)
        ).first()
    
    def get_holdings_history(
        self,
        days: Optional[int] = None,
        limit: Optional[int] = None
    ) -> List[HoldingsRecord]:
        """Get holdings history."""
        query = self.session.query(HoldingsRecord)
        
        if days:
            cutoff = datetime.utcnow() - timedelta(days=days)
            query = query.filter(HoldingsRecord.timestamp >= cutoff)
        
        query = query.order_by(desc(HoldingsRecord.timestamp))
        
        if limit:
            query = query.limit(limit)
        
        return query.all()
    
    def get_price_history(
        self,
        days: Optional[int] = None,
        limit: Optional[int] = None
    ) -> List[PriceRecord]:
        """Get price history."""
        query = self.session.query(PriceRecord)
        
        if days:
            cutoff = datetime.utcnow() - timedelta(days=days)
            query = query.filter(PriceRecord.timestamp >= cutoff)
        
        query = query.order_by(desc(PriceRecord.timestamp))
        
        if limit:
            query = query.limit(limit)
        
        return query.all()

