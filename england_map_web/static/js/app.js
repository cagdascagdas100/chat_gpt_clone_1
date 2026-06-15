"use strict";
(function () {
  const TOPOGRAPHY_FIELDS = [
    "center_elevation_m",
    "region_average_elevation_m",
    "elevation_difference_from_region_average_m",
    "confidence_level",
    "confidence_reason",
    "matching_method",
    "calculation_explanation",
    "source_resolution_m",
    "datum"
  ];

  function normalizeTopographyLookupForPopup(raw) {
    const data = raw && typeof raw === "object" ? raw : {};
    const topography = data.topography && typeof data.topography === "object" ? data.topography : data;
    const normalized = {};
    TOPOGRAPHY_FIELDS.forEach((field) => {
      normalized[field] = Object.prototype.hasOwnProperty.call(topography, field) ? topography[field] : null;
    });
    normalized.source = topography.source || topography.topography_source || data.source || null;
    normalized.topography_source = topography.topography_source || normalized.source || null;
    normalized.source_dataset = topography.source_dataset || data.source_dataset || null;
    normalized.calculated_at = topography.calculated_at || data.calculated_at || null;
    normalized.layer_name = topography.layer_name || data.layer_name || "hight_differance.png";
    return normalized;
  }

  function buildTopographyPopupRowsHtml(raw) {
    const data = normalizeTopographyLookupForPopup(raw);
    return TOPOGRAPHY_FIELDS.map((field) => {
      const label = field.replace(/_/g, " ");
      const value = data[field] === null || data[field] === undefined || data[field] === "" ? "-" : data[field];
      return `<div class="workspace-row"><span>${label}</span><strong>${value}</strong></div>`;
    }).join("");
  }

  window.AAYSTopographyPopupContract = {
    normalizeTopographyLookupForPopup,
    buildTopographyPopupRowsHtml,
    icon: "hight_differance.png"
  };
}());
