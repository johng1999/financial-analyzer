"""Cost-aware model routing: cheap model for routine reads, strong model for notable moves."""

import os
from typing import Optional

from anthropic import Anthropic

from .cost_logger import CostLogger
from .data_fetch import Quote


def compute_signal_score(q: Quote) -> float:
    """
    Very simple heuristic 0-100 "how notable is today's action" score.
    Combines: |% move| vs typical, volume vs 10d avg, proximity to 52w extremes.
    """
    score = 0.0

    # Weight 1: absolute % move (each 1% ~ 8 points, capped)
    score += min(abs(q.change_pct) * 8, 50)

    # Weight 2: volume surge vs 10-day average
    if q.avg_volume_10d and q.avg_volume_10d > 0:
        vol_ratio = q.volume / q.avg_volume_10d
        if vol_ratio > 1:
            score += min((vol_ratio - 1) * 30, 30)

    # Weight 3: proximity to 52-week high/low (within 2% of either)
    if q.week52_high:
        dist_to_high_pct = abs(q.week52_high - q.price) / q.week52_high * 100
        if dist_to_high_pct <= 2:
            score += 20
    if q.week52_low:
        dist_to_low_pct = abs(q.price - q.week52_low) / q.week52_low * 100
        if dist_to_low_pct <= 2:
            score += 20

    return min(score, 100)


def _build_prompt(q: Quote, score: float) -> str:
    return f"""You are a markets analyst. Give a concise, plain-English read on {q.ticker}.

Data:
- Price: {q.price:.2f} ({q.change_pct:+.2f}% vs prev close {q.prev_close:.2f})
- Day range: {q.day_low:.2f} - {q.day_high:.2f}
- Volume: {q.volume:,} (10d avg: {q.avg_volume_10d or 'n/a'})
- 52-week range: {q.week52_low:.2f} - {q.week52_high:.2f}
- 50-day MA: {q.ma50 if q.ma50 is None else f'{q.ma50:.2f}'}
- 200-day MA: {q.ma200 if q.ma200 is None else f'{q.ma200:.2f}'}
- Market cap: {q.market_cap}
- Trailing P/E: {q.pe_ratio}
- Internal signal score (0-100, higher = more notable action today): {score:.0f}

Write 2-4 sentences. Be specific and avoid generic disclaimers. This is not investment advice, just a market-color summary of what's happening.
"""


class ModelRouter:
    def __init__(self, cheap_model: str, strong_model: str, escalation_threshold: float, cost_logger: CostLogger):
        self.cheap_model = cheap_model
        self.strong_model = strong_model
        self.escalation_threshold = escalation_threshold
        self.cost_logger = cost_logger
        self.client = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

    def analyze(self, q: Quote) -> tuple[str, str]:
        """Returns (commentary_text, model_used)."""
        score = compute_signal_score(q)
        model = self.strong_model if score >= self.escalation_threshold else self.cheap_model
        reason = "escalated: notable signal" if score >= self.escalation_threshold else "routine"

        prompt = _build_prompt(q, score)
        response = self.client.messages.create(
            model=model,
            max_tokens=300,
            messages=[{"role": "user", "content": prompt}],
        )

        text = "".join(block.text for block in response.content if getattr(block, "type", None) == "text")
        usage = response.usage
        self.cost_logger.log(
            ticker=q.ticker,
            model=model,
            input_tokens=usage.input_tokens,
            output_tokens=usage.output_tokens,
            reason=reason,
        )
        return text.strip(), model
