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
  $old = git show 85985c28f22637c358f9b8910d46890c62d367aa
  $m = [regex]::Match($old, '<table>[\s\S]*?</table>')
  if (!$m.Success) { throw 'old review table not found' }
  $table = $m.Value -replace '<table>', '<table id="reviewTable">'
  $insertTemplate = @'
<h2>Satir satir review tablosu</h2>
<p class="muted">Eski islenen satir tablosu geri eklendi; kanit/geometri paneli korunmustur.</p>
<div class="table-wrap">
__OLD_TABLE__
</div>
'@
  $insert = $insertTemplate.Replace('__OLD_TABLE__', $table)
  if ($cur -notmatch 'table-wrap') {
    $cur = $cur -replace '</style>', '.table-wrap{max-width:100%;overflow-x:auto;border:1px solid #cbd5e1;border-radius:10px;background:white;margin-top:10px}#reviewTable{min-width:1500px;font-size:12px}</style>'
  }
  $cur = $cur -replace '</body>', ($insert + "`r`n</body>")
  Set-Content -LiteralPath $page -Value $cur -Encoding UTF8
  git add england_map_web/geometry_review_2of4_20260629.html
  git commit -m 'Restore row review table under dashboard safe'
  git push origin main
  Write-Output 'ROW_REVIEW_TABLE_RESTORED_SAFE'
} finally {
  Pop-Location
}
