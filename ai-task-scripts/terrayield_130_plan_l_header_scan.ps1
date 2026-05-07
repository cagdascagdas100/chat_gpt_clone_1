$ErrorActionPreference = 'Continue'

$ProjectRoot = 'C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence'
$PlanBase = 'D:\6 color parcells\plan_l_run01'
$PyPath = Join-Path $env:TEMP 'terrayield_130_header_scan.py'

$py = @'
import csv
import json
import pathlib

base = pathlib.Path(r"D:\6 color parcells\plan_l_run01")
candidates = [
    base / "output",
    base / "output" / "qa",
    base / "final_packages",
]

print("PROJECT=terrayield")
print("TASK=terrayield-130-plan-l-header-scan")
print("MODE=read_only_csv_geojson_header_scan")
print(f"PLAN_BASE={base}")
print(f"PLAN_BASE_EXISTS={'PASS' if base.exists() else 'FAIL'}")

expected = {"use6_class", "use6_color", "use6_confidence", "use6_sources"}

print("\n=== CSV HEADERS SCAN ===")
for root in candidates:
    if not root.exists():
        print(f"MISSING_ROOT={root}")
        continue
    for p in sorted(root.rglob("*.csv")):
        try:
            with p.open("r", encoding="utf-8-sig", newline="") as f:
                reader = csv.reader(f)
                header = next(reader, [])
                row_count = sum(1 for _ in reader)
            lower = {c.lower(): c for c in header}
            matched = [c for c in header if any(token in c.lower() for token in ["use6", "class", "color", "confidence", "source"])]
            missing = [c for c in expected if c not in lower]
            print()
            print(f"CSV_FILE={p}")
            print(f"CSV_ROWS={row_count}")
            print(f"HEADER_COUNT={len(header)}")
            print(f"HAS_ALL_EXPECTED_USE6={'PASS' if not missing else 'FAIL'}")
            print(f"MISSING_EXPECTED={missing}")
            print(f"MATCHED_COLUMNS={matched}")
            print(f"FIRST_40_COLUMNS={header[:40]}")
        except Exception as e:
            print(f"CSV_ERROR={p} :: {type(e).__name__}: {e}")

print("\n=== GEOJSON PROPERTY SCAN ===")
for p in sorted(base.rglob("*.geojson")):
    try:
        with p.open("r", encoding="utf-8-sig") as f:
            data = json.load(f)
        feats = data.get("features", [])
        props = feats[0].get("properties", {}) if feats else {}
        keys = list(props.keys())
        lower = {k.lower(): k for k in keys}
        matched = [k for k in keys if any(token in k.lower() for token in ["use6", "class", "color", "confidence", "source"])]
        missing = [k for k in expected if k not in lower]
        print()
        print(f"GEOJSON_FILE={p}")
        print(f"FEATURES={len(feats)}")
        print(f"HAS_ALL_EXPECTED_USE6={'PASS' if not missing else 'FAIL'}")
        print(f"MISSING_EXPECTED={missing}")
        print(f"MATCHED_PROPS={matched}")
        print(f"FIRST_40_PROPS={keys[:40]}")
    except Exception as e:
        print(f"GEOJSON_ERROR={p} :: {type(e).__name__}: {e}")

print("\nNEXT_COMMAND=devam et")
print("TERRAYIELD_130_PLAN_L_HEADER_SCAN_DONE")
'@

Set-Content -Encoding UTF8 -Path $PyPath -Value $py
Set-Location $ProjectRoot
python $PyPath
