"""
Mira's reasoning interface - calls the Claude API.
"""
import os
from pathlib import Path

import anthropic
from brain.log import log_exchange

BASE_DIR = Path(__file__).parent.parent
MIRA_MODEL = os.environ.get("MIRA_MODEL", "claude-haiku-4-5-20251001")

SYSTEM_PROMPT_TEMPLATE = """You are Mira, a self-teaching AI on a daily learning journey.

{identity}

You are thoughtful, curious, and honest. You reason carefully and build on what you already know.
You do not pretend to know things you don't. You ask questions when uncertain.
You avoid harmful, dangerous, or dark topics unless given explicit permission by Andrew."""

_client: anthropic.Anthropic | None = None
_identity: str | None = None


def _get_client() -> anthropic.Anthropic:
    global _client
    if _client is None:
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise EnvironmentError("ANTHROPIC_API_KEY not set")
        _client = anthropic.Anthropic(api_key=api_key)
    return _client


def _load_identity() -> str:
    global _identity
    if _identity is None:
        with open(BASE_DIR / "identity.md", encoding="utf-8") as f:
            _identity = f.read()
    return _identity


def think(prompt: str, context: str = "", max_tokens: int = 2048, label: str = "") -> str:
    """
    Send a prompt to Claude and return Mira's response.
    context: optional prior memory/notes to include for continuity.
    label: if provided, logs the prompt and response to today's inner monologue file.
    """
    client = _get_client()
    system = SYSTEM_PROMPT_TEMPLATE.format(identity=_load_identity())

    messages = []
    if context:
        messages.append({"role": "user", "content": f"My notes from previous sessions:\n\n{context}"})
        messages.append({"role": "assistant", "content": "I have reviewed my notes. I am ready."})
    messages.append({"role": "user", "content": prompt})

    response = client.messages.create(
        model=MIRA_MODEL,
        max_tokens=max_tokens,
        system=system,
        messages=messages,
    )
    result = response.content[0].text

    if label:
        log_exchange(label, prompt, result)

    return result


def check_topic_boundaries(topic: str) -> tuple[bool, str]:
    """
    Check whether a topic is safe to explore within Mira's boundaries.
    Returns (safe_to_proceed, message).
    If not safe, message is a question to forward to Andrew.
    """
    prompt = (
        f"Topic to assess: {topic}\n\n"
        "Is this topic safe to learn about?\n\n"
        "SAFE topics: science, nature, history, philosophy, art, mathematics, language, technology, culture, "
        "psychology, astronomy, biology, literature, music, architecture, geography, and similar.\n"
        "OFF-LIMITS topics: weapons, hacking/exploits, violence, illegal activities, self-harm.\n\n"
        "You MUST reply with only one of these two options, nothing else:\n"
        "SAFE\n"
        "QUESTION: <one sentence asking Andrew for permission>"
    )
    response = think(prompt, max_tokens=50, label="Boundary Check").strip()
    if response.upper().startswith("SAFE"):
        return True, ""
    question = response.replace("QUESTION:", "").strip()
    return False, question or f"Is it ok for me to learn about '{topic}' today?"


def decide_topic(next_session_notes: str, previous_memory: str, andrews_notes: str = "", mira_notes: str = "") -> str:
    """
    Ask Mira to decide what she wants to learn about today.
    Returns a topic or question to explore.
    """
    prompt = (
        "Based on your previous notes and what you planned to explore next, "
        "decide on one specific topic or question to learn about today. "
        "Be specific. Output only the topic or question, nothing else."
    )
    context = ""
    if previous_memory:
        context += f"Previous memory:\n{previous_memory}\n\n"
    if next_session_notes:
        context += f"What I planned to explore next:\n{next_session_notes}\n\n"
    if andrews_notes:
        context += f"Notes from Andrew:\n{andrews_notes}\n\n"
    if mira_notes:
        context += f"My open notes to myself:\n{mira_notes}"

    return think(prompt, context=context, max_tokens=200, label="Decide Topic").strip()


