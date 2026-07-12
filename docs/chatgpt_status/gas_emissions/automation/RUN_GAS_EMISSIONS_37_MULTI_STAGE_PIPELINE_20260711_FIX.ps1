[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$repoRoot = [System.IO.Path]::GetFullPath([string]$env:AAYS_REPO_ROOT)
if (-not $repoRoot -or [string]$env:AAYS_PAGE_KEY -ne 'gas_emissions') {
  throw 'GAS_EMISSIONS_37_FIX_WRAPPER_MUST_RUN_INSIDE_CANONICAL_SHARED_RUNNER'
}
$source = Join-Path $repoRoot 'docs\chatgpt_status\gas_emissions\automation\RUN_GAS_EMISSIONS_37_MULTI_STAGE_PIPELINE_20260711.ps1'
if (-not (Test-Path -LiteralPath $source)) { throw 'GAS_EMISSIONS_37_SOURCE_SCRIPT_MISSING' }
$text = Get-Content -LiteralPath $source -Raw -Encoding UTF8
$bad = '$actualTerritorial = [double]$_ = [double]$m.''Territorial emissions (kt CO2e)'''
$good = '$actualTerritorial = [double]$m.''Territorial emissions (kt CO2e)'''
if ($text.Contains($bad)) {
  $fixed = $text.Replace($bad, $good)
} elseif ($text.Contains($good)) {
  $fixed = $text
} else {
  throw 'EXPECTED_FIX_TARGET_NOT_FOUND'
}
$listCastBad = '$visible.rows = @($oldRows) + @($verified)'
$listCastGood = '$visible.rows = @($oldRows) + $verified.ToArray()'
if ($fixed.Contains($listCastBad)) {
  $fixed = $fixed.Replace($listCastBad, $listCastGood)
} elseif (-not $fixed.Contains($listCastGood)) {
  throw 'EXPECTED_LIST_CAST_FIX_TARGET_NOT_FOUND'
}
$safetyTargets = @('final_ready','product_final_ready','fake_data','db_write','migration','production_deploy')
foreach ($objectName in @('visible','status')) {
  foreach ($propertyName in $safetyTargets) {
    $directAssignment = '$' + $objectName + '.' + $propertyName + ' = $false'
    $safeAssignment = '$' + $objectName + ' | Add-Member -NotePropertyName ' + $propertyName + ' -NotePropertyValue $false -Force'
    if ($fixed.Contains($directAssignment)) {
      $fixed = $fixed.Replace($directAssignment, $safeAssignment)
    } elseif (-not $fixed.Contains($safeAssignment)) {
      throw "EXPECTED_SAFETY_PROPERTY_TARGET_NOT_FOUND_${objectName}_${propertyName}"
    }
  }
}
$portableCursor = $repoRoot
while ($portableCursor -and (Split-Path -Leaf $portableCursor) -ne 'runner_system') {
  $portableParent = Split-Path -Parent $portableCursor
  if ($portableParent -eq $portableCursor) { break }
  $portableCursor = $portableParent
}
if ((Split-Path -Leaf $portableCursor) -ne 'runner_system') { throw 'F_PORTABLE_ROOT_NOT_RESOLVED_FOR_GAS37_TEMP' }
$portableTempRoot = Join-Path (Split-Path -Parent $portableCursor) '_portable_logs\temp'
New-Item -ItemType Directory -Force -Path $portableTempRoot | Out-Null
$tmp = Join-Path $portableTempRoot ('gas_emissions_37_fixed_' + [Guid]::NewGuid().ToString('N') + '.ps1')
[System.IO.File]::WriteAllText($tmp, $fixed, [System.Text.UTF8Encoding]::new($false))
try {
  & powershell -NoProfile -ExecutionPolicy Bypass -File $tmp
  $code = $LASTEXITCODE
  if ($code -ne 0) { throw "GAS_EMISSIONS_37_FIXED_PIPELINE_EXIT_$code" }
} finally {
  Remove-Item -LiteralPath $tmp -Force -ErrorAction SilentlyContinue
}
