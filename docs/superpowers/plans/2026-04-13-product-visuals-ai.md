# Product Visuals AI — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** CLI tool qui génère des visuels produit photoréalistes via 5 agents IA coordonnés — 100% local, zéro clé API, auto-détection Claude Code / Ollama.

**Architecture:** 5 agents Python (Style Analyst, Prompt Engineer, Pipeline Orchestrator, Quality Review, Creative Director) alimentés par Claude Code CLI (`claude -p --bare`) avec fallback Ollama (Qwen 3.5 texte + LLaVA vision). Génération d'images via serveur Flux2 Klein 9B existant sur port 8190 (mflux/MLX natif Apple Silicon).

**Tech Stack:** Python 3.9+, httpx, Pillow, pytest, Claude Code CLI, Ollama API, Flux2 Klein 9B

---

## File Structure

```
~/projects/product-visuals-ai/
├── core/
│   ├── __init__.py            # Package init
│   ├── config.py              # Chemins, URLs, préférences modèle
│   ├── ai_backend.py          # Abstraction Claude Code / Ollama (auto-detect)
│   └── flux_client.py         # Client HTTP vers Flux server :8190
├── agents/
│   ├── __init__.py            # Package init, exports
│   ├── style_analyst.py       # Agent 1 — Analyse style moodboard
│   ├── prompt_engineer.py     # Agent 2 — Génération prompt maître
│   ├── pipeline.py            # Agent 3 — Orchestration batch Flux
│   ├── quality_review.py      # Agent 4 — Scoring images générées
│   └── creative_director.py   # Agent 5 — Coordination pipeline complet
├── tests/
│   ├── __init__.py
│   ├── test_config.py
│   ├── test_ai_backend.py
│   ├── test_flux_client.py
│   ├── test_style_analyst.py
│   ├── test_prompt_engineer.py
│   ├── test_pipeline.py
│   ├── test_quality_review.py
│   └── test_creative_director.py
├── data/
│   ├── moodboards/            # Images de référence (par projet)
│   ├── outputs/               # Images générées
│   └── prompts/               # Historique prompts maîtres (JSON)
├── main.py                    # CLI principal (argparse)
└── requirements.txt
```

## Data Contracts

**Style Analysis JSON** (output du Style Analyst) :
```json
{
  "lighting": {
    "type": "natural",
    "direction": "side",
    "quality": "soft golden hour"
  },
  "color_palette": {
    "dominant": ["amber", "terracotta", "warm brown"],
    "accents": ["cream", "olive"],
    "temperature": "warm"
  },
  "grain": {
    "type": "film",
    "intensity": "medium",
    "film_stock": "Kodak Portra 400"
  },
  "lens": {
    "focal_length": "35mm",
    "aperture": "f/2.8",
    "depth_of_field": "shallow"
  },
  "atmosphere": ["atmospheric bloom", "lifted blacks", "soft vignette"],
  "style_summary": "Retro 70s product photography with warm amber tones..."
}
```

**Master Prompt JSON** (output du Prompt Engineer) :
```json
{
  "base_prompt": "Product photography, 35mm film, Kodak Portra 400...",
  "product_placeholder": "INSERT YOUR PRODUCT HERE",
  "view_variants": {
    "wide": "wide establishing shot, full scene, environmental context",
    "closeup": "macro detail shot, shallow depth of field, texture focus",
    "medium": "medium shot, product centered, balanced composition",
    "interior": "interior lifestyle setting, natural light, lived-in feel"
  },
  "negative_prompt": "text, watermark, low quality, blurry, deformed",
  "style_analysis_ref": "path/to/analysis.json"
}
```

**Quality Score JSON** (output du Quality Review) :
```json
{
  "image_path": "data/outputs/candle_amber_wide_001.png",
  "scores": {
    "style_coherence": 8.5,
    "realism": 7.0,
    "technical_quality": 9.0,
    "product_showcase": 8.0,
    "composite": 8.1
  },
  "flags": [],
  "recommendation": "keep"
}
```

---

### Task 1: Project Scaffolding

**Files:**
- Create: `requirements.txt`
- Create: `core/__init__.py`
- Create: `agents/__init__.py`
- Create: `tests/__init__.py`
- Create: `data/moodboards/.gitkeep`
- Create: `data/outputs/.gitkeep`
- Create: `data/prompts/.gitkeep`

- [ ] **Step 1: Create directory structure**

```bash
cd ~/projects/product-visuals-ai
mkdir -p core agents tests data/moodboards data/outputs data/prompts
```

- [ ] **Step 2: Create requirements.txt**

```
httpx>=0.27
Pillow>=10.0
pytest>=8.0
```

- [ ] **Step 3: Create package init files**

`core/__init__.py`:
```python
"""Core modules: AI backend, Flux client, config."""
```

`agents/__init__.py`:
```python
"""AI agents for product visual generation pipeline."""
```

`tests/__init__.py`:
```python
```

- [ ] **Step 4: Create .gitkeep files for empty data dirs**

```bash
touch data/moodboards/.gitkeep data/outputs/.gitkeep data/prompts/.gitkeep
```

- [ ] **Step 5: Create virtual environment and install dependencies**

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

- [ ] **Step 6: Initialize git repo and commit**

```bash
git init
echo ".venv/" > .gitignore
echo "data/outputs/*.png" >> .gitignore
echo "data/moodboards/*.png" >> .gitignore
echo "data/moodboards/*.jpg" >> .gitignore
echo "__pycache__/" >> .gitignore
echo "*.pyc" >> .gitignore
git add .
git commit -m "chore: init project scaffolding"
```

---

### Task 2: Configuration Module

**Files:**
- Create: `core/config.py`
- Create: `tests/test_config.py`

- [ ] **Step 1: Write the failing test**

`tests/test_config.py`:
```python
from core.config import Config


def test_default_flux_url():
    cfg = Config()
    assert cfg.flux_url == "http://localhost:8190"


def test_default_data_paths():
    cfg = Config()
    assert cfg.moodboards_dir.name == "moodboards"
    assert cfg.outputs_dir.name == "outputs"
    assert cfg.prompts_dir.name == "prompts"


def test_default_views():
    cfg = Config()
    assert set(cfg.views) == {"wide", "closeup", "medium", "interior"}


def test_default_variants_per_view():
    cfg = Config()
    assert cfg.variants_per_view == 3


def test_custom_flux_url():
    cfg = Config(flux_url="http://myhost:9999")
    assert cfg.flux_url == "http://myhost:9999"
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd ~/projects/product-visuals-ai
source .venv/bin/activate
python -m pytest tests/test_config.py -v
```

