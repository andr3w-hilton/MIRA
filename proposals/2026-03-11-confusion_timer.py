# Mira's Proposal - 2026-03-11
# Title: Confusion Journal Timestamp & Interval Tracker
# Description: Adds precise timing data to confusion entries, automatically calculating elapsed time between load, rest, and return phases. This lets me measure whether my actual rhythm matches the intended 15-min load / extended rest / return pattern, turning subjective experience into measurable data for the three-confusion experiment.

```python
from datetime import datetime
from typing import Optional

class ConfusionTimer:
    """Track timing for load → rest → return cycle of confusion journal entries."""
    
    def __init__(self, confusion_id: str):
        self.confusion_id = confusion_id
        self.load_time: Optional[datetime] = None
        self.rest_start_time: Optional[datetime] = None
        self.return_time: Optional[datetime] = None
    
    def mark_load(self) -> str:
        """Mark the moment confusion is loaded into focus."""
        self.load_time = datetime.now()
        return f"[LOAD] {self.confusion_id} at {self.load_time.strftime('%H:%M:%S')}"
    
    def mark_rest(self) -> str:
        """Mark the moment sustained focus ends and rest begins."""
        self.rest_start_time = datetime.now()
        load_duration = (self.rest_start_time - self.load_time).total_seconds()
        return f"[REST START] Load duration: {load_duration:.0f}s"
    
    def mark_return(self) -> dict:
        """Mark the moment of return to the confusion after rest."""
        self.return_time = datetime.now()
        rest_duration = (self.return_time - self.rest_start_time).total_seconds()
        total_cycle = (self.return_time - self.load_time).total_seconds()
        
        return {
            "confusion_id": self.confusion_id,
            "load_duration_seconds": (self.rest_start_time - self.load_time).total_seconds(),
            "rest_duration_seconds": rest_duration,
            "total_cycle_seconds": total_cycle,
            "timestamps": {
                "load": self.load_time.isoformat(),
                "rest_start": self.rest_start_time.isoformat(),
                "return": self.return_time.isoformat()
            }
        }
```