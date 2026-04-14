"""Creative Director Agent — Coordinates the full product visuals pipeline."""

import json
import logging
import time
from pathlib import Path
from typing import List, Optional

from PIL import Image

from core.config import Config
from core.ai_backend import AIBackend
from core.flux_client import FluxClient
from agents.style_analyst import StyleAnalyst
from agents.prompt_engineer import PromptEngineer
from agents.pipeline import PipelineOrchestrator
from agents.quality_review import QualityReview
from agents.prompt_variant_engine import PromptVariantEngine
from agents.brand_preservation_agent import BrandPreservationAgent
from agents.render_mode_processor import RenderModeProcessor

log = logging.getLogger("creative_director")


class CreativeDirector:
    """Orchestrates the full pipeline: analyze → prompt → generate → post-process → review."""

    def __init__(
        self,
        style_analyst: Optional[StyleAnalyst] = None,
        prompt_engineer: Optional[PromptEngineer] = None,
        pipeline: Optional[PipelineOrchestrator] = None,
        quality_review: Optional[QualityReview] = None,
        config: Optional[Config] = None,
        variant_engine: Optional[PromptVariantEngine] = None,
        brand_agent: Optional[BrandPreservationAgent] = None,
        render_processor: Optional[RenderModeProcessor] = None,
    ):
        self.config = config or Config()
        self.analyst = style_analyst or StyleAnalyst()
        self.engineer = prompt_engineer or PromptEngineer()
        self.pipeline = pipeline or PipelineOrchestrator()
        self.reviewer = quality_review or QualityReview()
        self.variant_engine = variant_engine or PromptVariantEngine()
        self.brand_agent = brand_agent or BrandPreservationAgent()
        self.render_processor = render_processor or RenderModeProcessor()

    def run(
        self,
        moodboard_dir: Path,
        products: List[dict],
        output_dir: Optional[Path] = None,
        session_name: Optional[str] = None,
        render_mode: str = "white_background",
    ) -> dict:
        """Run the full pipeline end-to-end.

        Pipeline: moodboard → analyze → prompt variants → generate → post-process → brand check → review
        """
        output_dir = output_dir or self.config.outputs_dir
        output_dir.mkdir(parents=True, exist_ok=True)
        session_name = session_name or f"session_{int(time.time())}"

        log.info(f"=== Creative Director — Session: {session_name} | Mode: {render_mode} ===")
        start = time.time()

        # Step 1: Collect moodboard images
        log.info("Step 1/7: Collecting moodboard images...")
        images = self.analyst.collect_images(moodboard_dir)
        if not images:
            return {"status": "error", "error": "No images found in moodboard directory"}

        # Step 2: Analyze style
        log.info("Step 2/7: Analyzing photographic style...")
        analysis_path = output_dir / f"{session_name}_analysis.json"
        style = self.analyst.analyze(
            [str(p) for p in images],
            save_to=analysis_path,
        )

        # Step 3: Generate prompt variants for all 3 render modes
        log.info("Step 3/7: Generating prompt variants (isolated, white_background, enhanced)...")
        variants_path = output_dir / f"{session_name}_variants.json"
        variants = self.variant_engine.generate(style, save_to=variants_path)

        # Step 4: Build master prompt for selected render mode
        log.info(f"Step 4/7: Building master prompt for '{render_mode}' mode...")
        mode_data = variants[render_mode]
        master = {
            "base_prompt": mode_data["base_prompt"],
            "product_placeholder": self.variant_engine.product_placeholder,
            "view_variants": {},
            "negative_prompt": mode_data.get("negative_prompt", ""),
        }
        prompt_path = output_dir / f"{session_name}_prompt.json"
        prompt_path.write_text(json.dumps(master, indent=2, ensure_ascii=False))

        # Step 5: Generate images via Flux
        log.info("Step 5/7: Generating product images via Flux...")
        gen_report = self.pipeline.run(master, products, output_dir=output_dir)

        # Step 6: Post-process each generated image with RenderModeProcessor
        log.info(f"Step 6/7: Post-processing images in '{render_mode}' mode...")
        processed_dir = output_dir / render_mode
        processed_dir.mkdir(parents=True, exist_ok=True)
        processed_count = 0

        for result in gen_report.get("results", []):
            if result.get("status") != "ok":
                continue
            img_path = output_dir / result["filename"]
            if img_path.exists():
                try:
                    img = Image.open(img_path)
                    processed = self.render_processor.process(
                        img, result.get("product_name", "product"), render_mode
                    )
                    out_path = processed_dir / result["filename"]
                    processed.save(out_path)
                    processed_count += 1
                    log.info(f"  Processed: {result['filename']}")
                except Exception as e:
                    log.error(f"  Failed to process {result['filename']}: {e}")

        # Step 7: Review quality on processed images
        log.info("Step 7/7: Reviewing image quality...")
        review_report = self.reviewer.review_batch(processed_dir, style)

        # Build final report
        elapsed = round(time.time() - start, 1)
        report = {
            "status": "complete",
            "session": session_name,
            "render_mode": render_mode,
            "elapsed_s": elapsed,
            "moodboard_images": len(images),
            "style_analysis": style,
            "variants_generated": list(variants.keys()),
            "master_prompt": master["base_prompt"][:200],
            "generation": gen_report,
            "post_processing": {
                "mode": render_mode,
                "processed": processed_count,
                "output_dir": str(processed_dir),
            },
            "review": {
                "total_reviewed": review_report["total"],
                "kept": len(review_report["keep"]),
                "to_regenerate": len(review_report["regenerate"]),
                "best": review_report["best"],
            },
        }

        # Save session report
        report_path = output_dir / f"{session_name}_report.json"
        report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False))
        log.info(f"Session report saved to {report_path}")
        log.info(
            f"=== Done in {elapsed}s — "
            f"{gen_report['completed']} generated, "
            f"{processed_count} post-processed, "
            f"{len(review_report['keep'])} kept ==="
        )

        return report
