from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class ContractorExportRowsResponse(BaseModel):
    source_file: str
    total_rows: int
    offset: int
    limit: int
    rows: list[dict[str, Any]] = Field(default_factory=list)


class ContractorStatusResponse(BaseModel):
    status: str
    storage_root: str
    export_root: str
    warnings: list[str] = Field(default_factory=list)
    preflight_audit: dict[str, Any] = Field(default_factory=dict)
    postgres_load_manifest: dict[str, Any] = Field(default_factory=dict)
    parcel_match_manifest: dict[str, Any] = Field(default_factory=dict)
    export_manifest: dict[str, Any] = Field(default_factory=dict)
