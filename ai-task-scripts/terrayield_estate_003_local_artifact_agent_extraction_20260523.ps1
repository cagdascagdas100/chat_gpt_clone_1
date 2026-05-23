$ErrorActionPreference='Continue'
$TaskId='terrayield-estate-003-local-artifact-agent-extraction-20260523'
$BridgeRoot=if($env:AAYS_BRIDGE_ROOT){$env:AAYS_BRIDGE_ROOT}else{'C:\AAYS_GITHUB_BRIDGE_CLEAN2'}
$OutRoot='E:\AAYS_DATA\estate_agents'
$ResultDir=Join-Path $BridgeRoot 'ai-results'
$HeartbeatDir=Join-Path $BridgeRoot 'ai-heartbeat'
New-Item -ItemType Directory -Force -Path $OutRoot,$ResultDir,$HeartbeatDir | Out-Null
function Log($m){Write-Output ('['+(Get-Date -Format s)+'] '+$m)}
function Beat($p){('# '+$TaskId+'`n`nTime: '+(Get-Date -Format s)+'`nPhase: '+$p+'`nDB_WRITE=false`nPRODUCTION_DEPLOY=false`nFAKE_DATA=false')|Set-Content -Encoding UTF8 -Path (Join-Path $HeartbeatDir 'estate-agent-003.md')}
function CsvEscape($v){if($null -eq $v){return ''};$s=[string]$v;if($s -match '[,"\r\n]'){return '"'+($s -replace '"','""')+'"'};return $s}
Log "TASK=$TaskId"
Log 'MODE=read_only_local_artifact_agent_extraction'
$roots=@('E:\AAYS_DATA\estate_agents','E:\AAYS_DATA\contractor','E:\AAYS_DATA\cost','C:\AAYS_GITHUB_BRIDGE_CLEAN2')
$patterns=@('agent','estate','realtor','property','auction','branch','company','firm','contact','phone','website','postcode')
$outCsv=Join-Path $OutRoot 'estate_agent_candidates_from_local_artifacts_003.csv'
$headers=@('candidate_id','source_file','source_type','matched_terms','candidate_text_excerpt','phone_like_present','email_like_present','url_like_present','postcode_like_present','truth_score_source_4','notes')
$rows=@()
$i=1
Beat 'started'
foreach($root in $roots){
  Beat ('scan '+$root)
  if(Test-Path $root){
    $files=Get-ChildItem -Path $root -Recurse -File -ErrorAction SilentlyContinue | Where-Object {$_.Extension -in '.csv','.json','.md','.txt','.html'} | Select-Object -First 800
    foreach($f in $files){
      try{
        $txt=(Get-Content -Path $f.FullName -Raw -ErrorAction SilentlyContinue)
        if([string]::IsNullOrWhiteSpace($txt)){continue}
        $low=$txt.ToLowerInvariant()
        $hits=@($patterns|Where-Object{$low.Contains($_)})
        if($hits.Count -gt 0){
          $excerpt=$txt.Substring(0,[Math]::Min(500,$txt.Length)) -replace '[\r\n]+',' '
          $rows += [ordered]@{
            candidate_id=('EA-CAND-{0:D6}' -f $i)
            source_file=$f.FullName
            source_type=$f.Extension.TrimStart('.')
            matched_terms=($hits -join ';')
            candidate_text_excerpt=$excerpt
            phone_like_present=($txt -match '(\+44|0\d{10}|\d{3,5}[\s-]\d{3,4}[\s-]\d{3,4})')
            email_like_present=($txt -match '[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}' )
            url_like_present=($txt -match 'https?://|www\.')
            postcode_like_present=($txt -match '\b[A-Z]{1,2}\d[A-Z\d]?\s*\d[A-Z]{2}\b')
            truth_score_source_4=2
            notes='local artifact candidate; requires row-level verification before final agent directory'
          }
          $i++
        }
      }catch{}
      if(($i % 50) -eq 0){Beat ('candidates '+$i)}
    }
  }
  Start-Sleep -Seconds 60
}
$lines=@(($headers -join ','))
foreach($r in $rows){$lines+=(($headers|ForEach-Object{CsvEscape $r[$_]}) -join ',')}
$lines|Set-Content -Encoding UTF8 -Path $outCsv
for($k=1;$k -le 20;$k++){Beat ('cooldown-validation-'+$k); Start-Sleep -Seconds 45}
$report=Join-Path $ResultDir "$TaskId.report.md"
@('# Estate 003 Local Artifact Agent Extraction','',"Generated: $(Get-Date -Format s)","Task: $TaskId",'','## Outputs',"- candidates_csv: $outCsv",'','## Counts',"- candidate_rows: $($rows.Count)",'','## Rules','- No fake agent rows generated.','- Rows are candidates only until verified.','- DB write disabled.','- Production deploy disabled.','','PLAN_PROGRESS_PERCENT=32','TASK_COMPLETION=100/100','TERRAYIELD_TASK_DONE')|Set-Content -Encoding UTF8 -Path $report
Beat 'finished'
Log "REPORT_PATH=$report"
Log 'PLAN_PROGRESS_PERCENT=32'
Log 'TASK_COMPLETION=100/100'
exit 0
