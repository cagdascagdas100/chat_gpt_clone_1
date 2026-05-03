const SUPABASE_URL = "https://kkasmniqefjzgmfevjdr.supabase.co";
const SUPABASE_ANON_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImtrYXNtbmlxZWZqemdtZmV2amRyIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzM0ODAyMjMsImV4cCI6MjA4OTA1NjIyM30.eGWFiUdZFnMFq-naKgIYIaFkyF9ldttaatYz2Ov8x8Q";
const STORAGE_KEY = "deutsch_tests_1_history_v8";
const DEVICE_KEY = "deutsch_tests_1_device_id";
let selected = "t4";
let current = [];
let meta = {};
let results = [];
let hangWords = [];
let hangIndex = 0;
let hangScore = 0;
let deviceId = localStorage.getItem(DEVICE_KEY);
if (!deviceId) {
  deviceId = (window.crypto && crypto.randomUUID) ? crypto.randomUUID() : "dev_" + Date.now() + "_" + Math.random().toString(36).slice(2);
  localStorage.setItem(DEVICE_KEY, deviceId);
}
let sb = null;
try {
  if (window.supabase && SUPABASE_URL && SUPABASE_ANON_KEY) {
    sb = window.supabase.createClient(SUPABASE_URL, SUPABASE_ANON_KEY, { global: { headers: { "x-device-id": deviceId } } });
  }
} catch (e) {
  sb = null;
}
const $ = (id) => document.getElementById(id);
function esc(s) { return String(s).replace(/[&<>']/g, ch => ({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#039;'}[ch])); }
function norm(s) { return String(s || "").trim().replace(/[.,;:!?]+$/," ").replace(/\s+/g," ").trim().toLocaleLowerCase("de-DE"); }
function shuffle(arr) { const a = arr.slice(); for (let i=a.length-1;i>0;i--) { const j=Math.floor(Math.random()*(i+1)); [a[i],a[j]]=[a[j],a[i]]; } return a; }
function makeId() { return Date.now().toString(36) + Math.random().toString(36).slice(2, 10); }
function hideAll() { ["quiz","hang","shared"].forEach(id => $(id).classList.add("hide")); $("start").classList.add("hide"); }
function backToMenu() { ["quiz","hang","shared"].forEach(id => $(id).classList.add("hide")); $("start").classList.remove("hide"); }
function optionList(answer, test) {
  const pool = test.words.filter(w => norm(w) !== norm(answer));
  return shuffle([answer].concat(shuffle(pool).slice(0, 5)));
}
function makeBank(test) {
  const groups = { fill: [], mc: [], tf: [], gram: [], match: [] };
  test.fill.forEach(x => groups.fill.push({ type:"radio", section:"Lückentext 6 Optionen", q:x[0], a:x[1], options:optionList(x[1], test), tag:x[2] }));
  test.mc.forEach(x => groups.mc.push({ type:"radio", section:"Multiple Choice", q:x[0], a:x[1][x[2]], options:x[1], tag:x[3] }));
  test.tf.forEach(x => groups.tf.push({ type:"tf", section:"Richtig/Falsch", q:x[0], a:x[1] ? "Richtig" : "Falsch", bool:x[1], tag:x[2] }));
  test.gram.forEach(x => groups.gram.push({ type:"text", section:"Grammatik/Kollokation", q:x[0], a:x[1], tag:x[2] }));
  test.match.forEach((x, i) => {
    const distractors = shuffle(test.match.filter((_, j) => j !== i).map(y => y[1])).slice(0, 5);
    groups.match.push({ type:"radio", section:"Zuordnung", q:"Welche Definition passt zu: " + x[0] + "?", a:x[1], options:shuffle([x[1]].concat(distractors)), tag:"Definition" });
  });
  Object.keys(groups).forEach(k => groups[k] = shuffle(groups[k]));
  return groups;
}
function buildQuestions(test, count) {
  const groups = makeBank(test);
  const order = ["fill","mc","tf","gram","match"];
  const out = [];
  let guard = 0;
  while (out.length < count && Object.values(groups).some(g => g.length) && guard < 1000) {
    const key = order[guard % order.length];
    if (groups[key].length) out.push(groups[key].shift());
    guard++;
  }
  return out;
}
function init() {
  $("dbs").innerHTML = sb ? '<b class="dbok">Supabase: aktiv</b>' : '<b class="dberr">Supabase: ayarlı değil</b>';
  const tests = window.DEUTSCH_TESTS || {};
  $("testList").innerHTML = Object.entries(tests).map(([key, test], i) => '<label class="opt"><input type="radio" name="tc" value="' + key + '" ' + (i===0 ? 'checked' : '') + '> <b>' + esc(test.title) + '</b><br><span class="muted">' + esc(test.topic) + '</span></label>').join("");
  document.querySelectorAll('input[name="tc"]').forEach(el => el.addEventListener("change", () => { selected = el.value; }));
  $("btnShort").addEventListener("click", () => startQuiz(15));
  $("btnMedium").addEventListener("click", () => startQuiz(25));
  $("btnLong").addEventListener("click", () => startQuiz(35));
  $("btnHang").addEventListener("click", startHangman);
  $("btnGrade").addEventListener("click", grade);
  $("btnDownload").addEventListener("click", downloadReport);
  $("btnBack").addEventListener("click", backToMenu);
  $("btnBack2").addEventListener("click", backToMenu);
  $("btnCheckHang").addEventListener("click", checkHang);
  $("btnNextHang").addEventListener("click", nextHang);
  $("btnClearLocal").addEventListener("click", clearLocal);
  historyRender();
}
function startQuiz(count) {
  const test = window.DEUTSCH_TESTS[selected];
  current = buildQuestions(test, count);
  meta = { shareId: makeId(), slug:test.slug, title:test.title, topic:test.topic, len: count===15 ? "Az" : count===25 ? "Orta" : "Uzun", date:new Date().toISOString() };
  hideAll();
  $("quiz").classList.remove("hide");
  $("rep").classList.add("hide");
  $("ttl").textContent = test.title;
  $("meta").textContent = "Thema: " + test.topic + " · Länge: " + meta.len + " · Fragen: " + current.length + " · Verteilung: Lückentext, Multiple Choice, Richtig/Falsch, Grammatik, Zuordnung";
  $("wb").innerHTML = test.words.map(w => '<span class="pill">' + esc(w) + '</span>').join("");
  renderQuestions();
  progress();
}
function renderQuestions() {
  $("qs").innerHTML = current.map((q, i) => {
    q.id = "q_" + i;
    let html = '<div class="q"><div class="qt">' + (i+1) + '. [' + esc(q.section) + '] ' + esc(q.q) + '</div>';
    if (q.type === "radio") {
      html += q.options.map((o, j) => '<label class="opt"><input type="radio" name="' + q.id + '" value="' + j + '"> ' + String.fromCharCode(65+j) + ') ' + esc(o) + '</label>').join("");
    } else if (q.type === "tf") {
      html += '<label class="opt"><input type="radio" name="' + q.id + '" value="true"> Richtig</label><label class="opt"><input type="radio" name="' + q.id + '" value="false"> Falsch</label>';
    } else {
      html += '<input type="text" id="' + q.id + '" autocomplete="off">';
    }
    html += '<p class="muted">Fokus: ' + esc(q.tag) + '</p></div>';
    return html;
  }).join("");
  document.querySelectorAll("#qs input").forEach(el => { el.addEventListener("input", progress); el.addEventListener("change", progress); });
}
function userValue(q) {
  if (q.type === "text") return $(q.id).value;
  const checked = document.querySelector('input[name="' + q.id + '"]:checked');
  return checked ? checked.value : "";
}
function mark(q, ok) {
  if (q.type === "text") {
    const el = $(q.id);
    el.classList.remove("ok","no");
    if (userValue(q)) el.classList.add(ok ? "ok" : "no");
    return;
  }
  document.querySelectorAll('input[name="' + q.id + '"]').forEach(input => input.closest("label").classList.remove("ok","no"));
  const checked = document.querySelector('input[name="' + q.id + '"]:checked');
  if (checked) checked.closest("label").classList.add(ok ? "ok" : "no");
}
function checkQuestion(q) {
  const raw = userValue(q);
  let shown = raw || "—";
  let ok = false;
  if (q.type === "radio") {
    shown = raw === "" ? "—" : q.options[Number(raw)];
    ok = norm(shown) === norm(q.a);
  } else if (q.type === "tf") {
    shown = raw === "" ? "—" : (raw === "true" ? "Richtig" : "Falsch");
    ok = norm(shown) === norm(q.a);
  } else {
    ok = norm(raw) === norm(q.a);
  }
  mark(q, ok);
  return { section:q.section, tag:q.tag, q:q.q, u:shown, a:q.a, ok:ok };
}
function progress() {
  const answered = current.filter(q => userValue(q)).length;
  const total = current.length;
  $("pt").textContent = answered + "/" + total + " bearbeitet";
  $("pb").style.width = total ? (answered / total * 100) + "%" : "0%";
}
function localHistory() { try { return JSON.parse(localStorage.getItem(STORAGE_KEY) || "[]"); } catch (e) { return []; } }
function saveLocal(result) { const h = localHistory(); h.unshift(result); localStorage.setItem(STORAGE_KEY, JSON.stringify(h.slice(0,50))); }
async function saveRemote(result) {
  if (!sb) return false;
  const row = { share_id:result.shareId, device_id:deviceId, test_slug:result.slug, test_title:result.title, topic:result.topic, length_label:result.len, score:result.score, total:result.total, percent:result.percent, wrong:result.wrong };
  const { error } = await sb.from("deutsch_test_results").insert(row);
  if (error) console.error(error);
  return !error;
}
function encodeResult(obj) { return encodeURIComponent(btoa(unescape(encodeURIComponent(JSON.stringify(obj))))); }
function decodeResult(str) { return JSON.parse(decodeURIComponent(escape(atob(decodeURIComponent(str))))); }
async function grade() {
  results = current.map(checkQuestion);
  const correct = results.filter(r => r.ok).length;
  const wrong = results.filter(r => !r.ok);
  const percent = Math.round(correct / results.length * 100);
  const result = { ...meta, score:correct, total:results.length, percent:percent, wrong:wrong };
  saveLocal(result);
  const remote = await saveRemote(result);
  const link = remote ? location.origin + location.pathname + "#share=" + result.shareId : location.origin + location.pathname + "#result=" + encodeResult(result);
  $("out").innerHTML = '<p><b>' + correct + '/' + results.length + ' richtig – ' + percent + '%</b></p><p>' + (remote ? '<span class="dbok">Supabase kaydı yapıldı.</span>' : '<span class="dberr">Supabase kaydı yok; local/share hash kullanıldı.</span>') + '</p><p><input id="lnk" value="' + esc(link) + '" readonly onclick="this.select()"></p><button id="copyBtn">Link kopieren</button><h3>Falsche Antworten</h3>' + (wrong.length ? wrong.map((x,i)=>'<div class="wrong"><b>Fehler ' + (i+1) + '</b> <span class="pill">' + esc(x.section) + '</span><p>' + esc(x.q) + '</p><p>Deine Antwort: ' + esc(x.u) + '</p><p>Richtig: ' + esc(x.a) + '</p></div>').join("") : '<p class="ok">Keine Fehler.</p>');
  $("rep").classList.remove("hide");
  $("copyBtn").addEventListener("click", () => { const input = $("lnk"); input.select(); if (navigator.clipboard) navigator.clipboard.writeText(input.value); });
  $("rep").scrollIntoView({behavior:"smooth"});
  historyRender();
}
async function historyRender() {
  let h = localHistory();
  if (sb) {
    try {
      const { data, error } = await sb.rpc("get_deutsch_history", { p_device_id: deviceId });
      if (!error && data && data.length) {
        h = data.map(r => ({ shareId:r.share_id, title:r.test_title, topic:r.topic, len:r.length_label, score:r.score, total:r.total, percent:r.percent, wrong:r.wrong, date:r.created_at, remote:true }));
      }
    } catch (e) { console.error(e); }
  }
  window.currentHist = h;
  $("hist").innerHTML = h.length ? h.map((r,i)=>'<div class="hist"><b>' + esc(r.title) + '</b><br><span class="muted">' + new Date(r.date).toLocaleString() + ' · ' + esc(r.len) + ' · ' + r.score + '/' + r.total + ' · ' + r.percent + '% ' + (r.remote ? '· Supabase' : '· local') + '</span><p><button data-hist="' + i + '">Göster</button></p></div>').join("") : '<p class="muted">Henüz kayıt yok.</p>';
  document.querySelectorAll("[data-hist]").forEach(btn => btn.addEventListener("click", () => { hideAll(); showResult(window.currentHist[Number(btn.dataset.hist)]); }));
}
function showResult(r) {
  $("shared").classList.remove("hide");
  $("so").innerHTML = '<p><b>' + esc(r.title || r.test_title) + '</b></p><p>' + esc(r.topic || '') + '</p><p><b>' + r.score + '/' + r.total + ' richtig – ' + r.percent + '%</b></p>' + ((r.wrong && r.wrong.length) ? r.wrong.map((x,i)=>'<div class="wrong"><b>Fehler ' + (i+1) + '</b><p>' + esc(x.q) + '</p><p>Deine Antwort: ' + esc(x.u) + '</p><p>Richtig: ' + esc(x.a) + '</p></div>').join("") : '<p class="ok">Keine Fehler.</p>');
  $("shared").scrollIntoView({behavior:"smooth"});
}
async function loadShare(id) {
  hideAll();
  if (!sb) { $("shared").classList.remove("hide"); $("so").innerHTML = '<p class="dberr">Bu link Supabase gerektiriyor.</p>'; return; }
  const { data, error } = await sb.rpc("get_deutsch_result", { p_share_id:id });
  if (error || !data || !data.length) { $("shared").classList.remove("hide"); $("so").innerHTML = '<p class="dberr">Sonuç bulunamadı.</p>'; return; }
  showResult(data[0]);
}
function clearLocal() { if (confirm("Bu cihazdaki local geçmiş silinsin mi?")) { localStorage.removeItem(STORAGE_KEY); historyRender(); } }
function startHangman() {
  const test = window.DEUTSCH_TESTS[selected];
  hangWords = shuffle(test.hang);
  hangIndex = 0;
  hangScore = 0;
  hideAll();
  $("hang").classList.remove("hide");
  $("ht").textContent = "Adam asmaca: " + test.title;
  showHang();
}
function showHang() {
  const word = hangWords[hangIndex] || "";
  $("hh").textContent = (hangIndex+1) + "/" + hangWords.length + " · Begriff vollständig schreiben";
  $("hm").textContent = word.replace(/[A-Za-zÄÖÜäöüß]/g, "_");
  $("hi").value = "";
  $("hi").className = "";
  $("hr").innerHTML = "";
}
function checkHang() {
  const word = hangWords[hangIndex] || "";
  const user = $("hi").value;
  const ok = norm(user) === norm(word);
  $("hi").classList.add(ok ? "ok" : "no");
  if (ok) hangScore++;
  $("hr").innerHTML = ok ? '<p class="dbok">Richtig.</p>' : '<p class="dberr">Falsch. Richtig: <b>' + esc(word) + '</b></p>';
}
function nextHang() {
  if (hangIndex < hangWords.length - 1) {
    hangIndex++;
    showHang();
  } else {
    $("hr").innerHTML = '<p><b>Fertig: ' + hangScore + '/' + hangWords.length + '</b></p><button id="hangRestart">Neu starten</button>';
    $("hangRestart").addEventListener("click", startHangman);
  }
}
function downloadReport() {
  if (!results.length) { grade(); return; }
  const wrong = results.filter(r => !r.ok);
  const lines = ["Deutsch Tests 1 Bericht", meta.title, ""];
  wrong.forEach((x,i) => lines.push((i+1)+". "+x.q, "Deine Antwort: "+x.u, "Richtig: "+x.a, ""));
  const blob = new Blob([lines.join("\n")], {type:"text/plain;charset=utf-8"});
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = "deutsch_tests_bericht.txt";
  a.click();
  URL.revokeObjectURL(a.href);
}
document.addEventListener("DOMContentLoaded", () => {
  try {
    init();
    if (location.hash.startsWith("#result=")) { hideAll(); showResult(decodeResult(location.hash.slice(8))); }
    if (location.hash.startsWith("#share=")) { loadShare(location.hash.slice(7)); }
  } catch (e) {
    console.error(e);
    $("testList").innerHTML = '<p class="dberr">Uygulama başlatılamadı: ' + esc(e.message) + '</p>';
  }
});
