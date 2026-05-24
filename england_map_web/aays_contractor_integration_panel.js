(function () {
  const badgeEl = document.getElementById("contractorStatusBadge");
  const summaryEl = document.getElementById("contractorStatusSummary");
  const warningsEl = document.getElementById("contractorStatusWarnings");
  const previewEl = document.getElementById("contractorParcelMatchesPreview");
  const contactsHintEl = document.getElementById("contractorParcelContactsHint");
  const contactsPreviewEl = document.getElementById("contractorParcelContactsPreview");
  const refreshBtnEl = document.getElementById("refreshContractorStatus");

  if (!badgeEl || !summaryEl || !warningsEl || !previewEl || !contactsHintEl || !contactsPreviewEl) {
    return;
  }

  const API_TIMEOUT_MS = 6000;
  const REFRESH_INTERVAL_MS = 120000;
  let selectedParcelId = null;

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

  function safeNumber(value, fallback = 0) {
    const numeric = Number(value);
    return Number.isFinite(numeric) ? numeric : fallback;
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

  function renderContactSuggestions(payload, parcelId) {
    const rows = Array.isArray(payload?.rows) ? payload.rows : [];
    const totalRows = safeNumber(payload?.total_rows, 0);
    const readyRows = safeNumber(payload?.ready_rows, 0);
    const blockedRows = safeNumber(payload?.blocked_rows, 0);
    const parcelGroupIds = Array.isArray(payload?.parcel_group_ids) ? payload.parcel_group_ids : [];
    const reviewRequiredAgents = safeNumber(payload?.review_required_agents, 0);
    const reviewTokens = Array.isArray(payload?.review_required_tokens) ? payload.review_required_tokens : [];
    const groupLabel = parcelGroupIds.length ? parcelGroupIds.join(", ") : "-";
    const reviewLabel = reviewTokens.length ? `tokens=${reviewTokens.join(", ")}` : "tokens=-";

    if (!rows.length) {
      contactsHintEl.textContent = `parcel ${parcelId}: temas edilebilir estate-agent bulunamadi.`;
      contactsPreviewEl.innerHTML = `<div class="hint">group=${escapeHtml(groupLabel)} | total=${escapeHtml(totalRows)} | blocked=${escapeHtml(blockedRows)} | review_required_agents=${escapeHtml(reviewRequiredAgents)} | ${escapeHtml(reviewLabel)}</div>`;
      return;
    }

    contactsHintEl.textContent = `parcel ${parcelId}: group ${groupLabel} icin temas edilebilir ${readyRows}/${totalRows} estate-agent`;
    contactsPreviewEl.innerHTML = rows
      .slice(0, 5)
      .map((row, idx) => {
        const companyName = escapeHtml(row.company_name || row.contractor_id || "-");
        const matchMethod = escapeHtml(row.match_method || "-");
        const matchScore = escapeHtml(row.match_score || "-");
        const parcelGroupId = escapeHtml(row.parcel_group_id || "-");
        const reliability = escapeHtml(row.reliability_score || "-");
        const confidence = escapeHtml(row.data_confidence_score || "-");
        const legalScore = escapeHtml(row.legal_contact_score || "-");
        const density = escapeHtml(row.activity_density_label || row.region_activity_label || "-");
        const office = escapeHtml(row.registered_office_address || "-");
        const reviewRequired = Boolean(row.review_required);
        const reviewFlags = Array.isArray(row.review_flags) ? row.review_flags.map((v) => escapeHtml(v)).join(", ") : "-";
        const sourceUrl = row.company_source_url ? `<a href="${escapeHtml(row.company_source_url)}" target="_blank" rel="noopener noreferrer">source</a>` : "-";
        return `
          <div>
            <strong>#${idx + 1} ${companyName}</strong>
            <div>group=${parcelGroupId} | match=${matchMethod} (score ${matchScore}) | reliability=${reliability} | confidence=${confidence} | legal=${legalScore}</div>
            <div>density=${density} | office=${office} | review_required=${reviewRequired} (${reviewFlags}) | ${sourceUrl}</div>
          </div>
        `;
      })
      .join("");
  }

  async function loadContactsForParcel(parcelId) {
    const numericParcelId = Number(parcelId);
    if (!Number.isFinite(numericParcelId) || numericParcelId <= 0) {
      return;
    }
    selectedParcelId = numericParcelId;
    contactsHintEl.textContent = `parcel ${numericParcelId}: temas-onerileri yukleniyor...`;
    contactsPreviewEl.innerHTML = "";
    const result = await fetchJson(`/api/contractor/parcel/${numericParcelId}/contacts?limit=8`, "parcel contractor contacts");
    if (!result.ok) {
      contactsHintEl.textContent = `parcel ${numericParcelId}: contractor onerisi alinamadi`;
      contactsPreviewEl.innerHTML = `<div class="hint">${escapeHtml(result.error || "unknown error")}</div>`;
      return;
    }
    renderContactSuggestions(result.data || {}, numericParcelId);
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
      buttonEl.addEventListener("click", async () => {
        const parcelId = buttonEl.getAttribute("data-contractor-parcel-id");
        await focusParcelFromMatch(parcelId);
        await loadContactsForParcel(parcelId);
      });
    });
  }

  async function refreshContractorPanel() {
    setText(badgeEl, "Contractor durumu yenileniyor...");
    const statusResult = await fetchJson("/api/contractor/status", "contractor status");
    let matchesResult = await fetchJson("/api/contractor/exports/parcel-matches/preview?limit=20", "parcel match preview");
    if (!matchesResult.ok && String(matchesResult.error || "").includes("HTTP 404")) {
      matchesResult = await fetchJson("/api/contractor/exports/parcel-matches?offset=0&limit=20", "parcel matches");
    }

    if (!statusResult.ok) {
      setText(badgeEl, `Contractor status: unavailable (${statusResult.error})`);
      setText(summaryEl, "");
      renderWarnings([]);
      previewEl.innerHTML = '<div class="hint">API baglantisi kurulamadigi icin preview gosterilemiyor.</div>';
      return;
    }

    const statusPayload = statusResult.data || {};
    const manifests = statusPayload.manifests || {};
    const preflight = manifests.preflight || statusPayload.preflight_audit || {};
    const loadManifest = manifests.postgres_load || statusPayload.postgres_load_manifest || {};
    const matchManifest = manifests.parcel_match || statusPayload.parcel_match_manifest || {};
    const exportManifest = manifests.export || statusPayload.export_manifest || {};

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
      contactsHintEl.textContent = "Parcel temas-onerisi icin once match preview gerekli.";
      contactsPreviewEl.innerHTML = "";
      return;
    }
    const matchesPayload = matchesResult.data || {};
    const matchRows = matchesPayload.rows || [];
    renderMatches(matchRows, matchesPayload.total_rows || 0);
    if (selectedParcelId) {
      await loadContactsForParcel(selectedParcelId);
    } else {
      const firstParcelId = Number((matchRows[0] || {}).parcel_id);
      if (Number.isFinite(firstParcelId) && firstParcelId > 0) {
        await loadContactsForParcel(firstParcelId);
      } else {
        contactsHintEl.textContent = "Parcel secildiginde temas-onerileri burada gosterilir.";
        contactsPreviewEl.innerHTML = "";
      }
    }
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