Expected: FAIL — `ModuleNotFoundError: No module named 'core.config'`

- [ ] **Step 3: Write implementation**

`core/config.py`:
```python
"""Global configuration for Product Visuals AI."""

from pathlib import Path
from dataclasses import dataclass, field
from typing import List

PROJECT_ROOT = Path(__file__).resolve().parent.parent


@dataclass
class Config:
    flux_url: str = "http://localhost:8190"
    ollama_url: str = "http://localhost:11434"
    claude_model: str = "sonnet"
    ollama_text_model: str = "qwen3.5"
    ollama_vision_model: str = "llava"
    views: List[str] = field(default_factory=lambda: ["wide", "closeup", "medium", "interior"])
    variants_per_view: int = 3
    image_width: int = 1024
    image_height: int = 1024
    flux_steps: int = 15
    data_dir: Path = field(default_factory=lambda: PROJECT_ROOT / "data")

    @property
    def moodboards_dir(self) -> Path:
        return self.data_dir / "moodboards"

    @property
    def outputs_dir(self) -> Path:
        return self.data_dir / "outputs"

    @property
    def prompts_dir(self) -> Path:
        return self.data_dir / "prompts"

    def ensure_dirs(self):
        """Create data directories if they don't exist."""
        self.moodboards_dir.mkdir(parents=True, exist_ok=True)
        self.outputs_dir.mkdir(parents=True, exist_ok=True)
        self.prompts_dir.mkdir(parents=True, exist_ok=True)
```

- [ ] **Step 4: Run test to verify it passes**

```bash
python -m pytest tests/test_config.py -v
```

Expected: 5 passed

- [ ] **Step 5: Commit**

```bash
git add core/config.py tests/test_config.py
git commit -m "feat: add configuration module with paths and defaults"
```

---

### Task 3: AI Backend Abstraction

**Files:**
- Create: `core/ai_backend.py`
- Create: `tests/test_ai_backend.py`

- [ ] **Step 1: Write the failing tests**

`tests/test_ai_backend.py`:
```python
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
        assert "--bare" in cmd


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
```

- [ ] **Step 2: Run test to verify it fails**

```bash
python -m pytest tests/test_ai_backend.py -v
```

Expected: FAIL — `ModuleNotFoundError: No module named 'core.ai_backend'`

- [ ] **Step 3: Write implementation**

`core/ai_backend.py`:
```python
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
            "--bare",
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
            "--bare",
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
```

- [ ] **Step 4: Run test to verify it passes**

```bash
python -m pytest tests/test_ai_backend.py -v
```

Expected: 6 passed

- [ ] **Step 5: Commit**

```bash
git add core/ai_backend.py tests/test_ai_backend.py
git commit -m "feat: add AI backend with Claude Code / Ollama auto-detection"
```

---

### Task 4: Flux Client

**Files:**
- Create: `core/flux_client.py`
- Create: `tests/test_flux_client.py`

- [ ] **Step 1: Write the failing tests**

`tests/test_flux_client.py`:
```python
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
```

- [ ] **Step 2: Run test to verify it fails**

```bash
python -m pytest tests/test_flux_client.py -v
```

Expected: FAIL — `ModuleNotFoundError: No module named 'core.flux_client'`

- [ ] **Step 3: Write implementation**

`core/flux_client.py`:
```python
"""HTTP client for the local Flux2 image generation server."""

import base64
import logging
from pathlib import Path
from typing import Optional

import httpx

from core.config import Config

log = logging.getLogger("flux_client")


class FluxClient:
    """Client for the Flux2 Klein 9B server on localhost:8190."""

    def __init__(self, config: Optional[Config] = None):
        self.config = config or Config()
        self.base_url = self.config.flux_url

    def health(self) -> dict:
        """Check if Flux server is running."""
        try:
            resp = httpx.get(f"{self.base_url}/health", timeout=5.0)
            return resp.json()
        except Exception as e:
            log.warning(f"Flux server unreachable: {e}")
            return {"status": "unreachable", "error": str(e)}

    def generate(
        self,
        prompt: str,
        output_path: Path,
        width: Optional[int] = None,
        height: Optional[int] = None,
        steps: Optional[int] = None,
        seed: Optional[int] = None,
    ) -> dict:
        """Generate an image and save it to output_path.

        Returns dict with seed, time_s, prompt.
        """
        payload = {
            "prompt": prompt,
            "width": width or self.config.image_width,
            "height": height or self.config.image_height,
            "steps": steps or self.config.flux_steps,
        }
        if seed is not None:
            payload["seed"] = seed

        log.info(f"Generating: {output_path.name}")
        resp = httpx.post(
            f"{self.base_url}/generate",
            json=payload,
            timeout=600.0,
        )
        resp.raise_for_status()
        data = resp.json()

        # Decode base64 image and save
        b64_data = data["image"].split(",", 1)[1]
        image_bytes = base64.b64decode(b64_data)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(image_bytes)
        log.info(f"Saved: {output_path} (seed={data['seed']}, {data['time_s']}s)")

        return {
            "seed": data["seed"],
            "time_s": data["time_s"],
            "prompt": data["prompt"],
            "path": str(output_path),
        }
```

- [ ] **Step 4: Run test to verify it passes**

```bash
python -m pytest tests/test_flux_client.py -v
```

Expected: 4 passed

- [ ] **Step 5: Commit**

```bash
git add core/flux_client.py tests/test_flux_client.py
git commit -m "feat: add Flux2 HTTP client with health check and generation"
```

---

### Task 5: Style Analyst Agent

**Files:**
- Create: `agents/style_analyst.py`
- Create: `tests/test_style_analyst.py`

- [ ] **Step 1: Write the failing tests**

