import json
import logging
from pathlib import Path
from typing import List, Dict, Any

logger = logging.getLogger("parksense.history")

class HistoryStorage:
    def __init__(self, file_path: str):
        self.file_path = Path(file_path)
        # Ensure parent directory exists
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        # Initialize if not exists
        if not self.file_path.exists():
            self._save([])

    def _load(self) -> List[Dict[str, Any]]:
        try:
            with open(self.file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load history: {e}")
            return []

    def _save(self, data: List[Dict[str, Any]]) -> None:
        try:
            with open(self.file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save history: {e}")

    def add_record(self, record: Dict[str, Any]) -> None:
        """Add a new analysis record to history."""
        history = self._load()
        history.insert(0, record)  # Add to beginning
        # Keep only the last 100 records to prevent file from growing indefinitely
        if len(history) > 100:
            history = history[:100]
        self._save(history)

    def get_history(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Retrieve recent history records."""
        history = self._load()
        return history[:limit]

    def get_record(self, record_id: str) -> Dict[str, Any]:
        """Retrieve a specific record by ID."""
        history = self._load()
        for record in history:
            if record.get("id") == record_id:
                return record
        return None
