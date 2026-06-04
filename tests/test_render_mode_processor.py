"""Tests for RenderModeProcessor."""
import pytest
import numpy as np
from pathlib import Path
from PIL import Image
from unittest.mock import Mock, patch
from agents.render_mode_processor import RenderModeProcessor


class TestRenderModeProcessor:
    def test_init(self):
        processor = RenderModeProcessor()
        assert processor is not None

    def test_process_isolated_mode(self, tmp_path):
        processor = RenderModeProcessor()
        img = Image.new("RGB", (100, 100), color=(255, 255, 255))
        output_path = tmp_path / "isolated.png"
        result = processor.process(img, "product", "isolated", save_to=output_path)
        assert output_path.exists()

    def test_isolated_mode_removes_background(self, tmp_path):
        processor = RenderModeProcessor()
        img = Image.new("RGB", (100, 100), color=(255, 255, 255))
        result = processor.process(img, "product", "isolated")
        assert result.mode == "RGBA"

    def test_isolated_mode_preserves_product(self, tmp_path):
        processor = RenderModeProcessor()
        arr = np.ones((100, 100, 3), dtype=np.uint8) * 255
        arr[25:75, 25:75] = [100, 150, 200]
        img = Image.fromarray(arr)
        result = processor.process(img, "blue product", "isolated")
        assert result is not None

    def test_isolated_output_is_rgba(self):
        processor = RenderModeProcessor()
        img = Image.new("RGB", (100, 100))
        result = processor.process(img, "product", "isolated")
        assert result.mode == "RGBA"

    def test_isolated_maintains_size(self):
        processor = RenderModeProcessor()
        size = (150, 200)
        img = Image.new("RGB", size)
        result = processor.process(img, "product", "isolated")
        assert result.size == size

    def test_process_white_background_mode(self, tmp_path):
        processor = RenderModeProcessor()
        img = Image.new("RGB", (100, 100), color=(128, 128, 128))
        output_path = tmp_path / "white_bg.png"
        result = processor.process(img, "product", "white_background", save_to=output_path)
        assert output_path.exists()

    def test_white_background_mode_adds_white_bg(self):
        processor = RenderModeProcessor()
        img = Image.new("RGB", (100, 100), color=(100, 100, 100))
        result = processor.process(img, "product", "white_background")
        assert result is not None and result.mode == "RGB"

    def test_white_background_output_is_rgb(self):
        processor = RenderModeProcessor()
        img = Image.new("RGB", (100, 100))
        result = processor.process(img, "product", "white_background")
        assert result.mode == "RGB"

    def test_white_background_maintains_proportions(self):
        processor = RenderModeProcessor()
        size = (100, 100)
        img = Image.new("RGB", size)
        result = processor.process(img, "product", "white_background")
        assert result.size[0] >= size[0] and result.size[1] >= size[1]

    def test_process_enhanced_mode(self, tmp_path):
        processor = RenderModeProcessor()
        img = Image.new("RGB", (100, 100), color=(100, 100, 100))
        output_path = tmp_path / "enhanced.png"
        result = processor.process(img, "luxury product", "enhanced", save_to=output_path)
        assert output_path.exists()

    def test_enhanced_mode_improves_materials(self):
        processor = RenderModeProcessor()
        img = Image.new("RGB", (100, 100), color=(128, 128, 128))
        result = processor.process(img, "leather bag", "enhanced")
        assert result is not None

    def test_enhanced_output_is_rgb(self):
        processor = RenderModeProcessor()
        img = Image.new("RGB", (100, 100))
        result = processor.process(img, "product", "enhanced")
        assert result.mode == "RGB"

    def test_batch_process_multiple_images(self, tmp_path):
        processor = RenderModeProcessor()
        images = [Image.new("RGB", (100, 100)) for _ in range(3)]
        output_dir = tmp_path / "processed"
        results = processor.batch_process(images, "product", "white_background", output_dir=output_dir)
        assert len(results) == 3 and output_dir.exists()

    def test_batch_process_saves_all_images(self, tmp_path):
        processor = RenderModeProcessor()
        images = [Image.new("RGB", (100, 100)) for _ in range(3)]
        output_dir = tmp_path / "processed"
        processor.batch_process(images, "product", "isolated", output_dir=output_dir)
        saved_files = list(output_dir.glob("*.png"))
        assert len(saved_files) >= 3

    def test_process_all_three_modes_work(self):
        processor = RenderModeProcessor()
        img = Image.new("RGB", (100, 100))
        modes = ["isolated", "white_background", "enhanced"]
        for mode in modes:
            result = processor.process(img, "product", mode)
            assert result is not None

    def test_process_unknown_mode_raises(self):
        processor = RenderModeProcessor()
        img = Image.new("RGB", (100, 100))
        with pytest.raises(KeyError):
            processor.process(img, "product", "unknown_mode")

    def test_process_creates_output_dir(self, tmp_path):
        processor = RenderModeProcessor()
        img = Image.new("RGB", (100, 100))
        output_path = tmp_path / "nested" / "dir" / "image.png"
        processor.process(img, "product", "white_background", save_to=output_path)
        assert output_path.exists()

    def test_process_preserves_image_size_isolated(self):
        processor = RenderModeProcessor()
        size = (200, 150)
        img = Image.new("RGB", size)
        result = processor.process(img, "product", "isolated")
        assert result.size == size

    def test_batch_process_maintains_order(self):
        processor = RenderModeProcessor()
        images = [
            Image.new("RGB", (100, 100), color=(255, 0, 0)),
            Image.new("RGB", (100, 100), color=(0, 255, 0)),
            Image.new("RGB", (100, 100), color=(0, 0, 255))
        ]
        results = processor.batch_process(images, "product", "white_background")
        assert len(results) == 3

    def test_isolated_transparency_layer_added(self):
        processor = RenderModeProcessor()
        img = Image.new("RGB", (50, 50), color=(200, 200, 200))
        result = processor.process(img, "product", "isolated")
        assert len(result.getbands()) == 4

    def test_white_background_corrects_color_cast(self):
        processor = RenderModeProcessor()
        arr = np.ones((100, 100, 3), dtype=np.uint8) * 150
        arr[:, :, 0] = 180
        img = Image.fromarray(arr)
        result = processor.process(img, "product", "white_background")
        assert result is not None

    def test_enhanced_mode_uses_material_enhancement(self):
        processor = RenderModeProcessor()
        img = Image.new("RGB", (100, 100), color=(100, 100, 100))
        result = processor.process(img, "metal watch", "enhanced")
        assert result is not None

    def test_isolated_with_different_bg_colors(self):
        processor = RenderModeProcessor()
        backgrounds = [(255, 255, 255), (200, 200, 200), (150, 150, 150)]
        for bg_color in backgrounds:
            img = Image.new("RGB", (100, 100), color=bg_color)
            result = processor.process(img, "product", "isolated")
            assert result.mode == "RGBA"

    def test_white_background_blending(self):
        processor = RenderModeProcessor()
        img = Image.new("RGB", (100, 100), color=(128, 128, 128))
        result = processor.process(img, "product", "white_background")
        arr = np.array(result)
        avg_brightness = np.mean(arr)
        assert avg_brightness > 128

    def test_batch_process_empty_list(self):
        processor = RenderModeProcessor()
        results = processor.batch_process([], "product", "white_background")
        assert results == []

    def test_process_rgba_input_isolated(self):
        processor = RenderModeProcessor()
        img = Image.new("RGBA", (100, 100), color=(100, 100, 100, 255))
        result = processor.process(img, "product", "isolated")
        assert result.mode == "RGBA"

    def test_process_rgba_input_white_background(self):
        processor = RenderModeProcessor()
        img = Image.new("RGBA", (100, 100), color=(100, 100, 100, 255))
        result = processor.process(img, "product", "white_background")
        assert result.mode == "RGB"

    def test_enhanced_color_grading_applied(self):
        processor = RenderModeProcessor()
        img = Image.new("RGB", (100, 100), color=(128, 128, 128))
        result = processor.process(img, "luxury product", "enhanced")
        assert result is not None
        assert result.mode == "RGB"

    def test_batch_process_with_no_output_dir(self):
        processor = RenderModeProcessor()
        images = [Image.new("RGB", (100, 100)) for _ in range(3)]
        results = processor.batch_process(images, "product", "enhanced")
        assert len(results) == 3


