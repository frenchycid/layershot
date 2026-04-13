import json
from pathlib import Path
from unittest.mock import MagicMock

from agents.brief_parser import BriefParser


MOCK_PARSED = json.dumps({
    "brand": "Maison Lumière",
    "products": ["perfume bottle", "serum"],
    "palette": ["ivory", "gold", "black"],
    "style_keywords": ["luxury", "minimal", "editorial"],
    "deliverables": ["10 hero shots", "5 detail shots"],
    "constraints": ["no people", "white background only"],
})


def test_parse_returns_structured_dict():
    """parse() on plain text returns dict with all required keys + raw_brief."""
    mock_backend = MagicMock()
    mock_backend.complete.return_value = MOCK_PARSED

    parser = BriefParser(ai_backend=mock_backend)
    result = parser.parse("Client wants luxury perfume shots.")

    assert isinstance(result, dict)
    for key in ("brand", "products", "palette", "style_keywords", "deliverables", "constraints", "raw_brief"):
        assert key in result, f"Missing key: {key}"
    assert result["brand"] == "Maison Lumière"
    assert result["raw_brief"] == "Client wants luxury perfume shots."


def test_parse_calls_backend_complete_not_analyze_images():
    """parse() uses ai_backend.complete() — text only, no images."""
    mock_backend = MagicMock()
    mock_backend.complete.return_value = MOCK_PARSED

    parser = BriefParser(ai_backend=mock_backend)
    parser.parse("Some brief text.")

    mock_backend.complete.assert_called_once()
    mock_backend.analyze_images.assert_not_called()


def test_load_brief_from_txt_file(tmp_path):
    """load_brief() reads file content when source ends with .txt and exists."""
    brief_file = tmp_path / "brief.txt"
    brief_file.write_text("We need 5 product shots for our new skincare line.", encoding="utf-8")

    parser = BriefParser(ai_backend=MagicMock())
    content = parser.load_brief(str(brief_file))

    assert content == "We need 5 product shots for our new skincare line."


def test_load_brief_from_direct_text():
    """load_brief() returns text as-is when it's not a .txt file path."""
    raw = "Direct brief: minimalist jewellery campaign, black background, macro lens."

    parser = BriefParser(ai_backend=MagicMock())
    result = parser.load_brief(raw)

    assert result == raw


def test_parse_saves_json_when_save_to_provided(tmp_path):
    """parse(..., save_to=path) writes valid JSON to disk."""
    mock_backend = MagicMock()
    mock_backend.complete.return_value = MOCK_PARSED

    parser = BriefParser(ai_backend=mock_backend)
    output_file = tmp_path / "parsed_brief.json"
    result = parser.parse("Brief about sneakers campaign.", save_to=output_file)

    assert output_file.exists()
    saved = json.loads(output_file.read_text(encoding="utf-8"))
    assert saved["brand"] == "Maison Lumière"
    assert saved["raw_brief"] == "Brief about sneakers campaign."
    assert saved == result
