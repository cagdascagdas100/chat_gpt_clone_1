param([string]$Root='C:\AAYS_GITHUB_BRIDGE_CLEAN2')
$ErrorActionPreference='Continue'
$results=Join-Path $Root 'ai-results'
New-Item -ItemType Directory -Force -Path $results | Out-Null
$base=Join-Path $results 'aays-112-parcel-elevation-evidence-export-20260519'
$json=$base+'.result.json'
$csv=$base+'.csv'
$report=$base+'.report.md'
$xlsx=$base+'.xlsx'
$start=Get-Date
$parcel=@()
$dem=@()
if(Test-Path $Root){
  $parcel=Get-ChildItem $Root -Recurse -File -ErrorAction SilentlyContinue | Where-Object { $_.Name -match 'parcel|geometry|boundary|land' } | Select-Object -First 80 FullName,Length,LastWriteTime
  $dem=Get-ChildItem $Root -Recurse -File -ErrorAction SilentlyContinue | Where-Object { $_.Name -match 'dem|dtm|elevation|terrain|topograph|slope' } | Select-Object -First 80 FullName,Length,LastWriteTime
}
$rows=@()
$i=0
foreach($p in $parcel){
  $i++
  $rows += [pscustomobject]@{row=$i;parcel_candidate=$p.FullName;parcel_bytes=$p.Length;dem_candidate='';status='candidate_only';note='elevation_not_sampled_without_confirmed_dem_match'}
}
if($rows.Count -eq 0){$rows += [pscustomobject]@{row=1;parcel_candidate='';parcel_bytes=0;dem_candidate='';status='blocked';note='no_candidate_parcel_file_found'}}
$rows | Export-Csv -Path $csv -NoTypeInformation -Encoding UTF8
$xlsxWritten=$false
try{
  $excel=New-Object -ComObject Excel.Application
  $excel.Visible=$false
  $wb=$excel.Workbooks.Open($csv)
  $wb.SaveAs($xlsx,51)
  $wb.Close($false)
  $excel.Quit()
  $xlsxWritten=Test-Path $xlsx
}catch{}
$blockers=@()
if($parcel.Count -eq 0){$blockers+='no_candidate_parcel_file_found'}
if($dem.Count -eq 0){$blockers+='no_candidate_dem_file_found'}
if(-not $xlsxWritten){$blockers+='xlsx_not_written_excel_com_unavailable'}
$status=if($blockers.Count -eq 0){'completed_candidate_export'}else{'blocked_candidate_export'}
[ordered]@{status=$status;rows_written=$rows.Count;xlsx_written=$xlsxWritten;csv_written=(Test-Path $csv);elevation_sampled=$false;blockers=$blockers;warnings=@('no_fake_elevation_values_written');candidate_parcel_files=$parcel.Count;candidate_dem_files=$dem.Count;output_xlsx=$xlsx;output_csv=$csv;started_at=$start.ToString('s');finished_at=(Get-Date).ToString('s')} | ConvertTo-Json -Depth 6 | Set-Content -Path $json -Encoding UTF8
Set-Content -Path $report -Encoding UTF8 -Value "# AAYS 112 Parcel Elevation Evidence Export`nstatus=$status`nrows_written=$($rows.Count)`ncsv_written=$(Test-Path $csv)`nxlsx_written=$xlsxWritten`nelevation_sampled=false`nblockers=$($blockers -join ',')`noutput_csv=$csv`noutput_xlsx=$xlsx`n"
