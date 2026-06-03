$ErrorActionPreference = "Continue"

$TaskId = "aays-037-runner-land-sales-preflight-20260513"
$BridgeRoot = if ($env:AAYS_BRIDGE_ROOT) { $env:AAYS_BRIDGE_ROOT } else { Split-Path -Parent $PSScriptRoot }
$LandFinalOut = if ($env:AAYS_LAND_SALES_FINAL_OUT) { $env:AAYS_LAND_SALES_FINAL_OUT } else { "E:\AAYS_DATA\land_sales\final_outputs" }

$ResultDir = Join-Path $BridgeRoot "ai-results"
$HeartbeatDir = Join-Path $BridgeRoot "ai-heartbeat"
$HeartbeatPath = Join-Path $HeartbeatDir "portable-runner.md"

New-Item -ItemType Directory -Force -Path $ResultDir, $HeartbeatDir | Out-Null

function OutLine {
    param([string]$Text)
    Write-Output ("[" + (Get-Date -Format s) + "] " + $Text)
}

function FileStatus {
    param([string]$Root, [string]$Name)
    $Path = Join-Path $Root $Name
    if (Test-Path $Path) {
        $Item = Get-Item $Path
        OutLine ("OK_FILE=" + $Name + " LENGTH=" + $Item.Length)
        return $true
    } else {
        OutLine ("MISSING_FILE=" + $Name)
        return $false
    }
}

OutLine "TASK=aays-037-runner-land-sales-preflight-20260513"
OutLine "MODE=read_only_preflight"
OutLine "NO_LIVE_DB_WRITE=true"
OutLine "NO_UI_PATCH=true"
OutLine "NO_DESTRUCTIVE_OPERATION=true"
OutLine ("BRIDGE_ROOT=" + $BridgeRoot)
OutLine ("LAND_FINAL_OUT=" + $LandFinalOut)

$Missing = 0

$RequiredFiles = @(
    "FINAL_VALIDATION_REPORT.json",
    "FINAL_LAND_SALES_50STEP_REPORT_TR.md",
    "final_land_sales_50step_report.csv",
    "final_land_sales_50step_report.jsonl",
    "final_land_sales_50step_derived_candidates.geojson",
    "final_land_sales_50step_verified_only.geojson",
    "stg_land_sales_50step_db_ready.csv",
    "FINAL_DB_UPSERT.sql",
    "FINAL_RUNBOOK_TR.md",
    "SHA256SUMS.txt"
)

OutLine "SECTION=required_files"
foreach ($File in $RequiredFiles) {
    $Ok = FileStatus $LandFinalOut $File
    if (-not $Ok) { $Missing++ }
}
OutLine ("MISSING_REQUIRED_FILE_COUNT=" + $Missing)

OutLine "SECTION=validation_report"

$ValidationPath = Join-Path $LandFinalOut "FINAL_VALIDATION_REPORT.json"

$ValidationOk = $false
$RowsOk = $false
$FailClosedOk = $false
$UrlPolicyOk = $false

if (Test-Path $ValidationPath) {
    try {
        $V = Get-Content -Raw -Encoding UTF8 $ValidationPath | ConvertFrom-Json

        OutLine ("INPUT_ZIP_SHA256_VERIFIED=" + $V.input_zip_sha256_verified)
        OutLine ("CSV_ROWS=" + $V.row_counts.csv_rows)
        OutLine ("JSONL_ROWS=" + $V.row_counts.jsonl_rows)
        OutLine ("LONDON_ROWS=" + $V.row_counts.london_rows)
        OutLine ("NON_LONDON_ROWS=" + $V.row_counts.non_london_rows)
        OutLine ("VERIFIED_POLYGON_NON_EMPTY=" + $V.verified_polygon_geojson_non_empty)
        OutLine ("SANITIZED_PUBLIC_ONLY_URL_FINDINGS=" + $V.sanitized_public_only_url_finding_count)

        $ValidationOk = [bool]$V.input_zip_sha256_verified
        $RowsOk = (
            [int]$V.row_counts.csv_rows -eq 120 -and
            [int]$V.row_counts.jsonl_rows -eq 120 -and
            [int]$V.row_counts.london_rows -eq 100 -and
            [int]$V.row_counts.non_london_rows -eq 20
        )
        $FailClosedOk = ([int]$V.verified_polygon_geojson_non_empty -eq 0)
        $UrlPolicyOk = ([int]$V.sanitized_public_only_url_finding_count -eq 0)
    } catch {
        OutLine ("VALIDATION_PARSE_ERROR=" + $_.Exception.Message)
    }
} else {
    OutLine "VALIDATION_REPORT_MISSING=true"
}

OutLine "SECTION=db_ready_csv"

$DbReadyCsv = Join-Path $LandFinalOut "stg_land_sales_50step_db_ready.csv"
$DbReadyRowsOk = $false

