/* Stable strict main menu: single render only, no observer, no repeated redraw. */
(function(){
  'use strict';
  var MAIN_CARDS=[
    {id:'catTest',kind:'link',href:'./erorterung_tests.html?v=erorterung-8a3d0618c',title:'Test',desc:'C1/C2 Erörterung test sistemini aç.'},
    {id:'catGrammar',cat:'Genel Grammer',title:'Genel Grammar',desc:'Satzbau, Kasus, Artikel, Pronomen, Negation ve doğru gramerle yazma.'},
    {id:'catWrite',cat:'Schreiben Fehlern',title:'Schreiben Fehler',desc:'Kelime, kalıp, Präposition ve C1/C2 yazma hatası testleri.'},
    {id:'catNVV',cat:'NVV',title:'NVV',desc:'Nomen-Verb-Verbindungen ve akademik yazma kalıpları.'},
    {id:'catBefore',cat:'Bevor Schreiben',title:'Bevor Schreiben / Bewerbungsschreiben',desc:'Selbstfahrende Autos: C1/C2 Vorteilsabsatz, Redemittel, NVV ve yazma hazırlığı dahil tüm Vorteile/Nachteile konu anlatımları burada.'}
  ];
  function esc(s){return String(s==null?'':s).replace(/[&<>']/g,function(c){return {'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#039;'}[c];});}
  function el(id){return document.getElementById(id);}
  function setModeControls(show){var c=el('modeControls');if(c)c.classList.toggle('hide',!show);}
  function addStyle(){
    var st=el('aays-stable-menu-no-flicker-style');
    if(!st){
      st=document.createElement('style');
      st.id='aays-stable-menu-no-flicker-style';
      st.textContent='#testList{min-height:280px;}#strictMainGrid .opt,#strictMainGrid .opt b,#strictMainGrid .opt strong{color:#111827!important;text-shadow:none!important;opacity:1!important;}#strictMainGrid .muted,#artikelMenuCard .muted{color:#4b5563!important;text-shadow:none!important;opacity:1!important;}#artikelMenuCard h2,#artikelMenuCard b,#artikelMenuCard strong{color:#111827!important;text-shadow:none!important;opacity:1!important;}';
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
  function bindMainCardClicks(){
    MAIN_CARDS.forEach(function(card){
      if(!card.cat)return;
      var b=el(card.id);
      if(b)b.onclick=function(){
        window.__strictMainMenuActive=false;
        if(typeof window.renderTests==='function')window.renderTests(card.cat);
        else if(typeof renderTests==='function')renderTests(card.cat);
      };
    });
  }
  function renderStrictMainMenu(force){
    addStyle();
    var list=el('testList');if(!list)return;
    if(!force && el('strictMainGrid')){bindMainCardClicks();window.__strictMainMenuActive=true;return;}
    var artikel=el('artikelMenuCard');
    try{window.selectedCategory='';window.selected='';}catch(e){}
    try{if(typeof window.setControls==='function')window.setControls(false);else if(typeof setControls==='function')setControls(false);else setModeControls(false);}catch(e){setModeControls(false);}
    var html='<h2 style="color:#111827!important;text-shadow:none!important;opacity:1!important">İlk olarak ana başlığı seç</h2>'+
      '<p class="muted" style="color:#4b5563!important;text-shadow:none!important;opacity:1!important">Ana menüde sadece 5 ana başlık gösterilir. Alt konu başlıkları kendi ana bölümünün içine girince görünür.</p>'+
      '<div id="strictMainGrid" style="display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:12px;margin-top:12px">'+MAIN_CARDS.map(cardHtml).join('')+'</div>';
    list.innerHTML=html;
    if(artikel)list.appendChild(artikel);
    bindMainCardClicks();
    window.__strictMainMenuActive=true;
    window.AAYS_STABLE_MAIN_MENU_RENDERED_OK=true;
    window.AAYS_HOME_MENU_SINGLE_RENDER_OK=true;
  }
  window.renderCategoryChoice=function(){renderStrictMainMenu(true);};
  function boot(){addStyle();renderStrictMainMenu(false);}
  document.addEventListener('DOMContentLoaded',boot,{once:true});
  if(document.readyState!=='loading')boot();
  window.AAYS_NO_FLICKER_STRICT_MENU_OK=true;
  window.AAYS_ARTIKEL_CARD_PRESERVED_BY_STABLE_MENU_OK=true;
  window.AAYS_HOME_MENU_OBSERVER_REMOVED_OK=true;
})();

/* Loader for KI Arbeitsplatz Nachteile t53: local files only, keeps the fixed URL unchanged. */
(function(){
  'use strict';
  function loadLocal(src,flag){
    if(window[flag])return;
    window[flag]=true;
    var s=document.createElement('script');
    s.src=src;
    s.async=false;
    s.onload=function(){try{if(window.__strictMainMenuActive===false&&typeof window.renderTests==='function')window.renderTests('Bevor Schreiben');}catch(e){}};
    (document.head||document.documentElement).appendChild(s);
  }
  loadLocal('data_bevor_ki_arbeitsplatz_nachteile.js?v=1','AAYS_KI_ARBEITSPLATZ_NACHTEILE_STRICT_LOADER_OK');
  loadLocal('data_bevor_ki_arbeitsplatz_nachteile_expand.js?v=1','AAYS_KI_ARBEITSPLATZ_NACHTEILE_EXPAND_STRICT_LOADER_OK');
  window.AAYS_KI_ARBEITSPLATZ_NACHTEILE_STRICT_BOOTSTRAP_OK=true;
})();