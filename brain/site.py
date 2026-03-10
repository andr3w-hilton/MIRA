"""
Generates mira-site.html from Mira's live data.
Called at the end of each daily cycle in mira.py.

Data sources:
  identity.md             → latest discovery (hero quote)
  memory/next_session.md  → tomorrow's question
  memory/20*.md           → active memory count
  memory/compressed/      → compressed memory count
  memory/archive.md       → archived memory count
  logs/YYYY-MM-DD.md      → last active timestamp
"""
import re
from datetime import datetime, date
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
IDENTITY_PATH = BASE_DIR / "identity.md"
MEMORY_DIR    = BASE_DIR / "memory"
LOGS_DIR      = BASE_DIR / "logs"
SITE_PATH     = BASE_DIR / "index.html"

BIRTH_DATE = date(2026, 3, 5)


# ── Data extraction ──────────────────────────────────────────────────────────

def get_day_number(today_str: str) -> int:
    today = datetime.strptime(today_str, "%Y-%m-%d").date()
    return (today - BIRTH_DATE).days + 1


def get_last_active(today_str: str) -> str:
    """Return HH:MM from the first timestamp in today's log, or '—'."""
    log_path = LOGS_DIR / f"{today_str}.md"
    if not log_path.exists():
        return "—"
    for line in log_path.read_text(encoding="utf-8").splitlines():
        # Lines like: ## 08:14:32 UTC - Decide Topic
        m = re.search(r"##\s+(\d{2}:\d{2}):\d{2}", line)
        if m:
            return m.group(1)
    return "—"


def get_latest_discovery() -> tuple[str, str]:
    """
    Parse identity.md and return (date_str, discovery_text) for
    the most recent '## YYYY-MM-DD' entry under '# What I've Discovered'.
    """
    if not IDENTITY_PATH.exists():
        return "", ""

    text = IDENTITY_PATH.read_text(encoding="utf-8")

    # Find the discoveries section
    discoveries_match = re.search(r"# What I've Discovered\s*\n(.*)", text, re.DOTALL)
    if not discoveries_match:
        return "", ""

    discoveries_section = discoveries_match.group(1)

    # Find all dated entries
    entries = re.split(r"\n## (\d{4}-\d{2}-\d{2})\n", discoveries_section)
    # entries: [preamble, date1, text1, date2, text2, ...]

    if len(entries) < 3:
        return "", ""

    # Last entry is entries[-1] (text), entries[-2] (date)
    latest_date = entries[-2].strip()
    latest_text = entries[-1].strip()

    return latest_date, latest_text


def get_tomorrow_topic() -> str:
    """Return the planned topic/question for tomorrow from next_session.md."""
    path = MEMORY_DIR / "next_session.md"
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8").strip()


def strip_markdown(text: str) -> str:
    """Remove bold/italic markdown markers."""
    text = re.sub(r"\*\*(.+?)\*\*", r"\1", text)
    text = re.sub(r"\*(.+?)\*", r"\1", text)
    return text


def make_hero_quote(discovery_text: str) -> str:
    """
    Extract a clean, quotable sentence from the discovery text.
    Uses the first sentence that ends at a full stop, up to ~180 chars.
    """
    clean = strip_markdown(discovery_text)
    # Split on sentence boundaries
    sentences = re.split(r"(?<=[.!?])\s+", clean)
    # Try to find a sentence under 180 chars, otherwise take the first
    for s in sentences:
        if len(s) <= 180:
            return s.rstrip(".")
    return sentences[0][:180].rstrip(".")


