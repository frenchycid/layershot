#!/usr/bin/env python3
"""LayerShot — CLI for photoreal product image generation."""

import argparse
import json
import logging
import sys
from pathlib import Path

from core.config import Config
from core.ai_backend import AIBackend
from core.flux_client import FluxClient
from agents.style_analyst import StyleAnalyst
from agents.prompt_engineer import PromptEngineer
from agents.pipeline import PipelineOrchestrator
from agents.quality_review import QualityReview
from agents.creative_director import CreativeDirector


def parse_products(product_args: list) -> list:
    """Parse 'name:color' product arguments into dicts."""
    products = []
    for p in product_args:
        if ":" in p:
            name, color = p.split(":", 1)
        else:
            name, color = p, "default"
        products.append({"name": name.strip(), "color": color.strip()})
    return products


def cmd_analyze(args, config):
    """Analyze moodboard style."""
    ai = AIBackend(config)
    analyst = StyleAnalyst(ai_backend=ai)

    moodboard = Path(args.moodboard)
    images = analyst.collect_images(moodboard)
    if not images:
        print(f"No images found in {moodboard}")
        sys.exit(1)

    print(f"Found {len(images)} reference images")
    output = Path(args.output) if args.output else config.prompts_dir / "analysis.json"
    result = analyst.analyze([str(p) for p in images], save_to=output)
    print(f"\nStyle summary: {result.get('style_summary', 'N/A')}")
    print(f"Saved to: {output}")


def cmd_prompt(args, config):
    """Generate master prompt from analysis."""
    ai = AIBackend(config)
    engineer = PromptEngineer(ai_backend=ai)

    analysis = json.loads(Path(args.analysis).read_text())
    output = Path(args.output) if args.output else config.prompts_dir / "master_prompt.json"
    result = engineer.generate(analysis, save_to=output)
    print(f"Master prompt generated ({len(result['base_prompt'])} chars)")
    print(f"Views: {', '.join(result.get('view_variants', {}).keys())}")
    print(f"Saved to: {output}")


def cmd_generate(args, config):
    """Generate images from master prompt."""
    flux = FluxClient(config)
    health = flux.health()
    if health["status"] != "ok":
        print(f"Flux server not available: {health}")
        sys.exit(1)

    master = json.loads(Path(args.prompt).read_text())
    products = parse_products(args.products)
    output_dir = Path(args.output) if args.output else config.outputs_dir

    orch = PipelineOrchestrator(flux_client=flux, config=config)
    print(f"Generating images for {len(products)} products...")
    report = orch.run(master, products, output_dir=output_dir)

    print(f"\nDone: {report['completed']}/{report['total']} images")
    if report["errors"]:
        print(f"Errors: {report['errors']}")


def cmd_review(args, config):
    """Review generated images."""
    ai = AIBackend(config)
    reviewer = QualityReview(ai_backend=ai)

    images_dir = Path(args.images)
    style_ref = {}
    if args.analysis:
        style_ref = json.loads(Path(args.analysis).read_text())

    output = Path(args.output) if args.output else images_dir / "review_report.json"
    report = reviewer.review_batch(images_dir, style_ref, save_to=output)

    print(f"Reviewed: {report['total']} images")
    print(f"Keep: {len(report['keep'])} | Regenerate: {len(report['regenerate'])}")
    if report["best"]:
        print(f"Best: {report['best']['path']} (score: {report['best']['score']})")


def cmd_run(args, config):
    """Run full pipeline end-to-end."""
    ai = AIBackend(config)
    flux = FluxClient(config)
    health = flux.health()
    if health["status"] != "ok":
        print(f"Flux server not available: {health}")
        sys.exit(1)

    director = CreativeDirector(
        style_analyst=StyleAnalyst(ai_backend=ai),
        prompt_engineer=PromptEngineer(ai_backend=ai),
        pipeline=PipelineOrchestrator(flux_client=flux, config=config),
        quality_review=QualityReview(ai_backend=ai),
        config=config,
    )

    products = parse_products(args.products)
    output_dir = Path(args.output) if args.output else config.outputs_dir

    print(f"Full pipeline: {args.moodboard} -> {len(products)} products")
    report = director.run(
        moodboard_dir=Path(args.moodboard),
        products=products,
        output_dir=output_dir,
        session_name=args.session,
    )

    print(f"\n{'='*50}")
    print(f"Status: {report['status']}")
    if report["status"] == "complete":
        print(f"Images: {report['generation']['completed']}/{report['generation']['total']}")
        print(f"Kept: {report['review']['kept']}")
        print(f"Time: {report['elapsed_s']}s")
        if report["review"]["best"]:
            print(f"Best: {report['review']['best']['path']}")
    else:
        print(f"Error: {report.get('error', 'unknown')}")


def main():
    parser = argparse.ArgumentParser(
        prog="layershot",
        description="LayerShot — Generate photoreal product visuals with AI",
    )
    sub = parser.add_subparsers(dest="command")

    # analyze
    p_analyze = sub.add_parser("analyze", help="Analyze moodboard style")
    p_analyze.add_argument("--moodboard", "-m", required=True, help="Moodboard directory")
    p_analyze.add_argument("--output", "-o", help="Output JSON path")

    # prompt
    p_prompt = sub.add_parser("prompt", help="Generate master prompt")
    p_prompt.add_argument("--analysis", "-a", required=True, help="Style analysis JSON")
    p_prompt.add_argument("--output", "-o", help="Output JSON path")

    # generate
    p_gen = sub.add_parser("generate", help="Generate product images")
    p_gen.add_argument("--prompt", "-p", required=True, help="Master prompt JSON")
    p_gen.add_argument("--products", nargs="+", required=True, help="Products as name:color")
    p_gen.add_argument("--output", "-o", help="Output directory")

    # review
    p_review = sub.add_parser("review", help="Review generated images")
    p_review.add_argument("--images", "-i", required=True, help="Images directory")
    p_review.add_argument("--analysis", "-a", help="Style analysis JSON for reference")
    p_review.add_argument("--output", "-o", help="Output report path")

    # run (full pipeline)
    p_run = sub.add_parser("run", help="Run full pipeline end-to-end")
    p_run.add_argument("--moodboard", "-m", required=True, help="Moodboard directory")
    p_run.add_argument("--products", nargs="+", required=True, help="Products as name:color")
    p_run.add_argument("--output", "-o", help="Output directory")
    p_run.add_argument("--session", "-s", default=None, help="Session name")

    args = parser.parse_args()
    config = Config()
    config.ensure_dirs()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(name)s] %(message)s",
        datefmt="%H:%M:%S",
    )

    commands = {
        "analyze": cmd_analyze,
        "prompt": cmd_prompt,
        "generate": cmd_generate,
        "review": cmd_review,
        "run": cmd_run,
    }

    if args.command in commands:
        commands[args.command](args, config)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
