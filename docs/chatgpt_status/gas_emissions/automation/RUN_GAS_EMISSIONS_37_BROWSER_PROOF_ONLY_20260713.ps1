[CmdletBinding()]
param()

$ErrorActionPreference='Stop'
$repoRoot=[IO.Path]::GetFullPath([string]$env:AAYS_REPO_ROOT)
if(-not$repoRoot-or[string]$env:AAYS_PAGE_KEY-ne'gas_emissions'){throw'GAS_BROWSER_PROOF_MUST_RUN_IN_SHARED_RUNNER'}
$taskId=if($env:AAYS_TASK_ID){[string]$env:AAYS_TASK_ID}else{'gas_emissions_37_browser_proof_only_20260713'}
function Ensure-Dir([string]$Path){if(-not(Test-Path -LiteralPath $Path)){New-Item -ItemType Directory -Force -Path $Path|Out-Null}}
function Write-Json([string]$Path,[object]$Value){Ensure-Dir(Split-Path -Parent $Path);$tmp=$Path+'.tmp.'+$PID;[IO.File]::WriteAllText($tmp,(($Value|ConvertTo-Json -Depth 80)+[Environment]::NewLine),[Text.UTF8Encoding]::new($false));Move-Item -LiteralPath $tmp -Destination $Path -Force}
function Read-Json([string]$Path){if(Test-Path -LiteralPath $Path){Get-Content -LiteralPath $Path -Raw -Encoding UTF8|ConvertFrom-Json}}

$servedUrl='http://127.0.0.1:8012/england_map_web/data/program_layer_matrix/gas_emissions_visible_rows_latest.json?proof='+[DateTimeOffset]::UtcNow.ToUnixTimeSeconds()
$served=Invoke-RestMethod -Uri $servedUrl -TimeoutSec 30 -Headers @{'Cache-Control'='no-cache'}
$httpCount=@($served.rows).Count
if($httpCount-lt37){throw"GAS_BROWSER_PROOF_HTTP_ROWS_BELOW_37:$httpCount"}

$tmpBase=Join-Path([IO.Path]::GetTempPath())($taskId+'_'+[Guid]::NewGuid().ToString('N'))
$tmpPy=$tmpBase+'.py';$tmpOut=$tmpBase+'.json'
$pySource=@'
import json, sys, time
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait

out_path=Path(sys.argv[1]); expected_min=int(sys.argv[2])
url="http://127.0.0.1:8012/england_map_web/TerraYield_England_Program_Parcel_Layer_Matrix_20260629.html?gas_proof="+str(int(time.time()))
expected={
"GHG-HPL-2005-commercial-electricity-co2","GHG-HPL-2005-commercial-electricity-ch4","GHG-HPL-2005-commercial-electricity-n2o",
"GHG-HPL-2005-commercial-gas-co2","GHG-HPL-2005-commercial-gas-ch4","GHG-HPL-2005-commercial-gas-n2o",
"GHG-HPL-2005-commercial-other-co2","GHG-HPL-2005-commercial-other-ch4","GHG-HPL-2005-commercial-other-n2o"}
result={"status":"FAIL","phase":"start","url":url,"unique_row_count":0,"rendered_row_count":0,"new_marker_count":0,"manual_marker_count":0,"console_errors":[],"error":None}
driver=None
try:
    options=webdriver.ChromeOptions()
    for arg in ("--headless=new","--disable-gpu","--no-sandbox","--disable-dev-shm-usage","--window-size=1920,1400"):
        options.add_argument(arg)
    options.set_capability("goog:loggingPrefs",{"browser":"ALL"})
    result["phase"]="driver_start";driver=webdriver.Chrome(options=options);driver.set_script_timeout(90);driver.get(url)
    result["phase"]="dom";wait=WebDriverWait(driver,90);wait.until(lambda d:d.find_element(By.ID,"layerSelect"))
    stable=False
    for attempt in range(3):
        result["phase"]="load_gas_"+str(attempt+1)
        loaded=driver.execute_async_script("const done=arguments[arguments.length-1];const selector=document.getElementById('layerSelect');selector.value='gas';Promise.resolve(loadLayer('gas')).then(()=>done('ok')).catch(error=>done('error:'+String(error)))")
        if loaded!="ok": raise RuntimeError("gas_load_failed:"+str(loaded))
        wait.until(lambda d:d.execute_script("return state.layer==='gas'&&state.data&&Array.isArray(state.data.rows)&&state.data.rows.length>=arguments[0]&&state.data.rows[0].row_id!==undefined",expected_min))
        time.sleep(3)
        stable=bool(driver.execute_script("return state.layer==='gas'&&state.data&&Array.isArray(state.data.rows)&&state.data.rows.length>=arguments[0]&&state.data.rows[0].row_id!==undefined",expected_min))
        if stable: break
    if not stable: raise RuntimeError("gas_layer_was_overwritten_by_initial_load")
    result["phase"]="state_stable"
    rows={};rendered=0
    while True:
        page_rows=driver.find_elements(By.CSS_SELECTOR,"#table tbody tr");rendered+=len(page_rows)
        for tr in page_rows:
            td=tr.find_elements(By.TAG_NAME,"td")
            if len(td)>1 and td[1].text.strip():rows[td[1].text.strip()]=td[0].text.strip()
        more=driver.execute_script("return state.page+1<Math.ceil(state.filtered.length/state.pageSize)")
        if not more:break
        before=driver.execute_script("return state.page");driver.find_element(By.ID,"next").click();wait.until(lambda d:d.execute_script("return state.page")>before)
    severe=[]
    try:severe=[entry for entry in driver.get_log("browser") if str(entry.get("level","")).upper()=="SEVERE"]
    except Exception:severe=[]
    present=expected.issubset(rows.keys());new_count=sum(1 for rid in expected if "LATEST" in rows.get(rid,""));manual_count=sum(1 for rid in expected if "MANUEL" in rows.get(rid,""))
    passed=len(rows)>=expected_min and rendered>=expected_min and present and new_count==9 and manual_count==9 and not severe
    result.update({"status":"PASS" if passed else "FAIL","phase":"complete","unique_row_count":len(rows),"rendered_row_count":rendered,"expected_rows_present":present,"new_marker_count":new_count,"manual_marker_count":manual_count,"page_info":driver.find_element(By.ID,"pageInfo").text,"console_errors":severe})
    if not passed:result["error"]="rows_expected_ids_markers_or_console_failed"
