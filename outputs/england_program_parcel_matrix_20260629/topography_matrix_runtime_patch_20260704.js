/* TerraYield 8020 Topography latest changes panel patch - 2026-07-04 */
(function () {
  async function loadTopographyChanges() {
    const targetId = 'topography-guncel-degisiklikler-panel';
    let el = document.getElementById(targetId);
    if (!el) {
      el = document.createElement('section');
      el.id = targetId;
      el.style.cssText = 'margin:16px;padding:16px;border:1px solid #bbb;border-radius:8px;background:#fff;font-family:Arial,sans-serif';
      document.body.prepend(el);
    }
    try {
      const res = await fetch('topography_updates/latest_changes.json?refresh=' + Date.now());
      const data = await res.json();
      const s = data.summary || {};
      const changes = data.changes || [];
      const cards = changes.length ? changes.map(function (r) {
        return '<div style="border-top:1px solid #ddd;padding:8px 0"><b>' + (r.parcel_ref || r.parcel_id || 'parcel') + '</b>' +
          '<br>Sea level: ' + r.elevation_sea_level_m + ' m' +
          '<br>Regional diff: ' + r.elevation_difference_regional_average_m + ' m' +
          '<br>Source: ' + r.source + ' / ' + r.source_date +
          '<br>Confidence: ' + r.confidence_rating + ' ' + r.confidence_percent + '% ' +
          '<br>Match: ' + r.matching_method +
          '<br>Calculation: ' + r.calculation_explanation + '</div>';
      }).join('') : '<p>Henuz dogrulanmis Topography parsel satiri yok.</p>';
      el.innerHTML = '<h2>Topography - Guncel Degisiklikler</h2>' +
        '<p>Tamamlanan: %' + (s.completion_percent ?? 0) + ' | Kalan: %' + (s.remaining_percent ?? 100) + ' | Parsel: ' + (s.filled_parcel_count ?? 0) + ' | Dogruluk: ' + (s.accuracy_score_4 || '0/4') + '</p>' +
        '<p>Program entegrasyonu: %' + (s.program_integration_percent ?? 0) + ' | Web sitesi guncellemesi: %' + (s.website_update_percent ?? 0) + ' | final_ready: ' + Boolean(data.final_ready) + '</p>' + cards;
    } catch (err) {
      el.innerHTML = '<h2>Topography - Guncel Degisiklikler</h2><p>latest_changes.json okunamadi: ' + err.message + '</p>';
    }
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', loadTopographyChanges); else loadTopographyChanges();
})();
