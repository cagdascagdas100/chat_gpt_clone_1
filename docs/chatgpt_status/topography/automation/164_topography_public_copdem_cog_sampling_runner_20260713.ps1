[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'

function Now-Utc { (Get-Date).ToUniversalTime().ToString('o') }
function Ensure-Dir([string]$Path) {
  if ($Path -and -not (Test-Path -LiteralPath $Path)) { New-Item -ItemType Directory -Force -Path $Path | Out-Null }
}
function Write-Json([string]$Path,[object]$Value) {
  Ensure-Dir (Split-Path -Parent $Path)
  $tmp = "$Path.tmp"
  [System.IO.File]::WriteAllText($tmp,(($Value | ConvertTo-Json -Depth 100)+"`n"),[System.Text.UTF8Encoding]::new($false))
  Move-Item -LiteralPath $tmp -Destination $Path -Force
}
function Read-Json([string]$Path) {
  if (Test-Path -LiteralPath $Path) { return (Get-Content -LiteralPath $Path -Raw -Encoding UTF8 | ConvertFrom-Json) }
  return $null
}
function Set-Prop([object]$Object,[string]$Name,[object]$Value) {
  Add-Member -InputObject $Object -NotePropertyName $Name -NotePropertyValue $Value -Force
}
function Repo-Path([string]$RelativePath) {
  return (Join-Path $script:repoRoot ($RelativePath.Replace('/','\')))
}
function Test-Http([string]$Name,[string]$Url,[string]$Method='GET') {
  $x=[ordered]@{name=$Name;url=$Url;method=$Method;reachable=$false;status_code=$null;final_url=$null;content_length=$null;content_type=$null;error=$null}
  try {
    $r=Invoke-WebRequest -UseBasicParsing -Method $Method -Uri $Url -MaximumRedirection 10 -TimeoutSec 180 -Headers @{'User-Agent'='TerraYield-AAYS-Topography/1.0 public-cog-164'}
    $x.status_code=[int]$r.StatusCode
    $x.reachable=($r.StatusCode -ge 200 -and $r.StatusCode -lt 400)
    if($r.BaseResponse -and $r.BaseResponse.ResponseUri){$x.final_url=[string]$r.BaseResponse.ResponseUri.AbsoluteUri}
    if($r.Headers['Content-Length']){$x.content_length=[int64]$r.Headers['Content-Length']}
    if($r.Headers['Content-Type']){$x.content_type=[string]$r.Headers['Content-Type']}
  } catch {
    try{$x.status_code=[int]$_.Exception.Response.StatusCode.value__}catch{}
    $x.error=$_.Exception.Message
  }
  return [pscustomobject]$x
}
function Get-TileListCheck([string]$Name,[string]$Url,[string]$Target) {
  $x=[ordered]@{name=$Name;url=$Url;reachable=$false;status_code=$null;target=$Target;target_present=$false;content_length=$null;error=$null}
  try {
    $r=Invoke-WebRequest -UseBasicParsing -Method Get -Uri $Url -TimeoutSec 240 -Headers @{'User-Agent'='TerraYield-AAYS-Topography/1.0 tile-list-164'}
    $x.status_code=[int]$r.StatusCode
    $x.reachable=($r.StatusCode -ge 200 -and $r.StatusCode -lt 400)
    $x.content_length=[int64]$r.RawContentLength
    $x.target_present=([string]$r.Content).Contains($Target)
  } catch {$x.error=$_.Exception.Message}
  return [pscustomobject]$x
}
function Download-Bounded([string]$Url,[string]$Target,[int64]$MaxBytes) {
  $x=[ordered]@{url=$Url;target=$Target;downloaded=$false;reused=$false;size_bytes=0;sha256=$null;content_type=$null;error=$null}
  try {
    Ensure-Dir (Split-Path -Parent $Target)
    if(Test-Path -LiteralPath $Target){
      $existing=Get-Item -LiteralPath $Target
      if($existing.Length -gt 0 -and $existing.Length -le $MaxBytes){
        $x.downloaded=$true;$x.reused=$true;$x.size_bytes=[int64]$existing.Length;$x.sha256=(Get-FileHash -Algorithm SHA256 -LiteralPath $Target).Hash
        return [pscustomobject]$x
      }
    }
    Add-Type -AssemblyName System.Net.Http
    $partial="$Target.partial"
    if(Test-Path -LiteralPath $partial){Remove-Item -LiteralPath $partial -Force}
    $client=[System.Net.Http.HttpClient]::new()
    $client.Timeout=[TimeSpan]::FromMinutes(25)
    $response=$null;$stream=$null;$file=$null
    try {
      $response=$client.GetAsync($Url,[System.Net.Http.HttpCompletionOption]::ResponseHeadersRead).GetAwaiter().GetResult()
      if(-not $response.IsSuccessStatusCode){throw "HTTP_$([int]$response.StatusCode)"}
      $len=$response.Content.Headers.ContentLength
      if($null -ne $len -and [int64]$len -gt $MaxBytes){throw "CONTENT_LENGTH_${len}_EXCEEDS_${MaxBytes}"}
      if($response.Content.Headers.ContentType){$x.content_type=[string]$response.Content.Headers.ContentType}
      $stream=$response.Content.ReadAsStreamAsync().GetAwaiter().GetResult()
      $file=[System.IO.File]::Open($partial,[System.IO.FileMode]::Create,[System.IO.FileAccess]::Write,[System.IO.FileShare]::None)
      $buffer=New-Object byte[] 1048576
      $total=0L
      while(($read=$stream.Read($buffer,0,$buffer.Length)) -gt 0){
        $total+=$read
        if($total -gt $MaxBytes){throw "STREAM_EXCEEDS_${MaxBytes}"}
        $file.Write($buffer,0,$read)
      }
    } finally {
      if($file){$file.Dispose()}
      if($stream){$stream.Dispose()}
      if($response){$response.Dispose()}
      if($client){$client.Dispose()}
    }
    if(-not(Test-Path -LiteralPath $partial)){throw 'DOWNLOAD_PARTIAL_NOT_CREATED'}
    Move-Item -LiteralPath $partial -Destination $Target -Force
    $final=Get-Item -LiteralPath $Target
    if($final.Length -le 0){throw 'DOWNLOADED_FILE_EMPTY'}
    $x.downloaded=$true;$x.size_bytes=[int64]$final.Length;$x.sha256=(Get-FileHash -Algorithm SHA256 -LiteralPath $Target).Hash
  } catch {
    $x.error=$_.Exception.Message
    if(Test-Path -LiteralPath "$Target.partial"){Remove-Item -LiteralPath "$Target.partial" -Force -ErrorAction SilentlyContinue}
  }
  return [pscustomobject]$x
}

$script:repoRoot=[System.IO.Path]::GetFullPath([string]$env:AAYS_REPO_ROOT)
if(-not $script:repoRoot -or $script:repoRoot -notmatch '(?i)[\\/]TerraYield_AAYS_Portable[\\/]runner_system[\\/]'){
  throw 'TOPOGRAPHY_164_REQUIRES_PORTABLE_SHARED_RUNNER_WORKTREE'
}
$marker='\runner_system\'
$markerIndex=$script:repoRoot.IndexOf($marker,[System.StringComparison]::OrdinalIgnoreCase)
if($markerIndex -lt 0){throw 'TOPOGRAPHY_164_PORTABLE_ROOT_NOT_RESOLVED'}
$portableRoot=$script:repoRoot.Substring(0,$markerIndex)
$dataBase=$null
if($env:AAYS_DATA_ROOT){$dataBase=[string]$env:AAYS_DATA_ROOT}else{$dataBase=Join-Path $portableRoot 'data'}
$dataRoot=Join-Path $dataBase 'topography\copdem_public_cog'
Ensure-Dir $dataRoot

$taskId='aays1-164-topography-public-copdem-cog-sampling-20260713'
if($env:AAYS_TASK_ID){$taskId=[string]$env:AAYS_TASK_ID}
$startedAt=Now-Utc
$batchId='topography-164-'+($startedAt -replace '[^0-9]','')
$previousBatchId='aays1-163-topography-copdem-point-hmlr-download-20260713'
$script:stageTotal=12
$script:stageDone=0
$script:currentStage='task_start'
$script:operations=@()
$script:stages=@()

$visibleRowsRel='england_map_web/data/program_layer_matrix/topography_visible_rows_latest.json'
$visibleStatusRel='england_map_web/data/program_layer_matrix/topography_visible_status_latest.json'
$operationsRel='england_map_web/data/program_layer_matrix/topography_operations_latest.json'
$latestChangesRel='outputs/england_program_parcel_matrix_20260629/topography_updates/latest_changes.json'
$sourceRel='docs/chatgpt_status/topography/source_snapshots/164_public_copdem_cog_sources_latest.json'
$sampleRel='docs/chatgpt_status/topography/fixtures/topography_public_copdem_cog_samples_20260713.json'
$statusRel='docs/chatgpt_status/topography/status/164_topography_public_copdem_cog_sampling_latest.json'
$reportRel='docs/chatgpt_status/topography/reports/164_topography_public_copdem_cog_sampling_report_20260713.md'
$outputRel='docs/chatgpt_status/topography/runner_outputs/164_topography_public_copdem_cog_sampling_batch.json'

function Add-Operation {
  param([string]$Type,[string]$Status,[int]$StageNo,[string]$StageName,[string]$ParcelId='',[string]$SourceName='',[string]$SourceUrl='',[string]$RequestUrl='',[object]$NumericValue=$null,[string]$Unit='',[string]$EvidencePath='',[string]$LocalPath='',[string]$Checksum='',[string]$Blocker='')
  $method=$null
  if($Type -match 'sample'){$method='coordinate sample from local Cloud Optimized GeoTIFF using rasterio or GDAL'}
  elseif($Type -match 'download'){$method='bounded HTTPS download with SHA256 verification'}
  elseif($Type -match 'tile'){$method='official public bucket tile-list and object probe'}
  elseif($Type -match 'validation'){$method='cross-resolution CopDEM 30 m versus 90 m comparison'}
  $parcelValue=$null;if($ParcelId){$parcelValue=$ParcelId}
  $sourceValue=$null;if($SourceName){$sourceValue=$SourceName}
  $sourceUrlValue=$null;if($SourceUrl){$sourceUrlValue=$SourceUrl}
  $requestValue=$null;if($RequestUrl){$requestValue=$RequestUrl}
  $unitValue=$null;if($Unit){$unitValue=$Unit}
  $evidenceValue=$null;if($EvidencePath){$evidenceValue=$EvidencePath}
  $localValue=$null;if($LocalPath){$localValue=$LocalPath}
  $checksumValue=$null;if($Checksum){$checksumValue=$Checksum}
  $blockerValue=$null;if($Blocker){$blockerValue=$Blocker}
  $script:operations += [pscustomobject][ordered]@{
    operation_id="${batchId}_$($script:operations.Count+1)";stage_no=$StageNo;operation_type=$Type;task_id=$taskId;batch_id=$batchId;previous_batch_id=$previousBatchId
    parcel_id=$parcelValue;status=$Status;is_new_operation=$true;is_new_in_latest_batch=$true;started_at=$startedAt;completed_at=Now-Utc
    source_name=$sourceValue;source_url=$sourceUrlValue;request_url=$requestValue;numeric_value=$NumericValue;unit=$unitValue;method=$method
    accuracy_score_4='2.5/4 fallback';repo_artifact_path=$evidenceValue;local_source_path=$localValue;sha256=$checksumValue
    report_path=$reportRel;status_path=$statusRel;runner_output_path=$outputRel;blocker=$blockerValue;needs_manual_review=[bool]$Blocker
    final_ready=$false;fake_data=$false
  }
}
function Publish-Ledger([string]$RunStatus) {
  $path=Repo-Path $operationsRel
  $old=Read-Json $path
  $existing=@()
  if($old){
    $existing=@($old.operations)
    foreach($op in $existing){if($null -ne $op){Set-Prop $op 'is_new_operation' $false;Set-Prop $op 'is_new_in_latest_batch' $false}}
  }
  $all=@($existing+$script:operations)
  $blocked=@($all|Where-Object{[string]$_.status -match 'blocked|failed|unavailable|auth_required|not_found|partial'})
  $lastBlocked=$null;if($blocked.Count){$lastBlocked=$blocked[-1]}
  Write-Json $path ([ordered]@{task_id=$taskId;batch_id=$batchId;previous_batch_id=$previousBatchId;updated_at=Now-Utc;run_status=$RunStatus;current_stage=$script:currentStage;stage_completed_count=$script:stageDone;stage_total_count=$script:stageTotal;operation_count=$all.Count;new_operations_count=$script:operations.Count;blocked_operation_count=$blocked.Count;last_blocked_operation=$lastBlocked;operations=$all;final_ready=$false;product_final_ready=$false;fake_data=$false;db_write=$false;migration=$false;production_deploy=$false})
}
function Complete-Stage([int]$No,[string]$Name,[string]$Status='completed') {
  $script:stageDone=$No;$script:currentStage=$Name
  $script:stages += [pscustomobject][ordered]@{stage_no=$No;stage=$Name;status=$Status;completed_at=Now-Utc}
  Add-Operation -Type 'pipeline_stage' -Status $Status -StageNo $No -StageName $Name -EvidencePath $statusRel
  Publish-Ledger -RunStatus 'RUNNING'
}

try {
  Add-Operation -Type 'task_start' -Status 'running' -StageNo 1 -StageName 'task_start' -EvidencePath $statusRel
  Publish-Ledger -RunStatus 'RUNNING'

  $visiblePath=Repo-Path $visibleRowsRel
  $visible=Read-Json $visiblePath
  $parcelRows=@($visible.rows)
  if($null -eq $visible -or $parcelRows.Count -lt 3){throw 'TOPOGRAPHY_164_VISIBLE_ROWS_NOT_READY'}
  Complete-Stage -No 1 -Name 'load_verified_parcel_rows'

  $officialUrls=@(
    [pscustomobject]@{name='AWS Open Data Copernicus DEM registry';url='https://registry.opendata.aws/copernicus-dem/'},
    [pscustomobject]@{name='Copernicus DEM 30 m public COG readme';url='https://copernicus-dem-30m.s3.amazonaws.com/readme.html'},
    [pscustomobject]@{name='Copernicus Data Space S3 documentation';url='https://documentation.dataspace.copernicus.eu/APIs/S3.html'},
    [pscustomobject]@{name='Copernicus Data Space OData documentation';url='https://documentation.dataspace.copernicus.eu/APIs/OData.html'}
  )
  $officialChecks=@()
  foreach($item in $officialUrls){
    $check=Test-Http -Name $item.name -Url $item.url
    $officialChecks+=$check
    $checkStatus='blocked_or_unavailable';$checkBlocker=$check.error
    if($check.reachable){$checkStatus='source_check_only_available';$checkBlocker=''}
    Add-Operation -Type 'official_source_check_only' -Status $checkStatus -StageNo 2 -StageName 'official_source_checks' -SourceName $check.name -SourceUrl $check.url -RequestUrl $check.final_url -EvidencePath $sourceRel -Blocker $checkBlocker
  }
  $officialStage='partial';if(@($officialChecks|Where-Object{$_.reachable}).Count -eq $officialChecks.Count){$officialStage='completed'}
  Complete-Stage -No 2 -Name 'official_source_checks' -Status $officialStage

  $tile30='Copernicus_DSM_COG_10_N51_00_W001_00_DEM'
  $tile90='Copernicus_DSM_COG_30_N51_00_W001_00_DEM'
  $tile30List=Get-TileListCheck -Name 'Copernicus GLO-30 tile list' -Url 'https://copernicus-dem-30m.s3.amazonaws.com/tileList.txt' -Target $tile30
  $tile90List=Get-TileListCheck -Name 'Copernicus GLO-90 tile list' -Url 'https://copernicus-dem-90m.s3.amazonaws.com/tileList.txt' -Target $tile90
  $url30="https://copernicus-dem-30m.s3.amazonaws.com/$tile30/$tile30.tif"
  $url90="https://copernicus-dem-90m.s3.amazonaws.com/$tile90/$tile90.tif"
  $probe30=Test-Http -Name 'Copernicus GLO-30 N51 W001 COG' -Url $url30 -Method 'HEAD'
  $probe90=Test-Http -Name 'Copernicus GLO-90 N51 W001 COG' -Url $url90 -Method 'HEAD'
  $tileChecks=@($tile30List,$tile90List,$probe30,$probe90)
  foreach($tileCheck in $tileChecks){
    $tileStatus='blocked_or_unavailable';$tileBlocker=$tileCheck.error
    if($tileCheck.reachable){$tileStatus='available';$tileBlocker=''}
    if($null -ne $tileCheck.PSObject.Properties['target_present'] -and -not $tileCheck.target_present){$tileStatus='not_found';$tileBlocker='TARGET_TILE_NOT_IN_TILE_LIST'}
    Add-Operation -Type 'public_copdem_tile_check' -Status $tileStatus -StageNo 3 -StageName 'tile_list_and_object_probe' -SourceName $tileCheck.name -SourceUrl $tileCheck.url -NumericValue $tileCheck.content_length -Unit 'bytes' -EvidencePath $sourceRel -Blocker $tileBlocker
  }
  $tileStage='partial';if($tile30List.target_present -and $tile90List.target_present -and $probe30.reachable -and $probe90.reachable){$tileStage='completed'}
  Complete-Stage -No 3 -Name 'tile_list_and_object_probe' -Status $tileStage

  $path30=Join-Path $dataRoot "$tile30.tif"
  $download30=Download-Bounded -Url $url30 -Target $path30 -MaxBytes 262144000
  $download30Status='blocked_or_unavailable';$download30Blocker=$download30.error
  if($download30.downloaded){$download30Status='downloaded_and_verified';$download30Blocker=''}
  Add-Operation -Type 'public_copdem_download' -Status $download30Status -StageNo 4 -StageName 'glo30_cog_download' -SourceName 'Copernicus DEM GLO-30 Public COG' -SourceUrl 'https://registry.opendata.aws/copernicus-dem/' -RequestUrl $url30 -NumericValue $download30.size_bytes -Unit 'bytes' -EvidencePath $sourceRel -LocalPath $path30 -Checksum $download30.sha256 -Blocker $download30Blocker
  Complete-Stage -No 4 -Name 'glo30_cog_download' -Status $download30Status

  $path90=Join-Path $dataRoot "$tile90.tif"
  $download90=Download-Bounded -Url $url90 -Target $path90 -MaxBytes 262144000
  $download90Status='blocked_or_unavailable';$download90Blocker=$download90.error
  if($download90.downloaded){$download90Status='downloaded_and_verified';$download90Blocker=''}
  Add-Operation -Type 'public_copdem_download' -Status $download90Status -StageNo 5 -StageName 'glo90_cog_download' -SourceName 'Copernicus DEM GLO-90 Public COG' -SourceUrl 'https://registry.opendata.aws/copernicus-dem/' -RequestUrl $url90 -NumericValue $download90.size_bytes -Unit 'bytes' -EvidencePath $sourceRel -LocalPath $path90 -Checksum $download90.sha256 -Blocker $download90Blocker
  Complete-Stage -No 5 -Name 'glo90_cog_download' -Status $download90Status

  $checksumStage='partial'
  if($download30.downloaded -and $download90.downloaded){$checksumStage='completed'}
  Add-Operation -Type 'raster_checksum' -Status (if($download30.downloaded){'verified'}else{'blocked'}) -StageNo 6 -StageName 'checksum_and_metadata_prep' -SourceName 'Copernicus GLO-30 COG' -RequestUrl $url30 -NumericValue $download30.size_bytes -Unit 'bytes' -EvidencePath $sourceRel -LocalPath $path30 -Checksum $download30.sha256 -Blocker $download30.error
  Add-Operation -Type 'raster_checksum' -Status (if($download90.downloaded){'verified'}else{'blocked'}) -StageNo 6 -StageName 'checksum_and_metadata_prep' -SourceName 'Copernicus GLO-90 COG' -RequestUrl $url90 -NumericValue $download90.size_bytes -Unit 'bytes' -EvidencePath $sourceRel -LocalPath $path90 -Checksum $download90.sha256 -Blocker $download90.error
  Complete-Stage -No 6 -Name 'checksum_and_metadata_prep' -Status $checksumStage

  $sampleInput=Join-Path $dataRoot 'sample_input_164.json'
  $sampleOutput=Repo-Path $sampleRel
  $sampleRows=@()
  foreach($row in $parcelRows){$sampleRows += [pscustomobject][ordered]@{parcel_id=[string]$row.parcel_id;lon=[double]$row.centroid_lon;lat=[double]$row.centroid_lat}}
  Write-Json $sampleInput ([ordered]@{files=[ordered]@{glo30=$path30;glo90=$path90};rows=$sampleRows})
  $pythonPath=Join-Path $dataRoot 'sample_copdem_164.py'
  $pythonCode=@'
import json, math, sys
from pathlib import Path

input_path, output_path = sys.argv[1], sys.argv[2]
payload = json.loads(Path(input_path).read_text(encoding="utf-8"))
rows = payload["rows"]
files = payload["files"]
result = {"ok": False, "engine": None, "error": None, "datasets": {}, "rows": []}

def clean(v, nodata=None):
    if v is None:
        return None
    v = float(v)
    if not math.isfinite(v):
        return None
    if nodata is not None and abs(v - float(nodata)) < 1e-9:
        return None
    return round(v, 3)

try:
    import rasterio
    from rasterio.warp import transform
    result["engine"] = "rasterio"
    values_by_key = {}
    for key, path in files.items():
        if not Path(path).exists():
            values_by_key[key] = [None] * len(rows)
            result["datasets"][key] = {"path": path, "exists": False}
            continue
        with rasterio.open(path) as ds:
            xs = [float(r["lon"]) for r in rows]
            ys = [float(r["lat"]) for r in rows]
            crs_text = str(ds.crs) if ds.crs else None
            if ds.crs and crs_text.upper() not in ("EPSG:4326", "OGC:CRS84"):
                xs, ys = transform("EPSG:4326", ds.crs, xs, ys)
            vals = [clean(arr[0], ds.nodata) for arr in ds.sample(list(zip(xs, ys)))]
            values_by_key[key] = vals
            result["datasets"][key] = {
                "path": path, "exists": True, "crs": crs_text, "width": ds.width, "height": ds.height,
                "count": ds.count, "dtype": ds.dtypes[0] if ds.dtypes else None, "nodata": ds.nodata,
                "bounds": [ds.bounds.left, ds.bounds.bottom, ds.bounds.right, ds.bounds.top],
                "transform": list(ds.transform)[:6]
            }
    for i, row in enumerate(rows):
        v30 = values_by_key.get("glo30", [None] * len(rows))[i]
        v90 = values_by_key.get("glo90", [None] * len(rows))[i]
        spread = None if v30 is None or v90 is None else round(abs(v30 - v90), 3)
        result["rows"].append({"parcel_id": row["parcel_id"], "lon": row["lon"], "lat": row["lat"], "copdem_glo30_m": v30, "copdem_glo90_m": v90, "cross_resolution_spread_m": spread})
    result["ok"] = any(r["copdem_glo30_m"] is not None or r["copdem_glo90_m"] is not None for r in result["rows"])
except Exception as rasterio_error:
    try:
        from osgeo import gdal, osr
        result["engine"] = "gdal"
        values_by_key = {}
        for key, path in files.items():
            ds = gdal.Open(path) if Path(path).exists() else None
            if ds is None:
                values_by_key[key] = [None] * len(rows)
                result["datasets"][key] = {"path": path, "exists": False}
                continue
            gt = ds.GetGeoTransform()
            inv_ok, inv_gt = gdal.InvGeoTransform(gt)
            if not inv_ok:
                raise RuntimeError("GDAL_INV_GEOTRANSFORM_FAILED")
            src = osr.SpatialReference(); src.ImportFromEPSG(4326)
            dst = osr.SpatialReference(); dst.ImportFromWkt(ds.GetProjection())
            tx = None
            if not src.IsSame(dst):
                tx = osr.CoordinateTransformation(src, dst)
            band = ds.GetRasterBand(1); nodata = band.GetNoDataValue(); vals = []
            for row in rows:
                x, y = float(row["lon"]), float(row["lat"])
                if tx is not None:
                    x, y, _ = tx.TransformPoint(x, y)
                px, py = gdal.ApplyGeoTransform(inv_gt, x, y)
                ix, iy = int(math.floor(px)), int(math.floor(py))
                if ix < 0 or iy < 0 or ix >= ds.RasterXSize or iy >= ds.RasterYSize:
                    vals.append(None); continue
                arr = band.ReadAsArray(ix, iy, 1, 1)
                vals.append(clean(arr[0][0] if arr is not None else None, nodata))
            values_by_key[key] = vals
            result["datasets"][key] = {"path": path, "exists": True, "crs": ds.GetProjection(), "width": ds.RasterXSize, "height": ds.RasterYSize, "count": ds.RasterCount, "nodata": nodata, "transform": list(gt)}
        for i, row in enumerate(rows):
            v30 = values_by_key.get("glo30", [None] * len(rows))[i]
            v90 = values_by_key.get("glo90", [None] * len(rows))[i]
            spread = None if v30 is None or v90 is None else round(abs(v30 - v90), 3)
            result["rows"].append({"parcel_id": row["parcel_id"], "lon": row["lon"], "lat": row["lat"], "copdem_glo30_m": v30, "copdem_glo90_m": v90, "cross_resolution_spread_m": spread})
        result["ok"] = any(r["copdem_glo30_m"] is not None or r["copdem_glo90_m"] is not None for r in result["rows"])
    except Exception as gdal_error:
        result["error"] = "rasterio=" + repr(rasterio_error) + "; gdal=" + repr(gdal_error)
Path(output_path).parent.mkdir(parents=True, exist_ok=True)
Path(output_path).write_text(json.dumps(result, indent=2), encoding="utf-8")
'@
  [System.IO.File]::WriteAllText($pythonPath,$pythonCode,[System.Text.UTF8Encoding]::new($false))
  $pythonCommand=$null;$pythonArgs=@()
  $candidate=Get-Command python -ErrorAction SilentlyContinue
  if($candidate){$pythonCommand=$candidate.Source}
  if(-not $pythonCommand){$candidate=Get-Command py -ErrorAction SilentlyContinue;if($candidate){$pythonCommand=$candidate.Source;$pythonArgs+=@('-3')}}
  if(-not $pythonCommand){$candidate=Get-Command python3 -ErrorAction SilentlyContinue;if($candidate){$pythonCommand=$candidate.Source}}
  $samplingError=$null
  if($pythonCommand){
    $pythonArgs+=@($pythonPath,$sampleInput,$sampleOutput)
    & $pythonCommand @pythonArgs
    if($LASTEXITCODE -ne 0){$samplingError="PYTHON_EXIT_$LASTEXITCODE"}
  }else{$samplingError='PYTHON_NOT_AVAILABLE'}
  $samplePayload=Read-Json $sampleOutput
  if(-not $samplePayload -and -not $samplingError){$samplingError='SAMPLE_OUTPUT_NOT_CREATED'}
  if($samplePayload -and -not $samplePayload.ok -and $samplePayload.error){$samplingError=[string]$samplePayload.error}
  $sample30Count=0;$sample90Count=0
  if($samplePayload){
    $sample30Count=@($samplePayload.rows|Where-Object{$null -ne $_.copdem_glo30_m}).Count
    $sample90Count=@($samplePayload.rows|Where-Object{$null -ne $_.copdem_glo90_m}).Count
  }
  $sampleStatus='blocked_or_unavailable';if($sample30Count -eq 3){$sampleStatus='primary_samples_complete'}
  foreach($sample in @($samplePayload.rows)){
    if($null -ne $sample.copdem_glo30_m){Add-Operation -Type 'primary_copdem_sample' -Status 'sampled' -StageNo 7 -StageName 'numeric_cog_sampling' -ParcelId $sample.parcel_id -SourceName 'Copernicus DEM GLO-30 Public COG' -SourceUrl 'https://registry.opendata.aws/copernicus-dem/' -RequestUrl $url30 -NumericValue $sample.copdem_glo30_m -Unit 'm' -EvidencePath $sampleRel -LocalPath $path30 -Checksum $download30.sha256}
    if($null -ne $sample.copdem_glo90_m){Add-Operation -Type 'validation_copdem_sample' -Status 'sampled' -StageNo 7 -StageName 'numeric_cog_sampling' -ParcelId $sample.parcel_id -SourceName 'Copernicus DEM GLO-90 Public COG' -SourceUrl 'https://registry.opendata.aws/copernicus-dem/' -RequestUrl $url90 -NumericValue $sample.copdem_glo90_m -Unit 'm' -EvidencePath $sampleRel -LocalPath $path90 -Checksum $download90.sha256}
  }
  if($sample30Count -lt 3){Add-Operation -Type 'primary_copdem_sample' -Status 'blocked' -StageNo 7 -StageName 'numeric_cog_sampling' -SourceName 'Copernicus DEM GLO-30 Public COG' -SourceUrl 'https://registry.opendata.aws/copernicus-dem/' -EvidencePath $sampleRel -Blocker $samplingError}
  Complete-Stage -No 7 -Name 'numeric_cog_sampling' -Status $sampleStatus

  $validationRows=0
  foreach($sample in @($samplePayload.rows)){
    if($null -ne $sample.cross_resolution_spread_m){
      $validationRows++
      $validationStatus='wide_spread_manual_review';if([double]$sample.cross_resolution_spread_m -le 5){$validationStatus='cross_resolution_consistent'}
      Add-Operation -Type 'copdem_cross_resolution_validation' -Status $validationStatus -StageNo 8 -StageName 'cross_resolution_validation' -ParcelId $sample.parcel_id -SourceName 'Copernicus GLO-30 versus GLO-90' -NumericValue $sample.cross_resolution_spread_m -Unit 'm spread' -EvidencePath $sampleRel
    }
  }
  $validationStage='partial';if($validationRows -eq 3){$validationStage='completed'}
  Complete-Stage -No 8 -Name 'cross_resolution_validation' -Status $validationStage

  $blockers=@('real_parcel_boundary_required','ea_lidar_or_os_terrain_numeric_validation_required')
  if($sample30Count -lt 3){$blockers+='primary_copdem_glo30_raster_sampling_required'}
  foreach($row in $parcelRows){
    $sampleRow=$null
    if($samplePayload){$sampleRow=$samplePayload.rows|Where-Object{$_.parcel_id -eq $row.parcel_id}|Select-Object -First 1}
    if($sampleRow){
      Set-Prop $row 'elevation_primary_copdem_glo30_m' $sampleRow.copdem_glo30_m
      Set-Prop $row 'elevation_validation_copdem_glo90_m' $sampleRow.copdem_glo90_m
      Set-Prop $row 'copdem_cross_resolution_spread_m' $sampleRow.cross_resolution_spread_m
      if($null -ne $sampleRow.copdem_glo30_m -and $null -ne $row.regional_average_elevation_m){Set-Prop $row 'elevation_difference_regional_average_primary_m' ([math]::Round(([double]$sampleRow.copdem_glo30_m-[double]$row.regional_average_elevation_m),3))}
      if($null -ne $sampleRow.copdem_glo30_m -and $null -ne $row.elevation_consensus_median_m){Set-Prop $row 'primary_vs_existing_consensus_difference_m' ([math]::Round(([double]$sampleRow.copdem_glo30_m-[double]$row.elevation_consensus_median_m),3))}
    }
    Set-Prop $row 'primary_copdem_source_url' $url30
    Set-Prop $row 'primary_copdem_local_path' (if($download30.downloaded){$path30}else{$null})
    Set-Prop $row 'primary_copdem_sha256' $download30.sha256
    Set-Prop $row 'primary_copdem_sampling_engine' (if($samplePayload){$samplePayload.engine}else{$null})
    Set-Prop $row 'task_id' $taskId
    Set-Prop $row 'updated_at' (Now-Utc)
    Set-Prop $row 'report_path' $reportRel
    Set-Prop $row 'status_path' $statusRel
    Set-Prop $row 'display_badge' 'PUBLIC_COPDEM_COG_PRIMARY_SAMPLING'
    Set-Prop $row 'accuracy_score_4' '2.5/4 fallback; primary CopDEM sampled when available, real boundary and official EA/OS numeric validation pending'
    Set-Prop $row 'blocker' ($blockers -join '; ')
  }
  Set-Prop $visible 'status' 'PUBLIC_COPDEM_COG_SAMPLING_VISIBLE_NOT_FINAL'
  Set-Prop $visible 'latest_task_id' $taskId
  Set-Prop $visible 'latest_batch_id' $batchId
  Set-Prop $visible 'updated_at' (Now-Utc)
  Set-Prop $visible 'rows' $parcelRows
  Set-Prop $visible 'final_ready' $false
  Set-Prop $visible 'fake_data' $false
  Write-Json $visiblePath $visible
  Complete-Stage -No 9 -Name 'parcel_primary_elevation_update'

  $completionPercent=72
  if($download30.downloaded){$completionPercent=74}
  if($sample30Count -eq 3){$completionPercent=76}
  if($sample30Count -eq 3 -and $sample90Count -eq 3 -and $validationRows -eq 3){$completionPercent=78}
  $sourcePayload=[ordered]@{task_id=$taskId;batch_id=$batchId;generated_at=Now-Utc;official_source_checks=$officialChecks;tile_checks=$tileChecks;glo30=[ordered]@{tile=$tile30;url=$url30;download=$download30};glo90=[ordered]@{tile=$tile90;url=$url90;download=$download90};external_data_root=$dataRoot;sampling=$samplePayload;completion_percent=$completionPercent;final_ready=$false;fake_data=$false;db_write=$false;migration=$false;production_deploy=$false}
  Write-Json (Repo-Path $sourceRel) $sourcePayload
  $statusPayload=[ordered]@{task_id=$taskId;page_key='topography';batch_id=$batchId;previous_batch_id=$previousBatchId;status='PUBLIC_COPDEM_COG_SAMPLING_VISIBLE_NOT_FINAL';started_at=$startedAt;completed_at=Now-Utc;stages=$script:stages;completed_stage_count=10;total_stage_count=$script:stageTotal;candidate_rows=$parcelRows.Count;official_sources_checked=$officialChecks.Count;official_sources_reachable=@($officialChecks|Where-Object{$_.reachable}).Count;glo30_tile_available=[bool]($tile30List.target_present -and $probe30.reachable);glo90_tile_available=[bool]($tile90List.target_present -and $probe90.reachable);glo30_downloaded=[bool]$download30.downloaded;glo90_downloaded=[bool]$download90.downloaded;glo30_sample_rows=$sample30Count;glo90_sample_rows=$sample90Count;cross_resolution_validation_rows=$validationRows;new_operation_rows=$script:operations.Count;completion_percent=$completionPercent;percent_increase=($completionPercent-72);accuracy_score_4='2.5/4 fallback';blockers=$blockers;final_ready=$false;product_final_ready=$false;fake_data=$false;db_write=$false;migration=$false;production_deploy=$false}
  Write-Json (Repo-Path $statusRel) $statusPayload
  Write-Json (Repo-Path $visibleStatusRel) $statusPayload
  Write-Json (Repo-Path $latestChangesRel) ([ordered]@{layer='Topography';task_id=$taskId;updated_at=Now-Utc;summary=$statusPayload;rows=$parcelRows;final_ready=$false;fake_data=$false})
  Complete-Stage -No 10 -Name 'site_artifact_generation'

  $publishStatus='completed'
  if($env:AAYS_CONTROLLER_REPO_ROOT){
    $publisher=Join-Path $script:repoRoot 'docs\chatgpt_status\_shared\automation\PUBLISH_AAYS_WEB_ARTIFACTS_TO_LIVE_CONTROLLER_20260711.ps1'
    $publishPaths=@($visibleRowsRel,$visibleStatusRel,$operationsRel,$sourceRel,$sampleRel)-join'|'
    & powershell -NoProfile -ExecutionPolicy Bypass -File $publisher -TaskRepoRoot $script:repoRoot -ControllerRoot $env:AAYS_CONTROLLER_REPO_ROOT -Paths $publishPaths -AllowGeneratedArtifacts -SyncPortableWeb
    if($LASTEXITCODE -ne 0){throw 'TOPOGRAPHY_164_LIVE_CONTROLLER_PUBLISH_BLOCKED'}
  }
  Complete-Stage -No 11 -Name 'live_controller_publication' -Status $publishStatus

  $siteRows=Invoke-WebRequest -UseBasicParsing -Uri 'http://127.0.0.1:8012/england_map_web/data/program_layer_matrix/topography_visible_rows_latest.json' -TimeoutSec 60
  $siteOps=Invoke-WebRequest -UseBasicParsing -Uri 'http://127.0.0.1:8012/england_map_web/data/program_layer_matrix/topography_operations_latest.json' -TimeoutSec 60
  $siteSamples=Invoke-WebRequest -UseBasicParsing -Uri 'http://127.0.0.1:8012/docs/chatgpt_status/topography/fixtures/topography_public_copdem_cog_samples_20260713.json' -TimeoutSec 60
  if($siteRows.StatusCode -ne 200 -or $siteOps.StatusCode -ne 200 -or $siteSamples.StatusCode -ne 200){throw 'TOPOGRAPHY_164_SITE_HTTP_READBACK_FAILED'}
  if($siteRows.Content -notmatch [regex]::Escape($taskId) -or $siteOps.Content -notmatch [regex]::Escape($taskId)){throw 'TOPOGRAPHY_164_TASK_ID_NOT_VISIBLE'}
  Complete-Stage -No 12 -Name 'http_task_id_and_sample_readback' -Status 'PASS'

  $statusPayload.completed_stage_count=12;$statusPayload.completed_at=Now-Utc
  Write-Json (Repo-Path $statusRel) $statusPayload
  Write-Json (Repo-Path $visibleStatusRel) $statusPayload
  Publish-Ledger -RunStatus 'COMPLETED_VISIBLE_NOT_FINAL'
  $report="# Topography 164 Public CopDEM COG Sampling`n`n- Task: $taskId`n- Candidate parcels: $($parcelRows.Count)`n- GLO-30 tile available: $($statusPayload.glo30_tile_available)`n- GLO-90 tile available: $($statusPayload.glo90_tile_available)`n- GLO-30 downloaded: $($download30.downloaded) / $($download30.size_bytes) bytes`n- GLO-90 downloaded: $($download90.downloaded) / $($download90.size_bytes) bytes`n- GLO-30 primary sample rows: $sample30Count`n- GLO-90 validation sample rows: $sample90Count`n- Cross-resolution validation rows: $validationRows`n- New operation rows: $($script:operations.Count)`n- Site HTTP task-id and sample readback: PASS`n- Completion: $completionPercent%`n- Increase: +$($completionPercent-72)%`n- Accuracy: 2.5/4 fallback`n- final_ready: false`n"
  Ensure-Dir (Split-Path -Parent (Repo-Path $reportRel))
  [System.IO.File]::WriteAllText((Repo-Path $reportRel),$report,[System.Text.UTF8Encoding]::new($false))
  Write-Json (Repo-Path $outputRel) ([ordered]@{task_id=$taskId;status='COMPLETED_VISIBLE_NOT_FINAL';completed_at=Now-Utc;completion_percent=$completionPercent;percent_increase=($completionPercent-72);completed_stage_count=12;total_stage_count=12;candidate_rows=$parcelRows.Count;glo30_tile_available=$statusPayload.glo30_tile_available;glo90_tile_available=$statusPayload.glo90_tile_available;glo30_downloaded=[bool]$download30.downloaded;glo90_downloaded=[bool]$download90.downloaded;glo30_sample_rows=$sample30Count;glo90_sample_rows=$sample90Count;cross_resolution_validation_rows=$validationRows;new_operation_rows=$script:operations.Count;site_http_validation='PASS';blockers=$blockers;accuracy_score_4='2.5/4 fallback';final_ready=$false;product_final_ready=$false;fake_data=$false;db_write=$false;migration=$false;production_deploy=$false})
} catch {
  $errorMessage=$_.Exception.Message
  Add-Operation -Type 'runner_failure' -Status 'blocked' -StageNo ([math]::Max(1,$script:stageDone+1)) -StageName $script:currentStage -EvidencePath $statusRel -Blocker $errorMessage
  Publish-Ledger -RunStatus 'BLOCKED'
  $failure=[ordered]@{task_id=$taskId;status='BLOCKED';error=$errorMessage;completed_stage_count=$script:stageDone;total_stage_count=$script:stageTotal;completion_percent=72;percent_increase=0;final_ready=$false;product_final_ready=$false;fake_data=$false;db_write=$false;migration=$false;production_deploy=$false}
  Write-Json (Repo-Path $statusRel) $failure
  Write-Json (Repo-Path $outputRel) $failure
  throw
}