except Exception as exc:
    result["error"]=f"{type(exc).__name__}: {exc}"
finally:
    if driver:
        try:driver.quit()
        except Exception:pass
    out_path.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding="utf-8")
sys.exit(0 if result["status"]=="PASS" else 1)
'@
[IO.File]::WriteAllText($tmpPy,$pySource,[Text.UTF8Encoding]::new($false))
try{
  $python=Get-Command python -ErrorAction SilentlyContinue
  if($python){&$python.Source $tmpPy $tmpOut $httpCount}else{&(Get-Command py -ErrorAction Stop).Source -3 $tmpPy $tmpOut $httpCount}
  $browserExit=$LASTEXITCODE;$browser=Read-Json $tmpOut
}finally{Remove-Item -LiteralPath $tmpPy -Force -ErrorAction SilentlyContinue}
$passed=($browserExit-eq0-and[string]$browser.status-eq'PASS'-and[int]$browser.unique_row_count-ge37-and[int]$browser.new_marker_count-eq9-and[int]$browser.manual_marker_count-eq9-and@($browser.console_errors).Count-eq0)
$payload=[ordered]@{task_id=$taskId;page_key='gas_emissions';status=if($passed){'PASS'}else{'FAIL'};generated_at=(Get-Date).ToUniversalTime().ToString('o');served_http_row_count=$httpCount;browser_status=[string]$browser.status;browser_phase=[string]$browser.phase;browser_error=[string]$browser.error;browser_unique_row_count=[int]$browser.unique_row_count;browser_rendered_row_count=[int]$browser.rendered_row_count;expected_rows_present=[bool]$browser.expected_rows_present;browser_new_marker_count=[int]$browser.new_marker_count;browser_manual_marker_count=[int]$browser.manual_marker_count;browser_console_errors=@($browser.console_errors);single_runner_only=$true;new_runner=$false;parallel_runner=$false;final_ready=$false;product_final_ready=$false;fake_data=$false;db_write=$false;migration=$false;production_deploy=$false}
$reportRel='docs/chatgpt_status/gas_emissions/reports/176_gas_emissions_37_browser_proof_latest.json'
$statusRel='docs/chatgpt_status/gas_emissions/status/176_gas_emissions_37_browser_proof_latest.json'
Write-Json(Join-Path $repoRoot($reportRel-replace'/','\'))$payload;Write-Json(Join-Path $repoRoot($statusRel-replace'/','\'))$payload
$canonical=Join-Path $repoRoot 'docs/chatgpt_status/gas_emissions/reports/151_gas_emissions_official_csv_dual_match_and_37_browser_smoke_20260711.json'
$doc=Read-Json $canonical
if($doc){foreach($name in @('status','browser_status','browser_error','browser_unique_row_count','browser_rendered_row_count','browser_new_marker_count','browser_manual_marker_count','browser_console_errors')){$value=if($name-eq'status'-or$name-eq'browser_status'){if($passed){'PASS'}else{'FAIL'}}elseif($name-eq'browser_error'){$payload.browser_error}elseif($name-eq'browser_unique_row_count'){$payload.browser_unique_row_count}elseif($name-eq'browser_rendered_row_count'){$payload.browser_rendered_row_count}elseif($name-eq'browser_new_marker_count'){$payload.browser_new_marker_count}elseif($name-eq'browser_manual_marker_count'){$payload.browser_manual_marker_count}else{@($payload.browser_console_errors)};$doc|Add-Member -NotePropertyName $name -NotePropertyValue $value -Force};Write-Json $canonical $doc}
Remove-Item -LiteralPath $tmpOut -Force -ErrorAction SilentlyContinue
if(-not$passed){throw('GAS_BROWSER_PROOF_FAILED_PHASE_'+[string]$browser.phase+':'+[string]$browser.error)}
$payload|ConvertTo-Json -Depth 40
