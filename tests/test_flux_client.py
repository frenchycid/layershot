import json
from unittest.mock import patch, MagicMock
from pathlib import Path
from core.flux_client import FluxClient


def test_health_check_ok():
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"status": "ok", "model": "flux2-klein-9b"}

    client = FluxClient()
    with patch("httpx.get", return_value=mock_resp):
        health = client.health()
        assert health["status"] == "ok"


def test_health_check_down():
    client = FluxClient()
    with patch("httpx.get", side_effect=Exception("Connection refused")):
        health = client.health()
        assert health["status"] == "unreachable"


def test_generate_returns_path(tmp_path):
    fake_b64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAAC0lEQVQI12NgAAIABQAB"
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "image": f"data:image/png;base64,{fake_b64}",
        "seed": 42,
        "time_s": 3.5,
        "prompt": "test prompt",
    }

    client = FluxClient()
    with patch("httpx.post", return_value=mock_resp):
        result = client.generate(
            prompt="test prompt",
            output_path=tmp_path / "test.png",
        )
        assert result["seed"] == 42
        assert result["time_s"] == 3.5
        assert (tmp_path / "test.png").exists()


def test_generate_server_error():
    mock_resp = MagicMock()
    mock_resp.status_code = 503
    mock_resp.raise_for_status.side_effect = Exception("503 Service Unavailable")

    client = FluxClient()
    with patch("httpx.post", return_value=mock_resp):
        try:
            client.generate(prompt="test", output_path=Path("/tmp/fail.png"))
            assert False, "Should have raised"
        except Exception:
            pass
