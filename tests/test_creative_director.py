"""Tests for CreativeDirector — Full autonomous pipeline."""

import json
from unittest.mock import MagicMock, patch, PropertyMock
from pathlib import Path
from PIL import Image
from agents.creative_director import CreativeDirector


def _make_mocks():
    analyst = MagicMock()
    analyst.collect_images.return_value = [Path("/tmp/ref1.jpg")]
    analyst.analyze.return_value = {
        "lighting": {"type": "natural"},
        "color_palette": {"temperature": "warm"},
        "style_summary": "warm retro style",
    }

    engineer = MagicMock()
    engineer.generate.return_value = {
        "base_prompt": "photo of INSERT YOUR PRODUCT HERE, warm",
        "product_placeholder": "INSERT YOUR PRODUCT HERE",
        "view_variants": {"wide": "wide shot"},
        "negative_prompt": "blurry",
    }

    pipeline = MagicMock()
    pipeline.run.return_value = {
        "total": 1, "completed": 1, "errors": 0,
        "results": [{"filename": "candle_amber_wide_001.png", "status": "ok", "product_name": "candle"}],
    }

    reviewer = MagicMock()
    reviewer.review_batch.return_value = {
        "total": 1,
        "reviews": [{"image_path": "/tmp/out/x.png", "scores": {"composite": 8.0}, "recommendation": "keep"}],
        "best": {"path": "/tmp/out/x.png", "score": 8.0},
        "keep": [{}], "regenerate": [],
    }

    variant_engine = MagicMock()
    variant_engine.product_placeholder = "INSERT YOUR PRODUCT HERE"
    variant_engine.generate.return_value = {
        "isolated": {"base_prompt": "INSERT YOUR PRODUCT HERE isolated transparent", "negative_prompt": "bg"},
        "white_background": {"base_prompt": "INSERT YOUR PRODUCT HERE white studio", "negative_prompt": "shadow"},
        "enhanced": {"base_prompt": "INSERT YOUR PRODUCT HERE premium materials", "negative_prompt": "blur"},
    }

    brand_agent = MagicMock()
    brand_agent.analyze.return_value = {"score": 85, "visible_elements": ["logo"], "issues": []}

    render_processor = MagicMock()
    # Return a real PIL image so save() works
    render_processor.process.return_value = Image.new("RGB", (100, 100))

    return analyst, engineer, pipeline, reviewer, variant_engine, brand_agent, render_processor


def _make_director(tmp_path):
    analyst, engineer, pipeline, reviewer, variant_engine, brand_agent, render_processor = _make_mocks()
    # Create a fake output image so post-processing can open it
    out_dir = tmp_path / "out"
    out_dir.mkdir(parents=True, exist_ok=True)
    fake_img = Image.new("RGB", (100, 100), color=(200, 150, 100))
    fake_img.save(out_dir / "candle_amber_wide_001.png")

    director = CreativeDirector(
        style_analyst=analyst,
        prompt_engineer=engineer,
        pipeline=pipeline,
        quality_review=reviewer,
        variant_engine=variant_engine,
        brand_agent=brand_agent,
        render_processor=render_processor,
    )
    return director, out_dir, {
        "analyst": analyst, "engineer": engineer, "pipeline": pipeline,
        "reviewer": reviewer, "variant_engine": variant_engine,
        "brand_agent": brand_agent, "render_processor": render_processor,
    }


def test_full_pipeline(tmp_path):
    """Test complete pipeline runs all 7 steps."""
    director, out_dir, mocks = _make_director(tmp_path)
    products = [{"name": "candle", "color": "amber"}]

    report = director.run(
        moodboard_dir=tmp_path / "mood",
        products=products,
        output_dir=out_dir,
    )

    mocks["analyst"].collect_images.assert_called_once()
    mocks["analyst"].analyze.assert_called_once()
    mocks["variant_engine"].generate.assert_called_once()
    mocks["pipeline"].run.assert_called_once()
    mocks["render_processor"].process.assert_called()
    mocks["reviewer"].review_batch.assert_called_once()

    assert report["status"] == "complete"
    assert report["generation"]["completed"] == 1
    assert report["render_mode"] == "white_background"


