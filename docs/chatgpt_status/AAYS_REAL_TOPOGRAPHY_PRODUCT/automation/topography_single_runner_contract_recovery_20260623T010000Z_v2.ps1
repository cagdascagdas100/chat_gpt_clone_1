param(
  [string]$PageKey = 'AAYS_REAL_TOPOGRAPHY_PRODUCT',
  [string]$TaskId = 'topography_single_runner_contract_recovery_20260623T010000Z'
)
$ErrorActionPreference = 'Continue'
$ScriptPath = $MyInvocation.MyCommand.Path
$AutomationRoot = Split-Path -Parent $ScriptPath
$PageRoot = Split-Path -Parent $AutomationRoot
$RepoRoot = (Resolve-Path (Join-Path $PageRoot '..\..\..')).Path
$Reports = Join-Path $PageRoot 'reports'
$Status = Join-Path $PageRoot 'status'
$Heartbeat = Join-Path $PageRoot 'heartbeat'
$RunnerOutput = Join-Path $PageRoot 'runner_output'
New-Item -ItemType Directory -Force -Path $Reports,$Status,$Heartbeat,$RunnerOutput | Out-Null
function W([string]$p,[string[]]$x){ Set-Content -Path $p -Encoding UTF8 -Value $x }
function Has([string]$p,[string]$n){ if(Test-Path $p){ return ((Get-Content $p -Raw -ErrorAction SilentlyContinue) -like "*$n*") } return $false }

$contract = Join-Path $Reports ($TaskId + '_runner_contract_detect.txt')
$tokens = Join-Path $Reports ($TaskId + '_final_token_verify.txt')
$remote = Join-Path $Reports ($TaskId + '_remote_sync_diagnostic.txt')
$data = Join-Path $Reports ($TaskId + '_data_coverage_audit.txt')
$lookup = Join-Path $Reports ($TaskId + '_lookup_coverage_audit.txt')
$ui = Join-Path $Reports ($TaskId + '_ui_static_contract_audit.txt')
$naming = Join-Path $Reports ($TaskId + '_naming_debt_audit.txt')
$finalReport = Join-Path $Reports ($TaskId + '_final_report.txt')
$finalStatus = Join-Path $Status ($TaskId + '_final.status.txt')
$hb = Join-Path $Heartbeat ($TaskId + '.heartbeat.txt')
W $hb @("TASK_ID=$TaskId","PAGE_KEY=$PageKey","STATUS=RUNNING_COMPACT_V2","SCRIPT_PATH=$ScriptPath","PAGE_ROOT=$PageRoot","REPO_ROOT=$RepoRoot")

# runner contract and git shape
$c = @("TASK_ID=$TaskId","PAGE_KEY=$PageKey","REPORT_KIND=runner_contract_detect","REPO_ROOT=$RepoRoot")
@('control','queue','runner_tasks','current-task','automation','reports','status','heartbeat','runner_output') | ForEach-Object { $c += "PAGE_PATH_EXISTS[$_]=" + (Test-Path (Join-Path $PageRoot $_)) }
$c += 'SHARED_RUNNER_SCRIPT_EXISTS=' + (Test-Path (Join-Path $RepoRoot 'docs\chatgpt_status\_shared\automation\RUN_SINGLE_AAYS_MULTI_PAGE_QUEUE_RUNNER.ps1'))
try{ Push-Location $RepoRoot; $c += 'GIT_BRANCH=' + ((git rev-parse --abbrev-ref HEAD 2>&1 | Out-String).Trim()); $c += 'GIT_HEAD=' + ((git rev-parse HEAD 2>&1 | Out-String).Trim()); Pop-Location } catch { $c += 'GIT_ERROR=' + $_.Exception.Message; try{Pop-Location}catch{} }
W $contract $c

# final token verification in existing page reports and status
$toks = @('FINAL_STATUS=FINAL_READY_CONFIRMED','PRODUCT_PROGRESS_ESTIMATE=100','PRODUCTION_COMPLETE=true')
$tl = @('REPORT_KIND=final_token_verify')
$all = $true
$files = Get-ChildItem $PageRoot -Recurse -File -ErrorAction SilentlyContinue | Where-Object { $_.FullName -match '\\(reports|status)\\' }
foreach($tok in $toks){ $hit = $false; foreach($f in $files){ try{ if((Get-Content $f.FullName -Raw) -like "*$tok*"){ $hit=$true; $tl += "TOKEN_FILE[$tok]=$($f.FullName)" } } catch{} }; $tl += "TOKEN_FOUND[$tok]=$hit"; if(-not $hit){ $all=$false } }
$tl += "FINAL_TOKEN_SET_PRESENT=$all"
W $tokens $tl

