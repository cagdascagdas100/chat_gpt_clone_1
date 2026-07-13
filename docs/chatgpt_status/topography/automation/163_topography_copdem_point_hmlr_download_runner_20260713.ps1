[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'

function Now-Utc { (Get-Date).ToUniversalTime().ToString('o') }
function Ensure-Dir([string]$Path) {
  if ($Path -and -not (Test-Path -LiteralPath $Path)) {
    New-Item -ItemType Directory -Force -Path $Path | Out-Null
  }
}
function Write-Json([string]$Path, [object]$Value) {
  Ensure-Dir (Split-Path -Parent $Path)
  $tmp = "$Path.tmp"
  [System.IO.File]::WriteAllText($tmp, (($Value | ConvertTo-Json -Depth 100) + "`n"), [System.Text.UTF8Encoding]::new($false))
  Move-Item -LiteralPath $tmp -Destination $Path -Force
}
function Read-Json([string]$Path) {
  if (-not (Test-Path -LiteralPath $Path)) { return $null }
  return (Get-Content -LiteralPath $Path -Raw -Encoding UTF8 | ConvertFrom-Json)
}
function Set-Prop([object]$Object,[string]$Name,[object]$Value) {
  Add-Member -InputObject $Object -NotePropertyName $Name -NotePropertyValue $Value -Force
}
function Repo-Rel([string]$Path,[string]$Root) {
  $full = [System.IO.Path]::GetFullPath($Path)
  $base = [System.IO.Path]::GetFullPath($Root)
  if (-not $full.StartsWith($base,[System.StringComparison]::OrdinalIgnoreCase)) { return $full }
  return $full.Substring($base.Length).TrimStart('\','/').Replace('\','/')
}
function Test-Http([string]$Name,[string]$Url,[string]$Method='GET') {
  $x=[ordered]@{name=$Name;url=$Url;method=$Method;reachable=$false;status_code=$null;final_url=$null;content_length=$null;content_type=$null;error=$null}
  try {
    $r=Invoke-WebRequest -UseBasicParsing -Method $Method -Uri $Url -MaximumRedirection 10 -TimeoutSec 180 -Headers @{'User-Agent'='TerraYield-AAYS-Topography/1.0 primary-acquisition-163'}
    $x.status_code=[int]$r.StatusCode
    $x.reachable=($r.StatusCode -ge 200 -and $r.StatusCode -lt 400)
    if($r.BaseResponse -and $r.BaseResponse.ResponseUri){$x.final_url=[string]$r.BaseResponse.ResponseUri.AbsoluteUri}
    if($r.Headers['Content-Length']){$x.content_length=[int64]$r.Headers['Content-Length']}
    if($r.Headers['Content-Type']){$x.content_type=[string]$r.Headers['Content-Type']}
    $x['content']=$r.Content
  } catch {
    try{$x.status_code=[int]$_.Exception.Response.StatusCode.value__}catch{}
    $x.error=$_.Exception.Message
  }
  return [pscustomobject]$x
}
function Resolve-Links([string]$PageUrl,[string]$Html) {
  $result=@()
  foreach($m in [regex]::Matches($Html,'href\s*=\s*["'']([^"'']+)["'']',[System.Text.RegularExpressions.RegexOptions]::IgnoreCase)){
    $href=[System.Net.WebUtility]::HtmlDecode([string]$m.Groups[1].Value)
    if(-not $href -or $href.StartsWith('#') -or $href.StartsWith('javascript:')){continue}
    try{$result+=([uri]::new([uri]$PageUrl,$href)).AbsoluteUri}catch{}
  }
  return @($result|Select-Object -Unique)
}
function Invoke-CopDemPoint([double]$Lon,[double]$Lat,[string]$ParcelId) {
  $base='https://catalogue.dataspace.copernicus.eu/odata/v1/Products'
  $point=[string]::Format([Globalization.CultureInfo]::InvariantCulture,"POINT({0:R} {1:R})",$Lon,$Lat)
  $filter="Collection/Name eq 'COP-DEM' and OData.CSC.Intersects(area=geography'SRID=4326;$point')"
  $url=$base+'?$filter='+[uri]::EscapeDataString($filter)+'&$top=100&$expand=Attributes'
  $x=[ordered]@{parcel_id=$ParcelId;lon=$Lon;lat=$Lat;url=$url;reachable=$false;result_count=0;glo30_count=0;products=@();glo30_products=@();error=$null}
  try {
    $r=Invoke-RestMethod -Method Get -Uri $url -TimeoutSec 240 -Headers @{'User-Agent'='TerraYield-AAYS-Topography/1.0 CopDEM-point-163'}
    $p=@($r.value)
    $g=@($p|Where-Object{([string]$_.S3Path -match '(?i)COP-DEM_GLO-30') -or ([string]$_.Name -match '(?i)GLO.?30')})
    $x.reachable=$true;$x.result_count=$p.Count;$x.glo30_count=$g.Count
    $x.products=@($p|Select-Object -First 100 Id,Name,S3Path,ContentDate,PublicationDate,GeoFootprint,Attributes)
    $x.glo30_products=@($g|Select-Object -First 20 Id,Name,S3Path,ContentDate,PublicationDate,GeoFootprint,Attributes)
  } catch {$x.error=$_.Exception.Message}
  return [pscustomobject]$x
}
function Invoke-CopDemCollection([string]$Pattern) {
  $base='https://catalogue.dataspace.copernicus.eu/odata/v1/Products'
  $filter="Collection/Name eq 'COP-DEM' and contains(S3Path,'$Pattern')"
  $url=$base+'?$filter='+[uri]::EscapeDataString($filter)+'&$top=100&$expand=Attributes'
  $x=[ordered]@{pattern=$Pattern;url=$url;reachable=$false;result_count=0;products=@();error=$null}
  try{
    $r=Invoke-RestMethod -Method Get -Uri $url -TimeoutSec 240 -Headers @{'User-Agent'='TerraYield-AAYS-Topography/1.0 CopDEM-collection-163'}
    $p=@($r.value);$x.reachable=$true;$x.result_count=$p.Count;$x.products=@($p|Select-Object -First 100 Id,Name,S3Path,ContentDate,PublicationDate,GeoFootprint,Attributes)
  }catch{$x.error=$_.Exception.Message}
  return [pscustomobject]$x
}
function Get-ProductNodes([string]$ProductId) {
  $url="https://catalogue.dataspace.copernicus.eu/odata/v1/Products($ProductId)/Nodes?`$top=200"
  $x=[ordered]@{product_id=$ProductId;url=$url;reachable=$false;node_count=0;nodes=@();error=$null}
  try{
    $r=Invoke-RestMethod -Method Get -Uri $url -TimeoutSec 180 -Headers @{'User-Agent'='TerraYield-AAYS-Topography/1.0 CopDEM-nodes-163'}
    $nodes=@($r.value);$x.reachable=$true;$x.node_count=$nodes.Count;$x.nodes=@($nodes|Select-Object -First 200 Id,Name,ContentLength,ChildrenNumber,Nodes)
  }catch{$x.error=$_.Exception.Message}
  return [pscustomobject]$x
}
function Parse-HmlrForm([string]$PageUrl,[string]$Html) {
  $x=[ordered]@{form_action=$null;form_method='GET';select_name=$null;barnet_value=$null;hidden=@{};options=@();error=$null}
  try{
    $forms=[regex]::Matches($Html,'(?is)<form\b([^>]*)>(.*?)</form>')
    foreach($form in $forms){
      $attrs=$form.Groups[1].Value;$body=$form.Groups[2].Value
      if($body -notmatch '(?i)Barnet'){continue}
      $am=[regex]::Match($attrs,'(?i)\baction\s*=\s*["'']([^"'']+)["'']')
      $mm=[regex]::Match($attrs,'(?i)\bmethod\s*=\s*["'']([^"'']+)["'']')
      if($am.Success){$x.form_action=([uri]::new([uri]$PageUrl,[System.Net.WebUtility]::HtmlDecode($am.Groups[1].Value))).AbsoluteUri}else{$x.form_action=$PageUrl}
      if($mm.Success){$x.form_method=$mm.Groups[1].Value.ToUpperInvariant()}
      foreach($im in [regex]::Matches($body,'(?is)<input\b([^>]*)>')){
        $ia=$im.Groups[1].Value
        $nm=[regex]::Match($ia,'(?i)\bname\s*=\s*["'']([^"'']+)["'']')
        if(-not $nm.Success){continue}
        $vm=[regex]::Match($ia,'(?i)\bvalue\s*=\s*["'']([^"'']*)["'']')
        $val='';if($vm.Success){$val=[System.Net.WebUtility]::HtmlDecode($vm.Groups[1].Value)}
        $x.hidden[$nm.Groups[1].Value]=$val
      }
      foreach($sm in [regex]::Matches($body,'(?is)<select\b([^>]*)>(.*?)</select>')){
        $sa=$sm.Groups[1].Value;$sb=$sm.Groups[2].Value
        $sn=[regex]::Match($sa,'(?i)\bname\s*=\s*["'']([^"'']+)["'']')
        if(-not $sn.Success){continue}
        foreach($om in [regex]::Matches($sb,'(?is)<option\b([^>]*)>(.*?)</option>')){
          $oa=$om.Groups[1].Value
          $ov=[regex]::Match($oa,'(?i)\bvalue\s*=\s*["'']([^"'']*)["'']')
          $text=[regex]::Replace($om.Groups[2].Value,'<[^>]+>','')
          $text=[System.Net.WebUtility]::HtmlDecode($text).Trim()
          $value='';if($ov.Success){$value=[System.Net.WebUtility]::HtmlDecode($ov.Groups[1].Value)}
          $x.options+= [pscustomobject]@{select_name=$sn.Groups[1].Value;value=$value;text=$text}
          if($text -match '(?i)\bBarnet\b'){$x.select_name=$sn.Groups[1].Value;$x.barnet_value=$value}
        }
      }
      break
    }
  }catch{$x.error=$_.Exception.Message}
  return [pscustomobject]$x
}
function Submit-HmlrForm([object]$Form) {
  $x=[ordered]@{attempted=$false;method=$Form.form_method;url=$Form.form_action;reachable=$false;status_code=$null;links=@();content_length=$null;error=$null}
  if(-not $Form.form_action -or -not $Form.select_name -or $null -eq $Form.barnet_value){$x.error='HMLR_BARNET_FORM_NOT_RESOLVED';return [pscustomobject]$x}
  $body=@{};foreach($k in $Form.hidden.Keys){$body[$k]=$Form.hidden[$k]};$body[$Form.select_name]=$Form.barnet_value
  $x.attempted=$true
  try{
    if($Form.form_method -eq 'POST'){$r=Invoke-WebRequest -UseBasicParsing -Method Post -Uri $Form.form_action -Body $body -TimeoutSec 240 -Headers @{'User-Agent'='TerraYield-AAYS-Topography/1.0 HMLR-Barnet-163'}}
    else{
      $pairs=@();foreach($k in $body.Keys){$pairs+=([uri]::EscapeDataString([string]$k)+'='+[uri]::EscapeDataString([string]$body[$k]))}
      $u=$Form.form_action;if($u.Contains('?')){$u+='&'}else{$u+='?'};$u+=($pairs-join'&')
      $x.url=$u;$r=Invoke-WebRequest -UseBasicParsing -Method Get -Uri $u -TimeoutSec 240 -Headers @{'User-Agent'='TerraYield-AAYS-Topography/1.0 HMLR-Barnet-163'}
    }
    $x.status_code=[int]$r.StatusCode;$x.reachable=($r.StatusCode-ge200-and$r.StatusCode-lt400)
    $links=Resolve-Links -PageUrl $x.url -Html $r.Content
    $x.links=@($links|Where-Object{$_ -match '(?i)\.zip(?:$|\?)|\.gml(?:$|\?)|download'})
    $x.content_length=[int64]$r.RawContentLength
  }catch{$x.error=$_.Exception.Message}
  return [pscustomobject]$x
}
function Download-Bounded([string]$Url,[string]$Target,[int64]$MaxBytes) {
  $x=[ordered]@{url=$Url;target=$Target;downloaded=$false;size_bytes=0;sha256=$null;error=$null}
  try{
    Ensure-Dir (Split-Path -Parent $Target)
    $client=[System.Net.Http.HttpClient]::new()
    $client.Timeout=[TimeSpan]::FromMinutes(15)
    $response=$client.GetAsync($Url,[System.Net.Http.HttpCompletionOption]::ResponseHeadersRead).GetAwaiter().GetResult()
    if(-not $response.IsSuccessStatusCode){throw "HTTP_$([int]$response.StatusCode)"}
    $len=$response.Content.Headers.ContentLength
    if($len -and $len -gt $MaxBytes){throw "CONTENT_LENGTH_${len}_EXCEEDS_${MaxBytes}"}
    $stream=$response.Content.ReadAsStreamAsync().GetAwaiter().GetResult()
    $fs=[System.IO.File]::Open($Target,[System.IO.FileMode]::Create,[System.IO.FileAccess]::Write,[System.IO.FileShare]::None)
    try{
      $buf=New-Object byte[] 1048576;$total=0L
      while(($read=$stream.Read($buf,0,$buf.Length)) -gt 0){
        $total+=$read;if($total -gt $MaxBytes){throw "STREAM_EXCEEDS_${MaxBytes}"}
        $fs.Write($buf,0,$read)
      }
    }finally{$fs.Dispose();$stream.Dispose();$client.Dispose()}
    $x.downloaded=$true;$x.size_bytes=(Get-Item -LiteralPath $Target).Length;$x.sha256=(Get-FileHash -Algorithm SHA256 -LiteralPath $Target).Hash
  }catch{$x.error=$_.Exception.Message}
  return [pscustomobject]$x
}
function Scan-GmlForRefs([string]$ArchivePath,[object[]]$Rows) {
  Add-Type -AssemblyName System.IO.Compression.FileSystem
  $result=@()
  if(-not(Test-Path -LiteralPath $ArchivePath)){return $result}
  $ext=[System.IO.Path]::GetExtension($ArchivePath)
  if($ext -notmatch '(?i)\.zip'){return $result}
  $zip=[System.IO.Compression.ZipFile]::OpenRead($ArchivePath)
  try{
    foreach($entry in $zip.Entries){
      if($entry.FullName -notmatch '(?i)\.(gml|xml)$'){continue}
      if($entry.Length -gt 800000000){continue}
      $stream=$entry.Open();$reader=[System.IO.StreamReader]::new($stream,[System.Text.Encoding]::UTF8,$true,65536)
      try{
        $window='';$lineNo=0
        while(-not $reader.EndOfStream){
          $line=$reader.ReadLine();$lineNo++;$window+=$line
          if($window.Length -gt 300000){$window=$window.Substring($window.Length-300000)}
          foreach($row in $Rows){
            $ref=[string]$row.parcel_ref
            if($window.IndexOf($ref,[System.StringComparison]::OrdinalIgnoreCase)-ge0 -and $window -match '(?i)<(?:\w+:)?Polygon\b' -and $window -match '(?i)<(?:\w+:)?posList\b'){
              $pm=[regex]::Match($window,'(?is)<(?:\w+:)?posList\b[^>]*>(.*?)</(?:\w+:)?posList>')
              $sm=[regex]::Match($window,'(?is)<(?:\w+:)?Polygon\b[^>]*\bsrsName\s*=\s*["'']([^"'']+)["'']')
              if($pm.Success){
                $raw=[regex]::Replace($pm.Groups[1].Value,'\s+',' ').Trim()
                $srsValue=$null;if($sm.Success){$srsValue=$sm.Groups[1].Value}
                $result+=[pscustomobject]@{parcel_id=$row.parcel_id;parcel_ref=$ref;archive_path=$ArchivePath;entry=$entry.FullName;line_no=$lineNo;srs_name=$srsValue;pos_list=$raw;match_method='streamed_reference_and_polygon_posList_match'}
                break
              }
            }
          }
        }
      }finally{$reader.Dispose();$stream.Dispose()}
    }
  }finally{$zip.Dispose()}
  return @($result|Group-Object parcel_id|ForEach-Object{$_.Group|Select-Object -First 1})
}

$repoRoot=[System.IO.Path]::GetFullPath([string]$env:AAYS_REPO_ROOT)
if(-not $repoRoot -or $repoRoot -notmatch '(?i)[\\/]TerraYield_AAYS_Portable[\\/]runner_system[\\/]'){throw 'TOPOGRAPHY_163_REQUIRES_PORTABLE_SHARED_RUNNER_WORKTREE'}
$portableMarker='\runner_system\'
$idx=$repoRoot.IndexOf($portableMarker,[System.StringComparison]::OrdinalIgnoreCase)
if($idx-lt0){throw 'TOPOGRAPHY_163_PORTABLE_ROOT_RESOLUTION_FAILED'}
$portableRoot=$repoRoot.Substring(0,$idx)

$taskId='aays1-163-topography-copdem-point-hmlr-download-20260713';if($env:AAYS_TASK_ID){$taskId=[string]$env:AAYS_TASK_ID}
$startedAt=Now-Utc
$batchId='topography-163-'+($startedAt-replace'[^0-9]','')
$previousBatchId='aays1-162-topography-copdem-hmlr-targeted-acquisition-20260713'
$script:stageTotal=12;$script:stageDone=0;$script:currentStage='task_start';$script:operations=@();$script:stages=@()

$visibleRowsRel='england_map_web/data/program_layer_matrix/topography_visible_rows_latest.json'
$visibleStatusRel='england_map_web/data/program_layer_matrix/topography_visible_status_latest.json'
$operationsRel='england_map_web/data/program_layer_matrix/topography_operations_latest.json'
$latestChangesRel='outputs/england_program_parcel_matrix_20260629/topography_updates/latest_changes.json'
$sourceRel='docs/chatgpt_status/topography/source_snapshots/163_copdem_point_hmlr_sources_latest.json'
$downloadRel='docs/chatgpt_status/topography/source_snapshots/163_hmlr_download_and_gml_scan_latest.json'
$boundaryRowsRel='docs/chatgpt_status/topography/fixtures/topography_hmlr_streamed_boundary_matches_20260713.json'
$statusRel='docs/chatgpt_status/topography/status/163_topography_copdem_point_hmlr_download_latest.json'
$reportRel='docs/chatgpt_status/topography/reports/163_topography_copdem_point_hmlr_download_report_20260713.md'
$outputRel='docs/chatgpt_status/topography/runner_outputs/163_topography_copdem_point_hmlr_download_batch.json'

function Add-Operation {
  param([string]$Type,[string]$Status,[int]$StageNo,[string]$StageName,[string]$ParcelId='',[string]$SourceName='',[string]$SourceUrl='',[string]$RequestUrl='',[object]$NumericValue=$null,[string]$Unit='',[string]$EvidencePath='',[string]$Blocker='')
  $parcelValue=$null;if($ParcelId){$parcelValue=$ParcelId}
  $sourceValue=$null;if($SourceName){$sourceValue=$SourceName}
  $sourceUrlValue=$null;if($SourceUrl){$sourceUrlValue=$SourceUrl}
  $requestValue=$null;if($RequestUrl){$requestValue=$RequestUrl}
  $unitValue=$null;if($Unit){$unitValue=$Unit}
  $evidenceValue=$null;if($EvidencePath){$evidenceValue=$EvidencePath}
  $blockerValue=$null;if($Blocker){$blockerValue=$Blocker}
  $script:operations+=[pscustomobject][ordered]@{
    operation_id="${batchId}_$($script:operations.Count+1)";stage_no=$StageNo;operation_type=$Type;task_id=$taskId;batch_id=$batchId;previous_batch_id=$previousBatchId
    parcel_id=$parcelValue;status=$Status;is_new_operation=$true;is_new_in_latest_batch=$true;started_at=$startedAt;completed_at=Now-Utc
    source_name=$sourceValue;source_url=$sourceUrlValue;request_url=$requestValue
    numeric_value=$NumericValue;unit=$unitValue;method=$StageName;accuracy_score_4='2.5/4 fallback'
    repo_artifact_path=$evidenceValue;report_path=$reportRel;status_path=$statusRel;runner_output_path=$outputRel
    blocker=$blockerValue;needs_manual_review=[bool]$Blocker;final_ready=$false;fake_data=$false
  }
}
function Publish-Ledger([string]$RunStatus) {
  $path=Join-Path $repoRoot ($operationsRel.Replace('/','\'))
  $old=Read-Json $path;$existing=@()
  if($old){$existing=@($old.operations);foreach($op in $existing){if($null-ne$op){Set-Prop $op 'is_new_operation' $false;Set-Prop $op 'is_new_in_latest_batch' $false}}}
  $all=@($existing+$script:operations)
  $blocked=@($all|Where-Object{[string]$_.status -match 'blocked|failed|unavailable|auth_required|not_found|partial|candidate_only'})
  $lastBlocked=$null;if($blocked.Count){$lastBlocked=$blocked[-1]}
  Write-Json $path ([ordered]@{task_id=$taskId;batch_id=$batchId;previous_batch_id=$previousBatchId;updated_at=Now-Utc;run_status=$RunStatus;current_stage=$script:currentStage;stage_completed_count=$script:stageDone;stage_total_count=$script:stageTotal;operation_count=$all.Count;new_operations_count=$script:operations.Count;blocked_operation_count=$blocked.Count;last_blocked_operation=$lastBlocked;operations=$all;final_ready=$false;product_final_ready=$false;fake_data=$false;db_write=$false;migration=$false;production_deploy=$false})
}
function Complete-Stage([int]$No,[string]$Name,[string]$Status='completed'){
  $script:stageDone=$No;$script:currentStage=$Name;$script:stages+=[pscustomobject][ordered]@{stage_no=$No;stage=$Name;status=$Status;completed_at=Now-Utc}
  Add-Operation -Type 'pipeline_stage' -Status $Status -StageNo $No -StageName $Name -EvidencePath $statusRel
  Publish-Ledger -RunStatus 'RUNNING'
}

try{
  Add-Operation -Type 'task_start' -Status 'running' -StageNo 1 -StageName 'task_start' -EvidencePath $statusRel
  Publish-Ledger -RunStatus 'RUNNING'
  $visiblePath=Join-Path $repoRoot ($visibleRowsRel.Replace('/','\'));$visible=Read-Json $visiblePath;$parcelRows=@($visible.rows)
  if($null-eq$visible-or$parcelRows.Count-lt3){throw 'TOPOGRAPHY_163_VISIBLE_ROWS_NOT_READY'}
  Complete-Stage 1 'load_verified_parcel_rows'

  $docs=@(
    (Test-Http 'Copernicus OData documentation' 'https://documentation.dataspace.copernicus.eu/APIs/OData.html'),
    (Test-Http 'Copernicus COP-DEM collection' 'https://dataspace.copernicus.eu/explore-data/data-collections/copernicus-contributing-missions/collections-description/COP-DEM'),
    (Test-Http 'HMLR INSPIRE download page' 'https://use-land-property-data.service.gov.uk/datasets/inspire/download'),
    (Test-Http 'Environment Agency LiDAR survey' 'https://environment.data.gov.uk/survey'),
    (Test-Http 'OS Terrain 50' 'https://osdatahub.os.uk/downloads/open/Terrain50')
  )
  foreach($d in $docs){$s='blocked_or_unavailable';$b=$d.error;if($d.reachable){$s='source_check_only_available';$b=''};Add-Operation -Type 'official_source_check_only' -Status $s -StageNo 2 -StageName 'official_source_checks' -SourceName $d.name -SourceUrl $d.url -RequestUrl $d.final_url -EvidencePath $sourceRel -Blocker $b}
  $docStatus='partial';if(@($docs|Where-Object{$_.reachable}).Count-eq$docs.Count){$docStatus='completed'}
  Complete-Stage 2 'official_source_checks' $docStatus

  $pointQueries=@()
  foreach($row in $parcelRows){
    $q=Invoke-CopDemPoint -Lon ([double]$row.centroid_lon) -Lat ([double]$row.centroid_lat) -ParcelId ([string]$row.parcel_id);$pointQueries+=$q
    $s='blocked_or_unavailable';$b=$q.error;if($q.reachable){$s='completed';$b=''}
    Add-Operation -Type 'copdem_geographic_point_query' -Status $s -StageNo 3 -StageName 'copdem_point_intersects' -ParcelId $row.parcel_id -SourceName 'Copernicus COP-DEM' -SourceUrl 'https://documentation.dataspace.copernicus.eu/APIs/OData.html' -RequestUrl $q.url -NumericValue $q.glo30_count -Unit 'GLO-30 products' -EvidencePath $sourceRel -Blocker $b
  }
  Complete-Stage 3 'copdem_point_intersects'

  $collectionQueries=@((Invoke-CopDemCollection '/COP-DEM_GLO-30-DGED/'),(Invoke-CopDemCollection '/COP-DEM_GLO-30-DTED/'))
  foreach($q in $collectionQueries){$s='blocked_or_unavailable';$b=$q.error;if($q.reachable){$s='completed';$b=''};Add-Operation -Type 'copdem_collection_path_query' -Status $s -StageNo 4 -StageName 'copdem_collection_path_queries' -SourceName 'Copernicus COP-DEM' -RequestUrl $q.url -NumericValue $q.result_count -Unit 'products' -EvidencePath $sourceRel -Blocker $b}
  Complete-Stage 4 'copdem_collection_path_queries'

  $allProducts=@()
  foreach($q in $pointQueries){$allProducts+=@($q.glo30_products)}
  foreach($q in $collectionQueries){$allProducts+=@($q.products)}
  $uniqueProducts=@($allProducts|Where-Object{$_.Id}|Group-Object Id|ForEach-Object{$_.Group|Select-Object -First 1})
  $nodeInventories=@()
  foreach($p in @($uniqueProducts|Select-Object -First 3)){
    $n=Get-ProductNodes -ProductId ([string]$p.Id);$nodeInventories+=$n
    $s='blocked_or_unavailable';$b=$n.error;if($n.reachable){$s='completed';$b=''}
    Add-Operation -Type 'copdem_product_node_inventory' -Status $s -StageNo 5 -StageName 'copdem_node_inventory' -SourceName $p.Name -RequestUrl $n.url -NumericValue $n.node_count -Unit 'nodes' -EvidencePath $sourceRel -Blocker $b
  }
  if($uniqueProducts.Count-eq0){Add-Operation -Type 'copdem_product_node_inventory' -Status 'product_not_found' -StageNo 5 -StageName 'copdem_node_inventory' -SourceName 'Copernicus COP-DEM' -EvidencePath $sourceRel -Blocker 'NO_COPDEM_GLO30_PRODUCT_FROM_POINT_OR_PATH_QUERY'}
  $nodeStage='product_not_found';if($uniqueProducts.Count-gt0){$nodeStage='completed'}
  Complete-Stage 5 'copdem_node_inventory' $nodeStage

  $hmlrPage=Test-Http 'HMLR INSPIRE download page' 'https://use-land-property-data.service.gov.uk/datasets/inspire/download'
  $form=$null;$submission=$null
  if($hmlrPage.reachable){$form=Parse-HmlrForm -PageUrl $hmlrPage.final_url -Html $hmlrPage.content;$submission=Submit-HmlrForm -Form $form}
  if($null-eq$submission){$submission=[pscustomobject]@{attempted=$false;reachable=$false;links=@();error='HMLR_DOWNLOAD_PAGE_UNAVAILABLE'}}
  $formStatus='partial';$formBlock=$submission.error;if($submission.reachable){$formStatus='completed';$formBlock=''}
  Add-Operation -Type 'hmlr_barnet_form_submission' -Status $formStatus -StageNo 6 -StageName 'hmlr_barnet_download_resolution' -SourceName 'HMLR INSPIRE' -SourceUrl 'https://use-land-property-data.service.gov.uk/datasets/inspire/download' -RequestUrl $submission.url -NumericValue @($submission.links).Count -Unit 'candidate download links' -EvidencePath $downloadRel -Blocker $formBlock
  Complete-Stage 6 'hmlr_barnet_download_resolution' $formStatus

  $candidateLinks=@($submission.links|Where-Object{$_ -match '(?i)\.zip(?:$|\?)|\.gml(?:$|\?)'}|Select-Object -Unique)
  foreach($link in @($candidateLinks|Select-Object -First 10)){
    $hc=Test-Http 'HMLR candidate download' $link 'HEAD';$s='blocked_or_unavailable';$b=$hc.error;if($hc.reachable){$s='link_available';$b=''}
    Add-Operation -Type 'hmlr_download_link_check' -Status $s -StageNo 7 -StageName 'hmlr_download_link_validation' -SourceName 'HMLR INSPIRE' -SourceUrl $hmlrPage.url -RequestUrl $link -NumericValue $hc.content_length -Unit 'bytes' -EvidencePath $downloadRel -Blocker $b
  }
  $linkStage='not_found';if($candidateLinks.Count-gt0){$linkStage='completed'}
  if($candidateLinks.Count-eq0){Add-Operation -Type 'hmlr_download_link_check' -Status 'not_found' -StageNo 7 -StageName 'hmlr_download_link_validation' -SourceName 'HMLR INSPIRE' -EvidencePath $downloadRel -Blocker 'NO_GML_OR_ZIP_DOWNLOAD_LINK_RESOLVED'}
  Complete-Stage 7 'hmlr_download_link_validation' $linkStage

  $download=$null;$externalTarget=$null
  if($candidateLinks.Count-gt0){
    $externalDir=Join-Path $portableRoot 'data\topography\hmlr_inspire';Ensure-Dir $externalDir
    $name=[System.IO.Path]::GetFileName(([uri]$candidateLinks[0]).AbsolutePath);if(-not$name){$name='hmlr_inspire_barnet.zip'}
    $externalTarget=Join-Path $externalDir $name
    $download=Download-Bounded -Url $candidateLinks[0] -Target $externalTarget -MaxBytes 262144000
  }
  if($null-eq$download){$download=[pscustomobject]@{downloaded=$false;size_bytes=0;sha256=$null;error='NO_DOWNLOAD_CANDIDATE'}}
  $downloadStatus='blocked_or_unavailable';$downloadBlock=$download.error;if($download.downloaded){$downloadStatus='downloaded';$downloadBlock=''}
  $selectedHmlrUrl='';if($candidateLinks.Count){$selectedHmlrUrl=$candidateLinks[0]}
  Add-Operation -Type 'hmlr_bounded_download' -Status $downloadStatus -StageNo 8 -StageName 'hmlr_bounded_download' -SourceName 'HMLR INSPIRE Barnet' -RequestUrl $selectedHmlrUrl -NumericValue $download.size_bytes -Unit 'bytes' -EvidencePath $downloadRel -Blocker $downloadBlock
  Complete-Stage 8 'hmlr_bounded_download' $downloadStatus

  $boundaryMatches=@()
  if($download.downloaded){$boundaryMatches=Scan-GmlForRefs -ArchivePath $externalTarget -Rows $parcelRows}
  foreach($m in $boundaryMatches){Add-Operation -Type 'real_boundary_gml_match' -Status 'validated_gml_polygon' -StageNo 9 -StageName 'hmlr_streamed_gml_scan' -ParcelId $m.parcel_id -SourceName 'HMLR INSPIRE GML' -RequestUrl $candidateLinks[0] -NumericValue ([string]$m.pos_list).Length -Unit 'posList characters' -EvidencePath $boundaryRowsRel}
  if($boundaryMatches.Count-eq0){Add-Operation -Type 'real_boundary_gml_match' -Status 'not_found' -StageNo 9 -StageName 'hmlr_streamed_gml_scan' -SourceName 'HMLR INSPIRE GML' -EvidencePath $boundaryRowsRel -Blocker 'PARCEL_REFERENCE_POLYGON_NOT_FOUND_IN_DOWNLOADED_ARCHIVE'}
  $boundaryStage='partial';if($boundaryMatches.Count-eq3){$boundaryStage='completed'}
  Write-Json (Join-Path $repoRoot ($boundaryRowsRel.Replace('/','\'))) ([ordered]@{task_id=$taskId;batch_id=$batchId;generated_at=Now-Utc;real_boundary_rows=$boundaryMatches.Count;rows=$boundaryMatches;final_ready=$false;fake_data=$false})
  Complete-Stage 9 'hmlr_streamed_gml_scan' $boundaryStage

  $token=$null;if($env:CDSE_ACCESS_TOKEN){$token=[string]$env:CDSE_ACCESS_TOKEN}elseif($env:COPERNICUS_ACCESS_TOKEN){$token=[string]$env:COPERNICUS_ACCESS_TOKEN}
  $gate='product_not_found';$gateBlock='NO_COPDEM_GLO30_PRODUCT_FOUND';$selectedProduct=$null;$downloadUrl=$null
  if($uniqueProducts.Count-gt0){$selectedProduct=$uniqueProducts[0];$downloadUrl="https://download.dataspace.copernicus.eu/odata/v1/Products($([string]$selectedProduct.Id))/`$value";$gate='auth_required';$gateBlock='CDSE_ACCESS_TOKEN_NOT_AVAILABLE';if($token){$gate='download_ready';$gateBlock=''}}
  Add-Operation -Type 'primary_copdem_download_gate' -Status $gate -StageNo 10 -StageName 'copdem_download_gate' -SourceName 'Copernicus DEM GLO-30' -RequestUrl $downloadUrl -NumericValue $uniqueProducts.Count -Unit 'matching products' -EvidencePath $sourceRel -Blocker $gateBlock
  Complete-Stage 10 'copdem_download_gate' $gate

  $docEvidence=@($docs|Select-Object name,url,method,reachable,status_code,final_url,content_length,content_type,error)
  $formEvidence=$null
  if($form){$formEvidence=[ordered]@{form_action=$form.form_action;form_method=$form.form_method;select_name=$form.select_name;barnet_value=$form.barnet_value;hidden_field_names=@($form.hidden.Keys);option_count=@($form.options).Count;error=$form.error}}
  Write-Json (Join-Path $repoRoot ($sourceRel.Replace('/','\'))) ([ordered]@{task_id=$taskId;batch_id=$batchId;generated_at=Now-Utc;official_docs=$docEvidence;point_queries=$pointQueries;collection_queries=$collectionQueries;matching_products=$uniqueProducts;node_inventories=$nodeInventories;copdem_download_gate=[ordered]@{status=$gate;token_configured=[bool]$token;product_count=$uniqueProducts.Count;selected_product=$selectedProduct;download_url=$downloadUrl};hmlr_form=$formEvidence;hmlr_submission=$submission;hmlr_candidate_links=$candidateLinks;final_ready=$false;fake_data=$false;db_write=$false;migration=$false;production_deploy=$false})
  Write-Json (Join-Path $repoRoot ($downloadRel.Replace('/','\'))) ([ordered]@{task_id=$taskId;batch_id=$batchId;generated_at=Now-Utc;candidate_links=$candidateLinks;download=$download;external_target=$externalTarget;boundary_matches=$boundaryMatches;final_ready=$false;fake_data=$false})

  $productCount=$uniqueProducts.Count;$realBoundaryCount=$boundaryMatches.Count;$pct=70
  if($productCount-gt0 -or $candidateLinks.Count-gt0){$pct=72}
  if($realBoundaryCount-eq3){$pct=75}
  if($productCount-gt0 -and $realBoundaryCount-eq3){$pct=78}
  $blockers=@()
  if($realBoundaryCount-lt3){$blockers+='real_parcel_boundary_required'}
  $blockers+='primary_copdem_glo30_raster_sampling_required'
  $blockers+='ea_lidar_or_os_terrain_numeric_validation_required'
  foreach($row in $parcelRows){
    $bm=@($boundaryMatches|Where-Object{$_.parcel_id-eq$row.parcel_id})
    Set-Prop $row 'real_boundary_validated' ($bm.Count-gt0)
    Set-Prop $row 'real_boundary_evidence_path' $boundaryRowsRel
    Set-Prop $row 'copdem_product_candidates' $productCount
    Set-Prop $row 'copdem_download_gate_status' $gate
    Set-Prop $row 'hmlr_download_link_candidates' $candidateLinks.Count
    Set-Prop $row 'hmlr_archive_downloaded' [bool]$download.downloaded
    Set-Prop $row 'task_id' $taskId
    Set-Prop $row 'updated_at' (Now-Utc)
    Set-Prop $row 'report_path' $reportRel
    Set-Prop $row 'status_path' $statusRel
    Set-Prop $row 'display_badge' 'COPDEM_POINT_HMLR_DOWNLOAD_EVIDENCE_READY'
    Set-Prop $row 'accuracy_score_4' '2.5/4 fallback; primary numeric validation pending'
    Set-Prop $row 'blocker' ($blockers-join'; ')
  }
  Set-Prop $visible 'status' 'COPDEM_POINT_HMLR_DOWNLOAD_VISIBLE_NOT_FINAL';Set-Prop $visible 'latest_task_id' $taskId;Set-Prop $visible 'latest_batch_id' $batchId;Set-Prop $visible 'updated_at' (Now-Utc);Set-Prop $visible 'rows' $parcelRows;Set-Prop $visible 'final_ready' $false;Set-Prop $visible 'fake_data' $false
  Write-Json $visiblePath $visible
  $statusPayload=[ordered]@{task_id=$taskId;page_key='topography';batch_id=$batchId;previous_batch_id=$previousBatchId;status='COPDEM_POINT_HMLR_DOWNLOAD_VISIBLE_NOT_FINAL';started_at=$startedAt;completed_at=Now-Utc;stages=$script:stages;completed_stage_count=11;total_stage_count=$script:stageTotal;candidate_rows=$parcelRows.Count;official_sources_checked=$docs.Count;official_sources_reachable=@($docs|Where-Object{$_.reachable}).Count;copdem_products_found=$productCount;copdem_node_inventories=$nodeInventories.Count;hmlr_download_link_candidates=$candidateLinks.Count;hmlr_archive_downloaded=[bool]$download.downloaded;hmlr_archive_size_bytes=$download.size_bytes;real_boundary_rows=$realBoundaryCount;completion_percent=$pct;percent_increase=($pct-70);accuracy_score_4='2.5/4 fallback';blockers=$blockers;final_ready=$false;product_final_ready=$false;fake_data=$false;db_write=$false;migration=$false;production_deploy=$false}
  Write-Json (Join-Path $repoRoot ($statusRel.Replace('/','\'))) $statusPayload;Write-Json (Join-Path $repoRoot ($visibleStatusRel.Replace('/','\'))) $statusPayload;Write-Json (Join-Path $repoRoot ($latestChangesRel.Replace('/','\'))) ([ordered]@{layer='Topography';task_id=$taskId;updated_at=Now-Utc;summary=$statusPayload;rows=$parcelRows;final_ready=$false;fake_data=$false})
  Complete-Stage 11 'site_artifact_generation'

  if($env:AAYS_CONTROLLER_REPO_ROOT){$publisher=Join-Path $repoRoot 'docs\chatgpt_status\_shared\automation\PUBLISH_AAYS_WEB_ARTIFACTS_TO_LIVE_CONTROLLER_20260711.ps1';$paths=@($visibleRowsRel,$visibleStatusRel,$operationsRel,$sourceRel,$downloadRel,$boundaryRowsRel)-join'|';& powershell -NoProfile -ExecutionPolicy Bypass -File $publisher -TaskRepoRoot $repoRoot -ControllerRoot $env:AAYS_CONTROLLER_REPO_ROOT -Paths $paths -AllowGeneratedArtifacts -SyncPortableWeb;if($LASTEXITCODE-ne0){throw 'TOPOGRAPHY_163_LIVE_CONTROLLER_PUBLISH_BLOCKED'}}
  $siteRows=Invoke-WebRequest -UseBasicParsing -Uri 'http://127.0.0.1:8012/england_map_web/data/program_layer_matrix/topography_visible_rows_latest.json' -TimeoutSec 30
  $siteOps=Invoke-WebRequest -UseBasicParsing -Uri 'http://127.0.0.1:8012/england_map_web/data/program_layer_matrix/topography_operations_latest.json' -TimeoutSec 30
  if($siteRows.StatusCode-ne200-or$siteOps.StatusCode-ne200){throw 'TOPOGRAPHY_163_SITE_HTTP_READBACK_FAILED'}
  if($siteRows.Content-notmatch[regex]::Escape($taskId)-or$siteOps.Content-notmatch[regex]::Escape($taskId)){throw 'TOPOGRAPHY_163_TASK_ID_NOT_VISIBLE'}
  Complete-Stage 12 'live_publish_and_http_task_id_readback' 'PASS'

  $statusPayload.completed_stage_count=12;$statusPayload.completed_at=Now-Utc
  Write-Json (Join-Path $repoRoot ($statusRel.Replace('/','\'))) $statusPayload;Write-Json (Join-Path $repoRoot ($visibleStatusRel.Replace('/','\'))) $statusPayload
  Publish-Ledger 'COMPLETED_VISIBLE_NOT_FINAL'
  $report="# Topography 163 CopDEM Point and HMLR Download Acquisition`n`n- Task: $taskId`n- Candidate parcels: $($parcelRows.Count)`n- Official sources reachable: $(@($docs|Where-Object{$_.reachable}).Count)/$($docs.Count)`n- CopDEM GLO-30 products: $productCount`n- CopDEM node inventories: $($nodeInventories.Count)`n- HMLR download links: $($candidateLinks.Count)`n- HMLR archive downloaded: $($download.downloaded)`n- HMLR archive size: $($download.size_bytes)`n- Real boundary rows: $realBoundaryCount/3`n- New operation rows: $($script:operations.Count)`n- Site HTTP task-id readback: PASS`n- Completion: $pct%`n- Increase: +$($pct-70)%`n- Accuracy: 2.5/4 fallback`n- final_ready: false`n"
  Ensure-Dir (Split-Path -Parent (Join-Path $repoRoot ($reportRel.Replace('/','\'))));[System.IO.File]::WriteAllText((Join-Path $repoRoot ($reportRel.Replace('/','\'))),$report,[System.Text.UTF8Encoding]::new($false))
  Write-Json (Join-Path $repoRoot ($outputRel.Replace('/','\'))) ([ordered]@{task_id=$taskId;status='COMPLETED_VISIBLE_NOT_FINAL';completed_at=Now-Utc;completion_percent=$pct;percent_increase=($pct-70);completed_stage_count=12;total_stage_count=12;candidate_rows=$parcelRows.Count;copdem_products_found=$productCount;copdem_node_inventories=$nodeInventories.Count;hmlr_download_link_candidates=$candidateLinks.Count;hmlr_archive_downloaded=[bool]$download.downloaded;hmlr_archive_size_bytes=$download.size_bytes;real_boundary_rows=$realBoundaryCount;new_operation_rows=$script:operations.Count;site_http_validation='PASS';blockers=$blockers;accuracy_score_4='2.5/4 fallback';final_ready=$false;product_final_ready=$false;fake_data=$false;db_write=$false;migration=$false;production_deploy=$false})
}catch{
  $e=$_.Exception.Message
  Add-Operation -Type 'runner_failure' -Status 'blocked' -StageNo ([math]::Max(1,$script:stageDone+1)) -StageName $script:currentStage -EvidencePath $statusRel -Blocker $e
  Publish-Ledger 'BLOCKED'
  $failure=[ordered]@{task_id=$taskId;status='BLOCKED';error=$e;completed_stage_count=$script:stageDone;total_stage_count=$script:stageTotal;completion_percent=70;percent_increase=0;final_ready=$false;product_final_ready=$false;fake_data=$false;db_write=$false;migration=$false;production_deploy=$false}
  Write-Json (Join-Path $repoRoot ($statusRel.Replace('/','\'))) $failure;Write-Json (Join-Path $repoRoot ($outputRel.Replace('/','\'))) $failure
  throw
}
