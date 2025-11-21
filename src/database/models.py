"""Database models for historical records."""

from datetime import datetime
from sqlalchemy import (
    Column, Integer, Float, DateTime, String, Date, Boolean, 
    ForeignKey, UniqueConstraint, create_engine, Text
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from src.config import settings

Base = declarative_base()


# Legacy tables (kept for backward compatibility)
class HoldingsRecord(Base):
    """Record of MicroStrategy's BTC holdings at a point in time (legacy)."""
    
    __tablename__ = "holdings_records"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    btc_holdings = Column(Float, nullable=False)
    avg_cost_basis = Column(Float, nullable=False)
    total_cost = Column(Float, nullable=False)
    source = Column(String(100), nullable=True)
    notes = Column(String(500), nullable=True)


class PriceRecord(Base):
    """Record of BTC and MSTR prices at a point in time (legacy)."""
    
    __tablename__ = "price_records"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    btc_price_usd = Column(Float, nullable=False)
    mstr_price_usd = Column(Float, nullable=False)
    mstr_market_cap_usd = Column(Float, nullable=True)
    mstr_shares_outstanding = Column(Float, nullable=True)


class SimulationRecord(Base):
    """Record of price simulation results (legacy)."""
    
    __tablename__ = "simulation_records"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    simulation_type = Column(String(50), nullable=False)
    scenarios = Column(Integer, nullable=False)
    days = Column(Integer, nullable=False)
    initial_btc_price = Column(Float, nullable=False)
    mean_price = Column(Float, nullable=False)
    median_price = Column(Float, nullable=False)
    std_price = Column(Float, nullable=False)
    min_price = Column(Float, nullable=False)
    max_price = Column(Float, nullable=False)
    percentile_5 = Column(Float, nullable=False)
    percentile_95 = Column(Float, nullable=False)
    results_json = Column(String, nullable=True)


# Enhanced schema - New tables
class HoldingsTranche(Base):
    """Tranche-by-tranche BTC acquisition records."""
    
    __tablename__ = "holdings_tranche"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    as_of_date = Column(Date, nullable=False, index=True)
    btc_acquired = Column(Float, nullable=False)
    usd_spent = Column(Float, nullable=False)
    source_type = Column(String(100), nullable=False)  # e.g., "convertible_notes", "equity_raise", "atm", "cash"
    implied_btc_price = Column(Float, nullable=False)
    notes = Column(Text, nullable=True)


class CompanyStats(Base):
    """Company statistics (shares, cash, debt)."""
    
    __tablename__ = "company_stats"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    as_of_date = Column(Date, nullable=False, unique=True, index=True)
    shares_outstanding = Column(Float, nullable=False)
    cash_usd = Column(Float, nullable=True)
    debt_usd_face = Column(Float, nullable=True)
    debt_usd_market = Column(Float, nullable=True)


class MarketPrice(Base):
    """Unified market price records for all assets."""
    
    __tablename__ = "market_price"
    __table_args__ = (
        UniqueConstraint('as_of_date', 'asset', name='_date_asset_uc'),
    )
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    as_of_date = Column(Date, nullable=False, index=True)
    asset = Column(String(20), nullable=False, index=True)  # 'BTC', 'MSTR', 'SPX', etc.
    close_price = Column(Float, nullable=False)
    currency = Column(String(10), nullable=False, default='USD')


class DailySnapshot(Base):
    """Daily snapshot of computed metrics."""
    
    __tablename__ = "daily_snapshot"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    as_of_date = Column(Date, nullable=False, unique=True, index=True)
    total_btc = Column(Float, nullable=False)
    btc_spot_price = Column(Float, nullable=False)
    mstr_share_price = Column(Float, nullable=False)
    market_cap_usd = Column(Float, nullable=False)
    btc_nav_usd = Column(Float, nullable=False)
    bs_nav_usd = Column(Float, nullable=True)  # balance sheet NAV (btc + cash - debt)
    btc_per_share = Column(Float, nullable=True)
    bs_nav_per_share = Column(Float, nullable=True)
    premium_to_btc_nav = Column(Float, nullable=True)
    premium_to_bs_nav = Column(Float, nullable=True)


class UserPosition(Base):
    """User's personal MSTR position."""
    
    __tablename__ = "user_position"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    label = Column(String(100), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    is_active = Column(Boolean, nullable=False, default=True)
    shares = Column(Float, nullable=False)
    avg_entry_price = Column(Float, nullable=False)


class ScenarioDefinition(Base):
    """Simulation scenario definitions."""
    
    __tablename__ = "scenario_definition"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), nullable=False, unique=True, index=True)
    description = Column(Text, nullable=True)
    config_json = Column(Text, nullable=False)


class SimulationRun(Base):
    """Enhanced simulation run records."""
    
    __tablename__ = "simulation_run"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    scenario_id = Column(Integer, ForeignKey('scenario_definition.id'), nullable=True)
    horizon_days = Column(Integer, nullable=False)
    num_paths = Column(Integer, nullable=False)
    seed = Column(Integer, nullable=True)
    input_snapshot_date = Column(Date, nullable=False)
    results_summary_json = Column(Text, nullable=False)


# Create engine and session factory
engine = create_engine(f"sqlite:///{settings.database_path}", echo=False)
SessionLocal = sessionmaker(bind=engine)


def init_database():
    """Initialize the database by creating all tables."""
    Base.metadata.create_all(engine)

