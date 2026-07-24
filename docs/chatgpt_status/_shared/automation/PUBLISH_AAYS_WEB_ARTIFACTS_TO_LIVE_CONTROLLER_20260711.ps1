[CmdletBinding()]
param(
  [Parameter(Mandatory=$true)][string]$TaskRepoRoot,
  [Parameter(Mandatory=$true)][string]$ControllerRoot,
  [Parameter(Mandatory=$true)][string[]]$Paths,
  [switch]$AllowGeneratedArtifacts,
  [switch]$SyncPortableWeb
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
function Test-GeneratedArtifactPath([string]$RelativePath){
  return (
    $RelativePath -like 'england_map_web/data/program_layer_matrix/*' -or
    $RelativePath -like 'england_map_web/data/geometry_review_3of4/*' -or
    $RelativePath -like 'england_map_web/data/security_public_safety/*' -or
    $RelativePath -like 'england_map_web/data/distance_property_types/*' -or
    $RelativePath -eq 'england_map_web/TerraYield_England_Program_Parcel_Layer_Matrix_20260629.html'
  )
}
$taskRoot=[IO.Path]::GetFullPath($TaskRepoRoot);$controller=[IO.Path]::GetFullPath($ControllerRoot)
if($taskRoot-eq$controller){throw 'TASK_AND_CONTROLLER_ROOT_MUST_DIFFER'}
if(-not(Test-Path -LiteralPath (Join-Path $controller 'england_map_web'))){throw 'CONTROLLER_WEB_ROOT_MISSING'}
$manifestPath=Join-Path $controller 'docs\chatgpt_status\_shared\status\local_live_web_publish_latest.json'
$previous=$null;try{if(Test-Path -LiteralPath $manifestPath){$previous=Get-Content -LiteralPath $manifestPath -Raw -Encoding UTF8|ConvertFrom-Json}}catch{$previous=$null}
$expandedPaths=@()
foreach($pathArgument in @($Paths)){$expandedPaths+=@(([string]$pathArgument)-split'\|')}
$results=@()
foreach($raw in @($expandedPaths|Where-Object{$_}|Select-Object -Unique)){
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
      if(-not$safe-and$AllowGeneratedArtifacts-and(Test-GeneratedArtifactPath $rel)){$safe=$true;$reason='generated_artifact_allowlist'}
      if(-not$safe){$reason='controller_file_differs_from_controller_head_and_last_publish_user_change_preserved'}
    }
  }
  if(-not$safe){$results+=[ordered]@{path=$rel;status='skipped';reason=$reason};continue}
  $parent=Split-Path -Parent $destination;if(-not(Test-Path $parent)){New-Item -ItemType Directory -Force -Path $parent|Out-Null};$temp=$destination+'.publish.'+$PID+'.tmp';Copy-Item -LiteralPath $source -Destination $temp -Force;Move-Item -LiteralPath $temp -Destination $destination -Force
  $results+=[ordered]@{path=$rel;status='published';sha256=(Hash-File $destination)}
}
$parent=Split-Path -Parent $manifestPath;if(-not(Test-Path $parent)){New-Item -ItemType Directory -Force -Path $parent|Out-Null}
$portableSyncStatus='not_requested'
$portableSyncResults=@()
if($SyncPortableWeb){
  $cursor=$controller
  while($cursor-and(Split-Path -Leaf $cursor)-ne'runner_system'){$parent=Split-Path -Parent $cursor;if($parent-eq$cursor){break};$cursor=$parent}
  if((Split-Path -Leaf $cursor)-eq'runner_system'){
    $portableRoot=Split-Path -Parent $cursor
    $portableAppRoot=Join-Path $portableRoot 'AAYS'
    if(Test-Path -LiteralPath (Join-Path $portableAppRoot 'england_map_web')){
      foreach($row in @($results|Where-Object{$_.status-in@('published','already_current')})){
        $rel=[string]$row.path
        $liveSource=Join-Path $controller ($rel-replace'/','\')
        $liveDestination=Join-Path $portableAppRoot ($rel-replace'/','\')
        if(-not(Test-Path -LiteralPath $liveSource)){$portableSyncResults+=[ordered]@{path=$rel;status='source_missing'};continue}
        $liveParent=Split-Path -Parent $liveDestination;if(-not(Test-Path -LiteralPath $liveParent)){New-Item -ItemType Directory -Force -Path $liveParent|Out-Null}
        $liveTemp=$liveDestination+'.publish.'+$PID+'.tmp';Copy-Item -LiteralPath $liveSource -Destination $liveTemp -Force;Move-Item -LiteralPath $liveTemp -Destination $liveDestination -Force
        $portableSyncResults+=[ordered]@{path=$rel;status='published';sha256=(Hash-File $liveDestination)}
      }
      $portableSyncStatus='completed_targeted_files_only'
    }else{$portableSyncStatus='portable_app_web_root_missing'}
  }else{$portableSyncStatus='portable_root_not_resolved'}
}
$payload=[ordered]@{published_at=(Get-Date).ToUniversalTime().ToString('o');task_repo_root=$taskRoot;controller_root=$controller;allow_generated_artifacts=[bool]$AllowGeneratedArtifacts;portable_sync_status=$portableSyncStatus;portable_sync_results=$portableSyncResults;published_count=@($results|Where-Object{$_.status-eq'published'}).Count;skipped_count=@($results|Where-Object{$_.status-eq'skipped'}).Count;results=$results;final_ready=$false;fake_data=$false}
[IO.File]::WriteAllText($manifestPath,(($payload|ConvertTo-Json -Depth 30)+[Environment]::NewLine),[Text.UTF8Encoding]::new($false))
$payload|ConvertTo-Json -Depth 30
if(@($results|Where-Object{$_.status-eq'skipped'}).Count-gt0){exit 3}
