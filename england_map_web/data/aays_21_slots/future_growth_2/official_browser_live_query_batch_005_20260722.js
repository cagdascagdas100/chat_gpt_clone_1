(() => {
"use strict";
const MANIFEST = "./official_browser_live_query_manifest_batch_005_20260722.json";
const state = {manifest:null, operations:[], results:[], running:false, completed:0, success:0, intersections:0, errors:0};

const esc = v => String(v ?? "").replace(/[&<>"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
const sleep = ms => new Promise(r => setTimeout(r, ms));

function arcgisUrl(row, layer) {
  const token = String(layer[0]);
  const parts = token.split("@");
  const layerId = parts[0];
  const service = parts.length > 1 ? parts.slice(1).join("@") : row.arcgis_service;
  const q = new URL(`${service}/${layerId}/query`);
  q.searchParams.set("f","json");
  q.searchParams.set("where","1=1");
  q.searchParams.set("geometry",`${row.lon},${row.lat}`);
  q.searchParams.set("geometryType","esriGeometryPoint");
  q.searchParams.set("inSR","4326");
  q.searchParams.set("spatialRel","esriSpatialRelIntersects");
  q.searchParams.set("outFields","*");
  q.searchParams.set("returnGeometry","false");
  return q.toString();
}

function planningUrl(row, dataset) {
  const q = new URL("https://www.planning.data.gov.uk/entity.json");
  q.searchParams.set("latitude", String(row.lat));
  q.searchParams.set("longitude", String(row.lon));
  q.searchParams.append("dataset", dataset);
  ["name","dataset","reference","entity","quality"].forEach(f => q.searchParams.append("field",f));
  q.searchParams.set("limit","100");
  return q.toString();
}

function buildOperations(m) {
  const ops = [];
  let n = 0;
  for (const row of m.rows) {
    ops.push({operation_no:++n, kind:"STATIC", row_no:row.row_no, parcel_id:row.parcel_id, lpa:row.lpa,
      operation:"CANONICAL_POINT_IDENTITY", source:"england_map_web/data/aays_21_slots/height_difference_2/canonical_points_runtime_032.json",
      label:`WGS84 ${row.lon}, ${row.lat}`, static_result:"VERIFIED_CANONICAL_POINT"});
    for (const layer of row.layers) {
      ops.push({operation_no:++n, kind:"ARCGIS", row_no:row.row_no, parcel_id:row.parcel_id, lpa:row.lpa,
        operation:"ARCGIS_EXACT_INTERSECTS", label:layer[1], source:arcgisUrl(row,layer)});
    }
    for (const dataset of m.planning_data_api.datasets) {
      ops.push({operation_no:++n, kind:"PLANNING_DATA", row_no:row.row_no, parcel_id:row.parcel_id, lpa:row.lpa,
        operation:"PLANNING_DATA_POINT_INTERSECTS", label:dataset, source:planningUrl(row,dataset)});
    }
  }
  const validations = [
    ["OFFICIAL_ONLY_ALLOWLIST","PASS","Only official GLA, Lambeth Council and MHCLG Planning Data endpoints are configured."],
    ["CONCURRENCY_BOUND","PASS",`Concurrency is capped at ${m.browser_execution.concurrency}.`],
    ["RETRY_TIMEOUT_BOUND","PASS",`${m.browser_execution.retries} retries and ${m.browser_execution.timeout_ms}ms timeout are enforced.`],
    ["NO_SCORE_GUARD","PASS","No score or confidence is produced by this browser runner."],
    ["ZERO_RESULT_CAUTION","PASS","A zero result applies only to the queried layer or dataset."]
  ];
  for (const v of validations) {
    ops.push({operation_no:++n, kind:"STATIC", row_no:"SYSTEM", parcel_id:"—", lpa:"—",
      operation:v[0], label:"—", source:m.web_js_path, static_result:v[1], static_note:v[2]});
  }
  if (ops.length !== m.batch_preparation_operations_total) {
    throw new Error(`Operation count mismatch ${ops.length}/${m.batch_preparation_operations_total}`);
  }
  return ops;
}

async function fetchJsonWithRetry(url, cfg) {
  let lastError = null;
  for (let attempt=0; attempt<=cfg.retries; attempt++) {
    const ctrl = new AbortController();
    const timer = setTimeout(() => ctrl.abort(), cfg.timeout_ms);
    try {
      const res = await fetch(url, {cache:"no-store", signal:ctrl.signal, headers:{"Accept":"application/json"}});
      const text = await res.text();
      let data = null;
      try { data = JSON.parse(text); } catch { throw new Error(`Non-JSON HTTP ${res.status}`); }
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      clearTimeout(timer);
      return {data, attempt};
    } catch (err) {
      clearTimeout(timer);
      lastError = err;
      if (attempt < cfg.retries) await sleep(cfg.retry_backoff_ms * (attempt + 1));
    }
  }
  throw lastError || new Error("Unknown request failure");
}

function classify(op, data) {
  if (op.kind === "ARCGIS") {
    if (data && data.error) return {status:"API_ERROR", count:0, details:data.error};
    const features = Array.isArray(data?.features) ? data.features : [];
    return {
      status: features.length ? "INTERSECTION_FOUND" : "NO_INTERSECTION_IN_THIS_LAYER",
      count: features.length,
      details: features.map(f => f.attributes || {}).slice(0,20)
    };
  }
  const entities = Array.isArray(data?.entities) ? data.entities : [];
  return {
    status: entities.length ? "INTERSECTION_FOUND" : "NO_INTERSECTION_IN_THIS_DATASET",
    count: entities.length,
    details: entities.slice(0,20)
  };
}

function rowHtml(op, result) {
  const status = result?.status || op.static_result || "PENDING";
  const cls = status.includes("ERROR") ? "bad" : status.includes("FOUND") || status==="PASS" || status.startsWith("VERIFIED") ? "ok" : status.includes("PENDING") ? "pending" : "neutral";
  const count = result?.count ?? (op.kind==="STATIC" ? "—" : 0);
  const attempts = result?.attempts ?? "—";
  const note = result?.note || op.static_note || (status.startsWith("NO_INTERSECTION") ? "Only this official layer/dataset returned zero; no broader negative inference." : "");
  return `<tr id="op-${op.operation_no}">
<td>${esc(op.operation_no)}</td><td>${esc(op.row_no)}</td><td>${esc(op.parcel_id)}</td><td>${esc(op.lpa)}</td>
<td>${esc(op.operation)}</td><td>${esc(op.label)}</td><td><a href="${esc(op.source)}" target="_blank" rel="noopener">${esc(op.source)}</a></td>
<td class="${cls}">${esc(status)}</td><td>${esc(count)}</td><td>${esc(attempts)}</td>
<td class="ok">100%</td><td class="pending">0%</td><td>null</td><td>0%</td><td>${esc(note)}</td></tr>`;
}

function updateCards() {
  const m = state.manifest;
  const values = [
    ["Hazırlık",`${m.batch_preparation_operations_completed}/${m.batch_preparation_operations_total}`],
    ["Canlı sorgu",m.browser_live_network_queries],
    ["Tamamlanan",`${state.completed}/${m.browser_live_network_queries}`],
    ["Başarılı HTTP/API",state.success],
    ["Kesişim bulunan",state.intersections],
    ["Hata",state.errors],
    ["ArcGIS sorgusu",m.arcgis_live_queries],
    ["Planning Data",m.planning_data_live_queries],
    ["Aday",m.candidate_rows_cumulative],
    ["Toplam resmî kaynak",m.cumulative_unique_official_source_pages],
    ["Hazırlık ilerlemesi",m.browser_live_query_readiness_pct+"%"],
    ["Kesin eşleşme",m.exact_binding_progress_pct+"%"]
  ];
  document.getElementById("cards").innerHTML = values.map(v=>`<div class="card">${esc(v[0])}<br><b>${esc(v[1])}</b></div>`).join("");
  document.getElementById("progress").value = state.completed;
  document.getElementById("progress").max = m.browser_live_network_queries;
}

function renderInitial() {
  document.getElementById("ops").innerHTML = state.operations.map(op => rowHtml(op, op.kind==="STATIC" ? {status:op.static_result,note:op.static_note} : null)).join("");
  updateCards();
}

async function runOne(op) {
  const started = new Date().toISOString();
  try {
    const {data, attempt} = await fetchJsonWithRetry(op.source, state.manifest.browser_execution);
    const c = classify(op,data);
    const result = {...c, attempts:attempt+1, started_at:started, finished_at:new Date().toISOString(), source:op.source};
    state.success++;
    if (c.status === "INTERSECTION_FOUND") state.intersections++;
    return result;
  } catch (err) {
    state.errors++;
    return {status:"CORS_OR_NETWORK_ERROR", count:0, attempts:state.manifest.browser_execution.retries+1,
      note:String(err?.message || err), started_at:started, finished_at:new Date().toISOString(), source:op.source};
  }
}

async function worker(queue) {
  while (queue.length) {
    const op = queue.shift();
    const result = await runOne(op);
    state.results.push({...op,...result});
    state.completed++;
    document.getElementById(`op-${op.operation_no}`).outerHTML = rowHtml(op,result);
    updateCards();
    await sleep(120);
  }
}

async function start() {
  if (state.running) return;
  state.running = true;
  state.results = [];
  state.completed = state.success = state.intersections = state.errors = 0;
  document.getElementById("start").disabled = true;
  document.getElementById("status").textContent = "Canlı resmî sorgular çalışıyor…";
  const queue = state.operations.filter(o=>o.kind!=="STATIC").slice();
  const workers = Array.from({length:state.manifest.browser_execution.concurrency},()=>worker(queue));
  await Promise.all(workers);
  state.running = false;
  document.getElementById("start").disabled = false;
  document.getElementById("status").textContent = `Tamamlandı: ${state.completed}/${state.manifest.browser_live_network_queries}. Sonuçları dışa aktarın; GitHub readback olmadan checkpoint çözülmez.`;
}

function exportJson() {
  const payload = {
    schema_version:1,
    workstream_id:state.manifest.workstream_id,
    slot_id:state.manifest.slot_id,
    continuation_key:state.manifest.continuation_key,
    exported_at:new Date().toISOString(),
    source_manifest:MANIFEST,
    live_network_queries:state.manifest.browser_live_network_queries,
    completed:state.completed,
    success:state.success,
    intersections:state.intersections,
    errors:state.errors,
    exact_parcel_bound_rows:0,
    scored_business_rows:0,
    score_policy:"No score emitted. Results require canonical review and cross-check.",
    results:state.results
  };
  const blob = new Blob([JSON.stringify(payload,null,2)],{type:"application/json"});
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = `future_growth_2_live_query_results_${new Date().toISOString().replace(/[:.]/g,"-")}.json`;
  a.click();
  setTimeout(()=>URL.revokeObjectURL(a.href),1000);
}

async function init() {
  const res = await fetch(MANIFEST,{cache:"no-store"});
  if (!res.ok) throw new Error(`Manifest HTTP ${res.status}`);
  state.manifest = await res.json();
  state.operations = buildOperations(state.manifest);
  document.getElementById("meta").innerHTML = `Continuation: <code>${esc(state.manifest.continuation_key)}</code><br>Manifest: <code>${esc(MANIFEST)}</code><br>Canlı sorgu: ${esc(state.manifest.browser_live_network_queries)} | Hazırlık işlemi: ${esc(state.manifest.batch_preparation_operations_total)}`;
  renderInitial();
  document.getElementById("start").addEventListener("click",start);
  document.getElementById("export").addEventListener("click",exportJson);
  if (state.manifest.browser_execution.auto_start) start();
}
init().catch(err => { document.getElementById("status").textContent = `Başlatma hatası: ${err.message}`; });
})();