#!/usr/bin/env python3
"""Match contractors to parcels using fail-closed, evidence-aware hierarchy.

Order:
1) geometry intersection using ONS postcode latitude/longitude when available
2) authority + postcode proxy
3) region fallback with REVIEW / low score
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd
import psycopg
from pandas.errors import EmptyDataError
from psycopg.rows import dict_row

from contractor_env import load_contractor_env, redact_secrets

DEFAULT_STORAGE_ROOT = r"E:\AAYS_DATA\contractor"
PROJECT_ROOT = Path(__file__).resolve().parents[1]


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def write_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def read_csv_or_empty(path: Path) -> pd.DataFrame:
    try:
        return pd.read_csv(path, dtype=object)
    except EmptyDataError:
        return pd.DataFrame()


def status(storage_root: Path, status_type: str, reason: str, details: Optional[Dict[str, Any]] = None) -> Path:
    path = storage_root / "raw" / "status" / f"{status_type}_parcel_match.json"
    write_json(path, {"status": status_type, "source_name": "contractor parcel matcher", "reason": reason, "details": details or {}, "fetched_at": utc_now(), "license_name": None})
    return path


def norm_postcode(pc: Any) -> Optional[str]:
    if pc is None or pd.isna(pc):
        return None
    s = re.sub(r"\s+", "", str(pc).upper())
    return s or None


def find_ons_lookup(storage_root: Path, explicit: Optional[str]) -> Optional[Path]:
    if explicit:
        p = Path(explicit)
        return p if p.exists() else None
    base = storage_root / "raw" / "ons_lookup"
    if not base.exists():
        return None
    candidates = sorted(list(base.rglob("*.csv")) + list(base.rglob("*.CSV")), key=lambda p: p.stat().st_mtime, reverse=True)
    return candidates[0] if candidates else None


def load_postcode_lookup(storage_root: Path, explicit: Optional[str]) -> Dict[str, Dict[str, Any]]:
    path = find_ons_lookup(storage_root, explicit)
    if not path:
        return {}
    # ONS files vary by epoch; use flexible column detection.
    df = pd.read_csv(path, dtype=object, low_memory=False)
    lower = {c.lower(): c for c in df.columns}
    pc_col = next((lower[c] for c in ["pcds", "pcd", "postcode", "postcode_1"] if c in lower), None)
    lat_col = next((lower[c] for c in ["lat", "latitude"] if c in lower), None)
    lon_col = next((lower[c] for c in ["long", "lon", "longitude"] if c in lower), None)
    auth_col = next((lower[c] for c in ["oslaua", "laua", "ladcd", "ladnm", "local_authority"] if c in lower), None)
    region_col = next((lower[c] for c in ["rgn", "rgnnm", "region"] if c in lower), None)
    if not pc_col:
        return {}
    lookup: Dict[str, Dict[str, Any]] = {}
    for row in df.to_dict(orient="records"):
        pc = norm_postcode(row.get(pc_col))
        if not pc:
            continue
        def num(v: Any) -> Optional[float]:
            try:
                if v is None or pd.isna(v) or v == "":
                    return None
                return float(v)
            except Exception:
                return None
        lookup[pc] = {
            "lat": num(row.get(lat_col)) if lat_col else None,
            "lon": num(row.get(lon_col)) if lon_col else None,
            "authority": row.get(auth_col) if auth_col else None,
            "region": row.get(region_col) if region_col else None,
            "source_file": str(path),
        }
    return lookup


def table_exists(conn: psycopg.Connection, table_name: str) -> bool:
    schema, name = split_table(table_name)
    with conn.cursor() as cur:
        cur.execute("select exists(select 1 from information_schema.tables where table_schema=%s and table_name=%s)", (schema, name))
        return bool(cur.fetchone()["exists"])


def split_table(table_name: str) -> Tuple[str, str]:
    if "." in table_name:
        schema, name = table_name.split(".", 1)
    else:
        schema, name = "public", table_name
    if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", schema) or not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", name):
        raise ValueError("Invalid table name")
    return schema, name


def get_columns(conn: psycopg.Connection, table_name: str) -> List[str]:
    schema, name = split_table(table_name)
    with conn.cursor() as cur:
        cur.execute("select column_name from information_schema.columns where table_schema=%s and table_name=%s", (schema, name))
        return [r["column_name"] for r in cur.fetchall()]


def geometry_match(conn: psycopg.Connection, parcel_table: str, parcel_id_col: str, geom_col: str, lon: float, lat: float, limit: int) -> List[str]:
    schema, table = split_table(parcel_table)
    sql = f"""
    select {parcel_id_col}::text as parcel_id
    from {schema}.{table}
    where ST_Intersects(
      {geom_col},
      ST_Transform(ST_SetSRID(ST_Point(%s, %s), 4326), ST_SRID({geom_col}))
    )
    limit %s
    """
    with conn.cursor() as cur:
        cur.execute(sql, (lon, lat, limit))
        return [r["parcel_id"] for r in cur.fetchall()]


def proxy_match(conn: psycopg.Connection, parcel_table: str, parcel_id_col: str, postcode_col: Optional[str], authority_col: Optional[str], postcode: Optional[str], authority: Optional[str], limit: int) -> List[str]:
    if not postcode_col and not authority_col:
        return []
    schema, table = split_table(parcel_table)
    clauses = []
    params: List[Any] = []
    if postcode_col and postcode:
        clauses.append(f"regexp_replace(upper({postcode_col}::text), '\\s+', '', 'g') = %s")
        params.append(postcode)
    if authority_col and authority:
        clauses.append(f"upper({authority_col}::text) = upper(%s::text)")
        params.append(authority)
    if not clauses:
        return []
    params.append(limit)
    sql = f"select {parcel_id_col}::text as parcel_id from {schema}.{table} where {' and '.join(clauses)} limit %s"
    with conn.cursor() as cur:
        cur.execute(sql, params)
        return [r["parcel_id"] for r in cur.fetchall()]


def region_fallback(conn: psycopg.Connection, parcel_table: str, parcel_id_col: str, region_col: Optional[str], region: Optional[str], limit: int) -> List[str]:
    if not region_col or not region:
        return []
    schema, table = split_table(parcel_table)
    sql = f"select {parcel_id_col}::text as parcel_id from {schema}.{table} where upper({region_col}::text) = upper(%s::text) limit %s"
    with conn.cursor() as cur:
        cur.execute(sql, (region, limit))
        return [r["parcel_id"] for r in cur.fetchall()]


def select_col(columns: List[str], candidates: List[str]) -> Optional[str]:
    lower = {c.lower(): c for c in columns}
    return next((lower[c.lower()] for c in candidates if c.lower() in lower), None)


def contact_readiness(row: Dict[str, Any]) -> str:
    if str(row.get("do_not_contact")).lower() in {"true", "1", "yes"} or int(float(row.get("legal_contact_score") or 0)) < 50:
        return "DO_NOT_CONTACT"
    return str(row.get("contact_status") or "READY")


def ensure_match_table(conn: psycopg.Connection) -> None:
    with conn.cursor() as cur:
        cur.execute("""
        create table if not exists contractor_parcel_match (
          parcel_id text,
          contractor_id text,
          match_method text,
          match_score integer,
          region_activity_label text,
          contact_readiness text,
          reason text,
          matched_at timestamptz,
          evidence_source_name text,
          evidence_source_url text,
          evidence_record_id text,
          loaded_at timestamptz not null default now(),
          primary key(parcel_id, contractor_id, match_method)
        )
        """)
    conn.commit()


def upsert_matches(conn: psycopg.Connection, matches: List[Dict[str, Any]]) -> None:
    ensure_match_table(conn)
    sql = """
    insert into contractor_parcel_match
    (parcel_id, contractor_id, match_method, match_score, region_activity_label, contact_readiness, reason, matched_at, evidence_source_name, evidence_source_url, evidence_record_id)
    values (%(parcel_id)s, %(contractor_id)s, %(match_method)s, %(match_score)s, %(region_activity_label)s, %(contact_readiness)s, %(reason)s, %(matched_at)s, %(evidence_source_name)s, %(evidence_source_url)s, %(evidence_record_id)s)
    on conflict(parcel_id, contractor_id, match_method) do update set
      match_score=excluded.match_score,
      region_activity_label=excluded.region_activity_label,
      contact_readiness=excluded.contact_readiness,
      reason=excluded.reason,
      matched_at=excluded.matched_at,
      evidence_source_name=excluded.evidence_source_name,
      evidence_source_url=excluded.evidence_source_url,
      evidence_record_id=excluded.evidence_record_id,
      loaded_at=now()
    """
    with conn.cursor() as cur:
        cur.executemany(sql, matches)
    conn.commit()


def main() -> int:
    parser = argparse.ArgumentParser(description="Match contractors to parcels with geometry/proxy/fallback hierarchy.")
    parser.add_argument("--storage-root", default=DEFAULT_STORAGE_ROOT)
    parser.add_argument("--database-url", default=None)
    parser.add_argument("--project-root", default=str(PROJECT_ROOT))
    parser.add_argument("--parcel-table", default="parcels")
    parser.add_argument("--parcel-id-col", default=None)
    parser.add_argument("--geom-col", default=None)
    parser.add_argument("--postcode-col", default=None)
    parser.add_argument("--authority-col", default=None)
    parser.add_argument("--region-col", default=None)
    parser.add_argument("--ons-postcode-csv", default=None)
    parser.add_argument("--limit-per-contractor", type=int, default=10)
    args = parser.parse_args()
    env_info = load_contractor_env(Path(args.project_root))
    database_url = args.database_url or os.environ.get("CONTRACTOR_DATABASE_URL") or env_info.get("database_url")

    storage_root = Path(args.storage_root)
    curated = storage_root / "curated"
    contractors_file = curated / "contractor_score_snapshot.csv"
    if not contractors_file.exists():
        path = status(storage_root, "blocked_by_missing_input", f"Missing curated contractor file: {contractors_file}")
        print(f"FAIL-CLOSED: {path}", file=sys.stderr)
        return 2
    if not database_url:
        path = status(
            storage_root,
            "blocked_by_missing_credential",
            "No database credentials found in process environment, .env.local, .env, or bridge local secrets.",
            env_info["report"],
        )
        print(f"FAIL-CLOSED: {path}", file=sys.stderr)
        return 3

    postcode_lookup = load_postcode_lookup(storage_root, args.ons_postcode_csv)
    contractors = read_csv_or_empty(contractors_file).to_dict(orient="records")
    matches: List[Dict[str, Any]] = []
    try:
        conn_ctx = psycopg.connect(database_url, row_factory=dict_row)
    except Exception as exc:
        path = status(storage_root, "blocked_by_db_connection", redact_secrets(exc, env_info), env_info["report"])
        print(f"FAIL-CLOSED: {path}", file=sys.stderr)
        return 6
    with conn_ctx as conn:
        if not table_exists(conn, args.parcel_table):
            path = status(storage_root, "blocked_by_missing_input", f"Parcel table not found: {args.parcel_table}")
            print(f"FAIL-CLOSED: {path}", file=sys.stderr)
            return 4
        cols = get_columns(conn, args.parcel_table)
        parcel_id_col = args.parcel_id_col or select_col(cols, ["parcel_id", "id", "gid"])
        geom_col = args.geom_col or select_col(cols, ["geom", "geometry", "wkb_geometry"])
        postcode_col = args.postcode_col or select_col(cols, ["postcode", "postal_code", "pcd", "pcds"])
        authority_col = args.authority_col or select_col(cols, ["authority", "local_authority", "ladnm", "ladcd", "oslaua"])
        region_col = args.region_col or select_col(cols, ["region", "rgn", "rgnnm"])
        if not parcel_id_col:
            path = status(storage_root, "blocked_by_missing_input", "Parcel ID column could not be detected; pass --parcel-id-col.", {"columns": cols})
            print(f"FAIL-CLOSED: {path}", file=sys.stderr)
            return 5

        for row in contractors:
            contractor_id = row.get("contractor_id")
            if not contractor_id:
                continue
            pc = norm_postcode(row.get("postal_code"))
            lookup = postcode_lookup.get(pc or "", {})
            authority = lookup.get("authority") or row.get("locality")
            region = lookup.get("region") or row.get("region")
            ready = contact_readiness(row)
            base = {
                "contractor_id": contractor_id,
                "region_activity_label": row.get("activity_density_label"),
                "contact_readiness": ready,
                "matched_at": utc_now(),
                "evidence_source_name": "ONS lookup products" if lookup else row.get("company_license_name"),
                "evidence_source_url": row.get("company_source_url"),
                "evidence_record_id": pc,
            }
            parcel_ids: List[str] = []
            if geom_col and lookup.get("lon") is not None and lookup.get("lat") is not None:
                parcel_ids = geometry_match(conn, args.parcel_table, parcel_id_col, geom_col, float(lookup["lon"]), float(lookup["lat"]), args.limit_per_contractor)
                for pid in parcel_ids:
                    matches.append({**base, "parcel_id": pid, "match_method": "geometry_intersection", "match_score": 90, "reason": "ONS postcode coordinate intersects parcel geometry."})
            if not parcel_ids:
                parcel_ids = proxy_match(conn, args.parcel_table, parcel_id_col, postcode_col, authority_col, pc, authority, args.limit_per_contractor)
                for pid in parcel_ids:
                    matches.append({**base, "parcel_id": pid, "match_method": "authority_postcode_proxy", "match_score": 65, "reason": "Parcel matched by available postcode and/or authority columns; review before operational use."})
            if not parcel_ids:
                parcel_ids = region_fallback(conn, args.parcel_table, parcel_id_col, region_col, region, min(args.limit_per_contractor, 3))
                for pid in parcel_ids:
                    matches.append({**base, "parcel_id": pid, "match_method": "region_fallback_review", "match_score": 35, "reason": "Low-confidence region fallback. REVIEW required."})
        if matches:
            upsert_matches(conn, matches)

    out_csv = curated / "contractor_parcel_match.csv"
    match_frame = pd.DataFrame(matches)
    if matches:
        match_frame = match_frame.drop_duplicates(subset=["parcel_id", "contractor_id", "match_method"])
    match_frame.to_csv(out_csv, index=False, encoding="utf-8")
    manifest = {"match_count": len(matches), "output": str(out_csv), "matched_at": utc_now(), "hierarchy": ["geometry_intersection", "authority_postcode_proxy", "region_fallback_review"]}
    write_json(storage_root / "manifests" / "parcel_match_manifest.json", manifest)
    print(json.dumps(manifest, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
