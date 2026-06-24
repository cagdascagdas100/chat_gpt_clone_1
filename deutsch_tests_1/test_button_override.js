/* C1/C2 Erörterung-Testsystem: mevcut ana menüyü bozmadan "Test" başlığını ekler. */
(function(){
  const TEST_URL = './erorterung_tests.html?v=stable1';
  const TITLE_BY_ID = {
    catGrammar: 'Genel Grammar',
    catWrite: 'Schreiben Fehler',
    catNVV: 'NVV',
    catBefore: 'Beworschreiben / Bewerbungsschreiben'
  };

  function byId(id){ return document.getElementById(id); }

  function normalizeExistingTitles(){
    Object.keys(TITLE_BY_ID).forEach(function(id){
      const button = byId(id);
      if (!button) return;
      const titleNode = button.querySelector('b,strong') || button;
      titleNode.textContent = TITLE_BY_ID[id];
    });
  }

  function buildTestEntry(){
    const a = document.createElement('a');
    a.id = 'catTest';
    a.href = TEST_URL;
    a.className = 'opt';
    a.style.textAlign = 'left';
    a.style.display = 'block';
    a.style.textDecoration = 'none';
    a.style.color = 'inherit';
    a.innerHTML = '<b>Test</b><br><span class="muted">C1/C2 Erörterung test sistemini aç.</span>';
    return a;
  }

  function appendTestEntry(){
    const oldExternal = byId('catExternalTests');
    if (oldExternal && oldExternal.parentNode) oldExternal.parentNode.removeChild(oldExternal);

    const existing = byId('catTest');
    if (existing) {
      existing.href = TEST_URL;
      return;
    }

    const grammar = byId('catGrammar');
    const list = byId('testList');
    const container = grammar && grammar.parentElement ? grammar.parentElement : (list ? list.querySelector('div') : null);
    if (!container) return;
    container.appendChild(buildTestEntry());
  }

  function renderFallbackMenu(){
    const list = byId('testList');
    if (!list) return;

    list.innerHTML =
      '<h2>İlk olarak ana başlığı seç</h2>' +
      '<p class="muted">Önce çalışma alanını seç. Sonra ilgili testleri, konu anlatımını veya harf kutucukları modunu açabilirsin.</p>' +
      '<div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:12px;margin-top:12px">' +
      '<button class="opt" style="text-align:left" id="catGrammar"><b>Genel Grammar</b><br><span class="muted">Satzbau, Kasus, Artikel, Pronomen, Negation ve doğru gramerle yazma.</span></button>' +
      '<button class="opt" style="text-align:left" id="catWrite"><b>Schreiben Fehler</b><br><span class="muted">Kelime, kalıp, Präposition ve C1/C2 yazma hatası testleri.</span></button>' +
      '<button class="opt" style="text-align:left" id="catNVV"><b>NVV</b><br><span class="muted">Nomen-Verb-Verbindungen.</span></button>' +
      '<button class="opt" style="text-align:left" id="catBefore"><b>Beworschreiben / Bewerbungsschreiben</b><br><span class="muted">Yazma öncesi konu hazırlığı, Vorteile/Nachteile ve C1/C2 Redemittel.</span></button>' +
      '</div>';

    if (byId('catGrammar')) byId('catGrammar').onclick = function(){ renderTests('Genel Grammer'); };
    if (byId('catWrite')) byId('catWrite').onclick = function(){ renderTests('Schreiben Fehlern'); };
    if (byId('catNVV')) byId('catNVV').onclick = function(){ renderTests('NVV'); };
    if (byId('catBefore')) byId('catBefore').onclick = function(){ renderTests('Bevor Schreiben'); };
  }

  function applyMenuPatch(){
    normalizeExistingTitles();
    appendTestEntry();
  }

  const originalRenderCategoryChoice = window.renderCategoryChoice;

  window.renderCategoryChoice = function(){
    window.selectedCategory = '';
    window.selected = '';

    if (typeof originalRenderCategoryChoice === 'function') {
      originalRenderCategoryChoice.apply(this, arguments);
    } else {
      if (typeof setControls === 'function') {
        try { setControls(false); } catch(e) {}
      }
      renderFallbackMenu();
    }

    applyMenuPatch();
  };

  document.addEventListener('DOMContentLoaded', function(){
    try { window.renderCategoryChoice(); } catch(e) { console.error(e); }
  });

  if (document.readyState !== 'loading') {
    try { applyMenuPatch(); } catch(e) { console.error(e); }
  }
})();