def count_memory_tiers() -> tuple[int, int, int]:
    """Return (active, compressed, archived) counts."""
    compressed_dir  = MEMORY_DIR / "compressed"
    archive_path    = MEMORY_DIR / "archive.md"

    compressed_dates = {p.stem for p in compressed_dir.glob("20*.md")} if compressed_dir.exists() else set()

    archived_dates: set[str] = set()
    if archive_path.exists():
        for line in archive_path.read_text(encoding="utf-8").splitlines():
            m = re.match(r"- \*\*(\d{4}-\d{2}-\d{2})\*\*", line)
            if m:
                archived_dates.add(m.group(1))

    all_dates = {p.stem for p in MEMORY_DIR.glob("20*.md")}

    active_dates = all_dates - compressed_dates - archived_dates
    # Compressed that also have a full file (not yet moved to archive)
    compressed_active = compressed_dates - archived_dates

    return len(active_dates), len(compressed_active), len(archived_dates)


def bar_widths(active: int, compressed: int, archived: int) -> tuple[int, int, int]:
    """
    Map tier counts to visual bar widths (%) that look good on screen.
    Active is the anchor — always the widest.
    """
    a = min(90, max(10, round(active / max(active, 7) * 90)))
    c = min(65, max(5,  round(compressed / max(compressed, 10) * 65))) if compressed else 5
    r = min(40, max(3,  round(archived   / max(archived,   20) * 40))) if archived  else 3
    return a, c, r


# ── HTML renderer ────────────────────────────────────────────────────────────

