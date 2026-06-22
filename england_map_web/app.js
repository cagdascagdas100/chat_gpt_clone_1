(async function () {
  const configUrl = new URL(window.AAYS_CONFIG_URL || "./config/regions.local.json", window.location.href);
  configUrl.searchParams.set("v", "20260527-parcel-perf-v1");
  const statusEl = document.getElementById("status");
  const applySecurityMapControlFlag = () => {
    document.body?.setAttribute?.("data-aays-security-map-control", "1");
  };
  applySecurityMapControlFlag();
  if (!document.body) {
    window.addEventListener("DOMContentLoaded", applySecurityMapControlFlag, { once: true });
  }
  const debugBadgeEl = document.getElementById("debugBadge");
  const activeRegionEl = document.getElementById("activeRegion");
  const coverageStateEl = document.getElementById("coverageState");
  const parcelThresholdEl = document.getElementById("parcelThreshold");
  const poiThresholdEl = document.getElementById("poiThreshold");
  const selectedParcelEl = document.getElementById("selectedParcel");
  const renderModeEl = document.getElementById("renderMode");
  const regionSelectEl = document.getElementById("regionSelect");
  const baseMapSelectEl = document.getElementById("baseMapSelect");
  const mapViewModeEl = document.getElementById("mapViewMode");
  const mapModeCustomizerEl = document.getElementById("mapModeCustomizer");
  const screenMenuEl = document.getElementById("screenMenu");
  const citySelectEl = document.getElementById("citySelect");
  const cityInfoEl = document.getElementById("cityInfo");
  const freeCoverageInfoEl = document.getElementById("freeCoverageInfo");
  const coverageCitiesSummaryEl = document.getElementById("coverageCitiesSummary");
  const coverageCitiesListEl = document.getElementById("coverageCitiesList");
  const supportedUnitsSearchEl = document.getElementById("supportedUnitsSearch");
  const supportedUnitsSummaryEl = document.getElementById("supportedUnitsSummary");
  const supportedUnitsListEl = document.getElementById("supportedUnitsList");
  const workspaceContentEl = document.getElementById("workspaceContent");
  const workspaceShellEl = document.querySelector(".workspace-shell");
  const workspaceCollapseBtnEl = document.getElementById("workspaceCollapseBtn");
  const workspaceExpandBtnEl = document.getElementById("workspaceExpandBtn");
  const mapStageEl = document.querySelector(".map-stage");
  const showPoiPointsEl = document.getElementById("showPoiPoints");
  const showPoiLinesEl = document.getElementById("showPoiLines");
  const showTopographyOverlayEl = document.getElementById("showTopographyOverlay");
  const showFutureGrowthEl = document.getElementById("showFutureGrowth");
  const futureGrowthStatusEl = document.getElementById("futureGrowthStatus");
  const futureGrowthLegendEl = document.getElementById("futureGrowthLegend");
  const futureGrowthMethodologyLinkEl = document.getElementById("futureGrowthMethodologyLink");
  const showFacilitiesOverlayEl = document.getElementById("showFacilitiesOverlay");
  const facilitiesCategoryFilterEl = document.getElementById("facilitiesCategoryFilter");
  const scenarioScoreModeEl = document.getElementById("scenarioScoreMode");
  const facilitiesStatusEl = document.getElementById("facilitiesStatus");
  const showOfficialSaleEl = document.getElementById("showOfficialSale");
  const showHistoricSalesEl = document.getElementById("showHistoricSales");
  const showBrownfieldSignalsEl = document.getElementById("showBrownfieldSignals");
  const showMarketListingsEl = document.getElementById("showMarketListings");
  const landSourceStatusEl = document.getElementById("landSourceStatus");
  const landMinConfidenceEl = document.getElementById("landMinConfidence");
  const landMinConfidenceValueEl = document.getElementById("landMinConfidenceValue");
  const brownfieldSourceFilterEl = document.getElementById("brownfieldSourceFilter");
  const listingStatusFilterEl = document.getElementById("listingStatusFilter");
  const saleReadyQuickFiltersEl = document.getElementById("saleReadyQuickFilters");
  const landReviewOnlyEl = document.getElementById("landReviewOnly");
  const resetLandFiltersEl = document.getElementById("resetLandFilters");
  const landFilterSummaryEl = document.getElementById("landFilterSummary");
  const jumpNearestSaleBtnEl = document.getElementById("jumpNearestSaleBtn");

  const protocol = new pmtiles.Protocol();
  maplibregl.addProtocol("pmtiles", protocol.tile);

  const config = await fetch(configUrl.toString()).then((response) => response.json());
  const topographyConfigUrl = new URL(config.topographyOverlayConfigUrl || "./config/topography.overlay.json", window.location.href);
  let topographyOverlayFileConfig = null;
  try {
    const response = await fetch(topographyConfigUrl.toString());
    if (response.ok) {
      topographyOverlayFileConfig = await response.json();
    }
  } catch (_error) {
    topographyOverlayFileConfig = null;
  }
  config.topographyOverlay = mergeTopographyOverlayConfig(topographyOverlayFileConfig, config.topographyOverlay);
  const topographyOverlayConfig = normalizeTopographyOverlayConfig(config.topographyOverlay);
  const futureGrowthConfigUrl = new URL(config.futureGrowthLayerConfigUrl || "./config/future-growth-layer.json", window.location.href);
  let futureGrowthOverlayFileConfig = null;
  try {
    const response = await fetch(futureGrowthConfigUrl.toString());
    if (response.ok) {
      futureGrowthOverlayFileConfig = await response.json();
    }
  } catch (_error) {
    futureGrowthOverlayFileConfig = null;
  }
  config.futureGrowthLayer = mergeFutureGrowthLayerConfig(futureGrowthOverlayFileConfig, config.futureGrowthLayer);
  const futureGrowthLayerConfig = normalizeFutureGrowthLayerConfig(config.futureGrowthLayer);
  const regionMap = new Map(config.regions.map((region) => [region.slug, region]));
  const landIntelligenceApiBaseUrl = ((config.landIntelligenceApiBaseUrl || "same-origin") === "same-origin"
    ? window.location.origin
    : (config.landIntelligenceApiBaseUrl || "")).replace(/\/$/, "");
  const supabaseBridge = window.AAYSSupabaseBridge || null;
  let coverageIndex = null;
  try {
    if (config.coverageIndexUrl) {
      coverageIndex = await fetch(config.coverageIndexUrl).then((response) => (response.ok ? response.json() : null));
    }
  } catch (_error) {
    coverageIndex = null;
  }
  let cityFocusPoints = [];
  try {
    if (config.cityFocusPointsUrl) {
      cityFocusPoints = await fetch(config.cityFocusPointsUrl).then((response) => (response.ok ? response.json() : []));
    }
  } catch (_error) {
    cityFocusPoints = [];
  }
  const cityFocusMap = new Map(cityFocusPoints.map((city) => [city.city, city]));
  const API_FETCH_TIMEOUT_MS = Math.max(1500, Number(config.apiFetchTimeoutMs || 6500));
  const API_BACKOFF_MS = Math.max(5000, Number(config.apiBackoffMs || 30000));
  const apiBackoffState = new Map();
  const apiInFlightRequests = new Map();
  const layerRuntimeWarningGate = new Map();
  const AAYS_REAL_DATA_ONLY = String(window.AAYS_REAL_DATA_ONLY ?? config.aaysRealDataOnly ?? "true").trim().toLowerCase() !== "false";
  const AAYS_PERF_PROFILE = String(window.AAYS_PERF_PROFILE || config.aaysPerfProfile || "balanced").trim().toLowerCase();
  const AAYS_TOPOGRAPHY_TILE_REQUIRED = String(window.AAYS_TOPOGRAPHY_TILE_REQUIRED ?? config.aaysTopographyTileRequired ?? "false")
    .trim()
    .toLowerCase() === "true";
  const LOCAL_COMBINED_SALES_FALLBACK_URL = String(
    config.localCombinedSalesFallbackUrl || "./data/FINAL_3110_CURRENT_CONFIDENCE.polygons.geojson"
  );
  let localCombinedSalesFallbackPromise = null;

  const TURKISH_MOJIBAKE_REPLACEMENTS = [
    ["Ãƒâ€¡", "Ã‡"],
    ["ÃƒÂ§", "Ã§"],
    ["Ãƒâ€“", "Ã–"],
    ["ÃƒÂ¶", "Ã¶"],
    ["ÃƒÅ“", "Ãœ"],
    ["ÃƒÂ¼", "Ã¼"],
    ["Ã„Â°", "Ä°"],
    ["Ã„Â±", "Ä±"],
    ["Ã…Å¾", "Å"],
    ["Ã…Å¸", "ÅŸ"],
    ["Ã„Å¾", "Ä"],
    ["Ã„Å¸", "ÄŸ"],
    ["Ã‚Â·", "Â·"],
    ["Ã‚Â²", "Â²"],
    ["Ã‚Â©", "Â©"],
    ["Ã¢â‚¬â€", "â€”"],
    ["Ã¢â‚¬â€œ", "â€“"],
    ["Ã¢â‚¬Ëœ", "â€˜"],
    ["Ã¢â‚¬â„¢", "â€™"],
    ["Ã¢â‚¬Å“", "â€œ"],
    ["Ã¢â‚¬Â", "â€"],
  ];

  function repairTurkishMojibakeText(value) {
    if (value === null || value === undefined) return "";
    let text = String(value);
    TURKISH_MOJIBAKE_REPLACEMENTS.forEach(([from, to]) => {
      if (text.includes(from)) {
        text = text.split(from).join(to);
      }
    });
    return text;
  }

  function repairTurkishMojibakeInElement(root) {
    if (!root || typeof document === "undefined") return;
    const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
    let node = walker.nextNode();
    while (node) {
      const fixed = repairTurkishMojibakeText(node.nodeValue);
      if (fixed !== node.nodeValue) {
        node.nodeValue = fixed;
      }
      node = walker.nextNode();
    }
    const attrNames = ["title", "aria-label", "placeholder", "alt"];
    const elements = [];
    if (root.nodeType === 1) {
      elements.push(root);
    }
    if (typeof root.querySelectorAll === "function") {
      root.querySelectorAll("*").forEach((el) => elements.push(el));
    }
    elements.forEach((el) => {
      attrNames.forEach((attrName) => {
        if (!el?.hasAttribute?.(attrName)) return;
        const currentValue = el.getAttribute(attrName);
        const fixedValue = repairTurkishMojibakeText(currentValue);
        if (fixedValue !== currentValue) {
          el.setAttribute(attrName, fixedValue);
        }
      });
      if (el instanceof HTMLInputElement || el instanceof HTMLTextAreaElement || el instanceof HTMLOptionElement) {
        const fixedValue = repairTurkishMojibakeText(el.value);
        if (fixedValue !== el.value) {
          el.value = fixedValue;
        }
      }
    });
  }

  function setSanitizedText(element, value) {
    if (!element) return;
    element.textContent = repairTurkishMojibakeText(value);
  }

  function setSanitizedHtml(element, html) {
    if (!element) return;
    element.innerHTML = repairTurkishMojibakeText(html);
    repairTurkishMojibakeInElement(element);
  }

  function emitLayerRuntimeEvent(layer, status, detail = "") {
    try {
      window.dispatchEvent(new CustomEvent("aays:layer-runtime-event", {
        detail: {
          layer: String(layer || "unknown"),
          status: String(status || "unknown"),
          detail: String(detail || ""),
          ts: new Date().toISOString(),
        },
      }));
    } catch (_error) {
      // no-op
    }
  }

  function showThrottledStatus(key, message, sticky = true, cooldownMs = 5000) {
    const gateKey = String(key || "default");
    const lastTs = Number(layerRuntimeWarningGate.get(gateKey) || 0);
    const nowTs = Date.now();
    if ((nowTs - lastTs) < Math.max(500, Number(cooldownMs) || 5000)) {
      return;
    }
    layerRuntimeWarningGate.set(gateKey, nowTs);
    showStatus(message, sticky);
  }

  function normalizeFetchError(error, label) {
    const message = error?.message || "Bilinmeyen hata";
    return `${label}: ${message}`;
  }

  function getApiBackoffState(group = "default") {
    const key = String(group || "default");
    if (!apiBackoffState.has(key)) {
      apiBackoffState.set(key, { unavailableUntilTs: 0, failureStreak: 0 });
    }
    return apiBackoffState.get(key);
  }

  function markApiFailure(group = "default", isServerLikeError = true) {
    if (!isServerLikeError) return;
    const state = getApiBackoffState(group);
    state.failureStreak += 1;
    if (state.failureStreak >= 2) {
      state.unavailableUntilTs = Date.now() + API_BACKOFF_MS;
    }
  }

  function markApiSuccess(group = "default") {
    const state = getApiBackoffState(group);
    state.failureStreak = 0;
    state.unavailableUntilTs = 0;
  }

  async function fetchJsonWithTimeout(url, options = {}) {
    const {
      label = "API",
      timeoutMs = API_FETCH_TIMEOUT_MS,
      fallback = null,
      ignoreBackoff = false,
      backoffGroup = "default",
      dedupe = true,
      dedupeKey = null,
      method = "GET",
      headers = null,
      body = null,
    } = options;
    const fallbackData = typeof fallback === "function" ? fallback() : fallback;
    const backoffState = getApiBackoffState(backoffGroup);
    if (!ignoreBackoff && backoffState.unavailableUntilTs && Date.now() < backoffState.unavailableUntilTs) {
      const waitSec = Math.max(1, Math.round((backoffState.unavailableUntilTs - Date.now()) / 1000));
      return {
        ok: false,
        data: fallbackData,
        error: `${label}: backend gecici olarak beklemede (${waitSec}s, grup=${backoffGroup})`,
      };
    }

    const effectiveDedupeKey = dedupe
      ? String(dedupeKey || `${backoffGroup}::${String(url || "").trim()}`)
      : null;
    if (effectiveDedupeKey && apiInFlightRequests.has(effectiveDedupeKey)) {
      try {
        return await apiInFlightRequests.get(effectiveDedupeKey);
      } catch (_error) {
        // Fall through to create a new request if a previous shared promise unexpectedly failed.
      }
    }

    const requestPromise = (async () => {
      if (!url) {
        return { ok: false, data: fallbackData, error: `${label}: URL tanimli degil` };
      }
      const controller = new AbortController();
      const timer = window.setTimeout(() => controller.abort(), Math.max(500, Number(timeoutMs) || API_FETCH_TIMEOUT_MS));
      try {
        const requestOptions = {
          method,
          signal: controller.signal,
        };
        if (headers) requestOptions.headers = headers;
        if (body !== null && body !== undefined) requestOptions.body = body;
        const response = await fetch(url, requestOptions);
        window.clearTimeout(timer);
        if (!response.ok) {
          markApiFailure(backoffGroup, response.status >= 500 || response.status === 0);
          return { ok: false, data: fallbackData, status: response.status, error: `${label}: HTTP ${response.status}` };
        }
        const data = await response.json();
        markApiSuccess(backoffGroup);
        return { ok: true, data, status: response.status, error: null };
      } catch (error) {
        window.clearTimeout(timer);
        markApiFailure(backoffGroup, true);
        return { ok: false, data: fallbackData, error: normalizeFetchError(error, label) };
      }
    })();

    if (effectiveDedupeKey) {
      apiInFlightRequests.set(effectiveDedupeKey, requestPromise);
    }
    try {
      return await requestPromise;
    } finally {
      if (effectiveDedupeKey) {
        apiInFlightRequests.delete(effectiveDedupeKey);
      }
    }
  }

  async function loadLocalCombinedSalesFallback() {
    if (!localCombinedSalesFallbackPromise) {
      localCombinedSalesFallbackPromise = fetchJsonWithTimeout(LOCAL_COMBINED_SALES_FALLBACK_URL, {
        label: "Yerel satis hazir parsel veri seti",
        fallback: null,
        ignoreBackoff: true,
        backoffGroup: "local-combined-sales-fallback",
        dedupeKey: LOCAL_COMBINED_SALES_FALLBACK_URL,
      });
    }
    const result = await localCombinedSalesFallbackPromise;
    return result.ok && result.data ? result.data : null;
  }

  function escapeHtml(value) {
    return String(value ?? "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#039;");
  }

  function parseBooleanFlag(value, fallback = false) {
    if (typeof value === "boolean") return value;
    if (value === null || value === undefined || value === "") return Boolean(fallback);
    const normalized = String(value).trim().toLowerCase();
    if (["1", "true", "yes", "y", "evet"].includes(normalized)) return true;
    if (["0", "false", "no", "n", "hayir", "hayır"].includes(normalized)) return false;
    return Boolean(fallback);
  }

  function getFirstPresentValue(source, keys, fallback = "") {
    if (!source || !Array.isArray(keys)) return fallback;
    for (const key of keys) {
      if (source[key] !== undefined && source[key] !== null && source[key] !== "") return source[key];
    }
    return fallback;
  }

  function normalizeTextKey(value) {
    return String(value || "")
      .trim()
      .toLowerCase()
      .replace(/\s+/g, " ")
      .replace(/[\u2018\u2019]/g, "'")
      .replace(/[\u201c\u201d]/g, '"');
  }

  function normalizeIdKey(value) {
    return String(value || "")
      .trim()
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, "");
  }

  function getComparableParcelId(value) {
    return String(value || "")
      .trim()
      .replace(/\.0$/, "");
  }

  function getPropertyValue(props, keys, fallback = "") {
    if (!props || !keys) return fallback;
    for (const key of keys) {
      if (Object.prototype.hasOwnProperty.call(props, key)) {
        const value = props[key];
        if (value !== null && value !== undefined && value !== "") {
          return value;
        }
      }
    }
    return fallback;
  }

  function getParcelReference(props = {}) {
    return getPropertyValue(props, [
      "parcel_id",
      "parcel_ref",
      "parcelId",
      "parcel_ref_clean",
      "id",
      "uprn",
      "UPRN",
      "title_number",
      "TITLE_NUMBER",
      "objectid",
      "OBJECTID",
    ], "");
  }

  function getLayerFeatureId(feature) {
    if (!feature) return "";
    const props = feature.properties || {};
    return getPropertyValue(props, ["id", "parcel_id", "parcel_ref", "OBJECTID", "objectid"], feature.id || "");
  }

  function getSaleReadinessScore(props = {}) {
    const value = getPropertyValue(props, [
      "sale_readiness_score",
      "sale_ready_score",
      "confidence_score",
      "score",
      "classification_score",
      "final_score",
    ], "");
    const numeric = Number(value);
    return Number.isFinite(numeric) ? numeric : null;
  }

  function isPositiveSaleReadyEvidence(props = {}) {
    const text = normalizeTextKey([
      getPropertyValue(props, ["sale_ready", "is_sale_ready", "ready_to_sell", "classification", "class", "status"], ""),
      getPropertyValue(props, ["confidence_label", "label", "category"], ""),
    ].join(" "));
    const score = getSaleReadinessScore(props);
    return /\b(ready|yes|true|high|sale|accept|positive)\b/.test(text) || (score !== null && score >= 60);
  }

  function getLandSourceRecordId(record = {}) {
    return getPropertyValue(record, ["source_record_id", "record_id", "id", "listing_id", "transaction_id", "document_id"], "");
  }

  function normalizeSaleDate(value) {
    if (!value) return "";
    const text = String(value).trim();
    const parsed = Date.parse(text);
    if (!Number.isNaN(parsed)) {
      return new Date(parsed).toISOString().slice(0, 10);
    }
    return text;
  }

  function computeCentroidFromRing(ring) {
    if (!Array.isArray(ring) || !ring.length) return null;
    let sumLng = 0;
    let sumLat = 0;
    let count = 0;
    ring.forEach((point) => {
      if (Array.isArray(point) && point.length >= 2) {
        const lng = Number(point[0]);
        const lat = Number(point[1]);
        if (Number.isFinite(lng) && Number.isFinite(lat)) {
          sumLng += lng;
          sumLat += lat;
          count += 1;
        }
      }
    });
    if (!count) return null;
    return [sumLng / count, sumLat / count];
  }

  function getGeometryCentroid(geometry) {
    if (!geometry) return null;
    if (geometry.type === "Point" && Array.isArray(geometry.coordinates)) {
      return geometry.coordinates;
    }
    if (geometry.type === "Polygon" && Array.isArray(geometry.coordinates) && geometry.coordinates[0]) {
      return computeCentroidFromRing(geometry.coordinates[0]);
    }
    if (geometry.type === "MultiPolygon" && Array.isArray(geometry.coordinates)) {
      for (const polygon of geometry.coordinates) {
        const centroid = computeCentroidFromRing(polygon?.[0]);
        if (centroid) return centroid;
      }
    }
    return null;
  }

  function formatCurrency(value) {
    const numeric = Number(value);
    if (!Number.isFinite(numeric) || numeric <= 0) return "-";
    try {
      return new Intl.NumberFormat("en-GB", {
        style: "currency",
        currency: "GBP",
        maximumFractionDigits: 0,
      }).format(numeric);
    } catch (_error) {
      return `GBP ${numeric.toLocaleString("en-GB", { maximumFractionDigits: 0 })}`;
    }
  }

  function formatNumber(value, digits = 0) {
    const numeric = Number(value);
    if (!Number.isFinite(numeric)) return "-";
    return numeric.toLocaleString("en-GB", { maximumFractionDigits: digits });
  }

  function formatPercent(value, digits = 0) {
    const numeric = Number(value);
    if (!Number.isFinite(numeric)) return "-";
    return `${numeric.toLocaleString("en-GB", { maximumFractionDigits: digits })}%`;
  }

  function formatDateShort(value) {
    if (!value) return "-";
    const parsed = Date.parse(value);
    if (Number.isNaN(parsed)) return escapeHtml(value);
    return new Intl.DateTimeFormat("en-GB", { day: "2-digit", month: "short", year: "numeric" }).format(parsed);
  }

  function buildInfoRows(rows) {
    return rows
      .filter(([_, value]) => value !== null && value !== undefined && value !== "" && value !== "-")
      .map(([label, value]) => `
        <div class="info-row">
          <span>${escapeHtml(label)}</span>
          <strong>${escapeHtml(value)}</strong>
        </div>`)
      .join("");
  }

  const TOPIC_ICON_BY_ID = {
    conservation: "./assets/icons/terrayield_icons/wildlife.png",
    "planning-consent": "./assets/icons/terrayield_icons/permits.png",
    topography: "./assets/icons/terrayield_icons/topography.png",
    "future-growth": "./assets/icons/terrayield_icons/growth.png",
    facilities: "./assets/icons/terrayield_icons/facility.png",
    "official-sale": "./assets/icons/terrayield_icons/worth-trend.svg",
    "historic-sales": "./assets/icons/terrayield_icons/cash-sale.png",
    brownfield: "./assets/icons/terrayield_icons/brownfield.png",
    market: "./assets/icons/terrayield_icons/market.png",
    "gas-emissions": "./assets/icons/terrayield_icons/air.png",
  };

  const TOPIC_STATUS_LABEL = {
    conservation: "Dogal Yasam",
    "planning-consent": "Planlama Izinleri",
    topography: "Topografya",
    "future-growth": "Gelecek Buyume",
    facilities: "Tesisler",
    "official-sale": "Resmi Satis Hazirligi",
    "historic-sales": "Gecmis Satislar",
    brownfield: "Brownfield",
    market: "Pazar",
    "gas-emissions": "Hava Kirliligi",
  };

  const GAS_EMISSIONS_SOURCE_ID = "gas-emissions-source";
  const GAS_EMISSIONS_FILL_LAYER_ID = "gas-emissions-fill";
  const GAS_EMISSIONS_LINE_LAYER_ID = "gas-emissions-line";
  const GAS_EMISSIONS_DATA_URL = "./data/parcel_emissions_scores.geojson?v=20260622-gas-emissions-v2";
  const GAS_EMISSIONS_SOURCE_FEATURE_COUNT = 4246;
  const GAS_EMISSIONS_LEGEND_ROWS = [
    { label: "0-20 Very Low", color: "#1a9850" },
    { label: "21-40 Low", color: "#91cf60" },
    { label: "41-60 Medium", color: "#fee08b" },
    { label: "61-80 High", color: "#fc8d59" },
    { label: "81-100 Very High", color: "#d73027" },
    { label: "No Data", color: "#94a3b8" },
  ];

  const PLACEHOLDER_TEXT = "Bu katman icin veri hazirlanıyor.";

  function getTopicIcon(topicId) {
    return TOPIC_ICON_BY_ID[topicId] || "./assets/icons/terrayield_icons/market.png";
  }

  function getTopicStatusLabel(topicId) {
    return TOPIC_STATUS_LABEL[topicId] || topicId;
  }

  function getTopicLabel(topic) {
    return topic?.label || topic?.title || getTopicStatusLabel(topic?.id || "topic");
  }

  function buildTopicPlaceholderHtml(topic) {
    const label = getTopicLabel(topic);
    const icon = getTopicIcon(topic.id);
    return `
      <div class="topic-placeholder-card">
        <div class="topic-placeholder-icon"><img src="${escapeHtml(icon)}" alt="" /></div>
        <div>
          <h3>${escapeHtml(label)}</h3>
          <p>${escapeHtml(PLACEHOLDER_TEXT)}</p>
        </div>
      </div>`;
  }

  function buildGasEmissionsLegendHtml() {
    const rows = GAS_EMISSIONS_LEGEND_ROWS.map((row) => `
      <div class="map-legend-row">
        <span class="map-legend-swatch" style="background:${escapeHtml(row.color)}"></span>
        <span>${escapeHtml(row.label)}</span>
      </div>`).join("");
    return `
      <div class="map-legend-card gas-emissions-legend" data-layer="gas-emissions">
        <strong>Gas Emissions</strong>
        <span>Parcel thematic score (${GAS_EMISSIONS_SOURCE_FEATURE_COUNT} features)</span>
        ${rows}
      </div>`;
  }

  function ensureMapLegendContainer() {
    let container = document.getElementById("mapLegend");
    if (container) return container;
    container = document.createElement("div");
    container.id = "mapLegend";
    container.className = "map-legend-container";
    const mapContainer = document.getElementById("map") || document.querySelector(".map-shell") || document.body;
    mapContainer?.appendChild?.(container);
    return container;
  }

  function setGasEmissionsLegendVisible(visible) {
    const container = ensureMapLegendContainer();
    if (!container) return;
    const existing = container.querySelector('[data-layer="gas-emissions"]');
    if (!visible) {
      existing?.remove?.();
      return;
    }
    if (existing) {
      existing.outerHTML = buildGasEmissionsLegendHtml();
      return;
    }
    container.insertAdjacentHTML("beforeend", buildGasEmissionsLegendHtml());
  }

  function getEmissionColor(value) {
    const numeric = Number(value);
    if (!Number.isFinite(numeric)) return "#94a3b8";
    if (numeric <= 20) return "#1a9850";
    if (numeric <= 40) return "#91cf60";
    if (numeric <= 60) return "#fee08b";
    if (numeric <= 80) return "#fc8d59";
    return "#d73027";
  }

  function getEmissionLevel(value) {
    const numeric = Number(value);
    if (!Number.isFinite(numeric)) return "No Data";
    if (numeric <= 20) return "Very Low";
    if (numeric <= 40) return "Low";
    if (numeric <= 60) return "Medium";
    if (numeric <= 80) return "High";
    return "Very High";
  }

  function normalizeParcelLookupKey(value) {
    return String(value || "")
      .trim()
      .toLowerCase()
      .replace(/\.0$/, "")
      .replace(/[^a-z0-9]+/g, "");
  }

  function getGasEmissionRecordKeys(props = {}) {
    return [
      props.parcel_id,
      props.parcel_ref,
      props.parcel_ref_clean,
      props.id,
      props.uprn,
      props.UPRN,
      props.title_number,
      props.TITLE_NUMBER,
      props.objectid,
      props.OBJECTID,
    ].map(normalizeParcelLookupKey).filter(Boolean);
  }

  const gasEmissionsLookupState = {
    promise: null,
    byKey: new Map(),
    featureCount: 0,
    loaded: false,
    error: null,
  };

  async function ensureGasEmissionsPopupLookupLoaded() {
    if (gasEmissionsLookupState.loaded || gasEmissionsLookupState.promise) {
      return gasEmissionsLookupState.promise || gasEmissionsLookupState;
    }
    gasEmissionsLookupState.promise = fetchJsonWithTimeout(GAS_EMISSIONS_DATA_URL, {
      label: "Gas emissions popup lookup",
      fallback: null,
      ignoreBackoff: true,
      backoffGroup: "gas-emissions-popup-lookup",
      dedupeKey: GAS_EMISSIONS_DATA_URL,
    }).then((result) => {
      if (!result.ok || !result.data?.features) {
        gasEmissionsLookupState.error = result.error || "gas emissions data unavailable";
        gasEmissionsLookupState.loaded = true;
        return gasEmissionsLookupState;
      }
      result.data.features.forEach((feature) => {
        const props = feature?.properties || {};
        getGasEmissionRecordKeys(props).forEach((key) => {
          if (!gasEmissionsLookupState.byKey.has(key)) {
            gasEmissionsLookupState.byKey.set(key, props);
          }
        });
      });
      gasEmissionsLookupState.featureCount = result.data.features.length;
      gasEmissionsLookupState.loaded = true;
      return gasEmissionsLookupState;
    }).catch((error) => {
      gasEmissionsLookupState.error = error?.message || String(error);
      gasEmissionsLookupState.loaded = true;
      return gasEmissionsLookupState;
    });
    return gasEmissionsLookupState.promise;
  }

  function findGasEmissionsRecordForParcel(props = {}) {
    const keys = getGasEmissionRecordKeys(props);
    for (const key of keys) {
      if (gasEmissionsLookupState.byKey.has(key)) return gasEmissionsLookupState.byKey.get(key);
    }
    return null;
  }

  function normalizeGasEmissionsRecord(record = {}) {
    const emissionPercent = Number(getFirstPresentValue(record, ["emission_percent", "emissions_percent", "score", "emissionScore"], ""));
    const color = getFirstPresentValue(record, ["emission_color_hex", "color", "fill_color"], getEmissionColor(emissionPercent));
    const level = getFirstPresentValue(record, ["emission_level", "level", "category"], getEmissionLevel(emissionPercent));
    return {
      parcel_id: getFirstPresentValue(record, ["parcel_id", "id", "parcel_ref"], ""),
      parcel_ref: getFirstPresentValue(record, ["parcel_ref", "parcel_id", "id"], ""),
      emission_percent: Number.isFinite(emissionPercent) ? emissionPercent : null,
      emission_level: level,
      emission_color_hex: color,
      confidence: getFirstPresentValue(record, ["confidence", "confidence_label", "confidencePercent", "confidence_percent"], ""),
      source_type: getFirstPresentValue(record, ["source_type", "sourceType"], ""),
      source: getFirstPresentValue(record, ["source", "evidence", "source_name", "source_title"], ""),
      source_date: getFirstPresentValue(record, ["source_date", "date", "updated_at", "sourceDate"], ""),
      matching_method: getFirstPresentValue(record, ["matching_method", "match_method", "method"], ""),
      calculation_explanation: getFirstPresentValue(record, ["calculation_explanation", "explanation", "calculation"], ""),
    };
  }

  function buildGasEmissionsPopupMetaHtml(parcelProps = {}) {
    const record = findGasEmissionsRecordForParcel(parcelProps) || parcelProps;
    const gas = normalizeGasEmissionsRecord(record);
    const hasGasData = gas.emission_percent !== null || gas.emission_level || gas.source_type || gas.source;
    if (!hasGasData) return "";
    const rows = buildInfoRows([
      ["emission_percent", gas.emission_percent === null ? "" : formatPercent(gas.emission_percent, 0)],
      ["emission_level", gas.emission_level],
      ["emission_color_hex", gas.emission_color_hex],
      ["confidence", gas.confidence],
      ["source_type", gas.source_type],
      ["source/evidence", gas.source],
      ["source_date", gas.source_date],
      ["matching_method", gas.matching_method],
      ["calculation_explanation", gas.calculation_explanation],
    ]);
    if (!rows) return "";
    return `
      <div class="popup-section gas-emissions-popup-meta">
        <h4>Gas Emissions</h4>
        ${rows}
      </div>`;
  }

  async function buildVisiblePolygonFeatures(sourceFeatures, sourceLookupByParcelId, sourceLookupByParcelRef) {
    if (!Array.isArray(sourceFeatures) || !sourceFeatures.length) return [];
    const fallbackGeoJson = await loadLocalCombinedSalesFallback();
    const fallbackFeatures = Array.isArray(fallbackGeoJson?.features) ? fallbackGeoJson.features : [];
    const visibleFeatures = [];
    const getLookupMatch = (props = {}) => {
      const ids = getGasEmissionRecordKeys(props);
      for (const key of ids) {
        if (sourceLookupByParcelId.has(key) || sourceLookupByParcelRef.has(key)) {
          return sourceLookupByParcelId.get(key) || sourceLookupByParcelRef.get(key);
        }
      }
      return null;
    };
    fallbackFeatures.forEach((parcelFeature) => {
      const match = getLookupMatch(parcelFeature.properties || {});
      if (!match) return;
      const matchProps = match.properties || {};
      const emissionPercent = Number(getFirstPresentValue(matchProps, ["emission_percent", "score"], ""));
      const mergedProps = {
        ...(parcelFeature.properties || {}),
        ...matchProps,
        emission_percent: Number.isFinite(emissionPercent) ? emissionPercent : matchProps.emission_percent,
        emission_level: getFirstPresentValue(matchProps, ["emission_level"], getEmissionLevel(emissionPercent)),
        emission_color_hex: getFirstPresentValue(matchProps, ["emission_color_hex"], getEmissionColor(emissionPercent)),
      };
      visibleFeatures.push({
        type: "Feature",
        geometry: parcelFeature.geometry,
        properties: mergedProps,
      });
    });
    return visibleFeatures;
  }

  function resolveSaleReadyTopicState(topicId) {
    const topic = Array.isArray(config?.landIntelligenceTopics)
      ? config.landIntelligenceTopics.find((item) => item.id === topicId)
      : null;
    return {
      topic,
      icon: getTopicIcon(topicId),
      label: getTopicStatusLabel(topicId),
    };
  }

  function getLayerIdsForTopic(topicId) {
    switch (topicId) {
      case "conservation":
        return ["conservation-sites-fill", "conservation-sites-line"];
      case "planning-consent":
        return ["planning-consent-fill", "planning-consent-line", "planning-consent-points"];
      case "topography":
        return ["topography-fill", "topography-line"];
      case "future-growth":
        return ["future-growth-fill", "future-growth-line"];
      case "facilities":
        return ["facilities-circles", "facilities-labels"];
      case "official-sale":
        return ["official-sale-fill", "official-sale-line"];
      case "historic-sales":
        return ["historic-sales-fill", "historic-sales-line"];
      case "brownfield":
        return ["brownfield-fill", "brownfield-line"];
      case "market":
        return ["market-listings-circles", "market-listings-labels"];
      case "gas-emissions":
        return [GAS_EMISSIONS_FILL_LAYER_ID, GAS_EMISSIONS_LINE_LAYER_ID];
      default:
        return [];
    }
  }

  function getLayerVisibility(layerId) {
    if (!map || !layerId || !map.getLayer(layerId)) return "none";
    return map.getLayoutProperty(layerId, "visibility") || "visible";
  }

  function setLayerVisibilityIfExists(layerId, visible) {
    if (!map || !layerId || !map.getLayer(layerId)) return;
    map.setLayoutProperty(layerId, "visibility", visible ? "visible" : "none");
  }

  function setTopicButtonActive(topicId, active) {
    const button = document.querySelector(`[data-topic-button="${CSS.escape(topicId)}"]`);
    if (!button) return;
    button.classList.toggle("is-active", Boolean(active));
    button.setAttribute("aria-pressed", active ? "true" : "false");
  }

  function isTopicVisible(topicId) {
    return getLayerIdsForTopic(topicId).some((layerId) => getLayerVisibility(layerId) === "visible");
  }

  async function ensureGasEmissionsLayerLoaded() {
    if (!map) return { ok: false, error: "map unavailable" };
    await ensureGasEmissionsPopupLookupLoaded();
    if (map.getSource(GAS_EMISSIONS_SOURCE_ID)) return { ok: true, mode: "existing" };
    const sourceResult = await fetchJsonWithTimeout(GAS_EMISSIONS_DATA_URL, {
      label: "Gas emissions parcel dataset",
      fallback: null,
      ignoreBackoff: true,
      backoffGroup: "gas-emissions-layer",
      dedupeKey: GAS_EMISSIONS_DATA_URL,
    });
    if (!sourceResult.ok || !sourceResult.data?.features) {
      return { ok: false, error: sourceResult.error || "gas dataset unavailable" };
    }
    const sourceFeatures = sourceResult.data.features;
    const sourceLookupByParcelId = new Map();
    const sourceLookupByParcelRef = new Map();
    sourceFeatures.forEach((feature) => {
      const props = feature.properties || {};
      getGasEmissionRecordKeys(props).forEach((key) => {
        if (!sourceLookupByParcelId.has(key)) sourceLookupByParcelId.set(key, feature);
        if (!sourceLookupByParcelRef.has(key)) sourceLookupByParcelRef.set(key, feature);
      });
    });
    const directSourceMode = false;
    let visibleFeatures = directSourceMode ? sourceFeatures : await buildVisiblePolygonFeatures(sourceFeatures, sourceLookupByParcelId, sourceLookupByParcelRef);
    let geometryMode = directSourceMode ? "point_source" : "polygon_join";
    if (!visibleFeatures.length) {
      visibleFeatures = sourceFeatures;
      geometryMode = "point_fallback";
    }
    map.addSource(GAS_EMISSIONS_SOURCE_ID, {
      type: "geojson",
      data: {
        type: "FeatureCollection",
        features: visibleFeatures,
      },
    });
    map.addLayer({
      id: GAS_EMISSIONS_FILL_LAYER_ID,
      type: "fill",
      source: GAS_EMISSIONS_SOURCE_ID,
      layout: { visibility: "none" },
      paint: {
        "fill-color": ["coalesce", ["get", "emission_color_hex"], ["get", "color"], ["case",
          ["<=", ["to-number", ["get", "emission_percent"]], 20], "#1a9850",
          ["<=", ["to-number", ["get", "emission_percent"]], 40], "#91cf60",
          ["<=", ["to-number", ["get", "emission_percent"]], 60], "#fee08b",
          ["<=", ["to-number", ["get", "emission_percent"]], 80], "#fc8d59",
          "#d73027"
        ]],
        "fill-opacity": 0.52,
      },
    });
    map.addLayer({
      id: GAS_EMISSIONS_LINE_LAYER_ID,
      type: "line",
      source: GAS_EMISSIONS_SOURCE_ID,
      layout: { visibility: "none" },
      paint: {
        "line-color": "#0f172a",
        "line-width": 0.8,
        "line-opacity": 0.35,
      },
    });
    window.AAYS_GAS_EMISSIONS = window.AAYS_GAS_EMISSIONS || {};
    window.AAYS_GAS_EMISSIONS.getState = () => ({
      loaded: true,
      sourceId: GAS_EMISSIONS_SOURCE_ID,
      fillLayerId: GAS_EMISSIONS_FILL_LAYER_ID,
      lineLayerId: GAS_EMISSIONS_LINE_LAYER_ID,
      sourceFeatureCount: sourceFeatures.length,
      visibleFeatureCount: visibleFeatures.length,
      geometryMode,
      directSourceMode,
    });
    return { ok: true, mode: geometryMode, sourceFeatureCount: sourceFeatures.length, visibleFeatureCount: visibleFeatures.length };
  }

  async function setGasEmissionsLayerVisible(visible) {
    const loaded = await ensureGasEmissionsLayerLoaded();
    if (!loaded.ok) {
      showThrottledStatus("gas-emissions-layer", `Hava Kirliligi katmani yuklenemedi: ${loaded.error || "bilinmeyen hata"}`);
      emitLayerRuntimeEvent("gas-emissions", "error", loaded.error || "load failed");
      return false;
    }
    setLayerVisibilityIfExists(GAS_EMISSIONS_FILL_LAYER_ID, visible);
    setLayerVisibilityIfExists(GAS_EMISSIONS_LINE_LAYER_ID, visible);
    setGasEmissionsLegendVisible(visible);
    setTopicButtonActive("gas-emissions", visible);
    emitLayerRuntimeEvent("gas-emissions", visible ? "visible" : "hidden", loaded.mode || "loaded");
    return true;
  }

  async function toggleGasEmissionsLayer() {
    const visible = isTopicVisible("gas-emissions");
    return setGasEmissionsLayerVisible(!visible);
  }

  function updateTopicPlaceholder(topic) {
    if (!topic || !workspaceContentEl) return;
    setSanitizedHtml(workspaceContentEl, buildTopicPlaceholderHtml(topic));
  }

  function removeTopicPlaceholderIfActive(topicId) {
    if (!workspaceContentEl) return;
    const existing = workspaceContentEl.querySelector?.(".topic-placeholder-card");
    if (existing && existing.textContent.includes(getTopicStatusLabel(topicId))) {
      existing.remove();
    }
  }

  function getVisibleWorthTopics() {
    const topics = Array.isArray(config?.landIntelligenceTopics) ? config.landIntelligenceTopics : [];
    return topics.filter((topic) => topic?.visible !== false);
  }

  function buildLandSourceBadges() {
    return `<div class="topic-badges">
      <span>Evidence-first</span>
      <span>Real data only</span>
      <span>No DB write</span>
    </div>`;
  }

  function buildWorthTopicButtons() {
    const topics = getVisibleWorthTopics();
    if (!topics.length) return "";
    return topics.map((topic) => {
      const topicId = topic.id || "topic";
      const icon = getTopicIcon(topicId);
      const label = getTopicLabel(topic);
      const statusLabel = getTopicStatusLabel(topicId);
      return `
        <button class="worth-topic-button" type="button" data-topic-button="${escapeHtml(topicId)}" aria-pressed="false">
          <span class="worth-topic-icon"><img src="${escapeHtml(icon)}" alt="" /></span>
          <span>${escapeHtml(label || statusLabel)}</span>
        </button>`;
    }).join("");
  }

  function renderLandIntelligencePanel() {
    if (!workspaceContentEl) return;
    const topics = buildWorthTopicButtons();
    setSanitizedHtml(workspaceContentEl, `
      <section class="land-intelligence-panel">
        <div class="panel-header-row">
          <div>
            <p class="eyebrow">TerraYield Intelligence</p>
            <h3>Deger haritasi katmanlari</h3>
            <p>Planlama, cevre, pazar ve satis hazirligi katmanlarini tek harita uzerinden yonet.</p>
          </div>
        </div>
        ${buildLandSourceBadges()}
        <div class="worth-topic-grid">${topics}</div>
      </section>`);
    wireWorthTopicButtons();
  }

  function wireWorthTopicButtons() {
    if (!workspaceContentEl) return;
    workspaceContentEl.querySelectorAll("[data-topic-button]").forEach((button) => {
      button.addEventListener("click", async () => {
        const topicId = button.getAttribute("data-topic-button") || "";
        if (!topicId) return;
        if (topicId === "gas-emissions") {
          await toggleGasEmissionsLayer();
          return;
        }
        const topic = getVisibleWorthTopics().find((item) => item.id === topicId);
        updateTopicPlaceholder(topic || { id: topicId, label: getTopicStatusLabel(topicId) });
      });
    });
  }

  function applyWorthLayerBoot() {
    if (!Array.isArray(config.landIntelligenceTopics)) {
      config.landIntelligenceTopics = [];
    }
    const hasGasTopic = config.landIntelligenceTopics.some((topic) => topic.id === "gas-emissions");
    if (!hasGasTopic) {
      config.landIntelligenceTopics.push({ id: "gas-emissions", label: "Hava Kirliligi", visible: true });
    }
  }

  applyWorthLayerBoot();

  const DEFAULT_REGION_STYLE = {
    stroke: "#0f172a",
    fill: "#2563eb",
    fillOpacity: 0.12,
    lineOpacity: 0.55,
  };

  function normalizeTopographyOverlayConfig(value) {
    const configValue = value && typeof value === "object" ? value : {};
    const contour = configValue.contour || {};
    const flood = configValue.flood || {};
    const slope = configValue.slope || {};
    const hazard = configValue.hazard || {};
    return {
      enabled: parseBooleanFlag(configValue.enabled, true),
      tileRequired: parseBooleanFlag(configValue.tileRequired, AAYS_TOPOGRAPHY_TILE_REQUIRED),
      statusLabel: configValue.statusLabel || "Topografya hazir",
      contour: {
        enabled: parseBooleanFlag(contour.enabled, true),
        url: contour.url || "./data/topography/slope_contours.geojson",
        sourceId: contour.sourceId || "topography-contours-source",
        lineLayerId: contour.lineLayerId || "topography-contours-line",
        fillLayerId: contour.fillLayerId || "topography-contours-fill",
        labelLayerId: contour.labelLayerId || "topography-contours-label",
        lineColor: contour.lineColor || "#7c3aed",
        fillColor: contour.fillColor || "#a78bfa",
        fillOpacity: Number(contour.fillOpacity ?? 0.09),
        lineWidth: Number(contour.lineWidth ?? 1.05),
        labelField: contour.labelField || "elevation_label",
      },
      flood: {
        enabled: parseBooleanFlag(flood.enabled, true),
        url: flood.url || "./data/topography/flood_risk_zones.geojson",
        sourceId: flood.sourceId || "topography-flood-source",
        layerId: flood.layerId || "topography-flood-fill",
        outlineLayerId: flood.outlineLayerId || "topography-flood-line",
        fillColor: flood.fillColor || "#38bdf8",
        lineColor: flood.lineColor || "#0284c7",
        fillOpacity: Number(flood.fillOpacity ?? 0.16),
      },
      slope: {
        enabled: parseBooleanFlag(slope.enabled, true),
        url: slope.url || "./data/topography/slope_risk_grid.geojson",
        sourceId: slope.sourceId || "topography-slope-source",
        layerId: slope.layerId || "topography-slope-fill",
        outlineLayerId: slope.outlineLayerId || "topography-slope-line",
        fillColor: slope.fillColor || "#f59e0b",
        lineColor: slope.lineColor || "#b45309",
        fillOpacity: Number(slope.fillOpacity ?? 0.14),
      },
      hazard: {
        enabled: parseBooleanFlag(hazard.enabled, true),
        url: hazard.url || "./data/topography/topography_hazard_zones.geojson",
        sourceId: hazard.sourceId || "topography-hazard-source",
        layerId: hazard.layerId || "topography-hazard-fill",
        outlineLayerId: hazard.outlineLayerId || "topography-hazard-line",
        fillColor: hazard.fillColor || "#ef4444",
        lineColor: hazard.lineColor || "#991b1b",
        fillOpacity: Number(hazard.fillOpacity ?? 0.12),
      },
    };
  }

  function mergeTopographyOverlayConfig(fileConfig, inlineConfig) {
    return {
      ...(inlineConfig || {}),
      ...(fileConfig || {}),
      contour: {
        ...((inlineConfig || {}).contour || {}),
        ...((fileConfig || {}).contour || {}),
      },
      flood: {
        ...((inlineConfig || {}).flood || {}),
        ...((fileConfig || {}).flood || {}),
      },
      slope: {
        ...((inlineConfig || {}).slope || {}),
        ...((fileConfig || {}).slope || {}),
      },
      hazard: {
        ...((inlineConfig || {}).hazard || {}),
        ...((fileConfig || {}).hazard || {}),
      },
    };
  }

  function normalizeFutureGrowthLayerConfig(value) {
    const configValue = value && typeof value === "object" ? value : {};
    const source = configValue.source || {};
    const overlay = configValue.overlay || {};
    const demand = configValue.demand || {};
    const infrastructure = configValue.infrastructure || {};
    const constraints = configValue.constraints || {};
    const projects = configValue.projects || {};
    return {
      enabled: parseBooleanFlag(configValue.enabled, true),
      statusLabel: configValue.statusLabel || "Gelecek buyume hazir",
      source: {
        enabled: parseBooleanFlag(source.enabled, true),
        url: source.url || "./data/future_growth/future_growth_scores.geojson",
        sourceId: source.sourceId || "future-growth-source",
        fillLayerId: source.fillLayerId || "future-growth-fill",
        lineLayerId: source.lineLayerId || "future-growth-line",
        labelLayerId: source.labelLayerId || "future-growth-label",
      },
      overlay: {
        fillOpacity: Number(overlay.fillOpacity ?? 0.55),
        lineColor: overlay.lineColor || "#075985",
        lineOpacity: Number(overlay.lineOpacity ?? 0.58),
        lineWidth: Number(overlay.lineWidth ?? 1.1),
      },
      demand: {
        low: demand.low || "#dbeafe",
        medium: demand.medium || "#60a5fa",
        high: demand.high || "#2563eb",
        veryHigh: demand.veryHigh || "#1d4ed8",
        noData: demand.noData || "#cbd5e1",
      },
      infrastructure: {
        enabled: parseBooleanFlag(infrastructure.enabled, true),
        url: infrastructure.url || "./data/future_growth/infrastructure_pipeline.geojson",
        sourceId: infrastructure.sourceId || "future-growth-infrastructure-source",
        layerId: infrastructure.layerId || "future-growth-infrastructure-line",
        pointLayerId: infrastructure.pointLayerId || "future-growth-infrastructure-point",
        lineColor: infrastructure.lineColor || "#0891b2",
        pointColor: infrastructure.pointColor || "#0e7490",
      },
      constraints: {
        enabled: parseBooleanFlag(constraints.enabled, true),
        url: constraints.url || "./data/future_growth/growth_constraints.geojson",
        sourceId: constraints.sourceId || "future-growth-constraints-source",
        layerId: constraints.layerId || "future-growth-constraints-fill",
        lineLayerId: constraints.lineLayerId || "future-growth-constraints-line",
        fillColor: constraints.fillColor || "#dc2626",
        lineColor: constraints.lineColor || "#991b1b",
      },
      projects: {
        enabled: parseBooleanFlag(projects.enabled, true),
        url: projects.url || "./data/future_growth/project_pipeline_points.geojson",
        sourceId: projects.sourceId || "future-growth-projects-source",
        layerId: projects.layerId || "future-growth-projects-circle",
        labelLayerId: projects.labelLayerId || "future-growth-projects-label",
        circleColor: projects.circleColor || "#f97316",
      },
    };
  }

  function mergeFutureGrowthLayerConfig(fileConfig, inlineConfig) {
    return {
      ...(inlineConfig || {}),
      ...(fileConfig || {}),
      source: {
        ...((inlineConfig || {}).source || {}),
        ...((fileConfig || {}).source || {}),
      },
      overlay: {
        ...((inlineConfig || {}).overlay || {}),
        ...((fileConfig || {}).overlay || {}),
      },
      demand: {
        ...((inlineConfig || {}).demand || {}),
        ...((fileConfig || {}).demand || {}),
      },
      infrastructure: {
        ...((inlineConfig || {}).infrastructure || {}),
        ...((fileConfig || {}).infrastructure || {}),
      },
      constraints: {
        ...((inlineConfig || {}).constraints || {}),
        ...((fileConfig || {}).constraints || {}),
      },
      projects: {
        ...((inlineConfig || {}).projects || {}),
        ...((fileConfig || {}).projects || {}),
      },
    };
  }

  const COVERAGE_STATUS_LABELS = {
    active: "Aktif",
    live: "Canli",
    available: "Uygun",
    planned: "Planlandi",
    beta: "Beta",
    limited: "Sinirli",
    restricted: "Kisitli",
    unavailable: "Yok",
  };

  function getCoverageConfigFromIndex(regionSlug) {
    const normalizedSlug = String(regionSlug || "").trim().toLowerCase();
    if (!coverageIndex || !normalizedSlug) return null;
    if (Array.isArray(coverageIndex.regions)) {
      return coverageIndex.regions.find((entry) => String(entry.slug || "").trim().toLowerCase() === normalizedSlug) || null;
    }
    if (coverageIndex.regions && typeof coverageIndex.regions === "object") {
      return coverageIndex.regions[normalizedSlug] || null;
    }
    return null;
  }

  function normalizeCoverageMode(value, fallback = "active") {
    const normalized = String(value || "").trim().toLowerCase();
    if (["active", "live", "available", "planned", "beta", "limited", "restricted", "unavailable"].includes(normalized)) {
      return normalized;
    }
    return fallback;
  }

  function normalizeParcelCoverageConfig(region) {
    const indexed = getCoverageConfigFromIndex(region?.slug);
    const source = {
      ...(indexed?.parcelCoverage || {}),
      ...(region?.parcelCoverage || {}),
    };
    const mode = normalizeCoverageMode(source.mode || indexed?.mode || region?.coverageMode || "active");
    return {
      mode,
      label: source.label || COVERAGE_STATUS_LABELS[mode] || COVERAGE_STATUS_LABELS.active,
      message: source.message || "Parsel verisi kullanilabilir.",
      coveragePercent: Number(source.coveragePercent ?? 100),
      freeParcelLimit: Number(source.freeParcelLimit ?? region?.freeParcelLimit ?? 0),
      paidRequired: parseBooleanFlag(source.paidRequired ?? region?.paidRequired, false),
      disabledReason: source.disabledReason || "",
    };
  }

  function getFeatureCountFromSource(source) {
    if (!source) return 0;
    if (Array.isArray(source.features)) return source.features.length;
    if (source.data && Array.isArray(source.data.features)) return source.data.features.length;
    return 0;
  }

  function formatCoverageSummary(region, source, fallback = "") {
    const featureCount = getFeatureCountFromSource(source);
    const city = region?.city || region?.name || "Bolge";
    if (featureCount > 0) {
      return `${city}: ${formatNumber(featureCount)} parsel yuklendi`;
    }
    return fallback || `${city}: parsel kapsam bilgisi hazir`;
  }

  function buildCoverageCities(region) {
    const coverageConfig = normalizeParcelCoverageConfig(region);
    const cityName = region?.city || region?.name || region?.slug || "Bilinmeyen";
    const indexed = getCoverageConfigFromIndex(region?.slug);
    const aliases = Array.isArray(indexed?.aliases) ? indexed.aliases : [];
    const status = coverageConfig.label || COVERAGE_STATUS_LABELS[coverageConfig.mode] || "Aktif";
    return [{
      name: cityName,
      slug: region?.slug || cityName.toLowerCase(),
      status,
      mode: coverageConfig.mode,
      aliases,
      freeParcelLimit: coverageConfig.freeParcelLimit,
    }];
  }

  function updateCoverageCitiesPanel(region) {
    if (!coverageCitiesSummaryEl || !coverageCitiesListEl) return;
    const cities = buildCoverageCities(region);
    coverageCitiesSummaryEl.textContent = `${cities.length} desteklenen sehir`;
    coverageCitiesListEl.innerHTML = cities.map((city) => `
      <li>
        <strong>${escapeHtml(city.name)}</strong>
        <span>${escapeHtml(city.status)}</span>
      </li>
    `).join("");
  }

  function normalizeSupportedUnits(region) {
    const indexed = getCoverageConfigFromIndex(region?.slug);
    const units = [
      ...(Array.isArray(indexed?.supportedUnits) ? indexed.supportedUnits : []),
      ...(Array.isArray(region?.supportedUnits) ? region.supportedUnits : []),
    ];
    if (units.length) {
      const seen = new Set();
      return units.filter((unit) => {
        const key = normalizeTextKey(unit?.name || unit?.code || "");
        if (!key || seen.has(key)) return false;
        seen.add(key);
        return true;
      });
    }
    return [{
      name: region?.city || region?.name || "Ana kapsama alani",
      code: region?.slug || "region",
      type: "city",
      status: "active",
    }];
  }

  function updateSupportedUnitsPanel(region) {
    if (!supportedUnitsSummaryEl || !supportedUnitsListEl) return;
    const units = normalizeSupportedUnits(region);
    supportedUnitsSummaryEl.textContent = `${units.length} birim`;
    const query = normalizeTextKey(supportedUnitsSearchEl?.value || "");
    const filtered = query
      ? units.filter((unit) => normalizeTextKey(`${unit.name} ${unit.code} ${unit.type}`).includes(query))
      : units;
    supportedUnitsListEl.innerHTML = filtered.map((unit) => `
      <li>
        <strong>${escapeHtml(unit.name || unit.code || "Birim")}</strong>
        <span>${escapeHtml(unit.type || "unit")} · ${escapeHtml(unit.status || "active")}</span>
      </li>
    `).join("");
  }

  supportedUnitsSearchEl?.addEventListener("input", () => {
    updateSupportedUnitsPanel(currentRegion);
  });

  function updateCityPanel(region) {
    if (!citySelectEl || !cityInfoEl) return;
    const cities = buildCoverageCities(region);
    citySelectEl.innerHTML = cities.map((city) => `<option value="${escapeHtml(city.slug)}">${escapeHtml(city.name)}</option>`).join("");
    const coverage = normalizeParcelCoverageConfig(region);
    cityInfoEl.textContent = coverage.message || `${region?.city || region?.name || "Bolge"} kapsami aktif.`;
    if (freeCoverageInfoEl) {
      freeCoverageInfoEl.textContent = coverage.freeParcelLimit > 0
        ? `Ucretsiz goruntuleme limiti: ${formatNumber(coverage.freeParcelLimit)}`
        : "Bu bolge icin kapsam hazir.";
    }
    updateCoverageCitiesPanel(region);
    updateSupportedUnitsPanel(region);
  }

  function normalizeSources(value) {
    if (!Array.isArray(value)) return [];
    return value.map((item) => ({
      id: item.id || normalizeTextKey(item.name || "source"),
      name: item.name || item.id || "Source",
      url: item.url || "",
      reliability: item.reliability || "medium",
      date: item.date || item.updated_at || "",
    }));
  }

  function normalizeLandEvidenceSource(record) {
    const sources = normalizeSources(record.sources || record.evidence_sources || record.source_refs || []);
    if (sources.length) return sources;
    const sourceName = record.source || record.source_name || record.provider || record.dataset || "";
    if (!sourceName) return [];
    return [{
      id: normalizeTextKey(sourceName),
      name: sourceName,
      url: record.source_url || record.url || "",
      reliability: record.source_reliability || record.reliability || "medium",
      date: record.source_date || record.date || record.updated_at || "",
    }];
  }

  function normalizeLandRecord(record = {}, layerType = "unknown") {
    const props = record.properties || record;
    const saleDate = normalizeSaleDate(getPropertyValue(props, ["sale_date", "date", "transaction_date", "listed_date", "updated_at"], ""));
    const price = Number(getPropertyValue(props, ["price", "sale_price", "asking_price", "amount", "value"], 0));
    return {
      id: getLandSourceRecordId(props) || normalizeTextKey(`${layerType}-${getParcelReference(props)}-${saleDate}-${price}`),
      parcel_ref: getParcelReference(props),
      layer_type: layerType,
      status: getPropertyValue(props, ["status", "listing_status", "classification", "sale_ready"], "unknown"),
      title: getPropertyValue(props, ["title", "name", "address", "site_name"], `${layerType} evidence`),
      address: getPropertyValue(props, ["address", "site_address", "location"], ""),
      price,
      area_ha: Number(getPropertyValue(props, ["area_ha", "hectares", "area"], 0)),
      date: saleDate,
      confidence: Number(getPropertyValue(props, ["confidence", "confidence_score", "score"], 0)),
      sources: normalizeLandEvidenceSource(props),
      raw: props,
    };
  }

  function normalizeLandApiResponse(data, layerType = "unknown") {
    if (!data) return [];
    const records = Array.isArray(data) ? data : (Array.isArray(data.records) ? data.records : (Array.isArray(data.features) ? data.features : []));
    return records.map((record) => normalizeLandRecord(record, layerType));
  }

  const landDataState = {
    officialSale: [],
    historicSales: [],
    brownfield: [],
    market: [],
    loaded: false,
    errors: [],
  };

  async function fetchLandRecords(endpoint, layerType) {
    if (!endpoint) return [];
    const url = `${landIntelligenceApiBaseUrl}${endpoint}`;
    const result = await fetchJsonWithTimeout(url, {
      label: `${layerType} records`,
      fallback: [],
      backoffGroup: `land-${layerType}`,
    });
    if (!result.ok) {
      landDataState.errors.push(result.error);
      return [];
    }
    return normalizeLandApiResponse(result.data, layerType);
  }

  async function loadLandIntelligenceData() {
    if (landDataState.loaded) return landDataState;
    const topics = Array.isArray(config.landIntelligenceTopics) ? config.landIntelligenceTopics : [];
    const getEndpoint = (topicId) => topics.find((topic) => topic.id === topicId)?.endpoint || "";
    const [officialSale, historicSales, brownfield, market] = await Promise.all([
      fetchLandRecords(getEndpoint("official-sale"), "official-sale"),
      fetchLandRecords(getEndpoint("historic-sales"), "historic-sales"),
      fetchLandRecords(getEndpoint("brownfield"), "brownfield"),
      fetchLandRecords(getEndpoint("market"), "market"),
    ]);
    landDataState.officialSale = officialSale;
    landDataState.historicSales = historicSales;
    landDataState.brownfield = brownfield;
    landDataState.market = market;
    landDataState.loaded = true;
    return landDataState;
  }

  function filterLandRecords(records, filters = {}) {
    const minConfidence = Number(filters.minConfidence ?? 0);
    const source = normalizeTextKey(filters.source || "all");
    const status = normalizeTextKey(filters.status || "all");
    const reviewOnly = Boolean(filters.reviewOnly);
    return records.filter((record) => {
      if (record.confidence < minConfidence) return false;
      if (source !== "all" && !record.sources.some((item) => normalizeTextKey(item.name).includes(source))) return false;
      if (status !== "all" && normalizeTextKey(record.status) !== status) return false;
      if (reviewOnly && !isPositiveSaleReadyEvidence(record.raw)) return false;
      return true;
    });
  }

  function getAllLandRecords() {
    return [
      ...landDataState.officialSale,
      ...landDataState.historicSales,
      ...landDataState.brownfield,
      ...landDataState.market,
    ];
  }

  function buildLandSummary(records) {
    const total = records.length;
    const ready = records.filter((record) => isPositiveSaleReadyEvidence(record.raw)).length;
    const avgConfidence = total
      ? records.reduce((sum, record) => sum + Number(record.confidence || 0), 0) / total
      : 0;
    return { total, ready, avgConfidence };
  }

  function buildSourceList(records) {
    const map = new Map();
    records.forEach((record) => {
      record.sources.forEach((source) => {
        const key = normalizeTextKey(source.name || source.id);
        if (!key) return;
        const current = map.get(key) || { name: source.name, count: 0 };
        current.count += 1;
        map.set(key, current);
      });
    });
    return Array.from(map.values()).sort((a, b) => b.count - a.count);
  }

  function buildLandSourceFilterOptions(records) {
    const sources = buildSourceList(records);
    return `<option value="all">Tum kaynaklar</option>${sources.map((source) => `<option value="${escapeHtml(source.name)}">${escapeHtml(source.name)} (${source.count})</option>`).join("")}`;
  }

  function buildLandEvidenceTable(records) {
    if (!records.length) {
      return `<div class="empty-state">Bu filtrelerle kayit bulunamadi.</div>`;
    }
    return `
      <div class="evidence-table">
        <table>
          <thead>
            <tr>
              <th>Katman</th>
              <th>Parsel</th>
              <th>Durum</th>
              <th>Deger</th>
              <th>Guven</th>
              <th>Kaynak</th>
            </tr>
          </thead>
          <tbody>
            ${records.slice(0, 60).map((record) => `
              <tr>
                <td>${escapeHtml(getTopicStatusLabel(record.layer_type))}</td>
                <td>${escapeHtml(record.parcel_ref || "-")}</td>
                <td>${escapeHtml(record.status || "-")}</td>
                <td>${record.price ? escapeHtml(formatCurrency(record.price)) : escapeHtml(formatNumber(record.area_ha, 2) + " ha")}</td>
                <td>${escapeHtml(formatPercent(record.confidence, 0))}</td>
                <td>${escapeHtml(record.sources[0]?.name || "-")}</td>
              </tr>`).join("")}
          </tbody>
        </table>
      </div>`;
  }

  function renderLandIntelligenceDashboard(records) {
    if (!workspaceContentEl) return;
    const summary = buildLandSummary(records);
    const filtered = filterLandRecords(records, {
      minConfidence: landMinConfidenceEl?.value || 0,
      source: brownfieldSourceFilterEl?.value || "all",
      status: listingStatusFilterEl?.value || "all",
      reviewOnly: landReviewOnlyEl?.checked || false,
    });
    const filterOptions = buildLandSourceFilterOptions(records);
    setSanitizedHtml(workspaceContentEl, `
      <section class="land-intelligence-panel">
        <div class="panel-header-row">
          <div>
            <p class="eyebrow">Arazi Degeri</p>
            <h3>Kanita dayali satis hazirligi</h3>
            <p>Resmi satis, gecmis satis, brownfield ve pazar sinyalleri tek tabloda.</p>
          </div>
          <button type="button" id="landDashboardRefresh" class="pill-btn">Yenile</button>
        </div>
        <div class="score-cards">
          <div><strong>${formatNumber(summary.total)}</strong><span>Toplam kayit</span></div>
          <div><strong>${formatNumber(summary.ready)}</strong><span>Satisa yakin</span></div>
          <div><strong>${formatPercent(summary.avgConfidence, 0)}</strong><span>Ortalama guven</span></div>
        </div>
        <div class="land-filter-row">
          <label>Kaynak
            <select id="landSourceInlineFilter">${filterOptions}</select>
          </label>
          <label>Durum
            <select id="landStatusInlineFilter">
              <option value="all">Tum durumlar</option>
              <option value="active">active</option>
              <option value="sold">sold</option>
              <option value="ready">ready</option>
            </select>
          </label>
        </div>
        ${buildLandEvidenceTable(filtered)}
      </section>`);
  }

  async function ensureLandIntelligenceDashboard() {
    const data = await loadLandIntelligenceData();
    renderLandIntelligenceDashboard(getAllLandRecords());
    return data;
  }

  const map = new maplibregl.Map({
    container: "map",
    style: "https://demotiles.maplibre.org/style.json",
    center: [-1.8904, 52.4862],
    zoom: 10.6,
  });

  map.addControl(new maplibregl.NavigationControl({ showCompass: true }), "top-right");

  map.on("load", () => {
    showStatus("Harita hazir.", false);
  });

  const state = {
    activeRegionSlug: config.defaultRegion || config.regions[0]?.slug || "",
    source: null,
    selectedFeatureId: null,
    selectedParcelRef: null,
    selectedFeatureProps: null,
    comparison: { baseline: null, scenario: null },
    overlays: {
      poiPoints: true,
      poiLines: true,
      topography: false,
      futureGrowth: false,
      facilities: false,
      officialSale: false,
      historicSales: false,
      brownfield: false,
      market: false,
    },
    cityFilter: "all",
    saleReadyQuickFilter: "all",
    marketListingStatus: "all",
    brownfieldSource: "all",
    landReviewOnly: false,
  };

  let currentRegion = regionMap.get(state.activeRegionSlug) || config.regions[0];
  let currentGeoJson = null;
  let currentIsochrone = null;
  let topographyOverlayState = null;
  let futureGrowthLayerState = null;
  let facilitiesLayerState = null;
  let officialSaleLayerState = null;
  let historicSalesLayerState = null;
  let brownfieldLayerState = null;
  let marketLayerState = null;

  function showStatus(message, sticky = true) {
    if (!statusEl) return;
    statusEl.textContent = message;
    statusEl.classList.toggle("is-sticky", sticky);
  }

  function setCoverageStatus(region) {
    if (!coverageStateEl) return;
    const coverage = normalizeParcelCoverageConfig(region);
    coverageStateEl.textContent = coverage.label;
    coverageStateEl.dataset.mode = coverage.mode;
  }

  function setDebugBadge(text) {
    if (!debugBadgeEl) return;
    debugBadgeEl.textContent = text;
  }

  function buildFeatureId(feature) {
    return String(feature.id ?? feature.properties?.id ?? feature.properties?.parcel_id ?? feature.properties?.parcel_ref ?? "");
  }

  function getParcelDisplayName(props = {}) {
    return getPropertyValue(props, ["parcel_ref", "parcel_id", "title_number", "address"], "Secili parsel");
  }

  function updateSelectedParcelInfo(props = {}) {
    if (!selectedParcelEl) return;
    selectedParcelEl.textContent = getParcelDisplayName(props);
  }

  function buildParcelPopupContent(props = {}) {
    const gasHtml = buildGasEmissionsPopupMetaHtml(props);
    const baseRows = buildInfoRows([
      ["Parsel", getParcelDisplayName(props)],
      ["Alan", props.area_ha ? `${formatNumber(props.area_ha, 2)} ha` : ""],
      ["Skor", props.score ? formatNumber(props.score, 0) : ""],
      ["Durum", props.status || props.classification || ""],
      ["Kaynak", props.source || props.dataset || ""],
    ]);
    return `
      <div class="parcel-popup">
        <h3>${escapeHtml(getParcelDisplayName(props))}</h3>
        ${baseRows}
        ${gasHtml}
      </div>`;
  }

  function selectFeature(feature, lngLat) {
    const featureId = buildFeatureId(feature);
    state.selectedFeatureId = featureId;
    state.selectedParcelRef = getParcelReference(feature.properties || {});
    state.selectedFeatureProps = feature.properties || {};
    updateSelectedParcelInfo(feature.properties || {});
    const coordinates = lngLat || getGeometryCentroid(feature.geometry) || map.getCenter();
    new maplibregl.Popup({ closeButton: true, closeOnClick: true })
      .setLngLat(coordinates)
      .setHTML(buildParcelPopupContent(feature.properties || {}))
      .addTo(map);
  }

  function updateRenderMode(mode) {
    if (!renderModeEl) return;
    renderModeEl.textContent = mode;
  }

  function getRegionSourceId(region) {
    return `region-${region.slug}-parcels`;
  }

  function getRegionLayerIds(region) {
    const slug = region.slug;
    return {
      fill: `region-${slug}-fill`,
      line: `region-${slug}-line`,
      selected: `region-${slug}-selected`,
    };
  }

  function buildParcelFillColorExpression() {
    return [
      "case",
      ["==", ["get", "sale_ready"], true], "#22c55e",
      [">=", ["coalesce", ["to-number", ["get", "score"]], 0], 80], "#16a34a",
      [">=", ["coalesce", ["to-number", ["get", "score"]], 0], 60], "#f59e0b",
      "#3b82f6",
    ];
  }

  async function loadRegionGeoJson(region) {
    if (!region?.geojsonUrl) return null;
    const result = await fetchJsonWithTimeout(region.geojsonUrl, {
      label: `${region.name || region.slug} parsel`,
      fallback: null,
      backoffGroup: `region-${region.slug}`,
      dedupeKey: region.geojsonUrl,
    });
    if (!result.ok) {
      showThrottledStatus(`region-${region.slug}`, result.error || "Parsel verisi yuklenemedi");
      return null;
    }
    return result.data;
  }

  async function renderRegion(region) {
    if (!region) return;
    currentRegion = region;
    setCoverageStatus(region);
    updateCityPanel(region);
    setDebugBadge(region.name || region.slug);
    if (activeRegionEl) activeRegionEl.textContent = region.name || region.slug;
    const sourceId = getRegionSourceId(region);
    const layerIds = getRegionLayerIds(region);
    const geojson = await loadRegionGeoJson(region);
    currentGeoJson = geojson;
    if (!geojson) return;

    if (map.getSource(sourceId)) {
      map.getSource(sourceId).setData(geojson);
    } else {
      map.addSource(sourceId, { type: "geojson", data: geojson });
      map.addLayer({
        id: layerIds.fill,
        type: "fill",
        source: sourceId,
        paint: {
          "fill-color": buildParcelFillColorExpression(),
          "fill-opacity": 0.36,
        },
      });
      map.addLayer({
        id: layerIds.line,
        type: "line",
        source: sourceId,
        paint: {
          "line-color": "#0f172a",
          "line-width": 0.7,
          "line-opacity": 0.35,
        },
      });
      map.addLayer({
        id: layerIds.selected,
        type: "line",
        source: sourceId,
        paint: {
          "line-color": "#f97316",
          "line-width": 2.4,
        },
        filter: ["==", ["id"], ""],
      });
      map.on("click", layerIds.fill, async (event) => {
        const feature = event.features?.[0];
        if (feature) {
          await ensureGasEmissionsPopupLookupLoaded();
          selectFeature(feature, event.lngLat);
        }
      });
      map.on("mouseenter", layerIds.fill, () => { map.getCanvas().style.cursor = "pointer"; });
      map.on("mouseleave", layerIds.fill, () => { map.getCanvas().style.cursor = ""; });
    }

    const bounds = new maplibregl.LngLatBounds();
    geojson.features?.forEach((feature) => {
      const centroid = getGeometryCentroid(feature.geometry);
      if (centroid) bounds.extend(centroid);
    });
    if (!bounds.isEmpty()) {
      map.fitBounds(bounds, { padding: 60, maxZoom: 13, duration: 600 });
    }
    updateRenderMode("Parsel");
    showStatus(formatCoverageSummary(region, geojson), false);
  }

  function updateScenarioControls() {
    const mode = scenarioScoreModeEl?.value || "balanced";
    if (parcelThresholdEl) parcelThresholdEl.textContent = mode;
    if (poiThresholdEl) poiThresholdEl.textContent = mode;
  }

  scenarioScoreModeEl?.addEventListener("change", updateScenarioControls);

  regionSelectEl?.addEventListener("change", async (event) => {
    const next = regionMap.get(event.target.value);
    if (next) await renderRegion(next);
  });

  baseMapSelectEl?.addEventListener("change", () => {
    showStatus("Altlik harita degistirme bu demo profilinde pasif.", false);
  });

  mapViewModeEl?.addEventListener("change", () => {
    updateRenderMode(mapViewModeEl.value || "Parsel");
  });

  showPoiPointsEl?.addEventListener("change", () => {
    state.overlays.poiPoints = showPoiPointsEl.checked;
  });

  showPoiLinesEl?.addEventListener("change", () => {
    state.overlays.poiLines = showPoiLinesEl.checked;
  });

  showTopographyOverlayEl?.addEventListener("change", () => {
    state.overlays.topography = showTopographyOverlayEl.checked;
  });

  showFutureGrowthEl?.addEventListener("change", () => {
    state.overlays.futureGrowth = showFutureGrowthEl.checked;
  });

  showFacilitiesOverlayEl?.addEventListener("change", () => {
    state.overlays.facilities = showFacilitiesOverlayEl.checked;
  });

  showOfficialSaleEl?.addEventListener("change", () => {
    state.overlays.officialSale = showOfficialSaleEl.checked;
  });

  showHistoricSalesEl?.addEventListener("change", () => {
    state.overlays.historicSales = showHistoricSalesEl.checked;
  });

  showBrownfieldSignalsEl?.addEventListener("change", () => {
    state.overlays.brownfield = showBrownfieldSignalsEl.checked;
  });

  showMarketListingsEl?.addEventListener("change", () => {
    state.overlays.market = showMarketListingsEl.checked;
  });

  landMinConfidenceEl?.addEventListener("input", () => {
    if (landMinConfidenceValueEl) landMinConfidenceValueEl.textContent = `${landMinConfidenceEl.value}%`;
  });

  resetLandFiltersEl?.addEventListener("click", () => {
    if (landMinConfidenceEl) landMinConfidenceEl.value = "0";
    if (landMinConfidenceValueEl) landMinConfidenceValueEl.textContent = "0%";
    if (brownfieldSourceFilterEl) brownfieldSourceFilterEl.value = "all";
    if (listingStatusFilterEl) listingStatusFilterEl.value = "all";
    if (landReviewOnlyEl) landReviewOnlyEl.checked = false;
  });

  jumpNearestSaleBtnEl?.addEventListener("click", async () => {
    const data = await ensureLandIntelligenceDashboard();
    const first = getAllLandRecords()[0];
    if (!first) {
      showStatus("Satis kaydi bulunamadi.", false);
      return;
    }
    showStatus(`Ilk kanit kaydi: ${first.title}`, false);
  });

  function populateRegionSelect() {
    if (!regionSelectEl) return;
    regionSelectEl.innerHTML = config.regions.map((region) => `
      <option value="${escapeHtml(region.slug)}" ${region.slug === state.activeRegionSlug ? "selected" : ""}>${escapeHtml(region.name || region.slug)}</option>
    `).join("");
  }

  function maybeRenderInitialPanel() {
    renderLandIntelligencePanel();
  }

  populateRegionSelect();
  updateScenarioControls();
  maybeRenderInitialPanel();
  map.on("load", async () => {
    await renderRegion(currentRegion);
  });
})();
