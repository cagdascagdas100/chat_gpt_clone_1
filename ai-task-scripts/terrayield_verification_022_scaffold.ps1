$ErrorActionPreference = 'Continue'
$Project = 'C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence'
$Start = Get-Date
$Run = Get-Date -Format 'yyyyMMdd_HHmmss'
$ReportDir = Join-Path $Project ".aays_next_fix\verification_022_scaffold_$Run"
$BackupDir = Join-Path $ReportDir 'backup'
$SummaryFile = Join-Path $ReportDir 'summary.md'
$DetailFile = Join-Path $ReportDir 'detail.txt'
New-Item -ItemType Directory -Force -Path $ReportDir,$BackupDir | Out-Null
Set-Location $Project
function Log([string]$Text){$e=[int]((Get-Date)-$Start).TotalSeconds;$line="[$e s] $Text";Write-Output $line;Add-Content -Encoding UTF8 -Path $DetailFile -Value $line}
function Backup([string]$Path){if(Test-Path $Path){$safe=($Path -replace '[\\/:*?"<>|]','_');Copy-Item -Force $Path (Join-Path $BackupDir $safe);Log "BACKUP $Path"}}
function WriteSafe([string]$Path,[string]$Content){$dir=Split-Path -Parent $Path;if($dir){New-Item -ItemType Directory -Force -Path $dir|Out-Null};Backup $Path;Set-Content -Encoding UTF8 -Path $Path -Value $Content;Log "WROTE $Path"}
function RunCmd([string]$Label,[scriptblock]$Block){Log "--- $Label ---";try{& $Block 2>&1|Out-String|ForEach-Object{Add-Content -Encoding UTF8 -Path $DetailFile -Value $_;Write-Output $_};Log "$Label EXIT=$LASTEXITCODE"}catch{Log "$Label ERROR=$($_.Exception.Message)"}}
Log 'TASK: TerraYield verification 022 scaffold implementation'
Log 'MODE: parallel inspection + safe file scaffold; no destructive changes; no external scraping'
Log "PROJECT=$Project"
Log "REPORT_DIR=$ReportDir"

$jobs=@()
$jobs += Start-Job -Name 'inventory' -ArgumentList $Project -ScriptBlock {param($p) Set-Location $p; Get-ChildItem -Recurse -File -Include *.csv,*.json,*.geojson,*.gpkg,*.parquet,*.sqlite,*.db -ErrorAction SilentlyContinue | Where-Object {$_.FullName -notmatch '\\.git\\|node_modules|__pycache__|\.venv|venv|\.aays_next_fix'} | Select-Object -First 500 -ExpandProperty FullName | Out-String}
$jobs += Start-Job -Name 'api_health' -ScriptBlock {try{(Invoke-WebRequest -UseBasicParsing -TimeoutSec 10 'http://localhost:8010/health').StatusCode}catch{$_.Exception.Message}}
$jobs += Start-Job -Name 'tree_check' -ArgumentList $Project -ScriptBlock {param($p) Set-Location $p; @('app','app\api','app\api\routes','app\services','alembic','alembic\versions','pyproject.toml') | ForEach-Object { "$($_)="+(Test-Path $_) } | Out-String}
Wait-Job -Job $jobs -Timeout 90 | Out-Null
foreach($j in $jobs){if($j.State -eq 'Running'){Stop-Job $j -Force|Out-Null;Log "PARALLEL_TIMEOUT $($j.Name)"};$r=Receive-Job $j -ErrorAction SilentlyContinue|Out-String;Add-Content -Encoding UTF8 -Path $DetailFile -Value "--- JOB $($j.Name) ---`n$r";Remove-Job $j -Force -ErrorAction SilentlyContinue}

$doc = @'
# TerraYield Sale Land Verification Scaffold

This scaffold converts the 3110 sale-suitable land records into a defensible evidence-chain workflow.

Core rule: no candidate polygon, bounding box, centroid buffer, feed geometry, or matched official parcel is presented as a verified sale boundary. Only L4 records are rendered as verified sale boundary.

Verification levels:
- L0: unverified listing or source-only candidate.
- L1: normalized sale candidate with price, area, and location claims.
- L2: official parcel context matched, but not sale boundary.
- L3: document-derived candidate boundary awaiting georeference/review.
- L4: verified sale boundary with evidence chain, georeference, area/location/price consistency, and review.

