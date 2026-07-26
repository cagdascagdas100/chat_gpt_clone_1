$ErrorActionPreference = 'Stop'
$repo = $env:AAYS_REPO_ROOT
if ([string]::IsNullOrWhiteSpace($repo)) { $repo = 'F:\chatgpt\chat_gpt_clone_1_main' }
$page = Join-Path $repo 'england_map_web\geometry_review_2of4_20260629.html'
Push-Location $repo
try {
  $cur = Get-Content -Raw -LiteralPath $page
  if ($cur -match 'id="reviewTable"' -or $cur -match 'Satir satir review tablosu') {
    Write-Output 'TABLE_ALREADY_PRESENT'
    exit 0
  }
  $old = $null
  try { $old = git show 85985c28f22637c358f9b8910d46890c62d367aa } catch {}
  if ([string]::IsNullOrWhiteSpace($old)) { $old = git show b4b3f7c0b:england_map_web/geometry_review_2of4_20260629.html }
  $m = [regex]::Match($old, '<table>[\s\S]*?</table>')
  if (!$m.Success) { throw 'old review table not found' }
  $table = $m.Value -replace '<table>', '<table id="reviewTable">'
  $insert = "`r`n<h2>Satir satir review tablosu</h2>`r`n<p class="muted">Eski islenen satir tablosu geri eklendi; kanit/geometri paneli korunmustur.</p>`r`n<div class="table-wrap">$table</div>`r`n"
  $cur = $cur -replace '</body>', ($insert + '</body>')
  $cur = $cur -replace 'table\{border-collapse:collapse;width:100%;background:white;margin-top:10px\}', 'table{border-collapse:collapse;width:100%;background:white;margin-top:10px}.table-wrap{max-width:100%;overflow-x:auto;border:1px solid #cbd5e1;border-radius:10px;background:white;margin-top:10px}#reviewTable{min-width:1500px;font-size:12px}'
  Set-Content -LiteralPath $page -Value $cur -Encoding UTF8
  git add england_map_web/geometry_review_2of4_20260629.html
  git commit -m 'Restore row review table under dashboard'
  git push origin main
  Write-Output 'ROW_REVIEW_TABLE_RESTORED'
} finally { Pop-Location }
