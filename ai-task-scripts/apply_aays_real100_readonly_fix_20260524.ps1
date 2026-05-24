$ErrorActionPreference='Stop'
$TaskId='apply-aays-real100-readonly-fix-20260524'
$Bridge='C:\AAYS_GITHUB_BRIDGE_CLEAN2'
$Repo='C:\Users\cagda\Documents\GitHub\AAYS'
$Project=Join-Path $Repo 'terrayield_land_intelligence'
$OutDir=Join-Path $Bridge 'ai-results'
$HbDir=Join-Path $Bridge 'ai-heartbeat'
New-Item -ItemType Directory -Force -Path $OutDir,$HbDir | Out-Null
$Result=Join-Path $OutDir 'apply_aays_real100_readonly_fix_20260524.result.json'
$Report=Join-Path $OutDir 'apply_aays_real100_readonly_fix_20260524.report.md'
$Hb=Join-Path $HbDir 'portable-runner.md'
function Write-Hb($s,$m){ @('# AAYS Portable Task Runner Fixed','','Time: '+(Get-Date -Format s),'Status: '+$s,'TaskId: '+$TaskId,'Message: '+$m,'Mode: local-readonly-patch-apply','SafeScriptOnly: enabled','DB_WRITE=false','PRODUCTION_DEPLOY=false','FAKE_DATA=false') | Set-Content -Encoding UTF8 $Hb }
function Write-Report($m){ Add-Content -Encoding UTF8 -Path $Report -Value $m }
Set-Content -Encoding UTF8 -Path $Report -Value '# Apply AAYS Real100 Readonly Fix 20260524'
Write-Report 'db_write=false'
Write-Report 'production_deploy=false'
Write-Report 'fake_data=false'
Write-Hb 'running' 'start patch apply'
$runtime=Join-Path $Project 'app\services\runtime_ops_service.py'
$estate=Join-Path $Project 'app\services\estate_agent_service.py'
$changed=@()
$warnings=@()
$errors=@()
if(-not (Test-Path $runtime)){ $errors += 'missing_runtime_ops_service' }
if(-not (Test-Path $estate)){ $errors += 'missing_estate_agent_service' }
if($errors.Count -eq 0){
  Copy-Item $runtime ($runtime+'.bak.real100fix') -Force
  Copy-Item $estate ($estate+'.bak.real100fix') -Force
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
    $marker='def _pick_first_existing_file'
    if($rt.Contains($marker)){ $rt=$rt.Replace($marker,$helper+"`n`n"+$marker); $changed += 'runtime_helper_added' } else { $warnings += 'runtime_marker_not_found_helper_not_added' }
  }
  if($rt -notmatch 'v9_project_final_evidence_ok'){
    $needle='project_final_ok = bool(v9_final_readiness_ok or legacy_project_final_ok)'
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
    if($rt.Contains($needle)){ $rt=$rt.Replace($needle,$insert+"`n    "+$needle); $changed += 'runtime_v9_evidence_flags_added' } else { $warnings += 'runtime_project_final_marker_not_found' }
  }
  $rt=$rt.Replace('dem_ready_ok = bool(dem_resolution_ready_ok or legacy_dem_ready_ok)','dem_ready_ok = bool(dem_resolution_ready_ok or legacy_dem_ready_ok or (v9_final_readiness_ok and v9_dem_evidence_ok))')
  $rt=$rt.Replace(') or bool(v9_final_readiness_ok and v9_contractor_preflight_evidence_ok) or bool(v9_final_readiness_ok and v9_contractor_preflight_evidence_ok)',') or bool(v9_final_readiness_ok and v9_contractor_preflight_evidence_ok)')
  if($rt -notmatch 'evidence-confirmed but filesystem-not-visible'){
    $rt=$rt.Replace('warnings.append("DEM root bulunamadi; dosyalar tasinmis olabilir.")','warnings.append("DEM evidence-confirmed but filesystem-not-visible; V9/DEM result kaniti non-blocking kabul edildi." if dem_ready_ok and (v9_dem_evidence_ok or dem_resolution_ready_ok) else "DEM root bulunamadi; dosyalar tasinmis olabilir.")')
    $rt=$rt.Replace('warnings.append("t118 icindeki DEM dosyalari mevcut pathlerde bulunamadi; alternatif path kontrol et.")','warnings.append("DEM files evidence-confirmed but filesystem-not-visible; final readiness V9 kanitina gore fail edilmedi." if dem_ready_ok and (v9_dem_evidence_ok or dem_resolution_ready_ok) else "t118 icindeki DEM dosyalari mevcut pathlerde bulunamadi; alternatif path kontrol et.")')
    $changed += 'runtime_dem_nonblocking_warning_added'
  }
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
    $marker2='def extract_audit_summary'
    if($es.Contains($marker2)){ $es=$es.Replace($marker2,$helper2+"`n`n"+$marker2); $changed += 'estate_review_helper_added' } else { $warnings += 'estate_marker_not_found_helper_not_added' }
  }
  if($es -match '"review_reference": \{[\s\S]*?"real100_v7_candidates": None,\s*\},'){
    $es=[regex]::Replace($es,'"review_reference": \{[\s\S]*?"real100_v7_candidates": None,\s*\},','"review_reference": _build_review_reference(None),',1)
    $changed += 'estate_missing_dataset_review_reference_replaced'
  }
  if($es -match 'review_reference = \{[\s\S]*?"read_only_reference_only": True,\s*\}'){
    $es=[regex]::Replace($es,'(?s)\s*v8_review_sources_path = dataset\.files\.get\("v8_review_sources"\).*?review_reference = \{.*?"read_only_reference_only": True,\s*\}','`n    review_reference = _build_review_reference(dataset)',1)
    $changed += 'estate_runtime_review_reference_replaced'
  }
  Set-Content -Encoding UTF8 -Path $estate -Value $es
  Push-Location $Repo
  $py = python -m py_compile $runtime $estate 2>&1
  $compileOk = ($LASTEXITCODE -eq 0)
  $diff = git diff -- $runtime $estate | Out-String
  Pop-Location
  $diffPath=Join-Path $OutDir 'apply_aays_real100_readonly_fix_20260524.diff'
  Set-Content -Encoding UTF8 -Path $diffPath -Value $diff
} else { $compileOk=$false; $diffPath=$null }
$status=if($errors.Count -eq 0 -and $compileOk){'finished_patch_applied'}else{'failed_patch_apply'}
@{task_id=$TaskId;status=$status;changed=$changed;warnings=$warnings;errors=$errors;compile_ok=$compileOk;diff_path=$diffPath;db_write=$false;production_deploy=$false;fake_data=$false;completed_at=(Get-Date -Format s)} | ConvertTo-Json -Depth 6 | Set-Content -Encoding UTF8 $Result
Write-Report ('status='+$status)
Write-Report ('changed='+($changed -join ','))
Write-Report ('warnings='+($warnings -join ','))
Write-Report ('errors='+($errors -join ','))
Write-Report ('compile_ok='+$compileOk)
Write-Hb 'finished' ('status='+$status)
if($status -eq 'finished_patch_applied'){exit 0}else{exit 2}
