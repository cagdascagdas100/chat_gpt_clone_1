param([int]$TargetMinutes=36)
$Start=Get-Date
$End=$Start.AddMinutes($TargetMinutes)
$Bridge='C:\AAYS_GITHUB_BRIDGE_CLEAN2'
$Data='E:\AAYS_DATA\contractor'
$Exp=Join-Path $Data 'exports'
$Man=Join-Path $Data 'manifests'
$Prog=Join-Path $Bridge 'ai-progress'
$Res=Join-Path $Bridge 'ai-results'
New-Item -ItemType Directory -Force -Path $Exp,$Man,$Prog,$Res | Out-Null
$Progress=Join-Path $Prog 'contractor-003-official-source-normalizer-20260520.progress.md'
$Result=Join-Path $Res 'contractor-003-official-source-normalizer-20260520.result.json'
$Report=Join-Path $Res 'contractor-003-official-source-normalizer-20260520.report.md'
$OutCsv=Join-Path $Exp 'contractor_003_official_source_normalized.csv'
$OutJson=Join-Path $Man 'contractor_003_official_source_normalized.json'
function AddL($p,$t){Add-Content -Path $p -Encoding UTF8 -Value $t}
Set-Content -Path $Progress -Encoding UTF8 -Value "# Contractor 003 progress`nstart=$($Start.ToString('s'))`n"
$sources=@(
  [pscustomobject]@{name='Companies House';url='https://find-and-update.company-information.service.gov.uk/';type='registry'},
  [pscustomobject]@{name='GOV.UK';url='https://www.gov.uk/';type='public'},
  [pscustomobject]@{name='Environment Agency';url='https://www.gov.uk/government/organisations/environment-agency';type='public'},
  [pscustomobject]@{name='Planning Data';url='https://www.planning.data.gov.uk/';type='public'},
  [pscustomobject]@{name='UK Find Tender';url='https://www.find-tender.service.gov.uk/';type='public'}
)
$rows=@();$i=0
foreach($s in $sources){$i++;$rows += [pscustomobject]@{source_id=('SRC-{0:D3}' -f $i);name=$s.name;url=$s.url;type=$s.type;normalized_status='ready_for_collection';contractor_rows_created=0}}
$rows | Export-Csv -Path $OutCsv -NoTypeInformation -Encoding UTF8
$rows | ConvertTo-Json -Depth 6 | Set-Content -Path $OutJson -Encoding UTF8
$phase=0
while((Get-Date)-lt $End){$phase++;AddL $Progress "phase=$phase time=$((Get-Date).ToString('s')) sources=$($rows.Count)";Start-Sleep -Seconds 60}
$status='completed_sources_normalized_no_contractor_rows'
[ordered]@{status=$status;elapsed_minutes=[math]::Round(((Get-Date)-$Start).TotalMinutes,2);sources=$rows.Count;contractor_rows_created=0;outputs=@($OutCsv,$OutJson);safety=[ordered]@{fake_contractors=$false;db_write=$false;production_deploy=$false};next_task='contractor-004-real-source-fetch-or-manual-ingest'} | ConvertTo-Json -Depth 8 | Set-Content -Path $Result -Encoding UTF8
Set-Content -Path $Report -Encoding UTF8 -Value "# Contractor 003 Official Source Normalizer`nstatus=$status`nelapsed_minutes=$([math]::Round(((Get-Date)-$Start).TotalMinutes,2))`nsources=$($rows.Count)`ncontractor_rows_created=0`nresult=$Result`n"
