"""Enhanced REST API for MSTR Bitcoin Tracker."""

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime, date
import json

from src.database.session import get_db_session
from src.analytics import nav, tranches, position
from src.simulation import mc_paths, scenarios, risk
from src.database.models import SimulationRun

app = FastAPI(
    title="MSTR Bitcoin Tracker API",
    description="Enhanced API for comprehensive MicroStrategy Bitcoin tracking and analytics",
    version="2.0.0"
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
class SummaryResponse(BaseModel):
    """Summary of today's metrics."""
    date: str
    total_btc: float
    btc_spot: float
    mstr_price: float
    market_cap: float
    btc_per_share: Optional[float]
    btc_nav_per_share: Optional[float]
    bs_nav_per_share: Optional[float]
    premium_to_btc_nav: Optional[float]
    premium_to_bs_nav: Optional[float]


class NAVResponse(BaseModel):
    """NAV metrics response."""
    date: str
    total_btc: float
    btc_spot_price: float
    mstr_share_price: float
    market_cap_usd: float
    btc_nav_usd: float
    bs_nav_usd: Optional[float]
    btc_per_share: Optional[float]
    bs_nav_per_share: Optional[float]
    premium_to_btc_nav: Optional[float]
    premium_to_bs_nav: Optional[float]
    shares_outstanding: Optional[float]
    cash_usd: Optional[float]
    debt_usd_market: Optional[float]


class TrancheDetail(BaseModel):
    """Single tranche details."""
    id: int
    as_of_date: str
    btc_acquired: float
    usd_spent: float
    source_type: str
    implied_btc_price: float
    current_market_value: float
    unrealized_pnl_abs: float
    unrealized_pnl_pct: float
    age_days: int


class TranchesResponse(BaseModel):
    """Tranches summary response."""
    date: str
    tranches: List[TrancheDetail]
    portfolio_summary: Dict[str, float]


class PositionResponse(BaseModel):
    """Personal position response."""
    label: str
    shares: float
    avg_entry_price: float
    current_price: float
    current_value: float
    unrealized_pnl: float
    unrealized_pnl_pct: float
    implied_btc_exposure: Optional[float]


class SimulateRequest(BaseModel):
    """Simulation request."""
    scenario_name: Optional[str] = "base"
    horizon_days: Optional[int] = None
    num_paths: Optional[int] = None


class SimulateResponse(BaseModel):
    """Simulation response."""
    run_id: int
    scenario_name: str
    horizon_days: int
    num_paths: int
    btc_risk: Dict[str, Any]
    mstr_risk: Dict[str, Any]
    portfolio_risk: Optional[Dict[str, Any]]


@app.get("/")
def root():
    """Root endpoint."""
    return {
        "name": "MSTR Bitcoin Tracker API",
        "version": "2.0.0",
        "docs": "/docs"
    }


@app.get("/api/v1/health")
def health():
    """Health check endpoint."""
    return {"status": "healthy", "timestamp": datetime.utcnow()}


@app.get("/api/v1/summary/today", response_model=SummaryResponse)
def get_summary_today():
    """Get high-level summary for today."""
    with get_db_session() as session:
        nav_metrics = nav.compute_nav_metrics(session, date.today())
        
        if not nav_metrics:
            raise HTTPException(status_code=404, detail="No data available for today")
        
        btc_nav_per_share = None
        if nav_metrics.shares_outstanding and nav_metrics.shares_outstanding > 0:
            btc_nav_per_share = nav_metrics.btc_nav_usd / nav_metrics.shares_outstanding
        
        return SummaryResponse(
            date=date.today().isoformat(),
            total_btc=nav_metrics.total_btc,
            btc_spot=nav_metrics.btc_spot_price,
            mstr_price=nav_metrics.mstr_share_price,
            market_cap=nav_metrics.market_cap_usd,
            btc_per_share=nav_metrics.btc_per_share,
            btc_nav_per_share=btc_nav_per_share,
            bs_nav_per_share=nav_metrics.bs_nav_per_share,
            premium_to_btc_nav=nav_metrics.premium_to_btc_nav,
            premium_to_bs_nav=nav_metrics.premium_to_bs_nav
        )


@app.get("/api/v1/nav", response_model=NAVResponse)
def get_nav(
    date_param: Optional[str] = Query(None, alias="date", description="Date in YYYY-MM-DD format")
):
    """Get NAV metrics for a specific date."""
    query_date = date.today()
    if date_param:
        try:
            query_date = datetime.strptime(date_param, "%Y-%m-%d").date()
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
    
    with get_db_session() as session:
        nav_metrics = nav.compute_nav_metrics(session, query_date)
        
        if not nav_metrics:
            raise HTTPException(status_code=404, detail=f"No data available for {query_date}")
        
        return NAVResponse(
            date=query_date.isoformat(),
            total_btc=nav_metrics.total_btc,
            btc_spot_price=nav_metrics.btc_spot_price,
            mstr_share_price=nav_metrics.mstr_share_price,
            market_cap_usd=nav_metrics.market_cap_usd,
            btc_nav_usd=nav_metrics.btc_nav_usd,
            bs_nav_usd=nav_metrics.bs_nav_usd,
            btc_per_share=nav_metrics.btc_per_share,
            bs_nav_per_share=nav_metrics.bs_nav_per_share,
            premium_to_btc_nav=nav_metrics.premium_to_btc_nav,
            premium_to_bs_nav=nav_metrics.premium_to_bs_nav,
            shares_outstanding=nav_metrics.shares_outstanding,
            cash_usd=nav_metrics.cash_usd,
            debt_usd_market=nav_metrics.debt_usd_market
        )


@app.get("/api/v1/tranches", response_model=TranchesResponse)
def get_tranches(
    date_param: Optional[str] = Query(None, alias="date", description="Date in YYYY-MM-DD format")
):
    """Get tranche-level summary."""
    query_date = date.today()
    if date_param:
        try:
            query_date = datetime.strptime(date_param, "%Y-%m-%d").date()
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
    
    with get_db_session() as session:
        tranche_analysis = tranches.get_tranche_summary(session, query_date)
        
        if not tranche_analysis:
            raise HTTPException(status_code=404, detail=f"No tranches data for {query_date}")
        
        tranche_details = [
            TrancheDetail(
                id=t.id,
                as_of_date=t.as_of_date.isoformat(),
                btc_acquired=t.btc_acquired,
                usd_spent=t.usd_spent,
                source_type=t.source_type,
                implied_btc_price=t.implied_btc_price,
                current_market_value=t.current_market_value,
                unrealized_pnl_abs=t.unrealized_pnl_abs,
                unrealized_pnl_pct=t.unrealized_pnl_pct,
                age_days=t.age_days
            )
            for t in tranche_analysis.tranches
        ]
        
        portfolio_summary = {
            "total_btc": tranche_analysis.portfolio.total_btc,
            "total_cost": tranche_analysis.portfolio.total_cost,
            "total_current_value": tranche_analysis.portfolio.total_current_value,
            "total_unrealized_pnl": tranche_analysis.portfolio.total_unrealized_pnl,
            "total_unrealized_pnl_pct": tranche_analysis.portfolio.total_unrealized_pnl_pct,
            "weighted_avg_cost": tranche_analysis.portfolio.weighted_avg_cost,
            "tranches_count": tranche_analysis.portfolio.tranches_count
        }
        
        return TranchesResponse(
            date=query_date.isoformat(),
            tranches=tranche_details,
            portfolio_summary=portfolio_summary
        )


@app.get("/api/v1/my-position", response_model=PositionResponse)
def get_my_position():
    """Get personal position metrics."""
    with get_db_session() as session:
        pos_metrics = position.compute_position_metrics(session)
        
        if not pos_metrics:
            raise HTTPException(status_code=404, detail="No active position found")
        
        return PositionResponse(
            label=pos_metrics.label,
            shares=pos_metrics.shares,
            avg_entry_price=pos_metrics.avg_entry_price,
            current_price=pos_metrics.current_price,
            current_value=pos_metrics.current_value,
            unrealized_pnl=pos_metrics.unrealized_pnl,
            unrealized_pnl_pct=pos_metrics.unrealized_pnl_pct,
            implied_btc_exposure=pos_metrics.implied_btc_exposure
        )


@app.post("/api/v1/simulate", response_model=SimulateResponse)
def simulate(request: SimulateRequest):
    """Run simulation with specified scenario."""
    # Get scenario config
    try:
        scenario_config = scenarios.get_scenario(request.scenario_name or "base")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    # Override if provided
    if request.horizon_days:
        scenario_config.horizon_days = request.horizon_days
    if request.num_paths:
        scenario_config.num_paths = request.num_paths
    
    with get_db_session() as session:
        # Get current metrics
        nav_metrics = nav.compute_nav_metrics(session, date.today())
        if not nav_metrics:
            raise HTTPException(status_code=404, detail="Insufficient data for simulation")
        
        # Run simulation
        sim_paths = mc_paths.simulate_joint_btc_mstr_paths(
            initial_btc_price=nav_metrics.btc_spot_price,
            initial_mstr_price=nav_metrics.mstr_share_price,
            horizon_days=scenario_config.horizon_days,
            num_paths=scenario_config.num_paths,
            btc_mu=scenario_config.btc_mu,
            btc_sigma=scenario_config.btc_sigma,
            beta=scenario_config.mstr_beta,
            alpha=scenario_config.mstr_alpha,
            residual_sigma=scenario_config.mstr_residual_sigma
        )
        
        # Compute risk metrics
        btc_final = sim_paths.btc_paths[:, -1]
        mstr_final = sim_paths.mstr_paths[:, -1]
        
        btc_risk = risk.compute_risk_metrics(btc_final, nav_metrics.btc_spot_price)
        mstr_risk = risk.compute_risk_metrics(mstr_final, nav_metrics.mstr_share_price)
        
        # Get personal position if exists
        pos_metrics = position.compute_position_metrics(session)
        portfolio_risk_metrics = None
        if pos_metrics:
            portfolio_risk_metrics = risk.compute_portfolio_risk(
                btc_final, mstr_final,
                nav_metrics.btc_spot_price, nav_metrics.mstr_share_price,
                pos_metrics.shares
            )
        
        # Store simulation run
        risk_summary = risk.create_risk_summary(btc_risk, mstr_risk, portfolio_risk_metrics)
        
        sim_run = SimulationRun(
            created_at=datetime.utcnow(),
            scenario_id=None,
            horizon_days=scenario_config.horizon_days,
            num_paths=scenario_config.num_paths,
            seed=None,
            input_snapshot_date=date.today(),
            results_summary_json=json.dumps(risk_summary)
        )
        session.add(sim_run)
        session.flush()
        
        run_id = sim_run.id
        
        # Format response
        btc_risk_dict = {
            "var_95": btc_risk.var_95,
            "cvar_95": btc_risk.cvar_95,
            "var_99": btc_risk.var_99,
            "cvar_99": btc_risk.cvar_99,
            "mean_return": btc_risk.mean_return,
            "median_return": btc_risk.median_return,
            "std_return": btc_risk.std_return,
            "percentiles": btc_risk.percentiles
        }
        
        mstr_risk_dict = {
            "var_95": mstr_risk.var_95,
            "cvar_95": mstr_risk.cvar_95,
            "var_99": mstr_risk.var_99,
            "cvar_99": mstr_risk.cvar_99,
            "mean_return": mstr_risk.mean_return,
            "median_return": mstr_risk.median_return,
            "std_return": mstr_risk.std_return,
            "percentiles": mstr_risk.percentiles
        }
        
        portfolio_risk_dict = None
        if portfolio_risk_metrics:
            portfolio_risk_dict = {
                "var_95": portfolio_risk_metrics.var_95,
                "cvar_95": portfolio_risk_metrics.cvar_95,
                "var_99": portfolio_risk_metrics.var_99,
                "cvar_99": portfolio_risk_metrics.cvar_99,
                "mean_return": portfolio_risk_metrics.mean_return,
                "median_return": portfolio_risk_metrics.median_return,
                "std_return": portfolio_risk_metrics.std_return,
                "percentiles": portfolio_risk_metrics.percentiles
            }
        
        return SimulateResponse(
            run_id=run_id,
            scenario_name=scenario_config.name,
            horizon_days=scenario_config.horizon_days,
            num_paths=scenario_config.num_paths,
            btc_risk=btc_risk_dict,
            mstr_risk=mstr_risk_dict,
            portfolio_risk=portfolio_risk_dict
        )


@app.get("/api/v1/simulate/{run_id}")
def get_simulation_run(run_id: int):
    """Get stored simulation run results."""
    with get_db_session() as session:
        sim_run = session.query(SimulationRun).filter(SimulationRun.id == run_id).first()
        
        if not sim_run:
            raise HTTPException(status_code=404, detail=f"Simulation run {run_id} not found")
        
        results = json.loads(sim_run.results_summary_json)
        
        return {
            "run_id": sim_run.id,
            "created_at": sim_run.created_at.isoformat(),
            "horizon_days": sim_run.horizon_days,
            "num_paths": sim_run.num_paths,
            "input_snapshot_date": sim_run.input_snapshot_date.isoformat(),
            "results": results
        }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
