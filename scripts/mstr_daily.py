#!/usr/bin/env python3
"""
MSTR Bitcoin Tracker - Daily Data Collection Script

This script runs daily to:
1. Initialize the database if needed
2. Fetch and ingest current BTC and MSTR prices
3. Update holdings data
4. Store snapshot in the database

Environment Variables:
- DATABASE_PATH: Path to SQLite database (default: ./data/mstr_tracker.db)
- COINGECKO_API_KEY: Optional API key for CoinGecko (Bitcoin price data)
- ALPHA_VANTAGE_API_KEY: Optional API key for Alpha Vantage (MSTR stock data)
- FINNHUB_API_KEY: Optional API key for Finnhub (MSTR stock data)
"""

import os
import sys
from datetime import datetime
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.database.models import init_database
from src.database.operations import DatabaseOperations


def main():
    """Main function to run daily data collection."""
    print(f"[{datetime.now().isoformat()}] Starting MSTR Bitcoin Tracker daily run...")
    
    try:
        # Initialize database
        print("Initializing database...")
        init_database()
        print("✓ Database initialized successfully")
        
        # Use DatabaseOperations for legacy database operations
        db_ops = DatabaseOperations()
        
        try:
            # Fetch and store current prices
            print("Fetching current BTC and MSTR prices...")
            
            # Import scrapers
            from src.scraper.price_scraper import PriceScraper
            from src.scraper.holdings_scraper import HoldingsScraper
            
            price_scraper = PriceScraper()
            holdings_scraper = HoldingsScraper()
            
            # Get BTC price
            btc_price = price_scraper.fetch_btc_price()
            if btc_price:
                print(f"✓ BTC Price: ${btc_price:,.2f}")
            else:
                print("⚠ Could not fetch BTC price")
            
            # Get MSTR price
            mstr_data = price_scraper.fetch_mstr_data()
            mstr_price = mstr_data.get('price') if mstr_data else None
            if mstr_price:
                print(f"✓ MSTR Price: ${mstr_price:.2f}")
            else:
                print("⚠ Could not fetch MSTR price")
            
            # Get holdings data
            print("Fetching MicroStrategy BTC holdings...")
            holdings = holdings_scraper.fetch_latest()
            if holdings and holdings.get('btc_holdings', 0) > 0:
                print(f"✓ BTC Holdings: {holdings.get('btc_holdings', 0):,.0f} BTC")
                print(f"  Total Cost: ${holdings.get('total_cost', 0):,.0f}")
                print(f"  Average Cost: ${holdings.get('avg_cost_basis', 0):,.2f}")
            else:
                print("⚠ Could not fetch holdings data")
            
            # Store data in database using DatabaseOperations methods
            if btc_price and mstr_price:
                print("Storing price data in database...")
                db_ops.add_price_record(
                    btc_price_usd=btc_price,
                    mstr_price_usd=mstr_price
                )
                print("✓ Price data stored successfully")
            
            if holdings and holdings.get('btc_holdings', 0) > 0:
                print("Storing holdings data in database...")
                db_ops.add_holdings_record(
                    btc_holdings=holdings.get('btc_holdings', 0),
                    avg_cost_basis=holdings.get('avg_cost_basis', 0),
                    total_cost=holdings.get('total_cost', 0),
                    source='daily_scrape'
                )
                print("✓ Holdings data stored successfully")
        finally:
            db_ops.close()
        
        print(f"[{datetime.now().isoformat()}] Daily run completed successfully! ✓")
        return 0
        
    except Exception as e:
        print(f"[{datetime.now().isoformat()}] Error during daily run: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
