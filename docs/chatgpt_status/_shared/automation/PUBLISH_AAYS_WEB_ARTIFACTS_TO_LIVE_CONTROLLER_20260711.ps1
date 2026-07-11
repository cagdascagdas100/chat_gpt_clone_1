[CmdletBinding()]
param(
  [Parameter(Mandatory=$true)][string]$TaskRepoRoot,
  [Parameter(Mandatory=$true)][string]$ControllerRoot,
  [Parameter(Mandatory=$true)][string[]]$Paths
)
$ErrorActionPreference='Stop'
function Invoke-GitCommand([string]$Root,[string[]]$GitArgs){
  $previousPreference=$ErrorActionPreference
  try {
    $ErrorActionPreference='Continue'
    $o=& git.exe -C $Root @GitArgs 2>&1
    $code=$LASTEXITCODE
  } finally {
    $ErrorActionPreference=$previousPreference
  }
  [pscustomobject]@{code=$code;output=(($o|Out-String).Trim())}
}
function Hash-File([string]$Path){if(Test-Path -LiteralPath $Path){(Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant()}else{$null}}
$taskRoot=[IO.Path]::GetFullPath($TaskRepoRoot);$controller=[IO.Path]::GetFullPath($ControllerRoot)
if($taskRoot-eq$controller){throw 'TASK_AND_CONTROLLER_ROOT_MUST_DIFFER'}
if(-not(Test-Path -LiteralPath (Join-Path $controller 'england_map_web'))){throw 'CONTROLLER_WEB_ROOT_MISSING'}
$manifestPath=Join-Path $controller 'docs\chatgpt_status\_shared\status\local_live_web_publish_latest.json'
$previous=$null;try{if(Test-Path -LiteralPath $manifestPath){$previous=Get-Content -LiteralPath $manifestPath -Raw -Encoding UTF8|ConvertFrom-Json}}catch{$previous=$null}
$results=@()
foreach($raw in @($Paths|Select-Object -Unique)){
  $rel=([string]$raw).Replace('\','/').TrimStart('/')
  if($rel-notlike'england_map_web/*'){$results+=[ordered]@{path=$rel;status='rejected_non_web_path'};continue}
  $source=Join-Path $taskRoot ($rel-replace'/','\');$destination=Join-Path $controller ($rel-replace'/','\')
  if(-not(Test-Path -LiteralPath $source)){$results+=[ordered]@{path=$rel;status='source_missing'};continue}
  $safe=$false;$reason=''
  if(-not(Test-Path -LiteralPath $destination)){$controllerBase=Invoke-GitCommand -Root $controller -GitArgs @('cat-file','-e',('HEAD:'+$rel));if($controllerBase.code-ne0){$safe=$true}else{$reason='tracked_controller_file_missing_user_deletion_preserved'}}else{
    $baseBlob=Invoke-GitCommand -Root $taskRoot -GitArgs @('rev-parse',('HEAD:'+$rel));$workingBlob=Invoke-GitCommand -Root $controller -GitArgs @('hash-object',('--path='+$rel),'--',$rel)
    if($baseBlob.code-eq0-and$workingBlob.code-eq0-and$baseBlob.output.Trim()-eq$workingBlob.output.Trim()){$safe=$true}else{
      $sourceSha=Hash-File $source;$destinationSha=Hash-File $destination
      if($sourceSha-eq$destinationSha){$results+=[ordered]@{path=$rel;status='already_current';sha256=$sourceSha};continue}
      $controllerHeadBlob=Invoke-GitCommand -Root $controller -GitArgs @('rev-parse',('HEAD:'+$rel))
      if($controllerHeadBlob.code-eq0-and$workingBlob.code-eq0-and$controllerHeadBlob.output.Trim()-eq$workingBlob.output.Trim()){$safe=$true}
      $previousRow=$null;if($previous-and[string]$previous.task_repo_root-eq$taskRoot){$previousRow=@($previous.results|Where-Object{[string]$_.path-eq$rel-and[string]$_.status-in@('published','already_current')})|Select-Object -Last 1}
      if(-not$safe-and$previousRow-and[string]$previousRow.sha256-eq$destinationSha){$safe=$true}
      if(-not$safe){$reason='controller_file_differs_from_controller_head_and_last_publish_user_change_preserved'}
    }
  }
  if(-not$safe){$results+=[ordered]@{path=$rel;status='skipped';reason=$reason};continue}
  $parent=Split-Path -Parent $destination;if(-not(Test-Path $parent)){New-Item -ItemType Directory -Force -Path $parent|Out-Null};$temp=$destination+'.publish.'+$PID+'.tmp';Copy-Item -LiteralPath $source -Destination $temp -Force;Move-Item -LiteralPath $temp -Destination $destination -Force
  $results+=[ordered]@{path=$rel;status='published';sha256=(Hash-File $destination)}
}
$parent=Split-Path -Parent $manifestPath;if(-not(Test-Path $parent)){New-Item -ItemType Directory -Force -Path $parent|Out-Null}
$payload=[ordered]@{published_at=(Get-Date).ToUniversalTime().ToString('o');task_repo_root=$taskRoot;controller_root=$controller;published_count=@($results|Where-Object{$_.status-eq'published'}).Count;skipped_count=@($results|Where-Object{$_.status-eq'skipped'}).Count;results=$results;final_ready=$false;fake_data=$false}
[IO.File]::WriteAllText($manifestPath,(($payload|ConvertTo-Json -Depth 30)+[Environment]::NewLine),[Text.UTF8Encoding]::new($false))
$payload|ConvertTo-Json -Depth 30
if(@($results|Where-Object{$_.status-eq'skipped'}).Count-gt0){exit 3}
