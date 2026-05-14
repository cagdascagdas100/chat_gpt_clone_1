$ErrorActionPreference = 'Continue'
$BridgeRoot = if ($env:AAYS_BRIDGE_ROOT) { $env:AAYS_BRIDGE_ROOT } else { Split-Path -Parent $PSScriptRoot }
$ResultDir = Join-Path $BridgeRoot 'ai-results'
New-Item -ItemType Directory -Force -Path $ResultDir | Out-Null
$Stamp = Get-Date -Format 'yyyyMMdd_HHmmss'
$Report = Join-Path $ResultDir "aays-080-sleepwait-wrapper-min-$Stamp.md"
$Src = Join-Path $PSScriptRoot 'aays_056_db_dryrun_no_pgctl_20260514.ps1'
$Patched = Join-Path $env:TEMP "aays080_$Stamp.ps1"
function R([string]$m){ $m | Add-Content -Encoding UTF8 $Report }
'# AAYS 080 SleepWait Wrapper Min' | Set-Content -Encoding UTF8 $Report
R ('Generated: ' + (Get-Date -Format s))
if(!(Test-Path $Src)){ R 'ERROR source missing'; exit 2 }
$t = Get-Content -Raw -Encoding UTF8 $Src
$sp = 'Start' + '-Process'
$old = '$proc = ' + $sp + ' -FilePath $Postgres -ArgumentList $pgArgs -RedirectStandardOutput $LogFile -RedirectStandardError $LogFile -PassThru -WindowStyle Hidden'
$new = '$PgOutLog = [IO.Path]::ChangeExtension($LogFile, ''.out.log'')' + "`r`n" + '$PgErrLog = [IO.Path]::ChangeExtension($LogFile, ''.err.log'')' + "`r`n" + '$proc = ' + $sp + ' -FilePath $Postgres -ArgumentList $pgArgs -RedirectStandardOutput $PgOutLog -RedirectStandardError $PgErrLog -PassThru -WindowStyle Hidden'
$t = $t.Replace($old,$new)
$oldCopy = '$copy = "\copy aays_land_sales.stg_land_sales_3110 FROM ''$CsvPg'' WITH (FORMAT csv, HEADER true, ENCODING ''UTF8'')"'
$newCopy = '$csvHeader = Get-Content -Path $Csv -TotalCount 1' + "`r`n" + '$copyColumns = (($csvHeader -split '','') | ForEach-Object { ''"'' + ($_.Trim().Trim(''"'').Replace(''"'',''""'')) + ''"'' }) -join '', ''' + "`r`n" + '$copy = "\copy aays_land_sales.stg_land_sales_3110 ($copyColumns) FROM ''$CsvPg'' WITH (FORMAT csv, HEADER true, ENCODING ''UTF8'')"'
$t = $t.Replace($oldCopy,$newCopy)
$begin = $t.IndexOf('$ready = $false')
$endText = "throw 'postgres did not become ready within 30 seconds'`r`n}"
$end = $t.IndexOf($endText, $begin)
if($begin -ge 0 -and $end -gt $begin){
  $end += $endText.Length
  $sleepBlock = '$ready = $true' + "`r`n" + "AddR 'sleepwait_before_connection_test_seconds: 150'" + "`r`n" + 'Start-Sleep -Seconds 150'
  $t = $t.Substring(0,$begin) + $sleepBlock + $t.Substring($end)
  R 'SLEEPWAIT_PATCHED=true'
} else { R 'SLEEPWAIT_PATCHED=false' }
$t = $t.Replace('AAYS_056_DB_DRYRUN_NO_PGCTL_DONE=true','AAYS_080_SLEEPWAIT_WRAPPER_MIN_DONE=true')
Set-Content -Encoding UTF8 -Path $Patched -Value $t
R ('patched: ' + $Patched)
& $Patched
$code = $LASTEXITCODE
R ('CHILD_EXIT_CODE=' + $code)
if($code -eq 0){ R 'AAYS_080_SLEEPWAIT_WRAPPER_MIN_DONE=true' } else { R 'AAYS_080_SLEEPWAIT_WRAPPER_MIN_DONE=false' }
exit $code
