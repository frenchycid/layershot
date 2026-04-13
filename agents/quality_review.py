"""Quality Review Agent — Scores generated images on style, realism, and quality."""

import json
import logging
from pathlib import Path
from typing import Optional, List

from core.ai_backend import AIBackend

log = logging.getLogger("quality_review")

SYSTEM_PROMPT = """You are a product photography quality reviewer. You evaluate AI-generated
product images against a reference style.

Score each image on these 4 criteria (0-10 scale):
- style_coherence: How well does it match the reference style?
- realism: How photorealistic does it look?
- technical_quality: Resolution, artifacts, aberrations, composition?
- product_showcase: Is the product clearly visible and well-presented?

Respond with valid JSON:
{
  "style_coherence": 8.5,
  "realism": 7.0,
  "technical_quality": 9.0,
  "product_showcase": 8.0
}

Be strict. A score of 7+ means genuinely good. 5-7 is acceptable. Below 5 means regenerate."""

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}

# Weights for composite score
WEIGHTS = {
    "style_coherence": 0.30,
    "realism": 0.25,
    "technical_quality": 0.20,
    "product_showcase": 0.25,
}


class QualityReview:
    """Reviews generated images and scores them on quality criteria."""

    def __init__(self, ai_backend: Optional[AIBackend] = None):
        self.ai = ai_backend or AIBackend()

    def review_image(self, image_path: str, style_ref: dict) -> dict:
        """Review a single image against the style reference."""
        prompt = (
            "Evaluate this generated product image against the reference style.\n\n"
            f"Reference style: {json.dumps(style_ref)}\n\n"
            "Score it on the 4 criteria in your instructions. Respond with JSON only."
        )

        raw = self.ai.analyze_images([image_path], prompt, system=SYSTEM_PROMPT)
        scores = self._parse_json(raw)

        composite = sum(
            scores[k] * WEIGHTS[k] for k in WEIGHTS if k in scores
        )
        composite = round(composite, 1)

        return {
            "image_path": image_path,
            "scores": {**scores, "composite": composite},
            "recommendation": self._recommend(composite),
        }

    def review_batch(
        self,
        images_dir: Path,
        style_ref: dict,
        save_to: Optional[Path] = None,
    ) -> dict:
        """Review all images in a directory."""
        images = sorted(
            p for p in images_dir.iterdir()
            if p.suffix.lower() in IMAGE_EXTENSIONS
        )
        log.info(f"Reviewing {len(images)} images...")

        reviews = []
        for img in images:
            log.info(f"Reviewing: {img.name}")
            review = self.review_image(str(img), style_ref)
            reviews.append(review)

        reviews.sort(key=lambda r: r["scores"]["composite"], reverse=True)
        best = reviews[0] if reviews else None

        report = {
            "total": len(reviews),
            "reviews": reviews,
            "best": {"path": best["image_path"], "score": best["scores"]["composite"]} if best else None,
            "keep": [r for r in reviews if r["recommendation"] == "keep"],
            "regenerate": [r for r in reviews if r["recommendation"] == "regenerate"],
        }

        if save_to:
            save_to.parent.mkdir(parents=True, exist_ok=True)
            save_to.write_text(json.dumps(report, indent=2, ensure_ascii=False))
            log.info(f"Review report saved to {save_to}")

        return report

    def _recommend(self, composite: float) -> str:
        if composite >= 7.0:
            return "keep"
        if composite >= 5.0:
            return "maybe"
        return "regenerate"

    def _parse_json(self, raw: str) -> dict:
        text = raw.strip()
        if "```json" in text:
            text = text.split("```json", 1)[1].split("```", 1)[0]
        elif "```" in text:
            text = text.split("```", 1)[1].split("```", 1)[0]
        return json.loads(text.strip())
