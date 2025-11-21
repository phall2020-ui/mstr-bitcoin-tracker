"""Enhanced CLI interface with Typer for MSTR Bitcoin Tracker."""

import typer
import json
from datetime import date, datetime
from typing import Optional, List
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box

from src.database.models import init_database
from src.database.session import get_db_session
from src.database.operations import DatabaseOperations
from src.analytics import nav, tranches, performance, position
from src.simulation import mc_paths, scenarios, risk
from src.database.models import (
    HoldingsTranche, CompanyStats, MarketPrice, DailySnapshot,
    UserPosition, ScenarioDefinition, SimulationRun
)

app = typer.Typer(help="MSTR Bitcoin Tracker - Comprehensive analytics and tracking")
console = Console()


@app.command()
def init_db():
    """Initialize the database by creating all tables."""
    console.print("[bold blue]Initializing database...[/bold blue]")
    try:
        init_database()
        console.print("[bold green]✓ Database initialized successfully![/bold green]")
        console.print("\nYou can now:")
        console.print("  • Ingest data: mstr ingest prices")
        console.print("  • View status: mstr status")
        console.print("  • Set position: mstr set-position --shares 100 --avg-entry-price 900")
    except Exception as e:
        console.print(f"[bold red]Error initializing database: {e}[/bold red]")
        raise typer.Exit(code=1)


@app.command()
def ingest_prices(
    btc_price: Optional[float] = typer.Option(None, help="BTC price (if not provided, will fetch)"),
    mstr_price: Optional[float] = typer.Option(None, help="MSTR price (if not provided, will fetch)"),
    as_of: Optional[str] = typer.Option(None, help="Date (YYYY-MM-DD), defaults to today")
):
    """Ingest BTC and MSTR prices into the database."""
    console.print("[bold blue]Ingesting price data...[/bold blue]")
    
    # Parse date
    ingest_date = date.today()
    if as_of:
        try:
            ingest_date = datetime.strptime(as_of, "%Y-%m-%d").date()
        except ValueError:
            console.print("[bold red]Invalid date format. Use YYYY-MM-DD[/bold red]")
            raise typer.Exit(code=1)
    
    # If prices not provided, fetch them
    if btc_price is None or mstr_price is None:
        from src.scraper import PriceScraper
        scraper = PriceScraper()
        try:
            price_data = scraper.fetch_latest_prices()
            btc_price = btc_price or price_data.get("btc_price_usd", 0)
            mstr_price = mstr_price or price_data.get("mstr_price_usd", 0)
        finally:
            scraper.close()
    
    # Store in database
    with get_db_session() as session:
        # Check if already exists
        existing_btc = session.query(MarketPrice).filter(
            MarketPrice.as_of_date == ingest_date,
            MarketPrice.asset == 'BTC'
        ).first()
        
        if not existing_btc:
            session.add(MarketPrice(
                as_of_date=ingest_date,
                asset='BTC',
                close_price=btc_price,
                currency='USD'
            ))
        
        existing_mstr = session.query(MarketPrice).filter(
            MarketPrice.as_of_date == ingest_date,
            MarketPrice.asset == 'MSTR'
        ).first()
        
        if not existing_mstr:
            session.add(MarketPrice(
                as_of_date=ingest_date,
                asset='MSTR',
                close_price=mstr_price,
                currency='USD'
            ))
    
    console.print(f"[bold green]✓ Prices ingested for {ingest_date}[/bold green]")
    console.print(f"  BTC: ${btc_price:,.2f}")
    console.print(f"  MSTR: ${mstr_price:,.2f}")


@app.command()
def ingest_holdings(
    btc_amount: float = typer.Option(..., help="BTC amount acquired"),
    usd_spent: float = typer.Option(..., help="USD spent"),
    source_type: str = typer.Option("cash", help="Source type (cash, convertible_notes, equity_raise, atm)"),
    as_of: Optional[str] = typer.Option(None, help="Acquisition date (YYYY-MM-DD)"),
    notes: Optional[str] = typer.Option(None, help="Additional notes")
):
    """Ingest a new BTC holdings tranche."""
    console.print("[bold blue]Ingesting holdings tranche...[/bold blue]")
    
    # Parse date
    acquisition_date = date.today()
    if as_of:
        try:
            acquisition_date = datetime.strptime(as_of, "%Y-%m-%d").date()
        except ValueError:
            console.print("[bold red]Invalid date format. Use YYYY-MM-DD[/bold red]")
            raise typer.Exit(code=1)
    
    implied_price = usd_spent / btc_amount if btc_amount > 0 else 0
    
    with get_db_session() as session:
        session.add(HoldingsTranche(
            as_of_date=acquisition_date,
            btc_acquired=btc_amount,
            usd_spent=usd_spent,
            source_type=source_type,
            implied_btc_price=implied_price,
            notes=notes
        ))
    
    console.print(f"[bold green]✓ Tranche recorded for {acquisition_date}[/bold green]")
    console.print(f"  BTC: {btc_amount:,.2f}")
    console.print(f"  USD Spent: ${usd_spent:,.2f}")
    console.print(f"  Implied Price: ${implied_price:,.2f}")


