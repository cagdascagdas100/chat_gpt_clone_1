(function () {
  const badgeEl = document.getElementById("contractorStatusBadge");
  const summaryEl = document.getElementById("contractorStatusSummary");
  const warningsEl = document.getElementById("contractorStatusWarnings");
  const previewEl = document.getElementById("contractorParcelMatchesPreview");
  const refreshBtnEl = document.getElementById("refreshContractorStatus");

  if (!badgeEl || !summaryEl || !warningsEl || !previewEl) {
    return;
  }

  const API_TIMEOUT_MS = 6000;
  const REFRESH_INTERVAL_MS = 120000;

  function escapeHtml(value) {
    return String(value ?? "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#39;");
  }

  function setText(el, text) {
    if (!el) return;
    el.textContent = text;
  }

  async function focusParcelFromMatch(parcelId) {
    const numericParcelId = Number(parcelId);
    if (!Number.isFinite(numericParcelId) || numericParcelId <= 0) {
      setText(warningsEl, "Gecersiz parcel_id, harita odagi yapilamadi.");
      return;
    }
    const bridge = window.AAYS_CONTRACTOR_INTEGRATION;
    if (bridge && typeof bridge.focusParcelById === "function") {
      const result = await bridge.focusParcelById(numericParcelId);
      if (!result?.ok) {
        setText(warningsEl, `Parcel odagi basarisiz: ${result?.error || "unknown"}`);
      }
      return;
    }
    window.dispatchEvent(
      new CustomEvent("aays:contractor-focus-parcel", {
        detail: { parcelId: numericParcelId },
      })
    );
  }

  async function fetchJson(url, label) {
    const controller = new AbortController();
    const timer = window.setTimeout(() => controller.abort(), API_TIMEOUT_MS);
    try {
      const response = await fetch(url, { signal: controller.signal });
      window.clearTimeout(timer);
      if (!response.ok) {
        return { ok: false, error: `${label}: HTTP ${response.status}`, data: null };
      }
      const data = await response.json();
      return { ok: true, error: null, data };
    } catch (error) {
      window.clearTimeout(timer);
      if (error?.name === "AbortError") {
        return { ok: false, error: `${label}: timeout`, data: null };
      }
      return { ok: false, error: `${label}: ${error?.message || "request failed"}`, data: null };
    }
  }

  function renderWarnings(warnings) {
    if (!Array.isArray(warnings) || warnings.length === 0) {
      setText(warningsEl, "");
      return;
    }
    warningsEl.innerHTML = warnings.map((w) => `<div>- ${escapeHtml(w)}</div>`).join("");
  }

  function renderMatches(rows, totalRows) {
    if (!Array.isArray(rows) || rows.length === 0) {
      previewEl.innerHTML = '<div class="hint">Parcel match preview bulunamadi.</div>';
      return;
    }
    const items = rows
      .slice(0, 8)
      .map((row) => {
        const parcelIdValue = Number(row.parcel_id);
        const parcelId = escapeHtml(row.parcel_id || "-");
        const contractorId = escapeHtml(row.contractor_id || "-");
        const method = escapeHtml(row.match_method || "-");
        const score = escapeHtml(row.match_score || "-");
        const parcelAction = Number.isFinite(parcelIdValue) && parcelIdValue > 0
          ? `<button class="workspace-button subtle" type="button" data-contractor-parcel-id="${parcelIdValue}">parcel ${parcelId}</button>`
          : `<strong>parcel ${parcelId}</strong>`;
        return `<div>${parcelAction} - contractor ${contractorId} - ${method} - score ${score}</div>`;
      })
      .join("");
    previewEl.innerHTML = `<div class="hint">Toplam match: ${escapeHtml(totalRows)} (parcel dugmesine tiklayip haritada odaklanin)</div>${items}`;
    previewEl.querySelectorAll("[data-contractor-parcel-id]").forEach((buttonEl) => {
      buttonEl.addEventListener("click", () => {
        const parcelId = buttonEl.getAttribute("data-contractor-parcel-id");
        void focusParcelFromMatch(parcelId);
      });
    });
  }

  async function refreshContractorPanel() {
    setText(badgeEl, "Contractor durumu yenileniyor...");
    const statusResult = await fetchJson("/api/contractor/status", "contractor status");
    const matchesResult = await fetchJson("/api/contractor/exports/parcel-matches?offset=0&limit=20", "parcel matches");

    if (!statusResult.ok) {
      setText(badgeEl, `Contractor status: unavailable (${statusResult.error})`);
      setText(summaryEl, "");
      renderWarnings([]);
      previewEl.innerHTML = '<div class="hint">API baglantisi kurulamadigi icin preview gosterilemiyor.</div>';
      return;
    }

    const statusPayload = statusResult.data || {};
    const preflight = statusPayload.preflight_audit || {};
    const loadManifest = statusPayload.postgres_load_manifest || {};
    const matchManifest = statusPayload.parcel_match_manifest || {};
    const exportManifest = statusPayload.export_manifest || {};

    const statusValue = String(statusPayload.status || "unknown");
    const statusLabel = statusValue === "completed" ? "completed" : statusValue;
    setText(badgeEl, `Contractor status: ${statusLabel}`);

    const contractorCount =
      exportManifest.contractor_count ??
      loadManifest.loaded_companies ??
      "-";
    const projectCount =
      exportManifest.project_count ??
      loadManifest.loaded_projects ??
      "-";
    const matchCount =
      exportManifest.parcel_match_count ??
      matchManifest.match_count ??
      "-";
    const preflightOk =
      String(preflight.status || "").toLowerCase() === "completed" &&
      Boolean(preflight.db_credentials_present) &&
      Boolean(preflight.connection_ok) &&
      Boolean(preflight.db_query_ok);

    summaryEl.innerHTML = [
      `<div>preflight_ok: <strong>${preflightOk}</strong></div>`,
      `<div>contractors: <strong>${escapeHtml(contractorCount)}</strong></div>`,
      `<div>projects: <strong>${escapeHtml(projectCount)}</strong></div>`,
      `<div>parcel matches: <strong>${escapeHtml(matchCount)}</strong></div>`,
      `<div>contact rule: <strong>DO_NOT_CONTACT guard active</strong></div>`,
    ].join("");

    renderWarnings(statusPayload.warnings || []);

    if (!matchesResult.ok) {
      previewEl.innerHTML = `<div class="hint">Match preview hatasi: ${escapeHtml(matchesResult.error)}</div>`;
      return;
    }
    const matchesPayload = matchesResult.data || {};
    renderMatches(matchesPayload.rows || [], matchesPayload.total_rows || 0);
  }

  if (refreshBtnEl) {
    refreshBtnEl.addEventListener("click", () => {
      refreshContractorPanel();
    });
  }

  window.AAYSContractorIntegrationPanel = {
    refresh: refreshContractorPanel,
  };

  refreshContractorPanel();
  window.setInterval(refreshContractorPanel, REFRESH_INTERVAL_MS);
})();
