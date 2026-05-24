from __future__ import annotations

import csv
import sys

def _raise_csv_field_limit() -> None:
    limit = sys.maxsize
    while True:
        try:
            csv.field_size_limit(limit)
            return
        except OverflowError:
            limit = int(limit / 10)

_raise_csv_field_limit()
from dataclasses import dataclass
from pathlib import Path
from typing import Any


REQUIRED_FILES: dict[str, str] = {
    "agents": "estate_agent_verified_final.csv",
    "evidence": "estate_agent_evidence_sources_final.csv",
    "coverage": "estate_agent_coverage_groups_final.csv",
    "join": "terrayield_parcel_group_join_final.csv",
}

OPTIONAL_FILES: dict[str, str] = {
    "final_audit_csv": "estate023_final_acceptance_audit.csv",
    "final_audit_report_md": "estate023_final_acceptance_audit.report.md",
    "final_xlsx": "TerraYield_Emlakci_Parsel_Eslesme_FINAL.xlsx",
}


@dataclass
class EstateDataset:
    available: bool
    root: Path | None
    files: dict[str, Path]
    missing_files: list[str]
    join_rows: list[dict[str, Any]]
    coverage_rows: list[dict[str, Any]]
    agents_rows: list[dict[str, Any]]
    evidence_rows: list[dict[str, Any]]


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(str(value).strip())
    except (TypeError, ValueError):
        return default


def _safe_bool(value: Any) -> bool:
    return str(value).strip().lower() in {"true", "1", "yes"}


def _first_non_empty(row: dict[str, Any], keys: list[str]) -> str:
    for key in keys:
        value = row.get(key)
        if value is None:
            continue
        text = str(value).strip()
        if text:
            return text
    return ""


def _normalize_lookup_key(raw: Any) -> str:
    return str(raw or "").strip().lower()


def _derive_agent_id(candidate_id: str) -> str:
    candidate_id_clean = str(candidate_id or "").strip()
    if not candidate_id_clean:
        return ""
    return f"EA-REVIEW-{candidate_id_clean}"