@app.command()
def snapshot(
    as_of: Optional[str] = typer.Option(None, help="Date (YYYY-MM-DD), defaults to today")
):
    """Generate and store a daily snapshot of metrics."""
    console.print("[bold blue]Generating daily snapshot...[/bold blue]")
    
    # Parse date
    snapshot_date = date.today()
    if as_of:
        try:
            snapshot_date = datetime.strptime(as_of, "%Y-%m-%d").date()
        except ValueError:
            console.print("[bold red]Invalid date format. Use YYYY-MM-DD[/bold red]")
            raise typer.Exit(code=1)
    
    with get_db_session() as session:
        # Compute NAV metrics
        nav_metrics = nav.compute_nav_metrics(session, snapshot_date)
        
        if not nav_metrics:
            console.print("[bold red]Insufficient data to generate snapshot[/bold red]")
            raise typer.Exit(code=1)
        
        # Check if snapshot already exists
        existing = session.query(DailySnapshot).filter(
            DailySnapshot.as_of_date == snapshot_date
        ).first()
        
        if existing:
            # Update existing
            existing.total_btc = nav_metrics.total_btc
            existing.btc_spot_price = nav_metrics.btc_spot_price
            existing.mstr_share_price = nav_metrics.mstr_share_price
            existing.market_cap_usd = nav_metrics.market_cap_usd
            existing.btc_nav_usd = nav_metrics.btc_nav_usd
            existing.bs_nav_usd = nav_metrics.bs_nav_usd
            existing.btc_per_share = nav_metrics.btc_per_share
            existing.bs_nav_per_share = nav_metrics.bs_nav_per_share
            existing.premium_to_btc_nav = nav_metrics.premium_to_btc_nav
            existing.premium_to_bs_nav = nav_metrics.premium_to_bs_nav
        else:
            # Create new
            session.add(DailySnapshot(
                as_of_date=snapshot_date,
                total_btc=nav_metrics.total_btc,
                btc_spot_price=nav_metrics.btc_spot_price,
                mstr_share_price=nav_metrics.mstr_share_price,
                market_cap_usd=nav_metrics.market_cap_usd,
                btc_nav_usd=nav_metrics.btc_nav_usd,
                bs_nav_usd=nav_metrics.bs_nav_usd,
                btc_per_share=nav_metrics.btc_per_share,
                bs_nav_per_share=nav_metrics.bs_nav_per_share,
                premium_to_btc_nav=nav_metrics.premium_to_btc_nav,
                premium_to_bs_nav=nav_metrics.premium_to_bs_nav
            ))
    
    console.print(f"[bold green]✓ Snapshot created for {snapshot_date}[/bold green]")


