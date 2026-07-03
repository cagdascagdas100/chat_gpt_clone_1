$Repo=$env:AAYS_REPO_ROOT
if(!$Repo){$Repo='F:\chatgpt\chat_gpt_clone_1_runner_clean'}
$Root=$env:AAYS_AI_READY_ROOT
if(!$Root){$Root='F:\ai-ready-to-sell'}
$Base=Join-Path $Repo 'docs\chatgpt_status\aays1'
$Tasks=Join-Path $Base 'runner_tasks'
$Reports=Join-Path $Base 'reports'
$Status=Join-Path $Base 'status'
New-Item -ItemType Directory -Force $Tasks,$Reports,$Status | Out-Null
$stamp=Get-Date -Format 'yyyyMMdd_HHmmss'
$items=@()
for($i=1;$i -le 6;$i++){
  $p=Join-Path $Root ("photos\row_{0}_candidate.jpg" -f $i)
  $g=Join-Path $Root ("polygon_renders\row_{0}_existing_polygon.svg" -f $i)
  $items += [ordered]@{row=$i; photo=$p; polygon=$g; photo_exists=(Test-Path $p); polygon_exists=(Test-Path $g); ready=((Test-Path $p) -and (Test-Path $g)); review_status='pending'}
}
$ready=@($items|Where-Object{$_.ready}).Count
[ordered]@{page_key='aays1';task_id='111_build_first6_pair_index';final_ready=$false;ready_pairs=$ready;items=$items}|ConvertTo-Json -Depth 6|Set-Content -Encoding UTF8 (Join-Path $Tasks "first6_pair_index_$stamp.json")
"ready_pairs=$ready`nfinal_ready=false"|Set-Content -Encoding UTF8 (Join-Path $Reports "111_first6_pair_index_$stamp.md")
"PAGE_KEY=aays1`nTASK_ID=111_build_first6_pair_index`nSTATUS=index_written`nREADY_PAIRS=$ready`nFINAL_READY=false"|Set-Content -Encoding UTF8 (Join-Path $Status "111_first6_pair_index_status_$stamp.txt")
Write-Host "first6 pair index ready" $ready