`tests/test_style_analyst.py`:
```python
import json
from unittest.mock import MagicMock, patch
from pathlib import Path
from agents.style_analyst import StyleAnalyst


MOCK_ANALYSIS = json.dumps({
    "lighting": {"type": "natural", "direction": "side", "quality": "soft golden hour"},
    "color_palette": {"dominant": ["amber", "brown"], "accents": ["cream"], "temperature": "warm"},
    "grain": {"type": "film", "intensity": "medium", "film_stock": "Kodak Portra 400"},
    "lens": {"focal_length": "35mm", "aperture": "f/2.8", "depth_of_field": "shallow"},
    "atmosphere": ["atmospheric bloom", "lifted blacks"],
    "style_summary": "Retro 70s warm film look"
})


def test_analyze_returns_structured_json():
    mock_backend = MagicMock()
    mock_backend.analyze_images.return_value = MOCK_ANALYSIS

    analyst = StyleAnalyst(ai_backend=mock_backend)
    result = analyst.analyze(["/tmp/ref1.jpg", "/tmp/ref2.jpg"])

    assert "lighting" in result
    assert "color_palette" in result
    assert "grain" in result
    assert "lens" in result
    assert "atmosphere" in result
    assert result["color_palette"]["temperature"] == "warm"


def test_analyze_calls_backend_with_images():
    mock_backend = MagicMock()
    mock_backend.analyze_images.return_value = MOCK_ANALYSIS

    analyst = StyleAnalyst(ai_backend=mock_backend)
    analyst.analyze(["/tmp/ref1.jpg", "/tmp/ref2.jpg"])

    mock_backend.analyze_images.assert_called_once()
    call_args = mock_backend.analyze_images.call_args
    assert call_args[0][0] == ["/tmp/ref1.jpg", "/tmp/ref2.jpg"]


def test_analyze_saves_to_file(tmp_path):
    mock_backend = MagicMock()
    mock_backend.analyze_images.return_value = MOCK_ANALYSIS

    analyst = StyleAnalyst(ai_backend=mock_backend)
    output_file = tmp_path / "analysis.json"
    result = analyst.analyze(["/tmp/ref1.jpg"], save_to=output_file)

    assert output_file.exists()
    saved = json.loads(output_file.read_text())
    assert saved["lighting"]["type"] == "natural"


def test_collect_images_from_directory(tmp_path):
    (tmp_path / "img1.jpg").write_bytes(b"fake")
    (tmp_path / "img2.png").write_bytes(b"fake")
    (tmp_path / "notes.txt").write_bytes(b"ignore")

    analyst = StyleAnalyst(ai_backend=MagicMock())
    images = analyst.collect_images(tmp_path)

    assert len(images) == 2
    extensions = {p.suffix for p in images}
    assert extensions == {".jpg", ".png"}
```

- [ ] **Step 2: Run test to verify it fails**

```bash
python -m pytest tests/test_style_analyst.py -v
```

Expected: FAIL — `ModuleNotFoundError: No module named 'agents.style_analyst'`

- [ ] **Step 3: Write implementation**

`agents/style_analyst.py`:
```python
"""Style Analyst Agent — Extracts photographic style from moodboard images."""

import json
import logging
from pathlib import Path
from typing import List, Optional

from core.ai_backend import AIBackend

log = logging.getLogger("style_analyst")

SYSTEM_PROMPT = """You are a photographic style analyst. You analyze reference images 
to extract ONLY the visual style — never describe the content or subjects in the scenes.

You must respond with valid JSON matching this exact structure:
{
  "lighting": {"type": "...", "direction": "...", "quality": "..."},
  "color_palette": {"dominant": ["..."], "accents": ["..."], "temperature": "warm|cool|neutral"},
  "grain": {"type": "film|digital|none", "intensity": "low|medium|high", "film_stock": "..."},
  "lens": {"focal_length": "...", "aperture": "...", "depth_of_field": "shallow|medium|deep"},
  "atmosphere": ["list of atmospheric effects"],
  "style_summary": "One paragraph summarizing the overall photographic style"
}

Use precise photographic vocabulary: atmospheric bloom, lifted blacks, film grain, 
crushed shadows, highlight rolloff, color cast, bokeh, chromatic aberration, etc.
Do NOT use generic terms like "beautiful" or "nice photo"."""

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".tiff", ".bmp"}


class StyleAnalyst:
    """Analyzes moodboard images to extract a structured style profile."""

    def __init__(self, ai_backend: Optional[AIBackend] = None):
        self.ai = ai_backend or AIBackend()

    def collect_images(self, directory: Path) -> List[Path]:
        """Collect all image files from a directory."""
        images = sorted(
            p for p in directory.iterdir()
            if p.suffix.lower() in IMAGE_EXTENSIONS
        )
        log.info(f"Found {len(images)} images in {directory}")
        return images

    def analyze(
        self,
        image_paths: List[str],
        save_to: Optional[Path] = None,
    ) -> dict:
        """Analyze images and return structured style JSON."""
        log.info(f"Analyzing {len(image_paths)} reference images...")

        prompt = (
            f"Analyze the photographic style of these {len(image_paths)} reference images. "
            "Focus ONLY on style attributes: lighting, color palette, grain, lens characteristics, "
            "and atmospheric effects. Do NOT describe the content or subjects. "
            "Respond with the JSON structure specified in your instructions."
        )

        raw = self.ai.analyze_images(
            [str(p) for p in image_paths],
            prompt,
            system=SYSTEM_PROMPT,
        )

        result = self._parse_json(raw)
        log.info(f"Style analysis complete: {result.get('style_summary', '')[:80]}")

        if save_to:
            save_to.parent.mkdir(parents=True, exist_ok=True)
            save_to.write_text(json.dumps(result, indent=2, ensure_ascii=False))
            log.info(f"Analysis saved to {save_to}")

        return result

    def _parse_json(self, raw: str) -> dict:
        """Extract JSON from AI response, handling markdown code blocks."""
        text = raw.strip()
        if "```json" in text:
            text = text.split("```json", 1)[1].split("```", 1)[0]
        elif "```" in text:
            text = text.split("```", 1)[1].split("```", 1)[0]
        return json.loads(text.strip())
```

- [ ] **Step 4: Run test to verify it passes**

```bash
python -m pytest tests/test_style_analyst.py -v
```

Expected: 4 passed

- [ ] **Step 5: Commit**

```bash
git add agents/style_analyst.py tests/test_style_analyst.py
git commit -m "feat: add Style Analyst agent with moodboard analysis"
```

---

### Task 6: Prompt Engineer Agent

**Files:**
- Create: `agents/prompt_engineer.py`
- Create: `tests/test_prompt_engineer.py`

- [ ] **Step 1: Write the failing tests**

`tests/test_prompt_engineer.py`:
```python
import json
from unittest.mock import MagicMock
from pathlib import Path
from agents.prompt_engineer import PromptEngineer


