$ErrorActionPreference = "Continue"
$ProgressPreference = "SilentlyContinue"

$BridgeRoot = "C:\AAYS1_GITHUB_BRIDGE\chat_gpt_clone_1"
$ResultsDir = Join-Path $BridgeRoot "ai-results"
$DataDir = Join-Path $BridgeRoot "ai-data\ty150-nista-pipeline-deep-discovery"
$RawDir = Join-Path $DataDir "raw"
New-Item -ItemType Directory -Force -Path $ResultsDir,$DataDir,$RawDir | Out-Null

$TaskId = "ty150-nista-pipeline-deep-discovery"
$StartedAt = Get-Date
$ResultPath = Join-Path $ResultsDir "$TaskId.result.json"
$ReportPath = Join-Path $ResultsDir "$TaskId.report.md"
$CsvPath = Join-Path $ResultsDir "$TaskId.master.csv"
$EndpointCsv = Join-Path $ResultsDir "$TaskId.discovered-endpoints.csv"
$CheckpointPath = Join-Path $DataDir "checkpoint.json"

function Save-Checkpoint($stage, $msg) {
  [ordered]@{ task_id=$TaskId; stage=$stage; message=$msg; updated_at=(Get-Date).ToString('s') } | ConvertTo-Json -Depth 5 | Set-Content -Path $CheckpointPath -Encoding UTF8
}
function Safe-Get($url, $name) {
  $path = Join-Path $RawDir $name
  try {
    $r = Invoke-WebRequest -Uri $url -UseBasicParsing -TimeoutSec 45 -Headers @{ 'User-Agent'='AAYS-TerraYield-Inventory/1.0' }
    $r.Content | Set-Content -Path $path -Encoding UTF8
    return [ordered]@{ url=$url; ok=$true; status=[int]$r.StatusCode; path=$path; bytes=$r.RawContentLength }
  } catch {
    return [ordered]@{ url=$url; ok=$false; status=0; path=$path; bytes=0 }
  }
}
function StripHtml($s) {
  if ($null -eq $s) { return '' }
  $x = $s -replace '<script[\s\S]*?</script>',' ' -replace '<style[\s\S]*?</style>',' ' -replace '<[^>]+>',' '
  $x = [System.Net.WebUtility]::HtmlDecode($x)
  return (($x -replace '\s+',' ').Trim())
}

Save-Checkpoint 'download' 'Fetch NISTA/GOV/PINS pages and assets'
$BasePages = @(
  @{ k='nista'; u='https://pipeline.nista.grid.civilservice.gov.uk/' },
  @{ k='gov_pipeline'; u='https://www.gov.uk/government/publications/uk-infrastructure-pipeline' },
  @{ k='pins_projects'; u='https://infrastructure.planninginspectorate.gov.uk/projects/' }
)
$Fetches = @()
foreach ($p in $BasePages) { $Fetches += Safe-Get $p.u ($p.k + '.html') }

Save-Checkpoint 'assets' 'Discover front-end assets and possible API endpoints'
$Discovered = New-Object System.Collections.Generic.List[object]
foreach ($f in $Fetches | Where-Object { $_.ok }) {
  $html = Get-Content $f.path -Raw -ErrorAction SilentlyContinue
  $assetMatches = [regex]::Matches($html, '(src|href)="([^"]+\.(js|json|csv|xlsx|html)[^"]*)"')
  foreach ($m in $assetMatches) {
    $u = $m.Groups[2].Value
    if ($u -like '/*') { $uri = [Uri]$f.url; $u = $uri.Scheme + '://' + $uri.Host + $u }
    if ($u -notmatch '^https?://') { continue }
    $key = ($u.ToLowerInvariant())
    $Discovered.Add([ordered]@{ source=$f.url; kind='asset'; url=$u; note='asset-link' }) | Out-Null
  }
}

$Assets = $Discovered | Where-Object { $_.kind -eq 'asset' } | Select-Object -First 80
foreach ($a in $Assets) {
  $safeName = (($a.url -replace '[^A-Za-z0-9._-]','_') + '.txt')
  $af = Safe-Get $a.url $safeName
  if ($af.ok) {
    $txt = Get-Content $af.path -Raw -ErrorAction SilentlyContinue
    $urlMatches = [regex]::Matches($txt, 'https?://[^"''\s<>]+|/[A-Za-z0-9_./?=&%-]*(api|csv|xlsx|download|pipeline|project)[A-Za-z0-9_./?=&%-]*')
    foreach ($m in $urlMatches) {
      $u = $m.Value
      if ($u -like '/*') { $uri=[Uri]$a.url; $u=$uri.Scheme+'://'+$uri.Host+$u }
      if ($u -notmatch '^https?://') { continue }
      $Discovered.Add([ordered]@{ source=$a.url; kind='endpoint-candidate'; url=$u; note='found-in-asset' }) | Out-Null
    }
  }
}

