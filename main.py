#!/usr/bin/env python3
"""CLI entrypoint: python main.py --input ./input --output ./output"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Allow `python main.py` from project root without install
_ROOT = Path(__file__).resolve().parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from src.pipeline.orchestrator import run_pipeline  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Extract tables from PDFs using Gemini (PDF sent directly, no OCR pre-step)."
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=None,
        help="Folder of PDF documents (default: ./input from config.yaml)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Output folder for JSON and XLSX (default: ./output from config.yaml)",
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=None,
        help="Path to config.yaml (default: ./config.yaml)",
    )
    return parser.parse_args()


def main() -> int:
    print("[main] Table extraction CLI")
    args = parse_args()
    return run_pipeline(
        input_dir=args.input,
        output_dir=args.output,
        config_path=args.config,
    )


if __name__ == "__main__":
    raise SystemExit(main())
