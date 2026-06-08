$ErrorActionPreference='Continue'
$Remote='https://github.com/cagdascagdas100/chat_gpt_clone_1.git'
$FRoot='F:\chatgpt\AAYS_WORK'
$FRepo=Join-Path $FRoot 'repo'
$FLog=Join-Path $FRoot 'logs'
New-Item -ItemType Directory -Force $FRoot,$FLog | Out-Null
$stamp=Get-Date -Format yyyyMMdd_HHmmss
$log=Join-Path $FLog "aays_f_migrate_rescue_$stamp.txt"
function L($x){$x | Tee-Object -FilePath $log -Append}
L 'AAYS_F_MIGRATE_RESCUE_START'
L "F_ROOT=$FRoot"
L "F_REPO=$FRepo"
if(!(Test-Path (Join-Path $FRepo '.git'))){
  if(Test-Path $FRepo){Rename-Item $FRepo ($FRepo + '_old_' + $stamp) -ErrorAction SilentlyContinue}
  git clone $Remote $FRepo 2>&1 | Tee-Object -FilePath $log -Append
}
cd $FRepo
git fetch origin 2>&1 | Tee-Object -FilePath $log -Append
git checkout -B aays-mapdata-evidence-rescue-latest origin/main 2>&1 | Tee-Object -FilePath $log -Append
$dest=Join-Path $FRepo 'docs\chatgpt_status'
New-Item -ItemType Directory -Force $dest | Out-Null
$srcs=@('C:\Users\cagda\Documents\GitHub\AAYS','C:\AAYS_GITHUB_BRIDGE_CLEAN2')
foreach($s in $srcs){
  if(Test-Path $s){
    L "SCAN_SOURCE=$s"
    Get-ChildItem (Join-Path $s 'docs\chatgpt_status') -File -Filter 'AAYS_MAPDATA_LIVE_EVIDENCE_*.txt' -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending | Select-Object -First 10 | ForEach-Object {Copy-Item $_.FullName (Join-Path $dest $_.Name) -Force; L "COPIED=$($_.FullName)"}
    Get-ChildItem (Join-Path $s 'docs\chatgpt_status') -File -Filter 'AAYS_LIVE_*EVIDENCE_*.txt' -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending | Select-Object -First 10 | ForEach-Object {Copy-Item $_.FullName (Join-Path $dest $_.Name) -Force; L "COPIED=$($_.FullName)"}
  }
}
$marker=Join-Path $dest 'AAYS_F_WORK_ROOT_ACTIVE.txt'
@('AAYS_F_WORK_ROOT_ACTIVE',"F_ROOT=$FRoot",("CREATED_AT="+(Get-Date -Format s)),'PURPOSE=Use F drive for ChatGPT/AAYS local outputs and rescue branch push') | Set-Content -Encoding UTF8 $marker
git add docs/chatgpt_status 2>&1 | Tee-Object -FilePath $log -Append
if(git status --porcelain){
  git commit -m 'Add AAYS mapdata live evidence' 2>&1 | Tee-Object -FilePath $log -Append
} else { L 'NO_CHANGES_TO_COMMIT' }
git push origin aays-mapdata-evidence-rescue-latest --force-with-lease 2>&1 | Tee-Object -FilePath $log -Append
L 'AAYS_F_MIGRATE_RESCUE_END'
L "LOG=$log"
