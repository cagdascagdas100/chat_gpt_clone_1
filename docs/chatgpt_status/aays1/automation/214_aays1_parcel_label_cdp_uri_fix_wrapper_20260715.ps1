param()
$ErrorActionPreference = 'Stop'
$repoRoot = if ($env:AAYS_REPO_ROOT) { $env:AAYS_REPO_ROOT } else { (& git rev-parse --show-toplevel 2>$null).Trim() }
if ([string]::IsNullOrWhiteSpace($repoRoot)) { throw 'AAYS_REPO_ROOT_NOT_RESOLVED' }
$sourcePath = Join-Path $repoRoot 'docs\chatgpt_status\aays1\automation\214_aays1_parcel_label_4row_cdp_dom_proof_20260715.ps1'
if (-not (Test-Path -LiteralPath $sourcePath -PathType Leaf)) { throw "TASK_214_SOURCE_NOT_FOUND: $sourcePath" }
$text = Get-Content -LiteralPath $sourcePath -Raw -Encoding UTF8
$oldTarget = '$target = @($targets | Where-Object { $_.type -eq ''page'' -and $_.webSocketDebuggerUrl } | Select-Object -First 1)'
$newTarget = '$target = $targets | Where-Object { $_.type -eq ''page'' -and $_.webSocketDebuggerUrl } | Select-Object -First 1'
$oldConnect = '$socket.ConnectAsync([Uri]$target.webSocketDebuggerUrl,[Threading.CancellationToken]::None).GetAwaiter().GetResult()'
$newConnect = '$socket.ConnectAsync([Uri]([string]$target.webSocketDebuggerUrl),[Threading.CancellationToken]::None).GetAwaiter().GetResult()'
if (-not $text.Contains($oldTarget)) { throw 'TASK_214_TARGET_PATCH_PATTERN_NOT_FOUND' }
if (-not $text.Contains($oldConnect)) { throw 'TASK_214_CONNECT_PATCH_PATTERN_NOT_FOUND' }
$patched = $text.Replace($oldTarget,$newTarget).Replace($oldConnect,$newConnect)
$tempPath = Join-Path ([IO.Path]::GetTempPath()) ('aays_task214_uri_fix_' + [guid]::NewGuid().ToString('N') + '.ps1')
try {
  [IO.File]::WriteAllText($tempPath,$patched,[Text.UTF8Encoding]::new($false))
  $tokens=$null;$errors=$null
  [Management.Automation.Language.Parser]::ParseFile($tempPath,[ref]$tokens,[ref]$errors) | Out-Null
  if ($errors.Count) { throw ('TASK_214_PATCHED_SCRIPT_PARSE_FAILED: ' + $errors[0].Message) }
  & powershell -NoProfile -ExecutionPolicy Bypass -File $tempPath
  exit $LASTEXITCODE
} finally {
  Remove-Item -LiteralPath $tempPath -Force -ErrorAction SilentlyContinue
}
