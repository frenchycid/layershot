"""Render Mode Processor — Per-mode post-processing orchestrator."""
import logging
import numpy as np
from pathlib import Path
from typing import Optional, List
from PIL import Image, ImageEnhance
from agents.material_enhancement_agent import MaterialEnhancementAgent

log = logging.getLogger("render_mode_processor")


class RenderModeProcessor:
    """Orchestrates render mode-specific post-processing."""

    def __init__(self):
        self.material_enhancer = MaterialEnhancementAgent()

    def process(self, image: Image.Image, product_context: str, render_mode: str, save_to: Optional[Path] = None) -> Image.Image:
        """Process image according to render mode."""
        if render_mode not in ["isolated", "white_background", "enhanced"]:
            raise KeyError(f"Unknown render mode: {render_mode}")

        log.info(f"Processing image in {render_mode} mode")

        if render_mode == "isolated":
            result = self._process_isolated(image)
        elif render_mode == "white_background":
            result = self._process_white_background(image)
        elif render_mode == "enhanced":
            result = self._process_enhanced(image, product_context)

        if save_to:
            save_to.parent.mkdir(parents=True, exist_ok=True)
            result.save(save_to)
            log.info(f"Processed image saved to {save_to}")

        return result

    def _process_isolated(self, image: Image.Image) -> Image.Image:
        """Convert to transparent background (isolated product)."""
        if image.mode != "RGBA":
            image = image.convert("RGBA")

        img_array = np.array(image)
        gray = np.mean(img_array[:, :, :3], axis=2)
        mask = gray < 240
        img_array[~mask, 3] = 0

        return Image.fromarray(img_array)

    def _process_white_background(self, image: Image.Image) -> Image.Image:
        """Ensure white background with proper lighting."""
        if image.mode == "RGBA":
            image = image.convert("RGB")

        white_bg = Image.new("RGB", image.size, (255, 255, 255))
        return Image.blend(white_bg, image, 0.9)

    def _process_enhanced(self, image: Image.Image, product_context: str) -> Image.Image:
        """Apply material enhancement and color grading."""
        if image.mode == "RGBA":
            image = image.convert("RGB")

        enhanced = self.material_enhancer.process(image, product_context)
        return self._apply_color_grading(enhanced)

    def _apply_color_grading(self, image: Image.Image) -> Image.Image:
        """Apply color grading for premium/catalog look."""
        enhancer = ImageEnhance.Color(image)
        image = enhancer.enhance(1.1)
        enhancer = ImageEnhance.Contrast(image)
        image = enhancer.enhance(1.05)
        enhancer = ImageEnhance.Brightness(image)
        return enhancer.enhance(1.02)

    def batch_process(self, images: List[Image.Image], product_context: str, render_mode: str, output_dir: Optional[Path] = None) -> List[Image.Image]:
        """Process multiple images with same mode."""
        results = []
        for idx, img in enumerate(images):
            output_path = None
            if output_dir:
                output_dir.mkdir(parents=True, exist_ok=True)
                output_path = output_dir / f"{render_mode}_{idx:04d}.png"

            result = self.process(img, product_context, render_mode, save_to=output_path)
            results.append(result)

        log.info(f"Batch processed {len(results)} images in {render_mode} mode")
        return results
