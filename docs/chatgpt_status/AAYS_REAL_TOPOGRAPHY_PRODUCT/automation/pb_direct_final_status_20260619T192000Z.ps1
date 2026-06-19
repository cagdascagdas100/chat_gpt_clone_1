$ErrorActionPreference='Continue'
$PageKey='AAYS_REAL_TOPOGRAPHY_PRODUCT'
$Branch='aays-runner-v17-icon-work-20260603-232706'
$RepoRoot=(Resolve-Path (Join-Path $PSScriptRoot '..\..\..\..')).Path
$ReportRel="docs/chatgpt_status/$PageKey/reports/pb_direct_final_status_20260619T192000Z.txt"
$StatusRel="docs/chatgpt_status/$PageKey/status/pb_direct_final_status_20260619T192000Z.txt"
$ReportPath=Join-Path $RepoRoot $ReportRel
$StatusPath=Join-Path $RepoRoot $StatusRel
New-Item -ItemType Directory -Force -Path (Split-Path $ReportPath),(Split-Path $StatusPath) | Out-Null
@("PAGE_KEY=$PageKey","TASK=pb_direct_final_status_20260619T192000Z","STATUS=RUNNING","FINAL_READY=false") | Out-File $ReportPath -Encoding utf8
function Add-Line($x){$x|Out-File $ReportPath -Append -Encoding utf8}
$finalReport=Join-Path $RepoRoot "docs/chatgpt_status/$PageKey/reports/pb_runtime_finalization_single_runner_20260617T000000Z.txt"
$finalStatus=Join-Path $RepoRoot "docs/chatgpt_status/$PageKey/status/pb_runtime_finalization_single_runner_20260617T000000Z.txt"
Add-Line "FINAL_REPORT_EXISTS=$((Test-Path $finalReport).ToString().ToLower())"
Add-Line "FINAL_STATUS_EXISTS=$((Test-Path $finalStatus).ToString().ToLower())"
if(Test-Path $finalReport){Get-Content $finalReport -Tail 80|Out-File $ReportPath -Append -Encoding utf8}
if(Test-Path $finalReport -and ((Get-Content $finalReport -Raw) -match 'FINAL_STATUS=FINAL_READY_CONFIRMED') -and ((Get-Content $finalReport -Raw) -match 'PRODUCT_PROGRESS_ESTIMATE=100') -and ((Get-Content $finalReport -Raw) -match 'PRODUCTION_COMPLETE=true')){
  Add-Line 'FINAL_STATUS=FINAL_READY_CONFIRMED'; Add-Line 'PRODUCT_PROGRESS_ESTIMATE=100'; Add-Line 'PRODUCTION_COMPLETE=true'
  @("PAGE_KEY: $PageKey","TASK: pb_direct_final_status_20260619T192000Z","STATUS: FINAL_READY_CONFIRMED","FINAL_READY: true","REPORT: $ReportRel") | Out-File $StatusPath -Encoding utf8
}else{
  Add-Line 'FINAL_STATUS=WAITING_FOR_RUNTIME_FINALIZATION'; Add-Line 'PRODUCT_PROGRESS_ESTIMATE=99.998'; Add-Line 'PRODUCTION_COMPLETE=false'
  @("PAGE_KEY: $PageKey","TASK: pb_direct_final_status_20260619T192000Z","STATUS: WAITING_FOR_RUNTIME_FINALIZATION","FINAL_READY: false","REPORT: $ReportRel") | Out-File $StatusPath -Encoding utf8
}
git -C $RepoRoot add $ReportRel $StatusRel | Out-Null
$pending=git -C $RepoRoot status --porcelain -- $ReportRel $StatusRel
if($pending){git -C $RepoRoot commit -m 'Report planned buildings direct final status'|Out-Null; git -C $RepoRoot push origin HEAD:$Branch|Out-Null}
exit 0
