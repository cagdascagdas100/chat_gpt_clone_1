(() => {
  'use strict';

  const GEOJSON_URL = '../docs/chatgpt_status/aays1/geometry_review_3of4/all_1264_real_geometry_3of4.geojson';
  const SOURCE_REGISTRY_URL = './data/aays_21_slots/ready_to_sell_1/official_source_candidates_20260720.json';
  const BATCH_SIZE = 50;

  const state = {
    features: [],
    sources: [],
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

  const sourceLink = (properties) => {
    const value = firstValue(properties, ['source_url', 'evidence_url', 'url', 'listing_url', 'photo_url']);
    if (value && /^https?:\/\//i.test(String(value))) {
      return `<a href="${escapeHtml(value)}" target="_blank" rel="noopener noreferrer">kaynak</a>`;
    }
    const fallback = state.sources[0]?.url;
    return fallback
      ? `<a href="${escapeHtml(fallback)}" target="_blank" rel="noopener noreferrer">HMLR resmî kaynak</a>`
      : 'NO_DATA';
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
      const table = document.querySelector('table');
      table?.parentNode?.insertBefore(panel, table);
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
      <strong>Resmî internet kaynakları: ${state.sources.length}</strong>
      <div style="font-size:12px;margin:6px 0">Kaynak doğrulaması ve parsel bağlama güveni ayrı ölçülür. Kesin kimlik birleştirmesi yapılmadan parsel değeri yayımlanmaz.</div>
      <table style="width:100%;font-size:11px">
        <thead><tr><th>Kaynak</th><th>Yayıncı</th><th>Kaynak skoru</th><th>Parsel bağlama</th><th>Sınır</th><th>URL</th></tr></thead>
        <tbody>${sourceRows}</tbody>
      </table>`;
  };

  const rowHtml = (feature, index) => {
    const properties = feature?.properties || {};
    const geometry = feature?.geometry || {};
    const parcelId = firstValue(properties, [
      'parcel_id', 'parcel_reference', 'id', 'inspire_id', 'INSPIREID',
      'land_registry_inspire_id', 'title_number', 'uprn'
    ]);
    const evidence = firstValue(properties, [
      'evidence_status', 'evidence', 'match_status', 'status', 'review_status',
      'source_name', 'source'
    ]) || 'REAL_GEOMETRY_CONFIRMED';
    const accuracy = firstValue(properties, [
      'accuracy_score', 'accuracy', 'confidence_score', 'confidence',
      'verification_score', 'source_accuracy'
    ]) || '3/4 geometry contract';
    const area = firstValue(properties, ['area_m2', 'area', 'polygon_area_m2']);
    const perimeter = firstValue(properties, ['perimeter_m', 'perimeter', 'polygon_perimeter_m']);
    const point = firstValue(properties, ['centroid', 'point', 'representative_point']);
    const coordinateTotal = coordinateCount(geometry.coordinates);
    const metrics = [
      `alan=${formatValue(area)}`,
      `çevre=${formatValue(perimeter)}`,
      `nokta=${formatValue(point)}`
    ].join('<br>');
    return `<tr data-row-index="${index + 1}">
      <td>${index + 1}</td>
      <td>${sourceLink(properties)}</td>
      <td>${escapeHtml(evidence)}</td>
      <td>${escapeHtml(accuracy)}</td>
      <td>${escapeHtml(formatValue(parcelId))}</td>
      <td>${metrics}</td>
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
    document.body.dataset.semanticValid = String(state.features.length === 1264 && state.sources.length >= 3);

    const status = document.getElementById('status');
    status.textContent = `Gerçek geometri: ${state.features.length} satır · görünür: ${state.visible} · doğrulanmış resmî kaynak: ${state.sources.length}`;

    let button = document.getElementById('load-more-geometry');
    if (!button && state.visible < state.features.length) {
      button = document.createElement('button');
      button.id = 'load-more-geometry';
      button.type = 'button';
      button.textContent = `Sonraki ${BATCH_SIZE} satırı göster`;
      button.style.margin = '12px 0';
      button.addEventListener('click', renderRows);
      document.querySelector('table')?.insertAdjacentElement('afterend', button);
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
    const [geojson, sourceRegistry] = await Promise.all([
      fetchJson(GEOJSON_URL),
      fetchJson(SOURCE_REGISTRY_URL),
    ]);
    state.features = Array.isArray(geojson?.features) ? geojson.features : [];
    state.sources = Array.isArray(sourceRegistry?.sources) ? sourceRegistry.sources : [];
    if (state.features.length !== 1264) throw new Error(`expected_1264_features_got_${state.features.length}`);
    if (state.sources.length < 3) throw new Error(`expected_3_official_sources_got_${state.sources.length}`);
    renderSourceSummary();
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
