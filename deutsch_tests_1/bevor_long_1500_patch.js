(function(){
'use strict';
window.DEUTSCH_LESSONS=window.DEUTSCH_LESSONS||{};
window.DEUTSCH_TESTS=window.DEUTSCH_TESTS||{};
if(!window.AAYS_HOME_HEADINGS_BLACK_STYLE_OK){
  window.AAYS_HOME_HEADINGS_BLACK_STYLE_OK=true;
  try{
    var st=document.getElementById('aays-home-headings-black-style');
    if(!st){
      st=document.createElement('style');
      st.id='aays-home-headings-black-style';
      st.textContent='#start h2,#testList h2,#testList .opt,#testList .opt b,#testList .opt strong{color:#111827!important;}#testList .opt .muted{color:#374151!important;}';
      (document.head||document.documentElement).appendChild(st);
    }
  }catch(e){}
}
if(!window.AAYS_PRE_T50_BEVOR_PATCH_OK){
  window.AAYS_PRE_T50_BEVOR_PATCH_OK=true;
  document.write('<script src="https://rawcdn.githack.com/cagdascagdas100/chat_gpt_clone_1/712b59d07c4119e441992cc5b0f5e3ca0c460631/deutsch_tests_1/bevor_long_1500_patch.js?v=preT50"><\/script>');
}
if(!window.AAYS_MASCHINEN_VORTEILE_LOADER_OK){
  window.AAYS_MASCHINEN_VORTEILE_LOADER_OK=true;
  document.write('<script src="data_bevor_maschinen_vorteile.js?v=1"><\/script>');
}
if(!window.AAYS_MASCHINEN_NACHTEILE_LOADER_OK){
  window.AAYS_MASCHINEN_NACHTEILE_LOADER_OK=true;
  document.write('<script src="data_bevor_maschinen_nachteile.js?v=1"><\/script>');
}
if(!window.AAYS_MASCHINEN_NACHTEILE_EXPAND_LOADER_OK){
  window.AAYS_MASCHINEN_NACHTEILE_EXPAND_LOADER_OK=true;
  document.write('<script src="data_bevor_maschinen_nachteile_expand.js?v=1"><\/script>');
}
if(!window.AAYS_KI_ARBEITSPLATZ_VORTEILE_LOADER_OK){
  window.AAYS_KI_ARBEITSPLATZ_VORTEILE_LOADER_OK=true;
  document.write('<script src="data_bevor_ki_arbeitsplatz_vorteile.js?v=1"><\/script>');
}
if(!window.AAYS_KI_ARBEITSPLATZ_VORTEILE_EXPAND_LOADER_OK){
  window.AAYS_KI_ARBEITSPLATZ_VORTEILE_EXPAND_LOADER_OK=true;
  document.write('<script src="data_bevor_ki_arbeitsplatz_vorteile_expand.js?v=1"><\/script>');
}
window.AAYS_MASCHINEN_VORTEILE_BOOTSTRAP_OK=true;
window.AAYS_MASCHINEN_NACHTEILE_BOOTSTRAP_OK=true;
window.AAYS_KI_ARBEITSPLATZ_VORTEILE_BOOTSTRAP_OK=true;
window.AAYS_HOME_HEADINGS_BLACK_OK=true;
})();