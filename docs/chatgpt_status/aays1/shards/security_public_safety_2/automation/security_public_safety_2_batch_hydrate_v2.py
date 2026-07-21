from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import json
import os
import re
from html import escape
from pathlib import Path
from typing import Any

SLOT_ID = "security_public_safety_2"
EXPECTED = 300
REPO = Path(os.environ.get("AAYS_REPO_ROOT", r"F:\chatgpt\chat_gpt_clone_1_main"))
SHARD = REPO / "docs" / "chatgpt_status" / "aays1" / "shards" / SLOT_ID
WEB = REPO / "england_map_web" / "data" / "aays_18_slots" / SLOT_ID
OUT = SHARD / "runner_outputs"
BASE_SCRIPT = SHARD / "automation" / "security_public_safety_2_batch_hydrate.py"
MONTH_HEADER = re.compile(r"^(?:20\d{2}[-_/ ]?(?:0[1-9]|1[0-2])|(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[-_ /]?20\d{2})$", re.I)
CODE_ALIASES = ("lsoa code (2021)", "lsoa code", "lsoa_code", "lsoa21cd", "lsoa11cd")
NAME_ALIASES = ("lsoa name (2021)", "lsoa name", "lsoa_name", "lsoa21nm", "lsoa11nm")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def normalized_headers(fieldnames: list[str] | None) -> dict[str, str]:
    return {field.strip().lower(): field for field in (fieldnames or []) if field}


def first_header(names: dict[str, str], aliases: tuple[str, ...]) -> str | None:
    return next((names[alias] for alias in aliases if alias in names), None)


def number(value: Any) -> float | None:
    text = str(value or "").strip().replace(",", "")
    if not text:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def discover_csv(explicit: str | None, env_name: str, patterns: tuple[str, ...]) -> Path | None:
    values = [explicit, os.environ.get(env_name)]
    for value in values:
        if value and Path(value).is_file():
            return Path(value)
    for root in (REPO / "england_map_web" / "data", REPO / "docs" / "chatgpt_status"):
        if not root.is_dir():
            continue
        for pattern in patterns:
            matches = sorted(root.rglob(pattern), key=lambda path: path.stat().st_mtime, reverse=True)
            if matches:
                return matches[0]
    return None


def mps_lookup(path: Path | None) -> tuple[dict[str, dict[str, Any]], dict[str, Any]]:
    if not path or not path.is_file():
        return {}, {"status": "NOT_AVAILABLE", "path": str(path) if path else None}
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        names = normalized_headers(reader.fieldnames)
        code = first_header(names, CODE_ALIASES)
        name = first_header(names, NAME_ALIASES)
        if not code:
            return {}, {"status": "INVALID_COLUMNS", "fieldnames": reader.fieldnames}
        explicit_count = next((original for normalized, original in names.items() if normalized in {"count", "crime count", "offence count", "offences", "number of crimes"}), None)
        month_columns = [field for field in (reader.fieldnames or []) if MONTH_HEADER.match(field.strip())]
        if not explicit_count and not month_columns:
            return {}, {"status": "NO_COUNT_OR_MONTH_COLUMNS", "fieldnames": reader.fieldnames}
        output: dict[str, dict[str, Any]] = {}
        source_rows = 0
        for row in reader:
            lsoa = str(row.get(code) or "").strip()
            if not lsoa:
                continue
            source_rows += 1
            values = [number(row.get(explicit_count))] if explicit_count else [number(row.get(column)) for column in month_columns]
            total = sum(value for value in values if value is not None)
            item = output.setdefault(lsoa, {"mps_lsoa_name": row.get(name) if name else None, "mps_lsoa_crime_count_period": 0.0, "mps_lsoa_source_rows": 0})
            item["mps_lsoa_crime_count_period"] += total
            item["mps_lsoa_source_rows"] += 1
        for item in output.values():
            item["mps_lsoa_crime_count_period"] = round(item["mps_lsoa_crime_count_period"], 3)
    return output, {
        "status": "LOADED",
        "path": str(path),
        "sha256": sha256_file(path),
        "source_rows": source_rows,
        "unique_lsoa": len(output),
        "count_column": explicit_count,
        "month_columns": month_columns,
        "source_semantics": "LSOA_MONTHLY_RECORDED_CRIME_AREA_CONTEXT",
        "parcel_measurement": False,
    }


