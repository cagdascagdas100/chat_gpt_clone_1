$ErrorActionPreference = 'Stop'
$repo = $env:AAYS_REPO_ROOT
if ([string]::IsNullOrWhiteSpace($repo)) { $repo = 'F:\chatgpt\chat_gpt_clone_1_main' }
$page = Join-Path $repo 'england_map_web\geometry_review_2of4_20260629.html'
if (!(Test-Path $page)) { throw "missing page: $page" }
$html = Get-Content -Raw -LiteralPath $page
$js = @'
<script>
(function(){
  var sourceOk=[51,52,53,54,55,81,82,83,84,85,151,152,153,154,155,166,167,168,169,170,201,202,203,204,205,216,217,219,220,94,108,134,185];
  var retry=[107,108,134,185,218];
  var manual={94:1,108:1,134:1,185:1};
  var evidence={
    51:'evidence_external_051/b010_web_recheck.csv',81:'evidence_external_081/b017_real_web_recheck_20260630.csv',151:'evidence_external_151/b031_real_web_recheck_20260630.csv',166:'evidence_external_166/b034_real_web_recheck_20260630.csv',201:'evidence_external_201/b041_real_web_recheck_20260630.csv',216:'evidence_external_216/b044_web_recheck.csv',94:'problem_resolution/user_manual_confirmed',108:'problem_resolution/user_manual_confirmed',134:'problem_resolution/user_manual_confirmed',185:'problem_resolution/user_manual_confirmed'
  };
  function has(a,x){return a.indexOf(x)>=0}
  function pickEvidence(n){var starts=Object.keys(evidence).map(Number).sort(function(a,b){return b-a});for(var i=0;i<starts.length;i++){if(n>=starts[i]&&n<starts[i]+5)return evidence[starts[i]]}return ''}
  function ready(fn){if(document.readyState==='loading'){document.addEventListener('DOMContentLoaded',fn)}else{fn()}}
  ready(function(){
    var t=document.getElementById('reviewTable')||document.querySelector('table'); if(!t||!t.tBodies.length)return;
    var headers=[].map.call(t.querySelectorAll('thead th'),function(th){return th.textContent.trim().toLowerCase()});
    var si=headers.findIndex(function(x){return x.indexOf('source status')>=0});
    var ei=headers.findIndex(function(x){return x.indexOf('evidence')>=0});
    var di=headers.findIndex(function(x){return x.indexOf('do')>=0&&x.indexOf('ruluk')>=0});
    [].forEach.call(t.tBodies[0].rows,function(r,idx){
      var n=idx+1;
      var ok=has(sourceOk,n), re=has(retry,n), man=manual[n];
      if(si>=0&&r.cells[si]) r.cells[si].textContent = ok ? (man?'USER_CONFIRMED_SOURCE_OPEN':'SOURCE_URL_OPEN_VERIFIED') : (re?'SOURCE_RETRY_REQUIRED':'PENDING_SOURCE_REVIEW');
      if(ei>=0&&r.cells[ei]) r.cells[ei].textContent = pickEvidence(n);
      if(di>=0&&r.cells[di]) r.cells[di].textContent = ok ? '2/4 Source Evidence OK - boundary pending' : (re?'1/4 Source retry - boundary pending':'1/4 Pending source and boundary');
    });
  });
})();
</script>
'@
if ($html -notmatch 'apply_evidence_status_to_review_table') {
  $html = $html -replace '</body>', ($js + "`r`n<!-- apply_evidence_status_to_review_table -->`r`n</body>")
}
Set-Content -LiteralPath $page -Value $html -Encoding UTF8
Push-Location $repo
try { git add england_map_web/geometry_review_2of4_20260629.html; git commit -m 'Apply evidence status to review table'; git push origin main } finally { Pop-Location }
Write-Output 'EVIDENCE_STATUS_APPLIED_TO_REVIEW_TABLE'
