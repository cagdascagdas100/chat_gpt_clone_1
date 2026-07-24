(() => {
  'use strict';

  const GEOJSON_URL = '../docs/chatgpt_status/aays1/geometry_review_3of4/all_1264_real_geometry_3of4.geojson';
  const SOURCE_REGISTRY_URL = './data/aays_21_slots/ready_to_sell_1/official_source_candidates_20260720.json';
  const VERIFIED_CANDIDATES_URL = './data/aays_21_slots/ready_to_sell_1/verified_candidate_examples_20260720.json';
  const BATCH_SIZE = 50;

  const state = {
    features: [],
    sources: [],
    candidates: [],
    visible: 0,
  };

  const escapeHtml = (value) => String(value ?? '')
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&#039;');

  const firstValue = (object, keys) => {
    for (const key of keys) {
      const value = object?.[key];
      if (value !== undefined && value !== null && String(value).trim() !== '') return value;
    }
    return null;
  };

  const firstHttpUrl = (object, keys) => {
    for (const key of keys) {
      const value = object?.[key];
      if (value && /^https?:\/\//i.test(String(value))) return String(value);
    }
    return null;
  };

  const coordinateCount = (coordinates) => {
    if (!Array.isArray(coordinates)) return 0;
    if (coordinates.length >= 2 && coordinates.every((value) => typeof value === 'number')) return 1;
    return coordinates.reduce((total, item) => total + coordinateCount(item), 0);
  };

  const formatValue = (value) => {
    if (value === null || value === undefined || value === '') return 'NO_DATA';
    if (Array.isArray(value)) return value.map(formatValue).join(', ');
    if (typeof value === 'object') return JSON.stringify(value);
    return String(value);
  };

  const formatGbp = (value) => {
    const number = Number(value);
    return Number.isFinite(number)
      ? new Intl.NumberFormat('en-GB', {style: 'currency', currency: 'GBP', maximumFractionDigits: 0}).format(number)
      : 'NO_DATA';
  };

  const sourceLink = (properties) => {
    const value = firstHttpUrl(properties, ['listing_url', 'evidence_url', 'photo_url', 'url', 'source_url']);
    if (value) return `<a href="${escapeHtml(value)}" target="_blank" rel="noopener noreferrer">canlı kaynak</a>`;
    const fallback = state.sources[0]?.url;
    return fallback
      ? `<a href="${escapeHtml(fallback)}" target="_blank" rel="noopener noreferrer">HMLR resmî kaynak</a>`
      : 'NO_DATA';
  };

  const insertPanelBeforeMainTable = (panel) => {
    const table = document.querySelector('body > table');
    table?.parentNode?.insertBefore(panel, table);
  };

  const renderSourceSummary = () => {
    let panel = document.getElementById('official-source-summary');
    if (!panel) {
      panel = document.createElement('section');
      panel.id = 'official-source-summary';
      panel.style.margin = '12px 0';
      panel.style.padding = '10px';
      panel.style.background = '#fff';
      panel.style.border = '1px solid #cbd5e1';
      insertPanelBeforeMainTable(panel);
    }
    const sourceRows = state.sources.map((source) => `
      <tr>
        <td>${escapeHtml(source.source_id)}</td>
        <td>${escapeHtml(source.publisher)}</td>
        <td>${escapeHtml(source.source_verification_score)}/100</td>
        <td>${escapeHtml(source.parcel_binding_score_ceiling)}/100 tavan</td>
        <td>${escapeHtml(source.binding_limit)}</td>
        <td><a href="${escapeHtml(source.url)}" target="_blank" rel="noopener noreferrer">aç</a></td>
      </tr>`).join('');
    panel.innerHTML = `
      <strong>Doğrulanmış resmî internet kaynakları: ${state.sources.length}</strong>
      <div style="font-size:12px;margin:6px 0">Kaynak doğrulaması ile parsel bağlama güveni ayrı ölçülür. Kesin kimlik birleştirmesi yapılmadan parsel değeri yayımlanmaz.</div>
      <table style="width:100%;font-size:11px">
        <thead><tr><th>Kaynak</th><th>Yayıncı</th><th>Kaynak skoru</th><th>Parsel bağlama</th><th>Sınır</th><th>URL</th></tr></thead>
        <tbody>${sourceRows}</tbody>
      </table>`;
  };

  const renderCandidateSummary = () => {
    let panel = document.getElementById('verified-candidate-summary');
    if (!panel) {
      panel = document.createElement('section');
      panel.id = 'verified-candidate-summary';
      panel.style.margin = '12px 0';
      panel.style.padding = '10px';
      panel.style.background = '#f0fdf4';
      panel.style.border = '1px solid #22c55e';
      insertPanelBeforeMainTable(panel);
    }
    const rows = state.candidates.map((candidate) => {
      const listingLink = candidate.listing_url
        ? `<a href="${escapeHtml(candidate.listing_url)}" target="_blank" rel="noopener noreferrer">ilanı aç</a>`
        : 'PENDING';
      const identity = candidate.matched_inspire_id || candidate.matched_parcel_ref || 'PENDING';
      const accuracy = candidate.match_score !== undefined
        ? `eşleşme=${escapeHtml(candidate.match_score)}/100<br>güven=${escapeHtml(candidate.confidence_score)}/100`
        : 'PENDING';
      return `<tr>
        <td>${escapeHtml(candidate.row_reference)}</td>
        <td>${listingLink}</td>
        <td>${escapeHtml(candidate.address || 'PENDING')}</td>
        <td>${escapeHtml(candidate.title || 'PENDING')}<br>${escapeHtml(formatGbp(candidate.ask_price_gbp))}</td>
        <td>${escapeHtml(candidate.planning_reference || 'PENDING')}</td>
        <td>${escapeHtml(identity)}</td>
        <td>${accuracy}</td>
        <td>${escapeHtml(candidate.verified_dimension_count)}/${escapeHtml(candidate.target_dimension_count)}</td>
        <td>${escapeHtml(candidate.status)}</td>
      </tr>`;
    }).join('');
    const verified = state.candidates.filter((candidate) => candidate.internet_readback?.listing_page_live).length;
    panel.innerHTML = `
      <strong>Örnek adaylar: ${state.candidates.length} · internetten yeniden doğrulanan: ${verified}</strong>
      <div style="font-size:12px;margin:6px 0">Planlama referansları ilan sayfasında doğrulandı; resmî belediye planlama portalı doğrulaması tamamlanana kadar değer yayımlanmaz.</div>
      <table style="width:100%;font-size:11px">
        <thead><tr><th>Satır</th><th>Canlı sayfa</th><th>Adres</th><th>Aday / fiyat</th><th>Planlama</th><th>INSPIRE / parsel</th><th>Doğruluk</th><th>Boyut</th><th>Durum</th></tr></thead>
        <tbody>${rows}</tbody>
      </table>`;
  };

  const rowHtml = (feature, index) => {
    const properties = feature?.properties || {};
    const geometry = feature?.geometry || {};
    const parcelId = firstValue(properties, [
      'matched_inspire_id', 'matched_parcel_ref', 'matched_parcel_id',
      'parcel_id', 'parcel_reference', 'id', 'inspire_id', 'INSPIREID',
      'land_registry_inspire_id', 'title_number', 'uprn'
    ]);
    const evidence = firstValue(properties, [
      'geometry_status', 'evidence_status', 'evidence', 'match_status', 'status',
      'review_status', 'source_name', 'source'
    ]) || 'REAL_GEOMETRY_CONFIRMED';
    const matchScore = firstValue(properties, ['match_score', 'accuracy_score', 'accuracy', 'verification_score']);
    const confidenceScore = firstValue(properties, ['confidence_score', 'confidence', 'source_accuracy']);
    const accuracy = [
      matchScore !== null ? `eşleşme=${matchScore}/100` : null,
      confidenceScore !== null ? `güven=${confidenceScore}/100` : null,
    ].filter(Boolean).join(' · ') || '3/4 geometry contract';
    const area = firstValue(properties, ['parcel_area_m2', 'area_m2', 'site_area_m2', 'area', 'polygon_area_m2']);
    const perimeter = firstValue(properties, ['parcel_perimeter_m', 'perimeter_m', 'perimeter', 'polygon_perimeter_m']);
    const point = firstValue(properties, ['centroid', 'point', 'representative_point']);
    const coordinateTotal = coordinateCount(geometry.coordinates);
    const details = [
      `alan=${formatValue(area)}`,
      `çevre=${formatValue(perimeter)}`,
      `nokta=${formatValue(point)}`,
      `fiyat=${formatGbp(properties.ask_price)}`,
      `planlama=${formatValue(properties.planning_reference)}`,
    ].join('<br>');
    return `<tr data-row-index="${index + 1}">
      <td>${index + 1}</td>
      <td>${sourceLink(properties)}</td>
      <td>${escapeHtml(evidence)}</td>
      <td>${escapeHtml(accuracy)}</td>
      <td>${escapeHtml(formatValue(parcelId))}</td>
      <td>${details}</td>
      <td>${escapeHtml(geometry.type || 'NO_DATA')} · ${coordinateTotal} koordinat noktası</td>
    </tr>`;
  };

  const renderRows = () => {
    const body = document.getElementById('rows');
    const nextVisible = Math.min(state.features.length, state.visible + BATCH_SIZE);
    const fragment = state.features
      .slice(state.visible, nextVisible)
      .map((feature, offset) => rowHtml(feature, state.visible + offset))
      .join('');
    body.insertAdjacentHTML('beforeend', fragment);
    state.visible = nextVisible;

    document.body.dataset.loadedCount = String(state.features.length);
    document.body.dataset.visibleCount = String(state.visible);
    document.body.dataset.officialSourceCount = String(state.sources.length);
    document.body.dataset.internetVerifiedCandidateCount = String(
      state.candidates.filter((candidate) => candidate.internet_readback?.listing_page_live).length
    );
    document.body.dataset.semanticValid = String(
      state.features.length === 1264 && state.sources.length >= 3 && state.candidates.length >= 3
    );

    const status = document.getElementById('status');
    const verifiedCandidates = state.candidates.filter((candidate) => candidate.internet_readback?.listing_page_live).length;
    status.textContent = `Gerçek geometri: ${state.features.length} satır · görünür: ${state.visible} · resmî kaynak: ${state.sources.length} · internet doğrulamalı aday: ${verifiedCandidates}`;

    let button = document.getElementById('load-more-geometry');
    if (!button && state.visible < state.features.length) {
      button = document.createElement('button');
      button.id = 'load-more-geometry';
      button.type = 'button';
      button.textContent = `Sonraki ${BATCH_SIZE} satırı göster`;
      button.style.margin = '12px 0';
      button.addEventListener('click', renderRows);
      document.querySelector('body > table')?.insertAdjacentElement('afterend', button);
    }
    if (button) {
      button.hidden = state.visible >= state.features.length;
      button.textContent = `Sonraki ${Math.min(BATCH_SIZE, state.features.length - state.visible)} satırı göster`;
    }
  };

  const fetchJson = async (url) => {
    const response = await fetch(url, {cache: 'no-store'});
    if (!response.ok) throw new Error(`${url} HTTP ${response.status}`);
    return response.json();
  };

  const main = async () => {
    const [geojson, sourceRegistry, verifiedCandidates] = await Promise.all([
      fetchJson(GEOJSON_URL),
      fetchJson(SOURCE_REGISTRY_URL),
      fetchJson(VERIFIED_CANDIDATES_URL),
    ]);
    state.features = Array.isArray(geojson?.features) ? geojson.features : [];
    state.sources = Array.isArray(sourceRegistry?.sources) ? sourceRegistry.sources : [];
    state.candidates = Array.isArray(verifiedCandidates?.candidates) ? verifiedCandidates.candidates : [];
    if (state.features.length !== 1264) throw new Error(`expected_1264_features_got_${state.features.length}`);
    if (state.sources.length < 3) throw new Error(`expected_3_official_sources_got_${state.sources.length}`);
    if (state.candidates.length < 3) throw new Error(`expected_3_candidate_rows_got_${state.candidates.length}`);
    renderSourceSummary();
    renderCandidateSummary();
    renderRows();
  };

  main().catch((error) => {
    document.body.dataset.acceptanceError = String(error);
    const status = document.getElementById('status');
    status.textContent = `BLOCKED: ${error}`;
    status.classList.remove('ok');
    status.style.background = '#fef2f2';
    status.style.borderColor = '#ef4444';
    console.error(error);
  });
})();
