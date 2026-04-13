"""Tests for BackgroundCompositor agent — rembg + PIL composition."""

from pathlib import Path
from unittest.mock import patch, MagicMock

import numpy as np
import pytest
from PIL import Image

from agents.background_compositor import BackgroundCompositor


def make_rgb_image(width: int = 100, height: int = 100, color=(200, 100, 50)) -> Image.Image:
    """Create a synthetic RGB image for testing."""
    arr = np.full((height, width, 3), color, dtype=np.uint8)
    return Image.fromarray(arr, mode="RGB")


def make_rgba_image(width: int = 100, height: int = 100, color=(200, 100, 50, 255)) -> Image.Image:
    """Create a synthetic RGBA image for testing."""
    arr = np.full((height, width, 4), color, dtype=np.uint8)
    return Image.fromarray(arr, mode="RGBA")


def make_fake_rembg_result(image: Image.Image) -> Image.Image:
    """Return an RGBA version of the image as rembg would."""
    rgba = image.convert("RGBA")
    # Make the center region opaque, edges transparent (simulates bg removal)
    arr = np.array(rgba)
    arr[:10, :, 3] = 0   # top strip transparent
    arr[-10:, :, 3] = 0  # bottom strip transparent
    return Image.fromarray(arr, mode="RGBA")


class TestRemoveBackground:
    def test_remove_background_returns_rgba(self):
        """remove_background() should return an RGBA image."""
        compositor = BackgroundCompositor()
        product_img = make_rgb_image(80, 80)

        with patch("agents.background_compositor.rembg_remove") as mock_remove:
            mock_remove.return_value = make_fake_rembg_result(product_img)
            result = compositor.remove_background(product_img)

        assert result.mode == "RGBA", f"Expected RGBA, got {result.mode}"
        mock_remove.assert_called_once()

    def test_remove_background_accepts_rgba_input(self):
        """remove_background() should also accept RGBA input."""
        compositor = BackgroundCompositor()
        product_img = make_rgba_image(80, 80)

        with patch("agents.background_compositor.rembg_remove") as mock_remove:
            mock_remove.return_value = make_fake_rembg_result(product_img)
            result = compositor.remove_background(product_img)

        assert result.mode == "RGBA"


class TestComposite:
    def test_composite_returns_same_size_as_background(self):
        """composite() output must match background dimensions."""
        compositor = BackgroundCompositor(product_scale=0.4)
        bg_img = make_rgb_image(400, 300, color=(50, 100, 150))
        product_img = make_rgba_image(80, 80, color=(200, 100, 50, 255))

        result = compositor.composite(product_img, bg_img)

        assert result.size == bg_img.size, (
            f"Expected {bg_img.size}, got {result.size}"
        )

    def test_composite_returns_rgb_or_rgba_image(self):
        """composite() should return a valid PIL Image."""
        compositor = BackgroundCompositor()
        bg_img = make_rgb_image(200, 200)
        product_img = make_rgba_image(50, 50)

        result = compositor.composite(product_img, bg_img)

        assert isinstance(result, Image.Image)
        assert result.mode in ("RGB", "RGBA")


class TestProductPositioning:
    def test_product_is_centered_horizontally_and_in_lower_half(self):
        """Product should be horizontally centered and positioned in the bottom half."""
        compositor = BackgroundCompositor(product_scale=0.3)

        bg_w, bg_h = 400, 400
        bg_img = make_rgb_image(bg_w, bg_h, color=(30, 30, 30))

        # Product with distinct color so we can locate it
        product_arr = np.zeros((60, 60, 4), dtype=np.uint8)
        product_arr[:, :] = [255, 0, 0, 255]  # fully red, fully opaque
        product_img = Image.fromarray(product_arr, mode="RGBA")

        result = compositor.composite(product_img, bg_img)
        result_arr = np.array(result.convert("RGB"))

        # Find rows and cols where red pixels dominate
        red_mask = (result_arr[:, :, 0] > 200) & (result_arr[:, :, 1] < 50) & (result_arr[:, :, 2] < 50)

        assert red_mask.any(), "Product pixels not found in composite"

        rows = np.where(red_mask.any(axis=1))[0]
        cols = np.where(red_mask.any(axis=0))[0]

        product_center_y = (rows.min() + rows.max()) / 2
        product_center_x = (cols.min() + cols.max()) / 2

        # Horizontal centering: product center within 20% of bg center
        assert abs(product_center_x - bg_w / 2) < bg_w * 0.20, (
            f"Product not centered horizontally: center_x={product_center_x}, bg_center={bg_w/2}"
        )

        # Vertical: product should be in lower half (center_y > bg_h * 0.4)
        assert product_center_y > bg_h * 0.4, (
            f"Product not in lower half: center_y={product_center_y}, threshold={bg_h * 0.4}"
        )


class TestProcess:
    def test_process_creates_output_file(self, tmp_path):
        """process() should load images, remove bg, composite, and write output."""
        compositor = BackgroundCompositor()

        product_path = tmp_path / "product.png"
        background_path = tmp_path / "background.png"
        output_path = tmp_path / "output.png"

        make_rgb_image(100, 100, color=(200, 150, 100)).save(product_path)
        make_rgb_image(300, 300, color=(100, 120, 140)).save(background_path)

        with patch("agents.background_compositor.rembg_remove") as mock_remove:
            mock_remove.return_value = make_rgba_image(100, 100)
            result = compositor.process(product_path, background_path, output_path)

        assert output_path.exists(), "Output file was not created"
        assert result == output_path

        # Verify output is a valid image with bg dimensions
        out_img = Image.open(output_path)
        assert out_img.size == (300, 300)

    def test_process_creates_parent_dirs(self, tmp_path):
        """process() should create parent directories if they don't exist."""
        compositor = BackgroundCompositor()

        product_path = tmp_path / "product.png"
        background_path = tmp_path / "background.png"
        output_path = tmp_path / "nested" / "deep" / "output.png"

        make_rgb_image(80, 80).save(product_path)
        make_rgb_image(200, 200).save(background_path)

        with patch("agents.background_compositor.rembg_remove") as mock_remove:
            mock_remove.return_value = make_rgba_image(80, 80)
            compositor.process(product_path, background_path, output_path)

        assert output_path.exists()
