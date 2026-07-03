const fs = require('fs');
const path = require('path');
const resultPath = path.join(process.cwd(), 'docs/chatgpt_status/gas_emissions/reports/gas_emissions_browser_smoke_20260703.json');
const url = process.env.GAS_EMISSIONS_CONTROL_URL || 'http://127.0.0.1:8020/TerraYield_England_Program_Parcel_Layer_Matrix_20260629.html?refresh=20260630-final';
function write(obj) {
  fs.mkdirSync(path.dirname(resultPath), { recursive: true });
  fs.writeFileSync(resultPath, JSON.stringify({ ...obj, url, checked_at: new Date().toISOString() }, null, 2));
}
(async () => {
  let chromium;
  try {
    ({ chromium } = require('playwright'));
  } catch (err) {
    write({ passed: false, status: 'playwright_missing', detail: 'Playwright is not installed: ' + err.message });
    process.exit(2);
  }
  const requiredText = ['emission_percent', 'risk_color', 'confidence', 'source_date', 'matching_method', 'calculation_explanation'];
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage({ viewport: { width: 1440, height: 1100 } });
  try {
    await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 30000 });
    await page.waitForTimeout(1500);
    const iconClicked = await page.evaluate(() => {
      const candidates = Array.from(document.querySelectorAll('img,button,[role="button"],a,div,span'));
      const hit = candidates.find(el => {
        const txt = ((el.getAttribute('src') || '') + ' ' + (el.getAttribute('alt') || '') + ' ' + (el.getAttribute('title') || '') + ' ' + (el.textContent || '')).toLowerCase();
        return txt.includes('air.png') || txt.includes('gas emissions') || txt.includes('gas emission');
      });
      if (!hit) return false;
      hit.click();
      return true;
    });
    await page.waitForTimeout(2500);
    const body = await page.evaluate(() => document.body.innerText || '');
    const html = await page.content();
    const hasLegend = /legend|Gas Emissions|Gas Emission Level|emission/i.test(body + html);
    const hasGradientSignal = /green|red|#00|#ff|risk_color|emission_percent/i.test(body + html);
    const missingFields = requiredText.filter(t => !(body.includes(t) || html.includes(t)));
    const passed = iconClicked && hasLegend && hasGradientSignal && missingFields.length === 0;
    write({ passed, status: passed ? 'passed' : 'failed', detail: { iconClicked, hasLegend, hasGradientSignal, missingFields } });
    await browser.close();
    process.exit(passed ? 0 : 2);
  } catch (err) {
    await browser.close();
    write({ passed: false, status: 'error', detail: err.message });
    process.exit(2);
  }
})();