@app.command()
def status(
    as_of: Optional[str] = typer.Option(None, help="Date (YYYY-MM-DD), defaults to today")
):
    """Display comprehensive status and metrics."""
    # Parse date
    status_date = date.today()
    if as_of:
        try:
            status_date = datetime.strptime(as_of, "%Y-%m-%d").date()
        except ValueError:
            console.print("[bold red]Invalid date format. Use YYYY-MM-DD[/bold red]")
            raise typer.Exit(code=1)
    
    with get_db_session() as session:
        # Get NAV metrics
        nav_metrics = nav.compute_nav_metrics(session, status_date)
        
        if not nav_metrics:
            console.print("[bold red]No data available for the specified date[/bold red]")
            raise typer.Exit(code=1)
        
        # Get tranche summary
        tranche_analysis = tranches.get_tranche_summary(session, status_date)
        
        # Get personal position if exists
        pos_metrics = position.compute_position_metrics(session, as_of_date=status_date)
        
        # Display main metrics table
        table = Table(title=f"MSTR Bitcoin Tracker Status - {status_date}", box=box.ROUNDED)
        table.add_column("Metric", style="cyan", width=30)
        table.add_column("Value", style="green", justify="right")
        
        # Holdings
        table.add_row("Total BTC Holdings", f"{nav_metrics.total_btc:,.4f} BTC")
        if nav_metrics.btc_per_share:
            table.add_row("BTC per Share", f"{nav_metrics.btc_per_share:.8f} BTC")
        
        # Prices
        table.add_row("", "")  # Separator
        table.add_row("BTC Spot Price", f"${nav_metrics.btc_spot_price:,.2f}")
        table.add_row("MSTR Share Price", f"${nav_metrics.mstr_share_price:,.2f}")
        
        # NAV
        table.add_row("", "")
        table.add_row("BTC NAV", f"${nav_metrics.btc_nav_usd:,.0f}")
        table.add_row("BTC NAV per Share", f"${nav_metrics.btc_nav_usd / nav_metrics.shares_outstanding:,.2f}" if nav_metrics.shares_outstanding else "N/A")
        
        if nav_metrics.bs_nav_usd:
            table.add_row("Balance Sheet NAV", f"${nav_metrics.bs_nav_usd:,.0f}")
            if nav_metrics.bs_nav_per_share:
                table.add_row("BS NAV per Share", f"${nav_metrics.bs_nav_per_share:,.2f}")
        
        # Premium/Discount
        if nav_metrics.premium_to_btc_nav is not None:
            style = "red" if nav_metrics.premium_to_btc_nav > 0 else "green"
            table.add_row("", "")
            table.add_row(
                "Premium/Discount to BTC NAV",
                f"[{style}]{nav_metrics.premium_to_btc_nav * 100:+.2f}%[/{style}]"
            )
        
        if nav_metrics.premium_to_bs_nav is not None:
            style = "red" if nav_metrics.premium_to_bs_nav > 0 else "green"
            table.add_row(
                "Premium/Discount to BS NAV",
                f"[{style}]{nav_metrics.premium_to_bs_nav * 100:+.2f}%[/{style}]"
            )
        
        # Portfolio performance
        if tranche_analysis:
            table.add_row("", "")
            pf = tranche_analysis.portfolio
            table.add_row("Total Cost Basis", f"${pf.total_cost:,.0f}")
            table.add_row("Current Value", f"${pf.total_current_value:,.0f}")
            pnl_style = "green" if pf.total_unrealized_pnl >= 0 else "red"
            table.add_row(
                "Unrealized P&L",
                f"[{pnl_style}]${pf.total_unrealized_pnl:,.0f} ({pf.total_unrealized_pnl_pct:+.2f}%)[/{pnl_style}]"
            )
        
        # Personal position
        if pos_metrics:
            table.add_row("", "")
            table.add_row("[bold]My Position[/bold]", "")
            table.add_row("Shares", f"{pos_metrics.shares:,.2f}")
            table.add_row("Entry Price", f"${pos_metrics.avg_entry_price:,.2f}")
            table.add_row("Current Value", f"${pos_metrics.current_value:,.0f}")
            pos_pnl_style = "green" if pos_metrics.unrealized_pnl >= 0 else "red"
            table.add_row(
                "Unrealized P&L",
                f"[{pos_pnl_style}]${pos_metrics.unrealized_pnl:,.0f} ({pos_metrics.unrealized_pnl_pct:+.2f}%)[/{pos_pnl_style}]"
            )
            if pos_metrics.implied_btc_exposure:
                table.add_row("Implied BTC Exposure", f"{pos_metrics.implied_btc_exposure:,.4f} BTC")
        
        console.print(table)


