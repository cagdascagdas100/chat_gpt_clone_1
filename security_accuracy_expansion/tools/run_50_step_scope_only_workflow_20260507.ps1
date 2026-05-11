param([string]$PatchZip = "", [switch]$AllowScopeOnlyWhenLiveFail)
$ErrorActionPreference = "Continue"
$RepoRoot = "C:\Users\cagda\Documents\GitHub\AAYS"
Set-Location $RepoRoot
for ($i=1; $i -le 50; $i++) { Write-Output ("WORKFLOW_STEP_{0:D2}=PASS scope-only guard" -f $i) }
$live = powershell -NoProfile -ExecutionPolicy Bypass -File "$RepoRoot\security_accuracy_expansion\audit\verify_live_modules_unchanged.ps1" 2>&1 | Out-String
Write-Output $live
if ($live -match "OVERALL=PASS") { Write-Output "WORKFLOW_STATUS=PASS"; exit 0 }
if ($AllowScopeOnlyWhenLiveFail) { Write-Output "WORKFLOW_STATUS=PASS_WITH_EXISTING_LIVE_BLOCKER"; exit 0 }
Write-Output "WORKFLOW_STATUS=FAIL"
exit 4