def _read_csv(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as fh:
        return [dict(row) for row in csv.DictReader(fh)]


def _candidate_roots(settings: Any) -> list[Path]:
    roots: list[Path] = []
    explicit_root = getattr(settings, "estate_agent_final_root", None)
    if explicit_root:
        roots.append(Path(explicit_root))
    roots.append(Path(r"E:\AAYS_DATA\estate_agents"))

    explicit_fallbacks = getattr(settings, "estate_agent_fallback_roots", "")
    if explicit_fallbacks:
        for item in str(explicit_fallbacks).split(","):
            clean = item.strip()
            if clean:
                roots.append(Path(clean))
    roots.append(Path(r"C:\AAYS_GITHUB_BRIDGE_CLEAN2\ai-results"))

    package_expected_root = (
        Path(__file__).resolve().parents[2]
        / "docs"
        / "chatgpt_handoff"
        / "estate_integration_package_20260524_extracted"
        / "codex_estate_integration_package"
        / "expected_local_final_files"
    )
    roots.append(package_expected_root)

    unique_roots: list[Path] = []
    seen: set[str] = set()
    for root in roots:
        key = str(root).lower()
        if key in seen:
            continue
        seen.add(key)
        unique_roots.append(root)
    return unique_roots


def _resolve_dataset_root(settings: Any) -> tuple[Path | None, dict[str, Path], list[str]]:
    for root in _candidate_roots(settings):
        file_map = {name: (root / filename) for name, filename in REQUIRED_FILES.items()}
        missing = [name for name, path in file_map.items() if not path.exists()]
        if not missing:
            with_optional = dict(file_map)
            for name, filename in OPTIONAL_FILES.items():
                with_optional[name] = root / filename
            return root, with_optional, []
    first = _candidate_roots(settings)[0] if _candidate_roots(settings) else None
    missing_names = list(REQUIRED_FILES.keys())
    return None, {}, missing_names if first is not None else missing_names


def load_estate_dataset(settings: Any) -> EstateDataset:
    root, files, missing = _resolve_dataset_root(settings)
    if root is None:
        return EstateDataset(
            available=False,
            root=None,
            files={},
            missing_files=missing,
            join_rows=[],
            coverage_rows=[],
            agents_rows=[],
            evidence_rows=[],
        )

    return EstateDataset(
        available=True,
        root=root,
        files=files,
        missing_files=[],
        join_rows=_read_csv(files["join"]),
        coverage_rows=_read_csv(files["coverage"]),
        agents_rows=_read_csv(files["agents"]),
        evidence_rows=_read_csv(files["evidence"]),
    )


def _group_coverage(coverage_rows: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for row in coverage_rows:
        group_id = str(row.get("parcel_group_id") or "").strip()
        if not group_id:
            continue
        grouped.setdefault(group_id, []).append(row)
    return grouped


def _build_join_lookup(join_rows: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    lookup: dict[str, list[dict[str, Any]]] = {}
    for row in join_rows:
        raw_id = row.get("program_parcel_id")
        key = _normalize_lookup_key(raw_id)
        if not key:
            continue
        lookup.setdefault(key, []).append(row)
        as_float = _safe_float(raw_id, default=-1.0)
        if as_float >= 0 and as_float.is_integer():
            int_key = str(int(as_float))
            lookup.setdefault(int_key, []).append(row)
    return lookup


def _build_agent_maps(agents_rows: list[dict[str, Any]]) -> tuple[dict[str, dict[str, Any]], dict[str, dict[str, Any]]]:
    by_agent_id: dict[str, dict[str, Any]] = {}
    by_candidate_id: dict[str, dict[str, Any]] = {}
    for raw_row in agents_rows:
        row = dict(raw_row)
        candidate_id = str(row.get("candidate_id") or "").strip()
        row_agent_id = str(row.get("agent_id") or "").strip() or _derive_agent_id(candidate_id)
        if row_agent_id:
            row["agent_id"] = row_agent_id
            by_agent_id[row_agent_id] = row
        if candidate_id:
            row["candidate_id"] = candidate_id
            by_candidate_id[candidate_id] = row
    return by_agent_id, by_candidate_id


def _build_evidence_maps(
    evidence_rows: list[dict[str, Any]],
) -> tuple[dict[str, list[dict[str, Any]]], dict[str, list[dict[str, Any]]]]:
    by_agent_id: dict[str, list[dict[str, Any]]] = {}
    by_candidate_id: dict[str, list[dict[str, Any]]] = {}
    for raw_row in evidence_rows:
        row = dict(raw_row)
        candidate_id = str(row.get("candidate_id") or "").strip()
        row_agent_id = str(row.get("agent_id") or "").strip() or _derive_agent_id(candidate_id)
        if row_agent_id:
            by_agent_id.setdefault(row_agent_id, []).append(row)
        if candidate_id:
            by_candidate_id.setdefault(candidate_id, []).append(row)
    return by_agent_id, by_candidate_id


def _read_audit_csv(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    values: dict[str, Any] = {}
    try:
        with path.open("r", encoding="utf-8-sig", newline="") as fh:
            for row in csv.DictReader(fh):
                key = str(row.get("check") or "").strip()
                value = row.get("value")
                if key:
                    values[key] = value
    except OSError:
        return {}
    return values


def _read_audit_md(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    values: dict[str, Any] = {}
    try:
        lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
    except OSError:
        return {}
    for line in lines:
        if "=" not in line:
            continue
        left, right = line.split("=", 1)
        key = left.strip()
        value = right.strip()
        if key:
            values[key] = value
    return values


def extract_audit_summary(dataset: EstateDataset) -> dict[str, Any]:
    csv_values = _read_audit_csv(dataset.files.get("final_audit_csv", Path()))
    md_values = _read_audit_md(dataset.files.get("final_audit_report_md", Path()))

    merged: dict[str, Any] = {}
    merged.update(md_values)
    merged.update(csv_values)

    def _flag(name: str, default: bool) -> bool:
        raw = merged.get(name)
        if raw is None:
            return default
        return str(raw).strip().lower() == "true"

    return {
        "DB_WRITE": _flag("DB_WRITE", False),
        "PRODUCTION_DEPLOY": _flag("PRODUCTION_DEPLOY", False),
        "FAKE_DATA": _flag("FAKE_DATA", False),
        "FINAL_ACCEPTANCE": _flag("FINAL_ACCEPTANCE", False),
        "raw": merged,
    }


def validate_dataset(dataset: EstateDataset) -> dict[str, Any]:
    if not dataset.available:
        return {
            "dataset_available": False,
            "missing_files": dataset.missing_files,
            "blockers": ["required_files_missing"],
            "row_counts": {"agents": 0, "evidence": 0, "coverage": 0, "join": 0},
            "audit": {"DB_WRITE": False, "PRODUCTION_DEPLOY": False, "FAKE_DATA": False, "FINAL_ACCEPTANCE": False},
        }

    row_counts = {
        "agents": len(dataset.agents_rows),
        "evidence": len(dataset.evidence_rows),
        "coverage": len(dataset.coverage_rows),
        "join": len(dataset.join_rows),
    }
    blockers: list[str] = []
    for key, count in row_counts.items():
        if count <= 0:
            blockers.append(f"{key}_rows_zero")

    by_agent_id, by_candidate_id = _build_agent_maps(dataset.agents_rows)
    coverage_agent_ids = {
        str(row.get("agent_id") or "").strip()
        for row in dataset.coverage_rows
        if str(row.get("agent_id") or "").strip()
    }
    coverage_candidate_ids = {
        str(row.get("candidate_id") or "").strip()
        for row in dataset.coverage_rows
        if str(row.get("candidate_id") or "").strip()
    }
    missing_coverage_agent_ids = sorted([value for value in coverage_agent_ids if value not in by_agent_id])
    missing_coverage_candidate_ids = sorted([value for value in coverage_candidate_ids if value not in by_candidate_id])

    if missing_coverage_agent_ids and missing_coverage_candidate_ids:
        blockers.append("coverage_not_joinable_to_verified_agents")

    coverage_group_ids = {
        str(row.get("parcel_group_id") or "").strip()
        for row in dataset.coverage_rows
        if str(row.get("parcel_group_id") or "").strip()
    }
    join_group_ids = {
        str(row.get("parcel_group_id") or "").strip()
        for row in dataset.join_rows
        if str(row.get("parcel_group_id") or "").strip()
    }
    missing_group_ids = sorted([value for value in coverage_group_ids if value not in join_group_ids])
    if missing_group_ids:
        blockers.append("coverage_group_ids_missing_in_join")

    final_xlsx = dataset.files.get("final_xlsx")
    xlsx_exists = bool(final_xlsx and final_xlsx.exists())
    xlsx_size = final_xlsx.stat().st_size if xlsx_exists and final_xlsx is not None else 0
    if not xlsx_exists:
        blockers.append("final_xlsx_missing")
    if xlsx_size < 1000:
        blockers.append("final_xlsx_too_small")

    audit = extract_audit_summary(dataset)
    return {
        "dataset_available": True,
        "dataset_root": str(dataset.root),
        "missing_files": [],
        "row_counts": row_counts,
        "missing_coverage_agent_ids": missing_coverage_agent_ids,
        "missing_coverage_candidate_ids": missing_coverage_candidate_ids,
        "missing_coverage_group_ids": missing_group_ids,
        "xlsx_exists": xlsx_exists,
        "xlsx_size": xlsx_size,
        "blockers": blockers,
        "FINAL_ACCEPTANCE": len(blockers) == 0,
        "audit": audit,
    }


def lookup_agents_by_parcel(dataset: EstateDataset, program_parcel_id: str, limit: int = 10) -> dict[str, Any]:
    normalized = _normalize_lookup_key(program_parcel_id)
    if not dataset.available:
        return {
            "dataset_available": False,
            "program_parcel_id": str(program_parcel_id),
            "parcel_group_ids": [],
            "agents": [],
            "missing_files": dataset.missing_files,
            "source_files": {},
            "audit": {"DB_WRITE": False, "PRODUCTION_DEPLOY": False, "FAKE_DATA": False, "FINAL_ACCEPTANCE": False},
        }

    join_lookup = _build_join_lookup(dataset.join_rows)
    join_rows = join_lookup.get(normalized, [])
    parcel_group_ids = sorted(
        {
            str(row.get("parcel_group_id") or "").strip()
            for row in join_rows
            if str(row.get("parcel_group_id") or "").strip()
        }
    )
    coverage_by_group = _group_coverage(dataset.coverage_rows)
    agents_by_agent_id, agents_by_candidate_id = _build_agent_maps(dataset.agents_rows)
    evidence_by_agent_id, evidence_by_candidate_id = _build_evidence_maps(dataset.evidence_rows)

    built_agents: list[dict[str, Any]] = []
    seen_keys: set[str] = set()
    for group_id in parcel_group_ids:
        for coverage_row in coverage_by_group.get(group_id, []):
            coverage_agent_id = str(coverage_row.get("agent_id") or "").strip()
            coverage_candidate_id = str(coverage_row.get("candidate_id") or "").strip()

            agent_row = agents_by_agent_id.get(coverage_agent_id)
            if agent_row is None and coverage_candidate_id:
                agent_row = agents_by_candidate_id.get(coverage_candidate_id)
            if agent_row is None and coverage_agent_id.startswith("EA-REVIEW-"):
                suffix = coverage_agent_id.replace("EA-REVIEW-", "", 1)
                agent_row = agents_by_candidate_id.get(suffix)
            if agent_row is None:
                agent_row = {}

            candidate_id = _first_non_empty(
                {
                    "candidate_id": coverage_candidate_id,
                    "agent_candidate_id": agent_row.get("candidate_id"),
                },
                ["candidate_id", "agent_candidate_id"],
            )
            agent_id = coverage_agent_id or _first_non_empty(agent_row, ["agent_id"]) or _derive_agent_id(candidate_id)
            if not agent_id:
                continue
            dedupe_key = f"{group_id}:{agent_id}"
            if dedupe_key in seen_keys:
                continue
            seen_keys.add(dedupe_key)

            trust_score_10 = _safe_float(
                _first_non_empty(agent_row, ["trust_score_10", "reliability_score"]),
                default=0.0,
            )
            if trust_score_10 <= 0:
                trust_score_10 = _safe_float(
                    _first_non_empty(agent_row, ["overall_data_truth_score_4", "truth_score_source_4"]),
                    default=_safe_float(coverage_row.get("coverage_truth_score_4")),
                ) * 2.5

            overall_truth_score_4 = _safe_float(
                _first_non_empty(agent_row, ["overall_data_truth_score_4", "truth_score_source_4"]),
                default=_safe_float(coverage_row.get("coverage_truth_score_4")),
            )
            legal_contact_score = _safe_float(_first_non_empty(agent_row, ["legal_contact_score"]), default=0.0)
            do_not_contact = _safe_bool(
                _first_non_empty(agent_row, ["do_not_contact", "contact_suppressed", "contact_blocked"])
            )

            contact_status = _first_non_empty(agent_row, ["contact_status"]).upper() or "READY"
            if do_not_contact:
                contact_status = "DO_NOT_CONTACT"
            contact_allowed = not do_not_contact and contact_status != "DO_NOT_CONTACT"

            evidence_rows = evidence_by_agent_id.get(agent_id, [])
            if not evidence_rows and candidate_id:
                evidence_rows = evidence_by_candidate_id.get(candidate_id, [])
            evidence_payload = [
                {
                    "source_file": row.get("source_file"),
                    "source_type": row.get("source_type"),
                    "source_url": row.get("source_url"),
                    "truth_score_source_4": row.get("truth_score_source_4"),
                    "candidate_text_excerpt": row.get("candidate_text_excerpt"),
                }
                for row in evidence_rows
            ]

            company_name = _first_non_empty(
                agent_row,
                ["company_name", "agent_or_branch_name", "branch_name", "agent_name", "candidate_name", "candidate_id"],
            ) or agent_id
            row_source_url = _first_non_empty(
                agent_row,
                ["website_url", "web_url", "url", "source_url"],
            ) or str(coverage_row.get("source_url") or "")

            built_agents.append(
                {
                    "agent_id": agent_id,
                    "candidate_id": candidate_id or None,
                    "company_name": company_name,
                    "agent_or_branch_name": _first_non_empty(agent_row, ["agent_or_branch_name", "branch_name", "agent_name"])
                    or None,
                    "phone": _first_non_empty(agent_row, ["phone", "telephone", "contact_phone"]) or None,
                    "email": _first_non_empty(agent_row, ["email", "contact_email"]) or None,
                    "website_url": _first_non_empty(agent_row, ["website_url", "web_url", "url"]) or None,
                    "office_address": _first_non_empty(
                        agent_row,
                        ["office_address", "registered_office_address", "shop_address", "address"],
                    )
                    or None,
                    "postcode": _first_non_empty(agent_row, ["postcode", "postal_code"]) or None,
                    "locality": _first_non_empty(agent_row, ["locality", "city", "town", "district"]) or None,
                    "region": _first_non_empty(agent_row, ["region", "service_region", "local_authority"]) or None,
                    "trust_score_10": round(trust_score_10, 3),
                    "overall_data_truth_score_4": round(overall_truth_score_4, 3),
                    "coverage_method": coverage_row.get("coverage_method"),
                    "coverage_truth_score_4": coverage_row.get("coverage_truth_score_4"),
                    "parcel_group_id": group_id,
                    "contact_status": contact_status,
                    "do_not_contact": do_not_contact,
                    "contact_allowed": contact_allowed,
                    "company_source_url": row_source_url or None,
                    "evidence": evidence_payload,
                }
            )

    built_agents.sort(
        key=lambda row: (
            -_safe_float(row.get("trust_score_10")),
            -_safe_float(row.get("overall_data_truth_score_4")),
            str(row.get("company_name") or ""),
        )
    )

    audit = extract_audit_summary(dataset)
    source_files = {
        key: str(path)
        for key, path in dataset.files.items()
        if key in {"agents", "evidence", "coverage", "join", "final_audit_csv", "final_audit_report_md", "final_xlsx"}
    }
    return {
        "dataset_available": True,
        "program_parcel_id": str(program_parcel_id),
        "parcel_group_ids": parcel_group_ids,
        "join_rows_count": len(join_rows),
        "total_agents": len(built_agents),
        "agents": built_agents[:limit],
        "source_files": source_files,
        "missing_files": [],
        "audit": audit,
    }
