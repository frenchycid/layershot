"""Generate gondole (retail display shelf) moodboard refs via native SDXL.

These images are references for shooting actual retail gondolas (Sephora-style
display units) on a studio white background — NOT generic product shots.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.config import Config
from core.flux_client import FluxClient

PROMPTS = [
    "high-end retail cosmetics gondola display shelf, isolated on pure white studio background, "
    "seamless cyclorama, professional product photography lighting, soft key light, "
    "sharp focus, luxury beauty retail fixture, Sephora-style modular display unit, "
    "no people, commercial catalog photography, 8k ultra-detailed",

    "modern Sephora retail gondola unit with illuminated shelves, white seamless studio backdrop, "
    "professional strobe lighting, frontal hero shot, clean geometric design, matte black and chrome, "
    "empty shelves ready for products, architectural retail fixture photography, ultra sharp, 8k",

    "luxury perfume gondola display island, white infinity cove studio, softbox lighting, "
    "backlit glass shelves, polished metal frame, minimalist French retail aesthetic, "
    "high-end cosmetics fixture, hero product shot angle, commercial photography, 8k",

    "freestanding cosmetics retail gondola, empty illuminated shelves, pure white studio cyclorama, "
    "three-quarter angle view, professional lighting setup, subtle floor shadow, "
    "modular beauty retail display, premium fixture, ultra-detailed 8k product photography",

    "Sephora-style double-sided gondola merchandiser, white seamless backdrop, studio softboxes, "
    "black matte frame with LED-lit glass shelves, symmetrical composition, retail fixture catalog shot, "
    "clean commercial photography, hyperdetailed 8k",

    "tall luxury beauty gondola endcap display, white studio sweep, diffused top lighting, "
    "brushed metal frame, integrated LED strip lights, empty shelves, high-end retail fixture, "
    "commercial fixture photography, razor sharp, 8k",

    "premium cosmetics floor gondola with curved shelves, pure white infinity backdrop, "
    "studio beauty dish lighting, subtle gradient floor shadow, elegant retail fixture design, "
    "Parisian luxury aesthetic, catalog hero shot, ultra-detailed 8k",

    "modular retail gondola system, isolated on white studio cyclorama, frontal elevation view, "
    "industrial designer product shot, matte finish, empty glass and metal shelves, "
    "Sephora beauty store fixture, commercial photography, 8k sharp detail",
]

def main():
    cfg = Config()
    cfg.ensure_dirs()
    out_dir = cfg.moodboards_dir / "rendu-interieur"
    out_dir.mkdir(parents=True, exist_ok=True)

    client = FluxClient(cfg)

    for i, prompt in enumerate(PROMPTS, start=1):
        out = out_dir / f"gondole-ref-{i:02d}.jpg"
        print(f"\n[{i}/{len(PROMPTS)}] → {out.name}")
        print(f"    prompt: {prompt[:80]}...")
        client.generate(
            prompt=prompt,
            output_path=out,
            width=1024,
            height=1024,
            steps=25,
            seed=1000 + i,
        )

    print(f"\n✓ Generated {len(PROMPTS)} gondole refs in {out_dir}")

if __name__ == "__main__":
    main()
