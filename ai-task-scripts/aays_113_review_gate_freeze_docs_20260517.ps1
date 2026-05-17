$ErrorActionPreference='Continue'
$TaskId='aays-113-review-gate-freeze-docs-20260517-1915'
$BridgeRoot=Split-Path -Parent $PSScriptRoot
$ResultDir=Join-Path $BridgeRoot 'ai-results'
$HeartbeatDir=Join-Path $BridgeRoot 'ai-heartbeat'
New-Item -ItemType Directory -Force -Path $ResultDir,$HeartbeatDir | Out-Null
$HeartbeatPath=Join-Path $HeartbeatDir 'portable-runner.md'
$AaysRoot='C:\Users\cagda\Documents\GitHub\AAYS'
$Target=Join-Path $AaysRoot 'terrayield_land_intelligence'
$DocsDir=Join-Path $Target 'docs\review_gate_freeze_20260517'
$ReportPath=Join-Path $ResultDir ($TaskId+'.report.md')
$JsonPath=Join-Path $ResultDir ($TaskId+'.result.json')
function WriteNoBom($path,[string[]]$lines){
  $utf8NoBom = New-Object System.Text.UTF8Encoding($false)
  [System.IO.File]::WriteAllLines($path,$lines,$utf8NoBom)
}
function RunT($wd,$exe,$arg,$sec){
 try{
  $psi=New-Object System.Diagnostics.ProcessStartInfo
  $psi.FileName=$exe; $psi.Arguments=$arg; $psi.WorkingDirectory=$wd
  $psi.RedirectStandardOutput=$true; $psi.RedirectStandardError=$true; $psi.UseShellExecute=$false
  $p=[System.Diagnostics.Process]::Start($psi)
  if(-not $p.WaitForExit($sec*1000)){ try{$p.Kill()}catch{}; return [ordered]@{exit_code=124;timed_out=$true;output='TIMEOUT after '+$sec+' seconds'} }
  $o=$p.StandardOutput.ReadToEnd(); $e=$p.StandardError.ReadToEnd()
  return [ordered]@{exit_code=$p.ExitCode;timed_out=$false;output=(($o,$e)-join "`n").Trim()}
 }catch{return [ordered]@{exit_code=999;timed_out=$false;output=$_.Exception.Message}}
}
function GetUrl($url){
 try { return [ordered]@{ok=$true; text=((Invoke-RestMethod $url -TimeoutSec 8) | ConvertTo-Json -Depth 8)} }
 catch { return [ordered]@{ok=$false; text=$_.Exception.Message} }
}
@('# AAYS 113 Review Gate Freeze Docs','',"Time: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')",'Status: running',"TaskId: $TaskId",'Mode: read-only docs/smoke only','NoDbWrites: true','NoScoringPromotion: true','ProductionGate: NOT_READY_FOR_AUTO_ACCEPT') | Set-Content -Encoding UTF8 -Path $HeartbeatPath
$blockers=@(); $steps=@(); $docsWritten=$false; $compilePassed=$false; $pytestPassed=$false; $uiLive=$false; $backendLive=$false; $gateSafe=$false
if(!(Test-Path $Target)){ $blockers+='target terrayield_land_intelligence folder not found' }
else{
  New-Item -ItemType Directory -Force -Path $DocsDir | Out-Null
  WriteNoBom (Join-Path $DocsDir '00_REVIEW_GATE_FREEZE_README_TR.md') @(
'# TerraYield/AAYS Review-Gate Freeze Mode',
'',
'Bu klasor review-gate entegrasyonu icin freeze-mode dokumantasyon paketidir.',
'',
'Kapsam:',
'- Read-only guvenlik sertlestirmesi',
'- Endpoint contract dokumantasyonu',
'- Insan evidence review SOP/checklist',
'- GO/NO-GO tablosu',
'',
'Kesin yasaklar:',
'- production_acceptance_gate acilmayacak',
'- DB write/scoring promotion yapilmayacak',
'- evidence_checked=yes ve verified polygon/source olmadan accept/high-confidence onerilmeyecek',
'- review-gate disi feature konularina girilmeyecek',
'',
'Beklenen sistem durumu:',
'- production_acceptance_gate: NOT_READY_FOR_AUTO_ACCEPT',
'- can_production_auto_accept: false',
'- safe_output_gate: READY_FOR_HUMAN_EVIDENCE_REVIEW'
)
  WriteNoBom (Join-Path $DocsDir '01_ENDPOINT_CONTRACT_TR.md') @(
'# Review-Gate Endpoint Contract',
'',
'## GET /api/review/gates',
'- production_acceptance_gate daima NOT_READY_FOR_AUTO_ACCEPT kalir.',
'- can_production_auto_accept daima false kalir.',
'- evidence_checked_yes=0 ise production gate acilamaz.',
'- all_required_files_present sadece dosya varligini gosterir; kabul anlami tasimaz.',
'',
'## GET /api/review/status/by-listing/{listing_id}',
'- Listing ID uzerinden review, risk ve evidence durumunu dondurur.',
'- risk_label_v2 sadece inceleme onceligidir.',
'- acceptance_status_strict=manual_review ise UI kabul edilmis gibi gostermemelidir.',
'- has_source_url=true tek basina verified degildir.',
'- checked=no ise evidence verified degildir.',
'',
'## GET /api/review/status/{verification_id}',
'- Verification ID uzerinden fail-closed status bilgisi dondurur.',
'- Bilinmeyen kayitlarda production gate kapali kalir.',
'',
'## GET /api/review/risk-preview/{verification_id}',
'- Risk preview bilgisi verir; kabul karari vermez.',
'',
'## GET /api/review/tracking/{verification_id}',
'- Insan evidence review tracking durumunu verir.',
'- checked=yes sadece gercek insan kanit kontrolunden sonra verilebilir.'
)
  WriteNoBom (Join-Path $DocsDir '02_HUMAN_EVIDENCE_REVIEW_SOP_TR.md') @(
'# Human Evidence Review SOP',
'',
'1. Ilgili verification_id ve listing_id eslesmesini kontrol et.',
'2. /api/review/status/{verification_id} ve /api/review/status/by-listing/{listing_id} endpointlerini oku.',
'3. Source URL canonical ve erisilebilir mi kontrol et.',
'4. URL ayni listing/parsel kaydina mi ait kontrol et.',
'5. Postcode bilgisini kaynak, payload ve harita konumu ile karsilastir.',
'6. Local authority/council bilgisini karsilastir.',
'7. Polygon/boundary kaynaginin georeferenced ve kaynaktan dogrulanabilir oldugunu kontrol et.',
'8. Sadece gorsel tahmin polygon varsa verified sayma.',
'9. url_status, postcode_status, authority_status, polygon_status alanlarini gercek kanita gore doldur.',
'10. checked=yes sadece URL, postcode, authority ve polygon kaniti gercekten kontrol edildiyse ver.',
'',
'checked=yes icin minimum kosullar:',
'- url_status=checked',
'- postcode_status=checked',
'- authority_status=checked veya kanitla makul dogrulanmis',
'- polygon_status=checked',
'- evidence_notes denetlenebilir sekilde dolu',
'',
'Aksi durumda checked=no ve final_decision=needs_source veya ambiguous kalir.'
)
  WriteNoBom (Join-Path $DocsDir '03_GO_NOGO_TR.md') @(
'# Review-Gate GO / NO-GO',
'',
'| Alan | Karar | Not |',
'|---|---:|---|',
'| Backend live | GO | Smoke ile dogrulanir |',
'| UI live | GO | /england_map_web/ 200 olmali |',
'| Review endpointleri | GO | Read-only |',
'| Compile | GO | python -m compileall app -q |',
'| Pytest | GO | tests/test_review_status_api.py --basetemp |',
'| Read-only popup/status | GO | Kabul anlamina gelmez |',
'| Production auto-accept | NO-GO | Kesinlikle kapali |',
'| DB write | NO-GO | Freeze kapsam disi |',
'| Scoring promotion | NO-GO | Freeze kapsam disi |',
'| accept/high-confidence | NO-GO | evidence_checked=yes ve verified polygon/source yoksa yasak |',
'| threshold relax | NO-GO | DO_NOT_RELAX_THRESHOLDS |'
)
  WriteNoBom (Join-Path $DocsDir '04_POWERSHELL_VERIFY_FREEZE.ps1') @(
'cd C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence',
'Invoke-RestMethod "http://127.0.0.1:8010/api/review/gates" | ConvertTo-Json -Depth 8',
'Invoke-RestMethod "http://127.0.0.1:8010/api/review/status/by-listing/OTM-16748769" | ConvertTo-Json -Depth 8',
'Invoke-WebRequest "http://127.0.0.1:8010/england_map_web/" -UseBasicParsing | Select-Object StatusCode',
'python -m compileall app -q',
'$tmp = "$env:LOCALAPPDATA\Temp\aays_pytest"',
'New-Item -ItemType Directory -Force -Path $tmp | Out-Null',
'python -m pytest -q tests/test_review_status_api.py --basetemp "$tmp"'
)
  $docsWritten=$true
  $gates=GetUrl 'http://127.0.0.1:8010/api/review/gates'
  $status=GetUrl 'http://127.0.0.1:8010/api/review/status/by-listing/OTM-16748769'
  try { $uiResp=Invoke-WebRequest 'http://127.0.0.1:8010/england_map_web/' -UseBasicParsing -TimeoutSec 8; if($uiResp.StatusCode -eq 200){$uiLive=$true} } catch { $blockers+='ui smoke failed: '+$_.Exception.Message }
  if($gates.ok -and $status.ok){ $backendLive=$true } else { $blockers+='backend review endpoint smoke failed' }
  if($gates.text -match 'NOT_READY_FOR_AUTO_ACCEPT' -and $gates.text -match '"can_production_auto_accept"\s*:\s*false'){ $gateSafe=$true } else { $blockers+='gate safety response not confirmed' }
  $r=RunT $Target 'python' '-m compileall app -q' 180; $steps+=@([ordered]@{step='compile app';result=$r}); if($r.exit_code -eq 0){$compilePassed=$true}else{$blockers+='compileall failed'}
  $tmp=Join-Path $env:LOCALAPPDATA 'Temp\aays_pytest'
  New-Item -ItemType Directory -Force -Path $tmp | Out-Null
  $r=RunT $Target 'python' ('-m pytest -q tests/test_review_status_api.py --basetemp "'+$tmp+'"') 240; $steps+=@([ordered]@{step='pytest review status api with basetemp';result=$r}); if($r.exit_code -eq 0){$pytestPassed=$true}else{$blockers+='pytest review status api failed'}
  $localReport=Join-Path $DocsDir '05_FREEZE_MODE_STATUS_RESULT_TR.md'
  WriteNoBom $localReport @(
'# Review-Gate Freeze Mode Status Result',
'',
"Generated: $(Get-Date -Format s)",
"docs_written: $docsWritten",
"backend_live: $backendLive",
"ui_live: $uiLive",
"gate_safe_not_ready_for_auto_accept: $gateSafe",
"compile_passed: $compilePassed",
"pytest_passed: $pytestPassed",
'production_auto_accept: NO-GO',
'verified_promotion: NO-GO without evidence_checked=yes and verified polygon/source',
'',
'## Endpoint gates snapshot',
'```json',
$gates.text,
'```',
'',
'## Listing snapshot',
'```json',
$status.text,
'```'
  )
  $r=RunT $AaysRoot 'git' 'add terrayield_land_intelligence/docs/review_gate_freeze_20260517' 60; $steps+=@([ordered]@{step='git add freeze docs';result=$r})
  $r=RunT $AaysRoot 'git' 'commit -m "Add review gate freeze documentation and smoke status"' 60; $steps+=@([ordered]@{step='git commit freeze docs';result=$r})
}
$ready=($docsWritten -and $backendLive -and $uiLive -and $gateSafe -and $compilePassed -and $pytestPassed)
$statusText=if($ready){'completed'}elseif($blockers.Count -gt 0){'completed_with_blockers'}else{'completed_unknown'}
$report=@('# AAYS 113 Review Gate Freeze Docs Result','',"Generated: $(Get-Date -Format s)","STATUS=$statusText","DOCS_WRITTEN=$docsWritten","BACKEND_LIVE=$backendLive","UI_LIVE=$uiLive","GATE_SAFE_NOT_READY_FOR_AUTO_ACCEPT=$gateSafe","COMPILE_PASSED=$compilePassed","PYTEST_PASSED=$pytestPassed","READY=$ready",'','## Blockers')
if($blockers.Count -eq 0){$report+='- none'}else{foreach($b in $blockers){$report+='- '+$b}}
$report+=''; $report+='## Output docs'; $report+=('DOCS_DIR='+$DocsDir)
$report+=''; $report+='## Steps'
foreach($s in $steps){$report+='### '+$s.step;$report+='exit_code='+$s.result.exit_code+' timed_out='+$s.result.timed_out;$out=[string]$s.result.output;if($out.Length -gt 3000){$out=$out.Substring(0,3000)+'...TRUNCATED'};$report+='```text';$report+=$out;$report+='```'}
$report+='';$report+='PRODUCTION_AUTO_ACCEPT=NO-GO';$report+='DB_WRITE=NO-GO';$report+='SCORING_PROMOTION=NO-GO';$report+='AAYS_113_REVIEW_GATE_FREEZE_DOCS_DONE=true'
$report | Set-Content -Encoding UTF8 -Path $ReportPath
([ordered]@{task_id=$TaskId;status=$statusText;ready=$ready;docs_written=$docsWritten;backend_live=$backendLive;ui_live=$uiLive;gate_safe=$gateSafe;compile_passed=$compilePassed;pytest_passed=$pytestPassed;blockers=$blockers;docs_dir=$DocsDir;report_path=$ReportPath;generated_at=(Get-Date -Format s)} | ConvertTo-Json -Depth 8) | Set-Content -Encoding UTF8 -Path $JsonPath
@('# AAYS 113 Review Gate Freeze Docs','',"Time: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')",'Status: finished',"TaskId: $TaskId","Message: exit=0 status=$statusText ready=$ready",'Mode: read-only docs/smoke only','NoDbWrites: true','NoScoringPromotion: true','ProductionGate: NOT_READY_FOR_AUTO_ACCEPT') | Set-Content -Encoding UTF8 -Path $HeartbeatPath
Write-Output "AAYS_113_REVIEW_GATE_FREEZE_DOCS_DONE=true"
Write-Output "READY=$ready"
Write-Output "REPORT=$ReportPath"
Write-Output "DOCS_DIR=$DocsDir"
exit 0
