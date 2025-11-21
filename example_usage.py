#!/usr/bin/env python3
"""Example usage of MSTR Bitcoin Tracker."""

from src.scraper import HoldingsScraper, PriceScraper
from src.calculator import MetricsCalculator
from src.simulator import MonteCarloSimulator
from src.database import DatabaseOperations

def example_basic_usage():
    """Example of basic usage."""
    print("=" * 60)
    print("MSTR Bitcoin Tracker - Example Usage")
    print("=" * 60)
    
    # Initialize scrapers
    holdings_scraper = HoldingsScraper()
    price_scraper = PriceScraper()
    
    try:
        # Fetch data
        print("\n1. Fetching holdings data...")
        holdings_data = holdings_scraper.fetch_latest()
        print(f"   BTC Holdings: {holdings_data['btc_holdings']:,.2f} BTC")
        print(f"   Avg Cost Basis: ${holdings_data['avg_cost_basis']:,.2f}")
        
        print("\n2. Fetching price data...")
        price_data = price_scraper.fetch_latest_prices()
        print(f"   BTC Price: ${price_data['btc_price_usd']:,.2f}")
        print(f"   MSTR Price: ${price_data['mstr_price_usd']:,.2f}")
        
        # Calculate metrics
        print("\n3. Calculating metrics...")
        metrics = MetricsCalculator.calculate(
            btc_holdings=holdings_data["btc_holdings"],
            avg_cost_basis=holdings_data["avg_cost_basis"],
            current_btc_price=price_data["btc_price_usd"],
            mstr_price=price_data["mstr_price_usd"],
            mstr_market_cap=price_data.get("mstr_market_cap_usd"),
            mstr_shares_outstanding=price_data.get("mstr_shares_outstanding")
        )
        
        print(f"   Current Holdings Value: ${metrics.current_holdings_value:,.2f}")
        print(f"   Unrealized Gain/Loss: ${metrics.unrealized_gain_loss:,.2f} ({metrics.unrealized_gain_loss_pct:+.2f}%)")
        if metrics.nav_ratio:
            print(f"   NAV Ratio: {metrics.nav_ratio:.4f}")
            if metrics.premium_discount:
                print(f"   Premium/Discount: {metrics.premium_discount:+.2f}%")
        
        # Store in database
        print("\n4. Storing data in database...")
        db = DatabaseOperations()
        try:
            db.add_holdings_record(
                btc_holdings=holdings_data["btc_holdings"],
                avg_cost_basis=holdings_data["avg_cost_basis"],
                total_cost=holdings_data.get("total_cost", metrics.total_cost),
                source=holdings_data.get("source")
            )
            db.add_price_record(
                btc_price_usd=price_data["btc_price_usd"],
                mstr_price_usd=price_data["mstr_price_usd"],
                mstr_market_cap_usd=price_data.get("mstr_market_cap_usd"),
                mstr_shares_outstanding=price_data.get("mstr_shares_outstanding")
            )
            print("   ✓ Data stored successfully")
        finally:
            db.close()
        
        # Run simulation
        print("\n5. Running price simulation...")
        simulator = MonteCarloSimulator(annual_volatility=0.80, annual_drift=0.20)
        results = simulator.simulate_with_holdings(
            initial_price=price_data["btc_price_usd"],
            btc_holdings=holdings_data["btc_holdings"],
            avg_cost_basis=holdings_data["avg_cost_basis"],
            days=30,
            scenarios=1000
        )
        
        sim = results["simulation"]
        holdings = results["holdings_analysis"]
        
        print(f"   Initial Price: ${sim.initial_price:,.2f}")
        print(f"   Mean Price (30 days): ${sim.mean_price:,.2f}")
        print(f"   Median Price: ${sim.median_price:,.2f}")
        print(f"   5th Percentile: ${sim.percentile_5:,.2f}")
        print(f"   95th Percentile: ${sim.percentile_95:,.2f}")
        print(f"\n   Holdings Value at Mean: ${holdings['mean_value']:,.2f}")
        print(f"   Mean Gain/Loss: ${holdings['mean_gain_loss']:,.2f}")
        
        print("\n" + "=" * 60)
        print("Example completed successfully!")
        print("=" * 60)
        
    finally:
        holdings_scraper.close()
        price_scraper.close()


if __name__ == "__main__":
    example_basic_usage()

