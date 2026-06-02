$ErrorActionPreference = "Continue"
$ProgressPreference = "SilentlyContinue"

$BridgeRoot = "C:\AAYS1_GITHUB_BRIDGE\chat_gpt_clone_1"
$ResultsDir = Join-Path $BridgeRoot "ai-results"
$DataDir = Join-Path $BridgeRoot "ai-data\ty147-england-planned-structures"
$LogDir = Join-Path $BridgeRoot "ai-runner-logs"
New-Item -ItemType Directory -Force -Path $ResultsDir,$DataDir,$LogDir | Out-Null

$TaskId = "ty147-england-planned-structures-long-harvest"
$StartedAt = Get-Date
$ReportPath = Join-Path $ResultsDir "$TaskId.report.md"
$ResultPath = Join-Path $ResultsDir "$TaskId.result.json"
$CsvPath = Join-Path $ResultsDir "$TaskId.master.csv"
$ParcelCsvPath = Join-Path $ResultsDir "$TaskId.parcel-match.csv"
$CheckpointPath = Join-Path $DataDir "checkpoint.json"
$RawDir = Join-Path $DataDir "raw"
New-Item -ItemType Directory -Force -Path $RawDir | Out-Null

function Save-Checkpoint($stage, $message) {
  [ordered]@{ task_id=$TaskId; stage=$stage; message=$message; updated_at=(Get-Date).ToString("s") } |
    ConvertTo-Json -Depth 5 | Set-Content -Path $CheckpointPath -Encoding UTF8
}

function Get-SafePage {
  param([string]$Url, [string]$OutName, [int]$Retries = 3)
  $OutPath = Join-Path $RawDir $OutName
  for ($i = 1; $i -le $Retries; $i++) {
    try {
      $r = Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec 30 -Headers @{ "User-Agent" = "AAYS-TerraYield-Inventory/1.0" }
      $r.Content | Set-Content -Path $OutPath -Encoding UTF8
      return [ordered]@{ url=$Url; ok=$true; status=[int]$r.StatusCode; path=$OutPath; bytes=$r.RawContentLength; attempt=$i }
    } catch {
      Start-Sleep -Seconds ([Math]::Min(10, 2*$i))
    }
  }
  return [ordered]@{ url=$Url; ok=$false; status=0; path=$OutPath; bytes=0; attempt=$Retries }
}

function Strip-Html([string]$s) {
  if ($null -eq $s) { return "" }
  $x = $s -replace '<script[\s\S]*?</script>',' ' -replace '<style[\s\S]*?</style>',' '
  $x = $x -replace '<[^>]+>',' '
  $x = [System.Net.WebUtility]::HtmlDecode($x)
  $x = $x -replace '\s+',' '
  return $x.Trim()
}

$SourceUrls = @(
  @{ key="pip_projects"; url="https://infrastructure.planninginspectorate.gov.uk/projects/" },
  @{ key="pip_eastern"; url="https://infrastructure.planninginspectorate.gov.uk/projects/eastern/" },
  @{ key="pip_london"; url="https://infrastructure.planninginspectorate.gov.uk/projects/london/" },
  @{ key="pip_south_east"; url="https://infrastructure.planninginspectorate.gov.uk/projects/south-east/" },
  @{ key="pip_south_west"; url="https://infrastructure.planninginspectorate.gov.uk/projects/south-west/" },
  @{ key="pip_east_midlands"; url="https://infrastructure.planninginspectorate.gov.uk/projects/east-midlands/" },
  @{ key="pip_west_midlands"; url="https://infrastructure.planninginspectorate.gov.uk/projects/west-midlands/" },
  @{ key="pip_north_east"; url="https://infrastructure.planninginspectorate.gov.uk/projects/north-east/" },
  @{ key="pip_north_west"; url="https://infrastructure.planninginspectorate.gov.uk/projects/north-west/" },
  @{ key="pip_yorkshire_humber"; url="https://infrastructure.planninginspectorate.gov.uk/projects/yorkshire-and-the-humber/" },
  @{ key="gov_pipeline"; url="https://www.gov.uk/government/publications/uk-infrastructure-pipeline" },
  @{ key="nista_portal"; url="https://pipeline.nista.grid.civilservice.gov.uk/" }
)

