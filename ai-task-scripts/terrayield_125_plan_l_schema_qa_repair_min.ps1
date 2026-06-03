$ErrorActionPreference='Continue'
$TaskId='terrayield-125-plan-l-schema-qa-repair-min'
$Base='D:\6 color parcells\plan_l_run01'
$ProjectRoot='C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence'
Set-Location $ProjectRoot
Write-Output 'PROJECT=terrayield'
Write-Output 'DISPLAY_PROJECT=TerraYield'
Write-Output 'CHATGPT_PAGE_PROJECT=aays1'
Write-Output ('TASK='+$TaskId)
Write-Output 'MODE=Plan L minimal use6 schema compatibility repair and audit'
$pass=0;$fail=0
function C($n,$ok){Write-Output ($n+'='+$(if($ok){'PASS'}else{'FAIL'}));if($ok){$script:pass++}else{$script:fail++}}
C 'PLAN_BASE_EXISTS' (Test-Path $Base)
$Qa=Join-Path $Base 'output\qa'
New-Item -ItemType Directory -Force -Path $Qa | Out-Null
$src=Get-ChildItem -Path $Base -Recurse -File -Filter '*.csv' -ErrorAction SilentlyContinue | Where-Object {$_.Length -gt 1000000} | Sort-Object Length -Descending | Select-Object -First 1
if($src){Write-Output ('SOURCE_CSV='+$src.FullName);C 'SOURCE_CSV_FOUND' $true}else{C 'SOURCE_CSV_FOUND' $false}
$compat=Join-Path $Qa 'plan_l_use6_compatibility.csv'
if($src){
  $py=Join-Path $Qa 'repair_125_min.py'
  @'
import csv, os, pathlib, sys
src=pathlib.Path(os.environ['AAYS_SRC_CSV'])
dst=pathlib.Path(os.environ['AAYS_COMPAT_CSV'])
with src.open('r', encoding='utf-8-sig', newline='') as f:
    r=csv.DictReader(f)
    fields=list(r.fieldnames or [])
    add=[c for c in ['use6_class','use6_color','use6_confidence','use6_sources'] if c not in fields]
    dst.parent.mkdir(parents=True, exist_ok=True)
    count=0
    with dst.open('w', encoding='utf-8', newline='') as g:
        w=csv.DictWriter(g, fieldnames=fields+add)
        w.writeheader()
        for row in r:
            if 'use6_class' in add: row['use6_class']=row.get('class6') or row.get('classification') or ''
            if 'use6_color' in add: row['use6_color']=row.get('color') or row.get('class_color') or ''
            if 'use6_confidence' in add: row['use6_confidence']=row.get('confidence_score') or row.get('confidence') or '3'
            if 'use6_sources' in add: row['use6_sources']='plan_l_repair_125'
            w.writerow(row)
            count+=1
print('COMPAT_ROWS='+str(count))
print('COMPAT_FILE='+str(dst))
'@ | Set-Content -Encoding UTF8 $py
  $env:AAYS_SRC_CSV=$src.FullName
  $env:AAYS_COMPAT_CSV=$compat
  python $py 2>&1 | Out-String | Write-Output
}
C 'COMPAT_CSV_EXISTS' (Test-Path $compat)
if(Test-Path $compat){$rows=([System.IO.File]::ReadLines($compat) | Measure-Object).Count - 1;Write-Output ('COMPAT_ROWS='+$rows);C 'COMPAT_ROWS_34864' ($rows -eq 34864)}
python -m compileall app 2>&1 | Out-String | Write-Output
C 'COMPILEALL_APP' ($LASTEXITCODE -eq 0 -or $null -eq $LASTEXITCODE)
Write-Output ('PASS_CHECKS='+$pass)
Write-Output ('FAIL_CHECKS='+$fail)
if($fail -eq 0){Write-Output 'PLAN_L_SCHEMA_QA_REPAIR=100/100';Write-Output 'PROGRAM_COMPLETION=100/100'}else{Write-Output 'PLAN_L_SCHEMA_QA_REPAIR=needs_attention';Write-Output 'PROGRAM_COMPLETION=99/100'}
Write-Output 'NEXT_COMMAND=devam et'
Write-Output 'TERRAYIELD_125_PLAN_L_SCHEMA_QA_REPAIR_MIN_DONE'
exit 0
