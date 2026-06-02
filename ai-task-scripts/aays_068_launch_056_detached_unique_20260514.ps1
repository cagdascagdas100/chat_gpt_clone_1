$ErrorActionPreference = 'Stop'
$TaskId = 'aays-068-launch-056-detached-unique-20260514'
$BridgeRoot = if ($env:AAYS_BRIDGE_ROOT) { $env:AAYS_BRIDGE_ROOT } else { Split-Path -Parent $PSScriptRoot }
$ResultDir = Join-Path $BridgeRoot 'ai-results'
$RunDir = Join-Path $BridgeRoot 'ai-longruns'
New-Item -ItemType Directory -Force -Path $ResultDir,$RunDir | Out-Null
$RunId = 'aays-068-' + (Get-Date -Format 'yyyyMMdd_HHmmss_ffff') + '-pid' + $PID + '-' + ([guid]::NewGuid().ToString('N').Substring(0,8))
$Manifest = Join-Path $RunDir ($RunId + '.json')
$Report = Join-Path $ResultDir ($RunId + '-launcher.md')
$Src = Join-Path $PSScriptRoot 'aays_056_db_dryrun_no_pgctl_20260514.ps1'
$Patched = Join-Path $RunDir ($RunId + '-worker.ps1')
$Stdout = Join-Path $RunDir ($RunId + '-stdout.log')
$Stderr = Join-Path $RunDir ($RunId + '-stderr.log')
$Lines = New-Object System.Collections.Generic.List[string]
function L([string]$m){ [void]$Lines.Add($m) }
L '# AAYS 068 detached launcher'
L ('Generated: ' + (Get-Date -Format s))
L ('TaskId: ' + $TaskId)
L ('RunId: ' + $RunId)
L ('Source: ' + $Src)
L ('Patched: ' + $Patched)
L ('Stdout: ' + $Stdout)
L ('Stderr: ' + $Stderr)
if(!(Test-Path $Src)){ L 'ERROR: source script missing'; Set-Content -Encoding UTF8 -Path $Report -Value $Lines; exit 2 }
$text = Get-Content -Raw -Encoding UTF8 $Src
$oldRedirect = '$proc = Start-Process -FilePath $Postgres -ArgumentList $pgArgs -RedirectStandardOutput $LogFile -RedirectStandardError $LogFile -PassThru -WindowStyle Hidden'
$newRedirect = '$PgOutLog = [IO.Path]::ChangeExtension($LogFile, ''.out.log'')' + "`r`n" + '$PgErrLog = [IO.Path]::ChangeExtension($LogFile, ''.err.log'')' + "`r`n" + '$proc = Start-Process -FilePath $Postgres -ArgumentList $pgArgs -RedirectStandardOutput $PgOutLog -RedirectStandardError $PgErrLog -PassThru -WindowStyle Hidden'
if($text -like "*$oldRedirect*"){ $text = $text.Replace($oldRedirect,$newRedirect); L 'REDIRECT_PATCHED=true' } else { L 'REDIRECT_PATCHED=false' }
$oldCopy = '$copy = "\copy aays_land_sales.stg_land_sales_3110 FROM ''$CsvPg'' WITH (FORMAT csv, HEADER true, ENCODING ''UTF8'')"'
$newCopy = '$csvHeader = Get-Content -Path $Csv -TotalCount 1' + "`r`n" + '$copyColumns = (($csvHeader -split '','') | ForEach-Object { ''"'' + ($_.Trim().Trim(''"'').Replace(''"'',''""'')) + ''"'' }) -join '', ''' + "`r`n" + '$copy = "\copy aays_land_sales.stg_land_sales_3110 ($copyColumns) FROM ''$CsvPg'' WITH (FORMAT csv, HEADER true, ENCODING ''UTF8'')"'
if($text -like "*$oldCopy*"){ $text = $text.Replace($oldCopy,$newCopy); L 'COPY_COLUMNS_PATCHED=true' } else { L 'COPY_COLUMNS_PATCHED=false' }
$text = $text.Replace('for($i=1; $i -le 30; $i++){','for($i=1; $i -le 120; $i++){')
$text = $text.Replace('within 30 seconds','within 120 seconds')
$text = $text.Replace('AAYS_056_DB_DRYRUN_NO_PGCTL_DONE=true','AAYS_068_DETACHED_WORKER_DONE=true')
Set-Content -Encoding UTF8 -Path $Patched -Value $text
$proc = Start-Process powershell.exe -ArgumentList @('-NoProfile','-ExecutionPolicy','Bypass','-File',$Patched) -RedirectStandardOutput $Stdout -RedirectStandardError $Stderr -PassThru -WindowStyle Hidden
$manifestObj = [ordered]@{ run_id=$RunId; task_id=$TaskId; pid=$proc.Id; started_at=(Get-Date -Format s); status='started'; patched=$Patched; stdout=$Stdout; stderr=$Stderr; report=$Report }
($manifestObj | ConvertTo-Json -Depth 4) | Set-Content -Encoding UTF8 -Path $Manifest
L ('CHILD_PID=' + $proc.Id)
L ('MANIFEST=' + $Manifest)
L 'AAYS_068_DETACHED_LAUNCHER_DONE=true'
L 'plan_progress_percent: 100'
Set-Content -Encoding UTF8 -Path $Report -Value $Lines
Write-Output 'AAYS_068_DETACHED_LAUNCHER_DONE=true'
Write-Output ('MANIFEST=' + $Manifest)
exit 0
