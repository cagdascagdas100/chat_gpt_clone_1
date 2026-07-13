[CmdletBinding()]
param(
  [Parameter(Mandatory=$true)][int]$ExpectedRows
)

$ErrorActionPreference = 'Stop'

$repoRoot = [System.IO.Path]::GetFullPath([string]$env:AAYS_REPO_ROOT)
if (-not $repoRoot -or [string]$env:AAYS_PAGE_KEY -ne 'gas_emissions') {
  throw 'GAS_EMISSIONS_DOM_READY_FIX_WRONG_CONTEXT'
}
if ([string]$env:AAYS_TARGET_BRANCH -ne 'codex/aays-single-runner-v5-20260706') {
  throw 'GAS_EMISSIONS_DOM_READY_FIX_WRONG_BRANCH'
}

$sourceRel = 'docs\chatgpt_status\gas_emissions\automation\RUN_GAS_EMISSIONS_PUBLISH_CURRENT_AND_BROWSER_PROOF_20260713.ps1'
$sourcePath = Join-Path $repoRoot $sourceRel
if (-not (Test-Path -LiteralPath $sourcePath)) {
  throw 'GAS_EMISSIONS_GENERIC_PROOF_SOURCE_NOT_FOUND'
}

$source = Get-Content -LiteralPath $sourcePath -Raw -Encoding UTF8
$patched = $source

$oldArgs = '("--headless=new", "--disable-gpu", "--no-sandbox", "--disable-dev-shm-usage", "--window-size=1920,1400")'
$newArgs = '("--headless=new", "--disable-gpu", "--no-sandbox", "--disable-dev-shm-usage", "--window-size=1920,1400", "--no-proxy-server", "--proxy-bypass-list=<-loopback>")'
$patched = $patched.Replace($oldArgs, $newArgs)

$pattern = '(?ms)^    driver\.get\(url\)\r?\n    wait = WebDriverWait\(driver, 90\)\r?\n    wait\.until\(lambda d: d\.find_element\(By\.ID, "layerSelect"\)\)\r?\n    Select\(driver\.find_element\(By\.ID, "layerSelect"\)\)\.select_by_value\("gas"\)\r?\n    wait\.until\(lambda d: f"\{target\} satır" in d\.find_element\(By\.ID, "pageInfo"\)\.text\)'
$replacement = @'
    driver.get(url)
    wait = WebDriverWait(driver, 120)
    wait.until(lambda d: d.execute_script("return document.readyState") in ("interactive", "complete"))
    wait.until(lambda d: len(d.find_elements(By.ID, "layerSelect")) == 1)
    driver.execute_script("""
      const select = document.getElementById('layerSelect');
      select.value = 'gas';
      select.dispatchEvent(new Event('change', {bubbles:true}));
      if (typeof loadLayer === 'function') { loadLayer('gas'); }
    """)
    wait.until(lambda d: str(target) in d.find_element(By.ID, "pageInfo").text and "Sayfa" in d.find_element(By.ID, "pageInfo").text)
    wait.until(lambda d: len(d.find_elements(By.CSS_SELECTOR, "#table tbody tr")) > 0)
'@
$patched = [regex]::Replace($patched, $pattern, $replacement)

if ($patched -eq $source) {
  throw 'GAS_EMISSIONS_DOM_READY_FIX_NO_PATCH_APPLIED'
}
if ($patched -notmatch '--no-proxy-server') {
  throw 'GAS_EMISSIONS_DOM_READY_FIX_PROXY_PATCH_MISSING'
}
if ($patched -notmatch "typeof loadLayer === 'function'") {
  throw 'GAS_EMISSIONS_DOM_READY_FIX_LAYER_RELOAD_PATCH_MISSING'
}

$tmp = Join-Path ([System.IO.Path]::GetTempPath()) ('gas_dom_ready_fix_' + [Guid]::NewGuid().ToString('N') + '.ps1')
try {
  [System.IO.File]::WriteAllText($tmp, $patched, [System.Text.UTF8Encoding]::new($false))
  & powershell -NoProfile -ExecutionPolicy Bypass -File $tmp -ExpectedRows $ExpectedRows
  $exitCode = $LASTEXITCODE
  if ($exitCode -ne 0) {
    throw "GAS_EMISSIONS_DOM_READY_FIX_CHILD_FAILED: exit=$exitCode"
  }
} finally {
  Remove-Item -LiteralPath $tmp -Force -ErrorAction SilentlyContinue
}
