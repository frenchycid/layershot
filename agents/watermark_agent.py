"""Watermark Agent — Applies semi-transparent text watermarks to product images."""

import logging
from pathlib import Path
from typing import List

from PIL import Image, ImageDraw, ImageFont

log = logging.getLogger("watermark_agent")

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png"}


class WatermarkAgent:
    """Applies semi-transparent text watermarks to images."""

    def __init__(self, font_size: int = 24, position: str = "bottom-right"):
        self.font_size = font_size
        self.position = position

    def apply(self, image: Image.Image, text: str, opacity: int = 40) -> Image.Image:
        """Apply a watermark text to an image.

        Args:
            image: Source PIL Image.
            text: Watermark text to render.
            opacity: Alpha value 0-255 (0 = invisible, 255 = fully opaque).

        Returns:
            New Image with the watermark composited on top.
        """
        result = image.convert("RGBA")
        overlay = Image.new("RGBA", result.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)

        # Try to load a truetype font; fall back to default
        try:
            font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", self.font_size)
        except (IOError, OSError):
            try:
                font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", self.font_size)
            except (IOError, OSError):
                font = ImageFont.load_default()

        # Measure text bounding box
        bbox = draw.textbbox((0, 0), text, font=font)
        text_w = bbox[2] - bbox[0]
        text_h = bbox[3] - bbox[1]

        margin = 10
        img_w, img_h = result.size

        if self.position == "bottom-right":
            x = img_w - text_w - margin
            y = img_h - text_h - margin
        elif self.position == "bottom-left":
            x = margin
            y = img_h - text_h - margin
        elif self.position == "top-right":
            x = img_w - text_w - margin
            y = margin
        elif self.position == "top-left":
            x = margin
            y = margin
        else:  # center
            x = (img_w - text_w) // 2
            y = (img_h - text_h) // 2

        draw.text((x, y), text, font=font, fill=(255, 255, 255, opacity))

        composited = Image.alpha_composite(result, overlay)

        # Return in the original mode
        if image.mode != "RGBA":
            return composited.convert(image.mode)
        return composited

    def batch(self, input_dir: Path, output_dir: Path, text: str) -> List[Path]:
        """Apply watermark to all PNG/JPG files in input_dir.

        Args:
            input_dir: Directory containing source images.
            output_dir: Directory where watermarked images will be saved.
            text: Watermark text to apply.

        Returns:
            List of output file paths.
        """
        output_dir.mkdir(parents=True, exist_ok=True)
        sources = sorted(
            p for p in input_dir.iterdir()
            if p.suffix.lower() in IMAGE_EXTENSIONS
        )
        log.info(f"Watermarking {len(sources)} images → {output_dir}")

        outputs: List[Path] = []
        for src in sources:
            img = Image.open(src)
            watermarked = self.apply(img, text)
            dest = output_dir / src.name
            watermarked.save(dest)
            log.info(f"Saved: {dest.name}")
            outputs.append(dest)

        return outputs
