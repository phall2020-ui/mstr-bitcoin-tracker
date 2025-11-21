"""Scenario definitions for simulations."""

from dataclasses import dataclass
from typing import Dict
import json


@dataclass
class ScenarioConfig:
    """Configuration for a simulation scenario."""
    name: str
    description: str
    btc_mu: float  # Annual drift
    btc_sigma: float  # Annual volatility
    mstr_beta: float  # Beta vs BTC
    mstr_alpha: float  # Alpha (excess return)
    mstr_residual_sigma: float  # Idiosyncratic volatility
    horizon_days: int
    num_paths: int


# Pre-defined scenario configurations
SCENARIOS: Dict[str, ScenarioConfig] = {
    "bear": ScenarioConfig(
        name="bear",
        description="Bear market: Negative returns, high volatility",
        btc_mu=-0.30,  # -30% annual return
        btc_sigma=1.00,  # 100% volatility
        mstr_beta=1.8,  # High beta in downturn
        mstr_alpha=-0.05,  # Slight underperformance
        mstr_residual_sigma=0.40,
        horizon_days=365,
        num_paths=5000
    ),
    "base": ScenarioConfig(
        name="base",
        description="Base case: Moderate growth, typical volatility",
        btc_mu=0.20,  # 20% annual return
        btc_sigma=0.80,  # 80% volatility
        mstr_beta=1.5,  # Typical beta
        mstr_alpha=0.0,  # No alpha
        mstr_residual_sigma=0.30,
        horizon_days=365,
        num_paths=5000
    ),
    "bull": ScenarioConfig(
        name="bull",
        description="Bull market: Strong returns, moderate volatility",
        btc_mu=0.60,  # 60% annual return
        btc_sigma=0.70,  # 70% volatility (lower in bull)
        mstr_beta=1.7,  # Higher beta in uptrend
        mstr_alpha=0.10,  # Positive alpha
        mstr_residual_sigma=0.35,
        horizon_days=365,
        num_paths=5000
    ),
    "hyper": ScenarioConfig(
        name="hyper",
        description="Hyper bull: Extreme growth, increasing volatility",
        btc_mu=1.50,  # 150% annual return
        btc_sigma=1.20,  # 120% volatility
        mstr_beta=2.0,  # Very high beta
        mstr_alpha=0.20,  # Strong alpha
        mstr_residual_sigma=0.50,
        horizon_days=365,
        num_paths=5000
    )
}


def get_scenario(name: str) -> ScenarioConfig:
    """
    Get a pre-defined scenario by name.
    
    Args:
        name: Scenario name ('bear', 'base', 'bull', 'hyper')
        
    Returns:
        ScenarioConfig
        
    Raises:
        ValueError: If scenario name not found
    """
    if name.lower() not in SCENARIOS:
        raise ValueError(
            f"Unknown scenario '{name}'. Available: {list(SCENARIOS.keys())}"
        )
    
    return SCENARIOS[name.lower()]


def scenario_to_json(scenario: ScenarioConfig) -> str:
    """Convert scenario config to JSON string."""
    return json.dumps({
        "name": scenario.name,
        "description": scenario.description,
        "btc_mu": scenario.btc_mu,
        "btc_sigma": scenario.btc_sigma,
        "mstr_beta": scenario.mstr_beta,
        "mstr_alpha": scenario.mstr_alpha,
        "mstr_residual_sigma": scenario.mstr_residual_sigma,
        "horizon_days": scenario.horizon_days,
        "num_paths": scenario.num_paths
    })


def scenario_from_json(json_str: str) -> ScenarioConfig:
    """Create scenario config from JSON string."""
    data = json.loads(json_str)
    return ScenarioConfig(**data)


def create_custom_scenario(
    name: str,
    description: str,
    btc_mu: float,
    btc_sigma: float,
    mstr_beta: float = 1.5,
    mstr_alpha: float = 0.0,
    mstr_residual_sigma: float = 0.30,
    horizon_days: int = 365,
    num_paths: int = 5000
) -> ScenarioConfig:
    """
    Create a custom scenario configuration.
    
    Args:
        name: Scenario name
        description: Scenario description
        btc_mu: BTC annual drift (e.g., 0.20 for 20%)
        btc_sigma: BTC annual volatility (e.g., 0.80 for 80%)
        mstr_beta: MSTR beta vs BTC
        mstr_alpha: MSTR alpha (excess return)
        mstr_residual_sigma: MSTR idiosyncratic volatility
        horizon_days: Simulation horizon in days
        num_paths: Number of simulation paths
        
    Returns:
        ScenarioConfig
    """
    return ScenarioConfig(
        name=name,
        description=description,
        btc_mu=btc_mu,
        btc_sigma=btc_sigma,
        mstr_beta=mstr_beta,
        mstr_alpha=mstr_alpha,
        mstr_residual_sigma=mstr_residual_sigma,
        horizon_days=horizon_days,
        num_paths=num_paths
    )
