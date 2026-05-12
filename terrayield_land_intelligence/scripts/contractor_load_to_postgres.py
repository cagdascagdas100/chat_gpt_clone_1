#!/usr/bin/env python3
"""Load curated contractor intelligence snapshots to PostgreSQL/PostGIS."""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

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


def status(storage_root: Path, status_type: str, reason: str, details: Optional[Dict[str, Any]] = None) -> Path:
    path = storage_root / "raw" / "status" / f"{status_type}_postgres.json"
    write_json(path, {"status": status_type, "source_name": "PostgreSQL loader", "reason": reason, "details": details or {}, "fetched_at": utc_now(), "license_name": None})
    return path


def clean_nan(value: Any) -> Any:
    if pd.isna(value):
        return None
    if isinstance(value, float) and value.is_integer():
        return int(value)
    return value


def read_csv_or_empty(path: Path) -> pd.DataFrame:
    try:
        return pd.read_csv(path, dtype=object)
    except EmptyDataError:
        return pd.DataFrame()


def create_schema(conn: psycopg.Connection) -> None:
    ddl = """
    create table if not exists contractor_company (
      contractor_id text primary key,
      company_number text,
      company_name text,
      normalized_name text,
      company_status text,
      company_type text,
      date_of_creation text,
      sic_codes text,
      is_contractor_sic boolean,
      registered_office_address text,
      postal_code text,
      locality text,
      region text,
      country text,
      project_count integer,
      buyer_diversity_count integer,
      total_award_value numeric,
      award_value_currency_evidence text,
      source_count integer,
      reliability_score integer,
      data_confidence_score integer,
      legal_contact_score integer,
      quality_band text,
      activity_density_label text,
      do_not_contact boolean,
      contact_status text,
      company_source_url text,
      last_company_fetch_at text,
      company_license_name text,
      scored_at timestamptz,
      loaded_at timestamptz not null default now()
    );
    create unique index if not exists idx_contractor_company_company_number on contractor_company(company_number) where company_number is not null;

    create table if not exists contractor_project (
      project_id text primary key,
      contractor_id text references contractor_company(contractor_id) on delete set null,
      source_name text,
      source_url text,
      source_record_id text,
      ocid text,
      release_id text,
      release_date text,
      tag text,
      tender_title text,
      tender_description text,
      buyer_name text,
      buyer_normalized_name text,
      supplier_name text,
      award_id text,
      award_status text,
      award_amount numeric,
      award_currency text,
      procurement_method text,
      main_procurement_category text,
      fetched_at text,
      license_name text,
      loaded_at timestamptz not null default now()
    );

    create table if not exists contractor_provenance_evidence (
      evidence_id bigserial primary key,
      contractor_id text,
      source_name text not null,
      source_record_id text,
      source_url text,
      field_name text,
      field_value text,
      observed_at text,
      fetched_at text,
      license_name text,
      confidence_score integer,
      freshness_days integer,
      is_current boolean,
      raw_payload_path text,
      notes text,
      loaded_at timestamptz not null default now(),
      unique(contractor_id, source_name, source_record_id, field_name, field_value)
    );

    create table if not exists contractor_parcel_match (
      parcel_id text,
      contractor_id text references contractor_company(contractor_id) on delete cascade,
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
    );
    """
    with conn.cursor() as cur:
        cur.execute(ddl)
    conn.commit()


def upsert_company(conn: psycopg.Connection, row: Dict[str, Any]) -> None:
    cols = [
        "contractor_id", "company_number", "company_name", "normalized_name", "company_status", "company_type", "date_of_creation", "sic_codes", "is_contractor_sic", "registered_office_address", "postal_code", "locality", "region", "country", "project_count", "buyer_diversity_count", "total_award_value", "award_value_currency_evidence", "source_count", "reliability_score", "data_confidence_score", "legal_contact_score", "quality_band", "activity_density_label", "do_not_contact", "contact_status", "company_source_url", "last_company_fetch_at", "company_license_name", "scored_at"
    ]
    values = [clean_nan(row.get(c)) for c in cols]
    placeholders = ", ".join(["%s"] * len(cols))
    assignments = ", ".join([f"{c}=excluded.{c}" for c in cols if c != "contractor_id"])
    sql = f"insert into contractor_company ({', '.join(cols)}) values ({placeholders}) on conflict (contractor_id) do update set {assignments}, loaded_at=now()"
    with conn.cursor() as cur:
        cur.execute(sql, values)


