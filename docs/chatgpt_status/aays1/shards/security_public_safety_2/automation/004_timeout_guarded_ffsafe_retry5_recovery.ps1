[CmdletBinding()]
param([int]$TimeoutSeconds = 300)

$ErrorActionPreference = 'Stop'
$slotId = 'security_public_safety_2'
$taskId = 'security_public_safety_2_geometry_lsoa_police_sample_wave1_retry5_20260722'
$attemptId = 'attempt-005'
$repoRoot = 'F:\TerraYield_AAYS_Portable\runner_system\AAYS_WT\AAYS_RUNNER_HEALTHY_20260707'
$innerRel = 'docs\chatgpt_status\aays1\shards\security_public_safety_2\automation\003_ffsafe_sync_then_apply_retry5_recovery.ps1'
$innerBlob = '2a932991d13c0921c97433d0e57bb6a4b55eb972'
$outputRel = 'docs\chatgpt_status\aays1\shards\security_public_safety_2\runner_outputs\004_retry5_timeout_guard_latest.json'

function GitBlob([string]$Path) {
  if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) { return $null }
  $bytes=[IO.File]::ReadAllBytes($Path);$prefix=[Text.Encoding]::ASCII.GetBytes(('blob {0}' -f $bytes.Length)+[char]0)
  $sha=[Security.Cryptography.SHA1]::Create();try{[void]$sha.TransformBlock($prefix,0,$prefix.Length,$prefix,0);[void]$sha.TransformFinalBlock($bytes,0,$bytes.Length);return([BitConverter]::ToString($sha.Hash)).Replace('-','').ToLowerInvariant()}finally{$sha.Dispose()}
}
function Receipt([string]$Status,[int]$ExitCode,[bool]$TimedOut,[string]$Detail) {
  $path=Join-Path $repoRoot $outputRel;$parent=Split-Path -Parent $path;if(-not(Test-Path -LiteralPath $parent)){New-Item -ItemType Directory -Force -Path $parent|Out-Null}
  $o=[ordered]@{schema_version=1;slot_id=$slotId;task_id=$taskId;attempt_id=$attemptId;status=$Status;checked_at=[DateTimeOffset]::UtcNow.ToString('o');timeout_seconds=$TimeoutSeconds;timed_out=$TimedOut;inner_exit_code=$ExitCode;inner_path=$innerRel;inner_expected_blob=$innerBlob;same_attempt=$true;new_runner_created=$false;parallel_runner_started=$false;detail=$Detail;final_ready=$false;fake_data=$false}
  $tmp="$path.tmp.$PID";[IO.File]::WriteAllText($tmp,(($o|ConvertTo-Json -Depth 8)+"`n"),[Text.UTF8Encoding]::new($false));Move-Item -LiteralPath $tmp -Destination $path -Force
}

if(-not(Test-Path -LiteralPath $repoRoot -PathType Container)){throw"CANONICAL_F_REPO_ROOT_MISSING=$repoRoot"}
$inner=Join-Path $repoRoot $innerRel;$actual=GitBlob $inner
if($actual -ne $innerBlob){Receipt 'BLOCKED_LOCAL_003_BLOB_MISMATCH' -1 $false "expected=$innerBlob actual=$actual";exit 21}
$p=Start-Process -FilePath 'powershell.exe' -ArgumentList @('-NoProfile','-ExecutionPolicy','Bypass','-File',$inner) -WorkingDirectory $repoRoot -PassThru -WindowStyle Normal
if(-not $p.WaitForExit($TimeoutSeconds*1000)){
  try{Stop-Process -Id $p.Id -Force -ErrorAction SilentlyContinue}catch{}
  Receipt 'BLOCKED_RETRY5_RECOVERY_TIMEOUT' 124 $true "wrapper_pid=$($p.Id)"
  exit 124
}
$exit=$p.ExitCode
$status=if($exit -eq 0){'TIMEOUT_GUARDED_FFSAFE_RETRY5_RECOVERY_COMPLETED'}else{'BLOCKED_INNER_FFSAFE_RETRY5_RECOVERY_FAILED'}
Receipt $status $exit $false "wrapper_pid=$($p.Id)"
exit $exit