@app.command()
def nav_table(
    btc_prices: List[float] = typer.Option([50000, 75000, 100000, 150000, 200000], help="BTC prices to analyze"),
    as_of: Optional[str] = typer.Option(None, help="Date (YYYY-MM-DD)")
):
    """Display NAV sensitivity table across different BTC prices."""
    # Parse date
    analysis_date = date.today()
    if as_of:
        try:
            analysis_date = datetime.strptime(as_of, "%Y-%m-%d").date()
        except ValueError:
            console.print("[bold red]Invalid date format. Use YYYY-MM-DD[/bold red]")
            raise typer.Exit(code=1)
    
    with get_db_session() as session:
        # Get current metrics
        nav_metrics = nav.compute_nav_metrics(session, analysis_date)
        
        if not nav_metrics or not nav_metrics.shares_outstanding:
            console.print("[bold red]Insufficient data[/bold red]")
            raise typer.Exit(code=1)
        
        # Create sensitivity table
        table = Table(title=f"NAV Sensitivity Analysis - {analysis_date}", box=box.ROUNDED)
        table.add_column("BTC Price", style="cyan", justify="right")
        table.add_column("BTC NAV/Share", style="yellow", justify="right")
        if nav_metrics.bs_nav_per_share and nav_metrics.cash_usd and nav_metrics.debt_usd_market:
            table.add_column("BS NAV/Share", style="yellow", justify="right")
        table.add_column("Current MSTR", style="green", justify="right")
        table.add_column("Implied Premium", style="magenta", justify="right")
        
        current_mstr = nav_metrics.mstr_share_price
        shares = nav_metrics.shares_outstanding
        cash = nav_metrics.cash_usd or 0
        debt = nav_metrics.debt_usd_market or 0
        
        for btc_price in sorted(btc_prices):
            btc_nav_per_share = (nav_metrics.total_btc * btc_price) / shares
            
            if nav_metrics.bs_nav_per_share and nav_metrics.cash_usd and nav_metrics.debt_usd_market:
                bs_nav_per_share = ((nav_metrics.total_btc * btc_price) + cash - debt) / shares
                premium = ((current_mstr / bs_nav_per_share) - 1) * 100
                table.add_row(
                    f"${btc_price:,.0f}",
                    f"${btc_nav_per_share:,.2f}",
                    f"${bs_nav_per_share:,.2f}",
                    f"${current_mstr:,.2f}",
                    f"{premium:+.2f}%"
                )
            else:
                premium = ((current_mstr / btc_nav_per_share) - 1) * 100
                table.add_row(
                    f"${btc_price:,.0f}",
                    f"${btc_nav_per_share:,.2f}",
                    f"${current_mstr:,.2f}",
                    f"{premium:+.2f}%"
                )
        
        console.print(table)


