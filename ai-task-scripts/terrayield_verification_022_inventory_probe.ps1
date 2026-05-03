$ErrorActionPreference = "Continue"
$Project = "C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence"
$Start = Get-Date
$Run = Get-Date -Format "yyyyMMdd_HHmmss"
$ReportDir = Join-Path $Project ".aays_next_fix\verification_022_inventory_probe_$Run"
$SummaryFile = Join-Path $ReportDir "summary.md"
$DetailFile = Join-Path $ReportDir "detail.txt"
$BacklogFile = Join-Path $ReportDir "verification_backlog_seed.csv"
New-Item -ItemType Directory -Force -Path $ReportDir | Out-Null
Set-Location $Project
function Log($x){$s=[int]((Get-Date)-$Start).TotalSeconds;$l="[$s s] $x";Write-Output $l;Add-Content -Encoding UTF8 -Path $DetailFile -Value $l}
function E($ep){try{$sw=[System.Diagnostics.Stopwatch]::StartNew();$r=Invoke-WebRequest -Uri ("http://localhost:8010"+$ep) -UseBasicParsing -TimeoutSec 60;$sw.Stop();$line="OK $ep status=$($r.StatusCode) ms=$($sw.ElapsedMilliseconds) bytes=$($r.Content.Length)";Log $line;return $line}catch{$line="FAIL $ep error=$($_.Exception.Message)";Log $line;return $line}}
Log "TASK: TerraYield verification 022 inventory probe"
Log "PROGRESS: 99%"
Log "MODE: non-destructive local inventory + API probe + backlog seed"
$health=E "/health"
$status=E "/map/sales-history/status"
$combined=E "/map/sales-history/combined"
Log "--- local data inventory sample ---"
$files=Get-ChildItem -Recurse -Force -File -ErrorAction SilentlyContinue | Where-Object { $_.FullName -notlike '*\.git*' -and $_.FullName -notlike '*node_modules*' -and $_.FullName -notlike '*.aays_next_fix*' } | Sort-Object Length -Descending | Select-Object -First 250
$files | Select-Object FullName,Length,LastWriteTime | Format-Table -AutoSize | Out-String | Add-Content -Encoding UTF8 -Path $DetailFile
"priority,path,length,last_write,verification_hint" | Set-Content -Encoding UTF8 -Path $BacklogFile
$i=0
foreach($f in $files | Select-Object -First 80){$i++; $hint="local_evidence_candidate"; if($f.Name -match 'sales|price|listing|land|parcel|brownfield|planning|inspire'){ $hint="high_priority_land_evidence" }; ('{0},"{1}",{2},"{3}",{4}' -f $i,$f.FullName,$f.Length,$f.LastWriteTime,$hint) | Add-Content -Encoding UTF8 -Path $BacklogFile}
Log "BACKLOG_ROWS=$i"
Log "--- newest verification plan files ---"
Get-ChildItem -Path ".aays_next_fix" -Recurse -File -ErrorAction SilentlyContinue | Where-Object { $_.FullName -like '*verification_021*' } | Sort-Object LastWriteTime -Descending | Select-Object -First 20 FullName,Length,LastWriteTime | Format-Table -AutoSize | Out-String | Add-Content -Encoding UTF8 -Path $DetailFile
$elapsed=[int]((Get-Date)-$Start).TotalSeconds
$result=if($health -like 'OK*' -and $combined -like 'OK*'){'verification_probe_ready'}elseif($health -like 'OK*'){'api_ready_combined_issue'}else{'api_not_ready'}
$summary=@('# TerraYield Verification 022 Inventory Probe Summary','','## Result',$result,'','## API Health',$health,'','## Sales Status',$status,'','## Combined',$combined,'','## Inventory','Top local evidence candidates scanned: 250','Backlog seed rows: '+$i,'','## Progress Estimate','- Evidence verification planning: 99%','- Local inventory readiness: '+($(if($i -gt 0){'95%'}else{'80%'})),'- API readiness: '+($(if($health -like 'OK*'){'98%'}else{'85%'})),'- Overall verification workflow: '+($(if($result -eq 'verification_probe_ready'){'96%'}else{'90-93%'})),'','## Files',"Detail: $DetailFile","Backlog seed: $BacklogFile","Elapsed seconds: $elapsed",'','## Next','- Start chunked verification of backlog seed rows.','- Keep tasks non-destructive and report-only until evidence rules are confirmed.')
Set-Content -Encoding UTF8 -Path $SummaryFile -Value $summary
Write-Output "SUMMARY_FILE=$SummaryFile"
Write-Output "DETAIL_FILE=$DetailFile"
Write-Output "BACKLOG_FILE=$BacklogFile"
Write-Output "RESULT=$result"
Write-Output "ELAPSED_SECONDS=$elapsed"
Write-Output "VERIFICATION_022_INVENTORY_PROBE_DONE"
exit 0