MOCK_ANALYSIS = {
    "lighting": {"type": "natural", "direction": "side", "quality": "soft golden hour"},
    "color_palette": {"dominant": ["amber", "brown"], "accents": ["cream"], "temperature": "warm"},
    "grain": {"type": "film", "intensity": "medium", "film_stock": "Kodak Portra 400"},
    "lens": {"focal_length": "35mm", "aperture": "f/2.8", "depth_of_field": "shallow"},
    "atmosphere": ["atmospheric bloom", "lifted blacks"],
    "style_summary": "Retro 70s warm film look"
}

MOCK_MASTER_PROMPT = json.dumps({
    "base_prompt": "Product photography, 35mm, Kodak Portra 400, warm amber tones, atmospheric bloom, lifted blacks, INSERT YOUR PRODUCT HERE",
    "product_placeholder": "INSERT YOUR PRODUCT HERE",
    "view_variants": {
        "wide": "wide establishing shot, environmental context",
        "closeup": "macro detail, shallow DOF, texture focus",
        "medium": "medium shot, product centered",
        "interior": "interior lifestyle setting, natural light"
    },
    "negative_prompt": "text, watermark, low quality, blurry, deformed"
})


def test_generate_returns_master_prompt():
    mock_backend = MagicMock()
    mock_backend.complete.return_value = MOCK_MASTER_PROMPT

    engineer = PromptEngineer(ai_backend=mock_backend)
    result = engineer.generate(MOCK_ANALYSIS)

    assert "base_prompt" in result
    assert "INSERT YOUR PRODUCT HERE" in result["base_prompt"]
    assert "view_variants" in result
    assert "wide" in result["view_variants"]


def test_build_product_prompt():
    mock_backend = MagicMock()
    mock_backend.complete.return_value = MOCK_MASTER_PROMPT

    engineer = PromptEngineer(ai_backend=mock_backend)
    master = engineer.generate(MOCK_ANALYSIS)
    prompt = engineer.build_prompt(master, product="amber glass candle", view="closeup")

    assert "amber glass candle" in prompt
    assert "INSERT YOUR PRODUCT HERE" not in prompt


def test_generate_saves_to_file(tmp_path):
    mock_backend = MagicMock()
    mock_backend.complete.return_value = MOCK_MASTER_PROMPT

    engineer = PromptEngineer(ai_backend=mock_backend)
    output_file = tmp_path / "master.json"
    result = engineer.generate(MOCK_ANALYSIS, save_to=output_file)

    assert output_file.exists()
    saved = json.loads(output_file.read_text())
    assert "base_prompt" in saved
```

- [ ] **Step 2: Run test to verify it fails**

```bash
python -m pytest tests/test_prompt_engineer.py -v
```

Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Write implementation**

`agents/prompt_engineer.py`:
```python
"""Prompt Engineer Agent — Generates reusable master prompts from style analysis."""

import json
import logging
from pathlib import Path
from typing import Optional

from core.ai_backend import AIBackend

log = logging.getLogger("prompt_engineer")

SYSTEM_PROMPT = """You are a prompt engineer specialized in AI image generation.
Given a photographic style analysis, create a structured master prompt for generating
product photography that matches the analyzed style.

You must respond with valid JSON matching this exact structure:
{
  "base_prompt": "A detailed prompt including all style attributes with INSERT YOUR PRODUCT HERE as placeholder",
  "product_placeholder": "INSERT YOUR PRODUCT HERE",
  "view_variants": {
    "wide": "additional terms for wide establishing shots",
    "closeup": "additional terms for macro/detail shots",
    "medium": "additional terms for medium product shots",
    "interior": "additional terms for interior lifestyle shots"
  },
  "negative_prompt": "comma-separated list of things to avoid"
}

Rules:
- Use precise photographic terms: atmospheric bloom, lifted blacks, film grain, 35mm lens, etc.
- NEVER use generic terms like "beautiful", "stunning", "nice"
- The base_prompt must contain INSERT YOUR PRODUCT HERE exactly once
- Each view_variant adds shot-specific terms, not full prompts
- The negative_prompt prevents common AI artifacts"""


class PromptEngineer:
    """Transforms style analysis into structured, reusable generation prompts."""

    def __init__(self, ai_backend: Optional[AIBackend] = None):
        self.ai = ai_backend or AIBackend()

    def generate(
        self,
        style_analysis: dict,
        save_to: Optional[Path] = None,
    ) -> dict:
        """Generate a master prompt from a style analysis."""
        log.info("Generating master prompt from style analysis...")

        prompt = (
            "Create a master prompt for AI image generation based on this style analysis:\n\n"
            f"{json.dumps(style_analysis, indent=2)}\n\n"
            "The prompt must capture ALL style attributes (lighting, colors, grain, lens, atmosphere) "
            "and include INSERT YOUR PRODUCT HERE as a placeholder for any product. "
            "Respond with the JSON structure specified in your instructions."
        )

        raw = self.ai.complete(prompt, system=SYSTEM_PROMPT)
        result = self._parse_json(raw)
        log.info(f"Master prompt generated ({len(result['base_prompt'])} chars)")

        if save_to:
            save_to.parent.mkdir(parents=True, exist_ok=True)
            save_to.write_text(json.dumps(result, indent=2, ensure_ascii=False))
            log.info(f"Master prompt saved to {save_to}")

        return result

    def build_prompt(self, master: dict, product: str, view: str) -> str:
        """Build a final generation prompt for a specific product and view."""
        base = master["base_prompt"].replace(
            master["product_placeholder"], product
        )
        view_suffix = master.get("view_variants", {}).get(view, "")
        if view_suffix:
            return f"{base}, {view_suffix}"
        return base

    def _parse_json(self, raw: str) -> dict:
        """Extract JSON from AI response."""
        text = raw.strip()
        if "```json" in text:
            text = text.split("```json", 1)[1].split("```", 1)[0]
        elif "```" in text:
            text = text.split("```", 1)[1].split("```", 1)[0]
        return json.loads(text.strip())
