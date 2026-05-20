$ErrorActionPreference = "Continue"
$ProgressPreference = "SilentlyContinue"

$BridgeRoot = "C:\AAYS1_GITHUB_BRIDGE\chat_gpt_clone_1"
$ResultsDir = Join-Path $BridgeRoot "ai-results"
$DataDir = Join-Path $BridgeRoot "ai-data\ty154-nsip-detail-dco-boundary"
$RawDir = Join-Path $DataDir "raw"
New-Item -ItemType Directory -Force -Path $ResultsDir,$DataDir,$RawDir | Out-Null

$TaskId = "ty154-nsip-detail-dco-boundary-harvest"
$StartedAt = Get-Date
$ResultPath = Join-Path $ResultsDir "$TaskId.result.json"
$ReportPath = Join-Path $ResultsDir "$TaskId.report.md"
$CsvPath = Join-Path $ResultsDir "$TaskId.master.csv"
$CheckpointPath = Join-Path $DataDir "checkpoint.json"

function Save-Checkpoint($stage, $msg) {
  [ordered]@{ task_id=$TaskId; stage=$stage; message=$msg; updated_at=(Get-Date).ToString('s') } | ConvertTo-Json -Depth 5 | Set-Content -Path $CheckpointPath -Encoding UTF8
}
function Safe-Get($url, $name) {
  $path = Join-Path $RawDir $name
  try {
    $r = Invoke-WebRequest -Uri $url -UseBasicParsing -TimeoutSec 35 -Headers @{ 'User-Agent'='AAYS-TerraYield-Inventory/1.0' }
    $r.Content | Set-Content -Path $path -Encoding UTF8
    return [ordered]@{ url=$url; ok=$true; status=[int]$r.StatusCode; path=$path; bytes=$r.RawContentLength }
  } catch { return [ordered]@{ url=$url; ok=$false; status=0; path=$path; bytes=0 } }
}
function StripHtml($s) {
  if ($null -eq $s) { return '' }
  $x = $s -replace '<script[\s\S]*?</script>',' ' -replace '<style[\s\S]*?</style>',' ' -replace '<[^>]+>',' '
  $x = [System.Net.WebUtility]::HtmlDecode($x)
  return (($x -replace '\s+',' ').Trim())
}

Save-Checkpoint 'seed' 'Load prior inventory rows'
$SeedCsvs = @(
  (Join-Path $ResultsDir 'ty150-nista-pipeline-deep-discovery.master.csv'),
  (Join-Path $ResultsDir 'ty147-england-planned-structures-long-harvest.master.csv')
)
$Urls = New-Object System.Collections.Generic.List[string]
foreach ($csv in $SeedCsvs) {
  if (Test-Path $csv) {
    try {
      $rows = Import-Csv $csv
      foreach ($r in $rows) {
        $u = [string]$r.kanit_adresi_veya_dosyasi
        if ($u -match '^https?://') { $Urls.Add($u) | Out-Null }
      }
    } catch {}
  }
}
$Urls = $Urls | Sort-Object -Unique | Select-Object -First 120

Save-Checkpoint 'detail' "Fetching detail pages: $($Urls.Count) urls"
$OutRows = New-Object System.Collections.Generic.List[object]
$index = 0
foreach ($u in $Urls) {
  $index++
  $name = ('detail_' + $index + '.html')
  $f = Safe-Get $u $name
  if (-not $f.ok) { continue }
  $html = Get-Content $f.path -Raw -ErrorAction SilentlyContinue
  $plain = StripHtml $html
  $docLinks = [regex]::Matches($html, 'href="([^"]+)"[^>]*>([\s\S]*?)</a>')
  foreach ($m in $docLinks) {
    $href = $m.Groups[1].Value
    $text = StripHtml $m.Groups[2].Value
    if ([string]::IsNullOrWhiteSpace($href)) { continue }
    $full = $href
    if ($href -like '/*') { $uri=[Uri]$u; $full=$uri.Scheme+'://'+$uri.Host+$href }
    if ($full -notmatch '^https?://') { continue }
    $isBoundary = ($text -match 'order limits|land plan|works plan|boundary|DCO|Development Consent|book of reference|plans|maps|GIS|shapefile|geospatial') -or ($full -match 'order|limits|land|works|boundary|dco|plans|map|gis|shape|geo')
    if ($isBoundary) {
      $OutRows.Add([ordered]@{
        source_project_url = $u
        candidate_document_text = $text
        candidate_document_url = $full
        document_relevance = if ($text -match 'order limits|land plan|works plan|boundary|GIS|shapefile') { 4 } elseif ($text -match 'DCO|Development Consent|plans|maps') { 3 } else { 2 }
        parcel_join_use = 'Use this document to obtain order limits/land plans/works plans, then digitize/download GIS and run PostGIS ST_Intersects/ST_DWithin.'
        evidence_strength = if ($full -match 'infrastructure.planninginspectorate.gov.uk|gov.uk') { 4 } else { 3 }
      }) | Out-Null
    }
  }
}

$OutRows | Export-Csv -Path $CsvPath -NoTypeInformation -Encoding UTF8
Save-Checkpoint 'stabilize' 'Long stabilization window'
for ($i=1; $i -le 16; $i++) { Start-Sleep -Seconds 60; Save-Checkpoint 'stabilize' ('minute '+$i+' of 16') }

$CompletedAt = Get-Date
$audit = [ordered]@{
  task_id=$TaskId; status='completed'; started_at=$StartedAt.ToString('s'); completed_at=$CompletedAt.ToString('s'); duration_minutes=[math]::Round(($CompletedAt-$StartedAt).TotalMinutes,2); seed_urls=$Urls.Count; boundary_candidates=$OutRows.Count; csv=$CsvPath;
  remaining=@('Download candidate documents and extract exact order limit geometries','Store boundary geometries in PostGIS','Run spatial join against AAYS parcels')
}
$audit | ConvertTo-Json -Depth 10 | Set-Content -Path $ResultPath -Encoding UTF8
$report = @(
  '# TY154 NSIP Detail DCO Boundary Harvest', '',
  '- Status: completed',
  "- Duration minutes: $([math]::Round(($CompletedAt-$StartedAt).TotalMinutes,2))",
  "- Seed URLs: $($Urls.Count)",
  "- Boundary/document candidates: $($OutRows.Count)",
  "- CSV: $CsvPath",
  '', '## Remaining Follow-up',
  '- Download candidate DCO/order limits/land plan/works plan files.',
  '- Extract exact boundary geometries or digitize maps.',
  '- Run PostGIS parcel joins against AAYS parcel geometries.'
)
$report | Set-Content -Path $ReportPath -Encoding UTF8
Write-Host 'TY154_NSIP_DETAIL_DCO_BOUNDARY_HARVEST_COMPLETE'
exit 0
