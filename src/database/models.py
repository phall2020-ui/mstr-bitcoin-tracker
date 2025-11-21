"""Database models for historical records."""

from datetime import datetime
from sqlalchemy import Column, Integer, Float, DateTime, String, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from src.config import settings

Base = declarative_base()


class HoldingsRecord(Base):
    """Record of MicroStrategy's BTC holdings at a point in time."""
    
    __tablename__ = "holdings_records"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    btc_holdings = Column(Float, nullable=False)
    avg_cost_basis = Column(Float, nullable=False)
    total_cost = Column(Float, nullable=False)
    source = Column(String(100), nullable=True)
    notes = Column(String(500), nullable=True)


class PriceRecord(Base):
    """Record of BTC and MSTR prices at a point in time."""
    
    __tablename__ = "price_records"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    btc_price_usd = Column(Float, nullable=False)
    mstr_price_usd = Column(Float, nullable=False)
    mstr_market_cap_usd = Column(Float, nullable=True)
    mstr_shares_outstanding = Column(Float, nullable=True)


class SimulationRecord(Base):
    """Record of price simulation results."""
    
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
    results_json = Column(String, nullable=True)  # Store full results as JSON


# Create engine and session factory
engine = create_engine(f"sqlite:///{settings.database_path}", echo=False)
SessionLocal = sessionmaker(bind=engine)


def init_database():
    """Initialize the database by creating all tables."""
    Base.metadata.create_all(engine)