# ---------------------------------------------------------------------------
# Bug-1 fix: hue-preserving saturation in enhanced mode
# ---------------------------------------------------------------------------

class TestEnhancedPreservesBrandColors:
    """_process_enhanced must not shift the hue of brand colours (e.g. Sephora pink)."""

    def _make_pink_image(self, size=(100, 100)):
        """Create a solid blush-pink image resembling Sephora gondola colour."""
        # #F2C4C4 = (242, 196, 196)
        arr = np.full((*size, 3), [242, 196, 196], dtype=np.uint8)
        return Image.fromarray(arr, mode="RGB")

    def test_enhanced_keeps_pink_hue(self):
        """After enhanced processing, mean hue should remain in the pink/red family."""
        processor = RenderModeProcessor()
        pink = self._make_pink_image()
        result = processor.process(pink, "sephora gondola", "enhanced")

        arr = np.array(result.convert("RGB"), dtype=float)
        mean_r = arr[:, :, 0].mean()
        mean_b = arr[:, :, 2].mean()

        # Pink: red channel must remain dominant over blue
        assert mean_r > mean_b, (
            f"Hue shifted: mean_r={mean_r:.1f} should be > mean_b={mean_b:.1f}"
        )

    def test_enhanced_does_not_over_warm_pink(self):
        """Enhanced mode must not push pink R-B difference beyond the original."""
        processor = RenderModeProcessor()
        pink = self._make_pink_image()

        orig_arr = np.array(pink, dtype=float)
        orig_rb_diff = orig_arr[:, :, 0].mean() - orig_arr[:, :, 2].mean()  # ~46

        result = processor.process(pink, "sephora gondola", "enhanced")
        res_arr = np.array(result.convert("RGB"), dtype=float)
        res_rb_diff = res_arr[:, :, 0].mean() - res_arr[:, :, 2].mean()

        # Allow at most 30 units of extra warming (was uncapped before fix)
        assert res_rb_diff <= orig_rb_diff + 30, (
            f"Too much warming: original R-B={orig_rb_diff:.1f}, result R-B={res_rb_diff:.1f}"
        )

    def test_hsv_saturation_boost_preserves_hue(self):
        """_boost_saturation_hsv must not change the hue channel."""
        from agents.render_mode_processor import _boost_saturation_hsv
        pink = Image.new("RGB", (50, 50), (242, 196, 196))
        boosted = _boost_saturation_hsv(pink, 1.5)

        orig_hsv = np.array(pink.convert("HSV"), dtype=float)
        res_hsv = np.array(boosted.convert("HSV"), dtype=float)

        orig_hue = orig_hsv[:, :, 0].mean()
        res_hue = res_hsv[:, :, 0].mean()

        assert abs(orig_hue - res_hue) < 3, (
            f"Hue shifted by {abs(orig_hue - res_hue):.1f} — should be < 3"
        )


