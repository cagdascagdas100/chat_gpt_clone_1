import csv, json, os
from collections import Counter, defaultdict
from datetime import datetime, timezone

ROOT = r"E:\AAYS_DATA\legal"
CONTRACTOR_ROOT = r"E:\AAYS_DATA\contractor"
OUT = r"C:\AAYS1_GITHUB_BRIDGE\chat_gpt_clone_1\ai-results"
os.makedirs(OUT, exist_ok=True)
os.makedirs(os.path.join(ROOT, "reports"), exist_ok=True)

NEED = ["source_name","source_url","source_record_id","fetched_at","license_name"]

EVIDENCE_FILES = [
    os.path.join(ROOT, "curated", "provenance_evidence.csv"),
    os.path.join(CONTRACTOR_ROOT, "curated", "provenance_evidence.csv"),
]

TARGETS = [
    os.path.join(ROOT, "processed", "contractors_normalized.csv"),
    os.path.join(ROOT, "processed", "contractor_scores.csv"),
    os.path.join(ROOT, "processed", "contractor_parcel_matches.csv"),
    os.path.join(ROOT, "exports", "contractor_app_export.csv"),
]

EVENTS = os.path.join(ROOT, "processed", "procurement_events_normalized.csv")
APP_JSONL = os.path.join(ROOT, "exports", "contractor_app_export.jsonl")

def read_csv(path):
    if not os.path.exists(path):
        return []
    with open(path, newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))

def write_csv(path, rows, fields):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in fields})

def has_cols(path):
    rows = read_csv(path)
    if not rows:
        return False
    return all(c in rows[0].keys() for c in NEED)

def missing_rows(path):
    rows = read_csv(path)
    if not rows:
        return -1
    n = 0
    for r in rows:
        if any(not str(r.get(c, "")).strip() for c in NEED):
            n += 1
    return n

def prov_tuple(r):
    if not all(str(r.get(c, "")).strip() for c in NEED):
        return None
    return tuple(r.get(c, "") for c in NEED)

# Build contractor_id -> official provenance tuple index.
prov_counter = defaultdict(Counter)
evidence_rows = 0

for path in EVIDENCE_FILES:
    for r in read_csv(path):
        cid = str(r.get("contractor_id", "")).strip()
        pt = prov_tuple(r)
        if cid and pt:
            prov_counter[cid][pt] += 1
            evidence_rows += 1

prov_index = {}
ambiguous = {}

for cid, ctr in prov_counter.items():
    if not ctr:
        continue
    top, count = ctr.most_common(1)[0]
    # Safe rule: use the most frequent official evidence tuple for that contractor_id,
    # and record ambiguity if more than one tuple exists.
    prov_index[cid] = dict(zip(NEED, top))
    if len(ctr) > 1:
        ambiguous[cid] = [{"provenance": dict(zip(NEED, k)), "count": v} for k, v in ctr.most_common()]

def enrich_target(path):
    rows = read_csv(path)
    if not rows:
        return {"path": path, "exists": os.path.exists(path), "rows": 0, "filled": 0, "missing_after": -1, "has_cols": False}

    fields = list(rows[0].keys())
    for c in NEED:
        if c not in fields:
            fields.append(c)

    filled = 0
    unresolved = 0

    for r in rows:
        cid = str(r.get("contractor_id", "")).strip()
        p = prov_index.get(cid)
        if p:
            changed = False
            for c in NEED:
                if not str(r.get(c, "")).strip():
                    r[c] = p[c]
                    changed = True
            if changed and all(str(r.get(c, "")).strip() for c in NEED):
                filled += 1
        if any(not str(r.get(c, "")).strip() for c in NEED):
            unresolved += 1

    write_csv(path, rows, fields)
    return {
        "path": path,
        "exists": os.path.exists(path),
        "rows": len(rows),
        "filled": filled,
        "missing_after": unresolved,
        "has_cols": has_cols(path),
    }

results = [enrich_target(p) for p in TARGETS]

