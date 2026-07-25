$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$slotId = if ($env:AAYS_SLOT_ID) { [string]$env:AAYS_SLOT_ID } else { 'security_public_safety_3' }
$taskId = if ($env:AAYS_TASK_ID) { [string]$env:AAYS_TASK_ID } else { 'security-public-safety-3-resume-9147406c4a5f' }
$continuationKey = '9147406c4a5fb6fbd06910dddf2b38c200878a801d5bb0907aaf395f6170d1da'
if ($slotId -ne 'security_public_safety_3') { Write-Error "SLOT_ID_MISMATCH:$slotId"; exit 2 }

$repoRoot = (& git rev-parse --show-toplevel 2>$null).Trim()
if (-not $repoRoot) { Write-Error 'REPO_ROOT_UNAVAILABLE'; exit 2 }

$v4Relative = 'docs/chatgpt_status/aays1/shards/security_public_safety_3/runtime_browser_acceptance_worker_v4.ps1'
$v4Path = Join-Path $repoRoot $v4Relative
if (-not (Test-Path -LiteralPath $v4Path)) { Write-Error "V4_WORKER_MISSING:$v4Relative"; exit 2 }

$source = Get-Content -LiteralPath $v4Path -Raw -Encoding UTF8
$requiredFragments = @(
    "  const pageCounts=[];",
    "    pageCounts.push(document.querySelectorAll('#table tbody tr').length);",
    "  const parcelIds=state.filtered.map(row=>row&&row.parcel_id).filter(Boolean);",
    "v4_paginated_dom_all_rows"
)
foreach ($fragment in $requiredFragments) {
    $count = ([regex]::Matches($source,[regex]::Escape($fragment))).Count
    if ($count -lt 1) { Write-Error "V5_PATCH_FRAGMENT_MISSING:$fragment"; exit 2 }
}

$patched = $source.Replace(
    "  const pageCounts=[];",
    "  const pageCounts=[];`n  const renderedParcelIds=[];"
)
$patched = $patched.Replace(
    "    pageCounts.push(document.querySelectorAll('#table tbody tr').length);",
    @"
    const bodyRows=[...document.querySelectorAll('#table tbody tr')];
    const headerTexts=[...document.querySelectorAll('#table thead th')].map(th=>(th.textContent||'').trim());
    const parcelColumnIndex=headerTexts.findIndex(text=>text==='Parsel');
    if(parcelColumnIndex<0) throw new Error('Parsel column missing');
    pageCounts.push(bodyRows.length);
    renderedParcelIds.push(...bodyRows.map(tr=>((tr.children[parcelColumnIndex]||{}).textContent||'').trim()).filter(Boolean));
"@.TrimEnd()
)
$patched = $patched.Replace(
    "  const parcelIds=state.filtered.map(row=>row&&row.parcel_id).filter(Boolean);",
    "  const parcelIds=renderedParcelIds;"
)
$patched = $patched.Replace('v4_paginated_dom_all_rows','v5_paginated_dom_rendered_id_integrity')

if ($patched -eq $source) { Write-Error 'V5_PATCH_NO_CHANGE'; exit 2 }
if (-not $patched.Contains('const parcelIds=renderedParcelIds;')) { Write-Error 'V5_RENDERED_ID_PATCH_NOT_APPLIED'; exit 2 }
if ($patched.Contains('const parcelIds=state.filtered.map')) { Write-Error 'V5_STATE_ARRAY_ID_CHECK_STILL_PRESENT'; exit 2 }

$runStamp = [DateTimeOffset]::UtcNow.ToString('yyyyMMdd_HHmmss')
$patchRootRelative = "docs/chatgpt_status/aays1/shards/security_public_safety_3/runner_outputs/v5_patch_$runStamp"
$patchRoot = Join-Path $repoRoot $patchRootRelative
New-Item -ItemType Directory -Force -Path $patchRoot | Out-Null
$patchedPath = Join-Path $patchRoot 'runtime_browser_acceptance_worker_v5_patched.ps1'
[IO.File]::WriteAllText($patchedPath,$patched,[Text.UTF8Encoding]::new($false))

$engine = $null
foreach ($name in @('pwsh','powershell')) {
    $cmd = Get-Command $name -ErrorAction SilentlyContinue
    if ($cmd) { $engine = $cmd.Source; break }
}
if (-not $engine) { Write-Error 'POWERSHELL_ENGINE_UNAVAILABLE'; exit 2 }

& $engine -NoProfile -ExecutionPolicy Bypass -File $patchedPath
$exitCode = $LASTEXITCODE
if ($null -eq $exitCode) { $exitCode = 2 }
exit ([int]$exitCode)
