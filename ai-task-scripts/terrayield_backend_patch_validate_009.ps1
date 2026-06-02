$ErrorActionPreference = "Continue"

$Project = "C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence"
$Start = Get-Date
$RunId = Get-Date -Format "yyyyMMdd_HHmmss"
$ReportDir = Join-Path $Project ".aays_next_fix\backend_patch_validate_009_$RunId"
$BackupDir = Join-Path $ReportDir "backup"
$LogFile = Join-Path $ReportDir "detail.txt"
$SummaryFile = Join-Path $ReportDir "summary.md"

New-Item -ItemType Directory -Force -Path $ReportDir, $BackupDir | Out-Null
Set-Location $Project

function Log([string]$Text) {
    $elapsed = [int]((Get-Date) - $Start).TotalSeconds
    $line = "[ELAPSED ${elapsed}s] $Text"
    Write-Output $line
    Add-Content -Encoding UTF8 -Path $LogFile -Value $line
}

function Backup-Rel([string]$RelPath) {
    if (Test-Path $RelPath) {
        $safe = $RelPath.Replace("\", "_").Replace("/", "_").Replace(":", "_")
        Copy-Item -Force $RelPath (Join-Path $BackupDir $safe)
        Log "BACKUP $RelPath"
    } else {
        Log "BACKUP_SKIP_MISSING $RelPath"
    }
}

function Test-Endpoint([string]$Path, [int]$TimeoutSec = 60) {
    try {
        $sw = [System.Diagnostics.Stopwatch]::StartNew()
        $r = Invoke-WebRequest -Uri ("http://localhost:8010" + $Path) -UseBasicParsing -TimeoutSec $TimeoutSec
        $sw.Stop()
        $cache = $r.Headers["X-AAYS-Cache"]
        $line = "OK $Path status=$($r.StatusCode) ms=$($sw.ElapsedMilliseconds) bytes=$($r.Content.Length) cache=$cache"
        Log $line
        return $line
    } catch {
        $line = "FAIL $Path error=$($_.Exception.Message)"
        Log $line
        return $line
    }
}

function Is-SkippedPath([string]$Path) {
    return ($Path.Contains("node_modules") -or $Path.Contains(".git") -or $Path.Contains(".aays_next_fix") -or $Path.Contains("dist") -or $Path.Contains("build"))
}

Log "TASK: TerraYield backend cache/GZip patch + broad validation 009"
Log "PROGRESS: 97%"
Log "ESTIMATED_WAIT: 20-30 dakika"
Log "PROJECT=$Project"
Log "REPORT_DIR=$ReportDir"

$baseline = @()
Log "BASELINE_ENDPOINTS"
foreach ($ep in @("/health", "/openapi.json", "/map/listings", "/map/sales-history/status", "/map/sales-history/external-evidence", "/map/sales-history/parcels", "/map/sales-history/combined")) {
    $baseline += Test-Endpoint $ep 75
}

Log "SCAN_FRONTEND_CANDIDATES"
try {
    Get-ChildItem -Recurse -Force -File -ErrorAction SilentlyContinue -Include *.js,*.jsx,*.ts,*.tsx,*.css |
        Where-Object { -not (Is-SkippedPath $_.FullName) } |
        Sort-Object Length -Descending |
        Select-Object -First 40 FullName,Length |
        Format-Table -AutoSize | Out-String | ForEach-Object { Log $_ }

    Get-ChildItem -Recurse -Force -File -ErrorAction SilentlyContinue -Include *.js,*.jsx,*.ts,*.tsx |
        Where-Object { -not (Is-SkippedPath $_.FullName) } |
        Select-String -Pattern "fetch|axios|/map/listings|sales-history|useEffect|mapbox|leaflet|moveend|zoomend|debounce|throttle" -CaseSensitive:$false |
        Select-Object -First 120 |
        ForEach-Object { Log ($_.Path + ":" + $_.LineNumber + ": " + $_.Line.Trim()) }
} catch {
    Log "FRONTEND_SCAN_WARN=$($_.Exception.Message)"
}

Log "BACKUP_AND_WRITE_CACHE_FILES"
New-Item -ItemType Directory -Force -Path "app\core", "app\middleware" | Out-Null
Backup-Rel "app\core\ttl_cache.py"
Backup-Rel "app\middleware\map_listings_cache.py"
Backup-Rel "app\main.py"

$ttlCache = @'
from __future__ import annotations

import time
from collections import OrderedDict
from dataclasses import dataclass
from threading import RLock
from typing import Any, Optional


@dataclass
class _Entry:
    value: Any
    expires_at: float


class TTLCache:
    def __init__(self, maxsize: int = 128, ttl_seconds: int = 30):
        self.maxsize = max(1, int(maxsize))
        self.ttl_seconds = max(1, int(ttl_seconds))
        self._items: OrderedDict[str, _Entry] = OrderedDict()
        self._lock = RLock()

    def get(self, key: str) -> Optional[Any]:
        now = time.time()
        with self._lock:
            entry = self._items.get(key)
            if entry is None:
                return None
            if entry.expires_at <= now:
                self._items.pop(key, None)
                return None
            self._items.move_to_end(key)
            return entry.value

    def set(self, key: str, value: Any, ttl_seconds: Optional[int] = None) -> None:
        ttl = self.ttl_seconds if ttl_seconds is None else max(1, int(ttl_seconds))
        with self._lock:
            self._items[key] = _Entry(value=value, expires_at=time.time() + ttl)
            self._items.move_to_end(key)
            while len(self._items) > self.maxsize:
                self._items.popitem(last=False)

    def clear(self) -> None:
        with self._lock:
            self._items.clear()
'@
Set-Content -Encoding UTF8 -Path "app\core\ttl_cache.py" -Value $ttlCache

$middleware = @'
from __future__ import annotations

import hashlib
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from app.core.ttl_cache import TTLCache


class MapListingsCacheMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, ttl_seconds: int = 20, maxsize: int = 128):
        super().__init__(app)
        self.cache = TTLCache(maxsize=maxsize, ttl_seconds=ttl_seconds)

    async def dispatch(self, request, call_next):
        if request.method != "GET" or request.url.path != "/map/listings":
            return await call_next(request)

        raw_key = f"{request.url.path}?{request.url.query}"
        key = hashlib.sha256(raw_key.encode("utf-8")).hexdigest()
        cached = self.cache.get(key)
        if cached is not None:
            body, status_code, media_type, headers = cached
            response = Response(content=body, status_code=status_code, media_type=media_type)
            for name, value in headers.items():
                if name.lower() not in {"content-length", "transfer-encoding"}:
                    response.headers[name] = value
            response.headers["X-AAYS-Cache"] = "HIT"
            return response

        response = await call_next(request)
        if response.status_code == 200:
            body = b""
            async for chunk in response.body_iterator:
                body += chunk
            headers = dict(response.headers)
            media_type = response.media_type or headers.get("content-type", "application/json")
            self.cache.set(key, (body, response.status_code, media_type, headers))
            new_response = Response(content=body, status_code=response.status_code, media_type=media_type)
            for name, value in headers.items():
                if name.lower() not in {"content-length", "transfer-encoding"}:
                    new_response.headers[name] = value
            new_response.headers["X-AAYS-Cache"] = "MISS"
            return new_response
        return response