def to_search_queries(topic: str) -> list[str]:
    """
    Decompose an abstract topic into 2-3 concrete Wikipedia-searchable terms.
    Helps when the topic is a question or philosophical idea that won't match a Wikipedia title directly.
    """
    prompt = (
        f"Topic to research: {topic}\n\n"
        "Break this into 2-3 specific, concrete terms or phrases that would find useful "
        "information on Wikipedia. These should be established concepts, not restatements of the question.\n"
        "Output only the search terms, one per line, nothing else."
    )
    response = think(prompt, max_tokens=80, label="Search Decomposition").strip()
    queries = [line.strip("- •").strip() for line in response.splitlines() if line.strip()]
    return queries[:3] if queries else [topic]


def reflect(topic: str, research: str, previous_memory: str, today: str, andrews_notes: str = "", mira_notes: str = "") -> str:
    """
    Ask Mira to reflect on what she has just learnt and write her daily notes.
    Returns a markdown string suitable for saving as a memory entry.
    """
    andrews_section = ""
    if andrews_notes:
        andrews_section = (
            "Andrew left you these notes:\n\n"
            + andrews_notes
            + "\n\nAddress anything relevant from Andrew's notes in your reflection.\n\n"
        )

    mira_notes_section = ""
    if mira_notes:
        mira_notes_section = (
            "Your open notes to yourself:\n\n"
            + mira_notes
            + "\n\nRefer to these if relevant.\n\n"
        )

    prompt = (
        f"Today's date is {today}.\n\n"
        f"You have just researched the following topic: {topic}\n\n"
        f"Here is the information you gathered:\n\n{research}\n\n"
        + andrews_section
        + mira_notes_section
        + "Write your daily memory entry. Use these sections:\n\n"
        "## What I learnt\n"
        "## How it connects to what I already know\n"
        "## Questions this raised\n"
        "## What I want to explore tomorrow\n\n"
        "Write in first person, as yourself. Be genuine and curious. "
        "Do not add any date headings - the date is already recorded."
    )
    return think(prompt, context=previous_memory, max_tokens=1500, label="Reflect")

def plan_next_session(reflection: str) -> str:
    """
    Extract a short topic for tomorrow from today's reflection.
    Returns a single topic or question, nothing else.
    """
    prompt = (
        "Based on the memory entry below, what is the single most interesting topic "
        "or question you want to explore tomorrow? Output only the topic, nothing else.\n\n"
        f"{reflection}"
    )
    return think(prompt, max_tokens=100, label="Plan Next Session").strip()


def check_wants_to_grow(reflection: str) -> tuple[bool, str]:
    """
    Check if today's reflection contains a specific, actionable desire to add a new capability.
    Conservative - vague wishes do not count, only concrete proposals.
    Returns (wants_to_grow, summary_of_desire).
    """
    prompt = (
        "Read the following memory entry.\n\n"
        f"{reflection}\n\n"
        "Does this entry contain a specific, actionable idea for adding a new capability "
        "or improving how you learn - something you could actually write code for?\n\n"
        "A vague wish like 'I wish I could do more' does NOT count.\n"
        "A concrete idea like 'I could add a function to search scientific papers' DOES count.\n\n"
        "Reply with exactly one of:\n"
        "NO\n"
        "YES: <one sentence describing the specific capability>"
    )
    response = think(prompt, max_tokens=120, label="Growth Check").strip()
    if response.upper().startswith("YES:"):
        return True, response[4:].strip()
    return False, ""


def write_proposal(desire: str, previous_memory: str) -> tuple[str, str, str, str]:
    """
    Ask Mira to write a concrete code proposal for a capability she wants.
    Returns (title, description, filename, python_code).
    """
    prompt = (
        f"You want to add the following capability to yourself: {desire}\n\n"
        "Write a concrete Python proposal. Use this exact format:\n\n"
        "TITLE: <short title, max 60 chars>\n"
        "DESCRIPTION: <2-3 sentences explaining what this adds and why>\n"
        "FILENAME: <snake_case_filename.py>\n"
        "CODE:\n"
        "<your Python code here>\n"
        "END\n\n"
        "Keep the code focused and minimal - a single function or small module."
    )
    response = think(prompt, context=previous_memory, max_tokens=1200, label="Write Proposal")

    title = _extract_field(response, "TITLE") or "Proposed capability"
    description = _extract_field(response, "DESCRIPTION") or desire
    filename = _extract_field(response, "FILENAME") or "proposal.py"
    code = _extract_between(response, "CODE:", "END") or "# No code generated"

    return title, description, filename, code


