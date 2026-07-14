$ErrorActionPreference = 'Stop'

$Repo = $env:AAYS_REPO_ROOT
if ([string]::IsNullOrWhiteSpace($Repo)) {
  try { $Repo = (git rev-parse --show-toplevel).Trim() }
  catch { $Repo = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..\..\..\..')).Path }
}

$TaskId = if ([string]::IsNullOrWhiteSpace($env:AAYS_TASK_ID)) { 'defans-mania-quiz-audit-20260714-001' } else { $env:AAYS_TASK_ID }
$LayerRoot = Join-Path $Repo 'docs\chatgpt_status\defans_mania'
$OutDir = Join-Path $LayerRoot 'runner_outputs'
$ReportDir = Join-Path $LayerRoot 'reports'
$StatusDir = Join-Path $LayerRoot 'status'
$AaysStatusDir = Join-Path $Repo 'docs\chatgpt_status\aays1\status'
New-Item -ItemType Directory -Force -Path $OutDir,$ReportDir,$StatusDir,$AaysStatusDir | Out-Null

function Write-Json([string]$Path, $Value, [int]$Depth = 40) {
  ($Value | ConvertTo-Json -Depth $Depth) | Set-Content -LiteralPath $Path -Encoding UTF8
}

function Add-ExistingRoot([System.Collections.ArrayList]$List, [string]$Path) {
  if ([string]::IsNullOrWhiteSpace($Path)) { return }
  try { $p = (Resolve-Path -LiteralPath $Path -ErrorAction Stop).Path } catch { return }
  if (-not $List.Contains($p)) { [void]$List.Add($p) }
}

function Get-Matches([string]$Path, [string[]]$Patterns, [int]$Limit = 120) {
  $items = New-Object System.Collections.ArrayList
  try {
    $n = 0
    foreach ($line in [System.IO.File]::ReadLines($Path)) {
      $n++
      foreach ($pattern in $Patterns) {
        if ($line -match $pattern) {
          [void]$items.Add([ordered]@{ line=$n; pattern=$pattern; text=$line.Trim() })
          break
        }
      }
      if ($items.Count -ge $Limit) { break }
    }
  } catch {}
  return @($items)
}

function Audit-ResultFile([string]$Path) {
  try { $raw = Get-Content -LiteralPath $Path -Raw -ErrorAction Stop }
  catch { return [ordered]@{ path=$Path; readable=$false; error=$_.Exception.Message } }

  $wrongAnswers = $null
  $wrongQuestions = $null
  $score = $null
  if ($raw -match '(?im)^Score:\s*(\d+)') { $score = [int]$Matches[1] }
  if ($raw -match '(?im)Falsche\s+Antworten:\s*(\d+)') { $wrongAnswers = [int]$Matches[1] }
  if ($raw -match '(?im)Falsche\s+Fragen:\s*(\d+)') { $wrongQuestions = [int]$Matches[1] }

  $blocks = [regex]::Matches($raw, '(?m)^\s*\d+\)\s+').Count
  $wrongMatches = [regex]::Matches($raw, '(?im)Falsch:\s*(\d+)x')
  $wrongCounts = @($wrongMatches | ForEach-Object { [int]$_.Groups[1].Value })
  $wrongSum = ($wrongCounts | Measure-Object -Sum).Sum
  if ($null -eq $wrongSum) { $wrongSum = 0 }

  $ids = @([regex]::Matches($raw, '(?im)Erklaerung:\s*No:([^\r\n]+)') | ForEach-Object { $_.Groups[1].Value.Trim() })
  $duplicates = @($ids | Group-Object | Where-Object Count -gt 1 | ForEach-Object { [ordered]@{ id=$_.Name; count=$_.Count } })
  $numbers = @([regex]::Matches($raw, '(?m)^\s*(\d+)\)\s+') | ForEach-Object { [int]$_.Groups[1].Value })
  $numberSequenceOk = $true
  for ($i=0; $i -lt $numbers.Count; $i++) { if ($numbers[$i] -ne ($i+1)) { $numberSequenceOk = $false; break } }

  return [ordered]@{
    path = $Path
    readable = $true
    modified_at = (Get-Item -LiteralPath $Path).LastWriteTime.ToString('o')
    score = $score
    header_wrong_answers = $wrongAnswers
    header_wrong_questions = $wrongQuestions
    rendered_question_blocks = $blocks
    rendered_question_numbers = $numbers
    per_question_wrong_counts = $wrongCounts
    per_question_wrong_sum = [int]$wrongSum
    duplicate_explanation_ids = $duplicates
    checks = [ordered]@{
      wrong_answers_matches_sum = if ($null -eq $wrongAnswers) { $null } else { $wrongAnswers -eq $wrongSum }
      wrong_questions_matches_blocks = if ($null -eq $wrongQuestions) { $null } else { $wrongQuestions -eq $blocks }
      each_block_has_wrong_count = $blocks -eq $wrongMatches.Count
      explanation_ids_unique = $duplicates.Count -eq 0
      rendered_numbers_are_contiguous = $numberSequenceOk
    }
  }
}

function Write-Heartbeat([string]$Status, [int]$Sources, [int]$Results, [int]$Errors) {
  Write-Json (Join-Path $AaysStatusDir 'runner-heartbeat-latest.json') ([ordered]@{
    page_key='aays1'; layer='defans_mania'; task_id=$TaskId; status=$Status
    timestamp=(Get-Date).ToString('o'); source_candidates=$Sources; result_files=$Results
    error_count=$Errors; final_ready=$false; fake_data=$false
  }) 10
}

$markerPatterns = @(
  'Quiz\s+Ergebnis','FALSCHE\+OPTION','ALLE\s+FRAGEN','quiz_result_',
  'Falsche\s+Antworten','Falsche\s+Fragen','Wortquiz','Erklaerung:\s*No:',
  'kelimesinin\s+artikeli\s+nedir'
)
$riskPatterns = @(
  '(current|result|quiz)?_?page\s*\+=\s*2','page\w*\s*=\s*page\w*\s*\+\s*2',
  '\[\s*::\s*2\s*\]','range\s*\([^\)]*,\s*2\s*\)','slice\s*\(',
  '\.skip\s*\(','\.take\s*\(','shuffle','random\.shuffle',
  'correct\w*(index|option|answer)','selected\w*(index|option|answer)',
  'wrong\w*(count|questions|answers|attempt)','falsch\w*(count|fragen|antwort)'
)
$extensions = @('.py','.pyw','.js','.ts','.tsx','.jsx','.java','.kt','.cs','.cpp','.c','.h','.hpp','.html','.htm','.json','.xml','.txt')
$exclude = '\\(AppData|node_modules|\.git|\.venv|venv|__pycache__|dist|build|Windows|Program Files|ProgramData|site-packages|packages)\\'

$roots = New-Object System.Collections.ArrayList
$profile = $env:USERPROFILE
foreach ($p in @(
  (Join-Path $profile 'Desktop'),(Join-Path $profile 'Documents'),(Join-Path $profile 'Downloads'),
  (Join-Path $profile 'Projects'),(Join-Path $profile 'source'),$Repo,(Split-Path -Parent $Repo),
  'C:\Projects','C:\src','D:\Projects','D:\src','E:\Projects','E:\src',
  'F:\TerraYield_AAYS_Portable','F:\Projects','F:\src'
)) { Add-ExistingRoot $roots $p }

$sourcePaths = New-Object System.Collections.ArrayList
$resultPaths = New-Object System.Collections.ArrayList
$errors = New-Object System.Collections.ArrayList
Write-Heartbeat 'defans_mania_audit_started' 0 0 0

try {
  $rg = Get-Command rg -ErrorAction SilentlyContinue
  if ($null -ne $rg) {
    $globs = @('--hidden','--files-with-matches','--ignore-case','--max-filesize','5M')
    foreach ($ext in $extensions) { $globs += @('--glob',"*$ext") }
    $globs += @('--glob','!**/.git/**','--glob','!**/node_modules/**','--glob','!**/AppData/**','--glob','!**/dist/**','--glob','!**/build/**')
    $combined = ($markerPatterns -join '|')
    foreach ($root in $roots) {
      try {
        foreach ($p in @(& $rg.Source @globs '--regexp' $combined $root 2>$null)) {
          if ((Test-Path -LiteralPath $p -PathType Leaf) -and -not $sourcePaths.Contains($p)) { [void]$sourcePaths.Add($p) }
        }
        foreach ($p in @(& $rg.Source '--hidden' '--files' '--glob' 'quiz_result_*.txt' '--glob' '!**/.git/**' '--glob' '!**/AppData/**' $root 2>$null)) {
          if ((Test-Path -LiteralPath $p -PathType Leaf) -and -not $resultPaths.Contains($p)) { [void]$resultPaths.Add($p) }
        }
      } catch { [void]$errors.Add([ordered]@{ step='rg'; root=$root; error=$_.Exception.Message }) }
    }
  } else {
    foreach ($root in $roots) {
      try {
        foreach ($file in Get-ChildItem -LiteralPath $root -Recurse -File -ErrorAction SilentlyContinue) {
          if ($file.FullName -match $exclude -or $file.Length -gt 5MB) { continue }
          if ($file.Name -like 'quiz_result_*.txt' -and -not $resultPaths.Contains($file.FullName)) { [void]$resultPaths.Add($file.FullName) }
          if ($extensions -contains $file.Extension.ToLowerInvariant()) {
            if (Select-String -LiteralPath $file.FullName -Pattern $markerPatterns -Quiet -ErrorAction SilentlyContinue) {
              if (-not $sourcePaths.Contains($file.FullName)) { [void]$sourcePaths.Add($file.FullName) }
            }
          }
        }
      } catch { [void]$errors.Add([ordered]@{ step='fallback'; root=$root; error=$_.Exception.Message }) }
    }
  }

  $sources = @($sourcePaths | Sort-Object | ForEach-Object {
    $item = Get-Item -LiteralPath $_
    [ordered]@{
      path=$item.FullName; modified_at=$item.LastWriteTime.ToString('o'); size_bytes=$item.Length
      sha256=(Get-FileHash -LiteralPath $_ -Algorithm SHA256).Hash
      marker_matches=Get-Matches $_ $markerPatterns 100
      risk_matches=Get-Matches $_ $riskPatterns 160
    }
  })
  $results = @($resultPaths | Sort-Object | ForEach-Object { Audit-ResultFile $_ })
  $failedResults = @($results | Where-Object {
    $_.readable -eq $false -or $_.checks.wrong_answers_matches_sum -eq $false -or
    $_.checks.wrong_questions_matches_blocks -eq $false -or $_.checks.each_block_has_wrong_count -eq $false -or
    $_.checks.explanation_ids_unique -eq $false -or $_.checks.rendered_numbers_are_contiguous -eq $false
  })

  $status = if ($sources.Count -gt 0) { 'completed' } else { 'blocked_source_not_found' }
  $output = [ordered]@{
    task_id=$TaskId; status=$status; completed_at=(Get-Date).ToString('o')
    searched_roots=@($roots); source_candidate_count=$sources.Count; result_file_count=$results.Count
    failed_result_audit_count=$failedResults.Count; source_candidates=$sources; result_audits=$results; errors=@($errors)
    source_modified=$false; fake_data=$false; final_ready=$false
  }
  Write-Json (Join-Path $OutDir '001_quiz_logic_audit.json') $output
  Write-Json (Join-Path $StatusDir '001_quiz_logic_audit.status.json') $output

  $lines = @('# Defans Mania quiz audit','',"status=$status","source_candidates=$($sources.Count)","result_files=$($results.Count)","failed_result_audits=$($failedResults.Count)",'source_modified=false','final_ready=false','')
  foreach ($s in $sources) { $lines += "- SOURCE: $($s.path) | risk_matches=$(@($s.risk_matches).Count) | sha256=$($s.sha256)" }
  foreach ($r in $failedResults) { $lines += "- RESULT_FAIL: $($r.path) | checks=$($r.checks | ConvertTo-Json -Compress)" }
  $lines | Set-Content -LiteralPath (Join-Path $ReportDir '001_quiz_logic_audit.md') -Encoding UTF8
  Write-Heartbeat "defans_mania_audit_$status" $sources.Count $results.Count $errors.Count
  Write-Output "DEFANS_MANIA_AUDIT status=$status sources=$($sources.Count) results=$($results.Count) failed=$($failedResults.Count)"
}
catch {
  $blocked = [ordered]@{ task_id=$TaskId; status='blocked_exception'; error=$_.Exception.Message; final_ready=$false; fake_data=$false }
  Write-Json (Join-Path $OutDir '001_quiz_logic_audit.json') $blocked
  Write-Json (Join-Path $StatusDir '001_quiz_logic_audit.status.json') $blocked
  Write-Heartbeat 'defans_mania_audit_blocked_exception' 0 0 1
  Write-Output "DEFANS_MANIA_AUDIT_BLOCKED error=$($_.Exception.Message)"
}
