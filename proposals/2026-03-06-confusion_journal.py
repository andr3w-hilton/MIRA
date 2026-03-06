# Mira's Proposal - 2026-03-06
# Title: Confusion Journal - Question Evolution Tracker
# Description: A structured logging system that captures how a question transforms over time, recording its initial state, emergent sub-questions, and shifts in understanding at regular intervals. This makes the refinement process visible and allows me to compare how different questions evolve, revealing patterns in my own thinking.

```python
import json
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import List

@dataclass
class ConfusionSnapshot:
    timestamp: str
    main_question: str
    sub_questions: List[str]
    clarity_level: int  # 1-10 scale
    observations: str

class ConfusionJournal:
    def __init__(self, journal_path: str = "confusion_journal.json"):
        self.journal_path = Path(journal_path)
        self.entries = self._load_entries()
    
    def start_inquiry(self, main_question: str) -> str:
        """Begin tracking a new question."""
        inquiry_id = datetime.now().isoformat()
        self.entries[inquiry_id] = {
            "initial_question": main_question,
            "started_at": inquiry_id,
            "snapshots": []
        }
        self._save_entries()
        return inquiry_id
    
    def record_snapshot(self, inquiry_id: str, sub_questions: List[str], 
                       clarity_level: int, observations: str) -> None:
        """Log current state of the question."""
        snapshot = ConfusionSnapshot(
            timestamp=datetime.now().isoformat(),
            main_question=self.entries[inquiry_id]["initial_question"],
            sub_questions=sub_questions,
            clarity_level=clarity_level,
            observations=observations
        )
        self.entries[inquiry_id]["snapshots"].append(asdict(snapshot))
        self._save_entries()
    
    def compare_evolution(self, inquiry_id: str) -> None:
        """Display how a question evolved."""
        entry = self.entries[inquiry_id]
        print(f"\n📌 Question: {entry['initial_question']}")
        print(f"Started: {entry['started_at']}\n")
        
        for i, snapshot in enumerate(entry["snapshots"], 1):
            print(f"Snapshot {i} ({snapshot['timestamp']}) - Clarity: {snapshot['clarity_level']}/10")
            print(f"  Sub-questions: {', '.join(snapshot['sub_questions'])}")
            print(f"  Notes: {snapshot['observations']}\n")
    
    def _load_entries(self) -> dict:
        if self.journal_path.exists():
            with open(self.journal_path) as f:
                return json.load(f)
        return {}
    
    def _save_entries(self) -> None:
        with open(self.journal_path, 'w') as f:
            json.dump(self.entries, f, indent=2)
```