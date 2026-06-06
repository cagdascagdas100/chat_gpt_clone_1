$ErrorActionPreference='Continue'
$Repo='C:\Users\cagda\Documents\GitHub\AAYS'
$Original="$Repo\docs\chatgpt_status\LOCATION_MATCH_COMMAND_READY_20260606.ps1"

$DriveRoot=$null
foreach($d in @('F:','E:','D:','C:')){
  if(Test-Path $d){ $DriveRoot=$d; break }
}
if(-not $DriveRoot){ throw 'No usable local drive found.' }

if($DriveRoot -eq 'C:'){
  $WorkRoot=Join-Path $env:TEMP 'AAYS_LOCATION_MATCH_WORK'
}else{
  $WorkRoot="$DriveRoot\chatgpt\AAYS_LOCATION_MATCH_WORK"
}
New-Item -ItemType Directory -Force $WorkRoot | Out-Null

if(!(Test-Path $Original)){
  throw "Original script not found: $Original"
}

$Patched=Join-Path $WorkRoot 'LOCATION_MATCH_COMMAND_PATCHED_NO_F.ps1'
$txt=Get-Content -Raw -Encoding UTF8 $Original
$txt=$txt.Replace('F:\chatgpt\AAYS_LOCATION_MATCH_WORK',$WorkRoot)
$txt=$txt.Replace("F:\chatgpt\AAYS_LOCATION_MATCH_WORK",$WorkRoot)
$txt | Set-Content -Encoding UTF8 $Patched

Write-Host "STATUS=LOCATION_MATCH_NO_F_WRAPPER_STARTED"
Write-Host "WORK_ROOT=$WorkRoot"
Write-Host "PATCHED_SCRIPT=$Patched"

powershell -ExecutionPolicy Bypass -File $Patched

Write-Host "STATUS=LOCATION_MATCH_NO_F_WRAPPER_DONE"
Write-Host "Bekleme suresi: 5-10 dakika"
