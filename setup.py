#!/usr/bin/env python3
"""Setup script for MSTR Bitcoin Tracker."""

from pathlib import Path
from src.database import init_database

def setup():
    """Initialize the database and create necessary directories."""
    # Create data directory
    data_dir = Path(__file__).parent / "data"
    data_dir.mkdir(exist_ok=True)
    
    # Initialize database
    print("Initializing database...")
    init_database()
    print("✓ Database initialized successfully!")
    
    print("\nSetup complete! You can now use the CLI or API.")
    print("\nCLI Usage:")
    print("  python3 -m src.cli fetch")
    print("\nAPI Usage:")
    print("  python3 -m src.api")

if __name__ == "__main__":
    setup()

