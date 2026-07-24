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
    "    uniqueParcelCount:new Set(parcelIds).size,",
    '$uniqueParcelCount = if ($domEvidence) { [int]$domEvidence.uniqueParcelCount } else { 0 }',
    'if ($uniqueParcelCount -ne 300) { Add-Unique $blockers ("BROWSER_UNIQUE_PARCEL_COUNT_MISMATCH:$uniqueParcelCount/300") }',
    '    $uniqueParcelCount -eq 300 -and',
    '    browser_unique_parcel_count=$uniqueParcelCount',
    '        unique_parcel_count=$uniqueParcelCount',
    'v4_paginated_dom_all_rows'
)
foreach ($fragment in $requiredFragments) {
    $count = ([regex]::Matches($source,[regex]::Escape($fragment))).Count
    if ($count -ne 1) { Write-Error "V6_PATCH_FRAGMENT_COUNT_MISMATCH:${count}:$fragment"; exit 2 }
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
    @"
  const parcelIds=renderedParcelIds;
  const expectedParcelIds=Array.from({length:300},(_,index)=>'parcel_'+(index+1));
  const expectedParcelSet=new Set(expectedParcelIds);
  const actualParcelSet=new Set(parcelIds);
  const missingParcelIds=expectedParcelIds.filter(id=>!actualParcelSet.has(id));
  const unexpectedParcelIds=[...actualParcelSet].filter(id=>!expectedParcelSet.has(id));
  const exactParcelSetMatch=parcelIds.length===300&&actualParcelSet.size===300&&missingParcelIds.length===0&&unexpectedParcelIds.length===0;
"@.TrimEnd()
)
$patched = $patched.Replace(
    "    uniqueParcelCount:new Set(parcelIds).size,",
    @"
    uniqueParcelCount:new Set(parcelIds).size,
    exactParcelSetMatch,
    missingParcelIds,
    unexpectedParcelIds,
    renderedParcelIds:parcelIds,
"@.TrimEnd()
)
$patched = $patched.Replace(
    '$uniqueParcelCount = if ($domEvidence) { [int]$domEvidence.uniqueParcelCount } else { 0 }',
    @'
$uniqueParcelCount = if ($domEvidence) { [int]$domEvidence.uniqueParcelCount } else { 0 }
$exactParcelSetMatch = if ($domEvidence) { [bool]$domEvidence.exactParcelSetMatch } else { $false }
$missingParcelIds = if ($domEvidence) { @($domEvidence.missingParcelIds) } else { @() }
$unexpectedParcelIds = if ($domEvidence) { @($domEvidence.unexpectedParcelIds) } else { @() }
$renderedParcelIds = if ($domEvidence) { @($domEvidence.renderedParcelIds) } else { @() }
'@.TrimEnd()
)
$patched = $patched.Replace(
    'if ($uniqueParcelCount -ne 300) { Add-Unique $blockers ("BROWSER_UNIQUE_PARCEL_COUNT_MISMATCH:$uniqueParcelCount/300") }',
    @'
if ($uniqueParcelCount -ne 300) { Add-Unique $blockers ("BROWSER_UNIQUE_PARCEL_COUNT_MISMATCH:$uniqueParcelCount/300") }
if (-not $exactParcelSetMatch) { Add-Unique $blockers ("BROWSER_EXACT_PARCEL_SET_MISMATCH:missing=$($missingParcelIds.Count);unexpected=$($unexpectedParcelIds.Count)") }
'@.TrimEnd()
)
$patched = $patched.Replace(
    '    $uniqueParcelCount -eq 300 -and',
    "    `$uniqueParcelCount -eq 300 -and`n    `$exactParcelSetMatch -and"
)
$patched = $patched.Replace(
    '    browser_unique_parcel_count=$uniqueParcelCount',
    @'
    browser_unique_parcel_count=$uniqueParcelCount
    browser_exact_parcel_set_match=[bool]$exactParcelSetMatch
    browser_missing_parcel_ids=$missingParcelIds
    browser_unexpected_parcel_ids=$unexpectedParcelIds
    browser_rendered_parcel_ids=$renderedParcelIds
'@.TrimEnd()
)
$patched = $patched.Replace(
    '        unique_parcel_count=$uniqueParcelCount',
    @'
        unique_parcel_count=$uniqueParcelCount
        exact_parcel_set_match=[bool]$exactParcelSetMatch
        missing_parcel_ids=$missingParcelIds
        unexpected_parcel_ids=$unexpectedParcelIds
'@.TrimEnd()
)
$patched = $patched.Replace('v4_paginated_dom_all_rows','v6_paginated_dom_exact_parcel_set')

if ($patched -eq $source) { Write-Error 'V6_PATCH_NO_CHANGE'; exit 2 }
foreach ($required in @('const exactParcelSetMatch=','browser_exact_parcel_set_match=[bool]$exactParcelSetMatch','exact_parcel_set_match=[bool]$exactParcelSetMatch','v6_paginated_dom_exact_parcel_set')) {
    if (-not $patched.Contains($required)) { Write-Error "V6_PATCH_VALIDATION_FAILED:$required"; exit 2 }
}
if ($patched.Contains('const parcelIds=state.filtered.map')) { Write-Error 'V6_STATE_ARRAY_ID_CHECK_STILL_PRESENT'; exit 2 }

$runStamp = [DateTimeOffset]::UtcNow.ToString('yyyyMMdd_HHmmss')
$patchRootRelative = "docs/chatgpt_status/aays1/shards/security_public_safety_3/runner_outputs/v6_patch_$runStamp"
$patchRoot = Join-Path $repoRoot $patchRootRelative
New-Item -ItemType Directory -Force -Path $patchRoot | Out-Null
$patchedPath = Join-Path $patchRoot 'runtime_browser_acceptance_worker_v6_patched.ps1'
[IO.File]::WriteAllText($patchedPath,$patched,[Text.UTF8Encoding]::new($false))

$tokens = $null
$parseErrors = $null
[void][System.Management.Automation.Language.Parser]::ParseFile($patchedPath,[ref]$tokens,[ref]$parseErrors)
if (@($parseErrors).Count -gt 0) {
    $messages = @($parseErrors | ForEach-Object { $_.Message }) -join ' | '
    Write-Error "V6_PATCHED_WORKER_PARSE_FAILED:$messages"
    exit 2
}

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