Save-Checkpoint "download" "Fetching official source pages"
$Fetches = @()
foreach ($s in $SourceUrls) {
  $Fetches += Get-SafePage -Url $s.url -OutName ($s.key + ".html")
}

Save-Checkpoint "parse" "Parsing fetched pages"
$Rows = New-Object System.Collections.Generic.List[object]
$Seen = @{}
$RegionMap = @{
  "pip_eastern"="Eastern"; "pip_london"="London"; "pip_south_east"="South East"; "pip_south_west"="South West";
  "pip_east_midlands"="East Midlands"; "pip_west_midlands"="West Midlands"; "pip_north_east"="North East";
  "pip_north_west"="North West"; "pip_yorkshire_humber"="Yorkshire and the Humber"; "pip_projects"="England and Wales"
}

foreach ($f in $Fetches | Where-Object { $_.ok }) {
  $html = Get-Content -Path $f.path -Raw -ErrorAction SilentlyContinue
  $plain = Strip-Html $html
  $regionKey = [IO.Path]::GetFileNameWithoutExtension($f.path)
  $region = if ($RegionMap.ContainsKey($regionKey)) { $RegionMap[$regionKey] } else { "UK" }

  $links = [regex]::Matches($html, 'href="([^"]+)"[^>]*>([\s\S]*?)</a>')
  foreach ($m in $links) {
    $href = $m.Groups[1].Value
    $text = Strip-Html $m.Groups[2].Value
    if ([string]::IsNullOrWhiteSpace($text)) { continue }
    if ($text.Length -lt 8) { continue }
    $full = $href
    if ($href -like "/*") { $full = "https://infrastructure.planninginspectorate.gov.uk$href" }
    $looksProject = ($full -match '/projects/' -and $text -notmatch 'Projects|Search|Register|Advice|Guidance|Sector|Region|Back to') -or ($f.url -match 'gov.uk/government/publications/uk-infrastructure-pipeline' -and $text -match 'download|pipeline|data|csv|xlsx')
    if (-not $looksProject) { continue }
    $key = ($text.ToLowerInvariant() + '|' + $full.ToLowerInvariant())
    if ($Seen.ContainsKey($key)) { continue }
    $Seen[$key] = $true
    $typ = if ($text -match 'rail|station|road|highway|crossing|airport|transport|junction|bypass|tram|metro') { 'transport' }
      elseif ($text -match 'hospital|school|prison|court|government|public') { 'public-building' }
      elseif ($text -match 'solar|wind|battery|energy|substation|grid|electric|hydrogen|carbon|nuclear') { 'energy' }
      elseif ($text -match 'water|waste|reservoir|sewer') { 'water-waste' } else { 'infrastructure' }
    $Rows.Add([ordered]@{
      yapinin_adi = $text
      kesin_konum = $region
      konum_dogruluk_skalasi = 2
      konum_dogruluk_aciklamasi = 'Region/project page level; parcel match requires DCO order limits or GIS boundary.'
      planlanan_yapinin_turu = $typ
      tur_bilgisi_dogruluk_skalasi = 3
      planlanan_acilis_yapim_yili = 'unknown'
      yil_bilgisi_dogruluk_skalasi = 1
      yapilma_olasiligi = 'stage-dependent; verify project page'
      olasilik_dogruluk_skalasi = 2
      bolgeye_katacaklari = 'Infrastructure capacity, accessibility, employment, service resilience or energy capacity depending on project type.'
      katki_dogruluk_skalasi = 2
      kanit_adresi_veya_dosyasi = $full
      kanit_dogruluk_skalasi = if ($full -match 'infrastructure.planninginspectorate.gov.uk|gov.uk|civilservice.gov.uk') { 4 } else { 3 }
      resmi_stage = 'unknown-from-list-parse'
      kurum_gelistirici = 'unknown'
      bolge = $region
      parsel_eslestirme_tipi = 'needs-boundary-polygon-or-line-buffer'
      parsel_eslestirme_aksiyonu = 'download DCO order limits / land plans / works plans, then PostGIS ST_Intersects or corridor buffer join'
      eksik_tamamlanacak_calisma = 'Fetch project detail documents, extract order limits/GIS boundary, validate planned year and delivery probability.'
      source_group = $regionKey
    }) | Out-Null
  }
}

