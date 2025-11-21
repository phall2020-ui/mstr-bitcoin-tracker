"""CLI interface for MSTR Bitcoin Tracker."""

import click
import json
from datetime import datetime
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box

from src.scraper import HoldingsScraper, PriceScraper
from src.calculator import MetricsCalculator
from src.calculator.metrics import Metrics
from src.simulator import MonteCarloSimulator
from src.database import DatabaseOperations

console = Console()


@click.group()
def cli():
    """MSTR Bitcoin Tracker - Track MicroStrategy's Bitcoin holdings."""
    pass


@cli.command()
def fetch():
    """Fetch latest data and display metrics."""
    console.print("[bold blue]Fetching latest data...[/bold blue]")
    
    # Fetch data
    holdings_scraper = HoldingsScraper()
    price_scraper = PriceScraper()
    
    try:
        holdings_data = holdings_scraper.fetch_latest()
        price_data = price_scraper.fetch_latest_prices()
        
        # Calculate metrics
        metrics = MetricsCalculator.calculate(
            btc_holdings=holdings_data["btc_holdings"],
            avg_cost_basis=holdings_data["avg_cost_basis"],
            current_btc_price=price_data["btc_price_usd"],
            mstr_price=price_data["mstr_price_usd"],
            mstr_market_cap=price_data.get("mstr_market_cap_usd"),
            mstr_shares_outstanding=price_data.get("mstr_shares_outstanding")
        )
        
        # Store in database
        db = DatabaseOperations()
        try:
            db.add_holdings_record(
                btc_holdings=holdings_data["btc_holdings"],
                avg_cost_basis=holdings_data["avg_cost_basis"],
                total_cost=holdings_data.get("total_cost", metrics.total_cost),
                source=holdings_data.get("source"),
                timestamp=holdings_data.get("timestamp")
            )
            db.add_price_record(
                btc_price_usd=price_data["btc_price_usd"],
                mstr_price_usd=price_data["mstr_price_usd"],
                mstr_market_cap_usd=price_data.get("mstr_market_cap_usd"),
                mstr_shares_outstanding=price_data.get("mstr_shares_outstanding")
            )
        finally:
            db.close()
        
        # Display results
        display_metrics(metrics, holdings_data, price_data)
        
    finally:
        holdings_scraper.close()
        price_scraper.close()


@cli.command()
def holdings():
    """Show current BTC holdings."""
    console.print("[bold blue]Fetching holdings data...[/bold blue]")
    
    holdings_scraper = HoldingsScraper()
    try:
        data = holdings_scraper.fetch_latest()
        
        table = Table(title="MicroStrategy BTC Holdings", box=box.ROUNDED)
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green", justify="right")
        
        table.add_row("BTC Holdings", f"{data['btc_holdings']:,.2f} BTC")
        table.add_row("Average Cost Basis", f"${data['avg_cost_basis']:,.2f}")
        table.add_row("Total Cost", f"${data.get('total_cost', data['btc_holdings'] * data['avg_cost_basis']):,.2f}")
        table.add_row("Source", data.get("source", "unknown"))
        
        console.print(table)
    finally:
        holdings_scraper.close()


@cli.command()
def nav():
    """Calculate and display NAV ratio."""
    console.print("[bold blue]Calculating NAV ratio...[/bold blue]")
    
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
        
        table = Table(title="NAV Ratio Analysis", box=box.ROUNDED)
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green", justify="right")
        
        table.add_row("BTC Holdings Value", f"${metrics.current_holdings_value:,.2f}")
        table.add_row("MSTR Market Cap", f"${metrics.mstr_market_cap:,.2f}" if metrics.mstr_market_cap else "N/A")
        table.add_row("NAV Ratio", f"{metrics.nav_ratio:.4f}" if metrics.nav_ratio else "N/A")
        
        if metrics.premium_discount is not None:
            style = "red" if metrics.premium_discount > 0 else "green"
            table.add_row(
                "Premium/Discount",
                f"[{style}]{metrics.premium_discount:+.2f}%[/{style}]"
            )
        
        console.print(table)
        
    finally:
        holdings_scraper.close()
        price_scraper.close()


