$ErrorActionPreference = 'Continue'
$TaskId = 'aays-062-run-056-copy-columns-wrapper-20260514'
$BridgeRoot = if ($env:AAYS_BRIDGE_ROOT) { $env:AAYS_BRIDGE_ROOT } else { Split-Path -Parent $PSScriptRoot }
$ResultDir = Join-Path $BridgeRoot 'ai-results'
New-Item -ItemType Directory -Force -Path $ResultDir | Out-Null
$Stamp = Get-Date -Format 'yyyyMMdd_HHmmss'
$WrapperReport = Join-Path $ResultDir "aays-062-copy-columns-wrapper-$Stamp.md"
$Src = Join-Path $PSScriptRoot 'aays_056_db_dryrun_no_pgctl_20260514.ps1'
$Patched = Join-Path $env:TEMP "aays_056_copy_columns_$Stamp.ps1"
'# AAYS 062 Wrapper for AAYS 056 Copy Columns Fix' | Set-Content -Encoding UTF8 $WrapperReport
('Generated: ' + (Get-Date -Format s)) | Add-Content -Encoding UTF8 $WrapperReport
if(!(Test-Path $Src)){ 'ERROR: source script missing' | Add-Content -Encoding UTF8 $WrapperReport; exit 2 }
$text = Get-Content -Raw -Encoding UTF8 $Src
$oldRedirect = '$proc = Start-Process -FilePath $Postgres -ArgumentList $pgArgs -RedirectStandardOutput $LogFile -RedirectStandardError $LogFile -PassThru -WindowStyle Hidden'
$newRedirect = '$PgOutLog = [IO.Path]::ChangeExtension($LogFile, ''.out.log'')' + "`r`n" + '$PgErrLog = [IO.Path]::ChangeExtension($LogFile, ''.err.log'')' + "`r`n" + '$proc = Start-Process -FilePath $Postgres -ArgumentList $pgArgs -RedirectStandardOutput $PgOutLog -RedirectStandardError $PgErrLog -PassThru -WindowStyle Hidden'
if($text -like "*$oldRedirect*"){ $text = $text.Replace($oldRedirect,$newRedirect); 'REDIRECT_PATCHED=true' | Add-Content -Encoding UTF8 $WrapperReport } else { 'REDIRECT_PATCHED=false' | Add-Content -Encoding UTF8 $WrapperReport }
$oldCopy = '$copy = "\copy aays_land_sales.stg_land_sales_3110 FROM ''$CsvPg'' WITH (FORMAT csv, HEADER true, ENCODING ''UTF8'')"'
$newCopy = '$csvHeader = Get-Content -Path $Csv -TotalCount 1' + "`r`n" + '$copyColumns = (($csvHeader -split '','') | ForEach-Object { ''"'' + ($_.Trim().Trim(''"'').Replace(''"'',''""'')) + ''"'' }) -join '', ''' + "`r`n" + '$copy = "\copy aays_land_sales.stg_land_sales_3110 ($copyColumns) FROM ''$CsvPg'' WITH (FORMAT csv, HEADER true, ENCODING ''UTF8'')"'
if($text -like "*$oldCopy*"){ $text = $text.Replace($oldCopy,$newCopy); 'COPY_COLUMNS_PATCHED=true' | Add-Content -Encoding UTF8 $WrapperReport } else { 'COPY_COLUMNS_PATCHED=false' | Add-Content -Encoding UTF8 $WrapperReport; exit 3 }
$text = $text.Replace('AAYS_056_DB_DRYRUN_NO_PGCTL_DONE=true','AAYS_062_COPY_COLUMNS_WRAPPER_DONE=true')
Set-Content -Encoding UTF8 -Path $Patched -Value $text
('patched: ' + $Patched) | Add-Content -Encoding UTF8 $WrapperReport
$outFile = Join-Path $ResultDir "aays-062-child-stdout-$Stamp.log"
$errFile = Join-Path $ResultDir "aays-062-child-stderr-$Stamp.log"
$proc = Start-Process powershell.exe -ArgumentList @('-NoProfile','-ExecutionPolicy','Bypass','-File',$Patched) -RedirectStandardOutput $outFile -RedirectStandardError $errFile -PassThru -WindowStyle Hidden
$ok = $proc.WaitForExit(900000)
if(-not $ok){ 'CHILD_TIMEOUT=true' | Add-Content -Encoding UTF8 $WrapperReport; try{Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue}catch{}; exit 124 }
('CHILD_EXIT_CODE=' + $proc.ExitCode) | Add-Content -Encoding UTF8 $WrapperReport
'## child stdout tail' | Add-Content -Encoding UTF8 $WrapperReport
if(Test-Path $outFile){ Get-Content $outFile -Tail 180 | Add-Content -Encoding UTF8 $WrapperReport }
'## child stderr tail' | Add-Content -Encoding UTF8 $WrapperReport
if(Test-Path $errFile){ Get-Content $errFile -Tail 180 | Add-Content -Encoding UTF8 $WrapperReport }
if($proc.ExitCode -eq 0){ 'AAYS_062_WRAPPER_DONE=true' | Add-Content -Encoding UTF8 $WrapperReport } else { 'AAYS_062_WRAPPER_DONE=false' | Add-Content -Encoding UTF8 $WrapperReport }
exit $proc.ExitCode
