#!/bin/bash
# Quick setup script for API keys

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║     MSTR Bitcoin Tracker - API Key Setup                   ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""
echo "This script will help you set up an API key for MSTR price data."
echo ""
echo "Step 1: Get a FREE Finnhub API Key"
echo "  → Visit: https://finnhub.io/register"
echo "  → Sign up (takes 30 seconds)"
echo "  → Copy your API key from the dashboard"
echo ""
read -p "Press Enter when you have your API key ready..."
echo ""
read -p "Enter your Finnhub API key: " FINNHUB_KEY

if [ -z "$FINNHUB_KEY" ]; then
    echo "No API key provided. Exiting."
    exit 1
fi

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    cp .env.example .env 2>/dev/null || touch .env
fi

# Add or update FINNHUB_API_KEY
if grep -q "FINNHUB_API_KEY" .env; then
    sed -i '' "s/FINNHUB_API_KEY=.*/FINNHUB_API_KEY=$FINNHUB_KEY/" .env
    echo "✓ Updated FINNHUB_API_KEY in .env"
else
    echo "FINNHUB_API_KEY=$FINNHUB_KEY" >> .env
    echo "✓ Added FINNHUB_API_KEY to .env"
fi

echo ""
echo "Setup complete! Testing the API key..."
echo ""
python3 -m src.cli fetch

