$ErrorActionPreference = 'Continue'

$BridgeRoot = 'C:\AAYS1_GITHUB_BRIDGE\chat_gpt_clone_1'
$Backend = 'C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence'
$Frontend = 'C:\Users\cagda\Documents\GitHub\AAYS\england_map_web'
$PlannedDataRoot = 'E:\AAYS_DATA\planlanan yapılar'
$ResultsDir = Join-Path $BridgeRoot 'ai-results'
$QualityReportsDir = Join-Path $PlannedDataRoot '10_quality_reports'
$TaskId = 'terrayield-050-future-growth-stage3-insertion-audit'

New-Item -ItemType Directory -Force -Path $ResultsDir | Out-Null
New-Item -ItemType Directory -Force -Path $QualityReportsDir | Out-Null

$SkipDirs = @('.git','node_modules','.next','dist','build','__pycache__','.pytest_cache','.mypy_cache','.venv','venv','env','.tmp','tmp','temp')

function Safe-TestPath($Path) { try { return Test-Path -Path $Path } catch { return $false } }

function Safe-GitStatus($Path) {
  if (-not (Safe-TestPath $Path)) { return [ordered]@{ status='PATH_NOT_FOUND'; exit_code=$null; output='' } }
  try {
    Push-Location $Path
    $raw = git status --short --untracked-files=no 2>&1
    $code = $LASTEXITCODE
    Pop-Location
    if ($code -eq 0) {
      if ($raw) { return [ordered]@{ status='HAS_TRACKED_CHANGES'; exit_code=$code; output=($raw -join "`n") } }
      return [ordered]@{ status='CLEAN'; exit_code=$code; output='CLEAN' }
    }
    return [ordered]@{ status='GIT_STATUS_FAILED_NON_BLOCKING'; exit_code=$code; output=($raw -join "`n") }
  } catch {
    try { Pop-Location } catch {}
    return [ordered]@{ status='GIT_STATUS_EXCEPTION_NON_BLOCKING'; exit_code=$null; output=$_.Exception.Message }
  }
}

