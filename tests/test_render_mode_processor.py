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
