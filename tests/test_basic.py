"""Basic tests for MSTR Bitcoin Tracker."""

import pytest
from datetime import date
from src.database.models import init_database, HoldingsTranche, CompanyStats, MarketPrice
from src.database.session import get_db_session
from src.analytics import nav, tranches, position
from src.simulation import mc_paths, scenarios, risk


def test_database_initialization():
    """Test database can be initialized."""
    init_database()
    # Should not raise an error
    assert True


def test_scenario_definitions():
    """Test pre-defined scenarios exist."""
    assert "bear" in scenarios.SCENARIOS
    assert "base" in scenarios.SCENARIOS
    assert "bull" in scenarios.SCENARIOS
    assert "hyper" in scenarios.SCENARIOS
    
    base_scenario = scenarios.get_scenario("base")
    assert base_scenario.name == "base"
    assert base_scenario.horizon_days > 0
    assert base_scenario.num_paths > 0


def test_btc_path_simulation():
    """Test BTC path simulation runs without error."""
    paths = mc_paths.simulate_btc_paths(
        initial_price=50000.0,
        horizon_days=30,
        num_paths=100,
        mu=0.20,
        sigma=0.80,
        seed=42
    )
    
    assert paths.shape == (100, 31)  # 100 paths, 31 time points (0 to 30)
    assert paths[0, 0] == 50000.0  # Initial price
    assert paths[:, 0].mean() == 50000.0  # All paths start at same price


def test_joint_simulation():
    """Test joint BTC/MSTR simulation."""
    sim_paths = mc_paths.simulate_joint_btc_mstr_paths(
        initial_btc_price=50000.0,
        initial_mstr_price=300.0,
        horizon_days=30,
        num_paths=100,
        btc_mu=0.20,
        btc_sigma=0.80,
        beta=1.5,
        alpha=0.0,
        residual_sigma=0.30,
        seed=42
    )
    
    assert sim_paths.btc_paths.shape == (100, 31)
    assert sim_paths.mstr_paths.shape == (100, 31)
    assert sim_paths.btc_paths[0, 0] == 50000.0
    assert sim_paths.mstr_paths[0, 0] == 300.0


def test_risk_metrics_calculation():
    """Test VaR/CVaR calculation."""
    # Simulate some final prices
    import numpy as np
    np.random.seed(42)
    final_prices = np.random.lognormal(mean=10, sigma=0.5, size=1000)
    initial_price = 50000.0
    
    var, cvar = risk.compute_var_cvar(final_prices, initial_price, alpha=0.95)
    
    assert isinstance(var, float)
    assert isinstance(cvar, float)
    assert cvar >= var  # CVaR should be worse than or equal to VaR


def test_risk_metrics_comprehensive():
    """Test comprehensive risk metrics."""
    import numpy as np
    np.random.seed(42)
    final_prices = np.random.lognormal(mean=10, sigma=0.5, size=1000)
    initial_price = 50000.0
    
    risk_metrics = risk.compute_risk_metrics(final_prices, initial_price)
    
    assert hasattr(risk_metrics, 'var_95')
    assert hasattr(risk_metrics, 'cvar_95')
    assert hasattr(risk_metrics, 'mean_return')
    assert hasattr(risk_metrics, 'percentiles')
    assert '50' in risk_metrics.percentiles


def test_nav_calculation_with_sample_data(tmp_path):
    """Test NAV calculation with sample data."""
    # This would require setting up a temporary database
    # For now, just test that the function signature is correct
    from src.analytics.nav import compute_nav_metrics
    assert callable(compute_nav_metrics)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
