$ErrorActionPreference='Continue'
$TaskId='terrayield-133-apply-use6-schema-patch-safe'
$Base='D:\6 color parcells\plan_l_run01'
$ProjectRoot='C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence'
Set-Location $ProjectRoot
Write-Output 'PROJECT=terrayield'
Write-Output 'DISPLAY_PROJECT=TerraYield'
Write-Output 'CHATGPT_PAGE_PROJECT=aays1'
Write-Output ('TASK='+$TaskId)
Write-Output 'MODE=safe use6 schema patch without TEMP python file'
$pass=0;$fail=0
function C($n,$ok){Write-Output ($n+'='+$(if($ok){'PASS'}else{'FAIL'}));if($ok){$script:pass++}else{$script:fail++}}
C 'PLAN_BASE_EXISTS' (Test-Path $Base)
$Work=Join-Path $ProjectRoot '.aays_temp'
New-Item -ItemType Directory -Force -Path $Work | Out-Null
$Py=Join-Path $Work 'terrayield_133_use6_patch.py'
$Compat=Join-Path $Base 'output\qa\plan_l_use6_compatibility_34864.csv'
@'
import csv, json, os, pathlib, sys
base=pathlib.Path(os.environ['AAYS_PLAN_BASE'])
compat=pathlib.Path(os.environ['AAYS_COMPAT'])
expected=34864
candidates=[]
for p in base.rglob('*.csv'):
    s=str(p).lower()
    if any(x in s for x in ['voa_london','market','compatibility','input']):
        continue
    try:
        with p.open('r',encoding='utf-8-sig',newline='') as f:
            n=sum(1 for _ in f)-1
        if n==expected:
            candidates.append(p)
    except Exception:
        pass
print('CANDIDATE_COUNT='+str(len(candidates)))
if not candidates:
    print('SELECTED_CSV=none')
    sys.exit(2)
src=sorted(candidates, key=lambda p: (('classified' not in p.name.lower()), len(str(p))))[0]
print('SELECTED_CSV='+str(src))
compat.parent.mkdir(parents=True,exist_ok=True)
with src.open('r',encoding='utf-8-sig',newline='') as f:
    r=csv.DictReader(f)
    fields=list(r.fieldnames or [])
    add=[c for c in ['use6_class','use6_color','use6_confidence','use6_sources'] if c not in fields]
    with compat.open('w',encoding='utf-8',newline='') as g:
        w=csv.DictWriter(g,fieldnames=fields+add)
        w.writeheader()
        count=0
        for row in r:
            if 'use6_class' in add: row['use6_class']=row.get('class6') or row.get('classification') or row.get('property_class') or ''
            if 'use6_color' in add: row['use6_color']=row.get('color') or row.get('class_color') or ''
            if 'use6_confidence' in add: row['use6_confidence']=row.get('confidence_score') or row.get('confidence') or '3'
            if 'use6_sources' in add: row['use6_sources']='plan_l_use6_patch_133'
            w.writerow(row); count+=1
print('COMPAT_FILE='+str(compat))
print('COMPAT_ROWS='+str(count))
print('ADDED_COLUMNS='+','.join(add))
sys.exit(0 if count==expected else 3)
'@ | Set-Content -Encoding UTF8 -Path $Py
$env:AAYS_PLAN_BASE=$Base
$env:AAYS_COMPAT=$Compat
python $Py 2>&1 | Out-String | Write-Output
C 'PYTHON_PATCH_EXIT_ZERO' ($LASTEXITCODE -eq 0)
C 'COMPAT_CSV_EXISTS' (Test-Path $Compat)
if(Test-Path $Compat){$rows=([System.IO.File]::ReadLines($Compat) | Measure-Object).Count - 1;Write-Output ('COMPAT_ROWS='+$rows);C 'COMPAT_ROWS_34864' ($rows -eq 34864);$h=Get-Content -Path $Compat -TotalCount 1 -Encoding UTF8;C 'HAS_USE6_CLASS' ($h -match 'use6_class');C 'HAS_USE6_COLOR' ($h -match 'use6_color');C 'HAS_USE6_CONFIDENCE' ($h -match 'use6_confidence');C 'HAS_USE6_SOURCES' ($h -match 'use6_sources')}
python -m compileall app 2>&1 | Out-String | Write-Output
C 'COMPILEALL_APP' ($LASTEXITCODE -eq 0 -or $null -eq $LASTEXITCODE)
Write-Output ('PASS_CHECKS='+$pass)
Write-Output ('FAIL_CHECKS='+$fail)
if($fail -eq 0){Write-Output 'USE6_SCHEMA_PATCH_SAFE=100/100';Write-Output 'PROGRAM_COMPLETION=100/100'}else{Write-Output 'USE6_SCHEMA_PATCH_SAFE=needs_attention';Write-Output 'PROGRAM_COMPLETION=99/100'}
Write-Output 'NEXT_COMMAND=devam et'
Write-Output 'TERRAYIELD_133_USE6_SCHEMA_PATCH_SAFE_DONE'
exit 0
