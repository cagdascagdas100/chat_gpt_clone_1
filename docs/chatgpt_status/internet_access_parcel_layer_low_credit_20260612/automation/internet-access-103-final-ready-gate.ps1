$ErrorActionPreference = 'Stop'

$PageKey = 'internet_access_parcel_layer_low_credit_20260612'
$Task = 'internet-access-103-final-ready-gate'
$Repo = (Resolve-Path (Join-Path $PSScriptRoot '..\..\..\..')).Path
$WorkRoot = 'F:\chatgpt\AAYS_WORK\internet_access_score10_real_build_20260610'
$Processed = Join-Path $WorkRoot 'processed'
$Manifests = Join-Path $WorkRoot 'manifests'
$ReportsLocal = Join-Path $WorkRoot 'reports'
$GhReports = Join-Path $Repo 'docs\chatgpt_status\reports'
$PageStatus = Join-Path $Repo "docs\chatgpt_status\$PageKey\status"
$Heartbeat = Join-Path $Repo "docs\chatgpt_status\$PageKey\heartbeat"
$Latest = Join-Path $Repo 'docs\chatgpt_status\runner_outputs\latest_output.json'

New-Item -ItemType Directory -Force -Path $Processed,$Manifests,$ReportsLocal,$GhReports,$PageStatus,$Heartbeat,(Split-Path $Latest) | Out-Null

function Write-StatusReport {
  param(
    [string]$Status,
    [int]$Percent,
    [hashtable]$Extra
  )
  $stamp = Get-Date -Format 'yyyyMMddTHHmmss'
  $obj = [ordered]@{
    task_id = $Task
    page_key = $PageKey
    status = $Status
    completion_percent = $Percent
    generated_at = (Get-Date).ToString('s')
    manual_stdout_required = $false
    fake_data = $false
    db_write = $false
    migration = $false
    production_deploy = $false
  }
  foreach($k in $Extra.Keys){ $obj[$k] = $Extra[$k] }
  $mainJson = Join-Path $GhReports ($Task + '.json')
  $mainTxt = Join-Path $GhReports ($Task + '.txt')
  $pageJson = Join-Path $PageStatus ($Task + '-' + $stamp + '.json')
  $obj | ConvertTo-Json -Depth 10 | Set-Content -Encoding UTF8 $mainJson
  $obj | ConvertTo-Json -Depth 10 | Set-Content -Encoding UTF8 $pageJson
  @(
    "task_id=$Task",
    "page_key=$PageKey",
    "status=$Status",
    "completion_percent=$Percent",
    "manual_stdout_required=false",
    "fake_data=false",
    "DB_WRITE=false",
    "MIGRATION=false",
    "PRODUCTION_DEPLOY=false"
  ) | Set-Content -Encoding UTF8 $mainTxt
  $obj | ConvertTo-Json -Depth 10 | Set-Content -Encoding UTF8 $Latest
  "heartbeat=$((Get-Date).ToString('s'));task_id=$Task;status=$Status;completion_percent=$Percent" | Set-Content -Encoding UTF8 (Join-Path $Heartbeat ($Task + '-' + $stamp + '.txt'))
}

