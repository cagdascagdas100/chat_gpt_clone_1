$Repo = $env:AAYS_REPO_ROOT
if (!$Repo) { $Repo = 'F:\chatgpt\chat_gpt_clone_1_main' }
$Base = Join-Path $Repo 'docs\chatgpt_status\aays1'
$Reports = Join-Path $Base 'reports'
$Status = Join-Path $Base 'status'
$Tasks = Join-Path $Base 'runner_tasks'
New-Item -ItemType Directory -Force $Reports,$Status,$Tasks | Out-Null
$stamp = Get-Date -Format 'yyyyMMdd_HHmmss'
$download = Join-Path $Base 'automation\104_download_first6_photos.ps1'
$render = Join-Path $Base 'automation\105_render_first6_polygons.ps1'
$export = Join-Path $Base 'automation\100_export_ai_boundary_outputs_to_repo.ps1'
$steps = @()
foreach ($s in @($download,$render,$export)) {
  $name = Split-Path $s -Leaf
  $state = 'missing'
  if (Test-Path $s) {
    try {
      powershell -NoProfile -ExecutionPolicy Bypass -File $s
      $state = 'ran'
    } catch { $state = 'error' }
  }
  $steps += [ordered]@{ script=$name; status=$state }
}
$out = [ordered]@{ page_key='aays1'; task_id='106_first6_assets_combo'; final_ready=$false; steps=$steps }
$out | ConvertTo-Json -Depth 5 | Set-Content -Encoding UTF8 (Join-Path $Tasks "first6_assets_combo_$stamp.json")
@"
# First6 Assets Combo

- task: 106_first6_assets_combo
- final_ready: false
- steps: download, render, export
"@ | Set-Content -Encoding UTF8 (Join-Path $Reports "106_first6_assets_combo_$stamp.md")
@"
PAGE_KEY=aays1
TASK_ID=106_first6_assets_combo
STATUS=done
FINAL_READY=false
"@ | Set-Content -Encoding UTF8 (Join-Path $Status "106_first6_assets_combo_status_$stamp.txt")
Write-Host "first6 assets combo complete"
