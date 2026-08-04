@echo off
setlocal
set "AAYS_CANONICAL_ROOT=%~dp0"
set "AAYS_CMD_FILE=%~f0"
set "AAYS_BOOTSTRAP_FILE=%TEMP%\aays_contract9_%RANDOM%_%RANDOM%.ps1"
powershell -NoProfile -ExecutionPolicy Bypass -Command "$s=[IO.File]::ReadAllText($env:AAYS_CMD_FILE);$m='# AAYS_'+'POWERSHELL_BOOTSTRAP';$i=$s.IndexOf($m);if($i -lt 0){exit 97};[IO.File]::WriteAllText($env:AAYS_BOOTSTRAP_FILE,$s.Substring($i+$m.Length).TrimStart([char]13,[char]10),[Text.UTF8Encoding]::new($false));& $env:AAYS_BOOTSTRAP_FILE;exit $LASTEXITCODE"
set "AAYS_EXIT_CODE=%ERRORLEVEL%"
del /q "%AAYS_BOOTSTRAP_FILE%" >nul 2>&1
endlocal & exit /b %AAYS_EXIT_CODE%
# AAYS_POWERSHELL_BOOTSTRAP
$ErrorActionPreference='Stop'
$root=[IO.Path]::GetFullPath([string]$env:AAYS_CANONICAL_ROOT).TrimEnd('\')
$launcher=[IO.Path]::GetFullPath([string]$env:AAYS_CMD_FILE)
$branch='codex/aays-single-runner-v5-20260706'
$pinnedV7Blob='32251f0e5a824f885bd2a697939d5e4ebc9bfbbe'
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
if([string]::IsNullOrWhiteSpace($root)-or $root.StartsWith('C:\',[StringComparison]::OrdinalIgnoreCase)){
  throw "BLOCKED_CANONICAL_ROOT_INVALID=$root"
}
if(-not(Test-Path -LiteralPath (Join-Path $root '.git'))){
  throw "BLOCKED_CANONICAL_REPO_GIT_MISSING=$root"
}
if((G @('branch','--show-current')).Trim()-ne $branch){
  throw 'BLOCKED_CANONICAL_BRANCH_MISMATCH'
}
# Preserve tracked and untracked runtime changes. The pinned v7/core remote guard
# owns lock/process identity classification and fails closed there.
$trackedDirtyBefore=(G @('status','--porcelain','--untracked-files=no'))
$shallowBefore=(G @('rev-parse','--is-shallow-repository')).Trim().ToLowerInvariant()
$refspec="+refs/heads/$branch`:refs/remotes/origin/$branch"
$fetchArgs=@('fetch','--no-tags')
if($shallowBefore-eq'true'){$fetchArgs+='--unshallow'}
$fetchArgs+=@('origin',$refspec)
[void](G $fetchArgs)
$trackedDirtyAfter=(G @('status','--porcelain','--untracked-files=no'))
if($trackedDirtyAfter-ne $trackedDirtyBefore){
  throw 'BLOCKED_FETCH_CHANGED_TRACKED_WORKTREE_STATE'
}
$pinnedProbe=GR @('cat-file','-e',("$pinnedV7Blob`^{blob}"))
if($pinnedProbe.code-ne 0){
  throw "BLOCKED_PINNED_CONTRACT7_BLOB_UNAVAILABLE_AFTER_FETCH=$pinnedV7Blob"
}
$v7=(G @('cat-file','blob',$pinnedV7Blob))
$marker='# AAYS_'+'POWERSHELL_BOOTSTRAP'
$mi=$v7.IndexOf($marker)
if($mi-lt 0){throw 'BLOCKED_PINNED_CONTRACT7_MARKER_MISSING'}
$v7Ps=$v7.Substring($mi+$marker.Length).TrimStart([char]13,[char]10)
$tempV7=Join-Path $env:TEMP ("aays_contract7_core_from_v9_{0}_{1}.ps1"-f $PID,[guid]::NewGuid().ToString('N'))
try{
  [IO.File]::WriteAllText($tempV7,$v7Ps,[Text.UTF8Encoding]::new($false))
  $env:AAYS_CANONICAL_ROOT=$root+'\'
  $env:AAYS_CMD_FILE=$launcher
  & powershell -NoProfile -ExecutionPolicy Bypass -File $tempV7
  exit $LASTEXITCODE
}finally{
  Remove-Item $tempV7 -Force -ErrorAction SilentlyContinue
}
