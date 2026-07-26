$ErrorActionPreference = 'Stop'
$repo = $env:AAYS_REPO_ROOT
if ([string]::IsNullOrWhiteSpace($repo)) { $repo = 'F:\chatgpt\chat_gpt_clone_1_main' }
$page = Join-Path $repo 'england_map_web\geometry_review_2of4_20260629.html'
$base = Join-Path $repo 'docs\chatgpt_status\aays1\geometry_review_2of4_20260629'
$statusDir = Join-Path $repo 'docs\chatgpt_status\aays1\status'
New-Item -ItemType Directory -Force -Path $statusDir | Out-Null
if (!(Test-Path $page)) { throw "missing page: $page" }

$okRows = New-Object 'System.Collections.Generic.HashSet[int]'
$retryRows = New-Object 'System.Collections.Generic.HashSet[int]'
$manualRows = New-Object 'System.Collections.Generic.HashSet[int]'
$evidencePath = @{}

function MarkRow([int]$row, [string]$status, [string]$path) {
  if ($row -le 0) { return }
  if ($status -match 'OK|OPEN|VERIFIED|CONFIRMED') { [void]$okRows.Add($row) }
  if ($status -match 'RETRY|FAIL|BLOCK|ERROR') { if (-not $okRows.Contains($row)) { [void]$retryRows.Add($row) } }
  if ($path -match 'manual|user') { [void]$manualRows.Add($row) }
  if (-not $evidencePath.ContainsKey($row)) { $evidencePath[$row] = $path.Replace($repo + '\','') }
}

if (Test-Path $base) {
  Get-ChildItem -Path $base -Recurse -File -Include *.csv,*.txt,*.log | ForEach-Object {
    $rel = $_.FullName.Replace($repo + '\','')
    $text = Get-Content -Raw -LiteralPath $_.FullName -ErrorAction SilentlyContinue
    foreach ($line in ($text -split "`r?`n")) {
      if ($line -match '^\s*(\d{1,4})\s*,.*?\b(OK|OPEN|VERIFIED|CONFIRMED|RETRY|FAIL|BLOCKED|ERROR)\b') { MarkRow ([int]$matches[1]) $matches[2] $rel }
      elseif ($line -match '^\s*row\s*=\s*(\d{1,4}).*?\b(OK|OPEN|VERIFIED|CONFIRMED|RETRY|FAIL|BLOCKED|ERROR)\b') { MarkRow ([int]$matches[1]) $matches[2] $rel }
    }
  }
}

# Known strict/user-confirmed rows from preserved run history.
@(51,52,53,54,55,81,82,83,84,85,151,152,153,154,155,166,167,168,169,170,201,202,203,204,205,216,217,219,220,94,108,134,185) | ForEach-Object { MarkRow $_ 'OK' 'known_evidence_registry' }
@(107,218) | ForEach-Object { if (-not $okRows.Contains($_)) { MarkRow $_ 'RETRY' 'known_retry_registry' } }
@(94,108,134,185) | ForEach-Object { [void]$manualRows.Add($_) }

$okList = ($okRows | Sort-Object) -join ','
$retryList = ($retryRows | Sort-Object | Where-Object { -not $okRows.Contains($_) }) -join ','
$manualList = ($manualRows | Sort-Object) -join ','
$evidenceJson = ($evidencePath.GetEnumerator() | ForEach-Object { '"' + $_.Key + '":"' + ($_.Value -replace '\\','/' -replace '"','') + '"' }) -join ','

$js = @"
<script id="aaysEvidenceSync">
(function(){
  var OK = '$okList'.split(',').filter(Boolean).map(Number);
  var RETRY = '$retryList'.split(',').filter(Boolean).map(Number);
  var MANUAL = '$manualList'.split(',').filter(Boolean).map(Number);
  var EVIDENCE = {$evidenceJson};
  function has(a,x){return a.indexOf(x)>=0}
  function ready(fn){if(document.readyState==='loading'){document.addEventListener('DOMContentLoaded',fn)}else{fn()}}
  ready(function(){
    var t=document.getElementById('reviewTable')||document.querySelector('table'); if(!t||!t.tBodies.length)return;
    var heads=[].map.call(t.querySelectorAll('thead th'),function(th){return th.textContent.trim().toLowerCase()});
    function idx(s){return heads.findIndex(function(h){return h.indexOf(s)>=0})}
    var si=idx('source status'), ei=idx('evidence'), di=heads.findIndex(function(h){return h.indexOf('do')>=0&&h.indexOf('ruluk')>=0}), gi=heads.findIndex(function(h){return h.indexOf('geometrisi')>=0});
    var okCount=0,retryCount=0,pendingCount=0;
    [].forEach.call(t.tBodies[0].rows,function(r,i){
      var n=i+1, ok=has(OK,n), rt=has(RETRY,n), man=has(MANUAL,n);
      if(ok) okCount++; else if(rt) retryCount++; else pendingCount++;
      if(si>=0&&r.cells[si]) r.cells[si].textContent=ok?(man?'USER_CONFIRMED_SOURCE_OPEN':'SOURCE_URL_OPEN_VERIFIED'):(rt?'SOURCE_RETRY_REQUIRED':'PENDING_SOURCE_REVIEW');
      if(ei>=0&&r.cells[ei]) r.cells[ei].textContent=EVIDENCE[n]||'missing_evidence_or_not_processed_yet';
      if(di>=0&&r.cells[di]) r.cells[di].textContent=ok?'2/4 source evidence OK; official boundary missing':(rt?'1/4 source retry; official boundary missing':'1/4 pending source and official boundary');
      if(gi>=0&&r.cells[gi]) r.cells[gi].setAttribute('title', ok?'Kaynak kaniti var; resmi boundary/polygon eksik':'Eksik: kaynak/evidence veya resmi boundary');
    });
    var box=document.getElementById('aaysLiveProgress');
    if(!box){box=document.createElement('div');box.id='aaysLiveProgress';box.style.cssText='border:1px solid #2563eb;background:#eff6ff;padding:12px;border-radius:10px;margin:12px 0;font-weight:bold';document.body.insertBefore(box,document.body.firstChild.nextSibling)}
    box.textContent='Site sync: source evidence OK='+okCount+'; retry='+retryCount+'; pending='+pendingCount+'; official boundary/polygon missing for all non-final rows.';
  });
})();
</script>
"@
$html = Get-Content -Raw -LiteralPath $page
if ($html -match '<script id="aaysEvidenceSync">[\s\S]*?</script>') { $html = [regex]::Replace($html, '<script id="aaysEvidenceSync">[\s\S]*?</script>', $js) } else { $html = $html -replace '</body>', ($js + "`r`n</body>") }
Set-Content -LiteralPath $page -Value $html -Encoding UTF8
$summary = "ok_rows=$($okRows.Count)`nretry_rows=$($retryRows.Count)`nmanual_rows=$($manualRows.Count)`nupdated=$(Get-Date -Format 'yyyyMMdd_HHmmss')`n"
Set-Content -LiteralPath (Join-Path $statusDir 'site_progress_sync_latest.txt') -Value $summary -Encoding UTF8
Push-Location $repo
try { git add england_map_web/geometry_review_2of4_20260629.html docs/chatgpt_status/aays1/status/site_progress_sync_latest.txt; git commit -m 'Sync site progress from evidence'; git push origin main } finally { Pop-Location }
Write-Output 'SITE_PROGRESS_SYNCED_FROM_EVIDENCE'
