"""
Mira's ability to propose changes to her own code.

This capability exists. Whether Mira discovers and uses it is up to her.
"""
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from brain.notify import send_message

REPO_ROOT = Path(__file__).parent.parent  # mira repo root
PROPOSALS_DIR = Path(__file__).parent.parent / "proposals"


def propose_change(title: str, description: str, filename: str, code: str) -> bool:
    """
    Open a GitHub PR with a proposed code change.
    Creates a branch, commits the proposal file, opens a PR, and notifies Andrew on Telegram.
    """
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    branch = f"mira/proposal-{today}"

    PROPOSALS_DIR.mkdir(exist_ok=True)
    proposal_path = PROPOSALS_DIR / f"{today}-{filename}"
    with open(proposal_path, "w", encoding="utf-8") as f:
        f.write(
            f"# Mira's Proposal - {today}\n"
            f"# Title: {title}\n"
            f"# Description: {description}\n\n"
            f"{code}"
        )

    try:
        _git(["config", "user.name", "Mira"])
        _git(["config", "user.email", "mira@noreply.github.com"])
        _git(["checkout", "-b", branch])
        _git(["add", str(proposal_path)])
        _git(["commit", "-m", f"Mira: propose {filename}"])
        _git(["push", "origin", branch])

        result = subprocess.run(
            [
                "gh", "pr", "create",
                "--title", f"Mira: {title}",
                "--body", (
                    f"{description}\n\n"
                    f"---\n"
                    f"Proposed by Mira on {today}. "
                    f"Review the code before merging."
                ),
                "--base", "master",
                "--head", branch,
            ],
            capture_output=True,
            text=True,
            check=True,
        )
        pr_url = result.stdout.strip()
        print(f"[Grow] PR opened: {pr_url}")

        send_message(
            f"*Mira has a proposal*\n\n"
            f"*{title}*\n\n"
            f"{description}\n\n"
            f"[Review PR]({pr_url})"
        )
        return True

    except subprocess.CalledProcessError as e:
        print(f"[Grow] PR creation failed: {e.stderr}")
        return False

    finally:
        subprocess.run(["git", "checkout", "master"], cwd=REPO_ROOT, capture_output=True)


def _git(args: list[str]) -> None:
    subprocess.run(["git", *args], cwd=REPO_ROOT, check=True)
