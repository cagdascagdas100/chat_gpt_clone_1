import csv, os, json
from collections import Counter

ROOT = r"E:\AAYS_DATA\legal"
OUT = r"C:\AAYS1_GITHUB_BRIDGE\chat_gpt_clone_1\ai-results"
os.makedirs(OUT, exist_ok=True)

FILES = [
    r"E:\AAYS_DATA\legal\curated\provenance_evidence.csv",
    r"E:\AAYS_DATA\contractor\curated\provenance_evidence.csv",
    r"E:\AAYS_DATA\legal\processed\contractors_normalized.csv",
    r"E:\AAYS_DATA\legal\processed\contractor_scores.csv",
    r"E:\AAYS_DATA\legal\processed\contractor_parcel_matches.csv",
    r"E:\AAYS_DATA\legal\exports\contractor_app_export.csv",
    r"E:\AAYS_DATA\legal\processed\procurement_events_normalized.csv",
]

NEED = ["source_name","source_url","source_record_id","fetched_at","license_name"]

def read_rows(path, limit=None):
    if not os.path.exists(path):
        return []
    with open(path, newline="", encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))
    return rows[:limit] if limit else rows

def header(path):
    rows = read_rows(path, 1)
    return list(rows[0].keys()) if rows else []

def sample_values(rows, cols):
    out = {}
    for c in cols:
        vals = []
        for r in rows[:100]:
            v = str(r.get(c, "")).strip()
            if v and v not in vals:
                vals.append(v)
            if len(vals) >= 5:
                break
        out[c] = vals
    return out

report = ["# TY118 Provenance Header Discovery", ""]

all_headers = {}
all_rows = {}

for p in FILES:
    rows = read_rows(p)
    h = header(p)
    all_headers[p] = h
    all_rows[p] = rows
    report.append(f"## {p}")
    report.append(f"- exists: {os.path.exists(p)}")
    report.append(f"- rows: {len(rows)}")
    report.append(f"- has_required_provenance_cols: {all(c in h for c in NEED)}")
    report.append(f"- header: {', '.join(h)}")
    report.append("")
    if rows:
        interesting = [c for c in h if any(x in c.lower() for x in ["id","name","company","contractor","supplier","ocid","source","record","date","license","project","parcel"])]
        samples = sample_values(rows, interesting[:30])
        report.append("### Sample values")
        for c, vals in samples.items():
            report.append(f"- {c}: {vals}")
        report.append("")

# Common-column matrix between evidence files and target files
evidence_files = [p for p in FILES if "provenance_evidence.csv" in p]
target_files = [p for p in FILES if "provenance_evidence.csv" not in p]

report.append("# Common Columns")
for e in evidence_files:
    eh = set(all_headers.get(e, []))
    report.append(f"## Evidence: {e}")
    for t in target_files:
        th = set(all_headers.get(t, []))
        common = sorted(eh & th)
        useful = [c for c in common if c not in NEED and any(x in c.lower() for x in ["id","name","company","contractor","supplier","ocid","project","parcel","record"])]
        report.append(f"- target={t}")
        report.append(f"  - common_count={len(common)}")
        report.append(f"  - useful_common={useful}")
    report.append("")

out = os.path.join(OUT, "ty118-provenance-header-discovery.report.md")
with open(out, "w", encoding="utf-8") as f:
    f.write("\n".join(report))

print(out)
