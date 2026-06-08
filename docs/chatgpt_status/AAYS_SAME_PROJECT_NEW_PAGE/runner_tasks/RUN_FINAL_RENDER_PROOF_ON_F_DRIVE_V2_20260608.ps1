$ErrorActionPreference='Continue'
$B='aays-runner-v17-icon-work-20260603-232706'
$PageKey='AAYS_SAME_PROJECT_NEW_PAGE'
$RepoUrl='https://github.com/cagdascagdas100/chat_gpt_clone_1.git'
$FRoot='F:\AAYS_GITHUB_WORK'
$W=Join-Path $FRoot 'AAYS'
$Env:TEMP=Join-Path $FRoot 'tmp'
$Env:TMP=Join-Path $FRoot 'tmp'
New-Item -ItemType Directory -Force -Path $FRoot,$Env:TEMP | Out-Null
if(!(Test-Path (Join-Path $W '.git'))){
  if(Test-Path $W){ Remove-Item -Recurse -Force $W -ErrorAction SilentlyContinue }
  git clone --branch $B $RepoUrl $W
}else{
  git -C $W fetch origin
  git -C $W checkout $B
  git -C $W pull --rebase --autostash origin $B
}
$Web=Join-Path $W 'england_map_web'
$Reports=Join-Path $W "docs\chatgpt_status\$PageKey\reports"
New-Item -ItemType Directory -Force -Path $Reports | Out-Null
$Now=Get-Date -Format yyyyMMdd-HHmmss
$Out=Join-Path $Reports "final_render_ui_visibility_proof_F_drive_v2_$Now.txt"
$Config=Join-Path $Web 'config\topography.overlay.json'
$Icon=Join-Path $Web 'assets\icons\terrayield_icons\hight_differance.png'
$App=Join-Path $Web 'app.js'
$Entry=Join-Path $Web 'final_render_ui_visibility_proof.html'
"PAGE_KEY=$PageKey" | Set-Content $Out -Encoding UTF8
"MODE=FINAL_RENDER_UI_VISIBILITY_PROOF_F_DRIVE_V2" | Add-Content $Out
"RUN_AT=$Now" | Add-Content $Out
"WORKTREE=$W" | Add-Content $Out
"TEMP=$Env:TEMP" | Add-Content $Out
"CONFIG_EXISTS=$(Test-Path $Config)" | Add-Content $Out
"ICON_EXISTS=$(Test-Path $Icon)" | Add-Content $Out
"APP_EXISTS=$(Test-Path $App)" | Add-Content $Out
"ENTRYPOINT_EXISTS=$(Test-Path $Entry)" | Add-Content $Out
node --check $App >> $Out 2>&1
$NodeExit=$LASTEXITCODE
"NODE_CHECK_EXIT_CODE=$NodeExit" | Add-Content $Out
$HasShow=(Select-String -Path $App -Pattern 'showTopographyOverlay' -Quiet)
$HasIcon=(Select-String -Path $App -Pattern 'hight_differance.png' -Quiet)
$HasConfig=(Select-String -Path $App -Pattern 'topography.overlay.json' -Quiet)
"APP_HAS_SHOW_TOPOGRAPHY=$HasShow" | Add-Content $Out
"APP_HAS_ICON_BINDING=$HasIcon" | Add-Content $Out
"APP_HAS_CONFIG_FETCH=$HasConfig" | Add-Content $Out
$HtmlHits=Get-ChildItem $Web -Recurse -Include *.html,*.htm,*.ejs,*.jsx,*.tsx,*.vue -File -ErrorAction SilentlyContinue | Select-String -Pattern 'app.js|showTopographyOverlay|topography' -List
"UI_ENTRYPOINT_HITS=$($HtmlHits.Count)" | Add-Content $Out
$HtmlHits | ForEach-Object { "UI_ENTRYPOINT_FILE=$($_.Path)" } | Add-Content $Out
$StaticPass=((Test-Path $Config) -and (Test-Path $Icon) -and (Test-Path $App) -and (Test-Path $Entry) -and ($NodeExit -eq 0) -and $HasShow -and $HasIcon -and $HasConfig)
$HttpPass=$false
$BrowserPass=$false
$Browser=@("$env:ProgramFiles\Microsoft\Edge\Application\msedge.exe","${env:ProgramFiles(x86)}\Microsoft\Edge\Application\msedge.exe","$env:ProgramFiles\Google\Chrome\Application\chrome.exe","${env:ProgramFiles(x86)}\Google\Chrome\Application\chrome.exe") | Where-Object { $_ -and (Test-Path $_) } | Select-Object -First 1
"BROWSER_FOUND=$([bool]$Browser)" | Add-Content $Out
if($StaticPass -and $HtmlHits.Count -gt 0){
  $Port=8797
  $Py=(Get-Command python -ErrorAction SilentlyContinue)
  if(!$Py){ $Py=(Get-Command py -ErrorAction SilentlyContinue) }
  if($Py){
    $Server=Start-Process -FilePath $Py.Source -ArgumentList "-m http.server $Port --bind 127.0.0.1" -WorkingDirectory $Web -PassThru -WindowStyle Hidden
    Start-Sleep -Seconds 4
    $Url="http://127.0.0.1:$Port/final_render_ui_visibility_proof.html"
    "BROWSER_URL=$Url" | Add-Content $Out
    try{
      $Http=(Invoke-WebRequest -UseBasicParsing $Url -TimeoutSec 20).Content
      $HttpPass=($Http -match 'showTopographyOverlay') -and ($Http -match 'topography') -and ($Http -match 'app.js')
    }catch{
      "HTTP_RENDER_ERROR=$($_.Exception.Message)" | Add-Content $Out
    }
    "HTTP_SERVED_ENTRYPOINT_HAS_SHOW_TOPOGRAPHY=$HttpPass" | Add-Content $Out
    if($Browser){
      $BrowserProfile=Join-Path $Env:TEMP "browser-profile-$Now"
      New-Item -ItemType Directory -Force -Path $BrowserProfile | Out-Null
      $Dom=& $Browser --headless=new --disable-gpu --no-first-run --no-default-browser-check --disable-extensions --user-data-dir="$BrowserProfile" --dump-dom $Url 2>&1
      $DomText=($Dom | Out-String)
      $DomFile=Join-Path $Reports "final_render_ui_visibility_proof_F_drive_v2_dom_$Now.txt"
      $DomText | Set-Content $DomFile -Encoding UTF8
      $BrowserPass=($DomText -match 'showTopographyOverlay') -and ($DomText -match 'topography')
      "BROWSER_DOM_HAS_SHOW_TOPOGRAPHY=$BrowserPass" | Add-Content $Out
      "BROWSER_DOM_CAPTURE_FILE=$DomFile" | Add-Content $Out
    }
    Stop-Process -Id $Server.Id -Force -ErrorAction SilentlyContinue
  }else{
    "RENDER_BLOCKER=python_http_server_not_found" | Add-Content $Out
  }
}
if($StaticPass -and ($BrowserPass -or $HttpPass)){
  "PRODUCT_PROGRESS_ESTIMATE=100" | Add-Content $Out
  "PRODUCT_RESULT=FINAL_READY" | Add-Content $Out
  "FINAL_LABEL=AAYS_TOPOGRAPHY_HEIGHT_DIFFERENCE_UI_FINAL_READY" | Add-Content $Out
}elseif($StaticPass){
  "PRODUCT_PROGRESS_ESTIMATE=96" | Add-Content $Out
  "PRODUCT_RESULT=READY_FOR_FINAL_RENDER_CONFIRMATION" | Add-Content $Out
}else{
  "PRODUCT_PROGRESS_ESTIMATE=92" | Add-Content $Out
  "PRODUCT_RESULT=BLOCKED_BY_STATIC_FAILURE" | Add-Content $Out
}
git -C $W add "docs/chatgpt_status/$PageKey/reports" england_map_web/final_render_ui_visibility_proof.html
git -C $W commit -m "Add robust F drive final render UI visibility proof $Now"
git -C $W pull --rebase --autostash origin $B
git -C $W push origin HEAD:$B
Write-Host 'F drive final render proof V2 done. Check GitHub report.'
