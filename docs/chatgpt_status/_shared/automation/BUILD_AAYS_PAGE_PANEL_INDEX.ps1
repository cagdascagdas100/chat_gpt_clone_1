param(
  [string]$RepoRoot = 'F:\chatgpt\chat_gpt_clone_1_main'
)
$ErrorActionPreference = 'Stop'
function ReadJson($path){ if(Test-Path -LiteralPath $path){ try { return (Get-Content -LiteralPath $path -Raw | ConvertFrom-Json) } catch { return $null } }; return $null }
function Rel([string]$p){ (($p -replace '\\','/').TrimStart('/')) }
function FirstJson($dir,$pattern){ if(Test-Path -LiteralPath $dir){ $f=Get-ChildItem -LiteralPath $dir -File -Filter $pattern -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending | Select-Object -First 1; if($f){ return $f.FullName } }; return $null }
$root=[System.IO.Path]::GetFullPath($RepoRoot)
$registryPath=Join-Path $root 'docs\chatgpt_status\_shared\contracts\PAGE_KEY_REGISTRY.json'
$registry=ReadJson $registryPath
$items=@()
foreach($p in @($registry.pages)){
  $page=[string]$p.page_key
  $queuePath=Join-Path $root (([string]$p.current_queue) -replace '/','\')
  if(-not (Test-Path -LiteralPath $queuePath)){ $queuePath = FirstJson (Join-Path $root "docs\chatgpt_status\$page\queue") '*.json' }
  $queue=ReadJson $queuePath
  $heartbeatPath=FirstJson (Join-Path $root "docs\chatgpt_status\$page\heartbeat") '*heartbeat*'
  $completedPath=FirstJson (Join-Path $root "docs\chatgpt_status\$page\status") '*completed*.json'
  $statusPath=FirstJson (Join-Path $root "docs\chatgpt_status\$page\status") '*.json'
  $latest=$null
  if($p.PSObject.Properties['latest_changes']){ $latest=ReadJson (Join-Path $root (([string]$p.latest_changes) -replace '/','\')) }
  $items += [ordered]@{
    page_key=$page
    display_name=$p.display_name
    queue_status=$(if($queue){$queue.status}else{'missing'})
    queue_file=$(if($queuePath){Rel($queuePath.Substring($root.Length))}else{$null})
    heartbeat_file=$(if($heartbeatPath){Rel($heartbeatPath.Substring($root.Length))}else{$null})
    completed_file=$(if($completedPath){Rel($completedPath.Substring($root.Length))}else{$null})
    status_file=$(if($statusPath){Rel($statusPath.Substring($root.Length))}else{$null})
    latest_status=$(if($latest){$latest.status}else{$null})
    completion_percent=$(if($latest){$latest.overall_completion_percent}else{$null})
    remaining_percent=$(if($latest){$latest.remaining_percent}else{$null})
    final_ready=$(if($latest){$latest.final_ready}else{$false})
    fake_data=$(if($latest){$latest.fake_data}else{$false})
    expected_output=$p.current_expected_output
  }
}
$out=[ordered]@{ generated_at=(Get-Date).ToString('o'); source_registry='docs/chatgpt_status/_shared/contracts/PAGE_KEY_REGISTRY.json'; pages=$items }
$outPath=Join-Path $root 'docs\chatgpt_status\_shared\status\page_panel_index.json'
$dir=Split-Path -Parent $outPath; if(-not(Test-Path $dir)){New-Item -ItemType Directory -Force -Path $dir|Out-Null}
$out|ConvertTo-Json -Depth 30|Set-Content -LiteralPath $outPath -Encoding UTF8
