$ErrorActionPreference = 'Continue'
$BridgeRoot = if ($env:AAYS_BRIDGE_ROOT) { $env:AAYS_BRIDGE_ROOT } else { Split-Path -Parent $PSScriptRoot }
$ResultDir = Join-Path $BridgeRoot 'ai-results'
New-Item -ItemType Directory -Force -Path $ResultDir | Out-Null
$Stamp = Get-Date -Format 'yyyyMMdd_HHmmss'
$Report = Join-Path $ResultDir "aays-086-sleepwait-jsonb-fix-$Stamp.md"
$Src = Join-Path $PSScriptRoot 'aays_056_db_dryrun_no_pgctl_20260514.ps1'
$Patched = Join-Path $env:TEMP "aays086_$Stamp.ps1"
function AddLine { param([string]$m) $m | Add-Content -Encoding UTF8 $Report }
'# AAYS 086 SleepWait JSONB Fix' | Set-Content -Encoding UTF8 $Report
AddLine ('Generated: ' + (Get-Date -Format s))
if(!(Test-Path $Src)){ AddLine 'ERROR source missing'; exit 2 }
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
  $sleepBlock = '$ready = $true' + "`r`n" + "AddR 'sleepwait_before_connection_test_seconds: 180'" + "`r`n" + 'Start-Sleep -Seconds 180'
  $t = $t.Substring(0,$begin) + $sleepBlock + $t.Substring($end)
  AddLine 'SLEEPWAIT_PATCHED=true'
} else { AddLine 'SLEEPWAIT_PATCHED=false' }
$bad = "SELECT COUNT(*) AS verified_polygon_non_empty FROM aays_land_sales.stg_land_sales_3110 WHERE NULLIF(TRIM(verified_polygon_geojson), '') IS NOT NULL;"
$good = "SELECT COUNT(*) AS verified_polygon_non_empty FROM aays_land_sales.stg_land_sales_3110 WHERE verified_polygon_geojson IS NOT NULL AND verified_polygon_geojson::text NOT IN ('null', '{}', '[]', '\"\"');"
if($t.Contains($bad)){ $t = $t.Replace($bad,$good); AddLine 'JSONB_STEP10_PATCHED=true' } else { AddLine 'JSONB_STEP10_PATCHED=false' }
$t = $t.Replace('AAYS_056_DB_DRYRUN_NO_PGCTL_DONE=true','AAYS_086_SLEEPWAIT_JSONB_FIX_DONE=true')
Set-Content -Encoding UTF8 -Path $Patched -Value $t
Start-Sleep -Seconds 2
AddLine ('patched: ' + $Patched)
$out = Join-Path $ResultDir "aays-086-child-stdout-$Stamp.log"
$err = Join-Path $ResultDir "aays-086-child-stderr-$Stamp.log"
$p = Start-Process powershell.exe -ArgumentList @('-NoProfile','-ExecutionPolicy','Bypass','-File',$Patched) -RedirectStandardOutput $out -RedirectStandardError $err -PassThru -WindowStyle Hidden
$ok = $p.WaitForExit(900000)
if(-not $ok){ try{Stop-Process -Id $p.Id -Force -ErrorAction SilentlyContinue}catch{}; AddLine 'CHILD_TIMEOUT=true'; exit 124 }
AddLine ('CHILD_EXIT_CODE=' + $p.ExitCode)
AddLine '## child stdout tail'
if(Test-Path $out){ Get-Content $out -Tail 220 | Add-Content -Encoding UTF8 $Report }
AddLine '## child stderr tail'
if(Test-Path $err){ Get-Content $err -Tail 220 | Add-Content -Encoding UTF8 $Report }
if($p.ExitCode -eq 0){ AddLine 'AAYS_086_SLEEPWAIT_JSONB_FIX_DONE=true' } else { AddLine 'AAYS_086_SLEEPWAIT_JSONB_FIX_DONE=false' }
exit $p.ExitCode