```

- [ ] **Step 4: Run test to verify it passes**

```bash
python -m pytest tests/test_prompt_engineer.py -v
```

Expected: 3 passed

- [ ] **Step 5: Commit**

```bash
git add agents/prompt_engineer.py tests/test_prompt_engineer.py
git commit -m "feat: add Prompt Engineer agent with master prompt generation"
```

---

### Task 7: Pipeline Orchestrator Agent

**Files:**
- Create: `agents/pipeline.py`
- Create: `tests/test_pipeline.py`

- [ ] **Step 1: Write the failing tests**

`tests/test_pipeline.py`:
```python
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

    assert len(jobs) == 4  # 1 product × 2 views × 2 variants
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
```

- [ ] **Step 2: Run test to verify it fails**

```bash
python -m pytest tests/test_pipeline.py -v
```

Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Write implementation**

`agents/pipeline.py`:
```python
"""Pipeline Orchestrator Agent — Batch image generation via Flux."""

import re
import json
import logging
import time
from pathlib import Path
from typing import List, Optional

from core.config import Config
from core.flux_client import FluxClient

log = logging.getLogger("pipeline")


class PipelineOrchestrator:
    """Generates product images in batch across views and variants."""

    def __init__(
        self,
        flux_client: Optional[FluxClient] = None,
        config: Optional[Config] = None,
    ):
        self.config = config or Config()
        self.flux = flux_client or FluxClient(self.config)

    def build_jobs(self, master: dict, products: List[dict]) -> List[dict]:
        """Build the list of generation jobs.

        Each product dict has keys: name, color.
        Returns list of job dicts with prompt, filename, metadata.
        """
        jobs = []
        placeholder = master["product_placeholder"]
        views = self.config.views
        variants = self.config.variants_per_view

        for product in products:
            name = product["name"]
            color = product["color"]
            product_desc = f"{color} {name}"

            for view in views:
                base = master["base_prompt"].replace(placeholder, product_desc)
                view_suffix = master.get("view_variants", {}).get(view, "")
                prompt = f"{base}, {view_suffix}" if view_suffix else base

                for v in range(1, variants + 1):
                    jobs.append({
                        "prompt": prompt,
                        "filename": self._make_filename(name, color, view, v),
                        "product_name": name,
                        "color": color,
                        "view": view,
                        "variant": v,
                    })

        log.info(f"Built {len(jobs)} generation jobs")
        return jobs

    def run(
        self,
        master: dict,
        products: List[dict],
        output_dir: Optional[Path] = None,
    ) -> dict:
        """Execute all generation jobs and return a report."""
        output_dir = output_dir or self.config.outputs_dir
        output_dir.mkdir(parents=True, exist_ok=True)
        jobs = self.build_jobs(master, products)

        report = {
            "total": len(jobs),
            "completed": 0,
            "errors": 0,
            "results": [],
            "start_time": time.time(),
        }

        for i, job in enumerate(jobs, 1):
            log.info(f"[{i}/{len(jobs)}] {job['filename']}")
            output_path = output_dir / job["filename"]

            try:
                result = self.flux.generate(
                    prompt=job["prompt"],
                    output_path=output_path,
                )
                report["completed"] += 1
                report["results"].append({
                    "filename": job["filename"],
                    "status": "ok",
                    **result,
                    **{k: job[k] for k in ("product_name", "color", "view", "variant")},
                })
            except Exception as e:
                log.error(f"Failed: {job['filename']} — {e}")
                report["errors"] += 1
                report["results"].append({
                    "filename": job["filename"],
                    "status": "error",
                    "error": str(e),
                    **{k: job[k] for k in ("product_name", "color", "view", "variant")},
                })

        report["elapsed_s"] = round(time.time() - report["start_time"], 1)
        del report["start_time"]
        log.info(
            f"Pipeline complete: {report['completed']}/{report['total']} OK, "
            f"{report['errors']} errors, {report['elapsed_s']}s total"
        )
        return report

    def _make_filename(self, name: str, color: str, view: str, variant: int) -> str:
        """Generate filename: [product]_[color]_[view]_[variant].png"""
        slug = lambda s: re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")
        return f"{slug(name)}_{slug(color)}_{view}_{variant:03d}.png"
```

- [ ] **Step 4: Run test to verify it passes**

```bash
python -m pytest tests/test_pipeline.py -v
```

Expected: 4 passed

- [ ] **Step 5: Commit**

```bash
git add agents/pipeline.py tests/test_pipeline.py
git commit -m "feat: add Pipeline Orchestrator with batch Flux generation"
```

---

### Task 8: Quality Review Agent

**Files:**
- Create: `agents/quality_review.py`
- Create: `tests/test_quality_review.py`

- [ ] **Step 1: Write the failing tests**

`tests/test_quality_review.py`:
```python
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
```

- [ ] **Step 2: Run test to verify it fails**

```bash
python -m pytest tests/test_quality_review.py -v
```

Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Write implementation**

`agents/quality_review.py`:
```python
"""Quality Review Agent — Scores generated images on style, realism, and quality."""

import json
import logging
from pathlib import Path
from typing import Optional, List

from core.ai_backend import AIBackend

log = logging.getLogger("quality_review")

SYSTEM_PROMPT = """You are a product photography quality reviewer. You evaluate AI-generated
product images against a reference style.

Score each image on these 4 criteria (0-10 scale):
- style_coherence: How well does it match the reference style?
- realism: How photorealistic does it look?
- technical_quality: Resolution, artifacts, aberrations, composition?
- product_showcase: Is the product clearly visible and well-presented?

Respond with valid JSON:
{
  "style_coherence": 8.5,
  "realism": 7.0,
  "technical_quality": 9.0,
  "product_showcase": 8.0
}

Be strict. A score of 7+ means genuinely good. 5-7 is acceptable. Below 5 means regenerate."""

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}

# Weights for composite score
WEIGHTS = {
    "style_coherence": 0.30,
    "realism": 0.25,
    "technical_quality": 0.20,
    "product_showcase": 0.25,
}


