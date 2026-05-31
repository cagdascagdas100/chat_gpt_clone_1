param([string]$Repo='C:\Users\cagda\Documents\GitHub\AAYS')
$ErrorActionPreference='Continue'
$stamp=Get-Date -Format 'yyyyMMdd_HHmmss'
$out=Join-Path $Repo 'docs\chatgpt_status\runner_outputs'
New-Item -ItemType Directory -Force -Path $out | Out-Null
$source=Join-Path $Repo 'regions\bedfordshire\parcels_prepared.parquet'
$pmtiles=Join-Path $Repo 'tiles\bedfordshire\parcels.pmtiles'
function toWslPath($p){
  $full=[System.IO.Path]::GetFullPath($p)
  $drive=$full.Substring(0,1).ToLower()
  $rest=$full.Substring(2).Replace('\','/')
  return "/mnt/$drive$rest"
}
$sourceExists=Test-Path $source
$pmtilesExists=Test-Path $pmtiles
$sourceInfo='SKIPPED_SOURCE_MISSING'
$pmtilesInfo='SKIPPED_PMTILES_MISSING'
if($sourceExists){
  $ws=toWslPath $source
  try { $sourceInfo=(wsl bash -lc "ogrinfo -ro -so '$ws' 2>&1 | head -80" | Out-String).Trim() } catch { $sourceInfo=$_.Exception.Message }
}
if($pmtilesExists){
  $wp=toWslPath $pmtiles
  try { $pmtilesInfo=(wsl bash -lc "pmtiles show '$wp' 2>&1 | head -80" | Out-String).Trim() } catch { $pmtilesInfo=$_.Exception.Message }
}
$dryRunOk=($sourceExists -and $pmtilesExists -and $sourceInfo -notmatch 'ERROR|FAIL|not recognized|not found' -and $pmtilesInfo -notmatch 'ERROR|FAIL|not recognized|not found')
$progress=98
if($dryRunOk){$progress=99}
$result=[ordered]@{
 timestamp=$stamp
 region='bedfordshire'
 progress=$progress
 dry_run_ok=$dryRunOk
 source_exists=$sourceExists
 pmtiles_exists=$pmtilesExists
 source_path=$source
 pmtiles_path=$pmtiles
 source_info=$sourceInfo
 pmtiles_info=$pmtilesInfo
 safety=[ordered]@{ db_write=$false; deploy=$false; fake_data=$false; production_write=$false }
}
$result | ConvertTo-Json -Depth 8 | Set-Content (Join-Path $out 'aays-one-region-dry-run-latest.json') -Encoding UTF8
@"
AAYS one-region dry-run $stamp
region=bedfordshire
progress=$progress
dry_run_ok=$dryRunOk
source_exists=$sourceExists
pmtiles_exists=$pmtilesExists
safety_db_write=false
safety_deploy=false
safety_fake_data=false
"@ | Set-Content (Join-Path $out 'aays-one-region-dry-run-latest.txt') -Encoding UTF8
Write-Host 'AAYS_ONE_REGION_DRY_RUN_DONE'
