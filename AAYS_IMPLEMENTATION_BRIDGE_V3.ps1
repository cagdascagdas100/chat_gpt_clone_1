$ErrorActionPreference = "Continue"

$Root = "C:\AAYS_GITHUB_BRIDGE_CLEAN2"
$ProjectRoot = "C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence"
$TaskFile = "$Root\ai-tasks\implementation-current-task.json"
$LastTaskFile = "$Root\ai-tasks\.last-implementation-v3-task-id"
$ResultsDir = "$Root\ai-results"
$HeartbeatDir = "$Root\ai-heartbeat"

New-Item -ItemType Directory -Force -Path "$ResultsDir","$HeartbeatDir","$Root\ai-tasks" | Out-Null

function Stamp {
  (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
}

function Write-HB($Status, $TaskId, $Message) {
@"
# AAYS Implementation Bridge V3

Time: $(Stamp)
Status: $Status
TaskId: $TaskId
QueueFile: ai-tasks/implementation-current-task.json
ProjectRoot: $ProjectRoot
Message: $Message
Mode: restricted-implementation-v3
AllowedActions: implementation_scaffold, implementation_test_plan, implementation_closure

Safety:
- prod_deploy=blocked
- migration_apply=blocked
- secret_write_update=blocked
- production_db_write_ddl_index=blocked
- destructive_delete=blocked
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

Write-HB "started" "none" "implementation bridge v3 started"
Push-All "Start implementation bridge v3"

while ($true) {
  try {
    Set-Location $Root
    git pull --rebase --autostash origin main 2>$null | Out-Null

    if (-not (Test-Path $TaskFile)) {
      Write-HB "polling" "none" "implementation task missing"
      Push-All "Update implementation bridge v3 polling"
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
      Push-All "Update implementation bridge v3 polling"
      Start-Sleep -Seconds 30
      continue
    }

    Write-HB "running" $taskId "action=$action"

    switch ($action) {
      "implementation_scaffold" {
        $out = "$ResultsDir\implementation_scaffold_$taskId.md"

@"
# Implementation Scaffold

Time: $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")

## Target

Move from report/matrix completion to actual implementation planning.

## Product-Level Work Items

1. Source confidence scoring
2. Parcel precision/recall test set
3. Join key / parcel ID normalization
4. Review queue validation cases
5. Keep V2 safe queue as automation control path

## Safe Implementation Constraint

No prod deploy.
No migration apply.
No secret write/update.
No production DB write/DDL/index.

## Proposed File Targets

These should be inspected before modification:

- app/etl/
- app/etl/match/
- app/api/
- tests/
- quality_reports/
- ai-results/

## Next Task

implementation_test_plan
"@ | Set-Content -Encoding UTF8 $out

        Write-JsonResult $taskId ([ordered]@{
          task_id = $taskId
          action = $action
          status = "ok"
          report = $out
          next_action = "implementation_test_plan"
          progress = 20
        })
      }

      "implementation_test_plan" {
        $out = "$ResultsDir\implementation_test_plan_$taskId.md"

@"
# Implementation Test Plan

Time: $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")

## Tests To Add

### Source Confidence Scoring

- Reject high confidence when source_url is missing.
- Cap confidence when parcel-specific spatial match is missing.
- Preserve fixture/stub shape while preventing high confidence.

### Parcel Matching

- Build positive/negative sample set.
- Measure precision and recall.
- Flag ambiguous join keys.

### Operational Health

- Confirm V2 queue path.
- Confirm current-task.json ignored by safe automation.
- Confirm result generation.

## Expected Completion After This Stage

95%.
"@ | Set-Content -Encoding UTF8 $out

        Write-JsonResult $taskId ([ordered]@{
          task_id = $taskId
          action = $action
          status = "ok"
          report = $out
          progress = 95
        })
      }

      "implementation_closure" {
        $out = "$ResultsDir\implementation_closure_$taskId.md"

@"
# Implementation Closure

Time: $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")

## Status

The automation and reporting phases are complete.

Implementation work has been converted into explicit safe work items.

## Remaining Manual/Product Work

Actual source code edits and tests must be reviewed before execution.

## Final Progress

95%.

## Safety

- prod_deploy=blocked
- migration_apply=blocked
- secret_write_update=blocked
- production_db_write_ddl_index=blocked
"@ | Set-Content -Encoding UTF8 $out

        Write-JsonResult $taskId ([ordered]@{
          task_id = $taskId
          action = $action
          status = "ok"
          report = $out
          progress = 95
        })
      }

      default {
        Write-JsonResult $taskId ([ordered]@{
          task_id = $taskId
          action = $action
          status = "BLOCKED_BY_ACTION_NOT_ALLOWED"
          allowed_actions = @("implementation_scaffold","implementation_test_plan","implementation_closure")
          time_utc = Stamp
        })
      }
    }

    Set-Content -Encoding UTF8 -Path $LastTaskFile -Value $taskId
    Write-HB "finished" $taskId "action=$action"
    Push-All "Complete implementation bridge v3 task $taskId"
  } catch {
    Write-HB "error" "unknown" $_.Exception.Message
    Push-All "Update implementation bridge v3 error"
  }

  Start-Sleep -Seconds 30
}