class QualityReview:
    """Reviews generated images and scores them on quality criteria."""

    def __init__(self, ai_backend: Optional[AIBackend] = None):
        self.ai = ai_backend or AIBackend()

    def review_image(self, image_path: str, style_ref: dict) -> dict:
        """Review a single image against the style reference."""
        prompt = (
            "Evaluate this generated product image against the reference style.\n\n"
            f"Reference style: {json.dumps(style_ref)}\n\n"
            "Score it on the 4 criteria in your instructions. Respond with JSON only."
        )

        raw = self.ai.analyze_images([image_path], prompt, system=SYSTEM_PROMPT)
        scores = self._parse_json(raw)

        composite = sum(
            scores[k] * WEIGHTS[k] for k in WEIGHTS if k in scores
        )
        composite = round(composite, 1)

        return {
            "image_path": image_path,
            "scores": {**scores, "composite": composite},
            "recommendation": self._recommend(composite),
        }

    def review_batch(
        self,
        images_dir: Path,
        style_ref: dict,
        save_to: Optional[Path] = None,
    ) -> dict:
        """Review all images in a directory."""
        images = sorted(
            p for p in images_dir.iterdir()
            if p.suffix.lower() in IMAGE_EXTENSIONS
        )
        log.info(f"Reviewing {len(images)} images...")

        reviews = []
        for img in images:
            log.info(f"Reviewing: {img.name}")
            review = self.review_image(str(img), style_ref)
            reviews.append(review)

        reviews.sort(key=lambda r: r["scores"]["composite"], reverse=True)
        best = reviews[0] if reviews else None

        report = {
            "total": len(reviews),
            "reviews": reviews,
            "best": {"path": best["image_path"], "score": best["scores"]["composite"]} if best else None,
            "keep": [r for r in reviews if r["recommendation"] == "keep"],
            "regenerate": [r for r in reviews if r["recommendation"] == "regenerate"],
        }

        if save_to:
            save_to.parent.mkdir(parents=True, exist_ok=True)
            save_to.write_text(json.dumps(report, indent=2, ensure_ascii=False))
            log.info(f"Review report saved to {save_to}")

        return report

    def _recommend(self, composite: float) -> str:
        if composite >= 7.0:
            return "keep"
        if composite >= 5.0:
            return "maybe"
        return "regenerate"

    def _parse_json(self, raw: str) -> dict:
        text = raw.strip()
        if "```json" in text:
            text = text.split("```json", 1)[1].split("```", 1)[0]
        elif "```" in text:
            text = text.split("```", 1)[1].split("```", 1)[0]
        return json.loads(text.strip())
```

- [ ] **Step 4: Run test to verify it passes**

```bash
python -m pytest tests/test_quality_review.py -v
```

Expected: 4 passed

- [ ] **Step 5: Commit**

```bash
git add agents/quality_review.py tests/test_quality_review.py
git commit -m "feat: add Quality Review agent with image scoring"
```

---

### Task 9: Creative Director Agent

**Files:**
- Create: `agents/creative_director.py`
- Create: `tests/test_creative_director.py`

- [ ] **Step 1: Write the failing tests**

`tests/test_creative_director.py`:
```python
import json
from unittest.mock import MagicMock, patch
from pathlib import Path
from agents.creative_director import CreativeDirector


def _make_mocks():
    analyst = MagicMock()
    analyst.collect_images.return_value = [Path("/tmp/ref1.jpg")]
    analyst.analyze.return_value = {
        "lighting": {"type": "natural"},
        "color_palette": {"temperature": "warm"},
        "style_summary": "warm retro style",
    }

    engineer = MagicMock()
    engineer.generate.return_value = {
        "base_prompt": "photo of INSERT YOUR PRODUCT HERE, warm",
        "product_placeholder": "INSERT YOUR PRODUCT HERE",
        "view_variants": {"wide": "wide shot"},
        "negative_prompt": "blurry",
    }

    pipeline = MagicMock()
    pipeline.run.return_value = {
        "total": 1, "completed": 1, "errors": 0,
        "results": [{"filename": "candle_amber_wide_001.png", "status": "ok"}],
    }

    reviewer = MagicMock()
    reviewer.review_batch.return_value = {
        "total": 1,
        "reviews": [{"image_path": "/tmp/out/x.png", "scores": {"composite": 8.0}, "recommendation": "keep"}],
        "best": {"path": "/tmp/out/x.png", "score": 8.0},
        "keep": [{}], "regenerate": [],
    }

    return analyst, engineer, pipeline, reviewer


def test_full_pipeline(tmp_path):
    analyst, engineer, pipeline, reviewer = _make_mocks()
    director = CreativeDirector(
        style_analyst=analyst,
        prompt_engineer=engineer,
        pipeline=pipeline,
        quality_review=reviewer,
    )

    products = [{"name": "candle", "color": "amber"}]
    report = director.run(
        moodboard_dir=tmp_path / "mood",
        products=products,
        output_dir=tmp_path / "out",
    )

    analyst.collect_images.assert_called_once()
    analyst.analyze.assert_called_once()
    engineer.generate.assert_called_once()
    pipeline.run.assert_called_once()
    reviewer.review_batch.assert_called_once()

    assert report["status"] == "complete"
    assert report["generation"]["completed"] == 1


def test_saves_session_history(tmp_path):
    analyst, engineer, pipeline, reviewer = _make_mocks()
    director = CreativeDirector(
        style_analyst=analyst,
        prompt_engineer=engineer,
        pipeline=pipeline,
        quality_review=reviewer,
    )

    products = [{"name": "candle", "color": "amber"}]
    (tmp_path / "mood").mkdir()
    report = director.run(
        moodboard_dir=tmp_path / "mood",
        products=products,
        output_dir=tmp_path / "out",
        session_name="test_session",
    )

    history_file = tmp_path / "out" / "test_session_report.json"
    assert history_file.exists()


def test_pipeline_aborts_if_no_images(tmp_path):
    analyst, engineer, pipeline, reviewer = _make_mocks()
    analyst.collect_images.return_value = []

    director = CreativeDirector(
        style_analyst=analyst,
        prompt_engineer=engineer,
        pipeline=pipeline,
        quality_review=reviewer,
    )

    report = director.run(
        moodboard_dir=tmp_path,
        products=[{"name": "x", "color": "y"}],
    )

    assert report["status"] == "error"
    assert "No images" in report["error"]
```

- [ ] **Step 2: Run test to verify it fails**

```bash
python -m pytest tests/test_creative_director.py -v
```

Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Write implementation**

`agents/creative_director.py`:
```python
"""Creative Director Agent — Coordinates the full product visuals pipeline."""

import json
import logging
import time
from pathlib import Path
from typing import List, Optional

from core.config import Config
from core.ai_backend import AIBackend
from core.flux_client import FluxClient
from agents.style_analyst import StyleAnalyst
from agents.prompt_engineer import PromptEngineer
from agents.pipeline import PipelineOrchestrator
from agents.quality_review import QualityReview

log = logging.getLogger("creative_director")


