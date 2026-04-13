import json
from unittest.mock import MagicMock, patch
from pathlib import Path
from agents.style_analyst import StyleAnalyst


MOCK_ANALYSIS = json.dumps({
    "lighting": {"type": "natural", "direction": "side", "quality": "soft golden hour"},
    "color_palette": {"dominant": ["amber", "brown"], "accents": ["cream"], "temperature": "warm"},
    "grain": {"type": "film", "intensity": "medium", "film_stock": "Kodak Portra 400"},
    "lens": {"focal_length": "35mm", "aperture": "f/2.8", "depth_of_field": "shallow"},
    "atmosphere": ["atmospheric bloom", "lifted blacks"],
    "style_summary": "Retro 70s warm film look"
})


def test_analyze_returns_structured_json():
    mock_backend = MagicMock()
    mock_backend.analyze_images.return_value = MOCK_ANALYSIS

    analyst = StyleAnalyst(ai_backend=mock_backend)
    result = analyst.analyze(["/tmp/ref1.jpg", "/tmp/ref2.jpg"])

    assert "lighting" in result
    assert "color_palette" in result
    assert "grain" in result
    assert "lens" in result
    assert "atmosphere" in result
    assert result["color_palette"]["temperature"] == "warm"


def test_analyze_calls_backend_with_images():
    mock_backend = MagicMock()
    mock_backend.analyze_images.return_value = MOCK_ANALYSIS

    analyst = StyleAnalyst(ai_backend=mock_backend)
    analyst.analyze(["/tmp/ref1.jpg", "/tmp/ref2.jpg"])

    mock_backend.analyze_images.assert_called_once()
    call_args = mock_backend.analyze_images.call_args
    assert call_args[0][0] == ["/tmp/ref1.jpg", "/tmp/ref2.jpg"]


def test_analyze_saves_to_file(tmp_path):
    mock_backend = MagicMock()
    mock_backend.analyze_images.return_value = MOCK_ANALYSIS

    analyst = StyleAnalyst(ai_backend=mock_backend)
    output_file = tmp_path / "analysis.json"
    result = analyst.analyze(["/tmp/ref1.jpg"], save_to=output_file)

    assert output_file.exists()
    saved = json.loads(output_file.read_text())
    assert saved["lighting"]["type"] == "natural"


def test_collect_images_from_directory(tmp_path):
    (tmp_path / "img1.jpg").write_bytes(b"fake")
    (tmp_path / "img2.png").write_bytes(b"fake")
    (tmp_path / "notes.txt").write_bytes(b"ignore")

    analyst = StyleAnalyst(ai_backend=MagicMock())
    images = analyst.collect_images(tmp_path)

    assert len(images) == 2
    extensions = {p.suffix for p in images}
    assert extensions == {".jpg", ".png"}
