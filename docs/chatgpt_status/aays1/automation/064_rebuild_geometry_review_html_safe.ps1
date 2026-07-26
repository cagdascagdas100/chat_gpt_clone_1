$ErrorActionPreference = 'Stop'
$repo = $env:AAYS_REPO_ROOT
if ([string]::IsNullOrWhiteSpace($repo)) { $repo = 'F:\chatgpt\chat_gpt_clone_1_main' }
$csv = Join-Path $repo 'england_map_web\data\geometry_review_2of4_20260629\TerraYield_2OF4_Geometry_Review_Queue_20260629.csv'
$out = Join-Path $repo 'england_map_web\geometry_review_2of4_20260629.html'
if (!(Test-Path $csv)) { throw "missing csv: $csv" }
$rows = Import-Csv -LiteralPath $csv | Select-Object -First 275
function H([object]$v) { [System.Net.WebUtility]::HtmlEncode([string]$v) }
$trs = New-Object System.Collections.Generic.List[string]
$i = 0
foreach ($r in $rows) {
  $i++
  $url = [string]($r.source_url ?? $r.url ?? $r.listing_url ?? $r.'Listing / Source URL')
  if ([string]::IsNullOrWhiteSpace($url)) { $url = [string]($r.PSObject.Properties.Value | Where-Object { $_ -match '^https?://' } | Select-Object -First 1) }
  $title = [string]($r.title ?? $r.baslik ?? $r.address ?? $r.'Baslik / Adres')
  if ([string]::IsNullOrWhiteSpace($title)) { $title = 'Land / Plot source row' }
  $loc = [string]($r.postcode ?? $r.location ?? $r.konum ?? $r.'Konum')
  $lat = [string]($r.lat ?? $r.latitude ?? $r.centroid_lat ?? $r.Centroid)
  $safeUrl = H $url
  $link = if ($url -match '^https?://') { "<a href='$safeUrl' target='_blank' rel='noopener noreferrer'>$safeUrl</a>" } else { '' }
  $trs.Add("<tr><td>$i</td><td>OnTheMarket</td><td>$link</td><td>$(H $title)</td><td></td><td></td><td>$(H $loc)</td><td>$(H $lat)</td><td></td><td>PENDING_SOURCE_REVIEW</td><td></td><td>KEEP_2OF4_PENDING_SOURCE_REVIEW</td><td>Safe rebuild; fake polygon yok.</td></tr>")
}
$html = @"
<!doctype html>
<html lang="tr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>TerraYield 2/4 Satis Parsel Geometry Review</title>
<style>
body{font-family:Arial,sans-serif;margin:20px;background:#f8fafc;color:#111827}.panel{border:2px solid #2563eb;background:#eff6ff;padding:14px;border-radius:10px;margin-bottom:14px}.warn{border:1px solid #f59e0b;background:#fffbeb;padding:12px;border-radius:8px;margin-bottom:14px}.toolbar{display:flex;gap:10px;align-items:center;flex-wrap:wrap;margin:12px 0}.toolbar input{min-width:260px;padding:8px;border:1px solid #94a3b8;border-radius:8px}.table-wrap{max-width:100%;overflow-x:auto;border:1px solid #cbd5e1;border-radius:10px;background:white}table{border-collapse:collapse;width:100%;min-width:1500px;font-size:12px;background:white}th,td{border:1px solid #cbd5e1;padding:6px;vertical-align:top}th{background:#e5e7eb;position:sticky;top:0}a{color:#1d4ed8}.hidden-row{display:none}.muted{color:#64748b;font-size:12px}
</style>
</head>
<body>
<div class="panel"><h1>AAYS / TerraYield 2/4 Satis Parsel Geometry Review</h1><p><b>Toplam queue:</b> 1264</p><p><b>Tabloda gosterilen:</b> $($rows.Count)</p><p><b>Durum:</b> Site safe rebuild ile duzeltildi. Source/evidence review kademeli suruyor.</p><p><b>Final:</b> false</p></div>
<div class="warn">Sahte polygon yok. Bu asama 2/4 kaynak kontrol ekranidir; resmi boundary kaniti olmadan final kabul yok.</div>
<div class="toolbar"><input id="reviewSearch" type="search" placeholder="Satir, posta kodu veya link ara..."><span id="visibleCount" class="muted"></span></div>
<div class="table-wrap"><table id="reviewTable"><thead><tr><th>#</th><th>Site</th><th>Listing / Source URL</th><th>Baslik / Adres</th><th>Fiyat</th><th>Alan</th><th>Konum</th><th>Centroid</th><th>BBox</th><th>Source status</th><th>Evidence path</th><th>Karar</th><th>Gerekce</th></tr></thead><tbody>
$($trs -join "`n")
</tbody></table></div>
<script>(function(){const q=document.getElementById('reviewSearch'),t=document.getElementById('reviewTable'),o=document.getElementById('visibleCount');if(!q||!t||!o)return;const rows=Array.from(t.querySelectorAll('tbody tr'));function apply(){const n=q.value.trim().toLowerCase();let s=0;rows.forEach(r=>{const hit=!n||r.textContent.toLowerCase().includes(n);r.classList.toggle('hidden-row',!hit);if(hit)s++;});o.textContent=s+' / '+rows.length+' satir gosteriliyor';}q.addEventListener('input',apply);apply();})();</script>
</body>
</html>
"@
Set-Content -LiteralPath $out -Value $html -Encoding UTF8
Push-Location $repo
try { git add england_map_web/geometry_review_2of4_20260629.html; git commit -m 'Rebuild geometry review page safely'; git push origin main } finally { Pop-Location }
Write-Output 'SAFE_REBUILD_DONE'
