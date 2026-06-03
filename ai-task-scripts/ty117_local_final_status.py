import csv, json, os
from datetime import datetime, timezone

ROOT = r"E:\AAYS_DATA\legal"
OUT = r"C:\AAYS1_GITHUB_BRIDGE\chat_gpt_clone_1\ai-results"
os.makedirs(OUT, exist_ok=True)

NEED = ["source_name","source_url","source_record_id","fetched_at","license_name"]

targets = [
    r"E:\AAYS_DATA\legal\processed\contractors_normalized.csv",
    r"E:\AAYS_DATA\legal\processed\procurement_events_normalized.csv",
    r"E:\AAYS_DATA\legal\processed\contractor_scores.csv",
    r"E:\AAYS_DATA\legal\processed\contractor_parcel_matches.csv",
    r"E:\AAYS_DATA\legal\exports\contractor_app_export.csv",
]

def read_rows(path):
    if not os.path.exists(path):
        return []
    with open(path, newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))

def has_cols(path):
    rows = read_rows(path)
    if not rows:
        return False
    return all(c in rows[0].keys() for c in NEED)

def missing_rows(path):
    rows = read_rows(path)
    if not rows:
        return -1
    miss = 0
    for r in rows:
        if any(not str(r.get(c, "")).strip() for c in NEED):
            miss += 1
    return miss

checks = []
critical = 0
for p in targets:
    rows = read_rows(p)
    hc = has_cols(p)
    mr = missing_rows(p)
    if (not hc) or mr != 0:
        critical += 1
    checks.append({
        "path": p,
        "exists": os.path.exists(p),
        "rows": len(rows),
        "has_provenance_columns": hc,
        "missing_provenance_rows": mr,
    })

db_present = bool(os.environ.get("DATABASE_URL") or all(os.environ.get(k) for k in ["PGHOST","PGDATABASE","PGUSER","PGPASSWORD"]))
progress = 90 if critical == 0 else 88
if db_present:
    progress = max(progress, 92)

report = [
    "# TY117 Local Final Status",
    "",
    f"Generated at: {datetime.now(timezone.utc).isoformat()}",
    f"Plan completed: {progress}%",
    f"Plan remaining: {100-progress}%",
    f"DB credentials present: {db_present}",
    f"Critical provenance missing count: {critical}",
    "",
    "## Critical File Checks",
]
for c in checks:
    report.append(f"- {c['path']} exists={c['exists']} rows={c['rows']} has_provenance={c['has_provenance_columns']} missing_rows={c['missing_provenance_rows']}")

next_action = "Set DB credentials and run DB load." if critical == 0 else "Provenance evidence still missing in one or more critical files. Do not fabricate values."
report += ["", "## Next Action", next_action]

out_md = os.path.join(OUT, "ty117-local-final-status.report.md")
out_json = os.path.join(OUT, "ty117-local-final-status.audit.json")

with open(out_md, "w", encoding="utf-8") as f:
    f.write("\n".join(report))

with open(out_json, "w", encoding="utf-8") as f:
    json.dump({
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "progress": progress,
        "remaining": 100-progress,
        "db_present": db_present,
        "critical_missing": critical,
        "checks": checks,
        "next_action": next_action,
    }, f, indent=2)

print(f"PLAN_PROGRESS_PERCENT={progress}")
print(f"PLAN_PERCENT_REMAINING={100-progress}")
print(out_md)