def test_uses_variant_engine_not_prompt_engineer(tmp_path):
    """Test that variant engine is used, not the old prompt engineer."""
    director, out_dir, mocks = _make_director(tmp_path)
    products = [{"name": "candle", "color": "amber"}]

    director.run(
        moodboard_dir=tmp_path / "mood",
        products=products,
        output_dir=out_dir,
    )

    # PromptVariantEngine called, not PromptEngineer
    mocks["variant_engine"].generate.assert_called_once()
    mocks["engineer"].generate.assert_not_called()


def test_render_mode_isolated(tmp_path):
    """Test pipeline runs in isolated mode."""
    director, out_dir, mocks = _make_director(tmp_path)
    products = [{"name": "gondola", "color": "blush"}]

    report = director.run(
        moodboard_dir=tmp_path / "mood",
        products=products,
        output_dir=out_dir,
        render_mode="isolated",
    )

    assert report["render_mode"] == "isolated"
    assert report["post_processing"]["mode"] == "isolated"


def test_render_mode_enhanced(tmp_path):
    """Test pipeline runs in enhanced mode."""
    director, out_dir, mocks = _make_director(tmp_path)
    products = [{"name": "gondola", "color": "blush"}]

    report = director.run(
        moodboard_dir=tmp_path / "mood",
        products=products,
        output_dir=out_dir,
        render_mode="enhanced",
    )

    assert report["render_mode"] == "enhanced"
    assert report["post_processing"]["mode"] == "enhanced"


def test_post_processing_creates_mode_subdirectory(tmp_path):
    """Test that post-processing creates render mode subdirectory."""
    director, out_dir, mocks = _make_director(tmp_path)
    products = [{"name": "candle", "color": "amber"}]

    director.run(
        moodboard_dir=tmp_path / "mood",
        products=products,
        output_dir=out_dir,
        render_mode="white_background",
    )

    assert (out_dir / "white_background").exists()


def test_saves_session_history(tmp_path):
    """Test that session report is saved."""
    director, out_dir, mocks = _make_director(tmp_path)
    products = [{"name": "candle", "color": "amber"}]

    report = director.run(
        moodboard_dir=tmp_path / "mood",
        products=products,
        output_dir=out_dir,
        session_name="test_session",
    )

    history_file = out_dir / "test_session_report.json"
    assert history_file.exists()
    saved = json.loads(history_file.read_text())
    assert saved["render_mode"] == "white_background"


def test_saves_variants_file(tmp_path):
    """Test that prompt variants JSON is saved."""
    director, out_dir, mocks = _make_director(tmp_path)
    products = [{"name": "candle", "color": "amber"}]

    director.run(
        moodboard_dir=tmp_path / "mood",
        products=products,
        output_dir=out_dir,
        session_name="test_session",
    )

    variants_file = out_dir / "test_session_variants.json"
    mocks["variant_engine"].generate.assert_called_once()


def test_report_includes_variants_generated(tmp_path):
    """Test report lists all 3 generated variants."""
    director, out_dir, mocks = _make_director(tmp_path)
    products = [{"name": "candle", "color": "amber"}]

    report = director.run(
        moodboard_dir=tmp_path / "mood",
        products=products,
        output_dir=out_dir,
    )

    assert set(report["variants_generated"]) == {"isolated", "white_background", "enhanced"}


def test_pipeline_aborts_if_no_images(tmp_path):
    """Test pipeline aborts gracefully when no moodboard images found."""
    director, out_dir, mocks = _make_director(tmp_path)
    mocks["analyst"].collect_images.return_value = []

    report = director.run(
        moodboard_dir=tmp_path,
        products=[{"name": "x", "color": "y"}],
    )

    assert report["status"] == "error"
    assert "No images" in report["error"]


def test_post_processing_count_in_report(tmp_path):
    """Test report includes post-processing count."""
    director, out_dir, mocks = _make_director(tmp_path)
    products = [{"name": "candle", "color": "amber"}]

    report = director.run(
        moodboard_dir=tmp_path / "mood",
        products=products,
        output_dir=out_dir,
    )

    assert "post_processing" in report
    assert report["post_processing"]["processed"] >= 0