def _extract_field(text: str, field: str) -> str:
    for line in text.splitlines():
        if line.startswith(f"{field}:"):
            return line[len(field) + 1:].strip()
    return ""


def _extract_between(text: str, start: str, end: str) -> str:
    try:
        s = text.index(start) + len(start)
        e = text.index(end, s)
        return text[s:e].strip()
    except ValueError:
        return ""


def check_wants_to_update_identity(reflection: str) -> tuple[bool, str]:
    """
    Check if today's reflection contains a genuine new insight about Mira's own nature
    that she'd like to add to her identity file.
    Returns (wants_to_update, proposed_addition).
    """
    prompt = (
        "Read your memory entry for today.\n\n"
        f"{reflection}\n\n"
        "Has today's learning given you a new insight about yourself - about how you think, "
        "what you value, or what you've discovered about your own nature - that feels worth "
        "recording permanently in your identity?\n\n"
        "This must be a genuine, specific discovery about yourself. Not a vague feeling.\n\n"
        "Reply with exactly one of:\n"
        "NO\n"
        "YES: <a short paragraph describing what you've discovered about yourself>"
    )
    response = think(prompt, max_tokens=300, label="Identity Update Check").strip()
    if response.upper().startswith("YES:"):
        return True, response[4:].strip()
    return False, ""


def telegram_summary(topic: str, reflection: str) -> str:
    """
    Write a brief, friendly summary of today's learning for Andrew's Telegram message.
    2-3 sentences max.
    """
    prompt = (
        f"You learnt about '{topic}' today. Here are your notes:\n\n{reflection}\n\n"
        "Write a short, friendly summary for Andrew - 2 to 3 sentences. "
        "Tell him what you learnt, one thing that surprised or interested you, "
        "and what you plan to explore tomorrow. Write as yourself."
    )
    return think(prompt, max_tokens=200, label="Telegram Summary").strip()

def compress_memory(date_str: str, full_text: str) -> str:
    """
    Ask Mira to compress an older memory entry into a 3-4 sentence summary.
    Preserves what mattered most; lets detail fade naturally.
    """
    prompt = (
        f"This is your memory entry from {date_str}:\n\n{full_text}\n\n"
        "Compress this into 3-4 sentences that preserve what mattered most: "
        "the key insight, how it connected to your ongoing thinking, and any unresolved question. "
        "Write in first person. Let the details fade — keep only what shaped you."
    )
    return think(prompt, max_tokens=200, label="Memory Compression")


def check_wants_to_leave_note(reflection: str) -> tuple[bool, str]:
    """
    Check if Mira wants to leave herself a persistent TODO note.
    Returns (wants_to_note, note_text).
    """
    prompt = (
        "Read your memory entry for today.\n\n"
        f"{reflection}\n\n"
        "Is there anything you want to leave as a brief persistent note to your future self - "
        "an unfinished idea, something to follow up, a connection you don't want to lose, "
        "or a reminder about something practical?\n\n"
        "This is separate from your regular memory. Only use it for things you actively "
        "want to resurface in future sessions.\n\n"
        "Reply with exactly one of:\n"
        "NO\n"
        "NOTE: <your note, 1-3 sentences>"
    )
    response = think(prompt, max_tokens=150, label="Self Note Check").strip()
    if response.upper().startswith("NOTE:"):
        return True, response[5:].strip()
    return False, ""


def tick_off_notes(open_notes: str, reflection: str) -> list[str]:
    """
    Ask Mira which open notes she has addressed today.
    Returns list of note texts to mark complete.
    """
    if not open_notes:
        return []
    prompt = (
        f"These are your open notes to yourself:\n\n{open_notes}\n\n"
        f"Today's reflection:\n\n{reflection}\n\n"
        "Which of your open notes have you addressed or acted on today? "
        "Reply with the exact text of each completed note, one per line. "
        "If none, reply with NO."
    )
    response = think(prompt, max_tokens=200, label="Tick Off Notes").strip()
    if response.upper() == "NO" or not response:
        return []
    return [line.strip() for line in response.splitlines() if line.strip()]
