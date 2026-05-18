from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ListingManifestGap:
    code: str
    message: str


def _build_listing_manifest_gaps(
    source_name: str,
    *,
    manifest_status: dict[str, Any],
    row_count: int,
) -> list[ListingManifestGap]:
    gaps: list[ListingManifestGap] = []

    if not manifest_status.get("manifest_exists", False):
        gaps.append(ListingManifestGap(f"{source_name}_manifest_missing", "Manifest is missing."))
        return gaps

    if manifest_status.get("parse_error"):
        gaps.append(ListingManifestGap(f"{source_name}_manifest_parse_error", "Manifest cannot be parsed."))
        return gaps

    if manifest_status.get("missing_active_files"):
        gaps.append(ListingManifestGap(f"{source_name}_manifest_missing_files", "Active manifest files are missing."))
        return gaps

    if manifest_status.get("has_demo_only_manifest") and not manifest_status.get("has_live_ready_manifest"):
        gaps.append(ListingManifestGap(f"{source_name}_demo_only", "Only demo manifest entries are available."))
        return gaps

    if manifest_status.get("availability") == "inactive_only" or (
        not manifest_status.get("has_live_ready_manifest")
        and not manifest_status.get("has_demo_only_manifest")
        and row_count == 0
    ):
        gaps.append(ListingManifestGap(f"{source_name}_manifest_inactive", "Manifest has no active live-ready entries."))

    return gaps
