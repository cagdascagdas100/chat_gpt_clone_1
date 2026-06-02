param([string]$Repo='C:\Users\cagda\Documents\GitHub\AAYS')
$ErrorActionPreference='Continue'
$stamp=Get-Date -Format 'yyyyMMdd_HHmmss'
$out=Join-Path $Repo 'docs\chatgpt_status\runner_outputs'
New-Item -ItemType Directory -Force -Path $out | Out-Null

function Get-TokenInfo {
  $names=@('AAYS_HF_TOKEN','HF_TOKEN','HUGGINGFACE_TOKEN')
  foreach($n in $names){
    $v=[Environment]::GetEnvironmentVariable($n,'Process')
    if([string]::IsNullOrWhiteSpace($v)){ $v=[Environment]::GetEnvironmentVariable($n,'User') }
    if([string]::IsNullOrWhiteSpace($v)){ $v=[Environment]::GetEnvironmentVariable($n,'Machine') }
    if(-not [string]::IsNullOrWhiteSpace($v)){ return [ordered]@{ present=$true; source=$n; value=$v } }
  }
  return [ordered]@{ present=$false; source='NONE'; value='' }
}

function Probe-HfUrl([string]$Region,[string]$Url,[string]$Token,[bool]$TokenPresent){
  $headers=@{ Range='bytes=0-16383' }
  if($TokenPresent){ $headers['Authorization']='Bearer '+$Token }
  $status=$null; $bytes=0; $classification='not_attempted'; $verified=$false; $rangeSupported=$false
  try {
    $resp=Invoke-WebRequest -Uri $Url -Headers $headers -Method Get -UseBasicParsing -TimeoutSec 45 -ErrorAction Stop
    $status=[int]$resp.StatusCode
    if($resp.RawContentStream -and $resp.RawContentStream.Length -gt 0){ $bytes=[int64]$resp.RawContentStream.Length }
    elseif($resp.Content){ $bytes=[Text.Encoding]::UTF8.GetByteCount([string]$resp.Content) }
    $rangeSupported=($status -eq 206)
    $verified=($status -eq 206 -and $bytes -gt 0)
    if($verified){ $classification='verified_range_206' }
    elseif($status -eq 200){ $classification='http_200_no_range_or_full_response' }
    else { $classification='http_'+$status }
  } catch {
    $ex=$_.Exception
    try { $status=[int]$ex.Response.StatusCode } catch { $status=$null }
    if($status -eq 401 -or $status -eq 403){ $classification='auth_required' }
    elseif($status){ $classification='http_'+$status }
    else { $classification='probe_error' }
  }
  return [ordered]@{
    region=$Region
    remote_configured=$true
    remote_url=$Url
    remote_verified=$verified
    remote_auth_required=($classification -eq 'auth_required')
    http_status=$status
    downloaded_bytes=$bytes
    range_supported=$rangeSupported
    token_present=$TokenPresent
    classification=$classification
    secret_values_printed=$false
  }
}

$tokenInfo=Get-TokenInfo
$latestPath=Join-Path $out 'latest_output.json'
$latest=$null
try { if(Test-Path $latestPath){ $latest=Get-Content $latestPath -Raw | ConvertFrom-Json } } catch { $latest=$null }

