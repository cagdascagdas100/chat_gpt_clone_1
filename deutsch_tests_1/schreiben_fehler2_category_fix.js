(function(){
'use strict';
function patchCatOf(){
  try{
    catOf=function(t){return t&&t.category?t.category:'Schreiben Fehlern'};
    window.catOf=catOf;
    window.AAYS_SF2_CATOF_PATCH_OK=true;
  }catch(e){}
}
function load(src,flag,cb){
  if(window[flag]){if(cb)cb();return;}
  window[flag]=true;
  var s=document.createElement('script');
  s.src=src;
  s.async=false;
  s.onload=function(){if(cb)cb();};
  (document.head||document.documentElement).appendChild(s);
}
function loadSf2(cb){
  var n=4;
  function done(){n--;if(n<=0&&cb)cb();}
  load('data_schreiben_fehler2_kaliplar_praep_nvv.js?v=5','AAYS_SF2_1_CORE_FORCE_OK',done);
  load('data_schreiben_fehler2_kaliplar_praep_nvv_long.js?v=5','AAYS_SF2_1_LONG_FORCE_OK',done);
  load('data_schreiben_fehler2_medien_wirtschaft_praep_nvv.js?v=5','AAYS_SF2_2_CORE_FORCE_OK',done);
  load('data_schreiben_fehler2_medien_wirtschaft_praep_nvv_long.js?v=5','AAYS_SF2_2_LONG_FORCE_OK',done);
}
function openSf2(){
  patchCatOf();
  loadSf2(function(){
    patchCatOf();
    setTimeout(function(){
      try{renderTests('Schreiben Fehler 2');window.AAYS_SF2_RENDER_FORCED_OK=true;}catch(e){}
    },100);
  });
}
function bind(){
  patchCatOf();
  var b=document.getElementById('catWrite2');
  if(b&&!b.__aaysSf2Fixed){
    b.__aaysSf2Fixed=true;
    b.onclick=function(ev){if(ev){ev.preventDefault();ev.stopPropagation();}openSf2();return false;};
  }
}
var oldRender=window.renderTests;
try{
  if(typeof renderTests==='function'){
    oldRender=renderTests;
    renderTests=function(cat){patchCatOf();return oldRender.apply(this,arguments);};
    window.renderTests=renderTests;
  }
}catch(e){}
document.addEventListener('DOMContentLoaded',function(){patchCatOf();loadSf2(function(){window.AAYS_SF2_PRELOAD_FORCE_OK=true;});bind();setTimeout(bind,300);setTimeout(bind,1200);});
document.addEventListener('click',function(ev){var t=ev.target&&ev.target.closest&&ev.target.closest('#catWrite2');if(t){ev.preventDefault();ev.stopPropagation();openSf2();return false;}},true);
if(document.readyState!=='loading'){patchCatOf();loadSf2(function(){window.AAYS_SF2_PRELOAD_FORCE_OK=true;});bind();setTimeout(bind,300);}
})();