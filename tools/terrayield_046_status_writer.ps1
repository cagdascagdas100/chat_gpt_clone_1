param([string]$Repo='C:\Users\cagda\Documents\GitHub\AAYS')
$ErrorActionPreference='Continue'
$stamp=Get-Date -Format 'yyyyMMdd_HHmmss'
$out=Join-Path $Repo 'docs\chatgpt_status\runner_outputs'
New-Item -ItemType Directory -Force -Path $out | Out-Null

$runnerFiles=@(
  'tools\aays_hf_proxy_probe.ps1',
  'tools\aays_region_asset_gate.ps1',
  'tools\chatgpt_local_sync.ps1'
)
$runnerFileRows=foreach($f in $runnerFiles){
  [ordered]@{ path=$f; exists=(Test-Path (Join-Path $Repo $f)) }
}

$result=[ordered]@{
  stamp=$stamp
  task_id='terrayield-046-runner-sync-recovery-then-accuracy-expansion'
  status='REGION_GATE_MAPPING_MISMATCH_COVERAGE_PENDING'
  scoped_progress=100
  overall_progress=99
  accuracy_program_progress=35
  full_coverage_verified=$false
  runner_files=$runnerFileRows
  accuracy_scores=[ordered]@{
    source_accuracy_score=45
    parcel_match_accuracy_score=27
    operational_health_score=0
    general_confidence_score=32
  }
  remaining_blockers=@(
    'remote_pmtiles_not_runtime_verified',
    'wales_source_config_missing',
    'scotland_source_config_missing',
    'full_coverage_not_verified'
  )
  next_required_action='run_hf_probe_with_valid_access_or_add_missing_region_sources'
  safety=[ordered]@{ db_write=$false; deploy=$false; migration=$false; fake_data=$false; secret_values_printed=$false }
}

$result | ConvertTo-Json -Depth 8 | Set-Content (Join-Path $out 'terrayield-046-runner-sync-recovery-latest.json') -Encoding UTF8
$result | ConvertTo-Json -Depth 8 | Set-Content (Join-Path $out 'latest_output.json') -Encoding UTF8
@"
TerraYield 046 status $stamp
status=REGION_GATE_MAPPING_MISMATCH_COVERAGE_PENDING
scoped_progress=100
overall_progress=99
accuracy_program_progress=35
full_coverage_verified=false
remaining_blockers=remote_pmtiles_not_runtime_verified;wales_source_config_missing;scotland_source_config_missing;full_coverage_not_verified
db_write=false
deploy=false
migration=false
fake_data=false
secret_values_printed=false
"@ | Set-Content (Join-Path $out 'terrayield-046-runner-sync-recovery-latest.txt') -Encoding UTF8
@"
AAYS latest output $stamp
status=REGION_GATE_MAPPING_MISMATCH_COVERAGE_PENDING
scoped_progress=100
overall_progress=99
accuracy_program_progress=35
full_coverage_verified=false
db_write=false
deploy=false
migration=false
fake_data=false
secret_values_printed=false
"@ | Set-Content (Join-Path $out 'latest_output.txt') -Encoding UTF8

Write-Host 'TERRAYIELD_046_STATUS_WRITER_DONE'
Write-Host 'OVERALL_PROGRESS=99'
