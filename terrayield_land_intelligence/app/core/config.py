from __future__ import annotations

import datetime as dt
import os
from functools import lru_cache
from pathlib import Path
from typing import Any


def _env_int(name: str, default: int) -> int:
    raw = os.environ.get(name, "").strip()
    if not raw:
        return default
    try:
        return int(raw)
    except ValueError:
        return default


def _env_float(name: str, default: float) -> float:
    raw = os.environ.get(name, "").strip()
    if not raw:
        return default
    try:
        return float(raw)
    except ValueError:
        return default


def _env_list(name: str, default: list[str]) -> list[str]:
    raw = os.environ.get(name, "").strip()
    if not raw:
        return list(default)
    return [item.strip() for item in raw.split(",") if item.strip()]


class Settings:
    """Small runtime settings object used by API routes and tests.

    The project previously referenced app.core.config from multiple modules.
    This class keeps those imports stable without performing DB writes,
    migrations, network calls, or secret printing.
    """

    def __init__(self) -> None:
        self.app_name = os.environ.get("APP_NAME", "TerraYield Land Intelligence")
        self.app_host = os.environ.get("APP_HOST", "0.0.0.0")
        self.app_port = _env_int("APP_PORT", 8010)
        self.allowed_origins = _env_list("ALLOWED_ORIGINS", ["*"])

        self.confidence_weight_source_reliability = _env_float("CONFIDENCE_WEIGHT_SOURCE_RELIABILITY", 0.30)
        self.confidence_weight_freshness = _env_float("CONFIDENCE_WEIGHT_FRESHNESS", 0.20)
        self.confidence_weight_geometry_quality = _env_float("CONFIDENCE_WEIGHT_GEOMETRY_QUALITY", 0.20)
        self.confidence_weight_match_quality = _env_float("CONFIDENCE_WEIGHT_MATCH_QUALITY", 0.20)
        self.confidence_weight_completeness = _env_float("CONFIDENCE_WEIGHT_COMPLETENESS", 0.10)

        self.landhub_stale_after_days = _env_int("LANDHUB_STALE_AFTER_DAYS", 90)
        self.government_property_stale_after_days = _env_int("GOVERNMENT_PROPERTY_STALE_AFTER_DAYS", 90)
        self.planning_data_stale_after_days = _env_int("PLANNING_DATA_STALE_AFTER_DAYS", 180)
        self.local_brownfield_stale_after_days = _env_int("LOCAL_BROWNFIELD_STALE_AFTER_DAYS", 180)
        self.inspire_stale_after_days = _env_int("INSPIRE_STALE_AFTER_DAYS", 365)
        self.price_paid_stale_after_days = _env_int("PRICE_PAID_STALE_AFTER_DAYS", 90)
        self.market_stale_after_days = _env_int("MARKET_STALE_AFTER_DAYS", 30)

        default_storage_root = Path(os.environ.get("CONTRACTOR_STORAGE_ROOT", ".aays_contractor"))
        self.contractor_storage_root = default_storage_root
        self.contractor_export_root = Path(os.environ["CONTRACTOR_EXPORT_ROOT"]) if os.environ.get("CONTRACTOR_EXPORT_ROOT") else None
        self.contractor_manifest_root = Path(os.environ["CONTRACTOR_MANIFEST_ROOT"]) if os.environ.get("CONTRACTOR_MANIFEST_ROOT") else None
        self.contractor_preflight_audit_path = Path(
            os.environ.get(
                "CONTRACTOR_PREFLIGHT_AUDIT_PATH",
                str(default_storage_root / "preflight.audit.json"),
            )
        )

    def now_utc(self) -> dt.datetime:
        return dt.datetime.now(dt.UTC)

    def __getattr__(self, name: str) -> Any:
        if name.endswith("_path"):
            return Path(os.environ.get(name.upper(), ""))
        if name.endswith("_root"):
            return Path(os.environ.get(name.upper(), "."))
        if name.endswith("_days"):
            return 30
        raise AttributeError(name)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
