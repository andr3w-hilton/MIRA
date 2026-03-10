"""
Mira's memory decay system.

Memories move through three tiers over time:
  Active     (0–6 days)  — full text loaded as context
  Compressed (7–29 days) — 3-4 sentence summary Mira wrote herself
  Archived   (30+ days)  — single line in archive.md, not loaded unless relevant

High-salience sessions (led to identity update or growth proposal) have extended
thresholds, so memories that genuinely shaped Mira survive longer before fading.
"""
import json
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
MEMORY_DIR = BASE_DIR / "memory"
COMPRESSED_DIR = MEMORY_DIR / "compressed"
ARCHIVE_PATH = MEMORY_DIR / "archive.md"
SALIENCE_PATH = MEMORY_DIR / "salience.json"

# Age thresholds (days) — salience bonus extends these
COMPRESS_AFTER = 7
ARCHIVE_AFTER = 30
SALIENCE_COMPRESS_BONUS = 7   # identity update or growth proposal → +7 days active
SALIENCE_ARCHIVE_BONUS = 30   # same → +30 days compressed before archiving


# --- Salience tracking ---

def _load_salience() -> dict:
    if not SALIENCE_PATH.exists():
        return {}
    with open(SALIENCE_PATH, encoding="utf-8") as f:
        return json.load(f)


def _save_salience(data: dict) -> None:
    with open(SALIENCE_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def update_salience(date_str: str, identity_updated: bool, growth_proposed: bool) -> None:
    """Record salience signals for a completed session."""
    data = _load_salience()
    score = (2 if identity_updated else 0) + (1 if growth_proposed else 0)
    data[date_str] = score
    _save_salience(data)


# --- Threshold helpers ---

def _days_old(date_str: str, today_str: str) -> int:
    d = datetime.strptime(date_str, "%Y-%m-%d").date()
    t = datetime.strptime(today_str, "%Y-%m-%d").date()
    return (t - d).days


def _compress_threshold(score: int) -> int:
    return COMPRESS_AFTER + (SALIENCE_COMPRESS_BONUS if score >= 1 else 0)


def _archive_threshold(score: int) -> int:
    return ARCHIVE_AFTER + (SALIENCE_ARCHIVE_BONUS if score >= 1 else 0)


# --- Decay pass ---

def run_decay_pass(today: str) -> None:
    """
    Run at end of each session. Compresses or archives daily memory files
    that have aged past their threshold. Today's entry is never touched.
    """
    from brain import think as _think  # late import to avoid circular dependency

    COMPRESSED_DIR.mkdir(exist_ok=True)
    salience = _load_salience()

    for path in sorted(MEMORY_DIR.glob("20*.md")):
        date_str = path.stem
        if date_str == today:
            continue

        age = _days_old(date_str, today)
        score = salience.get(date_str, 0)
        compressed_path = COMPRESSED_DIR / f"{date_str}.md"

        if age >= _archive_threshold(score):
            _ensure_archived(date_str, path, compressed_path)
        elif age >= _compress_threshold(score) and not compressed_path.exists():
            print(f"[Memory] Compressing {date_str} (age={age}d, salience={score})")
            full_text = path.read_text(encoding="utf-8")
            summary = _think.compress_memory(date_str, full_text)
            compressed_path.write_text(summary, encoding="utf-8")


def _ensure_archived(date_str: str, full_path: Path, compressed_path: Path) -> None:
    """Append a single-line entry to archive.md if not already present."""
    if ARCHIVE_PATH.exists() and date_str in ARCHIVE_PATH.read_text(encoding="utf-8"):
        return

    # Use first sentence of compressed summary if available, else first content line
    if compressed_path.exists():
        source = compressed_path.read_text(encoding="utf-8").strip()
    else:
        source = full_path.read_text(encoding="utf-8")

    archive_line = ""
    for line in source.splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            archive_line = line[:200]
            break

    with open(ARCHIVE_PATH, "a", encoding="utf-8") as f:
        f.write(f"- **{date_str}**: {archive_line}\n")

    print(f"[Memory] Archived {date_str}")


# --- Context builder ---

def build_context(today: str) -> str:
    """
    Build a tiered memory context string to pass into Mira's session.

    Replaces the old load_previous_memory() call. Returns:
      - Full text for active memories (recent days)
      - Compressed summaries for older memories
      - Archive index for oldest entries
    """
    salience = _load_salience()
    full_entries = []
    compressed_entries = []

    for path in sorted(MEMORY_DIR.glob("20*.md"), reverse=True):
        date_str = path.stem
        if date_str == today:
            continue

        age = _days_old(date_str, today)
        score = salience.get(date_str, 0)
        compressed_path = COMPRESSED_DIR / f"{date_str}.md"

        if age >= _archive_threshold(score):
            continue  # archived — not loaded into active context
        elif age >= _compress_threshold(score) and compressed_path.exists():
            compressed_entries.append((date_str, compressed_path.read_text(encoding="utf-8").strip()))
        else:
            full_entries.append((date_str, path.read_text(encoding="utf-8").strip()))

    sections = []

    if full_entries:
        parts = [f"### {d}\n\n{text}" for d, text in full_entries]
        sections.append("## Recent memory\n\n" + "\n\n---\n\n".join(parts))

    if compressed_entries:
        parts = [f"**{d}:** {text}" for d, text in compressed_entries]
        sections.append("## Older memories (compressed)\n\n" + "\n\n".join(parts))

    if ARCHIVE_PATH.exists():
        archive_text = ARCHIVE_PATH.read_text(encoding="utf-8").strip()
        if archive_text:
            sections.append(f"## Archived memories\n\n{archive_text}")

    return "\n\n---\n\n".join(sections)
