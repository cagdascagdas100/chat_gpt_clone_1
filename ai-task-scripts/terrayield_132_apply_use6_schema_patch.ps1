$ErrorActionPreference = 'Continue'

$ProjectRoot = 'C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence'
$PlanBase = 'D:\6 color parcells\plan_l_run01'
$PyPath = Join-Path $env:TEMP 'terrayield_132_apply_use6_schema_patch.py'

$py = @'
import csv
import json
import pathlib
import shutil
from datetime import datetime

base = pathlib.Path(r"D:\6 color parcells\plan_l_run01")
out_csv = base / "output" / "london_6color.csv"
compat_csv = base / "output" / "qa" / "plan_l_use6_compatibility.csv"
stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
backup_dir = base / "output" / "qa" / f"use6_schema_patch_backup_{stamp}"
backup_dir.mkdir(parents=True, exist_ok=True)
expected = ["use6_class", "use6_color", "use6_confidence", "use6_sources"]

print("PROJECT=terrayield")
print("TASK=terrayield-132-apply-use6-schema-patch")
print("MODE=apply_use6_columns_to_primary_outputs_with_backups")
print(f"PLAN_BASE={base}")
print(f"BACKUP_DIR={backup_dir}")

status = []

def read_csv(path):
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        fields = list(reader.fieldnames or [])
    return fields, rows

def write_csv(path, fields, rows):
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)

if not out_csv.exists():
    print(f"PRIMARY_CSV_EXISTS=FAIL path={out_csv}")
    raise SystemExit(2)
if not compat_csv.exists():
    print(f"COMPAT_CSV_EXISTS=FAIL path={compat_csv}")
    raise SystemExit(3)

primary_fields, primary_rows = read_csv(out_csv)
compat_fields, compat_rows = read_csv(compat_csv)
print(f"PRIMARY_ROWS_BEFORE={len(primary_rows)}")
print(f"COMPAT_ROWS={len(compat_rows)}")
print(f"PRIMARY_FIELDS_BEFORE={primary_fields}")
print(f"COMPAT_HAS_EXPECTED={'PASS' if all(c in compat_fields for c in expected) else 'FAIL'}")

if len(primary_rows) != len(compat_rows):
    print("ROW_COUNT_MATCH=FAIL")
    raise SystemExit(4)

key_candidates = ["parcel_ref", "inspire_id"]
key = next((k for k in key_candidates if k in primary_fields and k in compat_fields), None)
print(f"JOIN_KEY={key}")
if key:
    compat_by_key = {r.get(key, ""): r for r in compat_rows}
    if len(compat_by_key) != len(compat_rows):
        print("JOIN_KEY_UNIQUE=FAIL")
        compat_by_key = None
else:
    compat_by_key = None

shutil.copy2(out_csv, backup_dir / out_csv.name)
print(f"PRIMARY_CSV_BACKUP={backup_dir / out_csv.name}")

new_fields = list(primary_fields)
for c in expected:
    if c not in new_fields:
        new_fields.append(c)

for i, row in enumerate(primary_rows):
    src = None
    if compat_by_key is not None:
        src = compat_by_key.get(row.get(key, ""))
    if src is None:
        src = compat_rows[i]
    row["use6_class"] = src.get("use6_class") or row.get("class6") or row.get("recommended_use6") or row.get("recommended_class") or ""
    row["use6_color"] = src.get("use6_color") or row.get("color") or ""
    row["use6_confidence"] = src.get("use6_confidence") or row.get("confidence_score") or ""
    row["use6_sources"] = src.get("use6_sources") or row.get("signal_sources") or ""

write_csv(out_csv, new_fields, primary_rows)
fields_after, rows_after = read_csv(out_csv)
missing_after = [c for c in expected if c not in fields_after]
print(f"PRIMARY_ROWS_AFTER={len(rows_after)}")
print(f"PRIMARY_FIELDS_AFTER={fields_after}")
print(f"PRIMARY_HAS_EXPECTED_USE6={'PASS' if not missing_after else 'FAIL'}")
print(f"PRIMARY_MISSING_AFTER={missing_after}")

# Patch GeoJSON files with matching feature counts and class/color/confidence fields.
geojson_patched = 0
geojson_seen = 0
for gj in sorted((base / "output").rglob("*.geojson")):
    try:
        with gj.open("r", encoding="utf-8-sig") as f:
            data = json.load(f)
        feats = data.get("features", [])
        if not feats:
            continue
        geojson_seen += 1
        props0 = feats[0].get("properties", {}) or {}
        has_expected = all(c in props0 for c in expected)
        has_sources = any(k in props0 for k in ["class6", "color", "confidence_score", "signal_sources", "recommended_use6", "recommended_class"])
        print(f"GEOJSON_CANDIDATE={gj} FEATURES={len(feats)} HAS_EXPECTED_BEFORE={has_expected} HAS_SOURCE_FIELDS={has_sources}")
        if has_expected or not has_sources:
            continue
        shutil.copy2(gj, backup_dir / gj.name)
        for feat in feats:
            props = feat.setdefault("properties", {})
            props["use6_class"] = props.get("use6_class") or props.get("class6") or props.get("recommended_use6") or props.get("recommended_class") or ""
            props["use6_color"] = props.get("use6_color") or props.get("color") or ""
            props["use6_confidence"] = props.get("use6_confidence") or props.get("confidence_score") or ""
            props["use6_sources"] = props.get("use6_sources") or props.get("signal_sources") or ""
        with gj.open("w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False)
        geojson_patched += 1
        print(f"GEOJSON_PATCHED={gj}")
    except Exception as e:
        print(f"GEOJSON_PATCH_ERROR={gj} :: {type(e).__name__}: {e}")

print(f"GEOJSON_SEEN={geojson_seen}")
print(f"GEOJSON_PATCHED_COUNT={geojson_patched}")

print("\nVALIDATION_SUMMARY")
print(f"CSV_ROWS_34864={'PASS' if len(rows_after) == 34864 else 'FAIL'}")
print(f"CSV_USE6_COLUMNS={'PASS' if not missing_after else 'FAIL'}")
print("NEXT_COMMAND=devam et")
print("TERRAYIELD_132_APPLY_USE6_SCHEMA_PATCH_DONE")
'@

Set-Content -Encoding UTF8 -Path $PyPath -Value $py
Set-Location $ProjectRoot
python $PyPath