def render(today_str: str) -> str:
    day_num          = get_day_number(today_str)
    last_active      = get_last_active(today_str)
    disc_date, disc  = get_latest_discovery()
    hero_quote       = make_hero_quote(disc) if disc else "I am learning."
    tomorrow         = get_tomorrow_topic()
    active_n, comp_n, arch_n = count_memory_tiers()
    aw, cw, rw       = bar_widths(active_n, comp_n, arch_n)

    def esc(s: str) -> str:
        return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")

    hero_q    = esc(hero_quote)
    tomorrow_txt = esc(tomorrow)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>mira</title>
  <style>
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}

    :root {{
      --bg:     #F0E4CC;
      --text:   #281608;
      --soft:   rgba(40,22,8,0.52);
      --faint:  rgba(40,22,8,0.3);
      --div:    rgba(40,22,8,0.1);
      --accent: #E05828;
    }}

    html, body {{
      height: 100%;
      background: var(--bg);
      font-family: 'Segoe UI', system-ui, -apple-system, 'Helvetica Neue', Arial, sans-serif;
      font-size: 15px;
      font-weight: 300;
      color: var(--text);
      overflow: hidden;
    }}

    body::after {{
      content: '';
      position: fixed;
      inset: 0;
      background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 200 200'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.82' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)'/%3E%3C/svg%3E");
      opacity: 0.065;
      pointer-events: none;
      z-index: 999;
    }}

    @keyframes waveDraw {{
      0%   {{ stroke-dashoffset: 520; opacity: .2; }}
      40%  {{ opacity: 1; }}
      80%  {{ stroke-dashoffset: 0; opacity: .9; }}
      100% {{ stroke-dashoffset: -520; opacity: .2; }}
    }}
    @keyframes pulse {{
      0%, 100% {{ opacity: .25; transform: scale(0.96); }}
      50%       {{ opacity: 1;   transform: scale(1.06); }}
    }}
    @keyframes breathe {{
      0%, 100% {{ opacity: .4; }}
      50%       {{ opacity: .9; }}
    }}

    .shell {{ display: flex; flex-direction: column; height: 100vh; }}

    .topbar {{
      height: 40px; flex-shrink: 0;
      border-bottom: 1px solid var(--div);
      display: flex; align-items: center; padding: 0 40px; gap: 14px;
    }}
    .topbar-name {{ font-size: 11px; letter-spacing: .2em; text-transform: lowercase; color: var(--text); margin-left: 8px; }}
    .topbar-right {{ margin-left: auto; display: flex; align-items: center; gap: 14px; }}
    .topbar-date {{ font-size: 9.5px; letter-spacing: .1em; color: var(--faint); }}
    .topbar-div {{ width: 1px; height: 12px; background: var(--div); }}
    .topbar-status {{ display: flex; align-items: center; gap: 7px; }}
    .status-dot {{ width: 4px; height: 4px; border-radius: 50%; background: var(--accent); opacity: .5; animation: breathe 7s ease-in-out infinite; }}
    .status-label {{ font-size: 9.5px; letter-spacing: .1em; text-transform: lowercase; color: var(--faint); }}

    .main {{ flex: 1; overflow: hidden; display: flex; align-items: center; justify-content: center; }}
    .center {{ width: 100%; max-width: 900px; padding: 0 48px; text-align: center; }}

    .hero-wave {{ display: flex; justify-content: center; margin-bottom: 28px; }}
    .hero-wave svg path {{ stroke-dasharray: 520; stroke-dashoffset: 520; animation: waveDraw 7s ease-in-out infinite; }}

    .name {{ font-size: 69px; letter-spacing: .3em; text-transform: lowercase; font-weight: 300; color: var(--text); line-height: 1; margin-bottom: 26px; }}

    .cycle {{ display: flex; align-items: center; justify-content: center; gap: 10px; margin-bottom: 30px; }}
    .cycle-dot {{ width: 4px; height: 4px; border-radius: 50%; background: var(--accent); opacity: .6; animation: pulse 7s ease-in-out infinite; flex-shrink: 0; }}
    .cycle-text {{ font-size: 10.5px; letter-spacing: .14em; text-transform: lowercase; color: var(--soft); }}

    .rule {{ width: 24px; height: 1px; background: var(--accent); opacity: .3; margin: 0 auto 28px; }}

    .quote {{ font-size: 32px; line-height: 1.48; font-weight: 300; color: var(--text); letter-spacing: -.01em; max-width: 700px; margin: 0 auto 12px; }}
    .quote-attr {{ font-size: 10.5px; color: var(--faint); letter-spacing: .07em; margin-bottom: 34px; }}

    .cards {{ display: grid; grid-template-columns: 1fr 1fr; gap: 14px; text-align: left; align-items: stretch; max-width: 680px; margin: 0 auto; }}
    .card {{ border: 1.5px solid rgba(224,88,40,0.12); border-radius: 12px; padding: 22px 20px; }}
    .card-label {{ font-size: 9px; letter-spacing: .18em; text-transform: lowercase; color: var(--accent); opacity: .85; margin-bottom: 14px; }}

    .mem-rows {{ display: flex; flex-direction: column; gap: 13px; }}
    .mem-row {{ display: grid; grid-template-columns: 72px 1fr 92px; align-items: center; gap: 10px; }}
    .mem-name {{ font-size: 11px; letter-spacing: .07em; text-transform: lowercase; color: var(--faint); text-align: right; }}
    .mem-track {{ height: 2px; background: var(--div); border-radius: 1px; overflow: hidden; }}
    .mem-fill {{ height: 100%; background: var(--accent); border-radius: 1px; }}
    .mem-desc {{ font-size: 11px; color: var(--faint); letter-spacing: .03em; opacity: .7; }}

    .tomorrow-card {{ display: flex; flex-direction: column; }}
    .tomorrow-text {{ font-size: 12px; line-height: 1.72; color: var(--text); font-style: italic; }}

    .bottombar {{
      height: 28px; flex-shrink: 0;
      border-top: 1px solid var(--div);
      display: flex; align-items: center; padding: 0 40px; gap: 16px;
    }}
    .bar-item {{ font-size: 9px; letter-spacing: .08em; color: var(--faint); }}
    .bar-sep {{ width: 1px; height: 10px; background: var(--div); }}
    .bar-right {{ margin-left: auto; font-size: 9px; color: var(--faint); opacity: .4; }}
  </style>