@cli.command()
@click.option("--scenarios", default=1000, help="Number of simulation scenarios")
@click.option("--days", default=30, help="Number of days to simulate")
@click.option("--volatility", default=0.80, help="Annual volatility (default 0.80)")
@click.option("--drift", default=0.20, help="Annual drift (default 0.20)")
def simulate(scenarios, days, volatility, drift):
    """Run price simulations."""
    console.print(f"[bold blue]Running simulation ({scenarios} scenarios, {days} days)...[/bold blue]")
    
    price_scraper = PriceScraper()
    holdings_scraper = HoldingsScraper()
    
    try:
        price_data = price_scraper.fetch_latest_prices()
        holdings_data = holdings_scraper.fetch_latest()
        
        initial_price = price_data["btc_price_usd"]
        
        if initial_price == 0:
            console.print("[bold red]Error: Could not fetch BTC price[/bold red]")
            return
        
        simulator = MonteCarloSimulator(
            annual_volatility=volatility,
            annual_drift=drift
        )
        
        results = simulator.simulate_with_holdings(
            initial_price=initial_price,
            btc_holdings=holdings_data["btc_holdings"],
            avg_cost_basis=holdings_data["avg_cost_basis"],
            days=days,
            scenarios=scenarios
        )
        
        sim = results["simulation"]
        holdings = results["holdings_analysis"]
        
        # Display simulation results
        table = Table(title=f"Price Simulation Results ({days} days)", box=box.ROUNDED)
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green", justify="right")
        
        table.add_row("Initial BTC Price", f"${sim.initial_price:,.2f}")
        table.add_row("Mean Price", f"${sim.mean_price:,.2f}")
        table.add_row("Median Price", f"${sim.median_price:,.2f}")
        table.add_row("5th Percentile", f"${sim.percentile_5:,.2f}")
        table.add_row("95th Percentile", f"${sim.percentile_95:,.2f}")
        table.add_row("Min Price", f"${sim.min_price:,.2f}")
        table.add_row("Max Price", f"${sim.max_price:,.2f}")
        table.add_row("Std Deviation", f"${sim.std_price:,.2f}")
        
        console.print(table)
        
        # Display holdings impact
        holdings_table = Table(title="Holdings Value Impact", box=box.ROUNDED)
        holdings_table.add_column("Scenario", style="cyan")
        holdings_table.add_column("Holdings Value", style="green", justify="right")
        holdings_table.add_column("Gain/Loss", style="yellow", justify="right")
        
        holdings_table.add_row(
            "Current",
            f"${holdings['current_value']:,.2f}",
            f"${holdings['current_value'] - holdings['total_cost']:,.2f}"
        )
        holdings_table.add_row(
            "Mean",
            f"${holdings['mean_value']:,.2f}",
            f"${holdings['mean_gain_loss']:,.2f}"
        )
        holdings_table.add_row(
            "Median",
            f"${holdings['median_value']:,.2f}",
            f"${holdings['median_gain_loss']:,.2f}"
        )
        holdings_table.add_row(
            "5th Percentile",
            f"${holdings['p5_value']:,.2f}",
            f"${holdings['p5_value'] - holdings['total_cost']:,.2f}"
        )
        holdings_table.add_row(
            "95th Percentile",
            f"${holdings['p95_value']:,.2f}",
            f"${holdings['p95_value'] - holdings['total_cost']:,.2f}"
        )
        
        console.print(holdings_table)
        
        # Store simulation in database
        db = DatabaseOperations()
        try:
            db.add_simulation_record(
                simulation_type="monte_carlo",
                scenarios=scenarios,
                days=days,
                initial_btc_price=initial_price,
                mean_price=sim.mean_price,
                median_price=sim.median_price,
                std_price=sim.std_price,
                min_price=sim.min_price,
                max_price=sim.max_price,
                percentile_5=sim.percentile_5,
                percentile_95=sim.percentile_95,
                results_json=json.dumps({
                    "initial_price": sim.initial_price,
                    "mean_price": sim.mean_price,
                    "median_price": sim.median_price,
                    "percentile_5": sim.percentile_5,
                    "percentile_95": sim.percentile_95,
                    "holdings_analysis": holdings
                })
            )
        finally:
            db.close()
        
    finally:
        price_scraper.close()
        holdings_scraper.close()


