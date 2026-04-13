"""Brief Parser Agent — Parses client briefs into structured JSON."""

import json
import logging
from pathlib import Path
from typing import Optional

from core.ai_backend import AIBackend

log = logging.getLogger("brief_parser")

SYSTEM_PROMPT = """You are a creative brief analyst for a professional photography studio.
You extract structured information from client briefs written in any language.

You must respond with valid JSON matching this exact structure:
{
  "brand": "brand or client name",
  "products": ["list of products or subjects to shoot"],
  "palette": ["list of colors or color directions"],
  "style_keywords": ["list of style descriptors"],
  "deliverables": ["list of expected outputs: number of shots, formats, etc."],
  "constraints": ["list of restrictions or mandatory requirements"]
}

Be concise. Extract only what is explicitly stated or clearly implied.
If a field has no relevant information, use an empty list or empty string.
Do NOT include extra keys. Do NOT wrap in markdown."""


class BriefParser:
    """Parses a client creative brief into a structured JSON profile."""

    def __init__(self, ai_backend: Optional[AIBackend] = None):
        self.ai = ai_backend or AIBackend()

    def load_brief(self, source: str) -> str:
        """Load brief content from a .txt file path or return text directly."""
        if source.endswith(".txt"):
            path = Path(source)
            if path.exists():
                log.info(f"Loading brief from file: {path}")
                return path.read_text(encoding="utf-8")
        return source

    def parse(self, brief_input: str, save_to: Optional[Path] = None) -> dict:
        """Parse a brief string and return structured dict. Optionally save JSON."""
        log.info("Parsing creative brief...")

        prompt = (
            f"Parse the following client creative brief and extract structured information.\n\n"
            f"Brief:\n{brief_input}\n\n"
            "Respond with the JSON structure specified in your instructions."
        )

        raw = self.ai.complete(prompt, system=SYSTEM_PROMPT)
        result = self._parse_json(raw)
        result["raw_brief"] = brief_input

        log.info(f"Brief parsed: brand={result.get('brand', '?')!r}, "
                 f"{len(result.get('products', []))} products")

        if save_to:
            save_to = Path(save_to)
            save_to.parent.mkdir(parents=True, exist_ok=True)
            save_to.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
            log.info(f"Brief saved to {save_to}")

        return result

    def _parse_json(self, raw: str) -> dict:
        """Extract JSON from AI response, handling markdown code blocks."""
        text = raw.strip()
        if "```json" in text:
            text = text.split("```json", 1)[1].split("```", 1)[0]
        elif "```" in text:
            text = text.split("```", 1)[1].split("```", 1)[0]
        return json.loads(text.strip())
