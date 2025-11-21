# MSTR Bitcoin Tracker - Enhanced Edition

A comprehensive, production-quality analytics tool for tracking MicroStrategy's Bitcoin exposure, valuation metrics, simulations, and personal position management.

## 🚀 Features

### Core Capabilities
- **Comprehensive Data Storage**: SQLite database with tranche-level BTC acquisition history
- **NAV Analytics**: BTC per share, NAV ratios, premium/discount calculations
- **Tranche Performance**: Individual tranche P&L tracking and analysis
- **Performance Analytics**: Returns, volatility, beta vs BTC, drawdowns
- **Personal Position Tracking**: Monitor your MSTR position with implied BTC exposure
- **Monte Carlo Simulations**: Joint BTC/MSTR price simulations with beta modeling
- **Risk Analysis**: VaR/CVaR calculations at multiple confidence levels
- **Scenario Analysis**: Pre-defined scenarios (bear, base, bull, hyper)
- **CLI Interface**: Rich terminal UI with Typer
- **REST API**: FastAPI-based API for programmatic access

## 📋 Requirements

- Python 3.11+
- Dependencies (see `requirements.txt`)

## 🔧 Installation

```bash
git clone https://github.com/phall2020-ui/mstr-bitcoin-tracker.git
cd mstr-bitcoin-tracker
pip3 install -r requirements.txt
```

## 🏁 Quick Start

### 1. Initialize Database

```bash
python3 -m src.cli_typer init-db
```

### 2. Ingest Data

```bash
# Ingest current prices
python3 -m src.cli_typer ingest-prices --btc-price 95000 --mstr-price 380

# Add BTC holdings tranche
python3 -m src.cli_typer ingest-holdings \
  --btc-amount 10000 \
  --usd-spent 500000000 \
  --source-type "cash" \
  --notes "Initial purchase"
```

### 3. Generate Snapshot

```bash
python3 -m src.cli_typer snapshot
```

### 4. View Status

```bash
python3 -m src.cli_typer status
```

### 5. Set Your Position

```bash
python3 -m src.cli_typer set-position \
  --shares 100 \
  --avg-entry-price 300 \
  --label "pension"
```

## 📊 CLI Commands

### Core Commands

#### `init-db`
Initialize the database with all required tables.

```bash
python3 -m src.cli_typer init-db
```

#### `ingest-prices`
Ingest BTC and MSTR price data.

```bash
python3 -m src.cli_typer ingest-prices \
  --btc-price 95000 \
  --mstr-price 380 \
  --as-of "2025-11-21"
```

#### `ingest-holdings`
Add a new BTC holdings tranche.

```bash
python3 -m src.cli_typer ingest-holdings \
  --btc-amount 5000 \
  --usd-spent 250000000 \
  --source-type "convertible_notes" \
  --as-of "2025-11-21" \
  --notes "Q4 2025 convertible notes"
```

**Source types**: `cash`, `convertible_notes`, `equity_raise`, `atm`

#### `snapshot`
Generate and store a daily snapshot of all computed metrics.

```bash
python3 -m src.cli_typer snapshot
python3 -m src.cli_typer snapshot --as-of "2025-11-01"
```

### Analysis Commands

#### `status`
Display comprehensive status with all metrics.

```bash
python3 -m src.cli_typer status
python3 -m src.cli_typer status --as-of "2025-11-15"
```

**Shows**:
- Total BTC holdings and BTC per share
- Current prices (BTC and MSTR)
- NAV metrics (BTC NAV, Balance Sheet NAV)
- Premium/discount to NAV
- Portfolio P&L (from tranches)
- Personal position (if set)

#### `nav-table`
Display NAV sensitivity across different BTC price levels.

```bash
python3 -m src.cli_typer nav-table \
  --btc-prices 50000 \
  --btc-prices 75000 \
  --btc-prices 100000 \
  --btc-prices 150000 \
  --btc-prices 200000
```