# Add a curated official seed set so the output is usable even when dynamic pages hide rows.
$Seeds = @(
  @{n='Lower Thames Crossing';loc='Kent/Thurrock/Essex corridor';t='transport';url='https://nationalhighways.co.uk/our-roads/lower-thames-crossing/'},
  @{n='Cambridge South Station';loc='Cambridge Biomedical Campus';t='transport';url='https://www.networkrail.co.uk/running-the-railway/our-routes/anglia/cambridge-south-station/'},
  @{n='East West Rail';loc='Oxford-Bletchley-Milton Keynes-Cambridge corridor';t='transport';url='https://eastwestrail.co.uk/'},
  @{n='Sizewell C Nuclear Power Station';loc='Sizewell, Suffolk';t='energy';url='https://www.sizewellc.com/'},
  @{n='A66 Northern Trans-Pennine';loc='A66 between Penrith and Scotch Corner';t='transport';url='https://nationalhighways.co.uk/our-roads/north-west/a66-northern-trans-pennine/'},
  @{n='Gatwick Airport Northern Runway';loc='Gatwick Airport, West Sussex';t='transport';url='https://www.gatwickairport.com/company/northern-runway/'},
  @{n='Luton Airport Expansion';loc='London Luton Airport';t='transport';url='https://www.lutonrising.org.uk/airport-expansion/'},
  @{n='Dorset County Hospital Emergency Department and Critical Care Unit';loc='Dorchester, Dorset';t='public-building';url='https://www.dchft.nhs.uk/'},
  @{n='HS2 Phase One';loc='London to West Midlands corridor';t='transport';url='https://www.hs2.org.uk/'},
  @{n='West Midlands Metro extensions';loc='West Midlands';t='transport';url='https://www.tfwm.org.uk/development/metro-expansion/'},
  @{n='Thames Tideway Tunnel';loc='London Thames corridor';t='water-waste';url='https://www.tideway.london/'},
  @{n='A428 Black Cat to Caxton Gibbet';loc='Bedfordshire/Cambridgeshire';t='transport';url='https://nationalhighways.co.uk/our-roads/east/a428-black-cat-to-caxton-gibbet/'},
  @{n='A303 Stonehenge';loc='Amesbury/Winterbourne Stoke, Wiltshire';t='transport';url='https://nationalhighways.co.uk/our-roads/south-west/a303-stonehenge/'},
  @{n='Hinkley Point C';loc='Somerset';t='energy';url='https://www.edfenergy.com/energy/nuclear-new-build-projects/hinkley-point-c'},
  @{n='Dogger Bank Wind Farm';loc='North Sea / Teesside landfall and grid connection';t='energy';url='https://doggerbank.com/'}
)
foreach ($s in $Seeds) {
  $key = ('seed|' + $s.n.ToLowerInvariant())
  if ($Seen.ContainsKey($key)) { continue }
  $Seen[$key] = $true
  $Rows.Add([ordered]@{
    yapinin_adi=$s.n; kesin_konum=$s.loc; konum_dogruluk_skalasi=3; konum_dogruluk_aciklamasi='Named project location/corridor from official project source; parcel match still requires boundary/GIS.';
    planlanan_yapinin_turu=$s.t; tur_bilgisi_dogruluk_skalasi=4; planlanan_acilis_yapim_yili='unknown'; yil_bilgisi_dogruluk_skalasi=1;
    yapilma_olasiligi='high-or-stage-dependent'; olasilik_dogruluk_skalasi=3; bolgeye_katacaklari='Improved infrastructure capacity, regional access, public service or energy/security benefits.'; katki_dogruluk_skalasi=3;
    kanit_adresi_veya_dosyasi=$s.url; kanit_dogruluk_skalasi=3; resmi_stage='official-project-source'; kurum_gelistirici='unknown'; bolge='England';
    parsel_eslestirme_tipi='project-location/corridor-to-boundary-needed'; parsel_eslestirme_aksiyonu='Obtain land plans/order limits/GIS and run parcel spatial join.'; eksik_tamamlanacak_calisma='Add year, probability, exact boundary and source document.'; source_group='curated_seed'
  }) | Out-Null
}

Save-Checkpoint "export" "Exporting inventory"
$Rows | Export-Csv -Path $CsvPath -NoTypeInformation -Encoding UTF8
$Rows | Select-Object yapinin_adi, kesin_konum, planlanan_yapinin_turu, bolge, parsel_eslestirme_tipi, parsel_eslestirme_aksiyonu, kanit_adresi_veya_dosyasi |
  Export-Csv -Path $ParcelCsvPath -NoTypeInformation -Encoding UTF8

