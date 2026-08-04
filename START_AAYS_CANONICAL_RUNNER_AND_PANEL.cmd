@echo off
setlocal
set "AAYS_CANONICAL_ROOT=%~dp0"
set "AAYS_CMD_FILE=%~f0"
set "AAYS_BOOTSTRAP_FILE=%TEMP%\aays_contract12_%RANDOM%_%RANDOM%.ps1"
powershell -NoProfile -ExecutionPolicy Bypass -Command "$s=[IO.File]::ReadAllText($env:AAYS_CMD_FILE);$m='# AAYS_'+'POWERSHELL_BOOTSTRAP';$i=$s.IndexOf($m);if($i -lt 0){exit 97};[IO.File]::WriteAllText($env:AAYS_BOOTSTRAP_FILE,$s.Substring($i+$m.Length).TrimStart([char]13,[char]10),[Text.UTF8Encoding]::new($false));& $env:AAYS_BOOTSTRAP_FILE;exit $LASTEXITCODE"
set "AAYS_EXIT_CODE=%ERRORLEVEL%"
del /q "%AAYS_BOOTSTRAP_FILE%" >nul 2>&1
endlocal & exit /b %AAYS_EXIT_CODE%
# AAYS_POWERSHELL_BOOTSTRAP
$ErrorActionPreference='Stop'
$root=[IO.Path]::GetFullPath([string]$env:AAYS_CANONICAL_ROOT).TrimEnd('\')
$launcher=[IO.Path]::GetFullPath([string]$env:AAYS_CMD_FILE)
$branch='codex/aays-single-runner-v5-20260706'
$pinnedV11Commit='0944bc04e60ffaff23939b3dc04bcec8d81a72e8'
$pinnedV11Blob='a60c586714d7c08714e640ea787a7b4e503f85a5'
$launcherPath='START_AAYS_CANONICAL_RUNNER_AND_PANEL.cmd'
function G([string[]]$a){
  $o=& git -c "safe.directory=$root" -C $root @a 2>&1
  $c=$LASTEXITCODE
  $t=($o|Out-String).TrimEnd()
  if($c-ne 0){throw "GIT_FAILED[$($a-join ' ')]: $t"}
  $t
}
function GR([string[]]$a){
  $o=& git -c "safe.directory=$root" -C $root @a 2>&1
  [pscustomobject]@{code=$LASTEXITCODE;text=(($o|Out-String).TrimEnd())}
}
function Normalize-Lf([string]$s){return ($s-replace "`r`n","`n")}
function Replace-Exact([string]$text,[string]$old,[string]$new,[string]$label){
  $first=$text.IndexOf($old,[StringComparison]::Ordinal)
  if($first-lt 0){throw "BLOCKED_PATCH_TARGET_MISSING=$label"}
  $second=$text.IndexOf($old,$first+$old.Length,[StringComparison]::Ordinal)
  if($second-ge 0){throw "BLOCKED_PATCH_TARGET_NOT_UNIQUE=$label"}
  return $text.Substring(0,$first)+$new+$text.Substring($first+$old.Length)
}
if([string]::IsNullOrWhiteSpace($root)-or $root.StartsWith('C:\',[StringComparison]::OrdinalIgnoreCase)){throw "BLOCKED_CANONICAL_ROOT_INVALID=$root"}
if(-not(Test-Path -LiteralPath (Join-Path $root '.git'))){throw "BLOCKED_CANONICAL_REPO_GIT_MISSING=$root"}
if((G @('branch','--show-current')).Trim()-ne $branch){throw 'BLOCKED_CANONICAL_BRANCH_MISMATCH'}
$trackedBefore=(G @('status','--porcelain','--untracked-files=no'))
$refspec="+refs/heads/$branch`:refs/remotes/origin/$branch"
$currentFetch=GR @('fetch','--no-tags','--depth=1','origin',$refspec)
if($currentFetch.code-ne 0){throw "BLOCKED_CURRENT_BRANCH_FETCH_FAILED=$($currentFetch.text)"}
if((GR @('cat-file','-e',("$pinnedV11Commit`^{commit}"))).code-ne 0-or (GR @('cat-file','-e',("$pinnedV11Blob`^{blob}"))).code-ne 0){
  $pinnedFetch=GR @('fetch','--no-tags','--depth=1','origin',$pinnedV11Commit)
  if($pinnedFetch.code-ne 0){throw "BLOCKED_PINNED_CONTRACT11_TARGETED_FETCH_FAILED=$($pinnedFetch.text)"}
}
if((GR @('cat-file','-e',("$pinnedV11Commit`^{commit}"))).code-ne 0){throw "BLOCKED_PINNED_CONTRACT11_COMMIT_UNAVAILABLE=$pinnedV11Commit"}
if((GR @('cat-file','-e',("$pinnedV11Blob`^{blob}"))).code-ne 0){throw "BLOCKED_PINNED_CONTRACT11_BLOB_UNAVAILABLE=$pinnedV11Blob"}
$treeBlob=(G @('rev-parse',("$pinnedV11Commit`:$launcherPath"))).Trim()
if($treeBlob-ne $pinnedV11Blob){throw "BLOCKED_PINNED_CONTRACT11_COMMIT_BLOB_BINDING_MISMATCH=$treeBlob/$pinnedV11Blob"}
$trackedAfter=(G @('status','--porcelain','--untracked-files=no'))
if($trackedAfter-ne $trackedBefore){throw 'BLOCKED_TARGETED_FETCH_CHANGED_TRACKED_WORKTREE_STATE'}
$v11=Normalize-Lf (G @('cat-file','blob',$pinnedV11Blob))
$oldBaseline=Normalize-Lf @'
      $ancestor = Invoke-AaysGitAtResult $root @('merge-base','--is-ancestor',$localHead,$remoteRef)
'@
$newBaseline=Normalize-Lf @'
      $trackedStatusAfterGuard = Invoke-AaysGit @('status','--porcelain','--untracked-files=no')
      $ancestor = Invoke-AaysGitAtResult $root @('merge-base','--is-ancestor',$localHead,$remoteRef)
'@
$v11=Replace-Exact $v11 $oldBaseline $newBaseline 'V11_POST_GUARD_BASELINE_CAPTURE'
$oldCompare=Normalize-Lf @'
          if ($trackedStatusAfterDeepen -ne $trackedStatusBeforeCoreFetch) {
'@
$newCompare=Normalize-Lf @'
          if ($trackedStatusAfterDeepen -ne $trackedStatusAfterGuard) {
'@
$v11=Replace-Exact $v11 $oldCompare $newCompare 'V11_BOUNDED_DEEPEN_BASELINE'
if(-not $v11.Contains('$trackedStatusAfterGuard = Invoke-AaysGit')){throw 'BLOCKED_PATCHED_V11_POST_GUARD_BASELINE_MISSING'}
if($v11.Contains('$trackedStatusAfterDeepen -ne $trackedStatusBeforeCoreFetch')){throw 'BLOCKED_PATCHED_V11_STALE_BASELINE_REMAINS'}
$marker='# AAYS_'+'POWERSHELL_BOOTSTRAP'
$mi=$v11.IndexOf($marker)
if($mi-lt 0){throw 'BLOCKED_PINNED_CONTRACT11_MARKER_MISSING'}
$v11Ps=$v11.Substring($mi+$marker.Length).TrimStart([char]13,[char]10)
$tempV11=Join-Path $env:TEMP ("aays_contract11_patched_from_v12_{0}_{1}.ps1"-f $PID,[guid]::NewGuid().ToString('N'))
try{
  [IO.File]::WriteAllText($tempV11,$v11Ps,[Text.UTF8Encoding]::new($false))
  $env:AAYS_CANONICAL_ROOT=$root+'\'
  $env:AAYS_CMD_FILE=$launcher
  & powershell -NoProfile -ExecutionPolicy Bypass -File $tempV11
  exit $LASTEXITCODE
}finally{
  Remove-Item $tempV11 -Force -ErrorAction SilentlyContinue
}
