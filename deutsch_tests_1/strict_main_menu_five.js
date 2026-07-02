/* Strict main menu black heading bootstrap: keeps previous strict menu/source locks and forces visible card headings to black. */
(function(){
  'use strict';
  if(!window.AAYS_STRICT_MAIN_MENU_PRE_BLACK_LOADER_OK){
    window.AAYS_STRICT_MAIN_MENU_PRE_BLACK_LOADER_OK=true;
    document.write('<script src="https://rawcdn.githack.com/cagdascagdas100/chat_gpt_clone_1/e8d0737003a0f459fea7a8df8e207fb8d4e9e6bd/deutsch_tests_1/strict_main_menu_five.js?v=preBlack"><\/script>');
  }
  function addStyle(){
    var st=document.getElementById('aays-main-card-black-final-style');
    if(!st){
      st=document.createElement('style');
      st.id='aays-main-card-black-final-style';
      st.textContent='#testList #strictMainGrid .opt,#testList #strictMainGrid .opt b,#testList #strictMainGrid .opt strong,#testList #catTest b,#testList #catGrammar b,#testList #catWrite b,#testList #catNVV b,#testList #catBefore b{color:#111827!important;text-shadow:none!important;opacity:1!important;}#testList #strictMainGrid .opt .muted,#testList #catTest .muted,#testList #catGrammar .muted,#testList #catWrite .muted,#testList #catNVV .muted,#testList #catBefore .muted{color:#4b5563!important;text-shadow:none!important;opacity:1!important;}';
      (document.head||document.documentElement).appendChild(st);
    }
  }
  function forceBlack(){
    addStyle();
    ['catTest','catGrammar','catWrite','catNVV','catBefore'].forEach(function(id){
      var n=document.getElementById(id);
      if(!n)return;
      try{n.style.setProperty('color','#111827','important');n.style.setProperty('text-shadow','none','important');n.style.setProperty('opacity','1','important');}catch(e){}
      Array.prototype.slice.call(n.querySelectorAll('b,strong')).forEach(function(x){
        try{x.style.setProperty('color','#111827','important');x.style.setProperty('text-shadow','none','important');x.style.setProperty('opacity','1','important');}catch(e){}
      });
      Array.prototype.slice.call(n.querySelectorAll('.muted,span')).forEach(function(x){
        try{x.style.setProperty('color','#4b5563','important');x.style.setProperty('text-shadow','none','important');x.style.setProperty('opacity','1','important');}catch(e){}
      });
    });
    window.AAYS_MAIN_MENU_HEADINGS_BLACK_FORCED_OK=true;
  }
  addStyle();
  document.addEventListener('DOMContentLoaded',function(){forceBlack();[50,150,300,700,1200,2000].forEach(function(ms){setTimeout(forceBlack,ms);});});
  if(document.readyState!=='loading'){forceBlack();[50,150,300,700,1200,2000].forEach(function(ms){setTimeout(forceBlack,ms);});}
  setInterval(forceBlack,1200);
})();