$ErrorActionPreference = 'Continue'
$TaskId = 'terrayield-130-plan-l-schema-source-diagnostic'
$Base = 'D:\6 color parcells\plan_l_run01'
$ProjectRoot = 'C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence'
Set-Location $ProjectRoot

Write-Output 'PROJECT=terrayield'
Write-Output 'DISPLAY_PROJECT=TerraYield'
Write-Output 'CHATGPT_PAGE_PROJECT=aays1'
Write-Output ('TASK=' + $TaskId)
Write-Output 'MODE=read_only_plan_l_schema_source_diagnostic'
Write-Output ('PLAN_BASE=' + $Base)
Write-Output ('PLAN_BASE_EXISTS=' + $(if (Test-Path $Base) { 'PASS' } else { 'FAIL' }))

$diagDir = Join-Path $Base 'output\qa'
New-Item -ItemType Directory -Force -Path $diagDir | Out-Null
$py = Join-Path $diagDir 'terrayield_130_schema_source_diag.py'

@'
import csv, json, os, pathlib, sys, time
base = pathlib.Path(r'D:\6 color parcells\plan_l_run01')
expected_cols = ['use6_class','use6_color','use6_confidence','use6_sources']
interesting_cols = expected_cols + ['class6','color','confidence_score','classification','class_color','confidence','parcel_id','uprn','lsoa11cd']
print('PY_DIAG_START=' + time.strftime('%Y-%m-%d_%H-%M-%S'))
if not base.exists():
    print('BASE_NOT_FOUND=' + str(base))
    sys.exit(0)

csvs = []
for p in base.rglob('*.csv'):
    try:
        if p.is_file():
            csvs.append(p)
    except Exception:
        pass
csvs.sort(key=lambda p: p.stat().st_size if p.exists() else 0, reverse=True)
print('CSV_FILE_COUNT=' + str(len(csvs)))

def safe_header(path):
    for enc in ('utf-8-sig','utf-8','cp1252'):
        try:
            with path.open('r', encoding=enc, newline='') as f:
                r = csv.reader(f)
                header = next(r, [])
                return enc, header
        except Exception:
            continue
    return 'unknown', []

def count_rows(path):
    try:
        with path.open('rb') as f:
            n = sum(1 for _ in f)
        return max(0, n - 1)
    except Exception as e:
        return 'ERROR:' + str(e)[:80]

records = []
for p in csvs:
    try:
        enc, header = safe_header(p)
        hset = set(header)
        rows = count_rows(p)
        rec = {
            'path': str(p),
            'size': p.stat().st_size,
            'rows': rows,
            'encoding': enc,
            'col_count': len(header),
            'has_expected_use6': all(c in hset for c in expected_cols),
            'expected_present': [c for c in expected_cols if c in hset],
            'interesting_present': [c for c in interesting_cols if c in hset],
            'header_head': header[:40],
        }
        records.append(rec)
    except Exception as e:
        records.append({'path': str(p), 'error': str(e)})

print('## TOP_CSV_BY_SIZE')
for rec in records[:25]:
    print(json.dumps(rec, ensure_ascii=False))

print('## ROWS_34864_CANDIDATES')
for rec in records:
    if rec.get('rows') == 34864:
        print(json.dumps(rec, ensure_ascii=False))

print('## HAS_EXPECTED_USE6_CANDIDATES')
for rec in records:
    if rec.get('has_expected_use6'):
        print(json.dumps(rec, ensure_ascii=False))

print('## COMPAT_FILE_SPECIFIC')
compat = base / 'output' / 'qa' / 'plan_l_use6_compatibility.csv'
if compat.exists():
    enc, header = safe_header(compat)
    print(json.dumps({
        'path': str(compat),
        'size': compat.stat().st_size,
        'rows': count_rows(compat),
        'encoding': enc,
        'col_count': len(header),
        'header': header,
        'expected_present': [c for c in expected_cols if c in set(header)]
    }, ensure_ascii=False))
else:
    print('COMPAT_FILE_MISSING=' + str(compat))

print('NEXT_COMMAND=devam et')
print('TERRAYIELD_130_SCHEMA_SOURCE_DIAG_DONE')
'@ | Set-Content -Encoding UTF8 $py

python $py 2>&1 | Write-Output
exit 0
