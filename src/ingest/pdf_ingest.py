"""Discover and prepare PDF documents for Gemini ingestion."""

from __future__ import annotations

from pathlib import Path


def document_id_from_path(pdf_path: Path) -> str:
    """Stem of filename, e.g. doc_001.pdf -> doc_001."""
    return pdf_path.stem


def discover_pdfs(input_dir: Path) -> list[Path]:
    """Return sorted list of PDF paths under input_dir."""
    print(f"[ingest] Scanning for PDFs in: {input_dir}")
    if not input_dir.is_dir():
        print(f"[ingest] Input directory does not exist: {input_dir}")
        return []

    pdfs = sorted(input_dir.glob("*.pdf")) + sorted(input_dir.glob("*.PDF"))
    # Deduplicate case-insensitive duplicates on case-insensitive filesystems
    seen: set[str] = set()
    unique: list[Path] = []
    for p in pdfs:
        key = p.resolve().as_posix().lower()
        if key not in seen:
            seen.add(key)
            unique.append(p)

    print(f"[ingest] Found {len(unique)} PDF(s)")
    for p in unique:
        print(f"[ingest]   - {p.name} ({p.stat().st_size / 1024:.1f} KB)")
    return unique
