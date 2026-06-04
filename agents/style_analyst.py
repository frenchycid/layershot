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
        try:
            self._validate_analysis(result)
        except ValueError as e:
            log.error(f"Style analysis JSON incomplete: {e}")
            log.error(f"Raw VLM output ({len(raw)} chars): {raw[:400]!r}")
            log.warning("Falling back to default studio style analysis")
            result = self._default_studio_style()
        log.info(f"Style analysis complete: {result.get('style_summary', '')[:80]}")

        if save_to:
            save_to.parent.mkdir(parents=True, exist_ok=True)
            save_to.write_text(json.dumps(result, indent=2, ensure_ascii=False))
            log.info(f"Analysis saved to {save_to}")

        return result

    @staticmethod
    def _default_studio_style() -> dict:
        """Fallback style when VLM analysis fails or is truncated.

        Encodes the canonical studio packshot aesthetic:
        - White seamless cyclorama sweep
        - Soft overhead diffused lighting with fill panels
        - Neutral cool palette, lifted whites
        - Minimal grain (digital clean)
        - 90mm macro lens, f/8–f/11 deep field
        - Soft contact shadow on white floor
        """
        return {
            "lighting": {
                "type": "diffused softbox",
                "direction": "overhead with bilateral fill panels",
                "quality": "soft, even, shadow-controlled with natural contact shadow"
            },
            "color_palette": {
                "dominant": ["pure white", "off-white", "cool light grey"],
                "accents": ["neutral shadow grey"],
                "temperature": "neutral"
            },
            "grain": {
                "type": "digital",
                "intensity": "low",
                "film_stock": "none — clean digital sensor"
            },
            "lens": {
                "focal_length": "90mm macro",
                "aperture": "f/8",
                "depth_of_field": "deep"
            },
            "atmosphere": [
                "white seamless cyclorama sweep background",
                "product casting soft natural contact shadow on white surface",
                "studio product photography",
                "clean highlight rolloff",
                "lifted whites without clipping",
                "controlled shadows",
                "commercial packshot quality"
            ],
            "style_summary": (
                "Professional studio packshot photography on a white seamless cyclorama sweep. "
                "Overhead diffused softbox with bilateral fill panels creates even, shadow-controlled "
                "illumination. The product casts a soft natural contact shadow on the white floor. "
                "Neutral cool palette with lifted whites, clean digital rendering, 90mm macro lens "
                "at f/8 for maximum product detail. Commercial packshot quality."
            )
        }

    def _parse_json(self, raw: str) -> dict:
        """Extract JSON from AI response, handling markdown code blocks."""
        import re

        text = raw.strip()
        if "```json" in text:
            text = text.split("```json", 1)[1].split("```", 1)[0]
        elif "```" in text:
            text = text.split("```", 1)[1].split("```", 1)[0]
        text = text.strip()

        def _sanitize(s: str) -> str:
            s = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", " ", s)
            return s.replace("\t", " ")

        # First attempt: parse the full text as-is, then sanitized.
        for candidate in (text, _sanitize(text)):
            try:
                return json.loads(candidate, strict=False)
            except json.JSONDecodeError:
                pass

        # Multi-image VLM outputs get concatenated with "---" separators;
        # each block may itself be truncated. Walk the string extracting every
        # balanced {...} block and return the first one that parses cleanly.
        for start in (m.start() for m in re.finditer(r"\{", text)):
            depth = 0
            in_str = False
            escape = False
            for i in range(start, len(text)):
                c = text[i]
                if in_str:
                    if escape:
                        escape = False
                    elif c == "\\":
                        escape = True
                    elif c == '"':
                        in_str = False
                else:
                    if c == '"':
                        in_str = True
                    elif c == "{":
                        depth += 1
                    elif c == "}":
                        depth -= 1
                        if depth == 0:
                            block = text[start:i + 1]
                            try:
                                return json.loads(_sanitize(block), strict=False)
                            except json.JSONDecodeError:
                                break
        raise ValueError(f"Could not extract valid JSON from VLM output "
                         f"({len(text)} chars, preview: {text[:200]!r})")

    _REQUIRED_KEYS = {"lighting", "color_palette", "grain", "lens", "atmosphere"}

    def _validate_analysis(self, data: dict) -> dict:
        """Ensure the parsed JSON is the top-level analysis object, not a sub-object.

        Bug: MLX VLM sometimes returns a truncated response; _parse_json then
        picks the first valid {} block, which can be the nested 'lighting' object
        instead of the full analysis.  We detect this by checking for required
        top-level keys and raise so the caller can handle the failure gracefully.
        """
        missing = self._REQUIRED_KEYS - set(data.keys())
        if missing:
            raise ValueError(
                f"Parsed JSON is missing required top-level keys: {missing}. "
                f"Got keys: {set(data.keys())}. "
                "Likely a truncated VLM response — only a sub-object was captured."
            )
        return data
