const fs = require('fs');
const path = require('path');
const resultPath = path.join(process.cwd(), 'docs/chatgpt_status/gas_emissions/reports/gas_emissions_browser_smoke_20260703.json');
const url = process.env.GAS_EMISSIONS_CONTROL_URL;
const required = ['emission_percent','level','risk_color','confidence','source','source_date','matching_method','calculation_explanation'];
function write(obj){ fs.mkdirSync(path.dirname(resultPath), {recursive:true}); fs.writeFileSync(resultPath, JSON.stringify({...obj,url,checked_at:new Date().toISOString()}, null, 2)); }
function existing(paths){ return paths.find(p => fs.existsSync(p)); }
(async()=>{
  let chromium;
  try { ({chromium}=require('playwright')); } catch(e){ write({passed:false,status:'playwright_missing',detail:String(e.message||e)}); process.exit(2); }
  const exe = process.env.PLAYWRIGHT_EXECUTABLE_PATH || existing(['C:/Program Files/Microsoft/Edge/Application/msedge.exe','C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe','C:/Program Files/Google/Chrome/Application/chrome.exe','C:/Program Files (x86)/Google/Chrome/Application/chrome.exe']);
  let browser;
  try { browser = await chromium.launch(exe ? {headless:true, executablePath:exe} : {headless:true}); } catch(e){ write({passed:false,status:'browser_launch_failed',detail:String(e.message||e),executablePath:exe||null}); process.exit(2); }
  const page = await browser.newPage({viewport:{width:1440,height:1100}});
  try {
    await page.goto(url, {waitUntil:'domcontentloaded', timeout:30000});
    await page.waitForTimeout(1200);
    const activated = await page.evaluate(async()=>{ if(window.__gasEmissionsActivate20260703){ await window.__gasEmissionsActivate20260703(); return true; } return false; });
    await page.waitForTimeout(1500);
    const body = await page.evaluate(()=>document.body.innerText||'');
    const html = await page.content();
    const missing = required.filter(x=>!body.includes(x)&&!html.includes(x));
    const hasLayer = /Gas Emissions|Gas Emission Level|legend|emission/i.test(body+html);
    const passed = activated && hasLayer && missing.length===0;
    write({passed,status:passed?'passed':'failed',detail:{activated,hasLayer,missing,executablePath:exe||null}});
    await browser.close();
    process.exit(passed?0:2);
  } catch(e) {
    await browser.close();
    write({passed:false,status:'error',detail:String(e.message||e),executablePath:exe||null});
    process.exit(2);
  }
})();
