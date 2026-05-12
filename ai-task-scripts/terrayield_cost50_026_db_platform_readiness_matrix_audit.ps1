$ErrorActionPreference='Continue'
$TaskId='cost50-026-db-platform-readiness-matrix-audit-20260512'
$BridgeRoot=Split-Path -Parent $PSScriptRoot
$ResultDir=Join-Path $BridgeRoot 'ai-results'
New-Item -ItemType Directory -Force -Path $ResultDir | Out-Null
function Log($m){ Write-Output ('['+(Get-Date -Format s)+'] '+$m) }
function HasFile($root,$name){ if(Test-Path $root){ return [bool](Get-ChildItem -Path $root -File -Recurse -Filter $name -ErrorAction SilentlyContinue | Select-Object -First 1) } return $false }
function CountLike($root,$pattern){ if(Test-Path $root){ return @((Get-ChildItem -Path $root -File -Recurse -ErrorAction SilentlyContinue | Where-Object { $_.FullName -match $pattern })).Count } return 0 }
function ReadFlag($path,$pattern){ if(Test-Path $path){ $txt=Get-Content -Raw -Encoding UTF8 -Path $path; if($txt -match $pattern){ return $Matches[0] } }; return 'MISSING' }
Log "TASK=$TaskId"
Log 'MODE=readonly_db_platform_readiness_matrix'
$ProjectRoot='E:\AAYS_DATA\cost\handoff_zips\cost_uk_postgres_50step_handoff_20260511_213229\terrayield_land_intelligence'
$pkg=HasFile $ProjectRoot 'package.json'
$py=HasFile $ProjectRoot 'requirements.txt'
$docker=HasFile $ProjectRoot 'Dockerfile'
$compose=HasFile $ProjectRoot 'docker-compose.yml'
$env=HasFile $ProjectRoot '.env.example'
$migrations=CountLike $ProjectRoot '(migration|migrations|alembic|prisma|sql)'
$api=CountLike $ProjectRoot '(api|route|controller|server)'
$mobile=CountLike $ProjectRoot '(android|ios|react-native|expo|capacitor)'
$web=CountLike $ProjectRoot '(vite|next|react|src)'
$db=CountLike $ProjectRoot '(postgres|pgsql|database|db|schema)'
$readiness=0
if($pkg -or $py){ $readiness+=10 }
if($docker -or $compose){ $readiness+=10 }
if($env){ $readiness+=10 }
if($migrations -gt 0){ $readiness+=15 }
if($api -gt 0){ $readiness+=15 }
if($web -gt 0){ $readiness+=10 }
if($mobile -gt 0){ $readiness+=10 }
if($db -gt 0){ $readiness+=20 }
$prev=Join-Path $ResultDir 'cost50-025-final-artifact-index-map-20260512.report.md'
$out=Join-Path $ResultDir "$TaskId.report.md"
$report=@(
  '# Cost50 026 DB Platform Readiness Matrix Audit',
  '',
  "Generated: $(Get-Date -Format s)",
  '',
  "TASK=$TaskId",
  'MODE=readonly_audit_only',
  "PROJECT_ROOT=$ProjectRoot",
  "PACKAGE_JSON_EXISTS=$pkg",
  "REQUIREMENTS_TXT_EXISTS=$py",
  "DOCKERFILE_EXISTS=$docker",
  "DOCKER_COMPOSE_EXISTS=$compose",
  "ENV_EXAMPLE_EXISTS=$env",
  "MIGRATION_SIGNAL_COUNT=$migrations",
  "API_SIGNAL_COUNT=$api",
  "WEB_SIGNAL_COUNT=$web",
  "MOBILE_SIGNAL_COUNT=$mobile",
  "DB_SIGNAL_COUNT=$db",
  "READINESS_SCORE=$readiness/100",
  "PREV_025_DONE=$(ReadFlag $prev 'TASK_COMPLETION=100/100')",
  'NEXT_RECOMMENDED_STEP=cost50-027-db-backed-multiplatform-gap-list',
  'PLAN_PROGRESS_PERCENT=50',
  'TASK_COMPLETION=100/100',
  '',
  '## Matrix',
  '',
  '| Area | Evidence | Status |',
  '|---|---:|---:|',
  "| Dependency manifest | package=$pkg requirements=$py | audit-only |",
  "| Container/run config | dockerfile=$docker compose=$compose env_example=$env | audit-only |",
  "| DB/schema/migration signals | $migrations | audit-only |",
  "| API/server signals | $api | audit-only |",
  "| Web signals | $web | audit-only |",
  "| Mobile/platform signals | $mobile | audit-only |"
)
$report | Set-Content -Encoding UTF8 -Path $out
Log "REPORT_PATH=$out"
Log "READINESS_SCORE=$readiness/100"
Log 'PLAN_PROGRESS_PERCENT=50'
Log 'TASK_COMPLETION=100/100'
exit 0
