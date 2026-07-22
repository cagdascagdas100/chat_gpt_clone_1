#!/usr/bin/env python3
"""Inject a bounded real-time Python stage runner into the height_difference_1 carrier."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import tempfile
from typing import Any

SLOT_ID = "height_difference_1"
SCRIPT_VERSION = "1.0-carrier-python-stage-watchdog-injector"
PATCH_LABEL = "PYTHON_STAGE_REALTIME_WATCHDOG"
STAGE_MAX_SECONDS = 1650
STAGE_HEARTBEAT_SECONDS = 30
STAGE_POLL_SECONDS = 5

OLD_INVOKE_PYTHON = r'''function Invoke-Python {
  param([string[]]$Arguments)
  $lines = if ($python.Name -eq 'py.exe' -or $python.Name -eq 'py') {
    & $python.Source -3 @Arguments 2>&1
  } else {
    & $python.Source @Arguments 2>&1
  }
  $code = $LASTEXITCODE
  if ($null -eq $code) { $code = 1 }
  foreach ($line in @($lines)) { [Console]::Out.WriteLine([string]$line) }
  return [int]$code
}
'''

NEW_INVOKE_PYTHON = r'''function Convert-ToQuotedProcessArgument {
  param([string]$Value)
  if ($Value -notmatch '[\s"]') { return $Value }
  return '"' + $Value.Replace('"','\"') + '"'
}

function Read-NewStageLog {
  param([string]$Path, [int64]$Offset, [bool]$AsError)
  if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) {
    return [pscustomobject]@{ Offset = $Offset; BytesRead = 0 }
  }
  $stream = [System.IO.File]::Open($Path, [System.IO.FileMode]::Open, [System.IO.FileAccess]::Read, [System.IO.FileShare]::ReadWrite)
  try {
    if ($Offset -gt $stream.Length) { $Offset = 0 }
    [void]$stream.Seek($Offset, [System.IO.SeekOrigin]::Begin)
    $reader = [System.IO.StreamReader]::new($stream, [System.Text.UTF8Encoding]::new($false), $true, 4096, $true)
    try {
      $text = $reader.ReadToEnd()
    } finally {
      $reader.Dispose()
    }
    $newOffset = $stream.Position
  } finally {
    $stream.Dispose()
  }
  if ($text.Length -gt 0) {
    foreach ($line in @($text -split "`r?`n")) {
      if ($line.Length -eq 0) { continue }
      if ($AsError) { [Console]::Error.WriteLine($line) } else { [Console]::Out.WriteLine($line) }
    }
  }
  return [pscustomobject]@{ Offset = [int64]$newOffset; BytesRead = [int64]($newOffset - $Offset) }
}

function Stop-StageProcessTree {
  param([int]$ProcessId)
  if ($env:OS -eq 'Windows_NT') {
    $taskkill = Get-Command taskkill.exe -ErrorAction SilentlyContinue
    if ($taskkill) { & $taskkill.Source /PID $ProcessId /T /F 2>$null | Out-Null }
  }
  Stop-Process -Id $ProcessId -Force -ErrorAction SilentlyContinue
}

function Invoke-Python {
  param([string[]]$Arguments)
  if (-not $Arguments -or $Arguments.Count -lt 1) { throw 'PYTHON_STAGE_ARGUMENTS_MISSING' }

  $stageName = [System.IO.Path]::GetFileName([string]$Arguments[0])
  if ($Arguments -contains '--self-test') { $stageName = "$stageName`:self-test" }

  $configuredMax = 1650
  if ($env:AAYS_HD1_PYTHON_STAGE_MAX_SECONDS) {
    $parsedMax = 0
    if (-not [int]::TryParse($env:AAYS_HD1_PYTHON_STAGE_MAX_SECONDS, [ref]$parsedMax)) {
      throw 'PYTHON_STAGE_MAX_SECONDS_INVALID'
    }
    if ($parsedMax -lt 300 -or $parsedMax -gt 1800) { throw 'PYTHON_STAGE_MAX_SECONDS_OUT_OF_RANGE' }
    $configuredMax = $parsedMax
  }

  $stageRoot = Join-Path ([System.IO.Path]::GetTempPath()) 'aays_height_difference_1_python_stage'
  New-Item -ItemType Directory -Path $stageRoot -Force | Out-Null
  $token = [Guid]::NewGuid().ToString('N')
  $stdoutPath = Join-Path $stageRoot "$token.stdout.log"
  $stderrPath = Join-Path $stageRoot "$token.stderr.log"

  $childArgs = @()
  if ($python.Name -eq 'py.exe' -or $python.Name -eq 'py') { $childArgs += '-3' }
  $childArgs += @($Arguments)
  $argumentString = (@($childArgs | ForEach-Object { Convert-ToQuotedProcessArgument -Value ([string]$_) }) -join ' ')

  $process = $null
  $stdoutOffset = 0L
  $stderrOffset = 0L
  $stopwatch = [System.Diagnostics.Stopwatch]::StartNew()
  $nextHeartbeat = 30.0
  try {
    $process = Start-Process -FilePath $python.Source -ArgumentList $argumentString -NoNewWindow -PassThru -RedirectStandardOutput $stdoutPath -RedirectStandardError $stderrPath
    Write-Output "PYTHON_STAGE_STARTED stage=$stageName pid=$($process.Id) max_seconds=$configuredMax"

    while (-not $process.HasExited) {
      Start-Sleep -Seconds 5
      $process.Refresh()

      $stdoutRead = Read-NewStageLog -Path $stdoutPath -Offset $stdoutOffset -AsError $false
      $stdoutOffset = [int64]$stdoutRead.Offset
      $stderrRead = Read-NewStageLog -Path $stderrPath -Offset $stderrOffset -AsError $true
      $stderrOffset = [int64]$stderrRead.Offset

      $elapsed = $stopwatch.Elapsed.TotalSeconds
      if ($elapsed -ge $configuredMax) {
        Stop-StageProcessTree -ProcessId $process.Id
        Write-Output "PYTHON_STAGE_TERMINATED stage=$stageName reason=STAGE_TIMEOUT elapsed_seconds=$([int]$elapsed)"
        Write-Output 'FINAL_READY=false'
        return 124
      }
      if ($elapsed -ge $nextHeartbeat) {
        Write-Output ("PYTHON_STAGE_HEARTBEAT stage={0} elapsed_seconds={1} stdout_offset={2} stderr_offset={3}" -f $stageName,[int]$elapsed,$stdoutOffset,$stderrOffset)
        $nextHeartbeat += 30.0
      }
    }

    $process.WaitForExit()
    $stdoutRead = Read-NewStageLog -Path $stdoutPath -Offset $stdoutOffset -AsError $false
    $stdoutOffset = [int64]$stdoutRead.Offset
    $stderrRead = Read-NewStageLog -Path $stderrPath -Offset $stderrOffset -AsError $true
    $stderrOffset = [int64]$stderrRead.Offset
    Write-Output "PYTHON_STAGE_COMPLETED stage=$stageName elapsed_seconds=$([int]$stopwatch.Elapsed.TotalSeconds) exit_code=$($process.ExitCode)"
    return [int]$process.ExitCode
  } finally {
    if ($process -and -not $process.HasExited) { Stop-StageProcessTree -ProcessId $process.Id }
    Remove-Item -LiteralPath $stdoutPath,$stderrPath -Force -ErrorAction SilentlyContinue
  }
}
'''


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def atomic_write(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=path.name + ".", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_name, path)
    finally:
        try:
            os.unlink(temp_name)
        except FileNotFoundError:
            pass


def inject(text: str) -> str:
    count = text.count(OLD_INVOKE_PYTHON)
    if count != 1:
        raise RuntimeError(f"INVOKE_PYTHON_MATCH_COUNT_INVALID:{count}")
    if PATCH_LABEL in text or "PYTHON_STAGE_HEARTBEAT" in text:
        raise RuntimeError("PYTHON_STAGE_WATCHDOG_ALREADY_PRESENT")
    return text.replace(OLD_INVOKE_PYTHON, NEW_INVOKE_PYTHON, 1)


def self_test() -> dict[str, Any]:
    fixture = "prefix\n" + OLD_INVOKE_PYTHON + "\nsuffix\n"
    patched = inject(fixture)
    checks = {
        "slot_isolated": SLOT_ID == "height_difference_1",
        "version_present": SCRIPT_VERSION == "1.0-carrier-python-stage-watchdog-injector",
        "old_block_removed": OLD_INVOKE_PYTHON not in patched,
        "start_process_present": "Start-Process -FilePath $python.Source" in patched,
        "realtime_stdout_present": "Read-NewStageLog -Path $stdoutPath" in patched,
        "realtime_stderr_present": "Read-NewStageLog -Path $stderrPath" in patched,
        "independent_offsets_present": "$stdoutOffset = 0L" in patched and "$stderrOffset = 0L" in patched,
        "heartbeat_present": "PYTHON_STAGE_HEARTBEAT" in patched and "30.0" in patched,
        "stage_timeout_present": "PYTHON_STAGE_TERMINATED" in patched and "return 124" in patched,
        "process_tree_cleanup_present": "Stop-StageProcessTree" in patched,
        "bounded_override_present": "PYTHON_STAGE_MAX_SECONDS_OUT_OF_RANGE" in patched,
        "duplicate_source_rejected": False,
    }
    try:
        inject(fixture + OLD_INVOKE_PYTHON)
    except RuntimeError as exc:
        checks["duplicate_source_rejected"] = str(exc).startswith("INVOKE_PYTHON_MATCH_COUNT_INVALID:")
    if not all(checks.values()):
        raise RuntimeError("SELF_TEST_FAILED:" + json.dumps(checks, sort_keys=True))
    return {
        "slot_id": SLOT_ID,
        "script_version": SCRIPT_VERSION,
        "state": "PASS",
        "checks": len(checks),
        "check_results": checks,
        "runtime_patch_count": 1,
        "runtime_patch_labels": [PATCH_LABEL],
        "stage_max_seconds": STAGE_MAX_SECONDS,
        "stage_heartbeat_seconds": STAGE_HEARTBEAT_SECONDS,
        "stage_poll_seconds": STAGE_POLL_SECONDS,
        "timeout_exit_code": 124,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--carrier", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--receipt", type=Path)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()

    if args.self_test:
        print(json.dumps(self_test(), sort_keys=True))
        return 0
    if args.carrier is None or args.output is None or args.receipt is None:
        raise SystemExit("--carrier, --output and --receipt are required")

    source_bytes = args.carrier.read_bytes()
    source_text = source_bytes.decode("utf-8").replace("\r\n", "\n")
    output_text = inject(source_text)
    output_bytes = output_text.encode("utf-8")
    atomic_write(args.output, output_bytes)

    receipt = {
        "schema_version": 1,
        "slot_id": SLOT_ID,
        "script_version": SCRIPT_VERSION,
        "state": "COMPLETED_PYTHON_STAGE_WATCHDOG_INJECTED",
        "runtime_patch_count": 1,
        "runtime_patch_labels": [PATCH_LABEL],
        "source_path": str(args.carrier.resolve()),
        "source_bytes": len(source_bytes),
        "source_sha256": sha256_bytes(source_bytes),
        "output_path": str(args.output.resolve()),
        "output_bytes": len(output_bytes),
        "output_sha256": sha256_bytes(output_bytes),
        "stage_max_seconds": STAGE_MAX_SECONDS,
        "stage_heartbeat_seconds": STAGE_HEARTBEAT_SECONDS,
        "stage_poll_seconds": STAGE_POLL_SECONDS,
        "timeout_exit_code": 124,
        "realtime_stdout_stderr": True,
        "independent_output_offsets": True,
        "process_tree_cleanup": True,
        "fake_data": False,
        "final_ready": False,
    }
    atomic_write(args.receipt, (json.dumps(receipt, indent=2, sort_keys=True) + "\n").encode("utf-8"))
    print(json.dumps(receipt, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
