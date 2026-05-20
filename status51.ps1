$Root='C:/AAYS_GITHUB_BRIDGE_CLEAN2'
$Start=Get-Date
$End=$Start.AddMinutes(35)
$Res=Join-Path $Root 'ai-results'
$Prog=Join-Path $Root 'ai-progress'
New-Item -ItemType Directory -Force -Path $Res,$Prog | Out-Null
$Progress=Join-Path $Prog 'status51.progress.md'
$Result=Join-Path $Res 'status51.result.json'
$Report=Join-Path $Res 'status51.report.md'
Set-Content -Path $Progress -Encoding UTF8 -Value "# status51 progress`nstart=$($Start.ToString('s'))`n"
$i=0
while((Get-Date)-lt $End){
  $i++
  Add-Content -Path $Progress -Encoding UTF8 -Value "phase=$i time=$((Get-Date).ToString('s')) mode=long_status_watch"
  Start-Sleep -Seconds 60
}
[ordered]@{status='completed_status_watch';elapsed_minutes=[math]::Round(((Get-Date)-$Start).TotalMinutes,2);db_write=$false;production_deploy=$false;fake_data=$false;next_command='devam et'} | ConvertTo-Json -Depth 5 | Set-Content -Path $Result -Encoding UTF8
Set-Content -Path $Report -Encoding UTF8 -Value "# status51`nstatus=completed_status_watch`ndb_write=false`nproduction_deploy=false`nnext_command=devam et`n"