Shows how NAV per share and implied premium/discount change at different BTC prices.

#### `risk-report`
Run Monte Carlo simulation and display risk metrics.

```bash
# Use pre-defined scenario
python3 -m src.cli_typer risk-report --scenario base

# Available scenarios: bear, base, bull, hyper
python3 -m src.cli_typer risk-report --scenario bull

# Override parameters
python3 -m src.cli_typer risk-report \
  --scenario base \
  --horizon-days 180 \
  --num-paths 10000
```

**Shows**:
- BTC risk metrics (returns, VaR, CVaR, percentiles)
- MSTR risk metrics
- Personal position risk (if position is set)

### Position Management

#### `set-position`
Set or update your personal MSTR position.

```bash
python3 -m src.cli_typer set-position \
  --shares 150 \
  --avg-entry-price 900 \
  --label "trading" \
  --deactivate-others
```

## 🌐 REST API

### Starting the API Server

```bash
python3 -m src.api_enhanced

# Or with uvicorn directly
uvicorn src.api_enhanced:app --host 0.0.0.0 --port 8000 --reload
```

API will be available at:
- Base URL: `http://localhost:8000`
- Interactive docs: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

### API Endpoints

#### Health Check
```bash
GET /api/v1/health
```

#### Summary
```bash
GET /api/v1/summary/today
```

Returns high-level metrics for today:
```json
{
  "date": "2025-11-21",
  "total_btc": 10000.0,
  "btc_spot": 95000.0,
  "mstr_price": 380.0,
  "market_cap": 76000000000.0,
  "btc_per_share": 0.00005,
  "btc_nav_per_share": 4.75,
  "bs_nav_per_share": -5.25,
  "premium_to_btc_nav": 79.0,
  "premium_to_bs_nav": null
}
```

#### NAV Metrics
```bash
GET /api/v1/nav?date=2025-11-21
```

Returns detailed NAV metrics:
```json
{
  "date": "2025-11-21",
  "total_btc": 10000.0,
  "btc_spot_price": 95000.0,
  "mstr_share_price": 380.0,
  "market_cap_usd": 76000000000.0,
  "btc_nav_usd": 950000000.0,
  "bs_nav_usd": -1050000000.0,
  "btc_per_share": 0.00005,
  "bs_nav_per_share": -5.25,
  "premium_to_btc_nav": 79.0,
  "premium_to_bs_nav": null,
  "shares_outstanding": 200000000.0,
  "cash_usd": 500000000.0,
  "debt_usd_market": 2500000000.0
}
```

#### Tranches
```bash
GET /api/v1/tranches?date=2025-11-21
```

Returns all tranches with individual and portfolio-level metrics.

#### Personal Position
```bash
GET /api/v1/my-position
```

Returns personal position metrics:
```json
{
  "label": "pension",
  "shares": 100.0,
  "avg_entry_price": 300.0,
  "current_price": 380.0,
  "current_value": 38000.0,
  "unrealized_pnl": 8000.0,
  "unrealized_pnl_pct": 26.67,
  "implied_btc_exposure": 0.005
}
```

#### Simulation
```bash
POST /api/v1/simulate
Content-Type: application/json

{
  "scenario_name": "base",
  "horizon_days": 365,
  "num_paths": 5000
}
```

Returns simulation results with risk metrics for BTC, MSTR, and portfolio.

#### Get Simulation Run
```bash
GET /api/v1/simulate/{run_id}
```

Retrieve previously run simulation results.

## 📊 Database Schema

### Core Tables

#### `holdings_tranche`
Individual BTC acquisition records with source type and implied price.

#### `company_stats`
MicroStrategy company statistics (shares, cash, debt).

#### `market_price`
Unified price storage for all assets (BTC, MSTR, etc.).

#### `daily_snapshot`
Pre-computed daily metrics snapshot.

#### `user_position`
Personal MSTR position tracking.

#### `scenario_definition`
Simulation scenario configurations.

#### `simulation_run`
Historical simulation results.

