"""REST API for MSTR Bitcoin Tracker."""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
import json

from src.scraper import HoldingsScraper, PriceScraper
from src.calculator import MetricsCalculator
from src.simulator import MonteCarloSimulator
from src.database import DatabaseOperations

app = FastAPI(
    title="MSTR Bitcoin Tracker API",
    description="API for tracking MicroStrategy's Bitcoin holdings and metrics",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Pydantic models
class HoldingsResponse(BaseModel):
    btc_holdings: float
    avg_cost_basis: float
    total_cost: float
    source: Optional[str]
    timestamp: datetime


class PriceResponse(BaseModel):
    btc_price_usd: float
    mstr_price_usd: float
    mstr_market_cap_usd: Optional[float]
    mstr_shares_outstanding: Optional[float]
    timestamp: datetime


class MetricsResponse(BaseModel):
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
    premium_discount: Optional[float]


class SimulationRequest(BaseModel):
    scenarios: int = 1000
    days: int = 30
    volatility: float = 0.80
    drift: float = 0.20


class SimulationResponse(BaseModel):
    initial_price: float
    scenarios: int
    days: int
    mean_price: float
    median_price: float
    std_price: float
    min_price: float
    max_price: float
    percentile_5: float
    percentile_25: float
    percentile_75: float
    percentile_95: float
    holdings_analysis: dict


@app.get("/")
def root():
    """Root endpoint."""
    return {
        "name": "MSTR Bitcoin Tracker API",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.get("/api/v1/health")
def health():
    """Health check endpoint."""
    return {"status": "healthy", "timestamp": datetime.utcnow()}


@app.get("/api/v1/holdings", response_model=HoldingsResponse)
def get_holdings():
    """Get current BTC holdings."""
    scraper = HoldingsScraper()
    try:
        data = scraper.fetch_latest()
        return HoldingsResponse(
            btc_holdings=data["btc_holdings"],
            avg_cost_basis=data["avg_cost_basis"],
            total_cost=data.get("total_cost", data["btc_holdings"] * data["avg_cost_basis"]),
            source=data.get("source"),
            timestamp=data.get("timestamp", datetime.utcnow())
        )
    finally:
        scraper.close()


@app.get("/api/v1/prices", response_model=PriceResponse)
def get_prices():
    """Get current BTC and MSTR prices."""
    scraper = PriceScraper()
    try:
        data = scraper.fetch_latest_prices()
        return PriceResponse(**data)
    finally:
        scraper.close()


@app.get("/api/v1/metrics", response_model=MetricsResponse)
def get_metrics():
    """Get calculated metrics."""
    holdings_scraper = HoldingsScraper()
    price_scraper = PriceScraper()
    
    try:
        holdings_data = holdings_scraper.fetch_latest()
        price_data = price_scraper.fetch_latest_prices()
        
        metrics = MetricsCalculator.calculate(
            btc_holdings=holdings_data["btc_holdings"],
            avg_cost_basis=holdings_data["avg_cost_basis"],
            current_btc_price=price_data["btc_price_usd"],
            mstr_price=price_data["mstr_price_usd"],
            mstr_market_cap=price_data.get("mstr_market_cap_usd"),
            mstr_shares_outstanding=price_data.get("mstr_shares_outstanding")
        )
        
        return MetricsResponse(**MetricsCalculator.to_dict(metrics))
    finally:
        holdings_scraper.close()
        price_scraper.close()


@app.post("/api/v1/simulate", response_model=SimulationResponse)
def simulate(request: SimulationRequest):
    """Run price simulation."""
    price_scraper = PriceScraper()
    holdings_scraper = HoldingsScraper()
    
    try:
        price_data = price_scraper.fetch_latest_prices()
        holdings_data = holdings_scraper.fetch_latest()
        
        initial_price = price_data["btc_price_usd"]
        
        if initial_price == 0:
            raise HTTPException(status_code=500, detail="Could not fetch BTC price")
        
        simulator = MonteCarloSimulator(
            annual_volatility=request.volatility,
            annual_drift=request.drift
        )
        
        results = simulator.simulate_with_holdings(
            initial_price=initial_price,
            btc_holdings=holdings_data["btc_holdings"],
            avg_cost_basis=holdings_data["avg_cost_basis"],
            days=request.days,
            scenarios=request.scenarios
        )
        
        sim = results["simulation"]
        
        # Store in database
        db = DatabaseOperations()
        try:
            db.add_simulation_record(
                simulation_type="monte_carlo",
                scenarios=request.scenarios,
                days=request.days,
                initial_btc_price=initial_price,
                mean_price=sim.mean_price,
                median_price=sim.median_price,
                std_price=sim.std_price,
                min_price=sim.min_price,
                max_price=sim.max_price,
                percentile_5=sim.percentile_5,
                percentile_95=sim.percentile_95
            )
        finally:
            db.close()
        
        return SimulationResponse(
            initial_price=sim.initial_price,
            scenarios=sim.scenarios,
            days=sim.days,
            mean_price=sim.mean_price,
            median_price=sim.median_price,
            std_price=sim.std_price,
            min_price=sim.min_price,
            max_price=sim.max_price,
            percentile_5=sim.percentile_5,
            percentile_25=sim.percentile_25,
            percentile_75=sim.percentile_75,
            percentile_95=sim.percentile_95,
            holdings_analysis=results["holdings_analysis"]
        )
    finally:
        price_scraper.close()
        holdings_scraper.close()


@app.get("/api/v1/history/holdings")
def get_holdings_history(days: Optional[int] = 30, limit: Optional[int] = 100):
    """Get holdings history."""
    db = DatabaseOperations()
    try:
        records = db.get_holdings_history(days=days, limit=limit)
        return [
            {
                "id": r.id,
                "timestamp": r.timestamp.isoformat(),
                "btc_holdings": r.btc_holdings,
                "avg_cost_basis": r.avg_cost_basis,
                "total_cost": r.total_cost,
                "source": r.source,
                "notes": r.notes
            }
            for r in records
        ]
    finally:
        db.close()


@app.get("/api/v1/history/prices")
def get_price_history(days: Optional[int] = 30, limit: Optional[int] = 100):
    """Get price history."""
    db = DatabaseOperations()
    try:
        records = db.get_price_history(days=days, limit=limit)
        return [
            {
                "id": r.id,
                "timestamp": r.timestamp.isoformat(),
                "btc_price_usd": r.btc_price_usd,
                "mstr_price_usd": r.mstr_price_usd,
                "mstr_market_cap_usd": r.mstr_market_cap_usd,
                "mstr_shares_outstanding": r.mstr_shares_outstanding
            }
            for r in records
        ]
    finally:
        db.close()


@app.post("/api/v1/fetch")
def fetch_and_store():
    """Fetch latest data and store in database."""
    holdings_scraper = HoldingsScraper()
    price_scraper = PriceScraper()
    
    try:
        holdings_data = holdings_scraper.fetch_latest()
        price_data = price_scraper.fetch_latest_prices()
        
        # Store in database
        db = DatabaseOperations()
        try:
            holdings_record = db.add_holdings_record(
                btc_holdings=holdings_data["btc_holdings"],
                avg_cost_basis=holdings_data["avg_cost_basis"],
                total_cost=holdings_data.get("total_cost", holdings_data["btc_holdings"] * holdings_data["avg_cost_basis"]),
                source=holdings_data.get("source"),
                timestamp=holdings_data.get("timestamp")
            )
            price_record = db.add_price_record(
                btc_price_usd=price_data["btc_price_usd"],
                mstr_price_usd=price_data["mstr_price_usd"],
                mstr_market_cap_usd=price_data.get("mstr_market_cap_usd"),
                mstr_shares_outstanding=price_data.get("mstr_shares_outstanding")
            )
            
            return {
                "status": "success",
                "holdings_record_id": holdings_record.id,
                "price_record_id": price_record.id,
                "timestamp": datetime.utcnow().isoformat()
            }
        finally:
            db.close()
    finally:
        holdings_scraper.close()
        price_scraper.close()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

