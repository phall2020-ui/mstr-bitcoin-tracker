"""Configuration settings for MSTR Bitcoin Tracker."""

from pathlib import Path
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""
    
    # Database
    database_path: str = str(Path(__file__).parent.parent / "data" / "mstr_tracker.db")
    
    # API Keys (optional, for enhanced data sources)
    coingecko_api_key: str = ""
    alpha_vantage_api_key: str = ""
    
    # Data sources
    coingecko_api_url: str = "https://api.coingecko.com/api/v3"
    yahoo_finance_enabled: bool = True
    
    # Scraping
    user_agent: str = "MSTR-Bitcoin-Tracker/1.0"
    request_timeout: int = 30
    
    # Simulation defaults
    default_simulation_scenarios: int = 1000
    default_simulation_days: int = 30
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()

