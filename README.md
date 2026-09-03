# Financial Analyzer

A lightweight, terminal-based "Bloomberg-style" financial analyzer. It pulls live market data for one or more tickers and layers AI-generated commentary on top, using a cost-aware model router (cheap model for routine summaries, a stronger model only when the situation calls for deeper analysis).

## Features

- **Live market data** via [yfinance](https://pypi.org/project/yfinance/) — price, volume, day range, 52-week range, moving averages, key fundamentals.
- **Cost-routed AI analysis** — a lightweight model (Claude Haiku) handles routine daily summaries; a stronger model (Claude Sonnet) is only invoked when volatility/signal thresholds are crossed, keeping API spend low.
- **Cost logging** — every AI call is logged to `logs/cost_log.csv` with timestamp, ticker, model used, input/output tokens, and estimated cost.
- **Terminal dashboard** — a single-screen text dashboard (via `rich`) showing quote, technicals, and the latest AI take, refreshable on demand.
- **Watchlist config** — track any number of tickers via `config.yaml` (defaults to `NVDA`).

## Project layout

```
financial-analyzer/
├── analyzer/
│   ├── __init__.py
│   ├── data_fetch.py       # Market data via yfinance
│   ├── model_router.py     # Haiku/Sonnet cost-aware routing + Claude API calls
│   ├── cost_logger.py      # Per-call cost logging to CSV
│   └── dashboard.py        # Rich-based terminal dashboard
├── config.yaml             # Watchlist + routing thresholds
├── main.py                 # Entry point
├── requirements.txt
├── .env.example
├── .gitignore
└── logs/                   # Created at runtime; cost_log.csv lives here
```

## Setup

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # add your ANTHROPIC_API_KEY
```

## Usage

```bash
python main.py                 # run dashboard for tickers in config.yaml
python main.py --tickers NVDA,AAPL,MSFT
python main.py --once           # single snapshot instead of live refresh loop
```

## Model routing logic

Every refresh cycle:

1. Fetch fresh quote/technicals for each ticker.
2. Compute a simple "signal score" from the day's move, volume vs. average volume, and proximity to 52-week highs/lows.
3. If the signal score is below the `escalation_threshold` in `config.yaml`, send a compact prompt to **Haiku** for a quick read.
4. If the score crosses the threshold (something notable is happening), escalate to **Sonnet** for deeper analysis.
5. Log the model used, token counts, and estimated cost for every call.

This keeps routine monitoring cheap while still getting higher-quality analysis exactly when it matters.

## Notes

This is a personal research/monitoring tool, not investment advice, and it is not affiliated with or endorsed by Bloomberg L.P.
