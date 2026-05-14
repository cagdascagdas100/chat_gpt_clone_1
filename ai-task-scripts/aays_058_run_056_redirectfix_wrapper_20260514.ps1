$ErrorActionPreference = 'Continue'
$TaskId = 'aays-058-run-056-redirectfix-wrapper-20260514'
$BridgeRoot = if ($env:AAYS_BRIDGE_ROOT) { $env:AAYS_BRIDGE_ROOT } else { Split-Path -Parent $PSScriptRoot }
$ResultDir = Join-Path $BridgeRoot 'ai-results'
New-Item -ItemType Directory -Force -Path $ResultDir | Out-Null
$Stamp = Get-Date -Format 'yyyyMMdd_HHmmss'
$WrapperReport = Join-Path $ResultDir "aays-058-wrapper-$Stamp.md"
$Src = Join-Path $PSScriptRoot 'aays_056_db_dryrun_no_pgctl_20260514.ps1'
$Patched = Join-Path $env:TEMP "aays_056_redirectfix_$Stamp.ps1"
'# AAYS 058 Wrapper for AAYS 056 Redirect Fix' | Set-Content -Encoding UTF8 $WrapperReport
('Generated: ' + (Get-Date -Format s)) | Add-Content -Encoding UTF8 $WrapperReport
('source: ' + $Src) | Add-Content -Encoding UTF8 $WrapperReport
('patched: ' + $Patched) | Add-Content -Encoding UTF8 $WrapperReport
if(!(Test-Path $Src)){
  'ERROR: source script missing' | Add-Content -Encoding UTF8 $WrapperReport
  exit 2
}
$text = Get-Content -Raw -Encoding UTF8 $Src
$old = '$proc = Start-Process -FilePath $Postgres -ArgumentList $pgArgs -RedirectStandardOutput $LogFile -RedirectStandardError $LogFile -PassThru -WindowStyle Hidden'
$new = '$PgOutLog = [IO.Path]::ChangeExtension($LogFile, ''.out.log'')' + "`r`n" + '$PgErrLog = [IO.Path]::ChangeExtension($LogFile, ''.err.log'')' + "`r`n" + '$proc = Start-Process -FilePath $Postgres -ArgumentList $pgArgs -RedirectStandardOutput $PgOutLog -RedirectStandardError $PgErrLog -PassThru -WindowStyle Hidden'
if($text -notlike "*$old*"){
  'ERROR: expected redirect line not found' | Add-Content -Encoding UTF8 $WrapperReport
  exit 3
}
$text = $text.Replace($old,$new)
$text = $text.Replace('AAYS_056_DB_DRYRUN_NO_PGCTL_DONE=true','AAYS_058_DB_DRYRUN_REDIRECTFIX_WRAPPER_DONE=true')
$text = $text.Replace('plan_progress_percent: 100','plan_progress_percent: 100')
Set-Content -Encoding UTF8 -Path $Patched -Value $text
'PATCHED_OK=true' | Add-Content -Encoding UTF8 $WrapperReport
$outFile = Join-Path $ResultDir "aays-058-wrapper-child-stdout-$Stamp.log"
$errFile = Join-Path $ResultDir "aays-058-wrapper-child-stderr-$Stamp.log"
$proc = Start-Process powershell.exe -ArgumentList @('-NoProfile','-ExecutionPolicy','Bypass','-File',$Patched) -RedirectStandardOutput $outFile -RedirectStandardError $errFile -PassThru -WindowStyle Hidden
$ok = $proc.WaitForExit(600000)
if(-not $ok){
  'CHILD_TIMEOUT=true' | Add-Content -Encoding UTF8 $WrapperReport
  exit 124
}
('CHILD_EXIT_CODE=' + $proc.ExitCode) | Add-Content -Encoding UTF8 $WrapperReport
'## child stdout tail' | Add-Content -Encoding UTF8 $WrapperReport
if(Test-Path $outFile){ Get-Content $outFile -Tail 120 | Add-Content -Encoding UTF8 $WrapperReport }
'## child stderr tail' | Add-Content -Encoding UTF8 $WrapperReport
if(Test-Path $errFile){ Get-Content $errFile -Tail 120 | Add-Content -Encoding UTF8 $WrapperReport }
if($proc.ExitCode -eq 0){ 'AAYS_058_WRAPPER_DONE=true' | Add-Content -Encoding UTF8 $WrapperReport } else { 'AAYS_058_WRAPPER_DONE=false' | Add-Content -Encoding UTF8 $WrapperReport }
exit $proc.ExitCode
