import json
from unittest.mock import MagicMock
from pathlib import Path
from agents.quality_review import QualityReview


MOCK_SCORE = json.dumps({
    "style_coherence": 8.5,
    "realism": 7.0,
    "technical_quality": 9.0,
    "product_showcase": 8.0
})


def test_review_single_image():
    mock_backend = MagicMock()
    mock_backend.analyze_images.return_value = MOCK_SCORE

    reviewer = QualityReview(ai_backend=mock_backend)
    style_ref = {"style_summary": "retro 70s warm tones"}
    result = reviewer.review_image("/tmp/test.png", style_ref)

    assert result["scores"]["style_coherence"] == 8.5
    assert result["scores"]["composite"] > 0
    assert result["recommendation"] in ("keep", "maybe", "regenerate")


def test_composite_score_is_weighted_average():
    mock_backend = MagicMock()
    mock_backend.analyze_images.return_value = json.dumps({
        "style_coherence": 10.0,
        "realism": 10.0,
        "technical_quality": 10.0,
        "product_showcase": 10.0
    })

    reviewer = QualityReview(ai_backend=mock_backend)
    result = reviewer.review_image("/tmp/test.png", {})

    assert result["scores"]["composite"] == 10.0


def test_review_batch(tmp_path):
    mock_backend = MagicMock()
    mock_backend.analyze_images.return_value = MOCK_SCORE

    (tmp_path / "img1.png").write_bytes(b"fake")
    (tmp_path / "img2.png").write_bytes(b"fake")

    reviewer = QualityReview(ai_backend=mock_backend)
    report = reviewer.review_batch(tmp_path, style_ref={})

    assert len(report["reviews"]) == 2
    assert "best" in report
    assert report["best"]["path"] is not None


def test_recommendation_thresholds():
    reviewer = QualityReview(ai_backend=MagicMock())
    assert reviewer._recommend(8.0) == "keep"
    assert reviewer._recommend(5.5) == "maybe"
    assert reviewer._recommend(3.0) == "regenerate"