Annual run outputs:
- sale verification backlog CSV
- confidence distribution
- source change report
- geometry decision change report
- L3 review queue
- L4 verified sale boundary export
'@
WriteSafe (Join-Path $Project '.aays_verification\README.md') $doc

$service = @'
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from math import isfinite
from typing import Any


class VerificationLevel(str, Enum):
    L0_UNVERIFIED_LISTING = "L0_unverified_listing"
    L1_CANDIDATE_SALE_RECORD = "L1_candidate_sale_record"
    L2_MATCHED_OFFICIAL_PARCEL = "L2_matched_official_parcel"
    L3_DOCUMENT_BOUNDARY_CANDIDATE = "L3_document_boundary_candidate"
    L4_VERIFIED_SALE_BOUNDARY = "L4_verified_sale_boundary"


@dataclass
class ConfidenceBreakdown:
    source_score: float = 0.0
    price_score: float = 0.0
    area_score: float = 0.0
    location_score: float = 0.0
    official_context_score: float = 0.0
    document_boundary_score: float = 0.0
    geometry_score: float = 0.0
    review_score: float = 0.0
    conflict_penalty: float = 0.0

    def total(self) -> float:
        raw = (
            self.source_score
            + self.price_score
            + self.area_score
            + self.location_score
            + self.official_context_score
            + self.document_boundary_score
            + self.geometry_score
            + self.review_score
            - self.conflict_penalty
        )
        return max(0.0, min(1.0, raw))


@dataclass
class VerificationDecision:
    level: VerificationLevel
    confidence: float
    confidence_breakdown: dict[str, float]
    missing_evidence: list[str] = field(default_factory=list)
    conflict_flags: list[str] = field(default_factory=list)
    display_polygon_warning: str | None = None
    verified_sale_boundary: bool = False


def _has_value(record: dict[str, Any], *keys: str) -> bool:
    for key in keys:
        value = record.get(key)
        if value not in (None, "", [], {}):
            return True
    return False


def _as_float(value: Any) -> float | None:
    try:
        x = float(value)
        return x if isfinite(x) else None
    except Exception:
        return None


def decide_sale_land_verification(record: dict[str, Any]) -> VerificationDecision:
    """Conservative verification decision for sale-suitable land records.

    The function is deliberately strict. It can enrich API responses now without
    falsely promoting current polygons to verified sale boundaries.
    """
    missing: list[str] = []
    conflicts: list[str] = []
    score = ConfidenceBreakdown()

    if _has_value(record, "url", "listing_url", "source_url", "canonical_url"):
        score.source_score = 0.10
    else:
        missing.append("source_url")

    if _has_value(record, "price", "ask_price", "guide_price"):
        score.price_score = 0.10
    else:
        missing.append("price")

    if _has_value(record, "area_m2", "area_sq_m", "area_acres", "area_ha"):
        score.area_score = 0.10
    else:
        missing.append("area")

    if _has_value(record, "lat", "lon", "latitude", "longitude", "postcode", "address"):
        score.location_score = 0.15
    else:
        missing.append("location")

    if _has_value(record, "inspire_id", "title_number", "official_parcel_id", "matched_parcel_id"):
        score.official_context_score = 0.15
        level = VerificationLevel.L2_MATCHED_OFFICIAL_PARCEL
    elif score.source_score or score.price_score or score.area_score or score.location_score:
        level = VerificationLevel.L1_CANDIDATE_SALE_RECORD
    else:
        level = VerificationLevel.L0_UNVERIFIED_LISTING

    if _has_value(record, "document_boundary_url", "red_line_plan_url", "site_plan_url", "brochure_url"):
        score.document_boundary_score = 0.15
        if level != VerificationLevel.L0_UNVERIFIED_LISTING:
            level = VerificationLevel.L3_DOCUMENT_BOUNDARY_CANDIDATE
    else:
        missing.append("public_boundary_document")

    if _has_value(record, "georef_rmse", "geometry_area_m2", "side_lengths_json"):
        score.geometry_score = 0.15
    else:
        missing.append("georeferenced_geometry_and_side_lengths")

    if _has_value(record, "review_status") and str(record.get("review_status")).lower() in {"approved", "verified"}:
        score.review_score = 0.10
    else:
        missing.append("review_or_second_source")

    source_area = _as_float(record.get("area_m2") or record.get("area_sq_m"))
    geom_area = _as_float(record.get("geometry_area_m2"))
    if source_area and geom_area:
        delta = abs(source_area - geom_area) / max(source_area, 1.0)
        if delta > 0.10:
            conflicts.append("area_mismatch_gt_10pct")
            score.conflict_penalty += 0.15

    can_l4 = (
        score.source_score > 0
        and score.price_score > 0
        and score.area_score > 0
        and score.location_score > 0
        and score.document_boundary_score > 0
        and score.geometry_score > 0
        and score.review_score > 0
        and not conflicts
    )
    if can_l4:
        level = VerificationLevel.L4_VERIFIED_SALE_BOUNDARY

    warning = None
    verified_boundary = level == VerificationLevel.L4_VERIFIED_SALE_BOUNDARY
    if not verified_boundary:
        warning = "Display as candidate/context only; do not render as verified sale boundary."

    breakdown = {
        "source_score": score.source_score,
        "price_score": score.price_score,
        "area_score": score.area_score,
        "location_score": score.location_score,
        "official_context_score": score.official_context_score,
        "document_boundary_score": score.document_boundary_score,
        "geometry_score": score.geometry_score,
        "review_score": score.review_score,
        "conflict_penalty": score.conflict_penalty,
    }
    return VerificationDecision(
        level=level,
        confidence=score.total(),
        confidence_breakdown=breakdown,
        missing_evidence=missing,
        conflict_flags=conflicts,
        display_polygon_warning=warning,
        verified_sale_boundary=verified_boundary,
    )
