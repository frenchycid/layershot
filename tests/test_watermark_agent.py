"""Tests for WatermarkAgent."""

import numpy as np
from pathlib import Path
from PIL import Image

from agents.watermark_agent import WatermarkAgent


def _make_image(width: int = 200, height: int = 200, color: tuple = (100, 150, 200)) -> Image.Image:
    """Create a solid-color test image."""
    return Image.new("RGB", (width, height), color)


def test_apply_returns_same_size():
    """apply() must return an image of the same dimensions as the input."""
    agent = WatermarkAgent()
    img = _make_image(320, 240)
    result = agent.apply(img, "LayerShot")
    assert result.size == img.size


def test_watermark_modifies_pixels():
    """apply() must visibly modify at least some pixels (watermark is visible)."""
    agent = WatermarkAgent(font_size=36)
    img = _make_image(400, 400, color=(50, 50, 50))
    result = agent.apply(img, "WATERMARK", opacity=200)

    orig_arr = np.array(img)
    result_arr = np.array(result)

    # At least one pixel must differ
    diff = np.abs(orig_arr.astype(int) - result_arr.astype(int))
    assert diff.max() > 0, "Expected watermark to modify at least one pixel"


def test_apply_opacity_zero_unchanged():
    """apply() with opacity=0 must return an image identical to the original."""
    agent = WatermarkAgent()
    img = _make_image(200, 200, color=(80, 120, 160))
    result = agent.apply(img, "invisible", opacity=0)

    orig_arr = np.array(img)
    result_arr = np.array(result)

    assert np.array_equal(orig_arr, result_arr), (
        "With opacity=0 the output must be pixel-identical to the input"
    )


def test_batch_processes_all_png_jpg(tmp_path: Path):
    """batch() must process every PNG and JPG in input_dir and write them to output_dir."""
    input_dir = tmp_path / "input"
    output_dir = tmp_path / "output"
    input_dir.mkdir()

    # Create 2 PNGs and 1 JPG — plus a non-image file that should be ignored
    _make_image(100, 100).save(input_dir / "a.png")
    _make_image(100, 100).save(input_dir / "b.png")
    _make_image(100, 100).save(input_dir / "c.jpg")
    (input_dir / "notes.txt").write_text("ignore me")

    agent = WatermarkAgent()
    outputs = agent.batch(input_dir, output_dir, "© LayerShot")

    assert len(outputs) == 3
    assert all(p.exists() for p in outputs)
    # Output files must live in output_dir
    assert all(p.parent == output_dir for p in outputs)