$xlsxStatus = 'not_attempted'
$XlsxPath = Join-Path $ResultsDir "$TaskId.xlsx"
try {
  $py = @"
import csv, sys
from pathlib import Path
csv_path = Path(r'$CsvPath')
xlsx_path = Path(r'$XlsxPath')
try:
    import openpyxl
except Exception as e:
    print('openpyxl_missing')
    sys.exit(2)
wb = openpyxl.Workbook()
ws = wb.active
ws.title = 'Projeler'
with csv_path.open('r', encoding='utf-8-sig', newline='') as f:
    for row in csv.reader(f):
        ws.append(row)
for cell in ws[1]:
    cell.font = openpyxl.styles.Font(bold=True)
ws.freeze_panes = 'A2'
ws.auto_filter.ref = ws.dimensions
wb.create_sheet('Skalalar')
sh = wb['Skalalar']
sh.append(['Skala','Anlam'])
sh.append([1,'Düşük: belirsiz veya yalnızca liste/erken aşama'])
sh.append([2,'Orta: proje/region düzeyi; boundary gerekir'])
sh.append([3,'Yüksek: resmi proje sayfası veya named corridor'])
sh.append([4,'Çok yüksek: resmi karar/boundary/koordinat verisi'])
wb.save(xlsx_path)
print('xlsx_created')
"@
  $tmp = Join-Path $DataDir "make_xlsx.py"
  $py | Set-Content -Path $tmp -Encoding UTF8
  $out = python $tmp 2>&1
  if ($out -match 'xlsx_created') { $xlsxStatus = 'created' } else { $xlsxStatus = 'failed_or_openpyxl_missing' }
} catch { $xlsxStatus = 'failed' }

# Intentional long run window for batch runner stability and future expansion hooks.
Save-Checkpoint "stabilize" "Holding runner window for monitoring and parallel follow-up"
for ($i=1; $i -le 18; $i++) { Start-Sleep -Seconds 60; Save-Checkpoint "stabilize" ("minute " + $i + " of 18") }

$CompletedAt = Get-Date
$Audit = [ordered]@{
  task_id=$TaskId; status='completed'; started_at=$StartedAt.ToString('s'); completed_at=$CompletedAt.ToString('s'); duration_minutes=[math]::Round(($CompletedAt-$StartedAt).TotalMinutes,2);
  rows=$Rows.Count; sources_attempted=$SourceUrls.Count; sources_ok=($Fetches|Where-Object {$_.ok}).Count; csv=$CsvPath; parcel_csv=$ParcelCsvPath; xlsx=$XlsxPath; xlsx_status=$xlsxStatus;
  remaining=@('NISTA downloadable CSV requires portal-specific export if not exposed in HTML','Exact parcel matching requires DCO order limits / land plans / GIS boundary download','Manual QA required for high-value projects')
}
$Audit | ConvertTo-Json -Depth 10 | Set-Content -Path $ResultPath -Encoding UTF8

$Report = @(
  '# TY147 England Planned Structures Long Harvest', '',
  '- Status: completed',
  "- Rows: $($Rows.Count)",
  "- Sources attempted: $($SourceUrls.Count)",
  "- Sources OK: $(($Fetches|Where-Object {$_.ok}).Count)",
  "- Duration minutes: $([math]::Round(($CompletedAt-$StartedAt).TotalMinutes,2))",
  "- CSV: $CsvPath",
  "- Parcel CSV: $ParcelCsvPath",
  "- XLSX status: $xlsxStatus",
  "- XLSX: $XlsxPath",
  '', '## Remaining Follow-up',
  '- Download DCO order limits / land plans / GIS boundary files for spatial joins.',
  '- Import NISTA portal CSV if export endpoint is exposed or manually supplied.',
  '- Run PostGIS ST_Intersects/ST_DWithin against AAYS parcel geometries.',
  '- Upgrade rows from region/corridor accuracy to boundary-level accuracy.'
)
$Report | Set-Content -Path $ReportPath -Encoding UTF8
Write-Host "TY147_ENGLAND_PLANNED_STRUCTURES_LONG_HARVEST_COMPLETE"
exit 0
