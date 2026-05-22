$ErrorActionPreference='Continue'
$Bridge='C:\AAYS_GITHUB_BRIDGE_CLEAN2'
$Out='E:\AAYS_DATA\elevation\copernicus_dem_glo30'
$Hb=Join-Path $Bridge 'ai-heartbeat\t117.md'
$Res=Join-Path $Bridge 'ai-results\t117.result.json'
$Rep=Join-Path $Bridge 'ai-results\t117.report.md'
New-Item -ItemType Directory -Force -Path $Out,(Split-Path $Hb -Parent),(Split-Path $Res -Parent) | Out-Null
function Write-T117Heartbeat($s,$m){ @('# t117 real dem download','status='+$s,'message='+$m,'time='+(Get-Date -Format s),'db_write=false','production_deploy=false','fake_data=false') | Set-Content -Encoding UTF8 $Hb }
Write-T117Heartbeat 'running' 'start real DEM download'
$tiles=@(@(51,-1),@(52,-1),@(53,-2),@(54,-2),@(50,-1),@(52,0))
$downloaded=@()
foreach($t in $tiles){
  $lat=[int]$t[0]; $lon=[int]$t[1]
  $ns='N'+('{0:D2}' -f $lat)
  if($lon -lt 0){$ew='W'+('{0:D3}' -f ([math]::Abs($lon)))}else{$ew='E'+('{0:D3}' -f $lon)}
  $name='Copernicus_DSM_COG_10_'+$ns+'_00_'+$ew+'_00_DEM'
  $url='https://copernicus-dem-30m.s3.amazonaws.com/'+$name+'/'+$name+'.tif'
  $dst=Join-Path $Out ($name+'.tif')
  if(Test-Path $dst){$downloaded += $dst; if($downloaded.Count -ge 2){ break } else { continue }}
  Write-T117Heartbeat 'running' ('download '+$name)
  try{
    Invoke-WebRequest -Uri $url -OutFile $dst -TimeoutSec 900 -UseBasicParsing
    if((Test-Path $dst) -and ((Get-Item $dst).Length -gt 1000000)){ $downloaded += $dst }
    else { Remove-Item $dst -Force -ErrorAction SilentlyContinue }
  }catch{ Add-Content -Encoding UTF8 $Rep ('failed '+$name+' '+$_.Exception.Message) }
  if($downloaded.Count -ge 2){ break }
}
$status=if($downloaded.Count -gt 0){'finished_dem_downloaded'}else{'failed_no_dem_downloaded'}
@{task_id='t117';status=$status;downloaded_count=$downloaded.Count;files=$downloaded;folder=$Out;db_write=$false;production_deploy=$false;fake_data=$false;next='rerun AAYS112 with downloaded DEM'} | ConvertTo-Json -Depth 5 | Set-Content -Encoding UTF8 $Res
@('# t117 DEM download','status='+$status,'downloaded_count='+$downloaded.Count,'folder='+$Out,'fake_data=false') | Set-Content -Encoding UTF8 $Rep
Write-T117Heartbeat $status ('downloaded='+$downloaded.Count)
if($downloaded.Count -gt 0){exit 0}else{exit 2}
