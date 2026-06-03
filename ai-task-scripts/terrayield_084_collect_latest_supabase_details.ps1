$ErrorActionPreference='Continue'
$Root='C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence'
$Pattern='terrayield__082_supabase_admin_compat_5worker__*'
Write-Output 'PROJECT=terrayield'
Write-Output 'DISPLAY_PROJECT=TerraYield'
Write-Output 'CHATGPT_PAGE_PROJECT=aays1'
Write-Output 'TASK=terrayield-084-collect-latest-supabase-details'
Write-Output 'MODE=collect latest supabase compatibility run details'
$base=Join-Path $Root '.aays_real_runs'
$latest=Get-ChildItem -LiteralPath $base -Directory -ErrorAction SilentlyContinue | Where-Object { $_.Name -like $Pattern } | Sort-Object LastWriteTime -Descending | Select-Object -First 1
if(!$latest){Write-Output 'LATEST_RUN=not_found'; exit 2}
Write-Output ('LATEST_RUN='+$latest.FullName)
foreach($name in @('terrayield__082_status.txt','terrayield__082_scorecard.csv','terrayield__082_summary.md')){
  $p=Join-Path $latest.FullName $name
  Write-Output ('--- FILE '+$p+' ---')
  if(Test-Path $p){Get-Content -LiteralPath $p -Raw -ErrorAction SilentlyContinue}else{Write-Output 'missing'}
}
$slots=Join-Path $latest.FullName 'slots'
Get-ChildItem -LiteralPath $slots -File -ErrorAction SilentlyContinue | Sort-Object Name | ForEach-Object {
  Write-Output ('--- SLOT '+$_.Name+' ---')
  Get-Content -LiteralPath $_.FullName -Raw -ErrorAction SilentlyContinue
}
Write-Output 'TERRAYIELD_084_COLLECT_LATEST_SUPABASE_DETAILS_DONE'
exit 0
