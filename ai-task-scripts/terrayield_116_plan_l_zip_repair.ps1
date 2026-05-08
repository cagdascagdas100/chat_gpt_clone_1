$ErrorActionPreference='Continue'
$TaskId='terrayield-116-plan-l-zip-repair'
$Bridge='C:\Users\cagda\Documents\chat_gpt_clone_1'
$PlanBase='D:\6 color parcells\plan_l_run01'
$OutputDir=Join-Path $PlanBase 'output'
$FinalRoot=Join-Path $PlanBase 'final_packages'
$ResultDir=Join-Path $Bridge 'ai-results'
New-Item -ItemType Directory -Force -Path $ResultDir,$FinalRoot|Out-Null
$Status=Join-Path $ResultDir ($TaskId+'-status.txt')
$Summary=Join-Path $ResultDir ($TaskId+'-summary.md')
function W($x){Write-Output $x;Add-Content -Encoding UTF8 -Path $Summary -Value $x}
function CsvRows($p){try{if(Test-Path -LiteralPath $p){return @((Import-Csv -LiteralPath $p)).Count}}catch{return -1};return 0}
function GeoCount($p){try{if(Test-Path -LiteralPath $p){$j=Get-Content -Raw -Encoding UTF8 -LiteralPath $p|ConvertFrom-Json;return $j.features.Count}}catch{return -1};return 0}
W '# TerraYield 116 Plan L ZIP Repair - patched'
W ('TASK='+$TaskId)
W 'FIX=Compress-Archive now uses -Path wildcard with -ErrorAction Stop; previous -LiteralPath wildcard caused final_zip_exists=False.'
$latest=Get-ChildItem -LiteralPath $FinalRoot -Directory -ErrorAction SilentlyContinue|Where-Object{$_.Name -like 'terrayield-112-plan-l-recovery-final-pack_*'}|Sort-Object LastWriteTime -Descending|Select-Object -First 1
if(!$latest){@('TASK='+$TaskId,'RESULT=blocked_no_final_dir','FINAL_ZIP_EXISTS=False','NEXT_COMMAND=devam et')|Set-Content -Encoding UTF8 $Status;W 'RESULT=blocked_no_final_dir';exit 0}
$zipPath=$latest.FullName+'.zip'
$zipError=''
try{
  if(Test-Path -LiteralPath $zipPath){Remove-Item -Force -LiteralPath $zipPath}
  $src=Join-Path $latest.FullName '*'
  Compress-Archive -Path $src -DestinationPath $zipPath -Force -ErrorAction Stop
}catch{$zipError=$_.Exception.Message;W ('ZIP_ERROR='+$zipError)}
$csv=Join-Path $OutputDir 'london_6color.csv'
$geo=Join-Path $OutputDir 'london_6color.geojson'
$summaryCsv=Join-Path $OutputDir 'london_6color_summary.csv'
$confCsv=Join-Path $OutputDir 'london_6color_confidence_summary.csv'
$rows=CsvRows $csv
$features=GeoCount $geo
$zipExists=Test-Path -LiteralPath $zipPath
$zipBytes=0;if($zipExists){$zipBytes=(Get-Item -LiteralPath $zipPath).Length}
$accept=($rows -eq 34864 -and $features -eq 34864 -and (Test-Path -LiteralPath $summaryCsv) -and (Test-Path -LiteralPath $confCsv) -and $zipExists -and $zipBytes -gt 0)
W ('FINAL_DIR='+$latest.FullName)
W ('FINAL_ZIP='+$zipPath)
W ('FINAL_ZIP_EXISTS='+$zipExists)
W ('FINAL_ZIP_BYTES='+$zipBytes)
W ('CSV_ROWS='+$rows)
W ('GEOJSON_FEATURES='+$features)
W ('ROWS_FEATURES_MATCH='+($rows -eq $features))
W ('SUMMARY_EXISTS='+(Test-Path -LiteralPath $summaryCsv))
W ('CONFIDENCE_SUMMARY_EXISTS='+(Test-Path -LiteralPath $confCsv))
W ('FINAL_ACCEPTANCE='+$(if($accept){'100/100'}else{'needs_attention'}))
@('TASK='+$TaskId,'RESULT='+$(if($accept){'completed_plan_l_zip_repair'}else{'needs_attention_plan_l_zip_repair'}),'FINAL_ZIP='+$zipPath,'FINAL_ZIP_EXISTS='+$zipExists,'FINAL_ZIP_BYTES='+$zipBytes,'CSV_ROWS='+$rows,'GEOJSON_FEATURES='+$features,'ROWS_FEATURES_MATCH='+($rows -eq $features),'ZIP_ERROR='+$zipError,'FINAL_ACCEPTANCE='+$(if($accept){'100/100'}else{'needs_attention'}),'NEXT_COMMAND=devam et')|Set-Content -Encoding UTF8 $Status
exit 0
