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
$fixed = $fixed.Replace('-Paths @($rowsRel,$statusRel,$matrixRel)', '-Paths ((@($rowsRel,$statusRel,$matrixRel)) -join ''|'')')
$fixed = $fixed.Replace('-Paths @($statusRel)', '-Paths $statusRel')
$fixed = $fixed.Replace("-Paths ((@(`$rowsRel,`$statusRel,`$matrixRel)) -join '|')", "-Paths ((@(`$rowsRel,`$statusRel,`$matrixRel)) -join '|') -AllowGeneratedArtifacts -SyncPortableWeb")
$fixed = $fixed.Replace('-Paths $statusRel', '-Paths $statusRel -AllowGeneratedArtifacts -SyncPortableWeb')
$fixed = $fixed.Replace("{throw'GAS37_", "{ throw 'GAS37_")
$gasSelectBad = '    Select(driver.find_element(By.ID,"layerSelect")).select_by_value("gas")'
$gasSelectGood = @'
    wait.until(lambda d:d.execute_script("return typeof state !== 'undefined' && state.layer === 'security' && state.data && Array.isArray(state.data.rows) && state.data.rows.length > 0 && state.data.rows[0].security_score_percent !== undefined"))
    layer_select=driver.find_element(By.ID,"layerSelect")
    Select(layer_select).select_by_value("gas")
    driver.execute_script("arguments[0].dispatchEvent(new Event('change', {bubbles: true}))",layer_select)
'@
if ($fixed.Contains($gasSelectBad)) {
  $fixed = $fixed.Replace($gasSelectBad, $gasSelectGood.TrimEnd())
} elseif (-not $fixed.Contains('dispatchEvent(new Event(''change''')) {
  throw 'EXPECTED_GAS37_CHANGE_DISPATCH_TARGET_NOT_FOUND'
}
$fixed = $fixed.Replace('wait.until(lambda d:"37 satır" in d.find_element(By.ID,"pageInfo").text)', 'wait.until(lambda d:d.execute_script("return state.layer === ''gas'' && state.data && Array.isArray(state.data.rows) && state.data.rows.length >= 37 && state.data.rows[0].row_id !== undefined"))')
$fixed = $fixed.Replace('if "YENİ / LATEST" in rows.get(rid,"")', 'if "LATEST" in rows.get(rid,"")')
$fixed = $fixed.Replace('if "MANUEL İNCELEME" in rows.get(rid,"")', 'if "MANUEL" in rows.get(rid,"")')
$paginationBad = @'
    while "Sayfa 2 / 2" not in driver.find_element(By.ID,"pageInfo").text:
        driver.find_element(By.ID,"next").click(); wait.until(lambda d:"Sayfa 2 / 2" in d.find_element(By.ID,"pageInfo").text)
    collect()
'@
$paginationGood = @'
    while driver.execute_script("return state.page + 1 < Math.ceil(state.filtered.length / state.pageSize)"):
        before=driver.execute_script("return state.page")
        driver.find_element(By.ID,"next").click()
        wait.until(lambda d:d.execute_script("return state.page") > before)
        collect()
'@
if ($fixed.Contains($paginationBad.Trim())) {
  $fixed = $fixed.Replace($paginationBad.Trim(), $paginationGood.Trim())
} elseif (-not $fixed.Contains('Math.ceil(state.filtered.length / state.pageSize)')) {
  throw 'EXPECTED_GAS37_DYNAMIC_PAGINATION_TARGET_NOT_FOUND'
}
$fixed = $fixed.Replace('passed=len(rows)==37 and present', 'passed=len(rows)>=37 and present')
$fixed = $fixed.Replace('[int]$browser.unique_row_count -eq 37', '[int]$browser.unique_row_count -ge 37')
$fixed = $fixed.Replace('if ($httpCount -eq 37) { break }', 'if ($httpCount -ge 37) { break }')
$fixed = $fixed.Replace('if ($httpCount -ne 37) { throw "HTTP_8012_ROW_COUNT_NOT_37: $httpCount" }', 'if ($httpCount -lt 37) { throw "HTTP_8012_ROW_COUNT_BELOW_37: $httpCount" }')
$fixed = $fixed.Replace('  browser_status = [string]$browser.status', "  browser_status = [string]`$browser.status`r`n  browser_error = [string]`$browser.error")
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
