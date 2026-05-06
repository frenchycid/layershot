import json
from unittest.mock import patch, MagicMock
from pathlib import Path
from core.flux_client import FluxClient
from PIL import Image


def test_health_check_ok():
    client = FluxClient()
    health = client.health()
    assert health["status"] == "ok"
    assert health["backend"] == "native"


def test_health_check_down():
    client = FluxClient()
    with patch("builtins.__import__", side_effect=ImportError("torch not available")):
        health = client.health()
        assert health["status"] == "unreachable"


def test_generate_returns_path(tmp_path):
    # Create a minimal test image
    test_img = Image.new("RGB", (100, 100), color="red")

    client = FluxClient()

    # Mock the model loading and generation
    with patch.object(client, "_load_model"):
        with patch.object(client, "pipe") as mock_pipe:
            mock_pipe_instance = MagicMock()
            mock_pipe_instance.return_value.images = [test_img]
            client.pipe = mock_pipe_instance

            result = client.generate(
                prompt="test prompt",
                output_path=tmp_path / "test.png",
                seed=42,
            )

            assert result["seed"] == 42
            assert result["prompt"] == "test prompt"
            assert (tmp_path / "test.png").exists()


def test_generate_server_error():
    client = FluxClient()

    with patch.object(client, "_load_model", side_effect=Exception("Model loading failed")):
        try:
            client.generate(prompt="test", output_path=Path("/tmp/fail.png"))
            assert False, "Should have raised"
        except Exception:
            pass
