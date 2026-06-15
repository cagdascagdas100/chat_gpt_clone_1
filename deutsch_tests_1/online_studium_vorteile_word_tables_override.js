(function(){
  function rerender(){
    try{
      if(typeof renderTests==='function' && window.selectedCategory==='Bevor Schreiben') renderTests('Bevor Schreiben');
      else if(typeof renderTests==='function' && window.selectedCategory==='Genel Grammer') renderTests('Genel Grammer');
      else if(typeof renderCategoryChoice==='function') renderCategoryChoice();
    }catch(e){console.error('late rerender failed',e)}
  }
  function loadScript(src,done){
    try{
      var s=document.createElement('script');
      s.src=src;
      s.onload=done||function(){};
      s.onerror=function(){console.error(src+' could not be loaded');};
      document.head.appendChild(s);
    }catch(e){console.error('script load failed',src,e)}
  }
  function loadOnlineNachteile(){
    if(window.DEUTSCH_TESTS && window.DEUTSCH_TESTS.t38){rerender();return;}
    loadScript('data_bevor_online_studium_nachteile.js?v=4',rerender);
  }
  function loadSatzmuster2(){
    loadScript('data_grammar_satzmuster2_full.js?v=1',function(){
      try{ if(window.__ensureAllLongLessons1500) window.__ensureAllLongLessons1500(); }catch(e){}
      rerender();
    });
  }
  loadOnlineNachteile();
  setTimeout(loadSatzmuster2,0);
  document.addEventListener('DOMContentLoaded',function(){setTimeout(loadOnlineNachteile,100);setTimeout(loadSatzmuster2,150);setTimeout(rerender,600);});
  setTimeout(loadOnlineNachteile,500);
  setTimeout(loadSatzmuster2,700);
  setTimeout(rerender,1200);
})();