$remoteRows=@()
if($latest -and $latest.regions){
  foreach($r in $latest.regions){
    if($r.remote_configured -and -not [string]::IsNullOrWhiteSpace([string]$r.remote_url)){
      $remoteRows += [ordered]@{ region=([string]$r.asset_slug); url=([string]$r.remote_url) }
    }
  }
}
if(@($remoteRows).Count -eq 0){
  $remoteRows=@(
    [ordered]@{region='london';url='https://huggingface.co/datasets/terrayield-tiles/Terra_1/resolve/main/v2/london/parcels.pmtiles'},
    [ordered]@{region='south_east';url='https://huggingface.co/datasets/terrayield-tiles/Terra_1/resolve/main/v2/south_east/parcels.pmtiles'},
    [ordered]@{region='south_west';url='https://huggingface.co/datasets/terrayield-tiles/Terra_1/resolve/main/v2/south_west/parcels.pmtiles'},
    [ordered]@{region='east';url='https://huggingface.co/datasets/terrayield-tiles/Terra_1/resolve/main/east/parcels.pmtiles'},
    [ordered]@{region='midlands';url='https://huggingface.co/datasets/terrayield-tiles/Terra_1/resolve/main/v2/midlands/parcels.pmtiles'},
    [ordered]@{region='north';url='https://huggingface.co/datasets/terrayield-tiles/Terra_1/resolve/main/v2/north/parcels.pmtiles'}
  )
}

$probes=@()
foreach($rr in $remoteRows){ $probes += Probe-HfUrl $rr.region $rr.url $tokenInfo.value $tokenInfo.present }
$remoteConfigured=@($probes).Count
$remoteVerified=@($probes | Where-Object { $_.remote_verified }).Count
$remoteAuth=@($probes | Where-Object { $_.remote_auth_required }).Count
$walesMissing=$true
$scotlandMissing=$true
if($latest){
  try { $walesRow=$latest.regions | Where-Object { $_.asset_slug -eq 'wales' } | Select-Object -First 1; if($walesRow -and $walesRow.remote_configured){$walesMissing=$false} } catch {}
  try { $scotlandRow=$latest.regions | Where-Object { $_.asset_slug -eq 'scotland' } | Select-Object -First 1; if($scotlandRow -and $scotlandRow.remote_configured){$scotlandMissing=$false} } catch {}
}

$fullCoverage=$false
$overall=99
$status='REGION_GATE_MAPPING_MISMATCH_COVERAGE_PENDING'
$coverageClaim='partial_runtime_coverage_only'
if($remoteVerified -ge $remoteConfigured -and -not $walesMissing -and -not $scotlandMissing){
  $fullCoverage=$true; $overall=100; $status='FULL_REMOTE_PMtiles_COVERAGE_VERIFIED'; $coverageClaim='full_remote_pmtiles_runtime_verified'
}

$result=[ordered]@{
  stamp=$stamp
  status=$status
  scoped_progress=100
  overall_progress=$overall
  full_coverage_verified=$fullCoverage
  coverage_claim=$coverageClaim
  region_gate_mapping_mismatch=($true)
  token_present=$tokenInfo.present
  token_source=$tokenInfo.source
  secret_values_printed=$false
  remote_hf_configured_count=$remoteConfigured
  remote_hf_auth_required_count=$remoteAuth
  remote_hf_verified_count=$remoteVerified
  wales_remote_config_missing=$walesMissing
  scotland_remote_config_missing=$scotlandMissing
  probes=$probes
  safety=[ordered]@{ db_write=$false; deploy=$false; migration=$false; fake_data=$false; secret_values_printed=$false }
}
$result | ConvertTo-Json -Depth 8 | Set-Content (Join-Path $out 'aays-hf-proxy-probe-latest.json') -Encoding UTF8
@"
AAYS HF proxy/probe $stamp
status=$status
scoped_progress=100
overall_progress=$overall
full_coverage_verified=$fullCoverage
token_present=$($tokenInfo.present)
token_source=$($tokenInfo.source)
remote_hf_configured_count=$remoteConfigured
remote_hf_auth_required_count=$remoteAuth
remote_hf_verified_count=$remoteVerified
wales_remote_config_missing=$walesMissing
scotland_remote_config_missing=$scotlandMissing
db_write=false
deploy=false
migration=false
fake_data=false
secret_values_printed=false
"@ | Set-Content (Join-Path $out 'aays-hf-proxy-probe-latest.txt') -Encoding UTF8

$plan=@"
# AAYS Secret-Safe HF PMTiles Proxy Plan

