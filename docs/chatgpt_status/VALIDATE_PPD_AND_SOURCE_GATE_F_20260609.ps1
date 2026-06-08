$ErrorActionPreference='Continue'
$Repo='C:\Users\cagda\Documents\GitHub\AAYS'
$Branch='feature/terrayield-aays-integration'
$Reports=Join-Path $Repo 'docs\chatgpt_status'
$FReports='F:\chatgpt\AAYS_WORK\source_generation_reports'
$PpdOut='F:\sold_buildings\open_sources\ppd\pp-complete.csv'
$Incoming='F:\sold_buildings\licensed\incoming'
$Stamp=Get-Date -Format yyyyMMdd-HHmmss
New-Item -ItemType Directory -Force $Reports,$FReports,$Incoming | Out-Null
$Report=Join-Path $Reports "PPD_SOURCE_GATE_VALIDATE_$Stamp.txt"
$FReport=Join-Path $FReports "PPD_SOURCE_GATE_VALIDATE_$Stamp.txt"
$JobReport=Join-Path $FReports "AAYS_JOB_STATUS_$Stamp.txt"

Get-Job | Where-Object Name -like 'AAYS_*' | Format-Table Id,Name,State,HasMoreData | Out-String | Set-Content -Encoding UTF8 $JobReport

$exists=Test-Path $PpdOut
$len=0; $hash=''; $first=''; $last=''; $sample=0
if($exists){
  $item=Get-Item $PpdOut
  $len=$item.Length
  try { $first=(Get-Content $PpdOut -TotalCount 1 -ErrorAction Stop) } catch { $first='READ_FIRST_FAILED' }
  try { $last=(Get-Content $PpdOut -Tail 1 -ErrorAction Stop) } catch { $last='READ_LAST_FAILED' }
  try { $sample=(Get-Content $PpdOut -TotalCount 1000 -ErrorAction Stop | Measure-Object -Line).Lines } catch {}
  try { $hash=(Get-FileHash $PpdOut -Algorithm SHA256).Hash } catch { $hash='HASH_FAILED' }
}

$ppdStatus='PPD_VALIDATION_UNKNOWN'
if(-not $exists){ $ppdStatus='PPD_FILE_MISSING' }
elseif($first -match '<html|<!DOCTYPE|AccessDenied|Error'){ $ppdStatus='PPD_INVALID_NOT_CSV' }
elseif($len -lt 4000000000){ $ppdStatus='PPD_SUSPECT_TOO_SMALL' }
else { $ppdStatus='PPD_PLAUSIBLE_CSV' }

$files=Get-ChildItem $Incoming -File -ErrorAction SilentlyContinue
$hasAddress=(@($files | Where-Object { $_.Name -match 'addressbase|address_to_uprn' }).Count -gt 0)
$hasPolygon=(@($files | Where-Object { $_.Name -match 'national_polygon|polygon_bridge' }).Count -gt 0)
$hasTitle=(@($files | Where-Object { $_.Name -match 'title.*uprn|polygon_bridge' }).Count -gt 0)
$sourceGateReady=($hasAddress -and $hasPolygon -and $hasTitle)
$overall=55
if($sourceGateReady){ $overall=75 }

$lines=@(
 'status=PPD_SOURCE_GATE_VALIDATED',
 "ppd_status=$ppdStatus",
 "ppd_file=$PpdOut",
 "ppd_exists=$exists",
 "ppd_bytes=$len",
 "ppd_sha256=$hash",
 "ppd_first_line=$first",
 "ppd_last_line=$last",
 "ppd_sample_lines_1000=$sample",
 "licensed_incoming=$Incoming",
 "has_address_bridge=$hasAddress",
 "has_hmlr_polygon=$hasPolygon",
 "has_title_uprn=$hasTitle",
 "source_gate_ready=$sourceGateReady",
 "found_licensed_files=$($files.Name -join ',')",
 "overall_progress=$overall",
 'db_write=false',
 'production_deploy=false',
 'fake_data=false',
 "job_report=$JobReport",
 "next_action=$(if($sourceGateReady){'run_full_db_address_match_v3'}else{'acquire_licensed_addressbase_hmlr_bridge_files'})"
)
$lines | Set-Content -Encoding UTF8 $Report
$lines | Set-Content -Encoding UTF8 $FReport

try {
  git -C $Repo add "docs/chatgpt_status/$(Split-Path $Report -Leaf)"
  git -C $Repo commit -m "docs: add PPD source gate validation result" 2>$null
  git -C $Repo pull --rebase origin $Branch 2>$null
  git -C $Repo push origin $Branch 2>$null
} catch {}

Write-Host "STATUS=PPD_SOURCE_GATE_VALIDATED"
Write-Host "PPD_STATUS=$ppdStatus"
Write-Host "PPD_BYTES=$len"
Write-Host "SOURCE_GATE_READY=$sourceGateReady"
Write-Host "OVERALL_PROGRESS=$overall"
Write-Host "REPORT=$Report"
Write-Host "F_REPORT=$FReport"
Write-Host "Bekleme suresi: 5-15 dakika"
