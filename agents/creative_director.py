"""Creative Director Agent — Coordinates the full product visuals pipeline."""

import json
import logging
import time
from pathlib import Path
from typing import List, Optional

from core.config import Config
from core.ai_backend import AIBackend
from core.flux_client import FluxClient
from agents.style_analyst import StyleAnalyst
from agents.prompt_engineer import PromptEngineer
from agents.pipeline import PipelineOrchestrator
from agents.quality_review import QualityReview

log = logging.getLogger("creative_director")


class CreativeDirector:
    """Orchestrates the full pipeline: analyze → prompt → generate → review."""

    def __init__(
        self,
        style_analyst: Optional[StyleAnalyst] = None,
        prompt_engineer: Optional[PromptEngineer] = None,
        pipeline: Optional[PipelineOrchestrator] = None,
        quality_review: Optional[QualityReview] = None,
        config: Optional[Config] = None,
    ):
        self.config = config or Config()
        self.analyst = style_analyst or StyleAnalyst()
        self.engineer = prompt_engineer or PromptEngineer()
        self.pipeline = pipeline or PipelineOrchestrator()
        self.reviewer = quality_review or QualityReview()

    def run(
        self,
        moodboard_dir: Path,
        products: List[dict],
        output_dir: Optional[Path] = None,
        session_name: Optional[str] = None,
    ) -> dict:
        """Run the full pipeline end-to-end."""
        output_dir = output_dir or self.config.outputs_dir
        output_dir.mkdir(parents=True, exist_ok=True)
        session_name = session_name or f"session_{int(time.time())}"

        log.info(f"=== Creative Director — Session: {session_name} ===")
        start = time.time()

        # Step 1: Collect moodboard images
        log.info("Step 1/4: Collecting moodboard images...")
        images = self.analyst.collect_images(moodboard_dir)
        if not images:
            return {"status": "error", "error": "No images found in moodboard directory"}

        # Step 2: Analyze style
        log.info("Step 2/4: Analyzing photographic style...")
        analysis_path = output_dir / f"{session_name}_analysis.json"
        style = self.analyst.analyze(
            [str(p) for p in images],
            save_to=analysis_path,
        )

        # Step 3: Generate master prompt
        log.info("Step 3/4: Generating master prompt...")
        prompt_path = output_dir / f"{session_name}_prompt.json"
        master = self.engineer.generate(style, save_to=prompt_path)

        # Step 4: Generate images
        log.info("Step 4/4: Generating product images...")
        gen_report = self.pipeline.run(master, products, output_dir=output_dir)

        # Step 5: Review quality
        log.info("Step 5/5: Reviewing image quality...")
        review_report = self.reviewer.review_batch(output_dir, style)

        # Build final report
        elapsed = round(time.time() - start, 1)
        report = {
            "status": "complete",
            "session": session_name,
            "elapsed_s": elapsed,
            "moodboard_images": len(images),
            "style_analysis": style,
            "master_prompt": master["base_prompt"][:200],
            "generation": gen_report,
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
            f"{gen_report['completed']} images, "
            f"{len(review_report['keep'])} kept ==="
        )

        return report
