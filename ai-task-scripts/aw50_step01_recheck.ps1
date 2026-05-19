$root='C:\AAYS_GITHUB_BRIDGE_CLEAN2'
$src=Join-Path $root 'ai-results\aw50_step01_long_orchestrator.md'
$out=Join-Path $root 'ai-results\aw50_step01_recheck.md'
New-Item -ItemType Directory -Force -Path (Split-Path $out)|Out-Null
$text=''
if(Test-Path $src){$text=Get-Content $src -Raw}
$count=0
foreach($n in 1..8){if($text.Contains('pass_'+$n)){$count++}}
$final=$text.Contains('STEP_1_PASS')
@('# AW50 step1 recheck',('pass_count='+$count),('final_seen='+$final),'write_mode=read_only')|Set-Content -Path $out -Encoding UTF8
Write-Host 'AW50_STEP1_RECHECK_DONE'
