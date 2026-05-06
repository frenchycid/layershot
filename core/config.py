"""Global configuration for LayerShot."""

from pathlib import Path
from dataclasses import dataclass, field
from typing import List

PROJECT_ROOT = Path(__file__).resolve().parent.parent


@dataclass
class Config:
    flux_url: str = "http://localhost:8190"
    flux_backend: str = "local"  # "local" | "hf_api"
    hf_api_key: str = ""  # Set via HF_API_KEY env var
    ollama_url: str = "http://localhost:11434"
    # backend: "auto" (prefer claude) | "ollama" | "claude" | "mlx"
    backend: str = "mlx"
    claude_model: str = "sonnet"
    ollama_text_model: str = "qwen3.5"
    ollama_vision_model: str = "llava"
    # MLX (Apple Silicon local inference — no credits, no GPU issues)
    mlx_text_model: str = "mlx-community/Mistral-7B-Instruct-v0.3-4bit"
    mlx_vision_model: str = "mlx-community/Qwen2-VL-2B-Instruct-4bit"
    # Default moodboard category — studio packshot references (not interior)
    default_moodboard: str = "studio"
    views: List[str] = field(default_factory=lambda: ["wide", "closeup", "medium", "detail"])
    # Legacy: "interior" view is deprecated — replaced with "detail" for studio packshots
    variants_per_view: int = 3
    render_modes: List[str] = field(default_factory=lambda: ["isolated", "white_background", "enhanced"])
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
