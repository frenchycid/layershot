import json
from unittest.mock import patch, MagicMock
from core.ai_backend import AIBackend


def test_detect_claude():
    with patch("shutil.which", return_value="/usr/local/bin/claude"):
        backend = AIBackend()
        assert backend.backend_name == "claude"


def test_detect_ollama_fallback():
    def which_side_effect(name):
        if name == "claude":
            return None
        if name == "ollama":
            return "/usr/local/bin/ollama"
        return None

    with patch("shutil.which", side_effect=which_side_effect):
        backend = AIBackend()
        assert backend.backend_name == "ollama"


def test_detect_none_raises():
    with patch("shutil.which", return_value=None):
        try:
            AIBackend()
            assert False, "Should have raised"
        except RuntimeError as e:
            assert "No AI backend" in str(e)


def test_claude_complete():
    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = json.dumps({
        "type": "result",
        "result": "Hello from Claude"
    })

    with patch("shutil.which", return_value="/usr/local/bin/claude"):
        backend = AIBackend()

    with patch("subprocess.run", return_value=mock_result) as mock_run:
        result = backend.complete("Say hello")
        assert result == "Hello from Claude"
        cmd = mock_run.call_args[0][0]
        assert "claude" in cmd
        assert "-p" in cmd
        assert "--output-format" in cmd


def test_ollama_complete():
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"response": "Hello from Qwen"}

    def which_side_effect(name):
        return "/usr/local/bin/ollama" if name == "ollama" else None

    with patch("shutil.which", side_effect=which_side_effect):
        backend = AIBackend()

    with patch("httpx.post", return_value=mock_response):
        result = backend.complete("Say hello")
        assert result == "Hello from Qwen"


def test_claude_analyze_image():
    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = json.dumps({
        "type": "result",
        "result": '{"lighting": "soft"}'
    })

    with patch("shutil.which", return_value="/usr/local/bin/claude"):
        backend = AIBackend()

    with patch("subprocess.run", return_value=mock_result):
        result = backend.analyze_images(["/tmp/test.jpg"], "Analyze style")
        assert "lighting" in result
