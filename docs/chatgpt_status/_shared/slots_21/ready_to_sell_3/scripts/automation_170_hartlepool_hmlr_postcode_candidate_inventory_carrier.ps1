[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$repoRoot = if ($env:AAYS_REPO_ROOT) {
  [System.IO.Path]::GetFullPath([string]$env:AAYS_REPO_ROOT)
} else {
  [System.IO.Path]::GetFullPath((Get-Location).Path)
}
$implementationRel = 'docs/chatgpt_status/_shared/slots_21/ready_to_sell_3/scripts/automation_170_hartlepool_hmlr_postcode_candidate_inventory.py'
$outputRel = 'docs/chatgpt_status/aays1/shards/ready_to_sell_3/validation/automation_170_hartlepool_hmlr_postcode_candidate_inventory_latest.json'
$implementation = Join-Path $repoRoot ($implementationRel -replace '/', '\')
$output = Join-Path $repoRoot ($outputRel -replace '/', '\')
if (-not (Test-Path -LiteralPath $implementation -PathType Leaf)) {
  throw "IMPLEMENTATION_NOT_FOUND=$implementation"
}

$python = Get-Command python.exe -ErrorAction SilentlyContinue
if (-not $python) { $python = Get-Command python -ErrorAction SilentlyContinue }
$prefix = @()
if (-not $python) {
  $python = Get-Command py.exe -ErrorAction SilentlyContinue
  if (-not $python) { $python = Get-Command py -ErrorAction SilentlyContinue }
  if ($python) { $prefix = @('-3') }
}
if (-not $python) { throw 'PYTHON_EXECUTABLE_NOT_FOUND' }

$argsList = @($prefix) + @(
  $implementation,
  '--output', $output,
  '--timeout-seconds', '120'
)
& $python.Source @argsList
exit $LASTEXITCODE
