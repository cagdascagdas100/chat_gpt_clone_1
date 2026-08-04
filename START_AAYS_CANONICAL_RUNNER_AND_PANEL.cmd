@echo off
setlocal
set "AAYS_CANONICAL_ROOT=%~dp0"
set "AAYS_CMD_FILE=%~f0"
set "AAYS_BOOTSTRAP_FILE=%TEMP%\aays_contract7_%RANDOM%_%RANDOM%.ps1"
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
$coreBlob='3319ab4f7d61705bc4a793d04e29508e28da0456'
$bootstrapPath='docs/chatgpt_status/_shared/status/runner_bootstrap_latest.json'
$receiptPath='docs/chatgpt_status/_shared/status/runner_bootstrap_publish_receipt_v7_latest.json'
$guardBlob='a81f26c35742024bfc167397fa7712e872cd7026'
$starterBlob='9178c9abb80786d4288305785324345093893265'
function G([string[]]$a){$o=& git -c "safe.directory=$root" -C $root @a 2>&1;$c=$LASTEXITCODE;$t=($o|Out-String).TrimEnd();if($c-ne 0){throw "GIT_FAILED[$($a-join ' ')]: $t"};$t}
function GR([string]$r,[string[]]$a){$o=& git -c "safe.directory=$r" -C $r @a 2>&1;[pscustomobject]@{code=$LASTEXITCODE;text=(($o|Out-String).TrimEnd())}}
if([string]::IsNullOrWhiteSpace($root)-or $root.StartsWith('C:\',[StringComparison]::OrdinalIgnoreCase)){throw "BLOCKED_CANONICAL_ROOT_INVALID=$root"}
if(-not(Test-Path -LiteralPath (Join-Path $root '.git'))){throw "BLOCKED_CANONICAL_REPO_GIT_MISSING=$root"}
if((G @('branch','--show-current')).Trim()-ne $branch){throw 'BLOCKED_CANONICAL_BRANCH_MISMATCH'}
$outerExecutingBlob=(G @('hash-object','--',$launcher)).Trim()
if($outerExecutingBlob-notmatch'^[0-9a-f]{40}$'){throw "BLOCKED_OUTER_EXECUTING_BLOB_INVALID=$outerExecutingBlob"}
$core=(G @('cat-file','blob',$coreBlob))
$marker='# AAYS_'+'POWERSHELL_BOOTSTRAP'
$mi=$core.IndexOf($marker)
if($mi-lt 0){throw 'BLOCKED_PINNED_CORE_MARKER_MISSING'}
$corePs=$core.Substring($mi+$marker.Length).TrimStart([char]13,[char]10)
$tempCore=Join-Path $env:TEMP ("aays_core_v5_{0}_{1}.ps1"-f $PID,[guid]::NewGuid().ToString('N'))
try{
  [IO.File]::WriteAllText($tempCore,$corePs,[Text.UTF8Encoding]::new($false))
  $env:AAYS_CANONICAL_ROOT=$root+'\'
  $env:AAYS_CMD_FILE=$launcher
  & powershell -NoProfile -ExecutionPolicy Bypass -File $tempCore
  $coreExit=$LASTEXITCODE
  if($coreExit-ne 0){exit $coreExit}

  $refspec="+refs/heads/$branch`:refs/remotes/origin/$branch"
  [void](G @('fetch','--no-tags','origin',$refspec))
  $rootBlob=(G @('rev-parse',("$remoteRef`:START_AAYS_CANONICAL_RUNNER_AND_PANEL.cmd"))).Trim()
  $diskBlob=(G @('hash-object','--',$launcher)).Trim()
  if($rootBlob-notmatch'^[0-9a-f]{40}$'-or $diskBlob-notmatch'^[0-9a-f]{40}$'){throw 'BLOCKED_ROOT_BLOB_INVALID_AFTER_CORE'}
  if($rootBlob-ne $diskBlob){throw "BLOCKED_ROOT_BLOB_MISMATCH=$diskBlob/$rootBlob"}

  if($outerExecutingBlob-ne $rootBlob){
    # The pinned core re-executed the current launcher and propagated its exit code.
    # Do not let this stale outer wrapper publish an obsolete receipt afterwards.
    exit 0
  }

  $bootstrapBlob=(G @('rev-parse',("$remoteRef`:$bootstrapPath"))).Trim()
  $bootstrapCommit=(G @('log','-1','--format=%H',$remoteRef,'--',$bootstrapPath)).Trim()
  $bootstrapParent=(G @('rev-parse',("$bootstrapCommit^"))).Trim()
  $bs=(G @('show',("$remoteRef`:$bootstrapPath"))|ConvertFrom-Json)
  $bootstrapAttempt=[int]$bs.root_launcher_bootstrap_publish_attempt
  $bootstrapValid=
    ([int]$bs.root_launcher_contract_version-eq 5)-and
    ([bool]$bs.root_launcher_execution_source_verified)-and
    ([bool]$bs.root_launcher_heads_match)-and
    ([string]$bs.root_launcher_blob_sha-eq $rootBlob)-and
    ([string]$bs.root_launcher_execution_blob_sha_before_sync-eq $rootBlob)-and
    ([string]$bs.root_launcher_remote_blob_sha_after_sync-eq $rootBlob)-and
    ([string]$bs.root_launcher_remote_guard_blob_sha-eq $guardBlob)-and
    ([string]$bs.root_launcher_starter_blob_sha-eq $starterBlob)-and
    ([string]$bs.root_launcher_bootstrap_publish_parent-eq $bootstrapParent)-and
    ($bootstrapAttempt-ge 1)-and($bootstrapAttempt-le 5)-and
    ([string]$bs.root_launcher_bootstrap_publish_mode-eq 'ISOLATED_DETACHED_WORKTREE_BOUNDED_RETRY_REMOTE_READBACK')-and
    ([bool]$bs.root_launcher_bootstrap_remote_readback_required)-and
    ([bool]$bs.root_launcher_no_reset_hard)-and
    ([bool]$bs.root_launcher_direct_starter_handoff)-and
    ([bool]$bs.root_launcher_wrapper_reentry_avoided)
  if(-not $bootstrapValid){throw 'BLOCKED_CONTRACT5_BOOTSTRAP_INVALID'}

  $localHead=(G @('rev-parse','HEAD')).Trim()
  $remoteHead=(G @('rev-parse',$remoteRef)).Trim()
  if((GR $root @('merge-base','--is-ancestor',$localHead,$remoteRef)).code-ne 0){throw 'BLOCKED_LOCAL_HEAD_NOT_REMOTE_ANCESTOR'}
  if((GR $root @('merge-base','--is-ancestor',$bootstrapCommit,$remoteRef)).code-ne 0){throw 'BLOCKED_BOOTSTRAP_COMMIT_NOT_REMOTE_ANCESTOR'}

  $max=5
  $attempt=0
  $published=$false
  $receiptCommit=$null
  $receiptBlob=$null
  $receiptParent=$null
  $wt=Join-Path $env:TEMP ("aays_receipt_v7_{0}_{1}"-f $PID,[guid]::NewGuid().ToString('N'))
  try{
    while(-not $published-and $attempt-lt $max){
      $attempt++
      [void](G @('fetch','--no-tags','origin',$refspec))
      $receiptParent=(G @('rev-parse',$remoteRef)).Trim()
      $r=[ordered]@{
        schema_version=1
        contract_version=7
        published_at=(Get-Date).ToUniversalTime().ToString('o')
        branch=$branch
        receipt_path=$receiptPath
        root_launcher_blob_sha=$rootBlob
        outer_execution_blob_sha=$outerExecutingBlob
        pinned_contract5_core_blob_sha=$coreBlob
        successful_core_reexec_stale_outer_must_exit=$true
        bootstrap_path=$bootstrapPath
        bootstrap_blob_sha=$bootstrapBlob
        bootstrap_publish_commit_sha=$bootstrapCommit
        bootstrap_publish_parent_sha=$bootstrapParent
        bootstrap_publish_attempt=$bootstrapAttempt
        bootstrap_heads_scope='PRESTART_SYNC_ONLY'
        bootstrap_prepublish_heads_match=$true
        postpublish_head_relation='LOCAL_ANCESTOR_REMOTE_INCLUDES_BOOTSTRAP_COMMIT'
        canonical_local_head_observed=$localHead
        remote_head_observed_before_receipt=$receiptParent
        canonical_local_head_is_remote_ancestor=$true
        receipt_publish_attempt=$attempt
        receipt_publish_parent_sha=$receiptParent
        remote_guard_blob_sha=$guardBlob
        starter_blob_sha=$starterBlob
        no_reset_hard=$true
        no_force_push=$true
        final_ready=$false
        fake_data=$false
      }
      $payload=($r|ConvertTo-Json -Depth 10)+"`n"
      [void](GR $root @('worktree','prune'))
      if(Test-Path $wt){Remove-Item $wt -Recurse -Force -ErrorAction SilentlyContinue}
      $a=GR $root @('worktree','add','--detach',$wt,$receiptParent)
      if($a.code-ne 0){throw "BLOCKED_RECEIPT_WORKTREE_ADD: $($a.text)"}
      try{
        $p=Join-Path $wt ($receiptPath-replace'/','\')
        New-Item -ItemType Directory -Force -Path (Split-Path $p)|Out-Null
        [IO.File]::WriteAllText($p,$payload,[Text.UTF8Encoding]::new($false))
        $receiptBlob=(GR $wt @('hash-object','--',$p)).text.Trim()
        if($receiptBlob-notmatch'^[0-9a-f]{40}$'){throw "BLOCKED_RECEIPT_BLOB_INVALID=$receiptBlob"}
        $add=GR $wt @('add','--',$receiptPath)
        if($add.code-ne 0){throw "BLOCKED_RECEIPT_ADD: $($add.text)"}
        if((GR $wt @('diff','--cached','--name-only')).text.Trim()-ne $receiptPath){throw 'BLOCKED_RECEIPT_SCOPE'}
        $c=GR $wt @('-c','user.name=AAYS canonical launcher','-c','user.email=aays-launcher@local.invalid','commit','--only','-m','aays: publish bootstrap contract v7 receipt','--',$receiptPath)
        if($c.code-ne 0){throw "BLOCKED_RECEIPT_COMMIT: $($c.text)"}
        $receiptCommit=(GR $wt @('rev-parse','HEAD')).text.Trim()
        $push=GR $wt @('push','origin',("${receiptCommit}:refs/heads/$branch"))
        if($push.code-eq 0){$published=$true}
        elseif($push.text-match'(?i)(non-fast-forward|fetch first|rejected)'){$published=$false}
        else{throw "BLOCKED_RECEIPT_PUSH: $($push.text)"}
      }finally{
        [void](GR $root @('worktree','remove','--force',$wt))
        Remove-Item $wt -Recurse -Force -ErrorAction SilentlyContinue
      }
    }
  }finally{
    [void](GR $root @('worktree','prune'))
    Remove-Item $wt -Recurse -Force -ErrorAction SilentlyContinue
  }
  if(-not $published){throw "BLOCKED_RECEIPT_RETRY_EXHAUSTED=$attempt"}

  [void](G @('fetch','--no-tags','origin',$refspec))
  if((GR $root @('merge-base','--is-ancestor',$receiptCommit,$remoteRef)).code-ne 0){throw 'BLOCKED_RECEIPT_NOT_REMOTE_ANCESTOR'}
  $remoteReceiptBlob=(G @('rev-parse',("$remoteRef`:$receiptPath"))).Trim()
  if($remoteReceiptBlob-ne $receiptBlob){throw 'BLOCKED_RECEIPT_BLOB_MISMATCH'}
  $rr=(G @('show',("$remoteRef`:$receiptPath"))|ConvertFrom-Json)
  $receiptValid=
    ([int]$rr.contract_version-eq 7)-and
    ([string]$rr.receipt_path-eq $receiptPath)-and
    ([string]$rr.bootstrap_publish_commit_sha-eq $bootstrapCommit)-and
    ([string]$rr.bootstrap_publish_parent_sha-eq $bootstrapParent)-and
    ([string]$rr.bootstrap_blob_sha-eq $bootstrapBlob)-and
    ([int]$rr.bootstrap_publish_attempt-eq $bootstrapAttempt)-and
    ([string]$rr.bootstrap_heads_scope-eq 'PRESTART_SYNC_ONLY')-and
    ([string]$rr.postpublish_head_relation-eq 'LOCAL_ANCESTOR_REMOTE_INCLUDES_BOOTSTRAP_COMMIT')-and
    ([bool]$rr.canonical_local_head_is_remote_ancestor)-and
    ([string]$rr.root_launcher_blob_sha-eq $rootBlob)-and
    ([string]$rr.outer_execution_blob_sha-eq $outerExecutingBlob)-and
    ([string]$rr.pinned_contract5_core_blob_sha-eq $coreBlob)-and
    ([bool]$rr.successful_core_reexec_stale_outer_must_exit)-and
    ([string]$rr.remote_guard_blob_sha-eq $guardBlob)-and
    ([string]$rr.starter_blob_sha-eq $starterBlob)-and
    ([bool]$rr.no_reset_hard)-and([bool]$rr.no_force_push)
  if(-not $receiptValid){throw 'BLOCKED_RECEIPT_REMOTE_READBACK_INVALID'}
  exit 0
}finally{
  Remove-Item $tempCore -Force -ErrorAction SilentlyContinue
}
