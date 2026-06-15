(function(){
  function rerender(){
    try{
      if(typeof renderTests==='function' && window.selectedCategory==='Bevor Schreiben') renderTests('Bevor Schreiben');
      else if(typeof renderCategoryChoice==='function') renderCategoryChoice();
    }catch(e){console.error('online_studium_nachteile rerender failed',e)}
  }
  function load(){
    if(window.DEUTSCH_TESTS && window.DEUTSCH_TESTS.t38){rerender();return;}
    var s=document.createElement('script');
    s.src='data_bevor_online_studium_nachteile.js?v=3';
    s.onload=function(){rerender();};
    s.onerror=function(){console.error('data_bevor_online_studium_nachteile.js could not be loaded');};
    document.head.appendChild(s);
  }
  load();
  document.addEventListener('DOMContentLoaded',function(){setTimeout(load,100);setTimeout(rerender,300);});
  setTimeout(load,500);
  setTimeout(rerender,900);
})();