# Rebuild app JSONL after app CSV provenance fill.
app_csv = os.path.join(ROOT, "exports", "contractor_app_export.csv")
if os.path.exists(app_csv):
    with open(APP_JSONL, "w", encoding="utf-8") as f:
        for r in read_csv(app_csv):
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

# Include procurement events in final gate; already expected to pass.
all_critical = TARGETS + [EVENTS]
checks = []
critical_missing = 0
for p in all_critical:
    check = {
        "path": p,
        "exists": os.path.exists(p),
        "rows": len(read_csv(p)),
        "has_provenance_columns": has_cols(p),
        "missing_provenance_rows": missing_rows(p),
    }
    checks.append(check)
    if not check["has_provenance_columns"] or check["missing_provenance_rows"] != 0:
        critical_missing += 1

db_present = bool(os.environ.get("DATABASE_URL") or all(os.environ.get(k) for k in ["PGHOST","PGDATABASE","PGUSER","PGPASSWORD"]))

if critical_missing:
    with open(os.path.join(ROOT, "reports", "blocked_critical_provenance_missing.json"), "w", encoding="utf-8") as f:
        json.dump({
            "status": "blocked",
            "reason": "critical_provenance_missing_after_contractor_id_mapping",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "checks": checks,
            "evidence_rows_indexed": evidence_rows,
            "ambiguous_contractor_ids_count": len(ambiguous),
            "rule": "No fabricated provenance. Only contractor_id-matched official provenance_evidence rows were used."
        }, f, indent=2)

if not db_present:
    with open(os.path.join(ROOT, "reports", "blocked_by_missing_credential_postgres.json"), "w", encoding="utf-8") as f:
        f.write('{"status":"blocked","reason":"missing_database_credential_or_not_visible_to_runner"}')

progress = 90 if critical_missing == 0 else 88
if db_present:
    progress = max(progress, 92)

report = [
    "# TY119 Contractor-ID Provenance Mapper",
    "",
    f"Generated at: {datetime.now(timezone.utc).isoformat()}",
    f"Plan completed: {progress}%",
    f"Plan remaining: {100-progress}%",
    f"DB credentials present: {db_present}",
    f"Evidence rows indexed: {evidence_rows}",
    f"Contractor IDs with evidence: {len(prov_index)}",
    f"Ambiguous contractor IDs recorded: {len(ambiguous)}",
    f"Critical provenance missing count: {critical_missing}",
    "",
    "## Enrichment Results",
]
for r in results:
    report.append(f"- {r['path']} rows={r['rows']} filled={r['filled']} has_cols={r['has_cols']} missing_after={r['missing_after']}")

report += ["", "## Final Critical Checks"]
for c in checks:
    report.append(f"- {c['path']} exists={c['exists']} rows={c['rows']} has_provenance={c['has_provenance_columns']} missing_rows={c['missing_provenance_rows']}")

next_action = "Set PostgreSQL credentials and run DB load." if critical_missing == 0 else "Some contractor_id rows still lack official provenance evidence; keep DB load blocked."
report += ["", "## Next Action", next_action]

out_md = os.path.join(OUT, "ty119-contractor-id-provenance-mapper.report.md")
out_json = os.path.join(OUT, "ty119-contractor-id-provenance-mapper.audit.json")

with open(out_md, "w", encoding="utf-8") as f:
    f.write("\n".join(report))

with open(out_json, "w", encoding="utf-8") as f:
    json.dump({
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "progress": progress,
        "remaining": 100-progress,
        "db_present": db_present,
        "evidence_rows_indexed": evidence_rows,
        "contractor_ids_with_evidence": len(prov_index),
        "ambiguous_contractor_ids_count": len(ambiguous),
        "results": results,
        "checks": checks,
        "critical_missing": critical_missing,
        "next_action": next_action,
    }, f, indent=2)

print(f"PLAN_PROGRESS_PERCENT={progress}")
print(f"PLAN_PERCENT_REMAINING={100-progress}")
print(out_md)
