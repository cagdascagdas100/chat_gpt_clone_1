$ErrorActionPreference = 'Continue'
$TaskId = 'aays-060-run-056-redirectfix-columncopy-20260514'
$BridgeRoot = if ($env:AAYS_BRIDGE_ROOT) { $env:AAYS_BRIDGE_ROOT } else { Split-Path -Parent $PSScriptRoot }
$ResultDir = Join-Path $BridgeRoot 'ai-results'
New-Item -ItemType Directory -Force -Path $ResultDir | Out-Null
$Stamp = Get-Date -Format 'yyyyMMdd_HHmmss'
$Report = Join-Path $ResultDir "aays-060-columncopy-$Stamp.md"
$Src = Join-Path $PSScriptRoot 'aays_056_db_dryrun_no_pgctl_20260514.ps1'
$Patched = Join-Path $env:TEMP "aays_060_columncopy_$Stamp.ps1"
function W([string]$m){ $m | Add-Content -Encoding UTF8 $Report }
'# AAYS 060 Column-copy Wrapper' | Set-Content -Encoding UTF8 $Report
W ('Generated: ' + (Get-Date -Format s))
W ('source: ' + $Src)
W ('patched: ' + $Patched)
if(!(Test-Path $Src)){ W 'ERROR: source script missing'; exit 2 }
$text = Get-Content -Raw -Encoding UTF8 $Src
$oldRedirect = '$proc = Start-Process -FilePath $Postgres -ArgumentList $pgArgs -RedirectStandardOutput $LogFile -RedirectStandardError $LogFile -PassThru -WindowStyle Hidden'
$newRedirect = '$PgOutLog = [IO.Path]::ChangeExtension($LogFile, ''.out.log'')' + "`r`n" + '$PgErrLog = [IO.Path]::ChangeExtension($LogFile, ''.err.log'')' + "`r`n" + '$proc = Start-Process -FilePath $Postgres -ArgumentList $pgArgs -RedirectStandardOutput $PgOutLog -RedirectStandardError $PgErrLog -PassThru -WindowStyle Hidden'
$text = $text.Replace($oldRedirect,$newRedirect)
$oldCopy = '$copy = "\copy aays_land_sales.stg_land_sales_3110 FROM ''$CsvPg'' WITH (FORMAT csv, HEADER true, ENCODING ''UTF8'')"'
$newCopy = @'
$csvHeader = (Get-Content -Path $Csv -TotalCount 1 -Encoding UTF8)
$csvColumns = $csvHeader.Split(',') | ForEach-Object { $_.Trim().Trim(''"'') } | Where-Object { $_ }
$quotedColumns = ($csvColumns | ForEach-Object { ''"'' + ($_.Replace(''"'',''""'')) + ''"'' }) -join '',''
$copy = "\copy aays_land_sales.stg_land_sales_3110 ($quotedColumns) FROM ''$CsvPg'' WITH (FORMAT csv, HEADER true, ENCODING ''UTF8'')"
'@
if($text -notlike "*$oldCopy*"){
  W 'ERROR: copy line not found'
  exit 3
}
$text = $text.Replace($oldCopy,$newCopy)
$text = $text.Replace('AAYS_056_DB_DRYRUN_NO_PGCTL_DONE=true','AAYS_060_COLUMNCOPY_DONE=true')
Set-Content -Encoding UTF8 -Path $Patched -Value $text
W 'PATCHED_OK=true'
$outFile = Join-Path $ResultDir "aays-060-child-stdout-$Stamp.log"
$errFile = Join-Path $ResultDir "aays-060-child-stderr-$Stamp.log"
$p = Start-Process powershell.exe -ArgumentList @('-NoProfile','-ExecutionPolicy','Bypass','-File',$Patched) -RedirectStandardOutput $outFile -RedirectStandardError $errFile -PassThru -WindowStyle Hidden
$ok = $p.WaitForExit(700000)
if(-not $ok){ W 'CHILD_TIMEOUT=true'; try{ Stop-Process -Id $p.Id -Force -ErrorAction SilentlyContinue }catch{}; exit 124 }
W ('CHILD_EXIT_CODE=' + $p.ExitCode)
W '## child stdout tail'
if(Test-Path $outFile){ Get-Content $outFile -Tail 160 | Add-Content -Encoding UTF8 $Report }
W '## child stderr tail'
if(Test-Path $errFile){ Get-Content $errFile -Tail 160 | Add-Content -Encoding UTF8 $Report }
if($p.ExitCode -eq 0){ W 'AAYS_060_COLUMNCOPY_WRAPPER_DONE=true' } else { W 'AAYS_060_COLUMNCOPY_WRAPPER_DONE=false' }
exit $p.ExitCode
