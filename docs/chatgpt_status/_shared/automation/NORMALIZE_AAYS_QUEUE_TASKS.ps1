param(
  [string]$RepoRoot = 'F:\chatgpt\chat_gpt_clone_1_main',
  [string]$Branch = 'main'
)
$ErrorActionPreference = 'Stop'
function Rel([string]$p){ (($p -replace '\\','/').TrimStart('/')) }
function WriteJson($path,$obj){ $dir=Split-Path -Parent $path; if($dir -and -not(Test-Path $dir)){New-Item -ItemType Directory -Force -Path $dir|Out-Null}; $obj|ConvertTo-Json -Depth 30|Set-Content -LiteralPath $path -Encoding UTF8 }
$root = [System.IO.Path]::GetFullPath($RepoRoot)
$base = Join-Path $root 'docs\chatgpt_status'
$files = Get-ChildItem -LiteralPath $base -Recurse -File -Filter '*.json' | Where-Object { $_.FullName -match '\\queue\\' -and $_.FullName -notmatch '\\_shared\\' }
$changed=@(); $skipped=@()
foreach($f in $files){
  $rel = Rel($f.FullName.Substring($root.Length))
  if($rel -notmatch '^docs/chatgpt_status/([^/]+)/queue/') { $skipped += $rel; continue }
  $page = $Matches[1]
  try { $j = Get-Content -LiteralPath $f.FullName -Raw | ConvertFrom-Json } catch { $skipped += $rel; continue }
  $dirty=$false
  if(-not $j.PSObject.Properties['page_key']){ $j | Add-Member -NotePropertyName page_key -NotePropertyValue $page -Force; $dirty=$true }
  if(-not $j.PSObject.Properties['status']){ $j | Add-Member -NotePropertyName status -NotePropertyValue 'pending' -Force; $dirty=$true }
  if(-not $j.PSObject.Properties['target_branch']){ $j | Add-Member -NotePropertyName target_branch -NotePropertyValue $Branch -Force; $dirty=$true }
  if(-not $j.PSObject.Properties['script_path']){
    if($j.PSObject.Properties['automation_script']){ $j | Add-Member -NotePropertyName script_path -NotePropertyValue ([string]$j.automation_script) -Force; $dirty=$true }
  }
  if(-not $j.PSObject.Properties['allowed_paths']){
    $j | Add-Member -NotePropertyName allowed_paths -NotePropertyValue @("docs/chatgpt_status/$page","docs/chatgpt_status/_shared/status","docs/chatgpt_status/_shared/reports","docs/chatgpt_status/_shared/heartbeat") -Force
    $dirty=$true
  }
  foreach($k in @('no_fake_final_ready','no_db_write','no_migration','no_production_deploy')){
    if(-not $j.PSObject.Properties[$k]){ $j | Add-Member -NotePropertyName $k -NotePropertyValue $true -Force; $dirty=$true }
  }
  if($dirty){ WriteJson $f.FullName $j; $changed += $rel }
}
$out = [ordered]@{ generated_at=(Get-Date).ToString('o'); changed=$changed; skipped=$skipped; changed_count=$changed.Count; skipped_count=$skipped.Count }
WriteJson (Join-Path $root 'docs\chatgpt_status\_shared\status\queue_normalizer_latest.json') $out
