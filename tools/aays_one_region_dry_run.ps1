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
function testParquetMagic($p){
  try {
    $bytes=[System.IO.File]::ReadAllBytes($p)
    if($bytes.Length -lt 8){ return $false }
    $head=[System.Text.Encoding]::ASCII.GetString($bytes,0,4)
    $tail=[System.Text.Encoding]::ASCII.GetString($bytes,$bytes.Length-4,4)
    return ($head -eq 'PAR1' -and $tail -eq 'PAR1')
  } catch { return $false }
}
$sourceExists=Test-Path $source
$pmtilesExists=Test-Path $pmtiles
$sourceOk=$false
$sourceInfo='SKIPPED_SOURCE_MISSING'
$pmtilesOk=$false
$pmtilesInfo='SKIPPED_PMTILES_MISSING'
if($sourceExists){
  $sourceLen=(Get-Item $source).Length
  $sourceOk=testParquetMagic $source
  $sourceInfo="parquet_path=$source`nparquet_bytes=$sourceLen`nparquet_magic_ok=$sourceOk"
}
if($pmtilesExists){
  $wp=toWslPath $pmtiles
  try { $pmtilesInfo=(wsl bash -lc "pmtiles show '$wp' 2>&1 | head -80" | Out-String).Trim() } catch { $pmtilesInfo=$_.Exception.Message }
  $pmtilesOk=($pmtilesInfo -match 'pmtiles spec version' -and $pmtilesInfo -match 'tile type')
}
$dryRunOk=($sourceExists -and $pmtilesExists -and $sourceOk -and $pmtilesOk)
$progress=98
if($dryRunOk){$progress=99}
$result=[ordered]@{
 timestamp=$stamp
 region='bedfordshire'
 progress=$progress
 dry_run_ok=$dryRunOk
 source_exists=$sourceExists
 source_ok=$sourceOk
 pmtiles_exists=$pmtilesExists
 pmtiles_ok=$pmtilesOk
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
source_ok=$sourceOk
pmtiles_exists=$pmtilesExists
pmtiles_ok=$pmtilesOk
safety_db_write=false
safety_deploy=false
safety_fake_data=false
"@ | Set-Content (Join-Path $out 'aays-one-region-dry-run-latest.txt') -Encoding UTF8
Write-Host 'AAYS_ONE_REGION_DRY_RUN_DONE'