# remote diagnostic, read only
$rl = @('REPORT_KIND=remote_sync_diagnostic')
try{ Push-Location $RepoRoot; $branch=((git rev-parse --abbrev-ref HEAD 2>&1|Out-String).Trim()); $head=((git rev-parse HEAD 2>&1|Out-String).Trim()); $remoteRef='origin/'+$branch; $fetch=((git fetch --prune origin 2>&1|Out-String).Trim()); $remoteHead=((git rev-parse $remoteRef 2>&1|Out-String).Trim()); $rl += "LOCAL_BRANCH=$branch"; $rl += "LOCAL_HEAD=$head"; $rl += "REMOTE_HEAD_FOR_LOCAL_BRANCH=$remoteHead"; if($remoteHead -and $remoteHead -notmatch 'fatal'){ $base=((git merge-base $branch $remoteRef 2>&1|Out-String).Trim()); $range=$branch+'...'+$remoteRef; $ab=((git rev-list --left-right --count $range 2>&1|Out-String).Trim()); $rl += "MERGE_BASE=$base"; $rl += "AHEAD_BEHIND_LOCAL_REMOTE=$ab"; if($head -eq $remoteHead){$rl+='REMOTE_SYNC_STATUS=IN_SYNC'} elseif($base -eq $remoteHead){$rl+='REMOTE_SYNC_STATUS=LOCAL_AHEAD_FAST_FORWARD_PUSH_POSSIBLE'} elseif($base -eq $head){$rl+='REMOTE_SYNC_STATUS=LOCAL_BEHIND_PULL_REQUIRED'} else {$rl+='REMOTE_SYNC_STATUS=DIVERGED_NON_FAST_FORWARD_RISK'} } else { $rl += 'REMOTE_SYNC_STATUS=REMOTE_BRANCH_NOT_FOUND_OR_UNREADABLE' }; Pop-Location } catch { $rl += 'REMOTE_SYNC_ERROR=' + $_.Exception.Message; try{Pop-Location}catch{} }
W $remote $rl

# data coverage
$roots=@('D:\AAYS_DATA\topography\england\raw','D:\AAYS_DATA\topography\england\tiles','D:\AAYS_DATA\topography\england\processed','D:\topografik_map\london\terrarium_tiles','F:\AAYS\london_parcel_sources\topography_reports\LONDON_ALL_PARCELS_TOPOGRAPHY_4LEVEL_20260501_001116.csv.gz')
$dl=@('REPORT_KIND=data_coverage_audit')
foreach($r in $roots){ $dl += "PATH_EXISTS[$r]=" + (Test-Path $r) }
$england=@($roots[0..2] | Where-Object { Test-Path $_ }).Count
$london=((Test-Path $roots[3]) -and (Test-Path $roots[4]))
$dl += "ENGLAND_WIDE_ROOTS_PRESENT_COUNT=$england"
$dl += "LONDON_ONLY_PROOF_PRESENT=$london"
if($england -ge 2){$dl+='DATA_COVERAGE_STATUS=ENGLAND_WIDE_EVIDENCE_PRESENT'} elseif($london){$dl+='DATA_COVERAGE_STATUS=LONDON_ONLY_EVIDENCE_PRESENT_PRODUCT_WIDE_BLOCKED'} else {$dl+='DATA_COVERAGE_STATUS=INSUFFICIENT_DATA_EVIDENCE'}
W $data $dl

# lookup route sample
$ll=@('REPORT_KIND=lookup_coverage_audit')
try{ $resp=Invoke-WebRequest -Uri 'http://127.0.0.1:8010/topography/lookup?parcel_id=29759443' -UseBasicParsing -TimeoutSec 5; $sv='unknown'; try{$json=$resp.Content|ConvertFrom-Json; $sv=[string]$json.status}catch{}; $ll += "LOOKUP[29759443]=http_$($resp.StatusCode);status_$sv"; if($resp.StatusCode -eq 200 -and $sv -ne 'no_data'){$ll+='LOOKUP_COVERAGE_STATUS=PARTIAL_OR_GOOD_DATA_PRESENT'} else {$ll+='LOOKUP_COVERAGE_STATUS=BLOCKED_NO_CONFIRMED_DATA_ROWS'} } catch { $ll += 'LOOKUP[29759443]=ERROR;' + $_.Exception.Message; $ll += 'LOOKUP_COVERAGE_STATUS=BLOCKED_NO_CONFIRMED_DATA_ROWS' }
W $lookup $ll

