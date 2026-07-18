[CmdletBinding()]
param(
    [string]$BaseUrl = "http://127.0.0.1:8012",
    [int]$VirtualTimeBudgetMs = 8000
)

$ErrorActionPreference = "Stop"
$chromeCandidates = @(
    "C:\Program Files\Google\Chrome\Application\chrome.exe",
    "C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
)
$chrome = $chromeCandidates | Where-Object { Test-Path -LiteralPath $_ } | Select-Object -First 1
if (-not $chrome) {
    throw "Chrome or Edge was not found."
}

$pages = @(
    [pscustomobject]@{ Name = "main"; Path = "/england_map_web/index.html" },
    [pscustomobject]@{ Name = "matrix"; Path = "/england_map_web/TerraYield_England_Program_Parcel_Layer_Matrix_20260629.html?refresh=audit" },
    [pscustomobject]@{ Name = "geometry_ai"; Path = "/england_map_web/geometry_review_3of4_columns_1264.html?refresh=audit" }
)

$auditRoot = Join-Path $env:TEMP ("aays_browser_audit_" + [guid]::NewGuid().ToString("N"))
New-Item -ItemType Directory -Path $auditRoot -Force | Out-Null

try {
    $results = foreach ($page in $pages) {
        $profile = Join-Path $auditRoot ("profile_" + $page.Name)
        $domPath = Join-Path $auditRoot ($page.Name + ".html")
        $errorPath = Join-Path $auditRoot ($page.Name + ".stderr.txt")
        $url = $BaseUrl.TrimEnd("/") + $page.Path
        $httpStatus = $null
        $httpError = $null

        try {
            $response = Invoke-WebRequest -Uri $url -UseBasicParsing -TimeoutSec 20
            $httpStatus = [int]$response.StatusCode
        } catch {
            $httpError = $_.Exception.Message
            if ($_.Exception.Response) {
                $httpStatus = [int]$_.Exception.Response.StatusCode
            }
        }

        $arguments = @(
            "--headless=new",
            "--disable-gpu",
            "--disable-extensions",
            "--no-first-run",
            "--no-default-browser-check",
            "--user-data-dir=$profile",
            "--virtual-time-budget=$VirtualTimeBudgetMs",
            "--dump-dom",
            $url
        )
        $browserProcess = Start-Process -FilePath $chrome -ArgumentList $arguments -WindowStyle Hidden -Wait -PassThru -RedirectStandardOutput $domPath -RedirectStandardError $errorPath
        $exitCode = $browserProcess.ExitCode
        [string]$dom = if (Test-Path -LiteralPath $domPath) { Get-Content -LiteralPath $domPath -Raw -Encoding UTF8 } else { "" }
        [string]$stderr = if (Test-Path -LiteralPath $errorPath) { Get-Content -LiteralPath $errorPath -Raw -Encoding UTF8 } else { "" }

        $title = if ($dom -match "(?is)<title[^>]*>(.*?)</title>") { $matches[1] } else { $null }
        $loadState = if ($dom -match 'data-load-state="([^"]+)"') { $matches[1] } else { $null }
        $loadMode = if ($dom -match 'data-load-mode="([^"]+)"') { $matches[1] } else { $null }
        $tableRows = ([regex]::Matches($dom, "(?is)<tr(?:\s|>)")).Count
        $mapShapes = ([regex]::Matches($dom, 'class="[^"]*leaflet-interactive')).Count
        $plainText = [regex]::Replace($dom, "(?is)<script.*?</script>|<style.*?</style>|<[^>]+>", " ")
        $plainText = [System.Net.WebUtility]::HtmlDecode(([regex]::Replace($plainText, "\s+", " ")).Trim())

        [pscustomobject]@{
            name = $page.Name
            url = $url
            http_status = $httpStatus
            http_error = $httpError
            browser_exit_code = $exitCode
            title = $title
            load_state = $loadState
            load_mode = $loadMode
            table_rows_in_dom = $tableRows
            map_shapes_in_dom = $mapShapes
            visible_text_sample = $plainText.Substring(0, [Math]::Min(1200, $plainText.Length))
            browser_error_sample = $stderr.Substring(0, [Math]::Min(800, $stderr.Length))
        }
    }
    $results | ConvertTo-Json -Depth 5
} finally {
    if ((Resolve-Path -LiteralPath $auditRoot).Path.StartsWith((Resolve-Path -LiteralPath $env:TEMP).Path, [System.StringComparison]::OrdinalIgnoreCase)) {
        Remove-Item -LiteralPath $auditRoot -Recurse -Force -ErrorAction SilentlyContinue
    }
}
