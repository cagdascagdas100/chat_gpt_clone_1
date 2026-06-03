$ErrorActionPreference='Continue'
$TaskId='aays-113-dem-dtm-recovery-inventory-20260519'
$Start=Get-Date
$BridgeRoot='C:/AAYS_GITHUB_BRIDGE_CLEAN2'
$ResultDir=Join-Path $BridgeRoot 'ai-results'
New-Item -ItemType Directory -Force -Path $ResultDir | Out-Null
$Report=Join-Path $ResultDir 'aays-113-dem-dtm-recovery-inventory-20260519.report.md'
$Json=Join-Path $ResultDir 'aays-113-dem-dtm-recovery-inventory-20260519.result.json'
function W($m){ Add-Content -LiteralPath $Report -Encoding UTF8 -Value $m }
Set-Content -LiteralPath $Report -Encoding UTF8 -Value '# AAYS 113 DEM DTM Recovery Inventory'
W "start_utc=$((Get-Date).ToUniversalTime().ToString('o'))"
W 'mode=read_only_long_inventory_no_db_write_no_download'
$Roots=@('E:/AAYS_DATA','F:/AAYS_DATA','C:/Users/cagda/Documents/GitHub/AAYS','C:/Users/cagda/Documents/GitHub/AAYS/terrayield_land_intelligence')
$Exts=@('*.tif','*.tiff','*.asc','*.vrt','*.bil','*.img','*.gpkg','*.geojson')
$Keys=@('dem','dtm','dsm','lidar','terrain','elevation','height','contour')
$all=@()
for($pass=1;$pass -le 12;$pass++){
  W ""
  W "## pass_$pass $((Get-Date).ToUniversalTime().ToString('o'))"
  $jobs=@()
  foreach($root in $Roots){
    $jobs += Start-Job -ScriptBlock {
      param($root,$Exts,$Keys)
      $out=@()
      $out += "root=$root exists=$(Test-Path -LiteralPath $root)"
      if(Test-Path -LiteralPath $root){
        foreach($ext in $Exts){
          $files=Get-ChildItem -LiteralPath $root -Recurse -File -Filter $ext -ErrorAction SilentlyContinue | Select-Object -First 300
          foreach($f in $files){
            $name=$f.FullName.ToLower()
            $hit=$false
            foreach($k in $Keys){ if($name.Contains($k)){ $hit=$true; break } }
            if($hit -or $ext -in @('*.tif','*.tiff','*.asc','*.vrt')){ $out += "candidate|$($f.FullName)|$($f.Length)|$($f.LastWriteTime.ToString('s'))" }
          }
        }
      }
      $out | Select-Object -First 350
    } -ArgumentList $root,(,$Exts),(,$Keys)
  }
  Wait-Job -Job $jobs -Timeout 150 | Out-Null
  foreach($j in $jobs){
    if($j.State -eq 'Running'){
      Stop-Job -Job $j -Force
      W "job_timeout_stopped=$($j.Id)"
    } else {
      $data=Receive-Job -Job $j -ErrorAction SilentlyContinue
      foreach($line in $data){ W $line; if($line -like 'candidate|*'){ $all += $line } }
    }
    Remove-Job -Job $j -Force -ErrorAction SilentlyContinue
  }
  if($pass -lt 12){ Start-Sleep -Seconds 180 }
}
$uniq=$all | Sort-Object -Unique
$status='completed'
if(@($uniq).Count -eq 0){ $status='completed_with_blockers' }
$obj=[ordered]@{task_id=$TaskId;status=$status;generated_at_utc=(Get-Date).ToUniversalTime().ToString('o');candidate_count=@($uniq).Count;candidate_files=$uniq;blockers=@();next_task='If candidates exist, validate readable raster/sample 50 parcel centroids. If none, user must place official DEM/DTM raster under E:/AAYS_DATA.'}
if(@($uniq).Count -eq 0){ $obj.blockers += 'No local DEM/DTM raster candidate found across E,F,C search roots.' }
$obj | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $Json -Encoding UTF8
W ""
W "## final"
W "candidate_count=$(@($uniq).Count)"
W "result_json=$Json"
W "end_utc=$((Get-Date).ToUniversalTime().ToString('o'))"
Write-Host "AAYS_113_OUTPUT=$ResultDir"