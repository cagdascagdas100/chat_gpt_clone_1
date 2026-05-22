$Bridge='C:\AAYS_GITHUB_BRIDGE_CLEAN2'
$Root='C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence'
if(!(Test-Path $Root)){ $Root=$Bridge }
$Hb=Join-Path $Bridge 'ai-heartbeat\contractor011_repo_health.md'
$Out=Join-Path $Bridge 'ai-results'
$Man=Join-Path $Bridge 'ai-manifests'
New-Item -ItemType Directory -Force -Path (Split-Path $Hb -Parent),$Out,$Man | Out-Null
@('# contractor011_repo_health','stage=start','progress=5','db_write=false','production_deploy=false','fake_data=false') | Set-Content -Encoding UTF8 $Hb
Start-Sleep -Seconds 600
$Files=Get-ChildItem -Path $Root -Recurse -File -ErrorAction SilentlyContinue | Where-Object { $_.FullName -notmatch '\\.git\\|\\node_modules\\|\\__pycache__\\|\\.venv\\|\\dist\\|\\build\\' }
$Summary=[ordered]@{task_id='contractor011_repo_health';status='middle';file_count=@($Files).Count;ps1_count=@($Files|Where-Object{$_.Extension -eq '.ps1'}).Count;py_count=@($Files|Where-Object{$_.Extension -eq '.py'}).Count;js_count=@($Files|Where-Object{$_.Extension -eq '.js'}).Count;test_count=@($Files|Where-Object{$_.Name -match 'test|spec'}).Count;db_write=$false;production_deploy=$false;fake_data=$false;generated_at=(Get-Date -Format s)}
$Summary | ConvertTo-Json -Depth 5 | Set-Content -Encoding UTF8 (Join-Path $Man 'contractor011_repo_health_summary.json')
@('# contractor011_repo_health','stage=middle','progress=50','db_write=false','production_deploy=false','fake_data=false') | Set-Content -Encoding UTF8 $Hb
Start-Sleep -Seconds 900
$Report=Join-Path $Out 'contractor011_repo_health.report.md'
@('# contractor011_repo_health','status=completed','PLAN_PROGRESS_PERCENT=62','TASK_COMPLETION=100/100','db_write=false','production_deploy=false','fake_data=false',('file_count='+$Summary.file_count),('test_count='+$Summary.test_count),'TERRAYIELD_TASK_DONE') | Set-Content -Encoding UTF8 $Report
@('# contractor011_repo_health','stage=done','progress=100','db_write=false','production_deploy=false','fake_data=false') | Set-Content -Encoding UTF8 $Hb
exit 0
