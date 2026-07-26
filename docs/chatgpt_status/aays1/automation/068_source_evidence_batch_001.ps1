$ErrorActionPreference='Stop'
$Repo='F:\chatgpt\chat_gpt_clone_1_main'
$Bridge='F:\AAYS_GITHUB_BRIDGE_CLEAN2'
$Stamp=Get-Date -Format yyyyMMdd_HHmmss
$Data=Join-Path $Repo 'england_map_web\data\geometry_review_2of4_20260629'
$Csv=Get-ChildItem $Data -File | Where-Object {$_.Name -like '*2OF4*Geometry*Review*Queue*20260629*.csv'} | Select-Object -First 1
if(!$Csv){throw 'source csv missing'}
$Rows=Import-Csv $Csv.FullName | Select-Object -First 5
$Out=Join-Path $Repo 'docs\chatgpt_status\aays1\geometry_review_2of4_20260629\evidence_068_batch_001'
$Status=Join-Path $Repo 'docs\chatgpt_status\aays1\status'
New-Item -ItemType Directory -Force -Path $Out,$Status | Out-Null
$results=@()
$i=0
foreach($r in $Rows){
  $i++
  $url=$r.listing_url; if(!$url){$url=$r.source_url}; if(!$url){$url=$r.url}
  $state='NO_URL'; $bytes=0; $path=''
  if($url){
    $path=Join-Path $Out ('row_'+$i+'.html')
    try{
      $resp=Invoke-WebRequest -Uri $url -UseBasicParsing -TimeoutSec 30
      $resp.Content | Set-Content -Encoding UTF8 $path
      $bytes=(Get-Item $path).Length
      $state='FETCH_OK'
    } catch { $state='FETCH_FAILED'; $_.Exception.Message | Set-Content -Encoding UTF8 $path }
  }
  $results += [pscustomobject]@{row=$i;url=$url;source_status=$state;evidence_path=$path;bytes=$bytes;decision='KEEP_2OF4_PENDING_BOUNDARY_REVIEW'}
}
$OutCsv=Join-Path $Out 'batch_001_results.csv'
$results | Export-Csv -NoTypeInformation -Encoding UTF8 $OutCsv
"status=SOURCE_EVIDENCE_BATCH_001_DONE`nfinal_ready=false`nrows=$($results.Count)`noutput=$OutCsv`nupdated_at=$Stamp" | Set-Content -Encoding UTF8 (Join-Path $Status "068_source_evidence_batch_001_$Stamp.txt")
Set-Location $Repo
git add -- docs/chatgpt_status/aays1/geometry_review_2of4_20260629/evidence_068_batch_001 docs/chatgpt_status/aays1/status
git commit -m 'Run 2of4 source evidence batch 001'
git pull --rebase origin main
git push origin HEAD:main
"status=OK`nfinal_ready=false`nrows=$($results.Count)`nupdated_at=$Stamp" | Set-Content -Encoding UTF8 (Join-Path $Bridge 'ai-results\terrayield_068_source_evidence_batch_001.result.txt')
