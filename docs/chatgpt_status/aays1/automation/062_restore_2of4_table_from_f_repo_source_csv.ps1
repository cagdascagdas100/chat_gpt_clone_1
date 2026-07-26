$ErrorActionPreference = "Stop"

$RepoRoot = "F:\chatgpt\chat_gpt_clone_1_main"
$BridgeRoot = "F:\AAYS_GITHUB_BRIDGE_CLEAN2"
$Worktree = "F:\chatgpt\aays_2of4_table_restore_worktree"
$Branch = "aays-2of4-table-restore"
$Stamp = Get-Date -Format "yyyyMMdd_HHmmss"

function HtmlEsc($v) {
  if ($null -eq $v) { return "" }
  return [System.Net.WebUtility]::HtmlEncode([string]$v)
}

function FirstVal($row, [string[]]$names) {
  foreach ($n in $names) {
    if ($row.PSObject.Properties.Name -contains $n) {
      $v = $row.$n
      if ($null -ne $v -and "$v".Trim() -ne "") { return "$v" }
    }
  }
  return ""
}

Set-Location $RepoRoot
git fetch origin main
if ($LASTEXITCODE -ne 0) { throw "fetch origin main failed" }

if (!(Test-Path "$Worktree\.git")) {
  if (Test-Path $Worktree) { Remove-Item -Recurse -Force $Worktree }
  git worktree add -B $Branch $Worktree origin/main
  if ($LASTEXITCODE -ne 0) { throw "worktree add failed" }
}

Set-Location $Worktree
git fetch origin main
if ($LASTEXITCODE -ne 0) { throw "worktree fetch failed" }
git reset --hard origin/main
if ($LASTEXITCODE -ne 0) { throw "worktree reset failed" }

$DataDir = "F:\chatgpt\chat_gpt_clone_1_main\england_map_web\data\geometry_review_2of4_20260629"
$QueueCsv = Get-ChildItem $DataDir -File -ErrorAction Stop |
  Where-Object { $_.Name -like '*2OF4*Geometry*Review*Queue*20260629*.csv' -or $_.Name -like '*Geometry_Review_Queue*.csv' } |
  Sort-Object LastWriteTime -Descending |
  Select-Object -First 1

$StatusDir = "docs\chatgpt_status\aays1\status"
$ReportDir = "docs\chatgpt_status\aays1\reports"
$OutDir = "docs\chatgpt_status\aays1\geometry_review_2of4_20260629"
New-Item -ItemType Directory -Force -Path $StatusDir,$ReportDir,$OutDir | Out-Null

if (!$QueueCsv) {
  "status=BLOCKED_SOURCE_QUEUE_NOT_FOUND`nfinal_ready=false`ndata_dir=$DataDir`nupdated_at=$Stamp" | Set-Content -Encoding UTF8 "$StatusDir\062_source_queue_missing_$Stamp.txt"
  "# 062 Source Queue Missing`n`nNo fake rows generated. Required 2/4 queue CSV was not found in F repo data dir." | Set-Content -Encoding UTF8 "$ReportDir\062_source_queue_missing_$Stamp.md"
  git add -- docs/chatgpt_status/aays1/status docs/chatgpt_status/aays1/reports
  git commit -m "Report missing 2of4 source queue in F repo data dir"
  git pull --rebase origin main
  git push origin HEAD:main
  throw "SOURCE_QUEUE_NOT_FOUND"
}

$Rows = Import-Csv $QueueCsv.FullName
if (!$Rows -or $Rows.Count -eq 0) { throw "Queue CSV is empty: $($QueueCsv.FullName)" }

$Batch = $Rows | Select-Object -First 275
$Results = New-Object System.Collections.Generic.List[object]
for ($i = 0; $i -lt $Batch.Count; $i++) {
  $row = $Batch[$i]
  $Results.Add([pscustomobject]@{
    row_index = $i + 1
    site = FirstVal $row @("site","source_site","listing_site","agent","source","Site")
    listing_url = FirstVal $row @("listing_url","source_url","url","Listing URL","Source URL")
    title_or_address = FirstVal $row @("title","name","address","property_address","description","Title","Address")
    price = FirstVal $row @("price","asking_price","sale_price","Price")
    area = FirstVal $row @("area","area_sq_m","area_acres","land_area","plot_size","Area")
    location = FirstVal $row @("location","postcode","lat_lon","centroid","address","Location")
    candidate_centroid = FirstVal $row @("centroid","candidate_centroid","lat","lon","latitude","longitude")
    candidate_bbox = FirstVal $row @("bbox","candidate_bbox","bounding_box")
    source_fetch_status = "NOT_FETCHED_TABLE_RESTORE_ONLY"
    evidence_path = ""
    review_decision = "KEEP_2OF4_PENDING_SOURCE_REVIEW"
    corrected_polygon_geojson = ""
    do_not_upgrade_reason = "Kaynak CSVden tabloya alindi; kaynak site/evidence incelemesi sonraki batchte yapilacak. Fake polygon yok."
  })
}

$UpdatesCsv = "$OutDir\TerraYield_2OF4_Geometry_Review_Updates_Template_20260629.csv"
$Results | Export-Csv -NoTypeInformation -Encoding UTF8 $UpdatesCsv

