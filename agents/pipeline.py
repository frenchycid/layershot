"""Pipeline Orchestrator Agent — Batch image generation via Flux."""

import re
import json
import logging
import time
from pathlib import Path
from typing import List, Optional

from core.config import Config
from core.flux_client import FluxClient

log = logging.getLogger("pipeline")


class PipelineOrchestrator:
    """Generates product images in batch across views and variants."""

    def __init__(
        self,
        flux_client: Optional[FluxClient] = None,
        config: Optional[Config] = None,
    ):
        self.config = config or Config()
        self.flux = flux_client or FluxClient(self.config)

    def build_jobs(self, master: dict, products: List[dict]) -> List[dict]:
        """Build the list of generation jobs.

        Each product dict has keys: name, color.
        Returns list of job dicts with prompt, filename, metadata.
        """
        jobs = []
        placeholder = master["product_placeholder"]
        views = self.config.views
        variants = self.config.variants_per_view

        for product in products:
            name = product["name"]
            color = product["color"]
            product_desc = f"{color} {name}"

            for view in views:
                base = master["base_prompt"].replace(placeholder, product_desc)
                view_suffix = master.get("view_variants", {}).get(view, "")
                prompt = f"{base}, {view_suffix}" if view_suffix else base

                for v in range(1, variants + 1):
                    jobs.append({
                        "prompt": prompt,
                        "filename": self._make_filename(name, color, view, v),
                        "product_name": name,
                        "color": color,
                        "view": view,
                        "variant": v,
                    })

        log.info(f"Built {len(jobs)} generation jobs")
        return jobs

    def run(
        self,
        master: dict,
        products: List[dict],
        output_dir: Optional[Path] = None,
    ) -> dict:
        """Execute all generation jobs and return a report."""
        output_dir = output_dir or self.config.outputs_dir
        output_dir.mkdir(parents=True, exist_ok=True)
        jobs = self.build_jobs(master, products)

        report = {
            "total": len(jobs),
            "completed": 0,
            "errors": 0,
            "results": [],
            "start_time": time.time(),
        }

        for i, job in enumerate(jobs, 1):
            log.info(f"[{i}/{len(jobs)}] {job['filename']}")
            output_path = output_dir / job["filename"]

            try:
                result = self.flux.generate(
                    prompt=job["prompt"],
                    output_path=output_path,
                )
                report["completed"] += 1
                report["results"].append({
                    "filename": job["filename"],
                    "status": "ok",
                    **result,
                    **{k: job[k] for k in ("product_name", "color", "view", "variant")},
                })
            except Exception as e:
                log.error(f"Failed: {job['filename']} — {e}")
                report["errors"] += 1
                report["results"].append({
                    "filename": job["filename"],
                    "status": "error",
                    "error": str(e),
                    **{k: job[k] for k in ("product_name", "color", "view", "variant")},
                })

        report["elapsed_s"] = round(time.time() - report["start_time"], 1)
        del report["start_time"]
        log.info(
            f"Pipeline complete: {report['completed']}/{report['total']} OK, "
            f"{report['errors']} errors, {report['elapsed_s']}s total"
        )
        return report

    def _make_filename(self, name: str, color: str, view: str, variant: int) -> str:
        """Generate filename: [product]_[color]_[view]_[variant].png"""
        slug = lambda s: re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")
        return f"{slug(name)}_{slug(color)}_{view}_{variant:03d}.png"
