[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'

$repoRoot = if ($env:AAYS_REPO_ROOT) {
  [System.IO.Path]::GetFullPath($env:AAYS_REPO_ROOT)
} else {
  [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..\..\..'))
}

$pythonScript = Join-Path $repoRoot 'docs\chatgpt_status\security_public_safety\automation\security_public_safety_3_smoke_v5_2_11.py'
$outputPath = Join-Path $repoRoot 'docs\chatgpt_status\security_public_safety\runner_outputs\security_public_safety_3_smoke_candidates_v5_2_latest.json'
$websitePath = Join-Path $repoRoot 'england_map_web\data\security_public_safety\security_public_safety_3_smoke_rows_latest.json'
$reconciliationPath = Join-Path $repoRoot 'docs\chatgpt_status\security_public_safety\runner_outputs\security_public_safety_3_smoke_reconciliation_v5_2_latest.json'
$manifestPath = Join-Path $repoRoot 'england_map_web\data\security_public_safety\security_public_safety_3_publication_manifest_latest.json'

function Set-JsonProperty {
  param(
    [Parameter(Mandatory=$true)] [object] $Object,
    [Parameter(Mandatory=$true)] [string] $Name,
    [AllowNull()] [object] $Value
  )
  $Object | Add-Member -NotePropertyName $Name -NotePropertyValue $Value -Force
}

function Write-JsonAtomic {
  param(
    [Parameter(Mandatory=$true)] [string] $Path,
    [Parameter(Mandatory=$true)] [object] $Value
  )
  $directory = Split-Path -Parent $Path
  if (-not (Test-Path -LiteralPath $directory -PathType Container)) {
    New-Item -ItemType Directory -Path $directory -Force | Out-Null
  }
  $tempPath = Join-Path $directory ('.aays-' + [guid]::NewGuid().ToString('N') + '.tmp')
  $json = $Value | ConvertTo-Json -Depth 100
  [System.IO.File]::WriteAllText($tempPath, $json + [Environment]::NewLine, [System.Text.UTF8Encoding]::new($false))
  if (Test-Path -LiteralPath $Path -PathType Leaf) {
    [System.IO.File]::Replace($tempPath, $Path, $null)
  } else {
    [System.IO.File]::Move($tempPath, $Path)
  }
}

function Invoke-EmergencyQuarantine {
  param([Parameter(Mandatory=$true)] [string] $Reason)

  foreach ($path in @($outputPath, $websitePath)) {
    if (-not (Test-Path -LiteralPath $path -PathType Leaf)) { continue }
    try {
      $payload = Get-Content -LiteralPath $path -Raw -Encoding UTF8 | ConvertFrom-Json
      if ($payload.rows) {
        foreach ($row in @($payload.rows)) {
          Set-JsonProperty $row 'security_score_percent' $null
          Set-JsonProperty $row 'publication_quarantine_gate' $false
          Set-JsonProperty $row 'prepublication_artifact_digest_gate' $false
          Set-JsonProperty $row 'published_score_release_gate' $false
          Set-JsonProperty $row 'final_artifact_manifest_gate' $false
          Set-JsonProperty $row 'final_artifact_manifest_fingerprint' $null
          Set-JsonProperty $row 'needs_manual_review' $true
          $status = [string]$row.candidate_status
          if (-not $status.StartsWith('POWERSHELL_EMERGENCY_QUARANTINED_')) {
            Set-JsonProperty $row 'candidate_status' ('POWERSHELL_EMERGENCY_QUARANTINED_' + $status)
          }
        }
      }
      Set-JsonProperty $payload 'task_version' '5.2.11-final-artifact-manifest'
      Set-JsonProperty $payload 'attempt_id' 'security-public-safety-3-20260721-020'
      Set-JsonProperty $payload 'supersedes_attempt_id' 'security-public-safety-3-20260721-019'
      Set-JsonProperty $payload 'publication_quarantine_passed' $false
      Set-JsonProperty $payload 'prepublication_artifact_digest_gate' $false
      Set-JsonProperty $payload 'published_score_release_gate' $false
      Set-JsonProperty $payload 'final_artifact_manifest_required' $true
      Set-JsonProperty $payload 'final_artifact_manifest_passed' $false
      Set-JsonProperty $payload 'final_artifact_manifest_fingerprint' $null
      Set-JsonProperty $payload 'final_artifact_manifest_errors' @($Reason)
      Set-JsonProperty $payload 'published_score_row_count' 0
      Set-JsonProperty $payload 'verified_slot_rows' 0
      Set-JsonProperty $payload 'actual_slot_rows_written' 0
      Set-JsonProperty $payload 'runtime_acceptance_passed' $false
      Set-JsonProperty $payload 'runtime_execution_success' $false
      Set-JsonProperty $payload 'fake_data' $false
      Set-JsonProperty $payload 'final_ready' $false
      Write-JsonAtomic -Path $path -Value $payload
    } catch {
      Write-Warning "EMERGENCY_QUARANTINE_FAILED path=$path error=$($_.Exception.Message)"
    }
  }

  if (Test-Path -LiteralPath $reconciliationPath -PathType Leaf) {
    try {
      $reconciliation = Get-Content -LiteralPath $reconciliationPath -Raw -Encoding UTF8 | ConvertFrom-Json
      Set-JsonProperty $reconciliation 'task_version' '5.2.11-final-artifact-manifest'
      Set-JsonProperty $reconciliation 'attempt_id' 'security-public-safety-3-20260721-020'
      Set-JsonProperty $reconciliation 'supersedes_attempt_id' 'security-public-safety-3-20260721-019'
      Set-JsonProperty $reconciliation 'publication_quarantine_passed' $false
      Set-JsonProperty $reconciliation 'final_artifact_manifest_required' $true
      Set-JsonProperty $reconciliation 'final_artifact_manifest_passed' $false
      Set-JsonProperty $reconciliation 'final_artifact_manifest_errors' @($Reason)
      Set-JsonProperty $reconciliation 'published_score_row_count' 0
      Set-JsonProperty $reconciliation 'actual_slot_rows_written' 0
      Set-JsonProperty $reconciliation 'runtime_acceptance_passed' $false
      Set-JsonProperty $reconciliation 'runtime_execution_success' $false
      Set-JsonProperty $reconciliation 'fake_data' $false
      Set-JsonProperty $reconciliation 'final_ready' $false
      Write-JsonAtomic -Path $reconciliationPath -Value $reconciliation
    } catch {
      Write-Warning "EMERGENCY_RECONCILIATION_QUARANTINE_FAILED error=$($_.Exception.Message)"
    }
  }

  try {
    $manifest = [ordered]@{
      schema_version = 1
      slot_id = 'security_public_safety_3'
      task_version = '5.2.11-final-artifact-manifest'
      attempt_id = 'security-public-safety-3-20260721-020'
      supersedes_attempt_id = 'security-public-safety-3-20260721-019'
      generated_at = [DateTime]::UtcNow.ToString('o')
      phase = 'powershell-emergency-quarantine'
      final_artifact_manifest_required = $true
      final_artifact_manifest_passed = $false
      final_artifact_sha256 = [ordered]@{}
      published_score_row_count = 0
      ordered_target_parcels = @('parcel_61523','parcel_61524','parcel_61525')
      errors = @($Reason)
      fake_data = $false
      final_ready = $false
    }
    Write-JsonAtomic -Path $manifestPath -Value $manifest
  } catch {
    Write-Warning "EMERGENCY_MANIFEST_WRITE_FAILED error=$($_.Exception.Message)"
  }
}

if (-not (Test-Path -LiteralPath $pythonScript -PathType Leaf)) {
  Invoke-EmergencyQuarantine -Reason "V5_2_11_SMOKE_PYTHON_SCRIPT_MISSING:$pythonScript"
  throw "V5_2_11_SMOKE_PYTHON_SCRIPT_MISSING: $pythonScript"
}

$python = Get-Command python -ErrorAction SilentlyContinue
if (-not $python) { $python = Get-Command py -ErrorAction SilentlyContinue }
if (-not $python) {
  Invoke-EmergencyQuarantine -Reason 'PYTHON_EXECUTABLE_NOT_FOUND'
  throw 'PYTHON_EXECUTABLE_NOT_FOUND'
}

Write-Output 'SLOT_ID=security_public_safety_3'
Write-Output 'TASK_VERSION=5.2.11-final-artifact-manifest'
Write-Output 'ATTEMPT_ID=security-public-safety-3-20260721-020'
Write-Output "REPO_ROOT=$repoRoot"
Write-Output "PYTHON_SCRIPT=$pythonScript"

try {
  if ($python.Name -eq 'py.exe' -or $python.Name -eq 'py') {
    & $python.Source -3 $pythonScript
  } else {
    & $python.Source $pythonScript
  }
  $exitCode = $LASTEXITCODE
  if ($null -eq $exitCode) { $exitCode = 1 }
} catch {
  $exitCode = 2
  Write-Warning "PYTHON_EXECUTION_EXCEPTION=$($_.Exception.Message)"
}

if ($exitCode -eq 0) {
  try {
    if (-not (Test-Path -LiteralPath $manifestPath -PathType Leaf)) {
      throw 'FINAL_ARTIFACT_MANIFEST_MISSING'
    }
    $manifest = Get-Content -LiteralPath $manifestPath -Raw -Encoding UTF8 | ConvertFrom-Json
    if (-not $manifest.final_artifact_manifest_passed) {
      throw 'FINAL_ARTIFACT_MANIFEST_NOT_PASSED'
    }
    if ($manifest.attempt_id -ne 'security-public-safety-3-20260721-020') {
      throw 'FINAL_ARTIFACT_MANIFEST_ATTEMPT_MISMATCH'
    }
    if ($manifest.published_score_row_count -lt 1) {
      throw 'FINAL_ARTIFACT_MANIFEST_ZERO_RELEASED_ROWS'
    }
  } catch {
    $exitCode = 2
    Write-Warning "FINAL_MANIFEST_CARRIER_CHECK_FAILED=$($_.Exception.Message)"
  }
}

if ($exitCode -ne 0) {
  Invoke-EmergencyQuarantine -Reason "PYTHON_OR_MANIFEST_EXIT_CODE_$exitCode"
}

Write-Output "PYTHON_EXIT_CODE=$exitCode"
Write-Output 'FINAL_READY=false'
exit $exitCode
