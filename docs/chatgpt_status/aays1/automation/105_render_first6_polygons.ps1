$Repo = $env:AAYS_REPO_ROOT
if (!$Repo) { $Repo = 'F:\chatgpt\chat_gpt_clone_1_main' }
$PolyRoot = Join-Path $Repo 'england_map_web\data\geometry_review_3of4\first6_assets'
$Base = Join-Path $Repo 'docs\chatgpt_status\aays1'
$Tasks = Join-Path $Base 'runner_tasks'
$Reports = Join-Path $Base 'reports'
$Status = Join-Path $Base 'status'
New-Item -ItemType Directory -Force $PolyRoot,$Tasks,$Reports,$Status | Out-Null
$stamp = Get-Date -Format 'yyyyMMdd_HHmmss'
$geoPath = Join-Path $Repo 'docs\chatgpt_status\aays1\geometry_review_3of4\all_1264_real_geometry_3of4.geojson'
$geo = Get-Content $geoPath -Raw | ConvertFrom-Json
$items = @()
foreach ($row in @(1,2,3,4,5,6)) {
  $f = $geo.features[$row-1]
  $ring = $f.geometry.coordinates[0][0]
  $xs = @(); $ys = @()
  foreach ($p in $ring) { $xs += [double]$p[0]; $ys += [double]$p[1] }
  $minx = ($xs | Measure-Object -Minimum).Minimum; $maxx = ($xs | Measure-Object -Maximum).Maximum
  $miny = ($ys | Measure-Object -Minimum).Minimum; $maxy = ($ys | Measure-Object -Maximum).Maximum
  $pts = @()
  foreach ($p in $ring) {
    $x = 20 + (([double]$p[0] - $minx) / (($maxx - $minx) + 0.000000001)) * 360
    $y = 230 - (([double]$p[1] - $miny) / (($maxy - $miny) + 0.000000001)) * 200
    $pts += (('{0:0.0},{1:0.0}' -f $x,$y))
  }
  $target = Join-Path $PolyRoot ("row_{0}_existing_polygon.svg" -f $row)
  $svg = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 260"><rect width="400" height="260" fill="white"/><polygon points="' + ($pts -join ' ') + '" fill="none" stroke="black" stroke-width="4"/><text x="12" y="250" font-size="13">row ' + $row + '</text></svg>'
  $svg | Set-Content -Encoding UTF8 $target
  $items += [ordered]@{ row=$row; target=$target; status='rendered' }
}
$out = [ordered]@{ page_key='aays1'; task_id='105_render_first6_polygons'; final_ready=$false; rendered=6; rows=$items; web_asset_folder=$PolyRoot }
$json = $out | ConvertTo-Json -Depth 6
$json | Set-Content -Encoding UTF8 (Join-Path $Tasks "first6_polygon_render_$stamp.json")
@"
# First6 Polygon Render

rendered: 6
final_ready: false
"@ | Set-Content -Encoding UTF8 (Join-Path $Reports "105_first6_polygon_render_$stamp.md")
@"
PAGE_KEY=aays1
TASK_ID=105_render_first6_polygons
STATUS=done
RENDERED=6
FINAL_READY=false
"@ | Set-Content -Encoding UTF8 (Join-Path $Status "105_first6_polygon_render_status_$stamp.txt")
Write-Host "first6 polygon render complete 6"