## 🎯 Simulation Scenarios

### Pre-defined Scenarios

#### Bear
- BTC: -30% annual return, 100% volatility
- MSTR: 1.8x beta, -5% alpha
- Description: Negative returns, high volatility

#### Base (Default)
- BTC: +20% annual return, 80% volatility
- MSTR: 1.5x beta, 0% alpha
- Description: Moderate growth, typical volatility

#### Bull
- BTC: +60% annual return, 70% volatility
- MSTR: 1.7x beta, +10% alpha
- Description: Strong returns, moderate volatility

#### Hyper
- BTC: +150% annual return, 120% volatility
- MSTR: 2.0x beta, +20% alpha
- Description: Extreme growth, increasing volatility

## 📈 Analytics Modules

### NAV Analytics (`src/analytics/nav.py`)
- `get_total_btc()` - Total BTC holdings
- `get_btc_per_share()` - BTC per share calculation
- `compute_nav_metrics()` - Comprehensive NAV metrics

### Tranche Analytics (`src/analytics/tranches.py`)
- `get_tranche_summary()` - Individual tranche performance
- Portfolio-level aggregation

### Performance Analytics (`src/analytics/performance.py`)
- `compute_returns()` - Daily returns and statistics
- `compute_beta_vs_btc()` - Beta and correlation vs BTC
- `compute_drawdowns()` - Drawdown analysis

### Position Analytics (`src/analytics/position.py`)
- `compute_position_metrics()` - Personal position P&L and exposure

## 🎲 Simulation Engine

### Monte Carlo Paths (`src/simulation/mc_paths.py`)
- `simulate_btc_paths()` - Geometric Brownian Motion for BTC
- `simulate_joint_btc_mstr_paths()` - Joint simulation with beta model
- `estimate_beta_parameters()` - Parameter estimation from historical data

### Risk Metrics (`src/simulation/risk.py`)
- `compute_var_cvar()` - Value at Risk and Conditional VaR
- `compute_risk_metrics()` - Comprehensive risk analysis
- `compute_portfolio_risk()` - Portfolio-level risk

## 🧪 Testing

Run tests (if available):
```bash
pytest
```

## 🔒 Security

- Run CodeQL security scanning before deployment
- Never commit API keys or sensitive data
- Use environment variables for configuration

## 📝 Project Structure

```
mstr-bitcoin-tracker/
├── src/
│   ├── analytics/          # Analytics modules
│   │   ├── nav.py
│   │   ├── tranches.py
│   │   ├── performance.py
│   │   └── position.py
│   ├── simulation/         # Simulation engine
│   │   ├── mc_paths.py
│   │   ├── scenarios.py
│   │   └── risk.py
│   ├── database/           # Database models and operations
│   │   ├── models.py
│   │   ├── session.py
│   │   └── operations.py
│   ├── scraper/            # Data scrapers (legacy)
│   ├── calculator/         # Metric calculators (legacy)
│   ├── simulator/          # Old simulator (legacy)
│   ├── cli_typer.py        # Enhanced CLI (Typer)
│   ├── api_enhanced.py     # Enhanced REST API
│   ├── cli.py              # Legacy CLI (Click)
│   ├── api.py              # Legacy API
│   └── config.py           # Configuration
├── data/                   # SQLite database
├── mstr_cli.py             # CLI entry point
├── requirements.txt
├── setup.py
└── README_ENHANCED.md      # This file
```

## 🤝 Contributing

Contributions welcome! Please ensure:
- Code follows existing patterns
- All tests pass
- Security scans pass
- Documentation is updated

## ⚠️ Disclaimer

This tool is for informational and analytical purposes only. It is not financial advice. Always verify data from official sources. The authors are not responsible for any financial decisions made based on this tool's output.

## 📄 License

MIT License - See LICENSE file for details

## 🙏 Acknowledgments

Built for comprehensive analysis of MicroStrategy's innovative Bitcoin treasury strategy.
