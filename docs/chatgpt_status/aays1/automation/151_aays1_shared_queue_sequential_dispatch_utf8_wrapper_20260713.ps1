$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$repoRoot = if ($env:AAYS_REPO_ROOT) { $env:AAYS_REPO_ROOT } else { (& git rev-parse --show-toplevel 2>$null).Trim() }
$sourceRelative = 'docs/chatgpt_status/aays1/automation/151_aays1_shared_queue_sequential_dispatch_20260711.ps1'
$sourcePath = Join-Path $repoRoot $sourceRelative
if (-not (Test-Path -LiteralPath $sourcePath)) { throw "Dispatcher missing: $sourceRelative" }

$text = Get-Content -LiteralPath $sourcePath -Raw -Encoding UTF8
# Windows PowerShell 5.1 requires a BOM for reliable non-ASCII parsing. Keep the
# generated child scripts ASCII-safe as an additional guard.
$text = $text.Replace('£','GBP')
$text = $text.Replace('[System.Text.UTF8Encoding]::new($false))','[System.Text.UTF8Encoding]::new($true))')

$tempPath = Join-Path ([System.IO.Path]::GetTempPath()) ("aays_151_utf8_{0}_{1}.ps1" -f $PID,[guid]::NewGuid().ToString('N'))
try {
  [System.IO.File]::WriteAllText($tempPath,$text,[System.Text.UTF8Encoding]::new($true))
  & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $tempPath
  $exitCode = $LASTEXITCODE
  if ($null -eq $exitCode) { $exitCode = 0 }
  exit $exitCode
} finally {
  if (Test-Path -LiteralPath $tempPath) { Remove-Item -LiteralPath $tempPath -Force -ErrorAction SilentlyContinue }
}