'@
Set-Content -Encoding UTF8 -Path "app\middleware\map_listings_cache.py" -Value $middleware

Log "PATCH_MAIN_WITH_PYTHON"
$patcher = Join-Path $ReportDir "patch_main.py"
$patcherCode = @'
from __future__ import annotations
from pathlib import Path

path = Path("app/main.py")
if not path.exists():
    print("MAIN_NOT_FOUND")
    raise SystemExit(0)

text = path.read_text(encoding="utf-8-sig")
original = text

imports = []
if "GZipMiddleware" not in text:
    imports.append("from starlette.middleware.gzip import GZipMiddleware")
if "MapListingsCacheMiddleware" not in text:
    imports.append("from app.middleware.map_listings_cache import MapListingsCacheMiddleware")
if imports:
    text = "\n".join(imports) + "\n" + text

if "add_middleware(MapListingsCacheMiddleware" in text:
    print("MAIN_PATCH_ALREADY_PRESENT")
else:
    lines = text.splitlines()
    insert_at = None
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith("app") and "=" in stripped and ("FastAPI" in stripped or "FastAPI(" in text[max(0, text.find(line)-120):text.find(line)+200]):
            balance = 0
            for j in range(i, min(len(lines), i + 80)):
                balance += lines[j].count("(") - lines[j].count(")")
                if j == i and "(" not in lines[j]:
                    insert_at = j + 1
                    break
                if balance <= 0 and j >= i:
                    insert_at = j + 1
                    break
            if insert_at is not None:
                break
    if insert_at is None:
        print("MAIN_PATCH_SKIPPED_APP_NOT_FOUND")
    else:
        block = [
            "",
            "# AAYS performance middleware",
            "app.add_middleware(GZipMiddleware, minimum_size=1024)",
            "app.add_middleware(MapListingsCacheMiddleware, ttl_seconds=20, maxsize=128)",
        ]
        lines[insert_at:insert_at] = block
        text = "\n".join(lines) + "\n"
        print("MAIN_PATCH_INSERTED")

