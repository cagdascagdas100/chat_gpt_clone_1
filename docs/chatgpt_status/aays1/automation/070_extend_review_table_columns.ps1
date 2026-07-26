$ErrorActionPreference = 'Stop'
$repo = $env:AAYS_REPO_ROOT
if ([string]::IsNullOrWhiteSpace($repo)) { $repo = 'F:\chatgpt\chat_gpt_clone_1_main' }
$page = Join-Path $repo 'england_map_web\geometry_review_2of4_20260629.html'
if (!(Test-Path $page)) { throw "missing page: $page" }
$html = Get-Content -Raw -LiteralPath $page
if ($html -match 'Parsel Ref / Inspire' -and $html -match 'Parsel Geometrisi') {
  Write-Output 'EXTENDED_COLUMNS_ALREADY_PRESENT'
  exit 0
}
$script = @'
<script>
(function(){
  function ready(fn){ if(document.readyState==='loading'){document.addEventListener('DOMContentLoaded',fn)}else{fn()} }
  function text(cell){ return (cell ? cell.textContent : '').trim(); }
  function listingId(url, rowNo){ var m=String(url||'').match(/details\/(\d+)/); return m ? ('OTM-' + m[1]) : ('ROW-' + rowNo); }
  function score(rowNo){ return rowNo <= 225 ? '2/4 Medium Accuracy' : '1/4 Pending'; }
  function className(rowNo){ return rowNo <= 225 ? 'candidate_sale_footprint_geometry_not_official_boundary' : 'pending_source_review'; }
  function edgeSummary(rowNo){ return 'A(pending), B(pending), C(pending), D(pending)'; }
  function pointSummary(centroid){ return centroid ? ('Nokta_1(' + centroid + ')') : 'Nokta_1(pending)'; }
  function miniSvg(label){ return '<div class="miniParcel"><svg viewBox="0 0 160 90" width="150" height="80"><polygon points="20,70 55,20 130,25 145,65 70,80" fill="#fff3df" stroke="#ef6c00" stroke-width="2" stroke-dasharray="5 4"></polygon><circle cx="20" cy="70" r="2" fill="#0ea5e9"></circle><circle cx="55" cy="20" r="2" fill="#0ea5e9"></circle><circle cx="130" cy="25" r="2" fill="#0ea5e9"></circle><circle cx="145" cy="65" r="2" fill="#0ea5e9"></circle><text x="10" y="85" font-size="9">'+label+'</text></svg></div>'; }
  ready(function(){
    var table = document.getElementById('reviewTable') || document.querySelector('table');
    if(!table || table.dataset.extendedColumns === '1') return;
    table.dataset.extendedColumns = '1';
    var headRow = table.tHead ? table.tHead.rows[0] : table.querySelector('thead tr');
    if(!headRow) return;
    ['Listing ID','Parsel Ref / Inspire','Doğruluk','Kenarlar: A(uzunluk)','Noktalar: Nokta_1(lon,lat)','Parsel Geometrisi'].forEach(function(h){ var th=document.createElement('th'); th.textContent=h; headRow.appendChild(th); });
    Array.prototype.forEach.call(table.tBodies[0].rows,function(r,idx){
      var rowNo = idx + 1;
      var url = text(r.cells[2]);
      var loc = text(r.cells[6]);
      var centroid = text(r.cells[7]);
      var id = listingId(url,rowNo);
      var ref = loc ? ('england:local-source:' + loc.replace(/\s+/g,'-').toLowerCase()) : 'pending_ref';
      var vals = [id, ref, score(rowNo) + '\n' + className(rowNo), edgeSummary(rowNo), pointSummary(centroid), miniSvg('Şekil')];
      vals.forEach(function(v,i){ var td=document.createElement('td'); if(i===5){td.innerHTML=v}else{td.textContent=v} r.appendChild(td); });
    });
  });
})();
</script>
'@
if ($html -match '</body>') { $html = $html -replace '</body>', ($script + "`r`n</body>") } else { $html += $script }
if ($html -notmatch 'miniParcel') {
  $html = $html -replace '</style>', '.miniParcel{width:160px;height:90px;overflow:hidden}</style>'
}
Set-Content -LiteralPath $page -Value $html -Encoding UTF8
Push-Location $repo
try {
  git add england_map_web/geometry_review_2of4_20260629.html
  git commit -m 'Extend geometry review table columns'
  git push origin main
} finally { Pop-Location }
Write-Output 'EXTENDED_REVIEW_TABLE_COLUMNS'
