"""Tests for PostProcessor agent — TDD style with synthetic PIL images."""

import numpy as np
import pytest
from pathlib import Path
from PIL import Image

from agents.post_processor import PostProcessor


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_image(width: int = 100, height: int = 100, color: tuple = (128, 64, 32)) -> Image.Image:
    """Create a solid-color RGB image for testing."""
    img = Image.new("RGB", (width, height), color=color)
    return img


def mean_rgb(img: Image.Image) -> tuple:
    """Return (R, G, B) mean pixel values for an image."""
    arr = np.array(img, dtype=float)
    return tuple(arr[:, :, c].mean() for c in range(3))


# ---------------------------------------------------------------------------
# 1. adjust_exposure
# ---------------------------------------------------------------------------

def test_adjust_exposure_increases_brightness():
    pp = PostProcessor()
    img = make_image(color=(100, 100, 100))
    result = pp.adjust_exposure(img, factor=1.5)

    assert isinstance(result, Image.Image)
    r, g, b = mean_rgb(result)
    # All channels should be brighter than original 100
    assert r > 100
    assert g > 100
    assert b > 100


def test_adjust_exposure_decreases_brightness():
    pp = PostProcessor()
    img = make_image(color=(200, 200, 200))
    result = pp.adjust_exposure(img, factor=0.5)

    assert isinstance(result, Image.Image)
    r, g, b = mean_rgb(result)
    assert r < 200
    assert g < 200
    assert b < 200


def test_adjust_exposure_factor_one_is_identity():
    pp = PostProcessor()
    img = make_image(color=(150, 80, 200))
    result = pp.adjust_exposure(img, factor=1.0)

    orig = mean_rgb(img)
    res = mean_rgb(result)
    for o, r in zip(orig, res):
        assert abs(o - r) < 2  # within 1 unit tolerance


# ---------------------------------------------------------------------------
# 2. adjust_saturation
# ---------------------------------------------------------------------------

def test_adjust_saturation_zero_returns_grayscale():
    pp = PostProcessor()
    img = make_image(color=(200, 50, 10))
    result = pp.adjust_saturation(img, factor=0.0)

    assert isinstance(result, Image.Image)
    r, g, b = mean_rgb(result)
    # A fully desaturated image has R == G == B
    assert abs(r - g) < 2
    assert abs(g - b) < 2


def test_adjust_saturation_increases_color_spread():
    pp = PostProcessor()
    # Use a color with moderate saturation
    img = make_image(color=(180, 100, 60))
    original_r, original_g, original_b = mean_rgb(img)

    result = pp.adjust_saturation(img, factor=2.0)
    assert isinstance(result, Image.Image)

    res_r, res_g, res_b = mean_rgb(result)
    # With higher saturation the dominant channel (R) should increase
    # or the spread between channels should widen
    orig_spread = original_r - original_b
    res_spread = res_r - res_b
    assert res_spread >= orig_spread


def test_adjust_saturation_factor_one_is_identity():
    pp = PostProcessor()
    img = make_image(color=(90, 140, 60))
    result = pp.adjust_saturation(img, factor=1.0)

    orig = mean_rgb(img)
    res = mean_rgb(result)
    for o, r in zip(orig, res):
        assert abs(o - r) < 2


# ---------------------------------------------------------------------------
# 3. adjust_temperature
# ---------------------------------------------------------------------------

def test_adjust_temperature_positive_shift_warms_image():
    pp = PostProcessor()
    img = make_image(color=(128, 128, 128))
    result = pp.adjust_temperature(img, shift=50)

    assert isinstance(result, Image.Image)
    r, g, b = mean_rgb(result)
    orig_r, orig_g, orig_b = mean_rgb(img)
    # Warm shift: red should increase, blue should decrease
    assert r > orig_r
    assert b < orig_b


def test_adjust_temperature_negative_shift_cools_image():
    pp = PostProcessor()
    img = make_image(color=(128, 128, 128))
    result = pp.adjust_temperature(img, shift=-50)

    assert isinstance(result, Image.Image)
    r, g, b = mean_rgb(result)
    orig_r, orig_g, orig_b = mean_rgb(img)
    # Cool shift: blue should increase, red should decrease
    assert b > orig_b
    assert r < orig_r


def test_adjust_temperature_zero_shift_is_identity():
    pp = PostProcessor()
    img = make_image(color=(100, 150, 200))
    result = pp.adjust_temperature(img, shift=0)

    orig = mean_rgb(img)
    res = mean_rgb(result)
    for o, r in zip(orig, res):
        assert abs(o - r) < 2


# ---------------------------------------------------------------------------
# 4. match_style
# ---------------------------------------------------------------------------

def test_match_style_returns_image():
    pp = PostProcessor()
    img = make_image(color=(100, 100, 100))
    ref = make_image(color=(200, 150, 80))
    result = pp.match_style(img, ref)

    assert isinstance(result, Image.Image)
    assert result.size == img.size


def test_match_style_moves_toward_reference_brightness():
    pp = PostProcessor()
    # Dark image, bright reference
    img = make_image(color=(50, 50, 50))
    ref = make_image(color=(200, 200, 200))
    result = pp.match_style(img, ref)

    orig_lum = sum(mean_rgb(img)) / 3
    res_lum = sum(mean_rgb(result)) / 3

    # Result should be brighter than original
    assert res_lum > orig_lum


def test_match_style_preserves_image_size():
    pp = PostProcessor()
    img = make_image(width=64, height=48, color=(100, 100, 100))
    ref = make_image(width=200, height=200, color=(200, 180, 160))
    result = pp.match_style(img, ref)

    assert result.size == (64, 48)


# ---------------------------------------------------------------------------
# 5. process — end-to-end pipeline
# ---------------------------------------------------------------------------

def test_process_creates_output_file(tmp_path):
    pp = PostProcessor()

    input_path = tmp_path / "input.png"
    ref_path = tmp_path / "reference.png"
    output_path = tmp_path / "output.png"

    make_image(color=(80, 80, 80)).save(input_path)
    make_image(color=(200, 160, 120)).save(ref_path)

    result = pp.process(input_path, ref_path, output_path)

    assert output_path.exists()
    assert result == output_path


def test_process_output_is_valid_image(tmp_path):
    pp = PostProcessor()

    input_path = tmp_path / "input.png"
    ref_path = tmp_path / "reference.png"
    output_path = tmp_path / "output.png"

    make_image(color=(60, 80, 100)).save(input_path)
    make_image(color=(180, 150, 100)).save(ref_path)

    pp.process(input_path, ref_path, output_path)

    loaded = Image.open(output_path)
    assert loaded.mode in ("RGB", "RGBA")
    assert loaded.size == (100, 100)


def test_process_creates_parent_dirs(tmp_path):
    pp = PostProcessor()

    input_path = tmp_path / "input.png"
    ref_path = tmp_path / "reference.png"
    output_path = tmp_path / "nested" / "deep" / "output.png"

    make_image(color=(100, 100, 100)).save(input_path)
    make_image(color=(200, 180, 160)).save(ref_path)

    pp.process(input_path, ref_path, output_path)

    assert output_path.exists()
