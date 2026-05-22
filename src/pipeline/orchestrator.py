"""End-to-end pipeline: ingest PDFs -> Gemini -> JSON + XLSX."""

from __future__ import annotations

import time
import traceback
from pathlib import Path

from src.config.loader import AppConfig, load_config
from src.export.json_export import write_tables_json
from src.export.xlsx_export import write_tables_xlsx
from src.extract.gemini_extractor import GeminiTableExtractor
from src.ingest.pdf_ingest import discover_pdfs, document_id_from_path


def run_pipeline(
    input_dir: Path | None = None,
    output_dir: Path | None = None,
    config_path: Path | None = None,
) -> int:
    """
    Run full extraction pipeline.

    Returns exit code: 0 if all documents succeeded, 1 if any failed or no input.
    """
    pipeline_start = time.perf_counter()
    print("=" * 60)
    print("[pipeline] Starting Gemini table extraction pipeline")
    print("=" * 60)

    config = load_config(config_path=config_path, input_dir=input_dir, output_dir=output_dir)
    config.output_dir.mkdir(parents=True, exist_ok=True)
    print(f"[pipeline] Input:  {config.input_dir}")
    print(f"[pipeline] Output: {config.output_dir}")

    pdfs = discover_pdfs(config.input_dir)
    if not pdfs:
        print("[pipeline] No PDFs found — exiting")
        elapsed = time.perf_counter() - pipeline_start
        print(f"[pipeline] Total pipeline time: {elapsed:.2f}s")
        return 1

    extractor = GeminiTableExtractor(config)
    failures = 0

    for idx, pdf_path in enumerate(pdfs, start=1):
        doc_start = time.perf_counter()
        document_id = document_id_from_path(pdf_path)
        print("-" * 60)
        print(f"[pipeline] Document {idx}/{len(pdfs)}: {pdf_path.name}")
        print(f"[pipeline] document_id={document_id}")

        try:
            doc = extractor.extract_from_pdf(pdf_path, document_id)
            write_tables_json(doc, config.output_dir)
            write_tables_xlsx(doc, config.output_dir)
            doc_elapsed = time.perf_counter() - doc_start
            print(f"[pipeline] Document {document_id} done in {doc_elapsed:.2f}s")
        except Exception as exc:
            failures += 1
            print(f"[pipeline] ERROR on {document_id}: {exc}")
            traceback.print_exc()

    total_elapsed = time.perf_counter() - pipeline_start
    print("=" * 60)
    print(
        f"[pipeline] Finished: {len(pdfs) - failures}/{len(pdfs)} succeeded, "
        f"{failures} failed"
    )
    print(f"[pipeline] Total pipeline time: {total_elapsed:.2f}s")
    print("=" * 60)
    return 0 if failures == 0 else 1
