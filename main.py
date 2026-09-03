"""Entry point for the financial analyzer."""

import argparse
import time

import yaml
from dotenv import load_dotenv

from analyzer.cost_logger import CostLogger
from analyzer.dashboard import render_dashboard
from analyzer.data_fetch import fetch_quote
from analyzer.model_router import ModelRouter

load_dotenv()


def load_config(path: str = "config.yaml") -> dict:
    with open(path) as f:
        return yaml.safe_load(f)


def parse_args():
    parser = argparse.ArgumentParser(description="Bloomberg-style terminal financial analyzer")
    parser.add_argument("--tickers", type=str, default=None, help="Comma-separated tickers, e.g. NVDA,AAPL")
    parser.add_argument("--once", action="store_true", help="Run a single snapshot instead of looping")
    parser.add_argument("--config", type=str, default="config.yaml")
    return parser.parse_args()


def run_once(tickers: list[str], router: ModelRouter) -> None:
    rows = []
    for ticker in tickers:
        try:
            q = fetch_quote(ticker)
            commentary, model = router.analyze(q)
            rows.append((q, commentary, model))
        except Exception as e:
            print(f"Failed to fetch/analyze {ticker}: {e}")
    render_dashboard(rows)


def main():
    args = parse_args()
    config = load_config(args.config)

    tickers = (
        [t.strip().upper() for t in args.tickers.split(",")]
        if args.tickers
        else config.get("tickers", ["NVDA"])
    )

    cost_logger = CostLogger(
        path=config["logging"]["path"],
        pricing=config["pricing"],
    )
    router = ModelRouter(
        cheap_model=config["models"]["cheap"],
        strong_model=config["models"]["strong"],
        escalation_threshold=config["models"]["escalation_threshold"],
        cost_logger=cost_logger,
    )

    if args.once:
        run_once(tickers, router)
        return

    refresh_seconds = config.get("refresh_seconds", 60)
    try:
        while True:
            run_once(tickers, router)
            time.sleep(refresh_seconds)
    except KeyboardInterrupt:
        print("\nStopped.")


if __name__ == "__main__":
    main()
