"""BackgroundCompositor Agent — removes product background with rembg and composites onto a new bg."""

import logging
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter

try:
    from rembg import remove as rembg_remove
except ImportError:  # pragma: no cover
    rembg_remove = None  # type: ignore

log = logging.getLogger("background_compositor")


class BackgroundCompositor:
    """Removes a product background with rembg and composites the product onto a new background.

    Attributes:
        product_scale: Fraction of background width the product occupies (0 < scale <= 1).
    """

    def __init__(self, product_scale: float = 0.5):
        if not (0 < product_scale <= 1.0):
            raise ValueError(f"product_scale must be in (0, 1]. Got: {product_scale}")
        self.product_scale = product_scale

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def remove_background(self, image: Image.Image) -> Image.Image:
        """Remove the background from a product image using rembg.

        Args:
            image: RGB or RGBA PIL image of the product.

        Returns:
            RGBA PIL image with background pixels set to transparent.
        """
        if rembg_remove is None:  # pragma: no cover
            raise RuntimeError("rembg is not installed. Run: pip install rembg")

        # rembg expects bytes or PIL; pass PIL directly — it returns PIL RGBA
        result = rembg_remove(image)

        if result.mode != "RGBA":
            result = result.convert("RGBA")

        log.debug("Background removed: %s → %s", image.size, result.size)
        return result

    def composite(self, product: Image.Image, background: Image.Image) -> Image.Image:
        """Paste a product (RGBA) onto a background, centered horizontally and near the bottom.

        Args:
            product: RGBA PIL image of the product (background already removed).
            background: RGB or RGBA PIL image used as the scene background.

        Returns:
            PIL Image with the same dimensions as `background`.
        """
        bg = background.convert("RGBA")
        bg_w, bg_h = bg.size

        # Scale product to fit within product_scale * bg width, preserving aspect ratio
        product_rgba = product if product.mode == "RGBA" else product.convert("RGBA")
        prod_w, prod_h = product_rgba.size

        target_w = int(bg_w * self.product_scale)
        scale_ratio = target_w / prod_w
        target_h = int(prod_h * scale_ratio)

        if target_w != prod_w or target_h != prod_h:
            product_rgba = product_rgba.resize((target_w, target_h), Image.LANCZOS)

        # Position: centered horizontally, bottom-aligned with a small margin
        margin_bottom = int(bg_h * 0.05)
        paste_x = (bg_w - target_w) // 2
        paste_y = bg_h - target_h - margin_bottom

        # Optionally add soft shadow below the product
        shadow_layer = Image.new("RGBA", bg.size, (0, 0, 0, 0))
        shadow = self._make_shadow(target_w, target_h)
        shadow_x = paste_x
        shadow_y = paste_y + int(target_h * 0.9)
        shadow_layer.paste(shadow, (shadow_x, shadow_y), mask=shadow)

        # Compose: background → shadow → product
        canvas = bg.copy()
        canvas = Image.alpha_composite(canvas, shadow_layer)

        product_layer = Image.new("RGBA", bg.size, (0, 0, 0, 0))
        product_layer.paste(product_rgba, (paste_x, paste_y), mask=product_rgba)
        canvas = Image.alpha_composite(canvas, product_layer)

        return canvas.convert("RGB")

    def process(
        self,
        product_path: Path,
        background_path: Path,
        output_path: Path,
    ) -> Path:
        """Full pipeline: load → remove_bg → composite → save.

        Args:
            product_path: Path to the product render (PNG/JPG).
            background_path: Path to the reference background image.
            output_path: Where the composited image is saved.

        Returns:
            The resolved output_path.
        """
        product_path = Path(product_path)
        background_path = Path(background_path)
        output_path = Path(output_path)

        log.info("Loading product: %s", product_path)
        product_img = Image.open(product_path)

        log.info("Loading background: %s", background_path)
        bg_img = Image.open(background_path)

        log.info("Removing background…")
        product_no_bg = self.remove_background(product_img)

        log.info("Compositing…")
        result = self.composite(product_no_bg, bg_img)

        output_path.parent.mkdir(parents=True, exist_ok=True)
        result.save(output_path)
        log.info("Saved composite to: %s", output_path)

        return output_path

    def add_shadow(self, image: Image.Image, opacity: int = 60) -> Image.Image:
        """Add a soft drop shadow beneath the product.

        Args:
            image: RGBA PIL image of the product.
            opacity: Shadow alpha (0–255).

        Returns:
            New RGBA image with the shadow composited below the product.
        """
        if image.mode != "RGBA":
            image = image.convert("RGBA")

        w, h = image.size
        shadow_h = max(int(h * 0.15), 4)
        shadow = self._make_shadow(w, shadow_h, opacity=opacity)

        canvas = Image.new("RGBA", (w, h + shadow_h), (0, 0, 0, 0))
        # Place shadow at bottom
        canvas.paste(shadow, (0, h - shadow_h // 2), mask=shadow)
        # Place product on top
        canvas.paste(image, (0, 0), mask=image)
        return canvas

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _make_shadow(self, width: int, height: int, opacity: int = 60) -> Image.Image:
        """Create a soft elliptical shadow image."""
        shadow_h = max(height // 3, 4)
        shadow = Image.new("RGBA", (width, shadow_h), (0, 0, 0, 0))

        arr = np.zeros((shadow_h, width, 4), dtype=np.uint8)
        cx, cy = width / 2, shadow_h / 2
        rx, ry = width / 2, shadow_h / 2

        for y in range(shadow_h):
            for x in range(width):
                dist = ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2
                if dist <= 1.0:
                    alpha = int(opacity * (1.0 - dist))
                    arr[y, x] = [0, 0, 0, alpha]

        shadow = Image.fromarray(arr, mode="RGBA")
        shadow = shadow.filter(ImageFilter.GaussianBlur(radius=max(shadow_h // 3, 1)))
        return shadow
