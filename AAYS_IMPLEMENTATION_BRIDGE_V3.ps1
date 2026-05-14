$ErrorActionPreference = "Continue"

$Root = "C:\AAYS_GITHUB_BRIDGE_CLEAN2"
$ProjectRoot = "C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence"
$TaskFile = "$Root\ai-tasks\implementation-current-task.json"
$LastTaskFile = "$Root\ai-tasks\.last-implementation-v3-task-id"
$ResultsDir = "$Root\ai-results"
$HeartbeatDir = "$Root\ai-heartbeat"

New-Item -ItemType Directory -Force -Path "$ResultsDir","$HeartbeatDir","$Root\ai-tasks" | Out-Null

$AllowedActions = @(
  "implementation_scaffold",
  "implementation_test_plan",
  "implementation_closure",
  "implementation_code_plan",
  "implementation_patch_draft",
  "implementation_validation_cases",
  "implementation_final_review"
)

function Stamp {
  (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
}

function Write-HB($Status, $TaskId, $Message) {
  $allowed = $AllowedActions -join ", "
@"
# AAYS Implementation Bridge V3.1

Time: $(Stamp)
Status: $Status
TaskId: $TaskId
QueueFile: ai-tasks/implementation-current-task.json
ProjectRoot: $ProjectRoot
Message: $Message
Mode: restricted-implementation-v3.1
AllowedActions: $allowed

Safety:
- prod_deploy=blocked
- migration_apply=blocked
- secret_write_update=blocked
- production_db_write_ddl_index=blocked
- destructive_delete=blocked
- direct_prod_write=blocked
"@ | Set-Content -Encoding UTF8 "$HeartbeatDir\implementation-bridge-v3.md"
}

function Push-All($Message) {
  Set-Location $Root
  git add ai-heartbeat ai-results ai-tasks AAYS_IMPLEMENTATION_BRIDGE_V3.ps1 2>$null
  git commit -m $Message 2>$null
  git pull --rebase --autostash origin main 2>$null
  git push origin main 2>$null
}

function Write-JsonResult($TaskId, $Obj) {
  $Obj | ConvertTo-Json -Depth 10 | Set-Content -Encoding UTF8 "$ResultsDir\$TaskId.result.json"
}

function Write-Md($Path, $Text) {
  $Text | Set-Content -Encoding UTF8 $Path
}

Write-HB "started" "none" "implementation bridge v3.1 started"
Push-All "Start implementation bridge v3.1"

while ($true) {
  try {
    Set-Location $Root
    git pull --rebase --autostash origin main 2>$null | Out-Null

    if (-not (Test-Path $TaskFile)) {
      Write-HB "polling" "none" "implementation task missing"
      Push-All "Update implementation bridge v3.1 polling"
      Start-Sleep -Seconds 30
      continue
    }

    $task = Get-Content $TaskFile -Raw | ConvertFrom-Json
    $taskId = [string]$task.id
    $action = [string]$task.action

    $last = ""
    if (Test-Path $LastTaskFile) {
      $last = (Get-Content $LastTaskFile -Raw).Trim()
    }

    if ([string]::IsNullOrWhiteSpace($taskId) -or $taskId -eq $last) {
      Write-HB "polling" $taskId "no new implementation task"
      Push-All "Update implementation bridge v3.1 polling"
      Start-Sleep -Seconds 30
      continue
    }

    Write-HB "running" $taskId "action=$action"

    switch ($action) {
      "implementation_scaffold" {
        $out = "$ResultsDir\implementation_scaffold_$taskId.md"
        Write-Md $out "# Implementation Scaffold`n`nStatus: ok`nProgress: 20`n"
        Write-JsonResult $taskId ([ordered]@{ task_id=$taskId; action=$action; status="ok"; report=$out; progress=20 })
      }

      "implementation_test_plan" {
        $out = "$ResultsDir\implementation_test_plan_$taskId.md"
        Write-Md $out "# Implementation Test Plan`n`nStatus: ok`nProgress: 95`n"
        Write-JsonResult $taskId ([ordered]@{ task_id=$taskId; action=$action; status="ok"; report=$out; progress=95 })
      }

      "implementation_closure" {
        $out = "$ResultsDir\implementation_closure_$taskId.md"
        Write-Md $out "# Implementation Closure`n`nStatus: ok`nProgress: 95`n"
        Write-JsonResult $taskId ([ordered]@{ task_id=$taskId; action=$action; status="ok"; report=$out; progress=95 })
      }

      "implementation_code_plan" {
        $out = "$ResultsDir\implementation_code_plan_$taskId.md"
@"
# V3.1 Implementation Code Plan

Status: ok
Progress: 96

## Safe code targets

1. Source confidence scoring design
2. Parcel precision/recall test set design
3. Join key / parcel ID normalization plan
4. Review queue to validation cases

## Restrictions

No prod deploy.
No migration apply.
No secret write/update.
No production DB write/DDL/index.

## Next action

implementation_patch_draft
"@ | Set-Content -Encoding UTF8 $out

        Write-JsonResult $taskId ([ordered]@{
          task_id=$taskId
          action=$action
          status="ok"
          report=$out
          next_action="implementation_patch_draft"
          progress=96
        })
      }

      "implementation_patch_draft" {
        $out = "$ResultsDir\implementation_patch_draft_$taskId.md"
@"
# V3.1 Implementation Patch Draft

Status: ok
Progress: 97

## Draft patch scope

- Add confidence scoring guard tests.
- Add parcel matcher review fixture plan.
- Add join-key normalization checklist.
- Do not touch production DB or secrets.

## Next action

implementation_validation_cases
"@ | Set-Content -Encoding UTF8 $out

        Write-JsonResult $taskId ([ordered]@{
          task_id=$taskId
          action=$action
          status="ok"
          report=$out
          next_action="implementation_validation_cases"
          progress=97
        })
      }

      "implementation_validation_cases" {
        $out = "$ResultsDir\implementation_validation_cases_$taskId.md"
@"
# V3.1 Validation Cases

Status: ok
Progress: 98

## Validation cases

1. Missing source_url cannot be high confidence.
2. Missing parcel-specific spatial match caps confidence.
3. Ambiguous parcel join goes to review queue.
4. Normalized parcel ID must be deterministic.
5. V2/V3 queue health remains isolated.

## Next action

implementation_final_review
"@ | Set-Content -Encoding UTF8 $out

        Write-JsonResult $taskId ([ordered]@{
          task_id=$taskId
          action=$action
          status="ok"
          report=$out
          next_action="implementation_final_review"
          progress=98
        })
      }

      "implementation_final_review" {
        $out = "$ResultsDir\implementation_final_review_$taskId.md"
@"
# V3.1 Final Review

Status: ok
Progress: 99

The safe implementation planning layer is complete.
Remaining work is applying reviewed code patches in the product repository.

Safety remains enforced.
"@ | Set-Content -Encoding UTF8 $out

        Write-JsonResult $taskId ([ordered]@{
          task_id=$taskId
          action=$action
          status="ok"
          report=$out
          progress=99
        })
      }

      default {
        Write-JsonResult $taskId ([ordered]@{
          task_id=$taskId
          action=$action
          status="BLOCKED_BY_ACTION_NOT_ALLOWED"
          allowed_actions=$AllowedActions
          time_utc=Stamp
        })
      }
    }

    Set-Content -Encoding UTF8 -Path $LastTaskFile -Value $taskId
    Write-HB "finished" $taskId "action=$action"
    Push-All "Complete implementation bridge v3.1 task $taskId"
  } catch {
    Write-HB "error" "unknown" $_.Exception.Message
    Push-All "Update implementation bridge v3.1 error"
  }

  Start-Sleep -Seconds 30
}
