"""Send PDFs directly to Gemini and parse structured table JSON."""

from __future__ import annotations

import json
import time
from pathlib import Path

from google import genai
from google.genai import types

from src.config.loader import AppConfig, get_api_key
from src.models.schema import DocumentTables, document_tables_json_schema


class GeminiTableExtractor:
    """Upload PDF to Gemini Files API and extract tables via structured output."""

    def __init__(self, config: AppConfig) -> None:
        self.config = config
        print("[gemini] Initializing Gemini client")
        self.client = genai.Client(api_key=get_api_key())
        self._schema = document_tables_json_schema()
        print(f"[gemini] Model: {config.gemini.model}")
        print(f"[gemini] Temperature: {config.gemini.temperature}")

    def extract_from_pdf(self, pdf_path: Path, document_id: str) -> DocumentTables:
        """Upload PDF, call generate_content, validate and return DocumentTables."""
        print(f"[gemini] Starting extraction for document_id={document_id}")
        uploaded = self._upload_pdf(pdf_path)
        try:
            result = self._generate_tables(uploaded, document_id)
            print(f"[gemini] Parsed {len(result.tables)} table(s) for {document_id}")
            return result
        finally:
            if self.config.pipeline.cleanup_uploaded_files:
                self._delete_file(uploaded.name)

    def _upload_pdf(self, pdf_path: Path) -> types.File:
        """Upload PDF via Files API and wait until ACTIVE."""
        print(f"[gemini] Uploading PDF: {pdf_path.name}")
        uploaded = self.client.files.upload(
            file=str(pdf_path),
            config=types.UploadFileConfig(
                display_name=pdf_path.name,
                mime_type="application/pdf",
            ),
        )
        print(f"[gemini] Upload complete, file name: {uploaded.name}")

        deadline = time.monotonic() + self.config.pipeline.file_upload_max_wait
        state_str = lambda s: getattr(s, "name", str(s)) if s else "UNKNOWN"
        while uploaded.state and state_str(uploaded.state) != "ACTIVE":
            if time.monotonic() > deadline:
                raise TimeoutError(
                    f"File {uploaded.name} did not become ACTIVE within "
                    f"{self.config.pipeline.file_upload_max_wait}s (state={uploaded.state})"
                )
            print(f"[gemini] Waiting for file processing (state={state_str(uploaded.state)})...")
            time.sleep(self.config.pipeline.file_upload_poll_interval)
            uploaded = self.client.files.get(name=uploaded.name)

        print("[gemini] File is ACTIVE, ready for generation")
        return uploaded

    def _generate_tables(self, uploaded: types.File, document_id: str) -> DocumentTables:
        """Call Gemini with system prompt + PDF; parse JSON response."""
        user_message = (
            f"document_id for this file: {document_id}\n"
            f"Original filename: {uploaded.display_name or document_id}.pdf\n"
            "Extract all tables from this PDF. Return JSON only."
        )
        print("[gemini] Calling generate_content (PDF sent directly, no OCR pre-step)")

        gen_kwargs: dict = {
            "system_instruction": self.config.system_prompt,
            "temperature": self.config.gemini.temperature,
            "top_p": self.config.gemini.top_p,
            "max_output_tokens": self.config.gemini.max_output_tokens,
            "response_mime_type": "application/json",
            "response_schema": self._schema,
        }
        if self.config.gemini.response_logprobs:
            gen_kwargs["response_logprobs"] = True
            gen_kwargs["logprobs"] = self.config.gemini.logprobs
            print("[gemini] Logprobs enabled (not converted to per-cell confidence)")

        response = self.client.models.generate_content(
            model=self.config.gemini.model,
            contents=[
                types.Content(
                    role="user",
                    parts=[
                        types.Part.from_uri(
                            file_uri=uploaded.uri,
                            mime_type=uploaded.mime_type or "application/pdf",
                        ),
                        types.Part.from_text(text=user_message),
                    ],
                )
            ],
            config=types.GenerateContentConfig(**gen_kwargs),
        )

        text = response.text
        if not text:
            raise ValueError("Gemini returned empty response text")
        print(f"[gemini] Response received ({len(text)} chars)")

        data = json.loads(text)
        # Enforce document_id from filename (model may drift)
        data["document_id"] = document_id
        doc = DocumentTables.model_validate(data)
        return doc

    def _delete_file(self, file_name: str) -> None:
        """Remove uploaded file from Gemini storage."""
        try:
            print(f"[gemini] Cleaning up uploaded file: {file_name}")
            self.client.files.delete(name=file_name)
        except Exception as exc:  # noqa: BLE001 — best-effort cleanup
            print(f"[gemini] Cleanup warning: {exc}")
