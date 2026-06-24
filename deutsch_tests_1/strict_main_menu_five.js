/* Strict main menu: only 5 main headings are shown on the start page.
   Topic buttons stay inside their real category, especially Bevor Schreiben / Bewerbungsschreiben. */
(function(){
  'use strict';

  var MAIN_CARDS = [
    {
      id: 'catTest',
      kind: 'link',
      href: './erorterung_tests.html?v=stable1',
      title: 'Test',
      desc: 'C1/C2 Erörterung test sistemini aç.'
    },
    {
      id: 'catGrammar',
      cat: 'Genel Grammer',
      title: 'Genel Grammar',
      desc: 'Satzbau, Kasus, Artikel, Pronomen, Negation ve doğru gramerle yazma.'
    },
    {
      id: 'catWrite',
      cat: 'Schreiben Fehlern',
      title: 'Schreiben Fehler',
      desc: 'Kelime, kalıp, Präposition ve C1/C2 yazma hatası testleri.'
    },
    {
      id: 'catNVV',
      cat: 'NVV',
      title: 'NVV',
      desc: 'Nomen-Verb-Verbindungen ve akademik yazma kalıpları.'
    },
    {
      id: 'catBefore',
      cat: 'Bevor Schreiben',
      title: 'Bevor Schreiben / Bewerbungsschreiben',
      desc: 'Selbstfahrende Autos: C1/C2 Vorteilsabsatz, Redemittel, NVV ve yazma hazırlığı dahil tüm Vorteile/Nachteile konu anlatımları burada.'
    }
  ];

  var MAIN_IDS = {catTest:1, catGrammar:1, catWrite:1, catNVV:1, catBefore:1};
  var observerInstalled = false;

  function esc(s){
    return String(s == null ? '' : s).replace(/[&<>']/g,function(c){
      return {'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#039;'}[c];
    });
  }
  function el(id){ return document.getElementById(id); }
  function isHidden(node){ return !node || node.classList.contains('hide'); }
  function showOnlyStart(){
    var quiz = el('quiz'), lesson = el('lesson'), hang = el('hang');
    return isHidden(quiz) && isHidden(lesson) && isHidden(hang);
  }
  function setModeControls(show){
    var c = el('modeControls');
    if (c) c.classList.toggle('hide', !show);
  }
  function cardHtml(card){
    var inner = '<b>' + esc(card.title) + '</b><br><span class="muted">' + esc(card.desc) + '</span>';
    if (card.kind === 'link') {
      return '<a class="opt" id="' + esc(card.id) + '" href="' + esc(card.href) + '" style="text-align:left;display:block;text-decoration:none;color:inherit">' + inner + '</a>';
    }
    return '<button class="opt" style="text-align:left" id="' + esc(card.id) + '">' + inner + '</button>';
  }

  function bindMainCardClicks(){
    MAIN_CARDS.forEach(function(card){
      if (!card.cat) return;
      var b = el(card.id);
      if (b) b.onclick = function(){
        window.__strictMainMenuActive = false;
        if (typeof window.renderTests === 'function') window.renderTests(card.cat);
        else if (typeof renderTests === 'function') renderTests(card.cat);
      };
    });
  }

  function renderStrictMainMenu(){
    var list = el('testList');
    if (!list) return;
    window.__strictMainMenuActive = true;
    try { window.selectedCategory = ''; window.selected = ''; } catch(e) {}
    try {
      if (typeof window.setControls === 'function') window.setControls(false);
      else if (typeof setControls === 'function') setControls(false);
      else setModeControls(false);
    } catch(e) { setModeControls(false); }
    list.innerHTML =
      '<h2>İlk olarak ana başlığı seç</h2>' +
      '<p class="muted">Ana menüde sadece 5 ana başlık gösterilir. Alt konu başlıkları kendi ana bölümünün içine girince görünür.</p>' +
      '<div id="strictMainGrid" style="display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:12px;margin-top:12px">' +
      MAIN_CARDS.map(cardHtml).join('') +
      '</div>';
    bindMainCardClicks();
  }

  function gridIsDirty(grid){
    if (!grid) return true;
    var nodes = Array.prototype.slice.call(grid.children).filter(function(n){ return n && n.id; });
    if (nodes.length !== 5) return true;
    for (var i=0;i<nodes.length;i++) {
      if (!MAIN_IDS[nodes[i].id]) return true;
    }
    var before = el('catBefore');
    if (!before || before.textContent.indexOf('Selbstfahrende Autos: C1/C2 Vorteilsabsatz') === -1) return true;
    return false;
  }

  function sanitizeStartMenu(){
    var list = el('testList');
    if (!list || !showOnlyStart()) return;
    if (window.__strictMainMenuActive === false) return;
    var grid = el('strictMainGrid');
    if (gridIsDirty(grid)) renderStrictMainMenu();
    else bindMainCardClicks();
  }

  window.renderCategoryChoice = function(){
    renderStrictMainMenu();
  };

  function installObserver(){
    if (observerInstalled) return;
    var list = el('testList');
    if (!list || !window.MutationObserver) return;
    observerInstalled = true;
    var obs = new MutationObserver(function(){
      if (window.__strictMainMenuActive !== false) {
        setTimeout(sanitizeStartMenu, 0);
      }
    });
    obs.observe(list, {childList:true, subtree:true, characterData:true});
  }

  document.addEventListener('DOMContentLoaded', function(){
    renderStrictMainMenu();
    installObserver();
    [50,150,300,700,1200,2000].forEach(function(ms){ setTimeout(sanitizeStartMenu, ms); });
  });

  if (document.readyState !== 'loading') {
    renderStrictMainMenu();
    installObserver();
    [50,150,300,700,1200,2000].forEach(function(ms){ setTimeout(sanitizeStartMenu, ms); });
  }

  setInterval(function(){
    if (window.__strictMainMenuActive !== false) sanitizeStartMenu();
  }, 1200);
})();
