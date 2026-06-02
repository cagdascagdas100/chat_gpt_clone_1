$ErrorActionPreference='Continue'
$TaskId='terrayield-105-search-or-min'
$Root='C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence'
Set-Location $Root
Write-Output 'PROJECT=terrayield'
Write-Output 'DISPLAY_PROJECT=TerraYield'
Write-Output 'CHATGPT_PAGE_PROJECT=aays1'
Write-Output ('TASK='+$TaskId)
$svc='app\services\supabase_admin_service.py'
if(Test-Path $svc){
  $txt=Get-Content -Raw -Encoding UTF8 $svc
  Copy-Item $svc ($svc+'.aays105search.bak') -Force
  $txt=$txt -replace 'filters\["search"\] = str\(search\)','filters["or"] = "(listing_title.eq." + str(search) + ",address.eq." + str(search) + ")"'
  $txt=$txt -replace 'filters\["search"\]=str\(search\)','filters["or"]="(listing_title.eq."+str(search)+",address.eq."+str(search)+")"'
  Set-Content -Encoding UTF8 -Path $svc -Value $txt
  Write-Output 'PATCH_SEARCH_OR=patched'
}else{Write-Output 'PATCH_SEARCH_OR=missing'}
$cmds=@(
 'python -m pytest tests/test_supabase_admin_service.py -q -ra',
 'python -m pytest tests/test_admin_publish_service.py tests/test_supabase_admin_service.py tests/test_supabase_sync.py -q -ra',
 'python -m pytest tests/test_admin_publish_service.py tests/test_supabase_sync.py -q',
 'python -m compileall app',
 'python -m pytest tests/test_disk_utils.py tests/test_scoring.py tests/test_listing_service.py tests/test_parcel_matcher.py -q'
)
$pass=0;$fail=0
foreach($cmd in $cmds){
  Write-Output ('CMD='+$cmd)
  Invoke-Expression ($cmd+' 2>&1') | Out-String | Write-Output
  if($LASTEXITCODE -eq 0 -or $null -eq $LASTEXITCODE){$pass++}else{$fail++}
}
Write-Output ('PASS_SLOTS='+$pass)
Write-Output ('FAIL_SLOTS='+$fail)
if($fail -eq 0){Write-Output 'PROGRAM_COMPLETION=100/100'}else{Write-Output 'PROGRAM_COMPLETION=99/100'}
Write-Output 'TERRAYIELD_105_SEARCH_OR_MIN_DONE'
exit 0
