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

/* Possessivartikel I/II ve Deklination I/II: tek kelimelik ipuçlarını kaldıran zor şık patch'i. */
(function(){
  function lower(s){return String(s||'').toLocaleLowerCase('de-DE').replace(/\s+/g,' ').trim();}
  var poss=[
    ['Nach der Prüfung änderte die Behörde ____.','ihre ursprüngliche Einschätzung','ihren ursprünglichen Einschätzung','ihrer ursprünglichen Einschätzung','ihrem ursprünglichen Einschätzung','ihres ursprünglichen Einschätzung'],
    ['Trotz ____ blieb der Beschluss gültig.','seines verspäteten Widerspruchs','seinem verspäteten Widerspruch','seinen verspäteten Widerspruch','sein verspäteter Widerspruch','seine verspätete Widersprüche'],
    ['Die Kommission folgte ____ nur teilweise.','unserer sachlichen Begründung','unsere sachliche Begründung','unseren sachlichen Begründung','unseres sachlichen Begründung','unserem sachliche Begründung'],
    ['Ohne ____ kann der Antrag nicht genehmigt werden.','Ihren schriftlichen Nachweis','Ihrem schriftlichen Nachweis','Ihres schriftlichen Nachweises','Ihr schriftlicher Nachweis','Ihrer schriftlichen Nachweis'],
    ['Die Kritik widerspricht ____.','seinen eigenen Interessen','seine eigenen Interessen','seiner eigenen Interessen','seinem eigenen Interessen','seines eigenen Interesses'],
    ['Angesichts ____ ist eine Neubewertung nötig.','eurer kritischen Einwände','euren kritischen Einwänden','eure kritischen Einwände','eurem kritischen Einwand','eures kritischen Einwands'],
    ['Die Verwaltung kam ____ entgegen.','Ihren berechtigten Forderungen','Ihre berechtigten Forderungen','Ihrer berechtigten Forderungen','Ihres berechtigten Forderungen','Ihrem berechtigten Forderung'],
    ['Wegen ____ wurde die Frist verlängert.','meines früheren Versäumnisses','meinem früheren Versäumnis','mein früheres Versäumnis','meinen früheren Versäumnis','meiner früheren Versäumnisse']
  ];
  var dekl=[
    ['____ wurde die Verordnung geändert.','Wegen neuer gesetzlicher Vorgaben','Wegen neuen gesetzlichen Vorgaben','Mit neuen gesetzlichen Vorgaben','Durch neue gesetzliche Vorgaben','Bei neue gesetzliche Vorgaben'],
    ['____ musste die Studie überarbeitet werden.','Trotz deutlicher methodischer Schwächen','Trotz deutliche methodische Schwächen','Mit deutlichen methodischen Schwächen','Für deutliche methodische Schwächen','Bei deutlicher methodischer Schwächen'],
    ['Die Entscheidung beruht auf ____.','einem nachvollziehbaren fachlichen Gutachten','ein nachvollziehbares fachliches Gutachten','eines nachvollziehbaren fachlichen Gutachtens','einen nachvollziehbaren fachlichen Gutachten','einer nachvollziehbaren fachlichen Gutachten'],
    ['Ohne ____ ist die These nicht haltbar.','ausreichende empirische Belege','ausreichenden empirischen Belegen','ausreichender empirischer Belege','ausreichendem empirischem Belegen','ausreichende empirischen Belege'],
    ['Die Kommission veröffentlichte ____.','die von Experten geprüften Unterlagen','der von Experten geprüften Unterlagen','den von Experten geprüften Unterlagen','die von Experten geprüfte Unterlagen','dem von Experten geprüften Unterlagen'],
    ['Die Bewertung ____ wurde kritisiert.','der von Experten geprüften Unterlagen','die von Experten geprüften Unterlagen','den von Experten geprüften Unterlagen','dem von Experten geprüften Unterlagen','des von Experten geprüften Unterlagen'],
    ['Die Behörde arbeitet mit ____.','den in der Sitzung vorgelegten Anträgen','die in der Sitzung vorgelegten Anträge','der in der Sitzung vorgelegten Anträge','das in der Sitzung vorgelegte Anträge','den in der Sitzung vorgelegte Anträge'],
    ['Erforderlich ist ____.','ein nach transparenten Kriterien entwickeltes Verfahren','eines nach transparenten Kriterien entwickelten Verfahrens','einem nach transparenten Kriterien entwickelten Verfahren','einen nach transparenten Kriterien entwickelten Verfahren','eine nach transparenten Kriterien entwickelte Verfahren']
  ];
  function apply(t,rows,tag){
    t._smartOptions=true;
    t.words=[];
    rows.forEach(function(r){t.words=t.words.concat(r.slice(1));});
    t.fill=rows.map(function(r){return ['Welche vollständige Form passt? '+r[0],r[1],tag];});
    t.mc=rows.map(function(r){return ['Welche Option ist grammatisch korrekt? '+r[0],r.slice(1),0,tag];});
    t.wordMatch=rows.map(function(r){return [r[1],'korrekte vollständige Nominalgruppe im passenden Kasus'];});
    t.phraseMatch=rows.map(function(r){return [r[0].replace('____','...'),r[1]];});
    t.tf=[
      ['Die Lösung muss zur Präposition, zum Verb und zum Kasus der ganzen Nominalgruppe passen.',true,tag],
      ['Bei diesen Aufgaben reicht es nicht, nur auf den letzten Buchstaben zu achten.',true,tag],
      ['Kasus, Artikelwort und Adjektivendung müssen zusammenpassen.',true,tag],
      ['Eine Option ist schon korrekt, wenn nur das Nomen richtig endet.',false,tag]
    ];
    t.prep=[];
  }
  function install(){
    var all=window.DEUTSCH_TESTS||{};
    Object.keys(all).forEach(function(k){
      var t=all[k]||{}, h=lower([k,t.slug,t.title,t.topic].join(' '));
      if(h.indexOf('possessivartikel i')>-1 || h.indexOf('possessivartikel ii')>-1) apply(t,poss,'Possessivartikel');
      if(h.indexOf('deklination i')>-1 || h.indexOf('deklination ii')>-1) apply(t,dekl,'Deklination');
    });
  }
  var oldBuild=(typeof build==='function')?build:null;
  function smartBuild(t,n){
    if(!t||!t._smartOptions||typeof bank!=='function') return oldBuild?oldBuild(t,n):[];
    var g=bank(t), keys=['tf','fill','mc','wordMatch','phraseMatch'], out=[], i=0;
    while(out.length<n && keys.some(function(k){return (g[k]||[]).length;})){
      var a=g[keys[i%keys.length]]||[];
      if(a.length) out.push(a.shift());
      i++;
    }
    return out;
  }
  install();
  try{ if(oldBuild){ window.build=smartBuild; build=smartBuild; } }catch(e){}
  document.addEventListener('DOMContentLoaded', install);
})();