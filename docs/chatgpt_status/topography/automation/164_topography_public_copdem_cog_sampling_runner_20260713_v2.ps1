[CmdletBinding()]
param()

$ErrorActionPreference='Stop'
$root=[System.IO.Path]::GetFullPath([string]$env:AAYS_REPO_ROOT)
if(-not $root -or $root -notmatch '(?i)[\\/]TerraYield_AAYS_Portable[\\/]runner_system[\\/]'){
  throw 'TOPOGRAPHY_164_V2_REQUIRES_PORTABLE_SHARED_RUNNER_WORKTREE'
}
$base=Join-Path $root 'docs\chatgpt_status\topography\automation\164_topography_public_copdem_cog_sampling_runner_20260713.ps1'
if(-not(Test-Path -LiteralPath $base)){throw 'TOPOGRAPHY_164_BASE_SCRIPT_NOT_FOUND'}
$text=Get-Content -LiteralPath $base -Raw -Encoding UTF8
$text=$text.Replace("  `$checksumStage='partial'","  `$checksumStage='partial'`r`n  `$checksum30Status='blocked';if(`$download30.downloaded){`$checksum30Status='verified'}`r`n  `$checksum90Status='blocked';if(`$download90.downloaded){`$checksum90Status='verified'}")
$text=$text.Replace("-Status (if(`$download30.downloaded){'verified'}else{'blocked'})","-Status `$checksum30Status")
$text=$text.Replace("-Status (if(`$download90.downloaded){'verified'}else{'blocked'})","-Status `$checksum90Status")
$text=$text.Replace("  `$blockers=@('real_parcel_boundary_required','ea_lidar_or_os_terrain_numeric_validation_required')","  `$blockers=@('real_parcel_boundary_required','ea_lidar_or_os_terrain_numeric_validation_required')`r`n  `$primaryLocalPathValue=`$null;if(`$download30.downloaded){`$primaryLocalPathValue=`$path30}`r`n  `$samplingEngineValue=`$null;if(`$samplePayload){`$samplingEngineValue=`$samplePayload.engine}")
$text=$text.Replace("(if(`$download30.downloaded){`$path30}else{`$null})","`$primaryLocalPathValue")
$text=$text.Replace("(if(`$samplePayload){`$samplePayload.engine}else{`$null})","`$samplingEngineValue")
if($text.Contains('(if(')){throw 'TOPOGRAPHY_164_INLINE_IF_REPAIR_INCOMPLETE'}
$tempRoot=Join-Path ([System.IO.Path]::GetTempPath()) 'aays_topography_164'
if(-not(Test-Path -LiteralPath $tempRoot)){New-Item -ItemType Directory -Force -Path $tempRoot|Out-Null}
$patched=Join-Path $tempRoot '164_topography_public_copdem_cog_sampling_runner_patched.ps1'
[System.IO.File]::WriteAllText($patched,$text,[System.Text.UTF8Encoding]::new($false))
& powershell -NoProfile -ExecutionPolicy Bypass -File $patched
$code=$LASTEXITCODE
if($code -ne 0){throw "TOPOGRAPHY_164_PATCHED_SCRIPT_EXIT_$code"}
