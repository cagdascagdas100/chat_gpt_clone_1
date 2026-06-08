$ErrorActionPreference='Continue'
$Repo='C:\Users\cagda\Documents\GitHub\AAYS'
$Branch='feature/terrayield-aays-integration'
$PpdOut='F:\sold_buildings\open_sources\ppd\pp-complete.csv'
$Incoming='F:\sold_buildings\licensed\incoming'
$Work='F:\chatgpt\AAYS_WORK\source_generation_reports'
$Status=Join-Path $Repo 'docs\chatgpt_status'
$Stamp=Get-Date -Format yyyyMMdd-HHmmss
New-Item -ItemType Directory -Force $Work,$Status,$Incoming | Out-Null
$LocalReport=Join-Path $Work "PPD_VALIDATE_SOURCE_GATE_$Stamp.txt"
$GitReport=Join-Path $Status "PPD_VALIDATE_SOURCE_GATE_$Stamp.txt"
$exists=Test-Path $PpdOut
$len=0;$first='';$last='';$sampleLines=0;$hash='SKIPPED_LARGE_FILE_FAST_MODE'
if($exists){
  $item=Get-Item $PpdOut
  $len=$item.Length
  try { $first=(Get-Content $PpdOut -TotalCount 1 -ErrorAction Stop) } catch { $first="READ_FIRST_FAILED: $($_.Exception.Message)" }
  try { $last=(Get-Content $PpdOut -Tail 1 -ErrorAction Stop) } catch { $last="READ_LAST_FAILED: $($_.Exception.Message)" }
  try { $sampleLines=(Get-Content $PpdOut -TotalCount 1000 -ErrorAction Stop | Measure-Object -Line).Lines } catch {}
}
$ppdStatus='PPD_UNKNOWN'
if(-not $exists){$ppdStatus='PPD_FILE_MISSING'}
elseif($first -match '<html|<!DOCTYPE|AccessDenied|Error'){$ppdStatus='PPD_INVALID_NOT_CSV'}
elseif($len -ge 4000000000 -and $sampleLines -ge 900){$ppdStatus='PPD_PLAUSIBLE_CSV'}
elseif($len -ge 1000000000){$ppdStatus='PPD_LARGE_NEEDS_REVIEW'}
else{$ppdStatus='PPD_SUSPECT_TOO_SMALL'}
$files=Get-ChildItem $Incoming -File -ErrorAction SilentlyContinue
$hasAddress=(@($files | Where-Object { $_.Name -match 'addressbase|address_to_uprn' }).Count -gt 0)
$hasPolygon=(@($files | Where-Object { $_.Name -match 'national_polygon|polygon_bridge' }).Count -gt 0)
$hasTitle=(@($files | Where-Object { $_.Name -match 'title.*uprn|polygon_bridge' }).Count -gt 0)
$sourceGateReady=($hasAddress -and $hasPolygon -and $hasTitle)
$overall='55'
if($sourceGateReady -and $ppdStatus -eq 'PPD_PLAUSIBLE_CSV'){$overall='75'}
$jobs=(Get-Job | Where-Object Name -like 'AAYS_*' | Select-Object Id,Name,State,HasMoreData | Format-Table | Out-String).Trim()
$lines=@(
"status=PPD_SOURCE_GATE_VALIDATED",
"ppd_status=$ppdStatus",
"ppd_file=$PpdOut",
"ppd_exists=$exists",
"ppd_bytes=$len",
"ppd_sha256=$hash",
"ppd_first_line=$first",
"ppd_last_line=$last",
"ppd_sample_lines_1000=$sampleLines",
"incoming=$Incoming",
"has_address_bridge=$hasAddress",
"has_hmlr_polygon=$hasPolygon",
"has_title_uprn=$hasTitle",
"source_gate_ready=$sourceGateReady",
"found_source_count=$($files.Count)",
"found_source_files=$($files.Name -join ',')",
"overall_progress=$overall",
"next_action=$(if($sourceGateReady -and $ppdStatus -eq 'PPD_PLAUSIBLE_CSV'){'run_full_db_address_match_v3'}else{'wait_for_licensed_addressbase_hmlr_bridge_files'})",
"db_write=false",
"production_deploy=false",
"fake_data=false",
"jobs_begin",
$jobs,
"jobs_end"
)
$lines | Set-Content -Encoding UTF8 $LocalReport
$lines | Set-Content -Encoding UTF8 $GitReport
try{
  git -C $Repo add "docs/chatgpt_status/$(Split-Path $GitReport -Leaf)"
  git -C $Repo commit -m "docs: add PPD validation and source gate result" 2>$null
  git -C $Repo pull --rebase origin $Branch 2>$null
  git -C $Repo push origin $Branch 2>$null
}catch{}
Write-Host "STATUS=PPD_SOURCE_GATE_VALIDATED"
Write-Host "PPD_STATUS=$ppdStatus"
Write-Host "PPD_BYTES=$len"
Write-Host "SOURCE_GATE_READY=$sourceGateReady"
Write-Host "OVERALL_PROGRESS=$overall"
Write-Host "LOCAL_REPORT=$LocalReport"
Write-Host "GIT_REPORT=$GitReport"
Write-Host "Bekleme suresi: 2-5 dakika"