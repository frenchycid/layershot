import json
from unittest.mock import MagicMock, call
from pathlib import Path
from agents.pipeline import PipelineOrchestrator
from core.config import Config


def test_build_job_list():
    config = Config(variants_per_view=2, views=["wide", "closeup"])
    orch = PipelineOrchestrator(flux_client=MagicMock(), config=config)

    master = {
        "base_prompt": "photo of INSERT YOUR PRODUCT HERE, warm tones",
        "product_placeholder": "INSERT YOUR PRODUCT HERE",
        "view_variants": {"wide": "wide shot", "closeup": "macro"},
        "negative_prompt": "blurry",
    }
    products = [{"name": "candle", "color": "amber"}]

    jobs = orch.build_jobs(master, products)

    assert len(jobs) == 4  # 1 product x 2 views x 2 variants
    assert jobs[0]["product_name"] == "candle"
    assert jobs[0]["color"] == "amber"
    assert "candle_amber_wide_001.png" == jobs[0]["filename"]


def test_filename_convention():
    orch = PipelineOrchestrator(flux_client=MagicMock())
    name = orch._make_filename("Glass Vase", "Cream White", "closeup", 3)
    assert name == "glass-vase_cream-white_closeup_003.png"


def test_run_executes_all_jobs(tmp_path):
    mock_flux = MagicMock()
    mock_flux.generate.return_value = {"seed": 42, "time_s": 3.0, "prompt": "test", "path": "x"}

    config = Config(variants_per_view=1, views=["wide"])
    orch = PipelineOrchestrator(flux_client=mock_flux, config=config)

    master = {
        "base_prompt": "photo of INSERT YOUR PRODUCT HERE",
        "product_placeholder": "INSERT YOUR PRODUCT HERE",
        "view_variants": {"wide": "wide shot"},
        "negative_prompt": "blurry",
    }
    products = [
        {"name": "candle", "color": "amber"},
        {"name": "vase", "color": "cream"},
    ]

    report = orch.run(master, products, output_dir=tmp_path)

    assert mock_flux.generate.call_count == 2
    assert len(report["results"]) == 2
    assert report["total"] == 2


def test_run_handles_flux_error(tmp_path):
    mock_flux = MagicMock()
    mock_flux.generate.side_effect = Exception("Flux down")

    config = Config(variants_per_view=1, views=["wide"])
    orch = PipelineOrchestrator(flux_client=mock_flux, config=config)

    master = {
        "base_prompt": "photo of INSERT YOUR PRODUCT HERE",
        "product_placeholder": "INSERT YOUR PRODUCT HERE",
        "view_variants": {"wide": "wide"},
        "negative_prompt": "",
    }

    report = orch.run(master, [{"name": "x", "color": "y"}], output_dir=tmp_path)

    assert report["errors"] == 1
    assert report["results"][0]["status"] == "error"
