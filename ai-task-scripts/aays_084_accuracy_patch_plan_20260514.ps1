$ErrorActionPreference = 'Continue'
$TaskId = 'aays-084-accuracy-patch-plan-20260514'
$BridgeRoot = if ($env:AAYS_BRIDGE_ROOT) { $env:AAYS_BRIDGE_ROOT } else { Split-Path -Parent $PSScriptRoot }
$ProjectRoot = 'C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence'
$ResultDir = Join-Path $BridgeRoot 'ai-results'
$HeartbeatDir = Join-Path $BridgeRoot 'ai-heartbeat'
New-Item -ItemType Directory -Force -Path $ResultDir,$HeartbeatDir | Out-Null
$Stamp = Get-Date -Format 'yyyyMMdd_HHmmss_ffff'
$Report = Join-Path $ResultDir ("aays-084-accuracy-patch-plan-$Stamp.md")
$Heartbeat = Join-Path $HeartbeatDir 'accuracy-patch-plan.md'
$Audit = Join-Path $HeartbeatDir 'wide-accuracy-gap-audit.md'
$Lines = New-Object System.Collections.Generic.List[string]
function L([string]$m){ [void]$Lines.Add($m) }
function AddSection($Title){ L ''; L ('## ' + $Title) }
function ListExisting($Title,$Paths){
  AddSection $Title
  foreach($p in $Paths){ if(Test-Path $p){ L ('FOUND: ' + $p) } else { L ('MISSING: ' + $p) } }
}
L '# AAYS 084 Accuracy Patch Plan'
L ('Generated: ' + (Get-Date -Format s))
L ('TaskId: ' + $TaskId)
L ('BridgeRoot: ' + $BridgeRoot)
L ('ProjectRoot: ' + $ProjectRoot)
L 'Mode: read-only plan; no DB writes; no UI patch.'
AddSection 'Audit source'
if(Test-Path $Audit){ L ('FOUND_AUDIT=' + $Audit); try { L 'Audit tail:'; L '```text'; Get-Content $Audit -Tail 80 -ErrorAction SilentlyContinue | ForEach-Object { L $_ }; L '```' } catch { L ('AUDIT_TAIL_ERROR=' + $_.Exception.Message) } } else { L ('MISSING_AUDIT=' + $Audit) }
ListExisting 'Core application files to inspect first' @(
  (Join-Path $ProjectRoot 'app\main.py'),
  (Join-Path $ProjectRoot 'app\services\cost_engine_service.py'),
  (Join-Path $ProjectRoot 'AAYS_TerraYield_FINAL_STABILIZE_PERF_VALIDATE.ps1'),
  (Join-Path $ProjectRoot '.aays_next_fix'),
  (Join-Path $ProjectRoot '.aays_50step_plan')
)
AddSection 'Patch lane 1 - source accuracy'
L 'Goal: lift source accuracy estimate from 45/100 to 60+/100.'
L 'Actions:'
L '1. Build a source registry: dataset name, path, authority level, freshness, schema, licence/status.'
L '2. Mark non-authoritative/demo CSVs so scoring does not treat them as trusted production evidence.'
L '3. Add schema fingerprints for sales history, parcel, valuation, and cost inputs.'
L '4. Add stale-data checks: missing date, old modified date, unknown provenance.'
AddSection 'Patch lane 2 - parcel match accuracy'
L 'Goal: lift parcel match accuracy estimate from 27/100 to 45+/100.'
L 'Actions:'
L '1. Create validation sample: exact matches, fuzzy matches, known non-matches, ambiguous multi-match rows.'
L '2. Standardize parcel keys: normalize case, whitespace, punctuation, leading zeros, borough/local authority fields.'
L '3. Add scoring fields: match_method, match_confidence, conflict_reason, source_priority.'
L '4. Fail closed on ambiguous parcel candidates instead of selecting first candidate silently.'
AddSection 'Patch lane 3 - endpoint and regression health'
L 'Goal: make API/endpoint health measurable before UI or DB-heavy jobs.'
L 'Actions:'
L '1. Add read-only health probe list for app/main.py routes.'
L '2. Add regression smoke script that records HTTP status, response time, and JSON shape.'
L '3. Keep probes separate from DB imports; emit markdown and machine-readable JSON.'
AddSection 'Patch lane 4 - runner hygiene'
L 'Goal: preserve the now-working single-runner model.'
L 'Actions:'
L '1. One Direct Autopilot instance only; kill duplicates before restart.'
L '2. Keep current-task short unless launching detached workers.'
L '3. For long workers, use unique run id, manifest, stdout/stderr files, and collector.'
L '4. Never run blocking DB job directly inside main runner.'
AddSection 'Recommended next task'
L 'AAYS 085 should be read-only source registry inventory: list candidate datasets, classify trusted/demo/archive, and produce source_registry_seed.md/json.'
L 'No DB writes. No UI patch. Timeout 180s.'
AddSection 'Progress update'
L 'runner_automation_percent: 100'
L 'single_runner_stability_percent: 100'
L 'db_dryrun_validation_percent: 99.9'
L 'wide_accuracy_program_percent: 40'
L 'next_expected_after_085_percent: 45'
L 'AAYS_084_ACCURACY_PATCH_PLAN_DONE=true'
Set-Content -Encoding UTF8 -Path $Report -Value $Lines
Set-Content -Encoding UTF8 -Path $Heartbeat -Value $Lines
Write-Output 'AAYS_084_ACCURACY_PATCH_PLAN_DONE=true'
Write-Output ('REPORT=' + $Report)
exit 0
