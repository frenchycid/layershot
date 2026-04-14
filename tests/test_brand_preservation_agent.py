"""Tests for BrandPreservationAgent."""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch
from PIL import Image
import numpy as np

from agents.brand_preservation_agent import BrandPreservationAgent


class TestBrandPreservationAgent:
    """Test suite for BrandPreservationAgent."""

    def test_init_with_ai_backend(self):
        """Test initialization with AI backend."""
        mock_ai = Mock()
        agent = BrandPreservationAgent(ai_backend=mock_ai)
        assert agent.ai is mock_ai

    def test_init_without_ai_backend(self):
        """Test initialization creates default AIBackend."""
        agent = BrandPreservationAgent()
        assert agent.ai is not None

    def test_analyze_returns_score_and_details(self):
        """Test that analyze() returns dict with score and details."""
        mock_ai = Mock()
        mock_ai.analyze_image.return_value = '{"score": 85, "visible_elements": ["logo", "typography"], "issues": []}'

        agent = BrandPreservationAgent(ai_backend=mock_ai)

        # Create dummy image
        img_array = np.random.randint(0, 256, (100, 100, 3), dtype=np.uint8)
        img = Image.fromarray(img_array)

        result = agent.analyze(img, "luxury brand")

        assert isinstance(result, dict)
        assert "score" in result
        assert "visible_elements" in result

    def test_analyze_checks_logo_visibility(self):
        """Test that analyze() checks for logo visibility."""
        mock_ai = Mock()
        mock_ai.analyze_image.return_value = '{"score": 90, "visible_elements": ["logo"], "issues": []}'

        agent = BrandPreservationAgent(ai_backend=mock_ai)
        img = Image.new("RGB", (100, 100), color="white")

        result = agent.analyze(img, "brand")

        assert "logo" in result["visible_elements"]

    def test_analyze_checks_typography_visibility(self):
        """Test that analyze() checks for typography."""
        mock_ai = Mock()
        mock_ai.analyze_image.return_value = '{"score": 85, "visible_elements": ["typography"], "issues": []}'

        agent = BrandPreservationAgent(ai_backend=mock_ai)
        img = Image.new("RGB", (100, 100))

        result = agent.analyze(img, "brand")

        assert "typography" in result["visible_elements"]

    def test_analyze_checks_pattern_visibility(self):
        """Test that analyze() checks for brand patterns."""
        mock_ai = Mock()
        mock_ai.analyze_image.return_value = '{"score": 80, "visible_elements": ["pattern"], "issues": []}'

        agent = BrandPreservationAgent(ai_backend=mock_ai)
        img = Image.new("RGB", (100, 100))

        result = agent.analyze(img, "brand")

        assert "pattern" in result["visible_elements"]

    def test_score_ranges_0_to_100(self):
        """Test that preservation score is between 0 and 100."""
        mock_ai = Mock()
        mock_ai.analyze_image.return_value = '{"score": 72, "visible_elements": [], "issues": []}'

        agent = BrandPreservationAgent(ai_backend=mock_ai)
        img = Image.new("RGB", (100, 100))

        result = agent.analyze(img, "brand")

        assert 0 <= result["score"] <= 100

    def test_batch_analyze_multiple_images(self):
        """Test that batch_analyze processes multiple images."""
        mock_ai = Mock()
        mock_ai.analyze_image.return_value = '{"score": 75, "visible_elements": ["logo"], "issues": []}'

        agent = BrandPreservationAgent(ai_backend=mock_ai)
        images = [Image.new("RGB", (100, 100)) for _ in range(3)]

        results = agent.batch_analyze(images, "brand")

        assert len(results) == 3
        assert all("score" in r for r in results)

    def test_analyze_saves_to_file(self, tmp_path):
        """Test that analyze() saves result when save_to provided."""
        mock_ai = Mock()
        mock_ai.analyze_image.return_value = '{"score": 80, "visible_elements": [], "issues": []}'

        agent = BrandPreservationAgent(ai_backend=mock_ai)
        img = Image.new("RGB", (100, 100))
        output_file = tmp_path / "brand_analysis.json"

        agent.analyze(img, "brand", save_to=output_file)

        assert output_file.exists()

    def test_high_score_when_all_elements_visible(self):
        """Test that score is high when all brand elements are visible."""
        mock_ai = Mock()
        mock_ai.analyze_image.return_value = '{"score": 95, "visible_elements": ["logo", "typography", "pattern"], "issues": []}'

        agent = BrandPreservationAgent(ai_backend=mock_ai)
        img = Image.new("RGB", (100, 100))

        result = agent.analyze(img, "brand")

        assert result["score"] >= 90

    def test_low_score_when_elements_missing(self):
        """Test that score is low when brand elements are missing."""
        mock_ai = Mock()
        mock_ai.analyze_image.return_value = '{"score": 35, "visible_elements": [], "issues": ["logo not found"]}'

        agent = BrandPreservationAgent(ai_backend=mock_ai)
        img = Image.new("RGB", (100, 100))

        result = agent.analyze(img, "brand")

        assert result["score"] < 50

    def test_reports_specific_issues(self):
        """Test that analyze() reports specific issues."""
        mock_ai = Mock()
        mock_ai.analyze_image.return_value = '{"score": 50, "visible_elements": ["logo"], "issues": ["typography partially obscured", "pattern faded"]}'

        agent = BrandPreservationAgent(ai_backend=mock_ai)
        img = Image.new("RGB", (100, 100))

        result = agent.analyze(img, "brand")

        assert len(result["issues"]) > 0

    def test_analyze_handles_ai_error(self):
        """Test that analyze() handles AI backend errors."""
        mock_ai = Mock()
        mock_ai.analyze_image.side_effect = Exception("AI error")

        agent = BrandPreservationAgent(ai_backend=mock_ai)
        img = Image.new("RGB", (100, 100))

        with pytest.raises(Exception):
            agent.analyze(img, "brand")

    def test_batch_analyze_returns_averages(self):
        """Test that batch_analyze returns summary statistics."""
        mock_ai = Mock()
        mock_ai.analyze_image.return_value = '{"score": 80, "visible_elements": [], "issues": []}'

        agent = BrandPreservationAgent(ai_backend=mock_ai)
        images = [Image.new("RGB", (100, 100)) for _ in range(5)]

        results = agent.batch_analyze(images, "brand")
        summary = agent.summarize_batch(results)

        assert "average_score" in summary
        assert "passing_count" in summary

    def test_summarize_batch_threshold_passing(self):
        """Test batch summary identifies passing vs failing images."""
        mock_ai = Mock()
        mock_ai.analyze_image.side_effect = [
            '{"score": 85, "visible_elements": [], "issues": []}',
            '{"score": 92, "visible_elements": [], "issues": []}',
            '{"score": 45, "visible_elements": [], "issues": []}'
        ]

        agent = BrandPreservationAgent(ai_backend=mock_ai)
        images = [Image.new("RGB", (100, 100)) for _ in range(3)]

        results = agent.batch_analyze(images, "brand")
        summary = agent.summarize_batch(results, threshold=70)

        assert summary["passing_count"] == 2
        assert summary["failing_count"] == 1