@cli.command()
@click.option("--days", default=30, help="Number of days of history to show")
def history(days):
    """View historical records."""
    console.print(f"[bold blue]Fetching last {days} days of history...[/bold blue]")
    
    db = DatabaseOperations()
    try:
        holdings_history = db.get_holdings_history(days=days, limit=50)
        price_history = db.get_price_history(days=days, limit=50)
        
        if holdings_history:
            table = Table(title=f"Holdings History (Last {days} days)", box=box.ROUNDED)
            table.add_column("Date", style="cyan")
            table.add_column("BTC Holdings", style="green", justify="right")
            table.add_column("Avg Cost", style="yellow", justify="right")
            table.add_column("Total Cost", style="yellow", justify="right")
            
            for record in holdings_history[:10]:  # Show last 10
                table.add_row(
                    record.timestamp.strftime("%Y-%m-%d %H:%M"),
                    f"{record.btc_holdings:,.2f}",
                    f"${record.avg_cost_basis:,.2f}",
                    f"${record.total_cost:,.2f}"
                )
            
            console.print(table)
        
        if price_history:
            table = Table(title=f"Price History (Last {days} days)", box=box.ROUNDED)
            table.add_column("Date", style="cyan")
            table.add_column("BTC Price", style="green", justify="right")
            table.add_column("MSTR Price", style="yellow", justify="right")
            table.add_column("MSTR Market Cap", style="yellow", justify="right")
            
            for record in price_history[:10]:  # Show last 10
                table.add_row(
                    record.timestamp.strftime("%Y-%m-%d %H:%M"),
                    f"${record.btc_price_usd:,.2f}",
                    f"${record.mstr_price_usd:,.2f}",
                    f"${record.mstr_market_cap_usd:,.2f}" if record.mstr_market_cap_usd else "N/A"
                )
            
            console.print(table)
        
    finally:
        db.close()


def display_metrics(metrics: Metrics, holdings_data: dict, price_data: dict):
    """Display metrics in a formatted table."""
    table = Table(title="MSTR Bitcoin Tracker - Current Metrics", box=box.ROUNDED)
    table.add_column("Metric", style="cyan", width=30)
    table.add_column("Value", style="green", justify="right")
    
    # Holdings
    table.add_row("BTC Holdings", f"{metrics.btc_holdings:,.2f} BTC")
    table.add_row("Average Cost Basis", f"${metrics.avg_cost_basis:,.2f}")
    table.add_row("Total Cost", f"${metrics.total_cost:,.2f}")
    
    # Current prices
    table.add_row("", "")  # Separator
    table.add_row("Current BTC Price", f"${metrics.current_btc_price:,.2f}")
    table.add_row("Current Holdings Value", f"${metrics.current_holdings_value:,.2f}")
    
    # Gain/Loss
    gain_loss_style = "green" if metrics.unrealized_gain_loss >= 0 else "red"
    table.add_row(
        "Unrealized Gain/Loss",
        f"[{gain_loss_style}]{metrics.unrealized_gain_loss:,.2f} ({metrics.unrealized_gain_loss_pct:+.2f}%)[/{gain_loss_style}]"
    )
    
    # MSTR
    table.add_row("", "")  # Separator
    table.add_row("MSTR Stock Price", f"${metrics.mstr_price:,.2f}")
    if metrics.mstr_market_cap:
        table.add_row("MSTR Market Cap", f"${metrics.mstr_market_cap:,.2f}")
    
    # NAV Ratio
    if metrics.nav_ratio:
        table.add_row("NAV Ratio", f"{metrics.nav_ratio:.4f}")
        if metrics.premium_discount is not None:
            pd_style = "red" if metrics.premium_discount > 0 else "green"
            table.add_row(
                "Premium/Discount",
                f"[{pd_style}]{metrics.premium_discount:+.2f}%[/{pd_style}]"
            )
    
    console.print(table)


if __name__ == "__main__":
    cli()

