$ErrorActionPreference = 'Stop'

$Repo = $env:AAYS_REPO_ROOT
if ([string]::IsNullOrWhiteSpace($Repo)) {
  try { $Repo = (git rev-parse --show-toplevel).Trim() }
  catch { $Repo = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..\..\..\..')).Path }
}

$TaskId = if ([string]::IsNullOrWhiteSpace($env:AAYS_TASK_ID)) { 'defans-mania-quiz-audit-20260714-001' } else { $env:AAYS_TASK_ID }
$PageKey = 'aays1'
$LayerKey = 'defans_mania'
$Now = (Get-Date).ToString('o')

$LayerRoot = Join-Path $Repo "docs\chatgpt_status\$LayerKey"
$OutDir = Join-Path $LayerRoot 'runner_outputs'
$ReportDir = Join-Path $LayerRoot 'reports'
$StatusDir = Join-Path $LayerRoot 'status'
$AaysStatusDir = Join-Path $Repo "docs\chatgpt_status\$PageKey\status"
New-Item -ItemType Directory -Force -Path $OutDir,$ReportDir,$StatusDir,$AaysStatusDir | Out-Null

function Write-JsonFile([string]$Path, $Object, [int]$Depth = 30) {
  ($Object | ConvertTo-Json -Depth $Depth) | Set-Content -LiteralPath $Path -Encoding UTF8
}

function Add-UniquePath([System.Collections.ArrayList]$List, [string]$Path) {
  if ([string]::IsNullOrWhiteSpace($Path)) { return }
  try { $resolved = (Resolve-Path -LiteralPath $Path -ErrorAction Stop).Path } catch { return }
  if (-not $List.Contains($resolved)) { [void]$List.Add($resolved) }
}

function Get-LineMatches([string]$Path, [string[]]$Patterns, [int]$MaxMatches = 80) {
  $matches = New-Object System.Collections.ArrayList
  try {
    $lineNo = 0
    foreach ($line in [System.IO.File]::ReadLines($Path)) {
      $lineNo++
      foreach ($pattern in $Patterns) {
        if ($line -match $pattern) {
          [void]$matches.Add([ordered]@{ line=$lineNo; pattern=$pattern; text=($line.Trim() | Select-Object -First 1) })
          break
        }
      }
      if ($matches.Count -ge $MaxMatches) { break }
    }
  } catch {}
  return @($matches)
}

function Get-ResultAudit([string]$Path) {
  $raw = ''
  try { $raw = Get-Content -LiteralPath $Path -Raw -ErrorAction Stop } catch {
    return [ordered]@{ path=$Path; readable=$false; error=$_.Exception.Message }
  }

  $score = $null
  $wrongAnswersHeader = $null
  $wrongQuestionsHeader = $null
  if ($raw -match '(?im)^Score:\s*(\d+)') { $score = [int]$Matches[1] }
  if ($raw -match '(?im)Falsche\s+Antworten:\s*(\d+)') { $wrongAnswersHeader = [int]$Matches[1] }
  if ($raw -match '(?im)Falsche\s+Fragen:\s*(\d+)') { $wrongQuestionsHeader = [int]$Matches[1] }

  $questionMatches = [regex]::Matches($raw, '(?m)^\s*\d+\)\s+')
  $wrongCountMatches = [regex]::Matches($raw, '(?im)Falsch:\s*(\d+)x')
  $explanationMatches = [regex]::Matches($raw, '(?im)Erklaerung:\s*No:([^\r\n]+)')

  $wrongCounts = New-Object System.Collections.ArrayList
  $wrongSum = 0
  foreach ($m in $wrongCountMatches) {
    $value = [int]$m.Groups[1].Value
    [void]$wrongCounts.Add($value)
    $wrongSum += $value
  }

  $explanationIds = @($explanationMatches | ForEach-Object { $_.Groups[1].Value.Trim() })
  $duplicateExplanationIds = @($explanationIds | Group-Object | Where-Object { $_.Count -gt 1 } | ForEach-Object { [ordered]@{ id=$_.Name; count=$_.Count } })
  $questionBlocks = $questionMatches.Count

  $checks = [ordered]@{
    wrong_questions_matches_rendered_blocks = if ($null -eq $wrongQuestionsHeader) { $null } else { $wrongQuestionsHeader -eq $questionBlocks }
    wrong_answers_matches_sum_of_per_question_counts = if ($null -eq $wrongAnswersHeader) { $null } else { $wrongAnswersHeader -eq $wrongSum }
    each_rendered_question_has_wrong_count = $questionBlocks -eq $wrongCountMatches.Count
    explanation_ids_are_unique = $duplicateExplanationIds.Count -eq 0
  }

  return [ordered]@{
    path = $Path
    readable = $true
    modified_at = (Get-Item -LiteralPath $Path).LastWriteTime.ToString('o')
    score = $score
    header_wrong_answers = $wrongAnswersHeader
    header_wrong_questions = $wrongQuestionsHeader
    rendered_question_blocks = $questionBlocks
    per_question_wrong_counts = @($wrongCounts)
    per_question_wrong_sum = $wrongSum
    explanation_id_count = $explanationIds.Count
    duplicate_explanation_ids = $duplicateExplanationIds
    checks = $checks
  }
}

function Write-Heartbeat([string]$Status, [int]$CandidateCount, [int]$ResultCount, [int]$ErrorCount) {
  Write-JsonFile -Path (Join-Path $AaysStatusDir 'runner-heartbeat-latest.json') -Object ([ordered]@{
    page_key=$PageKey
    layer=$LayerKey
    task_id=$TaskId
    status=$Status
    timestamp=(Get-Date).ToString('o')
    source_candidates=$CandidateCount
    result_files=$ResultCount
    error_count=$ErrorCount
    final_ready=$false
    fake_data=$false
  }) -Depth 10
}

$errors = New-Object System.Collections.ArrayList
$roots = New-Object System.Collections.ArrayList
$userProfile = $env:USERPROFILE
if (-not [string]::IsNullOrWhiteSpace($userProfile)) {
  Add-UniquePath $roots (Join-Path $userProfile 'Desktop')
  Add-UniquePath $roots (Join-Path $userProfile 'Documents')
  Add-UniquePath $roots (Join-Path $userProfile 'Downloads')
  Add-UniquePath $roots (Join-Path $userProfile 'OneDrive')
  Add-UniquePath $roots (Join-Path $userProfile 'source')
  Add-UniquePath $roots (Join-Path $userProfile 'Projects')
}
Add-UniquePath $roots 'C:\Projects'
Add-UniquePath $roots 'C:\src'
Add-UniquePath $roots 'D:\Projects'
Add-UniquePath $roots 'D:\src'

$markerPatterns = @(
  'Quiz\s+Ergebnis',
  'FALSCHE\+OPTION',
  'ALLE\s+FRAGEN',
  'quiz_result_',
  'Falsche\s+Antworten',
  'Falsche\s+Fragen',
  'Wortquiz',
  'Erklaerung:\s*No:',
  'kelimesinin\s+artikeli\s+nedir'
)
$riskPatterns = @(
  'current[_A-Za-z]*page\s*\+=\s*2',
  'page[_A-Za-z]*\s*=\s*page[_A-Za-z]*\s*\+\s*2',
  '\[\s*::\s*2\s*\]',
  'range\s*\([^\)]*,\s*2\s*\)',
  'shuffle',
  'random\.shuffle',
  'correct[_A-Za-z]*(index|option|answer)',
  'selected[_A-Za-z]*(index|option|answer)',
  'wrong[_A-Za-z]*(count|questions|answers|attempt)',
  'falsch[_A-Za-z]*(count|fragen|antwort)',
  'slice\s*\(',
  '\.skip\s*\(',
  '\.take\s*\('
)

$sourceExtensions = @('.py','.pyw','.js','.ts','.tsx','.jsx','.java','.kt','.cs','.cpp','.c','.h','.hpp','.html','.htm','.json','.yaml','.yml','.xml','.txt')
$excludePathRegex = '\\(AppData|node_modules|\.git|\.venv|venv|__pycache__|dist|build|Windows|Program Files|ProgramData|site-packages|packages)\\'
$candidatePaths = New-Object System.Collections.ArrayList
$resultPaths = New-Object System.Collections.ArrayList
Write-Heartbeat 'defans_mania_audit_started' 0 0 0

try {
  $rg = Get-Command rg -ErrorAction SilentlyContinue
  if ($null -ne $rg) {
    $globArgs = @('--hidden','--files-with-matches','--ignore-case','--max-filesize','5M')
    foreach ($ext in $sourceExtensions) { $globArgs += @('--glob',"*$ext") }
    $globArgs += @('--glob','!**/.git/**','--glob','!**/node_modules/**','--glob','!**/AppData/**','--glob','!**/.venv/**','--glob','!**/venv/**','--glob','!**/dist/**','--glob','!**/build/**')
    $combinedPattern = ($markerPatterns -join '|')
    foreach ($root in $roots) {
      try {
        $found = & $rg.Source @globArgs '--regexp' $combinedPattern $root 2>$null
        foreach ($path in @($found)) {
          if (-not [string]::IsNullOrWhiteSpace($path) -and (Test-Path -LiteralPath $path -PathType Leaf)) {
            if (-not $candidatePaths.Contains($path)) { [void]$candidatePaths.Add($path) }
          }
        }
        $results = & $rg.Source '--hidden' '--files' '--glob' 'quiz_result_*.txt' '--glob' '!**/.git/**' '--glob' '!**/AppData/**' $root 2>$null
        foreach ($path in @($results)) {
          if (-not [string]::IsNullOrWhiteSpace($path) -and (Test-Path -LiteralPath $path -PathType Leaf)) {
            if (-not $resultPaths.Contains($path)) { [void]$resultPaths.Add($path) }
          }
        }
      } catch { [void]$errors.Add([ordered]@{ step='ripgrep'; root=$root; error=$_.Exception.Message }) }
    }
  } else {
    foreach ($root in $roots) {
      try {
        $files = Get-ChildItem -LiteralPath $root -Recurse -File -ErrorAction SilentlyContinue | Where-Object {
          $_.FullName -notmatch $excludePathRegex -and $_.Length -le 5MB
        }
        foreach ($file in $files) {
          if ($file.Name -like 'quiz_result_*.txt' -and -not $resultPaths.Contains($file.FullName)) { [void]$resultPaths.Add($file.FullName) }
          if ($sourceExtensions -contains $file.Extension.ToLowerInvariant()) {
            try {
              if (Select-String -LiteralPath $file.FullName -Pattern $markerPatterns -Quiet -ErrorAction SilentlyContinue) {
                if (-not $candidatePaths.Contains($file.FullName)) { [void]$candidatePaths.Add($file.FullName) }
              }
            } catch {}
          }
        }
      } catch { [void]$errors.Add([ordered]@{ step='fallback_scan'; root=$root; error=$_.Exception.Message }) }
    }
  }

  $sourceAudits = New-Object System.Collections.ArrayList
  foreach ($path in @($candidatePaths | Sort-Object)) {
    try {
      $item = Get-Item -LiteralPath $path -ErrorAction Stop
      $hash = (Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash
      $markerMatches = Get-LineMatches -Path $path -Patterns $markerPatterns -MaxMatches 100
      $riskMatches = Get-LineMatches -Path $path -Patterns $riskPatterns -MaxMatches 160
      [void]$sourceAudits.Add([ordered]@{
        path=$item.FullName
        extension=$item.Extension
        size_bytes=$item.Length
        modified_at=$item.LastWriteTime.ToString('o')
        sha256=$hash
        marker_matches=$markerMatches
        risk_signal_matches=$riskMatches
      })
    } catch { [void]$errors.Add([ordered]@{ step='source_audit'; path=$path; error=$_.Exception.Message }) }
  }

  $resultAudits = New-Object System.Collections.ArrayList
  foreach ($path in @($resultPaths | Sort-Object)) {
    [void]$resultAudits.Add((Get-ResultAudit -Path $path))
  }

  $resultInconsistencies = @($resultAudits | Where-Object {
    $_.readable -eq $true -and (
      $_.checks.wrong_questions_matches_rendered_blocks -eq $false -or
      $_.checks.wrong_answers_matches_sum_of_per_question_counts -eq $false -or
      $_.checks.each_rendered_question_has_wrong_count -eq $false -or
      $_.checks.explanation_ids_are_unique -eq $false
    )
  })

  $statusName = if ($sourceAudits.Count -gt 0) { 'completed' } else { 'blocked_source_not_found' }
  $summary = [ordered]@{
    task_id=$TaskId
    page_key=$PageKey
    layer=$LayerKey
    status=$statusName
    started_at=$Now
    completed_at=(Get-Date).ToString('o')
    scanned_roots=@($roots)
    source_candidate_count=$sourceAudits.Count
    result_file_count=$resultAudits.Count
    inconsistent_result_file_count=$resultInconsistencies.Count
    source_candidates=@($sourceAudits)
    result_audits=@($resultAudits)
    inconsistent_results=@($resultInconsistencies)
    errors=@($errors)
    source_modified=$false
    external_write=$false
    fake_data=$false
    final_ready=$false
    next_action=if ($sourceAudits.Count -gt 0) { 'Open the highest-confidence source candidate, reproduce answer-evaluation and pagination defects, then patch with tests.' } else { 'Provide the Defans Mania source archive or exact local source directory; no matching source marker was found in the safe scan roots.' }
  }

  Write-JsonFile -Path (Join-Path $OutDir '001_quiz_logic_audit.json') -Object $summary -Depth 40
  Write-JsonFile -Path (Join-Path $StatusDir '001_quiz_logic_audit.status.json') -Object $summary -Depth 15
  Write-JsonFile -Path (Join-Path $AaysStatusDir "$TaskId`_$statusName.json") -Object $summary -Depth 15

  $candidateLines = if ($sourceAudits.Count -eq 0) { '- No source candidate found.' } else { ($sourceAudits | ForEach-Object { "- $($_.path) | modified=$($_.modified_at) | marker_hits=$(@($_.marker_matches).Count) | risk_hits=$(@($_.risk_signal_matches).Count)" }) -join "`n" }
  $resultLines = if ($resultAudits.Count -eq 0) { '- No quiz_result_*.txt files found.' } else { ($resultAudits | ForEach-Object { "- $($_.path) | header wrong answers=$($_.header_wrong_answers) | calculated=$($_.per_question_wrong_sum) | header wrong questions=$($_.header_wrong_questions) | rendered=$($_.rendered_question_blocks)" }) -join "`n" }

  @"
# Defans Mania quiz logic audit

status=$statusName
task_id=$TaskId
source_candidate_count=$($sourceAudits.Count)
result_file_count=$($resultAudits.Count)
inconsistent_result_file_count=$($resultInconsistencies.Count)
source_modified=false
external_write=false
fake_data=false
final_ready=false

## Source candidates
$candidateLines

## Saved result consistency
$resultLines

## Next action
$($summary.next_action)
"@ | Set-Content -LiteralPath (Join-Path $ReportDir '001_quiz_logic_audit.md') -Encoding UTF8

  Write-Heartbeat "defans_mania_audit_$statusName" $sourceAudits.Count $resultAudits.Count $errors.Count
  Write-Output "DEFANS_MANIA_AUDIT status=$statusName source_candidates=$($sourceAudits.Count) result_files=$($resultAudits.Count) inconsistent_results=$($resultInconsistencies.Count)"
  exit 0
}
catch {
  [void]$errors.Add([ordered]@{ step='fatal'; error=$_.Exception.Message })
  $blocked = [ordered]@{
    task_id=$TaskId
    page_key=$PageKey
    layer=$LayerKey
    status='blocked'
    blocked_at=(Get-Date).ToString('o')
    errors=@($errors)
    source_modified=$false
    external_write=$false
    fake_data=$false
    final_ready=$false
  }
  Write-JsonFile -Path (Join-Path $OutDir '001_quiz_logic_audit.json') -Object $blocked -Depth 30
  Write-JsonFile -Path (Join-Path $StatusDir '001_quiz_logic_audit.status.json') -Object $blocked -Depth 30
  Write-Heartbeat 'defans_mania_audit_blocked' 0 0 $errors.Count
  Write-Output "DEFANS_MANIA_AUDIT_BLOCKED task_id=$TaskId"
  exit 0
}
