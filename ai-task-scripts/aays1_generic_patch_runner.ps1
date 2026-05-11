$ErrorActionPreference = "Continue"

$BridgeRoot = "C:\AAYS1_GITHUB_BRIDGE\chat_gpt_clone_1"
$Backend = "C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence"
$TaskFile = Join-Path $BridgeRoot "ai-tasks\aays1-current-task.json"
$ResultsDir = Join-Path $BridgeRoot "ai-results"

New-Item -ItemType Directory -Force -Path $ResultsDir | Out-Null

$Task = Get-Content -Path $TaskFile -Raw | ConvertFrom-Json
$TaskId = [string]$Task.id
$Errors = New-Object System.Collections.Generic.List[string]
$Changed = New-Object System.Collections.Generic.List[string]

function Add-Err {
  param([string]$Message)
  if ($Message) { [void]$Errors.Add($Message) }
}

try {
  $BackendRoot = [System.IO.Path]::GetFullPath($Backend)

  foreach ($Patch in @($Task.patches)) {
    $RelativePath = [string]$Patch.path
    $Target = [System.IO.Path]::GetFullPath((Join-Path $Backend $RelativePath))

    if (-not $Target.StartsWith($BackendRoot, [System.StringComparison]::OrdinalIgnoreCase)) {
      throw "Patch target outside backend: $RelativePath"
    }

    if (-not (Test-Path -Path $Target)) {
      throw "Patch target not found: $RelativePath"
    }

    $Text = Get-Content -Path $Target -Raw
    $Old = [string]$Patch.old
    $New = [string]$Patch.new

    if (-not $Text.Contains($Old)) {
      throw "Old text not found in: $RelativePath"
    }

    $Text = $Text.Replace($Old, $New)
    Set-Content -Path $Target -Value $Text -Encoding UTF8
    [void]$Changed.Add($RelativePath)
  }
} catch {
  Add-Err $_.Exception.Message
}

$SyntaxExitCode = 0
$SyntaxOutput = ""
$PytestExitCode = 0
$PytestOutput = ""

try {
  Push-Location $Backend

  if ($Task.syntax_paths) {
    $SyntaxOutput = (& python -m py_compile @($Task.syntax_paths) 2>&1 | Out-String)
    $SyntaxExitCode = $LASTEXITCODE
  }

  if ($Task.pytest_path) {
    New-Item -ItemType Directory -Force -Path ".tmp_pytest_aays1" | Out-Null
    $PytestOutput = (& python -m pytest ([string]$Task.pytest_path) -q --basetemp=.tmp_pytest_aays1 2>&1 | Out-String)
    $PytestExitCode = $LASTEXITCODE
  }

  Pop-Location
} catch {
  try { Pop-Location } catch {}
  Add-Err $_.Exception.Message
  if ($null -eq $SyntaxExitCode) { $SyntaxExitCode = 999 }
  if ($null -eq $PytestExitCode) { $PytestExitCode = 999 }
}

$Status = if (($Errors.Count -eq 0) -and ($SyntaxExitCode -eq 0) -and ($PytestExitCode -eq 0)) {
  "completed"
} else {
  "failed"
}

$Audit = [ordered]@{
  task_id = $TaskId
  status = $Status
  generated_at = (Get-Date).ToString("s")
  changed = @($Changed)
  errors = @($Errors)
  syntax_exit_code = $SyntaxExitCode
  pytest_exit_code = $PytestExitCode
  syntax_output = $SyntaxOutput
  pytest_output = $PytestOutput
  runner = "aays1_generic_patch_runner"
}

$AuditPath = Join-Path $ResultsDir "$TaskId.audit.json"
$ReportPath = Join-Path $ResultsDir "$TaskId.report.md"

$Audit | ConvertTo-Json -Depth 10 | Set-Content -Path $AuditPath -Encoding UTF8

@(
  "# AAYS1 Generic Patch Runner",
  "",
  "Status: $Status",
  "Syntax exit code: $SyntaxExitCode",
  "Pytest exit code: $PytestExitCode",
  "",
  "Changed:",
  ($Changed | ForEach-Object { "- $_" }),
  "",
  "Errors:",
  ($Errors | ForEach-Object { "- $_" })
) | Set-Content -Path $ReportPath -Encoding UTF8

if ($Status -eq "completed") { exit 0 }
exit 1
