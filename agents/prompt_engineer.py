"""Prompt Engineer Agent — Generates reusable master prompts from style analysis."""

import json
import logging
from pathlib import Path
from typing import Optional

from core.ai_backend import AIBackend

log = logging.getLogger("prompt_engineer")

SYSTEM_PROMPT = """You are a prompt engineer specialized in AI image generation.
Given a photographic style analysis, create a structured master prompt for generating
product photography that matches the analyzed style.

You must respond with valid JSON matching this exact structure:
{
  "base_prompt": "A detailed prompt including all style attributes with INSERT YOUR PRODUCT HERE as placeholder",
  "product_placeholder": "INSERT YOUR PRODUCT HERE",
  "view_variants": {
    "wide": "additional terms for wide establishing shots",
    "closeup": "additional terms for macro/detail shots",
    "medium": "additional terms for medium product shots",
    "interior": "additional terms for interior lifestyle shots"
  },
  "negative_prompt": "comma-separated list of things to avoid"
}

Rules:
- Use precise photographic terms: atmospheric bloom, lifted blacks, film grain, 35mm lens, etc.
- NEVER use generic terms like "beautiful", "stunning", "nice"
- The base_prompt must contain INSERT YOUR PRODUCT HERE exactly once
- Each view_variant adds shot-specific terms, not full prompts
- The negative_prompt prevents common AI artifacts"""


class PromptEngineer:
    """Transforms style analysis into structured, reusable generation prompts."""

    def __init__(self, ai_backend: Optional[AIBackend] = None):
        self.ai = ai_backend or AIBackend()

    def generate(
        self,
        style_analysis: dict,
        save_to: Optional[Path] = None,
    ) -> dict:
        """Generate a master prompt from a style analysis."""
        log.info("Generating master prompt from style analysis...")

        prompt = (
            "Create a master prompt for AI image generation based on this style analysis:\n\n"
            f"{json.dumps(style_analysis, indent=2)}\n\n"
            "The prompt must capture ALL style attributes (lighting, colors, grain, lens, atmosphere) "
            "and include INSERT YOUR PRODUCT HERE as a placeholder for any product. "
            "Respond with the JSON structure specified in your instructions."
        )

        raw = self.ai.complete(prompt, system=SYSTEM_PROMPT)
        result = self._parse_json(raw)
        log.info(f"Master prompt generated ({len(result['base_prompt'])} chars)")

        if save_to:
            save_to.parent.mkdir(parents=True, exist_ok=True)
            save_to.write_text(json.dumps(result, indent=2, ensure_ascii=False))
            log.info(f"Master prompt saved to {save_to}")

        return result

    def build_prompt(self, master: dict, product: str, view: str) -> str:
        """Build a final generation prompt for a specific product and view."""
        base = master["base_prompt"].replace(
            master["product_placeholder"], product
        )
        view_suffix = master.get("view_variants", {}).get(view, "")
        if view_suffix:
            return f"{base}, {view_suffix}"
        return base

    def _parse_json(self, raw: str) -> dict:
        """Extract JSON from AI response."""
        text = raw.strip()
        if "```json" in text:
            text = text.split("```json", 1)[1].split("```", 1)[0]
        elif "```" in text:
            text = text.split("```", 1)[1].split("```", 1)[0]
        return json.loads(text.strip())
