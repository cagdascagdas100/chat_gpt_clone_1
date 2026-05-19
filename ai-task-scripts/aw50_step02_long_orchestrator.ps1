$ErrorActionPreference = "Stop"
$bridge = "C:\AAYS_GITHUB_BRIDGE_CLEAN2"
$pkg = "C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\docs\chatgpt_handoff\accuracy_warehouse_50step"
$res = Join-Path $bridge "ai-results\aw50_step02_long_orchestrator.md"
New-Item -ItemType Directory -Force -Path (Split-Path $res) | Out-Null
function L($s){ Add-Content -LiteralPath $res -Encoding UTF8 -Value $s }
Set-Content -LiteralPath $res -Encoding UTF8 -Value "# AW50 Step 2 Long Orchestrator"
L "start_utc=$((Get-Date).ToUniversalTime().ToString('o'))"
L "scope=step2_template_contract_validation_no_db_write"
L "package_root=$pkg"
if(!(Test-Path $pkg -PathType Container)){ L "STEP_2_FAIL"; L "verdict=fail"; L "reason=PACKAGE_ROOT_MISSING"; exit 20 }
$targets = @(
 "AW50_06_SOURCE_REGISTRY_TEMPLATE.csv",
 "AW50_07_CLAIM_CATALOG_TEMPLATE.csv",
 "AW50_08_EVIDENCE_MANIFEST_TEMPLATE.jsonl",
 "AW50_09_CONTRADICTION_LOG_TEMPLATE.csv",
 "AW50_10_CONFIDENCE_MODEL_TEMPLATE.json",
 "AW50_12_DB_SCHEMA_APPLY.sql",
 "AW50_13_DB_LOAD_ORDER.csv",
 "AW50_16_SOURCE_PROVENANCE_POLICY_TR.md",
 "AW50_17_FINAL_CONFIDENCE_REPORT_TEMPLATE.md"
)
$requiredTokens = @("source","claim","evidence","sha256","confidence","verdict")
$fail = 0
$warn = 0
for($pass=1; $pass -le 8; $pass++){
 L ""
 L "## pass_$pass"
 L "pass_utc=$((Get-Date).ToUniversalTime().ToString('o'))"
 foreach($f in $targets){
   $p = Join-Path $pkg $f
   if(!(Test-Path $p -PathType Leaf)){ L "file=$f | verdict=missing"; $fail++; continue }
   $raw = Get-Content -LiteralPath $p -Raw -Encoding UTF8
   $hash = (Get-FileHash -LiteralPath $p -Algorithm SHA256).Hash.ToLower()
   $lines = ($raw -split "`n").Count
   $tokenHits = 0
   foreach($t in $requiredTokens){ if($raw -match [regex]::Escape($t)){ $tokenHits++ } }
   $parse = "na"
   if($f.EndsWith(".json")){ try{ $null = $raw | ConvertFrom-Json; $parse = "pass" } catch { $parse = "fail"; $fail++ } }
   if($f.EndsWith(".jsonl")){ $bad=0; foreach($ln in ($raw -split "`n")){ if($ln.Trim().Length -gt 0){ try{ $null = $ln | ConvertFrom-Json } catch { $bad++ } } }; $parse = "jsonl_bad_$bad"; if($bad -gt 0){$fail++} }
   if($f.EndsWith(".csv")){ $header = ($raw -split "`n")[0]; if($header -notmatch ","){ $warn++ } }
   L "file=$f | lines=$lines | token_hits=$tokenHits | parse=$parse | sha256=$hash | verdict=present"
 }
 L "pass_warn_total=$warn"
 L "pass_fail_total=$fail"
 if($pass -lt 8){ Start-Sleep -Seconds 240 }
}
L ""
if($fail -eq 0){
 L "STEP_2_PASS"
 L "verdict=pass"
 L "result=TEMPLATE_CONTRACTS_REPEATEDLY_VALIDATED"
 L "aw50_progress=2/50"
 L "aw50_progress_percent=4"
} else {
 L "STEP_2_FAIL"
 L "verdict=fail"
 L "fail_count=$fail"
 L "warn_count=$warn"
}
L "end_utc=$((Get-Date).ToUniversalTime().ToString('o'))"
exit $(if($fail -eq 0){0}else{21})
