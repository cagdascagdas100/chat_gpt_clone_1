const fs = require("fs");
const vm = require("vm");
const timers = require("timers");

const overlayPath = process.argv[2];
if (!overlayPath) throw new Error("overlay path is required");

const sources = new Map();
const layers = new Map();
const map = {
  addSource(id, config) {
    sources.set(id, {
      data: config.data,
      setData(data) { this.data = data; },
    });
  },
  getSource(id) { return sources.get(id) || null; },
  addLayer(config) { layers.set(config.id, config); },
  getLayer(id) { return layers.get(id) || null; },
  setLayoutProperty() {},
  isStyleLoaded() { return true; },
  on() {},
  getCanvas() { return { style: {} }; },
  getBounds() { return null; },
  getZoom() { return 8; },
};

const baseHref = "http://127.0.0.1:8012/england_map_web/index.html";
const windowObject = {
  map,
  location: { origin: "http://127.0.0.1:8012", href: baseHref },
  AAYS_INTERNET_CONFIG: { allowSalesHistoryProxyFallback: false },
};

const context = vm.createContext({
  window: windowObject,
  document: { readyState: "complete", addEventListener() {} },
  URL,
  console,
  setInterval: timers.setInterval,
  clearInterval: timers.clearInterval,
  fetch(input, init) {
    return fetch(new URL(String(input), baseHref), init);
  },
});

vm.runInContext(fs.readFileSync(overlayPath, "utf8"), context, {
  filename: overlayPath,
});

(async () => {
  const activated = await windowObject.AAYS_INTERNET.activate();
  const state = windowObject.AAYS_INTERNET.getState();
  const source = sources.get("aays-internet-access-source");
  const features = Array.isArray(source?.data?.features) ? source.data.features : [];
  const first = features[0]?.properties || {};
  const pass = activated
    && state.active
    && features.length === 33785
    && first.measurement_level === "postcode"
    && first.quality_status === "POSTCODE_COVERAGE_PROXY_NOT_MEASURED_PARCEL_SPEED"
    && first.internet_access_score_10 === undefined;
  process.stdout.write(`${JSON.stringify({
    status: pass ? "PASS" : "BLOCKED",
    activated,
    state,
    feature_count: features.length,
    first_feature: {
      parcel_id: first.parcel_id || null,
      postcode: first.postcode || null,
      level: first.internet_access_level_5 || null,
      display_band_score_10: first.display_band_score_10 ?? null,
      gigabit_coverage_pct: first.gigabit_coverage_pct ?? null,
      measurement_level: first.measurement_level || null,
      quality_status: first.quality_status || null,
      measured_parcel_speed_claim_present: first.internet_access_score_10 !== undefined,
    },
    final_ready: false,
  }, null, 2)}\n`);
  process.exit(pass ? 0 : 2);
})().catch((error) => {
  process.stderr.write(`${String(error)}\n`);
  process.exit(1);
});
