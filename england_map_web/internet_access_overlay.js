(function () {
  "use strict";

  const SOURCE_ID = "aays-internet-access-source";
  const FILL_LAYER_ID = "aays-internet-access-fill";
  const LINE_LAYER_ID = "aays-internet-access-line";
  const POINT_LAYER_ID = "aays-internet-access-point";
  const DEFAULT_ENDPOINT = "/map/internet-access";
  const DEFAULT_DATA_URL = "./data/program_layer_matrix/internet.geojson";
  const SCORE_COLOR_STOPS = [
    [0, "#7f1d1d"],
    [2, "#dc2626"],
    [4, "#f59e0b"],
    [6, "#84cc16"],
    [8, "#22c55e"],
    [10, "#065f46"],
  ];

  let internetMap = null;
  let internetVisible = false;
  let internetLoaded = false;
  let internetFeatureCount = 0;
  let internetLastError = null;
  let popup = null;
  let styleHookBound = false;

  function isMapLike(value) {
    return value
      && typeof value.addSource === "function"
      && typeof value.addLayer === "function"
      && typeof value.getSource === "function"
      && typeof value.getLayer === "function"
      && typeof value.setLayoutProperty === "function";
  }

  function findMap() {
    const candidates = [
      window.__aaysActiveMap,
      window.__aaysGLMap,
      window.map,
      window.aaysMap,
      window.__AAYS_MAP__,
    ];
    for (const candidate of candidates) {
      if (isMapLike(candidate)) return candidate;
    }
    for (const key of Object.keys(window)) {
      try {
        if (isMapLike(window[key])) return window[key];
      } catch (_error) {
        // no-op
      }
    }
    return null;
  }

  function normalizeApiBase(url) {
    return String(url || "").trim().replace(/\/+$/, "");
  }

  function getConfig() {
    const raw = window.AAYS_INTERNET_CONFIG || {};
    return {
      apiBaseUrl: normalizeApiBase(raw.apiBaseUrl || raw.landIntelligenceApiBaseUrl),
      layerEndpoint: String(raw.layerEndpoint || DEFAULT_ENDPOINT),
      fallbackDataUrl: String(raw.fallbackDataUrl || DEFAULT_DATA_URL),
      allowSalesHistoryProxyFallback: raw.allowSalesHistoryProxyFallback === true,
      proxyEndpoint: String(raw.proxyEndpoint || ""),
    };
  }

  function resolveLayerEndpointUrl() {
    const cfg = getConfig();
    const endpoint = cfg.layerEndpoint || DEFAULT_ENDPOINT;
    if (/^https?:\/\//i.test(endpoint)) return endpoint;
    if (endpoint.startsWith("/")) {
      if (cfg.apiBaseUrl) return `${cfg.apiBaseUrl}${endpoint}`;
      return `${window.location.origin}${endpoint}`;
    }
    return new URL(endpoint, window.location.href).toString();
  }

  function resolveApiUrl(pathOrUrl) {
    const value = String(pathOrUrl || "").trim();
    if (!value) return "";
    if (/^https?:\/\//i.test(value)) return value;
    const cfg = getConfig();
    if (value.startsWith("/")) {
      if (cfg.apiBaseUrl) return `${cfg.apiBaseUrl}${value}`;
      return `${window.location.origin}${value}`;
    }
    return new URL(value, window.location.href).toString();
  }

  function toFiniteNumber(value, fallback = null) {
    const numeric = Number(value);
    return Number.isFinite(numeric) ? numeric : fallback;
  }

  function clampNumber(value, minValue, maxValue) {
    return Math.min(maxValue, Math.max(minValue, value));
  }

  function buildMapQueryBbox(map) {
    try {
      const bounds = map && typeof map.getBounds === "function" ? map.getBounds() : null;
      if (!bounds) return null;
      const west = toFiniteNumber(bounds.getWest ? bounds.getWest() : bounds._sw?.lng, null);
      const south = toFiniteNumber(bounds.getSouth ? bounds.getSouth() : bounds._sw?.lat, null);
      const east = toFiniteNumber(bounds.getEast ? bounds.getEast() : bounds._ne?.lng, null);
      const north = toFiniteNumber(bounds.getNorth ? bounds.getNorth() : bounds._ne?.lat, null);
      if (![west, south, east, north].every(Number.isFinite)) return null;
      return `${west.toFixed(6)},${south.toFixed(6)},${east.toFixed(6)},${north.toFixed(6)}`;
    } catch (_error) {
      return null;
    }
  }

  function hasRenderableGeometry(featureCollection) {
    const features = Array.isArray(featureCollection?.features) ? featureCollection.features : [];
    return features.some((feature) => feature && feature.geometry && typeof feature.geometry.type === "string");
  }

  function getScoreColorExpression() {
    return [
      "interpolate",
      ["linear"],
      ["to-number", ["coalesce", ["get", "display_band_score_10"], ["get", "internet_access_score_10"], 0]],
      SCORE_COLOR_STOPS[0][0], SCORE_COLOR_STOPS[0][1],
      SCORE_COLOR_STOPS[1][0], SCORE_COLOR_STOPS[1][1],
      SCORE_COLOR_STOPS[2][0], SCORE_COLOR_STOPS[2][1],
      SCORE_COLOR_STOPS[3][0], SCORE_COLOR_STOPS[3][1],
      SCORE_COLOR_STOPS[4][0], SCORE_COLOR_STOPS[4][1],
      SCORE_COLOR_STOPS[5][0], SCORE_COLOR_STOPS[5][1],
    ];
  }

  function scoreToLevel(value) {
    const score = Number(value);
    if (!Number.isFinite(score)) return "-";
    if (score >= 8) return "Cok iyi";
    if (score >= 6) return "Iyi";
    if (score >= 4) return "Orta";
    if (score >= 2) return "Dusuk";
    return "Cok dusuk";
  }

  function popupRow(label, value) {
    const safeValue = value === undefined || value === null || value === "" ? "-" : String(value);
    return `<div class="aays-internet-popup-row"><b>${label}:</b> ${safeValue}</div>`;
  }

  function setLayerVisibility(map, visibility) {
    [FILL_LAYER_ID, LINE_LAYER_ID, POINT_LAYER_ID].forEach((layerId) => {
      if (map.getLayer(layerId)) {
        map.setLayoutProperty(layerId, "visibility", visibility);
      }
    });
  }

  function attachPopup(map, layerId) {
    if (!map.getLayer(layerId)) return;
    map.__aaysInternetPopupLayers = map.__aaysInternetPopupLayers || {};
    if (map.__aaysInternetPopupLayers[layerId]) return;
    map.__aaysInternetPopupLayers[layerId] = true;
    map.on("click", layerId, (event) => {
      const feature = event.features && event.features[0];
      if (!feature) return;
      const props = feature.properties || {};
      const score = Number(props.internet_access_score_10);
      const level = props.internet_access_level_5 || scoreToLevel(score);
      const html = [
        '<div class="aays-internet-popup">',
        '<div class="aays-internet-popup-title">Internet Erisim Bilgisi</div>',
        popupRow("Parcel ID", props.parcel_id),
        popupRow("Parcel Ref", props.parcel_ref),
        popupRow("Gosterim bandi (olculmus hiz degil)", props.display_band_score_10),
        popupRow("Gigabit kapsami %", props.gigabit_coverage_pct),
        popupRow("UFBB 100 Mbps kapsami %", props.ufbb100_coverage_pct),
        popupRow("SFBB kapsami %", props.sfbb_coverage_pct),
        popupRow("30 Mbps alamayan %", props.unable30_pct),
        popupRow("Seviye", level),
        popupRow("Kaynak Modu", props.internet_layer_mode || "internet_access_score_10"),
        popupRow("Olcum seviyesi", props.measurement_level),
        popupRow("Kalite durumu", props.quality_status),
        popupRow("Confidence", props.confidence_level_4),
        popupRow("Confidence %", props.confidence_score_pct),
        popupRow("Faktor", props.factor_name),
        popupRow("Kaynak", props.source_name),
        popupRow("Kaynak URL", props.source_url),
        popupRow("Son dogrulama", props.last_verified_at),
        "</div>",
      ].join("");
      const Popup = window.maplibregl && window.maplibregl.Popup;
      if (!Popup) return;
      if (popup) popup.remove();
      popup = new Popup({ closeButton: true, closeOnClick: true })
        .setLngLat(event.lngLat)
        .setHTML(html)
        .addTo(map);
    });
    map.on("mouseenter", layerId, () => {
      try { map.getCanvas().style.cursor = "pointer"; } catch (_error) {}
    });
    map.on("mouseleave", layerId, () => {
      try { map.getCanvas().style.cursor = ""; } catch (_error) {}
    });
  }

  function normalizeProxyScore(rawValue) {
    const raw = toFiniteNumber(rawValue, null);
    if (!Number.isFinite(raw)) return { score10: 5, scorePct: 50 };
    const score10 = raw > 10 ? clampNumber(raw / 10, 0, 10) : clampNumber(raw, 0, 10);
    return { score10, scorePct: clampNumber(score10 * 10, 0, 100) };
  }

  function confidenceBand(scorePct) {
    if (scorePct >= 80) return "high";
    if (scorePct >= 60) return "medium";
    if (scorePct >= 40) return "low";
    return "very_low";
  }

  function parseCoverageValue(text, key) {
    const match = String(text || "").match(new RegExp(`${key}=([0-9.]+)%`, "i"));
    return match ? toFiniteNumber(match[1], null) : null;
  }

  function buildInternetMatrixFeature(sourceFeature) {
    if (!sourceFeature || sourceFeature.type !== "Feature" || !sourceFeature.geometry) return null;
    const props = sourceFeature.properties || {};
    const raw = String(props.internet_level_value || props.internet_level || "");
    if (!raw) return null;
    const level = raw.split(";")[0].trim() || "NO_DATA";
    const levelKey = level.toLowerCase();
    const bandScore = levelKey.includes("very high") ? 9
      : levelKey.includes("high") ? 7
        : levelKey.includes("medium") ? 5
          : levelKey.includes("low") ? 3
            : null;
    return {
      type: "Feature",
      geometry: sourceFeature.geometry,
      properties: {
        parcel_id: props.parcel_id ?? null,
        parcel_ref: props.hmlr_inspire_id ?? props.hmlr_row_id ?? null,
        postcode: (raw.match(/postcode=([^;]+)/i) || [])[1] || null,
        internet_access_level_5: level,
        display_band_score_10: bandScore,
        gigabit_coverage_pct: parseCoverageValue(raw, "gigabit"),
        ufbb100_coverage_pct: parseCoverageValue(raw, "ufbb100"),
        sfbb_coverage_pct: parseCoverageValue(raw, "sfbb"),
        unable30_pct: parseCoverageValue(raw, "unable30"),
        confidence_level_4: props.internet_level_accuracy || "2/4",
        confidence_score_pct: null,
        confidence_reason: "postcode_coverage_proxy_joined_to_london_parcel_centroid",
        factor_name: "ofcom_postcode_coverage_context",
        source_name: "Ofcom Connected Nations postcode coverage context",
        source_url: null,
        last_verified_at: null,
        measurement_level: "postcode",
        quality_status: "POSTCODE_COVERAGE_PROXY_NOT_MEASURED_PARCEL_SPEED",
        internet_layer_mode: "postcode_coverage_proxy",
      },
    };
  }

  function buildInternetProxyFeature(sourceFeature) {
    if (!sourceFeature || sourceFeature.type !== "Feature" || !sourceFeature.geometry) return null;
    const props = sourceFeature.properties || {};
    const reliabilityRaw =
      props.reliability_score
      ?? props.sales_history_confidence_score
      ?? props.correctness_likelihood_pct
      ?? null;
    const normalized = normalizeProxyScore(reliabilityRaw);
    const level = scoreToLevel(normalized.score10);
    return {
      type: "Feature",
      geometry: sourceFeature.geometry,
      properties: {
        parcel_id: props.parcel_id ?? null,
        parcel_ref: props.parcel_ref ?? null,
        inspire_id: props.inspire_id ?? null,
        local_authority: props.local_authority ?? null,
        postcode: props.postcode ?? null,
        address_text: props.address_text ?? null,
        area_m2: props.parcel_area_m2 ?? props.area_m2 ?? null,
        internet_access_score_10: Number(normalized.score10.toFixed(2)),
        internet_access_pct: Number(normalized.scorePct.toFixed(1)),
        internet_access_level_5: level,
        confidence_level_4: confidenceBand(normalized.scorePct),
        confidence_score_pct: Number(normalized.scorePct.toFixed(1)),
        confidence_reason: "internet_access_source_missing__proxy_from_sales_history_reliability",
        factor_name: "sales_history_reliability_proxy",
        factor_level: level,
        raw_value: toFiniteNumber(reliabilityRaw, null),
        normalized_0_100: Number(normalized.scorePct.toFixed(1)),
        weight: null,
        contribution: null,
        source_name: "sales_history_proxy",
        source_url: DEFAULT_PROXY_ENDPOINT,
        source_date: props.latest_sale_date ?? null,
        last_verified_at: props.latest_sale_date ?? null,
        evidence_ref: props.evidence_manifest_id ?? null,
        calculation_version: "internet_proxy_v1",
        layer_kind: "internet_access_proxy",
        internet_layer_mode: "sales_history_proxy",
      },
    };
  }

  async function fetchProxyFromSalesHistory(map) {
    const cfg = getConfig();
    if (!cfg.allowSalesHistoryProxyFallback) {
      return { ok: false, reason: "proxy_disabled" };
    }
    const baseUrl = resolveApiUrl(cfg.proxyEndpoint);
    if (!baseUrl) return { ok: false, reason: "proxy_endpoint_missing" };
    const url = new URL(baseUrl);
    const bbox = buildMapQueryBbox(map);
    if (bbox) {
      url.searchParams.set("bbox", bbox);
    } else {
      url.searchParams.set("bbox", "-8.650,49.800,2.100,61.150");
    }
    const zoom = map && typeof map.getZoom === "function" ? map.getZoom() : 8;
    url.searchParams.set("zoom", Number.isFinite(Number(zoom)) ? Number(zoom).toFixed(2) : "8.00");
    url.searchParams.set("limit", "5000");
    try {
      const response = await fetch(url.toString());
      if (!response.ok) {
        return { ok: false, reason: `proxy_http_${response.status}` };
      }
      const payload = await response.json();
      const features = Array.isArray(payload?.features) ? payload.features : [];
      if (!features.length) {
        return { ok: false, reason: "proxy_empty_feature_collection" };
      }
      const mapped = features.map(buildInternetProxyFeature).filter(Boolean);
      if (!mapped.length) {
        return { ok: false, reason: "proxy_mapping_empty" };
      }
      return {
        ok: true,
        payload: { type: "FeatureCollection", features: mapped },
        mode: "sales_history_proxy",
      };
    } catch (error) {
      return { ok: false, reason: `proxy_exception:${error?.message || "unknown"}` };
    }
  }

  async function fetchData(map) {
    const errors = [];
    const endpointUrl = resolveLayerEndpointUrl();
    try {
      const response = await fetch(endpointUrl);
      if (response.ok) {
        const payload = await response.json();
        if (payload && payload.type === "FeatureCollection" && Array.isArray(payload.features)) {
          if (payload.features.length > 0 && hasRenderableGeometry(payload)) {
            return { ok: true, payload, mode: "api" };
          }
          errors.push(payload.features.length > 0 ? "api_no_renderable_geometry" : "api_empty_feature_collection");
        } else {
          errors.push("api_invalid_payload");
        }
      } else {
        errors.push(`api_http_${response.status}`);
      }
    } catch (error) {
      errors.push(`api_exception:${error?.message || "unknown"}`);
    }

    const cfg = getConfig();
    if (cfg.fallbackDataUrl) {
      try {
        const fallbackResponse = await fetch(cfg.fallbackDataUrl);
        if (fallbackResponse.ok) {
          const payload = await fallbackResponse.json();
          if (payload && payload.type === "FeatureCollection" && Array.isArray(payload.features)) {
            if (payload.features.length > 0 && hasRenderableGeometry(payload)) {
              const mapped = payload.features.map(buildInternetMatrixFeature).filter(Boolean);
              if (mapped.length) {
                return {
                  ok: true,
                  payload: { type: "FeatureCollection", features: mapped },
                  mode: "postcode_coverage_proxy",
                };
              }
              errors.push("fallback_rows_missing_explicit_internet_values");
            }
            errors.push(payload.features.length > 0 ? "fallback_no_renderable_geometry" : "fallback_empty_feature_collection");
          } else {
            errors.push("fallback_invalid_payload");
          }
        } else {
          errors.push(`fallback_http_${fallbackResponse.status}`);
        }
      } catch (error) {
        errors.push(`fallback_exception:${error?.message || "unknown"}`);
      }
    } else {
      errors.push("fallback_data_url_missing");
    }

    const proxyResult = await fetchProxyFromSalesHistory(map);
    if (proxyResult.ok) {
      return proxyResult;
    }
    if (proxyResult.reason && proxyResult.reason !== "proxy_disabled") {
      errors.push(proxyResult.reason);
    }
    return { ok: false, reason: errors.join(";") };
  }

  function bindStyleReloadHook(map) {
    if (styleHookBound || !map || typeof map.on !== "function") return;
    styleHookBound = true;
    map.on("style.load", () => {
      internetLoaded = false;
      if (internetVisible) {
        void activateInternet();
      }
    });
  }

  function ensureLayersOnMap(map, featureCollection) {
    if (!map || !map.isStyleLoaded || !map.isStyleLoaded()) return false;

    const source = map.getSource(SOURCE_ID);
    if (!source) {
      map.addSource(SOURCE_ID, {
        type: "geojson",
        data: featureCollection,
        promoteId: "parcel_id",
      });
    } else {
      source.setData(featureCollection);
    }

    if (!map.getLayer(FILL_LAYER_ID)) {
      map.addLayer({
        id: FILL_LAYER_ID,
        type: "fill",
        source: SOURCE_ID,
        filter: ["any", ["==", ["geometry-type"], "Polygon"], ["==", ["geometry-type"], "MultiPolygon"]],
        paint: {
          "fill-color": getScoreColorExpression(),
          "fill-opacity": 0.45,
        },
        layout: { visibility: "none" },
      });
    }
    if (!map.getLayer(LINE_LAYER_ID)) {
      map.addLayer({
        id: LINE_LAYER_ID,
        type: "line",
        source: SOURCE_ID,
        filter: ["any", ["==", ["geometry-type"], "Polygon"], ["==", ["geometry-type"], "MultiPolygon"]],
        paint: {
          "line-color": "#111827",
          "line-width": 0.8,
          "line-opacity": 0.5,
        },
        layout: { visibility: "none" },
      });
    }
    if (!map.getLayer(POINT_LAYER_ID)) {
      map.addLayer({
        id: POINT_LAYER_ID,
        type: "circle",
        source: SOURCE_ID,
        filter: ["==", ["geometry-type"], "Point"],
        paint: {
          "circle-color": getScoreColorExpression(),
          "circle-radius": ["interpolate", ["linear"], ["zoom"], 5, 2, 10, 4, 14, 6],
          "circle-opacity": 0.85,
          "circle-stroke-color": "#111827",
          "circle-stroke-width": 0.65,
        },
        layout: { visibility: "none" },
      });
    }
    attachPopup(map, FILL_LAYER_ID);
    attachPopup(map, POINT_LAYER_ID);
    return true;
  }

  async function activateInternet() {
    internetMap = internetMap || findMap();
    if (!internetMap) {
      internetLastError = "map_not_found";
      internetVisible = false;
      return false;
    }
    bindStyleReloadHook(internetMap);

    if (!internetMap.isStyleLoaded || !internetMap.isStyleLoaded()) {
      internetLastError = "style_not_loaded";
      internetVisible = false;
      return false;
    }

    const dataResult = await fetchData(internetMap);
    if (!dataResult.ok) {
      internetLastError = dataResult.reason || "data_fetch_failed";
      internetFeatureCount = 0;
      internetVisible = false;
      return false;
    }

    const featureCollection = dataResult.payload;
    internetFeatureCount = Array.isArray(featureCollection.features) ? featureCollection.features.length : 0;
    internetLastError = null;

    const layerReady = ensureLayersOnMap(internetMap, featureCollection);
    if (!layerReady) {
      internetLastError = "layer_not_ready";
      internetVisible = false;
      return false;
    }

    internetLoaded = true;
    internetVisible = true;
    setLayerVisibility(internetMap, "visible");
    return true;
  }

  function deactivateInternet() {
    internetVisible = false;
    if (internetMap) {
      setLayerVisibility(internetMap, "none");
    }
    if (popup) {
      popup.remove();
      popup = null;
    }
    return true;
  }

  async function toggleInternet() {
    if (internetVisible) {
      return deactivateInternet();
    }
    return activateInternet();
  }

  function getState() {
    return {
      loaded: internetLoaded,
      active: internetVisible,
      featureCount: internetFeatureCount,
      lastError: internetLastError,
    };
  }

  function boot() {
    let attempts = 0;
    const timer = setInterval(() => {
      attempts += 1;
      if (!internetMap) {
        internetMap = findMap();
      }
      if (internetMap) {
        bindStyleReloadHook(internetMap);
        clearInterval(timer);
      } else if (attempts > 120) {
        clearInterval(timer);
      }
    }, 500);
  }

  window.AAYS_INTERNET = {
    activate: activateInternet,
    deactivate: deactivateInternet,
    toggle: toggleInternet,
    isActive: () => internetVisible,
    refresh: activateInternet,
    getState,
  };

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", boot);
  } else {
    boot();
  }
})();
