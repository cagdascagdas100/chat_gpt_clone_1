param(
  [string]$RepoRoot = (Get-Location).Path,
  [string]$BaseUrl = 'http://127.0.0.1:8012'
)
$ErrorActionPreference = 'Stop'
if ($env:AAYS_SLOT_ID -and $env:AAYS_SLOT_ID -ne 'gas_emissions_1') { throw 'WRONG_SLOT_CONTEXT' }
$taskId = if ($env:AAYS_TASK_ID) { $env:AAYS_TASK_ID } else { 'gas_emissions_1_browser_dump_dom_fallback_20260722_01' }
$reportPath = Join-Path $RepoRoot 'docs/chatgpt_status/gas_emissions/shards/gas_emissions_1/reports/gas_emissions_1_browser_dump_dom_latest.json'
$statusPath = Join-Path $RepoRoot 'docs/chatgpt_status/gas_emissions/shards/gas_emissions_1/status/gas_emissions_1_browser_dump_dom_latest.json'
$pageUrl = "$BaseUrl/england_map_web/data/aays_21_slots/gas_emissions_1/browser_acceptance_100.html?expected=100&ts=$([DateTimeOffset]::UtcNow.ToUnixTimeMilliseconds())"
$jsonUrl = "$BaseUrl/england_map_web/data/program_layer_matrix/gas_emissions_visible_rows_latest.json?expected=100&ts=$([DateTimeOffset]::UtcNow.ToUnixTimeMilliseconds())"
$browserCandidates = @()
foreach ($name in @('msedge','google-chrome','chrome','chromium','chromium-browser')) {
  $cmd = Get-Command $name -ErrorAction SilentlyContinue
  if ($cmd) { $browserCandidates += $cmd.Source }
}
$browserCandidates += @(
  "$env:ProgramFiles\Google\Chrome\Application\chrome.exe",
  "${env:ProgramFiles(x86)}\Google\Chrome\Application\chrome.exe",
  "$env:LOCALAPPDATA\Google\Chrome\Application\chrome.exe",
  "$env:ProgramFiles\Microsoft\Edge\Application\msedge.exe",
  "${env:ProgramFiles(x86)}\Microsoft\Edge\Application\msedge.exe"
)
$browser = $browserCandidates | Where-Object { $_ -and (Test-Path $_) } | Select-Object -First 1
$result = [ordered]@{
  schema_version = 1
  slot_id = 'gas_emissions_1'
  task_id = $taskId
  generated_at = [DateTime]::UtcNow.ToString('o')
  page_url = $pageUrl
  json_url = $jsonUrl
  browser_binary = $browser
  http_rows = 0
  http_unique_rows = 0
  dom_rows = 0
  dom_unique_rows = 0
  required_headers_present = $false
  body_acceptance_status = $null
  browser_exit_code = $null
  stderr_tail = $null
  browser_acceptance_100_passed = $false
  parcel_binding_gate_passed = $false
  final_ready = $false
  fake_data = $false
  db_write = $false
  migration = $false
  production_deploy = $false
}
try {
  $doc = Invoke-RestMethod -Uri $jsonUrl -TimeoutSec 30
  $rows = @($doc.rows)
  $ids = @($rows | ForEach-Object { [string]$_.row_id } | Where-Object { $_ })
  $result.http_rows = $rows.Count
  $result.http_unique_rows = @($ids | Sort-Object -Unique).Count
  if (-not $browser) { throw 'BROWSER_BINARY_NOT_FOUND' }
  $tmpRoot = Join-Path ([IO.Path]::GetTempPath()) ('gas_emissions_1_dump_dom_' + [Guid]::NewGuid().ToString('N'))
  New-Item -ItemType Directory -Path $tmpRoot | Out-Null
  $domPath = Join-Path $tmpRoot 'dom.html'
  $errPath = Join-Path $tmpRoot 'stderr.txt'
  $args = @('--headless=new','--disable-gpu','--no-sandbox','--disable-dev-shm-usage','--virtual-time-budget=20000','--dump-dom',$pageUrl)
  & $browser @args 1> $domPath 2> $errPath
  $result.browser_exit_code = $LASTEXITCODE
  $dom = Get-Content -Raw -Path $domPath
  $stderr = if (Test-Path $errPath) { Get-Content -Raw -Path $errPath } else { '' }
  $result.stderr_tail = if ($stderr.Length -gt 2000) { $stderr.Substring($stderr.Length - 2000) } else { $stderr }
  $result.dom_rows = ([regex]::Matches($dom, 'data-gas-row="true"')).Count
  $domIds = [regex]::Matches($dom, 'data-row-id="([^"]+)"') | ForEach-Object { $_.Groups[1].Value }
  $result.dom_unique_rows = @($domIds | Sort-Object -Unique).Count
  $statusMatch = [regex]::Match($dom, 'data-acceptance-status="([^"]+)"')
  if ($statusMatch.Success) { $result.body_acceptance_status = $statusMatch.Groups[1].Value }
  $requiredHeaders = @('Satır ID','Yıl','Sektör','Alt sektör','Gaz','Territorial kt CO2e','Kaynak satırı','Eşleştirme','Güven','Parsel durumu','Semantik')
  $result.required_headers_present = -not ($requiredHeaders | Where-Object { $dom -notmatch [regex]::Escape("<th>$_</th>") })
  $result.browser_acceptance_100_passed = (
    $result.browser_exit_code -eq 0 -and
    $result.http_rows -eq 100 -and
    $result.http_unique_rows -eq 100 -and
    $result.dom_rows -eq 100 -and
    $result.dom_unique_rows -eq 100 -and
    $result.body_acceptance_status -eq 'PASS' -and
    $result.required_headers_present
  )
  $result.status = if ($result.browser_acceptance_100_passed) { 'PASS_BROWSER_DUMP_DOM_100_OF_100' } else { 'BLOCKED_BROWSER_DUMP_DOM_ACCEPTANCE' }
  $result.blocker = if ($result.browser_acceptance_100_passed) { $null } else { 'HTTP_OR_DOM_COUNT_STATUS_HEADER_OR_BROWSER_EXIT_MISMATCH' }
} catch {
  $result.status = 'BLOCKED_BROWSER_DUMP_DOM_ACCEPTANCE'
  $result.blocker = $_.Exception.Message
}
foreach ($path in @($reportPath,$statusPath)) {
  $dir = Split-Path -Parent $path
  New-Item -ItemType Directory -Force -Path $dir | Out-Null
  $result | ConvertTo-Json -Depth 8 | Set-Content -Path $path -Encoding UTF8
}
$result | ConvertTo-Json -Depth 8
if ($result.browser_acceptance_100_passed) { exit 0 } else { exit 2 }
