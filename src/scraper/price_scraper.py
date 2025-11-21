"""Scraper for Bitcoin and MSTR stock prices."""

import httpx
import yfinance as yf
from typing import Optional, Dict
from datetime import datetime
from src.config import settings


class PriceScraper:
    """Scrape Bitcoin and MSTR stock prices."""
    
    def __init__(self):
        """Initialize the price scraper."""
        self.client = httpx.Client(
            timeout=settings.request_timeout,
            headers={"User-Agent": settings.user_agent}
        )
    
    def fetch_btc_price(self) -> Optional[float]:
        """Fetch current Bitcoin price from CoinGecko."""
        try:
            url = f"{settings.coingecko_api_url}/simple/price"
            params = {
                "ids": "bitcoin",
                "vs_currencies": "usd"
            }
            
            if settings.coingecko_api_key:
                params["x_cg_demo_api_key"] = settings.coingecko_api_key
            
            response = self.client.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            return data.get("bitcoin", {}).get("usd")
        except Exception as e:
            print(f"Error fetching BTC price from CoinGecko: {e}")
            return None
    
    def fetch_mstr_data(self) -> Optional[Dict]:
        """Fetch MSTR stock data from Yahoo Finance."""
        try:
            ticker = yf.Ticker("MSTR")
            info = ticker.info
            
            current_price = info.get("currentPrice") or info.get("regularMarketPrice")
            market_cap = info.get("marketCap")
            shares_outstanding = info.get("sharesOutstanding")
            
            if current_price:
                return {
                    "price": current_price,
                    "market_cap": market_cap,
                    "shares_outstanding": shares_outstanding
                }
        except Exception as e:
            print(f"Error fetching MSTR data from Yahoo Finance: {e}")
            return None
    
    def fetch_latest_prices(self) -> Dict:
        """Fetch latest BTC and MSTR prices."""
        btc_price = self.fetch_btc_price()
        mstr_data = self.fetch_mstr_data()
        
        return {
            "btc_price_usd": btc_price or 0.0,
            "mstr_price_usd": mstr_data.get("price") if mstr_data else 0.0,
            "mstr_market_cap_usd": mstr_data.get("market_cap") if mstr_data else None,
            "mstr_shares_outstanding": mstr_data.get("shares_outstanding") if mstr_data else None,
            "timestamp": datetime.utcnow()
        }
    
    def close(self):
        """Close the HTTP client."""
        self.client.close()

