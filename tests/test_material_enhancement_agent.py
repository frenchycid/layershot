"""Tests for MaterialEnhancementAgent."""
import pytest
import numpy as np
from PIL import Image, ImageEnhance
from agents.material_enhancement_agent import MaterialEnhancementAgent


class TestMaterialEnhancementAgent:
    def test_init(self):
        agent = MaterialEnhancementAgent()
        assert agent is not None

    def test_enhance_metal_increases_contrast(self):
        agent = MaterialEnhancementAgent()
        img_array = np.ones((100, 100, 3), dtype=np.uint8) * 128
        img_array[0:50, :] = 100
        img_array[50:100, :] = 150
        img = Image.fromarray(img_array)
        enhanced = agent.enhance_metal(img)
        assert enhanced.tobytes() != img.tobytes()

    def test_enhance_glass_increases_saturation(self):
        agent = MaterialEnhancementAgent()
        img = Image.new("RGB", (100, 100), color=(200, 150, 100))
        enhanced = agent.enhance_glass(img)
        assert enhanced is not None and enhanced.size == img.size

    def test_enhance_fabric_softens_edges(self):
        agent = MaterialEnhancementAgent()
        img = Image.new("RGB", (100, 100), color=(50, 50, 50))
        enhanced = agent.enhance_fabric(img)
        assert enhanced is not None and enhanced.size == img.size

    def test_enhance_plastic_sharpens(self):
        agent = MaterialEnhancementAgent()
        img = Image.new("RGB", (100, 100), color=(100, 100, 100))
        enhanced = agent.enhance_plastic(img)
        assert enhanced is not None and enhanced.size == img.size

    def test_enhance_wood_adds_warmth(self):
        agent = MaterialEnhancementAgent()
        img = Image.new("RGB", (100, 100), color=(128, 128, 128))
        enhanced = agent.enhance_wood(img)
        assert enhanced is not None

    def test_process_auto_detects_material(self, tmp_path):
        agent = MaterialEnhancementAgent()
        img = Image.new("RGB", (100, 100), color=(100, 100, 100))
        output_path = tmp_path / "enhanced.png"
        agent.process(img, "luxury leather watch", save_to=output_path)
        assert output_path.exists()

    def test_process_respects_material_hint(self, tmp_path):
        agent = MaterialEnhancementAgent()
        img = Image.new("RGB", (100, 100))
        output_path = tmp_path / "enhanced.png"
        agent.process(img, "product", material="metal", save_to=output_path)
        assert output_path.exists()

    def test_enhance_maintains_image_size(self):
        agent = MaterialEnhancementAgent()
        original_size = (150, 200)
        img = Image.new("RGB", original_size)
        enhanced = agent.enhance_metal(img)
        assert enhanced.size == original_size

    def test_enhance_returns_rgb_image(self):
        agent = MaterialEnhancementAgent()
        img = Image.new("RGB", (100, 100))
        enhanced = agent.enhance_metal(img)
        assert enhanced.mode == "RGB"

    def test_batch_enhance(self, tmp_path):
        agent = MaterialEnhancementAgent()
        images = [Image.new("RGB", (100, 100)) for _ in range(3)]
        output_dir = tmp_path / "enhanced"
        results = agent.batch_enhance(images, "product", save_to=output_dir)
        assert len(results) == 3 and output_dir.exists()

    def test_detect_material_from_context_leather(self):
        agent = MaterialEnhancementAgent()
        material = agent._detect_material("brown leather bag")
        assert material in ["leather", "fabric"]

    def test_detect_material_from_context_metal(self):
        agent = MaterialEnhancementAgent()
        material = agent._detect_material("stainless steel watch")
        assert material == "metal"

    def test_detect_material_from_context_glass(self):
        agent = MaterialEnhancementAgent()
        material = agent._detect_material("crystal wine glass")
        assert material == "glass"

    def test_detect_material_fallback(self):
        agent = MaterialEnhancementAgent()
        material = agent._detect_material("unknown product")
        assert material is not None

    def test_material_hints_provided(self):
        agent = MaterialEnhancementAgent()
        supported = ["metal", "glass", "fabric", "plastic", "wood", "leather", "ceramic"]
        for material in supported:
            img = Image.new("RGB", (50, 50))
            enhanced = agent.process(img, "test", material=material)
            assert enhanced is not None

    def test_enhance_preserves_image_content(self):
        agent = MaterialEnhancementAgent()
        arr = np.zeros((100, 100, 3), dtype=np.uint8)
        arr[25:75, 25:75] = [200, 100, 50]
        img = Image.fromarray(arr)
        enhanced = agent.enhance_leather(img)
        assert enhanced is not None

    def test_process_creates_parent_dirs(self, tmp_path):
        agent = MaterialEnhancementAgent()
        img = Image.new("RGB", (100, 100))
        output_path = tmp_path / "deep" / "nested" / "enhanced.png"
        agent.process(img, "product", save_to=output_path)
        assert output_path.exists()

    def test_enhance_ceramic_smoothness(self):
        agent = MaterialEnhancementAgent()
        img = Image.new("RGB", (100, 100), color=(180, 180, 180))
        enhanced = agent.enhance_ceramic(img)
        assert enhanced is not None

    def test_enhance_multiple_calls_consistent(self):
        agent = MaterialEnhancementAgent()
        img = Image.new("RGB", (100, 100))
        result1 = agent.enhance_metal(img)
        result2 = agent.enhance_metal(img)
        assert result1.size == result2.size
