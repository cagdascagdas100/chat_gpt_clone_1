$TaskId='terrayield-117-plan-l-manifest-accept'
$Run=Get-Date -Format 'yyyyMMdd_HHmmss'
$Bridge='C:\Users\cagda\Documents\chat_gpt_clone_1'
$Plan='D:\6 color parcells\plan_l_run01'
$Out=Join-Path $Plan 'output'
$Final=Join-Path $Plan ('final_packages\manifest_accept_'+$Run)
$Result=Join-Path $Bridge 'ai-results'
$Beat=Join-Path $Bridge 'ai-heartbeat'
New-Item -ItemType Directory -Force -Path $Final,$Result,$Beat | Out-Null
$Summary=Join-Path $Result ($TaskId+'-summary.md')
$Status=Join-Path $Result ($TaskId+'-status.txt')
function L($x){$x | Add-Content -Encoding UTF8 $Summary}
@('TASK_ID='+$TaskId,'STATUS=started','UPDATED='+(Get-Date -Format s)) | Set-Content -Encoding UTF8 (Join-Path $Beat ($TaskId+'.txt'))
$files=@('london_6color.geojson','london_6color.csv','london_6color_summary.csv','london_6color_confidence_summary.csv')
foreach($f in $files){$p=Join-Path $Out $f; if(Test-Path $p){Copy-Item -Force $p $Final}}
$qa=Join-Path $Out 'qa'
if(Test-Path $qa){Copy-Item -Recurse -Force $qa (Join-Path $Final 'qa')}
$manifest=Join-Path $Final 'ACCEPTANCE_MANIFEST.txt'
@('TASK='+$TaskId,'RUN='+$Run,'FINAL_DIR='+$Final,'GENERATED='+(Get-Date -Format s),'') | Set-Content -Encoding UTF8 $manifest
Get-ChildItem -File -Recurse $Final | Sort-Object FullName | ForEach-Object {($_.FullName.Substring($Final.Length+1)+' bytes='+$_.Length+' sha256='+(Get-FileHash -Algorithm SHA256 -LiteralPath $_.FullName).Hash) | Add-Content -Encoding UTF8 $manifest}
function Rows($p){try{if(Test-Path $p){return @((Import-Csv -LiteralPath $p)).Count}}catch{return -1};return 0}
$csv=Join-Path $Out 'london_6color.csv'
$geo=Join-Path $Out 'london_6color.geojson'
$rows=Rows $csv
$features=0
try{if(Test-Path $geo){$j=Get-Content -Raw -Encoding UTF8 $geo | ConvertFrom-Json; $features=$j.features.Count}}catch{$features=-1}
$ok=($rows -gt 0 -and $features -eq $rows -and (Test-Path $manifest))
L '# Plan L manifest acceptance'
L ('ROWS='+$rows)
L ('FEATURES='+$features)
L ('MATCH='+($features -eq $rows))
L ('FINAL_DIR='+$Final)
L ('MANIFEST='+$manifest)
if(Test-Path (Join-Path $Out 'london_6color_summary.csv')){L 'SUMMARY_BEGIN'; Get-Content (Join-Path $Out 'london_6color_summary.csv') | ForEach-Object {L $_}; L 'SUMMARY_END'}
if(Test-Path (Join-Path $Out 'london_6color_confidence_summary.csv')){L 'CONF_BEGIN'; Get-Content (Join-Path $Out 'london_6color_confidence_summary.csv') | ForEach-Object {L $_}; L 'CONF_END'}
$res=if($ok){'accepted_manifest_package'}else{'needs_attention_manifest_package'}
@('TASK='+$TaskId,'RESULT='+$res,'ROWS='+$rows,'FEATURES='+$features,'FINAL_DIR='+$Final,'MANIFEST='+$manifest,'NEXT_COMMAND=devam et') | Set-Content -Encoding UTF8 $Status
@('TASK_ID='+$TaskId,'STATUS=finished','UPDATED='+(Get-Date -Format s)) | Set-Content -Encoding UTF8 (Join-Path $Beat ($TaskId+'.txt'))
