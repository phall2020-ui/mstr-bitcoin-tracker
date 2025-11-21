# MSTR Bitcoin Tracker

A comprehensive tool for tracking MicroStrategy's Bitcoin holdings, calculating metrics, running simulations, and storing historical records.

## Features

- **BTC Holdings Scraper**: Fetches MicroStrategy's Bitcoin holdings from multiple sources
- **Average Cost Calculation**: Tracks the average purchase price of BTC holdings
- **NAV-like Ratio**: Calculates market cap to BTC holdings value ratio
- **Price Simulations**: Monte Carlo simulations for future price scenarios
- **Historical Records**: SQLite database for storing historical data
- **CLI Interface**: Command-line tool for quick access with rich formatting
- **REST API**: FastAPI-based REST API for programmatic access

## Installation

```bash
cd mstr-bitcoin-tracker
pip3 install -r requirements.txt

# Initialize the database
python3 setup.py
```

## Quick Start

### CLI Usage

```bash
# Fetch latest data and display metrics
python3 -m src.cli fetch

# Show current holdings
python3 -m src.cli holdings

# Calculate NAV ratio
python3 -m src.cli nav

# Run price simulation
python3 -m src.cli simulate --scenarios 1000 --days 30

# Custom simulation parameters
python3 -m src.cli simulate --scenarios 5000 --days 60 --volatility 0.90 --drift 0.15

# View historical data
python3 -m src.cli history --days 30
```

### REST API

```bash
# Start the API server
python3 -m src.api

# Or with uvicorn directly
uvicorn src.api:app --host 0.0.0.0 --port 8000

# API will be available at http://localhost:8000
# Interactive docs at http://localhost:8000/docs
```

### API Endpoints

#### Core Endpoints

- `GET /api/v1/holdings` - Get current BTC holdings
- `GET /api/v1/prices` - Get current BTC and MSTR prices
- `GET /api/v1/metrics` - Get calculated metrics (avg cost, NAV ratio, etc.)
- `POST /api/v1/fetch` - Fetch latest data and store in database

#### Simulation

- `POST /api/v1/simulate` - Run price simulations
  ```json
  {
    "scenarios": 1000,
    "days": 30,
    "volatility": 0.80,
    "drift": 0.20
  }
  ```

#### History

- `GET /api/v1/history/holdings?days=30&limit=100` - Get holdings history
- `GET /api/v1/history/prices?days=30&limit=100` - Get price history

#### Utility

- `GET /api/v1/health` - Health check
- `GET /` - API information
- `GET /docs` - Interactive API documentation (Swagger UI)

### Example API Usage

```python
import requests

# Get current metrics
response = requests.get("http://localhost:8000/api/v1/metrics")
metrics = response.json()
print(f"NAV Ratio: {metrics['nav_ratio']}")
print(f"Unrealized Gain: {metrics['unrealized_gain_loss']:,.2f}")

# Run simulation
sim_response = requests.post(
    "http://localhost:8000/api/v1/simulate",
    json={"scenarios": 1000, "days": 30}
)
sim_results = sim_response.json()
print(f"Mean price after 30 days: ${sim_results['mean_price']:,.2f}")
```

## Data Sources

- **MicroStrategy Holdings**: Web scraping from press releases and SEC filings (fallback to known data)
- **Bitcoin Price**: CoinGecko API (free tier available)
- **MSTR Stock Price**: Yahoo Finance API (via yfinance)

### Optional API Keys

For enhanced data access, you can set these environment variables:

```bash
export COINGECKO_API_KEY=your_key_here
export ALPHA_VANTAGE_API_KEY=your_key_here
```

Or create a `.env` file:

```
COINGECKO_API_KEY=your_key_here
ALPHA_VANTAGE_API_KEY=your_key_here
```

## Project Structure

```
mstr-bitcoin-tracker/
├── src/
│   ├── scraper/          # Data scraping modules
│   │   ├── holdings_scraper.py
│   │   └── price_scraper.py
│   ├── calculator/        # Metric calculations
│   │   └── metrics.py
│   ├── simulator/         # Price simulations
│   │   └── monte_carlo.py
│   ├── database/          # Database models and operations
│   │   ├── models.py
│   │   └── operations.py
│   ├── cli.py            # CLI interface
│   ├── api.py            # REST API
│   └── config.py         # Configuration
├── data/                 # SQLite database (created on first run)
├── setup.py              # Setup script
├── requirements.txt
└── README.md
```

## Metrics Explained

- **Average Cost Basis**: Average price paid per BTC
- **NAV Ratio**: Market Cap / BTC Holdings Value
  - Ratio < 1.0: Trading at discount to BTC value
  - Ratio > 1.0: Trading at premium to BTC value
- **Premium/Discount**: Percentage difference between market cap and BTC value
- **Unrealized Gain/Loss**: Current value minus total cost basis

## Simulation Parameters

- **Volatility**: Annual volatility (default 0.80 = 80% for BTC)
- **Drift**: Annual expected return (default 0.20 = 20%)
- **Scenarios**: Number of Monte Carlo simulations to run
- **Days**: Time horizon for simulation

## Database Schema

The SQLite database stores:

- **holdings_records**: Historical BTC holdings and cost basis
- **price_records**: Historical BTC and MSTR prices
- **simulation_records**: Historical simulation results

## Development

```bash
# Install in development mode
pip3 install -e .

# Run tests (if available)
pytest

# Format code
black src/
```

## License

MIT

## Disclaimer

This tool is for informational purposes only. It is not financial advice. Always verify data from official sources.
