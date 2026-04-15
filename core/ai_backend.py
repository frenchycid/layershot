"""AI Backend abstraction — auto-detects Claude Code CLI or Ollama."""

import json
import shutil
import subprocess
import base64
import logging
import tempfile
from pathlib import Path
from typing import List, Optional

import httpx

from core.config import Config

log = logging.getLogger("ai_backend")


class AIBackend:
    """Unified interface to Claude Code CLI or Ollama for text and vision tasks."""

    def __init__(self, config: Optional[Config] = None):
        self.config = config or Config()
        self.backend_name = self._detect()
        log.info(f"AI backend: {self.backend_name}")

    def _detect(self) -> str:
        forced = self.config.backend
        if forced == "mlx":
            try:
                import mlx_lm  # noqa: F401
                return "mlx"
            except ImportError:
                raise RuntimeError(
                    "mlx_lm not found. Install with: pip install mlx-lm mlx-vlm"
                )
        if forced == "ollama":
            if shutil.which("ollama"):
                return "ollama"
            raise RuntimeError("Ollama not found. Install it at https://ollama.ai")
        if forced == "claude":
            if shutil.which("claude"):
                return "claude"
            raise RuntimeError("Claude CLI not found. Install it at https://claude.ai/code")
        # auto: prefer claude, fall back to ollama, then mlx
        if shutil.which("claude"):
            return "claude"
        if shutil.which("ollama"):
            return "ollama"
        try:
            import mlx_lm  # noqa: F401
            return "mlx"
        except ImportError:
            pass
        raise RuntimeError(
            "No AI backend found. Options:\n"
            "  • MLX (Apple Silicon):  pip install mlx-lm mlx-vlm\n"
            "  • Ollama (local):       https://ollama.ai\n"
            "  • Claude Code (API):    https://claude.ai/code"
        )

    def complete(self, prompt: str, system: Optional[str] = None) -> str:
        """Send a text prompt and get a response."""
        if self.backend_name == "claude":
            return self._claude_complete(prompt, system)
        if self.backend_name == "mlx":
            return self._mlx_complete(prompt, system)
        return self._ollama_complete(prompt, system)

    def analyze_images(self, image_paths: List[str], prompt: str,
                       system: Optional[str] = None) -> str:
        """Analyze one or more images with a prompt."""
        if self.backend_name == "claude":
            return self._claude_vision(image_paths, prompt, system)
        if self.backend_name == "mlx":
            return self._mlx_vision(image_paths, prompt, system)
        return self._ollama_vision(image_paths, prompt, system)

    def analyze_image(self, prompt: str, image_b64: str,
                      system: Optional[str] = None) -> str:
        """Analyze a single image provided as base64 string."""
        if self.backend_name == "claude":
            return self._claude_vision_b64(prompt, image_b64, system)
        if self.backend_name == "mlx":
            return self._mlx_vision_b64(prompt, image_b64, system)
        return self._ollama_vision_b64(prompt, image_b64, system)

    # ── Claude Code CLI ──

    def _claude_complete(self, prompt: str, system: Optional[str] = None) -> str:
        cmd = [
            "claude", "-p", prompt,
            "--output-format", "json",
            "--model", self.config.claude_model,
        ]
        if system:
            cmd.extend(["--system-prompt", system])
        return self._run_claude(cmd, cwd=str(Path(__file__).parent.parent))

    def _claude_vision(self, image_paths: List[str], prompt: str,
                       system: Optional[str] = None) -> str:
        # Use absolute paths so Claude CLI works regardless of cwd
        abs_paths = [str(Path(p).resolve()) for p in image_paths]
        # Batch: max 20 images per call to stay within context limits
        if len(abs_paths) > 20:
            abs_paths = abs_paths[:20]
        paths_list = "\n".join(f"- {p}" for p in abs_paths)
        full_prompt = (
            f"Read and analyze these image files:\n{paths_list}\n\n{prompt}"
        )
        cmd = [
            "claude", "-p", full_prompt,
            "--output-format", "json",
            "--model", self.config.claude_model,
            "--allowedTools", "Read",
        ]
        if system:
            cmd.extend(["--system-prompt", system])
        # Run from project root so relative Read paths also work
        return self._run_claude(cmd, cwd=str(Path(__file__).parent.parent))

    def _claude_vision_b64(self, prompt: str, image_b64: str,
                           system: Optional[str] = None) -> str:
        """Analyze a single base64-encoded image via Claude."""
        # For Claude CLI, we write base64 to a temp file and read it
        import tempfile
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
            temp_path = f.name
            f.write(base64.b64decode(image_b64))

        try:
            full_prompt = f"Analyze this image:\n{prompt}"
            cmd = [
                "claude", "-p", full_prompt,
                "--output-format", "json",
                "--model", self.config.claude_model,
                "--allowedTools", "Read",
                temp_path,
            ]
            if system:
                cmd.extend(["--system-prompt", system])
            return self._run_claude(cmd, cwd=str(Path(__file__).parent.parent))
        finally:
            Path(temp_path).unlink()

    def _run_claude(self, cmd: list, cwd: Optional[str] = None) -> str:
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=300, cwd=cwd
        )
        if result.returncode != 0:
            raise RuntimeError(f"Claude CLI error: {result.stderr}")
        data = json.loads(result.stdout)
        if data.get("is_error"):
            raise RuntimeError(f"Claude returned error: {data.get('result', 'unknown')}")
        return data.get("result", "")

    # ── Ollama API ──

    def _ollama_complete(self, prompt: str, system: Optional[str] = None) -> str:
        payload = {
            "model": self.config.ollama_text_model,
            "prompt": prompt,
            "stream": False,
        }
        if system:
            payload["system"] = system
        resp = httpx.post(
            f"{self.config.ollama_url}/api/generate",
            json=payload,
            timeout=300.0,
        )
        resp.raise_for_status()
        return resp.json()["response"]

    def _ollama_vision(self, image_paths: List[str], prompt: str,
                       system: Optional[str] = None) -> str:
        images_b64 = []
        for p in image_paths:
            with open(p, "rb") as f:
                images_b64.append(base64.b64encode(f.read()).decode())
        payload = {
            "model": self.config.ollama_vision_model,
            "prompt": prompt,
            "images": images_b64,
            "stream": False,
        }
        if system:
            payload["system"] = system
        resp = httpx.post(
            f"{self.config.ollama_url}/api/generate",
            json=payload,
            timeout=300.0,
        )
        resp.raise_for_status()
        return resp.json()["response"]

    def _ollama_vision_b64(self, prompt: str, image_b64: str,
                           system: Optional[str] = None) -> str:
        """Analyze a single base64-encoded image via Ollama."""
        payload = {
            "model": self.config.ollama_vision_model,
            "prompt": prompt,
            "images": [image_b64],
            "stream": False,
        }
        if system:
            payload["system"] = system
        resp = httpx.post(
            f"{self.config.ollama_url}/api/generate",
            json=payload,
            timeout=300.0,
        )
        resp.raise_for_status()
        return resp.json()["response"]

    # ── MLX (Apple Silicon — local, free, no GPU driver issues) ──

    def _mlx_load_text(self):
        """Lazy-load the MLX text model (cached on self)."""
        if not hasattr(self, "_mlx_text_model"):
            from mlx_lm import load
            log.info(f"Loading MLX text model: {self.config.mlx_text_model}")
            self._mlx_text_model, self._mlx_text_tokenizer = load(
                self.config.mlx_text_model
            )

    def _mlx_load_vision(self):
        """Lazy-load the MLX vision model (cached on self)."""
        if not hasattr(self, "_mlx_vlm_model"):
            try:
                from mlx_vlm import load
                from mlx_vlm.utils import load_config
            except ImportError:
                raise RuntimeError(
                    "mlx_vlm not found. Install with: pip install mlx-vlm"
                )
            log.info(f"Loading MLX vision model: {self.config.mlx_vision_model}")
            self._mlx_vlm_model, self._mlx_vlm_processor = load(
                self.config.mlx_vision_model
            )
            self._mlx_vlm_config = load_config(self.config.mlx_vision_model)

    def _mlx_complete(self, prompt: str, system: Optional[str] = None) -> str:
        from mlx_lm import generate
        self._mlx_load_text()
        full_prompt = f"{system}\n\n{prompt}" if system else prompt
        return generate(
            self._mlx_text_model,
            self._mlx_text_tokenizer,
            prompt=full_prompt,
            max_tokens=4096,
            verbose=False,
        )

    def _mlx_vision(self, image_paths: List[str], prompt: str,
                    system: Optional[str] = None) -> str:
        """Analyze images with MLX vision model — processes up to 5 images sequentially."""
        from mlx_vlm import generate
        from mlx_vlm.prompt_utils import apply_chat_template
        self._mlx_load_vision()
        full_prompt = f"{system}\n\n{prompt}" if system else prompt
        # MLX-VLM processes one image at a time; concatenate results for batches
        results = []
        for path in image_paths[:5]:
            formatted = apply_chat_template(
                self._mlx_vlm_processor,
                self._mlx_vlm_config,
                full_prompt,
                num_images=1,
            )
            result = generate(
                self._mlx_vlm_model,
                self._mlx_vlm_processor,
                path,
                formatted,
                max_tokens=2048,
                verbose=False,
            )
            results.append(result)
        return "\n---\n".join(results) if len(results) > 1 else results[0]

    def _mlx_vision_b64(self, prompt: str, image_b64: str,
                        system: Optional[str] = None) -> str:
        """Analyze a base64 image with MLX vision — writes to temp file first."""
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
            temp_path = f.name
            f.write(base64.b64decode(image_b64))
        try:
            return self._mlx_vision([temp_path], prompt, system)
        finally:
            Path(temp_path).unlink()