# UI static contract
$ul=@('REPORT_KIND=ui_static_contract_audit')
$app=Join-Path $RepoRoot 'england_map_web\static\js\app.js'
$ul += 'APP_JS_EXISTS=' + (Test-Path $app)
if(Test-Path $app){ $txt=Get-Content $app -Raw; @('normalizeTopographyLookupForPopup','buildTopographyPopupRowsHtml','hight_differance.png','topography') | ForEach-Object { $ul += "UI_TOKEN_FOUND[$_]=" + ($txt -like "*$_*") }; $ul += 'UI_STATIC_CONTRACT_STATUS=CHECKED' } else { $ul += 'UI_STATIC_CONTRACT_STATUS=BLOCKED_APP_JS_NOT_FOUND' }
W $ui $ul

# naming debt
$pb=Get-ChildItem $PageRoot -Recurse -File -ErrorAction SilentlyContinue | Where-Object { $_.Name -like 'pb_*' }
$nl=@('REPORT_KIND=naming_debt_audit','PB_NAMED_FILE_COUNT=' + $pb.Count)
foreach($f in $pb){ $nl += 'PB_FILE=' + $f.FullName }
if($pb.Count -eq 0){$nl+='NAMING_DEBT_STATUS=CLEAN'} else {$nl+='NAMING_DEBT_STATUS=DEBT_PRESENT_COMPATIBILITY_RENAME_PLAN_REQUIRED'}
W $naming $nl

$blockers=@()
if(-not (Has $tokens 'FINAL_TOKEN_SET_PRESENT=True')){$blockers+='final_tokens_not_all_verified'}
if(Has $remote 'REMOTE_SYNC_STATUS=DIVERGED_NON_FAST_FORWARD_RISK'){$blockers+='remote_branch_diverged_non_fast_forward'}
if(Has $remote 'REMOTE_SYNC_STATUS=REMOTE_BRANCH_NOT_FOUND_OR_UNREADABLE'){$blockers+='remote_branch_not_found_or_unreadable'}
if(-not (Has $data 'DATA_COVERAGE_STATUS=ENGLAND_WIDE_EVIDENCE_PRESENT')){$blockers+='england_wide_coverage_not_proven'}
if(-not (Has $lookup 'LOOKUP_COVERAGE_STATUS=PARTIAL_OR_GOOD_DATA_PRESENT')){$blockers+='lookup_data_presence_not_proven'}
if(-not (Has $ui 'UI_STATIC_CONTRACT_STATUS=CHECKED')){$blockers+='ui_static_contract_not_verified'}
if(Has $naming 'DEBT_PRESENT'){$blockers+='pb_naming_debt_present'}
$manual = Get-ChildItem $Reports -File -ErrorAction SilentlyContinue | Where-Object { $_.Name -match 'manual.*ui.*smoke|ui.*smoke.*manual' }
if($manual.Count -eq 0){$blockers+='manual_ui_parcel_click_smoke_not_git_visible'}
$progress=88; if($blockers.Count -le 5){$progress=92}; if($blockers.Count -le 3){$progress=96}; if($blockers.Count -eq 0){$progress=100}
$fr=@("TASK_ID=$TaskId","PAGE_KEY=$PageKey",'LOCAL_TECHNICAL_COMPLETION_FROM_HANDOFF=100',"PRODUCT_PROGRESS_ESTIMATE=$progress",'BLOCKER_COUNT=' + $blockers.Count)
foreach($b in $blockers){$fr+='BLOCKER=' + $b}
W $finalReport $fr
$st=@("TASK_ID=$TaskId","PAGE_KEY=$PageKey","PRODUCT_PROGRESS_ESTIMATE=$progress",'BLOCKER_COUNT=' + $blockers.Count)
if($blockers.Count -eq 0){$st+='FINAL_STATUS=FINAL_READY_CONFIRMED';$st+='PRODUCTION_COMPLETE=true';$st+='PRODUCT_100_READY=true'} else {$st+='FINAL_STATUS=BLOCKED_NEEDS_EVIDENCE';$st+='PRODUCTION_COMPLETE=false';$st+='PRODUCT_100_READY=false';foreach($b in $blockers){$st+='BLOCKER=' + $b}}
W $finalStatus $st
Add-Content -Path $hb -Encoding UTF8 -Value @('STATUS=FINISHED','FINAL_REPORT_FILE=' + $finalReport,'FINAL_STATUS_FILE=' + $finalStatus)
exit 0
