"""Per-call cost logging for AI model usage."""

import csv
import os
from dataclasses import dataclass
from datetime import datetime, timezone


@dataclass
class UsageRecord:
    ticker: str
    model: str
    input_tokens: int
    output_tokens: int
    estimated_cost_usd: float
    reason: str


class CostLogger:
    def __init__(self, path: str, pricing: dict):
        self.path = path
        self.pricing = pricing
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        if not os.path.exists(path):
            with open(path, "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(
                    [
                        "timestamp_utc",
                        "ticker",
                        "model",
                        "reason",
                        "input_tokens",
                        "output_tokens",
                        "estimated_cost_usd",
                    ]
                )

    def estimate_cost(self, model: str, input_tokens: int, output_tokens: int) -> float:
        rates = self.pricing.get(model)
        if not rates:
            return 0.0
        input_cost = (input_tokens / 1_000_000) * rates.get("input_per_mtok", 0)
        output_cost = (output_tokens / 1_000_000) * rates.get("output_per_mtok", 0)
        return round(input_cost + output_cost, 6)

    def log(self, ticker: str, model: str, input_tokens: int, output_tokens: int, reason: str) -> UsageRecord:
        cost = self.estimate_cost(model, input_tokens, output_tokens)
        record = UsageRecord(
            ticker=ticker,
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            estimated_cost_usd=cost,
            reason=reason,
        )
        with open(self.path, "a", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(
                [
                    datetime.now(timezone.utc).isoformat(),
                    record.ticker,
                    record.model,
                    record.reason,
                    record.input_tokens,
                    record.output_tokens,
                    record.estimated_cost_usd,
                ]
            )
        return record
