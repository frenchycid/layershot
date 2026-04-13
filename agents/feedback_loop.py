"""Feedback Loop Agent — Records review outcomes and refines prompts over time."""

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

log = logging.getLogger("feedback_loop")

VALID_STATUSES = {"approved", "rejected", "maybe"}


class FeedbackLoopAgent:
    """Tracks generation feedback and uses it to iteratively improve prompts."""

    def __init__(self, history_path: Path, ai_backend=None):
        self.history_path = Path(history_path)
        self.ai = ai_backend

    # ── Public API ──

    def record(self, image_path: str, status: str, notes: str = "") -> None:
        """Append a review entry to the persistent history JSON.

        Args:
            image_path: Path (or identifier) of the reviewed image.
            status: One of "approved", "rejected", "maybe".
            notes: Optional free-text comment.
        """
        if status not in VALID_STATUSES:
            raise ValueError(f"status must be one of {VALID_STATUSES}, got {status!r}")

        history = self._load()
        entry = {
            "image_path": image_path,
            "status": status,
            "notes": notes,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        history.append(entry)
        self._save(history)
        log.info(f"Recorded {status} for {image_path}")

    def analyze(self) -> dict:
        """Analyse the history and return rejection patterns and improvement suggestions.

        Returns:
            {
                "total": int,
                "approved": int,
                "rejected": int,
                "maybe": int,
                "rejected_patterns": list[str],   # notes from rejected entries
                "suggested_improvements": list[str],
            }
        """
        history = self._load()

        counts = {"approved": 0, "rejected": 0, "maybe": 0}
        rejected_notes: List[str] = []

        for entry in history:
            st = entry.get("status", "")
            if st in counts:
                counts[st] += 1
            if st == "rejected" and entry.get("notes"):
                rejected_notes.append(entry["notes"])

        # Derive simple improvement suggestions from rejection notes
        suggestions: List[str] = []
        if rejected_notes:
            suggestions.append("Address recurring issues: " + "; ".join(rejected_notes[:5]))
        if counts["rejected"] > counts["approved"]:
            suggestions.append("High rejection rate — consider revising base prompt style")
        if counts["maybe"] > 0:
            suggestions.append(
                f"{counts['maybe']} 'maybe' entries — tighten quality threshold or re-review"
            )

        return {
            "total": len(history),
            "approved": counts["approved"],
            "rejected": counts["rejected"],
            "maybe": counts["maybe"],
            "rejected_patterns": rejected_notes,
            "suggested_improvements": suggestions,
        }

    def refine_prompt(self, master_prompt: dict, history: Optional[List[dict]] = None) -> dict:
        """Use the AI backend to produce an improved version of master_prompt.

        Args:
            master_prompt: The current structured prompt dict.
            history: Optional explicit history list; defaults to reading from disk.

        Returns:
            Refined prompt dict (same structure as master_prompt).
        """
        if self.ai is None:
            raise RuntimeError("No AI backend configured — cannot refine prompt")

        if history is None:
            history = self._load()

        analysis = self.analyze()

        user_message = (
            "You are improving an AI image generation prompt based on feedback history.\n\n"
            f"Current master prompt:\n{json.dumps(master_prompt, indent=2)}\n\n"
            f"Feedback analysis:\n{json.dumps(analysis, indent=2)}\n\n"
            "Return an improved version of the master prompt as valid JSON, "
            "keeping the exact same top-level keys. Only change values that address "
            "the feedback."
        )

        raw = self.ai.complete(user_message)
        refined = self._parse_json(raw)
        log.info("Prompt refined via AI backend")
        return refined

    # ── Persistence helpers ──

    def _load(self) -> List[dict]:
        if not self.history_path.exists():
            return []
        try:
            return json.loads(self.history_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            log.warning(f"Could not read history from {self.history_path}, starting fresh")
            return []

    def _save(self, history: List[dict]) -> None:
        self.history_path.parent.mkdir(parents=True, exist_ok=True)
        self.history_path.write_text(
            json.dumps(history, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    def _parse_json(self, raw: str) -> dict:
        text = raw.strip()
        if "```json" in text:
            text = text.split("```json", 1)[1].split("```", 1)[0]
        elif "```" in text:
            text = text.split("```", 1)[1].split("```", 1)[0]
        return json.loads(text.strip())
