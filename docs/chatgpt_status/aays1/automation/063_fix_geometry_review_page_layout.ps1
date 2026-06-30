$ErrorActionPreference = 'Stop'
$repo = $env:AAYS_REPO_ROOT
if ([string]::IsNullOrWhiteSpace($repo)) { $repo = 'F:\chatgpt\chat_gpt_clone_1_main' }
$page = Join-Path $repo 'england_map_web\geometry_review_2of4_20260629.html'
if (!(Test-Path $page)) { throw "missing page: $page" }
$html = Get-Content -Raw -LiteralPath $page
$orig = $html

$css = @'
    .meta-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 8px; margin-top: 10px; }
    .meta-card { background: white; border: 1px solid #bfdbfe; border-radius: 8px; padding: 10px; }
    .toolbar { display: flex; gap: 10px; align-items: center; flex-wrap: wrap; margin: 12px 0; }
    .toolbar input { min-width: 260px; padding: 8px; border: 1px solid #94a3b8; border-radius: 8px; }
    .table-wrap { max-width: 100%; overflow-x: auto; border: 1px solid #cbd5e1; border-radius: 10px; background: white; }
    #reviewTable { min-width: 1500px; }
    #reviewTable tr.hidden-row { display: none; }
    .muted { color: #64748b; font-size: 12px; }
'@
if ($html -notmatch 'class="table-wrap"') {
  $html = $html.Replace('</style>', "$css`r`n  </style>")
}

$html = $html -replace 'F:\\chatgpt\\chat_gpt_clone_1_main\\england_map_web\\data\\geometry_review_2of4_20260629\\TerraYield_2OF4_Geometry_Review_Queue_20260629\.csv','england_map_web/data/geometry_review_2of4_20260629/TerraYield_2OF4_Geometry_Review_Queue_20260629.csv'
$html = $html -replace "target='_blank'", "target='_blank' rel='noopener noreferrer'"

if ($html -notmatch 'id="reviewSearch"') {
  $toolbar = @'
<div class="toolbar">
  <input id="reviewSearch" type="search" placeholder="Satir, posta kodu veya link ara...">
  <span id="visibleCount" class="muted"></span>
</div>
<div class="table-wrap">
'@
  $html = [regex]::Replace($html, '<table>', ($toolbar + "`r`n<table id=\"reviewTable\">"), 1)
  $script = @'
</table>
</div>
<script>
(function(){
  const q = document.getElementById('reviewSearch');
  const table = document.getElementById('reviewTable');
  const out = document.getElementById('visibleCount');
  if (!q || !table || !out) return;
  const rows = Array.from(table.querySelectorAll('tbody tr'));
  function apply(){
    const needle = q.value.trim().toLowerCase();
    let shown = 0;
    rows.forEach(function(row){
      const hit = !needle || row.textContent.toLowerCase().includes(needle);
      row.classList.toggle('hidden-row', !hit);
      if (hit) shown += 1;
    });
    out.textContent = shown + ' / ' + rows.length + ' satir gosteriliyor';
  }
  q.addEventListener('input', apply);
  apply();
})();
</script>
'@
  $html = [regex]::Replace($html, '</table>\s*</body>', ($script + "`r`n</body>"), 1)
}

if ($html -eq $orig) {
  Write-Output 'NO_CHANGE'
  exit 0
}
$backup = $page + '.bak_063_' + (Get-Date -Format 'yyyyMMdd_HHmmss')
Set-Content -LiteralPath $backup -Value $orig -Encoding UTF8
Set-Content -LiteralPath $page -Value $html -Encoding UTF8
Push-Location $repo
try {
  git add england_map_web/geometry_review_2of4_20260629.html
  git commit -m 'Fix geometry review page layout'
  git push origin main
} finally {
  Pop-Location
}
Write-Output 'FIXED_GEOMETRY_REVIEW_PAGE_LAYOUT'
