"""Generate studio-photo packshot moodboard refs — pure white cyclorama,
isolated product, professional e-commerce catalog lighting. No interior,
no retail fixtures — just clean studio shots.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.config import Config
from core.flux_client import FluxClient

PROMPTS = [
    "professional e-commerce packshot of a luxury cosmetics bottle, pure white seamless studio "
    "cyclorama, soft beauty-dish lighting from above, subtle gradient floor shadow, crisp focus, "
    "clean commercial product photography, Amazon-grade catalog shot, ultra-sharp 8k, minimal styling",

    "high-end studio packshot of a glass perfume bottle, pure white infinity backdrop, symmetrical "
    "softbox lighting, crystal clear reflections, subtle contact shadow, magazine-ad quality, "
    "luxury beauty product photography, razor sharp, 8k catalog image",

    "minimalist product packshot of a skincare tube on pure white seamless background, even studio "
    "lighting, soft cast shadow, professional advertising photography, Sephora.com catalog style, "
    "hyperdetailed textures, 8k commercial shot",

    "studio packshot of a luxury watch, pure white cyclorama, three-light setup, crisp metallic "
    "reflections, polished case highlights, top catalog photography, ultra-detailed, 8k, no props",

    "e-commerce packshot of a designer handbag, pure white infinity backdrop, softbox lighting, "
    "subtle floor shadow, leather texture crisp, commercial retail photography, 8k ultra sharp, "
    "frontal hero shot, no model",

    "professional studio shot of a sneaker on pure white seamless, three-quarter angle, even "
    "softbox lighting, soft contact shadow, Nike-grade commercial photography, crisp fabric texture, "
    "hyperdetailed 8k catalog image",

    "studio packshot of a premium headphones set, pure white cyclorama, gradient drop shadow, "
    "polished metallic reflections, crisp focus on headband, Apple-style product photography, "
    "commercial hero shot, 8k sharp",

    "luxury jewelry packshot, diamond ring on pure white seamless backdrop, macro studio lighting, "
    "crystal facet reflections, subtle contact shadow, high-end catalog photography, razor sharp, "
    "8k commercial quality, no props",
]

def main():
    cfg = Config()
    cfg.ensure_dirs()
    out_dir = cfg.moodboards_dir / "studio"
    out_dir.mkdir(parents=True, exist_ok=True)

    # Wipe old mockup images that the user wanted replaced
    for old in out_dir.glob("*.jp*g"):
        old.unlink()
    for old in out_dir.glob("*.png"):
        old.unlink()

    client = FluxClient(cfg)

    for i, prompt in enumerate(PROMPTS, start=1):
        out = out_dir / f"studio-ref-{i:02d}.jpg"
        print(f"\n[{i}/{len(PROMPTS)}] -> {out.name}")
        print(f"    prompt: {prompt[:80]}...")
        client.generate(
            prompt=prompt,
            output_path=out,
            width=1024,
            height=1024,
            steps=25,
            seed=2000 + i,
        )

    print(f"\nGenerated {len(PROMPTS)} studio refs in {out_dir}")

if __name__ == "__main__":
    main()