def upsert_project(conn: psycopg.Connection, row: Dict[str, Any]) -> None:
    cols = [
        "project_id", "contractor_id", "source_name", "source_url", "source_record_id", "ocid", "release_id", "release_date", "tag", "tender_title", "tender_description", "buyer_name", "buyer_normalized_name", "supplier_name", "award_id", "award_status", "award_amount", "award_currency", "procurement_method", "main_procurement_category", "fetched_at", "license_name"
    ]
    values = [clean_nan(row.get(c)) for c in cols]
    placeholders = ", ".join(["%s"] * len(cols))
    assignments = ", ".join([f"{c}=excluded.{c}" for c in cols if c != "project_id"])
    sql = f"insert into contractor_project ({', '.join(cols)}) values ({placeholders}) on conflict (project_id) do update set {assignments}, loaded_at=now()"
    with conn.cursor() as cur:
        cur.execute(sql, values)


def insert_evidence(conn: psycopg.Connection, row: Dict[str, Any]) -> None:
    cols = ["contractor_id", "source_name", "source_record_id", "source_url", "field_name", "field_value", "observed_at", "fetched_at", "license_name", "confidence_score", "freshness_days", "is_current", "raw_payload_path", "notes"]
    values = [clean_nan(row.get(c)) for c in cols]
    placeholders = ", ".join(["%s"] * len(cols))
    sql = f"insert into contractor_provenance_evidence ({', '.join(cols)}) values ({placeholders}) on conflict do nothing"
    with conn.cursor() as cur:
        cur.execute(sql, values)


def main() -> int:
    parser = argparse.ArgumentParser(description="Load contractor curated snapshots to PostgreSQL/PostGIS.")
    parser.add_argument("--storage-root", default=DEFAULT_STORAGE_ROOT)
    parser.add_argument("--database-url", default=None)
    parser.add_argument("--project-root", default=str(PROJECT_ROOT))
    args = parser.parse_args()
    env_info = load_contractor_env(Path(args.project_root))
    database_url = args.database_url or os.environ.get("CONTRACTOR_DATABASE_URL") or env_info.get("database_url")
    storage_root = Path(args.storage_root)
    curated = storage_root / "curated"
    if not database_url:
        path = status(
            storage_root,
            "blocked_by_missing_credential",
            "No database credentials found in process environment, .env.local, .env, or bridge local secrets.",
            env_info["report"],
        )
        print(f"FAIL-CLOSED: missing database URL. Status written: {path}", file=sys.stderr)
        return 2
    company_csv = curated / "contractor_score_snapshot.csv"
    project_csv = curated / "contractor_project_snapshot.csv"
    evidence_csv = curated / "provenance_evidence.csv"
    if not company_csv.exists():
        path = status(storage_root, "blocked_by_missing_input", f"Missing curated company file: {company_csv}")
        print(f"FAIL-CLOSED: missing curated input. Status written: {path}", file=sys.stderr)
        return 3

    companies = read_csv_or_empty(company_csv)
    projects = read_csv_or_empty(project_csv) if project_csv.exists() else pd.DataFrame()
    evidence = read_csv_or_empty(evidence_csv) if evidence_csv.exists() else pd.DataFrame()
    try:
        with psycopg.connect(database_url, row_factory=dict_row) as conn:
            create_schema(conn)
            for row in companies.to_dict(orient="records"):
                upsert_company(conn, row)
            for row in projects.to_dict(orient="records"):
                upsert_project(conn, row)
            for row in evidence.to_dict(orient="records"):
                insert_evidence(conn, row)
            conn.commit()
    except Exception as exc:
        message = redact_secrets(exc, env_info)
        path = status(storage_root, "blocked_by_db_connection", message, env_info["report"])
        print(f"FAIL-CLOSED: database connection failed. Status written: {path}", file=sys.stderr)
        return 4
    manifest = {"loaded_companies": len(companies), "loaded_projects": len(projects), "loaded_evidence_rows": len(evidence), "loaded_at": utc_now()}
    write_json(storage_root / "manifests" / "postgres_load_manifest.json", manifest)
    print(json.dumps(manifest, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
