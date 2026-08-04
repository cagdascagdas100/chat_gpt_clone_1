@echo off
setlocal
set "AAYS_CANONICAL_ROOT=%~dp0"
set "AAYS_CMD_FILE=%~f0"
set "AAYS_BOOTSTRAP_FILE=%TEMP%\aays_contract11_%RANDOM%_%RANDOM%.ps1"
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
$launcherPath='START_AAYS_CANONICAL_RUNNER_AND_PANEL.cmd'
$pinnedV7Commit='4bfd99342f38b1bba1dd447bbd3abba47b4380d9'
$pinnedV7Blob='32251f0e5a824f885bd2a697939d5e4ebc9bfbbe'
$pinnedV5Commit='05696046ef99391c70826fbe4dd9a43ea293a116'
$pinnedV5Blob='3319ab4f7d61705bc4a793d04e29508e28da0456'
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
function Ensure-PinnedLauncher([string]$commit,[string]$blob,[string]$label){
  if((GR @('cat-file','-e',("$commit`^{commit}"))).code-ne 0-or (GR @('cat-file','-e',("$blob`^{blob}"))).code-ne 0){
    $f=GR @('fetch','--no-tags','--depth=1','origin',$commit)
    if($f.code-ne 0){throw "BLOCKED_${label}_TARGETED_FETCH_FAILED=$($f.text)"}
  }
  if((GR @('cat-file','-e',("$commit`^{commit}"))).code-ne 0){throw "BLOCKED_${label}_COMMIT_UNAVAILABLE=$commit"}
  if((GR @('cat-file','-e',("$blob`^{blob}"))).code-ne 0){throw "BLOCKED_${label}_BLOB_UNAVAILABLE=$blob"}
  $treeBlob=(G @('rev-parse',("$commit`:$launcherPath"))).Trim()
  if($treeBlob-ne $blob){throw "BLOCKED_${label}_COMMIT_BLOB_BINDING_MISMATCH=$treeBlob/$blob"}
}
if([string]::IsNullOrWhiteSpace($root)-or $root.StartsWith('C:\',[StringComparison]::OrdinalIgnoreCase)){throw "BLOCKED_CANONICAL_ROOT_INVALID=$root"}
if(-not(Test-Path -LiteralPath (Join-Path $root '.git'))){throw "BLOCKED_CANONICAL_REPO_GIT_MISSING=$root"}
if((G @('branch','--show-current')).Trim()-ne $branch){throw 'BLOCKED_CANONICAL_BRANCH_MISMATCH'}
$trackedBefore=(G @('status','--porcelain','--untracked-files=no'))
$refspec="+refs/heads/$branch`:refs/remotes/origin/$branch"
$currentFetch=GR @('fetch','--no-tags','--depth=1','origin',$refspec)
if($currentFetch.code-ne 0){throw "BLOCKED_CURRENT_BRANCH_FETCH_FAILED=$($currentFetch.text)"}
Ensure-PinnedLauncher $pinnedV7Commit $pinnedV7Blob 'PINNED_CONTRACT7'
Ensure-PinnedLauncher $pinnedV5Commit $pinnedV5Blob 'PINNED_CONTRACT5'
$trackedAfter=(G @('status','--porcelain','--untracked-files=no'))
if($trackedAfter-ne $trackedBefore){throw 'BLOCKED_TARGETED_FETCH_CHANGED_TRACKED_WORKTREE_STATE'}

$v5=Normalize-Lf (G @('cat-file','blob',$pinnedV5Blob))
$oldDirty=Normalize-Lf @'
$trackedStatus = Invoke-AaysGit @('status','--porcelain','--untracked-files=no')
if (-not [string]::IsNullOrWhiteSpace($trackedStatus)) {
  throw ("BLOCKED_CANONICAL_TRACKED_WORKTREE_DIRTY: " + $trackedStatus)
}
'@
$newDirty=Normalize-Lf @'
$trackedStatusBeforeCoreFetch = Invoke-AaysGit @('status','--porcelain','--untracked-files=no')
'@
$v5=Replace-Exact $v5 $oldDirty $newDirty 'V5_GLOBAL_TRACKED_DIRTY_REJECTION'
$oldFetch=Normalize-Lf @'
$shallow = (Invoke-AaysGit @('rev-parse','--is-shallow-repository')).Trim().ToLowerInvariant()
$refspec = "+refs/heads/$branch`:refs/remotes/origin/$branch"
$fetchArgs = @('fetch','--no-tags')
if ($shallow -eq 'true') { $fetchArgs += '--unshallow' }
$fetchArgs += @('origin',$refspec)
[void](Invoke-AaysGit $fetchArgs)
'@
$newFetch=Normalize-Lf @'
$shallow = (Invoke-AaysGit @('rev-parse','--is-shallow-repository')).Trim().ToLowerInvariant()
$refspec = "+refs/heads/$branch`:refs/remotes/origin/$branch"
$fetchArgs = @('fetch','--no-tags','origin',$refspec)
[void](Invoke-AaysGit $fetchArgs)
$trackedStatusAfterCoreFetch = Invoke-AaysGit @('status','--porcelain','--untracked-files=no')
if ($trackedStatusAfterCoreFetch -ne $trackedStatusBeforeCoreFetch) {
  throw 'BLOCKED_CORE_FETCH_CHANGED_TRACKED_WORKTREE_STATE'
}
'@
$v5=Replace-Exact $v5 $oldFetch $newFetch 'V5_FULL_UNSHALLOW_FETCH'
$oldMerge=Normalize-Lf @'
  if ($localHead -ne $remoteHead) {
    if ($syncSafeStates -contains $guardState) {
      [void](Invoke-AaysGit @('merge','--ff-only',$remoteRef))
      $fastForwardApplied = $true
    } elseif ($liveStates -contains $guardState) {
'@
$newMerge=Normalize-Lf @'
  if ($localHead -ne $remoteHead) {
    if ($syncSafeStates -contains $guardState) {
      $ancestor = Invoke-AaysGitAtResult $root @('merge-base','--is-ancestor',$localHead,$remoteRef)
      if ($ancestor.exit_code -ne 0 -and $shallow -eq 'true') {
        foreach ($deepenBy in @(64,256,1024,4096)) {
          [void](Invoke-AaysGit @('fetch','--no-tags',("--deepen=$deepenBy"),'origin',$refspec))
          $trackedStatusAfterDeepen = Invoke-AaysGit @('status','--porcelain','--untracked-files=no')
          if ($trackedStatusAfterDeepen -ne $trackedStatusBeforeCoreFetch) {
            throw "BLOCKED_BOUNDED_DEEPEN_CHANGED_TRACKED_WORKTREE_STATE=$deepenBy"
          }
          $remoteHead = (Invoke-AaysGit @('rev-parse',$remoteRef)).Trim()
          $ancestor = Invoke-AaysGitAtResult $root @('merge-base','--is-ancestor',$localHead,$remoteRef)
          if ($ancestor.exit_code -eq 0) { break }
        }
      }
      if ($ancestor.exit_code -ne 0) {
        throw "BLOCKED_LOCAL_HEAD_ANCESTRY_UNPROVEN_AFTER_BOUNDED_DEEPEN_LOCAL=$localHead`_REMOTE=$remoteHead"
      }
      [void](Invoke-AaysGit @('merge','--ff-only',$remoteRef))
      $fastForwardApplied = $true
    } elseif ($liveStates -contains $guardState) {
'@
$v5=Replace-Exact $v5 $oldMerge $newMerge 'V5_FF_ONLY_ANCESTRY_GATE'
if($v5.Contains('--unshallow')){throw 'BLOCKED_PATCHED_V5_STILL_CONTAINS_UNSHALLOW'}
$tempV5=Join-Path $env:TEMP ("aays_contract5_patched_from_v11_{0}_{1}.cmd"-f $PID,[guid]::NewGuid().ToString('N'))
$tempV7=Join-Path $env:TEMP ("aays_contract7_patched_from_v11_{0}_{1}.ps1"-f $PID,[guid]::NewGuid().ToString('N'))
try{
  [IO.File]::WriteAllText($tempV5,$v5,[Text.UTF8Encoding]::new($false))
  $v7=Normalize-Lf (G @('cat-file','blob',$pinnedV7Blob))
  $marker='# AAYS_'+'POWERSHELL_BOOTSTRAP'
  $mi=$v7.IndexOf($marker)
  if($mi-lt 0){throw 'BLOCKED_PINNED_CONTRACT7_MARKER_MISSING'}
  $v7Ps=$v7.Substring($mi+$marker.Length).TrimStart([char]13,[char]10)
  $oldCore="`$core=(G @('cat-file','blob',`$coreBlob))"
  $newCore="`$core=[IO.File]::ReadAllText([string]`$env:AAYS_PATCHED_CONTRACT5_FILE,[Text.Encoding]::UTF8)"
  $v7Ps=Replace-Exact $v7Ps $oldCore $newCore 'V7_PINNED_CORE_LOAD'
  [IO.File]::WriteAllText($tempV7,$v7Ps,[Text.UTF8Encoding]::new($false))
  $env:AAYS_PATCHED_CONTRACT5_FILE=$tempV5
  $env:AAYS_CANONICAL_ROOT=$root+'\'
  $env:AAYS_CMD_FILE=$launcher
  & powershell -NoProfile -ExecutionPolicy Bypass -File $tempV7
  exit $LASTEXITCODE
}finally{
  Remove-Item Env:AAYS_PATCHED_CONTRACT5_FILE -ErrorAction SilentlyContinue
  Remove-Item $tempV5,$tempV7 -Force -ErrorAction SilentlyContinue
}