'@
WriteSafe (Join-Path $Project 'app\services\sale_land_verification.py') $service

$migrationDir = Join-Path $Project 'alembic\versions'
New-Item -ItemType Directory -Force -Path $migrationDir | Out-Null
$migration = @'
"""sale land verification evidence scaffold

Revision ID: 20260504_022
Revises: 
Create Date: 2026-05-04
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "20260504_022"
down_revision = None
branch_labels = None
depends_on = None

verification_level = sa.Enum(
    "L0_unverified_listing",
    "L1_candidate_sale_record",
    "L2_matched_official_parcel",
    "L3_document_boundary_candidate",
    "L4_verified_sale_boundary",
    name="sale_land_verification_level",
)


def upgrade() -> None:
    verification_level.create(op.get_bind(), checkfirst=True)
    op.create_table(
        "sale_verification_run",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("run_label", sa.Text(), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("input_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("result_json", sa.JSON(), nullable=True),
    )
    op.create_table(
        "sale_opportunity_group",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("canonical_listing_id", sa.Text(), nullable=True),
        sa.Column("duplicate_confidence", sa.Float(), nullable=False, server_default="0"),
        sa.Column("active_source_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("conflict_flags", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_table(
        "sale_evidence",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("listing_id", sa.Text(), nullable=True),
        sa.Column("group_id", sa.BigInteger(), nullable=True),
        sa.Column("source_url", sa.Text(), nullable=False),
        sa.Column("source_type", sa.Text(), nullable=False),
        sa.Column("content_hash", sa.Text(), nullable=True),
        sa.Column("storage_path", sa.Text(), nullable=True),
        sa.Column("extraction_status", sa.Text(), nullable=False, server_default="pending"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_table(
        "sale_metric_claim",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("evidence_id", sa.BigInteger(), nullable=True),
        sa.Column("listing_id", sa.Text(), nullable=True),
        sa.Column("claim_type", sa.Text(), nullable=False),
        sa.Column("raw_value", sa.Text(), nullable=True),
        sa.Column("normalized_value", sa.Float(), nullable=True),
        sa.Column("unit", sa.Text(), nullable=True),
        sa.Column("confidence", sa.Float(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_table(
        "sale_boundary_verification",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("listing_id", sa.Text(), nullable=True),
        sa.Column("group_id", sa.BigInteger(), nullable=True),
        sa.Column("verification_level", verification_level, nullable=False, server_default="L0_unverified_listing"),
        sa.Column("confidence", sa.Float(), nullable=False, server_default="0"),
        sa.Column("confidence_breakdown", sa.JSON(), nullable=True),
        sa.Column("missing_evidence", sa.JSON(), nullable=True),
        sa.Column("conflict_flags", sa.JSON(), nullable=True),
        sa.Column("area_match_pct", sa.Float(), nullable=True),
        sa.Column("location_match_m", sa.Float(), nullable=True),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("sale_boundary_verification")
    op.drop_table("sale_metric_claim")
    op.drop_table("sale_evidence")
    op.drop_table("sale_opportunity_group")
    op.drop_table("sale_verification_run")
    verification_level.drop(op.get_bind(), checkfirst=True)
'@
WriteSafe (Join-Path $migrationDir '20260504_022_sale_land_verification_evidence.py') $migration

$generator = @'
from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

from app.services.sale_land_verification import decide_sale_land_verification


def iter_records(path: Path):
    if path.suffix.lower() == ".json":
        data = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            data = data.get("features") or data.get("records") or data.get("items") or []
        for item in data:
            if isinstance(item, dict) and "properties" in item:
                yield item.get("properties") or {}
            elif isinstance(item, dict):
                yield item
    elif path.suffix.lower() == ".csv":
        with path.open("r", encoding="utf-8-sig", newline="") as f:
            yield from csv.DictReader(f)


def write_backlog(input_path: Path, output_path: Path) -> None:
    rows: list[dict[str, Any]] = []
    for i, rec in enumerate(iter_records(input_path), start=1):
        decision = decide_sale_land_verification(rec)
        listing_id = rec.get("listing_id") or rec.get("id") or rec.get("source_id") or str(i)
        rows.append(
            {
                "listing_id": listing_id,
                "verification_level": decision.level.value,
                "confidence": round(decision.confidence, 4),
                "verified_sale_boundary": decision.verified_sale_boundary,
                "missing_evidence": ";".join(decision.missing_evidence),
                "conflict_flags": ";".join(decision.conflict_flags),
                "display_polygon_warning": decision.display_polygon_warning or "",
                "next_action": "promote_to_L4_review" if decision.level.value.startswith("L3") else "collect_missing_evidence",
            }
        )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()) if rows else ["listing_id"])
        writer.writeheader()
        writer.writerows(rows)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("input")
    parser.add_argument("output")
    args = parser.parse_args()
    write_backlog(Path(args.input), Path(args.output))
'@
WriteSafe (Join-Path $Project 'scripts\generate_sale_land_verification_backlog.py') $generator

$apiDraft = @'
from __future__ import annotations

from fastapi import APIRouter

from app.services.sale_land_verification import decide_sale_land_verification

router = APIRouter(prefix="/verification/sale-land", tags=["sale-land-verification"])


@router.post("/classify")
def classify_sale_land_record(record: dict):
    decision = decide_sale_land_verification(record)
    return {
        "verification_level": decision.level.value,
        "confidence": decision.confidence,
        "confidence_breakdown": decision.confidence_breakdown,
        "missing_evidence": decision.missing_evidence,
        "conflict_flags": decision.conflict_flags,
        "display_polygon_warning": decision.display_polygon_warning,
        "verified_sale_boundary": decision.verified_sale_boundary,
    }
'@
WriteSafe (Join-Path $Project 'app\api\routes\aays_sale_land_verification.py') $apiDraft

RunCmd 'python compile verification scaffold' { python -m py_compile app\services\sale_land_verification.py scripts\generate_sale_land_verification_backlog.py app\api\routes\aays_sale_land_verification.py }
RunCmd 'migration syntax compile' { python -m py_compile alembic\versions\20260504_022_sale_land_verification_evidence.py }

$summary=@(
'# Verification 022 Scaffold Summary','',
'## Result','verification_scaffold_created','',
'## Created Files','- app/services/sale_land_verification.py','- app/api/routes/aays_sale_land_verification.py','- scripts/generate_sale_land_verification_backlog.py','- alembic/versions/20260504_022_sale_land_verification_evidence.py','- .aays_verification/README.md','',
'## Safety','No external scraping. No API restart. Existing files backed up before overwrite. Candidate polygons are not promoted to verified sale boundary.','',
'## Next Step','Patch /map/listings response to include verification_level, confidence_breakdown, missing_evidence, conflict_flags, display_polygon_warning, and verified_sale_boundary fields; then expose backlog export endpoint.'
)
Add-Content -Encoding UTF8 -Path $SummaryFile -Value ($summary -join [Environment]::NewLine)
$elapsed=[int]((Get-Date)-$Start).TotalSeconds
Log "RESULT=verification_scaffold_created"
Log "ELAPSED_SECONDS=$elapsed"
Write-Output "SUMMARY_FILE=$SummaryFile"
Write-Output "DETAIL_FILE=$DetailFile"
Write-Output 'RESULT=verification_scaffold_created'
Write-Output 'VERIFICATION_022_SCAFFOLD_DONE'
exit 0
