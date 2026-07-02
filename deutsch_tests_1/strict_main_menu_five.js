/* Stable strict main menu: no chained document.write, no interval redraw flicker. */
(function(){
  'use strict';
  var MAIN_CARDS=[
    {id:'catTest',kind:'link',href:'./erorterung_tests.html?v=erorterung-8a3d0618c',title:'Test',desc:'C1/C2 Erörterung test sistemini aç.'},
    {id:'catGrammar',cat:'Genel Grammer',title:'Genel Grammar',desc:'Satzbau, Kasus, Artikel, Pronomen, Negation ve doğru gramerle yazma.'},
    {id:'catWrite',cat:'Schreiben Fehlern',title:'Schreiben Fehler',desc:'Kelime, kalıp, Präposition ve C1/C2 yazma hatası testleri.'},
    {id:'catNVV',cat:'NVV',title:'NVV',desc:'Nomen-Verb-Verbindungen ve akademik yazma kalıpları.'},
    {id:'catBefore',cat:'Bevor Schreiben',title:'Bevor Schreiben / Bewerbungsschreiben',desc:'Selbstfahrende Autos: C1/C2 Vorteilsabsatz, Redemittel, NVV ve yazma hazırlığı dahil tüm Vorteile/Nachteile konu anlatımları burada.'}
  ];
  var MAIN_IDS={catTest:1,catGrammar:1,catWrite:1,catNVV:1,catBefore:1};
  var observerInstalled=false, pending=false;
  function esc(s){return String(s==null?'':s).replace(/[&<>']/g,function(c){return {'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#039;'}[c];});}
  function el(id){return document.getElementById(id);}
  function isHidden(node){return !node||node.classList.contains('hide');}
  function showOnlyStart(){return isHidden(el('quiz'))&&isHidden(el('lesson'))&&isHidden(el('hang'));}
  function setModeControls(show){var c=el('modeControls');if(c)c.classList.toggle('hide',!show);}
  function addStyle(){
    var st=el('aays-stable-menu-no-flicker-style');
    if(!st){
      st=document.createElement('style');
      st.id='aays-stable-menu-no-flicker-style';
      st.textContent='body.aays-menu-rendering #testList{visibility:hidden!important;}#strictMainGrid .opt,#strictMainGrid .opt b,#strictMainGrid .opt strong{color:#111827!important;text-shadow:none!important;opacity:1!important;}#strictMainGrid .muted,#artikelMenuCard .muted{color:#4b5563!important;text-shadow:none!important;opacity:1!important;}#artikelMenuCard h2,#artikelMenuCard b,#artikelMenuCard strong{color:#111827!important;text-shadow:none!important;opacity:1!important;}';
      (document.head||document.documentElement).appendChild(st);
    }
  }
  function cardHtml(card){
    var title='<b style="color:#111827!important;text-shadow:none!important;opacity:1!important">'+esc(card.title)+'</b>';
    var desc='<span class="muted" style="color:#4b5563!important;text-shadow:none!important;opacity:1!important">'+esc(card.desc)+'</span>';
    var inner=title+'<br>'+desc;
    if(card.kind==='link')return '<a class="opt" id="'+esc(card.id)+'" href="'+esc(card.href)+'" style="text-align:left;display:block;text-decoration:none;color:#111827!important">'+inner+'</a>';
    return '<button class="opt" style="text-align:left;color:#111827!important" id="'+esc(card.id)+'">'+inner+'</button>';
  }
  function preserveArtikelNode(list){var a=el('artikelMenuCard');return a&&a.parentNode===list?a:null;}
  function bindMainCardClicks(){
    MAIN_CARDS.forEach(function(card){
      if(!card.cat)return;
      var b=el(card.id);
      if(b)b.onclick=function(){
        window.__strictMainMenuActive=false;
        try{document.body.classList.add('aays-menu-ready');}catch(e){}
        if(typeof window.renderTests==='function')window.renderTests(card.cat);
        else if(typeof renderTests==='function')renderTests(card.cat);
      };
    });
  }
  function renderStrictMainMenu(){
    addStyle();
    var list=el('testList');if(!list)return;
    var artikel=preserveArtikelNode(list);
    try{document.body.classList.add('aays-menu-rendering');}catch(e){}
    window.__strictMainMenuActive=true;
    try{window.selectedCategory='';window.selected='';}catch(e){}
    try{if(typeof window.setControls==='function')window.setControls(false);else if(typeof setControls==='function')setControls(false);else setModeControls(false);}catch(e){setModeControls(false);}
    list.innerHTML='<h2 style="color:#111827!important;text-shadow:none!important;opacity:1!important">İlk olarak ana başlığı seç</h2>'+
      '<p class="muted" style="color:#4b5563!important;text-shadow:none!important;opacity:1!important">Ana menüde sadece 5 ana başlık gösterilir. Alt konu başlıkları kendi ana bölümünün içine girince görünür.</p>'+
      '<div id="strictMainGrid" style="display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:12px;margin-top:12px">'+MAIN_CARDS.map(cardHtml).join('')+'</div>';
    if(artikel)list.appendChild(artikel);
    bindMainCardClicks();
    try{document.body.classList.remove('aays-menu-rendering');document.body.classList.add('aays-menu-ready');}catch(e){}
    window.AAYS_STABLE_MAIN_MENU_RENDERED_OK=true;
  }
  function gridIsDirty(){
    var grid=el('strictMainGrid');if(!grid)return true;
    for(var id in MAIN_IDS){if(!el(id))return true;}
    var list=el('testList'),text=list?String(list.textContent||''):'';
    if(text.indexOf('Individualität – Nachteile')>-1||text.indexOf('Lebenslanges Lernen – Nachteile')>-1||text.indexOf('Werbung – Nachteile · Medien-Einfluss')>-1)return true;
    return false;
  }
  function sanitizeStartMenu(){
    if(pending)return;
    var list=el('testList');if(!list||!showOnlyStart())return;
    if(window.__strictMainMenuActive===false)return;
    if(!gridIsDirty()){bindMainCardClicks();try{document.body.classList.add('aays-menu-ready');}catch(e){}return;}
    pending=true;
    try{document.body.classList.add('aays-menu-rendering');}catch(e){}
    setTimeout(function(){pending=false;renderStrictMainMenu();},0);
  }
  window.renderCategoryChoice=function(){renderStrictMainMenu();};
  function installObserver(){
    if(observerInstalled)return;
    var list=el('testList');if(!list||!window.MutationObserver)return;
    observerInstalled=true;
    new MutationObserver(function(){if(window.__strictMainMenuActive!==false)setTimeout(sanitizeStartMenu,0);}).observe(list,{childList:true,subtree:true,characterData:true});
  }
  function boot(){addStyle();renderStrictMainMenu();installObserver();[60,180,420,900].forEach(function(ms){setTimeout(sanitizeStartMenu,ms);});}
  document.addEventListener('DOMContentLoaded',boot);
  if(document.readyState!=='loading')boot();
  window.AAYS_NO_FLICKER_STRICT_MENU_OK=true;
  window.AAYS_ARTIKEL_CARD_PRESERVED_BY_STABLE_MENU_OK=true;
})();