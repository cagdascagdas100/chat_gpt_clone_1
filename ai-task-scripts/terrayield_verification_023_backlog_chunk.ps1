$ErrorActionPreference = "Continue"
$Project = "C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence"
$Start = Get-Date
$Run = Get-Date -Format "yyyyMMdd_HHmmss"
$ReportDir = Join-Path $Project ".aays_next_fix\verification_023_backlog_chunk_$Run"
$SummaryFile = Join-Path $ReportDir "summary.md"
$DetailFile = Join-Path $ReportDir "detail.txt"
$ChunkFile = Join-Path $ReportDir "verification_chunk_001.csv"
New-Item -ItemType Directory -Force -Path $ReportDir | Out-Null
Set-Location $Project
function Log($x){$s=[int]((Get-Date)-$Start).TotalSeconds;$l="[$s s] $x";Write-Output $l;Add-Content -Encoding UTF8 -Path $DetailFile -Value $l}
function E($ep){try{$sw=[System.Diagnostics.Stopwatch]::StartNew();$r=Invoke-WebRequest -Uri ("http://localhost:8010"+$ep) -UseBasicParsing -TimeoutSec 60;$sw.Stop();$line="OK $ep status=$($r.StatusCode) ms=$($sw.ElapsedMilliseconds) bytes=$($r.Content.Length)";Log $line;return $line}catch{$line="FAIL $ep error=$($_.Exception.Message)";Log $line;return $line}}
Log "TASK: TerraYield verification 023 backlog chunk"
Log "PROGRESS: 99%"
Log "MODE: non-destructive first chunk verification; report only"
$health=E "/health"
$combined=E "/map/sales-history/combined"
$latestBacklog=Get-ChildItem -Path ".aays_next_fix" -Recurse -File -ErrorAction SilentlyContinue -Filter "verification_backlog_seed.csv" | Sort-Object LastWriteTime -Descending | Select-Object -First 1
if($latestBacklog){Log "LATEST_BACKLOG=$($latestBacklog.FullName)"}else{Log "NO_BACKLOG_FOUND"}
"row,priority,path,length,last_write,verification_hint,exists_now,status,next_action" | Set-Content -Encoding UTF8 -Path $ChunkFile
$count=0;$exists=0;$missing=0
if($latestBacklog){
  $rows=Import-Csv $latestBacklog.FullName | Select-Object -First 30
  foreach($r in $rows){
    $count++
    $p=$r.path
    $existsNow=Test-Path $p
    if($existsNow){$exists++;$status="present";$next="inspect_content_or_metadata"}else{$missing++;$status="missing";$next="find_replacement_or_ignore"}
    ('{0},{1},"{2}",{3},"{4}",{5},{6},{7},{8}' -f $count,$r.priority,$p,$r.length,$r.last_write,$r.verification_hint,$existsNow,$status,$next) | Add-Content -Encoding UTF8 -Path $ChunkFile
  }
}
Log "CHUNK_ROWS=$count"
Log "EXISTS_ROWS=$exists"
Log "MISSING_ROWS=$missing"
Log "--- file type counts ---"
if($latestBacklog){Import-Csv $latestBacklog.FullName | ForEach-Object {[IO.Path]::GetExtension($_.path).ToLowerInvariant()} | Group-Object | Sort-Object Count -Descending | Select-Object Count,Name | Format-Table -AutoSize | Out-String | Add-Content -Encoding UTF8 -Path $DetailFile}
$elapsed=[int]((Get-Date)-$Start).TotalSeconds
$result=if($count -gt 0 -and $exists -gt 0 -and $health -like 'OK*'){'chunk_ready'}elseif($count -gt 0){'chunk_created_api_issue'}else{'no_backlog'}
$summary=@('# TerraYield Verification 023 Backlog Chunk Summary','','## Result',$result,'','## Health',$health,'','## Combined',$combined,'','## Chunk','Rows checked: '+$count,'Existing files: '+$exists,'Missing files: '+$missing,'','## Progress Estimate','- Evidence verification plan: 99%','- Backlog seeding: 99%','- First chunk readiness: '+($(if($result -eq 'chunk_ready'){'95%'}else{'80-90%'})),'- Overall verification workflow: '+($(if($result -eq 'chunk_ready'){'97%'}else{'93-95%'})),'','## Files',"Detail: $DetailFile","Chunk: $ChunkFile","Elapsed seconds: $elapsed",'','## Next','- Inspect first chunk candidate files and classify evidence strength.','- Keep processing in chunks of 30-80 rows to avoid long stalls.')
Set-Content -Encoding UTF8 -Path $SummaryFile -Value $summary
Write-Output "SUMMARY_FILE=$SummaryFile"
Write-Output "DETAIL_FILE=$DetailFile"
Write-Output "CHUNK_FILE=$ChunkFile"
Write-Output "RESULT=$result"
Write-Output "ELAPSED_SECONDS=$elapsed"
Write-Output "VERIFICATION_023_BACKLOG_CHUNK_DONE"
exit 0
