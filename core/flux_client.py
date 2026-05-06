"""FLUX 2.0 image generation — native Python (no server, no ComfyUI)."""

import logging
import os
from pathlib import Path
from typing import Optional
import time

from core.config import Config

log = logging.getLogger("flux_client")


class FluxClient:
    """Native FLUX.1-dev image generation via diffusers."""

    def __init__(self, config: Optional[Config] = None):
        self.config = config or Config()
        self.model_id = "stabilityai/stable-diffusion-xl-base-1.0"  # Open access, pro quality
        self.pipe = None
        self.device = "cpu"
        log.info(f"FluxClient: SDXL native (pro quality, no server)")

    def _load_model(self):
        """Lazy-load SDXL model."""
        if self.pipe is not None:
            return

        log.info("Loading SDXL model (first run, ~7GB)...")
        try:
            from diffusers import StableDiffusionXLPipeline
            import torch

            if torch.backends.mps.is_available():
                self.device = "mps"
                log.info("Apple Silicon detected, using MPS")
            elif torch.cuda.is_available():
                self.device = "cuda"
                log.info("CUDA available, using GPU")
            else:
                self.device = "cpu"

            self.pipe = StableDiffusionXLPipeline.from_pretrained(
                self.model_id,
                torch_dtype=torch.float16 if self.device != "cpu" else torch.float32,
            )
            self.pipe = self.pipe.to(self.device)
            log.info(f"✓ SDXL loaded on {self.device}")
        except Exception as e:
            log.error(f"Failed to load model: {e}")
            raise

    def health(self) -> dict:
        """Check model availability."""
        try:
            import torch
            return {"status": "ok", "backend": "native", "model": "SDXL", "device": self.device}
        except Exception as e:
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
        """Generate image with FLUX.1-dev."""
        self._load_model()

        w = width or self.config.image_width
        h = height or self.config.image_height
        num_steps = steps or 30

        log.info(f"Generating: {output_path.name} ({w}x{h}, {num_steps} steps)")
        start = time.time()

        try:
            import torch

            # Generate with FLUX
            with torch.inference_mode():
                image = self.pipe(
                    prompt=prompt,
                    height=h,
                    width=w,
                    num_inference_steps=num_steps,
                    guidance_scale=0.0,  # FLUX doesn't use guidance
                    generator=torch.Generator(device=self.device).manual_seed(seed or 0) if seed else None,
                ).images[0]

            # Save
            output_path.parent.mkdir(parents=True, exist_ok=True)
            image.save(output_path)

            elapsed = time.time() - start
            log.info(f"✓ Saved: {output_path} ({elapsed:.1f}s)")

            return {
                "seed": seed or 0,
                "time_s": elapsed,
                "prompt": prompt,
                "path": str(output_path),
            }
        except Exception as e:
            log.error(f"Generation failed: {e}")
            raise
