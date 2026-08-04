@echo off
setlocal
set "AAYS_CANONICAL_ROOT=%~dp0"
set "AAYS_CMD_FILE=%~f0"
set "AAYS_BOOTSTRAP_FILE=%TEMP%\aays_contract10_%RANDOM%_%RANDOM%.ps1"
powershell -NoProfile -ExecutionPolicy Bypass -Command "$s=[IO.File]::ReadAllText($env:AAYS_CMD_FILE);$m='# AAYS_'+'POWERSHELL_BOOTSTRAP';$i=$s.IndexOf($m);if($i -lt 0){exit 97};[IO.File]::WriteAllText($env:AAYS_BOOTSTRAP_FILE,$s.Substring($i+$m.Length).TrimStart([char]13,[char]10),[Text.UTF8Encoding]::new($false));& $env:AAYS_BOOTSTRAP_FILE;exit $LASTEXITCODE"
set "AAYS_EXIT_CODE=%ERRORLEVEL%"
del /q "%AAYS_BOOTSTRAP_FILE%" >nul 2>&1
endlocal & exit /b %AAYS_EXIT_CODE%
# AAYS_POWERSHELL_BOOTSTRAP
$ErrorActionPreference='Stop'
$root=[IO.Path]::GetFullPath([string]$env:AAYS_CANONICAL_ROOT).TrimEnd('\')
$launcher=[IO.Path]::GetFullPath([string]$env:AAYS_CMD_FILE)
$branch='codex/aays-single-runner-v5-20260706'
$remoteRef="refs/remotes/origin/$branch"
$pinnedV7Commit='4bfd99342f38b1bba1dd447bbd3abba47b4380d9'
$pinnedV7Blob='32251f0e5a824f885bd2a697939d5e4ebc9bfbbe'
$pinnedV5Commit='05696046ef99391c70826fbe4dd9a43ea293a116'
$pinnedV5CoreBlob='3319ab4f7d61705bc4a793d04e29508e28da0456'
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
function Ensure-PinnedLauncherBlob([string]$commit,[string]$blob,[string]$label){
  $blobProbe=GR @('cat-file','-e',("$blob`^{blob}"))
  $commitProbe=GR @('cat-file','-e',("$commit`^{commit}"))
  if($blobProbe.code-ne 0-or $commitProbe.code-ne 0){
    $fetch=GR @('fetch','--no-tags','--depth=1','origin',$commit)
    if($fetch.code-ne 0){
      throw "BLOCKED_${label}_TARGETED_FETCH_FAILED=$($fetch.text)"
    }
  }
  if((GR @('cat-file','-e',("$commit`^{commit}"))).code-ne 0){
    throw "BLOCKED_${label}_COMMIT_UNAVAILABLE_AFTER_TARGETED_FETCH=$commit"
  }
  if((GR @('cat-file','-e',("$blob`^{blob}"))).code-ne 0){
    throw "BLOCKED_${label}_BLOB_UNAVAILABLE_AFTER_TARGETED_FETCH=$blob"
  }
  $treeBlob=(G @('rev-parse',("$commit`:$launcherPath"))).Trim()
  if($treeBlob-ne $blob){
    throw "BLOCKED_${label}_COMMIT_BLOB_BINDING_MISMATCH=$treeBlob/$blob"
  }
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
# Fetch only the current branch tip plus the two exact historical launcher commits.
# Never unshallow the full repository; preserve the tracked runtime state exactly.
$trackedDirtyBefore=(G @('status','--porcelain','--untracked-files=no'))
$refspec="+refs/heads/$branch`:refs/remotes/origin/$branch"
$currentFetch=GR @('fetch','--no-tags','--depth=1','origin',$refspec)
if($currentFetch.code-ne 0){
  throw "BLOCKED_CURRENT_BRANCH_FETCH_FAILED=$($currentFetch.text)"
}
Ensure-PinnedLauncherBlob $pinnedV7Commit $pinnedV7Blob 'PINNED_CONTRACT7'
Ensure-PinnedLauncherBlob $pinnedV5Commit $pinnedV5CoreBlob 'PINNED_CONTRACT5'
$trackedDirtyAfter=(G @('status','--porcelain','--untracked-files=no'))
if($trackedDirtyAfter-ne $trackedDirtyBefore){
  throw 'BLOCKED_TARGETED_FETCH_CHANGED_TRACKED_WORKTREE_STATE'
}
$v7=(G @('cat-file','blob',$pinnedV7Blob))
$marker='# AAYS_'+'POWERSHELL_BOOTSTRAP'
$mi=$v7.IndexOf($marker)
if($mi-lt 0){throw 'BLOCKED_PINNED_CONTRACT7_MARKER_MISSING'}
$v7Ps=$v7.Substring($mi+$marker.Length).TrimStart([char]13,[char]10)
$tempV7=Join-Path $env:TEMP ("aays_contract7_core_from_v10_{0}_{1}.ps1"-f $PID,[guid]::NewGuid().ToString('N'))
try{
  [IO.File]::WriteAllText($tempV7,$v7Ps,[Text.UTF8Encoding]::new($false))
  $env:AAYS_CANONICAL_ROOT=$root+'\'
  $env:AAYS_CMD_FILE=$launcher
  & powershell -NoProfile -ExecutionPolicy Bypass -File $tempV7
  exit $LASTEXITCODE
}finally{
  Remove-Item $tempV7 -Force -ErrorAction SilentlyContinue
}
