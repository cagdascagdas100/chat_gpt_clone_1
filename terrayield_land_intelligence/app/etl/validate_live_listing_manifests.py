from __future__ import annotations

import argparse
from typing import Sequence

from app.core.config import get_settings
from app.services.source_manifest_status import inspect_configured_listing_manifest_status

LISTING_SOURCES = [
    "market_listing_adapter",
    "government_property_finder",
    "homes_england_landhub",
]


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate configured live listing manifests.")
    parser.add_argument("--require-live", action="store_true")
    args = parser.parse_args(list(argv) if argv is not None else None)

    settings = get_settings()
    statuses = {
        source_name: inspect_configured_listing_manifest_status(source_name, settings)
        for source_name in LISTING_SOURCES
    }
    live_ready_sources = [
        source_name
        for source_name, status in statuses.items()
        if status.get("availability") == "live_ready" or status.get("has_live_ready_manifest")
    ]

    if live_ready_sources:
        print("live_ready_sources: " + ", ".join(live_ready_sources))
    else:
        print("live_ready_sources: none")

    if args.require_live and not live_ready_sources:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
