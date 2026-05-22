"""Write extraction results to JSON files."""

from __future__ import annotations

import json
from pathlib import Path

from src.models.schema import DocumentTables


def write_tables_json(doc: DocumentTables, output_dir: Path) -> Path:
    """Write <document_id>_tables.json under output_dir."""
    output_dir.mkdir(parents=True, exist_ok=True)
    out_path = output_dir / f"{doc.document_id}_tables.json"
    print(f"[export/json] Writing: {out_path}")
    payload = doc.model_dump(mode="json")
    with out_path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)
    print(f"[export/json] Wrote {len(doc.tables)} table(s)")
    return out_path
