"""AI Backend abstraction — auto-detects Claude Code CLI or Ollama."""

import json
import shutil
import subprocess
import base64
import logging
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
        if shutil.which("claude"):
            return "claude"
        if shutil.which("ollama"):
            return "ollama"
        raise RuntimeError(
            "No AI backend found. Install Claude Code (https://claude.ai/code) "
            "or Ollama (https://ollama.ai)."
        )

    def complete(self, prompt: str, system: Optional[str] = None) -> str:
        """Send a text prompt and get a response."""
        if self.backend_name == "claude":
            return self._claude_complete(prompt, system)
        return self._ollama_complete(prompt, system)

    def analyze_images(self, image_paths: List[str], prompt: str,
                       system: Optional[str] = None) -> str:
        """Analyze one or more images with a prompt."""
        if self.backend_name == "claude":
            return self._claude_vision(image_paths, prompt, system)
        return self._ollama_vision(image_paths, prompt, system)

    # ── Claude Code CLI ──

    def _claude_complete(self, prompt: str, system: Optional[str] = None) -> str:
        cmd = [
            "claude", "-p", prompt,
            "--output-format", "json",
            "--model", self.config.claude_model,
        ]
        if system:
            cmd.extend(["--system-prompt", system])
        return self._run_claude(cmd)

    def _claude_vision(self, image_paths: List[str], prompt: str,
                       system: Optional[str] = None) -> str:
        paths_list = "\n".join(f"- {p}" for p in image_paths)
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
        return self._run_claude(cmd)

    def _run_claude(self, cmd: list) -> str:
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=300
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
