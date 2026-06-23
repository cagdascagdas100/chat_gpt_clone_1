# AAYS_REAL_TOPOGRAPHY_PRODUCT
# TASK_ID=topography_single_runner_contract_recovery_20260623T010000Z
# MODE=existing single shared runner only
# PURPOSE=contract probe + long read-only Topography audit + GitHub-reportable final evidence
# SAFETY=no db write, no migration, no deploy, no force push, no extra runner process

$ErrorActionPreference = 'Continue'
$TaskId = 'topography_single_runner_contract_recovery_20260623T010000Z'
$PageKey = 'AAYS_REAL_TOPOGRAPHY_PRODUCT'
$StartedUtc = (Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssZ')

$AutomationDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$PageRoot = Split-Path -Parent $AutomationDir
$StatusRoot = Split-Path -Parent $PageRoot
$DocsRoot = Split-Path -Parent $StatusRoot
$RepoRoot = Split-Path -Parent $DocsRoot

$ReportsDir = Join-Path $PageRoot 'reports'
$StatusDir = Join-Path $PageRoot 'status'
$HeartbeatDir = Join-Path $PageRoot 'heartbeat'
$RunnerOutputDir = Join-Path $PageRoot 'runner_output'
$WorkDir = Join-Path $PageRoot 'work'
$AuditDir = Join-Path $WorkDir 'topography_v4_audit'

foreach ($Dir in @($ReportsDir,$StatusDir,$HeartbeatDir,$RunnerOutputDir,$WorkDir,$AuditDir)) {
  if (-not (Test-Path -LiteralPath $Dir)) { New-Item -ItemType Directory -Force -Path $Dir | Out-Null }
}

function Write-TextFile {
  param([string]$Path,[string]$Text)
  $Parent = Split-Path -Parent $Path
  if ($Parent -and -not (Test-Path -LiteralPath $Parent)) { New-Item -ItemType Directory -Force -Path $Parent | Out-Null }
  Set-Content -LiteralPath $Path -Value $Text -Encoding UTF8
}

function Add-ReportLine {
  param([string]$Path,[string]$Line)
  Add-Content -LiteralPath $Path -Value $Line -Encoding UTF8
}

$RunnerOutput = Join-Path $RunnerOutputDir "$TaskId`_v4_output.txt"
$Heartbeat = Join-Path $HeartbeatDir "$TaskId`_v4.heartbeat.txt"
$FinalReport = Join-Path $ReportsDir "$TaskId`_final_report.txt"
$FinalStatus = Join-Path $StatusDir "$TaskId`_final.status.txt"
$BlockerReport = Join-Path $ReportsDir "$TaskId`_v4_blockers.txt"

Write-TextFile $Heartbeat @"
TASK_ID=$TaskId
PAGE_KEY=$PageKey
STATUS=V4_STARTED
STARTED_UTC=$StartedUtc
RUNNER_MODE=existing_single_shared_runner
SCRIPT=$($MyInvocation.MyCommand.Path)
"@

Write-TextFile $RunnerOutput @"
TASK_ID=$TaskId
PAGE_KEY=$PageKey
STATUS=V4_RUNNING
STARTED_UTC=$StartedUtc
REPO_ROOT=$RepoRoot
PAGE_ROOT=$PageRoot
NOTE=This output is produced only when the existing shared runner executes this script.
"@

$JobSpecs = @(
  @{
    Name='runner_contract_probe'
    Path=(Join-Path $ReportsDir "$TaskId`_runner_contract_detect.txt")
    Script={
      param($RepoRoot,$PageRoot,$StatusRoot,$TaskId,$PageKey)
      $out = New-Object System.Collections.Generic.List[string]
      $out.Add("TASK_ID=$TaskId")
      $out.Add("PAGE_KEY=$PageKey")
      $out.Add('REPORT_KIND=runner_contract_detect')
      $out.Add("PROBE_UTC=$((Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssZ'))")
      $known = Join-Path $RepoRoot 'docs/chatgpt_status/_shared/automation/RUN_SINGLE_AAYS_MULTI_PAGE_QUEUE_RUNNER.ps1'
      $out.Add("KNOWN_SHARED_RUNNER_PATH=$known")
      $out.Add("KNOWN_SHARED_RUNNER_EXISTS=$([string](Test-Path -LiteralPath $known))")
      foreach ($rel in @('control','queue','current-task','runner_tasks','automation','reports','status','heartbeat','runner_output')) {
        $p = Join-Path $PageRoot $rel
        $out.Add("PAGE_DIR_$($rel.Replace('-','_').ToUpper())=$([string](Test-Path -LiteralPath $p))")
        if (Test-Path -LiteralPath $p) {
          Get-ChildItem -LiteralPath $p -File -ErrorAction SilentlyContinue | Select-Object -First 25 | ForEach-Object { $out.Add("FILE:$rel/$($_.Name):$($_.Length)") }
        }
      }
      $shared = Join-Path $StatusRoot '_shared'
      if (Test-Path -LiteralPath $shared) {
        Get-ChildItem -LiteralPath $shared -Recurse -File -ErrorAction SilentlyContinue | Where-Object { $_.Name -match 'runner|queue|poll|bridge|task|ps1' } | Select-Object -First 100 | ForEach-Object { $out.Add("SHARED_CANDIDATE=$($_.FullName)") }
      } else {
        $out.Add('SHARED_ROOT_EXISTS=false')
      }
      $out -join [Environment]::NewLine
    }
  },
  @{
    Name='git_remote_sync_diagnostic'
    Path=(Join-Path $ReportsDir "$TaskId`_remote_sync_diagnostic.txt")
    Script={
      param($RepoRoot,$PageRoot,$StatusRoot,$TaskId,$PageKey)
      $out = New-Object System.Collections.Generic.List[string]
      $out.Add("TASK_ID=$TaskId")
      $out.Add("PAGE_KEY=$PageKey")
      $out.Add('REPORT_KIND=remote_sync_diagnostic')
      $out.Add("PROBE_UTC=$((Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssZ'))")
      Push-Location $RepoRoot
      try {
        $cmds = @(
          'git rev-parse --show-toplevel',
          'git branch --show-current',
          'git rev-parse HEAD',
          'git status --short',
          'git remote -v',
          'git ls-remote --heads origin main',
          'git ls-remote --heads origin aays-runner-v17-icon-work-20260603-232706'
        )
        foreach ($cmd in $cmds) {
          $out.Add("--- CMD: $cmd")
          try { $res = cmd.exe /c $cmd 2>&1; if ($res) { $out.Add(($res -join [Environment]::NewLine)) } else { $out.Add('<no output>') } }
          catch { $out.Add("ERROR=$($_.Exception.Message)") }
        }
      } finally { Pop-Location }
      $out.Add('NOTE=read_only_remote_diagnostic_no_push_no_merge_no_rebase')
      $out -join [Environment]::NewLine
    }
  },
  @{
    Name='topography_data_coverage_audit'
    Path=(Join-Path $ReportsDir "$TaskId`_data_coverage_audit.txt")
    Script={
      param($RepoRoot,$PageRoot,$StatusRoot,$TaskId,$PageKey)
      $out = New-Object System.Collections.Generic.List[string]
      $out.Add("TASK_ID=$TaskId")
      $out.Add("PAGE_KEY=$PageKey")
      $out.Add('REPORT_KIND=topography_data_coverage_audit')
      $out.Add("PROBE_UTC=$((Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssZ'))")
      $paths = @(
        'D:\topografik_map\london\terrarium_tiles',
        'F:\AAYS\london_parcel_sources\topography_reports\LONDON_ALL_PARCELS_TOPOGRAPHY_4LEVEL_20260501_001116.csv.gz',
        'D:\AAYS_DATA\topography\england',
        'D:\AAYS_DATA\topography\england\raw',
        'D:\AAYS_DATA\topography\england\tiles',
        'D:\AAYS_DATA\topography\england\processed'
      )
      foreach ($p in $paths) {
        $exists = Test-Path -LiteralPath $p
        $out.Add("PATH=$p")
        $out.Add("EXISTS=$exists")
        if ($exists) {
          try {
            $item = Get-Item -LiteralPath $p
            $out.Add("TYPE=$($item.PSIsContainer)")
            if ($item.PSIsContainer) {
              $count = (Get-ChildItem -LiteralPath $p -Recurse -File -ErrorAction SilentlyContinue | Select-Object -First 5000 | Measure-Object).Count
              $out.Add("FILE_COUNT_SAMPLE_MAX_5000=$count")
            } else {
              $out.Add("SIZE_BYTES=$($item.Length)")
            }
          } catch { $out.Add("ERROR=$($_.Exception.Message)") }
        }
      }
      $out.Add('ENGLAND_WIDE_COMPLETE_REQUIRES=raw_or_tiles_or_processed_root_present_with_nonzero_files_and_manifest')
      $out -join [Environment]::NewLine
    }
  },
  @{
    Name='lookup_coverage_audit'
    Path=(Join-Path $ReportsDir "$TaskId`_lookup_coverage_audit.txt")
    Script={
      param($RepoRoot,$PageRoot,$StatusRoot,$TaskId,$PageKey)
      $out = New-Object System.Collections.Generic.List[string]
      $out.Add("TASK_ID=$TaskId")
      $out.Add("PAGE_KEY=$PageKey")
      $out.Add('REPORT_KIND=lookup_coverage_audit')
      $out.Add("PROBE_UTC=$((Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssZ'))")
      $parcelIds = @('29759443','1','100','1000','99999999')
      foreach ($id in $parcelIds) {
        $url = "http://127.0.0.1:8010/topography/lookup?parcel_id=$id"
        $out.Add("URL=$url")
        try {
          $r = Invoke-WebRequest -Uri $url -UseBasicParsing -TimeoutSec 10
          $out.Add("HTTP_STATUS=$($r.StatusCode)")
          $body = [string]$r.Content
          $out.Add("BODY_PREVIEW=$($body.Substring(0,[Math]::Min(500,$body.Length)))")
          if ($body -match '"status"\s*:\s*"no_data"') { $out.Add("LOOKUP_DATA_STATUS_$id=no_data") }
          elseif ($body -match 'center_elevation|elevation_difference|region_average') { $out.Add("LOOKUP_DATA_STATUS_$id=has_contract_fields") }
          else { $out.Add("LOOKUP_DATA_STATUS_$id=unknown_body") }
        } catch { $out.Add("ERROR=$($_.Exception.Message)") }
      }
      $out -join [Environment]::NewLine
    }
  },
  @{
    Name='ui_static_contract_audit'
    Path=(Join-Path $ReportsDir "$TaskId`_ui_static_contract_audit.txt")
    Script={
      param($RepoRoot,$PageRoot,$StatusRoot,$TaskId,$PageKey)
      $out = New-Object System.Collections.Generic.List[string]
      $out.Add("TASK_ID=$TaskId")
      $out.Add("PAGE_KEY=$PageKey")
      $out.Add('REPORT_KIND=ui_static_contract_audit')
      $app = Join-Path $RepoRoot 'england_map_web/static/js/app.js'
      $out.Add("APP_JS=$app")
      $out.Add("APP_JS_EXISTS=$([string](Test-Path -LiteralPath $app))")
      if (Test-Path -LiteralPath $app) {
        $txt = Get-Content -LiteralPath $app -Raw -ErrorAction SilentlyContinue
        foreach ($pat in @('normalizeTopographyLookupForPopup','buildTopographyPopupRowsHtml','hight_differance.png','topography/lookup','no_data')) {
          $out.Add("PATTERN_$pat=$([string]($txt -like "*$pat*"))")
        }
      }
      $out.Add('MANUAL_UI_SMOKE_REQUIRED=true')
      $out -join [Environment]::NewLine
    }
  },
  @{
    Name='naming_debt_audit'
    Path=(Join-Path $ReportsDir "$TaskId`_naming_debt_audit.txt")
    Script={
      param($RepoRoot,$PageRoot,$StatusRoot,$TaskId,$PageKey)
      $out = New-Object System.Collections.Generic.List[string]
      $out.Add("TASK_ID=$TaskId")
      $out.Add("PAGE_KEY=$PageKey")
      $out.Add('REPORT_KIND=naming_debt_audit')
      $files = Get-ChildItem -LiteralPath $PageRoot -Recurse -File -ErrorAction SilentlyContinue | Where-Object { $_.Name -like 'pb_*' }
      $out.Add("PB_PREFIX_FILE_COUNT=$($files.Count)")
      foreach ($f in $files | Select-Object -First 100) { $out.Add("PB_FILE=$($f.FullName)") }
      $out.Add('NOTE=pb_prefix_is_naming_debt_only_unless_final_contract_requires_renamed_canonical_files')
      $out -join [Environment]::NewLine
    }
  },
  @{
    Name='final_token_verify'
    Path=(Join-Path $ReportsDir "$TaskId`_final_token_verify.txt")
    Script={
      param($RepoRoot,$PageRoot,$StatusRoot,$TaskId,$PageKey)
      $out = New-Object System.Collections.Generic.List[string]
      $out.Add("TASK_ID=$TaskId")
      $out.Add("PAGE_KEY=$PageKey")
      $out.Add('REPORT_KIND=final_token_verify')
      $matches = Get-ChildItem -LiteralPath (Join-Path $PageRoot 'reports') -File -ErrorAction SilentlyContinue | Where-Object { $_.Name -match 'final|runtime|pb' }
      foreach ($f in $matches) {
        $txt = Get-Content -LiteralPath $f.FullName -Raw -ErrorAction SilentlyContinue
        $hasA = $txt -match 'FINAL_STATUS=FINAL_READY_CONFIRMED'
        $hasB = $txt -match 'PRODUCT_PROGRESS_ESTIMATE=100'
        $hasC = $txt -match 'PRODUCTION_COMPLETE=true'
        $out.Add("FILE=$($f.Name);FINAL_STATUS_TOKEN=$hasA;PROGRESS_100_TOKEN=$hasB;PRODUCTION_COMPLETE_TOKEN=$hasC")
      }
      if (-not $matches) { $out.Add('NO_FINAL_LIKE_REPORTS_FOUND=true') }
      $out -join [Environment]::NewLine
    }
  }
)

$Jobs = @()
foreach ($Spec in $JobSpecs) {
  Add-ReportLine $RunnerOutput "START_JOB=$($Spec.Name) OUT=$($Spec.Path)"
  $Jobs += Start-Job -Name $Spec.Name -ScriptBlock $Spec.Script -ArgumentList $RepoRoot,$PageRoot,$StatusRoot,$TaskId,$PageKey
}

$TimeoutSec = 900
$Deadline = (Get-Date).AddSeconds($TimeoutSec)
while ((Get-Date) -lt $Deadline) {
  $running = @($Jobs | Where-Object { $_.State -eq 'Running' })
  Add-ReportLine $Heartbeat "HEARTBEAT_UTC=$((Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssZ'));RUNNING_JOBS=$($running.Count)"
  if ($running.Count -eq 0) { break }
  Start-Sleep -Seconds 15
}

foreach ($Job in $Jobs) {
  $spec = $JobSpecs | Where-Object { $_.Name -eq $Job.Name } | Select-Object -First 1
  if ($Job.State -eq 'Running') { Stop-Job $Job -Force | Out-Null }
  try { $content = Receive-Job $Job -ErrorAction SilentlyContinue; Write-TextFile $spec.Path (($content | Out-String).Trim()) }
  catch { Write-TextFile $spec.Path "TASK_ID=$TaskId`nPAGE_KEY=$PageKey`nREPORT_KIND=$($Job.Name)`nERROR=$($_.Exception.Message)" }
  Add-ReportLine $RunnerOutput "END_JOB=$($Job.Name) STATE=$($Job.State) OUT=$($spec.Path)"
  Remove-Job $Job -Force -ErrorAction SilentlyContinue | Out-Null
}

$Blockers = New-Object System.Collections.Generic.List[string]
function Add-BlockerIfTextMissing { param([string]$Path,[string]$Pattern,[string]$Blocker)
  if (-not (Test-Path -LiteralPath $Path)) { $Blockers.Add("missing_report:$Path"); return }
  $txt = Get-Content -LiteralPath $Path -Raw -ErrorAction SilentlyContinue
  if ($txt -notmatch $Pattern) { $Blockers.Add($Blocker) }
}

$ContractReport = Join-Path $ReportsDir "$TaskId`_runner_contract_detect.txt"
$RemoteReport = Join-Path $ReportsDir "$TaskId`_remote_sync_diagnostic.txt"
$DataReport = Join-Path $ReportsDir "$TaskId`_data_coverage_audit.txt"
$LookupReport = Join-Path $ReportsDir "$TaskId`_lookup_coverage_audit.txt"
$UiReport = Join-Path $ReportsDir "$TaskId`_ui_static_contract_audit.txt"
$TokenReport = Join-Path $ReportsDir "$TaskId`_final_token_verify.txt"

Add-BlockerIfTextMissing $ContractReport 'KNOWN_SHARED_RUNNER_EXISTS=True|SHARED_CANDIDATE=' 'runner_contract_not_proven_in_repo_or_shared_root'
Add-BlockerIfTextMissing $DataReport 'D:\\AAYS_DATA\\topography\\england.*?EXISTS=True|D:\\AAYS_DATA\\topography\\england\\tiles.*?EXISTS=True|D:\\AAYS_DATA\\topography\\england\\processed.*?EXISTS=True' 'england_wide_topography_root_not_proven'
Add-BlockerIfTextMissing $LookupReport 'HTTP_STATUS=200' 'lookup_endpoint_not_proven_200_during_v4'
if (Test-Path -LiteralPath $LookupReport) {
  $ltxt = Get-Content -LiteralPath $LookupReport -Raw -ErrorAction SilentlyContinue
  if ($ltxt -match 'LOOKUP_DATA_STATUS_29759443=no_data') { $Blockers.Add('sample_lookup_29759443_returns_no_data') }
}
Add-BlockerIfTextMissing $UiReport 'PATTERN_normalizeTopographyLookupForPopup=True' 'ui_normalize_function_not_proven'
Add-BlockerIfTextMissing $UiReport 'PATTERN_buildTopographyPopupRowsHtml=True' 'ui_popup_rows_function_not_proven'
Add-BlockerIfTextMissing $TokenReport 'FINAL_STATUS_TOKEN=True;PROGRESS_100_TOKEN=True;PRODUCTION_COMPLETE_TOKEN=True' 'canonical_final_tokens_not_proven_together_by_v4'
$Blockers.Add('manual_ui_parcel_click_smoke_not_proven_by_automated_runner')

$BlockerText = @()
$BlockerText += "TASK_ID=$TaskId"
$BlockerText += "PAGE_KEY=$PageKey"
$BlockerText += "REPORT_KIND=v4_blockers"
$BlockerText += "BLOCKER_COUNT=$($Blockers.Count)"
foreach ($b in $Blockers) { $BlockerText += "BLOCKER=$b" }
Write-TextFile $BlockerReport ($BlockerText -join [Environment]::NewLine)

$EndedUtc = (Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssZ')
if ($Blockers.Count -eq 0) {
  $finalStatusValue = 'FINAL_READY_CONFIRMED'
  $progress = '100'
  $prodComplete = 'true'
} else {
  $finalStatusValue = 'BLOCKED_PENDING_EVIDENCE'
  $progress = '92'
  $prodComplete = 'false'
}

$FinalReportText = @"
TASK_ID=$TaskId
PAGE_KEY=$PageKey
REPORT_KIND=final_report
STARTED_UTC=$StartedUtc
ENDED_UTC=$EndedUtc
FINAL_STATUS=$finalStatusValue
PRODUCT_PROGRESS_ESTIMATE=$progress
PRODUCTION_COMPLETE=$prodComplete
BLOCKER_COUNT=$($Blockers.Count)

REPORTS_WRITTEN:
- reports/$TaskId`_runner_contract_detect.txt
- reports/$TaskId`_remote_sync_diagnostic.txt
- reports/$TaskId`_data_coverage_audit.txt
- reports/$TaskId`_lookup_coverage_audit.txt
- reports/$TaskId`_ui_static_contract_audit.txt
- reports/$TaskId`_naming_debt_audit.txt
- reports/$TaskId`_final_token_verify.txt
- reports/$TaskId`_v4_blockers.txt

RULE:
FINAL_READY_CONFIRMED is emitted only when blocker_count is zero. No fake final token is emitted by this script.
"@
Write-TextFile $FinalReport $FinalReportText

$FinalStatusText = @"
TASK_ID=$TaskId
PAGE_KEY=$PageKey
STATUS=$finalStatusValue
PRODUCT_PROGRESS_ESTIMATE=$progress
PRODUCTION_COMPLETE=$prodComplete
BLOCKER_COUNT=$($Blockers.Count)
POWER_SHELL_REQUIRED_FROM_USER=false
EXPECTED_REPORT=docs/chatgpt_status/$PageKey/reports/$TaskId`_final_report.txt
EXPECTED_STATUS=docs/chatgpt_status/$PageKey/status/$TaskId`_final.status.txt
ENDED_UTC=$EndedUtc
"@
Write-TextFile $FinalStatus $FinalStatusText
Write-TextFile $Heartbeat "TASK_ID=$TaskId`nPAGE_KEY=$PageKey`nSTATUS=V4_FINISHED`nENDED_UTC=$EndedUtc`nBLOCKER_COUNT=$($Blockers.Count)`nFINAL_STATUS=$finalStatusValue"
Add-ReportLine $RunnerOutput "FINAL_STATUS=$finalStatusValue BLOCKERS=$($Blockers.Count) ENDED_UTC=$EndedUtc"
exit 0
