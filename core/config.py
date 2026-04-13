"""Global configuration for LayerShot."""

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
