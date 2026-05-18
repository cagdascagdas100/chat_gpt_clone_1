from __future__ import annotations

import datetime as dt
from typing import Any

from pydantic import BaseModel, Field


class SourceDescriptor(BaseModel):
    name: str
    label: str | None = None
    description: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class SourceStatus(BaseModel):
    name: str
    last_snapshot_at: dt.datetime | None = None
    last_source_updated_at: dt.datetime | None = None
    row_count: int = 0
    stale_threshold_days: int = 30
    is_stale: bool = True
    notes: dict[str, Any] = Field(default_factory=dict)
