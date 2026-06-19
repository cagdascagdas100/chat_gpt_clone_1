$ErrorActionPreference = "Stop"

$pageKey = "internet_access_parcel_layer_low_credit_20260612"
$taskId = "internet-access-108-real-parcel-final-gate"
$fixId = "ia108-real-geometry-join-v2-schema-probe"

$pageDir = "docs/chatgpt_status/$pageKey"
$statusDir = "$pageDir/status"
$heartbeatDir = "$pageDir/heartbeat"
$runnerOutDir = "$pageDir/runner_outputs"
$reportsDir = "docs/chatgpt_status/reports"
$pageReportsDir = "$pageDir/reports"

$sourceRoot = "F:\chatgpt\AAYS_WORK\internet_access_score10_real_build_20260610"
if (!(Test-Path $sourceRoot)) { $sourceRoot = "D:\chatgpt\AAYS_WORK\internet_access_score10_real_build_20260610" }

$heavyRoot = "F:\AAYS_WORK\internet_access_final_20260616"
if (!(Test-Path "F:\")) { $heavyRoot = "D:\AAYS_WORK\internet_access_final_20260616" }

$processedDir = Join-Path $heavyRoot "processed"
$diagDir = Join-Path $heavyRoot "diagnostics"
New-Item -ItemType Directory -Force $processedDir,$diagDir,$statusDir,$heartbeatDir,$runnerOutDir,$reportsDir,$pageReportsDir | Out-Null

$srcGeoJson = Join-Path $sourceRoot "processed\parcel_internet_access_scores.geojson"
$srcCsv = Join-Path $sourceRoot "processed\parcel_internet_access_scores.csv"
$srcBreakdown = Join-Path $sourceRoot "processed\parcel_internet_access_factor_breakdown.csv"

$readyGeoJson = Join-Path $processedDir "parcel_internet_access_scores_ready.geojson"
$readyCsv = Join-Path $processedDir "parcel_internet_access_scores_ready.csv"
$readyBreakdown = Join-Path $processedDir "parcel_internet_access_factor_breakdown_ready.csv"
$detailJson = Join-Path $processedDir "parcel_internet_access_detail_ready.json"

$repoReport = "$pageReportsDir/ia108_real_geometry_join_v2_schema_probe_report.json"
$repoStatus = "$statusDir/ia108_real_geometry_join_v2_schema_probe.txt"
$repoLog = "$statusDir/ia108_real_geometry_join_v2_schema_probe.log"
$finalReport = "$reportsDir/$taskId.json"
$pageOutput = "$runnerOutDir/internet_access_final_build_latest.json"

"V2_SCHEMA_PROBE_STARTED=$(Get-Date -Format o)" | Set-Content -Encoding UTF8 "$heartbeatDir/latest.txt"

function Write-Log([string]$s) {
    $s | Tee-Object -FilePath $repoLog -Append
}

function Get-PropValue($props, [string]$key) {
    if ($null -eq $props) { return $null }
    if ($props.PSObject.Properties.Name -contains $key) {
        $v = [string]$props.$key
        if ($v -and $v.Trim().Length -gt 0) { return $v.Trim() }
    }
    return $null
}

function Get-FeatureKey($props, $keys) {
    foreach ($k in $keys) {
        $v = Get-PropValue $props $k
        if ($v) { return @{ key = $k; value = $v } }
    }
    return $null
}

function Get-FeaturesFromJson($obj) {
    if ($null -eq $obj) { return @() }
    if ($obj.PSObject.Properties.Name -contains "features") { return @($obj.features) }
    if ($obj -is [System.Array]) { return @($obj) }
    if ($obj.PSObject.Properties.Name -contains "data" -and $obj.data.PSObject.Properties.Name -contains "features") { return @($obj.data.features) }
    return @()
}

try {
    if (!(Test-Path $srcGeoJson)) { throw "Source score GeoJSON missing: $srcGeoJson" }
    if (!(Test-Path $srcCsv)) { throw "Source score CSV missing: $srcCsv" }

    Write-Log "Reading score GeoJSON: $srcGeoJson"
    $scoreObj = Get-Content $srcGeoJson -Raw | ConvertFrom-Json
    $scoreFeatures = Get-FeaturesFromJson $scoreObj

    $scoreHeaders = @()
    $firstCsv = Get-Content $srcCsv -TotalCount 1
    if ($firstCsv) { $scoreHeaders = $firstCsv.Split(',') | ForEach-Object { $_.Trim('"').Trim() } }

    $preferred = @(
        "parcel_id", "parcelid", "parcel", "id", "uprn", "UPRN", "title_number", "title_no", "title",
        "property_id", "propertyid", "oa11cd", "lsoa11cd", "msoa11cd", "postcode", "pcd", "pcds"
    ) + $scoreHeaders
    $preferred = @($preferred | Where-Object { $_ } | Select-Object -Unique)

    $scoreIndexByKey = @{}
    $scorePrimaryKey = $null
    foreach ($k in $preferred) { $scoreIndexByKey[$k] = @{} }

    foreach ($f in $scoreFeatures) {
        foreach ($k in $preferred) {
            $v = Get-PropValue $f.properties $k
            if ($v) {
                if (-not $scorePrimaryKey) { $scorePrimaryKey = $k }
                if (-not $scoreIndexByKey[$k].ContainsKey($v)) { $scoreIndexByKey[$k][$v] = $f }
            }
        }
    }

    $searchRoots = @(
        "F:\AAYS_WORK", "F:\chatgpt\AAYS_WORK", "D:\AAYS_WORK", "D:\chatgpt\AAYS_WORK", "C:\Users\cagda\Documents\GitHub\AAYS"
    ) | Where-Object { Test-Path $_ }

    $candidateFiles = foreach ($root in $searchRoots) {
        Get-ChildItem -Path $root -Recurse -File -ErrorAction SilentlyContinue |
            Where-Object {
                $_.Extension -in @(".geojson", ".json") -and
                $_.FullName -match "(parcel|polygon|boundary|boundaries|cadastre|cadastral|title|uprn|footprint|security)" -and
                $_.Length -gt 1024 -and
                $_.FullName -notmatch "parcel_internet_access_scores"
            } |
            Sort-Object Length -Descending
    }

    $best = $null
    $bestKey = $null
    $bestScoreKey = $null
    $bestMatches = 0
    $bestPolygonCount = 0
    $candidateSummaries = @()

    foreach ($file in @($candidateFiles | Select-Object -First 200)) {
        try {
            $obj = Get-Content $file.FullName -Raw -ErrorAction Stop | ConvertFrom-Json
            $features = Get-FeaturesFromJson $obj
            if ($features.Count -eq 0) { continue }
            $polygonFeatures = @($features | Where-Object { $_.geometry -and ($_.geometry.type -eq "Polygon" -or $_.geometry.type -eq "MultiPolygon") })
            if ($polygonFeatures.Count -eq 0) { continue }

            $localBest = 0
            $localCandidateKey = $null
            $localScoreKey = $null
            $candidatePropKeys = @($polygonFeatures | Select-Object -First 20 | ForEach-Object { if ($_.properties) { $_.properties.PSObject.Properties.Name } } | Select-Object -Unique)
            $tryKeys = @($preferred + $candidatePropKeys | Where-Object { $_ } | Select-Object -Unique)

            foreach ($candidateKey in $tryKeys) {
                foreach ($scoreKey in $preferred) {
                    if (-not $scoreIndexByKey.ContainsKey($scoreKey)) { continue }
                    $idx = $scoreIndexByKey[$scoreKey]
                    if ($idx.Count -eq 0) { continue }
                    $m = 0
                    foreach ($pf in ($polygonFeatures | Select-Object -First 10000)) {
                        $v = Get-PropValue $pf.properties $candidateKey
                        if ($v -and $idx.ContainsKey($v)) { $m++ }
                    }
                    if ($m -gt $localBest) {
                        $localBest = $m
                        $localCandidateKey = $candidateKey
                        $localScoreKey = $scoreKey
                    }
                }
            }

            $candidateSummaries += [ordered]@{
                file = $file.FullName
                size = $file.Length
                feature_count = $features.Count
                polygon_count = $polygonFeatures.Count
                best_candidate_key = $localCandidateKey
                best_score_key = $localScoreKey
                sample_matches = $localBest
            }

            if ($localBest -gt $bestMatches) {
                $best = $file.FullName
                $bestMatches = $localBest
                $bestKey = $localCandidateKey
                $bestScoreKey = $localScoreKey
                $bestPolygonCount = $polygonFeatures.Count
            }
        }
        catch {
            $candidateSummaries += [ordered]@{ file = $file.FullName; size = $file.Length; error = $_.Exception.Message }
        }
    }

    if (-not $best -or $bestMatches -le 0) {
        $report = [ordered]@{
            task_id = $taskId
            page_key = $pageKey
            status = "REAL_PARCEL_GEOMETRY_JOIN_BLOCKED_NO_COMPATIBLE_KEY"
            completion_percent = 78
            final_ready = $false
            production_complete = $false
            score_feature_count = $scoreFeatures.Count
            score_primary_key_detected = $scorePrimaryKey
            searched_roots = $searchRoots
            candidate_count = @($candidateFiles).Count
            inspected_candidate_count = @($candidateSummaries).Count
            candidates = $candidateSummaries
            reason = "No real Polygon/MultiPolygon candidate had a join key matching score dataset values. Fake geometry refused."
            generated_at = (Get-Date -Format o)
        }
        $report | ConvertTo-Json -Depth 12 | Set-Content -Encoding UTF8 $repoReport
        "status=REAL_PARCEL_GEOMETRY_JOIN_BLOCKED_NO_COMPATIBLE_KEY`ncompletion_percent=78`nfinal_ready=false`nproduction_complete=false`nreport=$repoReport" | Set-Content -Encoding UTF8 $repoStatus
        "V2_SCHEMA_PROBE_FINISHED=$(Get-Date -Format o)`nSTATUS=BLOCKED_NO_COMPATIBLE_KEY" | Add-Content -Encoding UTF8 "$heartbeatDir/latest.txt"
        exit 0
    }

    Write-Log "Best candidate: $best; candidate_key=$bestKey; score_key=$bestScoreKey; sample_matches=$bestMatches"
    $polyObj = Get-Content $best -Raw | ConvertFrom-Json
    $polyFeatures = @(Get-FeaturesFromJson $polyObj | Where-Object { $_.geometry -and ($_.geometry.type -eq "Polygon" -or $_.geometry.type -eq "MultiPolygon") })
    $polyIndex = @{}
    foreach ($pf in $polyFeatures) {
        $v = Get-PropValue $pf.properties $bestKey
        if ($v -and -not $polyIndex.ContainsKey($v)) { $polyIndex[$v] = $pf.geometry }
    }

    $joined = 0
    $nullAfter = 0
    foreach ($sf in $scoreFeatures) {
        $v = Get-PropValue $sf.properties $bestScoreKey
        if ($v -and $polyIndex.ContainsKey($v)) { $sf.geometry = $polyIndex[$v]; $joined++ }
        if ($null -eq $sf.geometry) { $nullAfter++ }
    }

    $scoreObj | ConvertTo-Json -Depth 100 | Set-Content -Encoding UTF8 $readyGeoJson
    Copy-Item $srcCsv $readyCsv -Force
    if (Test-Path $srcBreakdown) { Copy-Item $srcBreakdown $readyBreakdown -Force }
    [ordered]@{
        task_id = $taskId
        page_key = $pageKey
        source_score_geojson = $srcGeoJson
        source_polygon_geojson = $best
        score_join_key = $bestScoreKey
        polygon_join_key = $bestKey
        joined_geometry_count = $joined
        null_geometry_after_join = $nullAfter
        generated_at = (Get-Date -Format o)
    } | ConvertTo-Json -Depth 10 | Set-Content -Encoding UTF8 $detailJson

    $status = if ($nullAfter -eq 0 -and $joined -eq $scoreFeatures.Count) { "REAL_PARCEL_GEOMETRY_JOIN_READY" } else { "REAL_PARCEL_GEOMETRY_JOIN_PARTIAL" }
    $percent = if ($status -eq "REAL_PARCEL_GEOMETRY_JOIN_READY") { 99 } else { 82 }
    $report2 = [ordered]@{
        task_id = $taskId
        page_key = $pageKey
        status = $status
        completion_percent = $percent
        final_ready = $false
        production_complete = $false
        source_polygon_geojson = $best
        polygon_feature_count = $bestPolygonCount
        score_join_key = $bestScoreKey
        polygon_join_key = $bestKey
        joined_geometry_count = $joined
        score_feature_count = $scoreFeatures.Count
        null_geometry_after_join = $nullAfter
        ready_geojson = $readyGeoJson
        ready_csv = $readyCsv
        ready_breakdown = $readyBreakdown
        detail_json = $detailJson
        generated_at = (Get-Date -Format o)
    }
    $report2 | ConvertTo-Json -Depth 12 | Set-Content -Encoding UTF8 $repoReport
    "status=$status`ncompletion_percent=$percent`njoined_geometry_count=$joined`nscore_feature_count=$($scoreFeatures.Count)`nnull_geometry_after_join=$nullAfter`nready_geojson=$readyGeoJson" | Set-Content -Encoding UTF8 $repoStatus

    if ($status -eq "REAL_PARCEL_GEOMETRY_JOIN_READY") {
        $final = [ordered]@{
            task_id = $taskId
            page_key = $pageKey
            status = "FINAL_READY"
            completion_percent = 100
            final_ready = $true
            production_complete = $true
            fake_data = $false
            db_write = $false
            migration = $false
            production_deploy = $false
            ready_outputs = [ordered]@{ scores_geojson = $readyGeoJson; scores_csv = $readyCsv; factor_breakdown_csv = $readyBreakdown; detail_json = $detailJson }
            FINAL_STATUS = "FINAL_READY_CONFIRMED"
            PRODUCT_PROGRESS_ESTIMATE = 100
            PRODUCTION_COMPLETE = $true
            generated_at_utc = (Get-Date).ToUniversalTime().ToString("o")
        }
        $final | ConvertTo-Json -Depth 10 | Set-Content -Encoding UTF8 $finalReport
        $final | ConvertTo-Json -Depth 10 | Set-Content -Encoding UTF8 $pageOutput
    }

    "V2_SCHEMA_PROBE_FINISHED=$(Get-Date -Format o)`nSTATUS=$status`nJOINED=$joined`nNULL_AFTER=$nullAfter" | Add-Content -Encoding UTF8 "$heartbeatDir/latest.txt"
    exit 0
}
catch {
    $err = $_.Exception.Message
    $reportErr = [ordered]@{
        task_id = $taskId
        page_key = $pageKey
        status = "V2_SCHEMA_PROBE_SCRIPT_ERROR"
        completion_percent = 78
        final_ready = $false
        production_complete = $false
        error = $err
        generated_at = (Get-Date -Format o)
    }
    $reportErr | ConvertTo-Json -Depth 10 | Set-Content -Encoding UTF8 $repoReport
    "status=V2_SCHEMA_PROBE_SCRIPT_ERROR`ncompletion_percent=78`nerror=$err`nreport=$repoReport" | Set-Content -Encoding UTF8 $repoStatus
    "V2_SCHEMA_PROBE_FAILED=$(Get-Date -Format o)`nERROR=$err" | Add-Content -Encoding UTF8 "$heartbeatDir/latest.txt"
    exit 1
}
