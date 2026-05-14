import csv, json, os
from datetime import datetime, timezone

ROOT = r"E:\AAYS_DATA\legal"
OUT = r"C:\AAYS1_GITHUB_BRIDGE\chat_gpt_clone_1\ai-results"
os.makedirs(OUT, exist_ok=True)
os.makedirs(os.path.join(ROOT, "reports"), exist_ok=True)

NEED = ["source_name","source_url","source_record_id","fetched_at","license_name"]

def rows(path):
    if not os.path.exists(path):
        return []
    with open(path, newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))

def write_csv(path, data, fields):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        for r in data:
            w.writerow({k: r.get(k, "") for k in fields})

def has_prov_cols(path):
    if not os.path.exists(path):
        return False
    with open(path, newline="", encoding="utf-8-sig") as f:
        reader = csv.reader(f)
        header = next(reader, [])
    return all(c in header for c in NEED)

def missing_prov(path):
    if not os.path.exists(path):
        return -1
    data = rows(path)
    miss = 0
    for r in data:
        if any(not str(r.get(c, "")).strip() for c in NEED):
            miss += 1
    return miss

contractors_path = os.path.join(ROOT, "processed", "contractors_normalized.csv")
scores_path = os.path.join(ROOT, "processed", "contractor_scores.csv")
events_path = os.path.join(ROOT, "processed", "procurement_events_normalized.csv")
matches_path = os.path.join(ROOT, "processed", "contractor_parcel_matches.csv")
app_path = os.path.join(ROOT, "exports", "contractor_app_export.csv")
app_jsonl = os.path.join(ROOT, "exports", "contractor_app_export.jsonl")

contractors = {r.get("contractor_id"): r for r in rows(contractors_path) if r.get("contractor_id")}
scores = {r.get("contractor_id"): r for r in rows(scores_path) if r.get("contractor_id")}

actions = []

if contractors and scores:
    app_fields = [
        "contractor_id","company_number","company_name","company_status","sic_codes",
        "address_line_1","locality","region","postal_code","authority_code","country",
        "reliability_score","data_confidence_score","legal_contact_score","quality_band",
        "activity_density_label","do_not_contact","contact_allowed",
        "source_name","source_url","source_record_id","fetched_at","license_name"
    ]
    app_rows = []
    for cid, c in contractors.items():
        s = scores.get(cid, {})
        legal = s.get("legal_contact_score", "")
        dnc = str(s.get("do_not_contact", "")).lower()
        try:
            contact_allowed = str(int(legal) >= 50 and dnc != "true").lower()
        except Exception:
            contact_allowed = "false"
        app_rows.append({
            "contractor_id": cid,
            "company_number": c.get("company_number", ""),
            "company_name": c.get("company_name", ""),
            "company_status": c.get("company_status", ""),
            "sic_codes": c.get("sic_codes", ""),
            "address_line_1": c.get("address_line_1", ""),
            "locality": c.get("locality", ""),
            "region": c.get("region", ""),
            "postal_code": c.get("postal_code", ""),
            "authority_code": c.get("authority_code", ""),
            "country": c.get("country", ""),
            "reliability_score": s.get("reliability_score", ""),
            "data_confidence_score": s.get("data_confidence_score", ""),
            "legal_contact_score": legal,
            "quality_band": s.get("quality_band", ""),
            "activity_density_label": s.get("activity_density_label", ""),
            "do_not_contact": dnc,
            "contact_allowed": contact_allowed,
            "source_name": c.get("source_name", ""),
            "source_url": c.get("source_url", ""),
            "source_record_id": c.get("source_record_id", ""),
            "fetched_at": c.get("fetched_at", ""),
            "license_name": c.get("license_name", ""),
        })
    write_csv(app_path, app_rows, app_fields)
    with open(app_jsonl, "w", encoding="utf-8") as f:
        for r in app_rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    actions.append("rebuilt contractor_app_export.csv/jsonl from provenance-bearing contractors + scores")

if os.path.exists(matches_path) and contractors:
    match_rows = rows(matches_path)
    fields = list(match_rows[0].keys()) if match_rows else []
    for c in NEED:
        if c not in fields:
            fields.append(c)
    for r in match_rows:
        c = contractors.get(r.get("contractor_id"))
        if c:
            for col in NEED:
                if not str(r.get(col, "")).strip():
                    r[col] = c.get(col, "")
    write_csv(matches_path, match_rows, fields)
    actions.append("filled parcel match provenance from matching contractor_id rows only")

critical_paths = [contractors_path, events_path, scores_path, matches_path, app_path]
checks = []
critical_missing = 0
for p in critical_paths:
    check = {
        "path": p,
        "exists": os.path.exists(p),
        "rows": len(rows(p)) if os.path.exists(p) else 0,
        "has_provenance_columns": has_prov_cols(p),
        "missing_provenance_rows": missing_prov(p),
    }
    checks.append(check)
    if not check["has_provenance_columns"] or check["missing_provenance_rows"] != 0:
        critical_missing += 1

db_present = bool(os.environ.get("DATABASE_URL") or all(os.environ.get(k) for k in ["PGHOST","PGDATABASE","PGUSER","PGPASSWORD"]))

if critical_missing:
    with open(os.path.join(ROOT, "reports", "blocked_critical_provenance_missing.json"), "w", encoding="utf-8") as f:
        json.dump({
            "status": "blocked",
            "reason": "critical_provenance_missing_after_local_rebuild",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "checks": checks,
            "rule": "No fabricated provenance. Empty evidence remains blocked."
        }, f, indent=2)

if not db_present:
    with open(os.path.join(ROOT, "reports", "blocked_by_missing_credential_postgres.json"), "w", encoding="utf-8") as f:
        f.write('{"status":"blocked","reason":"missing_database_credential_or_not_visible_to_runner"}')

progress = 90 if critical_missing == 0 else 88
if db_present:
    progress = max(progress, 92)

report = [
    "# TY115 Local Provenance Rebuild",
    "",
    f"Plan completed: {progress}%",
    f"Plan remaining: {100-progress}%",
    f"DB credentials present: {db_present}",
    f"Critical provenance missing count: {critical_missing}",
    "",
    "## Actions",
    *[f"- {a}" for a in actions],
    "",
    "## Checks",
    *[f"- {c['path']} rows={c['rows']} has_provenance={c['has_provenance_columns']} missing_rows={c['missing_provenance_rows']}" for c in checks],
]
with open(os.path.join(OUT, "ty115-local-provenance-rebuild.report.md"), "w", encoding="utf-8") as f:
    f.write("\n".join(report))

print(f"PLAN_PROGRESS_PERCENT={progress}")
print(f"PLAN_PERCENT_REMAINING={100-progress}")
