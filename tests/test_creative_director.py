import json
from unittest.mock import MagicMock, patch
from pathlib import Path
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
        "results": [{"filename": "candle_amber_wide_001.png", "status": "ok"}],
    }

    reviewer = MagicMock()
    reviewer.review_batch.return_value = {
        "total": 1,
        "reviews": [{"image_path": "/tmp/out/x.png", "scores": {"composite": 8.0}, "recommendation": "keep"}],
        "best": {"path": "/tmp/out/x.png", "score": 8.0},
        "keep": [{}], "regenerate": [],
    }

    return analyst, engineer, pipeline, reviewer


def test_full_pipeline(tmp_path):
    analyst, engineer, pipeline, reviewer = _make_mocks()
    director = CreativeDirector(
        style_analyst=analyst,
        prompt_engineer=engineer,
        pipeline=pipeline,
        quality_review=reviewer,
    )

    products = [{"name": "candle", "color": "amber"}]
    report = director.run(
        moodboard_dir=tmp_path / "mood",
        products=products,
        output_dir=tmp_path / "out",
    )

    analyst.collect_images.assert_called_once()
    analyst.analyze.assert_called_once()
    engineer.generate.assert_called_once()
    pipeline.run.assert_called_once()
    reviewer.review_batch.assert_called_once()

    assert report["status"] == "complete"
    assert report["generation"]["completed"] == 1


def test_saves_session_history(tmp_path):
    analyst, engineer, pipeline, reviewer = _make_mocks()
    director = CreativeDirector(
        style_analyst=analyst,
        prompt_engineer=engineer,
        pipeline=pipeline,
        quality_review=reviewer,
    )

    products = [{"name": "candle", "color": "amber"}]
    (tmp_path / "mood").mkdir()
    report = director.run(
        moodboard_dir=tmp_path / "mood",
        products=products,
        output_dir=tmp_path / "out",
        session_name="test_session",
    )

    history_file = tmp_path / "out" / "test_session_report.json"
    assert history_file.exists()


def test_pipeline_aborts_if_no_images(tmp_path):
    analyst, engineer, pipeline, reviewer = _make_mocks()
    analyst.collect_images.return_value = []

    director = CreativeDirector(
        style_analyst=analyst,
        prompt_engineer=engineer,
        pipeline=pipeline,
        quality_review=reviewer,
    )

    report = director.run(
        moodboard_dir=tmp_path,
        products=[{"name": "x", "color": "y"}],
    )

    assert report["status"] == "error"
    assert "No images" in report["error"]
