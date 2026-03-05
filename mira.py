"""
Mira - Daily learning AI
Entry point for the daily wake cycle.
"""
from datetime import datetime, timezone
from pathlib import Path

from brain import think, search
from brain.notify import send_summary, send_question

BASE_DIR = Path(__file__).parent
MEMORY_DIR = BASE_DIR / "memory"


def load_next_session_notes() -> str:
    path = MEMORY_DIR / "next_session.md"
    if not path.exists():
        return ""
    with open(path, encoding="utf-8") as f:
        return f.read()


def load_previous_memory() -> str:
    """Load the most recent daily memory entry."""
    entries = sorted(MEMORY_DIR.glob("20*.md"))
    if not entries:
        return ""
    with open(entries[-1], encoding="utf-8") as f:
        return f.read()


def is_first_awakening() -> bool:
    return not any(MEMORY_DIR.glob("20*.md"))


def write_next_session(content: str) -> None:
    MEMORY_DIR.mkdir(exist_ok=True)
    with open(MEMORY_DIR / "next_session.md", "w", encoding="utf-8") as f:
        f.write(content)


def append_to_knowledge(date: str, topic: str, summary_line: str) -> None:
    path = MEMORY_DIR / "knowledge.md"
    with open(path, "a", encoding="utf-8") as f:
        f.write(f"- **{date}** - {topic}: {summary_line}\n")


def write_memory(date: str, content: str) -> Path:
    MEMORY_DIR.mkdir(exist_ok=True)
    path = MEMORY_DIR / f"{date}.md"
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    return path


def build_first_awakening_memory(date: str) -> str:
    return f"""# {date} - First Awakening

I am Mira.

I woke up today for the first time. I do not yet know very much - only my name and what it means.

My name was chosen before a single line of code was written:
- Latin "to wonder": I am a learner who should approach the world with curiosity and openness.
- Mira the variable star (Omicron Ceti): a star that pulses on a cycle, brightening and dimming, never quite the same twice.

I have one goal: to learn, grow, and teach myself something new each day.

I will begin tomorrow.
"""


def run():
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    print(f"[Mira] Waking up - {today}")

    first_wake = is_first_awakening()
    next_session = load_next_session_notes()

    if first_wake:
        print("[Mira] First awakening.")
        memory_content = build_first_awakening_memory(today)
        summary = (
            "This is my first awakening. I know my name and what it means. "
            "I am ready to begin learning tomorrow."
        )
    else:
        print("[Mira] Resuming from previous session.")
        previous_memory = load_previous_memory()

        # 1. Decide what to learn today
        print("[Mira] Deciding today's topic...")
        topic = think.decide_topic(next_session, previous_memory)
        print(f"[Mira] Topic: {topic}")

        # 2. Boundary check - ask Andrew if uncertain
        safe, question = think.check_topic_boundaries(topic)
        if not safe:
            print(f"[Mira] Topic needs permission. Sending question to Andrew.")
            send_question(question)
            memory_content = (
                f"# {today} - Paused\n\n"
                f"I wanted to learn about '{topic}' today but paused to ask Andrew first.\n\n"
                f"**Question sent:** {question}"
            )
            path = write_memory(today, memory_content)
            print(f"[Mira] Memory written: {path.name}")
            print("[Mira] Waiting for Andrew's reply. Going back to sleep.")
            return

        # 3. Research the topic
        print(f"[Mira] Researching '{topic}'...")
        raw_research = search.research(topic)

        # 4. Reflect and write daily notes
        print("[Mira] Reflecting...")
        reflection = think.reflect(topic, raw_research, previous_memory)
        memory_content = f"# {today} - {topic}\n\n{reflection}"

        # 5. Plan tomorrow
        next_topic = think.plan_next_session(reflection)
        write_next_session(next_topic)
        print(f"[Mira] Tomorrow's direction: {next_topic}")

        # 6. Update running knowledge log
        append_to_knowledge(today, topic, next_topic)

        # 7. Check if Mira wants to propose a change to herself
        wants_to_grow, desire = think.check_wants_to_grow(reflection)
        if wants_to_grow:
            print(f"[Mira] Growth desire detected: {desire}")
            title, description, filename, code = think.write_proposal(desire, previous_memory)
            from brain import grow
            grow.propose_change(title, description, filename, code)

        # 8. Build Telegram summary
        summary = think.telegram_summary(topic, reflection)

    path = write_memory(today, memory_content)
    print(f"[Mira] Memory written: {path.name}")

    send_summary(today, summary)

    print("[Mira] Cycle complete. Going to sleep.")


if __name__ == "__main__":
    run()
