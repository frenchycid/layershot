"""Prompt Variant Engine — Generates 3 render mode prompts from style analysis."""

import json
import logging
from pathlib import Path
from typing import Optional

from core.ai_backend import AIBackend

log = logging.getLogger("prompt_variant_engine")

SYSTEM_PROMPT = """You are a prompt engineer specialized in multi-variant AI image generation.
Given a photographic style analysis, create 3 structured prompts for different render modes:
- isolated: product alone on transparent/PNG background (e-commerce, no context)
- white_background: product on white background with studio lighting (professional product shoot)
- enhanced: product with premium material emphasis and detailed textures (luxury/catalog)

Each variant must preserve INSERT YOUR PRODUCT HERE placeholder exactly once.

Respond with valid JSON:
{
  "isolated": {
    "base_prompt": "detailed prompt with INSERT YOUR PRODUCT HERE, emphasize transparency/PNG/alpha",
    "negative_prompt": "comma-separated things to avoid"
  },
  "white_background": {
    "base_prompt": "studio-style prompt with INSERT YOUR PRODUCT HERE, white background, professional lighting",
    "negative_prompt": "comma-separated things to avoid"
  },
  "enhanced": {
    "base_prompt": "premium prompt with INSERT YOUR PRODUCT HERE, material textures, fine details",
    "negative_prompt": "comma-separated things to avoid"
  }
}

Rules:
- Use precise photographic terms
- NEVER use generic terms like "beautiful", "stunning"
- Each variant is distinct in style and purpose
- Preserve INSERT YOUR PRODUCT HERE exactly once per variant
- Negative prompts prevent artifacts specific to each mode"""


class PromptVariantEngine:
    """Generates 3 render mode prompt variants from a single style analysis."""

    def __init__(self, ai_backend: Optional[AIBackend] = None):
        self.ai = ai_backend or AIBackend()
        self.product_placeholder = "INSERT YOUR PRODUCT HERE"

    def generate(
        self,
        style_analysis: dict,
        save_to: Optional[Path] = None,
    ) -> dict:
        """Generate 3 render mode variants from style analysis."""
        log.info("Generating prompt variants for 3 render modes...")

        prompt = (
            "Create prompt variants for 3 render modes based on this style analysis:\n\n"
            f"{json.dumps(style_analysis, indent=2)}\n\n"
            f"Each variant must contain '{self.product_placeholder}' exactly once. "
            "Respond with the JSON structure specified in your instructions."
        )

        raw = self.ai.complete(prompt, system=SYSTEM_PROMPT)
        result = self._parse_json(raw)

        # Validate all three modes exist
        required_modes = ["isolated", "white_background", "enhanced"]
        for mode in required_modes:
            if mode not in result:
                raise KeyError(f"Missing required render mode: {mode}")

        log.info(f"Generated variants for modes: {', '.join(result.keys())}")

        if save_to:
            save_to.parent.mkdir(parents=True, exist_ok=True)
            save_to.write_text(json.dumps(result, indent=2, ensure_ascii=False))
            log.info(f"Variants saved to {save_to}")

        return result

    def build_prompt(self, variants: dict, product: str, render_mode: str) -> str:
        """Build final generation prompt for specific product and render mode."""
        if render_mode not in variants:
            raise KeyError(f"Unknown render mode: {render_mode}")

        mode_data = variants[render_mode]
        base = mode_data["base_prompt"].replace(
            self.product_placeholder, product
        )
        return base

    def _parse_json(self, raw: str) -> dict:
        """Extract JSON from AI response, handling markdown code blocks."""
        if "```json" in raw:
            json_str = raw.split("```json")[1].split("```")[0].strip()
        elif "```" in raw:
            json_str = raw.split("```")[1].split("```")[0].strip()
        else:
            json_str = raw.strip()
        return json.loads(json_str)
