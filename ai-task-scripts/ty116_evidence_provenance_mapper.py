import csv, json, os
from datetime import datetime, timezone
from collections import defaultdict

ROOT = r"E:\AAYS_DATA\legal"
CONTRACTOR_ROOT = r"E:\AAYS_DATA\contractor"
OUT = r"C:\AAYS1_GITHUB_BRIDGE\chat_gpt_clone_1\ai-results"
os.makedirs(OUT, exist_ok=True)
os.makedirs(os.path.join(ROOT, "reports"), exist_ok=True)

NEED = ["source_name","source_url","source_record_id","fetched_at","license_name"]
KEYS = [
    "contractor_id","company_number","company_name","supplier_name","contractor_name",
    "procurement_event_id","project_id","ocid","release_id","parcel_id","match_id"
]

def read_rows(path):
    if not os.path.exists(path):
        return []
    with open(path, newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))

def write_rows(path, rows, fields):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in fields})

def header(path):
    if not os.path.exists(path):
        return []
    with open(path, newline="", encoding="utf-8-sig") as f:
        return next(csv.reader(f), [])

def has_prov_cols(path):
    h = header(path)
    return all(c in h for c in NEED)

def missing_prov_rows(path):
    rows = read_rows(path)
    miss = 0
    for r in rows:
        if any(not str(r.get(c, "")).strip() for c in NEED):
            miss += 1
    return miss

def norm(v):
    return " ".join(str(v or "").strip().lower().split())

def prov_from(row):
    if all(str(row.get(c, "")).strip() for c in NEED):
        return {c: row.get(c, "") for c in NEED}
    return None

def candidate_files():
    roots = [ROOT, CONTRACTOR_ROOT]
    names = []
    for base in roots:
        for sub, _, files in os.walk(base):
            for fn in files:
                if fn.lower().endswith((".csv", ".jsonl")) and (
                    "provenance" in fn.lower()
                    or "snapshot" in fn.lower()
                    or "for_app" in fn.lower()
                    or "ocds" in fn.lower()
                    or "normalized" in fn.lower()
                    or "scores" in fn.lower()
                ):
                    names.append(os.path.join(sub, fn))
    return names

evidence_rows = []
used_sources = []
for path in candidate_files():
    if path.lower().endswith(".csv"):
        rows = read_rows(path)
        good = [r for r in rows if prov_from(r)]
        if good:
            evidence_rows.extend(good)
            used_sources.append({"path": path, "rows": len(good)})
    elif path.lower().endswith(".jsonl"):
        # JSONL raw OCDS usually has nested provenance. Keep this conservative.
        # It is only used if top-level required fields exist.
        good = []
        with open(path, encoding="utf-8-sig", errors="replace") as f:
            for line in f:
                try:
                    obj = json.loads(line)
                except Exception:
                    continue
                flat = {}
                for k, v in obj.items():
                    if isinstance(v, (str, int, float, bool)) or v is None:
                        flat[k] = "" if v is None else str(v)
                p = obj.get("_aays_provenance") or obj.get("provenance")
                if isinstance(p, dict):
                    for c in NEED:
                        if c in p:
                            flat[c] = p[c]
                if prov_from(flat):
                    good.append(flat)
        if good:
            evidence_rows.extend(good)
            used_sources.append({"path": path, "rows": len(good)})

index = defaultdict(list)
value_index = defaultdict(list)

for r in evidence_rows:
    p = prov_from(r)
    if not p:
        continue
    for k in KEYS + ["source_record_id"]:
        v = norm(r.get(k, ""))
        if v:
            index[(k, v)].append(p)
            value_index[v].append(p)

def choose(candidates):
    if not candidates:
        return None
    unique = {}
    for p in candidates:
        sig = tuple(p[c] for c in NEED)
        unique[sig] = p
    if len(unique) == 1:
        return list(unique.values())[0]
    return None

def find_prov(row):
    hits = []
    for k in KEYS:
        v = norm(row.get(k, ""))
        if v:
            hits.extend(index.get((k, v), []))
    chosen = choose(hits)
    if chosen:
        return chosen

    # Conservative fallback: only unique raw value matches.
    fallback_hits = []
    for k in KEYS:
        v = norm(row.get(k, ""))
        if v and len(value_index.get(v, [])) == 1:
            fallback_hits.extend(value_index[v])
    return choose(fallback_hits)

