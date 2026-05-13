from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import urlopen


def _fetch_json(url: str, timeout: float = 8.0) -> Any:
    with urlopen(url, timeout=timeout) as response:  # nosec: B310 - controlled local URL input
        payload = response.read().decode("utf-8")
    return json.loads(payload)


def _contains_any(text: str, values: list[str]) -> bool:
    lowered = text.lower()
    return any(value.lower() in lowered for value in values)


def run_smoke(
    *,
    base_url: str,
    index_path: Path,
    config_path: Path,
    zoom: int,
    limit: int,
) -> dict[str, Any]:
    checks: dict[str, Any] = {}
    errors: list[str] = []
    status = "completed"

    try:
        index_text = index_path.read_text(encoding="utf-8")
    except OSError as exc:
        status = "failed"
        errors.append(f"index_read_error: {exc}")
        index_text = ""

    config_raw = ""
    try:
        config_raw = config_path.read_text(encoding="utf-8")
        config = json.loads(config_raw)
    except (OSError, json.JSONDecodeError) as exc:
        status = "failed"
        errors.append(f"config_read_error: {exc}")
        config = {}

    checks["ui_toggle_present"] = 'id="showFutureGrowth"' in index_text
    checks["ui_popup_hook_present"] = "future-growth-popup" in index_text or "future-growth-popup" in config_raw
    checks["ui_label_present"] = _contains_any(index_text, ["Gelecek Gelisim", "Future Growth"])
    checks["legend_present"] = 'id="futureGrowthLegend"' in index_text
    checks["config_enabled"] = bool(config.get("enabled"))
    checks["config_layer_name_present"] = bool(config.get("layerName"))
    checks["config_color_scale_count"] = len(config.get("colorScale", [])) if isinstance(config.get("colorScale"), list) else 0

    layer_path = str(config.get("api", {}).get("layer") or "/api/future-growth/layer")
    detail_path_template = str(config.get("api", {}).get("parcelDetail") or "/api/future-growth/parcels/{parcelId}")
    methodology_path = str(config.get("api", {}).get("methodology") or "/api/future-growth/methodology")

    layer_url = f"{base_url.rstrip('/')}{layer_path}?{urlencode({'zoom': zoom, 'limit': limit})}"
    layer_payload: dict[str, Any] = {}
    try:
        layer_payload = _fetch_json(layer_url)
        checks["layer_http_ok"] = True
        checks["layer_type_ok"] = layer_payload.get("type") == "FeatureCollection"
    except (HTTPError, URLError, TimeoutError, json.JSONDecodeError) as exc:
        status = "failed"
        checks["layer_http_ok"] = False
        checks["layer_type_ok"] = False
        errors.append(f"layer_request_error: {exc}")

    features = layer_payload.get("features", []) if isinstance(layer_payload, dict) else []
    checks["layer_feature_count"] = len(features)
    checks["layer_has_features"] = len(features) > 0

    required_layer_props = {"parcel_id", "future_growth_percent", "confidence_score", "color_class", "hex_color"}
    if features:
        props = (features[0] or {}).get("properties", {})
        checks["layer_required_properties_ok"] = required_layer_props.issubset(set(props.keys()))
        parcel_id = props.get("parcel_id")
    else:
        checks["layer_required_properties_ok"] = False
        parcel_id = None
        status = "failed"
        errors.append("no_features_from_layer")

    detail_payload: dict[str, Any] = {}
    if parcel_id is not None:
        detail_url = f"{base_url.rstrip('/')}{detail_path_template.replace('{parcelId}', str(parcel_id))}"
        try:
            detail_payload = _fetch_json(detail_url)
            checks["detail_http_ok"] = True
        except (HTTPError, URLError, TimeoutError, json.JSONDecodeError) as exc:
            status = "failed"
            checks["detail_http_ok"] = False
            errors.append(f"detail_request_error: {exc}")
    else:
        checks["detail_http_ok"] = False

    required_detail_fields = {
        "parcel_id",
        "future_growth_percent",
        "confidence_score",
        "color_class",
        "hex_color",
        "score_breakdown",
        "top_reasons",
        "warnings",
        "evidence",
        "calculation_version",
    }
    checks["detail_required_fields_ok"] = required_detail_fields.issubset(set(detail_payload.keys()))

    evidence = detail_payload.get("evidence", []) if isinstance(detail_payload, dict) else []
    parcel_id_value = detail_payload.get("parcel_id")
    checks["popup_evidence_scoped_to_parcel"] = bool(evidence) and all(row.get("parcel_id") == parcel_id_value for row in evidence)
    checks["popup_warning_present_for_non_parcel_data"] = any(
        isinstance(item, str) and "local authority" in item.lower() for item in detail_payload.get("warnings", [])
    )

    methodology_url = f"{base_url.rstrip('/')}{methodology_path}"
    try:
        methodology_payload = _fetch_json(methodology_url)
        checks["methodology_http_ok"] = True
        checks["methodology_disclaimer_present"] = "Kesin fiyat tahmini" in str(methodology_payload.get("methodology_markdown", ""))
    except (HTTPError, URLError, TimeoutError, json.JSONDecodeError) as exc:
        status = "failed"
        checks["methodology_http_ok"] = False
        checks["methodology_disclaimer_present"] = False
        errors.append(f"methodology_request_error: {exc}")

    if not all(
        bool(checks.get(name))
        for name in [
            "ui_toggle_present",
            "ui_label_present",
            "legend_present",
            "config_enabled",
            "layer_http_ok",
            "layer_type_ok",
            "layer_has_features",
            "layer_required_properties_ok",
            "detail_http_ok",
            "detail_required_fields_ok",
            "popup_evidence_scoped_to_parcel",
            "methodology_http_ok",
            "methodology_disclaimer_present",
        ]
    ):
        status = "failed"

    return {
        "status": status,
        "base_url": base_url,
        "layer_url": layer_url,
        "checked_parcel_id": parcel_id,
        "checks": checks,
        "errors": errors,
    }


def parse_args() -> argparse.Namespace:
    repo_root = Path(__file__).resolve().parents[1]
    default_index = repo_root.parent / "england_map_web" / "index.html"
    default_config = repo_root.parent / "england_map_web" / "config" / "future-growth-layer.json"

    parser = argparse.ArgumentParser(description="Future Growth frontend layer + popup smoke test")
    parser.add_argument("--base-url", default="http://127.0.0.1:8010")
    parser.add_argument("--index-path", type=Path, default=default_index)
    parser.add_argument("--config-path", type=Path, default=default_config)
    parser.add_argument("--zoom", type=int, default=10)
    parser.add_argument("--limit", type=int, default=5)
    parser.add_argument("--output", type=Path, default=None)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    result = run_smoke(
        base_url=args.base_url,
        index_path=args.index_path,
        config_path=args.config_path,
        zoom=args.zoom,
        limit=args.limit,
    )
    output = json.dumps(result, ensure_ascii=True, indent=2)
    print(output)

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(output + "\n", encoding="utf-8")

    return 0 if result["status"] == "completed" else 1


if __name__ == "__main__":
    sys.exit(main())
