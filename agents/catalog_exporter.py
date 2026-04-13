"""CatalogExporter Agent — Generates multi-format image exports for print, web, social, e-commerce."""

import logging
from pathlib import Path

from PIL import Image

log = logging.getLogger("catalog_exporter")

# Social format specs: (width_ratio, height_ratio, label)
SOCIAL_FORMATS = {
    "square": (1, 1),
    "portrait": (4, 5),
    "story": (9, 16),
}


class CatalogExporter:
    """Exports validated product images into all required channel formats."""

    def __init__(self, web_max_size: int = 1920, print_dpi: int = 300):
        self.web_max_size = web_max_size
        self.print_dpi = print_dpi

    # ─── Web ────────────────────────────────────────────────────────────────

    def export_web(self, image: Image.Image, output_path: Path) -> Path:
        """JPEG 72dpi, max 1920px on the long side, quality 90."""
        img = image.copy()
        img.thumbnail((self.web_max_size, self.web_max_size), Image.LANCZOS)
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        img.save(output_path, format="JPEG", quality=90, dpi=(72, 72))
        log.info(f"Web export saved: {output_path} {img.size}")
        return output_path

    # ─── Print ──────────────────────────────────────────────────────────────

    def export_print(self, image: Image.Image, output_path: Path) -> Path:
        """PNG 300dpi, original dimensions preserved."""
        img = image.copy()
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        img.save(output_path, format="PNG", dpi=(self.print_dpi, self.print_dpi))
        log.info(f"Print export saved: {output_path} {img.size}")
        return output_path

    # ─── Social ─────────────────────────────────────────────────────────────

    def export_social(self, image: Image.Image, output_dir: Path) -> dict:
        """Crop/pad image into square 1:1, portrait 4:5, and story 9:16 variants.

        Returns dict {square: Path, portrait: Path, story: Path}.
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        paths = {}

        for name, (w_ratio, h_ratio) in SOCIAL_FORMATS.items():
            result_path = output_dir / f"social_{name}.jpg"
            variant = self._crop_to_ratio(image, w_ratio, h_ratio)
            variant.save(result_path, format="JPEG", quality=90, dpi=(72, 72))
            log.info(f"Social {name} saved: {result_path} {variant.size}")
            paths[name] = result_path

        return paths

    # ─── E-commerce ─────────────────────────────────────────────────────────

    def export_ecommerce(self, image: Image.Image, output_path: Path) -> Path:
        """Place product on a white square canvas with 10% padding on each side."""
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Determine canvas size: longest side of original + 20% for padding
        w, h = image.size
        longest = max(w, h)
        canvas_size = int(longest / 0.80)  # 10% padding each side → product occupies 80%

        # Scale image to fit within the padded area
        max_product = int(canvas_size * 0.80)
        img = image.copy()
        img.thumbnail((max_product, max_product), Image.LANCZOS)

        # Paste centered on white canvas
        canvas = Image.new("RGB", (canvas_size, canvas_size), color=(255, 255, 255))
        x = (canvas_size - img.width) // 2
        y = (canvas_size - img.height) // 2
        canvas.paste(img, (x, y))

        canvas.save(output_path, format="PNG", dpi=(self.print_dpi, self.print_dpi))
        log.info(f"E-commerce export saved: {output_path} {canvas.size}")
        return output_path

    # ─── Export All ─────────────────────────────────────────────────────────

    def export_all(self, image_path: Path, output_dir: Path, sku: str) -> dict:
        """Export all format variants into output_dir/sku/. Returns dict of paths."""
        image_path = Path(image_path)
        output_dir = Path(output_dir)
        sku_dir = output_dir / sku
        sku_dir.mkdir(parents=True, exist_ok=True)

        image = Image.open(image_path).convert("RGB")

        web_path = self.export_web(image, sku_dir / f"{sku}_web.jpg")
        print_path = self.export_print(image, sku_dir / f"{sku}_print.png")
        social_paths = self.export_social(image, sku_dir)
        ecom_path = self.export_ecommerce(image, sku_dir / f"{sku}_ecommerce.png")

        return {
            "web": web_path,
            "print": print_path,
            "square": social_paths["square"],
            "portrait": social_paths["portrait"],
            "story": social_paths["story"],
            "ecommerce": ecom_path,
        }

    # ─── Internal helpers ───────────────────────────────────────────────────

    @staticmethod
    def _crop_to_ratio(image: Image.Image, w_ratio: int, h_ratio: int) -> Image.Image:
        """Center-crop image to the given w:h ratio, then resize to fit 1080px long side."""
        src_w, src_h = image.size
        target_ratio = w_ratio / h_ratio

        if src_w / src_h > target_ratio:
            # Image is wider than target — crop width
            new_w = int(src_h * target_ratio)
            left = (src_w - new_w) // 2
            box = (left, 0, left + new_w, src_h)
        else:
            # Image is taller than target — crop height
            new_h = int(src_w / target_ratio)
            top = (src_h - new_h) // 2
            box = (0, top, src_w, top + new_h)

        cropped = image.crop(box)

        # Resize so the long side is at most 1080 (standard social size)
        cropped.thumbnail((1080, 1080), Image.LANCZOS)
        return cropped
