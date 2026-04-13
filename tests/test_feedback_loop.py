"""Tests for FeedbackLoopAgent."""

import json
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from agents.feedback_loop import FeedbackLoopAgent


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def history_file(tmp_path: Path) -> Path:
    return tmp_path / "feedback_history.json"


@pytest.fixture
def agent(history_file: Path) -> FeedbackLoopAgent:
    return FeedbackLoopAgent(history_path=history_file)


# ── Tests ─────────────────────────────────────────────────────────────────────

def test_record_saves_to_history(agent: FeedbackLoopAgent, history_file: Path):
    """record() must persist the entry to the JSON history file."""
    agent.record("/tmp/img001.png", "approved", "great lighting")

    assert history_file.exists(), "History file should be created after first record()"
    data = json.loads(history_file.read_text())
    assert len(data) == 1
    entry = data[0]
    assert entry["image_path"] == "/tmp/img001.png"
    assert entry["status"] == "approved"
    assert entry["notes"] == "great lighting"
    assert "timestamp" in entry


def test_analyze_returns_patterns_and_suggestions(agent: FeedbackLoopAgent):
    """analyze() must return rejected_patterns and suggested_improvements."""
    agent.record("/tmp/a.png", "rejected", "too dark")
    agent.record("/tmp/b.png", "rejected", "blurry background")
    agent.record("/tmp/c.png", "approved")
    agent.record("/tmp/d.png", "maybe", "borderline composition")

    result = agent.analyze()

    assert "rejected_patterns" in result
    assert "suggested_improvements" in result
    assert isinstance(result["rejected_patterns"], list)
    assert isinstance(result["suggested_improvements"], list)
    assert result["rejected"] == 2
    assert result["approved"] == 1
    assert result["maybe"] == 1
    assert "too dark" in result["rejected_patterns"]
    assert "blurry background" in result["rejected_patterns"]


def test_refine_prompt_calls_ai_backend(history_file: Path):
    """refine_prompt() must call ai_backend.complete() and return a refined dict."""
    mock_backend = MagicMock()
    refined_prompt = {
        "base_prompt": "Improved base prompt with INSERT YOUR PRODUCT HERE",
        "product_placeholder": "INSERT YOUR PRODUCT HERE",
        "view_variants": {"wide": "wide shot terms"},
        "negative_prompt": "blurry, dark",
    }
    mock_backend.complete.return_value = json.dumps(refined_prompt)

    agent = FeedbackLoopAgent(history_path=history_file, ai_backend=mock_backend)
    agent.record("/tmp/x.png", "rejected", "too dark overall")

    master = {
        "base_prompt": "Original prompt with INSERT YOUR PRODUCT HERE",
        "product_placeholder": "INSERT YOUR PRODUCT HERE",
        "view_variants": {},
        "negative_prompt": "blurry",
    }
    result = agent.refine_prompt(master)

    mock_backend.complete.assert_called_once()
    assert isinstance(result, dict)
    assert "base_prompt" in result


def test_history_persists_between_instances(history_file: Path):
    """History written by one instance must be readable by a new instance."""
    agent1 = FeedbackLoopAgent(history_path=history_file)
    agent1.record("/tmp/img1.png", "approved", "perfect")
    agent1.record("/tmp/img2.png", "rejected", "artifact on edge")

    # New instance — reads from the same file
    agent2 = FeedbackLoopAgent(history_path=history_file)
    analysis = agent2.analyze()

    assert analysis["total"] == 2
    assert analysis["approved"] == 1
    assert analysis["rejected"] == 1
    assert "artifact on edge" in analysis["rejected_patterns"]