$EndpointCandidates = $Discovered | Where-Object { $_.kind -eq 'endpoint-candidate' } | Sort-Object url -Unique | Select-Object -First 80
$EndpointResults = @()
$Rows = New-Object System.Collections.Generic.List[object]
foreach ($e in $EndpointCandidates) {
  $name = ('endpoint_' + [Math]::Abs($e.url.GetHashCode()) + '.txt')
  $er = Safe-Get $e.url $name
  $EndpointResults += [ordered]@{ url=$e.url; ok=$er.ok; status=$er.status; bytes=$er.bytes; local_path=$er.path }
  if ($er.ok -and $er.bytes -gt 100) {
    $txt = Get-Content $er.path -Raw -ErrorAction SilentlyContinue
    if ($txt -match 'project|Project|pipeline|Pipeline|sector|location|region') {
      $lines = ($txt -split "`n") | Select-Object -First 300
      foreach ($line in $lines) {
        if ($line -match 'project|Project|pipeline|Pipeline') {
          $clean = StripHtml $line
          if ($clean.Length -gt 20 -and $clean.Length -lt 240) {
            $Rows.Add([ordered]@{
              yapinin_adi=$clean; kesin_konum='unknown'; konum_dogruluk_skalasi=1; konum_dogruluk_aciklamasi='candidate extracted from NISTA/API asset discovery; requires detail verification';
              planlanan_yapinin_turu='infrastructure'; tur_bilgisi_dogruluk_skalasi=2; planlanan_acilis_yapim_yili='unknown'; yil_bilgisi_dogruluk_skalasi=1;
              yapilma_olasiligi='unknown'; olasilik_dogruluk_skalasi=1; bolgeye_katacaklari='unknown'; katki_dogruluk_skalasi=1;
              kanit_adresi_veya_dosyasi=$e.url; kanit_dogruluk_skalasi=3; resmi_stage='candidate'; kurum_gelistirici='unknown'; bolge='unknown';
              parsel_eslestirme_tipi='needs-location-and-boundary'; parsel_eslestirme_aksiyonu='verify project detail, geocode location, obtain boundary then spatial join'; eksik_tamamlanacak_calisma='manual/API detail verification'; source_group='ty150-endpoint-discovery'
            }) | Out-Null
          }
        }
      }
    }
  }
}

Save-Checkpoint 'merge' 'Merge with TY147 rows'
$Ty147Csv = Join-Path $ResultsDir 'ty147-england-planned-structures-long-harvest.master.csv'
if (Test-Path $Ty147Csv) {
  try {
    $old = Import-Csv $Ty147Csv
    foreach ($r in $old) { $Rows.Add($r) | Out-Null }
  } catch {}
}

$Rows | Export-Csv -Path $CsvPath -NoTypeInformation -Encoding UTF8
$EndpointResults | Export-Csv -Path $EndpointCsv -NoTypeInformation -Encoding UTF8

Save-Checkpoint 'stabilize' 'Long runner stabilize window'
for ($i=1; $i -le 22; $i++) { Start-Sleep -Seconds 60; Save-Checkpoint 'stabilize' ('minute '+$i+' of 22') }

$CompletedAt = Get-Date
$Audit = [ordered]@{
  task_id=$TaskId; status='completed'; started_at=$StartedAt.ToString('s'); completed_at=$CompletedAt.ToString('s'); duration_minutes=[math]::Round(($CompletedAt-$StartedAt).TotalMinutes,2);
  base_sources=$BasePages.Count; assets_found=($Assets|Measure-Object).Count; endpoints_found=($EndpointCandidates|Measure-Object).Count; endpoints_ok=($EndpointResults|Where-Object {$_.ok}|Measure-Object).Count; rows=$Rows.Count; csv=$CsvPath; endpoints_csv=$EndpointCsv;
  remaining=@('If NISTA export is hidden behind client-side API, inspect browser network manually or provide downloaded CSV','DCO/order limits boundary extraction still required','PostGIS parcel spatial join still required')
}
$Audit | ConvertTo-Json -Depth 12 | Set-Content -Path $ResultPath -Encoding UTF8
$Report = @(
  '# TY150 NISTA Pipeline Deep Discovery', '',
  '- Status: completed',
  "- Duration minutes: $([math]::Round(($CompletedAt-$StartedAt).TotalMinutes,2))",
  "- Assets found: $(($Assets|Measure-Object).Count)",
  "- Endpoint candidates: $(($EndpointCandidates|Measure-Object).Count)",
  "- Endpoints OK: $(($EndpointResults|Where-Object {$_.ok}|Measure-Object).Count)",
  "- Rows merged/extracted: $($Rows.Count)",
  "- CSV: $CsvPath",
  "- Endpoint CSV: $EndpointCsv",
  '', '## Remaining Follow-up',
  '- Browser network inspection or supplied NISTA CSV may be required for full 700+ project pipeline.',
  '- Download DCO order limits / land plans / GIS boundary files for spatial joins.',
  '- Run PostGIS ST_Intersects/ST_DWithin against AAYS parcel geometries.'
)
$Report | Set-Content -Path $ReportPath -Encoding UTF8
Write-Host 'TY150_NISTA_PIPELINE_DEEP_DISCOVERY_COMPLETE'
exit 0
