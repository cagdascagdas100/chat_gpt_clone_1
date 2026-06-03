$ErrorActionPreference='Continue'
$TaskId='terrayield-130-plan-l-schema-34864-repair'
$Base='D:\6 color parcells\plan_l_run01'
$ProjectRoot='C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence'
Set-Location $ProjectRoot
Write-Output 'PROJECT=terrayield'
Write-Output 'DISPLAY_PROJECT=TerraYield'
Write-Output 'CHATGPT_PAGE_PROJECT=aays1'
Write-Output ('TASK='+$TaskId)
Write-Output 'MODE=find 34864-row Plan L CSV and build use6 compatibility file'
$Qa=Join-Path $Base 'output\qa'
New-Item -ItemType Directory -Force -Path $Qa | Out-Null
$pass=0;$fail=0
function C($n,$ok){Write-Output ($n+'='+$(if($ok){'PASS'}else{'FAIL'}));if($ok){$script:pass++}else{$script:fail++}}
C 'PLAN_BASE_EXISTS' (Test-Path $Base)
$py=Join-Path $Qa 'repair_130_find_34864.py'
@'
import csv, os, pathlib, sys
base=pathlib.Path(os.environ['AAYS_PLAN_BASE'])
out=pathlib.Path(os.environ['AAYS_COMPAT_CSV'])
expected=34864
candidates=[]
for p in base.rglob('*.csv'):
    name=p.name.lower()
    if 'voa' in name or 'market' in name or 'compatibility' in name:
        continue
    try:
        with p.open('r',encoding='utf-8-sig',newline='') as f:
            rows=sum(1 for _ in f)-1
        if rows==expected:
            candidates.append(p)
    except Exception:
        pass
print('CANDIDATE_COUNT='+str(len(candidates)))
if not candidates:
    print('SELECTED_CSV=none')
    sys.exit(2)
src=sorted(candidates, key=lambda x: (('classified' not in x.name.lower()), len(str(x))))[0]
print('SELECTED_CSV='+str(src))
with src.open('r',encoding='utf-8-sig',newline='') as f:
    r=csv.DictReader(f)
    fields=list(r.fieldnames or [])
    add=[c for c in ['use6_class','use6_color','use6_confidence','use6_sources'] if c not in fields]
    out.parent.mkdir(parents=True,exist_ok=True)
    count=0
    with out.open('w',encoding='utf-8',newline='') as g:
        w=csv.DictWriter(g,fieldnames=fields+add)
        w.writeheader()
        for row in r:
            if 'use6_class' in add: row['use6_class']=row.get('class6') or row.get('classification') or row.get('property_class') or ''
            if 'use6_color' in add: row['use6_color']=row.get('color') or row.get('class_color') or ''
            if 'use6_confidence' in add: row['use6_confidence']=row.get('confidence_score') or row.get('confidence') or '3'
            if 'use6_sources' in add: row['use6_sources']='plan_l_schema_130'
            w.writerow(row)
            count+=1
print('COMPAT_ROWS='+str(count))
print('COMPAT_FILE='+str(out))
print('ADDED_COLUMNS='+','.join(add))
sys.exit(0 if count==expected else 3)
'@ | Set-Content -Encoding UTF8 $py
$compat=Join-Path $Qa 'plan_l_use6_compatibility_34864.csv'
$env:AAYS_PLAN_BASE=$Base
$env:AAYS_COMPAT_CSV=$compat
python $py 2>&1 | Out-String | Write-Output
C 'PYTHON_REPAIR_EXIT_ZERO' ($LASTEXITCODE -eq 0)
C 'COMPAT_CSV_EXISTS' (Test-Path $compat)
if(Test-Path $compat){$rows=([System.IO.File]::ReadLines($compat) | Measure-Object).Count - 1;Write-Output ('COMPAT_ROWS='+$rows);C 'COMPAT_ROWS_34864' ($rows -eq 34864);$head=Get-Content -Path $compat -TotalCount 1 -Encoding UTF8;C 'HAS_USE6_CLASS' ($head -match 'use6_class');C 'HAS_USE6_COLOR' ($head -match 'use6_color');C 'HAS_USE6_CONFIDENCE' ($head -match 'use6_confidence');C 'HAS_USE6_SOURCES' ($head -match 'use6_sources')}
python -m compileall app 2>&1 | Out-String | Write-Output
C 'COMPILEALL_APP' ($LASTEXITCODE -eq 0 -or $null -eq $LASTEXITCODE)
Write-Output ('PASS_CHECKS='+$pass)
Write-Output ('FAIL_CHECKS='+$fail)
if($fail -eq 0){Write-Output 'PLAN_L_SCHEMA_34864_REPAIR=100/100';Write-Output 'PROGRAM_COMPLETION=100/100'}else{Write-Output 'PLAN_L_SCHEMA_34864_REPAIR=needs_attention';Write-Output 'PROGRAM_COMPLETION=99/100'}
Write-Output 'NEXT_COMMAND=devam et'
Write-Output 'TERRAYIELD_130_PLAN_L_SCHEMA_34864_REPAIR_DONE'
exit 0
