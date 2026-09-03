"""Terminal dashboard rendering using rich."""

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text

from .data_fetch import Quote

console = Console()


def render_dashboard(rows: list[tuple[Quote, str, str]]) -> None:
    """rows: list of (Quote, ai_commentary, model_used)"""
    console.clear()

    table = Table(title="Financial Analyzer", show_lines=True, expand=True)
    table.add_column("Ticker", style="bold")
    table.add_column("Price")
    table.add_column("Chg %")
    table.add_column("Day Range")
    table.add_column("52wk Range")
    table.add_column("Volume")
    table.add_column("50d/200d MA")
    table.add_column("Model")

    for q, _, model in rows:
        chg_style = "green" if q.change_pct >= 0 else "red"
        table.add_row(
            q.ticker,
            f"{q.price:.2f}",
            Text(f"{q.change_pct:+.2f}%", style=chg_style),
            f"{q.day_low:.2f} - {q.day_high:.2f}",
            f"{q.week52_low:.2f} - {q.week52_high:.2f}",
            f"{q.volume:,}",
            f"{q.ma50:.2f} / {q.ma200:.2f}" if q.ma50 and q.ma200 else "n/a",
            model,
        )

    console.print(table)

    for q, commentary, model in rows:
        console.print(
            Panel(
                commentary,
                title=f"AI Read: {q.ticker} ({model})",
                border_style="cyan",
            )
        )
