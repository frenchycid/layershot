"""Brand Preservation Agent — Validates that brand elements survive AI generation."""

import json
import logging
from pathlib import Path
from typing import Optional, List
from PIL import Image
from io import BytesIO
import base64

from core.ai_backend import AIBackend

log = logging.getLogger("brand_preservation_agent")

SYSTEM_PROMPT = """You are a brand analysis expert evaluating whether AI-generated product images
preserve critical brand elements. Analyze the image for:
1. Logo visibility and integrity
2. Typography/text legibility and style preservation
3. Brand patterns or distinctive design elements
4. Color palette consistency with brand guidelines

Respond with valid JSON:
{
  "score": <0-100 preservation score>,
  "visible_elements": ["logo", "typography", "pattern"],
  "issues": ["list of specific preservation problems found"]
}

Score guidelines:
- 90-100: All critical elements clearly visible and intact
- 70-89: Most elements visible, minor quality loss
- 50-69: Some elements visible but compromised
- 0-49: Critical elements missing or severely degraded"""


class BrandPreservationAgent:
    """Validates that logos, typography, and patterns survive generation."""

    PRESERVATION_THRESHOLD = 70  # Minimum acceptable preservation score

    def __init__(self, ai_backend: Optional[AIBackend] = None):
        self.ai = ai_backend or AIBackend()

    def analyze(
        self,
        image: Image.Image,
        brand_context: str,
        save_to: Optional[Path] = None,
    ) -> dict:
        """Analyze image for brand element preservation."""
        log.info(f"Analyzing brand preservation for: {brand_context}")

        # Convert image to base64 for AI analysis
        img_data = self._image_to_base64(image)

        prompt = (
            f"Analyze this {brand_context} product image for brand preservation.\n\n"
            "Check for: logos, typography, patterns, color consistency.\n"
            "Respond with the JSON structure specified in your instructions."
        )

        raw = self.ai.analyze_image(prompt, img_data, system=SYSTEM_PROMPT)
        result = self._parse_json(raw)

        log.info(f"Brand preservation score: {result['score']}")

        if save_to:
            save_to.parent.mkdir(parents=True, exist_ok=True)
            save_to.write_text(json.dumps(result, indent=2))

        return result

    def batch_analyze(
        self,
        images: List[Image.Image],
        brand_context: str,
    ) -> List[dict]:
        """Analyze multiple images for brand preservation."""
        log.info(f"Analyzing {len(images)} images for brand preservation")

        results = []
        for idx, img in enumerate(images):
            log.debug(f"  Analyzing image {idx + 1}/{len(images)}")
            result = self.analyze(img, brand_context)
            results.append(result)

        return results

    def summarize_batch(
        self,
        results: List[dict],
        threshold: int = None,
    ) -> dict:
        """Summarize batch analysis results."""
        threshold = threshold or self.PRESERVATION_THRESHOLD

        scores = [r["score"] for r in results]
        passing = [s for s in scores if s >= threshold]

        return {
            "average_score": sum(scores) / len(scores) if scores else 0,
            "min_score": min(scores) if scores else 0,
            "max_score": max(scores) if scores else 0,
            "passing_count": len(passing),
            "failing_count": len(scores) - len(passing),
            "pass_rate": len(passing) / len(scores) if scores else 0,
        }

    def _image_to_base64(self, image: Image.Image) -> str:
        """Convert PIL Image to base64 string."""
        buf = BytesIO()
        image.save(buf, format="PNG")
        return base64.b64encode(buf.getvalue()).decode()

    def _parse_json(self, raw: str) -> dict:
        """Extract JSON from AI response."""
        if "```json" in raw:
            json_str = raw.split("```json")[1].split("```")[0].strip()
        elif "```" in raw:
            json_str = raw.split("```")[1].split("```")[0].strip()
        else:
            json_str = raw.strip()
        return json.loads(json_str)
