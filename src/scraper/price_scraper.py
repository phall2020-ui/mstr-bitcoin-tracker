"""Scraper for Bitcoin and MSTR stock prices."""

import httpx
import yfinance as yf
import time
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
        """Fetch MSTR stock data from Yahoo Finance with retry logic."""
        ticker = yf.Ticker("MSTR")
        
        # Method 1: Try download() function (sometimes more reliable)
        try:
            time.sleep(1)  # Delay to avoid rate limiting
            df = yf.download("MSTR", period="1d", progress=False, interval="1m")
            if not df.empty:
                current_price = float(df['Close'].iloc[-1])
                if current_price and current_price > 0:
                    return {
                        "price": current_price,
                        "market_cap": None,
                        "shares_outstanding": None
                    }
        except Exception:
            pass
        
        # Method 2: Try history API with longer period
        for attempt in range(2):
            try:
                time.sleep(1.5)  # Longer delay
                hist = ticker.history(period="1mo", interval="1d")
                if not hist.empty:
                    current_price = float(hist['Close'].iloc[-1])
                    if current_price and current_price > 0:
                        return {
                            "price": current_price,
                            "market_cap": None,
                            "shares_outstanding": None
                        }
            except Exception:
                if attempt < 1:
                    time.sleep(2)
                    continue
        
        # Method 3: Fallback to info API with longer delay
        try:
            time.sleep(2)  # Longer delay to avoid rate limiting
            info = ticker.info
            current_price = (
                info.get("currentPrice") or 
                info.get("regularMarketPrice") or 
                info.get("previousClose") or
                info.get("open")
            )
            market_cap = info.get("marketCap")
            shares_outstanding = info.get("sharesOutstanding")
            
            if current_price and current_price > 0:
                return {
                    "price": float(current_price),
                    "market_cap": float(market_cap) if market_cap else None,
                    "shares_outstanding": float(shares_outstanding) if shares_outstanding else None
                }
        except Exception as e:
            print(f"Warning: Could not fetch MSTR data from Yahoo Finance (rate limited). Error: {str(e)[:100]}")
        
        # Method 4: Try Alpha Vantage if API key is available
        if settings.alpha_vantage_api_key:
            try:
                return self._fetch_mstr_from_alpha_vantage()
            except Exception:
                pass
        
        # Method 5: Try Finnhub (free tier available)
        try:
            return self._fetch_mstr_from_finnhub()
        except Exception:
            pass
        
        # Method 6: Try direct HTTP request to Yahoo Finance quote endpoint
        try:
            return self._fetch_mstr_direct_http()
        except Exception:
            pass
        
        return None
    
    def _fetch_mstr_direct_http(self) -> Optional[Dict]:
        """Try fetching MSTR price via direct HTTP request to Yahoo Finance."""
        try:
            import random
            # Use a different endpoint that might be less rate-limited
            url = "https://query1.finance.yahoo.com/v8/finance/chart/MSTR"
            params = {
                "interval": "1d",
                "range": "1d"
            }
            headers = {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
                "Accept": "application/json"
            }
            time.sleep(2)  # Wait before trying
            response = self.client.get(url, params=params, headers=headers, timeout=15)
            response.raise_for_status()
            data = response.json()
            
            result = data.get("chart", {}).get("result", [])
            if result:
                quote = result[0].get("meta", {})
                price = quote.get("regularMarketPrice") or quote.get("previousClose")
                if price and price > 0:
                    return {
                        "price": float(price),
                        "market_cap": quote.get("marketCap"),
                        "shares_outstanding": None
                    }
        except Exception:
            pass
        return None
    
    def _fetch_mstr_from_finnhub(self) -> Optional[Dict]:
        """Fetch MSTR data from Finnhub API (free tier)."""
        try:
            # Using Finnhub's free API (no key required for basic quote)
            url = "https://finnhub.io/api/v1/quote"
            params = {"symbol": "MSTR"}
            response = self.client.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            price = data.get("c")  # Current price
            if price and price > 0:
                return {
                    "price": float(price),
                    "market_cap": None,
                    "shares_outstanding": None
                }
        except Exception:
            pass
        
        # Last resort: Try a simple web scraping approach or return None
        # Note: Yahoo Finance rate limiting is aggressive. Consider:
        # 1. Adding delays between requests
        # 2. Using an API key for Alpha Vantage or Finnhub
        # 3. Caching results to reduce API calls
        return None
    
    def _fetch_mstr_from_alpha_vantage(self) -> Optional[Dict]:
        """Fetch MSTR data from Alpha Vantage API."""
        try:
            url = "https://www.alphavantage.co/query"
            params = {
                "function": "GLOBAL_QUOTE",
                "symbol": "MSTR",
                "apikey": settings.alpha_vantage_api_key
            }
            response = self.client.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            quote = data.get("Global Quote", {})
            if quote:
                price = quote.get("05. price")
                if price:
                    return {
                        "price": float(price),
                        "market_cap": None,
                        "shares_outstanding": None
                    }
        except Exception:
            pass
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

