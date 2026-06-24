/* Strict main menu: only 5 main headings are shown on the start page.
   Topic buttons stay inside their real category, especially Bevor Schreiben / Bewerbungsschreiben. */
(function(){
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

  function esc(s){
    return String(s == null ? '' : s).replace(/[&<>']/g,function(c){return {'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#039;'}[c];});
  }
  function el(id){ return document.getElementById(id); }
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

  function renderStrictMainMenu(){
    var list = el('testList');
    if (!list) return;
    try { window.selectedCategory = ''; window.selected = ''; } catch(e) {}
    try { if (typeof setControls === 'function') setControls(false); else setModeControls(false); } catch(e) { setModeControls(false); }
    list.innerHTML =
      '<h2>İlk olarak ana başlığı seç</h2>' +
      '<p class="muted">Ana menüde sadece 5 ana başlık gösterilir. Alt konu başlıkları kendi ana bölümünün içine girince görünür.</p>' +
      '<div id="strictMainGrid" style="display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:12px;margin-top:12px">' +
      MAIN_CARDS.map(cardHtml).join('') +
      '</div>';

    MAIN_CARDS.forEach(function(card){
      if (!card.cat) return;
      var b = el(card.id);
      if (b) b.onclick = function(){
        if (typeof renderTests === 'function') renderTests(card.cat);
      };
    });
  }

  window.renderCategoryChoice = renderStrictMainMenu;

  function sanitizeStartMenu(){
    var list = el('testList');
    if (!list) return;
    var grid = el('strictMainGrid');
    if (!grid) {
      renderStrictMainMenu();
      return;
    }
    Array.prototype.slice.call(grid.children).forEach(function(node){
      if (!/^cat(Test|Grammar|Write|NVV|Before)$/.test(node.id || '')) node.remove();
    });
  }

  document.addEventListener('DOMContentLoaded', function(){
    renderStrictMainMenu();
    setTimeout(sanitizeStartMenu, 300);
    setTimeout(sanitizeStartMenu, 900);
  });
  if (document.readyState !== 'loading') {
    renderStrictMainMenu();
    setTimeout(sanitizeStartMenu, 300);
  }
})();
