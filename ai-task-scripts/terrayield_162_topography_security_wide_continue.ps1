$ErrorActionPreference='Continue'
$TaskId='terrayield-162-topography-security-wide-continue'
$ProjectRoot='C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence'
$TopoRoot=Join-Path $ProjectRoot 'topography_accuracy_upgrade_plan'
$Out=Join-Path $TopoRoot 'phase_04_security_topography_wide_continue'
$Report=Join-Path $Out 'TERRAYIELD_162_WIDE_CONTINUE_REPORT.md'
function W($p,$c){$d=Split-Path -Parent $p;if($d -and !(Test-Path $d)){New-Item -ItemType Directory -Force -Path $d|Out-Null};$e=New-Object Text.UTF8Encoding($false);[IO.File]::WriteAllText($p,$c,$e)}
function Port($x){try{$c=New-Object Net.Sockets.TcpClient;$a=$c.BeginConnect('127.0.0.1',$x,$null,$null);$ok=$a.AsyncWaitHandle.WaitOne(750,$false);if($ok -and $c.Connected){$c.EndConnect($a);$c.Close();'OPEN'}else{$c.Close();'CLOSED'}}catch{'ERROR'}}
Write-Output "TASK_ID=$TaskId"
Write-Output 'MODE=WIDE_CONTINUE_SCOPE_ONLY_SINGLE_RUNNER'
Write-Output 'GUARDS=NO_DB NO_DOCKER NO_DOWNLOAD NO_RESTART NO_UI_EDIT NO_ACTIVE_SCORE_CHANGE NO_CRITICAL_JS_EDIT'
if(!(Test-Path $ProjectRoot)){Write-Output "PROJECT_ROOT_MISSING=$ProjectRoot";exit 2}
New-Item -ItemType Directory -Force -Path $Out|Out-Null
$packs=@(
  @{name='01_COMBINED_SCOPE_LEDGER.md';body='# Combined Scope Ledger

This continuation only writes governance/audit artifacts under topography_accuracy_upgrade_plan. It does not write active UI, active score production, england_map_web, DB, Docker, or download jobs.

Lanes: datum, source evidence, confidence, runtime guards, security expansion cross-check, future implementation backlog.'},
  @{name='02_SECURITY_TOPOGRAPHY_CROSS_GUARDS.csv';body='guard_id,domain,assertion,expected
CG001,topography,canonical datum remains mAOD,true
CG002,topography,ODN alias accepted,true
CG003,topography,Ordnance Datum Newlyn alias accepted,true
CG004,security,no active score write,true
CG005,security,no england_map_web diff,true
CG006,runtime,no restart,true
CG007,runtime,no Docker,true
CG008,data,no England-wide download,true
CG009,db,no SQL execution,true
CG010,ui,no critical JS edit,true'},
  @{name='03_LONG_RUNNING_TASK_PROTOCOL.md';body='# Long Running Task Protocol

Use one runner process. Prefer one large script over multiple simultaneous bridge writers. If a task is running, do not overwrite current-task. If heartbeat is polling and current task is complete, queue next task with a new monotonically increasing ID.

Expected wait windows: small verifier 3-5 minutes; wide verifier 10-20 minutes; hyper/long-wide batch 20-45 minutes.'},
  @{name='04_TOPOGRAPHY_EVIDENCE_COMPLETION_SCORECARD.json';body=(@{scorecard=@(@{source='HMLR/NPS';geometry=0;licence=0;limitations=0;status='stub'},@{source='EA LIDAR Composite DTM';datum=0;coverage=0;resolution=0;status='stub'},@{source='OS Terrain 5';fallback=0;licence=0;status='stub'},@{source='OS Terrain 50';fallback=0;licence=0;status='stub'},@{source='Local Terrarium 8099';runtime_label=1;authoritative=0;status='current_system_only'},@{source='Local lookup 8765';runtime_label=1;authoritative=0;status='current_system_only'})}|ConvertTo-Json -Depth 8)},
  @{name='05_IMPLEMENTATION_GATE_DECISIONS.md';body='# Implementation Gate Decisions

Gate A: Governance files parse. Gate B: Evidence populated. Gate C: AOI whitelist approved. Gate D: SQL migration reviewed but not executed. Gate E: staging extractor runs on AOI only. Gate F: read-only report endpoint reviewed. Gate G: UI integration only after separate approval.

Current phase: Gate A expansion only.'},
  @{name='06_RUNTIME_OBSERVABILITY_NOTES.md';body='# Runtime Observability Notes

Observe ports only: 8010 UI, 8099 DEM, 8765 lookup. Do not restart services. Do not rebuild Docker. Do not mutate DB. Do not infer authoritative accuracy from local Terrarium alone.'},
  @{name='07_100_GUARD_PLACEHOLDERS.csv';body=((1..100|ForEach-Object { 'TG{0:D3},scope_only_guard,pass_required' -f $_ }) -join "`n")},
  @{name='08_NEXT_10_CONTINUE_COMMANDS.md';body='# Next Continue Commands

1. Evidence source stubs to populated records.
2. Datum proof links audit.
3. Geometry limitation audit.
4. AOI whitelist draft.
5. Static parser tests.
6. Confidence vector tests.
7. SQL migration review notes.
8. Runtime health report.
9. Rollback rehearsal notes.
10. Final governance acceptance summary.'}
)
foreach($p in $packs){W (Join-Path $Out $p.name) $p.body}
$ok=$true
$r="# TerraYield 162 Wide Continue Report`n`nGenerated: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')`nTask: $TaskId`n`n## Output files`n"
foreach($p in $packs){if(Test-Path (Join-Path $Out $p.name)){$r+="- PASS $($p.name)`n"}else{$ok=$false;$r+="- FAIL $($p.name)`n"}}
$r+="`n## Observe-only ports`n- 8010: $(Port 8010)`n- 8099: $(Port 8099)`n- 8765: $(Port 8765)`n"
Set-Location $ProjectRoot
$st=git status --short 2>&1|Out-String
$r+="`n## Git status before guarded commit`n```text`n$st`n``` `n"
if($st -match 'england_map_web|aays_topography_mode_v1.js|aays_topography_bulk_visible_parcels_v1.js'){$ok=$false;$r+="- FAIL active/critical diff detected`n"}else{$r+="- PASS no active/critical diff detected by status scan`n"}
$r+="`nVALIDATION_OK=$ok`n"
W $Report $r
Write-Output 'WIDE_CONTINUE_FILES_BEGIN'
Get-ChildItem $Out|Select Name,Length,LastWriteTime|Format-Table|Out-String|Write-Output
Write-Output 'WIDE_CONTINUE_FILES_END'
try{Set-Location $ProjectRoot;git add topography_accuracy_upgrade_plan 2>&1|Out-String|Write-Output;$cached=git diff --cached --name-only 2>&1|Out-String;Write-Output 'CACHED_DIFF_BEGIN';Write-Output $cached;Write-Output 'CACHED_DIFF_END';$unsafe=$false;foreach($line in ($cached -split "`n")){$t=$line.Trim();if($t -and !$t.StartsWith('topography_accuracy_upgrade_plan/')){$unsafe=$true}};if($unsafe){git reset 2>&1|Out-String|Write-Output;Write-Output 'PROJECT_COMMIT_SKIPPED_UNSAFE_CACHED_PATH'}elseif([string]::IsNullOrWhiteSpace($cached)){Write-Output 'PROJECT_COMMIT_SKIPPED_NO_CHANGES'}else{git commit -m 'Add TerraYield 162 topography security wide continuation' 2>&1|Out-String|Write-Output;git push 2>&1|Out-String|Write-Output;Write-Output 'PROJECT_COMMIT_PUSH_ATTEMPTED=TRUE'}}catch{Write-Output "PROJECT_COMMIT_ERROR=$($_.Exception.Message)"}
Write-Output "VALIDATION_OK=$ok"
Write-Output 'TERRAYIELD_TASK_DONE'
if($ok){exit 0}else{exit 1}
