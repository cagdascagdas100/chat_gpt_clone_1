$ErrorActionPreference = "Continue"

$BridgeRoot = "C:\AAYS1_GITHUB_BRIDGE\chat_gpt_clone_1"
$WorkspaceRoot = "C:\Users\cagda\Documents\GitHub\AAYS"
$BackendRoot = Join-Path $WorkspaceRoot "terrayield_land_intelligence"
$FrontendRoot = Join-Path $WorkspaceRoot "england_map_web"
$ResultsDir = Join-Path $BridgeRoot "ai-results"
$ResultPath = Join-Path $ResultsDir "ty144-discover-service-commands.result.json"
$ReportPath = Join-Path $ResultsDir "ty144-discover-service-commands.report.md"
New-Item -ItemType Directory -Force -Path $ResultsDir | Out-Null

function Read-TextSafe {
  param([string]$Path, [int]$MaxChars = 12000)
  if (-not (Test-Path $Path)) { return $null }
  try {
    $text = Get-Content -Path $Path -Raw -ErrorAction Stop
    $text = $text -replace '(?i)(password|token|api[_-]?key|secret|database_url)\s*[:=]\s*[^\r\n,]+', '$1_PRESENT_REDACTED'
    if ($text.Length -gt $MaxChars) { return $text.Substring(0, $MaxChars) }
    return $text
  } catch { return $null }
}

function Test-CommandSafe {
  param([string]$CommandName)
  return [bool](Get-Command $CommandName -ErrorAction SilentlyContinue)
}

function Get-FileListSafe {
  param([string]$Root, [int]$Depth = 2)
  if (-not (Test-Path $Root)) { return @() }
  try {
    return Get-ChildItem -Path $Root -File -Recurse -ErrorAction SilentlyContinue |
      Where-Object { $_.FullName -notmatch '\\(\.git|node_modules|\.venv|venv|__pycache__|dist|build)\\' } |
      Select-Object -First 120 -ExpandProperty FullName
  } catch { return @() }
}

$BackendFiles = [ordered]@{
  pyproject = Read-TextSafe (Join-Path $BackendRoot "pyproject.toml")
  requirements = Read-TextSafe (Join-Path $BackendRoot "requirements.txt")
  package_json = Read-TextSafe (Join-Path $BackendRoot "package.json")
  main_py_exists = Test-Path (Join-Path $BackendRoot "app\main.py")
  app_py_exists = Test-Path (Join-Path $BackendRoot "app.py")
  manage_py_exists = Test-Path (Join-Path $BackendRoot "manage.py")
  docker_compose_exists = Test-Path (Join-Path $WorkspaceRoot "docker-compose.yml")
}

$FrontendFiles = [ordered]@{
  package_json = Read-TextSafe (Join-Path $FrontendRoot "package.json")
  vite_config_exists = (Test-Path (Join-Path $FrontendRoot "vite.config.js")) -or (Test-Path (Join-Path $FrontendRoot "vite.config.ts"))
  next_config_exists = (Test-Path (Join-Path $FrontendRoot "next.config.js")) -or (Test-Path (Join-Path $FrontendRoot "next.config.mjs"))
}

$CandidateBackendCommands = @()
if ($BackendFiles.main_py_exists) { $CandidateBackendCommands += "python -m uvicorn app.main:app --host 127.0.0.1 --port 8010" }
if ($BackendFiles.manage_py_exists) { $CandidateBackendCommands += "python manage.py runserver 127.0.0.1:8010" }
if ($BackendFiles.docker_compose_exists) { $CandidateBackendCommands += "docker compose up -d db" }

$CandidateFrontendCommands = @()
if ($FrontendFiles.package_json) { $CandidateFrontendCommands += "npm install"; $CandidateFrontendCommands += "npm run dev -- --host 127.0.0.1 --port 3000" }

$Audit = [ordered]@{
  task_id = "ty144-discover-service-commands"
  status = "completed"
  generated_at = (Get-Date).ToString("s")
  secrets_values_logged = $false
  tools = [ordered]@{
    python = Test-CommandSafe "python"
    py = Test-CommandSafe "py"
    node = Test-CommandSafe "node"
    npm = Test-CommandSafe "npm"
    docker = Test-CommandSafe "docker"
  }
  paths = [ordered]@{
    workspace_root = $WorkspaceRoot
    workspace_exists = Test-Path $WorkspaceRoot
    backend_root = $BackendRoot
    backend_exists = Test-Path $BackendRoot
    frontend_root = $FrontendRoot
    frontend_exists = Test-Path $FrontendRoot
  }
  backend_files = $BackendFiles
  frontend_files = $FrontendFiles
  backend_sample_files = Get-FileListSafe $BackendRoot
  frontend_sample_files = Get-FileListSafe $FrontendRoot
  candidate_backend_commands = $CandidateBackendCommands
  candidate_frontend_commands = $CandidateFrontendCommands
  recommended_next_step = "Run start command manually in visible PowerShell after reviewing candidate commands."
}

$Audit | ConvertTo-Json -Depth 20 | Set-Content -Path $ResultPath -Encoding UTF8

$Report = @(
  "# TY144 Discover Service Commands",
  "",
  "- Status: completed",
  "- Secrets logged: false",
  "- Backend exists: $($Audit.paths.backend_exists)",
  "- Frontend exists: $($Audit.paths.frontend_exists)",
  "- Python available: $($Audit.tools.python)",
  "- Node available: $($Audit.tools.node)",
  "- NPM available: $($Audit.tools.npm)",
  "- Docker available: $($Audit.tools.docker)",
  "",
  "## Candidate Backend Commands",
  ($CandidateBackendCommands | ForEach-Object { "- $_" }),
  "",
  "## Candidate Frontend Commands",
  ($CandidateFrontendCommands | ForEach-Object { "- $_" }),
  "",
  "## Output",
  "- Result JSON: $ResultPath"
)
$Report | Set-Content -Path $ReportPath -Encoding UTF8
Write-Host "TY144_DISCOVER_SERVICE_COMMANDS_COMPLETE"
exit 0