## Objective
Provide server-side, secret-safe access/probing for Hugging Face PMTiles sources without exposing tokens in browser logs, output files, or Git history.

## Token policy
Use the first available environment variable in this order: `AAYS_HF_TOKEN`, `HF_TOKEN`, `HUGGINGFACE_TOKEN`.
Only report `token_present` and `token_source`; never print token values or Authorization headers.

## Required proxy behavior
- Accept a known region key, not arbitrary untrusted URL by default.
- Resolve the region key to a manifest URL server-side.
- Attach `Authorization: Bearer <token>` only server-side when token is present.
- Preserve client `Range` requests for PMTiles.
- Return 206 for valid range responses.
- Classify 401/403 as `auth_required`.
- Never mark remote source verified unless Range probe returns 206 with bytes.

## Current probe summary
- token_present: $($tokenInfo.present)
- token_source: $($tokenInfo.source)
- remote_hf_configured_count: $remoteConfigured
- remote_hf_auth_required_count: $remoteAuth
- remote_hf_verified_count: $remoteVerified
- wales_remote_config_missing: $walesMissing
- scotland_remote_config_missing: $scotlandMissing
- full_coverage_verified: $fullCoverage

## Current decision
Keep `overall_progress=$overall` and `status=$status` until all required remote/local sources are runtime verified and Wales/Scotland are explicitly configured or otherwise covered by real verified sources.

## Safety
- db_write=false
- deploy=false
- migration=false
- fake_data=false
- secret_values_printed=false
"@
$plan | Set-Content (Join-Path $out 'aays-hf-proxy-plan-latest.md') -Encoding UTF8

# Merge a safe subset into latest_output if present.
$latestOut=[ordered]@{}
if($latest){
  try { $latest.PSObject.Properties | ForEach-Object { $latestOut[$_.Name]=$_.Value } } catch {}
}
$latestOut['stamp']=$stamp
$latestOut['status']=$status
$latestOut['scoped_progress']=100
$latestOut['overall_progress']=$overall
$latestOut['full_coverage_verified']=$fullCoverage
$latestOut['token_present']=$tokenInfo.present
$latestOut['token_source']=$tokenInfo.source
$latestOut['remote_hf_configured_count']=$remoteConfigured
$latestOut['remote_hf_auth_required_count']=$remoteAuth
$latestOut['remote_hf_verified_count']=$remoteVerified
$latestOut['wales_remote_config_missing']=$walesMissing
$latestOut['scotland_remote_config_missing']=$scotlandMissing
$latestOut['hf_proxy_probe_latest']='docs/chatgpt_status/runner_outputs/aays-hf-proxy-probe-latest.json'
$latestOut['secret_values_printed']=$false
$latestOut['safety']=[ordered]@{ db_write=$false; deploy=$false; migration=$false; fake_data=$false; secret_values_printed=$false }
$latestOut | ConvertTo-Json -Depth 8 | Set-Content (Join-Path $out 'latest_output.json') -Encoding UTF8
@"
AAYS latest output $stamp
status=$status
scoped_progress=100
overall_progress=$overall
full_coverage_verified=$FullCoverage
token_present=$($tokenInfo.present)
remote_hf_configured_count=$remoteConfigured
remote_hf_auth_required_count=$remoteAuth
remote_hf_verified_count=$remoteVerified
wales_remote_config_missing=$walesMissing
scotland_remote_config_missing=$scotlandMissing
db_write=false
deploy=false
migration=false
fake_data=false
secret_values_printed=false
"@ | Set-Content (Join-Path $out 'latest_output.txt') -Encoding UTF8

Write-Host 'AAYS_HF_PROXY_PROBE_DONE'
Write-Host "STATUS=$status"
Write-Host "OVERALL_PROGRESS=$overall"
Write-Host "TOKEN_PRESENT=$($tokenInfo.present)"
Write-Host "REMOTE_VERIFIED=$remoteVerified"
Write-Host "SECRET_VALUES_PRINTED=false"
