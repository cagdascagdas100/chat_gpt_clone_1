const fs = require('fs');
const path = require('path');
const outDir = path.resolve(__dirname, '..', 'reports');
fs.mkdirSync(outDir, {recursive:true});
const out = path.join(outDir, 'u_latest.txt');
(async()=>{
  let ok=false, msg='no_runtime';
  try {
    const pw = require('playwright');
    const root = 'C:/Users/cagda/Documents/GitHub/AAYS/england_map_web';
    const html = 'file:///' + path.join(root,'index.html').replace(/\\/g,'/');
    const browser = await pw.chromium.launch({headless:true});
    const page = await browser.newPage({viewport:{width:1600,height:1000}});
    await page.goto(html, {waitUntil:'domcontentloaded', timeout:45000});
    await page.waitForTimeout(3000);
    const before = await page.evaluate(() => document.body.innerText || '');
    const el = await page.locator('text=/security|safety|public/i').first();
    const count = await el.count();
    if (count > 0) {
      await el.click({timeout:5000});
      await page.waitForTimeout(5000);
      const after = await page.evaluate(() => document.body.innerText || '');
      await page.screenshot({path:path.join(outDir,'u_view.png'), fullPage:true});
      ok = after.length >= before.length;
      msg = 'clicked=' + (count>0) + ';shot=' + fs.existsSync(path.join(outDir,'u_view.png'));
    } else {
      msg = 'no_button';
    }
    await browser.close();
  } catch(e) { msg = 'err=' + String(e.message || e).slice(0,120); }
  const content = `state: u_done\npercent: 99\nfinal: false\nreason: runtime_interaction_review_needed\nok: ${ok}\n${msg}`;
  fs.writeFileSync(out, content, 'utf8');
  console.log(content);
})();