function Get-FilesSafe($Root, $Extensions, $Max = 600) {
  $items = New-Object System.Collections.Generic.List[object]
  if (-not (Safe-TestPath $Root)) { return @() }
  try {
    $stack = New-Object System.Collections.Stack
    $stack.Push((Get-Item -Path $Root))
    while ($stack.Count -gt 0 -and $items.Count -lt $Max) {
      $current = $stack.Pop()
      foreach ($child in Get-ChildItem -Path $current.FullName -Force -ErrorAction SilentlyContinue) {
        if ($child.PSIsContainer) {
          if ($SkipDirs -notcontains $child.Name) { $stack.Push($child) }
        } else {
          if ($Extensions -contains $child.Extension.ToLowerInvariant()) {
            $rel = $child.FullName.Substring($Root.Length).TrimStart('\')
            $items.Add([ordered]@{ name=$child.Name; path=$child.FullName; relative_path=$rel; extension=$child.Extension; length=$child.Length; last_write_time=$child.LastWriteTime.ToString('s') })
          }
        }
        if ($items.Count -ge $Max) { break }
      }
    }
  } catch {}
  return @($items | Sort-Object relative_path -Unique)
}

function Search-FileContent($Files, $Patterns, $MaxMatches = 80) {
  $matches = New-Object System.Collections.Generic.List[object]
  foreach ($file in $Files) {
    if ($matches.Count -ge $MaxMatches) { break }
    try {
      $text = Get-Content -Path $file.path -Raw -ErrorAction SilentlyContinue
      if (-not $text) { continue }
      foreach ($pattern in $Patterns) {
        if ($text -match $pattern) {
          $matches.Add([ordered]@{ pattern=$pattern; relative_path=$file.relative_path; path=$file.path })
          break
        }
      }
    } catch {}
  }
  return @($matches)
}

$BackendFiles = Get-FilesSafe -Root $Backend -Extensions @('.py','.json','.toml','.yaml','.yml','.md','.txt','.env','.example') -Max 900
$PythonFiles = @($BackendFiles | Where-Object { $_.extension -eq '.py' })

$FrameworkSignals = [ordered]@{
  fastapi = @(Search-FileContent -Files $PythonFiles -Patterns @('from\s+fastapi\s+import','import\s+fastapi','FastAPI\(') -MaxMatches 40)
  flask = @(Search-FileContent -Files $PythonFiles -Patterns @('from\s+flask\s+import','Flask\(') -MaxMatches 40)
  django = @(Search-FileContent -Files $PythonFiles -Patterns @('django\.','from\s+django','DJANGO_SETTINGS_MODULE') -MaxMatches 40)
  sqlalchemy = @(Search-FileContent -Files $PythonFiles -Patterns @('sqlalchemy','declarative_base','SessionLocal','create_engine') -MaxMatches 40)
  pydantic = @(Search-FileContent -Files $PythonFiles -Patterns @('BaseModel','pydantic') -MaxMatches 40)
  geospatial = @(Search-FileContent -Files $PythonFiles -Patterns @('geopandas','shapely','geoalchemy','postgis','geometry','Point\(','Polygon\(') -MaxMatches 40)
}

$PathSignals = [ordered]@{
  api_like = @($BackendFiles | Where-Object { $_.relative_path -match '(api|route|router|endpoint|controller)' } | Select-Object -First 80)
  model_like = @($BackendFiles | Where-Object { $_.relative_path -match '(model|schema|entity|database|db|sqlalchemy)' } | Select-Object -First 80)
  service_like = @($BackendFiles | Where-Object { $_.relative_path -match '(service|pipeline|processor|ingest|collector|connector)' } | Select-Object -First 80)
  test_like = @($BackendFiles | Where-Object { $_.relative_path -match '(test_|_test|tests|pytest)' } | Select-Object -First 80)
  config_like = @($BackendFiles | Where-Object { $_.relative_path -match '(config|settings|env|pyproject|requirements)' } | Select-Object -First 80)
}

$RecommendedPackageRoot = 'future_growth'
$ExistingFutureGrowth = @($BackendFiles | Where-Object { $_.relative_path -match '(future_growth|future-growth|planned|development|infrastructure)' } | Select-Object -First 80)

$InsertionPlan = [ordered]@{
  preferred_minimal_backend_package = $RecommendedPackageRoot
  proposed_files = @(
    'future_growth/__init__.py',
    'future_growth/connectors/__init__.py',
    'future_growth/connectors/base.py',
    'future_growth/evidence.py',
    'future_growth/timeline.py'
  )
  rationale = 'Create an isolated package first. Do not wire into API/routes/database until framework insertion points are confirmed and tests are added.'
  no_fake_data_rule = 'Connector interfaces must require source_url/source_name/retrieved_at/evidence_summary and must not include hardcoded demo records.'
  timeline_rule = 'Exact dates remain exact only when present in source; otherwise use estimated language and carry evidence text.'
}

$Audit = [ordered]@{
  task_id = $TaskId
  status = 'completed'
  generated_at = (Get-Date).ToString('s')
  scope = 'Read-only Stage3 insertion point audit. No backend/frontend source changes.'
  paths = [ordered]@{
    backend_exists = Safe-TestPath $Backend
    frontend_exists = Safe-TestPath $Frontend
    planned_data_root_exists = Safe-TestPath $PlannedDataRoot
    bridge_root_exists = Safe-TestPath $BridgeRoot
  }
  git_status = [ordered]@{
    backend = Safe-GitStatus $Backend
    frontend = Safe-GitStatus $Frontend
    bridge = Safe-GitStatus $BridgeRoot
  }
  counts = [ordered]@{
    backend_files_sampled = $BackendFiles.Count
    python_files_sampled = $PythonFiles.Count
  }
  framework_signals = $FrameworkSignals
  path_signals = $PathSignals
  existing_future_growth_related_files = $ExistingFutureGrowth
  insertion_plan = $InsertionPlan
  policy = [ordered]@{
    no_repo_source_changes = $true
    fake_data_allowed = $false
    hardcoded_demo_data_allowed = $false
    official_structured_sources_priority = $true
    evidence_required_for_scores_and_timelines = $true
    estimated_language_required_when_exact_dates_missing = $true
  }
  recommended_next_step = 'Create the isolated future_growth package skeleton only, with evidence/timeline dataclasses and connector protocol. Do not wire to API/database yet.'
}

$AuditJson = Join-Path $ResultsDir "$TaskId.audit.json"
$ReportPath = Join-Path $ResultsDir "$TaskId.report.md"
$ExternalReport = Join-Path $QualityReportsDir "$TaskId.report.md"

$Audit | ConvertTo-Json -Depth 14 | Set-Content -Path $AuditJson -Encoding UTF8

$ReportLines = @(
  '# TerraYield Future Growth Stage3 Insertion Audit',
  '',
  "Generated at: $($Audit.generated_at)",
  '',
  '## Scope',
  '',
  'Read-only insertion point audit. No backend/frontend source code was modified.',
  '',
  '## Counts',
  '',
  "- Backend files sampled: $($BackendFiles.Count)",
  "- Python files sampled: $($PythonFiles.Count)",
  '',
  '## Recommended Insertion Plan',
  '',
  "- Preferred package: $($InsertionPlan.preferred_minimal_backend_package)",
  '- Proposed files:',
  '  - future_growth/__init__.py',
  '  - future_growth/connectors/__init__.py',
  '  - future_growth/connectors/base.py',
  '  - future_growth/evidence.py',
  '  - future_growth/timeline.py',
  '',
  '## Policy',
  '',
  '- No fake data.',
  '- No hardcoded demo data.',
  '- Evidence required for scores and timelines.',
  '- Use estimated language when exact dates are missing.',
  '',
  '## Recommended Next Step',
  '',
  $Audit.recommended_next_step
)

$ReportLines | Set-Content -Path $ReportPath -Encoding UTF8
Copy-Item -Path $ReportPath -Destination $ExternalReport -Force

Write-Host 'STAGE3_INSERTION_AUDIT_COMPLETE'
exit 0
