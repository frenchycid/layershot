import json
from unittest.mock import patch, MagicMock
from core.ai_backend import AIBackend
from core.config import Config


def _claude_config():
    """Config that forces the Claude backend."""
    return Config(backend="claude")


def _ollama_config():
    """Config that forces the Ollama backend."""
    return Config(backend="ollama")


def _auto_config():
    """Config using auto-detection (prefer claude)."""
    return Config(backend="auto")


def test_detect_claude():
    """Explicit backend='claude' picks claude regardless of auto-detection order."""
    with patch("shutil.which", return_value="/usr/local/bin/claude"):
        backend = AIBackend(_claude_config())
        assert backend.backend_name == "claude"


def test_detect_ollama_explicit():
    """Explicit backend='ollama' picks ollama even when claude is installed."""
    with patch("shutil.which", return_value="/usr/local/bin/ollama"):
        backend = AIBackend(_ollama_config())
        assert backend.backend_name == "ollama"


def test_detect_ollama_fallback():
    """Auto mode falls back to ollama when claude is absent."""
    def which_side_effect(name):
        if name == "claude":
            return None
        if name == "ollama":
            return "/usr/local/bin/ollama"
        return None

    with patch("shutil.which", side_effect=which_side_effect):
        backend = AIBackend(_auto_config())
        assert backend.backend_name == "ollama"


def test_detect_none_raises():
    """Auto mode raises when no backend (claude, ollama, mlx) is found."""
    import builtins
    real_import = builtins.__import__

    def mock_import(name, *args, **kwargs):
        if name == "mlx_lm":
            raise ImportError("mocked: mlx_lm absent")
        return real_import(name, *args, **kwargs)

    with patch("shutil.which", return_value=None), patch("builtins.__import__", side_effect=mock_import):
        try:
            AIBackend(_auto_config())
            assert False, "Should have raised"
        except RuntimeError as e:
            assert "No AI backend" in str(e)


def test_detect_ollama_missing_raises():
    """Explicit backend='ollama' raises when ollama is not installed."""
    with patch("shutil.which", return_value=None):
        try:
            AIBackend(_ollama_config())
            assert False, "Should have raised"
        except RuntimeError as e:
            assert "Ollama not found" in str(e)


def test_claude_complete():
    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = json.dumps({
        "type": "result",
        "result": "Hello from Claude"
    })

    with patch("shutil.which", return_value="/usr/local/bin/claude"):
        backend = AIBackend(_claude_config())

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

    with patch("shutil.which", return_value="/usr/local/bin/ollama"):
        backend = AIBackend(_ollama_config())

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
        backend = AIBackend(_claude_config())

    with patch("subprocess.run", return_value=mock_result):
        result = backend.analyze_images(["/tmp/test.jpg"], "Analyze style")
        assert "lighting" in result