@app.command()
def risk_report(
    scenario: str = typer.Option("base", help="Scenario name (bear, base, bull, hyper)"),
    horizon_days: Optional[int] = typer.Option(None, help="Override horizon days"),
    num_paths: Optional[int] = typer.Option(None, help="Override number of paths"),
    as_of: Optional[str] = typer.Option(None, help="Date (YYYY-MM-DD)")
):
    """Run simulation and display risk report with VaR/CVaR."""
    console.print(f"[bold blue]Running {scenario} scenario simulation...[/bold blue]")
    
    # Parse date
    sim_date = date.today()
    if as_of:
        try:
            sim_date = datetime.strptime(as_of, "%Y-%m-%d").date()
        except ValueError:
            console.print("[bold red]Invalid date format. Use YYYY-MM-DD[/bold red]")
            raise typer.Exit(code=1)
    
    # Get scenario config
    try:
        scenario_config = scenarios.get_scenario(scenario)
    except ValueError as e:
        console.print(f"[bold red]{e}[/bold red]")
        raise typer.Exit(code=1)
    
    # Override if provided
    if horizon_days:
        scenario_config.horizon_days = horizon_days
    if num_paths:
        scenario_config.num_paths = num_paths
    
    with get_db_session() as session:
        # Get current prices
        nav_metrics = nav.compute_nav_metrics(session, sim_date)
        if not nav_metrics:
            console.print("[bold red]Insufficient data[/bold red]")
            raise typer.Exit(code=1)
        
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
        pos_metrics = position.compute_position_metrics(session, as_of_date=sim_date)
        portfolio_risk = None
        if pos_metrics:
            portfolio_risk = risk.compute_portfolio_risk(
                btc_final, mstr_final,
                nav_metrics.btc_spot_price, nav_metrics.mstr_share_price,
                pos_metrics.shares
            )
        
        # Display results
        console.print(f"\n[bold]Scenario: {scenario_config.name.upper()}[/bold]")
        console.print(f"Description: {scenario_config.description}")
        console.print(f"Horizon: {scenario_config.horizon_days} days | Paths: {scenario_config.num_paths:,}\n")
        
        # BTC Risk Table
        btc_table = Table(title="BTC Risk Metrics", box=box.ROUNDED)
        btc_table.add_column("Metric", style="cyan")
        btc_table.add_column("Value", style="green", justify="right")
        
        btc_table.add_row("Initial Price", f"${nav_metrics.btc_spot_price:,.2f}")
        btc_table.add_row("Mean Return", f"{btc_risk.mean_return * 100:+.2f}%")
        btc_table.add_row("Median Return", f"{btc_risk.median_return * 100:+.2f}%")
        btc_table.add_row("Std Dev", f"{btc_risk.std_return * 100:.2f}%")
        btc_table.add_row("VaR (95%)", f"[red]{btc_risk.var_95 * 100:.2f}%[/red]")
        btc_table.add_row("CVaR (95%)", f"[red]{btc_risk.cvar_95 * 100:.2f}%[/red]")
        btc_table.add_row("5th Percentile", f"${nav_metrics.btc_spot_price * (1 + btc_risk.percentiles['5']):,.2f}")
        btc_table.add_row("95th Percentile", f"${nav_metrics.btc_spot_price * (1 + btc_risk.percentiles['95']):,.2f}")
        
        console.print(btc_table)
        
        # MSTR Risk Table
        mstr_table = Table(title="MSTR Risk Metrics", box=box.ROUNDED)
        mstr_table.add_column("Metric", style="cyan")
        mstr_table.add_column("Value", style="green", justify="right")
        
        mstr_table.add_row("Initial Price", f"${nav_metrics.mstr_share_price:,.2f}")
        mstr_table.add_row("Mean Return", f"{mstr_risk.mean_return * 100:+.2f}%")
        mstr_table.add_row("Median Return", f"{mstr_risk.median_return * 100:+.2f}%")
        mstr_table.add_row("Std Dev", f"{mstr_risk.std_return * 100:.2f}%")
        mstr_table.add_row("VaR (95%)", f"[red]{mstr_risk.var_95 * 100:.2f}%[/red]")
        mstr_table.add_row("CVaR (95%)", f"[red]{mstr_risk.cvar_95 * 100:.2f}%[/red]")
        mstr_table.add_row("5th Percentile", f"${nav_metrics.mstr_share_price * (1 + mstr_risk.percentiles['5']):,.2f}")
        mstr_table.add_row("95th Percentile", f"${nav_metrics.mstr_share_price * (1 + mstr_risk.percentiles['95']):,.2f}")
        
        console.print(mstr_table)
        
        # Portfolio Risk Table (if position exists)
        if portfolio_risk and pos_metrics:
            port_table = Table(title=f"My Position Risk ({pos_metrics.shares:,.0f} shares)", box=box.ROUNDED)
            port_table.add_column("Metric", style="cyan")
            port_table.add_column("Value", style="green", justify="right")
            
            port_table.add_row("Current Value", f"${pos_metrics.current_value:,.0f}")
            port_table.add_row("Mean Return", f"{portfolio_risk.mean_return * 100:+.2f}%")
            port_table.add_row("Value at Risk (95%)", f"[red]${pos_metrics.current_value * portfolio_risk.var_95:,.0f}[/red]")
            port_table.add_row("CVaR (95%)", f"[red]${pos_metrics.current_value * portfolio_risk.cvar_95:,.0f}[/red]")
            port_table.add_row("5th Percentile Value", f"${pos_metrics.current_value * (1 + portfolio_risk.percentiles['5']):,.0f}")
            port_table.add_row("95th Percentile Value", f"${pos_metrics.current_value * (1 + portfolio_risk.percentiles['95']):,.0f}")
            
            console.print(port_table)
        
        # Store simulation run
        risk_summary = risk.create_risk_summary(btc_risk, mstr_risk, portfolio_risk)
        
        session.add(SimulationRun(
            created_at=datetime.utcnow(),
            scenario_id=None,  # TODO: Link to scenario_definition if stored
            horizon_days=scenario_config.horizon_days,
            num_paths=scenario_config.num_paths,
            seed=None,
            input_snapshot_date=sim_date,
            results_summary_json=json.dumps(risk_summary)
        ))


@app.command()
def set_position(
    shares: float = typer.Option(..., help="Number of MSTR shares"),
    avg_entry_price: float = typer.Option(..., help="Average entry price per share"),
    label: str = typer.Option("main", help="Position label"),
    deactivate_others: bool = typer.Option(True, help="Deactivate other positions")
):
    """Set or update personal MSTR position."""
    console.print("[bold blue]Setting position...[/bold blue]")
    
    with get_db_session() as session:
        # Deactivate other positions if requested
        if deactivate_others:
            # Only deactivate existing active positions
            active_positions = session.query(UserPosition).filter(
                UserPosition.is_active == True
            ).all()
            for pos in active_positions:
                pos.is_active = False
        
        # Create new position
        position = UserPosition(
            label=label,
            created_at=datetime.utcnow(),
            is_active=True,
            shares=shares,
            avg_entry_price=avg_entry_price
        )
        session.add(position)
    
    console.print(f"[bold green]✓ Position set![/bold green]")
    console.print(f"  Label: {label}")
    console.print(f"  Shares: {shares:,.2f}")
    console.print(f"  Entry Price: ${avg_entry_price:,.2f}")
    console.print(f"  Cost Basis: ${shares * avg_entry_price:,.2f}")


if __name__ == "__main__":
    app()
