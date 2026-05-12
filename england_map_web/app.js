(async function () {
  const configUrl = new URL(window.AAYS_CONFIG_URL || "./config/regions.local.json", window.location.href);
  configUrl.searchParams.set("v", "20260429-proxy-parcels-v22");
  const statusEl = document.getElementById("status");
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

  const TURKISH_MOJIBAKE_REPLACEMENTS = [
    ["Ãƒâ€¡", "Ã‡"],
    ["ÃƒÂ§", "Ã§"],
    ["Ãƒâ€“", "Ã–"],
    ["ÃƒÂ¶", "Ã¶"],
    ["ÃƒÅ“", "Ãœ"],
    ["ÃƒÂ¼", "Ã¼"],
    ["Ã„Â°", "Ä°"],
    ["Ã„Â±", "Ä±"],
    ["Ã…Å¾", "Å"],
    ["Ã…Å¸", "ÅŸ"],
    ["Ã„Å¾", "Ä"],
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

    const controller = new AbortController();
    const timer = window.setTimeout(() => controller.abort(), timeoutMs);
    try {
      const response = await fetch(url, { signal: controller.signal });
      window.clearTimeout(timer);
      if (!response.ok) {
        let detail = "";
        try {
          detail = (await response.text()).trim();
        } catch (_error) {
          detail = "";
        }
        const statusMessage = `${label}: HTTP ${response.status}${detail ? ` - ${detail.slice(0, 120)}` : ""}`;
        markApiFailure(backoffGroup, response.status >= 500);
        return {
          ok: false,
          data: fallbackData,
          error: statusMessage,
        };
      }
      const data = await response.json();
      markApiSuccess(backoffGroup);
      return {
        ok: true,
        data,
        error: null,
      };
    } catch (error) {
      window.clearTimeout(timer);
      const isAbort = error?.name === "AbortError";
      markApiFailure(backoffGroup, true);
      return {
        ok: false,
        data: fallbackData,
        error: isAbort
          ? `${label}: istek zaman asimina ugradi (${Math.round(timeoutMs / 1000)}s)`
          : normalizeFetchError(error, label),
      };
    }
  }

  const COVERAGE_STATUS_ORDER = ["direct", "qa_direct_hit", "qa_snapped_hit", "qa_nearby_only"];
  const COVERAGE_STATUS_LABELS = {
    direct: "Direct",
    qa_direct_hit: "QA Direct",
    qa_snapped_hit: "QA Snap",
    qa_nearby_only: "QA Near",
  };
  const COVERAGE_GROUP_LABELS = {
    direct: "Direct ve Calisan",
    qa_direct_hit: "QA-backed Direct Hit",
    qa_snapped_hit: "QA-backed Snapped Parcel",
    qa_nearby_only: "QA-backed Nearest Parcel",
  };
  const TOPOGRAPHY_SOURCE_ID = "topography-overlay";
  const TOPOGRAPHY_LAYER_ID = "topography-overlay";
  const TOPOGRAPHY_CONTROL_MODE = "__topography_overlay_toggle__";
  const FUTURE_GROWTH_SOURCE_ID = "future-growth-layer";
  const FUTURE_GROWTH_FILL_LAYER_ID = "future-growth-fill";
  const FUTURE_GROWTH_LINE_LAYER_ID = "future-growth-line";
  const FUTURE_GROWTH_POINT_LAYER_ID = "future-growth-point";
  const FUTURE_GROWTH_VECTOR_SOURCE_ID = "future-growth-vector";
  const FUTURE_GROWTH_VECTOR_LAYER_ID = "future-growth-vector-line";
  const FUTURE_GROWTH_CONTROL_MODE = "__future_growth_toggle__";
  const HISTORY_CONTROL_MODE = "__historic_sales_toggle__";
  const SECURITY_CONTROL_MODE = "__security_overlay_toggle__";
  const MAP_MODE_VISIBILITY_STORAGE_KEY = "aays.mapMode.visibleModes.v1";
  const MAP_VIEW_STATE_STORAGE_KEY = "aays.map.lastView.v1";
  const PRESERVE_VIEW_ON_LAYER_TOGGLE = config.preserveViewOnLayerToggle !== false;
  const SHOW_DEBUG_BADGE = Boolean(config.showDebugBadge);

  function mergeTopographyOverlayConfig(baseConfig, overrideConfig) {
    const base = baseConfig && typeof baseConfig === "object" ? baseConfig : {};
    const override = overrideConfig && typeof overrideConfig === "object" ? overrideConfig : {};
    return { ...base, ...override };
  }

  function normalizeTopographyOverlayConfig(rawConfig) {
    const raw = rawConfig && typeof rawConfig === "object" ? rawConfig : {};
    const sourceType = String(raw.sourceType || "raster").toLowerCase() === "raster-dem" ? "raster-dem" : "raster";
    const tileSize = Number(raw.tileSize);
    const minzoom = Number(raw.minzoom);
    const maxzoom = Number(raw.maxzoom);
    const opacity = Number(raw.opacity);
    const contrast = Number(raw.contrast);
    const saturation = Number(raw.saturation);
    const exaggeration = Number(raw.exaggeration);
    const tiles = Array.isArray(raw.tiles)
      ? raw.tiles.map((item) => String(item || "").trim()).filter(Boolean)
      : [];
    return {
      enabled: raw.enabled !== false,
      defaultVisible: Boolean(raw.defaultVisible),
      sourceType,
      tiles,
      url: String(raw.url || "").trim(),
      encoding: String(raw.encoding || "terrarium").toLowerCase(),
      tileSize: Number.isFinite(tileSize) ? tileSize : 256,
      minzoom: Number.isFinite(minzoom) ? minzoom : 0,
      maxzoom: Number.isFinite(maxzoom) ? maxzoom : 15,
      opacity: Number.isFinite(opacity) ? Math.max(0.05, Math.min(opacity, 1)) : 0.4,
      contrast: Number.isFinite(contrast) ? Math.max(-1, Math.min(contrast, 1)) : 0.08,
      saturation: Number.isFinite(saturation) ? Math.max(-1, Math.min(saturation, 1)) : 0.15,
      exaggeration: Number.isFinite(exaggeration) ? Math.max(0.05, Math.min(exaggeration, 2.5)) : 0.55,
      insertBeforeLayerId: String(raw.insertBeforeLayerId || "").trim() || null,
      label: String(raw.label || "Topografya"),
      attribution: String(raw.attribution || "").trim(),
    };
  }

  function toDisplayCityName(rawLabel) {
    if (!rawLabel) return "";
    let label = rawLabel;
    if (label === "City of Westminster" || label === "City of London Corporation") {
      return "London";
    }
    [
      " City and District Council",
      " Metropolitan District Council",
      " County Borough Council",
      " City Council",
      " Council",
    ].forEach((suffix) => {
      if (label.endsWith(suffix)) {
        label = label.slice(0, -suffix.length);
      }
    });
    if (label.startsWith("City of ")) {
      label = label.slice("City of ".length);
    }
    return label.trim();
  }

  function normalizeText(value) {
    return String(value || "").toLocaleLowerCase("tr-TR");
  }

  function toDisplayAuthorityName(rawLabel) {
    return String(rawLabel || "").trim();
  }

  function updateFreeCoverageInfo() {
    if (!freeCoverageInfoEl) return;
    if (!coverageIndex) {
      setSanitizedText(freeCoverageInfoEl, "Great Britain live coverage var. Northern Ireland icin esdeger free bulk parcel kaynagi henuz dogrulanmadi.");
      return;
    }
    const summary = coverageIndex.source_summary || {};
    const cityRecords = coverageIndex.city_records || [];
    const directCount = cityRecords.filter((city) => city.status === "direct").length;
    const qaCount = cityRecords.filter((city) => String(city.status || "").startsWith("qa_")).length;
    const niStatus = summary.northern_ireland_bulk_free_status === "unresolved_or_not_equivalent"
      ? "Northern Ireland henuz free bulk kapsamda degil."
      : "Northern Ireland free bulk statusi guncellendi.";
    setSanitizedHtml(freeCoverageInfoEl, [
      `<strong>Canli scope:</strong> ${coverageIndex.scope || "Great Britain"}.`,
      `<strong>Kaynak birimi:</strong> ${summary.total_supported_source_units || 0}.`,
      `<strong>Sehir durumu:</strong> ${directCount} direct, ${qaCount} QA destekli.`,
      `<strong>Not:</strong> ${niStatus}`,
    ].join("<br />"));
  }

  function renderCoverageCityList() {
    if (!coverageCitiesListEl || !coverageCitiesSummaryEl) return;
    if (!coverageIndex || !Array.isArray(coverageIndex.city_records)) {
      setSanitizedText(coverageCitiesSummaryEl, "Sehir kapsam raporu yuklenemedi.");
      setSanitizedHtml(coverageCitiesListEl, "");
      return;
    }

    const cityRecords = coverageIndex.city_records;
    const statusCounts = cityRecords.reduce((acc, record) => {
      const key = String(record.status || "unknown");
      acc[key] = (acc[key] || 0) + 1;
      return acc;
    }, {});
    setSanitizedHtml(coverageCitiesSummaryEl, [
      `<strong>Toplam:</strong> ${cityRecords.length} sehir`,
      `<strong>Direct:</strong> ${statusCounts.direct || 0}`,
      `<strong>QA:</strong> ${(statusCounts.qa_direct_hit || 0) + (statusCounts.qa_snapped_hit || 0) + (statusCounts.qa_nearby_only || 0)}`,
    ].join("<br />"));

    const groups = COVERAGE_STATUS_ORDER
      .map((status) => ({
        status,
        items: cityRecords.filter((record) => String(record.status || "") === status),
      }))
      .filter((group) => group.items.length > 0);

    setSanitizedHtml(coverageCitiesListEl, groups
      .map((group) => {
        const itemsHtml = group.items
          .sort((a, b) => toDisplayCityName(a.city_label).localeCompare(toDisplayCityName(b.city_label)))
          .map((record) => {
            const name = toDisplayCityName(record.city_label);
            const meta = `${record.country} - ${(record.live_regions || []).join(", ")}`;
            return `
              <button class="coverage-item" type="button" data-city="${name}">
                <div class="coverage-item-main">
                  <div class="coverage-item-name">${name}</div>
                  <div class="coverage-item-meta">${meta}</div>
                </div>
                <div class="coverage-badge" data-status="${record.status}">${COVERAGE_STATUS_LABELS[record.status] || record.status}</div>
              </button>
            `;
          })
          .join("");
        return `
          <div class="coverage-group">
            <div class="coverage-group-title">${COVERAGE_GROUP_LABELS[group.status] || group.status}</div>
            ${itemsHtml}
          </div>
        `;
      })
      .join(""));

    coverageCitiesListEl.querySelectorAll("[data-city]").forEach((buttonEl) => {
      buttonEl.addEventListener("click", async () => {
        const city = cityFocusMap.get(buttonEl.getAttribute("data-city"));
        if (!city) return;
        await focusCity(city);
      });
    });
  }

  async function focusCoverageRecord(record) {
    if (!record) return;
    const normalizedAuthority = toDisplayCityName(record.authority);
    const city = cityFocusMap.get(normalizedAuthority);
    if (city) {
      await focusCity(city);
      return;
    }
    const regionSlug = (record.live_regions || [])[0];
    const region = regionMap.get(regionSlug);
    if (!region) return;
    if (citySelectEl) {
      citySelectEl.value = "__NONE__";
    }
    updateCityInfo(null);
    await switchRegion(region, "manual");
    map.easeTo({ center: [region.center[1], region.center[0]], zoom: 10.8 });
    showStatus(`${record.authority} kapsami ${region.label} bolgesi icinde gosterildi.`, true);
  }

  function renderSupportedUnitsList(filterText = "") {
    if (!supportedUnitsListEl || !supportedUnitsSummaryEl) return;
    if (!coverageIndex || !Array.isArray(coverageIndex.records)) {
      setSanitizedText(supportedUnitsSummaryEl, "Destekli birim listesi yuklenemedi.");
      setSanitizedHtml(supportedUnitsListEl, "");
      return;
    }

    const filter = normalizeText(filterText);
    const allRecords = coverageIndex.records;
    const filtered = !filter
      ? allRecords
      : allRecords.filter((record) => {
          const haystack = [
            record.authority,
            record.country,
            record.assignment_group,
            ...(record.live_regions || []),
          ]
            .map((value) => normalizeText(value))
            .join(" ");
          return haystack.includes(filter);
        });

    const countsByCountry = filtered.reduce((acc, record) => {
      const key = String(record.country || "unknown");
      acc[key] = (acc[key] || 0) + 1;
      return acc;
    }, {});

    setSanitizedHtml(supportedUnitsSummaryEl, [
      `<strong>Eslesen:</strong> ${filtered.length} / ${allRecords.length}`,
      `<strong>England:</strong> ${countsByCountry.england || 0}`,
      `<strong>Wales:</strong> ${countsByCountry.wales || 0}`,
      `<strong>Scotland:</strong> ${countsByCountry.scotland || 0}`,
    ].join("<br />"));

    const countries = ["england", "wales", "scotland"];
    setSanitizedHtml(supportedUnitsListEl, countries
      .map((country) => {
        const items = filtered
          .filter((record) => String(record.country || "") === country)
          .sort((a, b) => toDisplayAuthorityName(a.authority).localeCompare(toDisplayAuthorityName(b.authority)));
        if (!items.length) return "";
        const countryTitle = country.charAt(0).toUpperCase() + country.slice(1);
        const itemsHtml = items
          .map((record) => {
            const meta = `${record.source_unit_type} - ${(record.live_regions || []).join(", ")}`;
            const key = encodeURIComponent(record.authority);
            return `
              <button class="coverage-item" type="button" data-authority="${key}">
                <div class="coverage-item-main">
                  <div class="coverage-item-name">${toDisplayAuthorityName(record.authority)}</div>
                  <div class="coverage-item-meta">${meta}</div>
                </div>
                <div class="coverage-badge" data-status="direct">${countryTitle}</div>
              </button>
            `;
          })
          .join("");
        return `
          <div class="coverage-group">
            <div class="coverage-group-title">${countryTitle}</div>
            ${itemsHtml}
          </div>
        `;
      })
      .join(""));

    const recordMap = new Map(filtered.map((record) => [encodeURIComponent(record.authority), record]));
    supportedUnitsListEl.querySelectorAll("[data-authority]").forEach((buttonEl) => {
      buttonEl.addEventListener("click", async () => {
        const record = recordMap.get(buttonEl.getAttribute("data-authority"));
        if (!record) return;
        await focusCoverageRecord(record);
      });
    });
  }

  function renderScreenMenu() {
    if (!screenMenuEl) return;
    setSanitizedHtml(screenMenuEl, WORKSPACE_SCREENS.map(
      (screen) =>
        `<button class="screen-menu-item" type="button" data-screen="${screen.id}" data-active="${screen.id === activeWorkspaceScreen}">${screen.label}</button>`
    ).join(""));
    screenMenuEl.querySelectorAll("[data-screen]").forEach((buttonEl) => {
      buttonEl.addEventListener("click", () => {
        activeWorkspaceScreen = buttonEl.getAttribute("data-screen");
        renderWorkspace();
      });
    });
  }

  function renderScenarioCards(parcel, scenarios) {
    return scenarios
      .map(
        (scenario) => `
          <div class="scenario-card">
            <div class="scenario-title">${scenario.name}</div>
            <div class="scenario-meta">
              ROI: ${formatNumber(scenario.roiPct, 1)}% Ã‚Â· IRR: ${formatNumber(scenario.irrPct, 1)}%<br />
              Gelir: ${formatMoney(scenario.revenue)} Ã‚Â· Maliyet: ${formatMoney(scenario.totalCost)}
            </div>
          </div>
        `
      )
      .join("");
  }

  function getParcelCompareKey(parcel) {
    return `${parcel.regionSlug || parcel.regionLabel || "region"}::${parcel.ref}`;
  }

  function isParcelCompared(parcel) {
    if (!parcel) return false;
    const key = getParcelCompareKey(parcel);
    return comparedParcels.some((item) => item.key === key);
  }

  function getComparedParcelByKey(key) {
    return comparedParcels.find((item) => item.key === key) || null;
  }

  function buildComparedParcelEntry(feature) {
    const parcel = getParcelModelFromFeature(feature);
    if (!parcel) return null;
    const insights = buildParcelInsights(parcel);
    const best = bestScenario(parcel);
    return {
      key: getParcelCompareKey(parcel),
      ref: parcel.ref,
      regionLabel: parcel.regionLabel,
      regionSlug: parcel.regionSlug,
      areaM2: parcel.areaM2,
      landCost: parcel.landCost,
      perimeterM: parcel.perimeterM,
      slopePct: parcel.slopePct,
      emptyLandSignal: parcel.emptyLandSignal,
      bestScenario: best
        ? {
            name: best.name,
            roiPct: best.roiPct,
            irrPct: best.irrPct,
            totalCost: best.totalCost,
            revenue: best.revenue,
          }
        : null,
      primaryUnits: insights.primaryUnits,
      nearbyUnits: insights.nearbyUnits.slice(0, 6),
      feature: {
        type: "Feature",
        geometry: feature.geometry ? JSON.parse(JSON.stringify(feature.geometry)) : null,
        properties: { ...(feature.properties || {}) },
      },
    };
  }

  function updateComparedParcelsSource() {
    const source = map && map.getSource("compared-parcels");
    if (source && source.setData) {
      source.setData({
        type: "FeatureCollection",
        features: comparedParcels.map((item) => item.feature).filter(Boolean),
      });
    }
  }

  function addComparedParcel(feature) {
    const entry = buildComparedParcelEntry(feature);
    if (!entry) return { changed: false, added: false, removed: false, entry: null };
    const existingIndex = comparedParcels.findIndex((item) => item.key === entry.key);
    if (existingIndex >= 0) {
      return { changed: false, added: false, removed: false, entry: comparedParcels[existingIndex] };
    }
    comparedParcels = [...comparedParcels, entry].slice(-12);
    updateComparedParcelsSource();
    renderWorkspace();
    refreshActiveParcelPopup();
    return { changed: true, added: true, removed: false, entry };
  }

  function removeComparedParcelByKey(key) {
    const existing = getComparedParcelByKey(key);
    if (!existing) return { changed: false, added: false, removed: false, entry: null };
    comparedParcels = comparedParcels.filter((item) => item.key !== key);
    selectedScenarioComparisons = selectedScenarioComparisons.filter((item) => item.key !== key);
    delete scenarioSelectState.manualDrafts[key];
    if (activeComparedParcelKey === key) {
      activeComparedParcelKey = null;
    }
    updateComparedParcelsSource();
    renderWorkspace();
    refreshActiveParcelPopup();
    return { changed: true, added: false, removed: true, entry: existing };
  }

  function toggleComparedParcel(feature) {
    const parcel = getParcelModelFromFeature(feature);
    if (!parcel) return { changed: false, added: false, removed: false, entry: null };
    const key = getParcelCompareKey(parcel);
    return isParcelCompared(parcel) ? removeComparedParcelByKey(key) : addComparedParcel(feature);
  }

  function renderParcelCompareAction(parcel) {
    if (!parcel) return "";
    const compared = isParcelCompared(parcel);
    return `
      <div class="workspace-section">
        <h3 class="workspace-section-title">KarÃ…Å¸Ã„Â±laÃ…Å¸tÃ„Â±rma Ã„Â°Ã…Å¸lemi</h3>
        <div class="workspace-row workspace-action-row">
          <span>${compared ? "Bu parsel karÃ…Å¸Ã„Â±laÃ…Å¸tÃ„Â±rma listesinde." : "Bu parsel henÃƒÂ¼z karÃ…Å¸Ã„Â±laÃ…Å¸tÃ„Â±rma listesinde deÃ„Å¸il."}</span>
          <button
            class="workspace-button"
            type="button"
            data-compare-action="${compared ? "remove" : "add"}"
            data-compare-key="${encodeURIComponent(getParcelCompareKey(parcel))}"
          >${compared ? "- Listeden Ãƒâ€¡Ã„Â±kar" : "+ Listeye Ekle"}</button>
        </div>
      </div>
    `;
  }

  function renderComparedParcelsList(includeRemoveButton = true) {
    if (!comparedParcels.length) {
      return '<div class="workspace-empty">Haritadan bir parcel seÃƒÂ§. AÃƒÂ§Ã„Â±lan + butonuyla karÃ…Å¸Ã„Â±laÃ…Å¸tÃ„Â±rma listesine ekleyebiliriz.</div>';
    }
    return `<div class="workspace-stack">${comparedParcels
      .map((item) => {
        const expanded = activeComparedParcelKey === item.key;
        return `
          <div class="workspace-compare-item" data-expanded="${expanded}">
            <button class="compare-parcel-toggle" type="button" data-compare-select="${encodeURIComponent(item.key)}">
              <div class="workspace-row">
                <span>${item.regionLabel}</span>
              </div>
              <div class="scenario-title">${item.ref}</div>
            </button>
            ${
              expanded
                ? `
                  <div class="compare-parcel-details">
                    ${renderUnitsOverviewSection(item.primaryUnits || [], item.nearbyUnits || [])}
                    ${renderParcelDetailsAccordion(item)}
                    ${
                      item.bestScenario
                        ? `
                          <div class="workspace-section">
                            <h3 class="workspace-section-title">En Ã„Â°yi Senaryo</h3>
                            <div class="workspace-stack">
                              <div class="workspace-row"><span>Senaryo</span><strong>${item.bestScenario.name}</strong></div>
                              <div class="workspace-row"><span>ROI</span><strong>${formatNumber(item.bestScenario.roiPct, 1)}%</strong></div>
                              <div class="workspace-row"><span>IRR</span><strong>${formatNumber(item.bestScenario.irrPct, 1)}%</strong></div>
                              <div class="workspace-row"><span>Maliyet</span><strong>${formatMoney(item.bestScenario.totalCost)}</strong></div>
                            </div>
                          </div>
                        `
                        : ""
                    }
                    ${
                      includeRemoveButton
                        ? `<button class="workspace-button" type="button" data-remove-compare="${encodeURIComponent(item.key)}">Listeden Ãƒâ€¡Ã„Â±kar</button>`
                        : ""
                    }
                  </div>
                `
                : ""
            }
          </div>
        `;
      })
      .join("")}</div>`;
  }

  function clearComparedParcels() {
    if (!comparedParcels.length) return;
    comparedParcels = [];
    activeComparedParcelKey = null;
    selectedScenarioComparisons = [];
    updateComparedParcelsSource();
    renderWorkspace();
    refreshActiveParcelPopup();
  }

  function buildCompareScenarioEntries() {
    if (selectedScenarioComparisons.length) {
      return selectedScenarioComparisons.slice();
    }
    const allowedTypes = WORKSPACE_SCENARIOS.filter((name) => scenarioSelectState.allowedTypes.includes(name));
    return comparedParcels
      .map((item) => {
        const parcelVariant = getPlanningParcelVariant(item);
        const rows = buildScenarioSelectionRows(parcelVariant, allowedTypes, scenarioSelectState.minUtil);
        const preferredName = scenarioSelectState.parcelKey === item.key ? scenarioSelectState.selectedScenarioName : null;
        const scenario = rows.find((row) => row.name === preferredName) || rows[0] || null;
        if (!scenario) return null;
        const factorRows = buildParcelAnalysisFactorRowsFromUnits(item.primaryUnits || [], item.nearbyUnits || []);
        const adjustedSaleMap = computeAdjustedSaleValueMap(factorRows);
        return {
          key: item.key,
          ref: item.ref,
          regionLabel: item.regionLabel,
          areaM2: parcelVariant.areaM2,
          landCost: parcelVariant.landCost,
          primaryUnits: item.primaryUnits || [],
          nearbyUnits: item.nearbyUnits || [],
          slopePct: item.slopePct,
          perimeterM: item.perimeterM,
          emptyLandSignal: item.emptyLandSignal,
          scenario,
          factorRows,
          adjustedSaleMap,
          feature: item.feature,
          selectionId: null,
        };
      })
      .filter(Boolean);
  }

  function renderSelectedScenariosCards(compareEntries) {
    return `
      <div class="compare-chip-grid">
        ${compareEntries
          .map(
            (entry) => `
              <div class="compare-selection-card">
                <div class="compare-selection-title">${entry.ref} Ã‚Â· ${entry.scenario.name}</div>
                <div class="compare-selection-meta">${formatNumber(entry.scenario.usedM2, 0)} mÃ‚Â² Ã‚Â· ROI %${formatNumber(entry.scenario.roiPct, 2)} Ã‚Â· IRR %${formatNumber(entry.scenario.irrPct, 2)}</div>
                ${
                  entry.selectionId
                    ? `<button class="workspace-button" type="button" data-remove-compare-selection="${entry.selectionId}">Senaryoyu KaldÃ„Â±r</button>`
                    : `<button class="workspace-button" type="button" data-remove-compare="${encodeURIComponent(entry.key)}">Parseli KaldÃ„Â±r</button>`
                }
              </div>
            `
          )
          .join("")}
      </div>
    `;
  }

  function renderSelectedParcelsTable(compareEntries) {
    const parcelMap = new Map(compareEntries.map((entry) => [entry.key, entry]));
    const rows = Array.from(parcelMap.values())
      .map(
        (entry) => `
          <tr>
            <td>${entry.ref}</td>
            <td>${entry.ref}</td>
            <td>${formatNumber(entry.areaM2, 0)}</td>
            <td>${formatNumber(entry.landCost, 0)}</td>
          </tr>
        `
      )
      .join("");
    return `
      <div class="workspace-section">
        <h3 class="workspace-section-title">SeÃƒÂ§ilen Parseller</h3>
        <div class="settings-table-wrap">
          <table class="settings-table">
            <thead>
              <tr>
                <th>Parsel</th>
                <th>Parsel ID</th>
                <th>Arsa alanÃ„Â± (mÃ‚Â²)</th>
                <th>Tahmini arsa maliyeti (TRY)</th>
              </tr>
            </thead>
            <tbody>${rows}</tbody>
          </table>
        </div>
      </div>
    `;
  }

  function getLandIntelligenceStateForRef(parcelRef) {
    return landIntelligenceCache.get(parcelRef) || createLandIntelligenceState(parcelRef);
  }

  function renderCompareSignalSummaryTable(compareEntries) {
    const parcelEntries = Array.from(new Map(compareEntries.map((entry) => [entry.key, entry])).values());
    const rows = parcelEntries
      .map((entry) => {
        const state = getLandIntelligenceStateForRef(entry.ref);
        const filteredView = buildFilteredLandIntelligenceView(state);
        if (state.loading) {
          return `
            <tr>
              <td>${entry.ref}</td>
              <td colspan="7">Kaynak sinyalleri yÃƒÂ¼kleniyor...</td>
            </tr>
          `;
        }
        if (state.error) {
          return `
            <tr>
              <td>${entry.ref}</td>
              <td colspan="7">${state.error}</td>
            </tr>
          `;
        }
        if (!state.hasFetched || !state.signals) {
          return `
            <tr>
              <td>${entry.ref}</td>
              <td colspan="7">Bu parsel iÃƒÂ§in source sinyali henÃƒÂ¼z hazÃ„Â±r deÃ„Å¸il.</td>
            </tr>
          `;
        }
        return `
          <tr>
            <td>${entry.ref}</td>
            <td>${filteredView.officialSaleSources.length ? "Var" : "Yok"}</td>
            <td>${filteredView.officialStatus || (filteredView.filterNotice ? "Filtre dÃ„Â±Ã…Å¸Ã„Â±" : "-")}</td>
            <td>${filteredView.brownfieldSources.length ? "Var" : "Yok"}</td>
            <td>${filteredView.marketSources.length ? "Var" : "Yok"}</td>
            <td>${filteredView.confidenceScore !== null ? formatNumber(filteredView.confidenceScore, 1) : "-"}</td>
            <td>${formatLandIntelligenceDate(filteredView.latestUpdatedAt || state.signals.latest_source_updated_at)}</td>
            <td>${filteredView.filterNotice ? filteredView.filterNotice : (state.parcelDetail?.warnings || state.signals.warnings || []).length ? "Var" : "Yok"}</td>
          </tr>
        `;
      })
      .join("");
    return `
      <div class="workspace-section">
        <h3 class="workspace-section-title">Parsel BazlÃ„Â± Kaynak Sinyalleri</h3>
        ${getLandFilterSummaryHtml()}
        <div class="settings-table-wrap">
          <table class="settings-table">
            <thead>
              <tr>
                <th>Parsel</th>
                <th>Official Sale</th>
                <th>Official Status</th>
                <th>Brownfield</th>
                <th>Portal Listing</th>
                <th>Confidence</th>
                <th>Last Updated</th>
                <th>Warning</th>
              </tr>
            </thead>
            <tbody>${rows}</tbody>
          </table>
        </div>
      </div>
    `;
  }

  function renderCompareSignalDetails(compareEntries) {
    const parcelEntries = Array.from(new Map(compareEntries.map((entry) => [entry.key, entry])).values());
    return `
      <div class="workspace-section">
        <h3 class="workspace-section-title">Kaynak Linkleri ve Warning DetaylarÃ„Â±</h3>
        ${getLandFilterSummaryHtml()}
        <div class="workspace-stack">
          ${parcelEntries
            .map((entry) => {
              const state = getLandIntelligenceStateForRef(entry.ref);
              const filteredView = buildFilteredLandIntelligenceView(state);
              if (!state.hasFetched || state.loading || !state.signals) {
                return `
                  <details class="workspace-section workspace-details">
                    <summary class="workspace-details-summary">${entry.ref}</summary>
                    <div class="workspace-details-body">
                      <div class="workspace-note">${state.loading ? "Kaynak sinyalleri yÃƒÂ¼kleniyor..." : "Bu parsel iÃƒÂ§in detay henÃƒÂ¼z hazÃ„Â±r deÃ„Å¸il."}</div>
                    </div>
                  </details>
                `;
              }
              const sourceRows = filteredView.filteredSources
                .map((source) => {
                  const label = source.source_name || "source";
                  const status = getLandSourceStatus(source);
                  const confidence = getLandSourceConfidence(source);
                  const link = resolveLandSourceLink(source);
                  return `<div class="workspace-row"><span>${label}</span><strong>${status || "-"} Ã‚Â· ${confidence !== null ? formatNumber(confidence, 1) : "-"} Ã‚Â· ${buildExternalSaleLink(link.url, link.label)}</strong></div>`;
                })
                .join("");
              const warningRows = [...(state.parcelDetail?.warnings || []), ...(state.signals.warnings || [])]
                .map((item) => `<div class="workspace-row"><span>${item.code || "warning"}</span><strong>${item.message}</strong></div>`)
                .join("");
              return `
                <details class="workspace-section workspace-details">
                  <summary class="workspace-details-summary">${entry.ref} Ã‚Â· ${entry.regionLabel}</summary>
                  <div class="workspace-details-body">
                    <div class="workspace-stack">
                      ${filteredView.filterNotice ? `<div class="workspace-note">${filteredView.filterNotice}</div>` : ""}
                      ${sourceRows || '<div class="workspace-note">Aktif filtreyle eÃ…Å¸leÃ…Å¸en kaynak linki bulunamadÃ„Â±.</div>'}
                      ${warningRows || '<div class="workspace-note">Bu parsel iÃƒÂ§in ek warning yok.</div>'}
                      <div class="workspace-row"><span>Price Paid History</span><strong>${(state.history || []).length} kayÃ„Â±t</strong></div>
                    </div>
                  </div>
                </details>
              `;
            })
            .join("")}
        </div>
      </div>
    `;
  }

  function renderParcelFeaturesAndDistances(compareEntries) {
    const parcelEntries = Array.from(new Map(compareEntries.map((entry) => [entry.key, entry])).values());
    return `
      <div class="workspace-section">
        <h3 class="workspace-section-title">Parsel Ãƒâ€“zellikleri ve UzaklÃ„Â±klar</h3>
        <div class="workspace-stack">
          ${parcelEntries
            .map(
              (entry) => `
                <details class="workspace-section workspace-details">
                  <summary class="workspace-details-summary">${entry.ref} Ã‚Â· ${entry.regionLabel}</summary>
                  <div class="workspace-details-body">
                    <div class="metric-grid">
                      <div class="metric-card"><div class="metric-card-label">Alan</div><div class="metric-card-value">${formatNumber(entry.areaM2, 0)} mÃ‚Â²</div></div>
                      <div class="metric-card"><div class="metric-card-label">EÃ„Å¸im</div><div class="metric-card-value">%${formatNumber(entry.slopePct, 1)}</div></div>
                      <div class="metric-card"><div class="metric-card-label">Arsa ÃƒÂ§evresi</div><div class="metric-card-value">${formatDistanceMeters(entry.perimeterM)}</div></div>
                      <div class="metric-card"><div class="metric-card-label">BoÃ…Å¸ arazi</div><div class="metric-card-value">%${formatNumber(entry.emptyLandSignal * 100, 0)}</div></div>
                    </div>
                    ${renderUnitsOverviewSection(entry.primaryUnits, entry.nearbyUnits)}
                  </div>
                </details>
              `
            )
            .join("")}
        </div>
      </div>
    `;
  }

  function renderCompareResultsTable(compareEntries) {
    const rows = compareEntries
      .map(
        (entry) => `
          <tr>
            <td>${entry.ref}</td>
            <td>${entry.scenario.name}</td>
            <td>${formatNumber(entry.scenario.usedM2, 0)}</td>
            <td>${formatNumber(entry.scenario.capacityM2, 0)}</td>
            <td>${formatNumber(entry.scenario.totalCost, 0)}</td>
            <td>${formatNumber(entry.scenario.revenue, 0)}</td>
            <td>${formatNumber(entry.scenario.profit, 0)}</td>
            <td>${formatNumber(entry.scenario.roiPct, 4)}</td>
            <td>${formatNumber(entry.scenario.irrPct, 4)}</td>
          </tr>
        `
      )
      .join("");
    return `
      <div class="workspace-section">
        <div class="settings-table-wrap">
          <table class="settings-table">
            <thead>
              <tr>
                <th>Parsel</th>
                <th>Senaryo</th>
                <th>KullanÃ„Â±m (mÃ‚Â²)</th>
                <th>Kapasite (mÃ‚Â²)</th>
                <th>Toplam Maliyet (TRY)</th>
                <th>Gelir (TRY)</th>
                <th>KÃƒÂ¢r (TRY)</th>
                <th>ROI</th>
                <th>IRR (Annual)</th>
              </tr>
            </thead>
            <tbody>${rows}</tbody>
          </table>
        </div>
      </div>
    `;
  }

  function renderScenarioDetailsByBuildingType(compareEntries) {
    return `
      <div class="workspace-section">
        <h3 class="workspace-section-title">Senaryo DetaylarÃ„Â± (YapÃ„Â± TÃƒÂ¼rÃƒÂ¼ne GÃƒÂ¶re)</h3>
        <div class="workspace-stack">
          ${compareEntries
            .map((entry) => {
              const components = entry.scenario.components?.length
                ? entry.scenario.components
                : [
                    {
                      label: entry.scenario.typeConfig?.label || entry.scenario.name,
                      equivalentUnits: entry.scenario.units || 1,
                      surfaceArea: entry.scenario.typeConfig?.unitArea || entry.scenario.usedM2,
                      usedM2: entry.scenario.usedM2,
                      typeConfig: entry.scenario.typeConfig || getBuildingTypeConfigByKey("karma"),
                      adjustedUnitSaleValue:
                        entry.adjustedSaleMap.get(entry.scenario.typeConfig?.key || "karma") ||
                        entry.scenario.typeConfig?.unitSaleValue ||
                        0,
                    },
                  ];
              const rows = components
                .map(
                  (component) => `
                    <tr>
                      <td>${component.label}</td>
                      <td>${formatNumber(component.equivalentUnits, 2)}</td>
                      <td>${formatNumber(component.surfaceArea, 0)}</td>
                      <td>${formatNumber(component.usedM2, 0)}</td>
                      <td>${formatNumber(component.typeConfig.unitCost, 0)}</td>
                      <td>${formatNumber(component.adjustedUnitSaleValue || component.typeConfig.unitSaleValue, 0)}</td>
                      <td>${formatNumber(component.revenue || (component.equivalentUnits * (component.adjustedUnitSaleValue || component.typeConfig.unitSaleValue)), 0)}</td>
                    </tr>
                  `
                )
                .join("");
              return `
                <details class="workspace-section workspace-details">
                  <summary class="workspace-details-summary">${entry.ref} Ã‚Â· ${entry.scenario.name}</summary>
                  <div class="workspace-details-body">
                    <div class="settings-table-wrap">
                      <table class="settings-table">
                        <thead>
                          <tr>
                            <th>YapÃ„Â± TÃƒÂ¼rÃƒÂ¼</th>
                            <th>Birim SayÃ„Â±sÃ„Â±</th>
                            <th>Birim AlanÃ„Â± (mÃ‚Â²)</th>
                            <th>KullanÃ„Â±m (mÃ‚Â²)</th>
                            <th>Birim Maliyet</th>
                            <th>Birim SatÃ„Â±Ã…Å¸ DeÃ„Å¸eri</th>
                            <th>Toplam DeÃ„Å¸er</th>
                          </tr>
                        </thead>
                        <tbody>${rows}</tbody>
                      </table>
                    </div>
                  </div>
                </details>
              `;
            })
            .join("")}
        </div>
      </div>
    `;
  }

  function renderScenarioComparisonChart(compareEntries, metricKey, title, formatter, axisLabel) {
    const maxValue = compareEntries.reduce((max, entry) => {
      const value = Number(entry.scenario?.[metricKey]) || 0;
      return Math.max(max, value);
    }, 0);
    const safeMax = maxValue > 0 ? maxValue : 1;
    return `
      <div class="workspace-section">
        <h3 class="workspace-section-title">${title}</h3>
        <div class="comparison-chart">
          ${compareEntries
            .map((entry) => {
              const value = Number(entry.scenario?.[metricKey]) || 0;
              const heightPct = Math.max(8, (value / safeMax) * 100);
              return `
                <div class="comparison-bar-item">
                  <div class="comparison-bar-value">${formatter(value)}</div>
                  <div class="comparison-bar-track">
                    <span class="comparison-bar-fill" style="height:${heightPct}%"></span>
                  </div>
                  <div class="comparison-bar-label">${entry.ref}</div>
                  <div class="comparison-bar-meta">${entry.scenario.name}</div>
                </div>
              `;
            })
            .join("")}
        </div>
        <div class="analysis-footnote">${axisLabel}</div>
      </div>
    `;
  }

  function renderScenarioComparisonCharts(compareEntries) {
    return `
      ${renderScenarioComparisonChart(compareEntries, "profit", "KÃƒÂ¢r (TRY)", (value) => formatNumber(value, 0), "SeÃƒÂ§ili senaryolarÃ„Â±n kÃƒÂ¢r karÃ…Å¸Ã„Â±laÃ…Å¸tÃ„Â±rmasÃ„Â±")}
      ${renderScenarioComparisonChart(compareEntries, "roiPct", "ROI", (value) => formatNumber(value, 4), "SeÃƒÂ§ili senaryolarÃ„Â±n ROI karÃ…Å¸Ã„Â±laÃ…Å¸tÃ„Â±rmasÃ„Â±")}
      ${renderScenarioComparisonChart(compareEntries, "irrPct", "IRR (Annual)", (value) => formatNumber(value, 4), "SeÃƒÂ§ili senaryolarÃ„Â±n yÃ„Â±llÃ„Â±k IRR karÃ…Å¸Ã„Â±laÃ…Å¸tÃ„Â±rmasÃ„Â±")}
    `;
  }

  function renderParcelAnalysisSummaryTable(entries) {
    const rows = entries
      .map(
        (entry) => `
          <tr>
            <td>${entry.ref}</td>
            <td>${entry.regionLabel}</td>
            <td>${formatNumber(entry.areaM2, 0)}</td>
            <td>${formatNumber(entry.slopePct, 1)}</td>
            <td>${formatNumber(entry.emptyLandSignal * 100, 0)}%</td>
            <td>${formatNumber(entry.landCost, 0)}</td>
          </tr>
        `
      )
      .join("");
    return `
      <div class="workspace-section">
        <h3 class="workspace-section-title">KarÃ…Å¸Ã„Â±laÃ…Å¸tÃ„Â±rma Listesindeki Parseller</h3>
        ${getLandFilterSummaryHtml()}
        <div class="settings-table-wrap">
          <table class="settings-table">
            <thead>
              <tr>
                <th>Parsel ID</th>
                <th>Aktif BÃƒÂ¶lge</th>
                <th>Alan (mÃ‚Â²)</th>
                <th>EÃ„Å¸im (%)</th>
                <th>BoÃ…Å¸ Arazi</th>
                <th>Tahmini Arsa Maliyeti (TRY)</th>
              </tr>
            </thead>
            <tbody>${rows}</tbody>
          </table>
        </div>
      </div>
    `;
  }

  function renderParcelAnalysisEntrySections(entries) {
    return entries
      .map((entry) => {
        const factorRows = buildParcelAnalysisFactorRowsFromUnits(entry.primaryUnits || [], entry.nearbyUnits || []);
        const detailRows = Object.entries(entry.feature?.properties || {})
          .filter(([, value]) => value !== null && value !== undefined && value !== "")
          .slice(0, 10)
          .map(([key, value]) => `<div class="workspace-row"><span>${key}</span><strong>${value}</strong></div>`)
          .join("");
        return `
          <div class="workspace-section">
            <h3 class="workspace-section-title">Parsel ${entry.ref}</h3>
            <div class="metric-grid">
              <div class="metric-card"><div class="metric-card-label">Parsel Ref</div><div class="metric-card-value">${entry.ref}</div></div>
              <div class="metric-card"><div class="metric-card-label">Aktif BÃƒÂ¶lge</div><div class="metric-card-value">${entry.regionLabel}</div></div>
              <div class="metric-card"><div class="metric-card-label">Alan</div><div class="metric-card-value">${formatNumber(entry.areaM2, 0)} mÃ‚Â²</div></div>
              <div class="metric-card"><div class="metric-card-label">Tahmini Arsa Maliyeti</div><div class="metric-card-value">${formatMoney(entry.landCost)}</div></div>
            </div>
            ${buildVerifiedSalesHistoryHtml(entry.feature?.properties || {})}
            ${buildDistrictSalesContextHtml(entry.feature?.properties || {})}
            ${buildExternalMarketEvidenceHtml(entry.feature?.properties || {})}
            ${renderCompactLandIntelligenceCard(entry.ref)}
            ${renderUnitsOverviewSection(entry.primaryUnits || [], entry.nearbyUnits || [])}
            ${renderParcelDetailsAccordion(entry)}
            <div class="workspace-section">
              <h3 class="workspace-section-title">Parsel Ãƒâ€“zellikleri</h3>
              <div class="workspace-stack">${detailRows || '<div class="workspace-note">Uygun parcel ÃƒÂ¶zelliÃ„Å¸i bulunamadÃ„Â±.</div>'}</div>
            </div>
            ${renderParcelAnalysisDistanceTable(entry, factorRows)}
            ${renderGeometricAverageDistributionTable(entry, factorRows)}
          </div>
        `;
      })
      .join("");
  }

  function renderPrimaryUnits(primaryUnits) {
    return primaryUnits
      .map(
        (unit) => `
          <div class="unit-card">
            <div class="unit-card-label">${unit.label}</div>
            <div class="unit-card-value">${formatDistanceMeters(unit.distanceM)}</div>
            <div class="unit-card-meta">${unit.name}</div>
          </div>
        `
      )
      .join("");
  }

  function renderNearbyUnits(nearbyUnits) {
    return nearbyUnits.length
      ? nearbyUnits
          .map(
            (unit) => `
              <div class="workspace-row">
                <span>${unit.label}</span>
                <strong>${unit.name} Ã‚Â· ${formatDistanceMeters(unit.distanceM)}</strong>
              </div>
            `
          )
          .join("")
      : '<div class="workspace-note">Aktif bÃƒÂ¶lgede uygun POI/birim detayÃ„Â± bulunamadÃ„Â±.</div>';
  }

  function renderUnitsOverviewSection(primaryUnits, nearbyUnits) {
    return `
      <div class="workspace-section">
        <h3 class="workspace-section-title">POI / Birim UzaklÃ„Â±klarÃ„Â±</h3>
        <div class="unit-grid">${renderPrimaryUnits(primaryUnits)}</div>
        <div class="workspace-stack unit-list-stack">${renderNearbyUnits(nearbyUnits)}</div>
      </div>
    `;
  }


  function formatLandIntelligenceDate(value) {
    if (!value) return '-';
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) return String(value);
    return date.toLocaleString('tr-TR');
  }

  const LAND_SOURCE_LABELS = {
    supabase_admin: "Managed Sales",
    homes_england_landhub: "Homes England",
    government_property_finder: "Government Property Finder",
    planning_data_brownfield: "Planning Data Brownfield",
    local_authority_brownfield: "Local Authority Brownfield",
    market_listing_adapter: "LisanslÃ„Â± Market Feed",
    hmlr_price_paid: "Price Paid History",
  };

  const LAND_SOURCE_PRIORITIES = {
    supabase_admin: 0,
    homes_england_landhub: 1,
    government_property_finder: 1,
    market_listing_adapter: 2,
    local_authority_brownfield: 3,
    planning_data_brownfield: 4,
    hmlr_price_paid: 5,
  };

  function getLandSourceDisplayName(sourceName) {
    return LAND_SOURCE_LABELS[sourceName] || sourceName || "Kaynak";
  }

  function getLandSourcePriority(sourceName) {
    return LAND_SOURCE_PRIORITIES[sourceName] ?? 99;
  }

  function hasSalePrice(record) {
    const numeric = Number(record?.ask_price);
    return Number.isFinite(numeric) && numeric > 0;
  }

  function isSyntheticSaleUrl(url) {
    return /example\.local/i.test(String(url || ""));
  }

  function getBackendTruthPayload(record, key) {
    const payload = record?.[key];
    return payload && typeof payload === "object" ? payload : null;
  }

  function getSaleRecordTruthTier(record) {
    if (!record) return "manual";
    const providerName = String(record.provider_name || "").trim().toLowerCase();
    const rawUrl = record.external_url || record.listing_url || record.source_url || "";
    const providerKind = String(record.provider_kind || "").trim().toLowerCase();
    if (record.is_demo || providerName === "sample_csv" || providerKind === "demo" || providerKind === "sample" || isSyntheticSaleUrl(rawUrl)) {
      return "demo";
    }
    const explicitTier = String(record.source_tier || record.truth_tier || "").trim().toLowerCase();
    if (explicitTier) {
      if (explicitTier === "official") return "official";
      if (explicitTier === "licensed") return "licensed";
      if (explicitTier === "manual") return "manual";
      if (explicitTier === "demo") return "demo";
    }
    const sourceName = String(record.source_name || "").trim().toLowerCase();
    if (sourceName === "homes_england_landhub" || sourceName === "government_property_finder") {
      return "official";
    }
    if (sourceName === "market_listing_adapter") {
      return "licensed";
    }
    return "manual";
  }

  function getSalePriceTruth(record, sources = []) {
    const backendTruth = getBackendTruthPayload(record, "price_truth");
    if (backendTruth?.label) {
      return {
        label: backendTruth.label,
        detail: backendTruth.detail || "Backend truth",
        tone: backendTruth.tone || "neutral",
        isReal: backendTruth.is_real ?? null,
      };
    }
    if (!record || !hasSalePrice(record)) {
      return {
        label: "Fiyat yok",
        detail: "Kaynakta ilan fiyatÃ„Â± bulunamadÃ„Â±.",
        tone: "neutral",
        isReal: null,
      };
    }
    const providerName = String(record.provider_name || "").trim();
    const tier = getSaleRecordTruthTier(record);
    if (tier === "demo") {
      return {
        label: "Demo fiyat",
        detail: providerName ? `${providerName} ornek feed verisi` : "Ornek / test listing verisi",
        tone: "demo",
        isReal: false,
      };
    }
    if (tier === "licensed") {
      return {
        label: "GerÃƒÂ§ek ilan fiyatÃ„Â±",
        detail: providerName || "Portal listing kaynaÃ„Å¸Ã„Â±",
        tone: "listing",
        isReal: true,
      };
    }
    if (tier === "official") {
      return {
        label: "Resmi kaynak fiyatÃ„Â±",
        detail: providerName || "Resmi kaynak kaydi",
        tone: "official",
        isReal: true,
      };
    }
    if (tier === "manual") {
      return {
        label: "Manuel fiyat",
        detail: providerName || "Supabase admin kaydi",
        tone: "manual",
        isReal: null,
      };
    }
    return {
      label: "Kaynak fiyatÃ„Â±",
      detail: getLandSourceDisplayName(record.source_name),
      tone: "price",
      isReal: null,
    };
  }

  function getSaleLinkTruth(record, sources = []) {
    const backendTruth = getBackendTruthPayload(record, "link_truth");
    if (backendTruth?.label) {
      return {
        label: backendTruth.label,
        detail: backendTruth.detail || "Backend truth",
        tone: backendTruth.tone || "neutral",
        isReal: backendTruth.is_real ?? null,
        hasLink: backendTruth.has_link ?? Boolean(resolveSaleRecordLink(record, sources)?.url),
      };
    }
    const resolvedLink = resolveSaleRecordLink(record, sources);
    if (!resolvedLink?.url) {
      return {
        label: "Link yok",
        detail: "Kaynakta acilabilir satis linki bulunamadi.",
        tone: "neutral",
        isReal: null,
        hasLink: false,
      };
    }
    const providerName = String(record?.provider_name || "").trim();
    const tier = getSaleRecordTruthTier(record);
    if (tier === "demo") {
      return {
        label: "Demo link",
        detail: providerName || "Ornek / test ilan linki",
        tone: "demo",
        isReal: false,
        hasLink: true,
      };
    }
    if (tier === "official") {
      return {
        label: "Resmi kaynak linki",
        detail: providerName || "Resmi kaynak baglantisi",
        tone: "official",
        isReal: true,
        hasLink: true,
      };
    }
    if (tier === "licensed") {
      return {
        label: "Lisansli ilan linki",
        detail: providerName || "Lisansli vendor/agent baglantisi",
        tone: "listing",
        isReal: true,
        hasLink: true,
      };
    }
    return {
      label: "Manuel link",
      detail: providerName || "Manuel / yonetimli baglanti",
      tone: "manual",
      isReal: null,
      hasLink: true,
    };
  }

  function formatSalePriceWithTruth(record, sources = []) {
    if (!record) return "Fiyat bilgisi yok";
    const priceLabel = formatSalePrice(record.ask_price);
    const truth = getSalePriceTruth(record, sources);
    return hasSalePrice(record) ? `${priceLabel} Ã‚Â· ${truth.label}` : priceLabel;
  }



  function getListingAreaM2(record) {
    const directValue = Number(record?.listing_area_m2 ?? record?.site_area_m2);
    if (Number.isFinite(directValue) && directValue > 0) {
      return directValue;
    }
    const acresValue = Number(record?.listing_area_acres ?? record?.site_area_acres);
    if (Number.isFinite(acresValue) && acresValue > 0) {
      return acresValue * 4046.8564224;
    }
    return null;
  }

  function getListingAreaAcres(record) {
    const directValue = Number(record?.listing_area_acres ?? record?.site_area_acres);
    if (Number.isFinite(directValue) && directValue > 0) {
      return directValue;
    }
    const m2Value = Number(record?.listing_area_m2 ?? record?.site_area_m2);
    if (Number.isFinite(m2Value) && m2Value > 0) {
      return m2Value / 4046.8564224;
    }
    return null;
  }

  function formatListingArea(record) {
    const areaM2 = getListingAreaM2(record);
    if (!(Number.isFinite(areaM2) && areaM2 > 0)) {
      return "-";
    }
    const acres = getListingAreaAcres(record);
    const areaLabel = `${formatNumber(areaM2, 0)} m2`;
    if (Number.isFinite(acres) && acres > 0) {
      return `${areaLabel} (${formatNumber(acres, 2)} acre)`;
    }
    return areaLabel;
  }

  function formatListingVsParcelAreaDelta(listingAreaM2, parcelAreaM2) {
    if (!(Number.isFinite(listingAreaM2) && listingAreaM2 > 0) || !(Number.isFinite(parcelAreaM2) && parcelAreaM2 > 0)) {
      return "-";
    }
    const deltaM2 = listingAreaM2 - parcelAreaM2;
    const pct = (deltaM2 / parcelAreaM2) * 100;
    const sign = deltaM2 > 0 ? "+" : "";
    return `${sign}${formatNumber(deltaM2, 0)} m2 (${sign}${formatNumber(pct, 1)}%)`;
  }

  function getActionableSaleSourcePriority(recordOrSourceName) {
    const tier = typeof recordOrSourceName === "string"
      ? getSaleRecordTruthTier({ source_name: recordOrSourceName })
      : getSaleRecordTruthTier(recordOrSourceName);
    return (
      {
        official: 3,
        licensed: 3,
        manual: 2,
        demo: 1,
      }[tier] ?? 0
    );
  }

  function buildLandSaleRecordKey(record) {
    if (!record) return "record::unknown";
    return `${record.source_name || "source"}::${record.source_record_id || record.listing_id || record.site_reference || record.label || record.parcel_name || "record"}`;
  }

  function createLandIntelligenceState(parcelRef, overrides = {}) {
    return {
      parcelRef,
      parcelDetail: null,
      loading: false,
      parcelMatch: null,
      matchMode: null,
      matchDistanceM: null,
      signals: null,
      history: [],
      error: null,
      hasFetched: false,
      fetchId: null,
      sourceDetails: [],
      sourceDetailsLoaded: false,
      managedSaleRecords: [],
      plannedAssets: [],
      futureGrowthScore: null,
      ...overrides,
    };
  }

  function mergeFutureGrowthLayerConfig(baseConfig, overrideConfig) {
    const base = baseConfig && typeof baseConfig === "object" ? baseConfig : {};
    const override = overrideConfig && typeof overrideConfig === "object" ? overrideConfig : {};
    return {
      ...base,
      ...override,
      labels: { ...(base.labels || {}), ...(override.labels || {}) },
      api: { ...(base.api || {}), ...(override.api || {}) },
    };
  }

  function normalizeFutureGrowthLayerConfig(rawConfig) {
    const raw = rawConfig && typeof rawConfig === "object" ? rawConfig : {};
    const sourceScale = Array.isArray(raw.colorScale) ? raw.colorScale : [];
    const fallbackScale = [
      { min: 0, max: 20, class: "decline_very_high", hex: "#7f1d1d", labelTr: "Koyu kirmizi: dusus / zayiflama" },
      { min: 20, max: 40, class: "decline_risk", hex: "#d9480f", labelTr: "Kirmizi-turuncu: riskli / zayif gelisim" },
      { min: 40, max: 55, class: "stagnant", hex: "#f4d35e", labelTr: "Sari: duragan" },
      { min: 55, max: 70, class: "limited_growth", hex: "#9fd356", labelTr: "Acik yesil: sinirli yukselis" },
      { min: 70, max: 85, class: "strong_growth", hex: "#2f9e44", labelTr: "Yesil: guclu yukselis" },
      { min: 85, max: 101, class: "breakout_growth", hex: "#1f6feb", labelTr: "Mavi: cok yuksek potansiyel" },
    ];
    const normalizedScale = (sourceScale.length ? sourceScale : fallbackScale).map((entry, index) => ({
      min: Number.isFinite(Number(entry?.min)) ? Number(entry.min) : fallbackScale[index]?.min ?? 0,
      max: Number.isFinite(Number(entry?.max)) ? Number(entry.max) : fallbackScale[index]?.max ?? 100,
      class: String(entry?.class || fallbackScale[index]?.class || `band_${index}`),
      hex: String(entry?.hex || fallbackScale[index]?.hex || "#f4d35e"),
      labelTr: String(entry?.labelTr || fallbackScale[index]?.labelTr || ""),
    }));
    return {
      enabled: raw.enabled !== false,
      defaultVisible: Boolean(raw.defaultVisible),
      layerName: String(raw.layerName || "Future Urban Growth & Value Shift Layer"),
      labels: {
        tr: String(raw.labels?.tr || "Gelecek Gelisim"),
        en: String(raw.labels?.en || "Future Growth"),
      },
      api: {
        layer: String(raw.api?.layer || "/api/future-growth/layer"),
        parcelDetail: String(raw.api?.parcelDetail || "/api/future-growth/parcels/{parcelId}"),
        parcelEvidence: String(raw.api?.parcelEvidence || "/api/future-growth/parcels/{parcelId}/evidence"),
        localAuthorityVector: String(raw.api?.localAuthorityVector || "/api/future-growth/local-authorities/{code}/vector"),
        methodology: String(raw.api?.methodology || "/api/future-growth/methodology"),
      },
      colorScale: normalizedScale,
      legendNote: String(
        raw.legendNote
        || "Bu katman kesin fiyat tahmini degildir; planlama, ulasim, satis, demografi ve sosyal erisim verilerine dayali gelisim potansiyeli skorudur."
      ),
      maxFeaturesPerRequest: Math.max(200, Math.min(12000, Number(raw.maxFeaturesPerRequest || 4500))),
      minZoom: Math.max(5, Number(raw.minZoom || config.parcelMinZoom || 8)),
      showVector: raw.showVector !== false,
      vectorColor: String(raw.vectorColor || "#3b82f6"),
    };
  }

  function hasActiveLandFilters() {
    return (
      landOverlayFilters.minConfidence > 0 ||
      landOverlayFilters.brownfieldSource !== "all" ||
      landOverlayFilters.listingStatus !== "all" ||
      landOverlayFilters.saleReadyQuickFilter !== "all" ||
      landOverlayFilters.reviewOnly
    );
  }

  function buildLandIntelligenceSourceDetailUrl(sourceName, sourceRecordId) {
    if (!sourceName || !sourceRecordId || !landIntelligenceApiBaseUrl) return null;
    if (sourceName === "planning_data_brownfield" || sourceName === "local_authority_brownfield") {
      return `${landIntelligenceApiBaseUrl}/brownfield-sites/${encodeURIComponent(sourceRecordId)}`;
    }
    if (sourceName === "homes_england_landhub" || sourceName === "government_property_finder" || sourceName === "market_listing_adapter") {
      return `${landIntelligenceApiBaseUrl}/listings/${encodeURIComponent(sourceRecordId)}`;
    }
    return null;
  }

  async function fetchLandIntelligenceSourceDetails(signals) {
    const sources = Array.isArray(signals?.sources) ? signals.sources : [];
    const results = await Promise.all(
      sources.map(async (source) => {
        const sourceUrl = buildLandIntelligenceSourceDetailUrl(source.source_name, source.source_record_id);
        if (!sourceUrl) {
          return { ...source, detail: null, detailError: null };
        }
        const payload = await fetchJsonWithTimeout(sourceUrl, {
          label: `Kaynak detayi (${source.source_name || "unknown"})`,
          fallback: null,
        });
        return {
          ...source,
          detail: payload.ok ? payload.data : null,
          detailError: payload.ok ? null : (payload.error || "Kaynak detayina ulasilamadi."),
        };
      })
    );
    return results;
  }

  async function fetchSupabaseManagedSaleRecords(parcelLike) {
    if (!supabaseBridge?.fetchParcelSaleRecords || !parcelLike?.ref) {
      return [];
    }
    try {
      return await supabaseBridge.fetchParcelSaleRecords(parcelLike);
    } catch (error) {
      console.warn("Supabase managed sale records fetch failed:", error?.message || error);
      return [];
    }
  }

  function buildSupabaseSourceDetails(records) {
    return (records || []).map((record) => ({
      source_name: "supabase_admin",
      source_record_id: record.source_record_id,
      source_url: record.source_url || null,
      confidence_score: record.confidence_score,
      requires_review: Boolean(record.requires_review),
      record_summary: {
        label: record.label || record.parcel_name || record.source_record_id,
        status: record.listing_status || record.status || null,
        planning_status: record.planning_status || null,
        confidence_score: record.confidence_score,
        source_updated_at: record.source_updated_at || null,
      },
      detail: {
        source_url: record.source_url || null,
        external_url: record.source_url || null,
        external_label: record.source_url ? "SatÃ„Â±Ã…Å¸ ilanÃ„Â±na git" : null,
        listing_status: record.listing_status || record.status || null,
        planning_status: record.planning_status || null,
        confidence_score: record.confidence_score,
        parcel_name: record.parcel_name || record.label || null,
      },
      source_label: getLandSourceDisplayName("supabase_admin"),
      isManaged: true,
      detailError: null,
    }));
  }

  function sortLandSources(sources) {
    return [...(sources || [])].sort((left, right) => {
      const priorityDelta = getLandSourcePriority(left?.source_name) - getLandSourcePriority(right?.source_name);
      if (priorityDelta !== 0) return priorityDelta;
      const leftUpdated = getLandSourceUpdatedAt(left) ? new Date(getLandSourceUpdatedAt(left)).getTime() : 0;
      const rightUpdated = getLandSourceUpdatedAt(right) ? new Date(getLandSourceUpdatedAt(right)).getTime() : 0;
      if (leftUpdated !== rightUpdated) return rightUpdated - leftUpdated;
      return (getLandSourceConfidence(right) || 0) - (getLandSourceConfidence(left) || 0);
    });
  }

  function dedupeLandSaleRecords(records) {
    const seen = new Set();
    return [...(records || [])]
      .sort((left, right) => {
        const priorityDelta = getLandSourcePriority(left?.source_name) - getLandSourcePriority(right?.source_name);
        if (priorityDelta !== 0) return priorityDelta;
        const leftUpdated = left?.source_updated_at ? new Date(left.source_updated_at).getTime() : 0;
        const rightUpdated = right?.source_updated_at ? new Date(right.source_updated_at).getTime() : 0;
        if (leftUpdated !== rightUpdated) return rightUpdated - leftUpdated;
        return Number(right?.confidence_score || 0) - Number(left?.confidence_score || 0);
      })
      .filter((record) => {
        const key = buildLandSaleRecordKey(record);
        if (seen.has(key)) return false;
        seen.add(key);
        return true;
      });
  }

  function mergeManagedSaleRecords(signals, sourceDetails, records) {
    if (!Array.isArray(records) || !records.length) {
      return { signals, sourceDetails };
    }
    const managedSources = records.map((record) => ({
      source_name: "supabase_admin",
      source_record_id: record.source_record_id,
      source_url: record.source_url || null,
      match_method: record.match_method || "supabase_manual",
      match_score: record.match_score ?? 100,
      confidence_score: record.confidence_score ?? 92,
      requires_review: Boolean(record.requires_review),
      record_summary: {
        label: record.label || record.parcel_name || record.source_record_id,
        status: record.listing_status || record.status || null,
        planning_status: record.planning_status || null,
        confidence_score: record.confidence_score ?? 92,
        source_updated_at: record.source_updated_at || null,
      },
      detail: {
        source_url: record.source_url || null,
        external_url: record.source_url || null,
        external_label: record.source_url ? "SatÃ„Â±Ã…Å¸ ilanÃ„Â±na git" : null,
        listing_status: record.listing_status || record.status || null,
        planning_status: record.planning_status || null,
        confidence_score: record.confidence_score ?? 92,
        parcel_name: record.parcel_name || record.label || null,
      },
    }));
    const mergedSources = sortLandSources([...(signals?.sources || []), ...managedSources]).filter((source, index, allSources) => {
      const key = buildLandSourceRecordKey(source);
      return allSources.findIndex((candidate) => buildLandSourceRecordKey(candidate) === key) === index;
    });
    const mergedSaleRecords = dedupeLandSaleRecords([...(signals?.sale_records || []), ...(signals?.source_summary?.active_sale_records || []), ...records]);
    const mergedSignals = {
      ...(signals || {}),
      portal_listing_signal: true,
      managed_sale_signal: true,
      managed_sale_count: records.length,
      sale_records: mergedSaleRecords,
      sources: mergedSources,
      source_summary: {
        ...(signals?.source_summary || {}),
        active_sale_records: mergedSaleRecords,
        sale_summary: {
          ...((signals?.source_summary?.sale_summary) || {}),
          managed_sale_count: records.length,
          active_count: mergedSaleRecords.length,
          latest_status: records[0]?.listing_status || records[0]?.status || signals?.source_summary?.sale_summary?.latest_status || null,
          latest_asking_price_gbp: records[0]?.ask_price || signals?.source_summary?.sale_summary?.latest_asking_price_gbp || null,
          top_managed_listing: records[0] || null,
          top_actionable_listing: pickTopActionableSaleRecord(mergedSaleRecords, mergedSources) || records[0] || null,
        },
      },
    };
    return {
      signals: mergedSignals,
      sourceDetails: sortLandSources([...(sourceDetails || []), ...buildSupabaseSourceDetails(records)]),
    };
  }

  function getLandSourceConfidence(source) {
    const value = source?.detail?.confidence_score ?? source?.record_summary?.confidence_score ?? source?.confidence_score;
    return Number.isFinite(Number(value)) ? Number(value) : null;
  }

  function getLandSourceUpdatedAt(source) {
    return source?.detail?.source_updated_at || source?.record_summary?.source_updated_at || null;
  }

  function getLandSourceStatus(source) {
    return source?.detail?.listing_status || source?.detail?.planning_status || source?.record_summary?.status || source?.record_summary?.planning_status || null;
  }

  function getLandSourceLabel(source) {
    return source?.detail?.parcel_name || source?.detail?.reference || source?.detail?.site_name_address || source?.record_summary?.label || getLandSourceDisplayName(source?.source_name);
  }

  function buildLandSourceRecordKey(source) {
    return `${source?.source_name || "source"}::${source?.source_record_id || "record"}`;
  }

  function filterParcelRecordRows(records, filteredSources) {
    const allowed = new Set((filteredSources || []).map((source) => buildLandSourceRecordKey(source)));
    return (records || []).filter((record) => allowed.has(`${record?.source_name || "source"}::${record?.source_record_id || "record"}`));
  }

  function renderParcelSaleRecords(records) {
    const rows = (records || [])
      .slice(0, 10)
      .map((record) => {
        const priceTruth = getSalePriceTruth(record);
        const linkTruth = getSaleLinkTruth(record);
        const resolvedLink = resolveSaleRecordLink(record);
        return `
          <tr>
            <td>${record.parcel_name || record.label || record.listing_id || record.source_record_id || "-"}</td>
            <td>${getLandSourceDisplayName(record.source_name)}</td>
            <td>${record.listing_status || record.status || "-"}</td>
            <td>${formatListingArea(record)}</td>
            <td>${formatSalePriceWithTruth(record)}</td>
            <td>${priceTruth.detail || "-"}${linkTruth?.label ? ` Ã‚Â· ${linkTruth.label}` : ""}</td>
            <td>${record.planning_status || "-"}</td>
            <td>${buildExternalSaleLink(resolvedLink.url, resolvedLink.label)}</td>
            <td>${formatLandIntelligenceDate(record.source_updated_at)}</td>
          </tr>
        `;
      })
      .join("");
    if (!rows) {
      return '<div class="workspace-note">Bu parcel iÃƒÂ§in filtrelenmiÃ…Å¸ satÃ„Â±Ã…Å¸ kaydÃ„Â± yok.</div>';
    }
    return `<table class="data-table"><thead><tr><th>SatÃ„Â±Ã…Å¸ KaydÃ„Â±</th><th>Kaynak</th><th>Durum</th><th>Ilan Alani</th><th>Fiyat</th><th>Fiyat TÃƒÂ¼rÃƒÂ¼</th><th>Planning</th><th>Link</th><th>Updated</th></tr></thead><tbody>${rows}</tbody></table>`;
  }

  function matchesLandSourceFilters(source) {
    if (!source) return false;
    const confidence = getLandSourceConfidence(source);
    if (landOverlayFilters.minConfidence > 0 && (confidence === null || confidence < landOverlayFilters.minConfidence)) {
      return false;
    }
    if (landOverlayFilters.reviewOnly && !source.requires_review) {
      return false;
    }
    if (
      landOverlayFilters.brownfieldSource !== "all" &&
      (source.source_name === "planning_data_brownfield" || source.source_name === "local_authority_brownfield") &&
      source.source_name !== landOverlayFilters.brownfieldSource
    ) {
      return false;
    }
    if (
      landOverlayFilters.listingStatus !== "all" &&
      (
        source.source_name === "homes_england_landhub" ||
        source.source_name === "government_property_finder" ||
        source.source_name === "market_listing_adapter" ||
        source.source_name === "supabase_admin"
      )
    ) {
      const statusValue = String(getLandSourceStatus(source) || "").toLowerCase();
      if (statusValue !== String(landOverlayFilters.listingStatus).toLowerCase()) {
        return false;
      }
    }
    return true;
  }

  function buildFilteredLandIntelligenceView(state) {
    if (!state?.signals) {
      return {
        allSources: [],
        filteredSources: [],
        managedSources: [],
        officialSaleSources: [],
        brownfieldSources: [],
        marketSources: [],
        filteredSaleRecords: [],
        topSaleRecord: null,
        topActionableSaleRecord: null,
        topOfficialSaleRecord: null,
        topMarketSaleRecord: null,
        topManagedRecord: null,
        confidenceScore: null,
        latestUpdatedAt: null,
        officialStatus: null,
        hasMatches: false,
        filterNotice: null,
      };
    }
    const allSources = Array.isArray(state.sourceDetails) && state.sourceDetails.length
      ? state.sourceDetails
      : (state.signals.sources || []);
    const sortedAllSources = sortLandSources(allSources);
    const filteredSources = sortLandSources(allSources.filter((source) => matchesLandSourceFilters(source)));
    const managedSources = filteredSources.filter((source) => source.source_name === "supabase_admin");
    const officialSaleSources = filteredSources.filter(
      (source) => source.source_name === "homes_england_landhub" || source.source_name === "government_property_finder"
    );
    const brownfieldSources = filteredSources.filter(
      (source) => source.source_name === "planning_data_brownfield" || source.source_name === "local_authority_brownfield"
    );
    const marketSources = filteredSources.filter((source) => source.source_name === "market_listing_adapter");
    const confidenceScore = filteredSources.reduce((best, source) => {
      const candidate = getLandSourceConfidence(source);
      if (candidate === null) return best;
      return best === null ? candidate : Math.max(best, candidate);
    }, null);
    const latestUpdatedAt = filteredSources.reduce((latest, source) => {
      const candidate = getLandSourceUpdatedAt(source);
      if (!candidate) return latest;
      if (!latest) return candidate;
      return new Date(candidate).getTime() > new Date(latest).getTime() ? candidate : latest;
    }, null);
    const officialStatus = officialSaleSources[0]
      ? getLandSourceStatus(officialSaleSources[0])
      : hasActiveLandFilters()
      ? null
      : state.signals.official_sale_status || null;
    const filteredSaleRecords = dedupeLandSaleRecords(
      filterParcelRecordRows(state.signals.sale_records || state.parcelDetail?.source_summary?.active_sale_records || [], filteredSources)
    );
    const topSaleRecord = filteredSaleRecords[0] || null;
    const topActionableSaleRecord = pickTopActionableSaleRecord(filteredSaleRecords, filteredSources) || topSaleRecord;
    const topOfficialSaleRecord = filteredSaleRecords.find(
      (record) => record.source_name === "homes_england_landhub" || record.source_name === "government_property_finder"
    ) || null;
    const topMarketSaleRecord = filteredSaleRecords.find((record) => record.source_name === "market_listing_adapter") || null;
    const topManagedRecord = filteredSaleRecords.find((record) => record.source_name === "supabase_admin") || dedupeLandSaleRecords(state.managedSaleRecords || [])[0] || null;
    const hasMatches = filteredSources.length > 0;
    const filterNotice = hasActiveLandFilters() && !hasMatches ? "Aktif filtrelerle eÃ…Å¸leÃ…Å¸en kaynak sinyali yok." : null;
    return {
      allSources: sortedAllSources,
      filteredSources,
      managedSources,
      officialSaleSources,
      brownfieldSources,
      marketSources,
      filteredSaleRecords,
      topSaleRecord,
      topActionableSaleRecord,
      topOfficialSaleRecord,
      topMarketSaleRecord,
      topManagedRecord,
      confidenceScore,
      latestUpdatedAt,
      officialStatus,
      hasMatches,
      filterNotice,
    };
  }

  async function fetchLandIntelligenceForParcelRef(parcelRef, options = {}) {
    const { syncSelected = false, force = false, fallbackCenter = null } = options;
    if (!parcelRef || !landIntelligenceApiBaseUrl) {
      const emptyState = createLandIntelligenceState(parcelRef);
      if (syncSelected) {
        landIntelligenceState = emptyState;
      }
      return emptyState;
    }

    const cached = landIntelligenceCache.get(parcelRef);
    if (!force && cached && (cached.loading || cached.hasFetched)) {
      if (syncSelected) {
        landIntelligenceState = { ...cached };
        renderWorkspace();
      }
      return cached;
    }

    const fetchId = ++landIntelligenceFetchCounter;
    const loadingState = createLandIntelligenceState(parcelRef, {
      parcelDetail: cached?.parcelDetail || null,
      parcelMatch: cached?.parcelMatch || null,
      matchMode: cached?.matchMode || null,
      matchDistanceM: cached?.matchDistanceM || null,
      signals: cached?.signals || null,
      history: cached?.history || [],
      sourceDetails: cached?.sourceDetails || [],
      sourceDetailsLoaded: Boolean(cached?.sourceDetailsLoaded),
      managedSaleRecords: cached?.managedSaleRecords || [],
      plannedAssets: cached?.plannedAssets || [],
      futureGrowthScore: cached?.futureGrowthScore || null,
      loading: true,
      fetchId,
    });
    landIntelligenceCache.set(parcelRef, loadingState);
    if (syncSelected) {
      landIntelligenceState = { ...loadingState };
      renderWorkspace();
    }

    try {
      const parcelListPayload = await fetchJsonWithTimeout(
        `${landIntelligenceApiBaseUrl}/parcels?parcel_ref=${encodeURIComponent(parcelRef)}&exclude_demo=true&limit=1`,
        {
          label: "Parsel eslesme sorgusu",
          fallback: [],
          ignoreBackoff: true,
        }
      );
      const parcelList = Array.isArray(parcelListPayload.data) ? parcelListPayload.data : [];
      const currentState = landIntelligenceCache.get(parcelRef);
      if (!currentState || currentState.fetchId !== fetchId) {
        return currentState || loadingState;
      }
      const managedSaleRecords = await fetchSupabaseManagedSaleRecords({ ref: parcelRef });
      const directMatch = Array.isArray(parcelList) && parcelList.length ? parcelList[0] : null;
      const fallbackMatch = !directMatch && fallbackCenter ? await fetchNearestManagedParcel(fallbackCenter) : null;
      const matchedParcel = directMatch || fallbackMatch;
      if (!matchedParcel?.parcel_id) {
        const supabaseOnlySignals = managedSaleRecords.length
          ? mergeManagedSaleRecords(
              {
                parcel_id: null,
                inspire_id: parcelRef,
                parcel_ref: parcelRef,
                official_sale_signal: false,
                official_sale_status: null,
                brownfield_signal: false,
                portal_listing_signal: false,
                confidence_score: null,
                latest_source_updated_at: null,
                source_summary: {},
                sale_records: [],
                brownfield_records: [],
                source_links: [],
                warnings: [
                  { code: "inspire_indicative", message: "INSPIRE boundaries are indicative and not legal boundaries." },
                  { code: "freshness_matters", message: "Source freshness matters." },
                ],
                sources: [],
                freshness: {},
              },
              [],
              managedSaleRecords
            )
          : null;
        const completedEmptyState = createLandIntelligenceState(parcelRef, {
          parcelMatch: managedSaleRecords.length ? { parcel_id: null, inspire_id: parcelRef, parcel_ref: parcelRef, sale_summary: { active_count: managedSaleRecords.length } } : null,
          matchMode: managedSaleRecords.length ? "supabase_only" : "none",
          matchDistanceM: null,
          signals: supabaseOnlySignals?.signals || null,
          sourceDetails: supabaseOnlySignals?.sourceDetails || [],
          managedSaleRecords,
          plannedAssets: [],
          futureGrowthScore: null,
          sourceDetailsLoaded: Boolean(supabaseOnlySignals?.sourceDetails?.length),
          loading: false,
          hasFetched: true,
          fetchId,
        });
        landIntelligenceCache.set(parcelRef, completedEmptyState);
        if (syncSelected && landIntelligenceState.parcelRef === parcelRef) {
          landIntelligenceState = { ...completedEmptyState };
          renderWorkspace();
        } else if (activeWorkspaceScreen === "parcel") {
          renderWorkspace();
        }
        return completedEmptyState;
      }
      const [parcelDetailPayload, signalsPayload, historyPayload, plannedAssetsPayload, futureGrowthPayload] = await Promise.all([
        fetchJsonWithTimeout(`${landIntelligenceApiBaseUrl}/parcels/${matchedParcel.parcel_id}`, {
          label: "Parsel detay",
          fallback: null,
          ignoreBackoff: true,
        }),
        fetchJsonWithTimeout(`${landIntelligenceApiBaseUrl}/parcels/${matchedParcel.parcel_id}/signals`, {
          label: "Parsel sinyalleri",
          fallback: null,
          ignoreBackoff: true,
        }),
        fetchJsonWithTimeout(`${landIntelligenceApiBaseUrl}/parcels/${matchedParcel.parcel_id}/history`, {
          label: "Parsel gecmis satis",
          fallback: [],
          ignoreBackoff: true,
        }),
        fetchJsonWithTimeout(`${landIntelligenceApiBaseUrl}/parcels/${matchedParcel.parcel_id}/planned-assets?limit=50`, {
          label: "Parsel planned assets",
          fallback: [],
          ignoreBackoff: true,
        }),
        fetchJsonWithTimeout(`${landIntelligenceApiBaseUrl}/parcels/${matchedParcel.parcel_id}/future-growth-score`, {
          label: "Future growth score",
          fallback: null,
          ignoreBackoff: true,
        }),
      ]);
      const parcelDetail = parcelDetailPayload.data;
      const signals = signalsPayload.data;
      const history = Array.isArray(historyPayload.data) ? historyPayload.data : [];
      const plannedAssets = Array.isArray(plannedAssetsPayload.data) ? plannedAssetsPayload.data : [];
      const futureGrowthScore = futureGrowthPayload.data || null;
      if (!signals) {
        throw new Error(signalsPayload.error || "Parsel sinyal verisi alinamadi.");
      }
      const sourceDetails = await fetchLandIntelligenceSourceDetails(signals);
      const mergedManagedState = mergeManagedSaleRecords(signals, sourceDetails, managedSaleRecords);
      const finishedState = createLandIntelligenceState(parcelRef, {
        parcelDetail,
        loading: false,
        parcelMatch: matchedParcel,
        matchMode: matchedParcel.match_mode || "exact_parcel_ref",
        matchDistanceM: Number.isFinite(Number(matchedParcel.match_distance_m)) ? Number(matchedParcel.match_distance_m) : null,
        signals: mergedManagedState.signals,
        history: history || [],
        sourceDetails: mergedManagedState.sourceDetails,
        managedSaleRecords,
        plannedAssets,
        futureGrowthScore,
        sourceDetailsLoaded: true,
        error: null,
        hasFetched: true,
        fetchId,
      });
      const latestState = landIntelligenceCache.get(parcelRef);
      if (!latestState || latestState.fetchId !== fetchId) {
        return latestState || finishedState;
      }
      landIntelligenceCache.set(parcelRef, finishedState);
      if (syncSelected && landIntelligenceState.parcelRef === parcelRef) {
        landIntelligenceState = { ...finishedState };
        renderWorkspace();
      } else if (activeWorkspaceScreen === "parcel") {
        renderWorkspace();
      }
      return finishedState;
    } catch (error) {
      const errorState = createLandIntelligenceState(parcelRef, {
        loading: false,
        error: error?.message || 'Land intelligence endpointine ulasilamadi.',
        managedSaleRecords: cached?.managedSaleRecords || [],
        plannedAssets: cached?.plannedAssets || [],
        futureGrowthScore: cached?.futureGrowthScore || null,
        hasFetched: true,
        fetchId,
      });
      const latestState = landIntelligenceCache.get(parcelRef);
      if (!latestState || latestState.fetchId !== fetchId) {
        return latestState || errorState;
      }
      landIntelligenceCache.set(parcelRef, errorState);
      if (syncSelected && landIntelligenceState.parcelRef === parcelRef) {
        landIntelligenceState = { ...errorState };
        renderWorkspace();
      } else if (activeWorkspaceScreen === "parcel") {
        renderWorkspace();
      }
      return errorState;
    }
  }

  async function syncLandIntelligenceForSelectedParcel(feature) {
    const parcel = feature ? getParcelModelFromFeature(feature) : null;
    if (!parcel || !landIntelligenceApiBaseUrl) {
      landIntelligenceState = createLandIntelligenceState(parcel ? parcel.ref : null);
      renderWorkspace();
      return;
    }
    const requestId = ++landIntelligenceRequestId;
    const fallbackCenter = geometryCenterLngLat(feature?.geometry);
    const state = await fetchLandIntelligenceForParcelRef(parcel.ref, { syncSelected: true, fallbackCenter });
    if (requestId !== landIntelligenceRequestId) return;
    landIntelligenceState = { ...state };
    renderWorkspace();
  }

  function renderContextList(items, emptyLabel) {
    if (!items || !items.length) {
      return `<div class="workspace-note">${emptyLabel}</div>`;
    }
    return `<div class="workspace-stack">${items.map((item) => `<div class="workspace-row"><span>${escapeHtml(item)}</span></div>`).join("")}</div>`;
  }

  function renderScenarioScoreCards(parcelDetail, parcelLike) {
    const detailScores = Array.isArray(parcelDetail?.scenario_scores) ? parcelDetail.scenario_scores : [];
    if (detailScores.length) {
      return `
        <div class="scenario-score-grid">
          ${detailScores
            .map((item) => {
              const topPositive = (item.positive_factors_json || [])
                .slice(0, 2)
                .map((factor) => factor.label || factor.metric_key || "-")
                .join(", ");
              const topNegative = (item.negative_factors_json || [])
                .slice(0, 2)
                .map((factor) => factor.label || factor.metric_key || "-")
                .join(", ");
              return `
                <div class="scenario-score-card">
                  <div class="scenario-score-header">
                    <strong>${escapeHtml(item.label_tr || getScenarioModeLabel(item.profile_code))}</strong>
                    <span class="scenario-score-badge" style="--scenario-score-color:${getScenarioScoreColor(item.score_total)}">${formatNumber(item.score_total, 0)}</span>
                  </div>
                  <div class="workspace-note">${escapeHtml(item.score_band || getScenarioScoreText(item.score_total))}</div>
                  ${topPositive ? `<div class="workspace-note"><strong>Arti:</strong> ${escapeHtml(topPositive)}</div>` : ""}
                  ${topNegative ? `<div class="workspace-note"><strong>Eksi:</strong> ${escapeHtml(topNegative)}</div>` : ""}
                </div>
              `;
            })
            .join("")}
        </div>
      `;
    }
    const quickScores = parcelLike?.properties?.scenario_scores || {};
    const entries = Object.entries(quickScores).filter(([, value]) => Number.isFinite(Number(value)));
    if (!entries.length) {
      return '<div class="workspace-note">HenÃƒÂ¼z scenario scoring hesaplanmadi.</div>';
    }
    return `
      <div class="scenario-score-grid">
        ${entries
          .map(([code, value]) => `
            <div class="scenario-score-card">
              <div class="scenario-score-header">
                <strong>${escapeHtml(getScenarioModeLabel(code))}</strong>
                <span class="scenario-score-badge" style="--scenario-score-color:${getScenarioScoreColor(value)}">${formatNumber(Number(value), 0)}</span>
              </div>
              <div class="workspace-note">${escapeHtml(getScenarioScoreText(Number(value)))}</div>
            </div>
          `)
          .join("")}
      </div>
    `;
  }

  function renderFacilityContextSection(parcelLike, parcelDetail) {
    const context = parcelDetail?.context_summary;
    if (!context) {
      return `
        <div class="workspace-section">
          <h3 class="workspace-section-title">YakÃ„Â±n Cevre Profili</h3>
          <div class="workspace-note">Buildings & facilities context henÃƒÂ¼z hesaplanmadi.</div>
        </div>
      `;
    }
    const nearestRows = [
      ["Nearest industrial", context.nearest_industrial_m],
      ["Nearest office", context.nearest_office_m],
      ["Nearest retail", context.nearest_retail_m],
      ["Nearest school", context.nearest_school_m],
      ["Nearest health", context.nearest_health_m],
      ["Nearest transport", context.nearest_transport_m],
    ];
    return `
      <div class="workspace-section">
        <h3 class="workspace-section-title">Yakin Cevre Profili</h3>
        <div class="metric-grid">
          <div class="metric-card"><div class="metric-card-label">Arazi kullanim tipi</div><div class="metric-card-value">${escapeHtml(getFacilityCategoryLabel(context.dominant_context_code))}</div></div>
          <div class="metric-card"><div class="metric-card-label">Nuisance score</div><div class="metric-card-value">${formatNumber((context.nuisance_score || 0) * 100, 0)}/100</div></div>
          <div class="metric-card"><div class="metric-card-label">Accessibility</div><div class="metric-card-value">${formatNumber((context.accessibility_score || 0) * 100, 0)}/100</div></div>
          <div class="metric-card"><div class="metric-card-label">Land-use mix</div><div class="metric-card-value">${formatNumber((context.land_use_mix_score || 0) * 100, 0)}/100</div></div>
          <div class="metric-card"><div class="metric-card-label">Residential ratio</div><div class="metric-card-value">${formatNumber((context.residential_ratio_500m || 0) * 100, 0)}%</div></div>
          <div class="metric-card"><div class="metric-card-label">Commercial ratio</div><div class="metric-card-value">${formatNumber((context.commercial_ratio_500m || 0) * 100, 0)}%</div></div>
        </div>
        <div class="workspace-stack">
          ${nearestRows
            .map(([label, distance]) => `<div class="workspace-row"><span>${label}</span><strong>${distance !== null && distance !== undefined ? formatDistanceMeters(distance) : "-"}</strong></div>`)
            .join("")}
        </div>
        <div class="metric-grid">
          <div class="metric-card"><div class="metric-card-label">Industrial 250m</div><div class="metric-card-value">${formatNumber(context.industrial_count_250m || 0, 0)}</div></div>
          <div class="metric-card"><div class="metric-card-label">Industrial 500m</div><div class="metric-card-value">${formatNumber(context.industrial_count_500m || 0, 0)}</div></div>
          <div class="metric-card"><div class="metric-card-label">Office 500m</div><div class="metric-card-value">${formatNumber(context.office_count_500m || 0, 0)}</div></div>
          <div class="metric-card"><div class="metric-card-label">Retail 500m</div><div class="metric-card-value">${formatNumber(context.retail_count_500m || 0, 0)}</div></div>
          <div class="metric-card"><div class="metric-card-label">Education 500m</div><div class="metric-card-value">${formatNumber(context.education_count_500m || 0, 0)}</div></div>
          <div class="metric-card"><div class="metric-card-label">Transport 500m</div><div class="metric-card-value">${formatNumber(context.transport_count_500m || 0, 0)}</div></div>
        </div>
        <div class="context-split-grid">
          <div class="context-list-card">
            <div class="field-label">Olumlu Etkiler</div>
            ${renderContextList(context.top_opportunities_json || [], "Belirgin firsat kaydi yok.")}
          </div>
          <div class="context-list-card">
            <div class="field-label">Olumsuz Etkiler</div>
            ${renderContextList(context.top_risks_json || [], "Belirgin risk kaydi yok.")}
          </div>
        </div>
      </div>
      <div class="workspace-section">
        <h3 class="workspace-section-title">Senaryo Uygunluk Skorlari</h3>
        ${renderScenarioScoreCards(parcelDetail, parcelLike)}
      </div>
    `;
  }

  function formatProbabilityLabel(score) {
    const numeric = Number(score);
    if (!Number.isFinite(numeric)) return "Insufficient evidence";
    if (numeric >= 85) return "Very High";
    if (numeric >= 70) return "High";
    if (numeric >= 50) return "Medium";
    if (numeric >= 25) return "Low-Medium";
    return "Low";
  }

  function formatDeliveryWindowText(summary, fallbackAssets = []) {
    if (!summary) return "Insufficient evidence";
    if (Number.isFinite(Number(summary?.estimated_delivery_window_start)) || Number.isFinite(Number(summary?.estimated_delivery_window_end))) {
      const start = summary?.estimated_delivery_window_start || "-";
      const end = summary?.estimated_delivery_window_end || "-";
      return `${start} - ${end} (estimated)`;
    }
    const years = [];
    (fallbackAssets || []).forEach((item) => {
      if (Number.isFinite(Number(item?.planned_start_year))) years.push(Number(item.planned_start_year));
      if (Number.isFinite(Number(item?.planned_completion_year))) years.push(Number(item.planned_completion_year));
      if (Number.isFinite(Number(item?.estimated_delivery_window_start))) years.push(Number(item.estimated_delivery_window_start));
      if (Number.isFinite(Number(item?.estimated_delivery_window_end))) years.push(Number(item.estimated_delivery_window_end));
    });
    if (!years.length) return "Insufficient evidence";
    return `${Math.min(...years)} - ${Math.max(...years)} (estimated)`;
  }

  function renderFutureDevelopmentSection(parcelDetail, futureGrowthScore, plannedAssets) {
    const summary = futureGrowthScore?.summary || parcelDetail?.future_intelligence_summary || null;
    const assets = Array.isArray(plannedAssets) ? [...plannedAssets] : [];
    const rankedAssets = assets
      .sort((left, right) => Number(right?.value_impact_score || 0) - Number(left?.value_impact_score || 0))
      .slice(0, 6);

    if (!summary && !rankedAssets.length) {
      return `
        <div class="workspace-section">
          <h3 class="workspace-section-title">Future Development & Infrastructure</h3>
          <div class="workspace-note">Insufficient evidence: bu parcel icin dogrulanmis planned-development sinyali bulunamadi.</div>
        </div>
      `;
    }

    const deliveryScore = Number(
      futureGrowthScore?.delivery_probability_score
      ?? summary?.delivery_probability_score
      ?? 0
    );
    const sourceConfidence = Number(
      futureGrowthScore?.source_confidence_score
      ?? summary?.source_confidence_score
      ?? 0
    );
    const delayRisk = Number(
      futureGrowthScore?.delay_risk_score
      ?? summary?.delay_risk_score
      ?? 0
    );
    const evidenceRows = (summary?.evidence || []).slice(0, 6);
    const riskRows = (summary?.risks || []).slice(0, 6);
    const deliveryWindowText = formatDeliveryWindowText(summary, rankedAssets);

    return `
      <div class="workspace-section">
        <h3 class="workspace-section-title">Future Development & Infrastructure</h3>
        <div class="workspace-note">Bu bolum yatırım tavsiyesi degil; resmi kaynaklara dayali evidence-backed forward-looking sinyal ozetidir.</div>
        <div class="metric-grid">
          <div class="metric-card"><div class="metric-card-label">Future Growth Score</div><div class="metric-card-value">${formatNumber(Number(futureGrowthScore?.future_growth_score ?? summary?.weighted_future_growth_score ?? 0), 1)}/100</div></div>
          <div class="metric-card"><div class="metric-card-label">Planned Dev Impact</div><div class="metric-card-value">${formatNumber(Number(futureGrowthScore?.planned_development_impact_score ?? summary?.weighted_future_growth_score ?? 0), 1)}/100</div></div>
          <div class="metric-card"><div class="metric-card-label">Planned Transport Uplift</div><div class="metric-card-value">${formatNumber(Number(futureGrowthScore?.planned_transport_uplift_score ?? summary?.weighted_transport_uplift_score ?? 0), 1)}/100</div></div>
          <div class="metric-card"><div class="metric-card-label">Planning Momentum</div><div class="metric-card-value">${formatNumber(Number(futureGrowthScore?.planning_momentum_score ?? summary?.planning_momentum_score ?? 0), 1)}/100</div></div>
          <div class="metric-card"><div class="metric-card-label">Regeneration Potential</div><div class="metric-card-value">${formatNumber(Number(futureGrowthScore?.regeneration_potential_score ?? summary?.regeneration_potential_score ?? 0), 1)}/100</div></div>
          <div class="metric-card"><div class="metric-card-label">Delivery Probability</div><div class="metric-card-value">${formatNumber(deliveryScore, 1)} (${formatProbabilityLabel(deliveryScore)})</div></div>
          <div class="metric-card"><div class="metric-card-label">Source Confidence</div><div class="metric-card-value">${formatNumber(sourceConfidence, 1)}/100</div></div>
          <div class="metric-card"><div class="metric-card-label">Delay Risk</div><div class="metric-card-value">${formatNumber(delayRisk, 1)}/100</div></div>
          <div class="metric-card"><div class="metric-card-label">Nearest Planned Station</div><div class="metric-card-value">${summary?.nearest_planned_station_distance_m !== null && summary?.nearest_planned_station_distance_m !== undefined ? formatDistanceMeters(summary.nearest_planned_station_distance_m) : "-"}</div></div>
          <div class="metric-card"><div class="metric-card-label">Nearest Major Approved Dev</div><div class="metric-card-value">${summary?.nearest_major_development_distance_m !== null && summary?.nearest_major_development_distance_m !== undefined ? formatDistanceMeters(summary.nearest_major_development_distance_m) : "-"}</div></div>
          <div class="metric-card"><div class="metric-card-label">Estimated Delivery Window</div><div class="metric-card-value">${escapeHtml(deliveryWindowText)}</div></div>
          <div class="metric-card"><div class="metric-card-label">Assets Within 1km</div><div class="metric-card-value">${formatNumber(Number(summary?.planned_assets_within_1km_count || 0), 0)}</div></div>
        </div>
        <details class="workspace-section workspace-details" open>
          <summary class="workspace-details-summary">Yakindaki Planlanan Gelismeler</summary>
          <div class="workspace-details-body">
            ${
              rankedAssets.length
                ? `<table class="data-table"><thead><tr><th>Proje</th><th>Tip</th><th>Durum</th><th>Mesafe</th><th>Delivery</th><th>Value Impact</th><th>Source Confidence</th><th>Timeline</th><th>Evidence</th><th>Kaynak</th></tr></thead><tbody>${rankedAssets
                    .map((item) => `
                      <tr>
                        <td>${escapeHtml(item?.title || "-")}</td>
                        <td>${escapeHtml(item?.asset_type || "-")}</td>
                        <td>${escapeHtml(item?.status || "-")}</td>
                        <td>${item?.distance_m !== null && item?.distance_m !== undefined ? formatDistanceMeters(item.distance_m) : "-"}</td>
                        <td>${formatNumber(Number(item?.delivery_probability_score || 0), 1)} (${escapeHtml(item?.delivery_probability_label || formatProbabilityLabel(item?.delivery_probability_score || 0))})</td>
                        <td>${formatNumber(Number(item?.value_impact_score || 0), 1)}/100</td>
                        <td>${formatNumber(Number(item?.source_confidence_score || 0), 1)}/100</td>
                        <td>${item?.planned_start_year || item?.planned_completion_year ? `${item?.planned_start_year || "-"} - ${item?.planned_completion_year || "-"}` : `${item?.estimated_delivery_window_start || "-"} - ${item?.estimated_delivery_window_end || "-"} (estimated)`}</td>
                        <td>${escapeHtml(item?.evidence_for_probability || item?.evidence_text || "insufficient evidence")}</td>
                        <td>${item?.source_url ? `<a href="${item.source_url}" target="_blank" rel="noreferrer">source</a>` : "-"}</td>
                      </tr>
                    `)
                    .join("")}</tbody></table>`
                : '<div class="workspace-note">Yakinda planlanan proje kaydi bulunamadi.</div>'
            }
          </div>
        </details>
        <details class="workspace-section workspace-details" open>
          <summary class="workspace-details-summary">Evidence Panel</summary>
          <div class="workspace-details-body context-split-grid">
            <div class="context-list-card">
              <div class="field-label">Kanitlar</div>
              ${renderContextList(evidenceRows, "Insufficient evidence")}
            </div>
            <div class="context-list-card">
              <div class="field-label">Riskler</div>
              ${renderContextList(riskRows, "Belirgin risk kaydi yok.")}
            </div>
          </div>
        </details>
      </div>
    `;
  }

  function renderLandIntelligenceSection(parcelLike) {
    const geometryPreviewBlock = renderParcelGeometryPreviewSection(parcelLike?.feature || null);
    const historyNoDataDetails = `
      <details class="workspace-section workspace-details">
        <summary class="workspace-details-summary">Price Paid History</summary>
        <div class="workspace-details-body">
          <div class="workspace-note">Gecmis Satis: Veri yok.</div>
        </div>
      </details>
    `;
    const historyLoadingDetails = `
      <details class="workspace-section workspace-details">
        <summary class="workspace-details-summary">Price Paid History</summary>
        <div class="workspace-details-body">
          <div class="workspace-note">Gecmis Satis: Yukleniyor...</div>
        </div>
      </details>
    `;
    if (!landIntelligenceApiBaseUrl) {
      return `
        <div class="workspace-section">
          <h3 class="workspace-section-title">Land Intelligence</h3>
          <div class="workspace-note">API base URL tanimli degil. <code>config/regions.local.json</code> icinde <code>landIntelligenceApiBaseUrl</code> ayarlayalim.</div>
          ${geometryPreviewBlock}
          ${historyNoDataDetails}
        </div>
      `;
    }
    if (landIntelligenceState.parcelRef !== parcelLike.ref) {
      return `
        <div class="workspace-section">
          <h3 class="workspace-section-title">Land Intelligence</h3>
          <div class="workspace-note">Bu parcel icin hen?z source sinyali yuklenmedi.</div>
          ${geometryPreviewBlock}
          ${historyLoadingDetails}
        </div>
      `;
    }
    if (landIntelligenceState.loading) {
      return `
        <div class="workspace-section">
          <h3 class="workspace-section-title">Land Intelligence</h3>
          <div class="workspace-note">Official sale, brownfield, listing ve history sinyalleri yukleniyor...</div>
          ${geometryPreviewBlock}
          ${historyLoadingDetails}
        </div>
      `;
    }
    if (landIntelligenceState.error) {
      return `
        <div class="workspace-section">
          <h3 class="workspace-section-title">Land Intelligence</h3>
          <div class="workspace-note">${landIntelligenceState.error}</div>
          ${geometryPreviewBlock}
          ${historyNoDataDetails}
        </div>
      `;
    }
    if (!landIntelligenceState.signals) {
      return `
        <div class="workspace-section">
          <h3 class="workspace-section-title">Land Intelligence</h3>
          <div class="workspace-note">Bu parcel icin parcel-centric source eslesmesi bulunamadi.</div>
          ${geometryPreviewBlock}
          ${historyNoDataDetails}
        </div>
      `;
    }

    const parcelDetail = landIntelligenceState.parcelDetail;
    const signals = landIntelligenceState.signals;
    const filteredView = buildFilteredLandIntelligenceView(landIntelligenceState);
    const sourceLinks = filteredView.filteredSources
      .map((source) => {
        const label = getLandSourceDisplayName(source.source_name);
        const link = resolveLandSourceLink(source);
        const confidence = getLandSourceConfidence(source);
        const status = getLandSourceStatus(source);
        return `<div class="workspace-row"><span>${label}</span><strong>${status || "status yok"} Ã‚Â· ${confidence !== null ? formatNumber(confidence, 1) : "-"} Ã‚Â· ${buildExternalSaleLink(link.url, link.label)}</strong></div>`;
      })
      .join("");
    const summaryRows = filteredView.filteredSources
      .map((source) => {
        const label = getLandSourceDisplayName(source.source_name);
        const status = getLandSourceStatus(source);
        const updated = formatLandIntelligenceDate(getLandSourceUpdatedAt(source));
        const confidence = getLandSourceConfidence(source);
        return `<div class="workspace-row"><span>${label}</span><strong>${status || "-"} Ã‚Â· ${updated} Ã‚Â· ${confidence !== null ? formatNumber(confidence, 1) : "-"}</strong></div>`;
      })
      .join("");
    const warnings = [...(parcelDetail?.warnings || []), ...(signals.warnings || [])]
      .map((item) => `<div class="workspace-row"><span>Uyari</span><strong>${item.message}</strong></div>`)
      .join('');
    const filteredSaleRecords = filteredView.filteredSaleRecords;
    const actionableSaleRecord = filteredView.topActionableSaleRecord;
    const actionableSaleLink = actionableSaleRecord ? resolveSaleRecordLink(actionableSaleRecord, filteredView.filteredSources) : { url: null, label: "SatÃ„Â±Ã…Å¸ adresine git" };
    const actionableSaleTruth = getSalePriceTruth(actionableSaleRecord, filteredView.filteredSources);
    const actionableLinkTruth = getSaleLinkTruth(actionableSaleRecord, filteredView.filteredSources);
    const managedSummaryBlock = filteredView.topManagedRecord
      ? `<div class="workspace-note">Supabase yÃƒÂ¶netimli kayÃ„Â±t ÃƒÂ¶ncelikli gÃƒÂ¶steriliyor: <strong>${filteredView.topManagedRecord.parcel_name || filteredView.topManagedRecord.label || filteredView.topManagedRecord.source_record_id || "-"}</strong> Ã‚Â· ${filteredView.topManagedRecord.listing_status || filteredView.topManagedRecord.status || "durum yok"}${filteredView.topManagedRecord.ask_price ? ` Ã‚Â· ${formatSalePriceWithTruth(filteredView.topManagedRecord, filteredView.filteredSources)}` : ""}</div>`
      : "";
    const actionableSummaryBlock = actionableSaleRecord
      ? `<div class="workspace-note">Bu parcel icin kullaniciya acik en iyi satis kaydi: <strong>${actionableSaleRecord.parcel_name || actionableSaleRecord.label || actionableSaleRecord.source_record_id || "-"}</strong> Ã‚Â· ${actionableSaleRecord.listing_status || actionableSaleRecord.status || "durum yok"} Ã‚Â· ${formatSalePriceWithTruth(actionableSaleRecord, filteredView.filteredSources)} Ã‚Â· ${actionableSaleTruth.detail || "-"} Ã‚Â· ${actionableLinkTruth.label || "Link tipi bilinmiyor"} Ã‚Â· ${buildExternalSaleLink(actionableSaleLink.url, actionableSaleLink.label)}</div>`
      : "";
    const historyRows = (landIntelligenceState.history || [])
      .slice(0, 10)
      .map(
        (item) => `
          <tr>
            <td>${item.sale_date || '-'}</td>
            <td>${item.sale_year || '-'}</td>
            <td>${item.price_paid ? formatMoney(Number(item.price_paid)) : '-'}</td>
            <td>${item.price_per_m2_gbp ? formatGbpPerM2(Number(item.price_per_m2_gbp)) : '-'}</td>
            <td>${item.postcode || '-'}</td>
            <td>${item.location_label || '-'}</td>
            <td>${classifyHistoryBuildingType(item.property_type)}</td>
            <td>${formatHistoryPropertyType(item.property_type)}</td>
            <td>${item.tenure || '-'}</td>
            <td>${item.building_area_m2 ? `${formatNumber(Number(item.building_area_m2), 0)} m2` : (item.parcel_area_m2 ? `${formatNumber(Number(item.parcel_area_m2), 0)} m2` : '-')}</td>
          </tr>
        `
      )
      .join('');

    return `
      <div class="workspace-section">
        <h3 class="workspace-section-title">Land Intelligence</h3>
        ${filteredView.filterNotice ? `<div class="workspace-note">${filteredView.filterNotice}</div>` : getLandFilterSummaryHtml()}
        ${managedSummaryBlock}
        ${actionableSummaryBlock}
        <div class="metric-grid">
          <div class="metric-card"><div class="metric-card-label">Supabase KaydÃ„Â±</div><div class="metric-card-value">${filteredView.managedSources.length ? 'Var' : 'Yok'}</div></div>
          <div class="metric-card"><div class="metric-card-label">Official Sale Signal</div><div class="metric-card-value">${filteredView.officialSaleSources.length ? 'Var' : 'Yok'}</div></div>
          <div class="metric-card"><div class="metric-card-label">Brownfield Signal</div><div class="metric-card-value">${filteredView.brownfieldSources.length ? 'Var' : 'Yok'}</div></div>
          <div class="metric-card"><div class="metric-card-label">Portal Listing Signal</div><div class="metric-card-value">${filteredView.marketSources.length ? 'Var' : 'Yok'}</div></div>
          <div class="metric-card"><div class="metric-card-label">Confidence Score</div><div class="metric-card-value">${filteredView.confidenceScore !== null ? formatNumber(filteredView.confidenceScore, 1) : '-'}</div></div>
          <div class="metric-card"><div class="metric-card-label">Last Updated</div><div class="metric-card-value">${formatLandIntelligenceDate(filteredView.latestUpdatedAt || signals.latest_source_updated_at)}</div></div>
          <div class="metric-card"><div class="metric-card-label">Official Status</div><div class="metric-card-value">${filteredView.officialStatus || '-'}</div></div>
        </div>
        ${geometryPreviewBlock}
        ${renderFacilityContextSection(parcelLike, parcelDetail)}
        ${renderFutureDevelopmentSection(parcelDetail, landIntelligenceState.futureGrowthScore, landIntelligenceState.plannedAssets)}
        ${!landIntelligenceState.parcelMatch ? '<div class="workspace-note">Bu parcel backend parcel tablosunda henuz eslesmemis olabilir; ancak Supabase yonetimli satis kayitlari parcel ref uzerinden gosteriliyor.</div>' : ''}
        <div class="workspace-stack">
          ${warnings || '<div class="workspace-note">Standart warning disinda ekstra warning yok.</div>'}
        </div>
        <details class="workspace-section workspace-details" open>
          <summary class="workspace-details-summary">Parcel Ã„Â°ÃƒÂ§ine YazÃ„Â±lan SatÃ„Â±Ã…Å¸ KayÃ„Â±tlarÃ„Â±</summary>
          <div class="workspace-details-body">
            ${renderParcelSaleRecords(filteredSaleRecords)}
          </div>
        </details>
        <details class="workspace-section workspace-details" open>
          <summary class="workspace-details-summary">FiltrelenmiÃ…Å¸ Kaynak Ãƒâ€“zeti</summary>
          <div class="workspace-details-body workspace-stack">${summaryRows || '<div class="workspace-note">Aktif filtreyle eÃ…Å¸leÃ…Å¸en kaynak ÃƒÂ¶zeti yok.</div>'}</div>
        </details>
        <details class="workspace-section workspace-details" open>
          <summary class="workspace-details-summary">FiltrelenmiÃ…Å¸ Source Links</summary>
          <div class="workspace-details-body workspace-stack">${sourceLinks || '<div class="workspace-note">Aktif filtreyle eÃ…Å¸leÃ…Å¸en kaynak linki yok.</div>'}</div>
        </details>
        <details class="workspace-section workspace-details">
          <summary class="workspace-details-summary">Price Paid History</summary>
          <div class="workspace-details-body">
            ${historyRows ? `<table class="data-table"><thead><tr><th>Sale Date</th><th>Year</th><th>Price Paid</th><th>Price / m2</th><th>Postcode</th><th>Location</th><th>Yapi Sinifi</th><th>Yapi Tipi</th><th>Tenure</th><th>Area</th></tr></thead><tbody>${historyRows}</tbody></table>` : '<div class="workspace-note">Gecmis Satis: Veri yok.</div>'}
          </div>
        </details>
      </div>
    `;
  }

  function renderSalesOnlyWorkspace(parcelLike) {
    if (!landIntelligenceApiBaseUrl) {
      return `
        <div class="workspace-section">
          <h2 class="workspace-page-title">Gecmis Satis Modu</h2>
          <div class="workspace-note">API base URL tanimli degil. Satis bilgisi yuklenemedi.</div>
        </div>
      `;
    }

    if (landIntelligenceState.parcelRef !== parcelLike.ref || landIntelligenceState.loading) {
      return `
        <div class="workspace-section">
          <h2 class="workspace-page-title">Gecmis Satis Modu</h2>
          <div class="workspace-note">Parsel icin gecmis satis bilgileri yukleniyor...</div>
        </div>
      `;
    }

    if (landIntelligenceState.error) {
      return `
        <div class="workspace-section">
          <h2 class="workspace-page-title">Gecmis Satis Modu</h2>
          <div class="workspace-note">${landIntelligenceState.error}</div>
        </div>
      `;
    }

    const history = Array.isArray(landIntelligenceState.history) ? landIntelligenceState.history : [];
    const latest = history[0] || null;
    const parcelUseLabel = getParcelUseCategoryLabel(
      landIntelligenceState.parcelDetail?.parcel_use_label
        || parcelLike.properties?.parcel_use_label
        || parcelLike.properties?.land_use_category
        || null
    );
    const historyRows = history
      .slice(0, 20)
      .map(
        (item) => `
          <tr>
            <td>${item.sale_date || "-"}</td>
            <td>${item.sale_year || "-"}</td>
            <td>${item.price_paid ? formatSalePrice(Number(item.price_paid)) : "-"}</td>
            <td>${item.price_per_m2_gbp ? formatGbpPerM2(Number(item.price_per_m2_gbp)) : "-"}</td>
            <td>${item.postcode || "-"}</td>
            <td>${item.location_label || "-"}</td>
            <td>${parcelUseLabel || "-"}</td>
            <td>${item.building_class_label || classifyHistoryBuildingType(item.property_type)}</td>
            <td>${item.property_type_label || formatHistoryPropertyType(item.property_type)}</td>
            <td>${item.tenure || "-"}</td>
            <td>${item.building_area_m2 ? `${formatNumber(Number(item.building_area_m2), 0)} m2` : (item.parcel_area_m2 ? `${formatNumber(Number(item.parcel_area_m2), 0)} m2` : "-")}</td>
          </tr>
        `
      )
      .join("");

    return `
      <div class="workspace-section">
        <h2 class="workspace-page-title">Gecmis Satis Modu</h2>
        <div class="workspace-note">Bu modda sadece secili parsele ait satis bilgileri gosterilir.</div>
        <div class="metric-grid">
          <div class="metric-card"><div class="metric-card-label">Parsel</div><div class="metric-card-value">${parcelLike.ref}</div></div>
          <div class="metric-card"><div class="metric-card-label">Parsel Turu</div><div class="metric-card-value">${parcelUseLabel || "-"}</div></div>
          <div class="metric-card"><div class="metric-card-label">Kayit Sayisi</div><div class="metric-card-value">${history.length}</div></div>
          <div class="metric-card"><div class="metric-card-label">Son Satis Tarihi</div><div class="metric-card-value">${latest?.sale_date || "-"}</div></div>
          <div class="metric-card"><div class="metric-card-label">Son Satis Fiyati</div><div class="metric-card-value">${latest?.price_paid ? formatSalePrice(Number(latest.price_paid)) : "-"}</div></div>
          <div class="metric-card"><div class="metric-card-label">Yapi Sinifi</div><div class="metric-card-value">${latest ? (latest.building_class_label || classifyHistoryBuildingType(latest.property_type)) : "-"}</div></div>
          <div class="metric-card"><div class="metric-card-label">Yapi Tipi</div><div class="metric-card-value">${latest ? (latest.property_type_label || formatHistoryPropertyType(latest.property_type)) : "-"}</div></div>
          <div class="metric-card"><div class="metric-card-label">Mulkiyet</div><div class="metric-card-value">${latest?.tenure || "-"}</div></div>
          <div class="metric-card"><div class="metric-card-label">Son m2 Fiyati</div><div class="metric-card-value">${latest?.price_per_m2_gbp ? formatGbpPerM2(Number(latest.price_per_m2_gbp)) : "-"}</div></div>
          <div class="metric-card"><div class="metric-card-label">Son Alan</div><div class="metric-card-value">${latest?.building_area_m2 ? `${formatNumber(Number(latest.building_area_m2), 0)} m2` : (latest?.parcel_area_m2 ? `${formatNumber(Number(latest.parcel_area_m2), 0)} m2` : "-")}</div></div>
          <div class="metric-card"><div class="metric-card-label">Konum</div><div class="metric-card-value">${latest?.location_label || "-"}</div></div>
        </div>
        <details class="workspace-section workspace-details" open>
          <summary class="workspace-details-summary">Satis Kayitlari</summary>
          <div class="workspace-details-body">
            ${historyRows
              ? `<table class="data-table"><thead><tr><th>Sale Date</th><th>Year</th><th>Price</th><th>Price / m2</th><th>Postcode</th><th>Location</th><th>Parsel Turu</th><th>Yapi Sinifi</th><th>Yapi Tipi</th><th>Tenure</th><th>Area</th></tr></thead><tbody>${historyRows}</tbody></table>`
              : '<div class="workspace-note">Gecmis Satis: Veri yok.</div>'}
          </div>
        </details>
      </div>
    `;
  }

  function renderParcelDetailsAccordion(parcelLike) {
    return `
      <details class="workspace-section workspace-details">
        <summary class="workspace-details-summary">Parsel AyrÃ„Â±ntÃ„Â±larÃ„Â±</summary>
        <div class="workspace-details-body">
          <div class="metric-grid">
            <div class="metric-card"><div class="metric-card-label">Parsel Ref</div><div class="metric-card-value">${parcelLike.ref}</div></div>
            <div class="metric-card"><div class="metric-card-label">Alan</div><div class="metric-card-value">${formatNumber(parcelLike.areaM2, 0)} mÃ‚Â²</div></div>
            <div class="metric-card"><div class="metric-card-label">EÃ„Å¸im</div><div class="metric-card-value">${formatNumber(parcelLike.slopePct, 1)}%</div></div>
            <div class="metric-card"><div class="metric-card-label">Arsa ÃƒÂ§evresi</div><div class="metric-card-value">${formatDistanceMeters(parcelLike.perimeterM)}</div></div>
            <div class="metric-card"><div class="metric-card-label">BoÃ…Å¸ arazi</div><div class="metric-card-value">%${formatNumber(parcelLike.emptyLandSignal * 100, 0)}</div></div>
            <div class="metric-card"><div class="metric-card-label">Aktif BÃƒÂ¶lge</div><div class="metric-card-value">${parcelLike.regionLabel}</div></div>
          </div>
        </div>
      </details>
    `;
  }

  const PARCEL_ANALYSIS_FACTORS = [
    { factor: "Hastane", unitKey: "hastane" },
    { factor: "Okul", unitKey: "okul" },
    { factor: "Polis Merkezi", unitKey: "polis" },
    { factor: "Metro (UlaÃ…Å¸Ã„Â±m)", unitKey: "metro" },
    { factor: "OtobÃƒÂ¼s DuraÃ„Å¸Ã„Â±", unitKey: "otobus" },
    { factor: "AVM", unitKey: "avm" },
    { factor: "Deniz Ã„Â°skelesi / Su KenarÃ„Â±", unitKey: "iskele" },
    { factor: "Nehir (Su KaynaklarÃ„Â±)", unitKey: "nehir" },
    { factor: "Ã„Â°mar PlanÃ„Â± & Hukuki Durum", unitKey: null },
    { factor: "Topografya & Zemin Ãƒâ€“zellikleri", unitKey: null },
    { factor: "Afet Risk Durumu", unitKey: null },
    { factor: "Piyasa & Sosyo-ekonomik Durum", unitKey: null },
  ];

  const DISTANCE_SCORE_BANDS = {
    hastane: [300, 600, 1000, 1500, 2200, 3200, 4500, 6500, 9000],
    okul: [150, 300, 500, 750, 1100, 1600, 2400, 3500, 5000],
    polis: [350, 700, 1200, 1800, 2500, 3500, 5000, 7000, 10000],
    metro: [250, 500, 800, 1200, 1800, 2600, 3600, 5200, 7500],
    otobus: [100, 250, 400, 700, 1000, 1500, 2200, 3200, 4500],
    avm: [400, 800, 1200, 1800, 2600, 3600, 5000, 7000, 10000],
    iskele: [500, 1000, 1600, 2400, 3400, 5000, 7000, 10000, 15000],
    nehir: [200, 400, 700, 1000, 1600, 2500, 4000, 6000, 9000],
    default: [250, 500, 900, 1400, 2200, 3200, 4500, 6500, 9000],
  };

  function clamp(value, min, max) {
    return Math.min(max, Math.max(min, value));
  }

  function getAnalysisUnitByKey(insights, unitKey) {
    const candidates = [...(insights.primaryUnits || []), ...(insights.nearbyUnits || [])];
    return candidates.find((item) => item?.key === unitKey && Number.isFinite(item?.distanceM)) || null;
  }

  function scoreDistanceByUnitKey(unitKey, distanceM) {
    if (!Number.isFinite(distanceM)) return null;
    const bands = DISTANCE_SCORE_BANDS[unitKey] || DISTANCE_SCORE_BANDS.default;
    for (let index = 0; index < bands.length; index += 1) {
      if (distanceM <= bands[index]) {
        return 10 - index;
      }
    }
    return 1;
  }

  function buildParcelAnalysisFactorRowsFromUnits(primaryUnits, nearbyUnits) {
    const unitMap = new Map([...(primaryUnits || []), ...(nearbyUnits || [])].map((unit) => [unit.key, unit]));
    return PARCEL_ANALYSIS_FACTORS.map((item) => {
      if (!item.unitKey) {
        return {
          factor: item.factor,
          distanceM: NaN,
          distanceLabel: "-",
          score: null,
        };
      }
      const unit = unitMap.get(item.unitKey) || null;
      return {
        factor: item.factor,
        distanceM: unit?.distanceM,
        distanceLabel: unit ? formatDistanceMeters(unit.distanceM) : "Bulunamadi",
        score: unit ? scoreDistanceByUnitKey(item.unitKey, unit.distanceM) : null,
      };
    });
  }

  function buildParcelAnalysisFactorRows(insights) {
    return buildParcelAnalysisFactorRowsFromUnits(insights.primaryUnits, insights.nearbyUnits);
  }

  function renderParcelAnalysisDistanceTable(parcel, factorRows) {
    const rows = factorRows
      .slice(0, 8)
      .map(
        (row) => `
          <tr>
            <td>${row.factor}</td>
            <td>${row.distanceLabel}</td>
            <td>${row.score ?? "Ã¢â‚¬â€"}</td>
          </tr>
        `
      )
      .join("");
    return `
      <div class="workspace-section">
        <h3 class="workspace-section-title">Alternatif YapÃ„Â± TÃƒÂ¼rleri (KarÃ…Å¸Ã„Â±laÃ…Å¸tÃ„Â±rmalÃ„Â±)</h3>
        <div class="workspace-note">Parsel ${parcel.ref}</div>
        <div class="settings-table-wrap">
          <table class="settings-table">
            <thead>
              <tr>
                <th>FaktÃƒÂ¶r / YapÃ„Â± TÃƒÂ¼rÃƒÂ¼</th>
                <th>Mesafe</th>
                <th>Skor (1-10)</th>
              </tr>
            </thead>
            <tbody>${rows}</tbody>
          </table>
        </div>
      </div>
    `;
  }

  function renderBuildingTypeCoefficientTable() {
    const supportedTypes = planningSettings.buildingTypes.filter((type) =>
      ["mustakil", "apartman", "site", "prefab", "perakende", "ofis", "karma", "endustriyel", "tarimsal"].includes(type.key)
    );
    const header = planningSettings.factorMatrix.map((row) => `<th>${row.factor}</th>`).join("");
    const rows = supportedTypes
      .map((type) => {
        const cells = planningSettings.factorMatrix.map((row) => `<td>${row[type.key] ?? "Ã¢â‚¬â€"}</td>`).join("");
        return `
          <tr>
            <td>${type.label}</td>
            ${cells}
          </tr>
        `;
      })
      .join("");
    return `
      <div class="workspace-section">
        <div class="workspace-note">Kurulum ekranÃ„Â±ndaki katsayÃ„Â± tablosuna gÃƒÂ¶re yapÃ„Â± tÃƒÂ¼rÃƒÂ¼ faktÃƒÂ¶r daÃ„Å¸Ã„Â±lÃ„Â±mÃ„Â±</div>
        <div class="settings-table-wrap">
          <table class="settings-table">
            <thead>
              <tr>
                <th>YapÃ„Â± TÃƒÂ¼rÃƒÂ¼</th>
                ${header}
              </tr>
            </thead>
            <tbody>${rows}</tbody>
          </table>
        </div>
      </div>
    `;
  }

  function computeAdjustedSaleValueMap(factorRows) {
    const scoreMap = new Map(factorRows.map((row) => [row.factor, row.score]));
    const supportedTypes = planningSettings.buildingTypes.filter((type) =>
      ["mustakil", "apartman", "site", "prefab", "perakende", "ofis", "karma", "endustriyel", "tarimsal"].includes(type.key)
    );
    const adjustedMap = new Map();
    supportedTypes.forEach((type) => {
      const values = planningSettings.factorMatrix
        .map((row) => {
          const score = scoreMap.get(row.factor);
          if (!Number.isFinite(score)) return null;
          const factorValue = Number(row[type.key]);
          if (!Number.isFinite(factorValue)) return null;
          return Math.sqrt(factorValue * score);
        })
        .filter((value) => Number.isFinite(value));
      if (!values.length) return;
      const product = values.reduce((acc, value) => acc * value, 1);
      const geometricMean = product ** (1 / values.length);
      adjustedMap.set(type.key, type.unitSaleValue * (1 + 0.1 * geometricMean));
    });
    return adjustedMap;
  }

  function renderGeometricAverageDistributionTable(parcel, factorRows, options = {}) {
    const { showTitle = true, footerNote = true } = options;
    const factorScoreMap = new Map(factorRows.map((row) => [row.factor, row.score]));
    const adjustedSaleMap = computeAdjustedSaleValueMap(factorRows);
    const supportedTypes = planningSettings.buildingTypes.filter((type) =>
      ["mustakil", "apartman", "site", "prefab", "perakende", "ofis", "karma", "endustriyel", "tarimsal"].includes(type.key)
    );
    const header = planningSettings.factorMatrix.map((row) => `<th>${row.factor}</th>`).join("");
    const rows = supportedTypes
      .map((type) => {
        const numericValues = [];
        const cells = planningSettings.factorMatrix
          .map((row) => {
            const score = factorScoreMap.get(row.factor);
            if (!Number.isFinite(score)) {
              return "<td>Ã¢â‚¬â€</td>";
            }
            const value = Math.sqrt((row[type.key] || 0) * score);
            numericValues.push(value);
            return `<td>${formatNumber(value, 2)}</td>`;
          })
          .join("");
        const geometricMean = numericValues.length
          ? (numericValues.reduce((acc, value) => acc * value, 1) ** (1 / numericValues.length))
          : null;
        return `
          <tr>
            <td>${type.label}</td>
            ${cells}
            <td>${geometricMean !== null ? formatNumber(geometricMean, 2) : "Ã¢â‚¬â€"}</td>
            <td>${adjustedSaleMap.has(type.key) ? formatNumber(adjustedSaleMap.get(type.key), 0) : "Ã¢â‚¬â€"}</td>
          </tr>
        `;
      })
      .join("");
    return `
      <div class="workspace-section">
        ${showTitle ? '<h3 class="workspace-section-title">YapÃ„Â± TÃƒÂ¼rÃƒÂ¼ FaktÃƒÂ¶r DaÃ„Å¸Ã„Â±lÃ„Â±mÃ„Â± (Geometrik Ortalama)</h3>' : ""}
        <div class="workspace-note">Parsel ${parcel.ref}</div>
        <div class="settings-table-wrap">
          <table class="settings-table">
            <thead>
              <tr>
                <th>YapÃ„Â± TÃƒÂ¼rÃƒÂ¼</th>
                ${header}
                <th>Toplam DeÃ„Å¸er</th>
                <th>Toplam Maliyet DeÃ„Å¸eri</th>
              </tr>
            </thead>
            <tbody>${rows}</tbody>
          </table>
        </div>
        ${footerNote ? '<div class="analysis-footnote">MVP Notu: Bu analiz, mesafe skorlarÃ„Â± ile kurulum katsayÃ„Â±larÃ„Â±nÃ„Â± geometrik ortalama mantÃ„Â±Ã„Å¸Ã„Â±nda birleÃ…Å¸tirir.</div>' : ""}
      </div>
    `;
  }

  function renderRecommendationGeometricTables(parcel, insights) {
    const tableEntries = [
      {
        ref: parcel.ref,
        factorRows: buildParcelAnalysisFactorRows(insights),
      },
      ...comparedParcels
        .filter((item) => item.ref !== parcel.ref)
        .map((item) => ({
          ref: item.ref,
          factorRows: buildParcelAnalysisFactorRowsFromUnits(item.primaryUnits, item.nearbyUnits),
        })),
    ];
    return `
      <div class="workspace-section">
        <h3 class="workspace-section-title">YapÃ„Â± TÃƒÂ¼rÃƒÂ¼ FaktÃƒÂ¶r DaÃ„Å¸Ã„Â±lÃ„Â±mÃ„Â± (Geometrik Ortalama)</h3>
        ${tableEntries
          .map(
            (entry) => `
              ${renderGeometricAverageDistributionTable({ ref: entry.ref }, entry.factorRows, { showTitle: false, footerNote: false })}
            `
          )
          .join("")}
        <div class="analysis-footnote">MVP notu: Bu ÃƒÂ¶neri motoru heuristik ve demo veriye dayanÃ„Â±r. ÃƒÅ“retimde veri gÃƒÂ¼ncelliÃ„Å¸i, belirsizlik raporu ve mevzuat doÃ„Å¸rulamasÃ„Â± zorunludur.</div>
      </div>
    `;
  }

  function computeRecommendationScoreCard(parcel, insights, best) {
    const nearest = new Map((insights.primaryUnits || []).map((unit) => [unit.label, unit]));
    const school = nearest.get("Okul");
    const metro = nearest.get("Metro");
    const market = nearest.get("Market");
    const hospital = nearest.get("Hastane");
    const avgDistance =
      [school, metro, market, hospital]
        .map((item) => item?.distanceM)
        .filter((value) => Number.isFinite(value))
        .reduce((sum, value, _idx, arr) => sum + value / arr.length, 0) || 4000;
    const locationScore = clamp(10 - avgDistance / 1200, 1.5, 9.8);
    const marketSignal = clamp((best?.roiPct || 0) / 14 + 2.2, 2.5, 9.7);
    const landScore = clamp(8.5 - (parcel.slopePct || 0) * 0.4 + (parcel.emptyLandSignal || 0) * 1.8, 2.5, 9.8);
    const general = clamp(locationScore * 0.35 + marketSignal * 0.35 + landScore * 0.3, 1, 10);
    const confidence = clamp(0.58 + general / 25, 0.55, 0.93);
    return {
      location: locationScore,
      market: marketSignal,
      land: landScore,
      general,
      confidence,
    };
  }

  function renderScoreBar(label, value) {
    const pct = clamp(value / 10, 0, 1) * 100;
    return `
      <div class="score-row">
        <div class="score-row-label">${label}: ${formatNumber(value, 1)}/10</div>
        <div class="score-bar"><span style="width:${pct}%"></span></div>
      </div>
    `;
  }

  function scenarioTypeConfig(scenarioName) {
    return planningSettings.buildingTypes.find((item) => item.scenarioName === scenarioName) || planningSettings.buildingTypes[0];
  }

  function getBuildingTypeConfigByKey(typeKey) {
    return planningSettings.buildingTypes.find((item) => item.key === typeKey) || planningSettings.buildingTypes[0];
  }

  function calculateScenarioCapacity(parcel) {
    const baseArea = Math.max(parcel.areaM2 * planningSettings.usableRatio, 1);
    return planningSettings.capacityMethod === "SatÃ„Â±labilir Alan"
      ? Math.max(baseArea * planningSettings.far, 1)
      : Math.max(baseArea, 1);
  }

  function getPlanningParcelVariant(parcelLike) {
    if (!parcelLike) return null;
    const key = getParcelCompareKey(parcelLike);
    const override = planningSettings.parcelOverrides[key] || {};
    return {
      ...parcelLike,
      areaM2: Number.isFinite(Number(override.areaM2)) ? Number(override.areaM2) : parcelLike.areaM2,
      landCost: Number.isFinite(Number(override.landCost)) ? Number(override.landCost) : parcelLike.landCost,
    };
  }

  function computeAverageFactorRows() {
    return planningSettings.buildingTypes
      .filter((type) => ["mustakil", "apartman", "site", "prefab", "perakende", "ofis", "karma", "endustriyel", "tarimsal"].includes(type.key))
      .map((type) => {
        const scores = planningSettings.factorMatrix.map((row) => Number(row[type.key]) || 0);
        const average = scores.reduce((sum, value) => sum + value, 0) / Math.max(scores.length, 1);
        return {
          label: type.label,
          average,
        };
      });
  }

  function getScenarioSelectCandidates(currentParcel) {
    const byKey = new Map();
    if (currentParcel) {
      byKey.set(getParcelCompareKey(currentParcel), getPlanningParcelVariant(currentParcel));
    }
    comparedParcels.forEach((item) => {
      byKey.set(item.key, getPlanningParcelVariant(item));
    });
    return Array.from(byKey.entries()).map(([key, item]) => ({ key, parcel: item }));
  }

  function buildScenarioSelectionRows(parcel, allowedTypes, minUtilization) {
    const capacityM2 = calculateScenarioCapacity(parcel);
    return allowedTypes
      .map((scenarioName) => {
        const typeConfig = scenarioTypeConfig(scenarioName);
        const unitArea = clamp(typeConfig.unitArea, typeConfig.minArea, typeConfig.maxArea);
        const units = Math.max(1, Math.floor(capacityM2 / unitArea));
        const usedM2 = Math.min(capacityM2, units * unitArea);
        const buildCost = units * typeConfig.unitCost;
        const revenue = units * typeConfig.unitSaleValue;
        const otherCosts = buildCost * 0.08;
        const totalCost = buildCost + otherCosts + parcel.landCost;
        const profit = revenue - totalCost;
        const roiPct = totalCost > 0 ? (profit / totalCost) * 100 : 0;
        const irrPct = totalCost > 0 ? ((revenue / totalCost) ** (12 / planningSettings.projectMonths) - 1) * 100 : 0;
        return {
          name: scenarioName,
          buildCost,
          revenue,
          otherCosts,
          totalCost,
          profit,
          roiPct,
          irrPct,
          usedM2,
          capacityM2,
          utilization: clamp(usedM2 / capacityM2, 0, 1.6),
          typeConfig,
          units,
        };
      })
      .filter((scenario) => scenario.utilization >= minUtilization)
      .sort((a, b) => b.profit - a.profit || b.roiPct - a.roiPct);
  }

  function createStateId(prefix) {
    return `${prefix}-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
  }

  function defaultManualFloors(typeKey) {
    return ["apartman", "site", "perakende", "ofis", "karma"].includes(typeKey) ? 2 : 1;
  }

  function createManualScenarioDraftEntry(typeKey) {
    const typeConfig = getBuildingTypeConfigByKey(typeKey);
    return {
      id: createStateId("draft"),
      typeKey,
      surfaceArea: clamp(typeConfig.unitArea, typeConfig.minArea, typeConfig.maxArea),
      floors: defaultManualFloors(typeKey),
    };
  }

  function getManualScenarioDraft(parcelKey) {
    if (!parcelKey) return [];
    if (!scenarioSelectState.manualDrafts[parcelKey]) {
      scenarioSelectState.manualDrafts[parcelKey] = [];
    }
    return scenarioSelectState.manualDrafts[parcelKey];
  }

  function addManualScenarioDraftEntry(parcelKey, typeKey) {
    if (!parcelKey || !typeKey) return;
    const nextDraft = [...getManualScenarioDraft(parcelKey), createManualScenarioDraftEntry(typeKey)];
    scenarioSelectState.manualDrafts[parcelKey] = nextDraft;
  }

  function updateManualScenarioDraftEntry(parcelKey, entryId, patch) {
    if (!parcelKey || !entryId) return;
    scenarioSelectState.manualDrafts[parcelKey] = getManualScenarioDraft(parcelKey).map((item) =>
      item.id === entryId ? { ...item, ...patch } : item
    );
  }

  function removeManualScenarioDraftEntry(parcelKey, entryId) {
    if (!parcelKey || !entryId) return;
    scenarioSelectState.manualDrafts[parcelKey] = getManualScenarioDraft(parcelKey).filter((item) => item.id !== entryId);
  }

  function clearManualScenarioDraft(parcelKey) {
    if (!parcelKey) return;
    scenarioSelectState.manualDrafts[parcelKey] = [];
  }

  function buildScenarioSourceEntry(candidateParcel) {
    if (!candidateParcel) return null;
    const key = getParcelCompareKey(candidateParcel);
    return getComparedParcelByKey(key) || (candidateParcel.feature ? buildComparedParcelEntry(candidateParcel.feature) : null);
  }

  function createScenarioComponentFromDraft(draft) {
    const typeConfig = getBuildingTypeConfigByKey(draft.typeKey);
    const surfaceArea = clamp(Number(draft.surfaceArea) || typeConfig.unitArea, typeConfig.minArea, typeConfig.maxArea);
    const floors = clamp(Math.round(Number(draft.floors) || 1), 1, 12);
    const usedM2 = surfaceArea * floors;
    const equivalentUnits = usedM2 / Math.max(typeConfig.unitArea, 1);
    return {
      typeKey: typeConfig.key,
      label: typeConfig.label,
      surfaceArea,
      floors,
      usedM2,
      equivalentUnits,
      typeConfig,
    };
  }

  function buildScenarioSelectionEntryFromDraft(sourceEntry, draftEntries, selectionId = null) {
    if (!sourceEntry || !draftEntries.length) return null;
    const parcelVariant = getPlanningParcelVariant(sourceEntry);
    const factorRows = buildParcelAnalysisFactorRowsFromUnits(sourceEntry.primaryUnits || [], sourceEntry.nearbyUnits || []);
    const adjustedSaleMap = computeAdjustedSaleValueMap(factorRows);
    const capacityM2 = calculateScenarioCapacity(parcelVariant);
    const components = draftEntries.map(createScenarioComponentFromDraft).map((component) => {
      const adjustedUnitSaleValue = adjustedSaleMap.get(component.typeKey) || component.typeConfig.unitSaleValue;
      const buildCost = component.equivalentUnits * component.typeConfig.unitCost;
      const revenue = component.equivalentUnits * adjustedUnitSaleValue;
      return {
        ...component,
        adjustedUnitSaleValue,
        buildCost,
        revenue,
      };
    });
    const usedM2 = components.reduce((sum, component) => sum + component.usedM2, 0);
    const buildCost = components.reduce((sum, component) => sum + component.buildCost, 0);
    const revenue = components.reduce((sum, component) => sum + component.revenue, 0);
    const otherCosts = buildCost * 0.08;
    const totalCost = buildCost + otherCosts + parcelVariant.landCost;
    const profit = revenue - totalCost;
    const roiPct = totalCost > 0 ? (profit / totalCost) * 100 : 0;
    const irrPct = totalCost > 0 ? ((revenue / totalCost) ** (12 / planningSettings.projectMonths) - 1) * 100 : 0;
    const utilization = capacityM2 > 0 ? usedM2 / capacityM2 : 0;
    return {
      selectionId: selectionId || createStateId("selection"),
      key: sourceEntry.key,
      ref: sourceEntry.ref,
      regionLabel: sourceEntry.regionLabel,
      areaM2: parcelVariant.areaM2,
      landCost: parcelVariant.landCost,
      primaryUnits: sourceEntry.primaryUnits || [],
      nearbyUnits: sourceEntry.nearbyUnits || [],
      slopePct: sourceEntry.slopePct,
      perimeterM: sourceEntry.perimeterM,
      emptyLandSignal: sourceEntry.emptyLandSignal,
      feature: sourceEntry.feature,
      factorRows,
      adjustedSaleMap,
      scenario: {
        name: components
          .map((component, index) => `${index + 1}. ${component.label} (${formatNumber(component.surfaceArea, 0)} mÃ‚Â², ${component.floors} kat)`)
          .join(" + "),
        shortName: components.map((component) => component.label).join(" + "),
        buildCost,
        revenue,
        otherCosts,
        totalCost,
        profit,
        roiPct,
        irrPct,
        usedM2,
        capacityM2,
        utilization,
        units: components.length,
        typeConfig: components[0]?.typeConfig || null,
        components,
      },
      overCapacity: usedM2 > capacityM2,
    };
  }

  function addScenarioSelectionToCompare(sourceEntry, draftEntries) {
    const entry = buildScenarioSelectionEntryFromDraft(sourceEntry, draftEntries);
    if (!entry) return { changed: false, entry: null, reason: "empty" };
    if (entry.overCapacity) return { changed: false, entry, reason: "capacity" };
    selectedScenarioComparisons = [...selectedScenarioComparisons, entry].slice(-10);
    renderWorkspace();
    return { changed: true, entry, reason: null };
  }

  function removeScenarioSelectionById(selectionId) {
    const existing = selectedScenarioComparisons.find((item) => item.selectionId === selectionId) || null;
    if (!existing) return { changed: false, entry: null };
    selectedScenarioComparisons = selectedScenarioComparisons.filter((item) => item.selectionId !== selectionId);
    renderWorkspace();
    return { changed: true, entry: existing };
  }

  function clearScenarioSelections() {
    if (!selectedScenarioComparisons.length) return;
    selectedScenarioComparisons = [];
    renderWorkspace();
  }

  function renderScenarioAutoTable(rows) {
    if (!rows.length) {
      return '<div class="workspace-empty">Bu ayarlarla ÃƒÂ¼retilebilen senaryo bulunamadÃ„Â±.</div>';
    }
    const header = `
      <div class="scenario-table-row scenario-table-head">
        <span>Senaryo</span>
        <span>KullanÃ„Â±m</span>
        <span>Doluluk</span>
        <span>Toplam Maliyet</span>
        <span>Gelir</span>
        <span>KÃƒÂ¢r</span>
        <span>ROI</span>
      </div>
    `;
    const body = rows
      .map(
        (scenario) => `
          <div class="scenario-table-row">
            <span>${scenario.name}</span>
            <span>${formatNumber(scenario.usedM2, 0)} mÃ‚Â²</span>
            <span>${formatNumber(scenario.utilization * 100, 0)}%</span>
            <span>${formatMoney(scenario.totalCost)}</span>
            <span>${formatMoney(scenario.revenue)}</span>
            <span>${formatMoney(scenario.profit)}</span>
            <span>%${formatNumber(scenario.roiPct, 1)}</span>
          </div>
        `
      )
      .join("");
    return `<div class="scenario-table">${header}${body}</div>`;
  }

  function renderManualScenarioEntryCards(draftEntries) {
    if (!draftEntries.length) {
      return '<div class="workspace-empty">Asagidan bir yapi turu ekleyerek kullanici senaryosunu kuralim.</div>';
    }
    return `
      <div class="manual-entry-list">
        ${draftEntries
          .map((draft, index) => {
            const typeConfig = getBuildingTypeConfigByKey(draft.typeKey);
            return `
              <div class="manual-entry-card">
                <div class="workspace-row workspace-action-row">
                  <div class="manual-entry-title">${index + 1}. ${typeConfig.label}</div>
                  <button class="workspace-button subtle" type="button" data-delete-manual-entry="${draft.id}">Sil</button>
                </div>
                <label class="field-label">${typeConfig.label} yuzey alani (mÃ‚Â²)</label>
                <div class="manual-range-wrap">
                  <div class="manual-range-value">${formatNumber(draft.surfaceArea, 2)}</div>
                  <input
                    type="range"
                    min="${typeConfig.minArea}"
                    max="${typeConfig.maxArea}"
                    step="10"
                    value="${draft.surfaceArea}"
                    data-manual-surface="${draft.id}"
                  />
                </div>
                <label class="field-label">${typeConfig.label} kat sayisi</label>
                <div class="manual-range-wrap">
                  <div class="manual-range-value">${draft.floors}</div>
                  <input
                    type="range"
                    min="1"
                    max="8"
                    step="1"
                    value="${draft.floors}"
                    data-manual-floors="${draft.id}"
                  />
                </div>
              </div>
            `;
          })
          .join("")}
      </div>
    `;
  }

  function renderScenarioSelectionSummaryCards(selectionEntry) {
    if (!selectionEntry) {
      return '<div class="workspace-empty">Sonuc olusturmak icin en az bir yapi turu ekleyelim.</div>';
    }
    const warning = selectionEntry.overCapacity
      ? `<div class="settings-warning">Toplam kullanim ${formatNumber(selectionEntry.scenario.usedM2, 0)} mÃ‚Â², parcel kapasitesi olan ${formatNumber(
          selectionEntry.scenario.capacityM2,
          0
        )} mÃ‚Â² degerini asiyor. Karsilastirmaya eklemeden once kullanim dusurulmeli.</div>`
      : "";
    return `
      ${warning}
      <div class="workspace-note">Toplam kullanim: ${formatNumber(selectionEntry.scenario.usedM2, 0)} mÃ‚Â² / ${formatNumber(
        selectionEntry.scenario.capacityM2,
        0
      )} mÃ‚Â²</div>
      <div class="metric-grid">
        <div class="metric-card"><div class="metric-card-label">Tahmini Arsa Maliyeti</div><div class="metric-card-value">${formatMoney(selectionEntry.landCost)}</div></div>
        <div class="metric-card"><div class="metric-card-label">Yapi Maliyeti</div><div class="metric-card-value">${formatMoney(selectionEntry.scenario.buildCost)}</div></div>
        <div class="metric-card"><div class="metric-card-label">Gelir</div><div class="metric-card-value">${formatMoney(selectionEntry.scenario.revenue)}</div></div>
        <div class="metric-card"><div class="metric-card-label">Kar</div><div class="metric-card-value">${formatMoney(selectionEntry.scenario.profit)}</div></div>
      </div>
      <div class="workspace-note">ROI: ${formatNumber(selectionEntry.scenario.roiPct, 2)} Ã‚Â· IRR: ${formatNumber(
        selectionEntry.scenario.irrPct,
        2
      )} Ã‚Â· Doluluk: %${formatNumber(selectionEntry.scenario.utilization * 100, 0)}</div>
    `;
  }

  function renderPlanningSettingsPanel(candidates) {
    const averageRows = computeAverageFactorRows();
    const parcelRows = candidates.length
      ? candidates
          .map(
            (item) => `
              <tr>
                <td>${item.parcel.ref}</td>
                <td>${item.parcel.regionLabel}</td>
                <td><input type="number" data-parcel-area="${encodeURIComponent(item.key)}" value="${Math.round(item.parcel.areaM2)}" min="1" step="10" /></td>
                <td><input type="number" data-parcel-cost="${encodeURIComponent(item.key)}" value="${Math.round(item.parcel.landCost)}" min="0" step="10000" /></td>
              </tr>
            `
          )
          .join("")
      : '<tr><td colspan="4">HenÃƒÂ¼z seÃƒÂ§ilebilir parcel bulunamadÃ„Â±.</td></tr>';
    const buildingRows = planningSettings.buildingTypes
      .map(
        (item) => `
          <tr>
            <td>${item.key}</td>
            <td>${item.label}</td>
            <td><input type="number" data-building-field="unitArea" data-building-key="${item.key}" value="${item.unitArea}" min="1" step="10" /></td>
            <td><input type="number" data-building-field="minArea" data-building-key="${item.key}" value="${item.minArea}" min="1" step="10" /></td>
            <td><input type="number" data-building-field="maxArea" data-building-key="${item.key}" value="${item.maxArea}" min="1" step="10" /></td>
            <td><input type="number" data-building-field="unitCost" data-building-key="${item.key}" value="${item.unitCost}" min="0" step="10000" /></td>
            <td><input type="number" data-building-field="unitSaleValue" data-building-key="${item.key}" value="${item.unitSaleValue}" min="0" step="10000" /></td>
          </tr>
        `
      )
      .join("");
    const factorHeader = `
      <tr>
        <th>FaktÃƒÂ¶r / YapÃ„Â± TÃƒÂ¼rÃƒÂ¼</th>
        <th>MÃƒÂ¼stakil Ev</th>
        <th>Apartman</th>
        <th>Site</th>
        <th>Prefabrik</th>
        <th>Perakende</th>
        <th>Ofis</th>
        <th>Karma</th>
        <th>EndÃƒÂ¼striyel</th>
        <th>TarÃ„Â±msal</th>
      </tr>
    `;
    const factorRows = planningSettings.factorMatrix
      .map(
        (row) => `
          <tr>
            <td>${row.factor}</td>
            <td>${row.mustakil}</td>
            <td>${row.apartman}</td>
            <td>${row.site}</td>
            <td>${row.prefab}</td>
            <td>${row.perakende}</td>
            <td>${row.ofis}</td>
            <td>${row.karma}</td>
            <td>${row.endustriyel}</td>
            <td>${row.tarimsal}</td>
          </tr>
        `
      )
      .join("");
    const averageTableRows = averageRows
      .map(
        (row, idx) => `
          <tr>
            <td>${idx}</td>
            <td>${row.label}</td>
            <td>${formatNumber(row.average, 4)}</td>
          </tr>
        `
      )
      .join("");
    return `
      <div class="workspace-section settings-hero">
        <div class="workspace-note settings-warning">Uygulama, aÃ…Å¸aÃ„Å¸Ã„Â±daki varsayÃ„Â±mlar ile ÃƒÂ§alÃ„Â±Ã…Å¸Ã„Â±r. Ã„Â°stersen buradan deÃ„Å¸iÃ…Å¸tirip kaydedebilirsin.</div>
        <h3 class="workspace-section-title settings-title">Uygulama aÃƒÂ§Ã„Â±lmadan ÃƒÂ¶nce temel varsayÃ„Â±mlarÃ„Â± girin ve onaylayÃ„Â±n.</h3>
        <div class="workspace-note">Devam ederseniz, sistem varsayÃ„Â±lan deÃ„Å¸erlerle baÃ…Å¸lar. Ã„Â°sterseniz burada deÃ„Å¸iÃ…Å¸tirebilirsiniz.</div>
        <div class="settings-grid">
          <div>
            <label class="field-label" for="planningUsableRatio">KullanÃ„Â±labilir arsa ÃƒÂ§arpanÃ„Â±</label>
            <input id="planningUsableRatio" type="number" min="0.1" max="1" step="0.05" value="${planningSettings.usableRatio}" />
          </div>
          <div>
            <label class="field-label" for="planningCapacityMethod">Kapasite hesabÃ„Â± yÃƒÂ¶ntemi</label>
            <select id="planningCapacityMethod">
              <option value="Taban AlanÃ„Â±" ${planningSettings.capacityMethod === "Taban AlanÃ„Â±" ? "selected" : ""}>Taban AlanÃ„Â±</option>
              <option value="SatÃ„Â±labilir Alan" ${planningSettings.capacityMethod === "SatÃ„Â±labilir Alan" ? "selected" : ""}>SatÃ„Â±labilir Alan</option>
            </select>
          </div>
          <div>
            <label class="field-label" for="planningFar">KAKS / FAR</label>
            <input id="planningFar" type="number" min="0.5" max="5" step="0.1" value="${planningSettings.far}" />
          </div>
          <div>
            <label class="field-label" for="planningProjectMonths">Proje sÃƒÂ¼resi (ay) Ã¢â‚¬â€ IRR iÃƒÂ§in</label>
            <input id="planningProjectMonths" type="number" min="6" max="60" step="1" value="${planningSettings.projectMonths}" />
          </div>
        </div>
      </div>
      <div class="workspace-section">
        <h3 class="workspace-section-title">Parsel deÃ„Å¸erleri (alan ve arsa maliyeti)</h3>
        <div class="workspace-note">Web sÃƒÂ¼rÃƒÂ¼mÃƒÂ¼nde sadece eriÃ…Å¸ilebilir seÃƒÂ§ili parselleri dÃƒÂ¼zenliyoruz.</div>
        <div class="settings-table-wrap">
          <table class="settings-table">
            <thead>
              <tr><th>Parsel ID</th><th>BÃƒÂ¶lge</th><th>Arsa alanÃ„Â± (mÃ‚Â²)</th><th>Tahmini arsa maliyeti (TRY)</th></tr>
            </thead>
            <tbody>${parcelRows}</tbody>
          </table>
        </div>
      </div>
      <div class="workspace-section">
        <h3 class="workspace-section-title">YapÃ„Â± tÃƒÂ¼rleri (birim alan / maliyet / satÃ„Â±Ã…Å¸ deÃ„Å¸eri)</h3>
        <div class="settings-table-wrap">
          <table class="settings-table">
            <thead>
              <tr><th>key</th><th>YapÃ„Â± tÃƒÂ¼rÃƒÂ¼</th><th>Birim alanÃ„Â± (mÃ‚Â²)</th><th>Min (mÃ‚Â²)</th><th>Max (mÃ‚Â²)</th><th>Birim maliyet (TRY)</th><th>Birim satÃ„Â±Ã…Å¸ deÃ„Å¸eri (TRY)</th></tr>
            </thead>
            <tbody>${buildingRows}</tbody>
          </table>
        </div>
      </div>
      <div class="workspace-section">
        <h3 class="workspace-section-title">Mesafe ve YapÃ„Â± TÃƒÂ¼rÃƒÂ¼ DeÃ„Å¸er Analiz Tablosu</h3>
        <div class="workspace-note">AÃ…Å¸aÃ„Å¸Ã„Â±daki katsayÃ„Â±larÃ„Â± deÃ„Å¸iÃ…Å¸tirmezseniz, sistem varsayÃ„Â±lan deÃ„Å¸erlerle devam eder.</div>
        <div class="settings-table-wrap">
          <table class="settings-table">
            <thead>${factorHeader}</thead>
            <tbody>${factorRows}</tbody>
          </table>
        </div>
      </div>
      <div class="workspace-section">
        <h3 class="workspace-section-title">Ortalama katsayÃ„Â±lar (bilgilendirme)</h3>
        <div class="settings-table-wrap">
          <table class="settings-table">
            <thead><tr><th></th><th>YapÃ„Â± TÃƒÂ¼rÃƒÂ¼</th><th>Ortalama KatsayÃ„Â±</th></tr></thead>
            <tbody>${averageTableRows}</tbody>
          </table>
        </div>
        <div class="settings-actions">
          <button class="workspace-button" type="button" data-settings-reset="true">VarsayÃ„Â±lanlara DÃƒÂ¶n</button>
          <button class="workspace-button workspace-button-primary" type="button" data-settings-confirm="true">Onayla ve Devam Et</button>
        </div>
      </div>
    `;
  }

  function renderWorkspace() {
    if (!workspaceContentEl) return;
    const setWorkspaceHtml = (html) => setSanitizedHtml(workspaceContentEl, html);
    renderScreenMenu();
    if (mapStageEl) {
      mapStageEl.dataset.screen = activeWorkspaceScreen;
    }
    const parcel = getParcelModel();
    const scenarios = generateScenarioModels(parcel);
    const best = bestScenario(parcel);
    const insights = buildParcelInsights(parcel);
    const unitsOverviewBlock = parcel
      ? renderUnitsOverviewSection(insights.primaryUnits, insights.nearbyUnits)
      : "";
    const parcelCompareActionBlock = parcel ? renderParcelCompareAction(parcel) : "";
    const parcelDetailsBlock = parcel ? renderParcelDetailsAccordion(parcel) : "";
    const salesOnlyModeActive = isSalesOnlyModeActive();

    if (parcel && salesOnlyModeActive) {
      setWorkspaceHtml(`
        <div class="workspace-panel">
          ${renderSalesOnlyWorkspace(parcel)}
        </div>
      `);
      return;
    }

    if (!parcel && !["portfolio", "parcel", "compare", "contact", "scenario_select"].includes(activeWorkspaceScreen)) {
      setWorkspaceHtml(`
        <div class="workspace-panel">
          <div class="workspace-empty">Bu paneli doldurmak icin haritadan bir parcel secelim. Sonra ayni ekranda PortfÃƒÂ¶y, Ãƒâ€“neri, Senaryo ve KarÃ…Å¸Ã„Â±laÃ…Å¸tÃ„Â±rma akÃ„Â±Ã…Å¸Ã„Â±nÃ„Â± web uygulamada kullanabiliriz.</div>
        </div>
      `);
      return;
    }

    if (activeWorkspaceScreen === "portfolio") {
      setWorkspaceHtml(`
        <div class="workspace-panel">
          ${
            parcel
              ? `
                <div class="metric-grid">
                  <div class="metric-card"><div class="metric-card-label">SeÃƒÂ§ili Parcel</div><div class="metric-card-value">${parcel.ref}</div></div>
                  <div class="metric-card"><div class="metric-card-label">Aktif BÃƒÂ¶lge</div><div class="metric-card-value">${parcel.regionLabel}</div></div>
                  <div class="metric-card"><div class="metric-card-label">Alan</div><div class="metric-card-value">${formatNumber(parcel.areaM2, 0)} mÃ‚Â²</div></div>
                  <div class="metric-card"><div class="metric-card-label">Tahmini Arsa Maliyeti</div><div class="metric-card-value">${formatMoney(parcel.landCost)}</div></div>
                </div>
                ${unitsOverviewBlock}
                ${parcelCompareActionBlock}
                ${parcelDetailsBlock}
                ${renderLandIntelligenceSection(parcel)}
              `
              : `<div class="workspace-note">Detay kartlarini doldurmak icin haritadan bir parcel sec. KarÃ…Å¸Ã„Â±laÃ…Å¸tÃ„Â±rma listesi ise aÃ…Å¸aÃ„Å¸Ã„Â±da gÃƒÂ¶rÃƒÂ¼nmeye devam eder.</div>`
          }
          <div class="workspace-section">
            <h3 class="workspace-section-title">KarÃ…Å¸Ã„Â±laÃ…Å¸tÃ„Â±rma Listesine Eklenen Parseller</h3>
            <div class="workspace-note">Haritadan parcel seÃƒÂ§ince popup ve saÃ„Å¸ panel ÃƒÂ¼zerinde + / - aksiyonu gÃƒÂ¶rÃƒÂ¼nÃƒÂ¼r. KarÃ…Å¸Ã„Â±laÃ…Å¸tÃ„Â±rmadaki parseller koyu gÃƒÂ¶rÃƒÂ¼nÃƒÂ¼r.</div>
            ${renderComparedParcelsList(true)}
          </div>
        </div>
      `);
    } else if (activeWorkspaceScreen === "parcel") {
      const analysisEntries = comparedParcels;
      ensureComparedParcelsLandIntelligence(analysisEntries);
      setWorkspaceHtml(`
        <div class="workspace-panel">
          <div class="workspace-section">
            <h2 class="workspace-page-title">Ãƒâ€“neri SonuÃƒÂ§larÃ„Â± Ã¢â‚¬â€ Parsel Analizi</h2>
            ${
              analysisEntries.length
                ? `<div class="workspace-note">Bu ekran artÃ„Â±k karÃ…Å¸Ã„Â±laÃ…Å¸tÃ„Â±rma listesindeki gÃƒÂ¼ncel parselleri birlikte gÃƒÂ¶sterir. Listeden ÃƒÂ§Ã„Â±karÃ„Â±lan parseller burada gÃƒÂ¶rÃƒÂ¼nmez.</div>`
                : '<div class="workspace-note">Parsel Analizi ekranÃ„Â±nÃ„Â± doldurmak iÃƒÂ§in ÃƒÂ¶nce haritadan parselleri karÃ…Å¸Ã„Â±laÃ…Å¸tÃ„Â±rma listesine ekleyelim.</div>'
            }
          </div>
          ${
            analysisEntries.length
              ? `
                ${parcel ? renderLandIntelligenceSection(parcel) : ""}
                ${renderParcelAnalysisSummaryTable(analysisEntries)}
                ${renderBuildingTypeCoefficientTable()}
                ${renderParcelAnalysisEntrySections(analysisEntries)}
              `
              : '<div class="workspace-empty">KarÃ…Å¸Ã„Â±laÃ…Å¸tÃ„Â±rma listesi boÃ…Å¸. Haritadan bir parsele tÃ„Â±klayÃ„Â±p + ile ekledikten sonra bu ekran ÃƒÂ§oklu karÃ…Å¸Ã„Â±laÃ…Å¸tÃ„Â±rmalÃ„Â± dolacaktÃ„Â±r.</div>'
          }
        </div>
      `);
    } else if (activeWorkspaceScreen === "recommendation") {
      const scoreCard = computeRecommendationScoreCard(parcel, insights, best);
      const factorRows = buildParcelAnalysisFactorRows(insights);
      const financeRows = best
        ? `
          <div class="workspace-stack">
            <div class="workspace-row"><span>Toplam Maliyet</span><strong>${formatMoney(best.totalCost)}</strong></div>
            <div class="workspace-row"><span>SatÃ„Â±Ã…Å¸ Geliri</span><strong>${formatMoney(best.revenue)}</strong></div>
            <div class="workspace-row"><span>Tahmini Arsa Maliyeti</span><strong>${formatMoney(parcel.landCost)}</strong></div>
            <div class="workspace-row"><span>Ã„Â°nÃ…Å¸aat KÃƒÂ¢rlÃ„Â±lÃ„Â±Ã„Å¸Ã„Â±</span><strong>${formatMoney(best.profit)}</strong></div>
          </div>
        `
        : '<div class="workspace-note">Finansal ÃƒÂ¶zet ÃƒÂ¼retilemedi.</div>';
      setWorkspaceHtml(`
        <div class="workspace-panel">
          <div class="workspace-section">
            <h2 class="workspace-page-title">Ãƒâ€“neri Motoru Ã¢â‚¬â€ Ãƒâ€“neri Ãƒâ€“zeti</h2>
            <div class="workspace-stack">
              <label class="field-label">Parsel ID</label>
              <div class="workspace-input-mimic">${parcel.ref}</div>
            </div>
          </div>
          <div class="workspace-section">
            <h3 class="workspace-section-title">Ãƒâ€“nerilen YapÃ„Â± TÃƒÂ¼rÃƒÂ¼: ${best ? best.name : "-"}</h3>
            <div class="workspace-note"><strong>Model GÃƒÂ¼ven DÃƒÂ¼zeyi:</strong> ${formatNumber(scoreCard.confidence, 2)}</div>
          </div>
          <div class="workspace-section">
            <h3 class="workspace-section-title">Ãƒâ€¡ok Kriterli DeÃ„Å¸erlendirme Ãƒâ€“zeti</h3>
            <div class="workspace-stack">
              <div class="workspace-note">Ã„Â°mar uygunluÃ„Å¸u (stub) ve pazar sinyali birlikte ele alÃ„Â±nÃ„Â±r.</div>
              <div class="workspace-note">Konum/eriÃ…Å¸im, piyasa ve arsa ÃƒÂ¶zellikleri ayrÃ„Â± skorlanÃ„Â±r.</div>
              <div class="workspace-note">AÃ„Å¸Ã„Â±rlÃ„Â±klÃ„Â± skor ile alternatifler kÃ„Â±yaslanÃ„Â±r.</div>
            </div>
          </div>
          <div class="workspace-section">
            <h3 class="workspace-section-title">Ãƒâ€¡ok Kriterli Skor KartÃ„Â±</h3>
            ${renderScoreBar("Konum", scoreCard.location)}
            ${renderScoreBar("Piyasa", scoreCard.market)}
            ${renderScoreBar("Arsa Ãƒâ€“zellikleri", scoreCard.land)}
            <div class="metric-grid">
              <div class="metric-card"><div class="metric-card-label">Genel Skor</div><div class="metric-card-value">${formatNumber(scoreCard.general, 1)}/10</div></div>
              <div class="metric-card"><div class="metric-card-label">Tahmini IRR</div><div class="metric-card-value">${best ? formatNumber(best.irrPct, 1) : "-"}%</div></div>
            </div>
          </div>
          <div class="workspace-section">
            <h3 class="workspace-section-title">Arsa Profili</h3>
            <div class="workspace-stack">
              <div class="workspace-row"><span>Alan</span><strong>${formatNumber(parcel.areaM2, 2)} mÃ‚Â²</strong></div>
              <div class="workspace-row"><span>EÃ„Å¸im</span><strong>%${formatNumber(parcel.slopePct, 1)}</strong></div>
              <div class="workspace-row"><span>Ãƒâ€¡evre Bilgisi</span><strong>Arsa ÃƒÂ§evresi ${formatDistanceMeters(parcel.perimeterM)}</strong></div>
              <div class="workspace-row"><span>BoÃ…Å¸ arazi sinyali</span><strong>%${formatNumber(parcel.emptyLandSignal * 100, 0)}</strong></div>
            </div>
          </div>
          ${renderParcelAnalysisDistanceTable(parcel, factorRows)}
          ${renderBuildingTypeCoefficientTable()}
          ${renderRecommendationGeometricTables(parcel, insights)}
          ${unitsOverviewBlock}
          ${renderLandIntelligenceSection(parcel)}
          <div class="workspace-section">
            <h3 class="workspace-section-title">Finansal Ãƒâ€“zet</h3>
            ${financeRows}
          </div>
          <div class="workspace-section">
            <h3 class="workspace-section-title">DiÃ„Å¸er Senaryolar</h3>
            <div class="workspace-stack">${renderScenarioCards(parcel, scenarios.slice().sort((a, b) => b.irrPct - a.irrPct))}</div>
          </div>
        </div>
      `);
    } else if (activeWorkspaceScreen === "scenario_select") {
      const candidates = getScenarioSelectCandidates(parcel);
      const manualRef = (scenarioSelectState.manualParcelRef || "").trim();
      let selectedCandidate =
        candidates.find((item) => item.key === scenarioSelectState.parcelKey) ||
        (manualRef
          ? candidates.find((item) => String(item.parcel.ref).toLowerCase() === manualRef.toLowerCase())
          : null) ||
        candidates[0] ||
        null;
      if (selectedCandidate && scenarioSelectState.parcelKey !== selectedCandidate.key) {
        scenarioSelectState.parcelKey = selectedCandidate.key;
      }
      const scenarioParcel = selectedCandidate?.parcel || null;
      const scenarioSourceEntry = buildScenarioSourceEntry(scenarioParcel);
      const allowedTypes = WORKSPACE_SCENARIOS.filter((name) => scenarioSelectState.allowedTypes.includes(name));
      const autoRows = scenarioParcel ? buildScenarioSelectionRows(scenarioParcel, allowedTypes, scenarioSelectState.minUtil) : [];
      const bestAuto = autoRows[0] || null;
      const selectedScenario =
        autoRows.find((scenario) => scenario.name === scenarioSelectState.selectedScenarioName) ||
        bestAuto ||
        null;
      scenarioSelectState.selectedScenarioName = selectedScenario ? selectedScenario.name : null;
      const manualDraftEntries = selectedCandidate ? getManualScenarioDraft(selectedCandidate.key) : [];
      const manualSelectionPreview = scenarioSourceEntry
        ? buildScenarioSelectionEntryFromDraft(scenarioSourceEntry, manualDraftEntries, "preview-selection")
        : null;
      setWorkspaceHtml(`
        <div class="workspace-panel">
          <div class="workspace-section">
            <div class="workspace-row workspace-action-row">
              <h2 class="workspace-page-title">Parsel ve Senaryo SeÃƒÂ§imi (Parsel BazlÃ„Â±)</h2>
              <button class="workspace-button" type="button" data-toggle-scenario-settings="true">${scenarioSelectState.showSettings ? "AyarlarÃ„Â± Gizle" : "VarsayÃ„Â±mlarÃ„Â± DÃƒÂ¼zenle"}</button>
            </div>
          </div>
          ${scenarioSelectState.showSettings ? renderPlanningSettingsPanel(candidates) : ""}
          <div class="workspace-section">
            <h3 class="workspace-section-title">Parsel SeÃƒÂ§imi</h3>
            ${
              candidates.length
                ? `
                  <label class="field-label" for="scenarioSelectParcel">Parsel seÃƒÂ§ (KarÃ…Å¸Ã„Â±laÃ…Å¸tÃ„Â±rmaya eklenenler)</label>
                  <select id="scenarioSelectParcel">
                    ${candidates
                      .map(
                        (item) => `<option value="${encodeURIComponent(item.key)}" ${
                          selectedCandidate && selectedCandidate.key === item.key ? "selected" : ""
                        }>${item.parcel.ref} Ã‚Â· ${formatNumber(item.parcel.areaM2, 0)} mÃ‚Â² Ã‚Â· ${item.parcel.regionLabel}</option>`
                      )
                      .join("")}
                  </select>
                `
                : '<div class="workspace-note">KarÃ…Å¸Ã„Â±laÃ…Å¸tÃ„Â±rmaya eklenmiÃ…Å¸ parcel yok. Haritadan bir parcel seÃƒÂ§ip + ile ekleyebilir ya da mevcut seÃƒÂ§ili parcel ÃƒÂ¼zerinden ilerleyebilirsin.</div>'
            }
            <label class="field-label" for="scenarioSelectManual">Parsel ID ile seÃƒÂ§</label>
            <input id="scenarioSelectManual" type="text" value="${manualRef}" placeholder="Parsel ID gir" />
            ${
              selectedCandidate
                ? `<div class="workspace-note">${selectedCandidate.parcel.ref} Ã‚Â· ${selectedCandidate.parcel.regionLabel} Ã‚Â· ${formatNumber(
                    selectedCandidate.parcel.areaM2,
                    0
                  )} mÃ‚Â²</div>`
                : '<div class="workspace-note">HenÃƒÂ¼z kullanÃ„Â±labilir bir parcel bulunamadÃ„Â±.</div>'
            }
          </div>
          <div class="workspace-section">
            <h3 class="workspace-section-title">Otomatik Senaryo ÃƒÅ“retimi</h3>
            <div class="metric-grid">
              <div class="metric-card">
                <div class="metric-card-label">Senaryo sayÃ„Â±sÃ„Â± (otomatik)</div>
                <div class="metric-card-value">${scenarioSelectState.maxScenarios}</div>
                <input id="scenarioMaxScenarios" type="range" min="30" max="500" step="10" value="${scenarioSelectState.maxScenarios}" />
              </div>
              <div class="metric-card">
                <div class="metric-card-label">Min doluluk</div>
                <div class="metric-card-value">%${formatNumber(scenarioSelectState.minUtil * 100, 0)}</div>
                <input id="scenarioMinUtil" type="range" min="10" max="100" step="5" value="${scenarioSelectState.minUtil * 100}" />
              </div>
            </div>
            <div class="workspace-section-title">Dahil edilecek yapÃ„Â± tÃƒÂ¼rleri</div>
            <div class="option-chip-grid">
              ${WORKSPACE_SCENARIOS.map(
                (name) => `
                  <label class="option-chip" data-active="${scenarioSelectState.allowedTypes.includes(name)}">
                    <input type="checkbox" data-scenario-type="${name}" ${scenarioSelectState.allowedTypes.includes(name) ? "checked" : ""} />
                    <span>${name}</span>
                  </label>
                `
              ).join("")}
            </div>
            ${
              scenarioParcel
                ? `<div class="workspace-note"><strong>Parsel alanÃ„Â±:</strong> ${formatNumber(scenarioParcel.areaM2, 0)} mÃ‚Â² Ã‚Â· <strong>KullanÃ„Â±labilir kapasite:</strong> ${formatNumber(
                    Math.max(scenarioParcel.areaM2 * 0.9, 1200),
                    0
                  )} mÃ‚Â² Ã‚Â· <strong>Tahmini arsa maliyeti:</strong> ${formatMoney(scenarioParcel.landCost)}</div>`
                : ""
            }
            ${
              bestAuto
                ? `<div class="workspace-note"><strong>En kÃƒÂ¢rlÃ„Â± otomatik senaryo:</strong> ${bestAuto.name} Ã‚Â· KÃƒÂ¢r: ${formatMoney(bestAuto.profit)} Ã‚Â· ROI: %${formatNumber(
                    bestAuto.roiPct,
                    1
                  )}</div>`
                : ""
            }
            ${renderScenarioAutoTable(autoRows.slice(0, Math.max(1, Math.min(autoRows.length, scenarioSelectState.maxScenarios))))}
          </div>
          <div class="workspace-section">
            <h3 class="workspace-section-title">Senaryo SeÃƒÂ§imi (KullanÃ„Â±cÃ„Â±)</h3>
            <div class="workspace-note">Asagidan yapi turu ekleyelim. Her ekleme icin yuzey alani ve kat sayisi ayri belirlenir.</div>
            <div class="option-chip-grid">
              ${planningSettings.buildingTypes
                .map(
                  (type) => `
                    <button class="option-chip option-chip-button" type="button" data-add-manual-type="${type.key}">
                      <span>${type.label} +</span>
                    </button>
                  `
                )
                .join("")}
            </div>
            ${renderManualScenarioEntryCards(manualDraftEntries)}
          </div>
          <div class="workspace-section">
            <h3 class="workspace-section-title">SonuÃƒÂ§</h3>
            ${renderScenarioSelectionSummaryCards(manualSelectionPreview)}
          </div>
          ${scenarioParcel ? renderLandIntelligenceSection(scenarioParcel) : ""}
          <div class="workspace-section">
            <h3 class="workspace-section-title">KarÃ…Å¸Ã„Â±laÃ…Å¸tÃ„Â±rma Listesi</h3>
            <div class="workspace-note">En az 2 ve en fazla 10 senaryo karÃ…Å¸Ã„Â±laÃ…Å¸tÃ„Â±rabiliriz.</div>
            <div class="workspace-row workspace-action-row">
              <button
                class="workspace-button"
                type="button"
                data-add-scenario-selection="true"
                ${manualSelectionPreview && !manualSelectionPreview.overCapacity ? "" : "disabled"}
              >SeÃƒÂ§imi KarÃ…Å¸Ã„Â±laÃ…Å¸tÃ„Â±rma Listesine Ekle</button>
              <button
                class="workspace-button subtle"
                type="button"
                data-reset-manual-selection="true"
                ${manualDraftEntries.length ? "" : "disabled"}
              >SeÃƒÂ§imi Temizle</button>
            </div>
            ${
              selectedScenarioComparisons.length
                ? renderSelectedScenariosCards(selectedScenarioComparisons)
                : '<div class="workspace-empty">Henuz karsilastirmaya eklenen bir kullanici senaryosu yok.</div>'
            }
          </div>
        </div>
      `);
    } else if (activeWorkspaceScreen === "compare") {
      const compareEntries = selectedScenarioComparisons.slice();
      ensureComparedParcelsLandIntelligence(compareEntries);
      setWorkspaceHtml(`
        <div class="workspace-panel">
          <div class="workspace-section">
            <h2 class="workspace-page-title">KarÃ…Å¸Ã„Â±laÃ…Å¸tÃ„Â±rma (ROI/IRR) Ã¢â‚¬â€ SeÃƒÂ§ilen Senaryolar</h2>
            ${
              !compareEntries.length
                ? '<div class="workspace-empty">Arsa & Senaryo SeÃƒÂ§imi ekraninda bir senaryo kurup karsilastirma listesine ekleyelim.</div>'
                : `
                  <div class="workspace-note">Streamlit akÃ„Â±Ã…Å¸Ã„Â±ndaki gibi seÃƒÂ§ilen parseller, seÃƒÂ§ilen senaryolar ve detay tablolarÃ„Â± aÃ…Å¸aÃ„Å¸Ã„Â±da birlikte gÃƒÂ¶steriliyor.</div>
                  <div class="workspace-row workspace-action-row">
                    <span>SeÃƒÂ§ilen Senaryolar</span>
                    <button class="workspace-button" type="button" data-clear-scenario-selections="true">TÃƒÂ¼m listeyi temizle</button>
                  </div>
                  ${renderSelectedScenariosCards(compareEntries)}
                  ${renderSelectedParcelsTable(compareEntries)}
                  ${renderCompareSignalSummaryTable(compareEntries)}
                  ${renderParcelFeaturesAndDistances(compareEntries)}
                  ${renderCompareResultsTable(compareEntries)}
                  ${renderScenarioDetailsByBuildingType(compareEntries)}
                  ${renderCompareSignalDetails(compareEntries)}
                `
            }
          </div>
        </div>
      `);
    } else if (activeWorkspaceScreen === "scenario_compare") {
      const compareEntries = selectedScenarioComparisons.slice();
      ensureComparedParcelsLandIntelligence(compareEntries);
      setWorkspaceHtml(`
        <div class="workspace-panel">
          <div class="workspace-section">
            <h2 class="workspace-page-title">Senaryo KarÃ…Å¸Ã„Â±laÃ…Å¸tÃ„Â±rma Ã¢â‚¬â€ SeÃƒÂ§ilen Senaryolar</h2>
            ${
              !compareEntries.length
                ? '<div class="workspace-empty">Senaryo karÃ…Å¸Ã„Â±laÃ…Å¸tÃ„Â±rmasÃ„Â± iÃƒÂ§in once birkac kullanici senaryosu ekleyelim.</div>'
                : `
                  <div class="workspace-row workspace-action-row">
                    <span>SeÃƒÂ§ilen Senaryolar</span>
                    <button class="workspace-button" type="button" data-clear-scenario-selections="true">TÃƒÂ¼m listeyi temizle</button>
                  </div>
                  ${renderSelectedScenariosCards(compareEntries)}
                  ${renderCompareSignalSummaryTable(compareEntries)}
                  ${renderScenarioDetailsByBuildingType(compareEntries)}
                  ${renderScenarioComparisonCharts(compareEntries)}
                  ${renderCompareSignalDetails(compareEntries)}
                `
            }
          </div>
        </div>
      `);
    } else if (activeWorkspaceScreen === "contact") {
      const compareEntries = buildCompareScenarioEntries();
      ensureComparedParcelsLandIntelligence(compareEntries);
      setWorkspaceHtml(`
        <div class="workspace-panel">
          <div class="workspace-section">
            <h2 class="workspace-page-title">Ã„Â°letiÃ…Å¸im MenÃƒÂ¼sÃƒÂ¼ Ã¢â‚¬â€ Arsa SatÃ„Â±n Alma KanallarÃ„Â±</h2>
            ${
              !compareEntries.length
                ? '<div class="workspace-empty">Ã„Â°letiÃ…Å¸im akÃ„Â±Ã…Å¸Ã„Â± iÃƒÂ§in ÃƒÂ¶nce birkaÃƒÂ§ parceli karÃ…Å¸Ã„Â±laÃ…Å¸tÃ„Â±rma listesine ekleyelim.</div>'
                : `
                  <div class="workspace-note">SeÃƒÂ§ilen parseller iÃƒÂ§in satÃ„Â±n alma kanallarÃ„Â± ve yapÃ„Â± tÃƒÂ¼rÃƒÂ¼ne gÃƒÂ¶re yÃƒÂ¼klenici iletiÃ…Å¸imleri aÃ…Å¸aÃ„Å¸Ã„Â±da listelenir.</div>
                  <div class="workspace-section">
                    <h3 class="workspace-section-title">KarÃ…Å¸Ã„Â±laÃ…Å¸tÃ„Â±rma listesindeki parseller</h3>
                    <div class="workspace-note">${compareEntries.map((entry) => entry.ref).join(", ")}</div>
                  </div>
                  ${renderContactParcelBlocks(compareEntries)}
                `
            }
          </div>
        </div>
      `);
    }

    workspaceContentEl.querySelectorAll("[data-remove-compare]").forEach((buttonEl) => {
      buttonEl.addEventListener("click", () => {
        const key = decodeURIComponent(buttonEl.getAttribute("data-remove-compare") || "");
        const result = removeComparedParcelByKey(key);
        if (result.changed) {
          showStatus(`${result.entry.ref} karÃ…Å¸Ã„Â±laÃ…Å¸tÃ„Â±rma listesinden ÃƒÂ§Ã„Â±karÃ„Â±ldÃ„Â±.`);
        }
      });
    });

    workspaceContentEl.querySelectorAll("[data-remove-compare-selection]").forEach((buttonEl) => {
      buttonEl.addEventListener("click", () => {
        const selectionId = buttonEl.getAttribute("data-remove-compare-selection") || "";
        const result = removeScenarioSelectionById(selectionId);
        if (result.changed) {
          showStatus(`${result.entry.ref} senaryosu karÃ…Å¸Ã„Â±laÃ…Å¸tÃ„Â±rma listesinden ÃƒÂ§Ã„Â±karÃ„Â±ldÃ„Â±.`);
        }
      });
    });

    const clearCompareEl = workspaceContentEl.querySelector("[data-clear-compare-all]");
    if (clearCompareEl) {
      clearCompareEl.addEventListener("click", () => {
        clearComparedParcels();
        showStatus("KarÃ…Å¸Ã„Â±laÃ…Å¸tÃ„Â±rma listesi temizlendi.");
      });
    }

    const clearScenarioSelectionsEl = workspaceContentEl.querySelector("[data-clear-scenario-selections]");
    if (clearScenarioSelectionsEl) {
      clearScenarioSelectionsEl.addEventListener("click", () => {
        clearScenarioSelections();
        showStatus("Senaryo karÃ…Å¸Ã„Â±laÃ…Å¸tÃ„Â±rma listesi temizlendi.");
      });
    }

    workspaceContentEl.querySelectorAll("[data-compare-select]").forEach((buttonEl) => {
      buttonEl.addEventListener("click", () => {
        const key = decodeURIComponent(buttonEl.getAttribute("data-compare-select") || "");
        const entry = getComparedParcelByKey(key);
        if (!entry) return;
        activeComparedParcelKey = activeComparedParcelKey === key ? null : key;
        updateSelectedParcel(entry.feature);
      });
    });

    workspaceContentEl.querySelectorAll("[data-compare-action]").forEach((buttonEl) => {
      buttonEl.addEventListener("click", () => {
        if (!parcel) return;
        const action = buttonEl.getAttribute("data-compare-action");
        const key = decodeURIComponent(buttonEl.getAttribute("data-compare-key") || "");
        if (action === "remove") {
          const result = removeComparedParcelByKey(key);
          if (result.changed) {
            showStatus(`${result.entry.ref} karÃ…Å¸Ã„Â±laÃ…Å¸tÃ„Â±rma listesinden ÃƒÂ§Ã„Â±karÃ„Â±ldÃ„Â±.`);
            refreshActiveParcelPopup();
          }
          return;
        }
        const result = addComparedParcel(parcel.feature);
        if (result.changed) {
          showStatus(`${result.entry.ref} karÃ…Å¸Ã„Â±laÃ…Å¸tÃ„Â±rma listesine eklendi.`);
          refreshActiveParcelPopup();
        }
      });
    });

    const toggleSettingsEl = workspaceContentEl.querySelector("[data-toggle-scenario-settings]");
    if (toggleSettingsEl) {
      toggleSettingsEl.addEventListener("click", () => {
        scenarioSelectState.showSettings = !scenarioSelectState.showSettings;
        renderWorkspace();
      });
    }

    const usableRatioEl = workspaceContentEl.querySelector("#planningUsableRatio");
    if (usableRatioEl) {
      usableRatioEl.addEventListener("change", (event) => {
        planningSettings.usableRatio = clamp(Number(event.target.value) || DEFAULT_PLANNING_SETTINGS.usableRatio, 0.1, 1);
        renderWorkspace();
      });
    }

    const capacityMethodEl = workspaceContentEl.querySelector("#planningCapacityMethod");
    if (capacityMethodEl) {
      capacityMethodEl.addEventListener("change", (event) => {
        planningSettings.capacityMethod = event.target.value || DEFAULT_PLANNING_SETTINGS.capacityMethod;
        renderWorkspace();
      });
    }

    const farEl = workspaceContentEl.querySelector("#planningFar");
    if (farEl) {
      farEl.addEventListener("change", (event) => {
        planningSettings.far = clamp(Number(event.target.value) || DEFAULT_PLANNING_SETTINGS.far, 0.5, 5);
        renderWorkspace();
      });
    }

    const projectMonthsEl = workspaceContentEl.querySelector("#planningProjectMonths");
    if (projectMonthsEl) {
      projectMonthsEl.addEventListener("change", (event) => {
        planningSettings.projectMonths = clamp(Number(event.target.value) || DEFAULT_PLANNING_SETTINGS.projectMonths, 6, 60);
        renderWorkspace();
      });
    }

    workspaceContentEl.querySelectorAll("[data-parcel-area]").forEach((inputEl) => {
      inputEl.addEventListener("change", (event) => {
        const key = decodeURIComponent(event.target.getAttribute("data-parcel-area") || "");
        planningSettings.parcelOverrides[key] = {
          ...(planningSettings.parcelOverrides[key] || {}),
          areaM2: Math.max(1, Number(event.target.value) || 1),
        };
        renderWorkspace();
      });
    });

    workspaceContentEl.querySelectorAll("[data-parcel-cost]").forEach((inputEl) => {
      inputEl.addEventListener("change", (event) => {
        const key = decodeURIComponent(event.target.getAttribute("data-parcel-cost") || "");
        planningSettings.parcelOverrides[key] = {
          ...(planningSettings.parcelOverrides[key] || {}),
          landCost: Math.max(0, Number(event.target.value) || 0),
        };
        renderWorkspace();
      });
    });

    workspaceContentEl.querySelectorAll("[data-building-field]").forEach((inputEl) => {
      inputEl.addEventListener("change", (event) => {
        const field = event.target.getAttribute("data-building-field");
        const key = event.target.getAttribute("data-building-key");
        const target = planningSettings.buildingTypes.find((item) => item.key === key);
        if (!target || !field) return;
        target[field] = Math.max(0, Number(event.target.value) || 0);
        renderWorkspace();
      });
    });

    const settingsResetEl = workspaceContentEl.querySelector("[data-settings-reset]");
    if (settingsResetEl) {
      settingsResetEl.addEventListener("click", () => {
        planningSettings = JSON.parse(JSON.stringify(DEFAULT_PLANNING_SETTINGS));
        renderWorkspace();
      });
    }

    const settingsConfirmEl = workspaceContentEl.querySelector("[data-settings-confirm]");
    if (settingsConfirmEl) {
      settingsConfirmEl.addEventListener("click", () => {
        scenarioSelectState.showSettings = false;
        showStatus("VarsayÃ„Â±mlar kaydedildi, program gÃƒÂ¼ncel ayarlarla devam ediyor.");
        renderWorkspace();
      });
    }

    const scenarioSelectParcelEl = workspaceContentEl.querySelector("#scenarioSelectParcel");
    if (scenarioSelectParcelEl) {
      scenarioSelectParcelEl.addEventListener("change", (event) => {
        const key = decodeURIComponent(event.target.value || "");
        scenarioSelectState.parcelKey = key;
        const entry = getComparedParcelByKey(key);
        if (entry?.feature) {
          updateSelectedParcel(entry.feature);
        } else {
          renderWorkspace();
        }
      });
    }

    const scenarioSelectManualEl = workspaceContentEl.querySelector("#scenarioSelectManual");
    if (scenarioSelectManualEl) {
      scenarioSelectManualEl.addEventListener("change", (event) => {
        scenarioSelectState.manualParcelRef = event.target.value || "";
        const normalized = (event.target.value || "").trim().toLowerCase();
        const match = getScenarioSelectCandidates(parcel).find((item) => String(item.parcel.ref).toLowerCase() === normalized);
        if (match?.parcel?.feature) {
          scenarioSelectState.parcelKey = match.key;
          updateSelectedParcel(match.parcel.feature);
        } else {
          renderWorkspace();
        }
      });
    }

    const scenarioMaxScenariosEl = workspaceContentEl.querySelector("#scenarioMaxScenarios");
    if (scenarioMaxScenariosEl) {
      scenarioMaxScenariosEl.addEventListener("input", (event) => {
        scenarioSelectState.maxScenarios = Number(event.target.value) || 200;
        renderWorkspace();
      });
    }

    const scenarioMinUtilEl = workspaceContentEl.querySelector("#scenarioMinUtil");
    if (scenarioMinUtilEl) {
      scenarioMinUtilEl.addEventListener("input", (event) => {
        scenarioSelectState.minUtil = (Number(event.target.value) || 40) / 100;
        renderWorkspace();
      });
    }

    workspaceContentEl.querySelectorAll("[data-scenario-type]").forEach((checkboxEl) => {
      checkboxEl.addEventListener("change", (event) => {
        const type = event.target.getAttribute("data-scenario-type");
        if (!type) return;
        if (event.target.checked) {
          scenarioSelectState.allowedTypes = Array.from(new Set([...scenarioSelectState.allowedTypes, type]));
        } else {
          scenarioSelectState.allowedTypes = scenarioSelectState.allowedTypes.filter((item) => item !== type);
        }
        renderWorkspace();
      });
    });

    workspaceContentEl.querySelectorAll("[data-pick-scenario]").forEach((buttonEl) => {
      buttonEl.addEventListener("click", () => {
        scenarioSelectState.selectedScenarioName = buttonEl.getAttribute("data-pick-scenario");
        renderWorkspace();
      });
    });

    workspaceContentEl.querySelectorAll("[data-add-manual-type]").forEach((buttonEl) => {
      buttonEl.addEventListener("click", () => {
        if (!scenarioSelectState.parcelKey) return;
        addManualScenarioDraftEntry(scenarioSelectState.parcelKey, buttonEl.getAttribute("data-add-manual-type"));
        renderWorkspace();
      });
    });

    workspaceContentEl.querySelectorAll("[data-delete-manual-entry]").forEach((buttonEl) => {
      buttonEl.addEventListener("click", () => {
        if (!scenarioSelectState.parcelKey) return;
        removeManualScenarioDraftEntry(scenarioSelectState.parcelKey, buttonEl.getAttribute("data-delete-manual-entry"));
        renderWorkspace();
      });
    });

    workspaceContentEl.querySelectorAll("[data-manual-surface]").forEach((inputEl) => {
      inputEl.addEventListener("input", (event) => {
        if (!scenarioSelectState.parcelKey) return;
        updateManualScenarioDraftEntry(scenarioSelectState.parcelKey, event.target.getAttribute("data-manual-surface"), {
          surfaceArea: Number(event.target.value) || 0,
        });
        renderWorkspace();
      });
    });

    workspaceContentEl.querySelectorAll("[data-manual-floors]").forEach((inputEl) => {
      inputEl.addEventListener("input", (event) => {
        if (!scenarioSelectState.parcelKey) return;
        updateManualScenarioDraftEntry(scenarioSelectState.parcelKey, event.target.getAttribute("data-manual-floors"), {
          floors: Number(event.target.value) || 1,
        });
        renderWorkspace();
      });
    });

    const addScenarioSelectionEl = workspaceContentEl.querySelector("[data-add-scenario-selection]");
    if (addScenarioSelectionEl) {
      addScenarioSelectionEl.addEventListener("click", () => {
        const parcelKey = scenarioSelectState.parcelKey;
        if (!parcelKey) return;
        const candidate = getScenarioSelectCandidates(parcel).find((item) => item.key === parcelKey) || null;
        const sourceEntry = buildScenarioSourceEntry(candidate?.parcel || null);
        const draftEntries = getManualScenarioDraft(parcelKey);
        const result = addScenarioSelectionToCompare(sourceEntry, draftEntries);
        if (result.reason === "capacity") {
          showStatus("Bu senaryo parcel kapasitesini aÃ…Å¸Ã„Â±yor. Eklenmeden ÃƒÂ¶nce kullanim azaltÃ„Â±lmalÃ„Â±.", true);
          return;
        }
        if (result.changed) {
          showStatus(`${result.entry.ref} iÃƒÂ§in kullanÃ„Â±cÃ„Â± senaryosu karÃ…Å¸Ã„Â±laÃ…Å¸tÃ„Â±rma listesine eklendi.`);
        }
      });
    }

    const resetManualSelectionEl = workspaceContentEl.querySelector("[data-reset-manual-selection]");
    if (resetManualSelectionEl) {
      resetManualSelectionEl.addEventListener("click", () => {
        if (!scenarioSelectState.parcelKey) return;
        clearManualScenarioDraft(scenarioSelectState.parcelKey);
        renderWorkspace();
      });
    }

    const compareAEl = workspaceContentEl.querySelector("#scenarioCompareA");
    const compareBEl = workspaceContentEl.querySelector("#scenarioCompareB");
    if (compareAEl) {
      compareAEl.addEventListener("change", (event) => {
        scenarioCompareSelection.a = event.target.value;
        renderWorkspace();
      });
    }
    if (compareBEl) {
      compareBEl.addEventListener("change", (event) => {
        scenarioCompareSelection.b = event.target.value;
        renderWorkspace();
      });
    }
  }

  let map = null;
  let activeRegion = null;
  let activeRegionMode = "auto";
  let parcelPopup = null;
  let activeParcelPopupState = null;
  let selectedParcelFeature = null;
  let landIntelligenceRequestId = 0;
  let landIntelligenceFetchCounter = 0;
  let landIntelligenceState = createLandIntelligenceState(null);
  const landIntelligenceCache = new Map();
  let pendingSwitch = null;
  let currentBaseMapMode = "standard";
  let currentMapViewMode = "parcel";
  let currentTopographyVisible = topographyOverlayConfig.defaultVisible && hasTopographyOverlayData();
  let currentFutureGrowthVisible = Boolean(futureGrowthLayerConfig.defaultVisible && futureGrowthLayerConfig.enabled);
  let workspacePanelCollapsed = false;
  let currentPoiPointsVisible = true;
  let currentPoiLinesVisible = true;
  let currentFacilitiesVisible = false;
  let currentFacilitiesCategory = "all";
  let currentScenarioScoreMode = "none";
  let currentOfficialSaleVisible = !!showOfficialSaleEl?.checked;
  let currentHistoricSalesVisible = !!showHistoricSalesEl?.checked;
  let currentBrownfieldVisible = !!showBrownfieldSignalsEl?.checked;
  let currentMarketListingsVisible = !!showMarketListingsEl?.checked;
  let previousSaleLayerVisibilityBeforeHistory = {
    official: currentOfficialSaleVisible,
    brownfield: currentBrownfieldVisible,
    market: currentMarketListingsVisible,
  };
  let currentPoiData = null;
  let facilitiesFetchTimer = null;
  let facilityRequestId = 0;
  let scenarioParcelRequestId = 0;
  let parcelFallbackFetchTimer = null;
  let parcelFallbackRequestId = 0;
  let landOverlayFetchTimer = null;
  let landOverlayRequestId = 0;
  let futureGrowthFetchTimer = null;
  let futureGrowthRequestId = 0;
  let futureGrowthHoverPopup = null;
  let globalOverviewFetchTimer = null;
  let globalSaleReadyRequestId = 0;
  let globalSaleReadyFetchPromise = null;
  let globalSaleReadyFetchPromiseKey = null;
  let combinedSalesLayerFetchPromise = null;
  let combinedSalesLayerFetchPromiseKey = null;
  let parcelInteractionsBound = false;
  let parcelClickSuppressionUntil = 0;
  let landSourceStatuses = [];
  let parcelFallbackState = {
    featureCount: 0,
    lastLoadedAt: null,
    lastBBoxKey: null,
    error: null,
  };
  let futureGrowthState = {
    featureCount: 0,
    lastLoadedAt: null,
    lastBBoxKey: null,
    vectorAuthorityCode: null,
    error: null,
  };
  let landOverlayState = {
    officialSaleCount: 0,
    historicSaleCount: 0,
    brownfieldCount: 0,
    marketListingCount: 0,
    officialSaleFeatures: [],
    historicSaleFeatures: [],
    brownfieldFeatures: [],
    marketListingFeatures: [],
    officialSaleFootprintCount: 0,
    officialSaleFootprintFeatures: [],
    lastLoadedAt: null,
    error: null,
    lastBBoxKey: null,
    lastRegionSlug: null,
    globalSaleReadyBaseCount: 0,
    globalSaleReadyVisibleCount: 0,
    globalActiveSaleCount: 0,
    globalActionableSaleCount: 0,
    globalRealPriceCount: 0,
    globalNonDemoVisibleCount: 0,
    globalSaleReadyFeatures: [],
    globalSaleReadyLoadedAt: null,
    globalSaleReadyFilterKey: null,
    globalHistoricSaleBaseCount: 0,
    globalHistoricSaleVisibleCount: 0,
    globalHistoricSaleFeatures: [],
    globalHistoricSaleLoadedAt: null,
    globalOverviewMode: "official",
  };
  let facilitiesOverlayState = {
    featureCount: 0,
    lastLoadedAt: null,
    lastBBoxKey: null,
    error: null,
    features: [],
  };
  let landUseGridState = {
    featureCount: 0,
    sourceFeatureCount: 0,
    dataSource: "api",
    truncated: false,
    lastLoadedAt: null,
    lastBBoxKey: null,
    error: null,
    features: [],
  };
  let scenarioOverlayState = {
    featureCount: 0,
    requestedCount: 0,
    lastLoadedAt: null,
    lastBBoxKey: null,
    error: null,
    features: [],
  };
  const regionSaleReadyCache = new Map();
  const globalSaleReadyCache = new Map();
  const globalHistoricSaleCache = new Map();
  const combinedSalesLayerCache = new Map();
  const saleFeatureBoundsCache = new Map();

  function getCachedSaleFeatureBounds(feature) {
    const featureKey = getSaleFeatureKey(feature);
    if (featureKey && saleFeatureBoundsCache.has(featureKey)) {
      return saleFeatureBoundsCache.get(featureKey);
    }
    const bounds = geometryBounds(feature?.geometry);
    if (featureKey && bounds) {
      saleFeatureBoundsCache.set(featureKey, bounds);
    }
    return bounds;
  }

  function getFeatureBoundsIntersectsBbox(feature, bboxObj) {
    if (!feature?.geometry || !bboxObj) return false;
    const featureBounds = getCachedSaleFeatureBounds(feature);
    if (!featureBounds) return false;
    return !(
      featureBounds.maxLng < bboxObj.west
      || featureBounds.minLng > bboxObj.east
      || featureBounds.maxLat < bboxObj.south
      || featureBounds.minLat > bboxObj.north
    );
  }
  let landOverlayFilters = {
    minConfidence: 0,
    brownfieldSource: "all",
    listingStatus: "all",
    saleReadyQuickFilter: "all",
    reviewOnly: false,
  };
  let lastGuidanceKey = "";
  let activeWorkspaceScreen = "portfolio";
  let comparedParcels = [];
  let selectedScenarioComparisons = [];
  let activeComparedParcelKey = null;
  let scenarioCompareSelection = { a: null, b: null };
  let scenarioSelectState = {
    parcelKey: null,
    manualParcelRef: "",
    showSettings: false,
    maxScenarios: 200,
    minUtil: 0.4,
    allowedTypes: ["Konut ApartmanÃ„Â±", "Site", "Karma KullanÃ„Â±m", "Ticari", "Ofis", "Konut", "EndÃƒÂ¼striyel", "Prefabrik", "TarÃ„Â±msal"],
    selectedScenarioName: null,
    manualDrafts: {},
  };
  const poiCache = new Map();
  const parcelInsightCache = new Map();
  const mapModeButtons = new Map();
  let mapModeControlInstance = null;
  let topographyModeButton = null;
  let futureGrowthModeButton = null;
  let historicSalesModeButton = null;
  let securityModeButton = null;
  let currentSecurityVisible = false;
  const WORKSPACE_SCENARIOS = ["Konut ApartmanÃ„Â±", "Site", "Karma KullanÃ„Â±m", "Ticari", "Ofis", "Konut", "EndÃƒÂ¼striyel", "Prefabrik", "TarÃ„Â±msal"];
  const LAND_SIGNAL_MIN_ZOOM = Number(config.landSignalMinZoom || 11.5);
  const LAND_SIGNAL_REGION_SCOPE_MAX_ZOOM = Number(config.landSignalRegionScopeMaxZoom || Math.max(LAND_SIGNAL_MIN_ZOOM + 2.5, 14));
  const LAND_SALE_OVERVIEW_HIDE_ZOOM = Number(config.landSaleOverviewHideZoom || 24);
  const LAND_SIGNAL_FETCH_LIMIT = Number(config.landSignalFetchLimit || 900);
  const LAND_MARKET_FETCH_LIMIT = Number(config.landMarketFetchLimit || 5000);
  const LAND_BROWNFIELD_FETCH_LIMIT = Number(config.landBrownfieldFetchLimit || 5000);
  const LAND_OVERLAY_TIMEOUT_MS = Math.max(API_FETCH_TIMEOUT_MS, Number(config.landOverlayFetchTimeoutMs || 14000));
  const LAND_MARKET_TIMEOUT_MS = Math.max(LAND_OVERLAY_TIMEOUT_MS, Number(config.landMarketFetchTimeoutMs || 18000));
  const PARCEL_FALLBACK_FETCH_LIMIT = Number(config.parcelFallbackFetchLimit || 5000);
  const PARCEL_FALLBACK_ENABLED = Boolean(config.enableParcelFallback);
  const LAND_OVERLAY_BBOX_DECIMALS = Math.min(6, Math.max(2, Number(config.landOverlayBboxDecimals || 4)));
  const GLOBAL_SALE_READY_FETCH_LIMIT = Number(config.globalSaleReadyFetchLimit || 5000);
  const GLOBAL_HISTORY_FETCH_LIMIT = Number(config.globalHistoryFetchLimit || 5000);
  const GLOBAL_OVERVIEW_PAGE_LIMIT = Number(config.globalOverviewPageLimit || 1200);
  const GLOBAL_OVERVIEW_MAX_PAGES = Number(config.globalOverviewMaxPages || 8);
  const FACILITY_MIN_ZOOM = Number(config.facilitiesMinZoom || 11);
  const FACILITY_FETCH_LIMIT = Number(config.facilitiesFetchLimit || 2000);
  const FACILITY_SCENARIO_MIN_ZOOM = Number(config.facilityScenarioMinZoom || Math.max(config.parcelMinZoom, 14));
  const PARCEL_USE_VIEW_FETCH_LIMIT = Number(config.parcelUseViewFetchLimit || 6000);
  const PARCEL_USE_VIEW_BATCH_LIMIT = 1200;
  const FACILITY_CATEGORY_COLORS = {
    residential: "#73c7a5",
    industrial: "#ef6f51",
    commercial: "#f5c451",
    office: "#7aa6ff",
    retail: "#f39a4a",
    education: "#8dd1ff",
    health: "#74d58f",
    cultural: "#c38fff",
    transport: "#5ab0ff",
    utilities: "#9aa0a8",
    religious: "#d7c38c",
    energy: "#ffbf54",
  };
  const FACILITY_CATEGORY_LABELS = {
    residential: "Residential",
    industrial: "Industrial",
    commercial: "Commercial",
    office: "Office",
    retail: "Retail",
    education: "Education",
    health: "Health",
    cultural: "Cultural",
    transport: "Transport",
    utilities: "Utilities",
    religious: "Religious",
    energy: "Energy",
  };
  const FACILITY_SCENARIO_LABELS = {
    none: "Kapali",
    apartment: "Konut / Apartman",
    retail: "Perakende",
    office: "Ofis",
    industrial: "Endustriyel",
    mixed_use: "Karma Kullanim",
  };
  const PARCEL_USE_CATEGORY_COLORS = {
    industrial: "#f2c94c",
    retail: "#77d6ff",
    office: "#1e5aa8",
    residential_detached: "#8fd66f",
    residential_apartment: "#2e8b57",
    residential: "#8fd66f",
    mixed_use: "#8e44ad",
  };
  const PARCEL_USE_CATEGORY_LABELS = {
    industrial: "Sanayi",
    commercial: "Perakende",
    retail: "Perakende",
    office: "Ofis",
    residential_detached: "Mustakil Konut",
    residential_apartment: "Apartman Konut",
    residential: "Konut",
    mixed_use: "Karma",
    unknown: "Bilinmiyor",
  };
  const LONDON_RESIDENTIAL_APARTMENT_MIN_AREA_M2 = 450;
  const LONDON_RETAIL_MIN_AREA_M2 = 1800;
  const LONDON_OFFICE_MIN_AREA_M2 = 4500;
  const LONDON_INDUSTRIAL_MIN_AREA_M2 = 12000;
  const MAP_VIEW_MODE_LABELS = {
    parcel: "Parsellerli",
    map_only: "Sadece harita",
    land_use: "Arazi kullanim (renkli)",
  };
  const MAP_MODE_CONTROL_ITEMS_ALL = [
    {
      mode: "map_only",
      label: "Parselsiz harita",
      iconUrl: "./assets/icons/map-mode-walk.jpg",
    },
    {
      mode: "land_use",
      label: "Arazi kullanim",
      iconUrl: "./assets/icons/icons8-factory-30.png",
    },
    {
      mode: "parcel",
      label: "Parsellerli gorunum",
      iconUrl: "./assets/icons/map-mode-parcel.png",
    },
    {
      mode: HISTORY_CONTROL_MODE,
      label: "Gecmis satis katmani",
      iconUrl: "./assets/icons/map-mode-sales.svg",
      historyToggle: true,
    },
    {
      mode: TOPOGRAPHY_CONTROL_MODE,
      label: "Topografya katmani",
      iconUrl: "./assets/icons/icons8-area-chart-50.png",
      overlayToggle: true,
    },
    {
      mode: FUTURE_GROWTH_CONTROL_MODE,
      label: "Gelecek Gelisim katmani",
      iconUrl: "./assets/icons/map-mode-future.png",
      futureGrowthToggle: true,
    },
    {
      mode: SECURITY_CONTROL_MODE,
      label: "Guvenlik katmani",
      iconUrl: "./assets/icons/map-mode-future.png",
      securityToggle: true,
    },
  ];

  function getDefaultMapModeControlModes() {
    return MAP_MODE_CONTROL_ITEMS_ALL.map((item) => item.mode);
  }

  function loadVisibleMapModeControlModes() {
    try {
      const rawValue = window.localStorage.getItem(MAP_MODE_VISIBILITY_STORAGE_KEY);
      if (!rawValue) return getDefaultMapModeControlModes();
      const parsed = JSON.parse(rawValue);
      if (!Array.isArray(parsed)) return getDefaultMapModeControlModes();
      const available = new Set(getDefaultMapModeControlModes());
      const filtered = parsed
        .map((value) => String(value || "").trim())
        .filter((value) => available.has(value));
      return filtered.length > 0 ? filtered : getDefaultMapModeControlModes();
    } catch (_error) {
      return getDefaultMapModeControlModes();
    }
  }

  function saveVisibleMapModeControlModes(modes) {
    const available = new Set(getDefaultMapModeControlModes());
    const unique = [];
    (Array.isArray(modes) ? modes : []).forEach((mode) => {
      const value = String(mode || "").trim();
      if (!available.has(value)) return;
      if (unique.includes(value)) return;
      unique.push(value);
    });
    const finalModes = unique.length > 0 ? unique : getDefaultMapModeControlModes();
    try {
      window.localStorage.setItem(MAP_MODE_VISIBILITY_STORAGE_KEY, JSON.stringify(finalModes));
    } catch (_error) {
      return false;
    }
    return true;
  }

  function getVisibleMapModeControlItems() {
    const visibleModes = new Set(loadVisibleMapModeControlModes());
    return MAP_MODE_CONTROL_ITEMS_ALL.filter((item) => visibleModes.has(item.mode));
  }

  function loadPersistedMapView() {
    try {
      const rawValue = window.localStorage.getItem(MAP_VIEW_STATE_STORAGE_KEY);
      if (!rawValue) return null;
      const parsed = JSON.parse(rawValue);
      const center = Array.isArray(parsed?.center) ? parsed.center : null;
      const zoom = Number(parsed?.zoom);
      if (!center || center.length < 2) return null;
      const lng = Number(center[0]);
      const lat = Number(center[1]);
      if (!(Number.isFinite(lng) && Number.isFinite(lat) && Number.isFinite(zoom))) return null;
      return {
        center: [lng, lat],
        zoom,
      };
    } catch (_error) {
      return null;
    }
  }

  function savePersistedMapView() {
    if (!map || typeof map.getCenter !== "function" || typeof map.getZoom !== "function") return;
    try {
      const center = map.getCenter();
      const zoom = Number(map.getZoom());
      if (!Number.isFinite(center?.lng) || !Number.isFinite(center?.lat) || !Number.isFinite(zoom)) return;
      const payload = {
        center: [Number(center.lng.toFixed(6)), Number(center.lat.toFixed(6))],
        zoom: Number(zoom.toFixed(3)),
      };
      window.localStorage.setItem(MAP_VIEW_STATE_STORAGE_KEY, JSON.stringify(payload));
    } catch (_error) {
      return;
    }
  }

  function rebuildMapModeControl() {
    if (!map || typeof map.addControl !== "function") return false;
    if (mapModeControlInstance && typeof map.removeControl === "function") {
      try {
        map.removeControl(mapModeControlInstance);
      } catch (_error) {}
    }
    mapModeControlInstance = createMapModeControl();
    map.addControl(mapModeControlInstance, "top-right");
    updateMapModeControlState();
    return true;
  }

  function renderMapModeCustomizer() {
    if (!mapModeCustomizerEl) return;
    const visibleModes = new Set(loadVisibleMapModeControlModes());
    const rows = getDefaultMapModeControlModes().map((mode) => {
      const item = MAP_MODE_CONTROL_ITEMS_ALL.find((entry) => entry.mode === mode);
      if (!item) return "";
      const checkedAttr = visibleModes.has(mode) ? "checked" : "";
      return `
        <label class="toggle">
          <input type="checkbox" data-map-mode-visibility="${mode}" ${checkedAttr} />
          <span>${item.label}</span>
        </label>
      `;
    }).join("");
    setSanitizedHtml(mapModeCustomizerEl, rows || '<div class="hint">Buton listesi bulunamadi.</div>');
    mapModeCustomizerEl.querySelectorAll("[data-map-mode-visibility]").forEach((inputEl) => {
      inputEl.addEventListener("change", () => {
        const nextVisibleModes = Array.from(
          mapModeCustomizerEl.querySelectorAll("[data-map-mode-visibility]:checked")
        )
          .map((node) => node.getAttribute("data-map-mode-visibility"))
          .filter(Boolean);
        saveVisibleMapModeControlModes(nextVisibleModes);
        rebuildMapModeControl();
      });
    });
  }

  window.AAYS_MAP_MODE_CONTROL = {
    listAvailableModes() {
      return MAP_MODE_CONTROL_ITEMS_ALL.map((item) => ({
        mode: item.mode,
        label: item.label,
      }));
    },
    getVisibleModes() {
      return loadVisibleMapModeControlModes();
    },
    setVisibleModes(modes) {
      const saved = saveVisibleMapModeControlModes(modes);
      if (!saved) return false;
      renderMapModeCustomizer();
      rebuildMapModeControl();
      showStatus("Harita buton duzeni kaydedildi.", true);
      return true;
    },
    resetVisibleModes() {
      const saved = saveVisibleMapModeControlModes(getDefaultMapModeControlModes());
      if (!saved) return false;
      renderMapModeCustomizer();
      rebuildMapModeControl();
      showStatus("Harita buton duzeni varsayilana alindi.", true);
      return true;
    },
  };
  const LAND_USE_CATEGORY_MAPPING = {
    industrial: "industrial",
    industry: "industrial",
    industrial_area: "industrial",
    logistics: "industrial",
    logistic: "industrial",
    warehouse: "industrial",
    factory: "industrial",
    manufacturing: "industrial",
    sanayi: "industrial",
    endustriyel: "industrial",
    retail: "retail",
    retail_park: "retail",
    shopping: "retail",
    shop: "retail",
    store: "retail",
    market: "retail",
    perakende: "retail",
    commercial: "retail",
    commercial_area: "retail",
    business: "office",
    office: "office",
    office_area: "office",
    ofis: "office",
    ticari: "retail",
    mixed_use: "mixed_use",
    "mixed-use": "mixed_use",
    "mixed use": "mixed_use",
    mixed: "mixed_use",
    karma: "mixed_use",
    residential: "residential",
    residential_area: "residential",
    residential_detached: "residential_detached",
    residential_house: "residential_detached",
    detached: "residential_detached",
    "detached house": "residential_detached",
    semi_detached: "residential_detached",
    "semi detached": "residential_detached",
    terraced: "residential_detached",
    townhouse: "residential_detached",
    mustakil: "residential_detached",
    villa: "residential_detached",
    bungalow: "residential_detached",
    residential_apartment: "residential_apartment",
    apartment: "residential_apartment",
    apartments: "residential_apartment",
    flat: "residential_apartment",
    flats: "residential_apartment",
    maisonette: "residential_apartment",
    apartman: "residential_apartment",
    site: "residential_apartment",
    block: "residential_apartment",
    tower: "residential_apartment",
    housing: "residential",
    house: "residential",
    houses: "residential",
    dwelling: "residential",
    konut: "residential",
    education: "residential",
    health: "residential",
    cultural: "residential",
    religious: "residential",
    transport: "industrial",
    utilities: "industrial",
    energy: "industrial",
  };

  const WORKSPACE_SCREENS = [
    { id: "portfolio", label: "PortfÃƒÂ¶y Analizi" },
    { id: "parcel", label: "Parsel Analizi" },
    { id: "recommendation", label: "Ãƒâ€“neri Motoru" },
    { id: "scenario_select", label: "Arsa & Senaryo SeÃƒÂ§imi" },
    { id: "compare", label: "KarÃ…Å¸Ã„Â±laÃ…Å¸tÃ„Â±rma (ROI/IRR)" },
    { id: "scenario_compare", label: "Senaryo KarÃ…Å¸Ã„Â±laÃ…Å¸tÃ„Â±rma" },
    { id: "contact", label: "Ã„Â°letiÃ…Å¸im MenÃƒÂ¼sÃƒÂ¼" },
  ];

  const DEFAULT_PLANNING_SETTINGS = {
    usableRatio: 0.6,
    capacityMethod: "Taban AlanÃ„Â±",
    far: 1.5,
    projectMonths: 18,
    buildingTypes: [
      { key: "mustakil", label: "MÃƒÂ¼stakil Ev", scenarioName: "Konut", unitArea: 150, minArea: 120, maxArea: 220, unitCost: 2000000, unitSaleValue: 3000000 },
      { key: "apartman", label: "Apartman", scenarioName: "Konut ApartmanÃ„Â±", unitArea: 400, minArea: 250, maxArea: 650, unitCost: 6500000, unitSaleValue: 9000000 },
      { key: "site", label: "Site", scenarioName: "Site", unitArea: 900, minArea: 600, maxArea: 1500, unitCost: 12000000, unitSaleValue: 18000000 },
      { key: "prefab", label: "Prefabrik", scenarioName: "Prefabrik", unitArea: 200, minArea: 120, maxArea: 400, unitCost: 1500000, unitSaleValue: 2300000 },
      { key: "perakende", label: "Perakende", scenarioName: "Ticari", unitArea: 300, minArea: 180, maxArea: 500, unitCost: 4000000, unitSaleValue: 6000000 },
      { key: "ofis", label: "Ofis", scenarioName: "Ofis", unitArea: 350, minArea: 200, maxArea: 600, unitCost: 5000000, unitSaleValue: 7500000 },
      { key: "karma", label: "Karma", scenarioName: "Karma KullanÃ„Â±m", unitArea: 500, minArea: 300, maxArea: 900, unitCost: 7000000, unitSaleValue: 10000000 },
      { key: "endustriyel", label: "EndÃƒÂ¼striyel", scenarioName: "EndÃƒÂ¼striyel", unitArea: 800, minArea: 500, maxArea: 1400, unitCost: 10000000, unitSaleValue: 14000000 },
      { key: "tarimsal", label: "TarÃ„Â±msal", scenarioName: "TarÃ„Â±msal", unitArea: 500, minArea: 250, maxArea: 900, unitCost: 3000000, unitSaleValue: 4200000 },
    ],
    factorMatrix: [
      { factor: "Hastane", mustakil: 7, apartman: 8, site: 9, prefab: 6, perakende: 7, ofis: 6, karma: 8, endustriyel: 4, tarimsal: 4 },
      { factor: "Okul", mustakil: 9, apartman: 8, site: 9, prefab: 7, perakende: 8, ofis: 7, karma: 9, endustriyel: 3, tarimsal: 4 },
      { factor: "Polis Merkezi", mustakil: 8, apartman: 7, site: 8, prefab: 7, perakende: 6, ofis: 7, karma: 8, endustriyel: 5, tarimsal: 3 },
      { factor: "Metro (UlaÃ…Å¸Ã„Â±m)", mustakil: 6, apartman: 9, site: 9, prefab: 5, perakende: 8, ofis: 9, karma: 9, endustriyel: 10, tarimsal: 3 },
      { factor: "OtobÃƒÂ¼s DuraÃ„Å¸Ã„Â±", mustakil: 7, apartman: 8, site: 8, prefab: 6, perakende: 9, ofis: 8, karma: 9, endustriyel: 8, tarimsal: 5 },
      { factor: "AVM", mustakil: 8, apartman: 9, site: 10, prefab: 6, perakende: 10, ofis: 9, karma: 8, endustriyel: 4, tarimsal: 4 },
      { factor: "Deniz Ã„Â°skelesi / Su KenarÃ„Â±", mustakil: 5, apartman: 7, site: 7, prefab: 5, perakende: 6, ofis: 5, karma: 6, endustriyel: 8, tarimsal: 7 },
      { factor: "Nehir (Su KaynaklarÃ„Â±)", mustakil: 7, apartman: 8, site: 8, prefab: 6, perakende: 7, ofis: 7, karma: 6, endustriyel: 9, tarimsal: 9 },
      { factor: "Ã„Â°mar PlanÃ„Â± & Hukuki Durum", mustakil: 9, apartman: 10, site: 10, prefab: 8, perakende: 8, ofis: 7, karma: 7, endustriyel: 3, tarimsal: 6 },
      { factor: "Topografya & Zemin Ãƒâ€“zellikleri", mustakil: 7, apartman: 8, site: 7, prefab: 7, perakende: 7, ofis: 8, karma: 7, endustriyel: 9, tarimsal: 8 },
      { factor: "Afet Risk Durumu", mustakil: 8, apartman: 8, site: 7, prefab: 8, perakende: 7, ofis: 8, karma: 7, endustriyel: 10, tarimsal: 6 },
      { factor: "Piyasa & Sosyo-ekonomik Durum", mustakil: 8, apartman: 9, site: 8, prefab: 6, perakende: 7, ofis: 9, karma: 7, endustriyel: 6, tarimsal: 5 },
    ],
    parcelOverrides: {},
  };

  let planningSettings = JSON.parse(JSON.stringify(DEFAULT_PLANNING_SETTINGS));

  function showStatus(message, sticky = false) {
    const normalizedMessage = String(message || "").trim();
    if (!normalizedMessage) return;
    const now = Date.now();
    const lastMessage = showStatus._lastMessage || "";
    const lastAt = Number(showStatus._lastAt || 0);
    if (lastMessage === normalizedMessage && now - lastAt < 1600) {
      return;
    }
    showStatus._lastMessage = normalizedMessage;
    showStatus._lastAt = now;
    setSanitizedText(statusEl, normalizedMessage);
    statusEl.classList.remove("hidden");
    if (!sticky) {
      window.clearTimeout(showStatus._timer);
      showStatus._timer = window.setTimeout(() => statusEl.classList.add("hidden"), 3200);
    }
  }

  function findContainingRegion(center) {
    const lng = center.lng;
    const lat = center.lat;
    for (const region of config.regions) {
      const [minx, miny, maxx, maxy] = region.bbox;
      if (lng >= minx && lng <= maxx && lat >= miny && lat <= maxy) {
        return region;
      }
    }
    return null;
  }

  function findNearestRegion(center) {
    const lng = center.lng;
    const lat = center.lat;
    return config.regions.reduce((best, region) => {
      const [latC, lngC] = region.center;
      const dist = Math.abs(lng - lngC) + Math.abs(lat - latC);
      if (!best || dist < best.dist) {
        return { dist, region };
      }
      return best;
    }, null)?.region || null;
  }

  function getCoverageState(center) {
    const containedRegion = findContainingRegion(center);
    return {
      isWithinSupportedArea: Boolean(containedRegion),
      containedRegion,
      nearestRegion: containedRegion || findNearestRegion(center),
    };
  }

  function updateDebug() {
    if (!SHOW_DEBUG_BADGE) {
      if (debugBadgeEl) {
        debugBadgeEl.classList.add("hidden");
      }
      return;
    }
    const center = map.getCenter();
    const coverageState = getCoverageState(center);
    const targetRegion = coverageState.nearestRegion;
    const zoom = map.getZoom();
    setSanitizedText(debugBadgeEl, [
      `active: ${activeRegion ? activeRegion.label : "-"}`,
      `target: ${targetRegion ? targetRegion.label : "-"}`,
      `coverage: ${coverageState.isWithinSupportedArea ? "supported" : "outside"}`,
      `zoom: ${zoom.toFixed(2)}`,
      `parcel_min: ${config.parcelMinZoom}`,
      `poi_min: ${config.poiMinZoom}`,
      `mode: ${activeRegionMode}`,
    ].join("\n"));
  }

  function updateStats() {
    const coverageState = map ? getCoverageState(map.getCenter()) : { isWithinSupportedArea: true };
    setSanitizedText(activeRegionEl, activeRegion ? activeRegion.label : "-");
    if (coverageStateEl) {
      const coverageLabel = config.coverageLabel || "England";
      setSanitizedText(coverageStateEl, coverageState.isWithinSupportedArea ? `${coverageLabel} ici` : `${coverageLabel} disi`);
      coverageStateEl.dataset.coverage = coverageState.isWithinSupportedArea ? "inside" : "outside";
    }
    setSanitizedText(parcelThresholdEl, String(config.parcelMinZoom));
    setSanitizedText(poiThresholdEl, String(config.poiMinZoom));
    const topographySuffix = hasTopographyOverlayData()
      ? ` Ã‚Â· Topografya ${currentTopographyVisible ? "acik" : "kapali"}`
      : "";
    const futureGrowthSuffix = futureGrowthLayerConfig.enabled
      ? ` Ã‚Â· Gelecek Gelisim ${currentFutureGrowthVisible ? "acik" : "kapali"}`
      : "";
    setSanitizedText(renderModeEl, currentBaseMapMode === "satellite"
      ? `MapLibre + PMTiles + GeoJSON + Satellite Ã‚Â· ${getMapViewModeLabel(currentMapViewMode)}${topographySuffix}${futureGrowthSuffix}`
      : `MapLibre + PMTiles + GeoJSON Ã‚Â· ${getMapViewModeLabel(currentMapViewMode)}${topographySuffix}${futureGrowthSuffix}`);
    updateDebug();
  }

  function createEmptyFeatureCollection() {
    return { type: "FeatureCollection", features: [] };
  }

  function coerceSalesLayerBoolean(value) {
    if (typeof value === "boolean") return value;
    const normalized = String(value || "").trim().toLowerCase();
    return normalized === "true" || normalized === "1" || normalized === "yes";
  }

  function coerceSalesLayerNumber(value) {
    const numeric = Number(value);
    return Number.isFinite(numeric) ? numeric : null;
  }

  function normalizeSalesLayerConfidence(value) {
    const numeric = coerceSalesLayerNumber(value);
    if (!Number.isFinite(numeric)) return null;
    return numeric > 0 && numeric <= 1 ? numeric * 100 : numeric;
  }

  function normalizeCombinedSalesLayerFeature(feature) {
    if (!feature || feature.type !== "Feature" || !feature.geometry) {
      return null;
    }
    const props = feature.properties && typeof feature.properties === "object" ? feature.properties : {};
    const salesHistoryAvailable = coerceSalesLayerBoolean(props.sales_history_available);
    const externalEvidenceAvailable = coerceSalesLayerBoolean(props.external_market_evidence_available);
    const sourceName = props.source_name || (salesHistoryAvailable ? "hmlr_price_paid" : "market_listing_adapter");
    const providerName = props.provider_name || (salesHistoryAvailable ? "HM Land Registry" : "External market evidence");
    const historyTransactionCount = coerceSalesLayerNumber(props.history_transaction_count ?? props.sales_history_count);
    const latestHistoryPricePaid = coerceSalesLayerNumber(props.latest_history_price_paid ?? props.latest_sale_price_gbp);
    const latestHistoryAreaM2 = coerceSalesLayerNumber(props.latest_history_area_m2 ?? props.latest_sale_area_m2);
    const latestHistoryPricePerM2 = coerceSalesLayerNumber(props.latest_history_price_per_m2 ?? props.latest_sale_price_per_m2_gbp);
    const externalEvidenceCount = coerceSalesLayerNumber(props.external_market_evidence_count);
    const confidenceScore = normalizeSalesLayerConfidence(
      props.highest_confidence_score
      ?? props.confidence_score
      ?? props.external_market_best_confidence_score
      ?? props.sales_history_confidence_score
      ?? props.best_sales_history_confidence_score
    );
    const salesHistoryRecords = Array.isArray(props.sales_history_records) ? props.sales_history_records : [];
    return {
      ...feature,
      properties: {
        ...props,
        sales_history_available: salesHistoryAvailable,
        external_market_evidence_available: externalEvidenceAvailable,
        sale_ready_signal: externalEvidenceAvailable,
        history_signal: salesHistoryAvailable,
        portal_listing_signal: externalEvidenceAvailable,
        source_name: sourceName,
        provider_name: providerName,
        listing_status: props.listing_status || (salesHistoryAvailable ? "sold_history" : "unknown"),
        visible_sale_count: coerceSalesLayerNumber(props.visible_sale_count) ?? (externalEvidenceAvailable ? Math.max(1, externalEvidenceCount || 0) : 0),
        real_price_count: coerceSalesLayerNumber(props.real_price_count) ?? (latestHistoryPricePaid && latestHistoryPricePaid > 0 ? 1 : 0),
        confidence_score: confidenceScore,
        highest_confidence_score: confidenceScore,
        external_market_best_confidence_score: normalizeSalesLayerConfidence(props.external_market_best_confidence_score),
        sales_history_confidence_score: normalizeSalesLayerConfidence(props.sales_history_confidence_score ?? props.best_sales_history_confidence_score),
        history_transaction_count: historyTransactionCount ?? 0,
        latest_history_sale_date: props.latest_history_sale_date || props.latest_sale_date || null,
        latest_history_price_paid: latestHistoryPricePaid,
        latest_history_area_m2: latestHistoryAreaM2,
        latest_history_price_per_m2: latestHistoryPricePerM2,
        latest_history_property_type: props.latest_history_property_type || props.latest_sale_property_type || null,
        sales_history_records: salesHistoryRecords,
        requires_review: Boolean(props.requires_review) || externalEvidenceAvailable,
        price_truth: props.price_truth && typeof props.price_truth === "object"
          ? props.price_truth
          : salesHistoryAvailable && latestHistoryPricePaid && latestHistoryPricePaid > 0
            ? {
                label: "Gercek satis fiyati",
                detail: "HM Land Registry price paid kaydindan alindi.",
                tone: "verified",
                is_real: true,
              }
            : externalEvidenceAvailable
              ? {
                  label: "Satis sinyali",
                  detail: "Fallback katmani sadece eslesen satis kanitini getiriyor; ilan fiyati bu endpointte yok.",
                  tone: "review",
                  is_real: false,
                }
              : null,
        link_truth: props.link_truth && typeof props.link_truth === "object"
          ? props.link_truth
          : {
              label: "Link yok",
              detail: "Bu fallback katmani geometriyi ve ozet kaydi getirir; harici ilan linki bu endpointte yok.",
              tone: "neutral",
              has_link: false,
              is_real: false,
            },
        sale_summary: props.sale_summary && typeof props.sale_summary === "object"
          ? props.sale_summary
          : {
              visible_sale_count: externalEvidenceAvailable ? Math.max(1, externalEvidenceCount || 0) : 0,
              real_price_count: latestHistoryPricePaid && latestHistoryPricePaid > 0 ? 1 : 0,
              latest_asking_price_gbp: null,
              official_sale_status: externalEvidenceAvailable ? "unknown" : null,
            },
      },
    };
  }

  function filterSalesLayerFeaturesByBbox(features, bbox) {
    const bboxObj = typeof bbox === "string" ? parseBboxString(bbox) : bbox;
    if (!bboxObj) return Array.isArray(features) ? features.slice() : [];
    return (features || []).filter((feature) => getFeatureBoundsIntersectsBbox(feature, bboxObj));
  }

  function setGeoJsonSourceData(sourceId, data) {
    const source = map && map.getSource(sourceId);
    if (source && source.setData) {
      source.setData(data || createEmptyFeatureCollection());
    }
  }

  function hasTopographyOverlayData() {
    if (!topographyOverlayConfig.enabled) return false;
    if (topographyOverlayConfig.url) return true;
    return Array.isArray(topographyOverlayConfig.tiles) && topographyOverlayConfig.tiles.length > 0;
  }

  function resolveTopographyInsertBeforeLayerId() {
    const preferredLayer = topographyOverlayConfig.insertBeforeLayerId;
    if (preferredLayer && map?.getLayer(preferredLayer)) {
      return preferredLayer;
    }
    for (const region of config.regions) {
      const parcelLayerId = getParcelFillLayerId(region);
      if (map?.getLayer(parcelLayerId)) {
        return parcelLayerId;
      }
    }
    return null;
  }

  function syncTopographyControls() {
    if (showTopographyOverlayEl) {
      showTopographyOverlayEl.checked = Boolean(currentTopographyVisible && hasTopographyOverlayData());
      showTopographyOverlayEl.disabled = !hasTopographyOverlayData();
    }
  }

  function addTopographyOverlayLayer() {
    if (!map || !hasTopographyOverlayData()) {
      syncTopographyControls();
      updateMapModeControlState();
      return;
    }
    if (!map.getSource(TOPOGRAPHY_SOURCE_ID)) {
      const sourceDef = {
        type: topographyOverlayConfig.sourceType === "raster-dem" ? "raster-dem" : "raster",
      };
      if (topographyOverlayConfig.url) {
        sourceDef.url = topographyOverlayConfig.url;
      } else {
        sourceDef.tiles = topographyOverlayConfig.tiles;
      }
      if (topographyOverlayConfig.sourceType === "raster-dem") {
        sourceDef.encoding = topographyOverlayConfig.encoding;
      }
      if (Number.isFinite(topographyOverlayConfig.tileSize)) {
        sourceDef.tileSize = topographyOverlayConfig.tileSize;
      }
      if (Number.isFinite(topographyOverlayConfig.minzoom)) {
        sourceDef.minzoom = topographyOverlayConfig.minzoom;
      }
      if (Number.isFinite(topographyOverlayConfig.maxzoom)) {
        sourceDef.maxzoom = topographyOverlayConfig.maxzoom;
      }
      if (topographyOverlayConfig.attribution) {
        sourceDef.attribution = topographyOverlayConfig.attribution;
      }
      map.addSource(TOPOGRAPHY_SOURCE_ID, sourceDef);
    }
    if (!map.getLayer(TOPOGRAPHY_LAYER_ID)) {
      const layerDef = topographyOverlayConfig.sourceType === "raster-dem"
        ? {
            id: TOPOGRAPHY_LAYER_ID,
            type: "hillshade",
            source: TOPOGRAPHY_SOURCE_ID,
            layout: {
              visibility: currentTopographyVisible ? "visible" : "none",
            },
            paint: {
              "hillshade-exaggeration": topographyOverlayConfig.exaggeration,
              "hillshade-shadow-color": "#2f2f35",
              "hillshade-highlight-color": "#ffe3b5",
              "hillshade-accent-color": "#ffd37f",
            },
          }
        : {
            id: TOPOGRAPHY_LAYER_ID,
            type: "raster",
            source: TOPOGRAPHY_SOURCE_ID,
            layout: {
              visibility: currentTopographyVisible ? "visible" : "none",
            },
            paint: {
              "raster-opacity": topographyOverlayConfig.opacity,
              "raster-saturation": topographyOverlayConfig.saturation,
              "raster-contrast": topographyOverlayConfig.contrast,
              "raster-resampling": "linear",
            },
          };
      const beforeLayerId = resolveTopographyInsertBeforeLayerId();
      if (beforeLayerId) {
        map.addLayer(layerDef, beforeLayerId);
      } else {
        map.addLayer(layerDef);
      }
    }
    syncTopographyControls();
    updateMapModeControlState();
  }

  function updateTopographyLayerVisibility() {
    if (map?.getLayer(TOPOGRAPHY_LAYER_ID)) {
      map.setLayoutProperty(TOPOGRAPHY_LAYER_ID, "visibility", currentTopographyVisible ? "visible" : "none");
    }
    syncTopographyControls();
    updateMapModeControlState();
  }

  function setTopographyOverlayVisibility(nextVisible, options = {}) {
    const available = hasTopographyOverlayData();
    if (!available) {
      currentTopographyVisible = false;
      syncTopographyControls();
      updateMapModeControlState();
      if (!options.silent) {
        showStatus("Topografya katmani icin veri tanimi bulunamadi. Once config/topography.overlay.json dosyasini doldurun.", true);
      }
      updateStats();
      return;
    }
    currentTopographyVisible = Boolean(nextVisible);
    addTopographyOverlayLayer();
    updateTopographyLayerVisibility();
    updateStats();
    if (!options.silent) {
      showStatus(`Topografya katmani ${currentTopographyVisible ? "acildi" : "kapatildi"}.`);
    }
  }

  function toggleTopographyOverlay() {
    setTopographyOverlayVisibility(!currentTopographyVisible);
  }

  function resolveFutureGrowthApiUrl(pathTemplate, replacements = {}) {
    const template = String(pathTemplate || "").trim();
    const rendered = Object.entries(replacements).reduce((acc, [key, value]) => (
      acc.replaceAll(`{${key}}`, encodeURIComponent(String(value ?? "")))
    ), template);
    if (!rendered) return `${landIntelligenceApiBaseUrl}/api/future-growth/layer`;
    if (/^https?:\/\//i.test(rendered)) return rendered;
    return `${landIntelligenceApiBaseUrl}${rendered.startsWith("/") ? rendered : `/${rendered}`}`;
  }

  function getFutureGrowthColorLabel(colorClass, score) {
    const colorKey = String(colorClass || "").trim();
    const scoreValue = Number(score);
    const direct = futureGrowthLayerConfig.colorScale.find((item) => item.class === colorKey);
    if (direct) return direct.labelTr || direct.class;
    if (!Number.isFinite(scoreValue)) return colorKey || "-";
    const byRange = futureGrowthLayerConfig.colorScale.find((item) => scoreValue >= item.min && scoreValue < item.max);
    return byRange?.labelTr || colorKey || "-";
  }

  function updateFutureGrowthLegend() {
    if (!futureGrowthLegendEl) return;
    if (!futureGrowthLayerConfig.enabled) {
      futureGrowthLegendEl.classList.add("hidden");
      setSanitizedHtml(futureGrowthLegendEl, "");
      return;
    }
    if (!currentFutureGrowthVisible) {
      futureGrowthLegendEl.classList.add("hidden");
      return;
    }
    const rows = futureGrowthLayerConfig.colorScale
      .map((item) => `
        <div class="future-growth-legend-item">
          <span class="future-growth-legend-swatch" style="background:${item.hex}"></span>
          <span>${escapeHtml(item.labelTr || `${item.min}-${item.max}`)}</span>
        </div>
      `)
      .join("");
    const detail = futureGrowthState.error
      ? `<div class="future-growth-legend-error">${escapeHtml(futureGrowthState.error)}</div>`
      : `<div class="future-growth-legend-meta">${futureGrowthState.featureCount || 0} feature gorunur</div>`;
    setSanitizedHtml(
      futureGrowthLegendEl,
      `
      <div class="future-growth-legend-title">${escapeHtml(futureGrowthLayerConfig.layerName)}</div>
      <div class="future-growth-legend-grid">${rows}</div>
      <div class="future-growth-legend-note">${escapeHtml(futureGrowthLayerConfig.legendNote)}</div>
      ${detail}
      `
    );
    futureGrowthLegendEl.classList.remove("hidden");
  }

  function updateFutureGrowthStatus(message, isError = false) {
    if (!futureGrowthStatusEl) return;
    futureGrowthStatusEl.dataset.error = isError ? "true" : "false";
    setSanitizedText(futureGrowthStatusEl, message);
  }

  function syncFutureGrowthControls() {
    if (showFutureGrowthEl) {
      showFutureGrowthEl.checked = Boolean(currentFutureGrowthVisible && futureGrowthLayerConfig.enabled);
      showFutureGrowthEl.disabled = !futureGrowthLayerConfig.enabled;
    }
    if (futureGrowthMethodologyLinkEl) {
      futureGrowthMethodologyLinkEl.href = resolveFutureGrowthApiUrl(futureGrowthLayerConfig.api.methodology);
    }
    updateFutureGrowthLegend();
  }

  function resolveFutureGrowthInsertBeforeLayerId() {
    const preferred = ["official-sale-parcel-fill", "historic-sale-parcel-fill", "brownfield-polygons-fill"];
    for (const layerId of preferred) {
      if (map?.getLayer(layerId)) return layerId;
    }
    for (const region of config.regions) {
      const parcelLayerId = getParcelFillLayerId(region);
      if (map?.getLayer(parcelLayerId)) return parcelLayerId;
    }
    return null;
  }

  function addFutureGrowthLayers() {
    if (!map || !futureGrowthLayerConfig.enabled) {
      syncFutureGrowthControls();
      updateMapModeControlState();
      return;
    }
    if (!map.getSource(FUTURE_GROWTH_SOURCE_ID)) {
      map.addSource(FUTURE_GROWTH_SOURCE_ID, {
        type: "geojson",
        data: createEmptyFeatureCollection(),
      });
    }
    const beforeLayerId = resolveFutureGrowthInsertBeforeLayerId();
    if (!map.getLayer(FUTURE_GROWTH_FILL_LAYER_ID)) {
      const def = {
        id: FUTURE_GROWTH_FILL_LAYER_ID,
        type: "fill",
        source: FUTURE_GROWTH_SOURCE_ID,
        minzoom: futureGrowthLayerConfig.minZoom,
        filter: ["in", ["geometry-type"], ["literal", ["Polygon", "MultiPolygon"]]],
        layout: {
          visibility: currentFutureGrowthVisible ? "visible" : "none",
        },
        paint: {
          "fill-color": ["coalesce", ["get", "hex_color"], "#f4d35e"],
          "fill-opacity": [
            "interpolate",
            ["linear"],
            ["zoom"],
            futureGrowthLayerConfig.minZoom,
            0.22,
            16,
            0.3,
            18,
            0.38,
          ],
        },
      };
      if (beforeLayerId) {
        map.addLayer(def, beforeLayerId);
      } else {
        map.addLayer(def);
      }
    }
    if (!map.getLayer(FUTURE_GROWTH_LINE_LAYER_ID)) {
      const def = {
        id: FUTURE_GROWTH_LINE_LAYER_ID,
        type: "line",
        source: FUTURE_GROWTH_SOURCE_ID,
        minzoom: futureGrowthLayerConfig.minZoom,
        filter: ["in", ["geometry-type"], ["literal", ["Polygon", "MultiPolygon"]]],
        layout: {
          visibility: currentFutureGrowthVisible ? "visible" : "none",
        },
        paint: {
          "line-color": ["coalesce", ["get", "hex_color"], "#f4d35e"],
          "line-width": [
            "interpolate",
            ["linear"],
            ["zoom"],
            futureGrowthLayerConfig.minZoom,
            1.2,
            16,
            2.1,
            18,
            3.0,
          ],
          "line-opacity": 0.95,
        },
      };
      if (beforeLayerId) {
        map.addLayer(def, beforeLayerId);
      } else {
        map.addLayer(def);
      }
    }
    if (!map.getLayer(FUTURE_GROWTH_POINT_LAYER_ID)) {
      const def = {
        id: FUTURE_GROWTH_POINT_LAYER_ID,
        type: "circle",
        source: FUTURE_GROWTH_SOURCE_ID,
        minzoom: 5,
        filter: ["in", ["geometry-type"], ["literal", ["Point", "MultiPoint"]]],
        layout: {
          visibility: currentFutureGrowthVisible ? "visible" : "none",
        },
        paint: {
          "circle-color": ["coalesce", ["get", "hex_color"], "#f4d35e"],
          "circle-radius": [
            "interpolate",
            ["linear"],
            ["zoom"],
            5,
            2.5,
            9,
            5.0,
            12,
            6.8,
          ],
          "circle-stroke-color": "#111827",
          "circle-stroke-width": 1.1,
          "circle-opacity": 0.9,
        },
      };
      if (beforeLayerId) {
        map.addLayer(def, beforeLayerId);
      } else {
        map.addLayer(def);
      }
    }
    if (!map.getSource(FUTURE_GROWTH_VECTOR_SOURCE_ID)) {
      map.addSource(FUTURE_GROWTH_VECTOR_SOURCE_ID, {
        type: "geojson",
        data: createEmptyFeatureCollection(),
      });
    }
    if (!map.getLayer(FUTURE_GROWTH_VECTOR_LAYER_ID)) {
      map.addLayer({
        id: FUTURE_GROWTH_VECTOR_LAYER_ID,
        type: "line",
        source: FUTURE_GROWTH_VECTOR_SOURCE_ID,
        layout: {
          visibility: currentFutureGrowthVisible && futureGrowthLayerConfig.showVector ? "visible" : "none",
          "line-cap": "round",
          "line-join": "round",
        },
        paint: {
          "line-color": futureGrowthLayerConfig.vectorColor,
          "line-width": [
            "interpolate",
            ["linear"],
            ["zoom"],
            7,
            1.4,
            12,
            2.8,
            16,
            4.0,
          ],
          "line-opacity": 0.85,
          "line-dasharray": [0.8, 0.45],
        },
      });
    }
    syncFutureGrowthControls();
    updateMapModeControlState();
  }

  function updateFutureGrowthLayerVisibility() {
    const visible = currentFutureGrowthVisible ? "visible" : "none";
    [FUTURE_GROWTH_FILL_LAYER_ID, FUTURE_GROWTH_LINE_LAYER_ID, FUTURE_GROWTH_POINT_LAYER_ID].forEach((layerId) => {
      if (map?.getLayer(layerId)) {
        map.setLayoutProperty(layerId, "visibility", visible);
      }
    });
    if (map?.getLayer(FUTURE_GROWTH_VECTOR_LAYER_ID)) {
      map.setLayoutProperty(
        FUTURE_GROWTH_VECTOR_LAYER_ID,
        "visibility",
        (currentFutureGrowthVisible && futureGrowthLayerConfig.showVector) ? "visible" : "none"
      );
    }
    syncFutureGrowthControls();
    updateMapModeControlState();
  }

  function clearFutureGrowthHoverPopup() {
    if (futureGrowthHoverPopup) {
      futureGrowthHoverPopup.remove();
      futureGrowthHoverPopup = null;
    }
  }

  function openFutureGrowthHoverPopup(feature, lngLat) {
    const props = feature?.properties || {};
    const parcelId = props.parcel_id || "-";
    const score = Number(props.future_growth_percent);
    const confidence = Number(props.confidence_score);
    const label = getFutureGrowthColorLabel(props.color_class, score);
    const html = `
      <div class="future-growth-hover-card">
        <div><strong>Parcel:</strong> ${escapeHtml(parcelId)}</div>
        <div><strong>Skor:</strong> ${Number.isFinite(score) ? `${formatNumber(score, 1)}%` : "-"}</div>
        <div><strong>Sinif:</strong> ${escapeHtml(label)}</div>
        <div><strong>Confidence:</strong> ${Number.isFinite(confidence) ? `${formatNumber(confidence, 1)}%` : "-"}</div>
      </div>
    `;
    if (!futureGrowthHoverPopup) {
      futureGrowthHoverPopup = new maplibregl.Popup({
        closeButton: false,
        closeOnClick: false,
        maxWidth: "220px",
      });
    }
    futureGrowthHoverPopup
      .setLngLat(lngLat)
      .setHTML(html)
      .addTo(map);
  }

  function normalizeFutureGrowthFeatureCollection(payload) {
    const input = payload && typeof payload === "object" ? payload : createEmptyFeatureCollection();
    const features = Array.isArray(input.features) ? input.features : [];
    return {
      type: "FeatureCollection",
      features: features
        .filter((feature) => feature?.type === "Feature" && feature?.geometry && feature?.properties)
        .map((feature) => ({
          ...feature,
          properties: {
            ...feature.properties,
            parcel_id: Number(feature.properties.parcel_id) || feature.properties.parcel_id,
            future_growth_percent: Number(feature.properties.future_growth_percent),
            confidence_score: Number(feature.properties.confidence_score),
            color_class: String(feature.properties.color_class || ""),
            hex_color: String(feature.properties.hex_color || "#f4d35e"),
          },
        })),
    };
  }

  async function loadFutureGrowthLayer(force = false) {
    if (!map) return;
    if (!futureGrowthLayerConfig.enabled || !currentFutureGrowthVisible) {
      setGeoJsonSourceData(FUTURE_GROWTH_SOURCE_ID, createEmptyFeatureCollection());
      setGeoJsonSourceData(FUTURE_GROWTH_VECTOR_SOURCE_ID, createEmptyFeatureCollection());
      futureGrowthState = {
        ...futureGrowthState,
        featureCount: 0,
        error: null,
      };
      syncFutureGrowthControls();
      return;
    }
    const bbox = mapBoundsToBboxString();
    const zoom = Number(map.getZoom());
    if (!bbox || !Number.isFinite(zoom)) return;
    const quantizedBbox = quantizeBboxString(bbox, 4);
    if (!force && quantizedBbox === futureGrowthState.lastBBoxKey) {
      return;
    }
    const requestId = ++futureGrowthRequestId;
    const url = new URL(resolveFutureGrowthApiUrl(futureGrowthLayerConfig.api.layer));
    url.searchParams.set("bbox", bbox);
    url.searchParams.set("zoom", zoom.toFixed(2));
    url.searchParams.set("limit", String(futureGrowthLayerConfig.maxFeaturesPerRequest));
    const response = await fetchJsonWithTimeout(url.toString(), {
      label: "Future Growth layer",
      fallback: createEmptyFeatureCollection(),
      backoffGroup: "future-growth-layer",
    });
    if (requestId !== futureGrowthRequestId) return;
    const normalized = normalizeFutureGrowthFeatureCollection(response.data);
    setGeoJsonSourceData(FUTURE_GROWTH_SOURCE_ID, normalized);
    futureGrowthState = {
      ...futureGrowthState,
      featureCount: Array.isArray(normalized.features) ? normalized.features.length : 0,
      lastLoadedAt: new Date().toISOString(),
      lastBBoxKey: quantizedBbox,
      error: response.ok ? null : response.error,
    };
    if (response.ok) {
      updateFutureGrowthStatus(`Gelecek Gelisim katmani hazir (${futureGrowthState.featureCount} feature).`);
    } else {
      updateFutureGrowthStatus(`Gelecek Gelisim katmani fallback modunda: ${response.error}`, true);
    }
    updateFutureGrowthLegend();
  }

  async function loadFutureGrowthVectorForAuthority(authorityCode) {
    if (!map || !futureGrowthLayerConfig.showVector || !futureGrowthLayerConfig.enabled) return;
    const normalizedCode = String(authorityCode || "").trim().toLowerCase();
    if (!normalizedCode) {
      setGeoJsonSourceData(FUTURE_GROWTH_VECTOR_SOURCE_ID, createEmptyFeatureCollection());
      futureGrowthState.vectorAuthorityCode = null;
      return;
    }
    if (futureGrowthState.vectorAuthorityCode === normalizedCode) {
      return;
    }
    const url = resolveFutureGrowthApiUrl(futureGrowthLayerConfig.api.localAuthorityVector, { code: normalizedCode });
    const response = await fetchJsonWithTimeout(url, {
      label: "Future Growth vector",
      fallback: null,
      backoffGroup: "future-growth-vector",
    });
    if (!response.ok || !response.data?.vector_geometry) {
      setGeoJsonSourceData(FUTURE_GROWTH_VECTOR_SOURCE_ID, createEmptyFeatureCollection());
      return;
    }
    setGeoJsonSourceData(FUTURE_GROWTH_VECTOR_SOURCE_ID, {
      type: "FeatureCollection",
      features: [{
        type: "Feature",
        geometry: response.data.vector_geometry,
        properties: {
          direction_label: response.data.direction_label || "-",
          strength_score: response.data.strength_score ?? null,
          confidence_score: response.data.confidence_score ?? null,
          city_name: response.data.city_name || normalizedCode,
        },
      }],
    });
    futureGrowthState.vectorAuthorityCode = normalizedCode;
  }

  function scheduleFutureGrowthRefresh(force = false) {
    window.clearTimeout(futureGrowthFetchTimer);
    futureGrowthFetchTimer = window.setTimeout(() => {
      void loadFutureGrowthLayer(force);
    }, force ? 120 : 320);
  }

  function setFutureGrowthLayerVisibility(nextVisible, options = {}) {
    if (!futureGrowthLayerConfig.enabled) {
      currentFutureGrowthVisible = false;
      syncFutureGrowthControls();
      updateMapModeControlState();
      if (!options.silent) {
        showStatus("Future Growth katmani config/devre disi.");
      }
      return;
    }
    currentFutureGrowthVisible = Boolean(nextVisible);
    addFutureGrowthLayers();
    updateFutureGrowthLayerVisibility();
    if (currentFutureGrowthVisible) {
      scheduleFutureGrowthRefresh(true);
      updateFutureGrowthStatus("Gelecek Gelisim katmani yukleniyor...");
    } else {
      setGeoJsonSourceData(FUTURE_GROWTH_SOURCE_ID, createEmptyFeatureCollection());
      setGeoJsonSourceData(FUTURE_GROWTH_VECTOR_SOURCE_ID, createEmptyFeatureCollection());
      clearFutureGrowthHoverPopup();
      updateFutureGrowthStatus("Gelecek Gelisim katmani kapali.");
    }
    if (!options.silent) {
      showStatus(`Gelecek Gelisim katmani ${currentFutureGrowthVisible ? "acildi" : "kapatildi"}.`);
    }
    updateStats();
  }

  function toggleFutureGrowthLayer() {
    setFutureGrowthLayerVisibility(!currentFutureGrowthVisible);
  }

  function formatFutureGrowthDate(value) {
    if (!value) return "-";
    const asDate = new Date(value);
    if (!Number.isFinite(asDate.getTime())) return String(value);
    return asDate.toISOString().slice(0, 10);
  }

  function buildFutureGrowthParcelPopupContent(detail, fallbackProps = {}) {
    const parcelId = detail?.parcel_id ?? fallbackProps?.parcel_id ?? "-";
    const score = Number(detail?.future_growth_percent ?? fallbackProps?.future_growth_percent);
    const confidence = Number(detail?.confidence_score ?? fallbackProps?.confidence_score);
    const colorClass = detail?.color_class || fallbackProps?.color_class;
    const colorLabel = getFutureGrowthColorLabel(colorClass, score);
    const scoreBreakdown = detail?.score_breakdown || {};
    const warnings = Array.isArray(detail?.warnings) ? detail.warnings : [];
    const evidenceRows = Array.isArray(detail?.evidence) ? detail.evidence : [];
    const evidenceHtml = evidenceRows.length
      ? evidenceRows
        .slice(0, 12)
        .map((row) => `
          <div class="future-growth-evidence-card">
            <div class="future-growth-evidence-title">${escapeHtml(row.source_title || row.evidence_title || "-")}</div>
            <div class="future-growth-evidence-meta">
              Yayinci: ${escapeHtml(row.source_publisher || "-")}<br />
              Veri tarihi: ${escapeHtml(formatFutureGrowthDate(row.data_date))}<br />
              Yayin tarihi: ${escapeHtml(formatFutureGrowthDate(row.publication_date))}<br />
              Iliski: ${escapeHtml(row.relation_label || row.relation_type || "-")}<br />
              Uzaklik: ${Number.isFinite(Number(row.distance_m)) ? `${formatNumber(Number(row.distance_m), 0)} m` : "-"}<br />
              Etki agirligi: ${Number.isFinite(Number(row.impact_weight)) ? formatNumber(Number(row.impact_weight), 2) : "-"}<br />
              Guven: ${Number.isFinite(Number(row.confidence)) ? `${formatNumber(Number(row.confidence), 1)}%` : "-"}<br />
              ${row.source_url ? `<a href="${escapeHtml(row.source_url)}" target="_blank" rel="noopener noreferrer">Kaynagi ac</a>` : "Kaynak linki yok"}
              ${row.display_warning ? `<div class="future-growth-warning-inline">${escapeHtml(row.display_warning)}</div>` : ""}
            </div>
          </div>
        `)
        .join("")
      : `<div class="future-growth-evidence-empty">No parcel-specific evidence available.</div>`;
    const warningHtml = warnings.length
      ? `<div class="future-growth-warning-list">${warnings.map((item) => `<div>${escapeHtml(item)}</div>`).join("")}</div>`
      : "";
    const topReasons = Array.isArray(detail?.top_reasons) ? detail.top_reasons.slice(0, 5) : [];
    const topReasonsHtml = topReasons.length
      ? topReasons.map((reason) => `
          <div class="future-growth-reason">
            ${escapeHtml(reason.factor_type || "-")}: ${Number.isFinite(Number(reason.impact_weight_total))
              ? formatNumber(Number(reason.impact_weight_total), 2)
              : "-"}
          </div>
        `).join("")
      : `<div class="future-growth-reason">No parcel-specific evidence available.</div>`;
    const html = `
      <div class="parcel-popup future-growth-popup">
        <div class="parcel-popup-title">Parcel ${escapeHtml(parcelId)}</div>
        <div class="parcel-popup-meta">
          <strong>Future Growth:</strong> ${Number.isFinite(score) ? `${formatNumber(score, 1)}%` : "-"}<br />
          <strong>Confidence:</strong> ${Number.isFinite(confidence) ? `${formatNumber(confidence, 1)}%` : "-"}<br />
          <strong>Renk sinifi:</strong> ${escapeHtml(colorLabel)}<br />
          <strong>Aciklama:</strong> ${escapeHtml(detail?.color_explanation || "-")}<br />
          <strong>Sehir kayma yonu:</strong> ${escapeHtml(detail?.city_growth_direction_label || "insufficient evidence")}
        </div>
        <div class="future-growth-breakdown">
          <div><strong>Planning:</strong> ${formatNumber(Number(scoreBreakdown.planning_growth_score || 0), 1)}</div>
          <div><strong>Transport:</strong> ${formatNumber(Number(scoreBreakdown.transport_infra_score || 0), 1)}</div>
          <div><strong>Market:</strong> ${formatNumber(Number(scoreBreakdown.market_momentum_score || 0), 1)}</div>
          <div><strong>Demographic:</strong> ${formatNumber(Number(scoreBreakdown.demographic_demand_score || 0), 1)}</div>
          <div><strong>Social:</strong> ${formatNumber(Number(scoreBreakdown.social_amenity_score || 0), 1)}</div>
          <div><strong>Policy:</strong> ${formatNumber(Number(scoreBreakdown.land_supply_and_policy_score || 0), 1)}</div>
          <div><strong>Risk penalty:</strong> ${formatNumber(Number(scoreBreakdown.risk_penalty || 0), 1)}</div>
        </div>
        <div class="future-growth-reasons">${topReasonsHtml}</div>
        ${warningHtml}
        <div class="future-growth-evidence-list">${evidenceHtml}</div>
      </div>
    `;
    const container = document.createElement("div");
    setSanitizedHtml(container, html);
    return container;
  }

  async function openFutureGrowthParcelPopup(feature, lngLat) {
    const props = feature?.properties || {};
    const parcelId = Number(props.parcel_id);
    const detailUrl = resolveFutureGrowthApiUrl(futureGrowthLayerConfig.api.parcelDetail, { parcelId });
    const response = await fetchJsonWithTimeout(detailUrl, {
      label: "Future Growth parcel detail",
      fallback: null,
      backoffGroup: "future-growth-detail",
    });
    const detail = response.ok ? response.data : null;
    const authorityCode = detail?.local_authority_code || props.local_authority_code || selectedParcelFeature?.properties?.local_authority;
    if (authorityCode) {
      void loadFutureGrowthVectorForAuthority(authorityCode);
    }
    if (parcelPopup) {
      parcelPopup.remove();
    }
    parcelPopup = new maplibregl.Popup({ closeButton: true, maxWidth: "420px" })
      .setLngLat(lngLat)
      .setDOMContent(buildFutureGrowthParcelPopupContent(detail, props))
      .addTo(map);
    parcelPopup.on("close", () => {
      parcelPopup = null;
      activeParcelPopupState = null;
    });
  }

  function setSecurityOverlayVisibility(nextVisible, options = {}) {
    const bridge = window.AAYS_SECURITY;
    if (!bridge || (typeof bridge.activate !== "function" && typeof bridge.deactivate !== "function")) {
      if (!options.silent) {
        showStatus("Guvenlik katmani yuklu degil. security_overlay.js dosyasini kontrol edin.", true);
      }
      return;
    }
    currentSecurityVisible = Boolean(nextVisible);
    try {
      if (currentSecurityVisible) {
        if (typeof bridge.activate === "function") {
          bridge.activate();
        }
      } else if (typeof bridge.deactivate === "function") {
        bridge.deactivate();
      }
    } catch (error) {
      currentSecurityVisible = false;
      if (!options.silent) {
        showStatus(`Guvenlik katmani hatasi: ${error?.message || "bilinmeyen hata"}`, true);
      }
      updateMapModeControlState();
      return;
    }
    document.body?.setAttribute?.("data-aays-security-map-control", "1");
    if (!options.silent) {
      showStatus(`Guvenlik katmani ${currentSecurityVisible ? "acildi" : "kapatildi"}.`);
    }
    updateMapModeControlState();
  }

  function toggleSecurityOverlay() {
    setSecurityOverlayVisibility(!currentSecurityVisible);
  }

  function setBaseMapMode(nextMode) {
    currentBaseMapMode = nextMode === "satellite" ? "satellite" : "standard";
    if (baseMapSelectEl) {
      baseMapSelectEl.value = currentBaseMapMode;
    }
    if (map?.getLayer("basemap-osm")) {
      map.setLayoutProperty("basemap-osm", "visibility", currentBaseMapMode === "standard" ? "visible" : "none");
    }
    if (map?.getLayer("basemap-satellite")) {
      map.setLayoutProperty("basemap-satellite", "visibility", currentBaseMapMode === "satellite" ? "visible" : "none");
    }
    updateStats();
  }

  function getFacilityStatusMessage() {
    const parts = [];
    const facilitiesVisible = shouldShowFacilitiesByMode();
    const scenarioVisible = shouldShowScenarioOverlayByMode();
    parts.push(`Gorunum: ${getMapViewModeLabel(currentMapViewMode)}`);
    if (!facilitiesVisible) {
      parts.push("Facilities overlay kapali");
    } else if (!map || map.getZoom() < FACILITY_MIN_ZOOM) {
      parts.push(`Facilities overlay icin en az zoom ${FACILITY_MIN_ZOOM.toFixed(1)} gerekir`);
    } else if (currentMapViewMode === "land_use") {
      parts.push(
        `Arazi kullanim: ${landUseGridState.featureCount} parsel, ${landUseGridState.sourceFeatureCount} kaynak kayit`
      );
      if (landUseGridState.dataSource === "parcel_tiles_fallback") {
        parts.push("Kaynak: Yerel parcel PMTiles fallback");
      }
      if (landUseGridState.truncated) {
        parts.push(`Gorunum limiti uygulandi (ilk ${PARCEL_USE_VIEW_FETCH_LIMIT} parsel)`);
      } else if ((landUseGridState.sourceFeatureCount || 0) === 0) {
        parts.push("Bu gorunumde parcel_use siniflandirmasi bulunan parsel yok");
      }
    } else {
      parts.push(
        `Facilities: ${facilitiesOverlayState.featureCount} feature, kategori ${currentFacilitiesCategory === "all" ? "Hepsi" : getFacilityCategoryLabel(currentFacilitiesCategory)}`
      );
    }
    if (scenarioVisible) {
      if (!map || map.getZoom() < FACILITY_SCENARIO_MIN_ZOOM) {
        parts.push(`Senaryo overlay icin en az zoom ${FACILITY_SCENARIO_MIN_ZOOM.toFixed(1)} gerekir`);
      } else {
        const scenarioLabel = getScenarioModeLabel(currentScenarioScoreMode);
        if ((scenarioOverlayState.requestedCount || 0) === 0) {
          parts.push(`${scenarioLabel} skoru: 0 parcel (bu gorunumde backend parcel kaydi yok)`);
        } else if ((scenarioOverlayState.featureCount || 0) === 0) {
          parts.push(`${scenarioLabel} skoru: 0 parcel (backend parcel var ama score alanlari bos)`);
        } else {
          parts.push(`${scenarioLabel} skoru: ${scenarioOverlayState.featureCount} parcel`);
        }
      }
    } else if (currentScenarioScoreMode !== "none" && !isParcelViewMode()) {
      parts.push("Senaryo skor overlay sadece 'Parsellerli' gorunumde aktif");
    }
    if (facilitiesOverlayState.error) {
      parts.push(`Facilities hata: ${facilitiesOverlayState.error}`);
    }
    if (scenarioOverlayState.error) {
      parts.push(`Senaryo hata: ${scenarioOverlayState.error}`);
    }
    return `${parts.join(" | ")}.`;
  }

  function updateFacilitiesStatus() {
    if (!facilitiesStatusEl) return;
    setSanitizedText(facilitiesStatusEl, getFacilityStatusMessage());
  }

  function mapBoundsToBboxString() {
    if (!map) return null;
    const bounds = map.getBounds();
    return [
      bounds.getWest(),
      bounds.getSouth(),
      bounds.getEast(),
      bounds.getNorth(),
    ]
      .map((value) => Number(value).toFixed(6))
      .join(",");
  }

  function quantizeBboxString(bbox, decimals = 4) {
    const parsed = parseBboxString(bbox);
    if (!parsed) return bbox;
    const precision = Math.min(6, Math.max(2, Number(decimals) || 4));
    return [parsed.west, parsed.south, parsed.east, parsed.north]
      .map((value) => Number(value).toFixed(precision))
      .join(",");
  }

  function escapeHtml(value) {
    return String(value ?? "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/\"/g, "&quot;")
      .replace(/'/g, "&#39;");
  }

  function getFacilityCategoryLabel(code) {
    return FACILITY_CATEGORY_LABELS[code] || code || "-";
  }

  function getParcelUseCategoryLabel(code) {
    return PARCEL_USE_CATEGORY_LABELS[code] || code || "-";
  }

  function getScenarioModeLabel(code) {
    return FACILITY_SCENARIO_LABELS[code] || code || "-";
  }

  function getMapViewModeLabel(code) {
    return MAP_VIEW_MODE_LABELS[code] || code || "-";
  }

  function updateWorkspacePanelVisibility() {
    const hasSelectedParcel = currentMapViewMode !== "land_use" && Boolean(selectedParcelFeature);
    const shouldShowPanel = hasSelectedParcel && !workspacePanelCollapsed;
    if (workspaceShellEl) {
      workspaceShellEl.classList.toggle("is-hidden", !shouldShowPanel);
    }
    if (workspaceExpandBtnEl) {
      workspaceExpandBtnEl.classList.toggle("hidden", !(hasSelectedParcel && workspacePanelCollapsed));
    }
    if (workspaceCollapseBtnEl) {
      workspaceCollapseBtnEl.disabled = !hasSelectedParcel;
    }
  }

  function setMapViewMode(nextMode, forceRefresh = true) {
    const previousMode = currentMapViewMode;
    currentMapViewMode = ["parcel", "map_only", "land_use"].includes(nextMode) ? nextMode : "parcel";
    if (currentMapViewMode === "land_use" && previousMode !== "land_use") {
      if (parcelPopup) {
        parcelPopup.remove();
        parcelPopup = null;
        activeParcelPopupState = null;
      }
      if (selectedParcelFeature) {
        updateSelectedParcel(null);
      }
    }
    applyMapViewMode(forceRefresh);
    if (!forceRefresh) {
      scheduleGlobalOverviewRefresh(false);
    }
  }

  function ensureOfficialSalesModeFocus() {
    if (!currentOfficialSaleVisible) return;
    if (!currentMarketListingsVisible) {
      currentMarketListingsVisible = true;
      if (showMarketListingsEl) {
        showMarketListingsEl.checked = true;
      }
    }
    if (!isParcelViewMode()) {
      setMapViewMode("parcel", false);
    }
    if (PRESERVE_VIEW_ON_LAYER_TOGGLE) return;
    if (!map) return;
    const zoom = map.getZoom();
    if (Number.isFinite(zoom) && zoom < LAND_SIGNAL_MIN_ZOOM) {
      map.easeTo({
        zoom: LAND_SIGNAL_MIN_ZOOM,
        duration: 650,
      });
      showStatus(`Satisa uygun parcel katmani icin harita ${LAND_SIGNAL_MIN_ZOOM}+ zoom seviyesine getirildi.`, true);
    }
  }

  function ensureHistoricSalesModeFocus() {
    if (!currentHistoricSalesVisible) return;
    if (!isParcelViewMode()) {
      setMapViewMode("parcel", false);
    }
    if (PRESERVE_VIEW_ON_LAYER_TOGGLE) return;
    if (!map) return;
    const zoom = map.getZoom();
    if (Number.isFinite(zoom) && zoom < LAND_SIGNAL_MIN_ZOOM) {
      map.easeTo({
        zoom: LAND_SIGNAL_MIN_ZOOM,
        duration: 650,
      });
      showStatus(`Gecmis satis katmani icin harita ${LAND_SIGNAL_MIN_ZOOM}+ zoom seviyesine getirildi.`, true);
    }
  }

  function updateMapModeControlState() {
    mapModeButtons.forEach((buttonEl, mode) => {
      buttonEl.classList.toggle("is-active", mode === currentMapViewMode);
    });
    if (historicSalesModeButton) {
      historicSalesModeButton.classList.toggle("is-active", currentHistoricSalesVisible);
      historicSalesModeButton.classList.remove("is-placeholder");
      historicSalesModeButton.title = currentHistoricSalesVisible
        ? "Gecmis satis katmanini kapat"
        : "Gecmis satis katmanini ac";
    }
    if (topographyModeButton) {
      const available = hasTopographyOverlayData();
      topographyModeButton.classList.toggle("is-active", available && currentTopographyVisible);
      topographyModeButton.classList.toggle("is-placeholder", !available);
      topographyModeButton.title = available
        ? "Topografya katmanini ac/kapat"
        : "Topografya katmani icin once config/topography.overlay.json tanimi gerekli";
    }
    if (futureGrowthModeButton) {
      const available = futureGrowthLayerConfig.enabled;
      futureGrowthModeButton.classList.toggle("is-active", available && currentFutureGrowthVisible);
      futureGrowthModeButton.classList.toggle("is-placeholder", !available);
      futureGrowthModeButton.title = available
        ? "Gelecek Gelisim katmanini ac/kapat"
        : "Future Growth katmani config devre disi";
    }
    if (securityModeButton) {
      securityModeButton.classList.toggle("is-active", currentSecurityVisible);
      securityModeButton.classList.remove("is-placeholder");
      securityModeButton.title = currentSecurityVisible
        ? "Guvenlik katmanini kapat"
        : "Guvenlik katmanini ac";
    }
  }

  function createMapModeControl() {
    return {
      onAdd() {
        const container = document.createElement("div");
        container.className = "maplibregl-ctrl maplibregl-ctrl-group map-mode-control";
        getVisibleMapModeControlItems().forEach((item) => {
          const buttonEl = document.createElement("button");
          buttonEl.type = "button";
          buttonEl.className = "map-mode-button";
          buttonEl.title = item.label;
          buttonEl.setAttribute("aria-label", item.label);
          const iconEl = document.createElement("img");
          iconEl.src = item.iconUrl;
          iconEl.alt = item.label;
          buttonEl.appendChild(iconEl);
          if (item.overlayToggle) {
            topographyModeButton = buttonEl;
            buttonEl.addEventListener("click", () => {
              toggleTopographyOverlay();
            });
          } else if (item.futureGrowthToggle) {
            futureGrowthModeButton = buttonEl;
            buttonEl.addEventListener("click", () => {
              toggleFutureGrowthLayer();
            });
          } else if (item.securityToggle) {
            securityModeButton = buttonEl;
            buttonEl.addEventListener("click", () => {
              toggleSecurityOverlay();
            });
          } else if (item.historyToggle) {
            historicSalesModeButton = buttonEl;
            buttonEl.addEventListener("click", () => {
              if (showHistoricSalesEl) {
                const nextVisible = !showHistoricSalesEl.checked;
                showStatus(nextVisible ? "Gecmis satis katmani aciliyor..." : "Gecmis satis katmani kapatildi.");
                showHistoricSalesEl.checked = nextVisible;
                showHistoricSalesEl.dispatchEvent(new Event("change", { bubbles: true }));
                return;
              }
              currentHistoricSalesVisible = !currentHistoricSalesVisible;
              if (currentHistoricSalesVisible) {
                ensureHistoricSalesModeFocus();
                showStatus("Gecmis satis katmani aciliyor...");
              } else {
                showStatus("Gecmis satis katmani kapatildi.");
              }
              applyMapViewMode(false);
              scheduleLandIntelligenceRefresh(true);
              void syncGlobalSaleReadyOverview(false);
              updateLandSourceStatusPanel();
              updateMapModeControlState();
              renderWorkspace();
            });
          } else if (item.placeholder) {
            buttonEl.classList.add("is-placeholder");
            buttonEl.addEventListener("click", () => {
              showStatus("Bu mini gorunum butonu simdilik rezerve edildi.");
            });
          } else {
            mapModeButtons.set(item.mode, buttonEl);
            buttonEl.addEventListener("click", () => {
              setMapViewMode(item.mode, true);
            });
          }
          container.appendChild(buttonEl);
        });
        updateMapModeControlState();
        return container;
      },
      onRemove() {
        mapModeButtons.clear();
        topographyModeButton = null;
        futureGrowthModeButton = null;
        historicSalesModeButton = null;
        securityModeButton = null;
      },
    };
  }

  function isParcelViewMode() {
    return currentMapViewMode === "parcel";
  }

  function shouldShowFacilitiesByMode() {
    if (currentMapViewMode === "map_only") return false;
    if (currentMapViewMode === "land_use") return true;
    return currentFacilitiesVisible;
  }

  function shouldShowScenarioOverlayByMode() {
    return isParcelViewMode() && currentScenarioScoreMode !== "none";
  }

  function shouldShowPoiByMode() {
    return isParcelViewMode();
  }

  function hasFacilityPolygonFeatures() {
    return (facilitiesOverlayState.features || []).some((feature) => {
      const type = String(feature?.geometry?.type || "").toLowerCase();
      return type === "polygon" || type === "multipolygon";
    });
  }

  function parseBboxString(bbox) {
    const parts = String(bbox || "")
      .split(",")
      .map((value) => Number(value.trim()));
    if (parts.length !== 4 || parts.some((value) => !Number.isFinite(value))) {
      return null;
    }
    const [west, south, east, north] = parts;
    if (east <= west || north <= south) return null;
    return { west, south, east, north };
  }

  function getLandUseCellSizeMeters(zoom) {
    if (zoom >= 16) return 60;
    if (zoom >= 15) return 85;
    if (zoom >= 14) return 120;
    if (zoom >= 13) return 180;
    if (zoom >= 12) return 260;
    return 340;
  }

  function normalizeParcelUseText(rawValue) {
    return String(rawValue || "")
      .trim()
      .toLowerCase()
      .replace(/[\u2018\u2019]/g, "'")
      .replace(/[\u201c\u201d]/g, '\"')
      .replace(/[_/|]+/g, " ")
      .replace(/\s+/g, " ");
  }

  function hasStrictMixedUseSignal(rawValues) {
    const text = (Array.isArray(rawValues) ? rawValues : [rawValues])
      .map(normalizeParcelUseText)
      .filter(Boolean)
      .join(" | ");
    if (!text) return false;

    const hasCommercial = /(retail|shop|store|market|commercial|business|office|restaurant|cafe|pub|bar|salon|showroom|unit|ticari|perakende|ofis)/.test(text);
    const hasResidential = /(residential|flat|flats|apartment|apartments|maisonette|dwelling|house|housing|residence|residences|konut|apartman)/.test(text);
    const hasStackedUse = /(ground[- ]?floor|street[- ]?level|lower[- ]?floor|upper[- ]?floor|upper[- ]?floors|above|over|shop\s+with\s+flat|shop\s+with\s+flats|retail\s+with\s+flat|retail\s+with\s+flats|commercial\s+with\s+residential|residential\s+above|flats?\s+above|apartments?\s+above|commercial\s+below|retail\s+below|shop\s+below|alt\s+kat|ust\s+kat|zemin\s+kat|dukkan\s+ustu)/.test(text);

    return hasCommercial && hasResidential && hasStackedUse;
  }

  function toLandUseCategory(rawCategoryCode, options = {}) {
    const strict = Boolean(options?.strict);
    const allowMixedUse = Boolean(options?.allowMixedUse);
    const normalized = normalizeParcelUseText(rawCategoryCode);
    const mapped = LAND_USE_CATEGORY_MAPPING[normalized];
    if (mapped) {
      if (mapped === "mixed_use" && !allowMixedUse) {
        return strict ? null : "residential_detached";
      }
      return mapped;
    }
    return strict ? null : "residential_detached";
  }

  function inferLandUseCategoryFromText(rawValue) {
    const normalized = normalizeParcelUseText(rawValue);
    if (!normalized) return null;
    if (hasStrictMixedUseSignal(normalized)) {
      return "mixed_use";
    }
    if (/(industrial|industry|factory|warehouse|logistic|manufactur|sanayi|endustri)/.test(normalized)) {
      return "industrial";
    }
    if (/(retail|shop|store|market|perakende|mall|high street)/.test(normalized)) {
      return "retail";
    }
    if (/(office|business|ofis)/.test(normalized)) {
      return "office";
    }
    if (/(apartment|flat|maisonette|apartman|blok|block|tower|site|residence)/.test(normalized)) {
      return "residential_apartment";
    }
    if (/(detached|semi[- ]?detached|terraced|townhouse|bungalow|villa|mustakil|house|home)/.test(normalized)) {
      return "residential_detached";
    }
    if (/(residential|housing|dwelling|konut)/.test(normalized)) {
      return "residential";
    }
    if (/(commercial|ticari)/.test(normalized)) {
      return "retail";
    }
    return null;
  }

  function classifyExplicitResidentialSubtypeFromProperties(props) {
    const subtypeCandidates = [
      props?.latest_history_property_type_label,
      props?.latest_history_property_type,
      props?.property_type,
      props?.building_type,
      props?.use_type,
      props?.usage,
      props?.building,
      props?.land_use_type,
      props?.land_use,
    ];
    for (const candidate of subtypeCandidates) {
      const normalized = normalizeParcelUseText(candidate);
      if (!normalized) continue;
      if (normalized === "f" || /(apartment|flat|maisonette|apartman|block|tower|site)/.test(normalized)) {
        return "residential_apartment";
      }
      if (
        normalized === "d"
        || normalized === "s"
        || normalized === "t"
        || /(detached|semi[- ]?detached|terraced|townhouse|bungalow|villa|mustakil|house)/.test(normalized)
      ) {
        return "residential_detached";
      }
    }
    return null;
  }

  function classifyResidentialSubtypeFromProperties(props) {
    const explicitSubtype = classifyExplicitResidentialSubtypeFromProperties(props);
    if (explicitSubtype) return explicitSubtype;
    const areaM2 = Number(props?.area_m2 ?? props?.latest_history_area_m2 ?? 0);
    if (Number.isFinite(areaM2) && areaM2 > 0) {
      return areaM2 >= LONDON_RESIDENTIAL_APARTMENT_MIN_AREA_M2 ? "residential_apartment" : "residential_detached";
    }
    return "residential_detached";
  }

  function inferLandUseCategoryFallback(props, feature = null) {
    const directArea = Number(props?.area_m2 ?? props?.latest_history_area_m2 ?? 0);
    const areaM2 = Number.isFinite(directArea) && directArea > 0 ? directArea : getParcelAreaM2(feature);
    if (!Number.isFinite(areaM2) || areaM2 <= 0) {
      return "residential_detached";
    }
    if (areaM2 >= LONDON_INDUSTRIAL_MIN_AREA_M2) return "industrial";
    if (areaM2 >= LONDON_OFFICE_MIN_AREA_M2) return "office";
    if (areaM2 >= LONDON_RETAIL_MIN_AREA_M2) return "retail";
    if (areaM2 >= LONDON_RESIDENTIAL_APARTMENT_MIN_AREA_M2) return "residential_apartment";
    return "residential_detached";
  }

  function resolveParcelUseCategoryFromProperties(props, feature = null) {
    const saleSummary = props?.sale_summary && typeof props.sale_summary === "object" ? props.sale_summary : null;
    const topMarketListing = saleSummary?.top_market_listing && typeof saleSummary.top_market_listing === "object"
      ? saleSummary.top_market_listing
      : null;
    const topOfficialListing = saleSummary?.top_official_listing && typeof saleSummary.top_official_listing === "object"
      ? saleSummary.top_official_listing
      : null;
    const inferredTextCandidates = [
      topMarketListing?.parcel_name,
      topMarketListing?.title,
      topMarketListing?.address_text,
      topOfficialListing?.parcel_name,
      topOfficialListing?.title,
      topOfficialListing?.address_text,
      topOfficialListing?.metadata?.propertyTypeLabel,
    ];
    const candidates = [
      props?.land_use_category,
      props?.parcel_use_label,
      props?.category_code,
      props?.latest_history_land_use_label,
      props?.latest_history_building_class_label,
      props?.latest_history_property_type_label,
      props?.latest_history_property_type,
      props?.landuse,
      props?.land_use,
      props?.land_use_type,
      props?.building,
      props?.building_use,
      props?.class,
      props?.subclass,
      props?.usage,
      props?.use_type,
      props?.use_class,
      props?.property_type,
      props?.building_type,
      props?.planning_use_class,
      props?.planning_class,
      props?.dominant_context_code,
      ...inferredTextCandidates,
    ];
    if (hasStrictMixedUseSignal(candidates)) {
      return "mixed_use";
    }
    for (const rawCandidate of candidates) {
      const mapped = toLandUseCategory(rawCandidate, { strict: true });
      if (mapped) {
        if (mapped === "residential") {
          const explicitSubtype = classifyExplicitResidentialSubtypeFromProperties(props);
          if (explicitSubtype) return explicitSubtype;
          continue;
        }
        return mapped;
      }
    }
    for (const rawCandidate of candidates) {
      const inferred = inferLandUseCategoryFromText(rawCandidate);
      if (inferred) {
        if (inferred === "residential") {
          const explicitSubtype = classifyExplicitResidentialSubtypeFromProperties(props);
          if (explicitSubtype) return explicitSubtype;
          continue;
        }
        return inferred;
      }
    }
    return inferLandUseCategoryFallback(props, feature);
  }

  function buildParcelUseFeaturesFromParcelTileSources(bbox, maxFeatures = PARCEL_USE_VIEW_FETCH_LIMIT) {
    if (!map) return [];
    const canQueryRendered = typeof map.queryRenderedFeatures === "function";
    const canQuerySource = typeof map.querySourceFeatures === "function";
    if (!canQueryRendered && !canQuerySource) return [];
    const parsed = parseBboxString(bbox);
    if (!parsed) return [];
    const sourceRegions = activeRegion ? [activeRegion] : config.regions;
    const dedupe = new Set();
    const output = [];
    const pushIfEligible = (feature) => {
      if (output.length >= maxFeatures) return;
      const geometryType = String(feature?.geometry?.type || "").toLowerCase();
      if (geometryType !== "polygon" && geometryType !== "multipolygon") return;
      const center = geometryCenterLngLat(feature?.geometry);
      if (!center) return;
      if (
        center.lng < parsed.west
        || center.lng > parsed.east
        || center.lat < parsed.south
        || center.lat > parsed.north
      ) {
        return;
      }
      const props = feature?.properties || {};
      const dedupeKey = String(
        props.parcel_id
        || props.inspire_id
        || props.parcel_ref
        || feature?.id
        || `${center.lng.toFixed(6)}_${center.lat.toFixed(6)}`
      );
      if (dedupe.has(dedupeKey)) return;
      dedupe.add(dedupeKey);
      const landUseCategory = resolveParcelUseCategoryFromProperties(props, feature);
      output.push({
        type: "Feature",
        geometry: feature.geometry,
        properties: {
          ...props,
          land_use_category: landUseCategory,
          category_code: landUseCategory,
        },
      });
    };

    if (canQueryRendered) {
      const candidateLayerIds = [];
      for (const region of sourceRegions) {
        const warmLayerId = getParcelWarmLayerId(region);
        const fillLayerId = getParcelFillLayerId(region);
        if (map.getLayer(warmLayerId)) candidateLayerIds.push(warmLayerId);
        if (map.getLayer(fillLayerId)) candidateLayerIds.push(fillLayerId);
      }
      if (candidateLayerIds.length) {
        let renderedFeatures = [];
        try {
          renderedFeatures = map.queryRenderedFeatures(undefined, { layers: candidateLayerIds }) || [];
        } catch (_) {
          try {
            renderedFeatures = map.queryRenderedFeatures({ layers: candidateLayerIds }) || [];
          } catch (_) {
            renderedFeatures = [];
          }
        }
        renderedFeatures.forEach(pushIfEligible);
      }
    }

    // Fallback: query source tiles when rendered query does not return visible parcel geometry.
    if (output.length === 0 && canQuerySource) {
      for (const region of sourceRegions) {
        if (output.length >= maxFeatures) break;
        const sourceId = getParcelSourceId(region);
        if (!map.getSource(sourceId)) continue;
        let sourceFeatures = [];
        try {
          sourceFeatures = map.querySourceFeatures(sourceId, { sourceLayer: "parcels" }) || [];
        } catch (_) {
          sourceFeatures = [];
        }
        sourceFeatures.forEach(pushIfEligible);
      }
    }
    return output.slice(0, maxFeatures);
  }

  function buildLandUseGridFeatures(sourceFeatures, bbox, zoom) {
    const parsed = parseBboxString(bbox);
    if (!parsed) return [];
    const seeds = (sourceFeatures || [])
      .map((feature) => {
        const center = geometryCenterLngLat(feature?.geometry);
        if (!center) return null;
        return {
          lng: center.lng,
          lat: center.lat,
          category: toLandUseCategory(feature?.properties?.category_code),
        };
      })
      .filter(Boolean);
    if (!seeds.length) return [];

    const centerLat = (parsed.south + parsed.north) / 2;
    const widthM = haversineDistanceMeters(
      { lng: parsed.west, lat: centerLat },
      { lng: parsed.east, lat: centerLat }
    );
    const heightM = haversineDistanceMeters(
      { lng: parsed.west, lat: parsed.south },
      { lng: parsed.west, lat: parsed.north }
    );
    const cellSizeM = getLandUseCellSizeMeters(zoom);
    const cols = Math.max(6, Math.min(42, Math.ceil(widthM / cellSizeM)));
    const rows = Math.max(6, Math.min(42, Math.ceil(heightM / cellSizeM)));
    const stepLng = (parsed.east - parsed.west) / cols;
    const stepLat = (parsed.north - parsed.south) / rows;
    if (!Number.isFinite(stepLng) || !Number.isFinite(stepLat) || stepLng <= 0 || stepLat <= 0) {
      return [];
    }

    const features = [];
    for (let row = 0; row < rows; row += 1) {
      for (let col = 0; col < cols; col += 1) {
        const cellWest = parsed.west + col * stepLng;
        const cellEast = cellWest + stepLng;
        const cellSouth = parsed.south + row * stepLat;
        const cellNorth = cellSouth + stepLat;
        const center = {
          lng: (cellWest + cellEast) / 2,
          lat: (cellSouth + cellNorth) / 2,
        };
        const scoreByCategory = {};
        for (const seed of seeds) {
          const distanceM = haversineDistanceMeters(center, { lng: seed.lng, lat: seed.lat });
          const weight = 1 / Math.max(distanceM, 30);
          scoreByCategory[seed.category] = (scoreByCategory[seed.category] || 0) + weight;
        }
        const dominantCategory =
          Object.entries(scoreByCategory).sort((left, right) => Number(right[1]) - Number(left[1]))[0]?.[0] || "commercial";
        features.push({
          type: "Feature",
          geometry: {
            type: "Polygon",
            coordinates: [[
              [cellWest, cellSouth],
              [cellEast, cellSouth],
              [cellEast, cellNorth],
              [cellWest, cellNorth],
              [cellWest, cellSouth],
            ]],
          },
          properties: {
            category_code: dominantCategory,
            mode: "land_use_interpolated",
          },
        });
      }
    }
    return features;
  }

  function getScenarioScoreColor(score) {
    const numeric = Number(score);
    if (!Number.isFinite(numeric)) return "#4e5864";
    if (numeric >= 80) return "#48c78e";
    if (numeric >= 65) return "#9fd66f";
    if (numeric >= 50) return "#f5c451";
    if (numeric >= 35) return "#f39a4a";
    return "#ef6f51";
  }

  function getScenarioScoreText(score) {
    const numeric = Number(score);
    if (!Number.isFinite(numeric)) return "Skor yok";
    if (numeric >= 80) return "Cok guclu";
    if (numeric >= 65) return "Guclu";
    if (numeric >= 50) return "Dengeli";
    if (numeric >= 35) return "Temkinli";
    return "Zayif";
  }

  function formatLandOverlayDate(value) {
    if (!value) return "-";
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) return String(value);
    return date.toLocaleString("tr-TR");
  }

  function updateLandFilterSummary() {
    if (!landFilterSummaryEl) return;
    const parts = [];
    if (landOverlayFilters.minConfidence > 0) {
      parts.push(`confidence ${landOverlayFilters.minConfidence}+`);
    }
    if (landOverlayFilters.brownfieldSource !== "all") {
      parts.push(
        landOverlayFilters.brownfieldSource === "planning_data_brownfield"
          ? "brownfield: Planning Data"
          : "brownfield: Local Authority"
      );
    }
    if (landOverlayFilters.listingStatus !== "all") {
      parts.push(`listing: ${landOverlayFilters.listingStatus}`);
    }
    if (landOverlayFilters.saleReadyQuickFilter !== "all") {
      parts.push(`hÃ„Â±zlÃ„Â± gÃƒÂ¶rÃƒÂ¼nÃƒÂ¼m: ${getSaleReadyQuickFilterLabel(landOverlayFilters.saleReadyQuickFilter)}`);
    }
    if (landOverlayFilters.reviewOnly) {
      parts.push("sadece review gereken kayÃ„Â±tlar");
    }
    setSanitizedText(landFilterSummaryEl, parts.length
      ? `Aktif filtreler: ${parts.join(" Ã‚Â· ")}`
      : "Harita sinyalleri tÃƒÂ¼m confidence seviyeleriyle gÃƒÂ¶steriliyor.");
    if (landMinConfidenceValueEl) {
      setSanitizedText(landMinConfidenceValueEl, `${landOverlayFilters.minConfidence}+`);
    }
  }

  function getLandFilterSummaryHtml() {
    const parts = [];
    if (landOverlayFilters.minConfidence > 0) {
      parts.push(`Min confidence ${landOverlayFilters.minConfidence}+`);
    }
    if (landOverlayFilters.brownfieldSource !== "all") {
      parts.push(
        landOverlayFilters.brownfieldSource === "planning_data_brownfield"
          ? "Brownfield: Planning Data"
          : "Brownfield: Local Authority"
      );
    }
    if (landOverlayFilters.listingStatus !== "all") {
      parts.push(`Listing status: ${landOverlayFilters.listingStatus}`);
    }
    if (landOverlayFilters.saleReadyQuickFilter !== "all") {
      parts.push(`HÃ„Â±zlÃ„Â± gÃƒÂ¶rÃƒÂ¼nÃƒÂ¼m: ${getSaleReadyQuickFilterLabel(landOverlayFilters.saleReadyQuickFilter)}`);
    }
    if (landOverlayFilters.reviewOnly) {
      parts.push("Review-only gÃƒÂ¶rÃƒÂ¼nÃƒÂ¼m");
    }
    if (!parts.length) {
      return '<div class="workspace-note">Aktif filtre yok. Harita tÃƒÂ¼m uygun sinyalleri gÃƒÂ¶steriyor.</div>';
    }
    return `<div class="workspace-note">${parts.join(" Ã‚Â· ")}</div>`;
  }

  function appendLandOverlayFilterParams(params, options = {}) {
    params.set("exclude_demo", "true");
    if (landOverlayFilters.minConfidence > 0) {
      params.set("min_confidence", String(landOverlayFilters.minConfidence));
    }
    if (options.brownfieldSource && landOverlayFilters.brownfieldSource !== "all") {
      params.set("source", landOverlayFilters.brownfieldSource);
    }
    if (options.listingStatus && landOverlayFilters.listingStatus !== "all") {
      params.set("listing_status", landOverlayFilters.listingStatus);
    }
    return params;
  }

  function filterLandOverlayFeatures(collection) {
    const safeCollection = collection && collection.type === "FeatureCollection" ? collection : createEmptyFeatureCollection();
    if (!landOverlayFilters.reviewOnly) {
      return safeCollection;
    }
    return {
      type: "FeatureCollection",
      features: (safeCollection.features || []).filter((feature) => Boolean(feature?.properties?.requires_review)),
    };
  }

  function updateSaleReadyQuickFilterButtons() {
    if (!saleReadyQuickFiltersEl) return;
    saleReadyQuickFiltersEl.querySelectorAll("[data-sale-ready-quick-filter]").forEach((buttonEl) => {
      const value = buttonEl.getAttribute("data-sale-ready-quick-filter") || "all";
      buttonEl.setAttribute("data-active", value === landOverlayFilters.saleReadyQuickFilter ? "true" : "false");
    });
  }

  function resetLandOverlayFilters() {
    landOverlayFilters = {
      minConfidence: 0,
      brownfieldSource: "all",
      listingStatus: "all",
      saleReadyQuickFilter: "all",
      reviewOnly: false,
    };
    if (landMinConfidenceEl) {
      landMinConfidenceEl.value = "0";
    }
    if (brownfieldSourceFilterEl) {
      brownfieldSourceFilterEl.value = "all";
    }
    if (listingStatusFilterEl) {
      listingStatusFilterEl.value = "all";
    }
    if (landReviewOnlyEl) {
      landReviewOnlyEl.checked = false;
    }
    updateSaleReadyQuickFilterButtons();
    updateLandFilterSummary();
  }

  function getLandSourceStatusEntry(sourceName) {
    return (landSourceStatuses || []).find((item) => item?.name === sourceName) || null;
  }

  function formatManifestAvailabilityLabel(status) {
    switch (status) {
      case "live_ready":
        return "Canli export hazir";
      case "demo_only":
        return "Yalnizca demo manifest var";
      case "missing_files":
        return "Aktif export dosyasi eksik";
      case "manifest_missing":
        return "Manifest dosyasi yok";
      case "waiting_for_live_export":
        return "Canli export bekleniyor";
      case "inactive_only":
        return "Tum manifest satirlari pasif";
      case "empty_manifest":
        return "Manifest bos";
      case "parse_error":
        return "Manifest parse hatasi";
      default:
        return "Manifest durumu bilinmiyor";
    }
  }

  function buildManifestStatusSummaryHtml(sourceName) {
    const statusEntry = getLandSourceStatusEntry(sourceName);
    const manifestStatus = statusEntry?.notes?.manifest_status;
    if (!manifestStatus) return "";
    const sourceLabel = getLandSourceDisplayName(sourceName);
    const missingFiles = Array.isArray(manifestStatus.missing_active_files)
      ? manifestStatus.missing_active_files.filter(Boolean)
      : [];
    const activeProviders = Array.isArray(manifestStatus.active_provider_names)
      ? manifestStatus.active_provider_names.filter(Boolean)
      : [];
    const details = [
      `${manifestStatus.live_ready_entries || 0} canli hazir`,
      `${manifestStatus.demo_entries || 0} demo`,
      `${manifestStatus.active_entries || 0} aktif giris`,
    ];
    if (activeProviders.length) {
      details.push(`provider: ${activeProviders.join(", ")}`);
    }
    if (missingFiles.length) {
      details.push(`eksik dosya: ${missingFiles.slice(0, 3).join(", ")}`);
    }
    if (manifestStatus.parse_error) {
      details.push(`hata: ${manifestStatus.parse_error}`);
    }
    return `
      <div class="workspace-note">
        <strong>${sourceLabel}</strong> Ã‚Â· ${formatManifestAvailabilityLabel(manifestStatus.availability)}<br />
        ${details.join(" Ã‚Â· ")}
      </div>
    `;
  }

  function updateLandSourceStatusPanel() {
    if (!landSourceStatusEl) return;
    if (!landIntelligenceApiBaseUrl) {
      setSanitizedHtml(landSourceStatusEl, "Land Intelligence API bagli degil. <code>config/regions.local.json</code> icindeki <code>landIntelligenceApiBaseUrl</code> ayarlaninca parcel bazli sinyaller burada gorunur.");
      return;
    }

    const overlayHint = map && map.getZoom() < LAND_SIGNAL_MIN_ZOOM
      ? `Bu katmanlar icin en az ${LAND_SIGNAL_MIN_ZOOM}+ zoom onerilir. Uzak-orta zoomda turuncu satis noktalarini kademeli rehber olarak gostermeye devam ediyoruz.`
      : "Harita parcel tabani ile acilir; satisa uygun parceller ayni parcel geometrisi ustunde ayri vurgu alir. Uzak-orta zoomda turuncu rehber noktalar kalir, yakin zoomda parcel ve footprint detayina gecilir.";

    const sourceChips = landSourceStatuses.length
      ? `
        <div class="source-status-chips">
          ${landSourceStatuses
            .map(
              (item) => `<span class="source-status-chip" data-stale="${item.is_stale}">${item.name}: ${item.row_count || 0}</span>`
            )
            .join("")}
        </div>
      `
      : '<div class="workspace-note">Kaynak snapshot ozeti henuz yuklenmedi.</div>';
    const manifestStatusBlock = [
      buildManifestStatusSummaryHtml("market_listing_adapter"),
      buildManifestStatusSummaryHtml("government_property_finder"),
    ]
      .filter(Boolean)
      .join("");

    const errorBlock = landOverlayState.error
      ? `<div class="workspace-note">Son overlay hatasi: ${landOverlayState.error}</div>`
      : "";

    const historyOverviewMode = currentHistoricSalesVisible && landOverlayState.globalOverviewMode === "history";
    const globalSaleReadyItems = historyOverviewMode ? [] : getGlobalSaleReadyDirectoryItems();
    const globalSaleReadyRegionGroups = historyOverviewMode ? [] : getSaleReadyRegionGroups();
    let globalSaleReadyBlock = landOverlayState.globalSaleReadyBaseCount
      ? `
        <div class="global-sale-panel">
          <div class="global-sale-panel-header">
            <div class="nearest-sale-panel-title">Program Genelindeki SatÃ„Â±Ã…Å¸a Uygun Parcel Dizini</div>
            <div class="nearest-sale-panel-note">
              ${hasActiveLandFilters()
                ? `Aktif filtrelerle ${landOverlayState.globalSaleReadyVisibleCount} parcel gÃƒÂ¶rÃƒÂ¼nÃƒÂ¼yor. Temel dizinde ${landOverlayState.globalSaleReadyBaseCount} parcel var.`
                : `TÃƒÂ¼m yÃƒÂ¼klÃƒÂ¼ satÃ„Â±Ã…Å¸a uygun parcel seti burada. Uzak zoomda turuncu cluster olarak gÃƒÂ¶rÃƒÂ¼nÃƒÂ¼r; bir kayda tÃ„Â±klayÃ„Â±nca harita ilgili parsele uÃƒÂ§ar.`}
            </div>
          </div>
          <div class="global-sale-metrics">
            <span class="global-sale-metric"><strong>${landOverlayState.globalSaleReadyVisibleCount}</strong> toplam satÃ„Â±Ã…Å¸ sinyali</span>
            <span class="global-sale-metric"><strong>${landOverlayState.globalRealPriceCount}</strong> gerÃƒÂ§ek fiyatlÃ„Â± kayÃ„Â±t</span>
            <span class="global-sale-metric"><strong>${landOverlayState.globalNonDemoVisibleCount}</strong> demo hariÃƒÂ§ gÃƒÂ¶rÃƒÂ¼nen</span>
          </div>
          <div class="global-sale-region-grid">
            ${globalSaleReadyRegionGroups
              .map(
                (group) => `
                  <button
                    type="button"
                    class="global-sale-region-card"
                    data-sale-ready-region-slug="${group.regionSlug || ""}"
                    data-active="${activeRegion?.slug === group.regionSlug}"
                  >
                    <strong>${group.regionLabel}</strong>
                    <span>${group.total} sale-ready</span>
                    <span>${group.onMarket} on_market</span>
                    <span>${group.realPrice} gerÃƒÂ§ek fiyat</span>
                  </button>
                `
              )
              .join("")}
          </div>
          <div class="global-sale-directory-list">
            ${globalSaleReadyItems
              .map(
                (item) => `
                  <div class="nearest-sale-card">
                    <button type="button" class="nearest-sale-item global-sale-item" data-global-sale-feature-key="${item.featureKey || ""}">
                      <span class="nearest-sale-item-main">
                        <strong>${item.parcelRef}</strong>
                        <span>${item.authority}</span>
                      </span>
                      ${buildSaleReadyBadgesHtml(item)}
                      <span class="nearest-sale-item-meta">
                        <span>Skor ${formatNumber(item.score || 0, 1)}</span>
                        <span>${item.listingStatus || "durum yok"}</span>
                      </span>
                      <span class="nearest-sale-item-meta">
                        <span>${formatSalePrice(item.askPrice)}</span>
                        <span>${item.saleSourceLabel || "Kaynak yok"}</span>
                      </span>
                      <span class="nearest-sale-item-meta">
                        <span>${item.priceTruthDetail || item.priceTruthLabel || "Fiyat tipi bilinmiyor"}</span>
                        <span>${item.linkTruthDetail || item.linkTruthLabel || "Link tipi bilinmiyor"}</span>
                      </span>
                    </button>
                    <div class="nearest-sale-link-row">${buildExternalSaleLink(item.saleUrl, item.saleLinkLabel || "SatÃ„Â±Ã…Å¸ adresine git")}</div>
                  </div>
                `
              )
              .join("") || '<div class="workspace-note">Aktif filtrelerle program genelinde gÃƒÂ¶rÃƒÂ¼nÃƒÂ¼r satÃ„Â±Ã…Å¸ parceli kalmadÃ„Â±.</div>'}
          </div>
          <div class="nearest-sale-panel-note">Son global yenileme: ${formatLandOverlayDate(landOverlayState.globalSaleReadyLoadedAt)}</div>
        </div>
      `
      : '<div class="workspace-note">Program genelindeki satÃ„Â±Ã…Å¸a uygun parcel dizini yÃƒÂ¼kleniyor...</div>';
    if (historyOverviewMode) {
      globalSaleReadyBlock = `
        <div class="global-sale-panel">
          <div class="global-sale-panel-header">
            <div class="nearest-sale-panel-title">Program Genelindeki Gecmis Satis Parcel Dizini</div>
            <div class="nearest-sale-panel-note">
              Uzak zoomda kume noktalari gorunur. Bir noktaya tiklayinca harita ilgili parsele gidip gecmis satis detayini acar.
            </div>
          </div>
          <div class="global-sale-metrics">
            <span class="global-sale-metric"><strong>${landOverlayState.globalHistoricSaleVisibleCount || 0}</strong> gorunen gecmis satis sinyali</span>
            <span class="global-sale-metric"><strong>${landOverlayState.globalHistoricSaleBaseCount || 0}</strong> toplam gecmis satis kaydi</span>
          </div>
          <div class="nearest-sale-panel-note">Son global yenileme: ${formatLandOverlayDate(landOverlayState.globalHistoricSaleLoadedAt)}</div>
        </div>
      `;
    }

    const currentViewSaleVisibleCount = getCurrentViewSaleReadyVisibleCount();
    const currentViewSaleItems = getCurrentViewSaleReadyItems(12);
    const currentViewHistoricSaleCount = getVisibleFeatureCount(landOverlayState.historicSaleFeatures || []);
    const currentViewFootprintCount = getVisibleFeatureCount(landOverlayState.officialSaleFootprintFeatures || []);
    const currentViewBrownfieldCount = getVisibleFeatureCount(landOverlayState.brownfieldFeatures || []);
    const currentViewMarketListingCount = getVisibleFeatureCount(landOverlayState.marketListingFeatures || []);
    const currentViewSaleBlock = currentViewSaleItems.length
      ? `
        <div class="nearest-sale-panel">
          <div class="nearest-sale-panel-title">Bu GÃƒÂ¶rÃƒÂ¼nÃƒÂ¼mdeki SatÃ„Â±Ã…Å¸a Uygun Parceller</div>
          <div class="nearest-sale-panel-note">
            Haritada hareket ettikÃƒÂ§e bu liste gÃƒÂ¼ncellenir. Su anki gorunumde ${currentViewSaleVisibleCount} parcel var${currentViewSaleVisibleCount > currentViewSaleItems.length ? `; ilk ${currentViewSaleItems.length} kayit listeleniyor.` : "."}
          </div>
          <div class="nearest-sale-list">
            ${currentViewSaleItems
              .map(
                (item) => `
                  <div class="nearest-sale-card">
                    <button type="button" class="nearest-sale-item" data-sale-feature-index="${item.index}">
                      <span class="nearest-sale-item-main">
                        <strong>${item.parcelRef}</strong>
                        <span>${item.authority}</span>
                      </span>
                      ${buildSaleReadyBadgesHtml(item)}
                      <span class="nearest-sale-item-meta">
                        <span>${formatDistanceMeters(item.distanceM)}</span>
                        <span>Skor ${formatNumber(item.score || 0, 1)}</span>
                      </span>
                      <span class="nearest-sale-item-meta">
                        <span>${formatSalePrice(item.askPrice)}</span>
                        <span>${item.saleSourceLabel || "Kaynak yok"}</span>
                      </span>
                      <span class="nearest-sale-item-meta">
                        <span>${item.priceTruthDetail || item.priceTruthLabel || "Fiyat tipi bilinmiyor"}</span>
                        <span>${item.linkTruthDetail || item.linkTruthLabel || "Link tipi bilinmiyor"}</span>
                      </span>
                    </button>
                    <div class="nearest-sale-link-row">${buildExternalSaleLink(item.saleUrl, item.saleLinkLabel || "SatÃ„Â±Ã…Å¸ adresine git")}</div>
                  </div>
                `
              )
              .join("")}
          </div>
        </div>
      `
      : `<div class="workspace-note">Bulundugun gorunumde henuz satÃ„Â±Ã…Å¸a uygun parcel bulunmadi. Haritayi kaydirinca veya biraz yakinlasinca bu mini panel dolacak.</div>`;
    const historicModeHintBlock = currentHistoricSalesVisible && currentViewHistoricSaleCount === 0
      ? '<div class="workspace-note">GeÃ§miÅŸ satÄ±ÅŸ modu aÃ§Ä±k: bu gÃ¶rÃ¼nÃ¼mde eÅŸleÅŸme yok veya backend/veritabanÄ± baÄŸlantÄ±sÄ± hazÄ±r deÄŸil.</div>'
      : "";

    setSanitizedHtml(landSourceStatusEl, `
      <div class="source-status-summary">
        <div class="source-status-counts">
          <div><strong>Program geneli ${historyOverviewMode ? "gecmis satis" : "sale-ready"} parcel:</strong> ${historyOverviewMode ? (landOverlayState.globalHistoricSaleVisibleCount || 0) : (landOverlayState.globalSaleReadyVisibleCount || 0)}</div>
          <div><strong>Aktif gorunumde sale-ready parcel:</strong> ${currentViewSaleVisibleCount}</div>
          <div><strong>Aktif gorunumde gecmis satis parcel:</strong> ${currentViewHistoricSaleCount}</div>
          <div><strong>Aktif gorunumde secilebilir satis footprint:</strong> ${currentViewFootprintCount}</div>
          <div><strong>Aktif gorunumde brownfield parcel:</strong> ${currentViewBrownfieldCount}</div>
          <div><strong>Aktif gorunumde portal listing parcel:</strong> ${currentViewMarketListingCount}</div>
          <div><strong>Son overlay yenileme:</strong> ${formatLandOverlayDate(landOverlayState.lastLoadedAt)}</div>
        </div>
        ${getLandFilterSummaryHtml()}
        <div class="workspace-note">${overlayHint}</div>
        ${globalSaleReadyBlock}
        ${currentViewSaleBlock}
        ${historicModeHintBlock}
        ${sourceChips}
        ${manifestStatusBlock}
        ${errorBlock}
      </div>
    `);
    updateNearestSaleJumpButton();
    bindNearestOfficialSaleActions();
    if (!historyOverviewMode) {
      bindGlobalSaleReadyDirectoryActions();
      bindSaleReadyRegionActions();
    }
  }

  function getParcelFeatureSaleSummary(feature) {
    return feature?.properties?.sale_summary && typeof feature.properties.sale_summary === "object"
      ? feature.properties.sale_summary
      : {};
  }

  function buildSaleRecordFromFeature(feature) {
    const props = feature?.properties || {};
    return {
      source_name: props.source_name || "homes_england_landhub",
      source_record_id: props.listing_id || props.source_record_id || props.site_reference || props.parcel_name || props.parcel_ref,
      listing_id: props.listing_id || null,
      parcel_name: props.parcel_name || null,
      label: props.parcel_name || props.listing_id || null,
      listing_status: props.listing_status || null,
      planning_status: props.planning_status || null,
      ask_price: props.ask_price ?? null,
      listing_area_m2: props.listing_area_m2 ?? props.site_area_m2 ?? null,
      listing_area_acres: props.listing_area_acres ?? props.site_area_acres ?? null,
      listing_url: props.listing_url || null,
      source_url: props.source_url || null,
      external_url: props.external_url || null,
      external_label: props.external_label || null,
      provider_name: props.provider_name || null,
      provider_kind: props.provider_kind || null,
      license_scope: props.license_scope || null,
      provider_listing_id: props.provider_listing_id || null,
      source_tier: props.source_tier || props.truth_tier || null,
      truth_tier: props.truth_tier || props.source_tier || null,
      is_demo: Boolean(props.is_demo),
      price_truth: props.price_truth && typeof props.price_truth === "object" ? props.price_truth : null,
      link_truth: props.link_truth && typeof props.link_truth === "object" ? props.link_truth : null,
      source_updated_at: props.source_updated_at || null,
      confidence_score: props.confidence_score ?? null,
      matched_parcel_ref: props.matched_parcel_ref || null,
      matched_inspire_id: props.matched_inspire_id || null,
    };
  }

  function getActionableSaleRecordForParcelFeature(feature, footprint = null) {
    const saleSummary = getParcelFeatureSaleSummary(feature);
    const summaryRecord = getSaleSummaryActionableRecord(saleSummary);
    if (summaryRecord) return summaryRecord;
    if (footprint) return buildSaleRecordFromFeature(footprint);
    return buildSaleRecordFromFeature(feature);
  }

  function getFeatureParcelId(feature) {
    const raw = feature?.properties?.parcel_id ?? feature?.properties?.PARCEL_ID ?? null;
    const numeric = Number(raw);
    return Number.isFinite(numeric) ? numeric : null;
  }

  function getSaleFeatureKey(feature) {
    const props = feature?.properties || {};
    const parcelId = getFeatureParcelId(feature);
    const parcelRef = getParcelRef(feature);
    const sourceName = String(props.source_name || "parcel").trim().toLowerCase() || "parcel";
    const sourceRecordId = props.listing_id || props.source_record_id || props.provider_listing_id || props.id || null;
    if (sourceRecordId) {
      return `${sourceName}::${sourceRecordId}`;
    }
    if (parcelId !== null) {
      return `${sourceName}::parcel_id::${parcelId}`;
    }
    if (parcelRef && parcelRef !== "Parsel") {
      return `${sourceName}::parcel_ref::${parcelRef}`;
    }
    const center = geometryCenterLngLat(feature?.geometry);
    if (center) {
      return `${sourceName}::center::${center.lng.toFixed(6)}:${center.lat.toFixed(6)}`;
    }
    return `${sourceName}::unknown`;
  }

  function findSaleFeatureByKey(featureKey, features = []) {
    if (!featureKey) return null;
    return (features || []).find((candidate) => getSaleFeatureKey(candidate) === featureKey) || null;
  }

  function isMarketListingFeature(feature) {
    const sourceName = String(feature?.properties?.source_name || "").trim().toLowerCase();
    return sourceName === "market_listing_adapter";
  }

  function normalizeListingStatus(value) {
    const normalized = String(value || "").trim().toLowerCase();
    return normalized || "unknown";
  }

  function getSaleReadyQuickFilterLabel(value) {
    return (
      {
        all: "Hepsi",
        on_market: "On market",
        priced: "FiyatÃ„Â± olan",
        linked: "Linki olan",
      }[value] || "Hepsi"
    );
  }

  function getSaleReadyFeatureConfidence(feature) {
    const raw = feature?.properties?.highest_confidence_score ?? feature?.properties?.confidence_score ?? null;
    const numeric = Number(raw);
    return Number.isFinite(numeric) ? numeric : null;
  }

  function getSaleReadyFeatureStatus(feature, fallbackRecord = null) {
    const saleSummary = getParcelFeatureSaleSummary(feature);
    const actionableRecord = fallbackRecord || getActionableSaleRecordForParcelFeature(feature);
    return normalizeListingStatus(actionableRecord?.listing_status || saleSummary?.official_sale_status || null);
  }

  function matchesSaleReadyFeatureFilters(feature) {
    if (!feature) return false;
    const summary = buildSaleReadyFeatureSummary(feature);
    if (!summary) return false;
    const confidence = getSaleReadyFeatureConfidence(feature);
    if (landOverlayFilters.minConfidence > 0 && (confidence === null || confidence < landOverlayFilters.minConfidence)) {
      return false;
    }
    if (landOverlayFilters.reviewOnly && !feature?.properties?.requires_review) {
      return false;
    }
    if (landOverlayFilters.listingStatus !== "all") {
      const statusValue = getSaleReadyFeatureStatus(feature);
      if (statusValue !== normalizeListingStatus(landOverlayFilters.listingStatus)) {
        return false;
      }
    }
    if (landOverlayFilters.saleReadyQuickFilter === "on_market" && !summary.isOnMarket) {
      return false;
    }
    if (landOverlayFilters.saleReadyQuickFilter === "priced" && !summary.hasPrice) {
      return false;
    }
    if (landOverlayFilters.saleReadyQuickFilter === "linked" && !summary.hasSaleLink) {
      return false;
    }
    return true;
  }

  function buildSaleReadyFeatureSummary(feature, options = {}) {
    if (!feature) return null;
    const centerPoint = options.centerPoint || geometryCenterLngLat(feature?.geometry);
    if (!centerPoint) return null;
    const footprint = options.footprint || null;
    const actionableRecord = getActionableSaleRecordForParcelFeature(feature, footprint);
    const actionableLink = actionableRecord
      ? resolveSaleRecordLink(actionableRecord)
      : { url: getListingFeatureLink(footprint), label: getListingFeatureLinkLabel(footprint) };
    const footprintLinkTruth = getBackendTruthPayload(footprint?.properties, "link_truth");
    const summaryPriceTruth = feature?.properties?.top_actionable_truth && typeof feature.properties.top_actionable_truth === "object"
      ? feature.properties.top_actionable_truth
      : null;
    const priceTruth = summaryPriceTruth?.label
      ? {
          label: summaryPriceTruth.label,
          detail: summaryPriceTruth.detail || null,
          tone: summaryPriceTruth.tone || "neutral",
          isReal: summaryPriceTruth.is_real ?? null,
        }
      : getSalePriceTruth(actionableRecord);
    const linkTruth = actionableRecord
      ? getSaleLinkTruth(actionableRecord)
      : footprintLinkTruth?.label
        ? {
            label: footprintLinkTruth.label,
            detail: footprintLinkTruth.detail || null,
            tone: footprintLinkTruth.tone || "neutral",
            isReal: footprintLinkTruth.is_real ?? null,
            hasLink: footprintLinkTruth.has_link ?? Boolean(actionableLink?.url),
          }
        : getSaleLinkTruth(
            footprint
              ? buildSaleRecordFromFeature(footprint)
              : { external_url: actionableLink?.url, external_label: actionableLink?.label, source_name: feature?.properties?.source_name || null }
          );
    const statusValue = getSaleReadyFeatureStatus(feature, actionableRecord);
    const askPrice = actionableRecord?.ask_price ?? footprint?.properties?.ask_price ?? feature?.properties?.sale_summary?.latest_asking_price_gbp ?? null;
    const score = Number(feature?.properties?.confidence_score ?? feature?.properties?.highest_confidence_score ?? 0);
    const parcelId = getFeatureParcelId(feature);
    const visibleSaleCount = Number(feature?.properties?.visible_sale_count ?? feature?.properties?.sale_summary?.visible_sale_count ?? 0) || 0;
    const realPriceCount = Number(feature?.properties?.real_price_count ?? feature?.properties?.sale_summary?.real_price_count ?? 0) || 0;
    return {
      index: Number.isFinite(options.index) ? options.index : null,
      feature,
      featureKey: getSaleFeatureKey(feature),
      parcelId,
      centerPoint,
      parcelRef: getParcelRef(feature),
      authority: feature?.properties?.local_authority || feature?.properties?.LOCAL_AUTHORITY || "Authority bilinmiyor",
      score,
      distanceM: Number.isFinite(options.distanceM) ? options.distanceM : null,
      askPrice,
      hasPrice: hasSalePrice({ ask_price: askPrice }),
      saleUrl: actionableLink?.url || null,
      saleLinkLabel: actionableLink?.label || "SatÃ„Â±Ã…Å¸ adresine git",
      hasSaleLink: linkTruth?.hasLink ?? Boolean(actionableLink?.url),
      saleSourceLabel: actionableRecord?.provider_name || getLandSourceDisplayName(actionableRecord?.source_name),
      listingStatus: statusValue,
      isOnMarket: statusValue === "on_market",
      visibleSaleCount,
      realPriceCount,
      isRealPrice: priceTruth.isReal === true,
      priceTruthLabel: priceTruth.label,
      priceTruthTone: priceTruth.tone,
      priceTruthDetail: priceTruth.detail,
      linkTruthLabel: linkTruth.label,
      linkTruthTone: linkTruth.tone,
      linkTruthDetail: linkTruth.detail,
      requiresReview: Boolean(feature?.properties?.requires_review),
      sourcePriority: getActionableSaleSourcePriority(actionableRecord || footprint),
    };
  }

  function findOfficialSaleParcelFeatureForFootprint(feature) {
    const matchedParcelRef = getMatchedParcelRefFromFeature(feature);
    const matchedInspireId = getMatchedInspireIdFromFeature(feature);
    return (landOverlayState.officialSaleFeatures || []).find((candidate) => {
      const parcelRef = getParcelRef(candidate);
      const inspireId = candidate?.properties?.inspire_id || candidate?.properties?.INSPIRE_ID || null;
      return (matchedParcelRef && parcelRef && matchedParcelRef === parcelRef) || (matchedInspireId && inspireId && matchedInspireId === inspireId);
    }) || null;
  }

  function findBestOfficialSaleFootprintForParcelFeature(feature) {
    const parcelRef = getParcelRef(feature);
    const inspireId = feature?.properties?.inspire_id || feature?.properties?.INSPIRE_ID || null;
    return (landOverlayState.officialSaleFootprintFeatures || [])
      .filter((candidate) => {
        const matchedParcelRef = getMatchedParcelRefFromFeature(candidate);
        const matchedInspireId = getMatchedInspireIdFromFeature(candidate);
        return (parcelRef && matchedParcelRef && matchedParcelRef === parcelRef) || (inspireId && matchedInspireId && matchedInspireId === inspireId);
      })
      .sort((left, right) => geometryAreaM2(left?.geometry) - geometryAreaM2(right?.geometry))[0] || null;
  }

  function getNearestOfficialSaleParcels(limit = 10) {
    if (!map || !Array.isArray(landOverlayState.officialSaleFeatures) || !landOverlayState.officialSaleFeatures.length) {
      return [];
    }
    const footprintByParcelRef = new Map();
    (landOverlayState.officialSaleFootprintFeatures || []).forEach((feature) => {
      const matchedParcelRef = getMatchedParcelRefFromFeature(feature);
      const matchedInspireId = getMatchedInspireIdFromFeature(feature);
      const key = matchedParcelRef || matchedInspireId;
      if (!key) return;
      const current = footprintByParcelRef.get(key);
      const currentScore = Number(current?.properties?.confidence_score || 0);
      const nextScore = Number(feature?.properties?.confidence_score || 0);
      const currentUpdated = current?.properties?.source_updated_at ? new Date(current.properties.source_updated_at).getTime() : 0;
      const nextUpdated = feature?.properties?.source_updated_at ? new Date(feature.properties.source_updated_at).getTime() : 0;
      if (!current || nextScore > currentScore || (nextScore === currentScore && nextUpdated > currentUpdated)) {
        footprintByParcelRef.set(key, feature);
      }
    });
    const center = map.getCenter();
    return landOverlayState.officialSaleFeatures
      .map((feature, index) => {
        const centerPoint = geometryCenterLngLat(feature?.geometry);
        if (!centerPoint) return null;
        const parcelRef = getParcelRef(feature);
        const inspireId = feature?.properties?.inspire_id || feature?.properties?.INSPIRE_ID || null;
        const footprint = footprintByParcelRef.get(parcelRef) || (inspireId ? footprintByParcelRef.get(inspireId) : null);
        const distanceM = haversineDistanceMeters(
          { lng: center.lng, lat: center.lat },
          { lng: centerPoint.lng, lat: centerPoint.lat }
        );
        return buildSaleReadyFeatureSummary(feature, { index, footprint, centerPoint, distanceM });
      })
      .filter(Boolean)
      .sort((a, b) => a.distanceM - b.distanceM)
      .slice(0, limit);
  }

  function getCurrentViewSaleReadyItems(limit = 12) {
    if (!map || !Array.isArray(landOverlayState.officialSaleFeatures) || !landOverlayState.officialSaleFeatures.length) {
      return [];
    }
    const mapBounds = map.getBounds();
    const footprintByParcelRef = new Map();
    (landOverlayState.officialSaleFootprintFeatures || []).forEach((feature) => {
      const matchedParcelRef = getMatchedParcelRefFromFeature(feature);
      const matchedInspireId = getMatchedInspireIdFromFeature(feature);
      const key = matchedParcelRef || matchedInspireId;
      if (!key) return;
      const current = footprintByParcelRef.get(key);
      const currentScore = Number(current?.properties?.confidence_score || 0);
      const nextScore = Number(feature?.properties?.confidence_score || 0);
      const currentUpdated = current?.properties?.source_updated_at ? new Date(current.properties.source_updated_at).getTime() : 0;
      const nextUpdated = feature?.properties?.source_updated_at ? new Date(feature.properties.source_updated_at).getTime() : 0;
      if (!current || nextScore > currentScore || (nextScore === currentScore && nextUpdated > currentUpdated)) {
        footprintByParcelRef.set(key, feature);
      }
    });
    const center = map.getCenter();
    return landOverlayState.officialSaleFeatures
      .map((feature, index) => {
        if (!doesFeatureIntersectMapBounds(feature, mapBounds)) return null;
        const centerPoint = geometryCenterLngLat(feature?.geometry);
        if (!centerPoint) return null;
        const parcelRef = getParcelRef(feature);
        const inspireId = feature?.properties?.inspire_id || feature?.properties?.INSPIRE_ID || null;
        const footprint = footprintByParcelRef.get(parcelRef) || (inspireId ? footprintByParcelRef.get(inspireId) : null);
        const distanceM = haversineDistanceMeters(
          { lng: center.lng, lat: center.lat },
          { lng: centerPoint.lng, lat: centerPoint.lat }
        );
        return buildSaleReadyFeatureSummary(feature, { index, footprint, centerPoint, distanceM });
      })
      .filter(Boolean)
      .sort(compareCurrentViewSaleReadySummaries)
      .slice(0, limit);
  }

  function getCurrentViewSaleReadyVisibleCount() {
    return getVisibleFeatureCount(landOverlayState.officialSaleFeatures || []);
  }

  function compareSaleReadySummaries(left, right) {
    const leftRank = [
      Number(left?.sourcePriority || 0),
      left?.isRealPrice ? 1 : 0,
      left?.hasSaleLink ? 1 : 0,
      left?.hasPrice ? 1 : 0,
      left?.isOnMarket ? 1 : 0,
      Number(left?.score || 0),
    ];
    const rightRank = [
      Number(right?.sourcePriority || 0),
      right?.isRealPrice ? 1 : 0,
      right?.hasSaleLink ? 1 : 0,
      right?.hasPrice ? 1 : 0,
      right?.isOnMarket ? 1 : 0,
      Number(right?.score || 0),
    ];
    const rankDelta = compareRankTuple(leftRank, rightRank);
    if (rankDelta !== 0) return rankDelta * -1;
    const authorityDelta = String(left?.authority || "").localeCompare(String(right?.authority || ""), "tr");
    if (authorityDelta !== 0) return authorityDelta;
    return String(left?.parcelRef || "").localeCompare(String(right?.parcelRef || ""), "tr");
  }

  function getFilteredGlobalSaleReadyFeatures() {
    return (landOverlayState.globalSaleReadyFeatures || []).filter((feature) => matchesSaleReadyFeatureFilters(feature));
  }

  function getGlobalSaleReadyDirectoryItems() {
    return getFilteredGlobalSaleReadyFeatures()
      .map((feature) => buildSaleReadyFeatureSummary(feature))
      .filter(Boolean)
      .sort(compareSaleReadySummaries);
  }

  function getRegionForLngLat(centerPoint) {
    if (!centerPoint) return null;
    return findContainingRegion(centerPoint) || findNearestRegion(centerPoint);
  }

  function getSaleReadyRegionGroups(features = null) {
    const sourceFeatures = Array.isArray(features) ? features : getFilteredGlobalSaleReadyFeatures();
    const groups = new Map();
    sourceFeatures.forEach((feature) => {
      const summary = buildSaleReadyFeatureSummary(feature);
      if (!summary) return;
      const region = getRegionForLngLat(summary.centerPoint);
      const key = region?.slug || "outside";
      const current = groups.get(key) || {
        regionSlug: region?.slug || null,
        regionLabel: region?.label || "Diger Alan",
        total: 0,
        onMarket: 0,
        realPrice: 0,
      };
      current.total += 1;
      if (summary.isOnMarket) current.onMarket += 1;
      if (summary.isRealPrice) current.realPrice += 1;
      groups.set(key, current);
    });
    return Array.from(groups.values()).sort((left, right) => {
      if (right.total !== left.total) return right.total - left.total;
      if (right.onMarket !== left.onMarket) return right.onMarket - left.onMarket;
      return String(left.regionLabel || "").localeCompare(String(right.regionLabel || ""), "tr");
    });
  }

  function buildSaleReadyBadgesHtml(summary) {
    if (!summary) return "";
    const badges = [];
    if (summary.isOnMarket) {
      badges.push({ label: "On market", tone: "market" });
    } else if (summary.listingStatus && summary.listingStatus !== "unknown") {
      badges.push({ label: summary.listingStatus, tone: "status" });
    }
    if (summary.hasPrice) {
      badges.push({ label: summary.priceTruthLabel || "Fiyat var", tone: summary.priceTruthTone || "price" });
    }
    if (summary.hasSaleLink) {
      badges.push({ label: summary.linkTruthLabel || "Link var", tone: summary.linkTruthTone || "link" });
    }
    if (summary.requiresReview) {
      badges.push({ label: "Review", tone: "review" });
    }
    if (!badges.length) {
      badges.push({ label: "Sinyal var", tone: "neutral" });
    }
    return `
      <div class="sale-ready-badges">
        ${badges.map((badge) => `<span class="sale-ready-badge" data-tone="${badge.tone}">${badge.label}</span>`).join("")}
      </div>
    `;
  }

  function compareCurrentViewSaleReadySummaries(left, right) {
    const baseCompare = compareSaleReadySummaries(left, right);
    if (baseCompare !== 0) return baseCompare;
    return Number(left?.distanceM ?? Number.MAX_SAFE_INTEGER) - Number(right?.distanceM ?? Number.MAX_SAFE_INTEGER);
  }

  function buildSaleReadyOverviewCollection(features) {
    return {
      type: "FeatureCollection",
      features: (features || [])
        .map((feature) => {
          const summary = buildSaleReadyFeatureSummary(feature);
          if (!summary?.centerPoint) return null;
          return {
            type: "Feature",
            geometry: {
              type: "Point",
              coordinates: [summary.centerPoint.lng, summary.centerPoint.lat],
            },
            properties: {
              sale_feature_key: summary.featureKey,
              parcel_id: summary.parcelId,
              parcel_ref: summary.parcelRef,
              local_authority: summary.authority,
              overview_kind: "official",
              listing_status: summary.listingStatus,
              score: summary.score,
              has_sale_link: summary.hasSaleLink,
              has_price: summary.hasPrice,
              is_on_market: summary.isOnMarket,
            },
          };
        })
        .filter(Boolean),
    };
  }

  function buildHistoricOverviewCollection(features) {
    return {
      type: "FeatureCollection",
      features: (features || [])
        .map((feature) => {
          const centerPoint = geometryCenterLngLat(feature?.geometry);
          if (!centerPoint) return null;
          const props = feature?.properties || {};
          return {
            type: "Feature",
            geometry: {
              type: "Point",
              coordinates: [centerPoint.lng, centerPoint.lat],
            },
            properties: {
              parcel_id: getFeatureParcelId(feature),
              parcel_ref: getParcelRef(feature),
              local_authority: props.local_authority || props.LOCAL_AUTHORITY || null,
              overview_kind: "history",
              history_transaction_count: Number(props.history_transaction_count || 0) || 0,
              latest_history_sale_date: props.latest_history_sale_date || null,
              latest_history_price_paid: props.latest_history_price_paid ?? null,
              has_sale_link: false,
              has_price: Number(props.latest_history_price_paid || 0) > 0,
              is_on_market: false,
            },
          };
        })
        .filter(Boolean),
    };
  }

  function getCurrentDetailedSaleFeatureCount() {
    return Number(landOverlayState.officialSaleCount || 0)
      + Number(landOverlayState.historicSaleCount || 0)
      + Number(landOverlayState.brownfieldCount || 0)
      + Number(landOverlayState.marketListingCount || 0);
  }

  function applyGlobalSaleReadyOverviewState() {
    const filteredFeatures = getFilteredGlobalSaleReadyFeatures();
    const summaryItems = filteredFeatures
      .map((feature) => buildSaleReadyFeatureSummary(feature))
      .filter(Boolean);
    const overviewCollection = buildSaleReadyOverviewCollection(filteredFeatures);
    setGeoJsonSourceData("sale-ready-overview", overviewCollection);
    landOverlayState = {
      ...landOverlayState,
      globalSaleReadyVisibleCount: filteredFeatures.length,
      globalActiveSaleCount: summaryItems.filter((item) => item.isOnMarket).length,
      globalActionableSaleCount: summaryItems.filter((item) => item.hasSaleLink || item.hasPrice).length,
      globalRealPriceCount: summaryItems.filter((item) => item.isRealPrice).length,
      globalNonDemoVisibleCount: summaryItems.filter((item) => item.visibleSaleCount > 0 || item.feature?.properties?.is_demo === false).length,
      globalSaleReadyLoadedAt: new Date().toISOString(),
      globalSaleReadyFilterKey: `${landOverlayFilters.minConfidence}:${landOverlayFilters.listingStatus}:${landOverlayFilters.saleReadyQuickFilter}:${landOverlayFilters.reviewOnly}`,
      globalOverviewMode: "official",
    };
  }

  function applyGlobalHistoricOverviewState() {
    const features = (landOverlayState.globalHistoricSaleFeatures || []).filter((feature) => {
      if (!feature) return false;
      if (landOverlayFilters.reviewOnly && !feature?.properties?.requires_review) {
        return false;
      }
      if (landOverlayFilters.minConfidence > 0) {
        const confidence = Number(feature?.properties?.highest_confidence_score ?? feature?.properties?.confidence_score);
        if (!Number.isFinite(confidence) || confidence < landOverlayFilters.minConfidence) {
          return false;
        }
      }
      return true;
    });
    const overviewCollection = buildHistoricOverviewCollection(features);
    setGeoJsonSourceData("sale-ready-overview", overviewCollection);
    landOverlayState = {
      ...landOverlayState,
      globalSaleReadyVisibleCount: 0,
      globalActiveSaleCount: 0,
      globalActionableSaleCount: 0,
      globalRealPriceCount: 0,
      globalNonDemoVisibleCount: 0,
      globalHistoricSaleVisibleCount: features.length,
      globalHistoricSaleLoadedAt: new Date().toISOString(),
      globalOverviewMode: "history",
    };
  }

  async function fetchGlobalOverviewFeaturesBySignal({ signalKey, signalValue, label, cacheMap, fetchLimit, force = false }) {
    const bbox = getUnionRegionBboxString() || getLandOverlayBboxString();
    const pageLimit = Math.max(100, Math.min(Math.max(1, Number(fetchLimit || GLOBAL_OVERVIEW_PAGE_LIMIT)), 5000));
    const maxPages = Math.max(1, Number(GLOBAL_OVERVIEW_MAX_PAGES || 1));
    const cacheKey = `${signalKey}:${bbox || "all"}:limit=${pageLimit}:pages=${maxPages}`;
    if (!force && cacheMap.has(cacheKey)) {
      return cacheMap.get(cacheKey) || [];
    }
    const collected = [];
    for (let page = 0; page < maxPages; page += 1) {
      const offset = page * pageLimit;
      const params = new URLSearchParams({
        exclude_demo: "true",
        limit: String(pageLimit),
        offset: String(offset),
        fast_mode: "true",
      });
      params.set(signalKey, signalValue);
      if (bbox) {
        params.set("bbox", bbox);
      }
      const payloadResponse = await fetchJsonWithTimeout(`${landIntelligenceApiBaseUrl}/map/parcels?${params.toString()}`, {
        label,
        fallback: createEmptyFeatureCollection,
        timeoutMs: LAND_OVERLAY_TIMEOUT_MS,
        backoffGroup: `land-overview-${signalKey}`,
      });
      if (!payloadResponse.ok) {
        throw new Error(payloadResponse.error || `${label} yuklenemedi.`);
      }
      const payload = payloadResponse.data || createEmptyFeatureCollection();
      const batch = Array.isArray(payload?.features) ? payload.features : [];
      collected.push(...batch);
      if (batch.length < pageLimit) {
        break;
      }
    }
    cacheMap.set(cacheKey, collected);
    return collected;
  }

  async function fetchCombinedSalesLayerFeatures(force = false) {
    const fetchLimit = Math.max(
      5000,
      Math.min(
        10000,
        Math.max(
          Number(GLOBAL_SALE_READY_FETCH_LIMIT || 5000),
          Number(GLOBAL_HISTORY_FETCH_LIMIT || 5000),
          Number(LAND_SIGNAL_FETCH_LIMIT || 0)
        )
      )
    );
    const cacheKey = `combined-sales-history:limit=${fetchLimit}`;
    if (!force && combinedSalesLayerCache.has(cacheKey)) {
      return combinedSalesLayerCache.get(cacheKey) || [];
    }
    if (!force && combinedSalesLayerFetchPromise && combinedSalesLayerFetchPromiseKey === cacheKey) {
      return combinedSalesLayerFetchPromise;
    }
    const fetchPromise = (async () => {
      const payloadResponse = await fetchJsonWithTimeout(`${landIntelligenceApiBaseUrl}/map/sales-history/combined?limit=${fetchLimit}`, {
        label: "Birlesik satis gecmisi katmani",
        fallback: createEmptyFeatureCollection,
        timeoutMs: LAND_MARKET_TIMEOUT_MS,
        backoffGroup: "land-combined-sales-history",
        ignoreBackoff: true,
      });
      if (!payloadResponse.ok) {
        throw new Error(payloadResponse.error || "Birlesik satis gecmisi katmani yuklenemedi.");
      }
      const payload = payloadResponse.data || createEmptyFeatureCollection();
      const features = (Array.isArray(payload?.features) ? payload.features : [])
        .map((feature) => normalizeCombinedSalesLayerFeature(feature))
        .filter(Boolean);
      combinedSalesLayerCache.set(cacheKey, features);
      return features;
    })();
    if (!force) {
      combinedSalesLayerFetchPromise = fetchPromise;
      combinedSalesLayerFetchPromiseKey = cacheKey;
    }
    try {
      return await fetchPromise;
    } finally {
      if (combinedSalesLayerFetchPromise === fetchPromise) {
        combinedSalesLayerFetchPromise = null;
        combinedSalesLayerFetchPromiseKey = null;
      }
    }
  }

  async function fetchGlobalSaleReadyFeatures(force = false) {
    const bbox = getUnionRegionBboxString() || getLandOverlayBboxString();
    const pageLimit = Math.max(100, Math.min(Math.max(1, Number(GLOBAL_SALE_READY_FETCH_LIMIT || GLOBAL_OVERVIEW_PAGE_LIMIT)), 5000));
    const maxPages = Math.max(1, Number(GLOBAL_OVERVIEW_MAX_PAGES || 1));
    const cacheKey = `market_listing_adapter:${bbox || "all"}:limit=${pageLimit}:pages=${maxPages}:status=${landOverlayFilters.listingStatus}`;
    if (!force && globalSaleReadyCache.has(cacheKey)) {
      return globalSaleReadyCache.get(cacheKey) || [];
    }
    if (!force && globalSaleReadyFetchPromise && globalSaleReadyFetchPromiseKey === cacheKey) {
      return globalSaleReadyFetchPromise;
    }
    const fetchPromise = (async () => {
      const collected = [];
      for (let page = 0; page < maxPages; page += 1) {
        const offset = page * pageLimit;
        const params = appendLandOverlayFilterParams(
          new URLSearchParams({
            source: "market_listing_adapter",
            exclude_demo: "true",
            limit: String(pageLimit),
            offset: String(offset),
          }),
          { listingStatus: true }
        );
        if (bbox) {
          params.set("bbox", bbox);
        }
        const payloadResponse = await fetchJsonWithTimeout(`${landIntelligenceApiBaseUrl}/map/listings?${params.toString()}`, {
          label: "Global market listing parcelleri",
          fallback: createEmptyFeatureCollection,
          timeoutMs: LAND_MARKET_TIMEOUT_MS,
          backoffGroup: "land-overview-market-listings",
          ignoreBackoff: true,
        });
        if (!payloadResponse.ok) {
          throw new Error(payloadResponse.error || "Global market listing parcelleri yuklenemedi.");
        }
        const payload = payloadResponse.data || createEmptyFeatureCollection();
        const batch = Array.isArray(payload?.features) ? payload.features : [];
        collected.push(...batch);
        if (batch.length < pageLimit) {
          break;
        }
      }
      let resolvedFeatures = collected;
      if (!resolvedFeatures.length) {
        const fallbackFeatures = await fetchCombinedSalesLayerFeatures(force);
        resolvedFeatures = filterSalesLayerFeaturesByBbox(
          fallbackFeatures.filter((feature) => feature?.properties?.external_market_evidence_available),
          bbox
        ).filter((feature) => {
          if (landOverlayFilters.listingStatus === "all") return true;
          return getSaleReadyFeatureStatus(feature) === normalizeListingStatus(landOverlayFilters.listingStatus);
        });
      }
      globalSaleReadyCache.set(cacheKey, resolvedFeatures);
      return resolvedFeatures;
    })();
    if (!force) {
      globalSaleReadyFetchPromise = fetchPromise;
      globalSaleReadyFetchPromiseKey = cacheKey;
    }
    try {
      return await fetchPromise;
    } finally {
      if (globalSaleReadyFetchPromise === fetchPromise) {
        globalSaleReadyFetchPromise = null;
        globalSaleReadyFetchPromiseKey = null;
      }
    }
  }

  async function fetchGlobalHistoricSaleFeatures(force = false) {
    const features = await fetchGlobalOverviewFeaturesBySignal({
      signalKey: "history_signal",
      signalValue: "true",
      label: "Global gecmis satis parcelleri",
      cacheMap: globalHistoricSaleCache,
      fetchLimit: GLOBAL_HISTORY_FETCH_LIMIT,
      force,
    });
    if (features.length > 0) {
      return features;
    }
    const bbox = getUnionRegionBboxString() || getLandOverlayBboxString();
    const fallbackFeatures = await fetchCombinedSalesLayerFeatures(force);
    const cacheKey = `history_signal:${bbox || "all"}:fallback`;
    const resolvedFeatures = filterSalesLayerFeaturesByBbox(
      fallbackFeatures.filter((feature) => feature?.properties?.sales_history_available),
      bbox
    );
    globalHistoricSaleCache.set(cacheKey, resolvedFeatures);
    return resolvedFeatures;
  }

  async function syncGlobalSaleReadyOverview(force = false) {
    if (!map) return;
    if (!landIntelligenceApiBaseUrl) {
      setGeoJsonSourceData("sale-ready-overview", createEmptyFeatureCollection());
      landOverlayState = {
        ...landOverlayState,
        globalSaleReadyBaseCount: 0,
        globalSaleReadyVisibleCount: 0,
        globalActiveSaleCount: 0,
        globalActionableSaleCount: 0,
        globalRealPriceCount: 0,
        globalNonDemoVisibleCount: 0,
        globalSaleReadyFeatures: [],
        globalSaleReadyLoadedAt: null,
        globalSaleReadyFilterKey: null,
        globalHistoricSaleBaseCount: 0,
        globalHistoricSaleVisibleCount: 0,
        globalHistoricSaleFeatures: [],
        globalHistoricSaleLoadedAt: null,
        globalOverviewMode: "official",
      };
      updateLandSourceStatusPanel();
      return;
    }
    if (map.getZoom() >= LAND_SALE_OVERVIEW_HIDE_ZOOM) {
      updateLandSourceStatusPanel();
      return;
    }
    if (!currentHistoricSalesVisible && !currentOfficialSaleVisible && !currentMarketListingsVisible && !currentBrownfieldVisible) {
      setGeoJsonSourceData("sale-ready-overview", createEmptyFeatureCollection());
      landOverlayState = {
        ...landOverlayState,
        globalSaleReadyVisibleCount: 0,
        globalHistoricSaleVisibleCount: 0,
      };
      updateLandSourceStatusPanel();
      return;
    }
    const requestId = ++globalSaleReadyRequestId;
    try {
      if (currentHistoricSalesVisible) {
        if (force || !(landOverlayState.globalHistoricSaleFeatures || []).length) {
          const features = await fetchGlobalHistoricSaleFeatures(force);
          if (requestId !== globalSaleReadyRequestId) return;
          landOverlayState = {
            ...landOverlayState,
            globalHistoricSaleBaseCount: features.length,
            globalHistoricSaleFeatures: features,
          };
        }
        applyGlobalHistoricOverviewState();
      } else {
        if (force || !(landOverlayState.globalSaleReadyFeatures || []).length) {
          const features = await fetchGlobalSaleReadyFeatures(force);
          if (requestId !== globalSaleReadyRequestId) return;
          landOverlayState = {
            ...landOverlayState,
            globalSaleReadyBaseCount: features.length,
            globalSaleReadyFeatures: features,
          };
        }
        applyGlobalSaleReadyOverviewState();
      }
    } catch (error) {
      if (requestId !== globalSaleReadyRequestId) return;
      landOverlayState = {
        ...landOverlayState,
        globalHistoricSaleLoadedAt: currentHistoricSalesVisible ? new Date().toISOString() : landOverlayState.globalHistoricSaleLoadedAt,
        globalSaleReadyLoadedAt: new Date().toISOString(),
        error: error?.message || (currentHistoricSalesVisible ? "Program geneli gecmis satis parcel dizini yuklenemedi." : "Program geneli satÃ„Â±Ã…Å¸ parcel dizini yÃƒÂ¼klenemedi."),
      };
    }
    updateLandSourceStatusPanel();
  }

  function buildRegionSaleReadyParams() {
    if (!activeRegion) return null;
    return appendLandOverlayFilterParams(
      new URLSearchParams({
        sale_ready_signal: "true",
        bbox: activeRegion.bbox.join(","),
        limit: String(Math.min(LAND_SIGNAL_FETCH_LIMIT, 900)),
      })
    );
  }

  function buildRegionSaleReadyCacheKey() {
    if (!activeRegion) return null;
    const params = buildRegionSaleReadyParams();
    if (!params) return null;
    return `${activeRegion.slug}:${params.toString()}`;
  }

  async function fetchRegionSaleReadyFeatures(force = false) {
    if (!activeRegion || !landIntelligenceApiBaseUrl) {
      return [];
    }
    const cacheKey = buildRegionSaleReadyCacheKey();
    const params = buildRegionSaleReadyParams();
    if (!cacheKey) {
      return [];
    }
    if (!params) {
      return [];
    }
    if (!force && regionSaleReadyCache.has(cacheKey)) {
      return regionSaleReadyCache.get(cacheKey) || [];
    }
    try {
      const payloadResponse = await fetchJsonWithTimeout(`${landIntelligenceApiBaseUrl}/map/parcels?${params.toString()}`, {
        label: "Bolge sale-ready parcelleri",
        fallback: createEmptyFeatureCollection,
      });
      if (!payloadResponse.ok) {
        return [];
      }
      const payload = payloadResponse.data || createEmptyFeatureCollection();
      const filtered = filterLandOverlayFeatures(payload);
      let features = filtered.features || [];
      if (!features.length && activeRegion?.bbox) {
        const fallbackFeatures = await fetchCombinedSalesLayerFeatures(force);
        features = filterSalesLayerFeaturesByBbox(
          fallbackFeatures.filter((feature) => feature?.properties?.external_market_evidence_available),
          activeRegion.bbox.join(",")
        );
      }
      regionSaleReadyCache.set(cacheKey, features);
      return features;
    } catch (_error) {
      return [];
    }
  }

  function updateNearestSaleJumpButton() {
    if (!jumpNearestSaleBtnEl) return;
    const shouldShow = Boolean(isParcelViewMode() && currentOfficialSaleVisible && activeRegion && !currentHistoricSalesVisible);
    jumpNearestSaleBtnEl.classList.toggle("hidden", !shouldShow);
    if (!shouldShow) {
      jumpNearestSaleBtnEl.disabled = false;
      setSanitizedText(jumpNearestSaleBtnEl, "En Yakin Satisa Uygun Parsele Git");
      return;
    }
    setSanitizedText(jumpNearestSaleBtnEl, "En Yakin Satisa Uygun Parsele Git");
  }

  async function jumpToNearestSaleReadyParcel() {
    if (!map || !activeRegion) return;
    if (currentHistoricSalesVisible) {
      showStatus("Gecmis satis modu acikken resmi satis odak atlamasi kapatilir.", true);
      return;
    }
    jumpNearestSaleBtnEl.disabled = true;
    setSanitizedText(jumpNearestSaleBtnEl, "Satis parcelleri araniyor...");
    try {
      let nearestItems = getNearestOfficialSaleParcels(1);
      if (!nearestItems.length) {
        const regionFeatures = await fetchRegionSaleReadyFeatures();
        const center = map.getCenter();
        nearestItems = (regionFeatures || [])
          .map((feature) => {
            const centerPoint = geometryCenterLngLat(feature?.geometry);
            if (!centerPoint) return null;
            return {
              feature,
              distanceM: haversineDistanceMeters(
                { lng: center.lng, lat: center.lat },
                { lng: centerPoint.lng, lat: centerPoint.lat }
              ),
            };
          })
          .filter(Boolean)
          .sort((a, b) => a.distanceM - b.distanceM)
          .slice(0, 1);
      }
      const nearestFeature = nearestItems[0]?.feature || null;
      if (!nearestFeature) {
        showStatus("Aktif bolgede gosterilecek satisa uygun parcel bulunamadi.", true);
        return;
      }
      showStatus("En yakin satisa uygun parsele gidiliyor...", true);
      await focusOfficialSaleParcel(nearestFeature);
    } finally {
      jumpNearestSaleBtnEl.disabled = false;
      updateNearestSaleJumpButton();
    }
  }

  function bindNearestOfficialSaleActions() {
    if (!landSourceStatusEl) return;
    landSourceStatusEl.querySelectorAll("[data-sale-feature-index]").forEach((buttonEl) => {
      buttonEl.addEventListener("click", () => {
        const index = Number(buttonEl.getAttribute("data-sale-feature-index"));
        const feature = Number.isFinite(index) ? landOverlayState.officialSaleFeatures?.[index] : null;
        if (!feature) return;
        void focusOfficialSaleParcel(feature);
      });
    });
  }

  function bindGlobalSaleReadyDirectoryActions() {
    if (!landSourceStatusEl) return;
    landSourceStatusEl.querySelectorAll("[data-global-sale-feature-key]").forEach((buttonEl) => {
      buttonEl.addEventListener("click", () => {
        const featureKey = buttonEl.getAttribute("data-global-sale-feature-key");
        if (!featureKey) return;
        const feature = findSaleFeatureByKey(featureKey, landOverlayState.globalSaleReadyFeatures || []);
        if (!feature) return;
        void focusSaleReadyFeature(feature);
      });
    });
  }

  function bindSaleReadyRegionActions() {
    if (!landSourceStatusEl) return;
    landSourceStatusEl.querySelectorAll("[data-sale-ready-region-slug]").forEach((buttonEl) => {
      buttonEl.addEventListener("click", async () => {
        const regionSlug = buttonEl.getAttribute("data-sale-ready-region-slug");
        if (!regionSlug) return;
        const region = regionMap.get(regionSlug);
        if (!region || !map) return;
        if (!activeRegion || activeRegion.slug !== region.slug) {
          activeRegionMode = "manual";
          await switchRegion(region, "manual");
        }
        map.fitBounds(
          [
            [region.bbox[0], region.bbox[1]],
            [region.bbox[2], region.bbox[3]],
          ],
          {
            padding: { top: 60, right: 360, bottom: 60, left: 60 },
            duration: 900,
            maxZoom: 10.5,
          }
        );
      });
    });
  }

  async function focusMarketListingFeature(feature) {
    if (!map || !feature) return;
    updateSelectedParcel(feature);
    const bounds = geometryBounds(feature.geometry);
    const centerPoint = geometryCenterLngLat(feature.geometry);
    if (bounds) {
      map.fitBounds(
        [
          [bounds.minLng, bounds.minLat],
          [bounds.maxLng, bounds.maxLat],
        ],
        {
          padding: { top: 80, right: 360, bottom: 80, left: 80 },
          duration: 900,
          maxZoom: 18.8,
        }
      );
    } else if (centerPoint) {
      map.easeTo({
        center: [centerPoint.lng, centerPoint.lat],
        zoom: Math.max(map.getZoom(), 17.8),
        duration: 900,
      });
    }
    if (centerPoint) {
      window.setTimeout(() => {
        openParcelPopup(feature, centerPoint);
      }, 520);
    }
  }

  async function focusSaleReadyFeature(feature) {
    if (!feature) return;
    if (isMarketListingFeature(feature)) {
      await focusMarketListingFeature(feature);
      return;
    }
    await focusOfficialSaleParcel(feature);
  }

  async function focusOfficialSaleParcel(feature) {
    if (!map || !feature) return;
    const parcelRef = getParcelRef(feature);
    const inspireId = feature?.properties?.inspire_id || feature?.properties?.INSPIRE_ID || null;
    const matchingFootprint = (landOverlayState.officialSaleFootprintFeatures || [])
      .filter((candidate) => {
        const matchedRef = getMatchedParcelRefFromFeature(candidate);
        const matchedInspireId = getMatchedInspireIdFromFeature(candidate);
        return (parcelRef && matchedRef && matchedRef === parcelRef) || (inspireId && matchedInspireId && matchedInspireId === inspireId);
      })
      .sort((a, b) => geometryAreaM2(a?.geometry) - geometryAreaM2(b?.geometry))[0];
    if (matchingFootprint) {
      const footprintCenter = geometryCenterLngLat(matchingFootprint.geometry);
      await focusOfficialSaleFootprint(matchingFootprint, footprintCenter);
      return;
    }
    updateSelectedParcel(feature);
    const bounds = geometryBounds(feature.geometry);
    const centerPoint = geometryCenterLngLat(feature.geometry);
    if (bounds) {
      map.fitBounds(
        [
          [bounds.minLng, bounds.minLat],
          [bounds.maxLng, bounds.maxLat],
        ],
        {
          padding: { top: 80, right: 360, bottom: 80, left: 80 },
          duration: 950,
          maxZoom: 18.2,
        }
      );
    } else if (centerPoint) {
      map.easeTo({
        center: [centerPoint.lng, centerPoint.lat],
        zoom: Math.max(map.getZoom(), 17.5),
        duration: 950,
      });
    }
    if (centerPoint) {
      window.setTimeout(() => {
        openParcelPopup(feature, centerPoint);
      }, 1000);
    }
  }

  async function focusHistoricSaleParcel(feature) {
    if (!map || !feature) return;
    updateSelectedParcel(feature);
    const bounds = geometryBounds(feature.geometry);
    const centerPoint = geometryCenterLngLat(feature.geometry);
    if (bounds) {
      map.fitBounds(
        [
          [bounds.minLng, bounds.minLat],
          [bounds.maxLng, bounds.maxLat],
        ],
        {
          padding: { top: 80, right: 360, bottom: 80, left: 80 },
          duration: 950,
          maxZoom: 18.2,
        }
      );
    } else if (centerPoint) {
      map.easeTo({
        center: [centerPoint.lng, centerPoint.lat],
        zoom: Math.max(map.getZoom(), 17.5),
        duration: 950,
      });
    }
    if (centerPoint) {
      window.setTimeout(() => {
        openSignalPopup(feature, centerPoint, "historic_sale");
      }, 650);
    }
  }

  function buildFeatureFromParcelDetail(detail) {
    if (!detail || typeof detail !== "object" || !detail.geometry) return null;
    return {
      type: "Feature",
      geometry: detail.geometry,
      properties: {
        parcel_id: detail.parcel_id ?? null,
        parcel_ref: detail.parcel_ref ?? detail.inspire_id ?? null,
        inspire_id: detail.inspire_id ?? null,
        local_authority: detail.local_authority ?? null,
        postcode: detail.postcode ?? null,
        address_text: detail.address_text ?? null,
        area_m2: detail.area_m2 ?? null,
        perimeter_m: detail.perimeter_m ?? null,
        confidence_score: detail.confidence_score ?? null,
      },
    };
  }

  async function focusParcelByIdForContractor(parcelId) {
    const numericParcelId = Number(parcelId);
    if (!Number.isFinite(numericParcelId) || numericParcelId <= 0) {
      showStatus("Contractor parcel odagi icin gecerli parcel_id gerekli.", true);
      return { ok: false, error: "invalid_parcel_id" };
    }
    if (!map || !landIntelligenceApiBaseUrl) {
      showStatus("Contractor parcel odagi icin harita/API hazir degil.", true);
      return { ok: false, error: "map_or_api_not_ready" };
    }

    const detailResponse = await fetchJsonWithTimeout(
      `${landIntelligenceApiBaseUrl}/parcels/${numericParcelId}`,
      {
        label: "Contractor parcel detail",
        fallback: null,
        backoffGroup: "contractor-parcel-focus",
      }
    );
    if (!detailResponse.ok || !detailResponse.data) {
      showStatus(`Contractor parcel ${numericParcelId} detayi alinamadi.`, true);
      return { ok: false, error: "parcel_detail_unavailable" };
    }

    const feature = buildFeatureFromParcelDetail(detailResponse.data);
    if (!feature || !feature.geometry) {
      showStatus(`Contractor parcel ${numericParcelId} geometri kaydi bulunamadi.`, true);
      return { ok: false, error: "parcel_geometry_missing" };
    }

    updateSelectedParcel(feature);
    const bounds = geometryBounds(feature.geometry);
    const centerPoint = geometryCenterLngLat(feature.geometry);

    if (bounds) {
      map.fitBounds(
        [
          [bounds.minLng, bounds.minLat],
          [bounds.maxLng, bounds.maxLat],
        ],
        {
          padding: { top: 80, right: 360, bottom: 80, left: 80 },
          duration: 900,
          maxZoom: 18.3,
        }
      );
    } else if (centerPoint) {
      map.easeTo({
        center: [centerPoint.lng, centerPoint.lat],
        zoom: Math.max(map.getZoom(), 17.3),
        duration: 900,
      });
    }

    if (centerPoint) {
      window.setTimeout(() => {
        openParcelPopup(feature, centerPoint);
      }, 520);
    }

    showStatus(`Contractor parcel ${numericParcelId} odaklandi.`);
    return {
      ok: true,
      parcel_id: numericParcelId,
      parcel_ref: feature?.properties?.parcel_ref || null,
    };
  }

  window.AAYS_CONTRACTOR_INTEGRATION = {
    focusParcelById(parcelId) {
      return focusParcelByIdForContractor(parcelId);
    },
  };

  window.addEventListener("aays:contractor-focus-parcel", (event) => {
    const parcelId = event?.detail?.parcelId;
    void focusParcelByIdForContractor(parcelId);
  });

  function findNearestFeatureToCenter(features, centerPoint) {
    if (!Array.isArray(features) || !features.length || !centerPoint) return null;
    let best = null;
    let bestDistance = Number.POSITIVE_INFINITY;
    features.forEach((feature) => {
      const featureCenter = geometryCenterLngLat(feature?.geometry);
      if (!featureCenter) return;
      const distance = haversineDistanceMeters(centerPoint, featureCenter);
      if (!Number.isFinite(distance)) return;
      if (distance < bestDistance) {
        bestDistance = distance;
        best = feature;
      }
    });
    return best;
  }

  async function focusNearestHistoricSaleParcelIfNeeded() {
    if (!map || !currentHistoricSalesVisible) return;
    const center = map.getCenter();
    const centerPoint = { lng: center.lng, lat: center.lat };
    let candidates = Array.isArray(landOverlayState.historicSaleFeatures) ? landOverlayState.historicSaleFeatures : [];
    if (!candidates.length) {
      try {
        candidates = await fetchGlobalHistoricSaleFeatures(false);
      } catch (_error) {
        candidates = [];
      }
    }
    if (!candidates.length) {
      showStatus("Gecmis satis kaydi bu gorunumde bulunamadi. En yakin kayda odaklanmak icin haritayi uzaklastirabilirsiniz.", true);
      return;
    }
    const target = findNearestFeatureToCenter(candidates, centerPoint) || candidates[0];
    if (target) {
      await focusHistoricSaleParcel(target);
    }
  }

  function getMatchedParcelRefFromFeature(feature) {
    const props = feature?.properties || {};
    return props.matched_parcel_ref || props.parcel_ref || props.PARCEL_REF || null;
  }

  function getMatchedInspireIdFromFeature(feature) {
    const props = feature?.properties || {};
    return props.matched_inspire_id || props.inspire_id || props.INSPIRE_ID || null;
  }

  async function fetchMatchedParcelFeature(feature) {
    if (!landIntelligenceApiBaseUrl || !feature) return null;
    const matchedParcelRef = getMatchedParcelRefFromFeature(feature);
    const matchedInspireId = getMatchedInspireIdFromFeature(feature);
    if (!matchedParcelRef && !matchedInspireId) {
      return null;
    }
    const params = new URLSearchParams({ format: "geojson", exclude_demo: "true", limit: "1" });
    if (matchedParcelRef) {
      params.set("parcel_ref", matchedParcelRef);
    } else if (matchedInspireId) {
      params.set("inspire_id", matchedInspireId);
    }
    const payloadResponse = await fetchJsonWithTimeout(`${landIntelligenceApiBaseUrl}/parcels?${params.toString()}`, {
      label: "Eslesen parcel sorgusu",
      fallback: { type: "FeatureCollection", features: [] },
    });
    const payload = payloadResponse.data || { type: "FeatureCollection", features: [] };
    return payload?.features?.[0] || null;
  }

  function hasOfficialSaleFootprintAtPoint(point) {
    if (!map || !point || !map.getLayer("official-sale-footprint-fill")) {
      return false;
    }
    return map.queryRenderedFeatures(point, { layers: ["official-sale-footprint-fill"] }).length > 0;
  }

  function findHistoricSaleFeatureAtPoint(point) {
    if (!map || !point) return null;
    const layerIds = ["historic-sale-parcel-fill", "historic-sale-parcel-line"].filter((layerId) => map.getLayer(layerId));
    if (!layerIds.length) return null;
    const features = map.queryRenderedFeatures(point, { layers: layerIds });
    return features[0] || null;
  }

  async function focusOfficialSaleFootprint(feature, lngLat) {
    if (!map || !feature) return;
    parcelClickSuppressionUntil = Date.now() + 450;
    const matchedParcelFeature = await fetchMatchedParcelFeature(feature);
    if (matchedParcelFeature) {
      updateSelectedParcel(matchedParcelFeature);
    }
    const focusGeometry = feature.geometry || matchedParcelFeature?.geometry;
    const bounds = geometryBounds(focusGeometry);
    const centerPoint = lngLat
      ? { lng: lngLat.lng, lat: lngLat.lat }
      : geometryCenterLngLat(focusGeometry) || geometryCenterLngLat(matchedParcelFeature?.geometry);
    if (bounds) {
      map.fitBounds(
        [
          [bounds.minLng, bounds.minLat],
          [bounds.maxLng, bounds.maxLat],
        ],
        {
          padding: { top: 80, right: 360, bottom: 80, left: 80 },
          duration: 850,
          maxZoom: 19,
        }
      );
    } else if (centerPoint) {
      map.easeTo({
        center: [centerPoint.lng, centerPoint.lat],
        zoom: Math.max(map.getZoom(), 18.2),
        duration: 850,
      });
    }
    const popupLngLat = centerPoint || geometryCenterLngLat(feature.geometry) || geometryCenterLngLat(matchedParcelFeature?.geometry);
    if (popupLngLat) {
      window.setTimeout(() => {
        openSignalPopup(feature, popupLngLat, "official_sale_footprint");
      }, 320);
    }
  }

  function ensureComparedParcelsLandIntelligence(entries) {
    if (!landIntelligenceApiBaseUrl || !Array.isArray(entries)) return;
    entries.forEach((entry) => {
      if (!entry?.ref) return;
      const cached = landIntelligenceCache.get(entry.ref);
      if (!cached || (!cached.loading && !cached.hasFetched)) {
        fetchLandIntelligenceForParcelRef(entry.ref).catch(() => {});
      }
    });
  }


  function buildDistrictSalesContextHtml(props) {
    const p = props || {};
    if (!p.district_sales_context_available) return "";

    const txCount = Number(p.district_sales_tx_count || 0);
    const recentCount = Number(p.district_sales_recent_5y_count || 0);
    const avgPrice = Number(p.district_sales_avg_price_gbp || 0);
    const recentAvgPrice = Number(p.district_sales_recent_5y_avg_price_gbp || 0);
    const confidence = Number(p.district_sales_context_confidence || 0);

    const matchedDistrict = p.district_sales_matched_district || "-";
    const county = p.district_sales_county || "-";
    const minDate = p.district_sales_min_sale_date || "-";
    const maxDate = p.district_sales_max_sale_date || "-";

    return `
      <div class="workspace-section district-sales-context-card">
        <h3 class="workspace-section-title">District sales context</h3>
        <div class="metric-grid">
          <div class="metric-card"><div class="metric-card-label">Matched district</div><div class="metric-card-value">${escapeHtml(matchedDistrict)}</div></div>
          <div class="metric-card"><div class="metric-card-label">County</div><div class="metric-card-value">${escapeHtml(county)}</div></div>
          <div class="metric-card"><div class="metric-card-label">All sales tx</div><div class="metric-card-value">${formatNumber(txCount, 0)}</div></div>
          <div class="metric-card"><div class="metric-card-label">Avg price</div><div class="metric-card-value">${avgPrice ? `GBP ${formatNumber(avgPrice, 0)}` : "-"}</div></div>
          <div class="metric-card"><div class="metric-card-label">Recent 5y tx</div><div class="metric-card-value">${formatNumber(recentCount, 0)}</div></div>
          <div class="metric-card"><div class="metric-card-label">Recent 5y avg</div><div class="metric-card-value">${recentAvgPrice ? `GBP ${formatNumber(recentAvgPrice, 0)}` : "-"}</div></div>
          <div class="metric-card"><div class="metric-card-label">Sale date range</div><div class="metric-card-value">${escapeHtml(minDate)} - ${escapeHtml(maxDate)}</div></div>
          <div class="metric-card"><div class="metric-card-label">Context confidence</div><div class="metric-card-value">${confidence ? `${formatNumber(confidence * 100, 0)}%` : "-"}</div></div>
        </div>
        <div class="workspace-note">
          District-level fallback from local authority to PPD district. This is regional sales context, not parcel-level sale history.
        </div>
      </div>
    `;
  }


  function buildExternalMarketEvidenceHtml(props) {
    const p = props || {};
    if (!p.external_market_evidence_available) return "";

    const count = Number(p.external_market_evidence_count || 0);
    const polygonCount = Number(p.external_market_polygon_match_count || 0);
    const l2Count = Number(p.external_market_l2_count || 0);
    const l3Count = Number(p.external_market_l3_count || 0);
    const bestOverlap = Number(p.external_market_best_overlap_ratio || 0);
    const avgOverlap = Number(p.external_market_avg_overlap_ratio || 0);
    const bestConfidence = Number(p.external_market_best_confidence_score || 0);
    const samples = Array.isArray(p.external_market_evidence_samples) ? p.external_market_evidence_samples : [];

    const sampleRows = samples.slice(0, 5).map((item) => {
      const url = item.source_url || "";
      const label = item.listing_id || item.source_row_id || "listing";
      const overlap = Number(item.overlap_ratio || 0);
      const conf = Number(item.confidence_score || 0);
      const link = url
        ? `<a href="${escapeHtml(url)}" target="_blank" rel="noopener noreferrer">${escapeHtml(label)}</a>`
        : escapeHtml(label);

      return `<div class="workspace-row"><span>${link}</span><strong>overlap ${formatNumber(overlap * 100, 0)}% Â· conf ${formatNumber(conf * 100, 0)}%</strong></div>`;
    }).join("");

    return `
      <div class="workspace-section external-market-evidence-card">
        <h3 class="workspace-section-title">External market polygon evidence</h3>
        <div class="metric-grid">
          <div class="metric-card"><div class="metric-card-label">Matched listings</div><div class="metric-card-value">${formatNumber(count, 0)}</div></div>
          <div class="metric-card"><div class="metric-card-label">Polygon matches</div><div class="metric-card-value">${formatNumber(polygonCount, 0)}</div></div>
          <div class="metric-card"><div class="metric-card-label">L2 rows</div><div class="metric-card-value">${formatNumber(l2Count, 0)}</div></div>
          <div class="metric-card"><div class="metric-card-label">L3 rows</div><div class="metric-card-value">${formatNumber(l3Count, 0)}</div></div>
          <div class="metric-card"><div class="metric-card-label">Best overlap</div><div class="metric-card-value">${bestOverlap ? `${formatNumber(bestOverlap * 100, 0)}%` : "-"}</div></div>
          <div class="metric-card"><div class="metric-card-label">Avg overlap</div><div class="metric-card-value">${avgOverlap ? `${formatNumber(avgOverlap * 100, 0)}%` : "-"}</div></div>
          <div class="metric-card"><div class="metric-card-label">Best confidence</div><div class="metric-card-value">${bestConfidence ? `${formatNumber(bestConfidence * 100, 0)}%` : "-"}</div></div>
        </div>
        <div class="workspace-stack">
          ${sampleRows || '<div class="workspace-note">Sample evidence row not available.</div>'}
        </div>
        <div class="workspace-note">
          External listing polygon matched to this parcel. This is corroborating market evidence, not official HMLR completed sale history.
        </div>
      </div>
    `;
  }


  function buildVerifiedSalesHistoryHtml(props) {
    const p = props || {};
    if (!p.sales_history_available) return "";
    const records = Array.isArray(p.sales_history_records) ? p.sales_history_records : [];
    const rows = records.slice(0, 10).map((r) => {
      return '<div class="workspace-row"><span>' +
        escapeHtml(String(r.sale_year || "-")) + ' Â· ' + escapeHtml(String(r.property_type || "-")) +
        '</span><strong>' +
        (r.price_paid_gbp ? ('GBP ' + formatNumber(Number(r.price_paid_gbp), 0)) : '-') +
        ' Â· ' + (r.building_area_m2 ? (formatNumber(Number(r.building_area_m2), 0) + ' mÂ²') : '-') +
        ' Â· ' + (r.price_per_m2_gbp ? ('GBP ' + formatNumber(Number(r.price_per_m2_gbp), 0) + '/mÂ²') : '-') +
        '</strong></div>';
    }).join("");

    return '<div class="workspace-section verified-sales-history-card">' +
      '<h3 class="workspace-section-title">Verified parcel sale history</h3>' +
      '<div class="metric-grid">' +
      '<div class="metric-card"><div class="metric-card-label">Sale records</div><div class="metric-card-value">' + formatNumber(Number(p.sales_history_count || 0), 0) + '</div></div>' +
      '<div class="metric-card"><div class="metric-card-label">Latest sale year</div><div class="metric-card-value">' + escapeHtml(String(p.latest_sale_year || "-")) + '</div></div>' +
      '<div class="metric-card"><div class="metric-card-label">Sale price</div><div class="metric-card-value">' + (p.latest_sale_price_gbp ? ('GBP ' + formatNumber(Number(p.latest_sale_price_gbp), 0)) : '-') + '</div></div>' +
      '<div class="metric-card"><div class="metric-card-label">Sale area</div><div class="metric-card-value">' + (p.latest_sale_area_m2 ? (formatNumber(Number(p.latest_sale_area_m2), 0) + ' mÂ²') : '-') + '</div></div>' +
      '<div class="metric-card"><div class="metric-card-label">Price per mÂ²</div><div class="metric-card-value">' + (p.latest_sale_price_per_m2_gbp ? ('GBP ' + formatNumber(Number(p.latest_sale_price_per_m2_gbp), 0)) : '-') + '</div></div>' +
      '<div class="metric-card"><div class="metric-card-label">Property type</div><div class="metric-card-value">' + escapeHtml(String(p.latest_sale_property_type || "-")) + '</div></div>' +
      '</div><div class="workspace-stack">' + (rows || '<div class="workspace-note">No sale record rows available.</div>') + '</div>' +
      '<div class="workspace-note">Official verified sale history only. Populated by HMLR PPD â†’ AddressBase UPRN â†’ Title_No â†’ NPS polygon â†’ parcel chain.</div>' +
      '</div>';
  }

  function renderCompactLandIntelligenceCard(parcelRef) {
    if (!landIntelligenceApiBaseUrl) {
      return `
        <div class="workspace-section">
          <h3 class="workspace-section-title">Kaynak Sinyalleri</h3>
          <div class="workspace-note">Land Intelligence API bagli degil.</div>
        </div>
      `;
    }

    const state = landIntelligenceCache.get(parcelRef) || createLandIntelligenceState(parcelRef);
    const filteredView = buildFilteredLandIntelligenceView(state);
    if (state.loading) {
      return `
        <div class="workspace-section">
          <h3 class="workspace-section-title">Kaynak Sinyalleri</h3>
          <div class="workspace-note">Official sale, brownfield, listing ve history sinyalleri bu parsel icin yukleniyor...</div>
        </div>
      `;
    }
    if (state.error) {
      return `
        <div class="workspace-section">
          <h3 class="workspace-section-title">Kaynak Sinyalleri</h3>
          <div class="workspace-note">${state.error}</div>
        </div>
      `;
    }
    if (!state.hasFetched) {
      return `
        <div class="workspace-section">
          <h3 class="workspace-section-title">Kaynak Sinyalleri</h3>
          <div class="workspace-note">Bu parsel icin source sinyali hazirlaniyor.</div>
        </div>
      `;
    }
    if (!state.parcelMatch || !state.signals) {
      return `
        <div class="workspace-section">
          <h3 class="workspace-section-title">Kaynak Sinyalleri</h3>
          <div class="workspace-note">Bu parsel icin parcel-centric source eslesmesi bulunamadi.</div>
        </div>
      `;
    }

    const warnings = [...(state.parcelDetail?.warnings || []), ...(state.signals.warnings || [])]
      .slice(0, 3)
      .map((item) => `<div class="workspace-row"><span>Uyari</span><strong>${item.message}</strong></div>`)
      .join("");
    const sourceLinks = filteredView.filteredSources
      .slice(0, 4)
      .map((source) => {
        const label = getLandSourceDisplayName(source.source_name);
        const link = resolveLandSourceLink(source);
        const status = getLandSourceStatus(source);
        return `<div class="workspace-row"><span>${label}</span><strong>${status || "-"} Ã‚Â· ${buildExternalSaleLink(link.url, link.label)}</strong></div>`;
      })
      .join("");
    const proxyNotice = state.matchMode === "nearest_bbox"
      ? `<div class="workspace-note">Bu PMTiles parseli backend parcel tablosunda birebir bulunamadi; en yakin parcel ile Plan C context ve skorlama gosteriliyor (~${formatNumber(state.matchDistanceM || 0, 0)} m).</div>`
      : "";

    return `
      <div class="workspace-section">
        <h3 class="workspace-section-title">Kaynak Sinyalleri</h3>
        ${proxyNotice}
        ${filteredView.filterNotice ? `<div class="workspace-note">${filteredView.filterNotice}</div>` : getLandFilterSummaryHtml()}
        <div class="metric-grid">
          <div class="metric-card"><div class="metric-card-label">Supabase KaydÃ„Â±</div><div class="metric-card-value">${filteredView.managedSources.length ? "Var" : "Yok"}</div></div>
          <div class="metric-card"><div class="metric-card-label">Official Sale</div><div class="metric-card-value">${filteredView.officialSaleSources.length ? "Var" : "Yok"}</div></div>
          <div class="metric-card"><div class="metric-card-label">Brownfield</div><div class="metric-card-value">${filteredView.brownfieldSources.length ? "Var" : "Yok"}</div></div>
          <div class="metric-card"><div class="metric-card-label">Portal Listing</div><div class="metric-card-value">${filteredView.marketSources.length ? "Var" : "Yok"}</div></div>
          <div class="metric-card"><div class="metric-card-label">Confidence</div><div class="metric-card-value">${filteredView.confidenceScore !== null ? formatNumber(filteredView.confidenceScore, 1) : "-"}</div></div>
        </div>
        <div class="workspace-note">Son kaynak gÃƒÂ¼ncellemesi: ${formatLandIntelligenceDate(filteredView.latestUpdatedAt || state.signals.latest_source_updated_at)}</div>
        ${warnings ? `<div class="workspace-stack">${warnings}</div>` : '<div class="workspace-note">Bu parsel icin ekstra warning yok.</div>'}
        <details class="workspace-section workspace-details">
          <summary class="workspace-details-summary">Kaynak Linkleri ve History Ãƒâ€“zeti</summary>
          <div class="workspace-details-body workspace-stack">
            ${sourceLinks || '<div class="workspace-note">Aktif filtreyle eÃ…Å¸leÃ…Å¸en kaynak linki bulunamadi.</div>'}
            <div class="workspace-row"><span>Price Paid History</span><strong>${(state.history || []).length} kayit</strong></div>
            <div class="workspace-row"><span>Official Status</span><strong>${filteredView.officialStatus || "-"}</strong></div>
          </div>
        </details>
      </div>
    `;
  }

  async function loadLandSourceStatuses() {
    if (!landIntelligenceApiBaseUrl) {
      landSourceStatuses = [];
      updateLandSourceStatusPanel();
      return;
    }
    const payload = await fetchJsonWithTimeout(`${landIntelligenceApiBaseUrl}/sources/status`, {
      label: "Kaynak durumlari",
      fallback: [],
    });
    landSourceStatuses = Array.isArray(payload.data) ? payload.data : [];
    updateLandSourceStatusPanel();
  }

  function getLandOverlayBboxString(decimals = 5) {
    if (!map) return null;
    const bounds = map.getBounds();
    const precision = Math.min(6, Math.max(2, Number(decimals) || 5));
    return [
      bounds.getWest().toFixed(precision),
      bounds.getSouth().toFixed(precision),
      bounds.getEast().toFixed(precision),
      bounds.getNorth().toFixed(precision),
    ].join(",");
  }

  function getRegionBboxString(region) {
    if (!region?.bbox || region.bbox.length !== 4) return null;
    return region.bbox.map((value) => Number(value).toFixed(5)).join(",");
  }

  function getUnionRegionBboxString() {
    if (!Array.isArray(config?.regions) || !config.regions.length) return null;
    let west = Number.POSITIVE_INFINITY;
    let south = Number.POSITIVE_INFINITY;
    let east = Number.NEGATIVE_INFINITY;
    let north = Number.NEGATIVE_INFINITY;
    config.regions.forEach((region) => {
      if (!Array.isArray(region?.bbox) || region.bbox.length !== 4) return;
      west = Math.min(west, Number(region.bbox[0]));
      south = Math.min(south, Number(region.bbox[1]));
      east = Math.max(east, Number(region.bbox[2]));
      north = Math.max(north, Number(region.bbox[3]));
    });
    if (![west, south, east, north].every((value) => Number.isFinite(value))) {
      return null;
    }
    return [west, south, east, north].map((value) => Number(value).toFixed(5)).join(",");
  }

  function getLandOverlayQueryContext() {
    if (!map) {
      return { bbox: null, cacheBbox: null, mode: "none" };
    }
    const bbox = getLandOverlayBboxString(5) || getUnionRegionBboxString();
    const cacheBbox = quantizeBboxString(bbox, LAND_OVERLAY_BBOX_DECIMALS);
    return {
      bbox,
      cacheBbox,
      mode: "view",
    };
  }

  function doesFeatureIntersectMapBounds(feature, bounds = null) {
    if (!map || !feature?.geometry) return false;
    const mapBounds = bounds || map.getBounds();
    if (!mapBounds) return false;
    const featureBounds = geometryBounds(feature.geometry);
    if (!featureBounds) return false;
    return !(
      featureBounds.maxLng < mapBounds.getWest() ||
      featureBounds.minLng > mapBounds.getEast() ||
      featureBounds.maxLat < mapBounds.getSouth() ||
      featureBounds.minLat > mapBounds.getNorth()
    );
  }

  function getVisibleFeatureCount(features = []) {
    if (!map || !Array.isArray(features) || !features.length) return 0;
    const mapBounds = map.getBounds();
    return features.reduce((count, feature) => count + (doesFeatureIntersectMapBounds(feature, mapBounds) ? 1 : 0), 0);
  }

  function updateGuidanceStatus() {
    if (!map) return;
    const center = map.getCenter();
    const zoom = map.getZoom();
    const coverageState = getCoverageState(center);
    let nextKey = "ok";
    let message = "";
    let sticky = false;
    if (!coverageState.isWithinSupportedArea) {
      nextKey = `outside:${coverageState.nearestRegion ? coverageState.nearestRegion.slug : "none"}`;
      message = config.coverageWarning || "Bu demo su an England parcel kapsami icin optimize edildi. Scotland tarafinda parseller eksik veya kesik gorunebilir.";
      sticky = true;
    } else if (zoom < config.parcelMinZoom) {
      nextKey = `zoom:${config.parcelMinZoom}`;
      message = `Parselleri guvenilir bicimde gormek icin en az ${config.parcelMinZoom}+ zoom seviyesine yakinlasin.`;
    }

    if (nextKey === lastGuidanceKey) {
      return;
    }
    lastGuidanceKey = nextKey;
    if (!message) {
      statusEl.classList.add("hidden");
      return;
    }
    showStatus(message, sticky);
  }

  function updateCityInfo(city) {
    if (!cityInfoEl) return;
    if (!city) {
      setSanitizedText(cityInfoEl, "Edinburgh ve Dundee gibi Scotland sehirleri icin alias/QA notlari burada gosterilir.");
      return;
    }
    const sourceText = Array.isArray(city.source_authorities) && city.source_authorities.length
      ? ` Kaynak: ${city.source_authorities.join(", ")}.`
      : "";
    const qa = city.qa_result;
    const statusText = city.status.includes("qa_")
      ? " Alias QA tamamlandi."
      : city.status === "needs_alias_qa"
      ? " Alias/QA gerekiyor."
      : " Dogrudan kaynak eslesmesi var.";
    const landingText = city.landing_reason
      ? ` Inis noktasi: ${
          city.landing_reason === "inside_parcel"
            ? "dogrudan parcel ici"
            : city.landing_reason === "snapped_city_focus"
            ? "merkeze en yakin parcel ici"
            : "en yakin parcel"
        }.`
      : "";
    const qaText = qa
      ? ` QA: ${qa.qa_status}. Onerilen kodlar: ${(qa.recommended_codes || []).join(", ") || "-"}.`
      : "";
    setSanitizedText(cityInfoEl, `${city.city}.${statusText}${sourceText}${qaText}${landingText} ${city.note || ""}`.trim());
  }

  async function focusCity(city) {
    if (!city) return;
    updateCityInfo(city);
    const region = regionMap.get(city.region_slug);
    if (region) {
      await switchRegion(region, "manual");
    }
    if (citySelectEl) {
      citySelectEl.value = city.city;
    }
    map.easeTo({ center: [city.lng, city.lat], zoom: city.zoom || 14.8 });
    if (city.status === "needs_alias_qa") {
      showStatus(`${city.city} icin parcel coverage source alias uzerinden dogrulaniyor. ${city.note || ""}`, true);
    } else if (city.status === "qa_snapped_hit") {
      showStatus(`${city.city} icin merkeze en yakin parcel ici odaga gidildi.`, true);
    } else if (city.status === "qa_nearby_only") {
      showStatus(`${city.city} icin en yakin parcel odaÃ„Å¸Ã„Â±na gidildi. Merkez nokta parcel disinda kalabiliyor.`, true);
    } else {
      showStatus(`${city.city} gorunumune gidildi.`);
    }
  }

  function formatNumber(value, digits = 0) {
    return new Intl.NumberFormat("tr-TR", {
      minimumFractionDigits: digits,
      maximumFractionDigits: digits,
    }).format(Number.isFinite(value) ? value : 0);
  }

  function formatMoney(value) {
    return `${formatNumber(value, 0)} TRY`;
  }

  function formatSalePrice(value) {
    const numeric = Number(value);
    if (!Number.isFinite(numeric) || numeric <= 0) return "Fiyat bilgisi yok";
    return new Intl.NumberFormat("en-GB", {
      style: "currency",
      currency: "GBP",
      maximumFractionDigits: 0,
    }).format(numeric);
  }

  function formatGbpPerM2(value) {
    const numeric = Number(value);
    if (!Number.isFinite(numeric) || numeric <= 0) return "-";
    return `${new Intl.NumberFormat("en-GB", {
      style: "currency",
      currency: "GBP",
      maximumFractionDigits: 0,
    }).format(numeric)} / m2`;
  }

  function isSalesOnlyModeActive() {
    return Boolean(currentHistoricSalesVisible);
  }

  function formatHistoryPropertyType(value) {
    const raw = String(value || "").trim();
    if (!raw) return "-";
    const upper = raw.toUpperCase();
    if (upper === "D") return "MÃ¼stakil Konut (Detached)";
    if (upper === "S") return "YarÄ± MÃ¼stakil Konut (Semi-Detached)";
    if (upper === "T") return "SÄ±ra Ev (Terraced)";
    if (upper === "F") return "Daire / Apartman (Flat)";
    if (upper === "O") return "DiÄŸer (Other)";
    return raw;
  }

  function classifyHistoryBuildingType(value) {
    const normalized = String(value || "").trim().toLowerCase();
    if (!normalized) return "Belirsiz";
    if (["d", "s", "t", "f", "o"].includes(normalized)) {
      const coded = {
        d: "Konut / MÃ¼stakil",
        s: "Konut / YarÄ± MÃ¼stakil",
        t: "Konut / SÄ±ra Ev",
        f: "Konut / Apartman-Daire",
        o: "DiÄŸer YapÄ±",
      };
      return coded[normalized] || "DiÄŸer YapÄ±";
    }
    if (/(industrial|factory|warehouse|logistics|depo|sanayi)/i.test(normalized)) return "Sanayi BinasÄ±";
    if (/(retail|shop|store|market|perakende)/i.test(normalized)) return "Perakende BinasÄ±";
    if (/(office|ofis)/i.test(normalized)) return "Ofis BinasÄ±";
    if (/(flat|apartment|apartman|maisonette)/i.test(normalized)) return "Apartman / Daire";
    if (/(detached|house|villa|mustakil)/i.test(normalized)) return "MÃ¼stakil Konut";
    if (/(residential|konut|dwelling)/i.test(normalized)) return "Konut";
    return "DiÄŸer YapÄ±";
  }

  function formatMarketPolygonSourceLabel(value) {
    const normalized = String(value || "").trim().toLowerCase();
    if (normalized === "original_site_polygon") return "Orijinal site poligonu";
    if (normalized === "feed_polygon") return "Feed poligonu";
    if (normalized === "feed_bbox_polygon") return "Feed dikdortgen geometri (bbox benzeri)";
    if (normalized === "derived_parcel_geometry") return "Turetilmis (parcel eslesmesi)";
    if (normalized === "synthetic_geometry") return "Uydurma / sentetik";
    return "Belirsiz";
  }

  function formatMarketOriginalSiteStatusLabel(value) {
    const normalized = String(value || "").trim().toLowerCase();
    if (!normalized) return "Bilinmiyor";
    if (normalized === "verified_original_site") return "Orijinal site dogrulandi";
    if (normalized === "site_verified_original") return "Orijinal site dogrulandi";
    if (normalized === "site_unverified_pipeline_verified") return "Pipeline dogrulu, site birebir dogrulama bekliyor";
    if (normalized === "unknown_not_verified") return "Unknown / site birebir dogrulanmadi";
    if (normalized === "feed_unverified") return "Feed kaynakli, site dogrulanmadi";
    if (normalized === "derived" || normalized === "derived_from_parcel_match") return "Turetilmis ve isaretlenmis";
    if (normalized === "synthetic_unverified" || normalized === "irregular" || normalized === "duzensiz" || normalized === "dÃ¼zensiz") return "Duzensiz/uydurma - gercek poligon degil";
    return value;
  }

  function normalizeMarketPolygonStatus(value) {
    const normalized = String(value || "").trim().toLowerCase();
    if (!normalized) return "unknown_not_verified";
    if (["original_site", "verified_original_site", "site_verified_original"].includes(normalized)) {
      return "verified_original_site";
    }
    if (["derived", "derived_parcel", "derived_location", "derived_from_parcel_match", "turetilmis", "tÃ¼retilmiÅŸ"].includes(normalized)) {
      return "derived";
    }
    if (["synthetic", "synthetic_unverified", "fabricated", "irregular", "duzensiz", "dÃ¼zensiz", "uydurma"].includes(normalized)) {
      return "synthetic_unverified";
    }
    if (["feed_unverified", "unknown", "unknown_not_verified"].includes(normalized)) {
      return "unknown_not_verified";
    }
    return normalized;
  }

  function isTrustedMarketPolygonStatus(value) {
    return ["verified_original_site", "derived"].includes(normalizeMarketPolygonStatus(value));
  }

  function canDisplayMarketListingPolygon(feature, displayPolygonSource, sourceStatus) {
    const geometryType = feature?.geometry?.type;
    if (!["Polygon", "MultiPolygon"].includes(geometryType)) return false;
    const normalizedStatus = normalizeMarketPolygonStatus(sourceStatus);
    const source = String(displayPolygonSource || "").trim().toLowerCase();
    const qualityClass = feature?.properties?.geometry_quality_class || classifyMarketListingGeometryQuality(feature).geometry_quality_class;
    const isRectangularFeed = qualityClass === "rectangular_feed_bbox_like" || source === "feed_bbox_polygon";

    if (isRectangularFeed && !isTrustedMarketPolygonStatus(normalizedStatus)) {
      return false;
    }
    if (isTrustedMarketPolygonStatus(normalizedStatus)) {
      return true;
    }
    return source === "derived_parcel_geometry" || source === "original_site_polygon";
  }

  function formatMarketPolygonDisplayState(value) {
    return value ? "Haritada poligon olarak gosteriliyor" : "Poligon gizli: gercek/turetilmis satis geometri dogrulanmadi";
  }

  function buildExternalSaleLink(url, label = "SatÃ„Â±Ã…Å¸ adresine git") {
    if (!url) return "Link yok";
    return `<a href="${url}" target="_blank" rel="noopener noreferrer">${label}</a>`;
  }

  function getListingFeatureLink(feature) {
    const props = feature?.properties || {};
    return props.external_url || props.listing_url || props.source_url || buildLandIntelligenceSourceDetailUrl(props.source_name, props.listing_id);
  }

  function getListingFeatureLinkLabel(feature) {
    const props = feature?.properties || {};
    if (props.external_label) return props.external_label;
    if (props.source_name === "government_property_finder") return "Government Property ilanina git";
    return "SatÃ„Â±Ã…Å¸ adresine git";
  }

  function resolveSaleRecordLink(record, sources = []) {
    if (!record) {
      return { url: null, label: "SatÃ„Â±Ã…Å¸ adresine git" };
    }
    if (record.external_url) {
      return { url: record.external_url, label: record.external_label || "SatÃ„Â±Ã…Å¸ adresine git" };
    }
    const matchingSource = (sources || []).find(
      (source) => source?.source_name === record.source_name && source?.source_record_id === record.source_record_id
    );
    const detail = matchingSource?.detail || null;
    return {
      url: detail?.external_url || detail?.listing_url || detail?.source_url || record.external_url || record.listing_url || record.source_url || buildLandIntelligenceSourceDetailUrl(record.source_name, record.source_record_id),
      label: detail?.external_label || record.external_label || "SatÃ„Â±Ã…Å¸ adresine git",
    };
  }

  function resolveLandSourceLink(source) {
    const detail = source?.detail || null;
    return {
      url: detail?.external_url || detail?.listing_url || detail?.source_url || source?.source_url || buildLandIntelligenceSourceDetailUrl(source?.source_name, source?.source_record_id),
      label: detail?.external_label || "KaynaÃ„Å¸a git",
    };
  }

  function getSaleRecordActionability(record, sources = []) {
    if (!record) {
      return [-1, -1, -1, 0, 0];
    }
    const link = resolveSaleRecordLink(record, sources);
    const priceTruth = getSalePriceTruth(record, sources);
    const linkTruth = getSaleLinkTruth(record, sources);
    const updatedAt = record?.source_updated_at ? new Date(record.source_updated_at).getTime() : 0;
    return [
      getActionableSaleSourcePriority(record),
      priceTruth?.isReal === true && hasSalePrice(record) ? 1 : 0,
      linkTruth?.isReal === true && Boolean(link?.url) ? 1 : 0,
      link?.url ? 1 : 0,
      updatedAt,
      Number(record?.confidence_score || 0),
    ];
  }

  function compareRankTuple(left, right) {
    const length = Math.max(left?.length || 0, right?.length || 0);
    for (let index = 0; index < length; index += 1) {
      const delta = Number(left?.[index] || 0) - Number(right?.[index] || 0);
      if (delta !== 0) return delta;
    }
    return 0;
  }

  function pickTopActionableSaleRecord(records, sources = []) {
    let bestRecord = null;
    let bestRank = null;
    (records || []).forEach((record) => {
      const rank = getSaleRecordActionability(record, sources);
      if (!bestRank || compareRankTuple(rank, bestRank) > 0) {
        bestRank = rank;
        bestRecord = record;
      }
    });
    return bestRecord;
  }

  function getSaleSummaryActionableRecord(saleSummary) {
    if (!saleSummary || typeof saleSummary !== "object") return null;
    return saleSummary.top_actionable_listing || saleSummary.top_market_listing || saleSummary.top_official_listing || null;
  }

  function formatDistanceMeters(value) {
    if (!Number.isFinite(value) || value <= 0) return "Ã¢â‚¬â€";
    if (value >= 1000) {
      return `${formatNumber(value / 1000, 2)} km`;
    }
    return `${formatNumber(value, 0)} m`;
  }

  function lonLatToMeters(lng, lat) {
    const x = (lng * 20037508.34) / 180;
    let y = Math.log(Math.tan(((90 + lat) * Math.PI) / 360)) / (Math.PI / 180);
    y = (y * 20037508.34) / 180;
    return [x, y];
  }

  function haversineDistanceMeters(a, b) {
    const toRad = (deg) => (deg * Math.PI) / 180;
    const earth = 6371000;
    const dLat = toRad(b.lat - a.lat);
    const dLng = toRad(b.lng - a.lng);
    const s1 = Math.sin(dLat / 2) ** 2;
    const s2 = Math.cos(toRad(a.lat)) * Math.cos(toRad(b.lat)) * Math.sin(dLng / 2) ** 2;
    return 2 * earth * Math.asin(Math.sqrt(s1 + s2));
  }

  function mapFacilityCategoryToInsightUnitKey(categoryCode) {
    switch (String(categoryCode || "").toLowerCase()) {
      case "education":
        return "okul";
      case "transport":
        return "metro";
      case "retail":
      case "commercial":
        return "avm";
      case "health":
        return "hastane";
      default:
        return null;
    }
  }

  function mapLineFeatureToInsightFeature(feature) {
    const coords = feature?.geometry?.coordinates;
    if (!Array.isArray(coords) || coords.length < 2) return null;
    if (String(feature?.properties?.line_kind || "").toLowerCase() !== "rail") return null;
    return {
      type: "Feature",
      geometry: {
        type: "Point",
        coordinates: [Number(coords[0]), Number(coords[1])],
      },
      properties: {
        unit_key: "metro",
        category: "metro",
        name: feature?.properties?.name || feature?.properties?.label || "Rail",
        label: "Metro (Ulasim)",
      },
    };
  }

  function mapFacilityFeatureToInsightFeature(feature) {
    const coords = feature?.geometry?.coordinates;
    if (!Array.isArray(coords) || coords.length < 2) return null;
    const unitKey = mapFacilityCategoryToInsightUnitKey(feature?.properties?.category_code);
    if (!unitKey) return null;
    return {
      type: "Feature",
      geometry: {
        type: "Point",
        coordinates: [Number(coords[0]), Number(coords[1])],
      },
      properties: {
        unit_key: unitKey,
        category: unitKey,
        name:
          feature?.properties?.name ||
          feature?.properties?.subtype ||
          getFacilityCategoryLabel(feature?.properties?.category_code),
        label: getFacilityCategoryLabel(feature?.properties?.category_code),
      },
    };
  }

  function polygonRingArea(coords) {
    let area = 0;
    for (let i = 0; i < coords.length - 1; i += 1) {
      const [x1, y1] = lonLatToMeters(coords[i][0], coords[i][1]);
      const [x2, y2] = lonLatToMeters(coords[i + 1][0], coords[i + 1][1]);
      area += x1 * y2 - x2 * y1;
    }
    return Math.abs(area) / 2;
  }

  function geometryAreaM2(geometry) {
    if (!geometry) return 0;
    if (geometry.type === "Polygon") {
      return (geometry.coordinates || []).reduce((sum, ring, idx) => sum + (idx === 0 ? polygonRingArea(ring) : -polygonRingArea(ring)), 0);
    }
    if (geometry.type === "MultiPolygon") {
      return (geometry.coordinates || []).reduce(
        (sum, polygon) => sum + polygon.reduce((polySum, ring, idx) => polySum + (idx === 0 ? polygonRingArea(ring) : -polygonRingArea(ring)), 0),
        0
      );
    }
    return 0;
  }

  function ringPerimeterM(coords) {
    let total = 0;
    for (let i = 0; i < coords.length - 1; i += 1) {
      total += haversineDistanceMeters(
        { lng: coords[i][0], lat: coords[i][1] },
        { lng: coords[i + 1][0], lat: coords[i + 1][1] }
      );
    }
    return total;
  }

  function geometryPerimeterM(geometry) {
    if (!geometry) return 0;
    if (geometry.type === "Polygon") {
      return (geometry.coordinates || []).reduce((sum, ring) => sum + ringPerimeterM(ring), 0);
    }
    if (geometry.type === "MultiPolygon") {
      return (geometry.coordinates || []).reduce(
        (sum, polygon) => sum + polygon.reduce((polySum, ring) => polySum + ringPerimeterM(ring), 0),
        0
      );
    }
    return 0;
  }

  function geometryBounds(geometry) {
    let minLng = Infinity;
    let minLat = Infinity;
    let maxLng = -Infinity;
    let maxLat = -Infinity;
    function walk(coords) {
      if (!Array.isArray(coords)) return;
      if (typeof coords[0] === "number" && typeof coords[1] === "number") {
        minLng = Math.min(minLng, coords[0]);
        minLat = Math.min(minLat, coords[1]);
        maxLng = Math.max(maxLng, coords[0]);
        maxLat = Math.max(maxLat, coords[1]);
        return;
      }
      coords.forEach(walk);
    }
    walk(geometry?.coordinates);
    if (!Number.isFinite(minLng)) return null;
    return { minLng, minLat, maxLng, maxLat };
  }

  function geometryCenterLngLat(geometry) {
    const bounds = geometryBounds(geometry);
    if (!bounds) return null;
    return {
      lng: (bounds.minLng + bounds.maxLng) / 2,
      lat: (bounds.minLat + bounds.maxLat) / 2,
    };
  }

  function ensureClosedRing(ring) {
    if (!Array.isArray(ring) || ring.length < 3) return [];
    const first = ring[0];
    const last = ring[ring.length - 1];
    if (!Array.isArray(first) || !Array.isArray(last)) return [];
    if (first[0] === last[0] && first[1] === last[1]) {
      return ring;
    }
    return [...ring, first];
  }

  function getPrimaryPolygonRing(geometry) {
    if (!geometry) return null;
    const sanitizeRing = (ring) => {
      if (!Array.isArray(ring)) return [];
      return ring
        .map((coord) => [Number(coord?.[0]), Number(coord?.[1])])
        .filter((coord) => Number.isFinite(coord[0]) && Number.isFinite(coord[1]));
    };
    if (geometry.type === "Polygon") {
      const ring = sanitizeRing(geometry.coordinates?.[0] || []);
      return ring.length >= 3 ? ensureClosedRing(ring) : null;
    }
    if (geometry.type === "MultiPolygon") {
      let bestRing = null;
      let bestArea = 0;
      (geometry.coordinates || []).forEach((polygon) => {
        const ring = sanitizeRing(polygon?.[0] || []);
        if (ring.length < 3) return;
        const closed = ensureClosedRing(ring);
        const area = polygonRingArea(closed);
        if (area > bestArea) {
          bestArea = area;
          bestRing = closed;
        }
      });
      return bestRing;
    }
    return null;
  }

  function getRingEdgeLengthsMeters(ring) {
    const closed = ensureClosedRing(ring || []);
    if (closed.length < 2) return [];
    const lengths = [];
    for (let i = 0; i < closed.length - 1; i += 1) {
      lengths.push(
        haversineDistanceMeters(
          { lng: closed[i][0], lat: closed[i][1] },
          { lng: closed[i + 1][0], lat: closed[i + 1][1] }
        )
      );
    }
    return lengths;
  }

  function isLikelyAxisAlignedRectangleRing(ring) {
    const closed = ensureClosedRing(ring || []);
    if (closed.length !== 5) return false;
    const uniqueLng = Array.from(new Set(closed.map((coord) => Number(coord[0]).toFixed(9))));
    const uniqueLat = Array.from(new Set(closed.map((coord) => Number(coord[1]).toFixed(9))));
    return uniqueLng.length === 2 && uniqueLat.length === 2;
  }

  function classifyMarketListingGeometryQuality(feature) {
    const ring = getPrimaryPolygonRing(feature?.geometry);
    const isRectangular = isLikelyAxisAlignedRectangleRing(ring);
    if (isRectangular) {
      return {
        geometry_quality_class: "rectangular_feed_bbox_like",
        geometry_quality_label: "Dikdortgen feed geometri (gercek parsel dogrulanmadi)",
      };
    }
    return {
      geometry_quality_class: "non_rectangular_feed_polygon",
      geometry_quality_label: "Feed poligonu (sekil korunuyor)",
    };
  }

  function buildParcelGeometryPreviewSvg(feature) {
    const ring = getPrimaryPolygonRing(feature?.geometry);
    if (!ring || ring.length < 4) return "";
    const lngs = ring.map((coord) => coord[0]);
    const lats = ring.map((coord) => coord[1]);
    const minLng = Math.min(...lngs);
    const maxLng = Math.max(...lngs);
    const minLat = Math.min(...lats);
    const maxLat = Math.max(...lats);
    const spanLng = Math.max(maxLng - minLng, 1e-9);
    const spanLat = Math.max(maxLat - minLat, 1e-9);
    const size = 128;
    const pad = 10;
    const drawSpan = size - pad * 2;
    const scale = Math.min(drawSpan / spanLng, drawSpan / spanLat);
    const project = (coord) => {
      const x = pad + (coord[0] - minLng) * scale;
      const y = size - (pad + (coord[1] - minLat) * scale);
      return [x, y];
    };
    const projected = ring.map(project);
    const pathData = projected
      .map((coord, index) => `${index === 0 ? "M" : "L"}${coord[0].toFixed(2)} ${coord[1].toFixed(2)}`)
      .join(" ");
    const center = geometryCenterLngLat(feature?.geometry);
    let centerSvg = "";
    if (center) {
      const [cx, cy] = project([center.lng, center.lat]);
      centerSvg = `<circle cx="${cx.toFixed(2)}" cy="${cy.toFixed(2)}" r="2.4" fill="#f6fbff" />`;
    }
    return `
      <svg viewBox="0 0 ${size} ${size}" role="img" aria-label="Parsel geometrisi onizleme">
        <rect x="0" y="0" width="${size}" height="${size}" rx="14" ry="14" fill="#0b1220"></rect>
        <path d="${pathData} Z" fill="rgba(67, 199, 153, 0.18)" stroke="#5fe3b4" stroke-width="2.2" stroke-linejoin="round"></path>
        ${centerSvg}
      </svg>
    `;
  }

  function renderParcelGeometryPreviewSection(feature) {
    if (!feature?.geometry) return "";
    const props = feature?.properties || {};
    const areaM2 = getParcelAreaM2(feature);
    const perimeterM = getParcelPerimeterM(feature);
    const ring = getPrimaryPolygonRing(feature?.geometry);
    const edgeLengths = getRingEdgeLengthsMeters(ring).slice(0, 4);
    const edgeSummary = edgeLengths.length
      ? edgeLengths.map((value) => formatDistanceMeters(value)).join(", ")
      : "-";
    const displayPolygonSource = props.display_polygon_source || (props.market_listing_source_geometry ? "feed_polygon" : null);
    const sourceStatus = props.source_polygon_original_site_status || null;
    const provenanceNote = props.polygon_provenance_note || null;
    const sourceLabel = displayPolygonSource ? formatMarketPolygonSourceLabel(displayPolygonSource) : "Parsel geometrisi";
    const statusLabel = sourceStatus ? formatMarketOriginalSiteStatusLabel(sourceStatus) : "-";
    return `
      <details class="workspace-section workspace-details" open>
        <summary class="workspace-details-summary">Parsel Geometrisi</summary>
        <div class="workspace-details-body">
          <div class="geometry-preview-wrap">
            <div class="geometry-preview-visual">${buildParcelGeometryPreviewSvg(feature)}</div>
            <div class="workspace-stack">
              <div class="workspace-row"><span>Geometri tipi</span><strong>${feature?.geometry?.type || "-"}</strong></div>
              <div class="workspace-row"><span>Alan</span><strong>${areaM2 > 0 ? `${formatNumber(areaM2, 0)} m2` : "-"}</strong></div>
              <div class="workspace-row"><span>Cevre</span><strong>${perimeterM > 0 ? formatDistanceMeters(perimeterM) : "-"}</strong></div>
              <div class="workspace-row"><span>Kenar ozeti</span><strong>${edgeSummary}</strong></div>
              <div class="workspace-row"><span>Geometri kaynagi</span><strong>${sourceLabel}</strong></div>
              <div class="workspace-row"><span>Orijinal site durumu</span><strong>${statusLabel}</strong></div>
              ${props.market_polygon_displayable !== undefined ? `<div class="workspace-row"><span>Poligon gosterimi</span><strong>${formatMarketPolygonDisplayState(props.market_polygon_displayable !== false)}</strong></div>` : ""}
              <div class="workspace-row"><span>Kaynak notu</span><strong>${provenanceNote || "-"}</strong></div>
            </div>
          </div>
        </div>
      </details>
    `;
  }

  function getParcelRef(feature) {
    const props = feature?.properties || {};
    return (
      props.matched_parcel_ref ||
      props.matched_inspire_id ||
      props.inspire_id ||
      props.INSPIRE_ID ||
      props.listing_id ||
      props.source_record_id ||
      props.provider_listing_id ||
      props.parsel_ref ||
      props.NATIONALCADASTRALREFERENCE ||
      props.parcel_ref ||
      props.id ||
      props.PARCEL_ID ||
      "Parsel"
    );
  }

  function getParcelAreaM2(feature) {
    const props = feature?.properties || {};
    const directKeys = ["area_m2", "AREA_M2", "shape_area", "Shape_Area", "area"];
    for (const key of directKeys) {
      const raw = Number(props[key]);
      if (Number.isFinite(raw) && raw > 0) return raw;
    }
    const computed = geometryAreaM2(feature?.geometry);
    return Number.isFinite(computed) && computed > 0 ? computed : 0;
  }

  function getParcelPerimeterM(feature) {
    const props = feature?.properties || {};
    for (const key of ["cevre_m", "perimeter_m", "perimeter", "PERIMETER_M"]) {
      const raw = Number(props[key]);
      if (Number.isFinite(raw) && raw > 0) return raw;
    }
    const computed = geometryPerimeterM(feature?.geometry);
    return Number.isFinite(computed) && computed > 0 ? computed : 0;
  }

  function getParcelSlopePct(feature) {
    const props = feature?.properties || {};
    for (const key of ["slope_pct", "SLOPE_PCT", "egim_pct", "egim", "slope"]) {
      const raw = Number(props[key]);
      if (Number.isFinite(raw)) return raw;
    }
    return 1;
  }

  function getParcelEmptyLandSignal(feature) {
    const props = feature?.properties || {};
    for (const key of ["empty_land_signal", "EMPTY_LAND_SIGNAL", "bos_arazi", "bos_arazi_pct"]) {
      const raw = Number(props[key]);
      if (Number.isFinite(raw)) return raw > 1 ? raw / 100 : raw;
    }
    return 0.7;
  }

  function getParcelModelFromFeature(feature) {
    if (!feature) return null;
    const areaM2 = Math.max(0, getParcelAreaM2(feature));
    const landCost = Math.max(1_200_000, areaM2 * 5666.67);
    const perimeterM = getParcelPerimeterM(feature);
    const slopePct = getParcelSlopePct(feature);
    const emptyLandSignal = getParcelEmptyLandSignal(feature);
    const center = geometryCenterLngLat(feature.geometry);
    return {
      ref: getParcelRef(feature),
      areaM2,
      landCost,
      perimeterM,
      slopePct,
      emptyLandSignal,
      center,
      regionLabel: activeRegion ? activeRegion.label : "-",
      regionSlug: activeRegion ? activeRegion.slug : "unknown",
      properties: feature.properties || {},
      feature,
    };
  }

  function getParcelModel() {
    return selectedParcelFeature ? getParcelModelFromFeature(selectedParcelFeature) : null;
  }

  function assumptionsForScenario(base, scenarioName) {
    const map = {
      "Konut ApartmanÃ„Â±": { rev: 1.0, area: 1.0, cost: 1.0, extraMonths: 0 },
      Site: { rev: 1.08, area: 1.05, cost: 1.05, extraMonths: 2 },
      "Karma KullanÃ„Â±m": { rev: 1.05, area: 0.98, cost: 1.0, extraMonths: 0 },
      Ticari: { rev: 0.95, area: 1.0, cost: 1.05, extraMonths: 2 },
      Ofis: { rev: 0.92, area: 1.0, cost: 1.05, extraMonths: 0 },
      Konut: { rev: 0.98, area: 1.0, cost: 1.0, extraMonths: 0 },
      "EndÃƒÂ¼striyel": { rev: 0.88, area: 1.08, cost: 1.08, extraMonths: 2 },
      Prefabrik: { rev: 0.9, area: 0.92, cost: 0.82, extraMonths: 0 },
      "TarÃ„Â±msal": { rev: 0.82, area: 1.05, cost: 0.72, extraMonths: 1 },
    };
    const mod = map[scenarioName] || { rev: 1.0, area: 1.0, cost: 1.0, extraMonths: 0 };
    return {
      constructionCostPerM2: base.constructionCostPerM2 * mod.cost,
      salePricePerM2: base.salePricePerM2 * mod.rev,
      sellableAreaM2: base.sellableAreaM2 * mod.area,
      landCost: base.landCost,
      projectMonths: base.projectMonths + mod.extraMonths,
      unexpectedPct: base.unexpectedPct,
    };
  }

  function generateScenarioModels(parcel) {
    if (!parcel) return [];
    const base = {
      constructionCostPerM2: 15000,
      salePricePerM2: 37000,
      sellableAreaM2: Math.max(1200, parcel.areaM2 * 0.65),
      landCost: parcel.landCost,
      projectMonths: 24,
      unexpectedPct: 0.05,
    };
    return ["Konut ApartmanÃ„Â±", "Site", "Karma KullanÃ„Â±m", "Ticari", "Ofis", "Konut", "EndÃƒÂ¼striyel", "Prefabrik", "TarÃ„Â±msal"].map((name) => {
      const assumptions = assumptionsForScenario(base, name);
      const buildCost = assumptions.constructionCostPerM2 * assumptions.sellableAreaM2;
      const unexpected = buildCost * assumptions.unexpectedPct;
      const totalCost = buildCost + unexpected + assumptions.landCost;
      const revenue = assumptions.salePricePerM2 * assumptions.sellableAreaM2;
      const profit = revenue - totalCost;
      const roiPct = totalCost > 0 ? (profit / totalCost) * 100 : 0;
      const irrPct = totalCost > 0 ? ((revenue / totalCost) ** (12 / assumptions.projectMonths) - 1) * 100 : 0;
      return {
        name,
        ...assumptions,
        buildCost,
        unexpected,
        totalCost,
        revenue,
        profit,
        roiPct,
        irrPct,
      };
    });
  }

  function bestScenario(parcel) {
    const scenarios = generateScenarioModels(parcel);
    return scenarios.sort((a, b) => b.irrPct - a.irrPct)[0] || null;
  }

  function slugify(text) {
    return String(text || "")
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, "-")
      .replace(/^-+|-+$/g, "");
  }

  function listingSites(parcel) {
    const slug = slugify(parcel.ref);
    return [
      {
        site: "ArsaMarket",
        url: `https://www.arsamarket.com/ilan/${slug}`,
        note: "BÃƒÂ¶lgesel arsa portfÃƒÂ¶yleri ve ekspertiz raporu sunar.",
      },
      {
        site: "YatirimEmlak",
        url: `https://www.yatirimemlak.net/arsa/${slug}`,
        note: "YatÃ„Â±rÃ„Â±mcÃ„Â± odaklÃ„Â± listeleme ve finansman danÃ„Â±Ã…Å¸manlÃ„Â±Ã„Å¸Ã„Â± saÃ„Å¸lar.",
      },
      {
        site: "ParselBorsa",
        url: `https://www.parselborsa.com/listing/${slug}`,
        note: "KarÃ…Å¸Ã„Â±laÃ…Å¸tÃ„Â±rmalÃ„Â± emsal analizi ve tapu doÃ„Å¸rulama akÃ„Â±Ã…Å¸Ã„Â± saÃ„Å¸lar.",
      },
      {
        site: "NovaArazi",
        url: `https://www.novaarazi.org/portfoy/${slug}`,
        note: "Mimari ÃƒÂ¶n ÃƒÂ§alÃ„Â±Ã…Å¸ma ve yatÃ„Â±rÃ„Â±m dÃƒÂ¶nÃƒÂ¼Ã…Å¸ simÃƒÂ¼lasyonu sunar.",
      },
    ];
  }

  function contractorContactsForEntry(entry) {
    const typeKey = entry?.scenario?.typeConfig?.key || "karma";
    const contacts = {
      mustakil: {
        buildingType: "MÃƒÂ¼stakil",
        company: "Arda MÃƒÂ¼stakil YapÃ„Â±",
        contact: "Arda YÃ„Â±ldÃ„Â±z",
        phone: "+90 212 555 1122",
        email: "iletisim@ardamustakil.com",
        note: "MÃƒÂ¼stakil konut ve bahÃƒÂ§eli yaÃ…Å¸am projeleri iÃƒÂ§in uygulama ekibi.",
      },
      apartman: {
        buildingType: "Apartman",
        company: "Kent Apartman Proje",
        contact: "Ece Demir",
        phone: "+90 212 555 1184",
        email: "apartman@kentproje.com",
        note: "Ãƒâ€¡ok katlÃ„Â± apartman ve site bloklarÃ„Â±nda tasarÃ„Â±m + yapÃ„Â±m desteÃ„Å¸i.",
      },
      site: {
        buildingType: "Site",
        company: "Toplu Konut GeliÃ…Å¸tirme",
        contact: "Mert AkÃ„Â±n",
        phone: "+90 212 555 1455",
        email: "site@toplukonut.com",
        note: "BÃƒÂ¼yÃƒÂ¼k ÃƒÂ¶lÃƒÂ§ekli toplu konut ve site masterplan ÃƒÂ§ÃƒÂ¶zÃƒÂ¼mÃƒÂ¼ sunar.",
      },
      perakende: {
        buildingType: "Perakende",
        company: "Perakende Construction & Project",
        contact: "Perakende UzmanÃ„Â±",
        phone: "+90 212 555 1943",
        email: "iletisim@perakendeyapi.com",
        note: "Anahtar teslim perakende ve maÃ„Å¸aza kullanÃ„Â±m tiplerinde destek verir.",
      },
      ofis: {
        buildingType: "Ofis",
        company: "WorkHub Office Build",
        contact: "Selin KoÃƒÂ§",
        phone: "+90 212 555 1620",
        email: "office@workhubbuild.com",
        note: "Ofis kampÃƒÂ¼sÃƒÂ¼ ve ticari ofis bloklarÃ„Â± iÃƒÂ§in yÃƒÂ¼klenici aÃ„Å¸Ã„Â± saÃ„Å¸lar.",
      },
      karma: {
        buildingType: "Karma",
        company: "Urban Mixed Use Studio",
        contact: "Can Ergin",
        phone: "+90 212 555 1701",
        email: "mixeduse@urbanstudio.com",
        note: "Karma kullanÃ„Â±m senaryolarÃ„Â±nda fazlama ve uygulama eÃ…Å¸leÃ…Å¸tirmesi yapar.",
      },
      endustriyel: {
        buildingType: "EndÃƒÂ¼striyel",
        company: "EndÃƒÂ¼stri YapÃ„Â± Sistemleri",
        contact: "Burak Tanel",
        phone: "+90 212 555 1880",
        email: "endustri@tesisproje.com",
        note: "Lojistik, depo ve ÃƒÂ¼retim yapÃ„Â±larÃ„Â± iÃƒÂ§in mÃƒÂ¼hendislik desteklidir.",
      },
      prefab: {
        buildingType: "Prefabrik",
        company: "Modul Prefab Systems",
        contact: "Elif Kara",
        phone: "+90 212 555 1322",
        email: "prefab@modulsystems.com",
        note: "HÃ„Â±zlÃ„Â± kurulumlu modÃƒÂ¼ler ve prefabrik yapÃ„Â± ÃƒÂ§ÃƒÂ¶zÃƒÂ¼mleri sunar.",
      },
      tarimsal: {
        buildingType: "TarÃ„Â±msal",
        company: "AgriBuild Projects",
        contact: "Murat Toprak",
        phone: "+90 212 555 1458",
        email: "tarim@agribuild.com",
        note: "TarÃ„Â±msal depolama, sera ve kÃ„Â±rsal yapÃ„Â± projelerinde ÃƒÂ§alÃ„Â±Ã…Å¸Ã„Â±r.",
      },
    };
    const fallback = contacts.karma;
    return contacts[typeKey] || fallback;
  }

  function renderPurchaseChannelsTable(parcel) {
    const rows = listingSites(parcel)
      .map(
        (item) => `
          <tr>
            <td>${item.site}</td>
            <td><a href="${item.url}" target="_blank" rel="noopener noreferrer">${item.url}</a></td>
            <td>${item.note}</td>
          </tr>
        `
      )
      .join("");
    return `
      <div class="settings-table-wrap">
        <table class="settings-table">
          <thead>
            <tr>
              <th>Website</th>
              <th>EriÃ…Å¸im URL</th>
              <th>AÃƒÂ§Ã„Â±klama</th>
            </tr>
          </thead>
          <tbody>${rows}</tbody>
        </table>
      </div>
    `;
  }

  function renderContractorContactsTable(entry) {
    const contact = contractorContactsForEntry(entry);
    return `
      <div class="settings-table-wrap">
        <table class="settings-table">
          <thead>
            <tr>
              <th>YapÃ„Â± TÃƒÂ¼rÃƒÂ¼</th>
              <th>Ã„Â°lgili Senaryo</th>
              <th>Firma</th>
              <th>Yetkili</th>
              <th>Telefon</th>
              <th>E-posta</th>
              <th>Not</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td>${contact.buildingType}</td>
              <td>${entry.scenario.name}</td>
              <td>${contact.company}</td>
              <td>${contact.contact}</td>
              <td>${contact.phone}</td>
              <td>${contact.email}</td>
              <td>${contact.note}</td>
            </tr>
          </tbody>
        </table>
      </div>
    `;
  }

  function renderContactParcelBlocks(compareEntries) {
    return compareEntries
      .map(
        (entry) => {
          const signalState = getLandIntelligenceStateForRef(entry.ref);
          const filteredView = buildFilteredLandIntelligenceView(signalState);
          const signalSummary = signalState.signals
            ? `
              <div class="metric-grid">
                <div class="metric-card"><div class="metric-card-label">Supabase KaydÃ„Â±</div><div class="metric-card-value">${filteredView.managedSources.length ? "Var" : "Yok"}</div></div>
                <div class="metric-card"><div class="metric-card-label">Official Sale</div><div class="metric-card-value">${filteredView.officialSaleSources.length ? "Var" : "Yok"}</div></div>
                <div class="metric-card"><div class="metric-card-label">Brownfield</div><div class="metric-card-value">${filteredView.brownfieldSources.length ? "Var" : "Yok"}</div></div>
                <div class="metric-card"><div class="metric-card-label">Portal Listing</div><div class="metric-card-value">${filteredView.marketSources.length ? "Var" : "Yok"}</div></div>
                <div class="metric-card"><div class="metric-card-label">Confidence</div><div class="metric-card-value">${filteredView.confidenceScore !== null ? formatNumber(filteredView.confidenceScore, 1) : "-"}</div></div>
              </div>
              ${filteredView.topManagedRecord ? `<div class="workspace-note">YÃƒÂ¶netimli kayÃ„Â±t: <strong>${filteredView.topManagedRecord.parcel_name || filteredView.topManagedRecord.label || "-"}</strong> Ã‚Â· ${filteredView.topManagedRecord.listing_status || filteredView.topManagedRecord.status || "-"}</div>` : ""}
            `
            : `<div class="workspace-note">${signalState.loading ? "Kaynak sinyalleri yÃƒÂ¼kleniyor..." : "Kaynak sinyali henÃƒÂ¼z hazÃ„Â±r deÃ„Å¸il."}</div>`;
          return `
            <div class="workspace-section">
              <h3 class="workspace-section-title">Parsel ${entry.ref}</h3>
              <div class="metric-grid">
                <div class="metric-card"><div class="metric-card-label">Parsel ID</div><div class="metric-card-value">${entry.ref}</div></div>
                <div class="metric-card"><div class="metric-card-label">Arsa alanÃ„Â± (mÃ‚Â²)</div><div class="metric-card-value">${formatNumber(entry.areaM2, 0)}</div></div>
                <div class="metric-card"><div class="metric-card-label">Tahmini arsa maliyeti (TRY)</div><div class="metric-card-value">${formatMoney(entry.landCost)}</div></div>
              </div>
              ${signalSummary}
              <div class="workspace-note">Bu parsel aÃ…Å¸aÃ„Å¸Ã„Â±daki kanallarda listelenebilir. Her platform farklÃ„Â± eriÃ…Å¸im ve fiyatlandÃ„Â±rma/finansman akÃ„Â±Ã…Å¸Ã„Â±na sahip olabilir.</div>
              <h4 class="workspace-section-title">SatÃ„Â±n alma kanallarÃ„Â± ve fiyat ÃƒÂ¶zetleri</h4>
              ${renderPurchaseChannelsTable(entry)}
              <h4 class="workspace-section-title">YapÃ„Â± tÃƒÂ¼rÃƒÂ¼ne gÃƒÂ¶re yÃƒÂ¼klenici iletiÃ…Å¸imleri</h4>
              ${renderContractorContactsTable(entry)}
            </div>
          `;
        }
      )
      .join("");
  }

  function buildParcelInsights(parcel) {
    if (!parcel) return { primaryUnits: [], nearbyUnits: [] };
    const cacheKey = [
      activeRegion ? activeRegion.slug : "none",
      parcel.ref,
      Array.isArray(currentPoiData?.points?.features) ? currentPoiData.points.features.length : 0,
      Array.isArray(currentPoiData?.lines?.features) ? currentPoiData.lines.features.length : 0,
      Array.isArray(facilitiesOverlayState?.features) ? facilitiesOverlayState.features.length : 0,
    ].join(":");
    if (parcelInsightCache.has(cacheKey)) {
      return parcelInsightCache.get(cacheKey);
    }
    const pointFeatures = [
      ...(Array.isArray(currentPoiData?.points?.features) ? currentPoiData.points.features : []),
      ...(Array.isArray(currentPoiData?.lines?.features)
        ? currentPoiData.lines.features.map(mapLineFeatureToInsightFeature).filter(Boolean)
        : []),
      ...(Array.isArray(facilitiesOverlayState?.features)
        ? facilitiesOverlayState.features.map(mapFacilityFeatureToInsightFeature).filter(Boolean)
        : []),
    ];
    const primaryKeys = ["okul", "metro", "avm", "hastane"];
    const labelMap = {
      okul: "Okul",
      metro: "Metro",
      avm: "Market",
      hastane: "Hastane",
      otobus: "OtobÃƒÂ¼s",
      polis: "Polis",
      iskele: "Ã„Â°skele",
    };
    const bestByKey = new Map();
    const allNearest = [];
    for (const feature of pointFeatures) {
      const coords = feature?.geometry?.coordinates;
      if (!Array.isArray(coords) || coords.length < 2 || !parcel.center) continue;
      const key = feature?.properties?.unit_key || feature?.properties?.category;
      if (!key) continue;
      const distanceM = haversineDistanceMeters(parcel.center, { lng: coords[0], lat: coords[1] });
      const item = {
        key,
        label: labelMap[key] || feature?.properties?.label || key,
        name: feature?.properties?.name || feature?.properties?.label || key,
        distanceM,
      };
      const current = bestByKey.get(key);
      if (!current || distanceM < current.distanceM) {
        bestByKey.set(key, item);
      }
      allNearest.push(item);
    }
    const primaryUnits = primaryKeys.map((key) => bestByKey.get(key) || {
      key,
      label: labelMap[key] || key,
      name: "Bulunamadi",
      distanceM: NaN,
    });
    const nearbyUnits = Array.from(bestByKey.values())
      .filter((item) => Number.isFinite(item?.distanceM))
      .sort((a, b) => a.distanceM - b.distanceM)
      .slice(0, 8);
    const payload = { primaryUnits, nearbyUnits };
    parcelInsightCache.set(cacheKey, payload);
    return payload;
  }

  function formatParcelFeature(feature) {
    if (isSalesOnlyModeActive()) {
      return formatSalesOnlyFeatureSummary(feature);
    }
    const props = feature?.properties || {};
    const entries = Object.entries(props)
      .filter(([, value]) => value !== null && value !== undefined && value !== "")
      .slice(0, 14)
      .map(([key, value]) => `${key}: ${value}`);
    return entries.length ? entries.join("\n") : "SeÃƒÂ§ili parcel ÃƒÂ¶zelliÃ„Å¸i bulunamadÃ„Â±.";
  }

  function formatSalesOnlyFeatureSummary(feature) {
    const props = feature?.properties || {};
    const parcelUseLabel = getParcelUseCategoryLabel(props.parcel_use_label || props.land_use_category || null);
    const historyCount = Number(props.history_transaction_count);
    const lines = [
      "Mod: Gecmis Satis",
      `Parsel: ${props.parcel_ref || props.inspire_id || props.parcel_id || "-"}`,
      `Parsel Turu: ${parcelUseLabel || "-"}`,
      `Kayit Sayisi: ${Number.isFinite(historyCount) ? historyCount : "-"}`,
      `Son Satis Tarihi: ${props.latest_history_sale_date || "-"}`,
      `Son Satis Fiyati: ${formatSalePrice(props.latest_history_price_paid)}`,
      `Yapi Sinifi: ${props.latest_history_building_class_label || classifyHistoryBuildingType(props.latest_history_property_type)}`,
      `Yapi Tipi: ${props.latest_history_property_type_label || formatHistoryPropertyType(props.latest_history_property_type)}`,
      `Mulkiyet: ${props.latest_history_tenure || "-"}`,
      `Konum: ${props.latest_history_location || props.local_authority || "-"}`,
      `Alan: ${Number.isFinite(Number(props.latest_history_area_m2)) ? `${formatNumber(Number(props.latest_history_area_m2), 0)} m2` : "-"}`,
      `m2 Fiyati: ${Number.isFinite(Number(props.latest_history_price_per_m2)) ? formatGbpPerM2(Number(props.latest_history_price_per_m2)) : "-"}`,
    ];
    return lines.join("\n");
  }

  function updateSelectedParcel(feature) {
    selectedParcelFeature = feature || null;
    workspacePanelCollapsed = false;
    setSanitizedText(selectedParcelEl, selectedParcelFeature
      ? formatParcelFeature(selectedParcelFeature)
      : "HenÃƒÂ¼z seÃƒÂ§im yok.");

    const source = map.getSource("selected-parcel");
    if (source && source.setData) {
      source.setData(
        feature
          ? { type: "FeatureCollection", features: [feature] }
          : { type: "FeatureCollection", features: [] }
      );
    }
    syncLandIntelligenceForSelectedParcel(feature);
    renderWorkspace();
    updateWorkspacePanelVisibility();
  }

  function buildParcelPopupContent(feature, lngLat) {
    const parcel = getParcelModelFromFeature(feature);
    const container = document.createElement("div");
    container.className = "parcel-popup";
    const compared = isParcelCompared(parcel);
    const cachedState = landIntelligenceCache.get(parcel.ref);
    const filteredView = cachedState?.signals ? buildFilteredLandIntelligenceView(cachedState) : null;
    const dominantContextCode = cachedState?.parcelDetail?.context_summary?.dominant_context_code || null;
    const dominantContextLabel = dominantContextCode ? getFacilityCategoryLabel(dominantContextCode) : null;
    const topSaleRecord = filteredView?.topActionableSaleRecord || filteredView?.topSaleRecord || null;
    const topSalePrice = topSaleRecord ? formatSalePrice(topSaleRecord.ask_price) : null;
    const topSaleTruth = topSaleRecord ? getSalePriceTruth(topSaleRecord, filteredView?.filteredSources || []) : null;
    const topSaleLinkTruth = topSaleRecord ? getSaleLinkTruth(topSaleRecord, filteredView?.filteredSources || []) : null;
    const topSaleLinkData = topSaleRecord ? resolveSaleRecordLink(topSaleRecord, filteredView?.filteredSources || []) : { url: null, label: "SatÃ„Â±Ã…Å¸ adresine git" };
    const officialSaleRecord = filteredView?.topOfficialSaleRecord || null;
    const marketListingFeature = isMarketListingFeature(feature);
    const marketDisplayPolygonSource = feature?.properties?.display_polygon_source || (feature?.properties?.market_listing_source_geometry ? "feed_polygon" : "derived_parcel_geometry");
    const marketSourceStatus = feature?.properties?.source_polygon_original_site_status || "unknown_not_verified";
    const marketProvenanceNote = feature?.properties?.polygon_provenance_note || "-";
    const marketGeometryQuality = feature?.properties?.geometry_quality_label || "-";

    if (isSalesOnlyModeActive()) {
      const history = Array.isArray(cachedState?.history) ? cachedState.history : [];
      const latest = history[0] || null;
      setSanitizedHtml(container, `
        <div class="parcel-popup-title">${parcel.ref}</div>
        <div class="signal-popup-list">
          <div><strong>Mod:</strong> Gecmis Satis</div>
          <div><strong>Parsel Turu:</strong> ${getParcelUseCategoryLabel(feature?.properties?.parcel_use_label || feature?.properties?.land_use_category || "-")}</div>
          <div><strong>Kayit Sayisi:</strong> ${history.length}</div>
          <div><strong>Son Satis Tarihi:</strong> ${latest?.sale_date || "-"}</div>
          <div><strong>Son Satis Fiyati:</strong> ${latest?.price_paid ? formatSalePrice(Number(latest.price_paid)) : "-"}</div>
          <div><strong>Yapi Sinifi:</strong> ${latest ? (latest.building_class_label || classifyHistoryBuildingType(latest.property_type)) : "-"}</div>
          <div><strong>Yapi Tipi:</strong> ${latest ? (latest.property_type_label || formatHistoryPropertyType(latest.property_type)) : "-"}</div>
          <div><strong>Mulkiyet:</strong> ${latest?.tenure || "-"}</div>
          <div><strong>Alan:</strong> ${latest?.building_area_m2 ? `${formatNumber(Number(latest.building_area_m2), 0)} m2` : (latest?.parcel_area_m2 ? `${formatNumber(Number(latest.parcel_area_m2), 0)} m2` : "-")}</div>
          <div><strong>m2 Fiyati:</strong> ${latest?.price_per_m2_gbp ? formatGbpPerM2(Number(latest.price_per_m2_gbp)) : "-"}</div>
          <div><strong>Postcode:</strong> ${latest?.postcode || "-"}</div>
          <div><strong>Konum:</strong> ${latest?.location_label || parcel.regionLabel || "-"}</div>
        </div>
      `);
      return container;
    }

    setSanitizedHtml(container, `
      <div class="parcel-popup-title">${parcel.ref}</div>
      <div class="parcel-popup-meta">${Object.entries(feature.properties || {})
        .slice(0, 4)
        .map(([key, value]) => `${key}: ${value}`)
        .join("<br />")}</div>
      ${dominantContextLabel ? `<div class="parcel-popup-meta" style="margin-top:8px;">Arazi kullanim tipi: ${dominantContextLabel}</div>` : ""}
      ${
        filteredView
          ? `<div class="parcel-popup-meta" style="margin-top:8px;">
              Official sale: ${filteredView.officialSaleSources.length ? "Var" : "Yok"}<br />
              Brownfield: ${filteredView.brownfieldSources.length ? "Var" : "Yok"}<br />
              Market listing: ${filteredView.marketSources.length ? "Var" : "Yok"}<br />
              Supabase kaydi: ${filteredView.managedSources.length ? "Var" : "Yok"}<br />
              ${officialSaleRecord ? `Official signal: ${officialSaleRecord.listing_status || officialSaleRecord.status || "-"}<br />` : ""}
              ${topSaleRecord ? `En ust kayÃ„Â±t: ${topSaleRecord.parcel_name || topSaleRecord.label || topSaleRecord.listing_id || "-"} Ã‚Â· ${topSaleRecord.listing_status || topSaleRecord.status || "-"}<br />Fiyat: ${topSalePrice} Ã‚Â· ${topSaleTruth?.label || "Fiyat tipi bilinmiyor"}<br />Kaynak: ${topSaleTruth?.detail || "-"}<br />Link: ${topSaleLinkTruth?.label || "Link tipi bilinmiyor"} Ã‚Â· ${topSaleLinkTruth?.detail || "-"}<br />${buildExternalSaleLink(topSaleLinkData.url, topSaleLinkData.label)}` : "SatÃ„Â±Ã…Å¸ kaydÃ„Â±: yok"}
            </div>`
          : ""
      }
      ${marketListingFeature ? `<div class="parcel-popup-meta" style="margin-top:8px;">
            Geometri modu: ${formatMarketPolygonSourceLabel(marketDisplayPolygonSource)}<br />
            Orijinal site: ${formatMarketOriginalSiteStatusLabel(marketSourceStatus)}<br />
            Geometri kalite: ${marketGeometryQuality}<br />
            Provenance: ${marketProvenanceNote}
          </div>` : ""}
    `);
    const actionButton = document.createElement("button");
    actionButton.type = "button";
    actionButton.className = "parcel-popup-action";
    actionButton.textContent = compared ? "-" : "+";
    actionButton.setAttribute("aria-label", compared ? "KarÃ…Å¸Ã„Â±laÃ…Å¸tÃ„Â±rma listesinden ÃƒÂ§Ã„Â±kar" : "KarÃ…Å¸Ã„Â±laÃ…Å¸tÃ„Â±rma listesine ekle");
    actionButton.title = compared ? "KarÃ…Å¸Ã„Â±laÃ…Å¸tÃ„Â±rma listesinden ÃƒÂ§Ã„Â±kar" : "KarÃ…Å¸Ã„Â±laÃ…Å¸tÃ„Â±rma listesine ekle";
    actionButton.addEventListener("click", (event) => {
      event.preventDefault();
      event.stopPropagation();
      const currentCompared = isParcelCompared(parcel);
      const result = currentCompared ? removeComparedParcelByKey(getParcelCompareKey(parcel)) : addComparedParcel(feature);
      if (result.changed) {
        showStatus(`${parcel.ref} ${currentCompared ? "karÃ…Å¸Ã„Â±laÃ…Å¸tÃ„Â±rma listesinden ÃƒÂ§Ã„Â±karÃ„Â±ldÃ„Â±" : "karÃ…Å¸Ã„Â±laÃ…Å¸tÃ„Â±rma listesine eklendi"}.`);
      }
      if (activeParcelPopupState && activeParcelPopupState.feature && getParcelRef(activeParcelPopupState.feature) === parcel.ref) {
        activeParcelPopupState = { feature, lngLat };
      }
      openParcelPopup(feature, lngLat);
    });
    container.appendChild(actionButton);
    return container;
  }

  function openParcelPopup(feature, lngLat) {
    activeParcelPopupState = { feature, lngLat };
    if (parcelPopup) {
      parcelPopup.remove();
    }
    parcelPopup = new maplibregl.Popup({ closeButton: true, maxWidth: "320px" })
      .setLngLat(lngLat)
      .setDOMContent(buildParcelPopupContent(feature, lngLat))
      .addTo(map);
    parcelPopup.on("close", () => {
      activeParcelPopupState = null;
      parcelPopup = null;
    });
  }

  function refreshActiveParcelPopup() {
    if (!parcelPopup || !activeParcelPopupState?.feature || !activeParcelPopupState?.lngLat) return;
    parcelPopup.setDOMContent(buildParcelPopupContent(activeParcelPopupState.feature, activeParcelPopupState.lngLat));
  }

  function buildSignalPopupContent(feature, title, rows, tags = []) {
    const container = document.createElement("div");
    container.className = "parcel-popup";
    const rowHtml = rows
      .filter((row) => row && row.value !== null && row.value !== undefined && row.value !== "")
      .map((row) => `<div><strong>${row.label}:</strong> ${row.value}</div>`)
      .join("");
    const tagHtml = tags.length
      ? `<div class="signal-popup-tags">${tags.map((tag) => `<span class="signal-popup-tag">${tag}</span>`).join("")}</div>`
      : "";
    setSanitizedHtml(container, `
      <div class="parcel-popup-title">${title}</div>
      <div class="signal-popup-list">${rowHtml || "Ek detay bulunamadi."}</div>
      ${tagHtml}
    `);
    return container;
  }

  function openFacilityPopup(feature, lngLat) {
    const props = feature?.properties || {};
    const rows = [
      { label: "Kategori", value: getFacilityCategoryLabel(props.category_code) },
      { label: "Ad", value: props.name || props.subtype || "-" },
      { label: "Kaynak", value: props.source_name || "-" },
      { label: "Oncelik", value: props.source_priority || "-" },
      { label: "Authority", value: props.local_authority || "-" },
      { label: "Adres", value: props.address_text || "-" },
      { label: "Postcode", value: props.postcode || "-" },
      { label: "Confidence", value: props.confidence_score ? formatNumber(props.confidence_score, 1) : "-" },
      { label: "Review", value: props.requires_review ? "Gerekli" : "Yok" },
    ];
    if (parcelPopup) {
      parcelPopup.remove();
    }
    parcelPopup = new maplibregl.Popup({ closeButton: true, maxWidth: "320px" })
      .setLngLat(lngLat)
      .setDOMContent(
        buildSignalPopupContent(
          feature,
          props.name || getFacilityCategoryLabel(props.category_code),
          rows,
          [getFacilityCategoryLabel(props.category_code), props.source_priority || null].filter(Boolean)
        )
      )
      .addTo(map);
    parcelPopup.on("close", () => {
      parcelPopup = null;
      activeParcelPopupState = null;
    });
  }

  function openLandUseGridPopup(feature, lngLat) {
    const props = feature?.properties || {};
    const categoryCode = String(
      props.land_use_category || props.parcel_use_label || props.category_code || "mixed_use"
    )
      .trim()
      .toLowerCase();
    const categoryLabel = getParcelUseCategoryLabel(categoryCode);
    const confidenceValue = Number(props.parcel_use_confidence);
    const rows = [
      { label: "Yapi turu", value: categoryLabel },
      { label: "Sinif", value: categoryCode },
      { label: "Guven", value: Number.isFinite(confidenceValue) ? `${formatNumber(confidenceValue, 1)}%` : "-" },
    ];
    if (parcelPopup) {
      parcelPopup.remove();
    }
    parcelPopup = new maplibregl.Popup({ closeButton: true, maxWidth: "320px" })
      .setLngLat(lngLat)
      .setDOMContent(buildSignalPopupContent(feature, `Yapi Turu Ã‚Â· ${categoryLabel}`, rows, [categoryLabel]))
      .addTo(map);
    parcelPopup.on("close", () => {
      parcelPopup = null;
      activeParcelPopupState = null;
    });
  }

  function openSignalPopup(feature, lngLat, kind) {
    const props = feature?.properties || {};
    const saleSummary = getParcelFeatureSaleSummary(feature);
    const matchedFootprint = kind === "official_sale" ? findBestOfficialSaleFootprintForParcelFeature(feature) : null;
    const matchedParcelFeature = kind === "official_sale_footprint" ? findOfficialSaleParcelFeatureForFootprint(feature) : null;
    const actionableSaleRecord = kind === "official_sale_footprint"
      ? getActionableSaleRecordForParcelFeature(matchedParcelFeature, feature)
      : getActionableSaleRecordForParcelFeature(feature, matchedFootprint);
    const actionableSaleLink = actionableSaleRecord
      ? resolveSaleRecordLink(actionableSaleRecord)
      : { url: null, label: "SatÃ„Â±Ã…Å¸ adresine git" };
    const actionableSaleTruth = getSalePriceTruth(actionableSaleRecord);
    const actionableSaleLinkTruth = getSaleLinkTruth(actionableSaleRecord);
    const actionableListingAreaM2 = getListingAreaM2(actionableSaleRecord);
    const parcelAreaM2 = Number(props.area_m2);
    const matchedParcelAreaM2 = Number(matchedParcelFeature?.properties?.area_m2);
    let title = "Kaynak Kaydi";
    let rows = [];
    let tags = [];

    if (kind === "official_sale") {
      title = props.parcel_ref || props.inspire_id || props.parcel_id || "Satisa Uygun Parcel";
      rows = [
        { label: "Parsel", value: props.parcel_ref || props.inspire_id || props.parcel_id },
        { label: "Local Authority", value: props.local_authority },
        { label: "Official Status", value: saleSummary.official_sale_status || "-" },
        { label: "Fiyat/Link Kaynagi", value: actionableSaleRecord?.provider_name || getLandSourceDisplayName(actionableSaleRecord?.source_name) || "-" },
        { label: "Fiyat", value: formatSalePrice(actionableSaleRecord?.ask_price ?? saleSummary.latest_asking_price_gbp) },
        { label: "Ilan alani", value: formatListingArea(actionableSaleRecord) },
        { label: "Ilan - parcel farki", value: formatListingVsParcelAreaDelta(actionableListingAreaM2, parcelAreaM2) },
        { label: "Fiyat TÃƒÂ¼rÃƒÂ¼", value: actionableSaleTruth.label },
        { label: "Fiyat Notu", value: actionableSaleTruth.detail },
        { label: "Link TÃƒÂ¼rÃƒÂ¼", value: actionableSaleLinkTruth.label },
        { label: "Link Notu", value: actionableSaleLinkTruth.detail },
        { label: "Satis adresi", value: buildExternalSaleLink(actionableSaleLink.url, actionableSaleLink.label) },
        { label: "Confidence", value: props.highest_confidence_score ? formatNumber(props.highest_confidence_score, 1) : "-" },
        { label: "Last Updated", value: formatLandOverlayDate(props.last_updated) },
        { label: "Review", value: props.requires_review ? "Gerekli" : "Yok" },
      ];
      tags = [
        "Satisa Uygun Parcel",
        props.official_sale_signal ? "Official Sale" : null,
        props.portal_listing_signal ? "Portal Listing" : null,
        actionableSaleTruth?.label || null,
        actionableSaleLinkTruth?.label || null,
        actionableSaleRecord?.source_name === "market_listing_adapter" ? "Portal fiyat/link" : null,
        actionableSaleRecord?.source_name === "supabase_admin" ? "Managed Sales fiyat/link" : null,
        props.brownfield_signal ? "Brownfield" : null,
      ].filter(Boolean);
    } else if (kind === "historic_sale") {
      title = props.parcel_ref || props.inspire_id || props.parcel_id || "Gecmis Satis Parcel";
      const latestHistorySaleDate = props.latest_history_sale_date || "-";
      const latestHistorySaleYear = String(latestHistorySaleDate || "").slice(0, 4);
      rows = [
        { label: "Parsel", value: props.parcel_ref || props.inspire_id || props.parcel_id },
        { label: "Local Authority", value: props.local_authority || "-" },
        { label: "Parsel turu", value: getParcelUseCategoryLabel(props.parcel_use_label || props.land_use_category || "-") },
        { label: "Gecmis satis kayit sayisi", value: Number.isFinite(Number(props.history_transaction_count)) ? Number(props.history_transaction_count) : "-" },
        { label: "Son satis tarihi", value: latestHistorySaleDate },
        { label: "Satis yili", value: latestHistorySaleYear && latestHistorySaleYear !== "-" ? latestHistorySaleYear : "-" },
        { label: "Son satis fiyati", value: formatSalePrice(props.latest_history_price_paid) },
        { label: "Yapi sinifi", value: props.latest_history_building_class_label || classifyHistoryBuildingType(props.latest_history_property_type) },
        { label: "Yapi tipi", value: props.latest_history_property_type_label || formatHistoryPropertyType(props.latest_history_property_type) },
        { label: "Mulkiyet", value: props.latest_history_tenure || "-" },
        { label: "Konum", value: props.latest_history_location || "-" },
        { label: "Alan", value: Number.isFinite(Number(props.latest_history_area_m2)) ? `${formatNumber(Number(props.latest_history_area_m2), 0)} m2` : "-" },
        { label: "m2 fiyati", value: Number.isFinite(Number(props.latest_history_price_per_m2)) ? formatGbpPerM2(Number(props.latest_history_price_per_m2)) : "-" },
      ];
      tags = ["Gecmis Satis", "Price Paid", Number(props.history_transaction_count) > 0 ? "Kayitli" : null].filter(Boolean);
    } else if (kind === "official_sale_footprint") {
      title = props.parcel_name || props.listing_id || "SatÃ„Â±Ã…Å¸ AlanÃ„Â±";
      rows = [
        { label: "SatÃ„Â±Ã…Å¸ alanÃ„Â±", value: props.parcel_name || props.listing_id || "-" },
        { label: "EÃ…Å¸leÃ…Å¸en parcel", value: props.matched_parcel_ref || props.matched_inspire_id || "-" },
        { label: "Authority", value: props.local_authority || "-" },
        { label: "Listing status", value: props.listing_status || "-" },
        { label: "Planning", value: props.planning_status || "-" },
        { label: "Fiyat/Link Kaynagi", value: actionableSaleRecord?.provider_name || getLandSourceDisplayName(actionableSaleRecord?.source_name) || "-" },
        { label: "Fiyat", value: formatSalePrice(actionableSaleRecord?.ask_price ?? props.ask_price) },
        { label: "Ilan alani", value: formatListingArea(actionableSaleRecord || buildSaleRecordFromFeature(feature)) },
        { label: "Ilan - parcel farki", value: formatListingVsParcelAreaDelta(actionableListingAreaM2, matchedParcelAreaM2) },
        { label: "Fiyat TÃƒÂ¼rÃƒÂ¼", value: actionableSaleTruth.label },
        { label: "Fiyat Notu", value: actionableSaleTruth.detail },
        { label: "Link TÃƒÂ¼rÃƒÂ¼", value: actionableSaleLinkTruth.label },
        { label: "Link Notu", value: actionableSaleLinkTruth.detail },
        { label: "SatÃ„Â±Ã…Å¸ adresi", value: buildExternalSaleLink(actionableSaleLink.url || getListingFeatureLink(feature), actionableSaleLink.label || getListingFeatureLinkLabel(feature)) },
        { label: "Confidence", value: props.confidence_score ? formatNumber(props.confidence_score, 1) : "-" },
        { label: "Last Updated", value: formatLandOverlayDate(props.source_updated_at) },
        { label: "Review", value: props.requires_review ? "Gerekli" : "Yok" },
      ];
      tags = [
        "SatÃ„Â±Ã…Å¸ AlanÃ„Â±",
        "Parcel-first seÃƒÂ§im",
        actionableSaleTruth?.label || null,
        actionableSaleLinkTruth?.label || null,
        actionableSaleRecord?.source_name === "market_listing_adapter" ? "Portal fiyat/link" : null,
        actionableSaleRecord?.source_name === "supabase_admin" ? "Managed Sales fiyat/link" : null,
        props.matched_match_method ? `Match: ${props.matched_match_method}` : null,
      ].filter(Boolean);
    } else if (kind === "brownfield") {
      title = props.reference || props.site_id || props.parcel_ref || props.inspire_id || props.parcel_id || "Brownfield Parcel";
      rows = [
        { label: "Kayit", value: props.reference || props.site_id || props.parcel_ref || props.inspire_id || props.parcel_id },
        { label: "Local Authority", value: props.local_authority || "-" },
        { label: "Geometri Modu", value: props.brownfield_fallback_source ? "Kaynak saha (parcel eslesmesi yok)" : "Parcel eslesmesi" },
        { label: "Brownfield Signal", value: props.brownfield_signal ? "Var" : "Yok" },
        { label: "Kaynak", value: props.source_name ? getLandSourceDisplayName(props.source_name) : "-" },
        { label: "Planning", value: props.planning_status || "-" },
        { label: "Hektar", value: Number.isFinite(Number(props.hectares)) ? formatNumber(Number(props.hectares), 2) : "-" },
        { label: "Confidence", value: props.confidence_score || props.highest_confidence_score ? formatNumber(Number(props.confidence_score ?? props.highest_confidence_score), 1) : "-" },
        { label: "Last Updated", value: formatLandOverlayDate(props.source_updated_at || props.last_updated) },
        { label: "Review", value: props.requires_review ? "Gerekli" : "Yok" },
      ];
      tags = ["Brownfield Parcel", "Brownfield ? Satilik Garantisi Degil", props.requires_review ? "Review Gerekli" : null].filter(Boolean);
    } else if (kind === "market_listing") {
      title = props.parcel_name || props.listing_id || props.parcel_ref || props.inspire_id || props.parcel_id || "Portal Listing Parcel";
      const displayPolygonSource = props.display_polygon_source || (props.market_listing_source_geometry ? "feed_polygon" : "derived_parcel_geometry");
      const sourceStatus = props.source_polygon_original_site_status || "unknown_not_verified";
      const provenanceNote = props.polygon_provenance_note || "-";
      const geometryQualityLabel = props.geometry_quality_label || "-";
      const edgeSummary = getRingEdgeLengthsMeters(getPrimaryPolygonRing(feature?.geometry))
        .slice(0, 4)
        .map((value) => formatDistanceMeters(value))
        .join(", ");
      rows = [
        { label: "Ilan", value: props.parcel_name || props.listing_id || "-" },
        { label: "Eslesen parsel", value: props.matched_parcel_ref || props.parcel_ref || props.matched_inspire_id || props.inspire_id || "-" },
        { label: "Parsel eslesme durumu", value: props.parcel_match_status === "matched_parcel" ? "Matched" : "Eslesme yok" },
        { label: "Authority", value: props.local_authority || "-" },
        { label: "Geometri tipi", value: feature?.geometry?.type || "-" },
        { label: "Kenar ozeti", value: edgeSummary || "-" },
        { label: "Geometri modu", value: formatMarketPolygonSourceLabel(displayPolygonSource) },
        { label: "Orijinal site durumu", value: formatMarketOriginalSiteStatusLabel(sourceStatus) },
        { label: "Geometri kalite", value: geometryQualityLabel },
        { label: "Poligon gosterimi", value: formatMarketPolygonDisplayState(props.market_polygon_displayable !== false) },
        { label: "Provenance", value: provenanceNote },
        { label: "Portal Listing", value: props.portal_listing_signal ? "Var" : "Yok" },
        { label: "Provider", value: props.provider_name || "-" },
        { label: "Fiyat", value: formatSalePrice(props.ask_price) },
        { label: "Satis adresi", value: buildExternalSaleLink(props.external_url || props.source_url, props.external_label || "Ilana git") },
        { label: "Confidence", value: props.confidence_score || props.highest_confidence_score ? formatNumber(Number(props.confidence_score ?? props.highest_confidence_score), 1) : "-" },
        { label: "Last Updated", value: formatLandOverlayDate(props.source_updated_at || props.last_updated) },
        { label: "Review", value: props.requires_review ? "Gerekli" : "Yok" },
      ];
      tags = [
        "Portal Listing",
        formatMarketPolygonSourceLabel(displayPolygonSource),
        props.market_polygon_displayable === false ? "Gercek poligon yok" : "Dogrulanmis/turetilmis poligon",
        sourceStatus.includes("synthetic") || displayPolygonSource === "synthetic_geometry" ? "Uydurma / duzensiz geometri" : null,
        props.matched_parcel_ref ? "Matched" : "Eslesme yok",
        props.requires_review ? "Review Gerekli" : null,
      ].filter(Boolean);
    }

    if (parcelPopup) {
      parcelPopup.remove();
    }
    parcelPopup = new maplibregl.Popup({ closeButton: true, maxWidth: "340px" })
      .setLngLat(lngLat)
      .setDOMContent(buildSignalPopupContent(feature, title, rows, tags))
      .addTo(map);
    parcelPopup.on("close", () => {
      parcelPopup = null;
      activeParcelPopupState = null;
    });
  }

  function createBaseStyle(baseMapMode = "standard") {
    return {
      version: 8,
      glyphs: "https://demotiles.maplibre.org/font/{fontstack}/{range}.pbf",
      sources: {
        osm: {
          type: "raster",
          tiles: [
            "https://a.tile.openstreetmap.org/{z}/{x}/{y}.png",
            "https://b.tile.openstreetmap.org/{z}/{x}/{y}.png",
            "https://c.tile.openstreetmap.org/{z}/{x}/{y}.png",
          ],
          tileSize: 256,
          attribution: "Ã‚Â© OpenStreetMap contributors",
        },
        satellite: {
          type: "raster",
          tiles: [
            "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
          ],
          tileSize: 256,
          attribution: "Tiles Ã‚Â© Esri",
        },
      },
      layers: [
        {
          id: "basemap-osm",
          type: "raster",
          source: "osm",
          layout: { visibility: baseMapMode === "standard" ? "visible" : "none" },
        },
        {
          id: "basemap-satellite",
          type: "raster",
          source: "satellite",
          layout: { visibility: baseMapMode === "satellite" ? "visible" : "none" },
        },
      ],
    };
  }

  function pickRegionForCenter(center) {
    return getCoverageState(center).nearestRegion;
  }

  async function loadPoiData(region) {
    if (poiCache.has(region.slug)) {
      return poiCache.get(region.slug);
    }
    const [pointsResult, linesResult] = await Promise.allSettled([
      fetch(region.poiPointsUrl).then((response) => response.json()),
      fetch(region.poiLinesUrl).then((response) => response.json()),
    ]);
    const points = pointsResult.status === "fulfilled" ? pointsResult.value : createEmptyFeatureCollection();
    const lines = linesResult.status === "fulfilled" ? linesResult.value : createEmptyFeatureCollection();
    if (pointsResult.status !== "fulfilled" && linesResult.status !== "fulfilled") {
      throw new Error("POI point ve line kaynaklari yuklenemedi.");
    }
    const payload = {
      points,
      lines,
      partial: pointsResult.status !== "fulfilled" || linesResult.status !== "fulfilled",
    };
    poiCache.set(region.slug, payload);
    return payload;
  }

  function getParcelSourceId(region) {
    return `parcels-${region.slug}`;
  }

  function getParcelFillLayerId(region) {
    return `parcel-fill-${region.slug}`;
  }

  function getParcelLineLayerId(region) {
    return `parcel-line-${region.slug}`;
  }

  function getParcelWarmLayerId(region) {
    return `parcel-warm-${region.slug}`;
  }

  function getAllParcelLayerIds() {
    return config.regions.flatMap((region) => [getParcelFillLayerId(region), getParcelLineLayerId(region), getParcelWarmLayerId(region)]);
  }

  function getAllParcelSourceIds() {
    return config.regions.map((region) => getParcelSourceId(region));
  }

  function clearDynamicSources() {
    [
      ...getAllParcelLayerIds(),
      TOPOGRAPHY_LAYER_ID,
      FUTURE_GROWTH_FILL_LAYER_ID,
      FUTURE_GROWTH_LINE_LAYER_ID,
      FUTURE_GROWTH_POINT_LAYER_ID,
      FUTURE_GROWTH_VECTOR_LAYER_ID,
      "compared-parcel-fill",
      "compared-parcel-line",
      "selected-parcel-fill",
      "selected-parcel-line",
      "official-sale-parcel-fill",
      "official-sale-parcel-line",
      "official-sale-parcel-label",
      "historic-sale-parcel-fill",
      "historic-sale-parcel-outline-halo",
      "historic-sale-parcel-line",
      "historic-sale-parcel-label",
      "official-sale-footprint-fill",
      "official-sale-footprint-line",
      "official-sale-footprint-label",
      "brownfield-polygons-fill",
      "brownfield-polygons-line",
      "brownfield-points",
      "market-listing-polygons-fill",
      "market-listing-polygons-outline-halo",
      "market-listing-polygons-line",
      "market-listing-points",
      "facilities-polygons-fill",
      "facilities-polygons-line",
      "facilities-points",
      "facilities-label",
      "parcel-use-parcels-fill",
      "parcel-use-parcels-line",
      "scenario-score-fill",
      "scenario-score-line",
      "poi-lines",
      "poi-points-clusters",
      "poi-points-count",
      "poi-points",
      "poi-points-label",
      "fallback-parcels-fill",
      "fallback-parcels-line",
    ].forEach((layerId) => {
      if (map.getLayer(layerId)) {
        map.removeLayer(layerId);
      }
    });
    [...getAllParcelSourceIds(), TOPOGRAPHY_SOURCE_ID, FUTURE_GROWTH_SOURCE_ID, FUTURE_GROWTH_VECTOR_SOURCE_ID, "fallback-parcels", "compared-parcels", "selected-parcel", "official-sale-parcels", "historic-sale-parcels", "official-sale-footprints", "brownfield-sites", "market-listings", "facilities-overlay", "parcel-use-parcels", "scenario-score-parcels", "poi-lines", "poi-points"].forEach((sourceId) => {
      if (map.getSource(sourceId)) {
        map.removeSource(sourceId);
      }
    });
  }

  function addParcelLayers(region) {
    config.regions.forEach((parcelRegion) => {
      const pmtilesUrl = new URL(parcelRegion.parcelsPmtilesUrl, window.location.href);
      pmtilesUrl.searchParams.set("v", "20260402-sale-links-and-price");
      const sourceId = getParcelSourceId(parcelRegion);
      const sourceDef = {
        type: "vector",
        url: `pmtiles://${pmtilesUrl.toString()}`,
      };
      if (Number.isFinite(Number(parcelRegion.parcelsMaxZoom))) {
        sourceDef.maxzoom = Number(parcelRegion.parcelsMaxZoom);
      }
      map.addSource(sourceId, sourceDef);

      map.addLayer({
        id: getParcelFillLayerId(parcelRegion),
        type: "fill",
        source: sourceId,
        "source-layer": "parcels",
        minzoom: config.parcelMinZoom,
        layout: {
          visibility: activeRegion && activeRegion.slug === parcelRegion.slug && isParcelViewMode() ? "visible" : "none",
        },
        paint: {
          "fill-color": "#d3a15a",
          "fill-opacity": ["interpolate", ["linear"], ["zoom"], config.parcelMinZoom, 0.1, 17, 0.18],
        },
      });

      map.addLayer({
        id: getParcelLineLayerId(parcelRegion),
        type: "line",
        source: sourceId,
        "source-layer": "parcels",
        minzoom: config.parcelMinZoom,
        layout: {
          visibility: activeRegion && activeRegion.slug === parcelRegion.slug && isParcelViewMode() ? "visible" : "none",
        },
        paint: {
          "line-color": "#15120e",
          "line-width": ["interpolate", ["linear"], ["zoom"], config.parcelMinZoom, 1.15, 17, 1.95],
          "line-opacity": ["interpolate", ["linear"], ["zoom"], config.parcelMinZoom, 0.92, 17, 0.99],
        },
      });

      // Invisible warm layer: keeps vector parcel tiles loaded for land-use fallback.
      map.addLayer({
        id: getParcelWarmLayerId(parcelRegion),
        type: "fill",
        source: sourceId,
        "source-layer": "parcels",
        minzoom: config.parcelMinZoom,
        layout: {
          visibility: activeRegion && activeRegion.slug === parcelRegion.slug && currentMapViewMode === "land_use" ? "visible" : "none",
        },
        paint: {
          "fill-color": "#000000",
          "fill-opacity": 0,
        },
      });
    });

    map.addSource("fallback-parcels", {
      type: "geojson",
      data: createEmptyFeatureCollection(),
    });

    map.addLayer({
      id: "fallback-parcels-fill",
      type: "fill",
      source: "fallback-parcels",
      minzoom: config.parcelMinZoom,
      filter: [
        "all",
        ["in", ["geometry-type"], ["literal", ["Polygon", "MultiPolygon"]]],
        ["==", ["get", "market_polygon_displayable"], true],
      ],
      layout: {
        visibility: isParcelViewMode() ? "visible" : "none",
      },
      paint: {
        "fill-color": "#d3a15a",
        "fill-opacity": ["interpolate", ["linear"], ["zoom"], config.parcelMinZoom, 0.08, 17, 0.14],
      },
    });

    map.addLayer({
      id: "fallback-parcels-line",
      type: "line",
      source: "fallback-parcels",
      minzoom: config.parcelMinZoom,
      filter: [
        "all",
        ["in", ["geometry-type"], ["literal", ["Polygon", "MultiPolygon"]]],
        ["==", ["get", "market_polygon_displayable"], true],
      ],
      layout: {
        visibility: isParcelViewMode() ? "visible" : "none",
      },
      paint: {
        "line-color": "#241b14",
        "line-width": ["interpolate", ["linear"], ["zoom"], config.parcelMinZoom, 0.95, 17, 1.45],
        "line-opacity": 0.92,
      },
    });

    map.addSource("compared-parcels", {
      type: "geojson",
      data: { type: "FeatureCollection", features: [] },
    });

    map.addLayer({
      id: "compared-parcel-fill",
      type: "fill",
      source: "compared-parcels",
      paint: {
        "fill-color": "#87532d",
        "fill-opacity": 0.52,
      },
    });

    map.addLayer({
      id: "compared-parcel-line",
      type: "line",
      source: "compared-parcels",
      paint: {
        "line-color": "#f7d6b3",
        "line-width": 1.6,
        "line-opacity": 0.96,
      },
    });

    map.addSource("selected-parcel", {
      type: "geojson",
      data: { type: "FeatureCollection", features: [] },
    });

    map.addLayer({
      id: "selected-parcel-fill",
      type: "fill",
      source: "selected-parcel",
      paint: {
        "fill-color": "#ff7f50",
        "fill-opacity": 0.16,
      },
    });

    map.addLayer({
      id: "selected-parcel-line",
      type: "line",
      source: "selected-parcel",
      paint: {
        "line-color": "#fff4e8",
        "line-width": 2,
      },
    });
  }

  function addPoiLayers(pointsData, linesData) {
    map.addSource("poi-lines", {
      type: "geojson",
      data: linesData,
    });

    map.addLayer({
      id: "poi-lines",
      type: "line",
      source: "poi-lines",
      minzoom: config.lineMinZoom,
      layout: {
        visibility: currentPoiLinesVisible ? "visible" : "none",
      },
      paint: {
        "line-color": ["coalesce", ["get", "color"], "#65c2ff"],
        "line-width": ["coalesce", ["get", "width"], 1.2],
        "line-opacity": 0.85,
      },
    });

    map.addSource("poi-points", {
      type: "geojson",
      data: pointsData,
      cluster: true,
      clusterMaxZoom: 13,
      clusterRadius: 40,
    });

    map.addLayer({
      id: "poi-points-clusters",
      type: "circle",
      source: "poi-points",
      filter: ["has", "point_count"],
      minzoom: config.poiMinZoom,
      layout: {
        visibility: currentPoiPointsVisible ? "visible" : "none",
      },
      paint: {
        "circle-color": "#173c63",
        "circle-stroke-color": "#c7ecff",
        "circle-stroke-width": 1.5,
        "circle-radius": ["step", ["get", "point_count"], 14, 25, 18, 100, 24],
      },
    });

    map.addLayer({
      id: "poi-points-count",
      type: "symbol",
      source: "poi-points",
      filter: ["has", "point_count"],
      minzoom: config.poiMinZoom,
      layout: {
        visibility: currentPoiPointsVisible ? "visible" : "none",
        "text-field": ["get", "point_count_abbreviated"],
        "text-size": 11,
      },
      paint: {
        "text-color": "#eff7ff",
      },
    });

    map.addLayer({
      id: "poi-points",
      type: "circle",
      source: "poi-points",
      filter: ["!", ["has", "point_count"]],
      minzoom: config.poiMinZoom,
      layout: {
        visibility: currentPoiPointsVisible ? "visible" : "none",
      },
      paint: {
        "circle-color": ["coalesce", ["get", "color"], "#52d8a3"],
        "circle-radius": ["interpolate", ["linear"], ["zoom"], config.poiMinZoom, 3, 16, 5],
        "circle-stroke-width": 1,
        "circle-stroke-color": "#0d1318",
      },
    });

    map.addLayer({
      id: "poi-points-label",
      type: "symbol",
      source: "poi-points",
      filter: ["!", ["has", "point_count"]],
      minzoom: 14,
      layout: {
        visibility: currentPoiPointsVisible ? "visible" : "none",
        "text-field": ["coalesce", ["get", "label"], ["get", "name"], ""],
        "text-font": ["Noto Sans Regular"],
        "text-size": 11,
        "text-offset": [0, 1.1],
      },
      paint: {
        "text-color": "#f5efe7",
        "text-halo-color": "#11161d",
        "text-halo-width": 1.1,
      },
    });
  }

  function addLandIntelligenceLayers() {
    if (map.getSource("official-sale-parcels")) return;

    map.addSource("sale-ready-overview", {
      type: "geojson",
      data: createEmptyFeatureCollection(),
      cluster: true,
      clusterMaxZoom: Math.max(0, Math.floor(LAND_SIGNAL_MIN_ZOOM) - 1),
      clusterRadius: 56,
    });
    map.addLayer({
      id: "sale-ready-overview-clusters",
      type: "circle",
      source: "sale-ready-overview",
      maxzoom: LAND_SIGNAL_MIN_ZOOM,
      filter: ["has", "point_count"],
      layout: {
        visibility: currentOfficialSaleVisible ? "visible" : "none",
      },
      paint: {
        "circle-color": [
          "case",
          ["==", ["coalesce", ["get", "overview_kind"], "official"], "history"],
          "#f05f57",
          "#ff7a00",
        ],
        "circle-radius": [
          "step",
          ["get", "point_count"],
          18,
          10,
          24,
          40,
          31,
          120,
          38,
        ],
        "circle-stroke-color": "#fff2e4",
        "circle-stroke-width": 2.2,
        "circle-opacity": 0.9,
      },
    });
    map.addLayer({
      id: "sale-ready-overview-count",
      type: "symbol",
      source: "sale-ready-overview",
      maxzoom: LAND_SIGNAL_MIN_ZOOM,
      filter: ["has", "point_count"],
      layout: {
        visibility: currentOfficialSaleVisible ? "visible" : "none",
        "text-field": ["get", "point_count_abbreviated"],
        "text-font": ["Noto Sans Regular"],
        "text-size": 12,
      },
      paint: {
        "text-color": "#24160c",
      },
    });
    map.addLayer({
      id: "sale-ready-overview-halo",
      type: "circle",
      source: "sale-ready-overview",
      maxzoom: LAND_SALE_OVERVIEW_HIDE_ZOOM,
      filter: ["!", ["has", "point_count"]],
      layout: {
        visibility: currentOfficialSaleVisible ? "visible" : "none",
      },
      paint: {
        "circle-color": "#ff7a00",
        "circle-radius": [
          "interpolate",
          ["linear"],
          ["zoom"],
          8,
          8,
          LAND_SIGNAL_MIN_ZOOM,
          14,
          LAND_SALE_OVERVIEW_HIDE_ZOOM,
          18,
        ],
        "circle-opacity": [
          "interpolate",
          ["linear"],
          ["zoom"],
          8,
          0.12,
          LAND_SIGNAL_MIN_ZOOM,
          0.1,
          LAND_SALE_OVERVIEW_HIDE_ZOOM,
          0.06,
        ],
        "circle-stroke-width": 0,
      },
    });
    map.addLayer({
      id: "sale-ready-overview-point",
      type: "circle",
      source: "sale-ready-overview",
      maxzoom: LAND_SALE_OVERVIEW_HIDE_ZOOM,
      filter: ["!", ["has", "point_count"]],
      layout: {
        visibility: currentOfficialSaleVisible ? "visible" : "none",
      },
      paint: {
        "circle-color": [
          "case",
          ["==", ["coalesce", ["get", "overview_kind"], "official"], "history"],
          "#f05f57",
          ["boolean", ["get", "is_on_market"], false],
          "#ff7a00",
          "#f2cf91",
        ],
        "circle-radius": [
          "interpolate",
          ["linear"],
          ["zoom"],
          5,
          5.5,
          LAND_SIGNAL_MIN_ZOOM,
          8.5,
          LAND_SALE_OVERVIEW_HIDE_ZOOM,
          10.5,
        ],
        "circle-stroke-color": [
          "case",
          ["==", ["coalesce", ["get", "overview_kind"], "official"], "history"],
          "#ffd6d1",
          ["boolean", ["get", "has_sale_link"], false],
          "#fff2e4",
          "#7a3a10",
        ],
        "circle-stroke-width": 1.4,
        "circle-opacity": 0.92,
      },
    });

    map.addSource("official-sale-parcels", {
      type: "geojson",
      data: createEmptyFeatureCollection(),
    });
    map.addLayer({
      id: "official-sale-parcel-fill",
      type: "fill",
      source: "official-sale-parcels",
      minzoom: LAND_SIGNAL_MIN_ZOOM,
      filter: ["==", ["geometry-type"], "Polygon"],
      layout: {
        visibility: currentOfficialSaleVisible ? "visible" : "none",
      },
      paint: {
        "fill-color": "#ff7a00",
        "fill-opacity": [
          "interpolate",
          ["linear"],
          ["zoom"],
          LAND_SIGNAL_MIN_ZOOM,
          0.12,
          16,
          0.17,
          18,
          0.22
        ],
      },
    });
    map.addLayer({
      id: "official-sale-parcel-outline-halo",
      type: "line",
      source: "official-sale-parcels",
      minzoom: LAND_SIGNAL_MIN_ZOOM,
      filter: ["==", ["geometry-type"], "Polygon"],
      layout: {
        visibility: currentOfficialSaleVisible ? "visible" : "none",
        "line-join": "round",
        "line-cap": "round",
      },
      paint: {
        "line-color": "#ffbf85",
        "line-width": [
          "interpolate",
          ["linear"],
          ["zoom"],
          LAND_SIGNAL_MIN_ZOOM,
          5.2,
          16,
          7.2,
          18,
          9.2
        ],
        "line-opacity": 0.42,
      },
    });
    map.addLayer({
      id: "official-sale-parcel-line",
      type: "line",
      source: "official-sale-parcels",
      minzoom: LAND_SIGNAL_MIN_ZOOM,
      filter: ["==", ["geometry-type"], "Polygon"],
      layout: {
        visibility: currentOfficialSaleVisible ? "visible" : "none",
        "line-join": "round",
        "line-cap": "round",
      },
      paint: {
        "line-color": "#ff7a00",
        "line-width": [
          "interpolate",
          ["linear"],
          ["zoom"],
          LAND_SIGNAL_MIN_ZOOM,
          3.2,
          16,
          4.4,
          18,
          5.6
        ],
        "line-opacity": 1,
      },
    });
    map.addLayer({
      id: "official-sale-parcel-label",
      type: "symbol",
      source: "official-sale-parcels",
      minzoom: Math.max(LAND_SIGNAL_MIN_ZOOM, 16),
      filter: ["==", ["geometry-type"], "Polygon"],
      layout: {
        visibility: currentOfficialSaleVisible ? "visible" : "none",
        "symbol-placement": "point",
        "text-field": "SATIS",
        "text-font": ["Noto Sans Regular"],
        "text-size": 10,
        "text-letter-spacing": 0.08,
        "text-allow-overlap": false,
        "text-ignore-placement": false,
      },
      paint: {
        "text-color": "#ffeddc",
        "text-halo-color": "#7a2b0c",
        "text-halo-width": 1.2,
      },
    });
    map.addSource("official-sale-footprints", {
      type: "geojson",
      data: createEmptyFeatureCollection(),
    });
    map.addLayer({
      id: "official-sale-footprint-fill",
      type: "fill",
      source: "official-sale-footprints",
      minzoom: Math.max(LAND_SIGNAL_MIN_ZOOM, Number(config.parcelMinZoom || LAND_SIGNAL_MIN_ZOOM)),
      filter: [
        "all",
        ["in", ["geometry-type"], ["literal", ["Polygon", "MultiPolygon"]]],
        ["==", ["get", "market_polygon_displayable"], true],
      ],
      layout: {
        visibility: currentOfficialSaleVisible ? "visible" : "none",
      },
      paint: {
        "fill-color": "#f2cf91",
        "fill-opacity": [
          "interpolate",
          ["linear"],
          ["zoom"],
          LAND_SIGNAL_MIN_ZOOM,
          0.12,
          16,
          0.16,
          18,
          0.2,
        ],
      },
    });
    map.addLayer({
      id: "official-sale-footprint-line",
      type: "line",
      source: "official-sale-footprints",
      minzoom: Math.max(LAND_SIGNAL_MIN_ZOOM, Number(config.parcelMinZoom || LAND_SIGNAL_MIN_ZOOM)),
      filter: ["==", ["geometry-type"], "Polygon"],
      layout: {
        visibility: currentOfficialSaleVisible ? "visible" : "none",
      },
      paint: {
        "line-color": "#17120d",
        "line-width": [
          "interpolate",
          ["linear"],
          ["zoom"],
          LAND_SIGNAL_MIN_ZOOM,
          1.8,
          16,
          2.8,
          18,
          3.8,
        ],
        "line-opacity": 0.96,
      },
    });
    map.addLayer({
      id: "official-sale-footprint-label",
      type: "symbol",
      source: "official-sale-footprints",
      minzoom: Math.max(LAND_SIGNAL_MIN_ZOOM, Number(config.parcelMinZoom || LAND_SIGNAL_MIN_ZOOM), 16),
      filter: ["==", ["geometry-type"], "Polygon"],
      layout: {
        visibility: currentOfficialSaleVisible ? "visible" : "none",
        "symbol-placement": "point",
        "text-field": "SATIS",
        "text-font": ["Noto Sans Regular"],
        "text-size": 10,
        "text-letter-spacing": 0.08,
        "text-allow-overlap": false,
      },
      paint: {
        "text-color": "#d26f45",
        "text-halo-color": "#f8e5c1",
        "text-halo-width": 1.2,
      },
    });
    map.addLayer({
      id: "official-sale-parcel-line-top",
      type: "line",
      source: "official-sale-parcels",
      minzoom: LAND_SIGNAL_MIN_ZOOM,
      filter: ["==", ["geometry-type"], "Polygon"],
      layout: {
        visibility: currentOfficialSaleVisible ? "visible" : "none",
        "line-join": "round",
        "line-cap": "round",
      },
      paint: {
        "line-color": "#ff7a00",
        "line-width": [
          "interpolate",
          ["linear"],
          ["zoom"],
          LAND_SIGNAL_MIN_ZOOM,
          2.6,
          16,
          3.8,
          18,
          4.8
        ],
        "line-opacity": 1,
      },
    });

    map.addSource("historic-sale-parcels", {
      type: "geojson",
      data: createEmptyFeatureCollection(),
    });
    map.addLayer({
      id: "historic-sale-parcel-fill",
      type: "fill",
      source: "historic-sale-parcels",
      minzoom: LAND_SIGNAL_MIN_ZOOM,
      filter: ["==", ["geometry-type"], "Polygon"],
      layout: {
        visibility: currentHistoricSalesVisible ? "visible" : "none",
      },
      paint: {
        "fill-color": "#ff4d6d",
        "fill-opacity": [
          "interpolate",
          ["linear"],
          ["zoom"],
          LAND_SIGNAL_MIN_ZOOM,
          0.34,
          16,
          0.4,
          18,
          0.48,
        ],
      },
    });
    map.addLayer({
      id: "historic-sale-parcel-outline-halo",
      type: "line",
      source: "historic-sale-parcels",
      minzoom: LAND_SIGNAL_MIN_ZOOM,
      filter: ["==", ["geometry-type"], "Polygon"],
      layout: {
        visibility: currentHistoricSalesVisible ? "visible" : "none",
        "line-join": "round",
        "line-cap": "round",
      },
      paint: {
        "line-color": "#ffd8e1",
        "line-width": [
          "interpolate",
          ["linear"],
          ["zoom"],
          LAND_SIGNAL_MIN_ZOOM,
          6.4,
          16,
          8.8,
          18,
          11.2,
        ],
        "line-opacity": 0.5,
      },
    });
    map.addLayer({
      id: "historic-sale-parcel-line",
      type: "line",
      source: "historic-sale-parcels",
      minzoom: LAND_SIGNAL_MIN_ZOOM,
      filter: ["==", ["geometry-type"], "Polygon"],
      layout: {
        visibility: currentHistoricSalesVisible ? "visible" : "none",
        "line-join": "round",
        "line-cap": "round",
      },
      paint: {
        "line-color": "#8d1832",
        "line-width": [
          "interpolate",
          ["linear"],
          ["zoom"],
          LAND_SIGNAL_MIN_ZOOM,
          4.2,
          16,
          5.9,
          18,
          7.6,
        ],
        "line-opacity": 1,
        "line-dasharray": [0.9, 0.4],
      },
    });
    map.addLayer({
      id: "historic-sale-parcel-label",
      type: "symbol",
      source: "historic-sale-parcels",
      minzoom: Math.max(LAND_SIGNAL_MIN_ZOOM, 16),
      filter: ["==", ["geometry-type"], "Polygon"],
      layout: {
        visibility: currentHistoricSalesVisible ? "visible" : "none",
        "symbol-placement": "point",
        "text-field": "$ SATIS",
        "text-font": ["Noto Sans Regular"],
        "text-size": 10,
        "text-letter-spacing": 0.06,
      },
      paint: {
        "text-color": "#ffece9",
        "text-halo-color": "#7c231f",
        "text-halo-width": 1.1,
      },
    });

    map.addSource("brownfield-sites", {
      type: "geojson",
      data: createEmptyFeatureCollection(),
    });
    map.addLayer({
      id: "brownfield-polygons-fill",
      type: "fill",
      source: "brownfield-sites",
      minzoom: LAND_SIGNAL_MIN_ZOOM,
      filter: ["==", ["geometry-type"], "Polygon"],
      layout: {
        visibility: currentBrownfieldVisible ? "visible" : "none",
      },
      paint: {
        "fill-color": "#67d5a5",
        "fill-opacity": 0.24,
      },
    });
    map.addLayer({
      id: "brownfield-polygons-line",
      type: "line",
      source: "brownfield-sites",
      minzoom: LAND_SIGNAL_MIN_ZOOM,
      filter: ["==", ["geometry-type"], "Polygon"],
      layout: {
        visibility: currentBrownfieldVisible ? "visible" : "none",
      },
      paint: {
        "line-color": "#b8f5d7",
        "line-width": 2.4,
        "line-opacity": 0.95,
      },
    });
    map.addLayer({
      id: "brownfield-points",
      type: "circle",
      source: "brownfield-sites",
      minzoom: LAND_SIGNAL_MIN_ZOOM,
      filter: ["==", ["geometry-type"], "Point"],
      layout: {
        visibility: currentBrownfieldVisible ? "visible" : "none",
      },
      paint: {
        "circle-color": "#67d5a5",
        "circle-radius": [
          "interpolate",
          ["linear"],
          ["zoom"],
          LAND_SIGNAL_MIN_ZOOM,
          3.8,
          16,
          5.6,
          18,
          7.2,
        ],
        "circle-stroke-color": "#0f2b22",
        "circle-stroke-width": 1.2,
        "circle-opacity": 0.95,
      },
    });
    map.addSource("market-listings", {
      type: "geojson",
      data: createEmptyFeatureCollection(),
    });
    map.addLayer({
      id: "market-listing-polygons-fill",
      type: "fill",
      source: "market-listings",
      minzoom: LAND_SIGNAL_MIN_ZOOM,
      filter: [
        "all",
        ["in", ["geometry-type"], ["literal", ["Polygon", "MultiPolygon"]]],
        ["==", ["get", "market_polygon_displayable"], true],
      ],
      layout: {
        visibility: currentMarketListingsVisible ? "visible" : "none",
      },
      paint: {
        "fill-color": "#f08a24",
        "fill-opacity": [
          "interpolate",
          ["linear"],
          ["zoom"],
          LAND_SIGNAL_MIN_ZOOM,
          0.08,
          16,
          0.11,
          18,
          0.14,
        ],
      },
    });
    map.addLayer({
      id: "market-listing-polygons-outline-halo",
      type: "line",
      source: "market-listings",
      minzoom: LAND_SIGNAL_MIN_ZOOM,
      filter: [
        "all",
        ["in", ["geometry-type"], ["literal", ["Polygon", "MultiPolygon"]]],
        ["==", ["get", "market_polygon_displayable"], true],
      ],
      layout: {
        visibility: currentMarketListingsVisible ? "visible" : "none",
        "line-join": "round",
        "line-cap": "round",
      },
      paint: {
        "line-color": "#ffd8b7",
        "line-width": [
          "interpolate",
          ["linear"],
          ["zoom"],
          LAND_SIGNAL_MIN_ZOOM,
          6.2,
          16,
          8.4,
          18,
          10.2,
        ],
        "line-opacity": 0.42,
      },
    });
    map.addLayer({
      id: "market-listing-polygons-line",
      type: "line",
      source: "market-listings",
      minzoom: LAND_SIGNAL_MIN_ZOOM,
      filter: [
        "all",
        ["in", ["geometry-type"], ["literal", ["Polygon", "MultiPolygon"]]],
        ["==", ["get", "market_polygon_displayable"], true],
      ],
      layout: {
        visibility: currentMarketListingsVisible ? "visible" : "none",
      },
      paint: {
        "line-color": "#b13d00",
        "line-width": [
          "interpolate",
          ["linear"],
          ["zoom"],
          LAND_SIGNAL_MIN_ZOOM,
          4.4,
          16,
          6.1,
          18,
          7.9,
        ],
        "line-opacity": 1,
      },
    });
    map.addLayer({
      id: "market-listing-points",
      type: "circle",
      source: "market-listings",
      minzoom: LAND_SIGNAL_MIN_ZOOM,
      filter: ["==", ["geometry-type"], "Point"],
      layout: {
        visibility: currentMarketListingsVisible ? "visible" : "none",
      },
      paint: {
        "circle-color": "#f08a24",
        "circle-radius": [
          "interpolate",
          ["linear"],
          ["zoom"],
          LAND_SIGNAL_MIN_ZOOM,
          3.8,
          16,
          5.6,
          18,
          7.4,
        ],
        "circle-stroke-color": "#6c2e00",
        "circle-stroke-width": 1.4,
        "circle-opacity": 0.96,
      },
    });
  }

  function buildFacilityCategoryColorExpression() {
    const expression = ["match", ["get", "category_code"]];
    Object.entries(FACILITY_CATEGORY_COLORS).forEach(([code, color]) => {
      expression.push(code, color);
    });
    expression.push("#9aa0a8");
    return expression;
  }

  function buildScenarioScoreColorExpression() {
    return [
      "interpolate",
      ["linear"],
      ["coalesce", ["to-number", ["get", "scenario_score"]], 0],
      0, "#ef6f51",
      35, "#f39a4a",
      50, "#f5c451",
      65, "#9fd66f",
      80, "#48c78e",
      100, "#1f9d68",
    ];
  }

  function buildParcelUseCategoryColorExpression() {
    return [
      "match",
      ["coalesce", ["get", "land_use_category"], ["get", "parcel_use_label"], "mixed_use"],
      "industrial",
      PARCEL_USE_CATEGORY_COLORS.industrial,
      "retail",
      PARCEL_USE_CATEGORY_COLORS.retail,
      "office",
      PARCEL_USE_CATEGORY_COLORS.office,
      "residential_detached",
      PARCEL_USE_CATEGORY_COLORS.residential_detached,
      "residential_apartment",
      PARCEL_USE_CATEGORY_COLORS.residential_apartment,
      "residential",
      PARCEL_USE_CATEGORY_COLORS.residential,
      "mixed_use",
      PARCEL_USE_CATEGORY_COLORS.mixed_use,
      "rgba(0, 0, 0, 0)",
    ];
  }

  function addFacilitiesLayers() {
    if (map.getSource("facilities-overlay")) return;

    const categoryColorExpression = buildFacilityCategoryColorExpression();
    const scenarioColorExpression = buildScenarioScoreColorExpression();

    map.addSource("facilities-overlay", {
      type: "geojson",
      data: createEmptyFeatureCollection(),
    });
    map.addLayer({
      id: "facilities-polygons-fill",
      type: "fill",
      source: "facilities-overlay",
      minzoom: FACILITY_MIN_ZOOM,
      filter: ["==", ["geometry-type"], "Polygon"],
      layout: {
        visibility: currentFacilitiesVisible ? "visible" : "none",
      },
      paint: {
        "fill-color": categoryColorExpression,
        "fill-opacity": 0.16,
      },
    });
    map.addLayer({
      id: "facilities-polygons-line",
      type: "line",
      source: "facilities-overlay",
      minzoom: FACILITY_MIN_ZOOM,
      filter: ["==", ["geometry-type"], "Polygon"],
      layout: {
        visibility: currentFacilitiesVisible ? "visible" : "none",
      },
      paint: {
        "line-color": categoryColorExpression,
        "line-width": 1.4,
        "line-opacity": 0.96,
      },
    });
    map.addLayer({
      id: "facilities-points",
      type: "circle",
      source: "facilities-overlay",
      minzoom: FACILITY_MIN_ZOOM,
      filter: ["==", ["geometry-type"], "Point"],
      layout: {
        visibility: currentFacilitiesVisible ? "visible" : "none",
      },
      paint: {
        "circle-color": categoryColorExpression,
        "circle-radius": [
          "interpolate",
          ["linear"],
          ["zoom"],
          FACILITY_MIN_ZOOM,
          4,
          16,
          6,
          18,
          7.5,
        ],
        "circle-stroke-color": "#11161d",
        "circle-stroke-width": 1,
        "circle-opacity": 0.9,
      },
    });
    map.addLayer({
      id: "facilities-label",
      type: "symbol",
      source: "facilities-overlay",
      minzoom: Math.max(FACILITY_MIN_ZOOM + 2, 14),
      filter: ["all", ["==", ["geometry-type"], "Point"], ["!=", ["coalesce", ["get", "name"], ""], ""]],
      layout: {
        visibility: currentFacilitiesVisible ? "visible" : "none",
        "text-field": ["coalesce", ["get", "name"], ["get", "subtype"], ["get", "category_code"]],
        "text-font": ["Noto Sans Regular"],
        "text-size": 10,
        "text-offset": [0, 1],
      },
      paint: {
        "text-color": "#f5efe7",
        "text-halo-color": "#11161d",
        "text-halo-width": 1,
      },
    });

    const parcelUseColorExpression = buildParcelUseCategoryColorExpression();

    map.addSource("parcel-use-parcels", {
      type: "geojson",
      data: createEmptyFeatureCollection(),
    });
    map.addLayer({
      id: "parcel-use-parcels-fill",
      type: "fill",
      source: "parcel-use-parcels",
      minzoom: FACILITY_MIN_ZOOM,
      filter: ["==", ["geometry-type"], "Polygon"],
      layout: {
        visibility: "none",
      },
      paint: {
        "fill-color": parcelUseColorExpression,
        "fill-opacity": 0.62,
      },
    });
    map.addLayer({
      id: "parcel-use-parcels-line",
      type: "line",
      source: "parcel-use-parcels",
      minzoom: FACILITY_MIN_ZOOM,
      filter: ["==", ["geometry-type"], "Polygon"],
      layout: {
        visibility: "none",
      },
      paint: {
        "line-color": parcelUseColorExpression,
        "line-width": 0.85,
        "line-opacity": 0.94,
      },
    });

    map.addSource("scenario-score-parcels", {
      type: "geojson",
      data: createEmptyFeatureCollection(),
    });
    map.addLayer({
      id: "scenario-score-fill",
      type: "fill",
      source: "scenario-score-parcels",
      minzoom: FACILITY_SCENARIO_MIN_ZOOM,
      filter: ["==", ["geometry-type"], "Polygon"],
      layout: {
        visibility: currentScenarioScoreMode !== "none" ? "visible" : "none",
      },
      paint: {
        "fill-color": scenarioColorExpression,
        "fill-opacity": 0.18,
      },
    });
    map.addLayer({
      id: "scenario-score-line",
      type: "line",
      source: "scenario-score-parcels",
      minzoom: FACILITY_SCENARIO_MIN_ZOOM,
      filter: ["==", ["geometry-type"], "Polygon"],
      layout: {
        visibility: currentScenarioScoreMode !== "none" ? "visible" : "none",
      },
      paint: {
        "line-color": scenarioColorExpression,
        "line-width": 1.5,
        "line-opacity": 0.9,
      },
    });
  }

  function updateFacilitiesLayerVisibility() {
    const facilitiesVisible = shouldShowFacilitiesByMode();
    const isLandUseMode = currentMapViewMode === "land_use";
    const showFacilityPolygons = facilitiesVisible && !isLandUseMode;
    const showFacilityPointsAndLabels = facilitiesVisible && !isLandUseMode;
    const showLandUseGrid = facilitiesVisible && isLandUseMode;
    [
      ["facilities-polygons-fill", showFacilityPolygons],
      ["facilities-polygons-line", showFacilityPolygons],
      ["facilities-points", showFacilityPointsAndLabels],
      ["facilities-label", showFacilityPointsAndLabels],
      ["parcel-use-parcels-fill", showLandUseGrid],
      ["parcel-use-parcels-line", showLandUseGrid],
      ["scenario-score-fill", shouldShowScenarioOverlayByMode()],
      ["scenario-score-line", shouldShowScenarioOverlayByMode()],
    ].forEach(([layerId, visible]) => {
      if (map.getLayer(layerId)) {
        map.setLayoutProperty(layerId, "visibility", visible ? "visible" : "none");
      }
    });
  }

  function updateParcelLayerVisibility() {
    const parcelVisible = isParcelViewMode();
    const landUseMode = currentMapViewMode === "land_use";
    config.regions.forEach((region) => {
      const regionVisible = parcelVisible && (!activeRegion || activeRegion.slug === region.slug);
      [getParcelFillLayerId(region), getParcelLineLayerId(region)].forEach((layerId) => {
        if (map.getLayer(layerId)) {
          map.setLayoutProperty(layerId, "visibility", regionVisible ? "visible" : "none");
        }
      });
      const warmLayerId = getParcelWarmLayerId(region);
      if (map.getLayer(warmLayerId)) {
        const warmVisible = landUseMode && (!activeRegion || activeRegion.slug === region.slug);
        map.setLayoutProperty(warmLayerId, "visibility", warmVisible ? "visible" : "none");
      }
    });
    [
      "fallback-parcels-fill",
      "fallback-parcels-line",
      "compared-parcel-fill",
      "compared-parcel-line",
      "selected-parcel-fill",
      "selected-parcel-line",
    ].forEach((layerId) => {
      if (map.getLayer(layerId)) {
        map.setLayoutProperty(layerId, "visibility", parcelVisible ? "visible" : "none");
      }
    });
  }

  function updatePoiLayerVisibility() {
    const poiAllowed = shouldShowPoiByMode();
    ["poi-points-clusters", "poi-points-count", "poi-points", "poi-points-label"].forEach((layerId) => {
      if (map.getLayer(layerId)) {
        map.setLayoutProperty(layerId, "visibility", poiAllowed && currentPoiPointsVisible ? "visible" : "none");
      }
    });
    if (map.getLayer("poi-lines")) {
      map.setLayoutProperty("poi-lines", "visibility", poiAllowed && currentPoiLinesVisible ? "visible" : "none");
    }
  }

  function updateLandIntelligenceLayerVisibility() {
    const layerAllowed = isParcelViewMode();
    const historyMode = currentHistoricSalesVisible;
    const showOverviewLayers = layerAllowed && (currentOfficialSaleVisible || currentHistoricSalesVisible || currentMarketListingsVisible || currentBrownfieldVisible);
    const showOfficialLayers = layerAllowed && currentOfficialSaleVisible && !historyMode;
    const showHistoryLayers = layerAllowed && currentHistoricSalesVisible;
    const showBrownfieldLayers = layerAllowed && currentBrownfieldVisible && !historyMode;
    const showMarketLayers = layerAllowed && currentMarketListingsVisible && !historyMode;
    [
      ["sale-ready-overview-clusters", showOverviewLayers],
      ["sale-ready-overview-count", showOverviewLayers],
      ["sale-ready-overview-halo", showOverviewLayers],
      ["sale-ready-overview-point", showOverviewLayers],
      ["official-sale-parcel-fill", showOfficialLayers],
      ["official-sale-parcel-outline-halo", showOfficialLayers],
      ["official-sale-parcel-line", showOfficialLayers],
      ["official-sale-parcel-line-top", showOfficialLayers],
      ["official-sale-parcel-label", showOfficialLayers],
      ["official-sale-footprint-fill", showOfficialLayers],
      ["official-sale-footprint-line", showOfficialLayers],
      ["official-sale-footprint-label", showOfficialLayers],
      ["historic-sale-parcel-fill", showHistoryLayers],
      ["historic-sale-parcel-outline-halo", showHistoryLayers],
      ["historic-sale-parcel-line", showHistoryLayers],
      ["historic-sale-parcel-label", showHistoryLayers],
      ["brownfield-polygons-fill", showBrownfieldLayers],
      ["brownfield-polygons-line", showBrownfieldLayers],
      ["brownfield-points", showBrownfieldLayers],
      ["market-listing-polygons-fill", showMarketLayers],
      ["market-listing-polygons-outline-halo", showMarketLayers],
      ["market-listing-polygons-line", showMarketLayers],
      ["market-listing-points", showMarketLayers],
    ].forEach(([layerId, visible]) => {
      if (map.getLayer(layerId)) {
        map.setLayoutProperty(layerId, "visibility", visible ? "visible" : "none");
      }
    });
  }

  function applyMapViewMode(forceRefresh = true) {
    updateParcelLayerVisibility();
    updatePoiLayerVisibility();
    updateFacilitiesLayerVisibility();
    updateLandIntelligenceLayerVisibility();
    updateTopographyLayerVisibility();
    updateFutureGrowthLayerVisibility();
    if (showFacilitiesOverlayEl) {
      if (currentMapViewMode === "land_use") {
        showFacilitiesOverlayEl.checked = true;
        showFacilitiesOverlayEl.disabled = true;
      } else {
        showFacilitiesOverlayEl.checked = currentFacilitiesVisible;
        showFacilitiesOverlayEl.disabled = false;
      }
    }
    if (mapViewModeEl) {
      mapViewModeEl.value = currentMapViewMode;
    }
    updateMapModeControlState();
    if (showPoiPointsEl) {
      showPoiPointsEl.disabled = !isParcelViewMode();
    }
    if (showPoiLinesEl) {
      showPoiLinesEl.disabled = !isParcelViewMode();
    }
    updateFacilitiesStatus();
    updateNearestSaleJumpButton();
    if (forceRefresh) {
      scheduleParcelFallbackRefresh(true);
      scheduleFacilitiesRefresh(true);
      scheduleLandIntelligenceRefresh(true);
      scheduleFutureGrowthRefresh(true);
      scheduleGlobalOverviewRefresh(true);
    }
  }

  function scheduleFacilitiesRefresh(force = false) {
    window.clearTimeout(facilitiesFetchTimer);
    facilitiesFetchTimer = window.setTimeout(() => {
      void syncFacilitiesOverlays(force);
    }, force ? 80 : 320);
  }

  function clearFacilitiesOverlayState() {
    setGeoJsonSourceData("facilities-overlay", createEmptyFeatureCollection());
    facilitiesOverlayState = {
      featureCount: 0,
      lastLoadedAt: null,
      lastBBoxKey: null,
      error: null,
      features: [],
    };
  }

  function clearLandUseGridState() {
    setGeoJsonSourceData("parcel-use-parcels", createEmptyFeatureCollection());
    landUseGridState = {
      featureCount: 0,
      sourceFeatureCount: 0,
      dataSource: "api",
      truncated: false,
      lastLoadedAt: null,
      lastBBoxKey: null,
      error: null,
      features: [],
    };
  }

  function clearScenarioOverlayState() {
    setGeoJsonSourceData("scenario-score-parcels", createEmptyFeatureCollection());
    scenarioOverlayState = {
      featureCount: 0,
      requestedCount: 0,
      lastLoadedAt: null,
      lastBBoxKey: null,
      error: null,
      features: [],
    };
  }

  function clearParcelFallbackState() {
    setGeoJsonSourceData("fallback-parcels", createEmptyFeatureCollection());
    parcelFallbackState = {
      featureCount: 0,
      lastLoadedAt: parcelFallbackState.lastLoadedAt,
      lastBBoxKey: null,
      error: null,
    };
  }

  async function syncParcelFallbackParcels(force = false) {
    if (!map || !landIntelligenceApiBaseUrl) {
      parcelFallbackState = {
        ...parcelFallbackState,
        error: landIntelligenceApiBaseUrl ? null : "Parcel fallback API bagli degil.",
      };
      return;
    }
    if (!PARCEL_FALLBACK_ENABLED) {
      clearParcelFallbackState();
      return;
    }
    if (!isParcelViewMode() || map.getZoom() < config.parcelMinZoom) {
      clearParcelFallbackState();
      return;
    }
    const bbox = mapBoundsToBboxString();
    if (!bbox) return;
    const key = `${bbox}|${Math.floor(map.getZoom() * 10)}`;
    if (!force && parcelFallbackState.lastBBoxKey === key) {
      return;
    }
    const requestId = ++parcelFallbackRequestId;
    try {
      const params = new URLSearchParams({
        bbox,
        exclude_demo: "true",
        limit: String(PARCEL_FALLBACK_FETCH_LIMIT),
      });
      const payloadResponse = await fetchJsonWithTimeout(`${landIntelligenceApiBaseUrl}/map/parcels?${params.toString()}`, {
        label: "Yerel parcel fallback",
        fallback: createEmptyFeatureCollection,
      });
      if (requestId !== parcelFallbackRequestId) return;
      const payload = payloadResponse.data || createEmptyFeatureCollection();
      setGeoJsonSourceData("fallback-parcels", payload);
      parcelFallbackState = {
        featureCount: (payload.features || []).length,
        lastLoadedAt: new Date().toISOString(),
        lastBBoxKey: key,
        error: payloadResponse.error || null,
      };
    } catch (error) {
      if (requestId !== parcelFallbackRequestId) return;
      parcelFallbackState = {
        ...parcelFallbackState,
        lastBBoxKey: key,
        error: error?.message || "Yerel parcel fallback yuklenemedi.",
      };
    }
  }

  function scheduleParcelFallbackRefresh(force = false) {
    if (!PARCEL_FALLBACK_ENABLED) return;
    window.clearTimeout(parcelFallbackFetchTimer);
    parcelFallbackFetchTimer = window.setTimeout(() => {
      void syncParcelFallbackParcels(force);
    }, force ? 80 : 260);
  }

  function bboxAroundCenter(centerPoint, halfSpanDeg) {
    if (!centerPoint || !Number.isFinite(centerPoint.lng) || !Number.isFinite(centerPoint.lat) || !Number.isFinite(halfSpanDeg) || halfSpanDeg <= 0) {
      return null;
    }
    const west = Math.max(-180, centerPoint.lng - halfSpanDeg);
    const east = Math.min(180, centerPoint.lng + halfSpanDeg);
    const south = Math.max(-90, centerPoint.lat - halfSpanDeg);
    const north = Math.min(90, centerPoint.lat + halfSpanDeg);
    return [west, south, east, north].map((value) => Number(value).toFixed(6)).join(",");
  }

  async function fetchNearestManagedParcel(centerPoint) {
    if (!centerPoint || !landIntelligenceApiBaseUrl) return null;
    const spans = [0.004, 0.008, 0.016, 0.03, 0.06, 0.12, 0.25, 0.5];
    for (const span of spans) {
      const bbox = bboxAroundCenter(centerPoint, span);
      if (!bbox) continue;
      const params = new URLSearchParams({
        bbox,
        limit: "180",
        exclude_demo: "true",
      });
      const payloadResponse = await fetchJsonWithTimeout(`${landIntelligenceApiBaseUrl}/map/parcels?${params.toString()}`, {
        label: "Yakin parcel arama",
        fallback: createEmptyFeatureCollection,
      });
      const payload = payloadResponse.data || createEmptyFeatureCollection();
      const nearest = (payload?.features || [])
        .map((feature) => {
          const props = feature?.properties || {};
          const parcelId = Number(props.parcel_id);
          if (!Number.isFinite(parcelId)) return null;
          const featureCenter = geometryCenterLngLat(feature?.geometry);
          if (!featureCenter) return null;
          return {
            parcel_id: parcelId,
            parcel_ref: props.parcel_ref || null,
            inspire_id: props.inspire_id || null,
            match_mode: "nearest_bbox",
            match_distance_m: Math.round(haversineDistanceMeters(centerPoint, featureCenter)),
          };
        })
        .filter(Boolean)
        .sort((left, right) => left.match_distance_m - right.match_distance_m)[0];
      if (nearest) {
        return nearest;
      }
    }
    return null;
  }

  async function syncFacilitiesOverlays(force = false) {
    if (!map || !landIntelligenceApiBaseUrl) {
      facilitiesOverlayState.error = landIntelligenceApiBaseUrl ? null : "Facilities API bagli degil.";
      updateFacilitiesStatus();
      return;
    }

    const bbox = mapBoundsToBboxString();
    if (!bbox) return;

    const zoom = map.getZoom();
    const facilitiesVisible = shouldShowFacilitiesByMode();
    const isLandUseMode = currentMapViewMode === "land_use";
    const scenarioVisible = shouldShowScenarioOverlayByMode();
    if (!facilitiesVisible || zoom < FACILITY_MIN_ZOOM) {
      clearFacilitiesOverlayState();
      clearLandUseGridState();
    } else {
      const facilitiesKey = `${bbox}|${currentFacilitiesCategory}|${currentMapViewMode}|${Math.floor(zoom * 10)}`;
      if (force || facilitiesOverlayState.lastBBoxKey !== facilitiesKey) {
        const requestId = ++facilityRequestId;
        try {
          if (isLandUseMode) {
            const maxFeatures = Math.max(PARCEL_USE_VIEW_BATCH_LIMIT, PARCEL_USE_VIEW_FETCH_LIMIT);
            const allParcelFeatures = [];
            let offset = 0;
            let truncated = false;
            while (allParcelFeatures.length < maxFeatures) {
              const remaining = maxFeatures - allParcelFeatures.length;
              const batchLimit = Math.max(1, Math.min(PARCEL_USE_VIEW_BATCH_LIMIT, remaining));
              const params = new URLSearchParams({
                bbox,
                exclude_demo: "true",
                limit: String(batchLimit),
                offset: String(offset),
              });
              const payloadResponse = await fetchJsonWithTimeout(`${landIntelligenceApiBaseUrl}/map/parcels?${params.toString()}`, {
                label: "Arazi kullanim parcelleri",
                fallback: createEmptyFeatureCollection,
              });
              const payload = payloadResponse.data || createEmptyFeatureCollection();
              const batch = Array.isArray(payload?.features) ? payload.features : [];
              if (batch.length === 0) {
                break;
              }
              allParcelFeatures.push(...batch);
              if (batch.length < batchLimit) {
                break;
              }
              offset += batchLimit;
              if (allParcelFeatures.length >= maxFeatures) {
                truncated = true;
                break;
              }
            }
            if (requestId === facilityRequestId) {
              const apiParcelUseFeatures = allParcelFeatures
                .map((feature) => {
                  const geometryType = String(feature?.geometry?.type || "").toLowerCase();
                  if (geometryType !== "polygon" && geometryType !== "multipolygon") {
                    return null;
                  }
                  const props = feature?.properties || {};
                  const landUseCategory = resolveParcelUseCategoryFromProperties(props, feature);
                  return {
                    ...feature,
                    properties: {
                      ...props,
                      land_use_category: landUseCategory,
                      category_code: landUseCategory,
                    },
                  };
                })
                .filter(Boolean);
              const fallbackParcelUseFeatures = apiParcelUseFeatures.length > 0
                ? []
                : buildParcelUseFeaturesFromParcelTileSources(bbox, maxFeatures);
              const parcelUseFeatures = apiParcelUseFeatures.length > 0
                ? apiParcelUseFeatures
                : fallbackParcelUseFeatures;
              setGeoJsonSourceData("parcel-use-parcels", {
                type: "FeatureCollection",
                features: parcelUseFeatures,
              });
              setGeoJsonSourceData("facilities-overlay", createEmptyFeatureCollection());
              landUseGridState = {
                featureCount: parcelUseFeatures.length,
                sourceFeatureCount: parcelUseFeatures.length,
                dataSource: apiParcelUseFeatures.length > 0 ? "api" : "parcel_tiles_fallback",
                truncated,
                lastLoadedAt: new Date().toISOString(),
                lastBBoxKey: facilitiesKey,
                error: null,
                features: parcelUseFeatures,
              };
              facilitiesOverlayState = {
                featureCount: 0,
                lastLoadedAt: new Date().toISOString(),
                lastBBoxKey: facilitiesKey,
                error: null,
                features: [],
              };
            }
          } else {
            const facilitiesFetchLimit = FACILITY_FETCH_LIMIT;
            const params = new URLSearchParams({
              format: "geojson",
              canonical: "true",
              bbox,
              limit: String(facilitiesFetchLimit),
            });
            if (currentFacilitiesCategory !== "all") {
              params.set("category", currentFacilitiesCategory);
            }
            const payloadResponse = await fetchJsonWithTimeout(`${landIntelligenceApiBaseUrl}/facilities?${params.toString()}`, {
              label: "Facilities overlay",
              fallback: createEmptyFeatureCollection,
            });
            const payload = payloadResponse.data || createEmptyFeatureCollection();
            if (requestId === facilityRequestId) {
              setGeoJsonSourceData("facilities-overlay", payload);
              clearLandUseGridState();
              facilitiesOverlayState = {
                featureCount: (payload.features || []).length,
                lastLoadedAt: new Date().toISOString(),
                lastBBoxKey: facilitiesKey,
                error: null,
                features: payload.features || [],
              };
            }
          }
        } catch (error) {
          if (isLandUseMode) {
            // Land-use modunda once parcel tile fallback dene; gecici hata nedeniyle harita tamamen bos kalmasin.
            const fallbackParcelUseFeatures = buildParcelUseFeaturesFromParcelTileSources(bbox, PARCEL_USE_VIEW_FETCH_LIMIT);
            if (fallbackParcelUseFeatures.length) {
              setGeoJsonSourceData("parcel-use-parcels", {
                type: "FeatureCollection",
                features: fallbackParcelUseFeatures,
              });
            }
            landUseGridState = {
              ...landUseGridState,
              featureCount: fallbackParcelUseFeatures.length || landUseGridState.featureCount,
              sourceFeatureCount: fallbackParcelUseFeatures.length || landUseGridState.sourceFeatureCount,
              dataSource: fallbackParcelUseFeatures.length ? "parcel_tiles_fallback" : landUseGridState.dataSource,
              features: fallbackParcelUseFeatures.length ? fallbackParcelUseFeatures : landUseGridState.features,
              lastBBoxKey: facilitiesKey,
              error: error?.message || "Arazi kullanim katmani yuklenemedi.",
            };
            facilitiesOverlayState = {
              ...facilitiesOverlayState,
              lastBBoxKey: facilitiesKey,
              error: error?.message || "Arazi kullanim katmani yuklenemedi.",
            };
          } else {
            setGeoJsonSourceData("facilities-overlay", createEmptyFeatureCollection());
            clearLandUseGridState();
            facilitiesOverlayState = {
              featureCount: 0,
              lastLoadedAt: facilitiesOverlayState.lastLoadedAt,
              lastBBoxKey: facilitiesKey,
              error: error?.message || "Facilities overlay yuklenemedi.",
              features: [],
            };
          }
        }
      }
    }

    if (!scenarioVisible || zoom < FACILITY_SCENARIO_MIN_ZOOM) {
      clearScenarioOverlayState();
      updateFacilitiesStatus();
      return;
    }

    const scenarioKey = `${bbox}|${currentScenarioScoreMode}|${Math.floor(zoom * 10)}`;
    if (!force && scenarioOverlayState.lastBBoxKey === scenarioKey) {
      updateFacilitiesStatus();
      return;
    }

    const requestId = ++scenarioParcelRequestId;
    try {
      const params = new URLSearchParams({
        bbox,
        limit: String(Math.min(FACILITY_FETCH_LIMIT, 1200)),
        exclude_demo: "true",
        fast_mode: "true",
      });
      const payloadResponse = await fetchJsonWithTimeout(`${landIntelligenceApiBaseUrl}/map/parcels?${params.toString()}`, {
        label: "Senaryo parcelleri",
        fallback: createEmptyFeatureCollection,
      });
      const payload = payloadResponse.data || createEmptyFeatureCollection();
      if (requestId !== scenarioParcelRequestId) {
        return;
      }
      const filteredFeatures = (payload.features || [])
        .filter((feature) => {
          const scoreValue = feature?.properties?.scenario_scores?.[currentScenarioScoreMode];
          return Number.isFinite(Number(scoreValue));
        })
        .map((feature) => ({
          ...feature,
          properties: {
            ...(feature.properties || {}),
            scenario_mode: currentScenarioScoreMode,
            scenario_score: Number(feature?.properties?.scenario_scores?.[currentScenarioScoreMode]),
          },
        }));
      setGeoJsonSourceData("scenario-score-parcels", {
        type: "FeatureCollection",
        features: filteredFeatures,
      });
      scenarioOverlayState = {
        featureCount: filteredFeatures.length,
        requestedCount: (payload.features || []).length,
        lastLoadedAt: new Date().toISOString(),
        lastBBoxKey: scenarioKey,
        error: null,
        features: filteredFeatures,
      };
    } catch (error) {
      setGeoJsonSourceData("scenario-score-parcels", createEmptyFeatureCollection());
      scenarioOverlayState = {
        featureCount: 0,
        requestedCount: 0,
        lastLoadedAt: scenarioOverlayState.lastLoadedAt,
        lastBBoxKey: scenarioKey,
        error: error?.message || "Senaryo score overlay yuklenemedi.",
        features: [],
      };
    }
    updateFacilitiesStatus();
  }

  async function refreshLandIntelligenceMapLayers(force = false) {
    if (!map) return;
    if (!landIntelligenceApiBaseUrl) {
      landOverlayState.error = "Land Intelligence API bagli degil.";
      updateLandSourceStatusPanel();
      return;
    }
    if (!activeRegion || !isParcelViewMode() || map.getZoom() < LAND_SIGNAL_MIN_ZOOM) {
      setGeoJsonSourceData("official-sale-parcels", createEmptyFeatureCollection());
      setGeoJsonSourceData("historic-sale-parcels", createEmptyFeatureCollection());
      setGeoJsonSourceData("official-sale-footprints", createEmptyFeatureCollection());
      setGeoJsonSourceData("brownfield-sites", createEmptyFeatureCollection());
      setGeoJsonSourceData("market-listings", createEmptyFeatureCollection());
      landOverlayState = {
        ...landOverlayState,
        officialSaleCount: 0,
        historicSaleCount: 0,
        brownfieldCount: 0,
        marketListingCount: 0,
        officialSaleFeatures: [],
        historicSaleFeatures: [],
        brownfieldFeatures: [],
        marketListingFeatures: [],
        officialSaleFootprintCount: 0,
        officialSaleFootprintFeatures: [],
        error: null,
      };
      updateLandSourceStatusPanel();
      return;
    }

    const overlayQuery = getLandOverlayQueryContext();
    const bbox = overlayQuery.bbox;
    const cacheBbox = overlayQuery.cacheBbox || bbox;
    const bboxKey = `${activeRegion.slug}:${overlayQuery.mode}:${cacheBbox}:confidence=${landOverlayFilters.minConfidence}:brownfield=${landOverlayFilters.brownfieldSource}:listing=${landOverlayFilters.listingStatus}:quick=${landOverlayFilters.saleReadyQuickFilter}:review=${landOverlayFilters.reviewOnly}`;
    if (!force && landOverlayState.lastBBoxKey === bboxKey) {
      updateLandSourceStatusPanel();
      return;
    }

    const requestId = ++landOverlayRequestId;
    const shouldFetchOfficial = currentOfficialSaleVisible;
    const shouldFetchHistoric = currentHistoricSalesVisible;
    const shouldFetchFootprints = shouldFetchOfficial && map.getZoom() >= Math.max(LAND_SIGNAL_MIN_ZOOM + 1, Number(config.parcelMinZoom || LAND_SIGNAL_MIN_ZOOM));
    const shouldFetchBrownfield = currentBrownfieldVisible;
    const shouldFetchMarketListings = currentMarketListingsVisible;
    const effectiveLimit = String(LAND_SIGNAL_FETCH_LIMIT);
    const brownfieldLimit = String(Math.max(LAND_SIGNAL_FETCH_LIMIT, LAND_BROWNFIELD_FETCH_LIMIT));

    try {
      const officialSaleParams = appendLandOverlayFilterParams(
        new URLSearchParams({
          sale_ready_signal: "true",
          bbox,
          limit: effectiveLimit,
          fast_mode: "true",
        })
      );
      const historicSaleParams = appendLandOverlayFilterParams(
        new URLSearchParams({
          history_signal: "true",
          bbox,
          limit: effectiveLimit,
          fast_mode: "true",
        })
      );
      const officialSaleFootprintParams = appendLandOverlayFilterParams(
        new URLSearchParams({
          bbox,
          limit: effectiveLimit,
        }),
        { listingStatus: true }
      );
      const brownfieldParams = appendLandOverlayFilterParams(
        new URLSearchParams({
          brownfield_signal: "true",
          bbox,
          limit: brownfieldLimit,
          fast_mode: "true",
        }),
        { brownfieldSource: true }
      );
      const [officialSaleResponse, historicSalesResponse, officialSaleFootprintsResponse, brownfieldResponse] = await Promise.all([
        shouldFetchOfficial
          ? fetchJsonWithTimeout(`${landIntelligenceApiBaseUrl}/map/parcels?${officialSaleParams.toString()}`, {
              label: "Official sale parcelleri",
              fallback: createEmptyFeatureCollection,
              timeoutMs: LAND_OVERLAY_TIMEOUT_MS,
              backoffGroup: "land-official-parcels",
            })
          : Promise.resolve({ ok: true, data: createEmptyFeatureCollection(), error: null }),
        shouldFetchHistoric
          ? fetchJsonWithTimeout(`${landIntelligenceApiBaseUrl}/map/parcels?${historicSaleParams.toString()}`, {
              label: "Gecmis satis parcelleri",
              fallback: createEmptyFeatureCollection,
              timeoutMs: LAND_OVERLAY_TIMEOUT_MS,
              backoffGroup: "land-history-parcels",
            })
          : Promise.resolve({ ok: true, data: createEmptyFeatureCollection(), error: null }),
        shouldFetchFootprints
          ? fetchJsonWithTimeout(`${landIntelligenceApiBaseUrl}/map/listings?${officialSaleFootprintParams.toString()}`, {
              label: "Satis footprint katmani",
              fallback: createEmptyFeatureCollection,
              timeoutMs: LAND_OVERLAY_TIMEOUT_MS,
              backoffGroup: "land-official-footprints",
            })
          : Promise.resolve({ ok: true, data: createEmptyFeatureCollection(), error: null }),
        shouldFetchBrownfield
          ? fetchJsonWithTimeout(`${landIntelligenceApiBaseUrl}/map/parcels?${brownfieldParams.toString()}`, {
              label: "Brownfield parcelleri",
              fallback: createEmptyFeatureCollection,
              timeoutMs: LAND_OVERLAY_TIMEOUT_MS,
              backoffGroup: "land-brownfield-parcels",
            })
          : Promise.resolve({ ok: true, data: createEmptyFeatureCollection(), error: null }),
      ]);
      if (requestId !== landOverlayRequestId) return;
      let marketSourceError = null;
      let marketListings = createEmptyFeatureCollection();
      if (shouldFetchMarketListings) {
        try {
          const allMarketListingFeatures = await fetchGlobalSaleReadyFeatures(false);
          if (requestId !== landOverlayRequestId) return;
          const bboxObj = parseBboxString(bbox);
          const visibleMarketFeatures = bboxObj
            ? (allMarketListingFeatures || []).filter((feature) => getFeatureBoundsIntersectsBbox(feature, bboxObj))
            : (allMarketListingFeatures || []);
          marketListings = {
            type: "FeatureCollection",
            features: visibleMarketFeatures,
          };
        } catch (error) {
          marketSourceError = error?.message || "Kullanici satis ilanlari kaynak geometrisi yuklenemedi.";
          marketListings = createEmptyFeatureCollection();
        }
      }
      const requestErrors = [
        officialSaleResponse.error,
        historicSalesResponse.error,
        officialSaleFootprintsResponse.error,
        brownfieldResponse.error,
        marketSourceError,
      ].filter(Boolean);

      const officialSale = officialSaleResponse.data || createEmptyFeatureCollection();
      const historicSales = historicSalesResponse.data || createEmptyFeatureCollection();
      const officialSaleFootprints = officialSaleFootprintsResponse.data || createEmptyFeatureCollection();
      const brownfield = brownfieldResponse.data || createEmptyFeatureCollection();

      let filteredOfficialSale = {
        type: "FeatureCollection",
        features: (filterLandOverlayFeatures(officialSale).features || []).filter((feature) => matchesSaleReadyFeatureFilters(feature)),
      };
      let filteredHistoricSales = filterLandOverlayFeatures(historicSales);
      if ((shouldFetchOfficial && (filteredOfficialSale.features || []).length === 0) || (shouldFetchHistoric && (filteredHistoricSales.features || []).length === 0)) {
        const combinedSalesFeatures = await fetchCombinedSalesLayerFeatures(false);
        if (requestId !== landOverlayRequestId) return;
        const combinedInView = filterSalesLayerFeaturesByBbox(combinedSalesFeatures, bbox);
        if (shouldFetchOfficial && (filteredOfficialSale.features || []).length === 0) {
          filteredOfficialSale = {
            type: "FeatureCollection",
            features: combinedInView
              .filter((feature) => feature?.properties?.external_market_evidence_available)
              .filter((feature) => matchesSaleReadyFeatureFilters(feature)),
          };
        }
        if (shouldFetchHistoric && (filteredHistoricSales.features || []).length === 0) {
          filteredHistoricSales = {
            type: "FeatureCollection",
            features: combinedInView.filter((feature) => feature?.properties?.sales_history_available),
          };
        }
      }
      const visibleSaleParcelKeys = new Set();
      (filteredOfficialSale.features || []).forEach((feature) => {
        const parcelRef = getParcelRef(feature);
        const inspireId = feature?.properties?.inspire_id || feature?.properties?.INSPIRE_ID || null;
        if (parcelRef) visibleSaleParcelKeys.add(String(parcelRef));
        if (inspireId) visibleSaleParcelKeys.add(String(inspireId));
      });
      const filteredOfficialSaleFootprints = {
        type: "FeatureCollection",
        features: (filterLandOverlayFeatures(officialSaleFootprints).features || []).filter((feature) => {
          const matchedParcelRef = getMatchedParcelRefFromFeature(feature);
          const matchedInspireId = getMatchedInspireIdFromFeature(feature);
          return (
            (matchedParcelRef && visibleSaleParcelKeys.has(String(matchedParcelRef))) ||
            (matchedInspireId && visibleSaleParcelKeys.has(String(matchedInspireId)))
          );
        }),
      };
      let filteredBrownfield = filterLandOverlayFeatures(brownfield);
      if (shouldFetchBrownfield && (filteredBrownfield.features || []).length === 0) {
        const brownfieldSiteParams = appendLandOverlayFilterParams(
          new URLSearchParams({
            bbox,
            limit: brownfieldLimit,
          }),
          { brownfieldSource: true }
        );
        const brownfieldSiteResponse = await fetchJsonWithTimeout(`${landIntelligenceApiBaseUrl}/map/brownfield?${brownfieldSiteParams.toString()}`, {
          label: "Brownfield kaynak sahalari",
          fallback: createEmptyFeatureCollection,
          timeoutMs: LAND_OVERLAY_TIMEOUT_MS,
          backoffGroup: "land-brownfield-sites",
        });
        const brownfieldSitePayload = brownfieldSiteResponse.data || createEmptyFeatureCollection();
        if (requestId !== landOverlayRequestId) return;
        if ((brownfieldSitePayload.features || []).length > 0) {
          filteredBrownfield = {
            type: "FeatureCollection",
            features: (brownfieldSitePayload.features || []).map((feature) => ({
              ...feature,
              properties: {
                ...(feature?.properties || {}),
                brownfield_signal: true,
                brownfield_fallback_source: true,
              },
            })),
          };
        }
      }
      const filteredMarketListings = filterLandOverlayFeatures({
        type: "FeatureCollection",
        features: (marketListings.features || []).map((feature) => {
          const props = feature?.properties || {};
          const geometryQuality = classifyMarketListingGeometryQuality(feature);
          const rectangularFeed = geometryQuality.geometry_quality_class === "rectangular_feed_bbox_like";
          const sourceStatus = normalizeMarketPolygonStatus(props.source_polygon_original_site_status || "unknown_not_verified");
          const displayPolygonSource = sourceStatus === "verified_original_site"
            ? (props.display_polygon_source || "original_site_polygon")
            : sourceStatus === "derived"
              ? (props.display_polygon_source || "derived_parcel_geometry")
              : rectangularFeed
                ? "feed_bbox_polygon"
                : (props.display_polygon_source || "feed_polygon");
          const marketPolygonDisplayable = canDisplayMarketListingPolygon(feature, displayPolygonSource, sourceStatus);
          const baseNote = props.polygon_provenance_note || "";
          const rectangularNote = rectangularFeed
            ? "Feed poligonu dikdortgen/bbox benzeri; gercek parsel sekli dogrulanmadi."
            : "";
          const hiddenNote = !marketPolygonDisplayable
            ? "Bu kayit nokta olarak kalir; dogrulanmamis/dÃ¼zensiz satis poligonu gercek parsel gibi cizilmez."
            : "";
          const polygonProvenanceNote = [baseNote, rectangularNote, hiddenNote].filter(Boolean).join(" ");
          return {
            ...feature,
            properties: {
              ...props,
              portal_listing_signal: true,
              market_listing_source_geometry: props.market_listing_source_geometry ?? true,
              display_polygon_source: displayPolygonSource,
              source_polygon_original_site_status: sourceStatus,
              market_polygon_displayable: marketPolygonDisplayable,
              polygon_provenance_note: polygonProvenanceNote || "-",
              geometry_quality_class: geometryQuality.geometry_quality_class,
              geometry_quality_label: geometryQuality.geometry_quality_label,
            },
          };
        }),
      });
      setGeoJsonSourceData("official-sale-parcels", filteredOfficialSale);
      setGeoJsonSourceData("historic-sale-parcels", filteredHistoricSales);
      setGeoJsonSourceData("official-sale-footprints", filteredOfficialSaleFootprints);
      setGeoJsonSourceData("brownfield-sites", filteredBrownfield);
      setGeoJsonSourceData("market-listings", filteredMarketListings);
      landOverlayState = {
        officialSaleCount: (filteredOfficialSale.features || []).length,
        historicSaleCount: (filteredHistoricSales.features || []).length,
        brownfieldCount: (filteredBrownfield.features || []).length,
        marketListingCount: (filteredMarketListings.features || []).length,
        officialSaleFeatures: filteredOfficialSale.features || [],
        historicSaleFeatures: filteredHistoricSales.features || [],
        brownfieldFeatures: filteredBrownfield.features || [],
        marketListingFeatures: filteredMarketListings.features || [],
        officialSaleFootprintCount: (filteredOfficialSaleFootprints.features || []).length,
        officialSaleFootprintFeatures: filteredOfficialSaleFootprints.features || [],
        lastLoadedAt: new Date().toISOString(),
        error: requestErrors.length ? requestErrors.join(" | ") : null,
        lastBBoxKey: bboxKey,
        lastRegionSlug: activeRegion.slug,
      };
      if (force && currentHistoricSalesVisible) {
        const visibleHistoricCount = (filteredHistoricSales.features || []).length;
        if (visibleHistoricCount > 0) {
          showStatus(`Gecmis satis katmani acik: bu gorunumde ${visibleHistoricCount} parcel bulundu.`);
        } else {
          showStatus("Gecmis satis katmani acik, bu gorunumde kayit yok. Haritayi kaydirin veya biraz uzaklasin.", true);
        }
      }
    } catch (error) {
      if (requestId !== landOverlayRequestId) return;
      landOverlayState = {
        ...landOverlayState,
        error: error?.message || "Land Intelligence katmanlari yuklenemedi.",
        lastLoadedAt: new Date().toISOString(),
      };
    }
    updateLandSourceStatusPanel();
  }

  function scheduleLandIntelligenceRefresh(force = false) {
    window.clearTimeout(landOverlayFetchTimer);
    landOverlayFetchTimer = window.setTimeout(() => {
      refreshLandIntelligenceMapLayers(force);
    }, force ? 120 : 360);
  }

  function scheduleGlobalOverviewRefresh(force = false) {
    window.clearTimeout(globalOverviewFetchTimer);
    globalOverviewFetchTimer = window.setTimeout(() => {
      void syncGlobalSaleReadyOverview(force);
    }, force ? 120 : 420);
  }

  function bindParcelInteractions() {
    if (parcelInteractionsBound) {
      return;
    }
    parcelInteractionsBound = true;

    ["official-sale-footprint-fill", "official-sale-footprint-line"].forEach((layerId) => {
      map.on("click", layerId, async (event) => {
        const feature = (event.features || [])[0];
        if (!feature) return;
        await focusOfficialSaleFootprint(feature, event.lngLat);
      });
    });

    config.regions.forEach((region) => {
      map.on("click", getParcelFillLayerId(region), (event) => {
        if (currentMapViewMode === "land_use") return;
        if (Date.now() < parcelClickSuppressionUntil || hasOfficialSaleFootprintAtPoint(event.point)) return;
        if (currentHistoricSalesVisible) {
          const historicFeature = findHistoricSaleFeatureAtPoint(event.point);
          if (historicFeature) {
            updateSelectedParcel(historicFeature);
            openSignalPopup(historicFeature, event.lngLat, "historic_sale");
            return;
          }
        }
        const feature = (event.features || [])[0];
        if (!feature) return;
        updateSelectedParcel(feature);
        openParcelPopup(feature, event.lngLat);
      });
    });

    ["official-sale-parcel-fill", "official-sale-parcel-outline-halo", "official-sale-parcel-line", "official-sale-parcel-line-top"].forEach((layerId) => {
    map.on("click", layerId, (event) => {
        if (Date.now() < parcelClickSuppressionUntil || hasOfficialSaleFootprintAtPoint(event.point)) return;
        if (currentHistoricSalesVisible) {
          const historicFeature = findHistoricSaleFeatureAtPoint(event.point);
          if (historicFeature) {
            updateSelectedParcel(historicFeature);
            openSignalPopup(historicFeature, event.lngLat, "historic_sale");
          }
          return;
        }
        const feature = (event.features || [])[0];
        if (!feature) return;
        updateSelectedParcel(feature);
        openSignalPopup(feature, event.lngLat, "official_sale");
      });
    });

    ["fallback-parcels-fill"].forEach((layerId) => {
      map.on("click", layerId, (event) => {
        if (currentMapViewMode === "land_use") return;
        const feature = (event.features || [])[0];
        if (!feature) return;
        updateSelectedParcel(feature);
        openParcelPopup(feature, event.lngLat);
      });
    });

    ["historic-sale-parcel-fill", "historic-sale-parcel-outline-halo", "historic-sale-parcel-line"].forEach((layerId) => {
      map.on("click", layerId, (event) => {
        if (Date.now() < parcelClickSuppressionUntil || hasOfficialSaleFootprintAtPoint(event.point)) return;
        const feature = (event.features || [])[0];
        if (!feature) return;
        updateSelectedParcel(feature);
        openSignalPopup(feature, event.lngLat, "historic_sale");
      });
    });

    map.on("click", "sale-ready-overview-clusters", (event) => {
      const feature = (event.features || [])[0];
      const clusterId = feature?.properties?.cluster_id;
      if (!feature || clusterId === undefined || clusterId === null) return;
      const source = map.getSource("sale-ready-overview");
      if (!source?.getClusterExpansionZoom) return;
      source.getClusterExpansionZoom(clusterId, (error, zoom) => {
        if (error) return;
        map.easeTo({
          center: feature.geometry.coordinates,
          zoom: Math.max(zoom || LAND_SIGNAL_MIN_ZOOM, map.getZoom() + 1),
          duration: 650,
        });
      });
    });

    map.on("click", "sale-ready-overview-point", (event) => {
      const pointFeature = (event.features || [])[0];
      const featureKey = pointFeature?.properties?.sale_feature_key || null;
      const parcelId = Number(pointFeature?.properties?.parcel_id);
      const sourceFeatures = landOverlayState.globalOverviewMode === "history"
        ? (landOverlayState.globalHistoricSaleFeatures || [])
        : (landOverlayState.globalSaleReadyFeatures || []);
      const feature = featureKey
        ? findSaleFeatureByKey(featureKey, sourceFeatures)
        : sourceFeatures.find((candidate) => getFeatureParcelId(candidate) === parcelId);
      if (!feature) return;
      if (landOverlayState.globalOverviewMode === "history") {
        void focusHistoricSaleParcel(feature);
      } else {
        void focusSaleReadyFeature(feature);
      }
    });

    ["brownfield-polygons-fill", "brownfield-points"].forEach((layerId) => {
      map.on("click", layerId, (event) => {
        const feature = (event.features || [])[0];
        if (!feature) return;
        updateSelectedParcel(feature);
        openSignalPopup(feature, event.lngLat, "brownfield");
      });
    });

    [FUTURE_GROWTH_FILL_LAYER_ID, FUTURE_GROWTH_POINT_LAYER_ID].forEach((layerId) => {
      map.on("click", layerId, (event) => {
        const feature = (event.features || [])[0];
        if (!feature) return;
        updateSelectedParcel(feature);
        void openFutureGrowthParcelPopup(feature, event.lngLat);
      });
      map.on("mousemove", layerId, (event) => {
        const feature = (event.features || [])[0];
        if (!feature || !currentFutureGrowthVisible) return;
        openFutureGrowthHoverPopup(feature, event.lngLat);
      });
      map.on("mouseleave", layerId, () => {
        clearFutureGrowthHoverPopup();
      });
    });

    ["market-listing-polygons-fill", "market-listing-polygons-outline-halo", "market-listing-polygons-line", "market-listing-points"].forEach((layerId) => {
      map.on("click", layerId, (event) => {
        const feature = (event.features || [])[0];
        if (!feature) return;
        updateSelectedParcel(feature);
        openParcelPopup(feature, event.lngLat);
      });
    });

    ["facilities-polygons-fill", "facilities-polygons-line", "facilities-points"].forEach((layerId) => {
      map.on("click", layerId, (event) => {
        const feature = (event.features || [])[0];
        if (!feature) return;
        openFacilityPopup(feature, event.lngLat);
      });
    });

    ["parcel-use-parcels-fill", "parcel-use-parcels-line"].forEach((layerId) => {
      map.on("click", layerId, () => {
        if (currentMapViewMode !== "land_use") return;
        if (parcelPopup) {
          parcelPopup.remove();
          parcelPopup = null;
          activeParcelPopupState = null;
        }
        if (facilityPopup) {
          facilityPopup.remove();
          facilityPopup = null;
        }
      });
    });

    ["scenario-score-fill", "scenario-score-line"].forEach((layerId) => {
      map.on("click", layerId, (event) => {
        const feature = (event.features || [])[0];
        if (!feature) return;
        updateSelectedParcel(feature);
        openParcelPopup(feature, event.lngLat);
      });
    });

    [...config.regions.map((region) => getParcelFillLayerId(region)), "fallback-parcels-fill", "sale-ready-overview-clusters", "sale-ready-overview-point", "official-sale-parcel-fill", "official-sale-parcel-outline-halo", "official-sale-parcel-line", "official-sale-parcel-line-top", "official-sale-footprint-fill", "official-sale-footprint-line", "historic-sale-parcel-fill", "historic-sale-parcel-outline-halo", "historic-sale-parcel-line", "brownfield-polygons-fill", "brownfield-points", FUTURE_GROWTH_FILL_LAYER_ID, FUTURE_GROWTH_POINT_LAYER_ID, "market-listing-polygons-fill", "market-listing-polygons-outline-halo", "market-listing-polygons-line", "market-listing-points", "facilities-polygons-fill", "facilities-polygons-line", "facilities-points", "parcel-use-parcels-fill", "parcel-use-parcels-line", "scenario-score-fill", "scenario-score-line", "poi-points", "poi-points-clusters"].forEach((layerId) => {
      map.on("mouseenter", layerId, () => {
        if (
          currentMapViewMode === "land_use"
          && (layerId === "parcel-use-parcels-fill" || layerId === "parcel-use-parcels-line")
        ) {
          map.getCanvas().style.cursor = "";
          return;
        }
        map.getCanvas().style.cursor = "pointer";
      });
      map.on("mouseleave", layerId, () => {
        map.getCanvas().style.cursor = "";
      });
    });
  }

  async function switchRegion(region, reason = "auto") {
    if (!region || (activeRegion && activeRegion.slug === region.slug)) {
      return;
    }
    activeRegion = region;
    activeRegionMode = reason;
    regionSelectEl.value = reason === "manual" ? region.slug : "__AUTO__";
    showStatus(`${region.label} yÃƒÂ¼kleniyor...`, true);
    if (parcelPopup) {
      parcelPopup.remove();
      parcelPopup = null;
      activeParcelPopupState = null;
    }
    clearFutureGrowthHoverPopup();
    clearDynamicSources();
    addParcelLayers(region);
    void syncParcelFallbackParcels(true);
    addFacilitiesLayers();
    addLandIntelligenceLayers();
    scheduleLandIntelligenceRefresh(true);
    addTopographyOverlayLayer();
    addFutureGrowthLayers();
    scheduleFutureGrowthRefresh(true);
    updateComparedParcelsSource();
    clearFacilitiesOverlayState();
    clearScenarioOverlayState();
    applyMapViewMode(false);
    updateNearestSaleJumpButton();
    updateSelectedParcel(null);
    scheduleParcelFallbackRefresh(true);
    scheduleFacilitiesRefresh(true);
    void syncGlobalSaleReadyOverview(false);
    try {
      const poiData = await loadPoiData(region);
      currentPoiData = poiData;
      addPoiLayers(poiData.points, poiData.lines);
      updatePoiLayerVisibility();
    } catch (error) {
      const emptyPoiData = { points: createEmptyFeatureCollection(), lines: createEmptyFeatureCollection() };
      currentPoiData = emptyPoiData;
      addPoiLayers(emptyPoiData.points, emptyPoiData.lines);
      updatePoiLayerVisibility();
      showStatus(`${region.label} parcel ve satis katmanlari yuklendi; POI katmani gecici olarak yuklenemedi.`, true);
    }
    bindParcelInteractions();
    updateStats();
    showStatus(`${region.label} hazir.`);
    updateGuidanceStatus();
  }

  function scheduleRegionCheck() {
    window.clearTimeout(pendingSwitch);
    pendingSwitch = window.setTimeout(async () => {
      const region = pickRegionForCenter(map.getCenter());
      if (activeRegionMode === "manual" && regionSelectEl.value !== "__AUTO__") {
        updateDebug();
        return;
      }
      if (map.getZoom() >= config.regionSwitchZoom) {
        await switchRegion(region, "auto");
      }
      updateStats();
      updateGuidanceStatus();
    }, 120);
  }

  function bindControls() {
    setSanitizedHtml(regionSelectEl, `<option value="__AUTO__">Auto</option>${config.regions
      .map((region) => `<option value="${region.slug}">${region.label}</option>`)
      .join("")}`);
    if (citySelectEl) {
      setSanitizedHtml(citySelectEl, `<option value=\"__NONE__\">Sehir secin</option>${cityFocusPoints
        .map((city) => `<option value=\"${city.city}\">${city.city}</option>`)
        .join("")}`);
      updateCityInfo(null);
    }

    regionSelectEl.addEventListener("change", async (event) => {
      const value = event.target.value;
      if (value === "__AUTO__") {
        activeRegionMode = "auto";
        await switchRegion(pickRegionForCenter(map.getCenter()), "auto");
        return;
      }
      const region = regionMap.get(value);
      if (!region) return;
      activeRegionMode = "manual";
      await switchRegion(region, "manual");
      map.easeTo({ center: [region.center[1], region.center[0]], zoom: 10.5 });
    });

    if (citySelectEl) {
      citySelectEl.addEventListener("change", async (event) => {
        const value = event.target.value;
        if (value === "__NONE__") {
          updateCityInfo(null);
          return;
        }
        const city = cityFocusMap.get(value);
        if (!city) return;
        await focusCity(city);
      });
    }

    if (jumpNearestSaleBtnEl) {
      jumpNearestSaleBtnEl.addEventListener("click", () => {
        void jumpToNearestSaleReadyParcel();
      });
    }

    if (workspaceCollapseBtnEl) {
      workspaceCollapseBtnEl.addEventListener("click", () => {
        if (!selectedParcelFeature) return;
        workspacePanelCollapsed = true;
        updateWorkspacePanelVisibility();
      });
    }

    if (workspaceExpandBtnEl) {
      workspaceExpandBtnEl.addEventListener("click", () => {
        if (!selectedParcelFeature) return;
        workspacePanelCollapsed = false;
        updateWorkspacePanelVisibility();
      });
    }

    if (baseMapSelectEl) {
      baseMapSelectEl.value = currentBaseMapMode;
      baseMapSelectEl.addEventListener("change", () => {
        setBaseMapMode(baseMapSelectEl.value || "standard");
      });
    }

    if (mapViewModeEl) {
      mapViewModeEl.value = currentMapViewMode;
      mapViewModeEl.addEventListener("change", () => {
        const nextMode = mapViewModeEl.value || "parcel";
        setMapViewMode(nextMode, true);
      });
    }
    renderMapModeCustomizer();

    syncTopographyControls();
    if (showTopographyOverlayEl) {
      showTopographyOverlayEl.addEventListener("change", () => {
        setTopographyOverlayVisibility(Boolean(showTopographyOverlayEl.checked));
      });
    }
    syncFutureGrowthControls();
    if (showFutureGrowthEl) {
      showFutureGrowthEl.addEventListener("change", () => {
        setFutureGrowthLayerVisibility(Boolean(showFutureGrowthEl.checked));
      });
    }

    showPoiPointsEl.addEventListener("change", () => {
      currentPoiPointsVisible = showPoiPointsEl.checked;
      updatePoiLayerVisibility();
    });

    showPoiLinesEl.addEventListener("change", () => {
      currentPoiLinesVisible = showPoiLinesEl.checked;
      updatePoiLayerVisibility();
    });

    if (showFacilitiesOverlayEl) {
      showFacilitiesOverlayEl.checked = currentFacilitiesVisible;
      showFacilitiesOverlayEl.addEventListener("change", () => {
        if (currentMapViewMode === "land_use") {
          showFacilitiesOverlayEl.checked = true;
          currentFacilitiesVisible = true;
          updateFacilitiesStatus();
          return;
        }
        currentFacilitiesVisible = Boolean(showFacilitiesOverlayEl.checked);
        updateFacilitiesLayerVisibility();
        updateFacilitiesStatus();
        scheduleFacilitiesRefresh(true);
      });
    }

    if (facilitiesCategoryFilterEl) {
      facilitiesCategoryFilterEl.value = currentFacilitiesCategory;
      facilitiesCategoryFilterEl.addEventListener("change", () => {
        currentFacilitiesCategory = facilitiesCategoryFilterEl.value || "all";
        updateFacilitiesStatus();
        scheduleFacilitiesRefresh(true);
      });
    }

    if (scenarioScoreModeEl) {
      scenarioScoreModeEl.value = currentScenarioScoreMode;
      scenarioScoreModeEl.addEventListener("change", () => {
        currentScenarioScoreMode = scenarioScoreModeEl.value || "none";
        updateFacilitiesLayerVisibility();
        updateFacilitiesStatus();
        scheduleFacilitiesRefresh(true);
      });
    }

    if (showOfficialSaleEl) {
      showOfficialSaleEl.addEventListener("change", () => {
        currentOfficialSaleVisible = showOfficialSaleEl.checked;
        if (currentOfficialSaleVisible) {
          if (currentHistoricSalesVisible) {
            currentHistoricSalesVisible = false;
            if (showHistoricSalesEl) {
              showHistoricSalesEl.checked = false;
            }
            showStatus("Resmi satis modu acildi; gecmis satis modu kapatildi.");
          }
          ensureOfficialSalesModeFocus();
        }
        applyMapViewMode(false);
        scheduleLandIntelligenceRefresh(true);
        void syncGlobalSaleReadyOverview(false);
        updateNearestSaleJumpButton();
        updateLandSourceStatusPanel();
        updateMapModeControlState();
      });
    }

    if (showHistoricSalesEl) {
      showHistoricSalesEl.addEventListener("change", async () => {
        currentHistoricSalesVisible = showHistoricSalesEl.checked;
        if (currentHistoricSalesVisible) {
          previousSaleLayerVisibilityBeforeHistory = {
            official: currentOfficialSaleVisible,
            brownfield: currentBrownfieldVisible,
            market: currentMarketListingsVisible,
          };
          if (currentOfficialSaleVisible) {
            currentOfficialSaleVisible = false;
            if (showOfficialSaleEl) {
              showOfficialSaleEl.checked = false;
            }
          }
          if (currentBrownfieldVisible) {
            currentBrownfieldVisible = false;
            if (showBrownfieldSignalsEl) {
              showBrownfieldSignalsEl.checked = false;
            }
          }
          if (currentMarketListingsVisible) {
            currentMarketListingsVisible = false;
            if (showMarketListingsEl) {
              showMarketListingsEl.checked = false;
            }
          }
          ensureHistoricSalesModeFocus();
          showStatus("Gecmis satis katmani acildi, veriler yukleniyor...", true);
        } else {
          if (previousSaleLayerVisibilityBeforeHistory.official) {
            currentOfficialSaleVisible = true;
            if (showOfficialSaleEl) {
              showOfficialSaleEl.checked = true;
            }
          }
          if (previousSaleLayerVisibilityBeforeHistory.brownfield) {
            currentBrownfieldVisible = true;
            if (showBrownfieldSignalsEl) {
              showBrownfieldSignalsEl.checked = true;
            }
          }
          if (previousSaleLayerVisibilityBeforeHistory.market) {
            currentMarketListingsVisible = true;
            if (showMarketListingsEl) {
              showMarketListingsEl.checked = true;
            }
          }
          showStatus("Gecmis satis katmani kapatildi.");
        }
        applyMapViewMode(false);
        scheduleLandIntelligenceRefresh(true);
        void syncGlobalSaleReadyOverview(false);
        updateLandSourceStatusPanel();
        updateMapModeControlState();
        updateNearestSaleJumpButton();
        if (selectedParcelFeature) {
          setSanitizedText(selectedParcelEl, formatParcelFeature(selectedParcelFeature));
        }
        renderWorkspace();
        if (currentHistoricSalesVisible) {
          window.setTimeout(() => {
            void focusNearestHistoricSaleParcelIfNeeded();
          }, 420);
        }
      });
    }

    if (showBrownfieldSignalsEl) {
      showBrownfieldSignalsEl.addEventListener("change", () => {
        currentBrownfieldVisible = showBrownfieldSignalsEl.checked;
        updateLandIntelligenceLayerVisibility();
        scheduleLandIntelligenceRefresh(true);
        void syncGlobalSaleReadyOverview(false);
        updateLandSourceStatusPanel();
      });
    }

    if (showMarketListingsEl) {
      showMarketListingsEl.addEventListener("change", () => {
        currentMarketListingsVisible = showMarketListingsEl.checked;
        updateLandIntelligenceLayerVisibility();
        scheduleLandIntelligenceRefresh(true);
        void syncGlobalSaleReadyOverview(false);
        updateLandSourceStatusPanel();
      });
    }

    if (landMinConfidenceEl) {
      landMinConfidenceEl.value = String(landOverlayFilters.minConfidence);
      landMinConfidenceEl.addEventListener("input", () => {
        landOverlayFilters.minConfidence = Number(landMinConfidenceEl.value || 0);
        updateLandFilterSummary();
        renderWorkspace();
        void syncGlobalSaleReadyOverview(false);
      });
      landMinConfidenceEl.addEventListener("change", () => {
        landOverlayFilters.minConfidence = Number(landMinConfidenceEl.value || 0);
        updateLandFilterSummary();
        renderWorkspace();
        scheduleLandIntelligenceRefresh(true);
        void syncGlobalSaleReadyOverview(false);
      });
    }

    if (brownfieldSourceFilterEl) {
      brownfieldSourceFilterEl.value = landOverlayFilters.brownfieldSource;
      brownfieldSourceFilterEl.addEventListener("change", () => {
        landOverlayFilters.brownfieldSource = brownfieldSourceFilterEl.value || "all";
        updateLandFilterSummary();
        renderWorkspace();
        scheduleLandIntelligenceRefresh(true);
        void syncGlobalSaleReadyOverview(false);
      });
    }

    if (listingStatusFilterEl) {
      listingStatusFilterEl.value = landOverlayFilters.listingStatus;
      listingStatusFilterEl.addEventListener("change", () => {
        landOverlayFilters.listingStatus = listingStatusFilterEl.value || "all";
        updateLandFilterSummary();
        renderWorkspace();
        scheduleLandIntelligenceRefresh(true);
        void syncGlobalSaleReadyOverview(false);
      });
    }

    if (saleReadyQuickFiltersEl) {
      updateSaleReadyQuickFilterButtons();
      saleReadyQuickFiltersEl.querySelectorAll("[data-sale-ready-quick-filter]").forEach((buttonEl) => {
        buttonEl.addEventListener("click", () => {
          const value = buttonEl.getAttribute("data-sale-ready-quick-filter") || "all";
          landOverlayFilters.saleReadyQuickFilter = value;
          updateSaleReadyQuickFilterButtons();
          updateLandFilterSummary();
          renderWorkspace();
          scheduleLandIntelligenceRefresh(true);
          void syncGlobalSaleReadyOverview(false);
        });
      });
    }

    if (landReviewOnlyEl) {
      landReviewOnlyEl.checked = landOverlayFilters.reviewOnly;
      landReviewOnlyEl.addEventListener("change", () => {
        landOverlayFilters.reviewOnly = Boolean(landReviewOnlyEl.checked);
        updateLandFilterSummary();
        renderWorkspace();
        scheduleLandIntelligenceRefresh(true);
        void syncGlobalSaleReadyOverview(false);
      });
    }

    if (resetLandFiltersEl) {
      resetLandFiltersEl.addEventListener("click", () => {
        resetLandOverlayFilters();
        renderWorkspace();
        scheduleLandIntelligenceRefresh(true);
        void syncGlobalSaleReadyOverview(false);
      });
    }

    updateWorkspacePanelVisibility();
  }

  const startupParcelView = {
    center: [-0.45676, 51.33692],
    zoom: Math.max(Number(config.parcelMinZoom || 14) + 1.2, 15.2),
  };
  const configuredInitialZoom = Number(config.initialView?.zoom);
  const hasConfiguredInitialView = Number.isFinite(configuredInitialZoom)
    && Array.isArray(config.initialView?.center)
    && config.initialView.center.length >= 2
    && Number.isFinite(Number(config.initialView.center[0]))
    && Number.isFinite(Number(config.initialView.center[1]));
  const initialMapCenter = hasConfiguredInitialView
    ? config.initialView.center
    : startupParcelView.center;
  const initialMapZoom = hasConfiguredInitialView
    ? configuredInitialZoom
    : startupParcelView.zoom;
  const persistedView = loadPersistedMapView();
  const bootMapCenter = persistedView?.center || initialMapCenter;
  const bootMapZoom = Number.isFinite(Number(persistedView?.zoom))
    ? Number(persistedView.zoom)
    : initialMapZoom;

  function syncMapControlOffsetVar() {
    try {
      const topRight = document.querySelector(".maplibregl-ctrl-top-right");
      const controlHeight = Math.ceil(topRight?.getBoundingClientRect?.().height || 0);
      const offsetTop = Math.max(152, controlHeight + 18);
      document.documentElement.style.setProperty("--aays-map-controls-offset-top", `${offsetTop}px`);
    } catch (_error) {
      document.documentElement.style.setProperty("--aays-map-controls-offset-top", "152px");
    }
  }

  map = new maplibregl.Map({
    container: "map",
    style: createBaseStyle(),
    center: bootMapCenter,
    zoom: bootMapZoom,
    maxZoom: 19,
    minZoom: 5,
    attributionControl: true,
  });

  map.addControl(new maplibregl.NavigationControl({ visualizePitch: true }), "top-right");
  mapModeControlInstance = createMapModeControl();
  map.addControl(mapModeControlInstance, "top-right");
  map.addControl(new maplibregl.ScaleControl({ maxWidth: 120, unit: "metric" }));
  syncMapControlOffsetVar();
  window.addEventListener("resize", syncMapControlOffsetVar);

  bindControls();
  updateFreeCoverageInfo();
  renderCoverageCityList();
  renderSupportedUnitsList();
  updateLandFilterSummary();
  updateLandSourceStatusPanel();
  updateFacilitiesStatus();
  syncFutureGrowthControls();
  updateFutureGrowthStatus(
    currentFutureGrowthVisible
      ? "Gelecek Gelisim katmani acik, veri yukleniyor..."
      : "Gelecek Gelisim katmani kapali."
  );
  loadLandSourceStatuses();
  renderWorkspace();
  repairTurkishMojibakeInElement(document.body);
  if (supportedUnitsSearchEl) {
    supportedUnitsSearchEl.addEventListener("input", (event) => {
      renderSupportedUnitsList(event.target.value || "");
    });
  }

  map.on("load", async () => {
    syncMapControlOffsetVar();
    await switchRegion(pickRegionForCenter(map.getCenter()) || config.regions[0], "auto");
    setBaseMapMode(currentBaseMapMode);
    updateStats();
    showStatus("Harita hazir. Isterseniz dogrudan yakinlasip bolge degistirebiliriz.");
    updateGuidanceStatus();
  });

  map.on("moveend", () => {
    savePersistedMapView();
    syncMapControlOffsetVar();
  });

  map.on("moveend", () => {
    scheduleRegionCheck();
    scheduleParcelFallbackRefresh();
    scheduleLandIntelligenceRefresh();
    scheduleFutureGrowthRefresh();
    scheduleFacilitiesRefresh();
    scheduleGlobalOverviewRefresh(false);
  });
  map.on("zoomend", () => {
    syncMapControlOffsetVar();
    updateDebug();
    updateGuidanceStatus();
    scheduleParcelFallbackRefresh();
    scheduleLandIntelligenceRefresh();
    scheduleFutureGrowthRefresh();
    scheduleFacilitiesRefresh();
    scheduleGlobalOverviewRefresh(false);
  });
})();

/* TY_CANDIDATE_METRICS_PATCH_START */
(function () {
  const TY_CANDIDATE_METRICS_BY_ID = {"OTM-18717324":{"listing_id":"OTM-18717324","confidence":"medium","previous_confidence":"medium_low","candidate_class":"candidate_medium_doc_area","area_m2":"450.0","computed_area_m2":"421.654","perimeter_m":"75.404","side_lengths_m_json":"[12.39, 6.453, 12.406, 6.453, 12.39, 6.453, 12.406, 6.453]","area_source":"public_site_area_text","area_raw":"450mÂ²","method":"public_doc_or_image_plus_site_area","planning_refs":"","lot_refs":"S","title_refs":"","doc_evidence":"yes","note":"estimated_candidate_not_verified | confidence=medium | previous_confidence=medium_low | class=candidate_medium_doc_area | reason=public document/image evidence plus public area text | area=450.00 mÂ² | computed_polygon_area=421.65 mÂ² | perimeter=75.40 m | sides=[K1=12.39m, K2=6.45m, K3=12.41m, K4=6.45m, K5=12.39m, K6=6.45m, K7=12.41m, K8=6.45m] | area_source=public_site_area_text (450mÂ²) | method=public_doc_or_image_plus_site_area | planning_refs= | lot_refs=S | title_refs= | doc_evidence=yes | NOT original/verified boundary; derived candidate geometry for display and review."},"OTM-18661723":{"listing_id":"OTM-18661723","confidence":"medium_low","previous_confidence":"low","candidate_class":"candidate_medium_low_doc_only","area_m2":"15164.992","computed_area_m2":"14474.878","perimeter_m":"441.72","side_lengths_m_json":"[72.234, 38.007, 72.613, 38.007, 72.232, 38.007, 72.613, 38.007]","area_source":"feed_bbox_area_fallback","area_raw":"feed_bbox_area_m2=15164.99","method":"feed_bbox_area_scaled_candidate","planning_refs":"25/04725/FPA","lot_refs":"","title_refs":"","doc_evidence":"yes","note":"estimated_candidate_not_verified | confidence=medium_low | previous_confidence=low | class=candidate_medium_low_doc_only | reason=public document/image evidence but no public site area | area=15,164.99 mÂ² | computed_polygon_area=14,474.88 mÂ² | perimeter=441.72 m | sides=[K1=72.23m, K2=38.01m, K3=72.61m, K4=38.01m, K5=72.23m, K6=38.01m, K7=72.61m, K8=38.01m] | area_source=feed_bbox_area_fallback (feed_bbox_area_m2=15164.99) | method=feed_bbox_area_scaled_candidate | planning_refs=25/04725/FPA | lot_refs= | title_refs= | doc_evidence=yes | NOT original/verified boundary; derived candidate geometry for display and review."},"OTM-19067395":{"listing_id":"OTM-19067395","confidence":"medium_low","previous_confidence":"low_plus","candidate_class":"candidate_medium_low_area_only","area_m2":"159.17","computed_area_m2":"169.14","perimeter_m":"47.7","side_lengths_m_json":"[7.581, 4.237, 7.795, 4.237, 7.581, 4.237, 7.795, 4.237]","area_source":"public_site_area_text","area_raw":"159.17 sq.m","method":"public_site_area_and_centroid","planning_refs":"","lot_refs":"","title_refs":"","doc_evidence":"no","note":"estimated_candidate_not_verified | confidence=medium_low | previous_confidence=low_plus | class=candidate_medium_low_area_only | reason=public area text and centroid; no plan/georef | area=159.17 mÂ² | computed_polygon_area=169.14 mÂ² | perimeter=47.70 m | sides=[K1=7.58m, K2=4.24m, K3=7.79m, K4=4.24m, K5=7.58m, K6=4.24m, K7=7.79m, K8=4.24m] | area_source=public_site_area_text (159.17 sq.m) | method=public_site_area_and_centroid | planning_refs= | lot_refs= | title_refs= | doc_evidence=no | NOT original/verified boundary; derived candidate geometry for display and review."},"OTM-17768121":{"listing_id":"OTM-17768121","confidence":"medium_low","previous_confidence":"low_plus","candidate_class":"candidate_medium_low_area_only","area_m2":"1618.743","computed_area_m2":"1516.775","perimeter_m":"143.016","side_lengths_m_json":"[23.5, 12.24, 23.529, 12.239, 23.5, 12.239, 23.529, 12.24]","area_source":"public_site_area_text","area_raw":"0.40 acre","method":"public_site_area_and_centroid","planning_refs":"","lot_refs":"","title_refs":"","doc_evidence":"no","note":"estimated_candidate_not_verified | confidence=medium_low | previous_confidence=low_plus | class=candidate_medium_low_area_only | reason=public area text and centroid; no plan/georef | area=1,618.74 mÂ² | computed_polygon_area=1,516.78 mÂ² | perimeter=143.02 m | sides=[K1=23.50m, K2=12.24m, K3=23.53m, K4=12.24m, K5=23.50m, K6=12.24m, K7=23.53m, K8=12.24m] | area_source=public_site_area_text (0.40 acre) | method=public_site_area_and_centroid | planning_refs= | lot_refs= | title_refs= | doc_evidence=no | NOT original/verified boundary; derived candidate geometry for display and review."},"OTM-19153457":{"listing_id":"OTM-19153457","confidence":"medium","previous_confidence":"medium_low","candidate_class":"candidate_medium_doc_area","area_m2":"809.371","computed_area_m2":"786.815","perimeter_m":"102.966","side_lengths_m_json":"[16.757, 8.907, 16.912, 8.907, 16.757, 8.907, 16.912, 8.907]","area_source":"public_site_area_text","area_raw":"0.2 acres","method":"public_doc_or_image_plus_site_area","planning_refs":"","lot_refs":"","title_refs":"","doc_evidence":"yes","note":"estimated_candidate_not_verified | confidence=medium | previous_confidence=medium_low | class=candidate_medium_doc_area | reason=public document/image evidence plus public area text | area=809.37 mÂ² | computed_polygon_area=786.82 mÂ² | perimeter=102.97 m | sides=[K1=16.76m, K2=8.91m, K3=16.91m, K4=8.91m, K5=16.76m, K6=8.91m, K7=16.91m, K8=8.91m] | area_source=public_site_area_text (0.2 acres) | method=public_doc_or_image_plus_site_area | planning_refs= | lot_refs= | title_refs= | doc_evidence=yes | NOT original/verified boundary; derived candidate geometry for display and review."},"OTM-18257284":{"listing_id":"OTM-18257284","confidence":"medium","previous_confidence":"medium_low","candidate_class":"candidate_medium_doc_area","area_m2":"67.912","computed_area_m2":"68.447","perimeter_m":"30.358","side_lengths_m_json":"[4.894, 2.654, 4.977, 2.654, 4.894, 2.654, 4.977, 2.654]","area_source":"public_site_area_text","area_raw":"731 sq ft","method":"public_doc_or_image_plus_site_area","planning_refs":"","lot_refs":"","title_refs":"","doc_evidence":"yes","note":"estimated_candidate_not_verified | confidence=medium | previous_confidence=medium_low | class=candidate_medium_doc_area | reason=public document/image evidence plus public area text | area=67.91 mÂ² | computed_polygon_area=68.45 mÂ² | perimeter=30.36 m | sides=[K1=4.89m, K2=2.65m, K3=4.98m, K4=2.65m, K5=4.89m, K6=2.65m, K7=4.98m, K8=2.65m] | area_source=public_site_area_text (731 sq ft) | method=public_doc_or_image_plus_site_area | planning_refs= | lot_refs= | title_refs= | doc_evidence=yes | NOT original/verified boundary; derived candidate geometry for display and review."},"OTM-18447115":{"listing_id":"OTM-18447115","confidence":"medium_low","previous_confidence":"low_plus","candidate_class":"candidate_medium_low_area_only","area_m2":"95.876","computed_area_m2":"105.703","perimeter_m":"37.772","side_lengths_m_json":"[6.267, 3.198, 6.223, 3.198, 6.267, 3.198, 6.223, 3.198]","area_source":"public_site_area_text","area_raw":"1032 sq ft","method":"public_site_area_and_centroid","planning_refs":"","lot_refs":"","title_refs":"","doc_evidence":"no","note":"estimated_candidate_not_verified | confidence=medium_low | previous_confidence=low_plus | class=candidate_medium_low_area_only | reason=public area text and centroid; no plan/georef | area=95.88 mÂ² | computed_polygon_area=105.70 mÂ² | perimeter=37.77 m | sides=[K1=6.27m, K2=3.20m, K3=6.22m, K4=3.20m, K5=6.27m, K6=3.20m, K7=6.22m, K8=3.20m] | area_source=public_site_area_text (1032 sq ft) | method=public_site_area_and_centroid | planning_refs= | lot_refs= | title_refs= | doc_evidence=no | NOT original/verified boundary; derived candidate geometry for display and review."},"OTM-17967212":{"listing_id":"OTM-17967212","confidence":"medium_low","previous_confidence":"low","candidate_class":"candidate_medium_low_doc_only","area_m2":"8580.074","computed_area_m2":"8340.964","perimeter_m":"335.247","side_lengths_m_json":"[54.56, 29.001, 55.063, 29.0, 54.559, 29.0, 55.063, 29.001]","area_source":"feed_bbox_area_fallback","area_raw":"feed_bbox_area_m2=8580.07","method":"feed_bbox_area_scaled_candidate","planning_refs":"","lot_refs":"","title_refs":"","doc_evidence":"yes","note":"estimated_candidate_not_verified | confidence=medium_low | previous_confidence=low | class=candidate_medium_low_doc_only | reason=public document/image evidence but no public site area | area=8,580.07 mÂ² | computed_polygon_area=8,340.96 mÂ² | perimeter=335.25 m | sides=[K1=54.56m, K2=29.00m, K3=55.06m, K4=29.00m, K5=54.56m, K6=29.00m, K7=55.06m, K8=29.00m] | area_source=feed_bbox_area_fallback (feed_bbox_area_m2=8580.07) | method=feed_bbox_area_scaled_candidate | planning_refs= | lot_refs= | title_refs= | doc_evidence=yes | NOT original/verified boundary; derived candidate geometry for display and review."},"OTM-18109783":{"listing_id":"OTM-18109783","confidence":"medium_low","previous_confidence":"low_plus","candidate_class":"candidate_medium_low_area_only","area_m2":"2428.114","computed_area_m2":"2447.228","perimeter_m":"181.524","side_lengths_m_json":"[29.261, 15.871, 29.759, 15.871, 29.261, 15.871, 29.759, 15.871]","area_source":"public_site_area_text","area_raw":"0.60 acre","method":"public_site_area_and_centroid","planning_refs":"","lot_refs":"","title_refs":"","doc_evidence":"no","note":"estimated_candidate_not_verified | confidence=medium_low | previous_confidence=low_plus | class=candidate_medium_low_area_only | reason=public area text and centroid; no plan/georef | area=2,428.11 mÂ² | computed_polygon_area=2,447.23 mÂ² | perimeter=181.52 m | sides=[K1=29.26m, K2=15.87m, K3=29.76m, K4=15.87m, K5=29.26m, K6=15.87m, K7=29.76m, K8=15.87m] | area_source=public_site_area_text (0.60 acre) | method=public_site_area_and_centroid | planning_refs= | lot_refs= | title_refs= | doc_evidence=no | NOT original/verified boundary; derived candidate geometry for display and review."},"OTM-18560410":{"listing_id":"OTM-18560410","confidence":"medium_low","previous_confidence":"low_plus","candidate_class":"candidate_medium_low_area_only","area_m2":"99.964","computed_area_m2":"99.151","perimeter_m":"36.634","side_lengths_m_json":"[6.253, 3.001, 6.062, 3.001, 6.253, 3.001, 6.062, 3.001]","area_source":"public_site_area_text","area_raw":"1,076 sq ft","method":"public_site_area_and_centroid","planning_refs":"","lot_refs":"","title_refs":"","doc_evidence":"no","note":"estimated_candidate_not_verified | confidence=medium_low | previous_confidence=low_plus | class=candidate_medium_low_area_only | reason=public area text and centroid; no plan/georef | area=99.96 mÂ² | computed_polygon_area=99.15 mÂ² | perimeter=36.63 m | sides=[K1=6.25m, K2=3.00m, K3=6.06m, K4=3.00m, K5=6.25m, K6=3.00m, K7=6.06m, K8=3.00m] | area_source=public_site_area_text (1,076 sq ft) | method=public_site_area_and_centroid | planning_refs= | lot_refs= | title_refs= | doc_evidence=no | NOT original/verified boundary; derived candidate geometry for display and review."},"OTM-13319386":{"listing_id":"OTM-13319386","confidence":"medium","previous_confidence":"medium_low","candidate_class":"candidate_medium_doc_area","area_m2":"2023.428","computed_area_m2":"1931.348","perimeter_m":"161.35","side_lengths_m_json":"[26.385, 13.883, 26.524, 13.883, 26.385, 13.883, 26.524, 13.883]","area_source":"public_site_area_text","area_raw":"0.50 acre","method":"public_doc_or_image_plus_site_area","planning_refs":"25/00841/OUT","lot_refs":"","title_refs":"","doc_evidence":"yes","note":"estimated_candidate_not_verified | confidence=medium | previous_confidence=medium_low | class=candidate_medium_doc_area | reason=public document/image evidence plus public area text | area=2,023.43 mÂ² | computed_polygon_area=1,931.35 mÂ² | perimeter=161.35 m | sides=[K1=26.39m, K2=13.88m, K3=26.52m, K4=13.88m, K5=26.39m, K6=13.88m, K7=26.52m, K8=13.88m] | area_source=public_site_area_text (0.50 acre) | method=public_doc_or_image_plus_site_area | planning_refs=25/00841/OUT | lot_refs= | title_refs= | doc_evidence=yes | NOT original/verified boundary; derived candidate geometry for display and review."},"OTM-18555242":{"listing_id":"OTM-18555242","confidence":"medium_low","previous_confidence":"low_plus","candidate_class":"candidate_medium_low_area_only","area_m2":"195.933","computed_area_m2":"180.195","perimeter_m":"49.306","side_lengths_m_json":"[8.141, 4.197, 8.118, 4.197, 8.141, 4.197, 8.118, 4.197]","area_source":"public_site_area_text","area_raw":"2109 sq ft","method":"public_site_area_and_centroid","planning_refs":"","lot_refs":"","title_refs":"","doc_evidence":"no","note":"estimated_candidate_not_verified | confidence=medium_low | previous_confidence=low_plus | class=candidate_medium_low_area_only | reason=public area text and centroid; no plan/georef | area=195.93 mÂ² | computed_polygon_area=180.19 mÂ² | perimeter=49.31 m | sides=[K1=8.14m, K2=4.20m, K3=8.12m, K4=4.20m, K5=8.14m, K6=4.20m, K7=8.12m, K8=4.20m] | area_source=public_site_area_text (2109 sq ft) | method=public_site_area_and_centroid | planning_refs= | lot_refs= | title_refs= | doc_evidence=no | NOT original/verified boundary; derived candidate geometry for display and review."},"OTM-14105467":{"listing_id":"OTM-14105467","confidence":"medium","previous_confidence":"medium_low","candidate_class":"candidate_medium_doc_area","area_m2":"768.773","computed_area_m2":"804.516","perimeter_m":"104.276","side_lengths_m_json":"[17.547, 8.685, 17.221, 8.685, 17.547, 8.685, 17.221, 8.685]","area_source":"public_site_area_text","area_raw":"8275 Square Feet","method":"public_doc_or_image_plus_site_area","planning_refs":"","lot_refs":"","title_refs":"","doc_evidence":"yes","note":"estimated_candidate_not_verified | confidence=medium | previous_confidence=medium_low | class=candidate_medium_doc_area | reason=public document/image evidence plus public area text | area=768.77 mÂ² | computed_polygon_area=804.52 mÂ² | perimeter=104.28 m | sides=[K1=17.55m, K2=8.69m, K3=17.22m, K4=8.69m, K5=17.55m, K6=8.69m, K7=17.22m, K8=8.69m] | area_source=public_site_area_text (8275 Square Feet) | method=public_doc_or_image_plus_site_area | planning_refs= | lot_refs= | title_refs= | doc_evidence=yes | NOT original/verified boundary; derived candidate geometry for display and review."},"OTM-17567927":{"listing_id":"OTM-17567927","confidence":"medium_low","previous_confidence":"low","candidate_class":"candidate_medium_low_doc_only","area_m2":"4904.976","computed_area_m2":"5070.338","perimeter_m":"261.063","side_lengths_m_json":"[42.713, 23.681, 40.457, 23.681, 42.712, 23.681, 40.457, 23.681]","area_source":"feed_bbox_area_fallback","area_raw":"feed_bbox_area_m2=4904.98","method":"feed_bbox_area_scaled_candidate","planning_refs":"","lot_refs":"","title_refs":"","doc_evidence":"yes","note":"estimated_candidate_not_verified | confidence=medium_low | previous_confidence=low | class=candidate_medium_low_doc_only | reason=public document/image evidence but no public site area | area=4,904.98 mÂ² | computed_polygon_area=5,070.34 mÂ² | perimeter=261.06 m | sides=[K1=42.71m, K2=23.68m, K3=40.46m, K4=23.68m, K5=42.71m, K6=23.68m, K7=40.46m, K8=23.68m] | area_source=feed_bbox_area_fallback (feed_bbox_area_m2=4904.98) | method=feed_bbox_area_scaled_candidate | planning_refs= | lot_refs= | title_refs= | doc_evidence=yes | NOT original/verified boundary; derived candidate geometry for display and review."},"OTM-19125446":{"listing_id":"OTM-19125446","confidence":"medium_low","previous_confidence":"low_plus","candidate_class":"candidate_medium_low_area_only","area_m2":"34398.28","computed_area_m2":"31635.307","perimeter_m":"653.278","side_lengths_m_json":"[107.868, 55.608, 107.558, 55.607, 107.864, 55.607, 107.558, 55.608]","area_source":"public_site_area_text","area_raw":"8.50 acre","method":"public_site_area_and_centroid","planning_refs":"","lot_refs":"","title_refs":"","doc_evidence":"no","note":"estimated_candidate_not_verified | confidence=medium_low | previous_confidence=low_plus | class=candidate_medium_low_area_only | reason=public area text and centroid; no plan/georef | area=34,398.28 mÂ² | computed_polygon_area=31,635.31 mÂ² | perimeter=653.28 m | sides=[K1=107.87m, K2=55.61m, K3=107.56m, K4=55.61m, K5=107.86m, K6=55.61m, K7=107.56m, K8=55.61m] | area_source=public_site_area_text (8.50 acre) | method=public_site_area_and_centroid | planning_refs= | lot_refs= | title_refs= | doc_evidence=no | NOT original/verified boundary; derived candidate geometry for display and review."},"OTM-16919068":{"listing_id":"OTM-16919068","confidence":"medium_low","previous_confidence":"low_plus","candidate_class":"candidate_medium_low_area_only","area_m2":"2100.0","computed_area_m2":"2231.538","perimeter_m":"173.255","side_lengths_m_json":"[27.535, 15.39, 28.313, 15.39, 27.534, 15.39, 28.313, 15.39]","area_source":"public_site_area_text","area_raw":"0.21 hectares","method":"public_site_area_and_centroid","planning_refs":"","lot_refs":"","title_refs":"","doc_evidence":"no","note":"estimated_candidate_not_verified | confidence=medium_low | previous_confidence=low_plus | class=candidate_medium_low_area_only | reason=public area text and centroid; no plan/georef | area=2,100.00 mÂ² | computed_polygon_area=2,231.54 mÂ² | perimeter=173.25 m | sides=[K1=27.54m, K2=15.39m, K3=28.31m, K4=15.39m, K5=27.53m, K6=15.39m, K7=28.31m, K8=15.39m] | area_source=public_site_area_text (0.21 hectares) | method=public_site_area_and_centroid | planning_refs= | lot_refs= | title_refs= | doc_evidence=no | NOT original/verified boundary; derived candidate geometry for display and review."},"OTM-18288130":{"listing_id":"OTM-18288130","confidence":"medium","previous_confidence":"medium_low","candidate_class":"candidate_medium_doc_area","area_m2":"999.574","computed_area_m2":"1102.03","perimeter_m":"121.956","side_lengths_m_json":"[20.235, 10.325, 20.093, 10.325, 20.235, 10.325, 20.093, 10.325]","area_source":"public_site_area_text","area_raw":"0.247 acre","method":"public_doc_or_image_plus_site_area","planning_refs":"","lot_refs":"","title_refs":"","doc_evidence":"yes","note":"estimated_candidate_not_verified | confidence=medium | previous_confidence=medium_low | class=candidate_medium_doc_area | reason=public document/image evidence plus public area text | area=999.57 mÂ² | computed_polygon_area=1,102.03 mÂ² | perimeter=121.96 m | sides=[K1=20.23m, K2=10.32m, K3=20.09m, K4=10.32m, K5=20.23m, K6=10.32m, K7=20.09m, K8=10.32m] | area_source=public_site_area_text (0.247 acre) | method=public_doc_or_image_plus_site_area | planning_refs= | lot_refs= | title_refs= | doc_evidence=yes | NOT original/verified boundary; derived candidate geometry for display and review."},"OTM-19136283":{"listing_id":"OTM-19136283","confidence":"medium","previous_confidence":"medium_low","candidate_class":"candidate_medium_doc_area","area_m2":"1294.994","computed_area_m2":"1213.42","perimeter_m":"127.916","side_lengths_m_json":"[21.019, 10.947, 21.045, 10.947, 21.019, 10.947, 21.045, 10.947]","area_source":"public_site_area_text","area_raw":"0.32 acres","method":"public_doc_or_image_plus_site_area","planning_refs":"15/02182/FUL","lot_refs":"IS","title_refs":"","doc_evidence":"yes","note":"estimated_candidate_not_verified | confidence=medium | previous_confidence=medium_low | class=candidate_medium_doc_area | reason=public document/image evidence plus public area text | area=1,294.99 mÂ² | computed_polygon_area=1,213.42 mÂ² | perimeter=127.92 m | sides=[K1=21.02m, K2=10.95m, K3=21.05m, K4=10.95m, K5=21.02m, K6=10.95m, K7=21.05m, K8=10.95m] | area_source=public_site_area_text (0.32 acres) | method=public_doc_or_image_plus_site_area | planning_refs=15/02182/FUL | lot_refs=IS | title_refs= | doc_evidence=yes | NOT original/verified boundary; derived candidate geometry for display and review."},"OTM-19142630":{"listing_id":"OTM-19142630","confidence":"medium_low","previous_confidence":"low_plus","candidate_class":"candidate_medium_low_area_only","area_m2":"362.0","computed_area_m2":"365.593","perimeter_m":"70.326","side_lengths_m_json":"[11.947, 5.793, 11.63, 5.793, 11.947, 5.793, 11.63, 5.793]","area_source":"public_site_area_text","area_raw":"362 sqm","method":"public_site_area_and_centroid","planning_refs":"","lot_refs":"","title_refs":"","doc_evidence":"no","note":"estimated_candidate_not_verified | confidence=medium_low | previous_confidence=low_plus | class=candidate_medium_low_area_only | reason=public area text and centroid; no plan/georef | area=362.00 mÂ² | computed_polygon_area=365.59 mÂ² | perimeter=70.33 m | sides=[K1=11.95m, K2=5.79m, K3=11.63m, K4=5.79m, K5=11.95m, K6=5.79m, K7=11.63m, K8=5.79m] | area_source=public_site_area_text (362 sqm) | method=public_site_area_and_centroid | planning_refs= | lot_refs= | title_refs= | doc_evidence=no | NOT original/verified boundary; derived candidate geometry for display and review."},"OTM-13125000":{"listing_id":"OTM-13125000","confidence":"medium","previous_confidence":"medium_low","candidate_class":"candidate_medium_doc_area","area_m2":"1358.614","computed_area_m2":"1438.361","perimeter_m":"139.937","side_lengths_m_json":"[24.146, 10.641, 24.542, 10.64, 24.145, 10.64, 24.542, 10.641]","area_source":"public_site_area_text","area_raw":"14624 sq ft","method":"public_doc_or_image_plus_site_area","planning_refs":"14/11168/FULL; 14/11168/LBC; 18/02453/CLEUD","lot_refs":"","title_refs":"","doc_evidence":"yes","note":"estimated_candidate_not_verified | confidence=medium | previous_confidence=medium_low | class=candidate_medium_doc_area | reason=public document/image evidence plus public area text | area=1,358.61 mÂ² | computed_polygon_area=1,438.36 mÂ² | perimeter=139.94 m | sides=[K1=24.15m, K2=10.64m, K3=24.54m, K4=10.64m, K5=24.14m, K6=10.64m, K7=24.54m, K8=10.64m] | area_source=public_site_area_text (14624 sq ft) | method=public_doc_or_image_plus_site_area | planning_refs=14/11168/FULL; 14/11168/LBC; 18/02453/CLEUD | lot_refs= | title_refs= | doc_evidence=yes | NOT original/verified boundary; derived candidate geometry for display and review."},"OTM-18173176":{"listing_id":"OTM-18173176","confidence":"medium","previous_confidence":"medium_low","candidate_class":"candidate_medium_doc_area","area_m2":"404.686","computed_area_m2":"386.27","perimeter_m":"72.16","side_lengths_m_json":"[11.8, 6.209, 11.862, 6.209, 11.8, 6.209, 11.862, 6.209]","area_source":"public_site_area_text","area_raw":"0.10 acre","method":"public_doc_or_image_plus_site_area","planning_refs":"18/01165/FUL","lot_refs":"","title_refs":"","doc_evidence":"yes","note":"estimated_candidate_not_verified | confidence=medium | previous_confidence=medium_low | class=candidate_medium_doc_area | reason=public document/image evidence plus public area text | area=404.69 mÂ² | computed_polygon_area=386.27 mÂ² | perimeter=72.16 m | sides=[K1=11.80m, K2=6.21m, K3=11.86m, K4=6.21m, K5=11.80m, K6=6.21m, K7=11.86m, K8=6.21m] | area_source=public_site_area_text (0.10 acre) | method=public_doc_or_image_plus_site_area | planning_refs=18/01165/FUL | lot_refs= | title_refs= | doc_evidence=yes | NOT original/verified boundary; derived candidate geometry for display and review."},"OTM-19302958":{"listing_id":"OTM-19302958","confidence":"medium","previous_confidence":"medium_low","candidate_class":"candidate_medium_doc_area","area_m2":"3237.485","computed_area_m2":"3262.97","perimeter_m":"209.606","side_lengths_m_json":"[33.788, 18.326, 34.363, 18.326, 33.788, 18.326, 34.363, 18.326]","area_source":"public_site_area_text","area_raw":"0.8 Acres","method":"public_doc_or_image_plus_site_area","planning_refs":"24/02474/FUL","lot_refs":"","title_refs":"","doc_evidence":"yes","note":"estimated_candidate_not_verified | confidence=medium | previous_confidence=medium_low | class=candidate_medium_doc_area | reason=public document/image evidence plus public area text | area=3,237.49 mÂ² | computed_polygon_area=3,262.97 mÂ² | perimeter=209.61 m | sides=[K1=33.79m, K2=18.33m, K3=34.36m, K4=18.33m, K5=33.79m, K6=18.33m, K7=34.36m, K8=18.33m] | area_source=public_site_area_text (0.8 Acres) | method=public_doc_or_image_plus_site_area | planning_refs=24/02474/FUL | lot_refs= | title_refs= | doc_evidence=yes | NOT original/verified boundary; derived candidate geometry for display and review."},"OTM-18946248":{"listing_id":"OTM-18946248","confidence":"medium","previous_confidence":"medium_low","candidate_class":"candidate_medium_doc_area","area_m2":"7324.81","computed_area_m2":"7304.425","perimeter_m":"313.513","side_lengths_m_json":"[51.815, 28.148, 48.646, 28.148, 51.814, 28.148, 48.646, 28.148]","area_source":"public_site_area_text","area_raw":"1.81 acre","method":"public_doc_or_image_plus_site_area","planning_refs":"","lot_refs":"","title_refs":"","doc_evidence":"yes","note":"estimated_candidate_not_verified | confidence=medium | previous_confidence=medium_low | class=candidate_medium_doc_area | reason=public document/image evidence plus public area text | area=7,324.81 mÂ² | computed_polygon_area=7,304.43 mÂ² | perimeter=313.51 m | sides=[K1=51.81m, K2=28.15m, K3=48.65m, K4=28.15m, K5=51.81m, K6=28.15m, K7=48.65m, K8=28.15m] | area_source=public_site_area_text (1.81 acre) | method=public_doc_or_image_plus_site_area | planning_refs= | lot_refs= | title_refs= | doc_evidence=yes | NOT original/verified boundary; derived candidate geometry for display and review."},"OTM-18641368":{"listing_id":"OTM-18641368","confidence":"medium","previous_confidence":"medium","candidate_class":"candidate_medium_visual_plan","area_m2":"1011.714","computed_area_m2":"1019.678","perimeter_m":"117.174","side_lengths_m_json":"[18.888, 10.245, 19.209, 10.245, 18.888, 10.245, 19.209, 10.245]","area_source":"public_site_area_text","area_raw":"0.25 Acre","method":"public_planning_visual_plan_no_georef","planning_refs":"24/00246/FUL","lot_refs":"","title_refs":"","doc_evidence":"yes","note":"estimated_candidate_not_verified | confidence=medium | previous_confidence=medium | class=candidate_medium_visual_plan | reason=public planning visual/site-plan evidence exists; no georeference | area=1,011.71 mÂ² | computed_polygon_area=1,019.68 mÂ² | perimeter=117.17 m | sides=[K1=18.89m, K2=10.24m, K3=19.21m, K4=10.24m, K5=18.89m, K6=10.24m, K7=19.21m, K8=10.24m] | area_source=public_site_area_text (0.25 Acre) | method=public_planning_visual_plan_no_georef | planning_refs=24/00246/FUL | lot_refs= | title_refs= | doc_evidence=yes | NOT original/verified boundary; derived candidate geometry for display and review."},"OTM-19248294":{"listing_id":"OTM-19248294","confidence":"medium_low","previous_confidence":"low_plus","candidate_class":"candidate_medium_low_area_only","area_m2":"2832.799","computed_area_m2":"2958.088","perimeter_m":"199.509","side_lengths_m_json":"[31.857, 17.629, 32.64, 17.629, 31.856, 17.629, 32.64, 17.629]","area_source":"public_site_area_text","area_raw":"0.70 acre","method":"public_site_area_and_centroid","planning_refs":"","lot_refs":"","title_refs":"","doc_evidence":"no","note":"estimated_candidate_not_verified | confidence=medium_low | previous_confidence=low_plus | class=candidate_medium_low_area_only | reason=public area text and centroid; no plan/georef | area=2,832.80 mÂ² | computed_polygon_area=2,958.09 mÂ² | perimeter=199.51 m | sides=[K1=31.86m, K2=17.63m, K3=32.64m, K4=17.63m, K5=31.86m, K6=17.63m, K7=32.64m, K8=17.63m] | area_source=public_site_area_text (0.70 acre) | method=public_site_area_and_centroid | planning_refs= | lot_refs= | title_refs= | doc_evidence=no | NOT original/verified boundary; derived candidate geometry for display and review."},"OTM-17653723":{"listing_id":"OTM-17653723","confidence":"medium_low","previous_confidence":"low_plus","candidate_class":"candidate_medium_low_area_only","area_m2":"1200.029","computed_area_m2":"1145.419","perimeter_m":"124.254","side_lengths_m_json":"[20.319, 10.691, 20.426, 10.691, 20.319, 10.691, 20.426, 10.691]","area_source":"public_site_area_text","area_raw":"12917 sq ft","method":"public_site_area_and_centroid","planning_refs":"","lot_refs":"","title_refs":"","doc_evidence":"no","note":"estimated_candidate_not_verified | confidence=medium_low | previous_confidence=low_plus | class=candidate_medium_low_area_only | reason=public area text and centroid; no plan/georef | area=1,200.03 mÂ² | computed_polygon_area=1,145.42 mÂ² | perimeter=124.25 m | sides=[K1=20.32m, K2=10.69m, K3=20.43m, K4=10.69m, K5=20.32m, K6=10.69m, K7=20.43m, K8=10.69m] | area_source=public_site_area_text (12917 sq ft) | method=public_site_area_and_centroid | planning_refs= | lot_refs= | title_refs= | doc_evidence=no | NOT original/verified boundary; derived candidate geometry for display and review."},"OTM-18726804":{"listing_id":"OTM-18726804","confidence":"medium","previous_confidence":"medium_low","candidate_class":"candidate_medium_doc_area","area_m2":"185.806","computed_area_m2":"183.934","perimeter_m":"49.776","side_lengths_m_json":"[8.062, 4.329, 8.168, 4.329, 8.062, 4.329, 8.168, 4.329]","area_source":"public_site_area_text","area_raw":"2000sqft","method":"public_doc_or_image_plus_site_area","planning_refs":"","lot_refs":"TOGETHER","title_refs":"","doc_evidence":"yes","note":"estimated_candidate_not_verified | confidence=medium | previous_confidence=medium_low | class=candidate_medium_doc_area | reason=public document/image evidence plus public area text | area=185.81 mÂ² | computed_polygon_area=183.93 mÂ² | perimeter=49.78 m | sides=[K1=8.06m, K2=4.33m, K3=8.17m, K4=4.33m, K5=8.06m, K6=4.33m, K7=8.17m, K8=4.33m] | area_source=public_site_area_text (2000sqft) | method=public_doc_or_image_plus_site_area | planning_refs= | lot_refs=TOGETHER | title_refs= | doc_evidence=yes | NOT original/verified boundary; derived candidate geometry for display and review."},"OTM-19165061":{"listing_id":"OTM-19165061","confidence":"medium","previous_confidence":"medium_low","candidate_class":"candidate_medium_doc_area","area_m2":"88.0","computed_area_m2":"93.721","perimeter_m":"35.582","side_lengths_m_json":"[5.959, 2.98, 5.872, 2.98, 5.959, 2.98, 5.872, 2.98]","area_source":"public_site_area_text","area_raw":"88 sq m","method":"public_doc_or_image_plus_site_area","planning_refs":"25/00214/FUL","lot_refs":"","title_refs":"","doc_evidence":"yes","note":"estimated_candidate_not_verified | confidence=medium | previous_confidence=medium_low | class=candidate_medium_doc_area | reason=public document/image evidence plus public area text | area=88.00 mÂ² | computed_polygon_area=93.72 mÂ² | perimeter=35.58 m | sides=[K1=5.96m, K2=2.98m, K3=5.87m, K4=2.98m, K5=5.96m, K6=2.98m, K7=5.87m, K8=2.98m] | area_source=public_site_area_text (88 sq m) | method=public_doc_or_image_plus_site_area | planning_refs=25/00214/FUL | lot_refs= | title_refs= | doc_evidence=yes | NOT original/verified boundary; derived candidate geometry for display and review."},"OTM-18774177":{"listing_id":"OTM-18774177","confidence":"medium_low","previous_confidence":"low","candidate_class":"candidate_medium_low_doc_only","area_m2":"2808.892","computed_area_m2":"2801.075","perimeter_m":"194.144","side_lengths_m_json":"[32.086, 17.431, 30.124, 17.431, 32.086, 17.431, 30.124, 17.431]","area_source":"feed_bbox_area_fallback","area_raw":"feed_bbox_area_m2=2808.89","method":"feed_bbox_area_scaled_candidate","planning_refs":"","lot_refs":"","title_refs":"","doc_evidence":"yes","note":"estimated_candidate_not_verified | confidence=medium_low | previous_confidence=low | class=candidate_medium_low_doc_only | reason=public document/image evidence but no public site area | area=2,808.89 mÂ² | computed_polygon_area=2,801.07 mÂ² | perimeter=194.14 m | sides=[K1=32.09m, K2=17.43m, K3=30.12m, K4=17.43m, K5=32.09m, K6=17.43m, K7=30.12m, K8=17.43m] | area_source=feed_bbox_area_fallback (feed_bbox_area_m2=2808.89) | method=feed_bbox_area_scaled_candidate | planning_refs= | lot_refs= | title_refs= | doc_evidence=yes | NOT original/verified boundary; derived candidate geometry for display and review."},"OTM-19294387":{"listing_id":"OTM-19294387","confidence":"medium_low","previous_confidence":"low_plus","candidate_class":"candidate_medium_low_area_only","area_m2":"1416.4","computed_area_m2":"1438.196","perimeter_m":"139.076","side_lengths_m_json":"[22.869, 12.551, 21.567, 12.551, 22.869, 12.551, 21.567, 12.551]","area_source":"public_site_area_text","area_raw":"0.35 acre","method":"public_site_area_and_centroid","planning_refs":"","lot_refs":"","title_refs":"","doc_evidence":"no","note":"estimated_candidate_not_verified | confidence=medium_low | previous_confidence=low_plus | class=candidate_medium_low_area_only | reason=public area text and centroid; no plan/georef | area=1,416.40 mÂ² | computed_polygon_area=1,438.20 mÂ² | perimeter=139.08 m | sides=[K1=22.87m, K2=12.55m, K3=21.57m, K4=12.55m, K5=22.87m, K6=12.55m, K7=21.57m, K8=12.55m] | area_source=public_site_area_text (0.35 acre) | method=public_site_area_and_centroid | planning_refs= | lot_refs= | title_refs= | doc_evidence=no | NOT original/verified boundary; derived candidate geometry for display and review."},"OTM-19260848":{"listing_id":"OTM-19260848","confidence":"medium","previous_confidence":"low_plus","candidate_class":"candidate_medium_ref_area","area_m2":"100.0","computed_area_m2":"102.597","perimeter_m":"37.16","side_lengths_m_json":"[5.962, 3.266, 6.086, 3.266, 5.962, 3.266, 6.086, 3.266]","area_source":"public_site_area_text","area_raw":"0.01 hectares","method":"public_site_area_and_centroid","planning_refs":"","lot_refs":"19; DETAILS; DURING; S; WILL","title_refs":"","doc_evidence":"no","note":"estimated_candidate_not_verified | confidence=medium | previous_confidence=low_plus | class=candidate_medium_ref_area | reason=public area text plus planning/lot/title reference | area=100.00 mÂ² | computed_polygon_area=102.60 mÂ² | perimeter=37.16 m | sides=[K1=5.96m, K2=3.27m, K3=6.09m, K4=3.27m, K5=5.96m, K6=3.27m, K7=6.09m, K8=3.27m] | area_source=public_site_area_text (0.01 hectares) | method=public_site_area_and_centroid | planning_refs= | lot_refs=19; DETAILS; DURING; S; WILL | title_refs= | doc_evidence=no | NOT original/verified boundary; derived candidate geometry for display and review."},"OTM-19100481":{"listing_id":"OTM-19100481","confidence":"medium_low","previous_confidence":"low","candidate_class":"candidate_medium_low_ref_feed","area_m2":"356.954","computed_area_m2":"347.663","perimeter_m":"68.616","side_lengths_m_json":"[11.769, 5.59, 11.359, 5.59, 11.769, 5.59, 11.359, 5.59]","area_source":"feed_bbox_area_fallback","area_raw":"feed_bbox_area_m2=356.95","method":"feed_bbox_area_scaled_candidate","planning_refs":"","lot_refs":"9","title_refs":"","doc_evidence":"no","note":"estimated_candidate_not_verified | confidence=medium_low | previous_confidence=low | class=candidate_medium_low_ref_feed | reason=reference evidence plus feed-scaled area fallback | area=356.95 mÂ² | computed_polygon_area=347.66 mÂ² | perimeter=68.62 m | sides=[K1=11.77m, K2=5.59m, K3=11.36m, K4=5.59m, K5=11.77m, K6=5.59m, K7=11.36m, K8=5.59m] | area_source=feed_bbox_area_fallback (feed_bbox_area_m2=356.95) | method=feed_bbox_area_scaled_candidate | planning_refs= | lot_refs=9 | title_refs= | doc_evidence=no | NOT original/verified boundary; derived candidate geometry for display and review."},"OTM-17994681":{"listing_id":"OTM-17994681","confidence":"medium_low","previous_confidence":"low_plus","candidate_class":"candidate_medium_low_area_only","area_m2":"566.0","computed_area_m2":"595.541","perimeter_m":"89.45","side_lengths_m_json":"[14.561, 8.156, 13.852, 8.156, 14.561, 8.156, 13.852, 8.156]","area_source":"public_site_area_text","area_raw":"566mÂ²","method":"public_site_area_and_centroid","planning_refs":"","lot_refs":"","title_refs":"","doc_evidence":"no","note":"estimated_candidate_not_verified | confidence=medium_low | previous_confidence=low_plus | class=candidate_medium_low_area_only | reason=public area text and centroid; no plan/georef | area=566.00 mÂ² | computed_polygon_area=595.54 mÂ² | perimeter=89.45 m | sides=[K1=14.56m, K2=8.16m, K3=13.85m, K4=8.16m, K5=14.56m, K6=8.16m, K7=13.85m, K8=8.16m] | area_source=public_site_area_text (566mÂ²) | method=public_site_area_and_centroid | planning_refs= | lot_refs= | title_refs= | doc_evidence=no | NOT original/verified boundary; derived candidate geometry for display and review."},"OTM-13262366":{"listing_id":"OTM-13262366","confidence":"medium","previous_confidence":"medium_low","candidate_class":"candidate_medium_doc_area","area_m2":"650.321","computed_area_m2":"692.597","perimeter_m":"96.724","side_lengths_m_json":"[16.2, 8.1, 15.962, 8.1, 16.2, 8.1, 15.962, 8.1]","area_source":"public_site_area_text","area_raw":"7,000sqft","method":"public_doc_or_image_plus_site_area","planning_refs":"","lot_refs":"","title_refs":"","doc_evidence":"yes","note":"estimated_candidate_not_verified | confidence=medium | previous_confidence=medium_low | class=candidate_medium_doc_area | reason=public document/image evidence plus public area text | area=650.32 mÂ² | computed_polygon_area=692.60 mÂ² | perimeter=96.72 m | sides=[K1=16.20m, K2=8.10m, K3=15.96m, K4=8.10m, K5=16.20m, K6=8.10m, K7=15.96m, K8=8.10m] | area_source=public_site_area_text (7,000sqft) | method=public_doc_or_image_plus_site_area | planning_refs= | lot_refs= | title_refs= | doc_evidence=yes | NOT original/verified boundary; derived candidate geometry for display and review."},"OTM-16150555":{"listing_id":"OTM-16150555","confidence":"medium_low","previous_confidence":"low_plus","candidate_class":"candidate_medium_low_area_only","area_m2":"4046.856","computed_area_m2":"4235.006","perimeter_m":"239.236","side_lengths_m_json":"[40.258, 19.925, 39.51, 19.925, 40.258, 19.925, 39.51, 19.925]","area_source":"public_site_area_text","area_raw":"1 acre","method":"public_site_area_and_centroid","planning_refs":"","lot_refs":"","title_refs":"","doc_evidence":"no","note":"estimated_candidate_not_verified | confidence=medium_low | previous_confidence=low_plus | class=candidate_medium_low_area_only | reason=public area text and centroid; no plan/georef | area=4,046.86 mÂ² | computed_polygon_area=4,235.01 mÂ² | perimeter=239.24 m | sides=[K1=40.26m, K2=19.93m, K3=39.51m, K4=19.93m, K5=40.26m, K6=19.93m, K7=39.51m, K8=19.93m] | area_source=public_site_area_text (1 acre) | method=public_site_area_and_centroid | planning_refs= | lot_refs= | title_refs= | doc_evidence=no | NOT original/verified boundary; derived candidate geometry for display and review."},"OTM-19260836":{"listing_id":"OTM-19260836","confidence":"medium","previous_confidence":"low_plus","candidate_class":"candidate_medium_ref_area","area_m2":"23600.0","computed_area_m2":"22942.315","perimeter_m":"555.999","side_lengths_m_json":"[90.487, 48.097, 91.321, 48.096, 90.484, 48.096, 91.321, 48.097]","area_source":"public_site_area_text","area_raw":"2.36 hectares","method":"public_site_area_and_centroid","planning_refs":"","lot_refs":"100; DETAILS; DURING; S; WILL","title_refs":"","doc_evidence":"no","note":"estimated_candidate_not_verified | confidence=medium | previous_confidence=low_plus | class=candidate_medium_ref_area | reason=public area text plus planning/lot/title reference | area=23,600.00 mÂ² | computed_polygon_area=22,942.31 mÂ² | perimeter=556.00 m | sides=[K1=90.49m, K2=48.10m, K3=91.32m, K4=48.10m, K5=90.48m, K6=48.10m, K7=91.32m, K8=48.10m] | area_source=public_site_area_text (2.36 hectares) | method=public_site_area_and_centroid | planning_refs= | lot_refs=100; DETAILS; DURING; S; WILL | title_refs= | doc_evidence=no | NOT original/verified boundary; derived candidate geometry for display and review."},"OTM-19122248":{"listing_id":"OTM-19122248","confidence":"medium","previous_confidence":"medium_low","candidate_class":"candidate_medium_doc_area","area_m2":"87.979","computed_area_m2":"93.698","perimeter_m":"35.576","side_lengths_m_json":"[5.959, 2.979, 5.871, 2.979, 5.959, 2.979, 5.871, 2.979]","area_source":"public_site_area_text","area_raw":"947 sq ft","method":"public_doc_or_image_plus_site_area","planning_refs":"26/00076/FUL","lot_refs":"COMPRISES","title_refs":"","doc_evidence":"yes","note":"estimated_candidate_not_verified | confidence=medium | previous_confidence=medium_low | class=candidate_medium_doc_area | reason=public document/image evidence plus public area text | area=87.98 mÂ² | computed_polygon_area=93.70 mÂ² | perimeter=35.58 m | sides=[K1=5.96m, K2=2.98m, K3=5.87m, K4=2.98m, K5=5.96m, K6=2.98m, K7=5.87m, K8=2.98m] | area_source=public_site_area_text (947 sq ft) | method=public_doc_or_image_plus_site_area | planning_refs=26/00076/FUL | lot_refs=COMPRISES | title_refs= | doc_evidence=yes | NOT original/verified boundary; derived candidate geometry for display and review."},"OTM-17888180":{"listing_id":"OTM-17888180","confidence":"medium_low","previous_confidence":"low_plus","candidate_class":"candidate_medium_low_area_only","area_m2":"2322.576","computed_area_m2":"2274.266","perimeter_m":"174.987","side_lengths_m_json":"[29.068, 15.63, 27.166, 15.63, 29.067, 15.63, 27.166, 15.63]","area_source":"public_site_area_text","area_raw":"25,000 sq ft","method":"public_site_area_and_centroid","planning_refs":"","lot_refs":"","title_refs":"","doc_evidence":"no","note":"estimated_candidate_not_verified | confidence=medium_low | previous_confidence=low_plus | class=candidate_medium_low_area_only | reason=public area text and centroid; no plan/georef | area=2,322.58 mÂ² | computed_polygon_area=2,274.27 mÂ² | perimeter=174.99 m | sides=[K1=29.07m, K2=15.63m, K3=27.17m, K4=15.63m, K5=29.07m, K6=15.63m, K7=27.17m, K8=15.63m] | area_source=public_site_area_text (25,000 sq ft) | method=public_site_area_and_centroid | planning_refs= | lot_refs= | title_refs= | doc_evidence=no | NOT original/verified boundary; derived candidate geometry for display and review."},"OTM-18138752":{"listing_id":"OTM-18138752","confidence":"medium_low","previous_confidence":"low_plus","candidate_class":"candidate_medium_low_area_only","area_m2":"19343.974","computed_area_m2":"18804.896","perimeter_m":"503.376","side_lengths_m_json":"[81.922, 43.545, 82.678, 43.544, 81.92, 43.544, 82.678, 43.545]","area_source":"public_site_area_text","area_raw":"4.78 Acres","method":"public_site_area_and_centroid","planning_refs":"","lot_refs":"","title_refs":"","doc_evidence":"no","note":"estimated_candidate_not_verified | confidence=medium_low | previous_confidence=low_plus | class=candidate_medium_low_area_only | reason=public area text and centroid; no plan/georef | area=19,343.97 mÂ² | computed_polygon_area=18,804.90 mÂ² | perimeter=503.38 m | sides=[K1=81.92m, K2=43.55m, K3=82.68m, K4=43.54m, K5=81.92m, K6=43.54m, K7=82.68m, K8=43.55m] | area_source=public_site_area_text (4.78 Acres) | method=public_site_area_and_centroid | planning_refs= | lot_refs= | title_refs= | doc_evidence=no | NOT original/verified boundary; derived candidate geometry for display and review."},"OTM-17277793":{"listing_id":"OTM-17277793","confidence":"medium_low","previous_confidence":"low_plus","candidate_class":"candidate_medium_low_area_only","area_m2":"44.036","computed_area_m2":"44.714","perimeter_m":"24.522","side_lengths_m_json":"[4.032, 2.213, 3.803, 2.213, 4.032, 2.213, 3.803, 2.213]","area_source":"public_site_area_text","area_raw":"474 sq ft","method":"public_site_area_and_centroid","planning_refs":"","lot_refs":"","title_refs":"","doc_evidence":"no","note":"estimated_candidate_not_verified | confidence=medium_low | previous_confidence=low_plus | class=candidate_medium_low_area_only | reason=public area text and centroid; no plan/georef | area=44.04 mÂ² | computed_polygon_area=44.71 mÂ² | perimeter=24.52 m | sides=[K1=4.03m, K2=2.21m, K3=3.80m, K4=2.21m, K5=4.03m, K6=2.21m, K7=3.80m, K8=2.21m] | area_source=public_site_area_text (474 sq ft) | method=public_site_area_and_centroid | planning_refs= | lot_refs= | title_refs= | doc_evidence=no | NOT original/verified boundary; derived candidate geometry for display and review."},"OTM-18195742":{"listing_id":"OTM-18195742","confidence":"medium_low","previous_confidence":"low_plus","candidate_class":"candidate_medium_low_area_only","area_m2":"2832.799","computed_area_m2":"2855.099","perimeter_m":"196.072","side_lengths_m_json":"[31.606, 17.143, 32.144, 17.143, 31.606, 17.143, 32.144, 17.143]","area_source":"public_site_area_text","area_raw":"0.70 acre","method":"public_site_area_and_centroid","planning_refs":"","lot_refs":"","title_refs":"","doc_evidence":"no","note":"estimated_candidate_not_verified | confidence=medium_low | previous_confidence=low_plus | class=candidate_medium_low_area_only | reason=public area text and centroid; no plan/georef | area=2,832.80 mÂ² | computed_polygon_area=2,855.10 mÂ² | perimeter=196.07 m | sides=[K1=31.61m, K2=17.14m, K3=32.14m, K4=17.14m, K5=31.61m, K6=17.14m, K7=32.14m, K8=17.14m] | area_source=public_site_area_text (0.70 acre) | method=public_site_area_and_centroid | planning_refs= | lot_refs= | title_refs= | doc_evidence=no | NOT original/verified boundary; derived candidate geometry for display and review."},"OTM-18640375":{"listing_id":"OTM-18640375","confidence":"medium","previous_confidence":"medium_low","candidate_class":"candidate_medium_doc_area","area_m2":"2832.799","computed_area_m2":"2703.887","perimeter_m":"190.914","side_lengths_m_json":"[31.219, 16.427, 31.384, 16.427, 31.219, 16.427, 31.384, 16.427]","area_source":"public_site_area_text","area_raw":"0.7 acres","method":"public_doc_or_image_plus_site_area","planning_refs":"22/03153/FULM","lot_refs":"","title_refs":"","doc_evidence":"yes","note":"estimated_candidate_not_verified | confidence=medium | previous_confidence=medium_low | class=candidate_medium_doc_area | reason=public document/image evidence plus public area text | area=2,832.80 mÂ² | computed_polygon_area=2,703.89 mÂ² | perimeter=190.91 m | sides=[K1=31.22m, K2=16.43m, K3=31.38m, K4=16.43m, K5=31.22m, K6=16.43m, K7=31.38m, K8=16.43m] | area_source=public_site_area_text (0.7 acres) | method=public_doc_or_image_plus_site_area | planning_refs=22/03153/FULM | lot_refs= | title_refs= | doc_evidence=yes | NOT original/verified boundary; derived candidate geometry for display and review."},"OTM-19248577":{"listing_id":"OTM-19248577","confidence":"medium","previous_confidence":"medium_low","candidate_class":"candidate_medium_doc_area","area_m2":"20234.282","computed_area_m2":"20545.647","perimeter_m":"525.66","side_lengths_m_json":"[86.438, 47.439, 81.515, 47.439, 86.436, 47.439, 81.515, 47.439]","area_source":"public_site_area_text","area_raw":"5.00 acre","method":"public_doc_or_image_plus_site_area","planning_refs":"","lot_refs":"","title_refs":"","doc_evidence":"yes","note":"estimated_candidate_not_verified | confidence=medium | previous_confidence=medium_low | class=candidate_medium_doc_area | reason=public document/image evidence plus public area text | area=20,234.28 mÂ² | computed_polygon_area=20,545.65 mÂ² | perimeter=525.66 m | sides=[K1=86.44m, K2=47.44m, K3=81.52m, K4=47.44m, K5=86.44m, K6=47.44m, K7=81.52m, K8=47.44m] | area_source=public_site_area_text (5.00 acre) | method=public_doc_or_image_plus_site_area | planning_refs= | lot_refs= | title_refs= | doc_evidence=yes | NOT original/verified boundary; derived candidate geometry for display and review."},"OTM-18046012":{"listing_id":"OTM-18046012","confidence":"medium","previous_confidence":"medium_low","candidate_class":"candidate_medium_doc_area","area_m2":"384.99","computed_area_m2":"361.366","perimeter_m":"69.996","side_lengths_m_json":"[12.122, 5.639, 11.598, 5.639, 12.122, 5.639, 11.598, 5.639]","area_source":"public_site_area_text","area_raw":"4144 sq ft","method":"public_doc_or_image_plus_site_area","planning_refs":"","lot_refs":"COMPRISES","title_refs":"","doc_evidence":"yes","note":"estimated_candidate_not_verified | confidence=medium | previous_confidence=medium_low | class=candidate_medium_doc_area | reason=public document/image evidence plus public area text | area=384.99 mÂ² | computed_polygon_area=361.37 mÂ² | perimeter=70.00 m | sides=[K1=12.12m, K2=5.64m, K3=11.60m, K4=5.64m, K5=12.12m, K6=5.64m, K7=11.60m, K8=5.64m] | area_source=public_site_area_text (4144 sq ft) | method=public_doc_or_image_plus_site_area | planning_refs= | lot_refs=COMPRISES | title_refs= | doc_evidence=yes | NOT original/verified boundary; derived candidate geometry for display and review."},"OTM-19289485":{"listing_id":"OTM-19289485","confidence":"medium","previous_confidence":"medium_low","candidate_class":"candidate_medium_doc_area","area_m2":"161.874","computed_area_m2":"156.909","perimeter_m":"45.908","side_lengths_m_json":"[7.074, 4.207, 7.466, 4.207, 7.074, 4.207, 7.466, 4.207]","area_source":"public_site_area_text","area_raw":"0.04 acres","method":"public_doc_or_image_plus_site_area","planning_refs":"","lot_refs":"","title_refs":"","doc_evidence":"yes","note":"estimated_candidate_not_verified | confidence=medium | previous_confidence=medium_low | class=candidate_medium_doc_area | reason=public document/image evidence plus public area text | area=161.87 mÂ² | computed_polygon_area=156.91 mÂ² | perimeter=45.91 m | sides=[K1=7.07m, K2=4.21m, K3=7.47m, K4=4.21m, K5=7.07m, K6=4.21m, K7=7.47m, K8=4.21m] | area_source=public_site_area_text (0.04 acres) | method=public_doc_or_image_plus_site_area | planning_refs= | lot_refs= | title_refs= | doc_evidence=yes | NOT original/verified boundary; derived candidate geometry for display and review."},"OTM-19039533":{"listing_id":"OTM-19039533","confidence":"medium_low","previous_confidence":"low_plus","candidate_class":"candidate_medium_low_area_only","area_m2":"111.762","computed_area_m2":"104.722","perimeter_m":"37.578","side_lengths_m_json":"[6.175, 3.216, 6.182, 3.216, 6.175, 3.216, 6.182, 3.216]","area_source":"public_site_area_text","area_raw":"1203 sq ft","method":"public_site_area_and_centroid","planning_refs":"","lot_refs":"","title_refs":"","doc_evidence":"no","note":"estimated_candidate_not_verified | confidence=medium_low | previous_confidence=low_plus | class=candidate_medium_low_area_only | reason=public area text and centroid; no plan/georef | area=111.76 mÂ² | computed_polygon_area=104.72 mÂ² | perimeter=37.58 m | sides=[K1=6.17m, K2=3.22m, K3=6.18m, K4=3.22m, K5=6.17m, K6=3.22m, K7=6.18m, K8=3.22m] | area_source=public_site_area_text (1203 sq ft) | method=public_site_area_and_centroid | planning_refs= | lot_refs= | title_refs= | doc_evidence=no | NOT original/verified boundary; derived candidate geometry for display and review."},"OTM-19218227":{"listing_id":"OTM-19218227","confidence":"low_plus","previous_confidence":"low","candidate_class":"candidate_low_plus_feed","area_m2":"912.774","computed_area_m2":"839.457","perimeter_m":"106.416","side_lengths_m_json":"[17.571, 9.058, 17.521, 9.058, 17.571, 9.058, 17.521, 9.058]","area_source":"feed_bbox_area_fallback","area_raw":"feed_bbox_area_m2=912.77","method":"feed_bbox_area_scaled_candidate","planning_refs":"","lot_refs":"","title_refs":"","doc_evidence":"no","note":"estimated_candidate_not_verified | confidence=low_plus | previous_confidence=low | class=candidate_low_plus_feed | reason=feed-scaled candidate; no public area/georef | area=912.77 mÂ² | computed_polygon_area=839.46 mÂ² | perimeter=106.42 m | sides=[K1=17.57m, K2=9.06m, K3=17.52m, K4=9.06m, K5=17.57m, K6=9.06m, K7=17.52m, K8=9.06m] | area_source=feed_bbox_area_fallback (feed_bbox_area_m2=912.77) | method=feed_bbox_area_scaled_candidate | planning_refs= | lot_refs= | title_refs= | doc_evidence=no | NOT original/verified boundary; derived candidate geometry for display and review."},"OTM-19230021":{"listing_id":"OTM-19230021","confidence":"medium_low","previous_confidence":"low_plus","candidate_class":"candidate_medium_low_area_only","area_m2":"11331.198","computed_area_m2":"10942.685","perimeter_m":"385.512","side_lengths_m_json":"[64.641, 30.358, 67.4, 30.358, 64.639, 30.358, 67.4, 30.358]","area_source":"public_site_area_text","area_raw":"2.80 acre","method":"public_site_area_and_centroid","planning_refs":"","lot_refs":"","title_refs":"","doc_evidence":"no","note":"estimated_candidate_not_verified | confidence=medium_low | previous_confidence=low_plus | class=candidate_medium_low_area_only | reason=public area text and centroid; no plan/georef | area=11,331.20 mÂ² | computed_polygon_area=10,942.68 mÂ² | perimeter=385.51 m | sides=[K1=64.64m, K2=30.36m, K3=67.40m, K4=30.36m, K5=64.64m, K6=30.36m, K7=67.40m, K8=30.36m] | area_source=public_site_area_text (2.80 acre) | method=public_site_area_and_centroid | planning_refs= | lot_refs= | title_refs= | doc_evidence=no | NOT original/verified boundary; derived candidate geometry for display and review."},"OTM-17942975":{"listing_id":"OTM-17942975","confidence":"medium","previous_confidence":"medium_low","candidate_class":"candidate_medium_doc_area","area_m2":"297.29","computed_area_m2":"307.313","perimeter_m":"64.27","side_lengths_m_json":"[10.515, 5.83, 9.96, 5.83, 10.515, 5.83, 9.96, 5.83]","area_source":"public_site_area_text","area_raw":"3200 sq ft","method":"public_doc_or_image_plus_site_area","planning_refs":"","lot_refs":"","title_refs":"","doc_evidence":"yes","note":"estimated_candidate_not_verified | confidence=medium | previous_confidence=medium_low | class=candidate_medium_doc_area | reason=public document/image evidence plus public area text | area=297.29 mÂ² | computed_polygon_area=307.31 mÂ² | perimeter=64.27 m | sides=[K1=10.52m, K2=5.83m, K3=9.96m, K4=5.83m, K5=10.52m, K6=5.83m, K7=9.96m, K8=5.83m] | area_source=public_site_area_text (3200 sq ft) | method=public_doc_or_image_plus_site_area | planning_refs= | lot_refs= | title_refs= | doc_evidence=yes | NOT original/verified boundary; derived candidate geometry for display and review."},"OTM-16762917":{"listing_id":"OTM-16762917","confidence":"medium_low","previous_confidence":"low","candidate_class":"candidate_medium_low_ref_feed","area_m2":"291.82","computed_area_m2":"304.726","perimeter_m":"64.034","side_lengths_m_json":"[10.225, 5.658, 10.476, 5.658, 10.225, 5.658, 10.476, 5.658]","area_source":"feed_bbox_area_fallback","area_raw":"feed_bbox_area_m2=291.82","method":"feed_bbox_area_scaled_candidate","planning_refs":"","lot_refs":"2","title_refs":"","doc_evidence":"no","note":"estimated_candidate_not_verified | confidence=medium_low | previous_confidence=low | class=candidate_medium_low_ref_feed | reason=reference evidence plus feed-scaled area fallback | area=291.82 mÂ² | computed_polygon_area=304.73 mÂ² | perimeter=64.03 m | sides=[K1=10.22m, K2=5.66m, K3=10.48m, K4=5.66m, K5=10.22m, K6=5.66m, K7=10.48m, K8=5.66m] | area_source=feed_bbox_area_fallback (feed_bbox_area_m2=291.82) | method=feed_bbox_area_scaled_candidate | planning_refs= | lot_refs=2 | title_refs= | doc_evidence=no | NOT original/verified boundary; derived candidate geometry for display and review."},"OTM-18791832":{"listing_id":"OTM-18791832","confidence":"low_plus","previous_confidence":"low","candidate_class":"candidate_low_plus_feed","area_m2":"284.658","computed_area_m2":"297.248","perimeter_m":"63.242","side_lengths_m_json":"[10.098, 5.588, 10.347, 5.588, 10.098, 5.588, 10.347, 5.588]","area_source":"feed_bbox_area_fallback","area_raw":"feed_bbox_area_m2=284.66","method":"feed_bbox_area_scaled_candidate","planning_refs":"","lot_refs":"","title_refs":"","doc_evidence":"no","note":"estimated_candidate_not_verified | confidence=low_plus | previous_confidence=low | class=candidate_low_plus_feed | reason=feed-scaled candidate; no public area/georef | area=284.66 mÂ² | computed_polygon_area=297.25 mÂ² | perimeter=63.24 m | sides=[K1=10.10m, K2=5.59m, K3=10.35m, K4=5.59m, K5=10.10m, K6=5.59m, K7=10.35m, K8=5.59m] | area_source=feed_bbox_area_fallback (feed_bbox_area_m2=284.66) | method=feed_bbox_area_scaled_candidate | planning_refs= | lot_refs= | title_refs= | doc_evidence=no | NOT original/verified boundary; derived candidate geometry for display and review."},"OTM-18066851":{"listing_id":"OTM-18066851","confidence":"medium_low","previous_confidence":"low","candidate_class":"candidate_medium_low_doc_only","area_m2":"11.721","computed_area_m2":"11.394","perimeter_m":"12.39","side_lengths_m_json":"[2.016, 1.072, 2.035, 1.072, 2.016, 1.072, 2.035, 1.072]","area_source":"feed_bbox_area_fallback","area_raw":"feed_bbox_area_m2=11.72","method":"feed_bbox_area_scaled_candidate","planning_refs":"","lot_refs":"","title_refs":"SGL266391","doc_evidence":"yes","note":"estimated_candidate_not_verified | confidence=medium_low | previous_confidence=low | class=candidate_medium_low_doc_only | reason=public document/image evidence but no public site area | area=11.72 mÂ² | computed_polygon_area=11.39 mÂ² | perimeter=12.39 m | sides=[K1=2.02m, K2=1.07m, K3=2.04m, K4=1.07m, K5=2.02m, K6=1.07m, K7=2.04m, K8=1.07m] | area_source=feed_bbox_area_fallback (feed_bbox_area_m2=11.72) | method=feed_bbox_area_scaled_candidate | planning_refs= | lot_refs= | title_refs=SGL266391 | doc_evidence=yes | NOT original/verified boundary; derived candidate geometry for display and review."},"OTM-13486283":{"listing_id":"OTM-13486283","confidence":"medium","previous_confidence":"medium_low","candidate_class":"candidate_medium_doc_area","area_m2":"282.983","computed_area_m2":"275.097","perimeter_m":"60.884","side_lengths_m_json":"[9.908, 5.267, 10.0, 5.267, 9.908, 5.267, 10.0, 5.267]","area_source":"public_site_area_text","area_raw":"3046 sq ft","method":"public_doc_or_image_plus_site_area","planning_refs":"17/00567/FUL","lot_refs":"","title_refs":"","doc_evidence":"yes","note":"estimated_candidate_not_verified | confidence=medium | previous_confidence=medium_low | class=candidate_medium_doc_area | reason=public document/image evidence plus public area text | area=282.98 mÂ² | computed_polygon_area=275.10 mÂ² | perimeter=60.88 m | sides=[K1=9.91m, K2=5.27m, K3=10.00m, K4=5.27m, K5=9.91m, K6=5.27m, K7=10.00m, K8=5.27m] | area_source=public_site_area_text (3046 sq ft) | method=public_doc_or_image_plus_site_area | planning_refs=17/00567/FUL | lot_refs= | title_refs= | doc_evidence=yes | NOT original/verified boundary; derived candidate geometry for display and review."},"OTM-15986296":{"listing_id":"OTM-15986296","confidence":"low_plus","previous_confidence":"low","candidate_class":"candidate_low_plus_feed","area_m2":"5841.752","computed_area_m2":"5662.557","perimeter_m":"275.791","side_lengths_m_json":"[42.496, 25.276, 44.849, 25.275, 42.495, 25.275, 44.849, 25.276]","area_source":"feed_bbox_area_fallback","area_raw":"feed_bbox_area_m2=5841.75","method":"feed_bbox_area_scaled_candidate","planning_refs":"","lot_refs":"","title_refs":"","doc_evidence":"no","note":"estimated_candidate_not_verified | confidence=low_plus | previous_confidence=low | class=candidate_low_plus_feed | reason=feed-scaled candidate; no public area/georef | area=5,841.75 mÂ² | computed_polygon_area=5,662.56 mÂ² | perimeter=275.79 m | sides=[K1=42.50m, K2=25.28m, K3=44.85m, K4=25.27m, K5=42.49m, K6=25.27m, K7=44.85m, K8=25.28m] | area_source=feed_bbox_area_fallback (feed_bbox_area_m2=5841.75) | method=feed_bbox_area_scaled_candidate | planning_refs= | lot_refs= | title_refs= | doc_evidence=no | NOT original/verified boundary; derived candidate geometry for display and review."},"OTM-19210677":{"listing_id":"OTM-19210677","confidence":"medium","previous_confidence":"medium_low","candidate_class":"candidate_medium_doc_area","area_m2":"10117.141","computed_area_m2":"9479.842","perimeter_m":"357.54","side_lengths_m_json":"[58.751, 30.599, 58.822, 30.599, 58.749, 30.599, 58.822, 30.599]","area_source":"public_site_area_text","area_raw":"2.50 acre","method":"public_doc_or_image_plus_site_area","planning_refs":"","lot_refs":"","title_refs":"","doc_evidence":"yes","note":"estimated_candidate_not_verified | confidence=medium | previous_confidence=medium_low | class=candidate_medium_doc_area | reason=public document/image evidence plus public area text | area=10,117.14 mÂ² | computed_polygon_area=9,479.84 mÂ² | perimeter=357.54 m | sides=[K1=58.75m, K2=30.60m, K3=58.82m, K4=30.60m, K5=58.75m, K6=30.60m, K7=58.82m, K8=30.60m] | area_source=public_site_area_text (2.50 acre) | method=public_doc_or_image_plus_site_area | planning_refs= | lot_refs= | title_refs= | doc_evidence=yes | NOT original/verified boundary; derived candidate geometry for display and review."},"OTM-19031444":{"listing_id":"OTM-19031444","confidence":"medium","previous_confidence":"medium_low","candidate_class":"candidate_medium_doc_area","area_m2":"98.0","computed_area_m2":"98.973","perimeter_m":"36.59","side_lengths_m_json":"[6.216, 3.014, 6.051, 3.014, 6.216, 3.014, 6.051, 3.014]","area_source":"public_site_area_text","area_raw":"98sqm","method":"public_doc_or_image_plus_site_area","planning_refs":"25/01541/FUL","lot_refs":"","title_refs":"","doc_evidence":"yes","note":"estimated_candidate_not_verified | confidence=medium | previous_confidence=medium_low | class=candidate_medium_doc_area | reason=public document/image evidence plus public area text | area=98.00 mÂ² | computed_polygon_area=98.97 mÂ² | perimeter=36.59 m | sides=[K1=6.22m, K2=3.01m, K3=6.05m, K4=3.01m, K5=6.22m, K6=3.01m, K7=6.05m, K8=3.01m] | area_source=public_site_area_text (98sqm) | method=public_doc_or_image_plus_site_area | planning_refs=25/01541/FUL | lot_refs= | title_refs= | doc_evidence=yes | NOT original/verified boundary; derived candidate geometry for display and review."},"OTM-15166073":{"listing_id":"OTM-15166073","confidence":"medium","previous_confidence":"medium_low","candidate_class":"candidate_medium_doc_area","area_m2":"906.919","computed_area_m2":"965.876","perimeter_m":"114.226","side_lengths_m_json":"[19.131, 9.566, 18.85, 9.566, 19.131, 9.566, 18.85, 9.566]","area_source":"public_site_area_text","area_raw":"9762 sq ft","method":"public_doc_or_image_plus_site_area","planning_refs":"","lot_refs":"","title_refs":"","doc_evidence":"yes","note":"estimated_candidate_not_verified | confidence=medium | previous_confidence=medium_low | class=candidate_medium_doc_area | reason=public document/image evidence plus public area text | area=906.92 mÂ² | computed_polygon_area=965.88 mÂ² | perimeter=114.23 m | sides=[K1=19.13m, K2=9.57m, K3=18.85m, K4=9.57m, K5=19.13m, K6=9.57m, K7=18.85m, K8=9.57m] | area_source=public_site_area_text (9762 sq ft) | method=public_doc_or_image_plus_site_area | planning_refs= | lot_refs= | title_refs= | doc_evidence=yes | NOT original/verified boundary; derived candidate geometry for display and review."},"OTM-19064785":{"listing_id":"OTM-19064785","confidence":"medium","previous_confidence":"medium_low","candidate_class":"candidate_medium_doc_area","area_m2":"59.922","computed_area_m2":"63.675","perimeter_m":"29.268","side_lengths_m_json":"[4.651, 2.6, 4.783, 2.6, 4.651, 2.6, 4.783, 2.6]","area_source":"public_site_area_text","area_raw":"645 sq ft","method":"public_doc_or_image_plus_site_area","planning_refs":"23/00971/FUL","lot_refs":"COMPRISES","title_refs":"","doc_evidence":"yes","note":"estimated_candidate_not_verified | confidence=medium | previous_confidence=medium_low | class=candidate_medium_doc_area | reason=public document/image evidence plus public area text | area=59.92 mÂ² | computed_polygon_area=63.67 mÂ² | perimeter=29.27 m | sides=[K1=4.65m, K2=2.60m, K3=4.78m, K4=2.60m, K5=4.65m, K6=2.60m, K7=4.78m, K8=2.60m] | area_source=public_site_area_text (645 sq ft) | method=public_doc_or_image_plus_site_area | planning_refs=23/00971/FUL | lot_refs=COMPRISES | title_refs= | doc_evidence=yes | NOT original/verified boundary; derived candidate geometry for display and review."},"OTM-18109724":{"listing_id":"OTM-18109724","confidence":"medium","previous_confidence":"medium","candidate_class":"candidate_medium_visual_plan","area_m2":"660.0","computed_area_m2":"606.987","perimeter_m":"90.492","side_lengths_m_json":"[14.941, 7.703, 14.899, 7.703, 14.941, 7.703, 14.899, 7.703]","area_source":"public_site_area_text","area_raw":"660 sqm","method":"public_planning_visual_plan_no_georef","planning_refs":"24/00279/OUT","lot_refs":"","title_refs":"","doc_evidence":"yes","note":"estimated_candidate_not_verified | confidence=medium | previous_confidence=medium | class=candidate_medium_visual_plan | reason=public planning visual/site-plan evidence exists; no georeference | area=660.00 mÂ² | computed_polygon_area=606.99 mÂ² | perimeter=90.49 m | sides=[K1=14.94m, K2=7.70m, K3=14.90m, K4=7.70m, K5=14.94m, K6=7.70m, K7=14.90m, K8=7.70m] | area_source=public_site_area_text (660 sqm) | method=public_planning_visual_plan_no_georef | planning_refs=24/00279/OUT | lot_refs= | title_refs= | doc_evidence=yes | NOT original/verified boundary; derived candidate geometry for display and review."},"OTM-14695987":{"listing_id":"OTM-14695987","confidence":"medium","previous_confidence":"medium_low","candidate_class":"candidate_medium_doc_area","area_m2":"6070.285","computed_area_m2":"6208.979","perimeter_m":"288.704","side_lengths_m_json":"[43.855, 26.869, 46.76, 26.868, 43.855, 26.868, 46.76, 26.869]","area_source":"public_site_area_text","area_raw":"1.50 acre","method":"public_doc_or_image_plus_site_area","planning_refs":"","lot_refs":"","title_refs":"","doc_evidence":"yes","note":"estimated_candidate_not_verified | confidence=medium | previous_confidence=medium_low | class=candidate_medium_doc_area | reason=public document/image evidence plus public area text | area=6,070.28 mÂ² | computed_polygon_area=6,208.98 mÂ² | perimeter=288.70 m | sides=[K1=43.85m, K2=26.87m, K3=46.76m, K4=26.87m, K5=43.85m, K6=26.87m, K7=46.76m, K8=26.87m] | area_source=public_site_area_text (1.50 acre) | method=public_doc_or_image_plus_site_area | planning_refs= | lot_refs= | title_refs= | doc_evidence=yes | NOT original/verified boundary; derived candidate geometry for display and review."},"OTM-14762234":{"listing_id":"OTM-14762234","confidence":"medium","previous_confidence":"medium_low","candidate_class":"candidate_medium_doc_area","area_m2":"45324.792","computed_area_m2":"48271.266","perimeter_m":"807.503","side_lengths_m_json":"[135.248, 67.624, 133.26, 67.623, 135.241, 67.623, 133.26, 67.624]","area_source":"public_site_area_text","area_raw":"11.20 acre","method":"public_doc_or_image_plus_site_area","planning_refs":"","lot_refs":"","title_refs":"","doc_evidence":"yes","note":"estimated_candidate_not_verified | confidence=medium | previous_confidence=medium_low | class=candidate_medium_doc_area | reason=public document/image evidence plus public area text | area=45,324.79 mÂ² | computed_polygon_area=48,271.27 mÂ² | perimeter=807.50 m | sides=[K1=135.25m, K2=67.62m, K3=133.26m, K4=67.62m, K5=135.24m, K6=67.62m, K7=133.26m, K8=67.62m] | area_source=public_site_area_text (11.20 acre) | method=public_doc_or_image_plus_site_area | planning_refs= | lot_refs= | title_refs= | doc_evidence=yes | NOT original/verified boundary; derived candidate geometry for display and review."},"OTM-19088694":{"listing_id":"OTM-19088694","confidence":"medium","previous_confidence":"low_plus","candidate_class":"candidate_medium_ref_area","area_m2":"1820.992","computed_area_m2":"1916.033","perimeter_m":"160.44","side_lengths_m_json":"[26.118, 14.628, 24.846, 14.628, 26.118, 14.628, 24.846, 14.628]","area_source":"public_site_area_text","area_raw":"19601 sq ft","method":"public_site_area_and_centroid","planning_refs":"","lot_refs":"COMPRISES","title_refs":"","doc_evidence":"no","note":"estimated_candidate_not_verified | confidence=medium | previous_confidence=low_plus | class=candidate_medium_ref_area | reason=public area text plus planning/lot/title reference | area=1,820.99 mÂ² | computed_polygon_area=1,916.03 mÂ² | perimeter=160.44 m | sides=[K1=26.12m, K2=14.63m, K3=24.85m, K4=14.63m, K5=26.12m, K6=14.63m, K7=24.85m, K8=14.63m] | area_source=public_site_area_text (19601 sq ft) | method=public_site_area_and_centroid | planning_refs= | lot_refs=COMPRISES | title_refs= | doc_evidence=no | NOT original/verified boundary; derived candidate geometry for display and review."},"OTM-17552310":{"listing_id":"OTM-17552310","confidence":"medium","previous_confidence":"medium_low","candidate_class":"candidate_medium_doc_area","area_m2":"305.094","computed_area_m2":"297.153","perimeter_m":"63.436","side_lengths_m_json":"[10.88, 5.168, 10.502, 5.168, 10.88, 5.168, 10.502, 5.168]","area_source":"public_site_area_text","area_raw":"3284 sq ft","method":"public_doc_or_image_plus_site_area","planning_refs":"","lot_refs":"","title_refs":"","doc_evidence":"yes","note":"estimated_candidate_not_verified | confidence=medium | previous_confidence=medium_low | class=candidate_medium_doc_area | reason=public document/image evidence plus public area text | area=305.09 mÂ² | computed_polygon_area=297.15 mÂ² | perimeter=63.44 m | sides=[K1=10.88m, K2=5.17m, K3=10.50m, K4=5.17m, K5=10.88m, K6=5.17m, K7=10.50m, K8=5.17m] | area_source=public_site_area_text (3284 sq ft) | method=public_doc_or_image_plus_site_area | planning_refs= | lot_refs= | title_refs= | doc_evidence=yes | NOT original/verified boundary; derived candidate geometry for display and review."},"OTM-19252323":{"listing_id":"OTM-19252323","confidence":"medium_low","previous_confidence":"low_plus","candidate_class":"candidate_medium_low_area_only","area_m2":"809.371","computed_area_m2":"832.14","perimeter_m":"106.072","side_lengths_m_json":"[17.934, 8.786, 17.53, 8.786, 17.934, 8.786, 17.53, 8.786]","area_source":"public_site_area_text","area_raw":"0.20 acre","method":"public_site_area_and_centroid","planning_refs":"","lot_refs":"","title_refs":"","doc_evidence":"no","note":"estimated_candidate_not_verified | confidence=medium_low | previous_confidence=low_plus | class=candidate_medium_low_area_only | reason=public area text and centroid; no plan/georef | area=809.37 mÂ² | computed_polygon_area=832.14 mÂ² | perimeter=106.07 m | sides=[K1=17.93m, K2=8.79m, K3=17.53m, K4=8.79m, K5=17.93m, K6=8.79m, K7=17.53m, K8=8.79m] | area_source=public_site_area_text (0.20 acre) | method=public_site_area_and_centroid | planning_refs= | lot_refs= | title_refs= | doc_evidence=no | NOT original/verified boundary; derived candidate geometry for display and review."},"OTM-13405675":{"listing_id":"OTM-13405675","confidence":"medium_low","previous_confidence":"low_plus","candidate_class":"candidate_medium_low_area_only","area_m2":"100.0","computed_area_m2":"110.25","perimeter_m":"38.574","side_lengths_m_json":"[6.4, 3.266, 6.355, 3.266, 6.4, 3.266, 6.355, 3.266]","area_source":"public_site_area_text","area_raw":"100 m2","method":"public_site_area_and_centroid","planning_refs":"","lot_refs":"","title_refs":"","doc_evidence":"no","note":"estimated_candidate_not_verified | confidence=medium_low | previous_confidence=low_plus | class=candidate_medium_low_area_only | reason=public area text and centroid; no plan/georef | area=100.00 mÂ² | computed_polygon_area=110.25 mÂ² | perimeter=38.57 m | sides=[K1=6.40m, K2=3.27m, K3=6.36m, K4=3.27m, K5=6.40m, K6=3.27m, K7=6.36m, K8=3.27m] | area_source=public_site_area_text (100 m2) | method=public_site_area_and_centroid | planning_refs= | lot_refs= | title_refs= | doc_evidence=no | NOT original/verified boundary; derived candidate geometry for display and review."},"OTM-17350990":{"listing_id":"OTM-17350990","confidence":"medium_low","previous_confidence":"low_plus","candidate_class":"candidate_medium_low_area_only","area_m2":"7608.09","computed_area_m2":"7261.869","perimeter_m":"312.869","side_lengths_m_json":"[51.163, 26.92, 51.432, 26.92, 51.162, 26.92, 51.432, 26.92]","area_source":"public_site_area_text","area_raw":"1.88 acre","method":"public_site_area_and_centroid","planning_refs":"","lot_refs":"","title_refs":"","doc_evidence":"no","note":"estimated_candidate_not_verified | confidence=medium_low | previous_confidence=low_plus | class=candidate_medium_low_area_only | reason=public area text and centroid; no plan/georef | area=7,608.09 mÂ² | computed_polygon_area=7,261.87 mÂ² | perimeter=312.87 m | sides=[K1=51.16m, K2=26.92m, K3=51.43m, K4=26.92m, K5=51.16m, K6=26.92m, K7=51.43m, K8=26.92m] | area_source=public_site_area_text (1.88 acre) | method=public_site_area_and_centroid | planning_refs= | lot_refs= | title_refs= | doc_evidence=no | NOT original/verified boundary; derived candidate geometry for display and review."},"OTM-18474329":{"listing_id":"OTM-18474329","confidence":"medium","previous_confidence":"medium_low","candidate_class":"candidate_medium_doc_area","area_m2":"195.003","computed_area_m2":"200.068","perimeter_m":"51.892","side_lengths_m_json":"[8.325, 4.561, 8.499, 4.561, 8.325, 4.561, 8.499, 4.561]","area_source":"public_site_area_text","area_raw":"2099 sq ft","method":"public_doc_or_image_plus_site_area","planning_refs":"24/01871/PRA","lot_refs":"","title_refs":"","doc_evidence":"yes","note":"estimated_candidate_not_verified | confidence=medium | previous_confidence=medium_low | class=candidate_medium_doc_area | reason=public document/image evidence plus public area text | area=195.00 mÂ² | computed_polygon_area=200.07 mÂ² | perimeter=51.89 m | sides=[K1=8.32m, K2=4.56m, K3=8.50m, K4=4.56m, K5=8.32m, K6=4.56m, K7=8.50m, K8=4.56m] | area_source=public_site_area_text (2099 sq ft) | method=public_doc_or_image_plus_site_area | planning_refs=24/01871/PRA | lot_refs= | title_refs= | doc_evidence=yes | NOT original/verified boundary; derived candidate geometry for display and review."},"OTM-19002859":{"listing_id":"OTM-19002859","confidence":"low_plus","previous_confidence":"low","candidate_class":"candidate_low_plus_feed","area_m2":"15.454","computed_area_m2":"14.751","perimeter_m":"14.1","side_lengths_m_json":"[2.306, 1.213, 2.318, 1.213, 2.306, 1.213, 2.318, 1.213]","area_source":"feed_bbox_area_fallback","area_raw":"feed_bbox_area_m2=15.45","method":"feed_bbox_area_scaled_candidate","planning_refs":"","lot_refs":"","title_refs":"","doc_evidence":"no","note":"estimated_candidate_not_verified | confidence=low_plus | previous_confidence=low | class=candidate_low_plus_feed | reason=feed-scaled candidate; no public area/georef | area=15.45 mÂ² | computed_polygon_area=14.75 mÂ² | perimeter=14.10 m | sides=[K1=2.31m, K2=1.21m, K3=2.32m, K4=1.21m, K5=2.31m, K6=1.21m, K7=2.32m, K8=1.21m] | area_source=feed_bbox_area_fallback (feed_bbox_area_m2=15.45) | method=feed_bbox_area_scaled_candidate | planning_refs= | lot_refs= | title_refs= | doc_evidence=no | NOT original/verified boundary; derived candidate geometry for display and review."},"OTM-19281696":{"listing_id":"OTM-19281696","confidence":"medium","previous_confidence":"medium_low","candidate_class":"candidate_medium_doc_area","area_m2":"528.0","computed_area_m2":"526.531","perimeter_m":"84.172","side_lengths_m_json":"[13.911, 7.557, 13.061, 7.557, 13.911, 7.557, 13.061, 7.557]","area_source":"public_site_area_text","area_raw":"528 sq m","method":"public_doc_or_image_plus_site_area","planning_refs":"25/00649/FUL","lot_refs":"COMPRISES","title_refs":"","doc_evidence":"yes","note":"estimated_candidate_not_verified | confidence=medium | previous_confidence=medium_low | class=candidate_medium_doc_area | reason=public document/image evidence plus public area text | area=528.00 mÂ² | computed_polygon_area=526.53 mÂ² | perimeter=84.17 m | sides=[K1=13.91m, K2=7.56m, K3=13.06m, K4=7.56m, K5=13.91m, K6=7.56m, K7=13.06m, K8=7.56m] | area_source=public_site_area_text (528 sq m) | method=public_doc_or_image_plus_site_area | planning_refs=25/00649/FUL | lot_refs=COMPRISES | title_refs= | doc_evidence=yes | NOT original/verified boundary; derived candidate geometry for display and review."},"OTM-18825135":{"listing_id":"OTM-18825135","confidence":"medium_low","previous_confidence":"low_plus","candidate_class":"candidate_medium_low_area_only","area_m2":"1214.057","computed_area_m2":"1137.581","perimeter_m":"123.858","side_lengths_m_json":"[20.352, 10.6, 20.377, 10.6, 20.352, 10.6, 20.377, 10.6]","area_source":"public_site_area_text","area_raw":"0.30 acre","method":"public_site_area_and_centroid","planning_refs":"","lot_refs":"","title_refs":"","doc_evidence":"no","note":"estimated_candidate_not_verified | confidence=medium_low | previous_confidence=low_plus | class=candidate_medium_low_area_only | reason=public area text and centroid; no plan/georef | area=1,214.06 mÂ² | computed_polygon_area=1,137.58 mÂ² | perimeter=123.86 m | sides=[K1=20.35m, K2=10.60m, K3=20.38m, K4=10.60m, K5=20.35m, K6=10.60m, K7=20.38m, K8=10.60m] | area_source=public_site_area_text (0.30 acre) | method=public_site_area_and_centroid | planning_refs= | lot_refs= | title_refs= | doc_evidence=no | NOT original/verified boundary; derived candidate geometry for display and review."},"OTM-16112915":{"listing_id":"OTM-16112915","confidence":"medium","previous_confidence":"medium_low","candidate_class":"candidate_medium_doc_area","area_m2":"3197.017","computed_area_m2":"3228.747","perimeter_m":"208.995","side_lengths_m_json":"[35.505, 17.216, 34.561, 17.216, 35.504, 17.216, 34.561, 17.216]","area_source":"public_site_area_text","area_raw":"0.79 acre","method":"public_doc_or_image_plus_site_area","planning_refs":"14/1456/FUL","lot_refs":"","title_refs":"","doc_evidence":"yes","note":"estimated_candidate_not_verified | confidence=medium | previous_confidence=medium_low | class=candidate_medium_doc_area | reason=public document/image evidence plus public area text | area=3,197.02 mÂ² | computed_polygon_area=3,228.75 mÂ² | perimeter=209.00 m | sides=[K1=35.51m, K2=17.22m, K3=34.56m, K4=17.22m, K5=35.50m, K6=17.22m, K7=34.56m, K8=17.22m] | area_source=public_site_area_text (0.79 acre) | method=public_doc_or_image_plus_site_area | planning_refs=14/1456/FUL | lot_refs= | title_refs= | doc_evidence=yes | NOT original/verified boundary; derived candidate geometry for display and review."},"OTM-10968251":{"listing_id":"OTM-10968251","confidence":"medium","previous_confidence":"medium_low","candidate_class":"candidate_medium_doc_area","area_m2":"400.639","computed_area_m2":"368.458","perimeter_m":"70.502","side_lengths_m_json":"[11.641, 6.001, 11.608, 6.001, 11.641, 6.001, 11.608, 6.001]","area_source":"public_site_area_text","area_raw":"0.099 acres","method":"public_doc_or_image_plus_site_area","planning_refs":"","lot_refs":"93; 93SELL","title_refs":"","doc_evidence":"yes","note":"estimated_candidate_not_verified | confidence=medium | previous_confidence=medium_low | class=candidate_medium_doc_area | reason=public document/image evidence plus public area text | area=400.64 mÂ² | computed_polygon_area=368.46 mÂ² | perimeter=70.50 m | sides=[K1=11.64m, K2=6.00m, K3=11.61m, K4=6.00m, K5=11.64m, K6=6.00m, K7=11.61m, K8=6.00m] | area_source=public_site_area_text (0.099 acres) | method=public_doc_or_image_plus_site_area | planning_refs= | lot_refs=93; 93SELL | title_refs= | doc_evidence=yes | NOT original/verified boundary; derived candidate geometry for display and review."},"OTM-18785153":{"listing_id":"OTM-18785153","confidence":"medium","previous_confidence":"medium_low","candidate_class":"candidate_medium_doc_area","area_m2":"121.406","computed_area_m2":"124.559","perimeter_m":"40.946","side_lengths_m_json":"[6.569, 3.599, 6.706, 3.599, 6.569, 3.599, 6.706, 3.599]","area_source":"public_site_area_text","area_raw":"0.03 acre","method":"public_doc_or_image_plus_site_area","planning_refs":"","lot_refs":"","title_refs":"","doc_evidence":"yes","note":"estimated_candidate_not_verified | confidence=medium | previous_confidence=medium_low | class=candidate_medium_doc_area | reason=public document/image evidence plus public area text | area=121.41 mÂ² | computed_polygon_area=124.56 mÂ² | perimeter=40.95 m | sides=[K1=6.57m, K2=3.60m, K3=6.71m, K4=3.60m, K5=6.57m, K6=3.60m, K7=6.71m, K8=3.60m] | area_source=public_site_area_text (0.03 acre) | method=public_doc_or_image_plus_site_area | planning_refs= | lot_refs= | title_refs= | doc_evidence=yes | NOT original/verified boundary; derived candidate geometry for display and review."},"OTM-17933968":{"listing_id":"OTM-17933968","confidence":"low_plus","previous_confidence":"low","candidate_class":"candidate_low_plus_feed","area_m2":"157.89","computed_area_m2":"153.047","perimeter_m":"45.338","side_lengths_m_json":"[6.986, 4.155, 7.373, 4.155, 6.986, 4.155, 7.373, 4.155]","area_source":"feed_bbox_area_fallback","area_raw":"feed_bbox_area_m2=157.89","method":"feed_bbox_area_scaled_candidate","planning_refs":"","lot_refs":"","title_refs":"","doc_evidence":"no","note":"estimated_candidate_not_verified | confidence=low_plus | previous_confidence=low | class=candidate_low_plus_feed | reason=feed-scaled candidate; no public area/georef | area=157.89 mÂ² | computed_polygon_area=153.05 mÂ² | perimeter=45.34 m | sides=[K1=6.99m, K2=4.16m, K3=7.37m, K4=4.16m, K5=6.99m, K6=4.16m, K7=7.37m, K8=4.16m] | area_source=feed_bbox_area_fallback (feed_bbox_area_m2=157.89) | method=feed_bbox_area_scaled_candidate | planning_refs= | lot_refs= | title_refs= | doc_evidence=no | NOT original/verified boundary; derived candidate geometry for display and review."},"OTM-18462895":{"listing_id":"OTM-18462895","confidence":"medium_low","previous_confidence":"low_plus","candidate_class":"candidate_medium_low_area_only","area_m2":"121.406","computed_area_m2":"123.274","perimeter_m":"40.718","side_lengths_m_json":"[6.695, 3.675, 6.314, 3.675, 6.695, 3.675, 6.314, 3.675]","area_source":"public_site_area_text","area_raw":"0.03 acre","method":"public_site_area_and_centroid","planning_refs":"","lot_refs":"","title_refs":"","doc_evidence":"no","note":"estimated_candidate_not_verified | confidence=medium_low | previous_confidence=low_plus | class=candidate_medium_low_area_only | reason=public area text and centroid; no plan/georef | area=121.41 mÂ² | computed_polygon_area=123.27 mÂ² | perimeter=40.72 m | sides=[K1=6.70m, K2=3.67m, K3=6.31m, K4=3.67m, K5=6.70m, K6=3.67m, K7=6.31m, K8=3.67m] | area_source=public_site_area_text (0.03 acre) | method=public_site_area_and_centroid | planning_refs= | lot_refs= | title_refs= | doc_evidence=no | NOT original/verified boundary; derived candidate geometry for display and review."},"OTM-18447112":{"listing_id":"OTM-18447112","confidence":"medium_low","previous_confidence":"low_plus","candidate_class":"candidate_medium_low_area_only","area_m2":"139.355","computed_area_m2":"145.834","perimeter_m":"44.396","side_lengths_m_json":"[7.471, 3.698, 7.332, 3.697, 7.471, 3.697, 7.332, 3.698]","area_source":"public_site_area_text","area_raw":"1500 sq.ft","method":"public_site_area_and_centroid","planning_refs":"","lot_refs":"","title_refs":"","doc_evidence":"no","note":"estimated_candidate_not_verified | confidence=medium_low | previous_confidence=low_plus | class=candidate_medium_low_area_only | reason=public area text and centroid; no plan/georef | area=139.35 mÂ² | computed_polygon_area=145.83 mÂ² | perimeter=44.40 m | sides=[K1=7.47m, K2=3.70m, K3=7.33m, K4=3.70m, K5=7.47m, K6=3.70m, K7=7.33m, K8=3.70m] | area_source=public_site_area_text (1500 sq.ft) | method=public_site_area_and_centroid | planning_refs= | lot_refs= | title_refs= | doc_evidence=no | NOT original/verified boundary; derived candidate geometry for display and review."},"OTM-19008892":{"listing_id":"OTM-19008892","confidence":"medium_low","previous_confidence":"low_plus","candidate_class":"candidate_medium_low_area_only","area_m2":"181.997","computed_area_m2":"183.43","perimeter_m":"49.696","side_lengths_m_json":"[8.011, 4.345, 8.147, 4.345, 8.011, 4.345, 8.147, 4.345]","area_source":"public_site_area_text","area_raw":"1959 sq ft","method":"public_site_area_and_centroid","planning_refs":"","lot_refs":"","title_refs":"","doc_evidence":"no","note":"estimated_candidate_not_verified | confidence=medium_low | previous_confidence=low_plus | class=candidate_medium_low_area_only | reason=public area text and centroid; no plan/georef | area=182.00 mÂ² | computed_polygon_area=183.43 mÂ² | perimeter=49.70 m | sides=[K1=8.01m, K2=4.34m, K3=8.15m, K4=4.34m, K5=8.01m, K6=4.34m, K7=8.15m, K8=4.34m] | area_source=public_site_area_text (1959 sq ft) | method=public_site_area_and_centroid | planning_refs= | lot_refs= | title_refs= | doc_evidence=no | NOT original/verified boundary; derived candidate geometry for display and review."},"OTM-15203552":{"listing_id":"OTM-15203552","confidence":"medium","previous_confidence":"medium_low","candidate_class":"candidate_medium_doc_area","area_m2":"99.0","computed_area_m2":"94.667","perimeter_m":"35.814","side_lengths_m_json":"[6.173, 2.901, 5.932, 2.901, 6.173, 2.901, 5.932, 2.901]","area_source":"public_site_area_text","area_raw":"99 sqm","method":"public_doc_or_image_plus_site_area","planning_refs":"","lot_refs":"","title_refs":"","doc_evidence":"yes","note":"estimated_candidate_not_verified | confidence=medium | previous_confidence=medium_low | class=candidate_medium_doc_area | reason=public document/image evidence plus public area text | area=99.00 mÂ² | computed_polygon_area=94.67 mÂ² | perimeter=35.81 m | sides=[K1=6.17m, K2=2.90m, K3=5.93m, K4=2.90m, K5=6.17m, K6=2.90m, K7=5.93m, K8=2.90m] | area_source=public_site_area_text (99 sqm) | method=public_doc_or_image_plus_site_area | planning_refs= | lot_refs= | title_refs= | doc_evidence=yes | NOT original/verified boundary; derived candidate geometry for display and review."},"OTM-18379773":{"listing_id":"OTM-18379773","confidence":"medium","previous_confidence":"medium_low","candidate_class":"candidate_medium_doc_area","area_m2":"176766.689","computed_area_m2":"185992.496","perimeter_m":"1580.765","side_lengths_m_json":"[257.342, 144.129, 244.799, 144.124, 257.319, 144.124, 244.799, 144.129]","area_source":"public_site_area_text","area_raw":"43.68 acre","method":"public_doc_or_image_plus_site_area","planning_refs":"","lot_refs":"","title_refs":"","doc_evidence":"yes","note":"estimated_candidate_not_verified | confidence=medium | previous_confidence=medium_low | class=candidate_medium_doc_area | reason=public document/image evidence plus public area text | area=176,766.69 mÂ² | computed_polygon_area=185,992.50 mÂ² | perimeter=1,580.77 m | sides=[K1=257.34m, K2=144.13m, K3=244.80m, K4=144.12m, K5=257.32m, K6=144.12m, K7=244.80m, K8=144.13m] | area_source=public_site_area_text (43.68 acre) | method=public_doc_or_image_plus_site_area | planning_refs= | lot_refs= | title_refs= | doc_evidence=yes | NOT original/verified boundary; derived candidate geometry for display and review."},"OTM-19215216":{"listing_id":"OTM-19215216","confidence":"medium_low","previous_confidence":"low_plus","candidate_class":"candidate_medium_low_area_only","area_m2":"8093.713","computed_area_m2":"8321.405","perimeter_m":"335.433","side_lengths_m_json":"[56.714, 27.784, 55.435, 27.784, 56.713, 27.784, 55.435, 27.784]","area_source":"public_site_area_text","area_raw":"2.00 acre","method":"public_site_area_and_centroid","planning_refs":"","lot_refs":"","title_refs":"","doc_evidence":"no","note":"estimated_candidate_not_verified | confidence=medium_low | previous_confidence=low_plus | class=candidate_medium_low_area_only | reason=public area text and centroid; no plan/georef | area=8,093.71 mÂ² | computed_polygon_area=8,321.41 mÂ² | perimeter=335.43 m | sides=[K1=56.71m, K2=27.78m, K3=55.44m, K4=27.78m, K5=56.71m, K6=27.78m, K7=55.44m, K8=27.78m] | area_source=public_site_area_text (2.00 acre) | method=public_site_area_and_centroid | planning_refs= | lot_refs= | title_refs= | doc_evidence=no | NOT original/verified boundary; derived candidate geometry for display and review."},"OTM-19167160":{"listing_id":"OTM-19167160","confidence":"medium","previous_confidence":"medium_low","candidate_class":"candidate_medium_doc_area","area_m2":"209.961","computed_area_m2":"231.482","perimeter_m":"55.894","side_lengths_m_json":"[9.274, 4.732, 9.209, 4.732, 9.274, 4.732, 9.209, 4.732]","area_source":"public_site_area_text","area_raw":"2260 sq ft","method":"public_doc_or_image_plus_site_area","planning_refs":"24/1006/FUL","lot_refs":"COMPRISES","title_refs":"","doc_evidence":"yes","note":"estimated_candidate_not_verified | confidence=medium | previous_confidence=medium_low | class=candidate_medium_doc_area | reason=public document/image evidence plus public area text | area=209.96 mÂ² | computed_polygon_area=231.48 mÂ² | perimeter=55.89 m | sides=[K1=9.27m, K2=4.73m, K3=9.21m, K4=4.73m, K5=9.27m, K6=4.73m, K7=9.21m, K8=4.73m] | area_source=public_site_area_text (2260 sq ft) | method=public_doc_or_image_plus_site_area | planning_refs=24/1006/FUL | lot_refs=COMPRISES | title_refs= | doc_evidence=yes | NOT original/verified boundary; derived candidate geometry for display and review."},"OTM-14565352":{"listing_id":"OTM-14565352","confidence":"medium_low","previous_confidence":"low","candidate_class":"candidate_medium_low_doc_only","area_m2":"449.423","computed_area_m2":"495.489","perimeter_m":"81.774","side_lengths_m_json":"[13.568, 6.923, 13.473, 6.923, 13.568, 6.923, 13.473, 6.923]","area_source":"feed_bbox_area_fallback","area_raw":"feed_bbox_area_m2=449.42","method":"feed_bbox_area_scaled_candidate","planning_refs":"19/02683/FUL","lot_refs":"","title_refs":"","doc_evidence":"yes","note":"estimated_candidate_not_verified | confidence=medium_low | previous_confidence=low | class=candidate_medium_low_doc_only | reason=public document/image evidence but no public site area | area=449.42 mÂ² | computed_polygon_area=495.49 mÂ² | perimeter=81.77 m | sides=[K1=13.57m, K2=6.92m, K3=13.47m, K4=6.92m, K5=13.57m, K6=6.92m, K7=13.47m, K8=6.92m] | area_source=feed_bbox_area_fallback (feed_bbox_area_m2=449.42) | method=feed_bbox_area_scaled_candidate | planning_refs=19/02683/FUL | lot_refs= | title_refs= | doc_evidence=yes | NOT original/verified boundary; derived candidate geometry for display and review."},"OTM-18775673":{"listing_id":"OTM-18775673","confidence":"low_plus","previous_confidence":"low","candidate_class":"candidate_low_plus_feed","area_m2":"7119.636","computed_area_m2":"7359.66","perimeter_m":"314.529","side_lengths_m_json":"[51.46, 28.531, 48.743, 28.531, 51.459, 28.531, 48.743, 28.531]","area_source":"feed_bbox_area_fallback","area_raw":"feed_bbox_area_m2=7119.64","method":"feed_bbox_area_scaled_candidate","planning_refs":"","lot_refs":"","title_refs":"","doc_evidence":"no","note":"estimated_candidate_not_verified | confidence=low_plus | previous_confidence=low | class=candidate_low_plus_feed | reason=feed-scaled candidate; no public area/georef | area=7,119.64 mÂ² | computed_polygon_area=7,359.66 mÂ² | perimeter=314.53 m | sides=[K1=51.46m, K2=28.53m, K3=48.74m, K4=28.53m, K5=51.46m, K6=28.53m, K7=48.74m, K8=28.53m] | area_source=feed_bbox_area_fallback (feed_bbox_area_m2=7119.64) | method=feed_bbox_area_scaled_candidate | planning_refs= | lot_refs= | title_refs= | doc_evidence=no | NOT original/verified boundary; derived candidate geometry for display and review."},"OTM-19260834":{"listing_id":"OTM-19260834","confidence":"medium","previous_confidence":"low_plus","candidate_class":"candidate_medium_ref_area","area_m2":"26200.0","computed_area_m2":"24549.61","perimeter_m":"575.371","side_lengths_m_json":"[94.545, 49.241, 94.66, 49.241, 94.542, 49.241, 94.66, 49.241]","area_source":"public_site_area_text","area_raw":"2.62 hectares","method":"public_site_area_and_centroid","planning_refs":"","lot_refs":"8; DETAILS; DURING; S; WILL","title_refs":"","doc_evidence":"no","note":"estimated_candidate_not_verified | confidence=medium | previous_confidence=low_plus | class=candidate_medium_ref_area | reason=public area text plus planning/lot/title reference | area=26,200.00 mÂ² | computed_polygon_area=24,549.61 mÂ² | perimeter=575.37 m | sides=[K1=94.55m, K2=49.24m, K3=94.66m, K4=49.24m, K5=94.54m, K6=49.24m, K7=94.66m, K8=49.24m] | area_source=public_site_area_text (2.62 hectares) | method=public_site_area_and_centroid | planning_refs= | lot_refs=8; DETAILS; DURING; S; WILL | title_refs= | doc_evidence=no | NOT original/verified boundary; derived candidate geometry for display and review."},"OTM-19087249":{"listing_id":"OTM-19087249","confidence":"medium_low","previous_confidence":"low","candidate_class":"candidate_medium_low_ref_feed","area_m2":"226.971","computed_area_m2":"241.188","perimeter_m":"56.96","side_lengths_m_json":"[9.052, 5.06, 9.308, 5.06, 9.052, 5.06, 9.308, 5.06]","area_source":"feed_bbox_area_fallback","area_raw":"feed_bbox_area_m2=226.97","method":"feed_bbox_area_scaled_candidate","planning_refs":"","lot_refs":"3","title_refs":"","doc_evidence":"no","note":"estimated_candidate_not_verified | confidence=medium_low | previous_confidence=low | class=candidate_medium_low_ref_feed | reason=reference evidence plus feed-scaled area fallback | area=226.97 mÂ² | computed_polygon_area=241.19 mÂ² | perimeter=56.96 m | sides=[K1=9.05m, K2=5.06m, K3=9.31m, K4=5.06m, K5=9.05m, K6=5.06m, K7=9.31m, K8=5.06m] | area_source=feed_bbox_area_fallback (feed_bbox_area_m2=226.97) | method=feed_bbox_area_scaled_candidate | planning_refs= | lot_refs=3 | title_refs= | doc_evidence=no | NOT original/verified boundary; derived candidate geometry for display and review."},"OTM-16840600":{"listing_id":"OTM-16840600","confidence":"medium_low","previous_confidence":"low","candidate_class":"candidate_medium_low_doc_only","area_m2":"361.867","computed_area_m2":"358.926","perimeter_m":"69.7","side_lengths_m_json":"[11.897, 5.71, 11.533, 5.71, 11.897, 5.71, 11.533, 5.71]","area_source":"feed_bbox_area_fallback","area_raw":"feed_bbox_area_m2=361.87","method":"feed_bbox_area_scaled_candidate","planning_refs":"21/3970/FUL","lot_refs":"TO","title_refs":"","doc_evidence":"yes","note":"estimated_candidate_not_verified | confidence=medium_low | previous_confidence=low | class=candidate_medium_low_doc_only | reason=public document/image evidence but no public site area | area=361.87 mÂ² | computed_polygon_area=358.93 mÂ² | perimeter=69.70 m | sides=[K1=11.90m, K2=5.71m, K3=11.53m, K4=5.71m, K5=11.90m, K6=5.71m, K7=11.53m, K8=5.71m] | area_source=feed_bbox_area_fallback (feed_bbox_area_m2=361.87) | method=feed_bbox_area_scaled_candidate | planning_refs=21/3970/FUL | lot_refs=TO | title_refs= | doc_evidence=yes | NOT original/verified boundary; derived candidate geometry for display and review."},"OTM-17651556":{"listing_id":"OTM-17651556","confidence":"low_plus","previous_confidence":"low","candidate_class":"candidate_low_plus_feed","area_m2":"24644.892","computed_area_m2":"24396.595","perimeter_m":"573.245","side_lengths_m_json":"[92.848, 49.854, 94.068, 49.854, 92.845, 49.854, 94.068, 49.854]","area_source":"feed_bbox_area_fallback","area_raw":"feed_bbox_area_m2=24644.89","method":"feed_bbox_area_scaled_candidate","planning_refs":"","lot_refs":"","title_refs":"","doc_evidence":"no","note":"estimated_candidate_not_verified | confidence=low_plus | previous_confidence=low | class=candidate_low_plus_feed | reason=feed-scaled candidate; no public area/georef | area=24,644.89 mÂ² | computed_polygon_area=24,396.60 mÂ² | perimeter=573.25 m | sides=[K1=92.85m, K2=49.85m, K3=94.07m, K4=49.85m, K5=92.84m, K6=49.85m, K7=94.07m, K8=49.85m] | area_source=feed_bbox_area_fallback (feed_bbox_area_m2=24644.89) | method=feed_bbox_area_scaled_candidate | planning_refs= | lot_refs= | title_refs= | doc_evidence=no | NOT original/verified boundary; derived candidate geometry for display and review."},"OTM-18195743":{"listing_id":"OTM-18195743","confidence":"medium_low","previous_confidence":"low_plus","candidate_class":"candidate_medium_low_area_only","area_m2":"3237.485","computed_area_m2":"3321.572","perimeter_m":"211.444","side_lengths_m_json":"[33.923, 18.585, 34.629, 18.585, 33.923, 18.585, 34.629, 18.585]","area_source":"public_site_area_text","area_raw":"0.80 acre","method":"public_site_area_and_centroid","planning_refs":"","lot_refs":"","title_refs":"","doc_evidence":"no","note":"estimated_candidate_not_verified | confidence=medium_low | previous_confidence=low_plus | class=candidate_medium_low_area_only | reason=public area text and centroid; no plan/georef | area=3,237.49 mÂ² | computed_polygon_area=3,321.57 mÂ² | perimeter=211.44 m | sides=[K1=33.92m, K2=18.59m, K3=34.63m, K4=18.59m, K5=33.92m, K6=18.59m, K7=34.63m, K8=18.59m] | area_source=public_site_area_text (0.80 acre) | method=public_site_area_and_centroid | planning_refs= | lot_refs= | title_refs= | doc_evidence=no | NOT original/verified boundary; derived candidate geometry for display and review."},"OTM-16930731":{"listing_id":"OTM-16930731","confidence":"medium","previous_confidence":"medium_low","candidate_class":"candidate_medium_doc_area","area_m2":"63.639","computed_area_m2":"68.964","perimeter_m":"30.514","side_lengths_m_json":"[5.087, 2.569, 5.032, 2.569, 5.087, 2.569, 5.032, 2.569]","area_source":"public_site_area_text","area_raw":"685 sq ft","method":"public_doc_or_image_plus_site_area","planning_refs":"","lot_refs":"COMPRISING","title_refs":"","doc_evidence":"yes","note":"estimated_candidate_not_verified | confidence=medium | previous_confidence=medium_low | class=candidate_medium_doc_area | reason=public document/image evidence plus public area text | area=63.64 mÂ² | computed_polygon_area=68.96 mÂ² | perimeter=30.51 m | sides=[K1=5.09m, K2=2.57m, K3=5.03m, K4=2.57m, K5=5.09m, K6=2.57m, K7=5.03m, K8=2.57m] | area_source=public_site_area_text (685 sq ft) | method=public_doc_or_image_plus_site_area | planning_refs= | lot_refs=COMPRISING | title_refs= | doc_evidence=yes | NOT original/verified boundary; derived candidate geometry for display and review."},"OTM-19290099":{"listing_id":"OTM-19290099","confidence":"medium_low","previous_confidence":"low_plus","candidate_class":"candidate_medium_low_area_only","area_m2":"8048.19","computed_area_m2":"8404.145","perimeter_m":"336.281","side_lengths_m_json":"[53.696, 29.715, 55.016, 29.714, 53.695, 29.714, 55.016, 29.715]","area_source":"public_site_area_text","area_raw":"86,630 sq ft","method":"public_site_area_and_centroid","planning_refs":"","lot_refs":"","title_refs":"","doc_evidence":"no","note":"estimated_candidate_not_verified | confidence=medium_low | previous_confidence=low_plus | class=candidate_medium_low_area_only | reason=public area text and centroid; no plan/georef | area=8,048.19 mÂ² | computed_polygon_area=8,404.15 mÂ² | perimeter=336.28 m | sides=[K1=53.70m, K2=29.71m, K3=55.02m, K4=29.71m, K5=53.70m, K6=29.71m, K7=55.02m, K8=29.71m] | area_source=public_site_area_text (86,630 sq ft) | method=public_site_area_and_centroid | planning_refs= | lot_refs= | title_refs= | doc_evidence=no | NOT original/verified boundary; derived candidate geometry for display and review."},"OTM-19252324":{"listing_id":"OTM-19252324","confidence":"medium_low","previous_confidence":"low_plus","candidate_class":"candidate_medium_low_area_only","area_m2":"930.777","computed_area_m2":"974.052","perimeter_m":"114.734","side_lengths_m_json":"[19.307, 9.556, 18.948, 9.556, 19.307, 9.556, 18.948, 9.556]","area_source":"public_site_area_text","area_raw":"0.23 acre","method":"public_site_area_and_centroid","planning_refs":"","lot_refs":"","title_refs":"","doc_evidence":"no","note":"estimated_candidate_not_verified | confidence=medium_low | previous_confidence=low_plus | class=candidate_medium_low_area_only | reason=public area text and centroid; no plan/georef | area=930.78 mÂ² | computed_polygon_area=974.05 mÂ² | perimeter=114.73 m | sides=[K1=19.31m, K2=9.56m, K3=18.95m, K4=9.56m, K5=19.31m, K6=9.56m, K7=18.95m, K8=9.56m] | area_source=public_site_area_text (0.23 acre) | method=public_site_area_and_centroid | planning_refs= | lot_refs= | title_refs= | doc_evidence=no | NOT original/verified boundary; derived candidate geometry for display and review."},"OTM-18572142":{"listing_id":"OTM-18572142","confidence":"medium_low","previous_confidence":"low_plus","candidate_class":"candidate_medium_low_area_only","area_m2":"10319.484","computed_area_m2":"11182.987","perimeter_m":"388.578","side_lengths_m_json":"[64.777, 32.719, 64.075, 32.719, 64.775, 32.719, 64.075, 32.719]","area_source":"public_site_area_text","area_raw":"2.55 acre","method":"public_site_area_and_centroid","planning_refs":"","lot_refs":"","title_refs":"","doc_evidence":"no","note":"estimated_candidate_not_verified | confidence=medium_low | previous_confidence=low_plus | class=candidate_medium_low_area_only | reason=public area text and centroid; no plan/georef | area=10,319.48 mÂ² | computed_polygon_area=11,182.99 mÂ² | perimeter=388.58 m | sides=[K1=64.78m, K2=32.72m, K3=64.08m, K4=32.72m, K5=64.78m, K6=32.72m, K7=64.08m, K8=32.72m] | area_source=public_site_area_text (2.55 acre) | method=public_site_area_and_centroid | planning_refs= | lot_refs= | title_refs= | doc_evidence=no | NOT original/verified boundary; derived candidate geometry for display and review."},"OTM-18845028":{"listing_id":"OTM-18845028","confidence":"low_plus","previous_confidence":"low","candidate_class":"candidate_low_plus_feed","area_m2":"49.111","computed_area_m2":"48.616","perimeter_m":"25.588","side_lengths_m_json":"[4.145, 2.225, 4.199, 2.225, 4.145, 2.225, 4.199, 2.225]","area_source":"feed_bbox_area_fallback","area_raw":"feed_bbox_area_m2=49.11","method":"feed_bbox_area_scaled_candidate","planning_refs":"","lot_refs":"","title_refs":"","doc_evidence":"no","note":"estimated_candidate_not_verified | confidence=low_plus | previous_confidence=low | class=candidate_low_plus_feed | reason=feed-scaled candidate; no public area/georef | area=49.11 mÂ² | computed_polygon_area=48.62 mÂ² | perimeter=25.59 m | sides=[K1=4.14m, K2=2.23m, K3=4.20m, K4=2.23m, K5=4.14m, K6=2.23m, K7=4.20m, K8=2.23m] | area_source=feed_bbox_area_fallback (feed_bbox_area_m2=49.11) | method=feed_bbox_area_scaled_candidate | planning_refs= | lot_refs= | title_refs= | doc_evidence=no | NOT original/verified boundary; derived candidate geometry for display and review."},"OTM-16395649":{"listing_id":"OTM-16395649","confidence":"medium_low","previous_confidence":"low_plus","candidate_class":"candidate_medium_low_area_only","area_m2":"8093.713","computed_area_m2":"8218.259","perimeter_m":"332.457","side_lengths_m_json":"[54.668, 30.003, 51.555, 30.003, 54.667, 30.003, 51.555, 30.003]","area_source":"public_site_area_text","area_raw":"2.00 acre","method":"public_site_area_and_centroid","planning_refs":"","lot_refs":"","title_refs":"","doc_evidence":"no","note":"estimated_candidate_not_verified | confidence=medium_low | previous_confidence=low_plus | class=candidate_medium_low_area_only | reason=public area text and centroid; no plan/georef | area=8,093.71 mÂ² | computed_polygon_area=8,218.26 mÂ² | perimeter=332.46 m | sides=[K1=54.67m, K2=30.00m, K3=51.55m, K4=30.00m, K5=54.67m, K6=30.00m, K7=51.55m, K8=30.00m] | area_source=public_site_area_text (2.00 acre) | method=public_site_area_and_centroid | planning_refs= | lot_refs= | title_refs= | doc_evidence=no | NOT original/verified boundary; derived candidate geometry for display and review."},"OTM-17610506":{"listing_id":"OTM-17610506","confidence":"medium","previous_confidence":"medium_low","candidate_class":"candidate_medium_doc_area","area_m2":"399.948","computed_area_m2":"403.917","perimeter_m":"73.92","side_lengths_m_json":"[12.558, 6.089, 12.224, 6.089, 12.558, 6.089, 12.224, 6.089]","area_source":"public_site_area_text","area_raw":"4305 sq ft","method":"public_doc_or_image_plus_site_area","planning_refs":"","lot_refs":"FOR; HAS","title_refs":"","doc_evidence":"yes","note":"estimated_candidate_not_verified | confidence=medium | previous_confidence=medium_low | class=candidate_medium_doc_area | reason=public document/image evidence plus public area text | area=399.95 mÂ² | computed_polygon_area=403.92 mÂ² | perimeter=73.92 m | sides=[K1=12.56m, K2=6.09m, K3=12.22m, K4=6.09m, K5=12.56m, K6=6.09m, K7=12.22m, K8=6.09m] | area_source=public_site_area_text (4305 sq ft) | method=public_doc_or_image_plus_site_area | planning_refs= | lot_refs=FOR; HAS | title_refs= | doc_evidence=yes | NOT original/verified boundary; derived candidate geometry for display and review."},"OTM-17669286":{"listing_id":"OTM-17669286","confidence":"medium","previous_confidence":"medium_low","candidate_class":"candidate_medium_doc_area","area_m2":"507.994","computed_area_m2":"534.507","perimeter_m":"84.74","side_lengths_m_json":"[13.795, 7.726, 13.123, 7.726, 13.795, 7.726, 13.123, 7.726]","area_source":"public_site_area_text","area_raw":"5468 sq ft","method":"public_doc_or_image_plus_site_area","planning_refs":"25/0841/FUL","lot_refs":"","title_refs":"","doc_evidence":"yes","note":"estimated_candidate_not_verified | confidence=medium | previous_confidence=medium_low | class=candidate_medium_doc_area | reason=public document/image evidence plus public area text | area=507.99 mÂ² | computed_polygon_area=534.51 mÂ² | perimeter=84.74 m | sides=[K1=13.79m, K2=7.73m, K3=13.12m, K4=7.73m, K5=13.79m, K6=7.73m, K7=13.12m, K8=7.73m] | area_source=public_site_area_text (5468 sq ft) | method=public_doc_or_image_plus_site_area | planning_refs=25/0841/FUL | lot_refs= | title_refs= | doc_evidence=yes | NOT original/verified boundary; derived candidate geometry for display and review."},"OTM-17832713":{"listing_id":"OTM-17832713","confidence":"medium","previous_confidence":"medium_low","candidate_class":"candidate_medium_doc_area","area_m2":"1911.0","computed_area_m2":"1757.503","perimeter_m":"153.98","side_lengths_m_json":"[25.424, 13.107, 25.352, 13.107, 25.424, 13.107, 25.352, 13.107]","area_source":"public_site_area_text","area_raw":"1,911 sq.m","method":"public_doc_or_image_plus_site_area","planning_refs":"","lot_refs":"","title_refs":"","doc_evidence":"yes","note":"estimated_candidate_not_verified | confidence=medium | previous_confidence=medium_low | class=candidate_medium_doc_area | reason=public document/image evidence plus public area text | area=1,911.00 mÂ² | computed_polygon_area=1,757.50 mÂ² | perimeter=153.98 m | sides=[K1=25.42m, K2=13.11m, K3=25.35m, K4=13.11m, K5=25.42m, K6=13.11m, K7=25.35m, K8=13.11m] | area_source=public_site_area_text (1,911 sq.m) | method=public_doc_or_image_plus_site_area | planning_refs= | lot_refs= | title_refs= | doc_evidence=yes | NOT original/verified boundary; derived candidate geometry for display and review."},"OTM-18912919":{"listing_id":"OTM-18912919","confidence":"medium_low","previous_confidence":"low_plus","candidate_class":"candidate_medium_low_area_only","area_m2":"1659.211","computed_area_m2":"1763.139","perimeter_m":"154.004","side_lengths_m_json":"[24.475, 13.68, 25.167, 13.68, 24.475, 13.68, 25.167, 13.68]","area_source":"public_site_area_text","area_raw":"0.41 Acres","method":"public_site_area_and_centroid","planning_refs":"","lot_refs":"","title_refs":"","doc_evidence":"no","note":"estimated_candidate_not_verified | confidence=medium_low | previous_confidence=low_plus | class=candidate_medium_low_area_only | reason=public area text and centroid; no plan/georef | area=1,659.21 mÂ² | computed_polygon_area=1,763.14 mÂ² | perimeter=154.00 m | sides=[K1=24.48m, K2=13.68m, K3=25.17m, K4=13.68m, K5=24.48m, K6=13.68m, K7=25.17m, K8=13.68m] | area_source=public_site_area_text (0.41 Acres) | method=public_site_area_and_centroid | planning_refs= | lot_refs= | title_refs= | doc_evidence=no | NOT original/verified boundary; derived candidate geometry for display and review."},"OTM-16962291":{"listing_id":"OTM-16962291","confidence":"medium_low","previous_confidence":"low_plus","candidate_class":"candidate_medium_low_area_only","area_m2":"11.706","computed_area_m2":"11.588","perimeter_m":"12.496","side_lengths_m_json":"[2.024, 1.087, 2.05, 1.087, 2.024, 1.087, 2.05, 1.087]","area_source":"public_site_area_text","area_raw":"126 sq ft","method":"public_site_area_and_centroid","planning_refs":"","lot_refs":"","title_refs":"","doc_evidence":"no","note":"estimated_candidate_not_verified | confidence=medium_low | previous_confidence=low_plus | class=candidate_medium_low_area_only | reason=public area text and centroid; no plan/georef | area=11.71 mÂ² | computed_polygon_area=11.59 mÂ² | perimeter=12.50 m | sides=[K1=2.02m, K2=1.09m, K3=2.05m, K4=1.09m, K5=2.02m, K6=1.09m, K7=2.05m, K8=1.09m] | area_source=public_site_area_text (126 sq ft) | method=public_site_area_and_centroid | planning_refs= | lot_refs= | title_refs= | doc_evidence=no | NOT original/verified boundary; derived candidate geometry for display and review."},"OTM-17103484":{"listing_id":"OTM-17103484","confidence":"medium","previous_confidence":"medium_low","candidate_class":"candidate_medium_doc_area","area_m2":"2060.961","computed_area_m2":"2156.781","perimeter_m":"170.727","side_lengths_m_json":"[28.73, 14.219, 28.196, 14.219, 28.729, 14.219, 28.196, 14.219]","area_source":"public_site_area_text","area_raw":"22184 sq ft","method":"public_doc_or_image_plus_site_area","planning_refs":"","lot_refs":"COMPRISES","title_refs":"","doc_evidence":"yes","note":"estimated_candidate_not_verified | confidence=medium | previous_confidence=medium_low | class=candidate_medium_doc_area | reason=public document/image evidence plus public area text | area=2,060.96 mÂ² | computed_polygon_area=2,156.78 mÂ² | perimeter=170.73 m | sides=[K1=28.73m, K2=14.22m, K3=28.20m, K4=14.22m, K5=28.73m, K6=14.22m, K7=28.20m, K8=14.22m] | area_source=public_site_area_text (22184 sq ft) | method=public_doc_or_image_plus_site_area | planning_refs= | lot_refs=COMPRISES | title_refs= | doc_evidence=yes | NOT original/verified boundary; derived candidate geometry for display and review."},"OTM-18586479":{"listing_id":"OTM-18586479","confidence":"medium_low","previous_confidence":"low_plus","candidate_class":"candidate_medium_low_area_only","area_m2":"10359.952","computed_area_m2":"10410.229","perimeter_m":"373.864","side_lengths_m_json":"[57.062, 34.617, 60.637, 34.617, 57.06, 34.617, 60.637, 34.617]","area_source":"public_site_area_text","area_raw":"2.56 acres","method":"public_site_area_and_centroid","planning_refs":"","lot_refs":"","title_refs":"","doc_evidence":"no","note":"estimated_candidate_not_verified | confidence=medium_low | previous_confidence=low_plus | class=candidate_medium_low_area_only | reason=public area text and centroid; no plan/georef | area=10,359.95 mÂ² | computed_polygon_area=10,410.23 mÂ² | perimeter=373.86 m | sides=[K1=57.06m, K2=34.62m, K3=60.64m, K4=34.62m, K5=57.06m, K6=34.62m, K7=60.64m, K8=34.62m] | area_source=public_site_area_text (2.56 acres) | method=public_site_area_and_centroid | planning_refs= | lot_refs= | title_refs= | doc_evidence=no | NOT original/verified boundary; derived candidate geometry for display and review."},"OTM-18381098":{"listing_id":"OTM-18381098","confidence":"medium_low","previous_confidence":"low","candidate_class":"candidate_medium_low_doc_only","area_m2":"154.907","computed_area_m2":"158.93","perimeter_m":"46.25","side_lengths_m_json":"[7.42, 4.065, 7.575, 4.065, 7.42, 4.065, 7.575, 4.065]","area_source":"feed_bbox_area_fallback","area_raw":"feed_bbox_area_m2=154.91","method":"feed_bbox_area_scaled_candidate","planning_refs":"","lot_refs":"","title_refs":"","doc_evidence":"yes","note":"estimated_candidate_not_verified | confidence=medium_low | previous_confidence=low | class=candidate_medium_low_doc_only | reason=public document/image evidence but no public site area | area=154.91 mÂ² | computed_polygon_area=158.93 mÂ² | perimeter=46.25 m | sides=[K1=7.42m, K2=4.07m, K3=7.58m, K4=4.07m, K5=7.42m, K6=4.07m, K7=7.58m, K8=4.07m] | area_source=feed_bbox_area_fallback (feed_bbox_area_m2=154.91) | method=feed_bbox_area_scaled_candidate | planning_refs= | lot_refs= | title_refs= | doc_evidence=yes | NOT original/verified boundary; derived candidate geometry for display and review."},"OTM-16424212":{"listing_id":"OTM-16424212","confidence":"medium_low","previous_confidence":"low","candidate_class":"candidate_medium_low_doc_only","area_m2":"12778.833","computed_area_m2":"11994.686","perimeter_m":"403.258","side_lengths_m_json":"[69.838, 32.487, 66.818, 32.487, 69.836, 32.487, 66.818, 32.487]","area_source":"feed_bbox_area_fallback","area_raw":"feed_bbox_area_m2=12778.83","method":"feed_bbox_area_scaled_candidate","planning_refs":"","lot_refs":"","title_refs":"","doc_evidence":"yes","note":"estimated_candidate_not_verified | confidence=medium_low | previous_confidence=low | class=candidate_medium_low_doc_only | reason=public document/image evidence but no public site area | area=12,778.83 mÂ² | computed_polygon_area=11,994.69 mÂ² | perimeter=403.26 m | sides=[K1=69.84m, K2=32.49m, K3=66.82m, K4=32.49m, K5=69.84m, K6=32.49m, K7=66.82m, K8=32.49m] | area_source=feed_bbox_area_fallback (feed_bbox_area_m2=12778.83) | method=feed_bbox_area_scaled_candidate | planning_refs= | lot_refs= | title_refs= | doc_evidence=yes | NOT original/verified boundary; derived candidate geometry for display and review."},"OTM-19010583":{"listing_id":"OTM-19010583","confidence":"medium","previous_confidence":"low_plus","candidate_class":"candidate_medium_ref_area","area_m2":"444.913","computed_area_m2":"457.429","perimeter_m":"78.644","side_lengths_m_json":"[13.297, 6.514, 12.997, 6.514, 13.297, 6.514, 12.997, 6.514]","area_source":"public_site_area_text","area_raw":"4789 sq ft","method":"public_site_area_and_centroid","planning_refs":"","lot_refs":"COMPRISES","title_refs":"","doc_evidence":"no","note":"estimated_candidate_not_verified | confidence=medium | previous_confidence=low_plus | class=candidate_medium_ref_area | reason=public area text plus planning/lot/title reference | area=444.91 mÂ² | computed_polygon_area=457.43 mÂ² | perimeter=78.64 m | sides=[K1=13.30m, K2=6.51m, K3=13.00m, K4=6.51m, K5=13.30m, K6=6.51m, K7=13.00m, K8=6.51m] | area_source=public_site_area_text (4789 sq ft) | method=public_site_area_and_centroid | planning_refs= | lot_refs=COMPRISES | title_refs= | doc_evidence=no | NOT original/verified boundary; derived candidate geometry for display and review."},"OTM-17277828":{"listing_id":"OTM-17277828","confidence":"medium_low","previous_confidence":"low_plus","candidate_class":"candidate_medium_low_area_only","area_m2":"84.449","computed_area_m2":"84.214","perimeter_m":"33.662","side_lengths_m_json":"[5.564, 3.022, 5.223, 3.022, 5.564, 3.022, 5.223, 3.022]","area_source":"public_site_area_text","area_raw":"909 sq ft","method":"public_site_area_and_centroid","planning_refs":"","lot_refs":"","title_refs":"","doc_evidence":"no","note":"estimated_candidate_not_verified | confidence=medium_low | previous_confidence=low_plus | class=candidate_medium_low_area_only | reason=public area text and centroid; no plan/georef | area=84.45 mÂ² | computed_polygon_area=84.21 mÂ² | perimeter=33.66 m | sides=[K1=5.56m, K2=3.02m, K3=5.22m, K4=3.02m, K5=5.56m, K6=3.02m, K7=5.22m, K8=3.02m] | area_source=public_site_area_text (909 sq ft) | method=public_site_area_and_centroid | planning_refs= | lot_refs= | title_refs= | doc_evidence=no | NOT original/verified boundary; derived candidate geometry for display and review."},"OTM-16563297":{"listing_id":"OTM-16563297","confidence":"medium","previous_confidence":"medium_low","candidate_class":"candidate_medium_doc_area","area_m2":"1092.651","computed_area_m2":"1140.977","perimeter_m":"123.908","side_lengths_m_json":"[19.785, 10.949, 20.271, 10.949, 19.785, 10.949, 20.271, 10.949]","area_source":"public_site_area_text","area_raw":"0.27 acre","method":"public_doc_or_image_plus_site_area","planning_refs":"","lot_refs":"","title_refs":"","doc_evidence":"yes","note":"estimated_candidate_not_verified | confidence=medium | previous_confidence=medium_low | class=candidate_medium_doc_area | reason=public document/image evidence plus public area text | area=1,092.65 mÂ² | computed_polygon_area=1,140.98 mÂ² | perimeter=123.91 m | sides=[K1=19.79m, K2=10.95m, K3=20.27m, K4=10.95m, K5=19.79m, K6=10.95m, K7=20.27m, K8=10.95m] | area_source=public_site_area_text (0.27 acre) | method=public_doc_or_image_plus_site_area | planning_refs= | lot_refs= | title_refs= | doc_evidence=yes | NOT original/verified boundary; derived candidate geometry for display and review."},"OTM-10278618":{"listing_id":"OTM-10278618","confidence":"medium","previous_confidence":"medium_low","candidate_class":"candidate_medium_doc_area","area_m2":"221.945","computed_area_m2":"207.964","perimeter_m":"52.956","side_lengths_m_json":"[8.702, 4.532, 8.712, 4.532, 8.702, 4.532, 8.712, 4.532]","area_source":"public_site_area_text","area_raw":"2389 sq ft","method":"public_doc_or_image_plus_site_area","planning_refs":"","lot_refs":"","title_refs":"","doc_evidence":"yes","note":"estimated_candidate_not_verified | confidence=medium | previous_confidence=medium_low | class=candidate_medium_doc_area | reason=public document/image evidence plus public area text | area=221.94 mÂ² | computed_polygon_area=207.96 mÂ² | perimeter=52.96 m | sides=[K1=8.70m, K2=4.53m, K3=8.71m, K4=4.53m, K5=8.70m, K6=4.53m, K7=8.71m, K8=4.53m] | area_source=public_site_area_text (2389 sq ft) | method=public_doc_or_image_plus_site_area | planning_refs= | lot_refs= | title_refs= | doc_evidence=yes | NOT original/verified boundary; derived candidate geometry for display and review."},"OTM-17102757":{"listing_id":"OTM-17102757","confidence":"medium_low","previous_confidence":"low","candidate_class":"candidate_medium_low_doc_only","area_m2":"1932.111","computed_area_m2":"2093.785","perimeter_m":"168.139","side_lengths_m_json":"[28.029, 14.158, 27.725, 14.158, 28.028, 14.158, 27.725, 14.158]","area_source":"feed_bbox_area_fallback","area_raw":"feed_bbox_area_m2=1932.11","method":"feed_bbox_area_scaled_candidate","planning_refs":"","lot_refs":"","title_refs":"","doc_evidence":"yes","note":"estimated_candidate_not_verified | confidence=medium_low | previous_confidence=low | class=candidate_medium_low_doc_only | reason=public document/image evidence but no public site area | area=1,932.11 mÂ² | computed_polygon_area=2,093.78 mÂ² | perimeter=168.14 m | sides=[K1=28.03m, K2=14.16m, K3=27.73m, K4=14.16m, K5=28.03m, K6=14.16m, K7=27.73m, K8=14.16m] | area_source=feed_bbox_area_fallback (feed_bbox_area_m2=1932.11) | method=feed_bbox_area_scaled_candidate | planning_refs= | lot_refs= | title_refs= | doc_evidence=yes | NOT original/verified boundary; derived candidate geometry for display and review."},"OTM-19247791":{"listing_id":"OTM-19247791","confidence":"medium","previous_confidence":"medium_low","candidate_class":"candidate_medium_doc_area","area_m2":"325.161","computed_area_m2":"345.528","perimeter_m":"68.176","side_lengths_m_json":"[10.835, 6.056, 11.141, 6.056, 10.835, 6.056, 11.141, 6.056]","area_source":"public_site_area_text","area_raw":"3,500 Square Feet","method":"public_doc_or_image_plus_site_area","planning_refs":"","lot_refs":"","title_refs":"","doc_evidence":"yes","note":"estimated_candidate_not_verified | confidence=medium | previous_confidence=medium_low | class=candidate_medium_doc_area | reason=public document/image evidence plus public area text | area=325.16 mÂ² | computed_polygon_area=345.53 mÂ² | perimeter=68.18 m | sides=[K1=10.84m, K2=6.06m, K3=11.14m, K4=6.06m, K5=10.84m, K6=6.06m, K7=11.14m, K8=6.06m] | area_source=public_site_area_text (3,500 Square Feet) | method=public_doc_or_image_plus_site_area | planning_refs= | lot_refs= | title_refs= | doc_evidence=yes | NOT original/verified boundary; derived candidate geometry for display and review."},"OTM-18702213":{"listing_id":"OTM-18702213","confidence":"medium","previous_confidence":"medium_low","candidate_class":"candidate_medium_doc_area","area_m2":"4046.856","computed_area_m2":"3941.528","perimeter_m":"231.037","side_lengths_m_json":"[39.627, 18.822, 38.248, 18.822, 39.626, 18.822, 38.248, 18.822]","area_source":"public_site_area_text","area_raw":"1 Acre","method":"public_doc_or_image_plus_site_area","planning_refs":"","lot_refs":"","title_refs":"","doc_evidence":"yes","note":"estimated_candidate_not_verified | confidence=medium | previous_confidence=medium_low | class=candidate_medium_doc_area | reason=public document/image evidence plus public area text | area=4,046.86 mÂ² | computed_polygon_area=3,941.53 mÂ² | perimeter=231.04 m | sides=[K1=39.63m, K2=18.82m, K3=38.25m, K4=18.82m, K5=39.63m, K6=18.82m, K7=38.25m, K8=18.82m] | area_source=public_site_area_text (1 Acre) | method=public_doc_or_image_plus_site_area | planning_refs= | lot_refs= | title_refs= | doc_evidence=yes | NOT original/verified boundary; derived candidate geometry for display and review."},"OTM-19298297":{"listing_id":"OTM-19298297","confidence":"medium_low","previous_confidence":"low_plus","candidate_class":"candidate_medium_low_area_only","area_m2":"323.749","computed_area_m2":"319.544","perimeter_m":"65.51","side_lengths_m_json":"[10.046, 6.035, 10.639, 6.035, 10.046, 6.035, 10.639, 6.035]","area_source":"public_site_area_text","area_raw":"0.08 acre","method":"public_site_area_and_centroid","planning_refs":"","lot_refs":"","title_refs":"","doc_evidence":"no","note":"estimated_candidate_not_verified | confidence=medium_low | previous_confidence=low_plus | class=candidate_medium_low_area_only | reason=public area text and centroid; no plan/georef | area=323.75 mÂ² | computed_polygon_area=319.54 mÂ² | perimeter=65.51 m | sides=[K1=10.05m, K2=6.04m, K3=10.64m, K4=6.04m, K5=10.05m, K6=6.04m, K7=10.64m, K8=6.04m] | area_source=public_site_area_text (0.08 acre) | method=public_site_area_and_centroid | planning_refs= | lot_refs= | title_refs= | doc_evidence=no | NOT original/verified boundary; derived candidate geometry for display and review."},"OTM-16460389":{"listing_id":"OTM-16460389","confidence":"medium","previous_confidence":"medium_low","candidate_class":"candidate_medium_doc_area","area_m2":"26.942","computed_area_m2":"27.154","perimeter_m":"19.122","side_lengths_m_json":"[3.082, 1.672, 3.135, 1.672, 3.082, 1.672, 3.135, 1.672]","area_source":"public_site_area_text","area_raw":"290 sq ft","method":"public_doc_or_image_plus_site_area","planning_refs":"","lot_refs":"","title_refs":"","doc_evidence":"yes","note":"estimated_candidate_not_verified | confidence=medium | previous_confidence=medium_low | class=candidate_medium_doc_area | reason=public document/image evidence plus public area text | area=26.94 mÂ² | computed_polygon_area=27.15 mÂ² | perimeter=19.12 m | sides=[K1=3.08m, K2=1.67m, K3=3.13m, K4=1.67m, K5=3.08m, K6=1.67m, K7=3.13m, K8=1.67m] | area_source=public_site_area_text (290 sq ft) | method=public_doc_or_image_plus_site_area | planning_refs= | lot_refs= | title_refs= | doc_evidence=yes | NOT original/verified boundary; derived candidate geometry for display and review."},"OTM-17750343":{"listing_id":"OTM-17750343","confidence":"medium","previous_confidence":"medium_low","candidate_class":"candidate_medium_doc_area","area_m2":"124198.024","computed_area_m2":"134590.542","perimeter_m":"1348.059","side_lengths_m_json":"[224.729, 113.511, 222.29, 113.508, 224.712, 113.508, 222.29, 113.511]","area_source":"public_site_area_text","area_raw":"30.69 acres","method":"public_doc_or_image_plus_site_area","planning_refs":"","lot_refs":"S","title_refs":"","doc_evidence":"yes","note":"estimated_candidate_not_verified | confidence=medium | previous_confidence=medium_low | class=candidate_medium_doc_area | reason=public document/image evidence plus public area text | area=124,198.02 mÂ² | computed_polygon_area=134,590.54 mÂ² | perimeter=1,348.06 m | sides=[K1=224.73m, K2=113.51m, K3=222.29m, K4=113.51m, K5=224.71m, K6=113.51m, K7=222.29m, K8=113.51m] | area_source=public_site_area_text (30.69 acres) | method=public_doc_or_image_plus_site_area | planning_refs= | lot_refs=S | title_refs= | doc_evidence=yes | NOT original/verified boundary; derived candidate geometry for display and review."},"OTM-14925101":{"listing_id":"OTM-14925101","confidence":"medium","previous_confidence":"medium_low","candidate_class":"candidate_medium_doc_area","area_m2":"5099.039","computed_area_m2":"4875.844","perimeter_m":"257.033","side_lengths_m_json":"[44.299, 20.823, 42.572, 20.823, 44.298, 20.823, 42.572, 20.823]","area_source":"public_site_area_text","area_raw":"1.26 acres","method":"public_doc_or_image_plus_site_area","planning_refs":"","lot_refs":"13","title_refs":"","doc_evidence":"yes","note":"estimated_candidate_not_verified | confidence=medium | previous_confidence=medium_low | class=candidate_medium_doc_area | reason=public document/image evidence plus public area text | area=5,099.04 mÂ² | computed_polygon_area=4,875.84 mÂ² | perimeter=257.03 m | sides=[K1=44.30m, K2=20.82m, K3=42.57m, K4=20.82m, K5=44.30m, K6=20.82m, K7=42.57m, K8=20.82m] | area_source=public_site_area_text (1.26 acres) | method=public_doc_or_image_plus_site_area | planning_refs= | lot_refs=13 | title_refs= | doc_evidence=yes | NOT original/verified boundary; derived candidate geometry for display and review."},"OTM-18629244":{"listing_id":"OTM-18629244","confidence":"medium_low","previous_confidence":"low","candidate_class":"candidate_medium_low_doc_only","area_m2":"49.156","computed_area_m2":"48.66","perimeter_m":"25.604","side_lengths_m_json":"[4.147, 2.227, 4.201, 2.227, 4.147, 2.227, 4.201, 2.227]","area_source":"feed_bbox_area_fallback","area_raw":"feed_bbox_area_m2=49.16","method":"feed_bbox_area_scaled_candidate","planning_refs":"23/01900/FUL; 24/02188/FUL","lot_refs":"","title_refs":"","doc_evidence":"yes","note":"estimated_candidate_not_verified | confidence=medium_low | previous_confidence=low | class=candidate_medium_low_doc_only | reason=public document/image evidence but no public site area | area=49.16 mÂ² | computed_polygon_area=48.66 mÂ² | perimeter=25.60 m | sides=[K1=4.15m, K2=2.23m, K3=4.20m, K4=2.23m, K5=4.15m, K6=2.23m, K7=4.20m, K8=2.23m] | area_source=feed_bbox_area_fallback (feed_bbox_area_m2=49.16) | method=feed_bbox_area_scaled_candidate | planning_refs=23/01900/FUL; 24/02188/FUL | lot_refs= | title_refs= | doc_evidence=yes | NOT original/verified boundary; derived candidate geometry for display and review."},"OTM-19306833":{"listing_id":"OTM-19306833","confidence":"medium_low","previous_confidence":"low_plus","candidate_class":"candidate_medium_low_area_only","area_m2":"1214.057","computed_area_m2":"1137.581","perimeter_m":"123.858","side_lengths_m_json":"[20.352, 10.6, 20.377, 10.6, 20.352, 10.6, 20.377, 10.6]","area_source":"public_site_area_text","area_raw":"0.3 acres","method":"public_site_area_and_centroid","planning_refs":"","lot_refs":"","title_refs":"","doc_evidence":"no","note":"estimated_candidate_not_verified | confidence=medium_low | previous_confidence=low_plus | class=candidate_medium_low_area_only | reason=public area text and centroid; no plan/georef | area=1,214.06 mÂ² | computed_polygon_area=1,137.58 mÂ² | perimeter=123.86 m | sides=[K1=20.35m, K2=10.60m, K3=20.38m, K4=10.60m, K5=20.35m, K6=10.60m, K7=20.38m, K8=10.60m] | area_source=public_site_area_text (0.3 acres) | method=public_site_area_and_centroid | planning_refs= | lot_refs= | title_refs= | doc_evidence=no | NOT original/verified boundary; derived candidate geometry for display and review."},"OTM-19088750":{"listing_id":"OTM-19088750","confidence":"medium","previous_confidence":"low_plus","candidate_class":"candidate_medium_ref_area","area_m2":"13.935","computed_area_m2":"14.297","perimeter_m":"13.872","side_lengths_m_json":"[2.226, 1.219, 2.272, 1.219, 2.226, 1.219, 2.272, 1.219]","area_source":"public_site_area_text","area_raw":"150 sq ft","method":"public_site_area_and_centroid","planning_refs":"","lot_refs":"COMPRISES","title_refs":"","doc_evidence":"no","note":"estimated_candidate_not_verified | confidence=medium | previous_confidence=low_plus | class=candidate_medium_ref_area | reason=public area text plus planning/lot/title reference | area=13.94 mÂ² | computed_polygon_area=14.30 mÂ² | perimeter=13.87 m | sides=[K1=2.23m, K2=1.22m, K3=2.27m, K4=1.22m, K5=2.23m, K6=1.22m, K7=2.27m, K8=1.22m] | area_source=public_site_area_text (150 sq ft) | method=public_site_area_and_centroid | planning_refs= | lot_refs=COMPRISES | title_refs= | doc_evidence=no | NOT original/verified boundary; derived candidate geometry for display and review."},"OTM-17289552":{"listing_id":"OTM-17289552","confidence":"medium_low","previous_confidence":"low_plus","candidate_class":"candidate_medium_low_area_only","area_m2":"218.972","computed_area_m2":"228.657","perimeter_m":"55.468","side_lengths_m_json":"[8.857, 4.901, 9.075, 4.901, 8.857, 4.901, 9.075, 4.901]","area_source":"public_site_area_text","area_raw":"2357 sq ft","method":"public_site_area_and_centroid","planning_refs":"","lot_refs":"","title_refs":"","doc_evidence":"no","note":"estimated_candidate_not_verified | confidence=medium_low | previous_confidence=low_plus | class=candidate_medium_low_area_only | reason=public area text and centroid; no plan/georef | area=218.97 mÂ² | computed_polygon_area=228.66 mÂ² | perimeter=55.47 m | sides=[K1=8.86m, K2=4.90m, K3=9.07m, K4=4.90m, K5=8.86m, K6=4.90m, K7=9.07m, K8=4.90m] | area_source=public_site_area_text (2357 sq ft) | method=public_site_area_and_centroid | planning_refs= | lot_refs= | title_refs= | doc_evidence=no | NOT original/verified boundary; derived candidate geometry for display and review."},"OTM-14260994":{"listing_id":"OTM-14260994","confidence":"medium","previous_confidence":"medium_low","candidate_class":"candidate_medium_doc_area","area_m2":"420.015","computed_area_m2":"408.31","perimeter_m":"74.172","side_lengths_m_json":"[12.071, 6.416, 12.183, 6.416, 12.071, 6.416, 12.183, 6.416]","area_source":"public_site_area_text","area_raw":"4,521 Sq ft","method":"public_doc_or_image_plus_site_area","planning_refs":"","lot_refs":"","title_refs":"","doc_evidence":"yes","note":"estimated_candidate_not_verified | confidence=medium | previous_confidence=medium_low | class=candidate_medium_doc_area | reason=public document/image evidence plus public area text | area=420.01 mÂ² | computed_polygon_area=408.31 mÂ² | perimeter=74.17 m | sides=[K1=12.07m, K2=6.42m, K3=12.18m, K4=6.42m, K5=12.07m, K6=6.42m, K7=12.18m, K8=6.42m] | area_source=public_site_area_text (4,521 Sq ft) | method=public_doc_or_image_plus_site_area | planning_refs= | lot_refs= | title_refs= | doc_evidence=yes | NOT original/verified boundary; derived candidate geometry for display and review."},"OTM-19202001":{"listing_id":"OTM-19202001","confidence":"medium_low","previous_confidence":"low_plus","candidate_class":"candidate_medium_low_area_only","area_m2":"1800.0","computed_area_m2":"1819.822","perimeter_m":"157.41","side_lengths_m_json":"[28.126, 12.186, 26.207, 12.186, 28.126, 12.186, 26.207, 12.186]","area_source":"public_site_area_text","area_raw":"0.18 hectares","method":"public_site_area_and_centroid","planning_refs":"","lot_refs":"","title_refs":"","doc_evidence":"no","note":"estimated_candidate_not_verified | confidence=medium_low | previous_confidence=low_plus | class=candidate_medium_low_area_only | reason=public area text and centroid; no plan/georef | area=1,800.00 mÂ² | computed_polygon_area=1,819.82 mÂ² | perimeter=157.41 m | sides=[K1=28.13m, K2=12.19m, K3=26.21m, K4=12.19m, K5=28.13m, K6=12.19m, K7=26.21m, K8=12.19m] | area_source=public_site_area_text (0.18 hectares) | method=public_site_area_and_centroid | planning_refs= | lot_refs= | title_refs= | doc_evidence=no | NOT original/verified boundary; derived candidate geometry for display and review."},"OTM-19058119":{"listing_id":"OTM-19058119","confidence":"low_plus","previous_confidence":"low","candidate_class":"candidate_low_plus_feed","area_m2":"32.967","computed_area_m2":"31.467","perimeter_m":"20.596","side_lengths_m_json":"[3.368, 1.772, 3.386, 1.772, 3.368, 1.772, 3.386, 1.772]","area_source":"feed_bbox_area_fallback","area_raw":"feed_bbox_area_m2=32.97","method":"feed_bbox_area_scaled_candidate","planning_refs":"","lot_refs":"","title_refs":"","doc_evidence":"no","note":"estimated_candidate_not_verified | confidence=low_plus | previous_confidence=low | class=candidate_low_plus_feed | reason=feed-scaled candidate; no public area/georef | area=32.97 mÂ² | computed_polygon_area=31.47 mÂ² | perimeter=20.60 m | sides=[K1=3.37m, K2=1.77m, K3=3.39m, K4=1.77m, K5=3.37m, K6=1.77m, K7=3.39m, K8=1.77m] | area_source=feed_bbox_area_fallback (feed_bbox_area_m2=32.97) | method=feed_bbox_area_scaled_candidate | planning_refs= | lot_refs= | title_refs= | doc_evidence=no | NOT original/verified boundary; derived candidate geometry for display and review."},"OTM-17136443":{"listing_id":"OTM-17136443","confidence":"medium","previous_confidence":"medium_low","candidate_class":"candidate_medium_doc_area","area_m2":"323.749","computed_area_m2":"344.795","perimeter_m":"68.246","side_lengths_m_json":"[11.43, 5.715, 11.263, 5.715, 11.43, 5.715, 11.263, 5.715]","area_source":"public_site_area_text","area_raw":"0.08 acre","method":"public_doc_or_image_plus_site_area","planning_refs":"","lot_refs":"","title_refs":"","doc_evidence":"yes","note":"estimated_candidate_not_verified | confidence=medium | previous_confidence=medium_low | class=candidate_medium_doc_area | reason=public document/image evidence plus public area text | area=323.75 mÂ² | computed_polygon_area=344.80 mÂ² | perimeter=68.25 m | sides=[K1=11.43m, K2=5.71m, K3=11.26m, K4=5.71m, K5=11.43m, K6=5.71m, K7=11.26m, K8=5.71m] | area_source=public_site_area_text (0.08 acre) | method=public_doc_or_image_plus_site_area | planning_refs= | lot_refs= | title_refs= | doc_evidence=yes | NOT original/verified boundary; derived candidate geometry for display and review."},"OTM-18109749":{"listing_id":"OTM-18109749","confidence":"medium_low","previous_confidence":"low_plus","candidate_class":"candidate_medium_low_area_only","area_m2":"3237.485","computed_area_m2":"3380.672","perimeter_m":"213.282","side_lengths_m_json":"[34.056, 18.846, 34.893, 18.846, 34.056, 18.846, 34.893, 18.846]","area_source":"public_site_area_text","area_raw":"0.8 acre","method":"public_site_area_and_centroid","planning_refs":"","lot_refs":"","title_refs":"","doc_evidence":"no","note":"estimated_candidate_not_verified | confidence=medium_low | previous_confidence=low_plus | class=candidate_medium_low_area_only | reason=public area text and centroid; no plan/georef | area=3,237.49 mÂ² | computed_polygon_area=3,380.67 mÂ² | perimeter=213.28 m | sides=[K1=34.06m, K2=18.85m, K3=34.89m, K4=18.85m, K5=34.06m, K6=18.85m, K7=34.89m, K8=18.85m] | area_source=public_site_area_text (0.8 acre) | method=public_site_area_and_centroid | planning_refs= | lot_refs= | title_refs= | doc_evidence=no | NOT original/verified boundary; derived candidate geometry for display and review."},"OTM-14925027":{"listing_id":"OTM-14925027","confidence":"medium","previous_confidence":"medium_low","candidate_class":"candidate_medium_doc_area","area_m2":"4734.822","computed_area_m2":"5131.018","perimeter_m":"263.21","side_lengths_m_json":"[43.877, 22.163, 43.402, 22.163, 43.877, 22.163, 43.402, 22.163]","area_source":"public_site_area_text","area_raw":"1.17 acres","method":"public_doc_or_image_plus_site_area","planning_refs":"","lot_refs":"15","title_refs":"","doc_evidence":"yes","note":"estimated_candidate_not_verified | confidence=medium | previous_confidence=medium_low | class=candidate_medium_doc_area | reason=public document/image evidence plus public area text | area=4,734.82 mÂ² | computed_polygon_area=5,131.02 mÂ² | perimeter=263.21 m | sides=[K1=43.88m, K2=22.16m, K3=43.40m, K4=22.16m, K5=43.88m, K6=22.16m, K7=43.40m, K8=22.16m] | area_source=public_site_area_text (1.17 acres) | method=public_doc_or_image_plus_site_area | planning_refs= | lot_refs=15 | title_refs= | doc_evidence=yes | NOT original/verified boundary; derived candidate geometry for display and review."},"OTM-19122596":{"listing_id":"OTM-19122596","confidence":"medium_low","previous_confidence":"low_plus","candidate_class":"candidate_medium_low_area_only","area_m2":"1699.68","computed_area_m2":"1652.313","perimeter_m":"149.212","side_lengths_m_json":"[24.283, 12.908, 24.507, 12.908, 24.283, 12.908, 24.507, 12.908]","area_source":"public_site_area_text","area_raw":"0.42 Acres","method":"public_site_area_and_centroid","planning_refs":"","lot_refs":"","title_refs":"","doc_evidence":"no","note":"estimated_candidate_not_verified | confidence=medium_low | previous_confidence=low_plus | class=candidate_medium_low_area_only | reason=public area text and centroid; no plan/georef | area=1,699.68 mÂ² | computed_polygon_area=1,652.31 mÂ² | perimeter=149.21 m | sides=[K1=24.28m, K2=12.91m, K3=24.51m, K4=12.91m, K5=24.28m, K6=12.91m, K7=24.51m, K8=12.91m] | area_source=public_site_area_text (0.42 Acres) | method=public_site_area_and_centroid | planning_refs= | lot_refs= | title_refs= | doc_evidence=no | NOT original/verified boundary; derived candidate geometry for display and review."},"OTM-17230637":{"listing_id":"OTM-17230637","confidence":"medium_low","previous_confidence":"low_plus","candidate_class":"candidate_medium_low_area_only","area_m2":"172.0","computed_area_m2":"183.181","perimeter_m":"49.744","side_lengths_m_json":"[8.331, 4.166, 8.209, 4.166, 8.331, 4.166, 8.209, 4.166]","area_source":"public_site_area_text","area_raw":"172 sq m","method":"public_site_area_and_centroid","planning_refs":"","lot_refs":"","title_refs":"","doc_evidence":"no","note":"estimated_candidate_not_verified | confidence=medium_low | previous_confidence=low_plus | class=candidate_medium_low_area_only | reason=public area text and centroid; no plan/georef | area=172.00 mÂ² | computed_polygon_area=183.18 mÂ² | perimeter=49.74 m | sides=[K1=8.33m, K2=4.17m, K3=8.21m, K4=4.17m, K5=8.33m, K6=4.17m, K7=8.21m, K8=4.17m] | area_source=public_site_area_text (172 sq m) | method=public_site_area_and_centroid | planning_refs= | lot_refs= | title_refs= | doc_evidence=no | NOT original/verified boundary; derived candidate geometry for display and review."},"OTM-19091340":{"listing_id":"OTM-19091340","confidence":"medium","previous_confidence":"medium_low","candidate_class":"candidate_medium_doc_area","area_m2":"59.922","computed_area_m2":"61.608","perimeter_m":"28.864","side_lengths_m_json":"[4.88, 2.391, 4.77, 2.391, 4.88, 2.391, 4.77, 2.391]","area_source":"public_site_area_text","area_raw":"645 sqft","method":"public_doc_or_image_plus_site_area","planning_refs":"24/01377/FUL; 24/01378/LB","lot_refs":"","title_refs":"","doc_evidence":"yes","note":"estimated_candidate_not_verified | confidence=medium | previous_confidence=medium_low | class=candidate_medium_doc_area | reason=public document/image evidence plus public area text | area=59.92 mÂ² | computed_polygon_area=61.61 mÂ² | perimeter=28.86 m | sides=[K1=4.88m, K2=2.39m, K3=4.77m, K4=2.39m, K5=4.88m, K6=2.39m, K7=4.77m, K8=2.39m] | area_source=public_site_area_text (645 sqft) | method=public_doc_or_image_plus_site_area | planning_refs=24/01377/FUL; 24/01378/LB | lot_refs= | title_refs= | doc_evidence=yes | NOT original/verified boundary; derived candidate geometry for display and review."},"OTM-19160820":{"listing_id":"OTM-19160820","confidence":"medium_low","previous_confidence":"low_plus","candidate_class":"candidate_medium_low_area_only","area_m2":"323.749","computed_area_m2":"332.857","perimeter_m":"67.088","side_lengths_m_json":"[11.343, 5.557, 11.087, 5.557, 11.343, 5.557, 11.087, 5.557]","area_source":"public_site_area_text","area_raw":"0.08 acre","method":"public_site_area_and_centroid","planning_refs":"","lot_refs":"","title_refs":"","doc_evidence":"no","note":"estimated_candidate_not_verified | confidence=medium_low | previous_confidence=low_plus | class=candidate_medium_low_area_only | reason=public area text and centroid; no plan/georef | area=323.75 mÂ² | computed_polygon_area=332.86 mÂ² | perimeter=67.09 m | sides=[K1=11.34m, K2=5.56m, K3=11.09m, K4=5.56m, K5=11.34m, K6=5.56m, K7=11.09m, K8=5.56m] | area_source=public_site_area_text (0.08 acre) | method=public_site_area_and_centroid | planning_refs= | lot_refs= | title_refs= | doc_evidence=no | NOT original/verified boundary; derived candidate geometry for display and review."},"OTM-19106269":{"listing_id":"OTM-19106269","confidence":"medium","previous_confidence":"low_plus","candidate_class":"candidate_medium_ref_area","area_m2":"155.0","computed_area_m2":"147.946","perimeter_m":"44.656","side_lengths_m_json":"[7.303, 3.842, 7.341, 3.842, 7.303, 3.842, 7.341, 3.842]","area_source":"public_site_area_text","area_raw":"155mÂ²","method":"public_site_area_and_centroid","planning_refs":"","lot_refs":"S","title_refs":"","doc_evidence":"no","note":"estimated_candidate_not_verified | confidence=medium | previous_confidence=low_plus | class=candidate_medium_ref_area | reason=public area text plus planning/lot/title reference | area=155.00 mÂ² | computed_polygon_area=147.95 mÂ² | perimeter=44.66 m | sides=[K1=7.30m, K2=3.84m, K3=7.34m, K4=3.84m, K5=7.30m, K6=3.84m, K7=7.34m, K8=3.84m] | area_source=public_site_area_text (155mÂ²) | method=public_site_area_and_centroid | planning_refs= | lot_refs=S | title_refs= | doc_evidence=no | NOT original/verified boundary; derived candidate geometry for display and review."},"OTM-19181813":{"listing_id":"OTM-19181813","confidence":"medium","previous_confidence":"medium_low","candidate_class":"candidate_medium_doc_area","area_m2":"7081.999","computed_area_m2":"6513.152","perimeter_m":"296.423","side_lengths_m_json":"[48.944, 25.232, 48.804, 25.232, 48.943, 25.232, 48.804, 25.232]","area_source":"public_site_area_text","area_raw":"1.75 acre","method":"public_doc_or_image_plus_site_area","planning_refs":"","lot_refs":"","title_refs":"","doc_evidence":"yes","note":"estimated_candidate_not_verified | confidence=medium | previous_confidence=medium_low | class=candidate_medium_doc_area | reason=public document/image evidence plus public area text | area=7,082.00 mÂ² | computed_polygon_area=6,513.15 mÂ² | perimeter=296.42 m | sides=[K1=48.94m, K2=25.23m, K3=48.80m, K4=25.23m, K5=48.94m, K6=25.23m, K7=48.80m, K8=25.23m] | area_source=public_site_area_text (1.75 acre) | method=public_doc_or_image_plus_site_area | planning_refs= | lot_refs= | title_refs= | doc_evidence=yes | NOT original/verified boundary; derived candidate geometry for display and review."},"OTM-18178169":{"listing_id":"OTM-18178169","confidence":"medium","previous_confidence":"medium_low","candidate_class":"candidate_medium_doc_area","area_m2":"42491.992","computed_area_m2":"41608.159","perimeter_m":"748.473","side_lengths_m_json":"[124.333, 66.855, 116.197, 66.854, 124.328, 66.854, 116.197, 66.855]","area_source":"public_site_area_text","area_raw":"10.50 acre","method":"public_doc_or_image_plus_site_area","planning_refs":"","lot_refs":"S","title_refs":"","doc_evidence":"yes","note":"estimated_candidate_not_verified | confidence=medium | previous_confidence=medium_low | class=candidate_medium_doc_area | reason=public document/image evidence plus public area text | area=42,491.99 mÂ² | computed_polygon_area=41,608.16 mÂ² | perimeter=748.47 m | sides=[K1=124.33m, K2=66.86m, K3=116.20m, K4=66.85m, K5=124.33m, K6=66.85m, K7=116.20m, K8=66.86m] | area_source=public_site_area_text (10.50 acre) | method=public_doc_or_image_plus_site_area | planning_refs= | lot_refs=S | title_refs= | doc_evidence=yes | NOT original/verified boundary; derived candidate geometry for display and review."},"OTM-18629579":{"listing_id":"OTM-18629579","confidence":"low_plus","previous_confidence":"low","candidate_class":"candidate_low_plus_feed","area_m2":"1353.307","computed_area_m2":"1335.731","perimeter_m":"133.934","side_lengths_m_json":"[20.539, 12.338, 21.752, 12.338, 20.539, 12.338, 21.752, 12.338]","area_source":"feed_bbox_area_fallback","area_raw":"feed_bbox_area_m2=1353.31","method":"feed_bbox_area_scaled_candidate","planning_refs":"","lot_refs":"","title_refs":"","doc_evidence":"no","note":"estimated_candidate_not_verified | confidence=low_plus | previous_confidence=low | class=candidate_low_plus_feed | reason=feed-scaled candidate; no public area/georef | area=1,353.31 mÂ² | computed_polygon_area=1,335.73 mÂ² | perimeter=133.93 m | sides=[K1=20.54m, K2=12.34m, K3=21.75m, K4=12.34m, K5=20.54m, K6=12.34m, K7=21.75m, K8=12.34m] | area_source=feed_bbox_area_fallback (feed_bbox_area_m2=1353.31) | method=feed_bbox_area_scaled_candidate | planning_refs= | lot_refs= | title_refs= | doc_evidence=no | NOT original/verified boundary; derived candidate geometry for display and review."},"OTM-19211068":{"listing_id":"OTM-19211068","confidence":"medium","previous_confidence":"low_plus","candidate_class":"candidate_medium_ref_area","area_m2":"1169.0","computed_area_m2":"1223.35","perimeter_m":"128.58","side_lengths_m_json":"[21.637, 10.709, 21.235, 10.709, 21.637, 10.709, 21.235, 10.709]","area_source":"public_site_area_text","area_raw":"1,169 sq m","method":"public_site_area_and_centroid","planning_refs":"","lot_refs":"COMPRISES","title_refs":"","doc_evidence":"no","note":"estimated_candidate_not_verified | confidence=medium | previous_confidence=low_plus | class=candidate_medium_ref_area | reason=public area text plus planning/lot/title reference | area=1,169.00 mÂ² | computed_polygon_area=1,223.35 mÂ² | perimeter=128.58 m | sides=[K1=21.64m, K2=10.71m, K3=21.23m, K4=10.71m, K5=21.64m, K6=10.71m, K7=21.23m, K8=10.71m] | area_source=public_site_area_text (1,169 sq m) | method=public_site_area_and_centroid | planning_refs= | lot_refs=COMPRISES | title_refs= | doc_evidence=no | NOT original/verified boundary; derived candidate geometry for display and review."},"OTM-13517231":{"listing_id":"OTM-13517231","confidence":"medium","previous_confidence":"medium_low","candidate_class":"candidate_medium_doc_area","area_m2":"38849.822","computed_area_m2":"37149.288","perimeter_m":"709.481","side_lengths_m_json":"[122.278, 57.478, 117.51, 57.477, 122.273, 57.477, 117.51, 57.478]","area_source":"public_site_area_text","area_raw":"9.60 acre","method":"public_doc_or_image_plus_site_area","planning_refs":"","lot_refs":"","title_refs":"","doc_evidence":"yes","note":"estimated_candidate_not_verified | confidence=medium | previous_confidence=medium_low | class=candidate_medium_doc_area | reason=public document/image evidence plus public area text | area=38,849.82 mÂ² | computed_polygon_area=37,149.29 mÂ² | perimeter=709.48 m | sides=[K1=122.28m, K2=57.48m, K3=117.51m, K4=57.48m, K5=122.27m, K6=57.48m, K7=117.51m, K8=57.48m] | area_source=public_site_area_text (9.60 acre) | method=public_doc_or_image_plus_site_area | planning_refs= | lot_refs= | title_refs= | doc_evidence=yes | NOT original/verified boundary; derived candidate geometry for display and review."},"OTM-19122328":{"listing_id":"OTM-19122328","confidence":"medium_low","previous_confidence":"low_plus","candidate_class":"candidate_medium_low_area_only","area_m2":"2298.22","computed_area_m2":"2405.071","perimeter_m":"180.288","side_lengths_m_json":"[30.338, 15.016, 29.774, 15.016, 30.338, 15.016, 29.774, 15.016]","area_source":"public_site_area_text","area_raw":"2298.22 Square Metres","method":"public_site_area_and_centroid","planning_refs":"","lot_refs":"","title_refs":"","doc_evidence":"no","note":"estimated_candidate_not_verified | confidence=medium_low | previous_confidence=low_plus | class=candidate_medium_low_area_only | reason=public area text and centroid; no plan/georef | area=2,298.22 mÂ² | computed_polygon_area=2,405.07 mÂ² | perimeter=180.29 m | sides=[K1=30.34m, K2=15.02m, K3=29.77m, K4=15.02m, K5=30.34m, K6=15.02m, K7=29.77m, K8=15.02m] | area_source=public_site_area_text (2298.22 Square Metres) | method=public_site_area_and_centroid | planning_refs= | lot_refs= | title_refs= | doc_evidence=no | NOT original/verified boundary; derived candidate geometry for display and review."},"OTM-18626551":{"listing_id":"OTM-18626551","confidence":"low_plus","previous_confidence":"low","candidate_class":"candidate_low_plus_feed","area_m2":"9127.738","computed_area_m2":"8712.362","perimeter_m":"342.693","side_lengths_m_json":"[56.04, 29.486, 56.335, 29.486, 56.039, 29.486, 56.335, 29.486]","area_source":"feed_bbox_area_fallback","area_raw":"feed_bbox_area_m2=9127.74","method":"feed_bbox_area_scaled_candidate","planning_refs":"","lot_refs":"","title_refs":"","doc_evidence":"no","note":"estimated_candidate_not_verified | confidence=low_plus | previous_confidence=low | class=candidate_low_plus_feed | reason=feed-scaled candidate; no public area/georef | area=9,127.74 mÂ² | computed_polygon_area=8,712.36 mÂ² | perimeter=342.69 m | sides=[K1=56.04m, K2=29.49m, K3=56.34m, K4=29.49m, K5=56.04m, K6=29.49m, K7=56.34m, K8=29.49m] | area_source=feed_bbox_area_fallback (feed_bbox_area_m2=9127.74) | method=feed_bbox_area_scaled_candidate | planning_refs= | lot_refs= | title_refs= | doc_evidence=no | NOT original/verified boundary; derived candidate geometry for display and review."},"OTM-18738147":{"listing_id":"OTM-18738147","confidence":"medium_low","previous_confidence":"low_plus","candidate_class":"candidate_medium_low_area_only","area_m2":"78.039","computed_area_m2":"81.491","perimeter_m":"33.112","side_lengths_m_json":"[5.287, 2.926, 5.417, 2.926, 5.287, 2.926, 5.417, 2.926]","area_source":"public_site_area_text","area_raw":"840 sq ft","method":"public_site_area_and_centroid","planning_refs":"","lot_refs":"","title_refs":"","doc_evidence":"no","note":"estimated_candidate_not_verified | confidence=medium_low | previous_confidence=low_plus | class=candidate_medium_low_area_only | reason=public area text and centroid; no plan/georef | area=78.04 mÂ² | computed_polygon_area=81.49 mÂ² | perimeter=33.11 m | sides=[K1=5.29m, K2=2.93m, K3=5.42m, K4=2.93m, K5=5.29m, K6=2.93m, K7=5.42m, K8=2.93m] | area_source=public_site_area_text (840 sq ft) | method=public_site_area_and_centroid | planning_refs= | lot_refs= | title_refs= | doc_evidence=no | NOT original/verified boundary; derived candidate geometry for display and review."},"OTM-7634689":{"listing_id":"OTM-7634689","confidence":"medium_low","previous_confidence":"low_plus","candidate_class":"candidate_medium_low_area_only","area_m2":"106.931","computed_area_m2":"101.808","perimeter_m":"37.412","side_lengths_m_json":"[6.967, 2.563, 6.613, 2.563, 6.967, 2.563, 6.613, 2.563]","area_source":"public_site_area_text","area_raw":"1151 sq ft","method":"public_site_area_and_centroid","planning_refs":"","lot_refs":"","title_refs":"","doc_evidence":"no","note":"estimated_candidate_not_verified | confidence=medium_low | previous_confidence=low_plus | class=candidate_medium_low_area_only | reason=public area text and centroid; no plan/georef | area=106.93 mÂ² | computed_polygon_area=101.81 mÂ² | perimeter=37.41 m | sides=[K1=6.97m, K2=2.56m, K3=6.61m, K4=2.56m, K5=6.97m, K6=2.56m, K7=6.61m, K8=2.56m] | area_source=public_site_area_text (1151 sq ft) | method=public_site_area_and_centroid | planning_refs= | lot_refs= | title_refs= | doc_evidence=no | NOT original/verified boundary; derived candidate geometry for display and review."},"OTM-17591025":{"listing_id":"OTM-17591025","confidence":"medium","previous_confidence":"medium_low","candidate_class":"candidate_medium_doc_area","area_m2":"19910.534","computed_area_m2":"21576.588","perimeter_m":"539.75","side_lengths_m_json":"[89.977, 45.448, 89.003, 45.448, 89.975, 45.448, 89.003, 45.448]","area_source":"public_site_area_text","area_raw":"4.92 acre","method":"public_doc_or_image_plus_site_area","planning_refs":"","lot_refs":"","title_refs":"","doc_evidence":"yes","note":"estimated_candidate_not_verified | confidence=medium | previous_confidence=medium_low | class=candidate_medium_doc_area | reason=public document/image evidence plus public area text | area=19,910.53 mÂ² | computed_polygon_area=21,576.59 mÂ² | perimeter=539.75 m | sides=[K1=89.98m, K2=45.45m, K3=89.00m, K4=45.45m, K5=89.97m, K6=45.45m, K7=89.00m, K8=45.45m] | area_source=public_site_area_text (4.92 acre) | method=public_doc_or_image_plus_site_area | planning_refs= | lot_refs= | title_refs= | doc_evidence=yes | NOT original/verified boundary; derived candidate geometry for display and review."},"OTM-17510501":{"listing_id":"OTM-17510501","confidence":"medium_low","previous_confidence":"low_plus","candidate_class":"candidate_medium_low_area_only","area_m2":"40000.0","computed_area_m2":"40048.68","perimeter_m":"737.251","side_lengths_m_json":"[122.516, 58.728, 128.657, 58.727, 122.511, 58.727, 128.657, 58.728]","area_source":"public_site_area_text","area_raw":"4HA","method":"public_site_area_and_centroid","planning_refs":"","lot_refs":"","title_refs":"","doc_evidence":"no","note":"estimated_candidate_not_verified | confidence=medium_low | previous_confidence=low_plus | class=candidate_medium_low_area_only | reason=public area text and centroid; no plan/georef | area=40,000.00 mÂ² | computed_polygon_area=40,048.68 mÂ² | perimeter=737.25 m | sides=[K1=122.52m, K2=58.73m, K3=128.66m, K4=58.73m, K5=122.51m, K6=58.73m, K7=128.66m, K8=58.73m] | area_source=public_site_area_text (4HA) | method=public_site_area_and_centroid | planning_refs= | lot_refs= | title_refs= | doc_evidence=no | NOT original/verified boundary; derived candidate geometry for display and review."},"OTM-17638486":{"listing_id":"OTM-17638486","confidence":"low_plus","previous_confidence":"low","candidate_class":"candidate_low_plus_feed","area_m2":"116.314","computed_area_m2":"118.104","perimeter_m":"39.854","side_lengths_m_json":"[6.553, 3.597, 6.18, 3.597, 6.553, 3.597, 6.18, 3.597]","area_source":"feed_bbox_area_fallback","area_raw":"feed_bbox_area_m2=116.31","method":"feed_bbox_area_scaled_candidate","planning_refs":"","lot_refs":"","title_refs":"","doc_evidence":"no","note":"estimated_candidate_not_verified | confidence=low_plus | previous_confidence=low | class=candidate_low_plus_feed | reason=feed-scaled candidate; no public area/georef | area=116.31 mÂ² | computed_polygon_area=118.10 mÂ² | perimeter=39.85 m | sides=[K1=6.55m, K2=3.60m, K3=6.18m, K4=3.60m, K5=6.55m, K6=3.60m, K7=6.18m, K8=3.60m] | area_source=feed_bbox_area_fallback (feed_bbox_area_m2=116.31) | method=feed_bbox_area_scaled_candidate | planning_refs= | lot_refs= | title_refs= | doc_evidence=no | NOT original/verified boundary; derived candidate geometry for display and review."},"OTM-18622740":{"listing_id":"OTM-18622740","confidence":"medium_low","previous_confidence":"low_plus","candidate_class":"candidate_medium_low_area_only","area_m2":"1618.743","computed_area_m2":"1754.195","perimeter_m":"153.902","side_lengths_m_json":"[25.655, 12.959, 25.378, 12.959, 25.655, 12.959, 25.378, 12.959]","area_source":"public_site_area_text","area_raw":"0.40 acre","method":"public_site_area_and_centroid","planning_refs":"","lot_refs":"","title_refs":"","doc_evidence":"no","note":"estimated_candidate_not_verified | confidence=medium_low | previous_confidence=low_plus | class=candidate_medium_low_area_only | reason=public area text and centroid; no plan/georef | area=1,618.74 mÂ² | computed_polygon_area=1,754.19 mÂ² | perimeter=153.90 m | sides=[K1=25.66m, K2=12.96m, K3=25.38m, K4=12.96m, K5=25.66m, K6=12.96m, K7=25.38m, K8=12.96m] | area_source=public_site_area_text (0.40 acre) | method=public_site_area_and_centroid | planning_refs= | lot_refs= | title_refs= | doc_evidence=no | NOT original/verified boundary; derived candidate geometry for display and review."},"OTM-16593662":{"listing_id":"OTM-16593662","confidence":"medium","previous_confidence":"medium","candidate_class":"candidate_medium_visual_plan","area_m2":"6636.845","computed_area_m2":"6809.224","perimeter_m":"302.742","side_lengths_m_json":"[48.57, 26.61, 49.581, 26.61, 48.57, 26.61, 49.581, 26.61]","area_source":"public_site_area_text","area_raw":"1.64 acre","method":"public_planning_visual_plan_no_georef","planning_refs":"24/00250/FUL","lot_refs":"","title_refs":"","doc_evidence":"yes","note":"estimated_candidate_not_verified | confidence=medium | previous_confidence=medium | class=candidate_medium_visual_plan | reason=public planning visual/site-plan evidence exists; no georeference | area=6,636.85 mÂ² | computed_polygon_area=6,809.22 mÂ² | perimeter=302.74 m | sides=[K1=48.57m, K2=26.61m, K3=49.58m, K4=26.61m, K5=48.57m, K6=26.61m, K7=49.58m, K8=26.61m] | area_source=public_site_area_text (1.64 acre) | method=public_planning_visual_plan_no_georef | planning_refs=24/00250/FUL | lot_refs= | title_refs= | doc_evidence=yes | NOT original/verified boundary; derived candidate geometry for display and review."},"OTM-16441318":{"listing_id":"OTM-16441318","confidence":"medium_low","previous_confidence":"low","candidate_class":"candidate_medium_low_doc_only","area_m2":"1193.779","computed_area_m2":"1249.282","perimeter_m":"129.936","side_lengths_m_json":"[21.865, 10.822, 21.459, 10.822, 21.865, 10.822, 21.459, 10.822]","area_source":"feed_bbox_area_fallback","area_raw":"feed_bbox_area_m2=1193.78","method":"feed_bbox_area_scaled_candidate","planning_refs":"","lot_refs":"","title_refs":"","doc_evidence":"yes","note":"estimated_candidate_not_verified | confidence=medium_low | previous_confidence=low | class=candidate_medium_low_doc_only | reason=public document/image evidence but no public site area | area=1,193.78 mÂ² | computed_polygon_area=1,249.28 mÂ² | perimeter=129.94 m | sides=[K1=21.86m, K2=10.82m, K3=21.46m, K4=10.82m, K5=21.86m, K6=10.82m, K7=21.46m, K8=10.82m] | area_source=feed_bbox_area_fallback (feed_bbox_area_m2=1193.78) | method=feed_bbox_area_scaled_candidate | planning_refs= | lot_refs= | title_refs= | doc_evidence=yes | NOT original/verified boundary; derived candidate geometry for display and review."},"OTM-15986295":{"listing_id":"OTM-15986295","confidence":"low_plus","previous_confidence":"low","candidate_class":"candidate_low_plus_feed","area_m2":"5841.752","computed_area_m2":"6146.645","perimeter_m":"287.369","side_lengths_m_json":"[46.781, 26.201, 44.502, 26.201, 46.78, 26.201, 44.502, 26.201]","area_source":"feed_bbox_area_fallback","area_raw":"feed_bbox_area_m2=5841.75","method":"feed_bbox_area_scaled_candidate","planning_refs":"","lot_refs":"","title_refs":"","doc_evidence":"no","note":"estimated_candidate_not_verified | confidence=low_plus | previous_confidence=low | class=candidate_low_plus_feed | reason=feed-scaled candidate; no public area/georef | area=5,841.75 mÂ² | computed_polygon_area=6,146.65 mÂ² | perimeter=287.37 m | sides=[K1=46.78m, K2=26.20m, K3=44.50m, K4=26.20m, K5=46.78m, K6=26.20m, K7=44.50m, K8=26.20m] | area_source=feed_bbox_area_fallback (feed_bbox_area_m2=5841.75) | method=feed_bbox_area_scaled_candidate | planning_refs= | lot_refs= | title_refs= | doc_evidence=no | NOT original/verified boundary; derived candidate geometry for display and review."},"OTM-18980499":{"listing_id":"OTM-18980499","confidence":"medium_low","previous_confidence":"low_plus","candidate_class":"candidate_medium_low_area_only","area_m2":"404.686","computed_area_m2":"406.65","perimeter_m":"73.894","side_lengths_m_json":"[11.278, 6.842, 11.985, 6.842, 11.278, 6.842, 11.985, 6.842]","area_source":"public_site_area_text","area_raw":"0.10 acre","method":"public_site_area_and_centroid","planning_refs":"","lot_refs":"","title_refs":"","doc_evidence":"no","note":"estimated_candidate_not_verified | confidence=medium_low | previous_confidence=low_plus | class=candidate_medium_low_area_only | reason=public area text and centroid; no plan/georef | area=404.69 mÂ² | computed_polygon_area=406.65 mÂ² | perimeter=73.89 m | sides=[K1=11.28m, K2=6.84m, K3=11.98m, K4=6.84m, K5=11.28m, K6=6.84m, K7=11.98m, K8=6.84m] | area_source=public_site_area_text (0.10 acre) | method=public_site_area_and_centroid | planning_refs= | lot_refs= | title_refs= | doc_evidence=no | NOT original/verified boundary; derived candidate geometry for display and review."},"OTM-19139156":{"listing_id":"OTM-19139156","confidence":"medium","previous_confidence":"low_plus","candidate_class":"candidate_medium_ref_area","area_m2":"331.943","computed_area_m2":"322.692","perimeter_m":"65.938","side_lengths_m_json":"[10.731, 5.704, 10.83, 5.704, 10.731, 5.704, 10.83, 5.704]","area_source":"public_site_area_text","area_raw":"3573 sq ft","method":"public_site_area_and_centroid","planning_refs":"","lot_refs":"COMPRISES","title_refs":"","doc_evidence":"no","note":"estimated_candidate_not_verified | confidence=medium | previous_confidence=low_plus | class=candidate_medium_ref_area | reason=public area text plus planning/lot/title reference | area=331.94 mÂ² | computed_polygon_area=322.69 mÂ² | perimeter=65.94 m | sides=[K1=10.73m, K2=5.70m, K3=10.83m, K4=5.70m, K5=10.73m, K6=5.70m, K7=10.83m, K8=5.70m] | area_source=public_site_area_text (3573 sq ft) | method=public_site_area_and_centroid | planning_refs= | lot_refs=COMPRISES | title_refs= | doc_evidence=no | NOT original/verified boundary; derived candidate geometry for display and review."},"OTM-18511608":{"listing_id":"OTM-18511608","confidence":"low_plus","previous_confidence":"low","candidate_class":"candidate_low_plus_feed","area_m2":"63894.166","computed_area_m2":"69240.638","perimeter_m":"966.899","side_lengths_m_json":"[161.186, 81.416, 159.438, 81.414, 161.177, 81.414, 159.438, 81.416]","area_source":"feed_bbox_area_fallback","area_raw":"feed_bbox_area_m2=63894.17","method":"feed_bbox_area_scaled_candidate","planning_refs":"","lot_refs":"","title_refs":"","doc_evidence":"no","note":"estimated_candidate_not_verified | confidence=low_plus | previous_confidence=low | class=candidate_low_plus_feed | reason=feed-scaled candidate; no public area/georef | area=63,894.17 mÂ² | computed_polygon_area=69,240.64 mÂ² | perimeter=966.90 m | sides=[K1=161.19m, K2=81.42m, K3=159.44m, K4=81.41m, K5=161.18m, K6=81.41m, K7=159.44m, K8=81.42m] | area_source=feed_bbox_area_fallback (feed_bbox_area_m2=63894.17) | method=feed_bbox_area_scaled_candidate | planning_refs= | lot_refs= | title_refs= | doc_evidence=no | NOT original/verified boundary; derived candidate geometry for display and review."},"OTM-19167220":{"listing_id":"OTM-19167220","confidence":"medium","previous_confidence":"low_plus","candidate_class":"candidate_medium_ref_area","area_m2":"160.908","computed_area_m2":"168.389","perimeter_m":"47.704","side_lengths_m_json":"[8.028, 3.973, 7.878, 3.973, 8.028, 3.973, 7.878, 3.973]","area_source":"public_site_area_text","area_raw":"1732 sq ft","method":"public_site_area_and_centroid","planning_refs":"","lot_refs":"COMPRISES","title_refs":"","doc_evidence":"no","note":"estimated_candidate_not_verified | confidence=medium | previous_confidence=low_plus | class=candidate_medium_ref_area | reason=public area text plus planning/lot/title reference | area=160.91 mÂ² | computed_polygon_area=168.39 mÂ² | perimeter=47.70 m | sides=[K1=8.03m, K2=3.97m, K3=7.88m, K4=3.97m, K5=8.03m, K6=3.97m, K7=7.88m, K8=3.97m] | area_source=public_site_area_text (1732 sq ft) | method=public_site_area_and_centroid | planning_refs= | lot_refs=COMPRISES | title_refs= | doc_evidence=no | NOT original/verified boundary; derived candidate geometry for display and review."},"OTM-18087053":{"listing_id":"OTM-18087053","confidence":"medium_low","previous_confidence":"low_plus","candidate_class":"candidate_medium_low_area_only","area_m2":"121.406","computed_area_m2":"111.654","perimeter_m":"38.812","side_lengths_m_json":"[6.408, 3.304, 6.39, 3.304, 6.408, 3.304, 6.39, 3.304]","area_source":"public_site_area_text","area_raw":"0.030 acres","method":"public_site_area_and_centroid","planning_refs":"","lot_refs":"","title_refs":"","doc_evidence":"no","note":"estimated_candidate_not_verified | confidence=medium_low | previous_confidence=low_plus | class=candidate_medium_low_area_only | reason=public area text and centroid; no plan/georef | area=121.41 mÂ² | computed_polygon_area=111.65 mÂ² | perimeter=38.81 m | sides=[K1=6.41m, K2=3.30m, K3=6.39m, K4=3.30m, K5=6.41m, K6=3.30m, K7=6.39m, K8=3.30m] | area_source=public_site_area_text (0.030 acres) | method=public_site_area_and_centroid | planning_refs= | lot_refs= | title_refs= | doc_evidence=no | NOT original/verified boundary; derived candidate geometry for display and review."},"OTM-19032477":{"listing_id":"OTM-19032477","confidence":"low_plus","previous_confidence":"low","candidate_class":"candidate_low_plus_feed","area_m2":"25557.666","computed_area_m2":"23947.738","perimeter_m":"568.271","side_lengths_m_json":"[93.378, 48.634, 93.492, 48.633, 93.375, 48.633, 93.492, 48.634]","area_source":"feed_bbox_area_fallback","area_raw":"feed_bbox_area_m2=25557.67","method":"feed_bbox_area_scaled_candidate","planning_refs":"","lot_refs":"","title_refs":"","doc_evidence":"no","note":"estimated_candidate_not_verified | confidence=low_plus | previous_confidence=low | class=candidate_low_plus_feed | reason=feed-scaled candidate; no public area/georef | area=25,557.67 mÂ² | computed_polygon_area=23,947.74 mÂ² | perimeter=568.27 m | sides=[K1=93.38m, K2=48.63m, K3=93.49m, K4=48.63m, K5=93.38m, K6=48.63m, K7=93.49m, K8=48.63m] | area_source=feed_bbox_area_fallback (feed_bbox_area_m2=25557.67) | method=feed_bbox_area_scaled_candidate | planning_refs= | lot_refs= | title_refs= | doc_evidence=no | NOT original/verified boundary; derived candidate geometry for display and review."},"OTM-18499425":{"listing_id":"OTM-18499425","confidence":"medium","previous_confidence":"medium_low","candidate_class":"candidate_medium_doc_area","area_m2":"572.933","computed_area_m2":"571.339","perimeter_m":"87.68","side_lengths_m_json":"[14.491, 7.872, 13.605, 7.872, 14.491, 7.872, 13.605, 7.872]","area_source":"public_site_area_text","area_raw":"6167 sq ft","method":"public_doc_or_image_plus_site_area","planning_refs":"24/01871/PRA","lot_refs":"","title_refs":"","doc_evidence":"yes","note":"estimated_candidate_not_verified | confidence=medium | previous_confidence=medium_low | class=candidate_medium_doc_area | reason=public document/image evidence plus public area text | area=572.93 mÂ² | computed_polygon_area=571.34 mÂ² | perimeter=87.68 m | sides=[K1=14.49m, K2=7.87m, K3=13.61m, K4=7.87m, K5=14.49m, K6=7.87m, K7=13.61m, K8=7.87m] | area_source=public_site_area_text (6167 sq ft) | method=public_doc_or_image_plus_site_area | planning_refs=24/01871/PRA | lot_refs= | title_refs= | doc_evidence=yes | NOT original/verified boundary; derived candidate geometry for display and review."},"OTM-14648028":{"listing_id":"OTM-14648028","confidence":"medium","previous_confidence":"medium_low","candidate_class":"candidate_medium_doc_area","area_m2":"809.371","computed_area_m2":"758.387","perimeter_m":"101.13","side_lengths_m_json":"[16.617, 8.655, 16.638, 8.655, 16.617, 8.655, 16.638, 8.655]","area_source":"public_site_area_text","area_raw":"0.2 acres","method":"public_doc_or_image_plus_site_area","planning_refs":"","lot_refs":"","title_refs":"","doc_evidence":"yes","note":"estimated_candidate_not_verified | confidence=medium | previous_confidence=medium_low | class=candidate_medium_doc_area | reason=public document/image evidence plus public area text | area=809.37 mÂ² | computed_polygon_area=758.39 mÂ² | perimeter=101.13 m | sides=[K1=16.62m, K2=8.65m, K3=16.64m, K4=8.65m, K5=16.62m, K6=8.65m, K7=16.64m, K8=8.65m] | area_source=public_site_area_text (0.2 acres) | method=public_doc_or_image_plus_site_area | planning_refs= | lot_refs= | title_refs= | doc_evidence=yes | NOT original/verified boundary; derived candidate geometry for display and review."},"OTM-19137618":{"listing_id":"OTM-19137618","confidence":"medium_low","previous_confidence":"low_plus","candidate_class":"candidate_medium_low_area_only","area_m2":"4046.856","computed_area_m2":"4006.084","perimeter_m":"232.293","side_lengths_m_json":"[37.624, 20.202, 38.119, 20.202, 37.623, 20.202, 38.119, 20.202]","area_source":"public_site_area_text","area_raw":"1.00 acre","method":"public_site_area_and_centroid","planning_refs":"","lot_refs":"","title_refs":"","doc_evidence":"no","note":"estimated_candidate_not_verified | confidence=medium_low | previous_confidence=low_plus | class=candidate_medium_low_area_only | reason=public area text and centroid; no plan/georef | area=4,046.86 mÂ² | computed_polygon_area=4,006.08 mÂ² | perimeter=232.29 m | sides=[K1=37.62m, K2=20.20m, K3=38.12m, K4=20.20m, K5=37.62m, K6=20.20m, K7=38.12m, K8=20.20m] | area_source=public_site_area_text (1.00 acre) | method=public_site_area_and_centroid | planning_refs= | lot_refs= | title_refs= | doc_evidence=no | NOT original/verified boundary; derived candidate geometry for display and review."},"OTM-8146777":{"listing_id":"OTM-8146777","confidence":"medium","previous_confidence":"medium_low","candidate_class":"candidate_medium_doc_area","area_m2":"1858.061","computed_area_m2":"1853.447","perimeter_m":"159.73","side_lengths_m_json":"[28.659, 10.733, 29.74, 10.733, 28.659, 10.733, 29.74, 10.733]","area_source":"public_site_area_text","area_raw":"20,000 sq ft","method":"public_doc_or_image_plus_site_area","planning_refs":"","lot_refs":"","title_refs":"","doc_evidence":"yes","note":"estimated_candidate_not_verified | confidence=medium | previous_confidence=medium_low | class=candidate_medium_doc_area | reason=public document/image evidence plus public area text | area=1,858.06 mÂ² | computed_polygon_area=1,853.45 mÂ² | perimeter=159.73 m | sides=[K1=28.66m, K2=10.73m, K3=29.74m, K4=10.73m, K5=28.66m, K6=10.73m, K7=29.74m, K8=10.73m] | area_source=public_site_area_text (20,000 sq ft) | method=public_doc_or_image_plus_site_area | planning_refs= | lot_refs= | title_refs= | doc_evidence=yes | NOT original/verified boundary; derived candidate geometry for display and review."},"OTM-18447114":{"listing_id":"OTM-18447114","confidence":"medium_low","previous_confidence":"low_plus","candidate_class":"candidate_medium_low_area_only","area_m2":"185.806","computed_area_m2":"201.354","perimeter_m":"52.14","side_lengths_m_json":"[8.692, 4.39, 8.598, 4.39, 8.692, 4.39, 8.598, 4.39]","area_source":"public_site_area_text","area_raw":"2,000 sq ft","method":"public_site_area_and_centroid","planning_refs":"","lot_refs":"","title_refs":"","doc_evidence":"no","note":"estimated_candidate_not_verified | confidence=medium_low | previous_confidence=low_plus | class=candidate_medium_low_area_only | reason=public area text and centroid; no plan/georef | area=185.81 mÂ² | computed_polygon_area=201.35 mÂ² | perimeter=52.14 m | sides=[K1=8.69m, K2=4.39m, K3=8.60m, K4=4.39m, K5=8.69m, K6=4.39m, K7=8.60m, K8=4.39m] | area_source=public_site_area_text (2,000 sq ft) | method=public_site_area_and_centroid | planning_refs= | lot_refs= | title_refs= | doc_evidence=no | NOT original/verified boundary; derived candidate geometry for display and review."},"OTM-18084236":{"listing_id":"OTM-18084236","confidence":"low_plus","previous_confidence":"low","candidate_class":"candidate_low_plus_feed","area_m2":"25557.666","computed_area_m2":"23504.798","perimeter_m":"563.109","side_lengths_m_json":"[92.979, 47.933, 92.712, 47.932, 92.976, 47.932, 92.712, 47.933]","area_source":"feed_bbox_area_fallback","area_raw":"feed_bbox_area_m2=25557.67","method":"feed_bbox_area_scaled_candidate","planning_refs":"","lot_refs":"","title_refs":"","doc_evidence":"no","note":"estimated_candidate_not_verified | confidence=low_plus | previous_confidence=low | class=candidate_low_plus_feed | reason=feed-scaled candidate; no public area/georef | area=25,557.67 mÂ² | computed_polygon_area=23,504.80 mÂ² | perimeter=563.11 m | sides=[K1=92.98m, K2=47.93m, K3=92.71m, K4=47.93m, K5=92.98m, K6=47.93m, K7=92.71m, K8=47.93m] | area_source=feed_bbox_area_fallback (feed_bbox_area_m2=25557.67) | method=feed_bbox_area_scaled_candidate | planning_refs= | lot_refs= | title_refs= | doc_evidence=no | NOT original/verified boundary; derived candidate geometry for display and review."},"OTM-19170813":{"listing_id":"OTM-19170813","confidence":"medium","previous_confidence":"medium_low","candidate_class":"candidate_medium_doc_area","area_m2":"80.082","computed_area_m2":"86.783","perimeter_m":"34.23","side_lengths_m_json":"[5.706, 2.882, 5.645, 2.882, 5.706, 2.882, 5.645, 2.882]","area_source":"public_site_area_text","area_raw":"862 sq ft","method":"public_doc_or_image_plus_site_area","planning_refs":"","lot_refs":"","title_refs":"","doc_evidence":"yes","note":"estimated_candidate_not_verified | confidence=medium | previous_confidence=medium_low | class=candidate_medium_doc_area | reason=public document/image evidence plus public area text | area=80.08 mÂ² | computed_polygon_area=86.78 mÂ² | perimeter=34.23 m | sides=[K1=5.71m, K2=2.88m, K3=5.64m, K4=2.88m, K5=5.71m, K6=2.88m, K7=5.64m, K8=2.88m] | area_source=public_site_area_text (862 sq ft) | method=public_doc_or_image_plus_site_area | planning_refs= | lot_refs= | title_refs= | doc_evidence=yes | NOT original/verified boundary; derived candidate geometry for display and review."},"OTM-15740059":{"listing_id":"OTM-15740059","confidence":"medium","previous_confidence":"medium_low","candidate_class":"candidate_medium_doc_area","area_m2":"829.6","computed_area_m2":"914.634","perimeter_m":"111.102","side_lengths_m_json":"[18.434, 9.406, 18.305, 9.406, 18.434, 9.406, 18.305, 9.406]","area_source":"public_site_area_text","area_raw":"829.6 sqm","method":"public_doc_or_image_plus_site_area","planning_refs":"","lot_refs":"","title_refs":"","doc_evidence":"yes","note":"estimated_candidate_not_verified | confidence=medium | previous_confidence=medium_low | class=candidate_medium_doc_area | reason=public document/image evidence plus public area text | area=829.60 mÂ² | computed_polygon_area=914.63 mÂ² | perimeter=111.10 m | sides=[K1=18.43m, K2=9.41m, K3=18.30m, K4=9.41m, K5=18.43m, K6=9.41m, K7=18.30m, K8=9.41m] | area_source=public_site_area_text (829.6 sqm) | method=public_doc_or_image_plus_site_area | planning_refs= | lot_refs= | title_refs= | doc_evidence=yes | NOT original/verified boundary; derived candidate geometry for display and review."},"OTM-19122668":{"listing_id":"OTM-19122668","confidence":"medium_low","previous_confidence":"low_plus","candidate_class":"candidate_medium_low_area_only","area_m2":"7243.873","computed_area_m2":"7042.001","perimeter_m":"308.038","side_lengths_m_json":"[50.131, 26.647, 50.594, 26.647, 50.131, 26.647, 50.594, 26.647]","area_source":"public_site_area_text","area_raw":"1.79 Acres","method":"public_site_area_and_centroid","planning_refs":"","lot_refs":"","title_refs":"","doc_evidence":"no","note":"estimated_candidate_not_verified | confidence=medium_low | previous_confidence=low_plus | class=candidate_medium_low_area_only | reason=public area text and centroid; no plan/georef | area=7,243.87 mÂ² | computed_polygon_area=7,042.00 mÂ² | perimeter=308.04 m | sides=[K1=50.13m, K2=26.65m, K3=50.59m, K4=26.65m, K5=50.13m, K6=26.65m, K7=50.59m, K8=26.65m] | area_source=public_site_area_text (1.79 Acres) | method=public_site_area_and_centroid | planning_refs= | lot_refs= | title_refs= | doc_evidence=no | NOT original/verified boundary; derived candidate geometry for display and review."},"OTM-18317780":{"listing_id":"OTM-18317780","confidence":"medium","previous_confidence":"medium_low","candidate_class":"candidate_medium_doc_area","area_m2":"181.499","computed_area_m2":"176.441","perimeter_m":"48.76","side_lengths_m_json":"[7.935, 4.218, 8.009, 4.218, 7.935, 4.218, 8.009, 4.218]","area_source":"public_site_area_text","area_raw":"1953.64 sq ft","method":"public_doc_or_image_plus_site_area","planning_refs":"","lot_refs":"S","title_refs":"","doc_evidence":"yes","note":"estimated_candidate_not_verified | confidence=medium | previous_confidence=medium_low | class=candidate_medium_doc_area | reason=public document/image evidence plus public area text | area=181.50 mÂ² | computed_polygon_area=176.44 mÂ² | perimeter=48.76 m | sides=[K1=7.93m, K2=4.22m, K3=8.01m, K4=4.22m, K5=7.93m, K6=4.22m, K7=8.01m, K8=4.22m] | area_source=public_site_area_text (1953.64 sq ft) | method=public_doc_or_image_plus_site_area | planning_refs= | lot_refs=S | title_refs= | doc_evidence=yes | NOT original/verified boundary; derived candidate geometry for display and review."},"OTM-18186897":{"listing_id":"OTM-18186897","confidence":"medium","previous_confidence":"medium_low","candidate_class":"candidate_medium_doc_area","area_m2":"8619.804","computed_area_m2":"8661.636","perimeter_m":"341.023","side_lengths_m_json":"[52.049, 31.576, 55.311, 31.576, 52.048, 31.576, 55.311, 31.576]","area_source":"public_site_area_text","area_raw":"2.13 acre","method":"public_doc_or_image_plus_site_area","planning_refs":"","lot_refs":"","title_refs":"","doc_evidence":"yes","note":"estimated_candidate_not_verified | confidence=medium | previous_confidence=medium_low | class=candidate_medium_doc_area | reason=public document/image evidence plus public area text | area=8,619.80 mÂ² | computed_polygon_area=8,661.64 mÂ² | perimeter=341.02 m | sides=[K1=52.05m, K2=31.58m, K3=55.31m, K4=31.58m, K5=52.05m, K6=31.58m, K7=55.31m, K8=31.58m] | area_source=public_site_area_text (2.13 acre) | method=public_doc_or_image_plus_site_area | planning_refs= | lot_refs= | title_refs= | doc_evidence=yes | NOT original/verified boundary; derived candidate geometry for display and review."},"OTM-19300302":{"listing_id":"OTM-19300302","confidence":"medium","previous_confidence":"medium_low","candidate_class":"candidate_medium_doc_area","area_m2":"2023.428","computed_area_m2":"1954.051","perimeter_m":"162.91","side_lengths_m_json":"[27.315, 12.829, 28.482, 12.829, 27.315, 12.829, 28.482, 12.829]","area_source":"public_site_area_text","area_raw":"0.50 acres","method":"public_doc_or_image_plus_site_area","planning_refs":"","lot_refs":"","title_refs":"","doc_evidence":"yes","note":"estimated_candidate_not_verified | confidence=medium | previous_confidence=medium_low | class=candidate_medium_doc_area | reason=public document/image evidence plus public area text | area=2,023.43 mÂ² | computed_polygon_area=1,954.05 mÂ² | perimeter=162.91 m | sides=[K1=27.32m, K2=12.83m, K3=28.48m, K4=12.83m, K5=27.32m, K6=12.83m, K7=28.48m, K8=12.83m] | area_source=public_site_area_text (0.50 acres) | method=public_doc_or_image_plus_site_area | planning_refs= | lot_refs= | title_refs= | doc_evidence=yes | NOT original/verified boundary; derived candidate geometry for display and review."},"OTM-18691204":{"listing_id":"OTM-18691204","confidence":"medium","previous_confidence":"medium_low","candidate_class":"candidate_medium_doc_area","area_m2":"173.914","computed_area_m2":"191.74","perimeter_m":"50.87","side_lengths_m_json":"[8.44, 4.307, 8.381, 4.307, 8.44, 4.307, 8.381, 4.307]","area_source":"public_site_area_text","area_raw":"1872 sq ft","method":"public_doc_or_image_plus_site_area","planning_refs":"","lot_refs":"MORE","title_refs":"","doc_evidence":"yes","note":"estimated_candidate_not_verified | confidence=medium | previous_confidence=medium_low | class=candidate_medium_doc_area | reason=public document/image evidence plus public area text | area=173.91 mÂ² | computed_polygon_area=191.74 mÂ² | perimeter=50.87 m | sides=[K1=8.44m, K2=4.31m, K3=8.38m, K4=4.31m, K5=8.44m, K6=4.31m, K7=8.38m, K8=4.31m] | area_source=public_site_area_text (1872 sq ft) | method=public_doc_or_image_plus_site_area | planning_refs= | lot_refs=MORE | title_refs= | doc_evidence=yes | NOT original/verified boundary; derived candidate geometry for display and review."}};

  function tyEsc(value) {
    return String(value ?? "")
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;");
  }

  function tyParseSides(raw) {
    if (!raw) return [];
    try {
      const v = JSON.parse(raw);
      return Array.isArray(v) ? v.map(Number).filter(Number.isFinite) : [];
    } catch (_) {
      return [];
    }
  }

  function tyFmtM(value) {
    const n = Number(value);
    return Number.isFinite(n) ? n.toLocaleString(undefined, { maximumFractionDigits: 2 }) + " m" : tyEsc(value);
  }

  function tyFmtM2(value) {
    const n = Number(value);
    return Number.isFinite(n) ? n.toLocaleString(undefined, { maximumFractionDigits: 2 }) + " mÃ‚Â²" : tyEsc(value);
  }

  function tyConfidenceLabel(conf) {
    if (conf === "medium") return "Medium";
    if (conf === "medium_low") return "Medium-Low";
    if (conf === "low_plus") return "Low+";
    if (conf === "low") return "Low";
    return tyEsc(conf || "unknown");
  }

  function tyFindIds(text) {
    const ids = new Set();
    String(text || "").replace(/OTM-\d+/g, function (m) {
      if (TY_CANDIDATE_METRICS_BY_ID[m]) ids.add(m);
      return m;
    });
    return Array.from(ids);
  }

  function tyCard(id) {
    const m = TY_CANDIDATE_METRICS_BY_ID[id];
    if (!m) return "";
    const sides = tyParseSides(m.side_lengths_m_json);
    const sideRows = sides.map((v, i) =>
      `<tr><td>K${i + 1}</td><td>${tyFmtM(v)}</td></tr>`
    ).join("");

    const refs = [
      m.planning_refs ? `Planning: ${tyEsc(m.planning_refs)}` : "",
      m.lot_refs ? `Lot: ${tyEsc(m.lot_refs)}` : "",
      m.title_refs ? `Title: ${tyEsc(m.title_refs)}` : ""
    ].filter(Boolean).join("<br>");

    const refBlock = refs ? `<div class="ty-candidate-metrics-refs">${refs}</div>` : "";

    return `
      <div class="ty-candidate-metrics-card" data-ty-candidate-metrics="${tyEsc(id)}">
        <div class="ty-candidate-metrics-title">SatÃ„Â±Ã…Å¸ Geometrisi Aday Plan Bilgisi</div>
        <div class="ty-candidate-metrics-badge">Durum: derived / estimated candidate Ã‚Â· GÃƒÂ¼ven: ${tyConfidenceLabel(m.confidence)}</div>
        <table class="ty-candidate-metrics-table">
          <tr><td>Alan</td><td>${tyFmtM2(m.area_m2)}</td></tr>
          <tr><td>Hesaplanan poligon alanÃ„Â±</td><td>${tyFmtM2(m.computed_area_m2)}</td></tr>
          <tr><td>Ãƒâ€¡evre</td><td>${tyFmtM(m.perimeter_m)}</td></tr>
          <tr><td>Alan kaynaÃ„Å¸Ã„Â±</td><td>${tyEsc(m.area_source)} ${m.area_raw ? "(" + tyEsc(m.area_raw) + ")" : ""}</td></tr>
          <tr><td>YÃƒÂ¶ntem</td><td>${tyEsc(m.method)}</td></tr>
          <tr><td>Belge/gÃƒÂ¶rsel kanÃ„Â±tÃ„Â±</td><td>${tyEsc(m.doc_evidence || "unknown")}</td></tr>
        </table>
        <div class="ty-candidate-metrics-subtitle">Kenar uzunluklarÃ„Â±</div>
        <table class="ty-candidate-metrics-table">${sideRows || "<tr><td colspan='2'>Kenar bilgisi yok</td></tr>"}</table>
        ${refBlock}
        <div class="ty-candidate-metrics-note">
          Bu geometri gerÃƒÂ§ek/original verified boundary deÃ„Å¸ildir. Alan, konum, kaynak sinyalleri ve oranlardan tÃƒÂ¼retilmiÃ…Å¸ satÃ„Â±Ã…Å¸ geometrisi adayÃ„Â±dÃ„Â±r.
        </div>
      </div>
    `;
  }

  function tyEnsureStyle() {
    if (document.getElementById("ty-candidate-metrics-style")) return;
    const s = document.createElement("style");
    s.id = "ty-candidate-metrics-style";
    s.textContent = `
      .ty-candidate-metrics-card {
        margin-top: 10px;
        padding: 10px;
        border: 1px solid #f59e0b;
        border-left: 4px solid #f59e0b;
        border-radius: 8px;
        background: #fff7ed;
        color: #1f2937;
        font-size: 12px;
        line-height: 1.35;
      }
      .ty-candidate-metrics-title {
        font-weight: 700;
        font-size: 13px;
        margin-bottom: 4px;
      }
      .ty-candidate-metrics-badge {
        font-size: 11px;
        color: #92400e;
        margin-bottom: 6px;
      }
      .ty-candidate-metrics-subtitle {
        font-weight: 700;
        margin-top: 8px;
        margin-bottom: 3px;
      }
      .ty-candidate-metrics-table {
        width: 100%;
        border-collapse: collapse;
        margin-top: 4px;
      }
      .ty-candidate-metrics-table td {
        border-bottom: 1px solid rgba(146,64,14,0.18);
        padding: 3px 4px;
        vertical-align: top;
      }
      .ty-candidate-metrics-table td:first-child {
        font-weight: 600;
        width: 42%;
      }
      .ty-candidate-metrics-refs {
        margin-top: 8px;
        padding-top: 6px;
        border-top: 1px dashed rgba(146,64,14,0.35);
      }
      .ty-candidate-metrics-note {
        margin-top: 8px;
        font-size: 11px;
        color: #7c2d12;
      }
    `;
    document.head.appendChild(s);
  }

  function tyEnhanceElement(el) {
    if (!el || !el.textContent) return;
    const ids = tyFindIds(el.textContent);
    if (!ids.length) return;
    tyEnsureStyle();
    ids.forEach((id) => {
      try {
        if (el.querySelector(`[data-ty-candidate-metrics="${CSS.escape(id)}"]`)) return;
      } catch (_) {
        if (el.innerHTML && el.innerHTML.includes(`data-ty-candidate-metrics="${id}"`)) return;
      }
      el.insertAdjacentHTML("beforeend", tyCard(id));
    });
  }

  function tyScan() {
    const selectors = [
      ".leaflet-popup-content",
      ".mapboxgl-popup-content",
      "[class*='popup']",
      "[class*='Popup']",
      "[class*='sidebar']",
      "[class*='Sidebar']",
      "[class*='panel']",
      "[class*='Panel']",
      "[class*='detail']",
      "[class*='Detail']",
      "[class*='parcel']",
      "[class*='Parcel']"
    ].join(",");
    document.querySelectorAll(selectors).forEach(tyEnhanceElement);
  }

  if (window.L && window.L.Popup && window.L.Popup.prototype && !window.L.Popup.prototype.__tyCandidateMetricsPatched) {
    const originalSetContent = window.L.Popup.prototype.setContent;
    window.L.Popup.prototype.setContent = function (content) {
      try {
        if (typeof content === "string") {
          const ids = tyFindIds(content);
          ids.forEach((id) => {
            if (!content.includes(`data-ty-candidate-metrics="${id}"`)) {
              content += tyCard(id);
            }
          });
        }
      } catch (_) {}
      return originalSetContent.call(this, content);
    };
    window.L.Popup.prototype.__tyCandidateMetricsPatched = true;
  }

  if (!window.__tyCandidateMetricsObserver) {
    window.__tyCandidateMetricsObserver = new MutationObserver(() => tyScan());
    window.__tyCandidateMetricsObserver.observe(document.documentElement, { childList: true, subtree: true });
  }

  document.addEventListener("DOMContentLoaded", tyScan);
  setTimeout(tyScan, 500);
  setTimeout(tyScan, 1500);
  setTimeout(tyScan, 3000);

  window.TY_CANDIDATE_METRICS_BY_ID = TY_CANDIDATE_METRICS_BY_ID;

/* TY_SALE_GEOMETRY_OVERLAY_PATCH_V3 */
(function () {
  const TY_SOURCE_ID = "ty-sale-geometry-overlay-source";
  const TY_FILL_ID = "ty-sale-geometry-overlay-fill";
  const TY_LINE_ID = "ty-sale-geometry-overlay-line";
  const TY_LABEL_ID = "ty-sale-geometry-overlay-label";
  const TY_STYLE_ID = "ty-sale-geometry-overlay-style";
  const ENABLE_TY_POPUP_AUGMENT = config.enablePopupSaleGeometryAugment === true;

  function tyEsc(value) {
    return String(value ?? "")
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;");
  }

  function tySafeJsonParse(value) {
    if (!value) return null;
    if (typeof value === "object") return value;
    try {
      return JSON.parse(value);
    } catch (_) {
      return null;
    }
  }

  function tySideList(raw) {
    if (!raw) return [];
    if (Array.isArray(raw)) return raw.map(Number).filter(Number.isFinite);
    try {
      const parsed = JSON.parse(raw);
      if (Array.isArray(parsed)) return parsed.map(Number).filter(Number.isFinite);
    } catch (_) {}
    return String(raw)
      .split(/[;,|]/)
      .map((v) => Number(String(v).trim()))
      .filter(Number.isFinite);
  }

  function tyFmtNum(value, digits = 2) {
    const n = Number(value);
    return Number.isFinite(n)
      ? n.toLocaleString(undefined, { maximumFractionDigits: digits })
      : null;
  }

  function tyFmtM(value) {
    const x = tyFmtNum(value, 2);
    return x ? `${x} m` : "-";
  }

  function tyFmtM2(value) {
    const x = tyFmtNum(value, 2);
    return x ? `${x} mÂ²` : "-";
  }

  function tyNormalizeGeometry(geom) {
    if (!geom || !geom.type || !geom.coordinates) return null;
    function roundDeep(val) {
      if (Array.isArray(val)) return val.map(roundDeep);
      const n = Number(val);
      return Number.isFinite(n) ? Number(n.toFixed(6)) : val;
    }
    return { type: geom.type, coordinates: roundDeep(geom.coordinates) };
  }

  function tySameGeometry(a, b) {
    const na = tyNormalizeGeometry(a);
    const nb = tyNormalizeGeometry(b);
    if (!na || !nb) return false;
    try {
      return JSON.stringify(na) === JSON.stringify(nb);
    } catch (_) {
      return false;
    }
  }

  function tyExtractGeometry(raw) {
    if (!raw) return null;

    let obj = raw;
    if (typeof obj === "string") {
      obj = tySafeJsonParse(obj);
      if (!obj) return null;
    }

    if (obj.type === "FeatureCollection" && Array.isArray(obj.features) && obj.features.length) {
      return tyExtractGeometry(obj.features[0]);
    }

    if (obj.type === "Feature" && obj.geometry) {
      return obj.geometry;
    }

    if ((obj.type === "Polygon" || obj.type === "MultiPolygon") && obj.coordinates) {
      return obj;
    }

    return null;
  }

  function tyIsVerifiedOriginalSaleGeometry(props) {
    const text = [
      props?.is_verified_original,
      props?.geometry_status,
      props?.verification_note,
      props?.source_level,
      props?.confidence_label,
      props?.generation_method,
      props?.source_polygon_original_site_status,
      props?.polygon_provenance_note,
      props?.display_polygon_source
    ]
      .map((v) => String(v || "").toLowerCase())
      .join(" ");

    if (
      text.includes("bbox") ||
      text.includes("rectangle") ||
      text.includes("rectangular") ||
      text.includes("feed_bbox") ||
      text.includes("candidate") ||
      text.includes("estimated") ||
      text.includes("derived") ||
      text.includes("centroid") ||
      text.includes("area_scaled") ||
      text.includes("feed polygon")
    ) {
      return false;
    }

    if (
      props?.is_verified_original === true ||
      props?.is_verified_original === "true" ||
      props?.is_verified_original === "yes"
    ) {
      return true;
    }

    return (
      text.includes("verified_original") ||
      text.includes("original_site") ||
      text.includes("verified boundary") ||
      text.includes("original boundary")
    );
  }

  function tyExtractSaleGeometryAndMeta(sourceObj) {
    const props = sourceObj?.properties || sourceObj || {};
    const verifiedCandidates = [
      props.verified_polygon_geojson,
      props.sale_verified_polygon_geojson,
      props.original_site_polygon_geojson,
      props.verified_original_polygon_geojson,
      props.original_boundary_geojson,
      props.verified_boundary_geojson
    ];

    const isVerifiedOriginal = tyIsVerifiedOriginalSaleGeometry(props);
    let geometry = null;
    if (isVerifiedOriginal) {
      for (const candidate of verifiedCandidates) {
        geometry = tyExtractGeometry(candidate);
        if (geometry) break;
      }
    }

    return {
      geometry,
      isVerifiedOriginal,
      confidence:
        props.confidence_tier ||
        props.confidence_level ||
        props.upgraded_confidence_level ||
        props.geometry_confidence_tier ||
        "-",
      area_m2:
        props.estimated_area_m2 ||
        props.polygon_area_m2_computed ||
        props.listing_area_m2 ||
        props.site_area_m2 ||
        props.area_m2 ||
        null,
      perimeter_m:
        props.perimeter_m ||
        props.polygon_perimeter_m ||
        null,
      side_lengths_m_json:
        props.side_lengths_m_json ||
        props.side_lengths_m ||
        null,
      note:
        props.verification_note ||
        props.polygon_provenance_note ||
        props.menu_display_note ||
        props.geometry_quality_label ||
        "-",
      source:
        props.source_name ||
        props.geometry_source ||
        props.display_polygon_source ||
        props.area_source ||
        "-"
    };
  }

  function tyGetCurrentSaleContext(feature) {
    const parcel = typeof getParcelModelFromFeature === "function" ? getParcelModelFromFeature(feature) : null;
    const parcelRef = parcel?.ref || feature?.properties?.parcel_ref || null;
    const state = parcelRef && typeof landIntelligenceCache !== "undefined"
      ? landIntelligenceCache.get(parcelRef)
      : null;

    let filteredView = null;
    if (state?.signals && typeof buildFilteredLandIntelligenceView === "function") {
      try {
        filteredView = buildFilteredLandIntelligenceView(state);
      } catch (_) {}
    }

    const candidateRecords = [
      feature,
      filteredView?.topActionableSaleRecord,
      filteredView?.topSaleRecord,
      filteredView?.topOfficialSaleRecord,
      ...(Array.isArray(filteredView?.filteredSaleRecords) ? filteredView.filteredSaleRecords : []),
      ...(Array.isArray(state?.signals?.sale_records) ? state.signals.sale_records : []),
      ...(Array.isArray(state?.parcelDetail?.source_summary?.active_sale_records) ? state.parcelDetail.source_summary.active_sale_records : [])
    ].filter(Boolean);

    let best = null;
    let fallback = null;
    for (const rec of candidateRecords) {
      const out = tyExtractSaleGeometryAndMeta(rec);
      if (out.geometry && out.isVerifiedOriginal) {
        best = out;
        break;
      }
      if (!fallback && (out.area_m2 || out.perimeter_m || out.side_lengths_m_json || out.note || out.source || out.confidence)) {
        fallback = out;
      }
    }
    if (!best) best = fallback;

    const brownfieldSources = Array.isArray(filteredView?.brownfieldSources)
      ? filteredView.brownfieldSources
      : [];

    const brownfieldText = brownfieldSources.length
      ? brownfieldSources.map((s) => s.source_name || s.label || s.source_record_id || "brownfield").join(", ")
      : "";

    return {
      parcel,
      parcelRef,
      state,
      filteredView,
      saleGeometry: best,
      brownfield: {
        present: brownfieldSources.length > 0,
        text: brownfieldText
      }
    };
  }

  function tyEnsureStyle() {
    if (document.getElementById(TY_STYLE_ID)) return;
    const style = document.createElement("style");
    style.id = TY_STYLE_ID;
    style.textContent = `
      .ty-sale-geometry-card {
        margin-top: 10px;
        padding: 10px;
        border: 1px solid #c2410c;
        border-left: 5px solid #9a3412;
        border-radius: 8px;
        background: #fff7ed;
        color: #1f2937;
        font-size: 12px;
        line-height: 1.4;
      }
      .ty-sale-geometry-card .title {
        font-weight: 700;
        font-size: 13px;
        margin-bottom: 4px;
      }
      .ty-sale-geometry-card .badge {
        display: inline-block;
        margin-right: 6px;
        margin-bottom: 6px;
        padding: 2px 8px;
        border-radius: 999px;
        background: #ffedd5;
        color: #9a3412;
        font-weight: 700;
        font-size: 11px;
      }
      .ty-sale-geometry-card .badge.brownfield {
        background: #ecfccb;
        color: #3f6212;
      }
      .ty-sale-geometry-card table {
        width: 100%;
        border-collapse: collapse;
        margin-top: 6px;
      }
      .ty-sale-geometry-card td {
        border-bottom: 1px solid rgba(154,52,18,0.18);
        padding: 4px;
        vertical-align: top;
      }
      .ty-sale-geometry-card td:first-child {
        font-weight: 600;
        width: 42%;
      }
      .ty-sale-geometry-card .note {
        margin-top: 8px;
        padding-top: 6px;
        border-top: 1px dashed rgba(154,52,18,0.35);
        color: #7c2d12;
      }
    `;
    document.head.appendChild(style);
  }

  function tyBuildInfoHtml(context, feature) {
    const meta = context?.saleGeometry;
    if (!meta) return "";

    const hasVerifiedGeometry = Boolean(meta?.geometry && meta?.isVerifiedOriginal);
    const different = hasVerifiedGeometry ? !tySameGeometry(feature?.geometry, meta.geometry) : false;
    const sideList = tySideList(meta.side_lengths_m_json);
    const sideRows = sideList.length
      ? sideList.map((v, idx) => `<tr><td>Kenar ${idx + 1}</td><td>${tyFmtM(v)}</td></tr>`).join("")
      : `<tr><td>Kenar bilgisi</td><td>-</td></tr>`;

    const diffText = hasVerifiedGeometry
      ? "Bu kayit verified/original satis boundary icerir; haritada koyu turuncu kalin cizgiyle gosterilir."
      : "Bu kayitta satis kaynagina dayali aday geometri / alan / cevre / kenar bilgisi vardir; ancak verified/original satis boundary yoktur. Bu nedenle gercek poligon olarak cizilmez.";

    return `
      <div class="ty-sale-geometry-card" data-ty-sale-geometry-card="1">
        <div class="title">SatÄ±ÅŸ Geometrisi</div>
        <div class="badge">GÃ¼ven: ${tyEsc(meta.confidence || "-")}</div>
        <div class="badge">Kaynak: ${tyEsc(meta.source || "-")}</div>
        ${context?.brownfield?.present ? `<div class="badge brownfield">Brownfield: Var</div>` : `<div class="badge brownfield">Brownfield: Yok</div>`}
        <table>
          <tr><td>Alan</td><td>${tyFmtM2(meta.area_m2)}</td></tr>
          <tr><td>Ã‡evre</td><td>${tyFmtM(meta.perimeter_m)}</td></tr>
          ${sideRows}
        </table>
        <div class="note">
          <div><strong>Brownfield kaynaklarÄ±:</strong> ${tyEsc(context?.brownfield?.text || "-")}</div>
          <div><strong>Durum:</strong> ${tyEsc(diffText)}</div>
          <div><strong>Not:</strong> ${tyEsc(meta.note || "-")}</div>
          <div><strong>Overlay:</strong> ${hasVerifiedGeometry ? "verified_original_polygon" : "hidden_candidate_geometry"}</div>
        </div>
      </div>
    `;
  }

  function tyEnsureOverlayLayers() {
    if (!map || !map.getStyle || !map.getStyle()) return;
    if (!map.getSource(TY_SOURCE_ID)) {
      map.addSource(TY_SOURCE_ID, {
        type: "geojson",
        data: { type: "FeatureCollection", features: [] }
      });
    }

    if (!map.getLayer(TY_FILL_ID)) {
      map.addLayer({
        id: TY_FILL_ID,
        type: "fill",
        source: TY_SOURCE_ID,
        paint: {
          "fill-color": "#c2410c",
          "fill-opacity": 0.18
        }
      });
    }

    if (!map.getLayer(TY_LINE_ID)) {
      map.addLayer({
        id: TY_LINE_ID,
        type: "line",
        source: TY_SOURCE_ID,
        paint: {
          "line-color": "#9a3412",
          "line-width": 4.5,
          "line-opacity": 0.95
        }
      });
    }

    if (!map.getLayer(TY_LABEL_ID)) {
      map.addLayer({
        id: TY_LABEL_ID,
        type: "symbol",
        source: TY_SOURCE_ID,
        layout: {
          "text-field": ["coalesce", ["get", "label"], "SatÄ±ÅŸ"],
          "text-size": 12,
          "text-offset": [0, 0]
        },
        paint: {
          "text-color": "#7c2d12"
        }
      });
    }
  }

  function tySetOverlayFeature(feature) {
    if (!map || !map.getSource) return;
    tyEnsureOverlayLayers();

    const source = map.getSource(TY_SOURCE_ID);
    if (!source || !source.setData) return;

    if (!feature) {
      source.setData({ type: "FeatureCollection", features: [] });
      return;
    }

    const ctx = tyGetCurrentSaleContext(feature);
    const meta = ctx?.saleGeometry;
    if (!meta?.geometry || !meta?.isVerifiedOriginal) {
      source.setData({ type: "FeatureCollection", features: [] });
      return;
    }

    const different = !tySameGeometry(feature?.geometry, meta.geometry);
    if (!different) {
      source.setData({ type: "FeatureCollection", features: [] });
      return;
    }

    source.setData({
      type: "FeatureCollection",
      features: [
        {
          type: "Feature",
          geometry: meta.geometry,
          properties: {
            label: `SatÄ±ÅŸ ${meta.confidence || ""}`.trim()
          }
        }
      ]
    });
  }

  function tyAugmentPopup(container, feature) {
    if (!container || !feature) return;
    tyEnsureStyle();

    const ctx = tyGetCurrentSaleContext(feature);
    const html = tyBuildInfoHtml(ctx, feature);
    if (!html) return;

    const existing = container.querySelector('[data-ty-sale-geometry-card="1"]');
    if (existing) existing.remove();

    container.insertAdjacentHTML("beforeend", html);
  }

  function tyInjectWorkspaceCard() {
    if (!selectedParcelFeature) return;
    tyEnsureStyle();

    const candidates = [
      document.querySelector(".workspace-panel .workspace-stack"),
      document.querySelector(".workspace-stack"),
      document.querySelector(".workspace-panel"),
      document.querySelector("#workspacePanel"),
      document.querySelector("#selectedParcel")?.parentElement
    ].filter(Boolean);

    const target = candidates[0];
    if (!target) return;

    const ctx = tyGetCurrentSaleContext(selectedParcelFeature);
    const html = tyBuildInfoHtml(ctx, selectedParcelFeature);
    if (!html) return;

    const old = target.querySelector('[data-ty-sale-geometry-card="1"]');
    if (old) old.remove();

    const wrap = document.createElement("div");
    wrap.innerHTML = html;
    target.appendChild(wrap.firstElementChild);
  }

  const __tyOriginalBuildParcelPopupContent = buildParcelPopupContent;
  buildParcelPopupContent = function (feature, lngLat) {
    const container = __tyOriginalBuildParcelPopupContent(feature, lngLat);
    if (!ENABLE_TY_POPUP_AUGMENT) {
      return container;
    }
    try {
      tyAugmentPopup(container, feature);
    } catch (err) {
      console.warn("TY popup augment error", err);
    }
    return container;
  };

  const __tyOriginalUpdateSelectedParcel = updateSelectedParcel;
  updateSelectedParcel = function (feature) {
    const result = __tyOriginalUpdateSelectedParcel(feature);
    try {
      setTimeout(() => {
        tySetOverlayFeature(feature || null);
        tyInjectWorkspaceCard();
      }, 0);
    } catch (err) {
      console.warn("TY selected parcel patch error", err);
    }
    return result;
  };

  const __tyOriginalRenderWorkspace = renderWorkspace;
  renderWorkspace = function () {
    const result = __tyOriginalRenderWorkspace.apply(this, arguments);
    try {
      setTimeout(() => {
        tyInjectWorkspaceCard();
        tySetOverlayFeature(selectedParcelFeature || null);
      }, 0);
    } catch (err) {
      console.warn("TY workspace patch error", err);
    }
    return result;
  };

  if (map && map.on) {
    map.on("load", function () {
      try {
        tyEnsureOverlayLayers();
        tySetOverlayFeature(selectedParcelFeature || null);
      } catch (err) {
        console.warn("TY map load patch error", err);
      }
    });
  }

  setTimeout(() => {
    try {
      tyEnsureOverlayLayers();
      tySetOverlayFeature(selectedParcelFeature || null);
      tyInjectWorkspaceCard();
    } catch (err) {
      console.warn("TY initial patch error", err);
    }
  }, 500);
})();
/* TY_SALE_GEOMETRY_OVERLAY_PATCH_V3_END */
})();
/* TY_CANDIDATE_METRICS_PATCH_END */


// AAYS sales-history layer convention: sales_history_available=true should render dark orange fill and thick orange/brown stroke in sales-history mode.
