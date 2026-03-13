"""
Mira's notification interface - sends messages to Andrew via Telegram.
"""
import os
import requests

TELEGRAM_API = "https://api.telegram.org/bot{token}/sendMessage"
MAX_MESSAGE_LENGTH = 3800  # Telegram limit is 4096, leave headroom


def send_message(text: str, parse_mode: str | None = None) -> bool:
    """Send a message via the Telegram bot. Pass parse_mode='Markdown' for formatted messages."""
    bot_token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")

    if not bot_token or not chat_id:
        print("[Notify] Telegram credentials not set - skipping.")
        return False

    if len(text) > MAX_MESSAGE_LENGTH:
        truncated = text[:MAX_MESSAGE_LENGTH]
        # Trim to last newline to avoid breaking mid-Markdown token
        last_newline = truncated.rfind("\n")
        text = truncated[:last_newline] + "\n\n_(message truncated)_"

    payload: dict = {"chat_id": chat_id, "text": text}
    if parse_mode:
        payload["parse_mode"] = parse_mode

    try:
        response = requests.post(
            TELEGRAM_API.format(token=bot_token),
            json=payload,
            timeout=10,
        )
        response.raise_for_status()
        print("[Notify] Telegram message sent.")
        return True
    except requests.exceptions.HTTPError as e:
        body = e.response.text if e.response is not None else "no body"
        print(f"[Notify] Telegram send failed: {e} | response: {body}")
        return False
    except Exception as e:
        print(f"[Notify] Telegram send failed: {e}")
        return False


def send_summary(date: str, content: str) -> bool:
    """Send Mira's daily summary to Andrew."""
    message = f"*Mira - {date}*\n\n{content}"
    return send_message(message, parse_mode="Markdown")


def send_question(question: str) -> bool:
    """Send a question from Mira to Andrew when she needs guidance."""
    message = f"*Mira has a question:*\n\n{question}\n\n_Reply here and I will pick it up tomorrow._"
    return send_message(message, parse_mode="Markdown")
