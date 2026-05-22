# ITaskRag — Gemini Table Extraction

Extract **tables only** from mixed-content PDFs (digital, scanned, or mixed) by sending each PDF **directly to the Gemini API**—no separate OCR step. Outputs structured JSON and an Excel workbook per document.

## Architecture

```
main.py
  └── pipeline/orchestrator.py   # timing, per-doc loop
        ├── ingest/pdf_ingest.py # discover PDFs
        ├── extract/gemini_extractor.py  # upload PDF → Gemini → JSON
        └── export/
              ├── json_export.py
              └── xlsx_export.py
config.yaml                      # model, temperature, system prompt
.env                             # GEMINI_API_KEY (you create this)
```

## Setup

1. **Python 3.10+** recommended.

2. **Virtual environment** (optional but recommended):

   ```bash
   cd /yourpathlocation
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

3. **API key** — create a file named `.env` in the project root (same folder as `main.py`):

   ```env
   GEMINI_API_KEY=your_actual_key_here
   ```

   Get a key from [Google AI Studio](https://aistudio.google.com/apikey).  

4. **Configuration** — edit `config.yaml` to change:
   - `gemini.model` (e.g. `gemini-2.5-flash`, `gemini-2.5-pro`)
   - `gemini.temperature`, `top_p`, `max_output_tokens`
   - `system_prompt` (full extraction instructions)
   - Default `input_dir` / `output_dir`

5. **Input PDFs** — place files in `./input/`, e.g. `input/doc_001.pdf`.

## Run

```bash
python main.py --input ./input --output ./output
```

Optional:

```bash
python main.py --config ./config.yaml --input ./input --output ./output
```

## Outputs

For each `doc_001.pdf`:

| File | Description |
|------|-------------|
| `output/doc_001_tables.json` | Tables-only JSON (assignment schema) |
| `output/doc_001_tables.xlsx` | One worksheet per table |


## Assumptions & design choices

| Topic | Approach |
|-------|----------|
| OCR | **Not used** — Gemini multimodal document understanding reads the PDF natively (works for scanned and digital PDFs). |
| Running text | Excluded via system prompt + schema (tables only). |
| Bounding boxes | **Not included** — LLMs do not provide reliable layout boxes for this task. |
| Confidence scores | **Not fabricated.** The Gemini structured-output API does not expose per-cell OCR-style confidence. Optional `response_logprobs` in `config.yaml` enables token logprobs only; they are not mapped to cell/row scores. |
| Multi-page tables | Merged into one logical table with `page_start` / `page_end`. |
| Runtime | Logged per document and as **total pipeline time** in the final print line. |
| Target ≤2 min/doc | Use `gemini-2.5-flash` and reasonable PDF size; large scans may take longer. |

## Logging

The pipeline prints tagged steps throughout, e.g. `[ingest]`, `[gemini]`, `[export/json]`, `[pipeline]`. The last line reports total elapsed seconds.

## Compared to PyMuPDF + Camelot

This repo is a **Gemini-first** alternative: one API call per document with structured JSON, simpler pipeline, stronger on messy scans at the cost of API latency and key management.

## Troubleshooting

- **`GEMINI_API_KEY is missing`** — create `.env` with `GEMINI_API_KEY=...`
- **Empty tables** — tighten `system_prompt` or try `gemini-2.5-pro` in `config.yaml`
- **Upload timeout** — increase `pipeline.file_upload_max_wait` in `config.yaml`
