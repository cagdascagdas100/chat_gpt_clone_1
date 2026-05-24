$ErrorActionPreference='Stop'
$TaskId='repair-aays-real100-readonly-fix-20260524'
$Bridge='C:\AAYS_GITHUB_BRIDGE_CLEAN2'
$Repo='C:\Users\cagda\Documents\GitHub\AAYS'
$Project=Join-Path $Repo 'terrayield_land_intelligence'
$OutDir=Join-Path $Bridge 'ai-results'
$HbDir=Join-Path $Bridge 'ai-heartbeat'
New-Item -ItemType Directory -Force -Path $OutDir,$HbDir | Out-Null
$Result=Join-Path $OutDir 'repair_aays_real100_readonly_fix_20260524.result.json'
$Report=Join-Path $OutDir 'repair_aays_real100_readonly_fix_20260524.report.md'
$Hb=Join-Path $HbDir 'portable-runner.md'
function Hb($s,$m){ @('# AAYS Portable Task Runner Fixed','','Time: '+(Get-Date -Format s),'Status: '+$s,'TaskId: '+$TaskId,'Message: '+$m,'Mode: readonly-patch-repair','SafeScriptOnly: enabled','DB_WRITE=false','PRODUCTION_DEPLOY=false','FAKE_DATA=false') | Set-Content -Encoding UTF8 $Hb }
function Rep($m){ Add-Content -Encoding UTF8 -Path $Report -Value $m }
Set-Content -Encoding UTF8 -Path $Report -Value '# Repair AAYS Real100 Readonly Fix 20260524'
Rep 'db_write=false'
Rep 'production_deploy=false'
Rep 'fake_data=false'
Hb 'running' 'restore backups and apply safer patch'
$runtime=Join-Path $Project 'app\services\runtime_ops_service.py'
$estate=Join-Path $Project 'app\services\estate_agent_service.py'
$changed=@(); $warnings=@(); $errors=@()
try{
  if(-not (Test-Path $runtime)){ throw 'runtime_ops_service.py missing' }
  if(-not (Test-Path $estate)){ throw 'estate_agent_service.py missing' }
  $runtimeBackup=$runtime+'.bak.real100fix'
  $estateBackup=$estate+'.bak.real100fix'
  if(Test-Path $runtimeBackup){ Copy-Item $runtimeBackup $runtime -Force; $changed+='runtime_restored_from_backup' } else { $warnings+='runtime_backup_missing_using_current' }
  if(Test-Path $estateBackup){ Copy-Item $estateBackup $estate -Force; $changed+='estate_restored_from_backup' } else { $warnings+='estate_backup_missing_using_current' }
  Copy-Item $runtime ($runtime+'.bak.repair.real100fix') -Force
  Copy-Item $estate ($estate+'.bak.repair.real100fix') -Force

  $rt=Get-Content -Raw -Encoding UTF8 $runtime
  if($rt -notmatch 'def _v9_check_exists'){
    $helper=@'

def _v9_check_exists(payload: dict, name: str) -> bool:
    checks = payload.get("checks") if isinstance(payload, dict) else None
    if not isinstance(checks, list):
        return False
    for item in checks:
        if not isinstance(item, dict):
            continue
        if str(item.get("name") or "").strip() == name and _as_bool(item, "exists") is True:
            return True
    return False

'@
    $idx=$rt.IndexOf('def _pick_first_existing_file')
    if($idx -ge 0){ $rt=$rt.Insert($idx,$helper); $changed+='runtime_helper_inserted' } else { $warnings+='runtime_helper_marker_missing' }
  }
  if($rt -notmatch 'v9_project_final_evidence_ok'){
    $needle='    project_final_ok = bool(v9_final_readiness_ok or legacy_project_final_ok)'
    $insert=@'
    v9_project_final_evidence_ok = _v9_check_exists(v9_final_readiness, "project_finalize_result")
    v9_dem_evidence_ok = bool(
        _v9_check_exists(v9_final_readiness, "dem_51")
        and _v9_check_exists(v9_final_readiness, "dem_52")
    )
    v9_v8_review_evidence_ok = bool(
        _v9_check_exists(v9_final_readiness, "v8_review_sources")
        and _v9_check_exists(v9_final_readiness, "v8_review_result")
    )
    v9_contractor_preflight_evidence_ok = _v9_check_exists(v9_final_readiness, "contractor_preflight")
'@
    if($rt.Contains($needle)){ $rt=$rt.Replace($needle,$insert+$needle); $changed+='runtime_v9_flags_inserted' } else { $warnings+='runtime_project_final_line_missing' }
  }
  $rt=$rt.Replace('dem_ready_ok = bool(dem_resolution_ready_ok or legacy_dem_ready_ok)','dem_ready_ok = bool(dem_resolution_ready_ok or legacy_dem_ready_ok or (v9_final_readiness_ok and v9_dem_evidence_ok))')
  Set-Content -Encoding UTF8 -Path $runtime -Value $rt

  $es=Get-Content -Raw -Encoding UTF8 $estate
  if($es -notmatch 'def _build_review_reference'){
    $helper2=@'

def _first_existing_path(paths: list[Path]) -> Path | None:
    for path in paths:
        if path.exists():
            return path
    return None


def _build_review_reference(dataset: EstateDataset | None = None) -> dict[str, Any]:
    """Return read-only real-source review evidence even when the final dataset is missing."""
    bridge_results_root = Path(r"C:\AAYS_GITHUB_BRIDGE_CLEAN2\ai-results")
    estate_root = Path(r"E:\AAYS_DATA\estate_agents")
    roots: list[Path] = []
    if dataset is not None and dataset.root is not None:
        roots.append(dataset.root)
    roots.extend([bridge_results_root, estate_root])
    v8_review_sources_path = _first_existing_path([root / "v8_review_sources.csv" for root in roots])
    v8_review_result_path = _first_existing_path([root / "v8_review.result.json" for root in roots])
    real100_v7_result_path = _first_existing_path([root / "real100_v7_real_source_filter.result.json" for root in roots])
    real100_candidates_path = _first_existing_path([
        estate_root / "real100_v7_real_source_candidates.csv",
        bridge_results_root / "real100_v7_real_source_candidates.csv",
    ])
    v8_review_sources_rows = len(_read_csv(v8_review_sources_path)) if v8_review_sources_path else 0
    v8_review_result_payload = _read_json_dict(v8_review_result_path or Path())
    real100_v7_result_payload = _read_json_dict(real100_v7_result_path or Path())
    real100_candidates_rows = len(_read_csv(real100_candidates_path)) if real100_candidates_path else 0
    return {
        "v8_review_sources_exists": bool(v8_review_sources_path and v8_review_sources_path.exists()),
        "v8_review_sources_rows": v8_review_sources_rows,
        "v8_review_status": v8_review_result_payload.get("status"),
        "v8_review_source_rows": v8_review_result_payload.get("source_rows"),
        "v8_review_review_rows": v8_review_result_payload.get("review_rows"),
        "real100_v7_status": real100_v7_result_payload.get("status"),
        "real100_v7_candidates": real100_v7_result_payload.get("real_source_candidates"),
        "real100_v7_candidates_rows": real100_candidates_rows,
        "read_only_reference_only": True,
    }

'@
    $idx2=$es.IndexOf('def extract_audit_summary')
    if($idx2 -ge 0){ $es=$es.Insert($idx2,$helper2); $changed+='estate_helper_inserted' } else { $warnings+='estate_helper_marker_missing' }
  }
  $missingBlockPattern='(?s)"review_reference": \{\s*"v8_review_sources_exists": False,\s*"v8_review_sources_rows": 0,\s*"v8_review_status": None,\s*"v8_review_source_rows": None,\s*"v8_review_review_rows": None,\s*"real100_v7_status": None,\s*"real100_v7_candidates": None,\s*\},'
  if([regex]::IsMatch($es,$missingBlockPattern)){
    $es=[regex]::Replace($es,$missingBlockPattern,'"review_reference": _build_review_reference(None),',1)
    $changed+='estate_missing_dataset_reference_replaced'
  }
  Set-Content -Encoding UTF8 -Path $estate -Value $es

  Push-Location $Repo
  $py = python -m py_compile $runtime $estate 2>&1
  $compileOk = ($LASTEXITCODE -eq 0)
  $diff = git diff -- $runtime $estate | Out-String
  Pop-Location
  $diffPath=Join-Path $OutDir 'repair_aays_real100_readonly_fix_20260524.diff'
  Set-Content -Encoding UTF8 -Path $diffPath -Value $diff
  if(-not $compileOk){
    Copy-Item ($runtime+'.bak.repair.real100fix') $runtime -Force
    Copy-Item ($estate+'.bak.repair.real100fix') $estate -Force
    $errors += ('py_compile_failed_restored_repair_backup: '+($py | Out-String))
  }
}catch{
  $errors += $_.Exception.Message
  if(Test-Path ($runtime+'.bak.repair.real100fix')){ Copy-Item ($runtime+'.bak.repair.real100fix') $runtime -Force }
  if(Test-Path ($estate+'.bak.repair.real100fix')){ Copy-Item ($estate+'.bak.repair.real100fix') $estate -Force }
  $compileOk=$false
  $diffPath=$null
}
$status=if($errors.Count -eq 0 -and $compileOk){'finished_repair_patch_applied'}else{'failed_repair_patch_restored'}
@{task_id=$TaskId;status=$status;changed=$changed;warnings=$warnings;errors=$errors;compile_ok=$compileOk;diff_path=$diffPath;db_write=$false;production_deploy=$false;fake_data=$false;completed_at=(Get-Date -Format s)} | ConvertTo-Json -Depth 6 | Set-Content -Encoding UTF8 $Result
Rep ('status='+$status)
Rep ('changed='+($changed -join ','))
Rep ('warnings='+($warnings -join ','))
Rep ('errors='+($errors -join ','))
Rep ('compile_ok='+$compileOk)
Hb 'finished' ('status='+$status)
if($status -eq 'finished_repair_patch_applied'){exit 0}else{exit 2}