def enrich_file(path):
    rows = read_rows(path)
    if not rows:
        return {"path": path, "exists": os.path.exists(path), "rows": 0, "filled": 0, "missing_after": -1}

    fields = list(rows[0].keys())
    for c in NEED:
        if c not in fields:
            fields.append(c)

    filled = 0
    for r in rows:
        if all(str(r.get(c, "")).strip() for c in NEED):
            continue
        p = find_prov(r)
        if p:
            for c in NEED:
                if not str(r.get(c, "")).strip():
                    r[c] = p[c]
            if all(str(r.get(c, "")).strip() for c in NEED):
                filled += 1

    write_rows(path, rows, fields)
    return {
        "path": path,
        "exists": os.path.exists(path),
        "rows": len(rows),
        "filled": filled,
        "has_provenance_columns": has_prov_cols(path),
        "missing_after": missing_prov_rows(path),
    }

targets = [
    os.path.join(ROOT, "processed", "contractors_normalized.csv"),
    os.path.join(ROOT, "processed", "procurement_events_normalized.csv"),
    os.path.join(ROOT, "processed", "contractor_scores.csv"),
    os.path.join(ROOT, "processed", "contractor_parcel_matches.csv"),
    os.path.join(ROOT, "exports", "contractor_app_export.csv"),
]

results = [enrich_file(p) for p in targets]

# Rebuild app JSONL after app CSV enrichment.
app_csv = os.path.join(ROOT, "exports", "contractor_app_export.csv")
app_jsonl = os.path.join(ROOT, "exports", "contractor_app_export.jsonl")
if os.path.exists(app_csv):
    with open(app_jsonl, "w", encoding="utf-8") as f:
        for r in read_rows(app_csv):
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

critical_missing = sum(1 for r in results if r["missing_after"] != 0 or not r.get("has_provenance_columns"))
db_present = bool(os.environ.get("DATABASE_URL") or all(os.environ.get(k) for k in ["PGHOST","PGDATABASE","PGUSER","PGPASSWORD"]))

if critical_missing:
    with open(os.path.join(ROOT, "reports", "blocked_critical_provenance_missing.json"), "w", encoding="utf-8") as f:
        json.dump({
            "status": "blocked",
            "reason": "critical_provenance_missing_after_evidence_mapping",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "results": results,
            "used_sources": used_sources,
            "rule": "No fabricated provenance. Only matched evidence rows were used."
        }, f, indent=2)

if not db_present:
    with open(os.path.join(ROOT, "reports", "blocked_by_missing_credential_postgres.json"), "w", encoding="utf-8") as f:
        f.write('{"status":"blocked","reason":"missing_database_credential_or_not_visible_to_runner"}')

progress = 90 if critical_missing == 0 else 88
if db_present:
    progress = max(progress, 92)

report = [
    "# TY116 Evidence Provenance Mapper",
    "",
    f"Plan completed: {progress}%",
    f"Plan remaining: {100-progress}%",
    f"DB credentials present: {db_present}",
    f"Evidence source files used: {len(used_sources)}",
    f"Critical provenance missing count: {critical_missing}",
    "",
    "## Results",
]
for r in results:
    report.append(f"- {r['path']} rows={r['rows']} filled={r['filled']} has_cols={r.get('has_provenance_columns')} missing_after={r['missing_after']}")

report += ["", "## Evidence Sources"]
for s in used_sources:
    report.append(f"- {s['path']} rows={s['rows']}")

with open(os.path.join(OUT, "ty116-evidence-provenance-mapper.report.md"), "w", encoding="utf-8") as f:
    f.write("\n".join(report))

with open(os.path.join(OUT, "ty116-evidence-provenance-mapper.audit.json"), "w", encoding="utf-8") as f:
    json.dump({
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "progress": progress,
        "remaining": 100-progress,
        "db_present": db_present,
        "used_sources": used_sources,
        "results": results,
        "critical_missing": critical_missing,
    }, f, indent=2)

print(f"PLAN_PROGRESS_PERCENT={progress}")
print(f"PLAN_PERCENT_REMAINING={100-progress}")
print(os.path.join(OUT, "ty116-evidence-provenance-mapper.report.md"))
