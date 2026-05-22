"""Pydantic models and JSON schema for Gemini structured table extraction."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class TableRecord(BaseModel):
    """Single extracted table (assignment JSON shape; no bounding boxes)."""

    table_id: int = Field(..., ge=1, description="Sequential table index in document")
    page_start: int = Field(..., ge=1, description="First page (1-based)")
    page_end: int = Field(..., ge=1, description="Last page (1-based)")
    title: str = Field(default="", description="Caption or heading if present")
    columns: list[str] = Field(..., min_length=1)
    rows: list[list[str]] = Field(default_factory=list)


class DocumentTables(BaseModel):
    """Root extraction result per PDF."""

    document_id: str
    tables: list[TableRecord] = Field(default_factory=list)


def document_tables_json_schema() -> dict[str, Any]:
    """
    Flat JSON Schema for Gemini structured output (no $ref/$defs).

    Matches assignment example; no bounding boxes; no fabricated confidence.
    """
    return {
        "type": "object",
        "properties": {
            "document_id": {"type": "string"},
            "tables": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "table_id": {"type": "integer"},
                        "page_start": {"type": "integer"},
                        "page_end": {"type": "integer"},
                        "title": {"type": "string"},
                        "columns": {
                            "type": "array",
                            "items": {"type": "string"},
                        },
                        "rows": {
                            "type": "array",
                            "items": {
                                "type": "array",
                                "items": {"type": "string"},
                            },
                        },
                    },
                    "required": [
                        "table_id",
                        "page_start",
                        "page_end",
                        "columns",
                        "rows",
                    ],
                },
            },
        },
        "required": ["document_id", "tables"],
    }


def example_output() -> dict[str, Any]:
    """Reference shape from assignment overview."""
    return {
        "document_id": "doc_001",
        "tables": [
            {
                "table_id": 1,
                "page_start": 2,
                "page_end": 2,
                "title": "Transaction Summary",
                "columns": ["Date", "Description", "Debit", "Credit", "Balance"],
                "rows": [
                    ["2025-01-05", "Opening Balance", "", "", "5000.00"],
                    ["2025-01-06", "ATM Withdrawal", "200.00", "", "4800.00"],
                ],
            }
        ],
    }
