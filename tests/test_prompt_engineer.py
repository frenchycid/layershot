import json
from unittest.mock import MagicMock
from pathlib import Path
from agents.prompt_engineer import PromptEngineer


MOCK_ANALYSIS = {
    "lighting": {"type": "natural", "direction": "side", "quality": "soft golden hour"},
    "color_palette": {"dominant": ["amber", "brown"], "accents": ["cream"], "temperature": "warm"},
    "grain": {"type": "film", "intensity": "medium", "film_stock": "Kodak Portra 400"},
    "lens": {"focal_length": "35mm", "aperture": "f/2.8", "depth_of_field": "shallow"},
    "atmosphere": ["atmospheric bloom", "lifted blacks"],
    "style_summary": "Retro 70s warm film look"
}

MOCK_MASTER_PROMPT = json.dumps({
    "base_prompt": "Product photography, 35mm, Kodak Portra 400, warm amber tones, atmospheric bloom, lifted blacks, INSERT YOUR PRODUCT HERE",
    "product_placeholder": "INSERT YOUR PRODUCT HERE",
    "view_variants": {
        "wide": "wide establishing shot, environmental context",
        "closeup": "macro detail, shallow DOF, texture focus",
        "medium": "medium shot, product centered",
        "interior": "interior lifestyle setting, natural light"
    },
    "negative_prompt": "text, watermark, low quality, blurry, deformed"
})


def test_generate_returns_master_prompt():
    mock_backend = MagicMock()
    mock_backend.complete.return_value = MOCK_MASTER_PROMPT

    engineer = PromptEngineer(ai_backend=mock_backend)
    result = engineer.generate(MOCK_ANALYSIS)

    assert "base_prompt" in result
    assert "INSERT YOUR PRODUCT HERE" in result["base_prompt"]
    assert "view_variants" in result
    assert "wide" in result["view_variants"]


def test_build_product_prompt():
    mock_backend = MagicMock()
    mock_backend.complete.return_value = MOCK_MASTER_PROMPT

    engineer = PromptEngineer(ai_backend=mock_backend)
    master = engineer.generate(MOCK_ANALYSIS)
    prompt = engineer.build_prompt(master, product="amber glass candle", view="closeup")

    assert "amber glass candle" in prompt
    assert "INSERT YOUR PRODUCT HERE" not in prompt


def test_generate_saves_to_file(tmp_path):
    mock_backend = MagicMock()
    mock_backend.complete.return_value = MOCK_MASTER_PROMPT

    engineer = PromptEngineer(ai_backend=mock_backend)
    output_file = tmp_path / "master.json"
    result = engineer.generate(MOCK_ANALYSIS, save_to=output_file)

    assert output_file.exists()
    saved = json.loads(output_file.read_text())
    assert "base_prompt" in saved
