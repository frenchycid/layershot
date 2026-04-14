"""Material Enhancement Agent — Improves texture, reflection, and finish quality."""
import logging
import numpy as np
from pathlib import Path
from typing import Optional
from PIL import Image, ImageEnhance, ImageFilter

log = logging.getLogger("material_enhancement_agent")


class MaterialEnhancementAgent:
    """Enhances material appearance through texture and finish adjustments."""

    MATERIAL_KEYWORDS = {
        "metal": ["metal", "steel", "aluminum", "chrome", "copper", "brass"],
        "glass": ["glass", "crystal", "transparent"],
        "fabric": ["fabric", "cloth", "leather", "suede", "velvet", "cotton", "linen"],
        "plastic": ["plastic", "resin", "poly", "synthetic"],
        "wood": ["wood", "wooden", "oak", "maple", "walnut"],
        "ceramic": ["ceramic", "porcelain", "clay"],
    }

    def enhance_metal(self, image: Image.Image) -> Image.Image:
        """Enhance metal materials with contrast and sharpness."""
        enhancer = ImageEnhance.Contrast(image)
        img = enhancer.enhance(1.3)
        enhancer = ImageEnhance.Sharpness(img)
        return enhancer.enhance(1.2)

    def enhance_glass(self, image: Image.Image) -> Image.Image:
        """Enhance glass materials with saturation and brightness."""
        enhancer = ImageEnhance.Color(image)
        img = enhancer.enhance(1.1)
        enhancer = ImageEnhance.Brightness(img)
        return enhancer.enhance(1.05)

    def enhance_fabric(self, image: Image.Image) -> Image.Image:
        """Enhance fabric materials with soft edges and reduced contrast."""
        img = image.filter(ImageFilter.GaussianBlur(radius=0.5))
        enhancer = ImageEnhance.Contrast(img)
        return enhancer.enhance(0.9)

    def enhance_plastic(self, image: Image.Image) -> Image.Image:
        """Enhance plastic materials with sharpness and color."""
        enhancer = ImageEnhance.Sharpness(image)
        img = enhancer.enhance(1.15)
        enhancer = ImageEnhance.Color(img)
        return enhancer.enhance(1.05)

    def enhance_wood(self, image: Image.Image) -> Image.Image:
        """Enhance wood materials by adding warmth."""
        arr = np.array(image, dtype=np.float32)
        arr[:, :, 0] = np.clip(arr[:, :, 0] * 1.1, 0, 255)
        arr[:, :, 1] = np.clip(arr[:, :, 1] * 1.05, 0, 255)
        return Image.fromarray(arr.astype(np.uint8))

    def enhance_leather(self, image: Image.Image) -> Image.Image:
        """Enhance leather materials with color and contrast."""
        enhancer = ImageEnhance.Color(image)
        img = enhancer.enhance(1.2)
        enhancer = ImageEnhance.Contrast(img)
        return enhancer.enhance(1.1)

    def enhance_ceramic(self, image: Image.Image) -> Image.Image:
        """Enhance ceramic materials with smoothness and brightness."""
        img = image.filter(ImageFilter.GaussianBlur(radius=0.3))
        enhancer = ImageEnhance.Brightness(img)
        return enhancer.enhance(1.05)

    def process(self, image: Image.Image, product_context: str, material: Optional[str] = None, save_to: Optional[Path] = None) -> Image.Image:
        """Process image with material-specific enhancements."""
        detected_material = material or self._detect_material(product_context)
        log.info(f"Enhancing {detected_material} material")

        enhancement_method = getattr(self, f"enhance_{detected_material}", self.enhance_plastic)
        enhanced = enhancement_method(image)

        if save_to:
            save_to.parent.mkdir(parents=True, exist_ok=True)
            enhanced.save(save_to)
            log.info(f"Enhanced image saved to {save_to}")

        return enhanced

    def batch_enhance(self, images: list, product_context: str, save_to: Optional[Path] = None) -> list:
        """Process multiple images with the same context."""
        results = []
        for idx, img in enumerate(images):
            enhanced = self.process(img, product_context)
            if save_to:
                save_to.mkdir(parents=True, exist_ok=True)
                output_path = save_to / f"enhanced_{idx:04d}.png"
                enhanced.save(output_path)
            results.append(enhanced)
        return results

    def _detect_material(self, product_context: str) -> str:
        """Auto-detect material from product context."""
        context_lower = product_context.lower()
        for material, keywords in self.MATERIAL_KEYWORDS.items():
            if any(kw in context_lower for kw in keywords):
                return material
        return "plastic"
