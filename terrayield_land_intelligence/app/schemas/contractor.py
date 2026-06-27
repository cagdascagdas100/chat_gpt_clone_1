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

class ContractorParcelContactsResponse(BaseModel):
    parcel_id: str
    source_matches_file: str
    source_contractors_file: str
    total_rows: int
    ready_rows: int
    blocked_rows: int
    limit: int
    include_blocked: bool
    structure_type: str | None = None
    rows: list[dict[str, Any]] = Field(default_factory=list)
    integration_mode: str = "unknown"
    parcel_group_ids: list[Any] = Field(default_factory=list)
    source_files: dict[str, Any] = Field(default_factory=dict)
    final_audit: dict[str, Any] = Field(default_factory=dict)

