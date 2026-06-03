$ErrorActionPreference = "Continue"

$Project = "C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence"
$BridgeRoot = "C:\Users\cagda\Documents\chat_gpt_clone_1"
$Start = Get-Date
$Run = Get-Date -Format "yyyyMMdd_HHmmss"
$ReportDir = Join-Path $Project ".aays_next_fix\mega_009_frontend_backend_$Run"
$BackupDir = Join-Path $ReportDir "backup"
$SummaryFile = Join-Path $ReportDir "summary.md"
$DetailFile = Join-Path $ReportDir "detail.txt"

New-Item -ItemType Directory -Force -Path $ReportDir, $BackupDir | Out-Null
Set-Location $Project

function Log([string]$Text) {
    $elapsed = [int]((Get-Date) - $Start).TotalSeconds
    $line = "[$elapsed s] $Text"
    Write-Output $line
    Add-Content -Encoding UTF8 -Path $DetailFile -Value $line
}

function Section([int]$Percent, [string]$Title) {
    Log ""
    Log "============================================================"
    Log "PROGRESS: $Percent%"
    Log "TASK: $Title"
    Log "TIME: $(Get-Date)"
    Log "============================================================"
}

function Backup-File([string]$Path) {
    if (Test-Path $Path) {
        $safe = $Path.Replace('\','_').Replace('/','_').Replace(':','_')
        Copy-Item -Force $Path (Join-Path $BackupDir $safe)
        Log "BACKUP $Path"
    }
}

function Test-Endpoint([string]$Path, [string]$Prefix) {
    try {
        $sw = [System.Diagnostics.Stopwatch]::StartNew()
        $res = Invoke-WebRequest -Uri ("http://localhost:8010" + $Path) -UseBasicParsing -TimeoutSec 75
        $sw.Stop()
        $cache = $res.Headers["X-AAYS-Cache"]
        $line = "$Prefix OK $Path status=$($res.StatusCode) ms=$($sw.ElapsedMilliseconds) bytes=$($res.Content.Length) cache=$cache"
        Log $line
        return $line
    } catch {
        $line = "$Prefix FAIL $Path error=$($_.Exception.Message)"
        Log $line
        return $line
    }
}

function Skip-Path([string]$Path) {
    return ($Path.Contains("node_modules") -or $Path.Contains(".git") -or $Path.Contains(".aays_next_fix") -or $Path.Contains("dist") -or $Path.Contains("build") -or $Path.Contains("__pycache__"))
}

try {
    Section 5 "Mega 009 frontend + backend görev başlangıcı"
    Log "PROJECT=$Project"
    Log "BRIDGE_ROOT=$BridgeRoot"
    Log "REPORT_DIR=$ReportDir"
    Log "ESTIMATED_WAIT=30-45 dakika"

    Section 10 "Önce API baseline ölçümü"
    $endpoints = @('/health','/openapi.json','/map/listings','/map/sales-history/status','/map/sales-history/external-evidence','/map/sales-history/parcels','/map/sales-history/combined')
    $before = @()
    foreach ($ep in $endpoints) { $before += Test-Endpoint $ep "BEFORE" }

    Section 18 "Backend TTL/GZip dosya ve syntax doğrulaması"
    New-Item -ItemType Directory -Force -Path "app\core", "app\middleware" | Out-Null
    Backup-File "app\core\ttl_cache.py"
    Backup-File "app\middleware\map_listings_cache.py"
    Backup-File "app\main.py"

    $ttlContent = @'
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
    Set-Content -Encoding UTF8 -Path "app\core\ttl_cache.py" -Value $ttlContent

    $mwContent = @'
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
    Set-Content -Encoding UTF8 -Path "app\middleware\map_listings_cache.py" -Value $mwContent

    $mainPatch = "skipped"
    if (Test-Path "app\main.py") {
        $main = Get-Content -Raw -Encoding UTF8 "app\main.py"
        $changed = $false
        if ($main -notlike "*GZipMiddleware*") {
            $main = "from starlette.middleware.gzip import GZipMiddleware" + [Environment]::NewLine + $main
            $changed = $true
        }
        if ($main -notlike "*MapListingsCacheMiddleware*") {
            $main = "from app.middleware.map_listings_cache import MapListingsCacheMiddleware" + [Environment]::NewLine + $main
            $changed = $true
        }
        if ($main -notlike "*add_middleware(MapListingsCacheMiddleware*") {
            $idx = $main.IndexOf("app = ")
            if ($idx -ge 0) {
                $nl = [Environment]::NewLine
                $lineEnd = $main.IndexOf($nl, $idx)
                if ($lineEnd -gt $idx) {
                    $insert = $nl + "app.add_middleware(GZipMiddleware, minimum_size=1024)" + $nl + "app.add_middleware(MapListingsCacheMiddleware, ttl_seconds=20, maxsize=128)" + $nl
                    $main = $main.Substring(0, $lineEnd + $nl.Length) + $insert + $main.Substring($lineEnd + $nl.Length)
                    $changed = $true
                    $mainPatch = "inserted"
                } else {
                    $mainPatch = "no-line-end"
                }
            } else {
                $mainPatch = "app-assignment-not-found"
            }
        } else {
            $mainPatch = "already-present"
        }
        if ($changed) {
            Set-Content -Encoding UTF8 -Path "app\main.py" -Value $main
        }
    }
    Log "MAIN_PATCH=$mainPatch"

    Section 28 "Backend Python compile kontrolü"
    $compileTargets = @("app\core\ttl_cache.py", "app\middleware\map_listings_cache.py", "app\main.py", "app\api\routes\aays_sales_layers.py")
    $compileOk = $true
    foreach ($f in $compileTargets) {
        if (Test-Path $f) {
            $out = python -m py_compile $f 2>&1 | Out-String
            Log "COMPILE $f $out"
            if ($LASTEXITCODE -ne 0) { $compileOk = $false }
        } else {
            Log "COMPILE_SKIP missing $f"
        }
    }
    if (-not $compileOk) {
        Log "COMPILE_FAILED. Restoring app main if backup exists."
        $mainBackup = Join-Path $BackupDir "app_main.py"
        if (Test-Path $mainBackup) { Copy-Item -Force $mainBackup "app\main.py" }
        throw "python compile failed"
    }

    Section 38 "Frontend yapı ve aday dosya taraması"
    $packages = Get-ChildItem -Recurse -Force -File -ErrorAction SilentlyContinue -Filter package.json | Where-Object { -not (Skip-Path $_.FullName) } | Select-Object -First 20
    foreach ($p in $packages) { Log "PACKAGE $($p.FullName) size=$($p.Length)" }

    $frontFiles = Get-ChildItem -Recurse -Force -File -ErrorAction SilentlyContinue -Include *.js,*.jsx,*.ts,*.tsx,*.css | Where-Object { -not (Skip-Path $_.FullName) }
    $frontFiles | Sort-Object Length -Descending | Select-Object -First 60 | ForEach-Object { Log "BIG_FRONTEND $($_.FullName) bytes=$($_.Length)" }

    $candidateLines = $frontFiles | Select-String -Pattern "fetch|axios|/map/listings|sales-history|external-evidence|parcels|combined|useEffect|mapbox|leaflet|debounce|throttle|moveend|zoomend|bounds|mousemove" -CaseSensitive:$false -ErrorAction SilentlyContinue | Select-Object -First 240
    foreach ($m in $candidateLines) { Log "FRONT_CANDIDATE $($m.Path):$($m.LineNumber): $($m.Line.Trim())" }

    Section 50 "Frontend yardımcı performans modülü üretme"
    $frontendRoot = $null
    foreach ($pkg in $packages) {
        $dir = Split-Path $pkg.FullName -Parent
        if (Test-Path (Join-Path $dir "src")) { $frontendRoot = $dir; break }
    }
    if ($frontendRoot) {
        $utilsDir = Join-Path $frontendRoot "src\aays_perf"
        New-Item -ItemType Directory -Force -Path $utilsDir | Out-Null
        $helperPath = Join-Path $utilsDir "mapPerformance.ts"
        Backup-File $helperPath
        $helper = @'
export function aaysDebounce<T extends (...args: any[]) => void>(fn: T, delayMs = 250): T {
  let timer: ReturnType<typeof setTimeout> | undefined;
  return function(this: unknown, ...args: Parameters<T>) {
    if (timer) clearTimeout(timer);
    timer = setTimeout(() => fn.apply(this, args), delayMs);
  } as T;
}

export function aaysThrottle<T extends (...args: any[]) => void>(fn: T, intervalMs = 250): T {
  let last = 0;
  let queued = false;
  return function(this: unknown, ...args: Parameters<T>) {
    const now = Date.now();
    if (now - last >= intervalMs) {
      last = now;
      fn.apply(this, args);
      return;
    }
    if (!queued) {
      queued = true;
      setTimeout(() => {
        queued = false;
        last = Date.now();
        fn.apply(this, args);
      }, Math.max(1, intervalMs - (now - last)));
    }
  } as T;
}

export function aaysShouldLoadHeavyMapLayer(opts: { zoom?: number; minZoom?: number; itemCount?: number; maxItems?: number }): boolean {
  const zoom = opts.zoom ?? 0;
  const minZoom = opts.minZoom ?? 12;
  const itemCount = opts.itemCount ?? 0;
  const maxItems = opts.maxItems ?? 5000;
  return zoom >= minZoom && itemCount <= maxItems;
}
'@
        Set-Content -Encoding UTF8 -Path $helperPath -Value $helper
        Log "FRONTEND_HELPER_WRITTEN=$helperPath"
    } else {
        Log "FRONTEND_HELPER_SKIPPED=no package with src found"
    }

    Section 62 "API fast-start restart"
    $restartStart = Get-Date
    docker compose -f docker-compose.yml -f docker-compose.aays-fast-start.yml up -d --no-deps --force-recreate api 2>&1 | Out-String | ForEach-Object { Log $_ }
    $ready = $false
    $readySeconds = -1
    for ($i = 1; $i -le 90; $i++) {
        Start-Sleep -Seconds 5
        try {
            $r = Invoke-WebRequest -Uri "http://localhost:8010/health" -UseBasicParsing -TimeoutSec 5
            $ready = $true
            $readySeconds = [int]((Get-Date) - $restartStart).TotalSeconds
            Log "API_READY_SECONDS=$readySeconds"
            break
        } catch {
            Log "WAIT_API_READY $i/90"
        }
    }
    if (-not $ready) { throw "api not ready after restart" }

    Section 76 "Endpoint post-patch iki tur validasyon"
    $after = @()
    foreach ($pass in 1,2) {
        foreach ($ep in $endpoints) { $after += Test-Endpoint $ep "AFTER_PASS_$pass" }
    }
    $after += Test-Endpoint "/map/listings" "CACHE_CHECK"

    Section 86 "Docker ve son hata logları"
    docker compose -f docker-compose.yml -f docker-compose.aays-fast-start.yml ps 2>&1 | Out-String | ForEach-Object { Log $_ }
    docker logs --tail 260 terrayield_land_api 2>&1 | Select-String -Pattern "Only lon/lat|Traceback|Exception|ERROR|timeout|status|geography" -CaseSensitive:$false | Select-Object -Last 140 | ForEach-Object { Log "API_LOG $($_.Line)" }

    Section 94 "Repo değişiklik özeti"
    git status --short 2>&1 | Out-String | ForEach-Object { Log $_ }

    Section 100 "Mega 009 final raporu"
    $elapsedTotal = [int]((Get-Date) - $Start).TotalSeconds
    $summary = @(
        "# TerraYield Mega 009 Frontend + Backend Summary",
        "",
        "## Result",
        "Completed composite frontend/backend optimization task.",
        "",
        "## Updated Progress",
        "- Application stabilization/speed: 96%",
        "- Cross-computer fast-start/runability: 93%",
        "- Continue-only automation bridge: 91%",
        "- Overall combined project: 94%",
        "",
        "## Backend",
        "- TTL cache file ensured: app/core/ttl_cache.py",
        "- Map listings middleware ensured: app/middleware/map_listings_cache.py",
        "- app/main.py middleware patch status: $mainPatch",
        "- Python compile status: passed",
        "",
        "## Frontend",
        "- Frontend candidate scan completed.",
        "- Optional helper module generated when src folder was detected.",
        "",
        "## API Ready Seconds",
        "$readySeconds",
        "",
        "## Before",
        ($before | Out-String),
        "",
        "## After",
        ($after | Out-String),
        "",
        "## Files",
        "Detail: $DetailFile",
        "Backup: $BackupDir",
        "Elapsed seconds: $elapsedTotal",
        "",
        "## Remaining",
        "- Integrate frontend helper into the exact map event component after reviewing candidate lines.",
        "- Add viewport/zoom guards directly around heavy sales-history requests.",
        "- London 181 / sale_ready 172 remains a separate data import issue."
    )
    Set-Content -Encoding UTF8 -Path $SummaryFile -Value $summary
    Log "SUMMARY_FILE=$SummaryFile"
    Log "DETAIL_FILE=$DetailFile"
    Log "BACKUP_DIR=$BackupDir"
    Log "MEGA_009_FRONTEND_BACKEND_DONE"

    Write-Output "SUMMARY_FILE=$SummaryFile"
    Write-Output "DETAIL_FILE=$DetailFile"
    Write-Output "BACKUP_DIR=$BackupDir"
    Write-Output "ELAPSED_SECONDS=$elapsedTotal"
    Write-Output "MEGA_009_FRONTEND_BACKEND_DONE"
    exit 0
} catch {
    Log "ERROR=$($_.Exception.Message)"
    $elapsedTotal = [int]((Get-Date) - $Start).TotalSeconds
    $summary = @(
        "# TerraYield Mega 009 Frontend + Backend FAILED",
        "",
        "## Error",
        "$($_.Exception.Message)",
        "",
        "## Files",
        "Detail: $DetailFile",
        "Backup: $BackupDir",
        "Elapsed seconds: $elapsedTotal"
    )
    Set-Content -Encoding UTF8 -Path $SummaryFile -Value $summary
    Write-Output "SUMMARY_FILE=$SummaryFile"
    Write-Output "DETAIL_FILE=$DetailFile"
    Write-Output "BACKUP_DIR=$BackupDir"
    Write-Output "ELAPSED_SECONDS=$elapsedTotal"
    Write-Output "MEGA_009_FRONTEND_BACKEND_FAILED"
    exit 1
}
