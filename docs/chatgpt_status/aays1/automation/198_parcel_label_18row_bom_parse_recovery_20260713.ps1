$ErrorActionPreference = 'Stop'

$repoRoot = $env:AAYS_REPO_ROOT
if ([string]::IsNullOrWhiteSpace($repoRoot)) { $repoRoot = (Get-Location).Path }
$repoRoot = [System.IO.Path]::GetFullPath($repoRoot)
Set-Location -LiteralPath $repoRoot

$sourceRel = 'docs/chatgpt_status/aays1/automation/188_parcel_label_18row_source_classification_publish_20260713.ps1'
$sourcePath = Join-Path $repoRoot ($sourceRel.Replace('/', [System.IO.Path]::DirectorySeparatorChar))
if (-not (Test-Path -LiteralPath $sourcePath)) { throw ('source automation missing: ' + $sourceRel) }

$scriptText = Get-Content -LiteralPath $sourcePath -Raw -Encoding UTF8

$replacements = [ordered]@{
  "188_aays1_parcel_label_18row_source_classification_publish_20260713" = "198_aays1_parcel_label_18row_bom_parse_recovery_20260713"
  "188_parcel_label_18row_source_classification_publish_evidence_20260713.json" = "198_parcel_label_18row_bom_parse_recovery_evidence_20260713.json"
  "188_parcel_label_18row_source_classification_publish_report_20260713.md" = "198_parcel_label_18row_bom_parse_recovery_report_20260713.md"
  "188_source_classification_publish_20260713" = "198_bom_parse_recovery_20260713"
  "188_source_classification_publish" = "198_bom_parse_recovery"
  "task_188_combined_research_batches_185_186_187" = "task_198_bom_parse_recovery_of_task_188"
}
foreach ($key in $replacements.Keys) { $scriptText = $scriptText.Replace($key, $replacements[$key]) }

$scriptText = $scriptText.Replace("Set-Value `$row 'batch_id' '188'", "Set-Value `$row 'batch_id' '198'")
$scriptText = $scriptText.Replace("latest_batch_id='188'", "latest_batch_id='198'")
$scriptText = $scriptText.Replace("batches_seen=@('185','186','187','188')", "batches_seen=@('185','186','187','188','198')")

$oldParse = '$served = $dataResponse.Content | ConvertFrom-Json'
$newParse = @'
$servedText = [string]$dataResponse.Content
$servedText = $servedText.TrimStart([char]0xFEFF)
if ($servedText.Length -ge 3 -and [int]$servedText[0] -eq 239 -and [int]$servedText[1] -eq 187 -and [int]$servedText[2] -eq 191) {
  $servedText = $servedText.Substring(3)
}
$served = $servedText | ConvertFrom-Json
'@
if (-not $scriptText.Contains($oldParse)) { throw 'Task 188 HTTP JSON parse statement not found; recovery not executed.' }
$scriptText = $scriptText.Replace($oldParse, $newParse.TrimEnd())

$tempScript = Join-Path $env:TEMP ('aays_task198_' + [Guid]::NewGuid().ToString('N') + '.ps1')
try {
  [System.IO.File]::WriteAllText($tempScript, $scriptText, (New-Object System.Text.UTF8Encoding($false)))
  & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $tempScript
  if ($LASTEXITCODE -ne 0) { throw ('Task 198 patched execution exited ' + $LASTEXITCODE) }
} finally {
  Remove-Item -LiteralPath $tempScript -Force -ErrorAction SilentlyContinue
}
