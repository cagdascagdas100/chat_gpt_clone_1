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
  function runGuards(){
    try{ if(window.__ensureAllLongLessons1500) window.__ensureAllLongLessons1500(); }catch(e){}
    try{ if(window.__ensureAllLongLessons1500Final) window.__ensureAllLongLessons1500Final(); }catch(e){}
    try{ if(window.__boostSatzmuster2Source) window.__boostSatzmuster2Source(); }catch(e){}
    try{ if(window.__edgeReaderEnhanceLesson) window.__edgeReaderEnhanceLesson(); }catch(e){}
  }
  function loadOnlineNachteile(){
    if(window.DEUTSCH_TESTS && window.DEUTSCH_TESTS.t38){rerender();return;}
    loadScript('data_bevor_online_studium_nachteile.js?v=6',function(){runGuards();rerender();});
  }
  function loadSatzmuster2(){
    loadScript('data_grammar_satzmuster2_full.js?v=3',function(){
      loadScript('t37_satzmuster2_source_boost.js?v=1',function(){runGuards();rerender();});
    });
  }
  function loadReaderSupport(){
    if(window.__edgeReaderEnhanceLesson){runGuards();return;}
    loadScript('edge_reader_support.js?v=1',function(){runGuards();});
  }
  loadOnlineNachteile();
  setTimeout(loadSatzmuster2,0);
  setTimeout(loadReaderSupport,0);
  document.addEventListener('DOMContentLoaded',function(){setTimeout(loadOnlineNachteile,100);setTimeout(loadSatzmuster2,150);setTimeout(loadReaderSupport,180);setTimeout(runGuards,500);setTimeout(rerender,650);});
  setTimeout(loadOnlineNachteile,500);
  setTimeout(loadSatzmuster2,700);
  setTimeout(loadReaderSupport,750);
  setTimeout(runGuards,1300);
  setTimeout(rerender,1500);
})();
