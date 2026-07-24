$ErrorActionPreference = 'Stop'

$repoRoot = $env:AAYS_REPO_ROOT
if ([string]::IsNullOrWhiteSpace($repoRoot)) { $repoRoot = (Get-Location).Path }
$repoRoot = [System.IO.Path]::GetFullPath($repoRoot)
Set-Location -LiteralPath $repoRoot

$templateRel = 'docs/chatgpt_status/aays1/automation/202_parcel_label_36row_source_classification_publish_20260713.ps1'
$templatePath = Join-Path $repoRoot ($templateRel.Replace('/', [System.IO.Path]::DirectorySeparatorChar))
if (-not (Test-Path -LiteralPath $templatePath -PathType Leaf)) { throw ('template automation missing: ' + $templateRel) }

$source = Get-Content -LiteralPath $templatePath -Raw -Encoding UTF8
$source = $source.Replace('202_aays1_parcel_label_36row_source_classification_publish_20260713','205_aays1_parcel_label_53row_source_classification_publish_20260714')
$source = $source.Replace('202_parcel_label_36row_source_classification_publish','205_parcel_label_53row_source_classification_publish')
$source = $source.Replace('$expectedCount = 36','$expectedCount = 53')
$source = $source.Replace('task_202_combined_research_batches_189_190_191_192_193_194','task_205_combined_research_batches_195_196_197_199_200_201_203_204_deduped')
$source = $source.Replace('202_source_classification_publish_20260713','205_source_classification_publish_20260714')
$source = $source.Replace('202_source_classification_publish','205_source_classification_publish')
$source = $source.Replace("Set-Value `$row 'batch_id' '202'","Set-Value `$row 'batch_id' '205'")
$source = $source.Replace("latest_batch_id='202'","latest_batch_id='205'")
$source = $source.Replace("batches_seen=@('189','190','191','192','193','194','202')","batches_seen=@('195','196','197','199','200','201','203','204','205')")
$source = $source.Replace("Set-Value `$row 'source_date' '2026-07-13'","Set-Value `$row 'source_date' '2026-07-14'")
$source = $source.Replace('Task 202','Task 205')
$source = $source.Replace('36-row','53-row')
$source = $source.Replace('36ROW','53ROW')
$source = $source.Replace('thirty-six','fifty-three')
$source = $source.Replace('aays202_served_','aays205_served_')

$inputStart = $source.IndexOf('$inputRels = @(', [System.StringComparison]::Ordinal)
$queueStart = $source.IndexOf('$queueRel =', $inputStart, [System.StringComparison]::Ordinal)
if ($inputStart -lt 0 -or $queueStart -lt 0) { throw 'cannot locate template input array' }
$inputBlock = @'
$inputRels = @(
  'docs/chatgpt_status/aays1/inputs/195_distance_property_types_source_classification_research_hold_20260713.json',
  'docs/chatgpt_status/aays1/inputs/196_distance_property_types_source_classification_research_hold_20260713.json',
  'docs/chatgpt_status/aays1/inputs/197_distance_property_types_source_classification_research_hold_20260713.json',
  'docs/chatgpt_status/aays1/inputs/199_distance_property_types_source_classification_research_hold_20260713.json',
  'docs/chatgpt_status/aays1/inputs/200_distance_property_types_source_classification_research_hold_20260713.json',
  'docs/chatgpt_status/aays1/inputs/201_distance_property_types_source_classification_research_hold_20260713.json',
  'docs/chatgpt_status/aays1/inputs/203_distance_property_types_source_classification_research_hold_20260713.json',
  'docs/chatgpt_status/aays1/inputs/204_distance_property_types_source_classification_research_hold_20260713.json'
)
'@
$source = $source.Substring(0, $inputStart) + $inputBlock + "`r`n" + $source.Substring($queueStart)

$oldStart = '  $features = @()'
$oldEnd = '  if ($uniqueFeatureIds.Count -ne $expectedCount) { throw (''expected '' + $expectedCount + '' unique parcel ids, found '' + $uniqueFeatureIds.Count) }'
$featureStart = $source.IndexOf($oldStart, [System.StringComparison]::Ordinal)
$featureEnd = $source.IndexOf($oldEnd, $featureStart, [System.StringComparison]::Ordinal)
if ($featureStart -lt 0 -or $featureEnd -lt 0) { throw 'cannot locate template feature collection block' }
$featureEnd += $oldEnd.Length
$newFeatureBlock = @'
  $featureMap = @{}
  $rawFeatureCount = 0
  foreach ($inputRel in $inputRels) {
    $inputPath = Repo-Path $inputRel
    if (-not (Test-Path -LiteralPath $inputPath)) { throw ('input missing: ' + $inputRel) }
    $inputData = Parse-JsonText (Get-Content -LiteralPath $inputPath -Raw -Encoding UTF8)
    foreach ($feature in @($inputData.features)) {
      $rawFeatureCount++
      $parcelId = [string]$feature.parcel_id
      if ([string]::IsNullOrWhiteSpace($parcelId)) { throw ('blank parcel id in ' + $inputRel) }
      if (-not $featureMap.ContainsKey($parcelId) -or [double]$feature.accuracy_score_4 -gt [double]$featureMap[$parcelId].accuracy_score_4) {
        $featureMap[$parcelId] = $feature
      }
    }
  }
  if ($rawFeatureCount -ne 54) { throw ('expected 54 raw research features, found ' + $rawFeatureCount) }
  $features = @($featureMap.Values | Sort-Object -Property parcel_id)
  if (@($features).Count -ne $expectedCount) { throw ('expected ' + $expectedCount + ' deduplicated research features, found ' + @($features).Count) }
  $featureIds = @($features | ForEach-Object { [string]$_.parcel_id })
  $uniqueFeatureIds = @($featureIds | Sort-Object -Unique)
  if ($uniqueFeatureIds.Count -ne $expectedCount) { throw ('expected ' + $expectedCount + ' unique parcel ids, found ' + $uniqueFeatureIds.Count) }
'@
$source = $source.Substring(0, $featureStart) + $newFeatureBlock + $source.Substring($featureEnd)

$tempScript = Join-Path $env:TEMP ('aays205_publish_' + [Guid]::NewGuid().ToString('N') + '.ps1')
try {
  [System.IO.File]::WriteAllText($tempScript, $source, (New-Object System.Text.UTF8Encoding($false)))
  & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $tempScript
  $exitCode = $LASTEXITCODE
} finally {
  Remove-Item -LiteralPath $tempScript -Force -ErrorAction SilentlyContinue
}
exit $exitCode
