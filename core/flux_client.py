"""HTTP client for the local Flux2 image generation server."""

import base64
import logging
from pathlib import Path
from typing import Optional

import httpx

from core.config import Config

log = logging.getLogger("flux_client")


class FluxClient:
    """Client for the Flux2 Klein 9B server on localhost:8190."""

    def __init__(self, config: Optional[Config] = None):
        self.config = config or Config()
        self.base_url = self.config.flux_url

    def health(self) -> dict:
        """Check if Flux server is running."""
        try:
            resp = httpx.get(f"{self.base_url}/health", timeout=5.0)
            return resp.json()
        except Exception as e:
            log.warning(f"Flux server unreachable: {e}")
            return {"status": "unreachable", "error": str(e)}

    def generate(
        self,
        prompt: str,
        output_path: Path,
        width: Optional[int] = None,
        height: Optional[int] = None,
        steps: Optional[int] = None,
        seed: Optional[int] = None,
    ) -> dict:
        """Generate an image and save it to output_path.

        Returns dict with seed, time_s, prompt.
        """
        payload = {
            "prompt": prompt,
            "width": width or self.config.image_width,
            "height": height or self.config.image_height,
            "steps": steps or self.config.flux_steps,
        }
        if seed is not None:
            payload["seed"] = seed

        log.info(f"Generating: {output_path.name}")
        resp = httpx.post(
            f"{self.base_url}/generate",
            json=payload,
            timeout=600.0,
        )
        resp.raise_for_status()
        data = resp.json()

        # Decode base64 image and save
        b64_data = data["image"].split(",", 1)[1]
        image_bytes = base64.b64decode(b64_data)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(image_bytes)
        log.info(f"Saved: {output_path} (seed={data['seed']}, {data['time_s']}s)")

        return {
            "seed": data["seed"],
            "time_s": data["time_s"],
            "prompt": data["prompt"],
            "path": str(output_path),
        }