$tableRows = New-Object System.Text.StringBuilder
foreach ($r in $Results) {
  $url = HtmlEsc $r.listing_url
  [void]$tableRows.AppendLine("<tr><td>$(HtmlEsc $r.row_index)</td><td>$(HtmlEsc $r.site)</td><td><a href='$url' target='_blank'>$url</a></td><td>$(HtmlEsc $r.title_or_address)</td><td>$(HtmlEsc $r.price)</td><td>$(HtmlEsc $r.area)</td><td>$(HtmlEsc $r.location)</td><td>$(HtmlEsc $r.candidate_centroid)</td><td>$(HtmlEsc $r.candidate_bbox)</td><td>$(HtmlEsc $r.source_fetch_status)</td><td>$(HtmlEsc $r.evidence_path)</td><td>$(HtmlEsc $r.review_decision)</td><td>$(HtmlEsc $r.do_not_upgrade_reason)</td></tr>")
}

$HtmlPath = "england_map_web\geometry_review_2of4_20260629.html"
New-Item -ItemType Directory -Force -Path (Split-Path $HtmlPath) | Out-Null
$queueCsvEsc = HtmlEsc $QueueCsv.FullName
@"
<!doctype html>
<html lang="tr">
<head>
  <meta charset="utf-8">
  <title>TerraYield 2/4 Satis Parsel Geometry Review</title>
  <style>
    body { font-family: Arial, sans-serif; margin: 20px; background: #f8fafc; color: #111827; }
    .panel { border: 2px solid #2563eb; background: #eff6ff; padding: 14px; border-radius: 10px; margin-bottom: 14px; }
    .warn { border: 1px solid #f59e0b; background: #fffbeb; padding: 12px; border-radius: 8px; margin-bottom: 14px; }
    table { border-collapse: collapse; width: 100%; font-size: 12px; background: white; }
    th, td { border: 1px solid #cbd5e1; padding: 6px; vertical-align: top; }
    th { background: #e5e7eb; position: sticky; top: 0; }
    a { color: #1d4ed8; }
  </style>
</head>
<body>
<div class="panel">
  <h1>AAYS / TerraYield 2/4 Satis Parsel Geometry Review</h1>
  <p><b>Toplam queue:</b> $($Rows.Count)</p>
  <p><b>Tabloda gosterilen:</b> $($Results.Count)</p>
  <p><b>Durum:</b> Tablo F repo kaynak CSVden geri yuklendi. Source/evidence review sonraki batchte yapilacak.</p>
  <p><b>Kaynak CSV:</b> $queueCsvEsc</p>
  <p><b>Final:</b> false</p>
</div>
<div class="warn">
  Sahte polygon yok. Bu asama tablo restorasyonudur; parsel siniri yukseltmesi icin source URL/evidence/resmi boundary kaniti gerekir.
</div>
<table>
<thead>
<tr>
<th>#</th><th>Site</th><th>Listing / Source URL</th><th>Baslik / Adres</th><th>Fiyat</th><th>Alan</th><th>Konum</th><th>Centroid</th><th>BBox</th><th>Source status</th><th>Evidence path</th><th>Karar</th><th>Gerekce</th>
</tr>
</thead>
<tbody>
$tableRows
</tbody>
</table>
</body>
</html>
"@ | Set-Content -Encoding UTF8 $HtmlPath

"status=TABLE_RESTORED_FROM_F_REPO_SOURCE_CSV`nfinal_ready=false`nqueue_total=$($Rows.Count)`nrows_visible=$($Results.Count)`nsource_csv=$($QueueCsv.FullName)`nupdates_csv=$UpdatesCsv`nupdated_at=$Stamp" | Set-Content -Encoding UTF8 "$StatusDir\062_table_restored_from_f_repo_source_csv_$Stamp.txt"

"# 062 Table Restored From F Repo Source CSV`n`nstatus: TABLE_RESTORED_FROM_F_REPO_SOURCE_CSV`nqueue_total: $($Rows.Count)`nrows_visible: $($Results.Count)`nsource_csv: $($QueueCsv.FullName)`nupdates_csv: $UpdatesCsv`n`nNo fake rows. No fake polygon. No DB write. No migration. No DDL. No deploy." | Set-Content -Encoding UTF8 "$ReportDir\062_table_restored_from_f_repo_source_csv_$Stamp.md"

git add -- england_map_web/geometry_review_2of4_20260629.html docs/chatgpt_status/aays1/geometry_review_2of4_20260629 docs/chatgpt_status/aays1/status docs/chatgpt_status/aays1/reports
git commit -m "Restore 2of4 sales parcel review table from F repo source CSV"
if ($LASTEXITCODE -ne 0) { Write-Host "No commit created or commit failed; continuing to push/status." }
git pull --rebase origin main
git push origin HEAD:main

$LocalHtml = "F:\chatgpt\chat_gpt_clone_1_main\england_map_web\geometry_review_2of4_20260629.html"
New-Item -ItemType Directory -Force -Path (Split-Path $LocalHtml) | Out-Null
Copy-Item -Force $HtmlPath $LocalHtml

"status=OK`nfinal_ready=false`nqueue_total=$($Rows.Count)`nrows_visible=$($Results.Count)`nsource_csv=$($QueueCsv.FullName)`nupdated_at=$Stamp" | Set-Content -Encoding UTF8 "$BridgeRoot\ai-results\terrayield_062_restore_2of4_table_from_f_repo_source_csv.result.txt"
exit 0
