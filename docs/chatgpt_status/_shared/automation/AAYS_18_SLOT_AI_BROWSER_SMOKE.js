'use strict';

const fs = require('fs');
const path = require('path');
const { chromium } = require('playwright');

async function main() {
  const outputPath = process.argv[2];
  const screenshotPath = process.argv[3];
  if (!outputPath || !screenshotPath) {
    throw new Error('Usage: node AAYS_18_SLOT_AI_BROWSER_SMOKE.js <output.json> <screenshot.png>');
  }

  const url = 'http://127.0.0.1:8012/england_map_web/geometry_review_3of4_columns_1264.html';
  const browserExecutable = process.env.AAYS_BROWSER_EXECUTABLE || [
    'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe',
    'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe',
    'C:\\Program Files\\Microsoft\\Edge\\Application\\msedge.exe',
  ].find(candidate => fs.existsSync(candidate));
  const browser = await chromium.launch({
    headless: true,
    ...(browserExecutable ? { executablePath: browserExecutable } : {}),
  });
  const page = await browser.newPage({ viewport: { width: 1600, height: 1000 } });
  const pageErrors = [];
  page.on('pageerror', error => pageErrors.push(String(error)));

  try {
    const response = await page.goto(url, { waitUntil: 'networkidle', timeout: 120000 });
    await page.waitForFunction(
      () => document.body.dataset.loadState === 'ready' || document.body.dataset.loadState === 'error',
      null,
      { timeout: 120000 }
    );

    const dom = await page.evaluate(() => {
      const photoLinks = Array.from(document.querySelectorAll('a.path-value'))
        .map(anchor => anchor.getAttribute('href') || '')
        .filter(href => /source_photo_\d+\.(?:jpg|jpeg|png|webp)$/i.test(href));
      return {
        loadState: document.body.dataset.loadState,
        loadMode: document.body.dataset.loadMode,
        visibleRowCount: Number(document.body.dataset.visibleRowCount || 0),
        liveSourceCount: Number(document.body.dataset.liveSourceCount || 0),
        metrics: document.querySelector('#metrics')?.textContent || '',
        message: document.querySelector('#message')?.textContent || '',
        firstRowStatus: document.querySelector('tbody#rows tr')?.dataset.rowStatus || '',
        photoLinkCount: photoLinks.length,
        photoLinks: photoLinks.slice(0, 6),
      };
    });

    const firstPhotoUrl = dom.photoLinks.length ? new URL(dom.photoLinks[0], url).href : null;
    let firstPhoto = null;
    if (firstPhotoUrl) {
      const photoResponse = await page.request.get(firstPhotoUrl, { timeout: 30000 });
      firstPhoto = {
        url: firstPhotoUrl,
        status: photoResponse.status(),
        contentType: photoResponse.headers()['content-type'] || '',
        bytes: (await photoResponse.body()).length,
      };
    }

    await page.screenshot({ path: screenshotPath, fullPage: false });

    const checks = {
      pageHttp200: response?.status() === 200,
      loadReady: dom.loadState === 'ready',
      canonicalGeometryMode: dom.loadMode === 'canonical_geometry',
      canonicalGeometryRows1264: /Canonical geometri ile 1264 satır yüklendi\./i.test(dom.message),
      evidenceFilteredRows911: dom.visibleRowCount === 911,
      liveSourceRows911: dom.liveSourceCount === 911,
      photoMetric781: /Fotoğraf:\s*781/i.test(dom.metrics),
      polygonMetric782: /Polygon:\s*782/i.test(dom.metrics),
      visionComparedZero: /Vision compared:\s*0/i.test(dom.metrics),
      finalReadyFalse: /final_ready:\s*false/i.test(dom.metrics),
      firstRowRendered: Boolean(dom.firstRowStatus),
      photoLinkRendered: dom.photoLinks.length > 0,
      firstPhotoHttpImage: Boolean(
        firstPhoto &&
        firstPhoto.status === 200 &&
        firstPhoto.contentType.toLowerCase().startsWith('image/') &&
        firstPhoto.bytes > 0
      ),
      noPageErrors: pageErrors.length === 0,
    };
    const pass = Object.values(checks).every(Boolean);
    const report = {
      status: pass ? 'BROWSER_UI_PASS_AI_COMPARISON_PENDING' : 'BLOCKED',
      url,
      checks,
      dom,
      firstPhoto,
      pageErrors,
      actualAiModelInferenceTested: false,
      aiVisualComparisonExecuted: false,
      blockers: pass ? ['AI_VISUAL_COMPARISON_ROWS_ZERO'] : ['BROWSER_UI_CHECK_FAILED', 'AI_VISUAL_COMPARISON_ROWS_ZERO'],
      businessFilesWritten: 0,
      fakeData: false,
      finalReady: false,
    };
    fs.mkdirSync(path.dirname(outputPath), { recursive: true });
    fs.writeFileSync(outputPath, `${JSON.stringify(report, null, 2)}\n`, 'utf8');
    process.stdout.write(`${JSON.stringify(report, null, 2)}\n`);
    process.exitCode = pass ? 0 : 2;
  } finally {
    await browser.close();
  }
}

main().catch(error => {
  console.error(error);
  process.exitCode = 1;
});