class CreativeDirector:
    """Orchestrates the full pipeline: analyze → prompt → generate → review."""

    def __init__(
        self,
        style_analyst: Optional[StyleAnalyst] = None,
        prompt_engineer: Optional[PromptEngineer] = None,
        pipeline: Optional[PipelineOrchestrator] = None,
        quality_review: Optional[QualityReview] = None,
        config: Optional[Config] = None,
    ):
        self.config = config or Config()
        self.analyst = style_analyst or StyleAnalyst()
        self.engineer = prompt_engineer or PromptEngineer()
        self.pipeline = pipeline or PipelineOrchestrator()
        self.reviewer = quality_review or QualityReview()

    def run(
        self,
        moodboard_dir: Path,
        products: List[dict],
        output_dir: Optional[Path] = None,
        session_name: Optional[str] = None,
    ) -> dict:
        """Run the full pipeline end-to-end."""
        output_dir = output_dir or self.config.outputs_dir
        output_dir.mkdir(parents=True, exist_ok=True)
        session_name = session_name or f"session_{int(time.time())}"

        log.info(f"=== Creative Director — Session: {session_name} ===")
        start = time.time()

        # Step 1: Collect moodboard images
        log.info("Step 1/4: Collecting moodboard images...")
        images = self.analyst.collect_images(moodboard_dir)
        if not images:
            return {"status": "error", "error": "No images found in moodboard directory"}

        # Step 2: Analyze style
        log.info("Step 2/4: Analyzing photographic style...")
        analysis_path = output_dir / f"{session_name}_analysis.json"
        style = self.analyst.analyze(
            [str(p) for p in images],
            save_to=analysis_path,
        )

        # Step 3: Generate master prompt
        log.info("Step 3/4: Generating master prompt...")
        prompt_path = output_dir / f"{session_name}_prompt.json"
        master = self.engineer.generate(style, save_to=prompt_path)

        # Step 4: Generate images
        log.info("Step 4/4: Generating product images...")
        gen_report = self.pipeline.run(master, products, output_dir=output_dir)

        # Step 5: Review quality
        log.info("Step 5/5: Reviewing image quality...")
        review_report = self.reviewer.review_batch(output_dir, style)

        # Build final report
        elapsed = round(time.time() - start, 1)
        report = {
            "status": "complete",
            "session": session_name,
            "elapsed_s": elapsed,
            "moodboard_images": len(images),
            "style_analysis": style,
            "master_prompt": master["base_prompt"][:200],
            "generation": gen_report,
            "review": {
                "total_reviewed": review_report["total"],
                "kept": len(review_report["keep"]),
                "to_regenerate": len(review_report["regenerate"]),
                "best": review_report["best"],
            },
        }

        # Save session report
        report_path = output_dir / f"{session_name}_report.json"
        report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False))
        log.info(f"Session report saved to {report_path}")
        log.info(
            f"=== Done in {elapsed}s — "
            f"{gen_report['completed']} images, "
            f"{len(review_report['keep'])} kept ==="
        )

        return report
```

- [ ] **Step 4: Run test to verify it passes**

```bash
python -m pytest tests/test_creative_director.py -v
```

Expected: 3 passed

- [ ] **Step 5: Commit**

```bash
git add agents/creative_director.py tests/test_creative_director.py
git commit -m "feat: add Creative Director agent for full pipeline coordination"
```

---

### Task 10: Main CLI

**Files:**
- Create: `main.py`
- Create: `tests/test_main.py`

- [ ] **Step 1: Write the failing tests**

`tests/test_main.py`:
```python
import sys
from unittest.mock import patch, MagicMock
from pathlib import Path


def test_cli_analyze_command(tmp_path):
    sys.argv = ["main.py", "analyze", "--moodboard", str(tmp_path)]

    with patch("agents.style_analyst.StyleAnalyst") as MockAnalyst:
        instance = MockAnalyst.return_value
        instance.collect_images.return_value = [tmp_path / "img.jpg"]
        instance.analyze.return_value = {"style_summary": "test"}

        from main import main
        # Should not raise
        with patch("sys.exit"):
            main()


def test_cli_generate_command(tmp_path):
    prompt_file = tmp_path / "prompt.json"
    prompt_file.write_text('{"base_prompt":"test INSERT YOUR PRODUCT HERE","product_placeholder":"INSERT YOUR PRODUCT HERE","view_variants":{},"negative_prompt":""}')

    sys.argv = [
        "main.py", "generate",
        "--prompt", str(prompt_file),
        "--products", "candle:amber",
    ]

    with patch("agents.pipeline.PipelineOrchestrator") as MockPipeline:
        instance = MockPipeline.return_value
        instance.run.return_value = {"total": 1, "completed": 1, "errors": 0, "results": []}

        from main import main
        with patch("sys.exit"):
            main()


def test_parse_products():
    from main import parse_products
    result = parse_products(["candle:amber", "vase:cream white"])
    assert result == [
        {"name": "candle", "color": "amber"},
        {"name": "vase", "color": "cream white"},
    ]
```

- [ ] **Step 2: Run test to verify it fails**

```bash
python -m pytest tests/test_main.py -v
```

Expected: FAIL — `ModuleNotFoundError: No module named 'main'`

- [ ] **Step 3: Write implementation**

`main.py`:
```python
#!/usr/bin/env python3
"""Product Visuals AI — CLI for photoreal product image generation."""

import argparse
import json
import logging
import sys
from pathlib import Path

from core.config import Config
from core.ai_backend import AIBackend
from core.flux_client import FluxClient
from agents.style_analyst import StyleAnalyst
from agents.prompt_engineer import PromptEngineer
from agents.pipeline import PipelineOrchestrator
from agents.quality_review import QualityReview
from agents.creative_director import CreativeDirector


def parse_products(product_args: list) -> list:
    """Parse 'name:color' product arguments into dicts."""
    products = []
    for p in product_args:
        if ":" in p:
            name, color = p.split(":", 1)
        else:
            name, color = p, "default"
        products.append({"name": name.strip(), "color": color.strip()})
    return products


def cmd_analyze(args, config):
    """Analyze moodboard style."""
    ai = AIBackend(config)
    analyst = StyleAnalyst(ai_backend=ai)

    moodboard = Path(args.moodboard)
    images = analyst.collect_images(moodboard)
    if not images:
        print(f"No images found in {moodboard}")
        sys.exit(1)

    print(f"Found {len(images)} reference images")
    output = Path(args.output) if args.output else config.prompts_dir / "analysis.json"
    result = analyst.analyze([str(p) for p in images], save_to=output)
    print(f"\nStyle summary: {result.get('style_summary', 'N/A')}")
    print(f"Saved to: {output}")


