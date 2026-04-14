"""Tests for PromptVariantEngine."""

import json
import pytest
from pathlib import Path
from unittest.mock import Mock, MagicMock

from agents.prompt_variant_engine import PromptVariantEngine


class TestPromptVariantEngine:
    """Test suite for PromptVariantEngine."""

    def test_init_with_ai_backend(self):
        """Test initialization with AI backend."""
        mock_ai = Mock()
        engine = PromptVariantEngine(ai_backend=mock_ai)
        assert engine.ai is mock_ai

    def test_init_without_ai_backend(self):
        """Test initialization creates default AIBackend."""
        engine = PromptVariantEngine()
        assert engine.ai is not None

    def test_generate_returns_three_variants(self):
        """Test that generate() returns dict with 3 variants."""
        mock_ai = Mock()
        mock_ai.complete.return_value = json.dumps({
            "isolated": {
                "base_prompt": "product isolated INSERT YOUR PRODUCT HERE on transparent",
                "negative_prompt": "background, context"
            },
            "white_background": {
                "base_prompt": "product on white background INSERT YOUR PRODUCT HERE studio lighting",
                "negative_prompt": "shadows, outdoor"
            },
            "enhanced": {
                "base_prompt": "product premium INSERT YOUR PRODUCT HERE enhanced materials",
                "negative_prompt": "artifacts, low quality"
            }
        })

        engine = PromptVariantEngine(ai_backend=mock_ai)
        style_analysis = {"colors": ["white", "gold"], "lighting": "soft"}

        result = engine.generate(style_analysis)

        assert isinstance(result, dict)
        assert "isolated" in result
        assert "white_background" in result
        assert "enhanced" in result

    def test_generate_preserves_product_placeholder(self):
        """Test that product placeholder is preserved in all variants."""
        mock_ai = Mock()
        mock_ai.complete.return_value = json.dumps({
            "isolated": {"base_prompt": "INSERT YOUR PRODUCT HERE isolated"},
            "white_background": {"base_prompt": "INSERT YOUR PRODUCT HERE white"},
            "enhanced": {"base_prompt": "INSERT YOUR PRODUCT HERE premium"}
        })

        engine = PromptVariantEngine(ai_backend=mock_ai)
        result = engine.generate({})

        assert "INSERT YOUR PRODUCT HERE" in result["isolated"]["base_prompt"]
        assert "INSERT YOUR PRODUCT HERE" in result["white_background"]["base_prompt"]
        assert "INSERT YOUR PRODUCT HERE" in result["enhanced"]["base_prompt"]

    def test_generate_calls_ai_backend(self):
        """Test that generate() calls ai_backend.complete()."""
        mock_ai = Mock()
        mock_ai.complete.return_value = json.dumps({
            "isolated": {"base_prompt": "test"},
            "white_background": {"base_prompt": "test"},
            "enhanced": {"base_prompt": "test"}
        })

        engine = PromptVariantEngine(ai_backend=mock_ai)
        style_analysis = {"test": "data"}

        engine.generate(style_analysis)

        mock_ai.complete.assert_called_once()

    def test_generate_saves_to_file(self, tmp_path):
        """Test that generate() saves result to file when save_to provided."""
        mock_ai = Mock()
        mock_ai.complete.return_value = json.dumps({
            "isolated": {"base_prompt": "test"},
            "white_background": {"base_prompt": "test"},
            "enhanced": {"base_prompt": "test"}
        })

        engine = PromptVariantEngine(ai_backend=mock_ai)
        output_file = tmp_path / "variants.json"

        engine.generate({}, save_to=output_file)

        assert output_file.exists()
        data = json.loads(output_file.read_text())
        assert "isolated" in data

    def test_build_isolated_prompt(self):
        """Test building prompt for isolated render mode."""
        mock_ai = Mock()
        mock_ai.complete.return_value = json.dumps({
            "isolated": {"base_prompt": "INSERT YOUR PRODUCT HERE on transparent background"},
            "white_background": {"base_prompt": "INSERT YOUR PRODUCT HERE on white"},
            "enhanced": {"base_prompt": "INSERT YOUR PRODUCT HERE premium"}
        })

        engine = PromptVariantEngine(ai_backend=mock_ai)
        variants = engine.generate({})

        prompt = engine.build_prompt(variants, "luxury watch", "isolated")

        assert "luxury watch" in prompt
        assert "transparent" in prompt

    def test_build_white_background_prompt(self):
        """Test building prompt for white background mode."""
        mock_ai = Mock()
        mock_ai.complete.return_value = json.dumps({
            "isolated": {"base_prompt": "INSERT YOUR PRODUCT HERE"},
            "white_background": {"base_prompt": "INSERT YOUR PRODUCT HERE studio lighting white background"},
            "enhanced": {"base_prompt": "INSERT YOUR PRODUCT HERE"}
        })

        engine = PromptVariantEngine(ai_backend=mock_ai)
        variants = engine.generate({})

        prompt = engine.build_prompt(variants, "perfume bottle", "white_background")

        assert "perfume bottle" in prompt
        assert "white" in prompt or "studio" in prompt

    def test_build_enhanced_prompt(self):
        """Test building prompt for enhanced materials mode."""
        mock_ai = Mock()
        mock_ai.complete.return_value = json.dumps({
            "isolated": {"base_prompt": "INSERT YOUR PRODUCT HERE"},
            "white_background": {"base_prompt": "INSERT YOUR PRODUCT HERE"},
            "enhanced": {"base_prompt": "INSERT YOUR PRODUCT HERE premium materials detailed textures"}
        })

        engine = PromptVariantEngine(ai_backend=mock_ai)
        variants = engine.generate({})

        prompt = engine.build_prompt(variants, "leather bag", "enhanced")

        assert "leather bag" in prompt
        assert "premium" in prompt or "material" in prompt

    def test_generate_with_invalid_json_raises(self):
        """Test that invalid JSON from AI backend raises error."""
        mock_ai = Mock()
        mock_ai.complete.return_value = "not valid json"

        engine = PromptVariantEngine(ai_backend=mock_ai)

        with pytest.raises(json.JSONDecodeError):
            engine.generate({})

    def test_generate_requires_all_three_modes(self):
        """Test that response must contain all three render modes."""
        mock_ai = Mock()
        mock_ai.complete.return_value = json.dumps({
            "isolated": {"base_prompt": "test"}
        })

        engine = PromptVariantEngine(ai_backend=mock_ai)

        with pytest.raises(KeyError):
            engine.generate({})

    def test_variants_include_negative_prompts(self):
        """Test that each variant includes negative_prompt."""
        mock_ai = Mock()
        mock_ai.complete.return_value = json.dumps({
            "isolated": {
                "base_prompt": "test",
                "negative_prompt": "background, shadow"
            },
            "white_background": {
                "base_prompt": "test",
                "negative_prompt": "outdoor, color"
            },
            "enhanced": {
                "base_prompt": "test",
                "negative_prompt": "artifact, blur"
            }
        })

        engine = PromptVariantEngine(ai_backend=mock_ai)
        result = engine.generate({})

        assert "negative_prompt" in result["isolated"]
        assert "negative_prompt" in result["white_background"]
        assert "negative_prompt" in result["enhanced"]

    def test_isolated_mode_emphasizes_transparency(self):
        """Test isolated mode prompt mentions transparent/png/alpha."""
        mock_ai = Mock()
        mock_ai.complete.return_value = json.dumps({
            "isolated": {"base_prompt": "product on transparent background", "negative_prompt": "bg"},
            "white_background": {"base_prompt": "product", "negative_prompt": ""},
            "enhanced": {"base_prompt": "product", "negative_prompt": ""}
        })

        engine = PromptVariantEngine(ai_backend=mock_ai)
        result = engine.generate({})

        iso_prompt = result["isolated"]["base_prompt"].lower()
        assert "transparent" in iso_prompt or "png" in iso_prompt or "alpha" in iso_prompt

    def test_white_background_mode_emphasizes_studio(self):
        """Test white_background mode emphasizes studio/professional."""
        mock_ai = Mock()
        mock_ai.complete.return_value = json.dumps({
            "isolated": {"base_prompt": "product", "negative_prompt": ""},
            "white_background": {"base_prompt": "product studio lighting white", "negative_prompt": ""},
            "enhanced": {"base_prompt": "product", "negative_prompt": ""}
        })

        engine = PromptVariantEngine(ai_backend=mock_ai)
        result = engine.generate({})

        white_prompt = result["white_background"]["base_prompt"].lower()
        assert "white" in white_prompt or "studio" in white_prompt or "professional" in white_prompt

    def test_enhanced_mode_emphasizes_materials(self):
        """Test enhanced mode emphasizes textures and materials."""
        mock_ai = Mock()
        mock_ai.complete.return_value = json.dumps({
            "isolated": {"base_prompt": "product", "negative_prompt": ""},
            "white_background": {"base_prompt": "product", "negative_prompt": ""},
            "enhanced": {"base_prompt": "product premium materials detailed", "negative_prompt": ""}
        })

        engine = PromptVariantEngine(ai_backend=mock_ai)
        result = engine.generate({})

        enhanced_prompt = result["enhanced"]["base_prompt"].lower()
        assert "material" in enhanced_prompt or "premium" in enhanced_prompt or "texture" in enhanced_prompt

    def test_generate_passes_system_prompt(self):
        """Test that generate() passes appropriate system prompt to AI."""
        mock_ai = Mock()
        mock_ai.complete.return_value = json.dumps({
            "isolated": {"base_prompt": "test", "negative_prompt": ""},
            "white_background": {"base_prompt": "test", "negative_prompt": ""},
            "enhanced": {"base_prompt": "test", "negative_prompt": ""}
        })

        engine = PromptVariantEngine(ai_backend=mock_ai)
        engine.generate({})

        call_kwargs = mock_ai.complete.call_args[1]
        assert "system" in call_kwargs

    def test_build_prompt_raises_for_unknown_mode(self):
        """Test that build_prompt raises for unknown render mode."""
        mock_ai = Mock()
        mock_ai.complete.return_value = json.dumps({
            "isolated": {"base_prompt": "test"},
            "white_background": {"base_prompt": "test"},
            "enhanced": {"base_prompt": "test"}
        })

        engine = PromptVariantEngine(ai_backend=mock_ai)
        variants = engine.generate({})

        with pytest.raises(KeyError):
            engine.build_prompt(variants, "product", "unknown_mode")

    def test_generate_handles_ai_backend_error(self):
        """Test that generate() handles AI backend errors gracefully."""
        mock_ai = Mock()
        mock_ai.complete.side_effect = Exception("AI backend error")

        engine = PromptVariantEngine(ai_backend=mock_ai)

        with pytest.raises(Exception):
            engine.generate({})

    def test_multiple_calls_return_consistent_structure(self):
        """Test that multiple calls return consistent JSON structure."""
        mock_ai = Mock()
        mock_ai.complete.return_value = json.dumps({
            "isolated": {"base_prompt": "test", "negative_prompt": ""},
            "white_background": {"base_prompt": "test", "negative_prompt": ""},
            "enhanced": {"base_prompt": "test", "negative_prompt": ""}
        })

        engine = PromptVariantEngine(ai_backend=mock_ai)

        result1 = engine.generate({})
        result2 = engine.generate({})

        assert set(result1.keys()) == set(result2.keys())

    def test_product_placeholder_default_value(self):
        """Test default product placeholder is INSERT YOUR PRODUCT HERE."""
        engine = PromptVariantEngine()
        assert engine.product_placeholder == "INSERT YOUR PRODUCT HERE"
