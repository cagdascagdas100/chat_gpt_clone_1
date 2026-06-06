$ErrorActionPreference='Continue'
$Repo='C:\Users\cagda\Documents\GitHub\AAYS'
$Branch='feature/terrayield-aays-integration'
$Stamp=Get-Date -Format yyyyMMdd-HHmmss
$WorkCandidates=@('E:\chatgpt\AAYS_LOCAL_MAP_DATA','D:\chatgpt\AAYS_LOCAL_MAP_DATA','C:\Temp\AAYS_LOCAL_MAP_DATA')
$Work=$null
foreach($c in $WorkCandidates){ try{ New-Item -ItemType Directory -Force $c | Out-Null; $Work=$c; break }catch{} }
if(-not $Work){ throw 'No writable work directory found' }
$Log="$Work\LOCAL_MAP_DATA_RUN_$Stamp.txt"
$MapRoot="$Repo\england_map_web"
$ApiRoot="$Repo\terrayield_land_intelligence"
$ReportDir="$Repo\docs\chatgpt_status\local_map_data_run_$Stamp"
New-Item -ItemType Directory -Force $ReportDir | Out-Null
function Add-Line($s){ $s | Tee-Object -FilePath $Log -Append }
Add-Line "status=LOCAL_MAP_DATA_RUN_STARTED"
Add-Line "stamp=$Stamp"
Add-Line "work=$Work"
Add-Line "repo=$Repo"
Add-Line "db_write=false"
Add-Line "production_deploy=false"
Add-Line "migration_ddl=false"
Add-Line "fake_data=false"
Add-Line "map_root_exists=$(Test-Path $MapRoot)"
Add-Line "api_root_exists=$(Test-Path $ApiRoot)"
$files=@('england_map_web\index.html','england_map_web\app.js','england_map_web\data','england_map_web\tiles','terrayield_land_intelligence\app\main.py','terrayield_land_intelligence\docker-compose.yml','terrayield_land_intelligence\docker-compose.override.yml')
foreach($f in $files){ $p=Join-Path $Repo $f; Add-Line "exists:$f=$(Test-Path $p)" }
try{
  if(Test-Path "$MapRoot\run_local_map.ps1"){
    Add-Line "map_command=run_local_map.ps1"
    Start-Process powershell -ArgumentList @('-ExecutionPolicy','Bypass','-File',"$MapRoot\run_local_map.ps1") -WorkingDirectory $MapRoot -WindowStyle Minimized
    Add-Line "map_start_requested=true"
  } else {
    Add-Line "map_command=python_static_server_8099"
    Start-Process powershell -ArgumentList @('-NoExit','-Command',"cd '$MapRoot'; python -m http.server 8099") -WorkingDirectory $MapRoot -WindowStyle Minimized
    Add-Line "map_start_requested=true"
    Add-Line "map_url=http://localhost:8099/index.html"
  }
}catch{ Add-Line "map_start_error=$($_.Exception.Message)" }
try{
  $ports=@(8010,8000,8099)
  foreach($port in $ports){
    try{
      $u="http://localhost:$port"
      $r=Invoke-WebRequest -Uri $u -UseBasicParsing -TimeoutSec 5
      Add-Line "probe:$u=$($r.StatusCode)"
    }catch{ Add-Line "probe:http://localhost:$port=failed" }
  }
}catch{}
try{
  $dataFiles=Get-ChildItem $MapRoot -Recurse -File -ErrorAction SilentlyContinue | Where-Object { $_.Extension -match '\.(json|geojson|pmtiles|mbtiles|csv|parquet)$' } | Select-Object -First 200 FullName,Length,LastWriteTime
  $dataFiles | ConvertTo-Json -Depth 4 | Set-Content -Encoding UTF8 "$ReportDir\LOCAL_MAP_DATA_FILES.json"
  Add-Line "data_file_sample_count=$($dataFiles.Count)"
}catch{ Add-Line "data_inventory_error=$($_.Exception.Message)" }
Copy-Item $Log "$ReportDir\LOCAL_MAP_DATA_RUN_REPORT.txt" -Force
Add-Line "status=LOCAL_MAP_DATA_RUN_COMPLETE"
Add-Line "report_dir=$ReportDir"
Write-Host "STATUS=LOCAL_MAP_DATA_RUN_COMPLETE"
Write-Host "REPORT_DIR=$ReportDir"
Write-Host "Bekleme suresi: 2-5 dakika"