def cmd_prompt(args, config):
    """Generate master prompt from analysis."""
    ai = AIBackend(config)
    engineer = PromptEngineer(ai_backend=ai)

    analysis = json.loads(Path(args.analysis).read_text())
    output = Path(args.output) if args.output else config.prompts_dir / "master_prompt.json"
    result = engineer.generate(analysis, save_to=output)
    print(f"Master prompt generated ({len(result['base_prompt'])} chars)")
    print(f"Views: {', '.join(result.get('view_variants', {}).keys())}")
    print(f"Saved to: {output}")


def cmd_generate(args, config):
    """Generate images from master prompt."""
    flux = FluxClient(config)
    health = flux.health()
    if health["status"] != "ok":
        print(f"Flux server not available: {health}")
        sys.exit(1)

    master = json.loads(Path(args.prompt).read_text())
    products = parse_products(args.products)
    output_dir = Path(args.output) if args.output else config.outputs_dir

    orch = PipelineOrchestrator(flux_client=flux, config=config)
    print(f"Generating images for {len(products)} products...")
    report = orch.run(master, products, output_dir=output_dir)

    print(f"\nDone: {report['completed']}/{report['total']} images")
    if report["errors"]:
        print(f"Errors: {report['errors']}")


def cmd_review(args, config):
    """Review generated images."""
    ai = AIBackend(config)
    reviewer = QualityReview(ai_backend=ai)

    images_dir = Path(args.images)
    style_ref = {}
    if args.analysis:
        style_ref = json.loads(Path(args.analysis).read_text())

    output = Path(args.output) if args.output else images_dir / "review_report.json"
    report = reviewer.review_batch(images_dir, style_ref, save_to=output)

    print(f"Reviewed: {report['total']} images")
    print(f"Keep: {len(report['keep'])} | Regenerate: {len(report['regenerate'])}")
    if report["best"]:
        print(f"Best: {report['best']['path']} (score: {report['best']['score']})")


def cmd_run(args, config):
    """Run full pipeline end-to-end."""
    ai = AIBackend(config)
    flux = FluxClient(config)
    health = flux.health()
    if health["status"] != "ok":
        print(f"Flux server not available: {health}")
        sys.exit(1)

    director = CreativeDirector(
        style_analyst=StyleAnalyst(ai_backend=ai),
        prompt_engineer=PromptEngineer(ai_backend=ai),
        pipeline=PipelineOrchestrator(flux_client=flux, config=config),
        quality_review=QualityReview(ai_backend=ai),
        config=config,
    )

    products = parse_products(args.products)
    output_dir = Path(args.output) if args.output else config.outputs_dir

    print(f"Full pipeline: {args.moodboard} → {len(products)} products")
    report = director.run(
        moodboard_dir=Path(args.moodboard),
        products=products,
        output_dir=output_dir,
        session_name=args.session,
    )

    print(f"\n{'='*50}")
    print(f"Status: {report['status']}")
    if report["status"] == "complete":
        print(f"Images: {report['generation']['completed']}/{report['generation']['total']}")
        print(f"Kept: {report['review']['kept']}")
        print(f"Time: {report['elapsed_s']}s")
        if report["review"]["best"]:
            print(f"Best: {report['review']['best']['path']}")
    else:
        print(f"Error: {report.get('error', 'unknown')}")


def main():
    parser = argparse.ArgumentParser(
        prog="product-visuals-ai",
        description="Generate photoreal product visuals with AI",
    )
    sub = parser.add_subparsers(dest="command")

    # analyze
    p_analyze = sub.add_parser("analyze", help="Analyze moodboard style")
    p_analyze.add_argument("--moodboard", "-m", required=True, help="Moodboard directory")
    p_analyze.add_argument("--output", "-o", help="Output JSON path")

    # prompt
    p_prompt = sub.add_parser("prompt", help="Generate master prompt")
    p_prompt.add_argument("--analysis", "-a", required=True, help="Style analysis JSON")
    p_prompt.add_argument("--output", "-o", help="Output JSON path")

    # generate
    p_gen = sub.add_parser("generate", help="Generate product images")
    p_gen.add_argument("--prompt", "-p", required=True, help="Master prompt JSON")
    p_gen.add_argument("--products", nargs="+", required=True, help="Products as name:color")
    p_gen.add_argument("--output", "-o", help="Output directory")

    # review
    p_review = sub.add_parser("review", help="Review generated images")
    p_review.add_argument("--images", "-i", required=True, help="Images directory")
    p_review.add_argument("--analysis", "-a", help="Style analysis JSON for reference")
    p_review.add_argument("--output", "-o", help="Output report path")

    # run (full pipeline)
    p_run = sub.add_parser("run", help="Run full pipeline end-to-end")
    p_run.add_argument("--moodboard", "-m", required=True, help="Moodboard directory")
    p_run.add_argument("--products", nargs="+", required=True, help="Products as name:color")
    p_run.add_argument("--output", "-o", help="Output directory")
    p_run.add_argument("--session", "-s", default=None, help="Session name")

    args = parser.parse_args()
    config = Config()
    config.ensure_dirs()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(name)s] %(message)s",
        datefmt="%H:%M:%S",
    )

    commands = {
        "analyze": cmd_analyze,
        "prompt": cmd_prompt,
        "generate": cmd_generate,
        "review": cmd_review,
        "run": cmd_run,
    }

    if args.command in commands:
        commands[args.command](args, config)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run test to verify it passes**

```bash
python -m pytest tests/test_main.py -v
```

Expected: 3 passed

- [ ] **Step 5: Run full test suite**

```bash
python -m pytest tests/ -v
```

Expected: All 31 tests passed

- [ ] **Step 6: Commit**

```bash
git add main.py tests/test_main.py
git commit -m "feat: add CLI with analyze, prompt, generate, review, and run commands"
```

---

## CLI Usage Summary

```bash
# Step by step
python main.py analyze --moodboard data/moodboards/retro70s/
python main.py prompt --analysis data/prompts/analysis.json
python main.py generate --prompt data/prompts/master_prompt.json --products "candle:amber" "vase:cream"
python main.py review --images data/outputs/ --analysis data/prompts/analysis.json

# Full pipeline (one command)
python main.py run --moodboard data/moodboards/retro70s/ --products "candle:amber" "vase:cream" --session retro70s
```
