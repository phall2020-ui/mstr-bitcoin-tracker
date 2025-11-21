"""Monte Carlo simulation for Bitcoin price scenarios."""

import numpy as np
from typing import Dict, List
from dataclasses import dataclass


@dataclass
class SimulationResults:
    """Results from a Monte Carlo simulation."""
    
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
    price_paths: List[List[float]]  # Sample paths for visualization


class MonteCarloSimulator:
    """Monte Carlo simulator for Bitcoin price forecasting."""
    
    def __init__(
        self,
        annual_volatility: float = 0.80,  # ~80% annual volatility for BTC
        annual_drift: float = 0.20  # ~20% annual drift (can be adjusted)
    ):
        """
        Initialize the simulator.
        
        Args:
            annual_volatility: Annual volatility (default ~80% for BTC)
            annual_drift: Annual drift/expected return (default ~20%)
        """
        self.annual_volatility = annual_volatility
        self.annual_drift = annual_drift
    
    def simulate(
        self,
        initial_price: float,
        days: int,
        scenarios: int = 1000,
        return_paths: bool = False
    ) -> SimulationResults:
        """
        Run Monte Carlo simulation.
        
        Args:
            initial_price: Starting BTC price
            days: Number of days to simulate
            scenarios: Number of simulation scenarios
            return_paths: Whether to return sample price paths
        
        Returns:
            SimulationResults with statistics
        """
        # Convert annual parameters to daily
        dt = 1 / 365.0  # One day
        daily_drift = self.annual_drift * dt
        daily_volatility = self.annual_volatility * np.sqrt(dt)
        
        # Generate random shocks
        random_shocks = np.random.normal(0, 1, (scenarios, days))
        
        # Simulate price paths using geometric Brownian motion
        price_paths = np.zeros((scenarios, days + 1))
        price_paths[:, 0] = initial_price
        
        for day in range(1, days + 1):
            # GBM: S(t+1) = S(t) * exp((mu - 0.5*sigma^2)*dt + sigma*dW)
            price_paths[:, day] = price_paths[:, day - 1] * np.exp(
                (daily_drift - 0.5 * daily_volatility**2) * dt +
                daily_volatility * random_shocks[:, day - 1]
            )
        
        # Extract final prices
        final_prices = price_paths[:, -1]
        
        # Calculate statistics
        mean_price = np.mean(final_prices)
        median_price = np.median(final_prices)
        std_price = np.std(final_prices)
        min_price = np.min(final_prices)
        max_price = np.max(final_prices)
        
        percentiles = np.percentile(final_prices, [5, 25, 75, 95])
        
        # Sample paths for visualization (return first 10)
        sample_paths = []
        if return_paths:
            sample_paths = price_paths[:min(10, scenarios)].tolist()
        
        return SimulationResults(
            initial_price=initial_price,
            scenarios=scenarios,
            days=days,
            mean_price=float(mean_price),
            median_price=float(median_price),
            std_price=float(std_price),
            min_price=float(min_price),
            max_price=float(max_price),
            percentile_5=float(percentiles[0]),
            percentile_25=float(percentiles[1]),
            percentile_75=float(percentiles[2]),
            percentile_95=float(percentiles[3]),
            price_paths=sample_paths
        )
    
    def simulate_with_holdings(
        self,
        initial_price: float,
        btc_holdings: float,
        avg_cost_basis: float,
        days: int,
        scenarios: int = 1000
    ) -> Dict:
        """
        Simulate price and calculate impact on holdings value.
        
        Returns:
            Dictionary with simulation results and holdings impact
        """
        results = self.simulate(initial_price, days, scenarios, return_paths=False)
        
        # Calculate holdings value at different price points
        total_cost = btc_holdings * avg_cost_basis
        
        holdings_at_mean = btc_holdings * results.mean_price
        holdings_at_median = btc_holdings * results.median_price
        holdings_at_p5 = btc_holdings * results.percentile_5
        holdings_at_p95 = btc_holdings * results.percentile_95
        
        return {
            "simulation": results,
            "holdings_analysis": {
                "total_cost": total_cost,
                "current_value": btc_holdings * initial_price,
                "mean_value": holdings_at_mean,
                "median_value": holdings_at_median,
                "p5_value": holdings_at_p5,
                "p95_value": holdings_at_p95,
                "mean_gain_loss": holdings_at_mean - total_cost,
                "median_gain_loss": holdings_at_median - total_cost
            }
        }

