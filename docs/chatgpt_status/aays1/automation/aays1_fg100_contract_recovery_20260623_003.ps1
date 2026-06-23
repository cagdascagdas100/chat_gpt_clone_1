param([string]$StatusRepoRoot='', [string]$ProductRoot='')
$ErrorActionPreference='Continue'
$TaskId='aays1_fg100_contract_recovery_20260623_003'
$PageKey='aays1'
function Resolve-Root([string]$InputRoot){
  if($InputRoot -and (Test-Path $InputRoot)){ return (Resolve-Path $InputRoot).Path }
  try { return (git rev-parse --show-toplevel).Trim() } catch {}
  $p=$PSScriptRoot; for($i=0;$i -lt 4;$i++){ $p=Split-Path -Parent $p }; return $p
}
$StatusRepoRoot=Resolve-Root $StatusRepoRoot
$StatusDir=Join-Path $StatusRepoRoot 'docs/chatgpt_status/aays1/status'
$ReportDir=Join-Path $StatusRepoRoot 'docs/chatgpt_status/aays1/reports'
$HeartbeatDir=Join-Path $StatusRepoRoot 'docs/chatgpt_status/aays1/heartbeat'
$WorkRoot='F:\chatgpt\AAYS_WORK\aays1\fg100_003'
foreach($d in @($StatusDir,$ReportDir,$HeartbeatDir,$WorkRoot)){ New-Item -ItemType Directory -Force -Path $d | Out-Null }
$StatusPath=Join-Path $StatusDir ($TaskId + '_status.json')
$ReportPath=Join-Path $ReportDir ($TaskId + '_report.txt')
$BlockerPath=Join-Path $ReportDir ($TaskId + '_blocker.txt')
$PatchReportPath=Join-Path $ReportDir ($TaskId + '_patch_report.txt')
$SmokeReportPath=Join-Path $ReportDir ($TaskId + '_smoke_report.txt')
$HeartbeatPath=Join-Path $HeartbeatDir ($TaskId + '_heartbeat.txt')
function Write-Status([string]$State,[int]$Progress,[hashtable]$Extra){
  $body=@{task_id=$TaskId;page_key=$PageKey;status=$State;progress_percent=$Progress;status_repo_root=$StatusRepoRoot;product_root=$script:DetectedProductRoot;updated_at=(Get-Date).ToString('o');final_ready_confirmed=$false;production_complete=$false;internet_can_fill=$false}
  if($Extra){ foreach($k in $Extra.Keys){ $body[$k]=$Extra[$k] } }
  $body | ConvertTo-Json -Depth 8 | Set-Content -Encoding UTF8 $StatusPath
  "TASK_ID=$TaskId`nSTATUS=$State`nPROGRESS_PERCENT=$Progress`nUPDATED_AT=$((Get-Date).ToString('o'))" | Set-Content -Encoding UTF8 $HeartbeatPath
}
function Add-Report([string]$Line){ Add-Content -Encoding UTF8 -Path $ReportPath -Value $Line }
function Read-Utf8([string]$Path){ return [System.IO.File]::ReadAllText($Path,[System.Text.Encoding]::UTF8) }
function Write-Utf8([string]$Path,[string]$Text){ [System.IO.File]::WriteAllText($Path,$Text,[System.Text.Encoding]::UTF8) }
Set-Content -Encoding UTF8 -Path $ReportPath -Value "STATUS=STARTED`nTASK_ID=$TaskId`nPAGE_KEY=$PageKey`nNO_FAKE_COMPLETION=true`nUSE_SHARED_RUNNER_ONLY=true"
Write-Status 'STARTED_LOCAL_RUNNER_SCRIPT' 72 @{}
$required=@('england_map_web/app.js','terrayield_land_intelligence/app/schemas/future_growth.py','terrayield_land_intelligence/app/api/routes/future_growth.py','terrayield_land_intelligence/app/future_growth/evidence_service.py','terrayield_land_intelligence/app/future_growth/tile_service.py')
$candidates=@(); if($ProductRoot){$candidates+=$ProductRoot}; if($env:AAYS_PRODUCT_ROOT){$candidates+=$env:AAYS_PRODUCT_ROOT}; if($env:AAYS_WORKTREE){$candidates+=$env:AAYS_WORKTREE}
$candidates+=@($StatusRepoRoot,'C:\Users\cagda\Documents\GitHub\AAYS','C:\Users\cagda\Documents\GitHub\chat_gpt_clone_1','F:\chatgpt\AAYS','F:\chatgpt\AAYS_WORK\AAYS')
$DetectedProductRoot=$null
foreach($c in ($candidates | Select-Object -Unique)){
  if(-not $c -or -not(Test-Path $c)){ continue }
  $missing=@(); foreach($r in $required){ if(-not(Test-Path (Join-Path $c $r))){ $missing+=$r } }
  if($missing.Count -eq 0){ $DetectedProductRoot=(Resolve-Path $c).Path; break }
}
if(-not $DetectedProductRoot){
  "BLOCKER_STATUS=OPEN`nTASK_ID=$TaskId`nFAILED_STEP=product_root_detection`nCHECKED_ROOTS=$($candidates -join '; ')`nFINAL_READY_CONFIRMED=false`nPRODUCTION_COMPLETE=false" | Set-Content -Encoding UTF8 $BlockerPath
  Add-Report 'STATUS=BLOCKED_PRODUCT_ROOT_NOT_FOUND'; Add-Report 'PROGRESS_PERCENT=72'; Add-Report 'WHY_NOT_100=Local shared runner did not expose the AAYS product worktree.'
  Write-Status 'BLOCKED_PRODUCT_ROOT_NOT_FOUND' 72 @{blocker_path=$BlockerPath;checked_roots=$candidates}
  try { git -C $StatusRepoRoot add docs/chatgpt_status/aays1; git -C $StatusRepoRoot commit -m 'aays1 fg100 003 product-root blocker'; git -C $StatusRepoRoot push } catch {}
  exit 2
}
Add-Report "PRODUCT_ROOT=$DetectedProductRoot"
Write-Status 'PRODUCT_ROOT_DETECTED' 78 @{product_root=$DetectedProductRoot}
$schema=Join-Path $DetectedProductRoot 'terrayield_land_intelligence/app/schemas/future_growth.py'
$evidence=Join-Path $DetectedProductRoot 'terrayield_land_intelligence/app/future_growth/evidence_service.py'
$tile=Join-Path $DetectedProductRoot 'terrayield_land_intelligence/app/future_growth/tile_service.py'
$app=Join-Path $DetectedProductRoot 'england_map_web/app.js'
$changed=@()
try{
  $s=Read-Utf8 $schema
  if($s -notmatch 'probability_status:'){
    $s=$s.Replace('probability_not_calibrated: bool = True', "probability_not_calibrated: bool = True`n    probability_status: Literal[`"calibrated`", `"probability_not_calibrated`", `"no_data`"] = `"probability_not_calibrated`"")
  }
  if($s -notmatch 'layer_name: str = "Parcel Future Growth Potential"'){
    $s=$s.Replace("parcel_id: int`n    future_growth_percent:", "parcel_id: int`n    layer_name: str = `"Parcel Future Growth Potential`"`n    future_growth_percent:")
    $s=$s.Replace("parcel_id: int`n    local_authority_code:", "parcel_id: int`n    layer_name: str = `"Parcel Future Growth Potential`"`n    local_authority_code:")
  }
  if($s -notmatch 'calculation_explanation:'){
    $s=$s.Replace("evidence: list[FutureGrowthEvidenceItem] = Field(default_factory=list)`n    calculation_version:", "evidence: list[FutureGrowthEvidenceItem] = Field(default_factory=list)`n    calculation_explanation: str = `"Future Growth is an evidence-based development potential score, not a guaranteed price prediction or investment advice.`"`n    no_data_reason: str | None = None`n    source_summary: dict[str, Any] = Field(default_factory=dict)`n    calculation_version:")
  }
  Write-Utf8 $schema $s; $changed+='schema'
}catch{ Add-Report "PATCH_SCHEMA_ERROR=$($_.Exception.Message)" }
try{
  $e=Read-Utf8 $evidence
  if($e -notmatch 'probability_status'){
    $e=$e.Replace('"parcel_id": int(score["parcel_id"]),', "`"parcel_id`": int(score[`"parcel_id`"]),`n            `"layer_name`": `"Parcel Future Growth Potential`",")
    $e=$e.Replace('"probability_not_calibrated": True,', "`"probability_not_calibrated`": True,`n            `"probability_status`": `"probability_not_calibrated`",")
  }
  if($e -notmatch 'calculation_explanation'){
    $e=$e.Replace('"evidence": evidence_rows,', "`"evidence`": evidence_rows,`n            `"calculation_explanation`": `"Future Growth is an evidence-based development potential score, not a guaranteed price prediction or investment advice.`",`n            `"no_data_reason`": None if evidence_rows else `"no_parcel_specific_evidence`",`n            `"source_summary`": {`"evidence_count`": len(evidence_rows)},")
  }
  Write-Utf8 $evidence $e; $changed+='evidence_service'
}catch{ Add-Report "PATCH_EVIDENCE_ERROR=$($_.Exception.Message)" }
try{
  $t=Read-Utf8 $tile
  if($t -notmatch 'probability_status'){
    $t=$t.Replace('"parcel_id": row["parcel_id"],', "`"parcel_id`": row[`"parcel_id`"],`n                        `"layer_name`": `"Parcel Future Growth Potential`",")
    $t=$t.Replace('"probability_not_calibrated": True,', "`"probability_not_calibrated`": True,`n                        `"probability_status`": `"probability_not_calibrated`",")
  }
  Write-Utf8 $tile $t; $changed+='tile_service'
}catch{ Add-Report "PATCH_TILE_ERROR=$($_.Exception.Message)" }
try{
  $j=Read-Utf8 $app
  if($j -notmatch 'probability_status'){
    $j=$j.Replace('confidence_score: Number(feature.properties.confidence_score),', "growth_probability_percent: Number(feature.properties.growth_probability_percent),`n            probability_status: String(feature.properties.probability_status || `"probability_not_calibrated`"),`n            layer_name: String(feature.properties.layer_name || `"Parcel Future Growth Potential`"),`n            confidence_score: Number(feature.properties.confidence_score),")
    $j=$j.Replace('const confidence = Number(detail?.confidence_score ?? fallbackProps?.confidence_score);', "const probability = Number(detail?.growth_probability_percent ?? fallbackProps?.growth_probability_percent);`n    const probabilityStatus = String(detail?.probability_status || fallbackProps?.probability_status || `"probability_not_calibrated`");`n    const confidence = Number(detail?.confidence_score ?? fallbackProps?.confidence_score);")
    $j=$j.Replace('<strong>Confidence:</strong> ${Number.isFinite(confidence) ? `${formatNumber(confidence, 1)}%` : "-"}<br />', '<strong>Future Growth Probability:</strong> ${Number.isFinite(probability) ? `${formatNumber(probability, 1)}%` : escapeHtml(probabilityStatus)}<br />`n          <strong>Confidence:</strong> ${Number.isFinite(confidence) ? `${formatNumber(confidence, 1)}%` : "-"}<br />')
    $j=$j.Replace('<div class="future-growth-reasons">${topReasonsHtml}</div>', '<div class="future-growth-disclaimer">This is not a guaranteed price prediction or investment advice.</div>`n        <div class="future-growth-reasons">${topReasonsHtml}</div>`n        <div class="future-growth-calculation">${escapeHtml(detail?.calculation_explanation || "Evidence-based potential score; not a guaranteed price prediction.")}</div>')
  }
  Write-Utf8 $app $j; $changed+='app_js'
}catch{ Add-Report "PATCH_APP_ERROR=$($_.Exception.Message)" }
"PATCHED_COMPONENTS=$($changed -join ',')" | Set-Content -Encoding UTF8 $PatchReportPath
Write-Status 'PATCH_APPLIED_OR_CONFIRMED' 86 @{changed_components=$changed;patch_report=$PatchReportPath}
$jobs=@()
$jobs += Start-Job -Name 'python_compile' -ScriptBlock { param($root) $files=@('terrayield_land_intelligence/app/schemas/future_growth.py','terrayield_land_intelligence/app/api/routes/future_growth.py','terrayield_land_intelligence/app/future_growth/evidence_service.py','terrayield_land_intelligence/app/future_growth/tile_service.py'); $out=@(); foreach($f in $files){$p=Join-Path $root $f; if(Test-Path $p){ $r=& python -m py_compile $p 2>&1; $out += "PY_COMPILE $f EXIT=$LASTEXITCODE $r" } else { $out += "MISSING $f" }}; $out } -ArgumentList $DetectedProductRoot
$jobs += Start-Job -Name 'node_check' -ScriptBlock { param($root) $p=Join-Path $root 'england_map_web/app.js'; if(Test-Path $p){ $r=& node --check $p 2>&1; "NODE_CHECK EXIT=$LASTEXITCODE $r" } else { 'MISSING app.js' } } -ArgumentList $DetectedProductRoot
$jobs += Start-Job -Name 'marker_scan' -ScriptBlock { param($root) $files=@('england_map_web/app.js','terrayield_land_intelligence/app/schemas/future_growth.py','terrayield_land_intelligence/app/future_growth/evidence_service.py','terrayield_land_intelligence/app/future_growth/tile_service.py'); $markers=@('probability_status','layer_name','calculation_explanation','no_data_reason','not a guaranteed price prediction'); $res=@(); foreach($f in $files){$p=Join-Path $root $f; $txt= if(Test-Path $p){Get-Content -Raw $p}else{''}; foreach($m in $markers){$res += "$f :: $m :: $($txt.Contains($m))"}}; $res } -ArgumentList $DetectedProductRoot
$jobs += Start-Job -Name 'api_smoke' -ScriptBlock { $bases=@($env:AAYS_API_BASE,'http://127.0.0.1:8010','http://localhost:8010') | Where-Object { $_ }; $out=@(); foreach($b in $bases){ try { $u=$b.TrimEnd('/') + '/api/future-growth/layer?limit=1'; $r=Invoke-WebRequest -UseBasicParsing -TimeoutSec 20 -Uri $u; $out += "API_SMOKE $u STATUS=$($r.StatusCode) LEN=$($r.Content.Length)"; break } catch { $out += "API_SMOKE_FAIL $b $($_.Exception.Message)" } }; $out }
Wait-Job $jobs -Timeout 600 | Out-Null
$smoke=@(); foreach($j in $jobs){ $smoke += "--- JOB $($j.Name) STATE=$($j.State) ---"; $smoke += Receive-Job $j -Keep }
$smoke | Set-Content -Encoding UTF8 $SmokeReportPath
$markerText=Get-Content -Raw $SmokeReportPath
$allMarkers=($markerText -match 'probability_status :: True' -and $markerText -match 'layer_name :: True' -and $markerText -match 'calculation_explanation :: True' -and $markerText -match 'no_data_reason :: True')
$syntaxFail=($markerText -match 'EXIT=1|SyntaxError|Traceback')
$apiOk=($markerText -match 'API_SMOKE .* STATUS=200')
if($allMarkers -and -not $syntaxFail -and $apiOk){
  @{task_id=$TaskId;status='FINAL_READY_CONFIRMED';progress_percent=100;product_root=$DetectedProductRoot;FINAL_STATUS='FINAL_READY_CONFIRMED';PRODUCT_PROGRESS_ESTIMATE=100;PRODUCTION_COMPLETE=$true;final_ready_confirmed=$true;production_complete=$true;patch_report=$PatchReportPath;smoke_report=$SmokeReportPath;updated_at=(Get-Date).ToString('o')} | ConvertTo-Json -Depth 8 | Set-Content -Encoding UTF8 $StatusPath
  "STATUS=FINAL_READY_CONFIRMED`nPRODUCT_PROGRESS_ESTIMATE=100`nPRODUCTION_COMPLETE=true`nAPI_SMOKE=PASS`nSYNTAX=PASS`nMARKERS=PASS" | Set-Content -Encoding UTF8 $ReportPath
} else {
  $why=@(); if(-not $allMarkers){$why+='markers_missing'}; if($syntaxFail){$why+='syntax_failed'}; if(-not $apiOk){$why+='api_smoke_not_200'}
  "BLOCKER_STATUS=OPEN`nTASK_ID=$TaskId`nFAILED_STEP=$($why -join ',')`nPATCH_REPORT=$PatchReportPath`nSMOKE_REPORT=$SmokeReportPath`nFINAL_READY_CONFIRMED=false`nPRODUCTION_COMPLETE=false" | Set-Content -Encoding UTF8 $BlockerPath
  Add-Report 'STATUS=PATCHED_BUT_NOT_FINAL'; Add-Report 'PROGRESS_PERCENT=90'; Add-Report "WHY_NOT_100=$($why -join ',')"
  Write-Status 'PATCHED_BUT_NOT_FINAL' 90 @{why_not_100=$why;patch_report=$PatchReportPath;smoke_report=$SmokeReportPath;blocker_path=$BlockerPath}
}
try { git -C $DetectedProductRoot diff -- england_map_web/app.js terrayield_land_intelligence/app/schemas/future_growth.py terrayield_land_intelligence/app/future_growth/evidence_service.py terrayield_land_intelligence/app/future_growth/tile_service.py | Set-Content -Encoding UTF8 (Join-Path $ReportDir ($TaskId + '_product_diff.patch')) } catch {}
try { git -C $StatusRepoRoot add docs/chatgpt_status/aays1; git -C $StatusRepoRoot commit -m 'aays1 fg100 003 runner outputs'; git -C $StatusRepoRoot push } catch {}
exit 0