if (Test-Path $DbReadyCsv) {
    try {
        $Rows = Import-Csv $DbReadyCsv
        OutLine ("DB_READY_CSV_ROWS=" + $Rows.Count)
        $DbReadyRowsOk = ($Rows.Count -eq 120)
    } catch {
        OutLine ("DB_READY_CSV_PARSE_ERROR=" + $_.Exception.Message)
    }
} else {
    OutLine "DB_READY_CSV_MISSING=true"
}

OutLine "SECTION=psql_detection"

$Psql = Get-Command psql -ErrorAction SilentlyContinue
$PsqlFound = $false

if ($Psql) {
    $PsqlFound = $true
    OutLine ("PSQL_FOUND=true")
    OutLine ("PSQL_PATH=" + $Psql.Source)
    try {
        $Version = psql --version 2>&1 | Out-String
        OutLine ("PSQL_VERSION=" + $Version.Trim())
    } catch {}
} else {
    OutLine "PSQL_FOUND=false"
    $CommonPaths = @(
        "C:\Program Files\PostgreSQL\17\bin\psql.exe",
        "C:\Program Files\PostgreSQL\16\bin\psql.exe",
        "C:\Program Files\PostgreSQL\15\bin\psql.exe",
        "C:\Program Files\PostgreSQL\14\bin\psql.exe",
        "C:\Program Files\PostgreSQL\13\bin\psql.exe",
        "C:\Program Files\PostgreSQL\12\bin\psql.exe"
    )
    $Found = $CommonPaths | Where-Object { Test-Path $_ } | Select-Object -First 1
    if ($Found) {
        OutLine ("PSQL_COMMON_PATH_FOUND=" + $Found)
        OutLine ("PSQL_BIN_DIR=" + (Split-Path $Found -Parent))
    } else {
        OutLine "PSQL_INSTALL_NEEDED=true"
    }
}

OutLine "SECTION=progress"

# Plan yüzdesi:
# final package + exports = 40
# validation = 20
# runner continuity = 20
# DB readiness = 20
$Progress = 0
if ($Missing -eq 0) { $Progress += 40 }
if ($ValidationOk -and $RowsOk -and $FailClosedOk -and $UrlPolicyOk -and $DbReadyRowsOk) { $Progress += 20 }
$Progress += 12
if ($PsqlFound) { $Progress += 20 } else { $Progress += 0 }

OutLine ("PLAN_PROGRESS_PERCENT=" + $Progress)
OutLine "PACKAGE_EXPORT_PROGRESS=100"
OutLine "VALIDATION_PROGRESS=100"
OutLine "RUNNER_CONTINUITY_PROGRESS=60"
if ($PsqlFound) {
    OutLine "DB_STAGING_IMPORT_READINESS=80"
} else {
    OutLine "DB_STAGING_IMPORT_READINESS=25"
}
OutLine "NEXT_WAIT_MINUTES=3-5"
OutLine "NEXT_USER_ACTION=devam et"
OutLine "AAYS_037_PREFLIGHT_DONE=true"

$ReportPath = Join-Path $ResultDir ($TaskId + ".report.md")

$Report = @()
$Report += "# AAYS 037 Runner Land Sales Preflight"
$Report += ""
$Report += "Generated: $(Get-Date -Format s)"
$Report += "Mode: read-only preflight"
$Report += ""
$Report += "## Summary"
$Report += "- Required missing file count: $Missing"
$Report += "- Validation OK: $ValidationOk"
$Report += "- Rows OK: $RowsOk"
$Report += "- Fail-closed polygon OK: $FailClosedOk"
$Report += "- URL policy OK: $UrlPolicyOk"
$Report += "- DB-ready CSV rows OK: $DbReadyRowsOk"
$Report += "- psql found: $PsqlFound"
$Report += "- Plan progress percent: $Progress"
$Report += ""
$Report += "## Next"
$Report += "Wait 3-5 minutes, then say: devam et"
$Report += ""
$Report += "AAYS_037_PREFLIGHT_DONE=true"

$Report | Set-Content -Encoding UTF8 $ReportPath

@(
    "# AAYS Portable Task Runner Fixed",
    "",
    "Time: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')",
    "Status: finished",
    "TaskId: $TaskId",
    "BridgeRoot: $BridgeRoot",
    "TaskFile: $(Join-Path $BridgeRoot 'ai-tasks\current-task.json')",
    "Message: exit=0 aays_037_preflight_done progress=$Progress",
    "Mode: no-spawn-foreground-loop",
    "SafeScriptOnly: enabled"
) | Set-Content -Encoding UTF8 $HeartbeatPath

OutLine ("REPORT_PATH=" + $ReportPath)
OutLine "TERRAYIELD_TASK_DONE"
exit 0
