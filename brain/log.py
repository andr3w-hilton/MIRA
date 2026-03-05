"""
Mira's inner monologue log - records every prompt and response.
Gives visibility into her reasoning process, not just her conclusions.
"""
from datetime import datetime, timezone
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
LOGS_DIR = BASE_DIR / "logs"


def log_exchange(label: str, prompt: str, response: str) -> None:
    """Append a prompt/response pair to today's log file."""
    LOGS_DIR.mkdir(exist_ok=True)

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    timestamp = datetime.now(timezone.utc).strftime("%H:%M:%S UTC")
    path = LOGS_DIR / f"{today}.md"

    if not path.exists():
        with open(path, "w", encoding="utf-8") as f:
            f.write(f"# Mira - Inner Monologue - {today}\n\n")

    with open(path, "a", encoding="utf-8") as f:
        f.write(f"## {timestamp} - {label}\n\n")
        f.write(f"**Prompt:**\n\n{prompt}\n\n")
        f.write(f"**Response:**\n\n{response}\n\n")
        f.write("---\n\n")
