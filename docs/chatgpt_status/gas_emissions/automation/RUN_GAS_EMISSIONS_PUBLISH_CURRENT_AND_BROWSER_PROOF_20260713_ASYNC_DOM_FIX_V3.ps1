[CmdletBinding()]
param(
  [Parameter(Mandatory=$true)][int]$ExpectedRows
)

$ErrorActionPreference = 'Stop'

$repoRoot = [System.IO.Path]::GetFullPath([string]$env:AAYS_REPO_ROOT)
if (-not $repoRoot -or [string]$env:AAYS_PAGE_KEY -ne 'gas_emissions') {
  throw 'GAS_EMISSIONS_ASYNC_DOM_FIX_V3_WRONG_CONTEXT'
}
if ([string]$env:AAYS_TARGET_BRANCH -ne 'codex/aays-single-runner-v5-20260706') {
  throw 'GAS_EMISSIONS_ASYNC_DOM_FIX_V3_WRONG_BRANCH'
}

$sourceRel = 'docs\chatgpt_status\gas_emissions\automation\RUN_GAS_EMISSIONS_PUBLISH_CURRENT_AND_BROWSER_PROOF_20260713.ps1'
$sourcePath = Join-Path $repoRoot $sourceRel
if (-not (Test-Path -LiteralPath $sourcePath)) {
  throw 'GAS_EMISSIONS_GENERIC_PROOF_SOURCE_NOT_FOUND'
}

$source = Get-Content -LiteralPath $sourcePath -Raw -Encoding UTF8
$patched = $source.Replace("`r`n", "`n")

$oldArgs = '("--headless=new", "--disable-gpu", "--no-sandbox", "--disable-dev-shm-usage", "--window-size=1920,1400")'
$newArgs = '("--headless=new", "--disable-gpu", "--no-sandbox", "--disable-dev-shm-usage", "--window-size=1920,1400", "--no-proxy-server", "--proxy-bypass-list=<-loopback>")'
$patched = $patched.Replace($oldArgs, $newArgs)

$oldBlock = @(
  '    driver.get(url)',
  '    wait = WebDriverWait(driver, 90)',
  '    wait.until(lambda d: d.find_element(By.ID, "layerSelect"))',
  '    Select(driver.find_element(By.ID, "layerSelect")).select_by_value("gas")',
  '    wait.until(lambda d: f"{target} satır" in d.find_element(By.ID, "pageInfo").text)'
) -join "`n"

$newBlock = @(
  '    driver.get(url)',
  '    wait = WebDriverWait(driver, 150)',
  '    wait.until(lambda d: d.execute_script("return document.readyState") in ("interactive", "complete"))',
  '    wait.until(lambda d: len(d.find_elements(By.ID, "layerSelect")) == 1)',
  '    wait.until(lambda d: len(d.find_elements(By.ID, "message")) == 1)',
  '    try:',
  '        wait.until(lambda d: "Veri yükleniyor" not in d.find_element(By.ID, "message").text)',
  '    except Exception:',
  '        pass',
  '    async_result = driver.execute_async_script("""',
  '      const done = arguments[arguments.length - 1];',
  '      (async () => {',
  '        const select = document.getElementById(''layerSelect'');',
  '        if (!select) throw new Error(''layerSelect_missing'');',
  '        select.value = ''gas'';',
  '        if (typeof loadLayer === ''function'') {',
  '          await loadLayer(''gas'');',
  '        } else {',
  '          select.dispatchEvent(new Event(''change'', {bubbles:true}));',
  '        }',
  '        return true;',
  '      })().then(v => done(v)).catch(e => done(''ERROR:'' + String(e)));',
  '    """)',
  '    if isinstance(async_result, str) and async_result.startswith("ERROR:"):',
  '        raise RuntimeError(async_result)',
  '    wait.until(lambda d: str(target) in d.find_element(By.ID, "pageInfo").text and "Sayfa" in d.find_element(By.ID, "pageInfo").text)',
  '    wait.until(lambda d: len(d.find_elements(By.CSS_SELECTOR, "#table tbody tr")) > 0)'
) -join "`n"

if (-not $patched.Contains($oldBlock)) {
  throw 'GAS_EMISSIONS_ASYNC_DOM_FIX_V3_SOURCE_BLOCK_NOT_FOUND'
}
$patched = $patched.Replace($oldBlock, $newBlock)

if ($patched -notmatch '--no-proxy-server') {
  throw 'GAS_EMISSIONS_ASYNC_DOM_FIX_V3_PROXY_PATCH_MISSING'
}
if ($patched -notmatch 'execute_async_script') {
  throw 'GAS_EMISSIONS_ASYNC_DOM_FIX_V3_ASYNC_PATCH_MISSING'
}
if ($patched -match 'WebDriverWait\(driver, 90\)') {
  throw 'GAS_EMISSIONS_ASYNC_DOM_FIX_V3_OLD_BLOCK_REMAINS'
}

$tmp = Join-Path ([System.IO.Path]::GetTempPath()) ('gas_async_dom_fix_v3_' + [Guid]::NewGuid().ToString('N') + '.ps1')
try {
  [System.IO.File]::WriteAllText($tmp, $patched, [System.Text.UTF8Encoding]::new($false))
  & powershell -NoProfile -ExecutionPolicy Bypass -File $tmp -ExpectedRows $ExpectedRows
  $exitCode = $LASTEXITCODE
  if ($exitCode -ne 0) {
    throw "GAS_EMISSIONS_ASYNC_DOM_FIX_V3_CHILD_FAILED: exit=$exitCode"
  }
} finally {
  Remove-Item -LiteralPath $tmp -Force -ErrorAction SilentlyContinue
}
