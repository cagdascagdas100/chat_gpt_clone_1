/* TerraYield Topography runtime panel patch - 2026-07-04 */
(function () {
  const REQUIRED = [
    'parcel_id','parcel_ref','elevation_sea_level_m','regional_average_elevation_m',
    'elevation_difference_regional_average_m','elevation_class','color_category',
    'confidence_rating','confidence_percent','source','source_url','source_date',
    'matching_method','calculation_explanation','accuracy_score_4','needs_manual_review','changed_in_latest_run'
  ];
  function value(obj, key) {
    return obj && obj[key] !== undefined && obj[key] !== null && String(obj[key]).trim() !== '' ? obj[key] : 'Eksik';
  }
  function renderTopographyPanel(props) {
    const p = props || {};
    const rows = REQUIRED.map(function (k) {
      return '<tr><th style="text-align:left;padding:4px 8px;border-bottom:1px solid #ddd">' + k + '</th><td style="padding:4px 8px;border-bottom:1px solid #ddd">' + value(p, k) + '</td></tr>';
    }).join('');
    return '<section id="aays-topography-detail-panel" style="font-family:Arial,sans-serif;line-height:1.35">' +
      '<h3>Topography / Elevation</h3>' +
      '<p><b>Deniz seviyesine gore yukseklik:</b> ' + value(p, 'elevation_sea_level_m') + ' m</p>' +
      '<p><b>Bolgesel ortalamaya gore fark:</b> ' + value(p, 'elevation_difference_regional_average_m') + ' m</p>' +
      '<table style="border-collapse:collapse;width:100%;font-size:13px">' + rows + '</table>' +
      '</section>';
  }
  window.AAYS_RENDER_TOPOGRAPHY_PANEL = renderTopographyPanel;
  window.AAYS_TOPOGRAPHY_REQUIRED_FIELDS = REQUIRED;
})();