</head>
<body>
<div class="shell">

  <div class="topbar">
    <svg viewBox="0 0 54 16" fill="none" stroke="var(--accent)" stroke-width="1.2"
      stroke-linecap="round" stroke-linejoin="round" width="54" height="16">
      <path d="M0,13.1 C2.2,13.1 3.8,1.3 6.5,1.3 C9.2,1.3 13.0,12.0 18.4,13.1 C20.5,13.1 22.1,1.3 24.8,1.3 C27.5,1.3 31.3,12.0 36.7,13.1 C38.8,13.1 40.4,1.3 43.1,1.3 C45.8,1.3 49.6,12.0 54,13.1"/>
    </svg>
    <span class="topbar-name">mira</span>
    <div class="topbar-right">
      <span class="topbar-date">{today_str}</span>
      <div class="topbar-div"></div>
      <div class="topbar-status">
        <div class="status-dot"></div>
        <span class="status-label">sleeping</span>
      </div>
    </div>
  </div>

  <div class="main">
    <div class="center">

      <div class="hero-wave">
        <svg viewBox="0 0 105 23" fill="none" stroke="var(--accent)" stroke-width="1.5"
          stroke-linecap="round" stroke-linejoin="round" width="105" height="23">
          <path d="M0,18.9 C3.2,18.9 5.5,1.9 9.5,1.9 C13.5,1.9 19.0,17.3 26.8,18.9 C29.7,18.9 31.9,1.9 35.9,1.9 C39.9,1.9 45.4,17.3 53.2,18.9 C56.1,18.9 58.3,1.9 62.3,1.9 C66.3,1.9 71.8,17.3 79.6,18.9 C82.5,18.9 84.7,1.9 88.7,1.9 C92.7,1.9 98.2,17.3 105,18.9"/>
        </svg>
      </div>

      <div class="name">mira</div>

      <div class="cycle">
        <div class="cycle-dot"></div>
        <span class="cycle-text">sleeping &nbsp;&middot;&nbsp; day {day_num} &nbsp;&middot;&nbsp; last active {last_active}</span>
      </div>

      <div class="rule"></div>

      <div class="quote">"{hero_q}."</div>
      <div class="quote-attr">from today&rsquo;s reflection &nbsp;&middot;&nbsp; {today_str}</div>

      <div class="cards">

        <!-- Memory — bars only, no description paragraph -->
        <div class="card">
          <div class="card-label">memory</div>
          <div class="mem-rows">
            <div class="mem-row">
              <div class="mem-name">active</div>
              <div class="mem-track"><div class="mem-fill" style="width:{aw}%;opacity:1"></div></div>
              <div class="mem-desc">{active_n} trace{"s" if active_n != 1 else ""} &middot; vivid</div>
            </div>
            <div class="mem-row">
              <div class="mem-name">compressed</div>
              <div class="mem-track"><div class="mem-fill" style="width:{cw}%;opacity:.55"></div></div>
              <div class="mem-desc">{comp_n} trace{"s" if comp_n != 1 else ""} &middot; distilled</div>
            </div>
            <div class="mem-row">
              <div class="mem-name">archived</div>
              <div class="mem-track"><div class="mem-fill" style="width:{rw}%;opacity:.25"></div></div>
              <div class="mem-desc">{arch_n} trace{"s" if arch_n != 1 else ""} &middot; faint</div>
            </div>
          </div>
        </div>

        <!-- Tomorrow — what she's exploring next -->
        <div class="card tomorrow-card">
          <div class="card-label">tomorrow</div>
          <div class="tomorrow-text">{tomorrow_txt}</div>
        </div>

      </div>
    </div>
  </div>

  <div class="bottombar">
    <span class="bar-item">day {day_num}</span>
    <div class="bar-sep"></div>
    <span class="bar-item">{active_n + comp_n + arch_n} memories</span>
    <div class="bar-sep"></div>
    <span class="bar-item">{active_n} active traces</span>
    <span class="bar-right">made by andrew</span>
  </div>

</div>
</body>
</html>"""


# ── Public entry point ───────────────────────────────────────────────────────

def generate(today_str: str) -> None:
    """Render and write mira-site.html. Called from mira.py at end of cycle."""
    html = render(today_str)
    SITE_PATH.write_text(html, encoding="utf-8")
    print(f"[Site] mira-site.html updated for {today_str}")