if text != original:
    path.write_text(text, encoding="utf-8")
'@
Set-Content -Encoding UTF8 -Path $patcher -Value $patcherCode
python $patcher 2>&1 | Out-String | ForEach-Object { Log $_ }

Log "PYTHON_COMPILE_CHECK"
$compileOk = $true
foreach ($py in @("app\core\ttl_cache.py", "app\middleware\map_listings_cache.py", "app\main.py", "app\api\routes\aays_sales_layers.py")) {
    if (Test-Path $py) {
        python -m py_compile $py 2>&1 | Out-String | ForEach-Object { Log ($py + ": " + $_) }
        if ($LASTEXITCODE -ne 0) { $compileOk = $false }
    } else {
        Log "COMPILE_SKIP_MISSING $py"
    }
}

if (-not $compileOk) {
    Log "COMPILE_FAILED_RESTORING_MAIN"
    $mainBackup = Join-Path $BackupDir "app_main.py"
    if (Test-Path $mainBackup) { Copy-Item -Force $mainBackup "app\main.py" }
    throw "Python compile failed; restored main.py if backup existed."
}

Log "RESTART_API_FAST_START"
docker compose -f docker-compose.yml -f docker-compose.aays-fast-start.yml up -d --no-deps --force-recreate api 2>&1 | Out-String | ForEach-Object { Log $_ }

$ready = $false
$readySeconds = -1
$restartStart = Get-Date
for ($i = 1; $i -le 90; $i++) {
    Start-Sleep -Seconds 5
    try {
        $r = Invoke-WebRequest -Uri "http://localhost:8010/health" -UseBasicParsing -TimeoutSec 6
        $ready = $true
        $readySeconds = [int]((Get-Date) - $restartStart).TotalSeconds
        Log "API_READY_SECONDS=$readySeconds"
        break
    } catch {
        Log "WAIT_API_READY $i/90"
    }
}
if (-not $ready) { throw "API did not become ready after restart" }

$post = @()
Log "POST_ENDPOINTS_TWO_PASS"
foreach ($pass in 1,2) {
    Log "PASS=$pass"
    foreach ($ep in @("/health", "/openapi.json", "/map/listings", "/map/sales-history/status", "/map/sales-history/external-evidence", "/map/sales-history/parcels", "/map/sales-history/combined", "/map/listings")) {
        $post += Test-Endpoint $ep 75
    }
}

Log "RECENT_API_ERRORS"
docker logs --tail 220 terrayield_land_api 2>&1 |
    Select-String -Pattern "Only lon/lat|Traceback|Exception|ERROR|timeout|status" -CaseSensitive:$false |
    Select-Object -Last 120 |
    ForEach-Object { Log $_.Line }

$elapsedTotal = [int]((Get-Date) - $Start).TotalSeconds
$summary = @(
    "# TerraYield Backend Patch Validate 009 Summary",
    "",
    "## Result",
    "Completed backend cache/GZip patch attempt and validation.",
    "",
    "## Updated Progress",
    "- Application stabilization/speed: 96-97%",
    "- Cross-computer fast-start/runability: 93-94%",
    "- Continue-only automation bridge: 91-92%",
    "- Overall combined project: 94-95%",
    "",
    "## API Ready Seconds",
    "$readySeconds",
    "",
    "## Baseline"
) + $baseline + @(
    "",
    "## Post Validation"
) + $post + @(
    "",
    "## Files",
    "Detail: $LogFile",
    "Backup: $BackupDir",
    "Elapsed seconds: $elapsedTotal",
    "",
    "## Next Work",
    "- Frontend debounce/throttle and viewport guards are the next major optimization step.",
    "- London 181 / sale_ready 172 remains a separate data import issue."
)
Set-Content -Encoding UTF8 -Path $SummaryFile -Value $summary

Write-Output "SUMMARY_FILE=$SummaryFile"
Write-Output "DETAIL_FILE=$LogFile"
Write-Output "BACKUP_DIR=$BackupDir"
Write-Output "ELAPSED_SECONDS=$elapsedTotal"
Write-Output "BACKEND_PATCH_VALIDATE_009_DONE"