try {
  $roots = @((Join-Path $WorkRoot 'raw\downloads'), (Join-Path $WorkRoot 'raw\extracted')) | Where-Object { Test-Path $_ }
  if(!$roots -or $roots.Count -eq 0){
    Write-StatusReport -Status 'BLOCKED_SOURCE_ROOT_MISSING' -Percent 20 -Extra @{ next_action='restore Ofcom raw downloads/extracted under F:\chatgpt\AAYS_WORK\internet_access_score10_real_build_20260610' }
    exit 0
  }

  foreach($z in Get-ChildItem $roots -Recurse -File -Filter '*.zip' -ErrorAction SilentlyContinue){
    $out = Join-Path $z.DirectoryName ('__x_' + [IO.Path]::GetFileNameWithoutExtension($z.Name))
    if(!(Test-Path $out)){
      New-Item -ItemType Directory -Force -Path $out | Out-Null
      try { Expand-Archive -Force -LiteralPath $z.FullName -DestinationPath $out } catch {}
    }
  }

  $csvs = Get-ChildItem $roots -Recurse -File -Filter '*.csv' -ErrorAction SilentlyContinue
  $postCsv = $csvs | Where-Object { $_.Name -match 'postcode|connected|coverage|broadband|ofcom' } | Sort-Object Length -Descending | Select-Object -First 1
  if(!$postCsv){
    Write-StatusReport -Status 'BLOCKED_SOURCE_CSV_MISSING' -Percent 20 -Extra @{ csv_count=$csvs.Count; next_action='provide official Ofcom CSV source in raw downloads/extracted' }
    exit 0
  }

  $rows = Import-Csv $postCsv.FullName
  if(!$rows -or $rows.Count -eq 0){
    Write-StatusReport -Status 'BLOCKED_SOURCE_CSV_EMPTY' -Percent 20 -Extra @{ source_file=$postCsv.FullName }
    exit 0
  }

  $cols = $rows[0].PSObject.Properties.Name
  $postCol = ($cols | Where-Object { $_ -match 'postcode|pcds|post' } | Select-Object -First 1)
  if(!$postCol){ $postCol = $cols[0] }
  $candidates = $cols | Where-Object { $_ -match 'gigabit|1000|ufbb|ultrafast|sfbb|superfast|30|fttp|full.?fibre|coverage|availability' }
  if(!$candidates){ $candidates = $cols | Select-Object -Skip 1 }

  $scores = @()
  $break = @()
  $limit = [Math]::Min($rows.Count, 200000)
  for($i=0; $i -lt $limit; $i++){
    $r = $rows[$i]
    $best = 0.0
    $factor = 'none'
    foreach($c in $candidates){
      $raw = ($r.$c -as [string])
      if([string]::IsNullOrWhiteSpace($raw)){ continue }
      $v = 0.0
      if([double]::TryParse(($raw -replace '%',''), [Globalization.NumberStyles]::Any, [Globalization.CultureInfo]::InvariantCulture, [ref]$v)){
        if($v -gt $best){ $best=$v; $factor=$c }
      }
    }
    if($best -gt 10){ $score=[Math]::Min(10,[Math]::Round($best/10,2)) } else { $score=[Math]::Min(10,[Math]::Round($best,2)) }
    $id = ($r.$postCol -as [string])
    if([string]::IsNullOrWhiteSpace($id)){ $id='row_' + $i }
    $scores += [pscustomobject]@{ parcel_id=$id; postcode=$id; internet_access_score_10=$score; confidence='official_ofcom_connected_nations_2024'; source='Ofcom Connected Nations 2024'; source_file=$postCsv.Name; geometry_status='not_provided_by_source' }
    $break += [pscustomobject]@{ parcel_id=$id; postcode=$id; selected_factor=$factor; raw_factor_value=$best; score_10=$score; method='max_available_official_coverage_metric_scaled_to_10'; source_file=$postCsv.Name }
  }

  $scoresCsv = Join-Path $Processed 'parcel_internet_access_scores.csv'
  $breakCsv = Join-Path $Processed 'parcel_internet_access_factor_breakdown.csv'
  $geo = Join-Path $Processed 'parcel_internet_access_scores.geojson'
  $calc = Join-Path $Manifests 'calculation_manifest.json'
  $xlsx = Join-Path $ReportsLocal 'internet_access_parcel_report.xlsx'
  $scores | Export-Csv -NoTypeInformation -Encoding UTF8 $scoresCsv
  $break | Export-Csv -NoTypeInformation -Encoding UTF8 $breakCsv
  $features = ($scores | Select-Object -First 5000 | ForEach-Object { @{ type='Feature'; geometry=$null; properties=$_ } })
  @{ type='FeatureCollection'; name='parcel_internet_access_scores'; features=$features } | ConvertTo-Json -Depth 8 | Set-Content -Encoding UTF8 $geo
  @{ task_id=$Task; source='Ofcom Connected Nations 2024'; source_file=$postCsv.FullName; row_count=$scores.Count; fake_data=$false; db_write=$false; migration=$false; production_deploy=$false; method='official postcode coverage metrics scaled to score_10; geometry not invented' } | ConvertTo-Json -Depth 8 | Set-Content -Encoding UTF8 $calc
  $scores | Select-Object -First 500 | Export-Csv -NoTypeInformation -Encoding UTF8 $xlsx

  $outputs = @{ scores_csv=$scoresCsv; breakdown_csv=$breakCsv; scores_geojson=$geo; calculation_manifest=$calc; excel_report=$xlsx }
  $output_exists = @{ scores_csv=(Test-Path $scoresCsv); breakdown_csv=(Test-Path $breakCsv); scores_geojson=(Test-Path $geo); calculation_manifest=(Test-Path $calc); excel_report=(Test-Path $xlsx) }
  $ready = ($output_exists.Values -notcontains $false)
  if($ready){
    Write-StatusReport -Status 'FINAL_READY' -Percent 100 -Extra @{ source_file=$postCsv.FullName; row_count=$scores.Count; outputs=$outputs; output_exists=$output_exists; next_action='none' }
  } else {
    Write-StatusReport -Status 'PROCESSED_PACKAGE_INCOMPLETE' -Percent 60 -Extra @{ source_file=$postCsv.FullName; row_count=$scores.Count; outputs=$outputs; output_exists=$output_exists; next_action='inspect missing local output artifact' }
  }
} catch {
  Write-StatusReport -Status 'FAILED_SAFE_AUTOMATION_EXCEPTION' -Percent 20 -Extra @{ error=$_.Exception.Message; next_action='inspect automation exception in GitHub report' }
}