def load_base() -> Any:
    spec = importlib.util.spec_from_file_location("security_slot2_base", BASE_SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"BASE_IMPORT_FAILED:{BASE_SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    keys = sorted({key for row in rows for key in row if key != "geometry"})
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=keys, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def render_html(payload: dict[str, Any]) -> str:
    body = "".join(
        f"<tr><td>{index}</td><td>{escape(str(row['parcel_id']))}</td><td>{escape(str(row['candidate_status']))}</td>"
        f"<td>{row['accuracy_score_4']}</td><td>{escape(str(row.get('lsoa_code') or 'not_available'))}</td>"
        f"<td>{escape(str(row.get('mps_lsoa_crime_count_period') or 'not_available'))}</td>"
        f"<td>{escape(str(row.get('official_api_http_status') or 'not_available'))}</td>"
        f"<td>{escape(str(row.get('official_api_one_mile_supporting_count') or 'not_available'))}</td></tr>"
        for index, row in enumerate(payload["rows"], 1)
    )
    return f'''<!doctype html><html lang="tr"><head><meta charset="utf-8"><meta http-equiv="refresh" content="15"><title>Security/Public Safety Slot 2</title><style>body{{font-family:Segoe UI,Arial,sans-serif;margin:20px}}table{{border-collapse:collapse;width:100%}}th,td{{border:1px solid #bbb;padding:6px}}</style></head><body data-slot-id="{SLOT_ID}" data-visible-row-count="{len(payload['rows'])}" data-final-ready="false"><h1>Security / Public Safety — Slot 2</h1><p>Gerçek canonical={payload['canonical_rows']}/300; doğruluk ≥3={payload['accuracy_ge_3_count']}; 4/4={payload['accuracy_4_count']}; promoted=0.</p><table><thead><tr><th>#</th><th>Parsel</th><th>Durum</th><th>/4</th><th>LSOA</th><th>MPS LSOA dönem toplamı</th><th>HTTP</th><th>1 mil destek</th></tr></thead><tbody>{body}</tbody></table><p>AREA_LEVEL_PROXY; exact parsel suçu değildir. 4/4 için canonical + Police.uk + IoD25 corrected v2 + MPS LSOA gerekir. final_ready=false.</p></body></html>'''


def enrich(payload: dict[str, Any], mps: dict[str, dict[str, Any]], mps_meta: dict[str, Any]) -> dict[str, Any]:
    rows = payload.get("rows") or []
    for row in rows:
        lsoa = row.get("lsoa_code")
        mps_ok = bool(lsoa and lsoa in mps)
        iod_ok = row.get("iod25_crime_score") not in (None, "")
        api_ok = row.get("official_api_http_status") == 200 and bool(row.get("official_api_sha256"))
        row["mps_lsoa_join_pass"] = mps_ok
        row["iod25_v2_join_pass"] = iod_ok
        if mps_ok:
            row.update(mps[lsoa])
        if row.get("candidate_status") == "CANONICAL_FEATURE_NOT_FOUND":
            continue
        if api_ok and iod_ok and mps_ok:
            row["accuracy_score_4"] = 4
            row["candidate_status"] = "CANONICAL_API_IOD25_V2_MPS_LSOA_VERIFIED"
        elif api_ok:
            row["accuracy_score_4"] = 3
            row["candidate_status"] = "CANONICAL_API_VERIFIED_CONTEXT_INCOMPLETE"
        else:
            row["accuracy_score_4"] = min(int(row.get("accuracy_score_4") or 0), 2)
    payload["schema_version"] = 4
    payload["mps_lsoa"] = mps_meta
    payload["accuracy_ge_3_count"] = sum(int(row.get("accuracy_score_4") or 0) >= 3 for row in rows)
    payload["accuracy_4_count"] = sum(int(row.get("accuracy_score_4") or 0) == 4 for row in rows)
    payload["accuracy_4_rule"] = "canonical identity + Police.uk HTTP/SHA + IoD25 corrected v2 LSOA + MPS LSOA recorded-crime join"
    payload["actual_business_rows_written"] = 0
    payload["promoted_business_rows"] = 0
    payload["output_semantics"] = "AREA_LEVEL_PROXY"
    payload["final_ready"] = False
    return payload


def run(arguments: argparse.Namespace) -> dict[str, Any]:
    iod_path = discover_csv(arguments.iod25_csv, "AAYS_IOD25_V2_CSV", ("*IoD*2025*v2*.csv", "*File*2*v2*.csv", "*deprivation*v2*.csv"))
    mps_path = discover_csv(arguments.mps_lsoa_csv, "AAYS_MPS_LSOA_CSV", ("*MPS*LSOA*Level*Crime*.csv", "*LSOA*Level*Crime*.csv", "*LSOA*Crime*.csv"))
    base = load_base()
    base_args = argparse.Namespace(iod25_csv=str(iod_path) if iod_path else None, skip_api=arguments.skip_api, test_month=arguments.test_month)
    payload = base.run(base_args)
    mps, mps_meta = mps_lookup(mps_path)
    payload = enrich(payload, mps, mps_meta)
    OUT.mkdir(parents=True, exist_ok=True)
    WEB.mkdir(parents=True, exist_ok=True)
    json_path = OUT / "security_public_safety_2_hydrated_300_latest.json"
    csv_path = OUT / "security_public_safety_2_hydrated_300_latest.csv"
    geojson_path = OUT / "security_public_safety_2_hydrated_300_latest.geojson"
    html_path = WEB / "progress.html"
    web_json = WEB / "hydrated_300_latest.json"
    write_csv(csv_path, payload["rows"])
    geojson_path.write_text(json.dumps({"type": "FeatureCollection", "features": [{"type": "Feature", "geometry": row.get("geometry"), "properties": {key: value for key, value in row.items() if key != "geometry"}} for row in payload["rows"]]}, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
    html_path.write_text(render_html(payload), encoding="utf-8")
    csv_rows = sum(1 for _ in csv_path.open(encoding="utf-8")) - 1
    geo_rows = len(json.loads(geojson_path.read_text(encoding="utf-8"))["features"])
    payload["artifacts"] = {
        "csv_sha256": sha256_file(csv_path),
        "geojson_sha256": sha256_file(geojson_path),
        "html_sha256": sha256_file(html_path),
        "parity_pass": csv_rows == geo_rows == len(payload["rows"]) == EXPECTED,
    }
    text = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    json_path.write_text(text, encoding="utf-8")
    web_json.write_text(text, encoding="utf-8")
    return payload


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--iod25-csv")
    parser.add_argument("--mps-lsoa-csv")
    parser.add_argument("--skip-api", action="store_true")
    parser.add_argument("--test-month")
    return parser.parse_args()


if __name__ == "__main__":
    result = run(parse_args())
    print(json.dumps({"slot_id": SLOT_ID, "canonical_rows": result["canonical_rows"], "accuracy_ge_3_count": result["accuracy_ge_3_count"], "accuracy_4_count": result["accuracy_4_count"], "parity_pass": result["artifacts"]["parity_pass"], "final_ready": False}))
