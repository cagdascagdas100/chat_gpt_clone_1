/* Strict main menu final bootstrap: keeps Artikel quiz card, black headings, and hides the unwanted Bevor topic rows shown on the main page. */
(function(){
  'use strict';
  if(!window.AAYS_STRICT_MAIN_MENU_PRE_HIDE_LOADER_OK){
    window.AAYS_STRICT_MAIN_MENU_PRE_HIDE_LOADER_OK=true;
    document.write('<script src="https://rawcdn.githack.com/cagdascagdas100/chat_gpt_clone_1/c84db34e60a1aa5df2c527bfcad858496e2a22e6/deutsch_tests_1/strict_main_menu_five.js?v=preHide"><\/script>');
  }
  var HIDE_TITLES=[
    'Individualität – Nachteile',
    'Lebenslanges Lernen – Nachteile',
    'Werbung – Nachteile · C1/C2 Nachteilsabsatz',
    'Werbung – Nachteile · Medien-Einfluss'
  ];
  function addStyle(){
    var st=document.getElementById('aays-main-menu-hide-photo-topic-rows-style');
    if(!st){
      st=document.createElement('style');
      st.id='aays-main-menu-hide-photo-topic-rows-style';
      st.textContent='[data-aays-main-photo-row-hidden="1"]{display:none!important;}#artikelMenuCard,#artikelMenuCard *{display:revert-layer;}';
      (document.head||document.documentElement).appendChild(st);
    }
  }
  function shouldHide(text){
    text=String(text||'').replace(/\s+/g,' ').trim();
    return HIDE_TITLES.some(function(t){return text.indexOf(t)>-1;});
  }
  function hidePhotoRows(){
    addStyle();
    var list=document.getElementById('testList');
    if(!list)return;
    Array.prototype.slice.call(list.querySelectorAll('.opt,label,button,a,div')).forEach(function(n){
      if(!n || n.id==='artikelMenuCard' || (n.closest&&n.closest('#artikelMenuCard')))return;
      if(n.id==='catTest'||n.id==='catGrammar'||n.id==='catWrite'||n.id==='catNVV'||n.id==='catBefore')return;
      var txt=n.textContent||'';
      if(shouldHide(txt)){
        n.setAttribute('data-aays-main-photo-row-hidden','1');
        try{n.style.setProperty('display','none','important');}catch(e){}
      }
    });
    window.AAYS_MAIN_PHOTO_BEVOR_ROWS_HIDDEN_OK=true;
    window.AAYS_ARTIKEL_CARD_PRESERVE_OK=!!document.getElementById('artikelMenuCard') || window.AAYS_ARTIKEL_QUIZ_MENU_OK===true;
  }
  document.addEventListener('DOMContentLoaded',function(){hidePhotoRows();[50,150,300,700,1200,2000].forEach(function(ms){setTimeout(hidePhotoRows,ms);});});
  if(document.readyState!=='loading'){hidePhotoRows();[50,150,300,700,1200,2000].forEach(function(ms){setTimeout(hidePhotoRows,ms);});}
  setInterval(hidePhotoRows,1000);
})();