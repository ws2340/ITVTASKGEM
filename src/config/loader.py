"""Load config.yaml and environment variables."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv


@dataclass
class GeminiConfig:
    model: str
    temperature: float
    top_p: float
    max_output_tokens: int
    response_logprobs: bool
    logprobs: int


@dataclass
class PipelineConfig:
    file_upload_poll_interval: float
    file_upload_max_wait: float
    cleanup_uploaded_files: bool


@dataclass
class AppConfig:
    gemini: GeminiConfig
    pipeline: PipelineConfig
    input_dir: Path
    output_dir: Path
    system_prompt: str
    config_path: Path


def _project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def load_config(
    config_path: Path | None = None,
    input_dir: Path | None = None,
    output_dir: Path | None = None,
) -> AppConfig:
    """Load YAML config, .env, and apply CLI path overrides."""
    root = _project_root()
    load_dotenv(root / ".env")

    cfg_file = config_path or (root / "config.yaml")
    print(f"[config] Loading config from: {cfg_file}")
    with cfg_file.open(encoding="utf-8") as f:
        raw: dict[str, Any] = yaml.safe_load(f) or {}

    g = raw.get("gemini", {})
    p = raw.get("pipeline", {})
    paths = raw.get("paths", {})

    gemini = GeminiConfig(
        model=str(g.get("model", "gemini-2.5-flash")),
        temperature=float(g.get("temperature", 0.1)),
        top_p=float(g.get("top_p", 0.95)),
        max_output_tokens=int(g.get("max_output_tokens", 65536)),
        response_logprobs=bool(g.get("response_logprobs", False)),
        logprobs=int(g.get("logprobs", 5)),
    )
    pipeline = PipelineConfig(
        file_upload_poll_interval=float(p.get("file_upload_poll_interval", 2)),
        file_upload_max_wait=float(p.get("file_upload_max_wait", 120)),
        cleanup_uploaded_files=bool(p.get("cleanup_uploaded_files", True)),
    )

    in_dir = input_dir or (root / paths.get("input_dir", "./input"))
    out_dir = output_dir or (root / paths.get("output_dir", "./output"))

    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if not api_key:
        print("[config] WARNING: GEMINI_API_KEY is not set in .env")
    else:
        print("[config] GEMINI_API_KEY loaded from environment")

    return AppConfig(
        gemini=gemini,
        pipeline=pipeline,
        input_dir=Path(in_dir).resolve(),
        output_dir=Path(out_dir).resolve(),
        system_prompt=str(raw.get("system_prompt", "")).strip(),
        config_path=cfg_file.resolve(),
    )


def get_api_key() -> str:
    """Return Gemini API key from environment."""
    load_dotenv(_project_root() / ".env")
    key = os.getenv("GEMINI_API_KEY", "").strip()
    if not key:
        raise ValueError(
            "GEMINI_API_KEY is missing. Create a .env file in the project root "
            "with: GEMINI_API_KEY=your_key_here"
        )
    return key
