// TerraYield Topography browser smoke check - run from repo root when local 8010/8020 servers are available.
const fs = require('fs');
const path = require('path');
const { chromium } = require('playwright');

(async () => {
  const outPath = path.join('docs','chatgpt_status','topography','browser_smoke','topography_browser_smoke_latest_20260704.json');
  fs.mkdirSync(path.dirname(outPath), { recursive: true });
  const result = {
    generated_at: new Date().toISOString(),
    final_ready_smoke: false,
    checks: [],
    blockers: []
  };
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();
  try {
    await page.goto('http://127.0.0.1:8020/TerraYield_England_Program_Parcel_Layer_Matrix_20260629.html?refresh=topography-smoke', { waitUntil: 'domcontentloaded', timeout: 15000 });
    const body = await page.textContent('body');
    const hasPanel = body && body.includes('Topography');
    result.checks.push({ site: '8020', has_topography_text: Boolean(hasPanel) });
    if (!hasPanel) result.blockers.push('8020_topography_text_missing');
  } catch (err) {
    result.blockers.push('8020_unreachable_or_failed:' + err.message);
  }
  try {
    await page.goto('http://127.0.0.1:8010/england_map_web/', { waitUntil: 'domcontentloaded', timeout: 15000 });
    const body = await page.textContent('body');
    const hasMain = body && (body.includes('Topography') || body.includes('Elevation'));
    result.checks.push({ site: '8010', has_topography_or_elevation_text: Boolean(hasMain) });
    if (!hasMain) result.blockers.push('8010_topography_or_elevation_text_missing');
  } catch (err) {
    result.blockers.push('8010_unreachable_or_failed:' + err.message);
  }
  await browser.close();
  result.final_ready_smoke = result.blockers.length === 0;
  fs.writeFileSync(outPath, JSON.stringify(result, null, 2));
  console.log(JSON.stringify(result, null, 2));
})().catch(err => {
  console.error(err);
  process.exit(1);
});
