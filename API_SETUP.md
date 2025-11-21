# API Key Setup Guide

To get reliable MSTR stock prices, you'll need a free API key from one of these services.

## Option 1: Finnhub (Recommended - Easiest)

Finnhub offers a free tier with 60 API calls/minute.

### Steps:

1. **Register for free account:**
   - Go to: https://finnhub.io/register
   - Sign up with your email
   - Verify your email

2. **Get your API key:**
   - After logging in, go to: https://finnhub.io/dashboard
   - Copy your API key from the dashboard

3. **Add to your .env file:**
   ```bash
   cd mstr-bitcoin-tracker
   cp .env.example .env
   # Edit .env and add: FINNHUB_API_KEY=your_key_here
   ```

4. **Or set as environment variable:**
   ```bash
   export FINNHUB_API_KEY=your_key_here
   ```

## Option 2: Alpha Vantage

Alpha Vantage offers a free tier with 5 API calls/minute and 500 calls/day.

### Steps:

1. **Get free API key:**
   - Go to: https://www.alphavantage.co/support/#api-key
   - Fill out the form to get your free API key

2. **Add to your .env file:**
   ```bash
   # Edit .env and add: ALPHA_VANTAGE_API_KEY=your_key_here
   ```

3. **Or set as environment variable:**
   ```bash
   export ALPHA_VANTAGE_API_KEY=your_key_here
   ```

## Quick Setup

```bash
# 1. Copy the example file
cp .env.example .env

# 2. Edit .env and add your API key
# For Finnhub:
FINNHUB_API_KEY=your_actual_key_here

# 3. Test it
python3 -m src.cli fetch
```

## Verify It's Working

After setting up your API key, test it:

```bash
python3 -m src.cli fetch
```

You should see a non-zero MSTR Stock Price in the output.

## Troubleshooting

- **Still showing $0.00?** Make sure your API key is correct and the .env file is in the project root
- **Rate limited?** Wait a few minutes between requests
- **API key not working?** Check that you've activated your account (some services require email verification)

