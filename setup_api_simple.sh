#!/bin/bash
# Simple API key setup script

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║     MSTR Bitcoin Tracker - API Key Setup                   ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""
echo "Step 1: Get a FREE Finnhub API Key"
echo "  → Visit: https://finnhub.io/register"
echo "  → Sign up (takes 30 seconds)"
echo "  → Copy your API key from the dashboard"
echo ""
echo "Step 2: Enter your API key below"
echo ""
read -p "Enter your Finnhub API key: " FINNHUB_KEY

if [ -z "$FINNHUB_KEY" ]; then
    echo ""
    echo "❌ No API key provided. Exiting."
    exit 1
fi

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    if [ -f .env.example ]; then
        cp .env.example .env
        echo "✓ Created .env from .env.example"
    else
        touch .env
        echo "✓ Created new .env file"
    fi
fi

# Add or update FINNHUB_API_KEY
if grep -q "^FINNHUB_API_KEY=" .env 2>/dev/null; then
    # Update existing key (works on both macOS and Linux)
    if [[ "$OSTYPE" == "darwin"* ]]; then
        sed -i '' "s|^FINNHUB_API_KEY=.*|FINNHUB_API_KEY=$FINNHUB_KEY|" .env
    else
        sed -i "s|^FINNHUB_API_KEY=.*|FINNHUB_API_KEY=$FINNHUB_KEY|" .env
    fi
    echo "✓ Updated FINNHUB_API_KEY in .env"
else
    echo "FINNHUB_API_KEY=$FINNHUB_KEY" >> .env
    echo "✓ Added FINNHUB_API_KEY to .env"
fi

echo ""
echo "✅ Setup complete!"
echo ""
echo "Testing the API key..."
echo ""
python3 -m src.cli fetch