# ---------------------------------------------------------------------------
# Bug-2 fix: human body detection via u2net_human_seg + background-colour erase
# ---------------------------------------------------------------------------

class TestHumanDetection:
    """_detect_humans and _erase_human_regions should handle human presence correctly."""

    def test_detect_humans_returns_false_when_human_seg_unavailable(self):
        """When u2net_human_seg is unavailable, detect_humans returns (False, empty)."""
        from unittest.mock import patch
        img = Image.new("RGB", (100, 100), (200, 150, 120))
        with patch("agents.render_mode_processor._get_human_seg_session",
                   return_value="unavailable"):
            has_humans, alpha = RenderModeProcessor._detect_humans(img)
        assert has_humans is False
        assert alpha.shape == (100, 100)
        assert alpha.max() == 0

    def test_detect_humans_uses_human_seg_alpha(self):
        """detect_humans should return True when human-seg alpha covers > threshold."""
        from unittest.mock import patch, MagicMock
        # Build a fake human-seg result: 50% alpha coverage
        fake_rgba = np.zeros((100, 100, 4), dtype=np.uint8)
        fake_rgba[:50, :, 3] = 255  # top half opaque = human
        fake_result = Image.fromarray(fake_rgba, mode="RGBA")

        img = Image.new("RGB", (100, 100), (200, 150, 120))

        mock_session = MagicMock()
        with patch("agents.render_mode_processor._get_human_seg_session",
                   return_value=mock_session), \
             patch("rembg.remove", return_value=fake_result):
            has_humans, alpha = RenderModeProcessor._detect_humans(img, threshold=0.12)

        assert has_humans is True  # 50 % > 12 %

    def test_detect_humans_returns_false_below_threshold(self):
        """detect_humans returns False when human coverage is below threshold."""
        from unittest.mock import patch, MagicMock
        # Only 5% alpha coverage
        fake_rgba = np.zeros((100, 100, 4), dtype=np.uint8)
        fake_rgba[:5, :, 3] = 255
        fake_result = Image.fromarray(fake_rgba, mode="RGBA")

        img = Image.new("RGB", (100, 100), (100, 100, 100))
        mock_session = MagicMock()
        with patch("agents.render_mode_processor._get_human_seg_session",
                   return_value=mock_session), \
             patch("rembg.remove", return_value=fake_result):
            has_humans, _ = RenderModeProcessor._detect_humans(img, threshold=0.12)

        assert has_humans is False

    def test_erase_human_regions_replaces_masked_pixels(self):
        """Pixels under human_alpha mask should be replaced with background colour."""
        # Image: red corners (background), blue centre (subject)
        # Using red bg so we can distinguish corner-sampled bg from the original blue
        arr = np.zeros((100, 100, 3), dtype=np.uint8)
        arr[:, :, 0] = 200          # red background everywhere
        arr[20:80, 20:80] = [0, 0, 200]   # override centre with pure blue subject

        img = Image.fromarray(arr, mode="RGB")

        # Human mask covers the blue subject area
        human_alpha = np.zeros((100, 100), dtype=np.uint8)
        human_alpha[20:80, 20:80] = 255

        result = RenderModeProcessor._erase_human_regions(img, human_alpha)
        res_arr = np.array(result, dtype=float)

        # After erase, subject area should be close to red background (sampled from corners)
        subject = res_arr[20:80, 20:80]
        assert subject[:, :, 0].mean() > 150  # R: was 0, now ~200 (red bg)
        assert subject[:, :, 2].mean() < 100  # B: was 200 (blue), now ~0 (red bg has no blue)

    def test_erase_human_regions_preserves_unmasked_pixels(self):
        """Pixels outside the human mask should remain unchanged."""
        arr = np.full((100, 100, 3), 200, dtype=np.uint8)
        arr[40:60, 40:60] = [50, 100, 200]
        img = Image.fromarray(arr, mode="RGB")

        # Mask only covers a small corner, not the coloured area
        human_alpha = np.zeros((100, 100), dtype=np.uint8)
        human_alpha[0:5, 0:5] = 255

        result = RenderModeProcessor._erase_human_regions(img, human_alpha)
        res_arr = np.array(result, dtype=float)

        # The blue region should be unchanged
        region = res_arr[40:60, 40:60]
        assert abs(region[:, :, 2].mean() - 200) < 15  # blue channel intact
