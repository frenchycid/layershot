"""Style Analyst Agent — Extracts photographic style from moodboard images."""

import json
import logging
from pathlib import Path
from typing import List, Optional

from core.ai_backend import AIBackend

log = logging.getLogger("style_analyst")

SYSTEM_PROMPT = """You are a photographic style analyst. You analyze reference images
to extract ONLY the visual style — never describe the content or subjects in the scenes.

You must respond with valid JSON matching this exact structure:
{
  "lighting": {"type": "...", "direction": "...", "quality": "..."},
  "color_palette": {"dominant": ["..."], "accents": ["..."], "temperature": "warm|cool|neutral"},
  "grain": {"type": "film|digital|none", "intensity": "low|medium|high", "film_stock": "..."},
  "lens": {"focal_length": "...", "aperture": "...", "depth_of_field": "shallow|medium|deep"},
  "atmosphere": ["list of atmospheric effects"],
  "style_summary": "One paragraph summarizing the overall photographic style"
}

Use precise photographic vocabulary: atmospheric bloom, lifted blacks, film grain,
crushed shadows, highlight rolloff, color cast, bokeh, chromatic aberration, etc.
Do NOT use generic terms like "beautiful" or "nice photo"."""

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".tiff", ".bmp"}


class StyleAnalyst:
    """Analyzes moodboard images to extract a structured style profile."""

    def __init__(self, ai_backend: Optional[AIBackend] = None):
        self.ai = ai_backend or AIBackend()

    def collect_images(self, directory: Path) -> List[Path]:
        """Collect all image files from a directory."""
        images = sorted(
            p for p in directory.iterdir()
            if p.suffix.lower() in IMAGE_EXTENSIONS
        )
        log.info(f"Found {len(images)} images in {directory}")
        return images

    def analyze(
        self,
        image_paths: List[str],
        save_to: Optional[Path] = None,
    ) -> dict:
        """Analyze images and return structured style JSON."""
        log.info(f"Analyzing {len(image_paths)} reference images...")

        prompt = (
            f"Analyze the photographic style of these {len(image_paths)} reference images. "
            "Focus ONLY on style attributes: lighting, color palette, grain, lens characteristics, "
            "and atmospheric effects. Do NOT describe the content or subjects. "
            "Respond with the JSON structure specified in your instructions."
        )

        raw = self.ai.analyze_images(
            [str(p) for p in image_paths],
            prompt,
            system=SYSTEM_PROMPT,
        )

        result = self._parse_json(raw)
        log.info(f"Style analysis complete: {result.get('style_summary', '')[:80]}")

        if save_to:
            save_to.parent.mkdir(parents=True, exist_ok=True)
            save_to.write_text(json.dumps(result, indent=2, ensure_ascii=False))
            log.info(f"Analysis saved to {save_to}")

        return result

    def _parse_json(self, raw: str) -> dict:
        """Extract JSON from AI response, handling markdown code blocks."""
        text = raw.strip()
        if "```json" in text:
            text = text.split("```json", 1)[1].split("```", 1)[0]
        elif "```" in text:
            text = text.split("```", 1)[1].split("```", 1)[0]
        return json.loads(text.strip())
