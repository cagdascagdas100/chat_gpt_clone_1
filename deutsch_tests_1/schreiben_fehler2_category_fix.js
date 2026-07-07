(function(){
'use strict';
function patchCatOf(){try{catOf=function(t){return t&&t.category?t.category:'Schreiben Fehlern'};window.catOf=catOf;window.AAYS_SF2_CATOF_PATCH_OK=true;}catch(e){}}
function load(src,flag,cb){if(window[flag]){if(cb)cb();return;}window[flag]=true;var s=document.createElement('script');s.src=src;s.async=false;s.onload=function(){if(cb)cb();};(document.head||document.documentElement).appendChild(s);}
function loadSf2(cb){var n=25;function done(){n--;if(n<=0&&cb)cb();}
load('data_schreiben_fehler2_kaliplar_praep_nvv.js?v=5','AAYS_SF2_1_CORE_FORCE_OK',done);
load('data_schreiben_fehler2_kaliplar_praep_nvv_long.js?v=5','AAYS_SF2_1_LONG_FORCE_OK',done);
load('data_schreiben_fehler2_medien_wirtschaft_praep_nvv.js?v=6','AAYS_SF2_2_CORE_FORCE_OK',done);
load('data_schreiben_fehler2_medien_wirtschaft_praep_nvv_long.js?v=5','AAYS_SF2_2_LONG_FORCE_OK',done);
load('data_schreiben_fehler3_sprachfehler_praep_nvv.js?v=1','AAYS_SF2_3_SOURCE_FORCE_OK',done);
load('sf2_4_pure_de_1500_final.js?v=2','AAYS_SF2_4_PURE_DE_1500_FORCE_OK',done);
load('data_schreiben_fehler5_core.js?v=1','AAYS_SF2_5_CORE_FORCE_OK',done);
load('data_schreiben_fehler5_mindestlohn_mehrsprachigkeit.js?v=1','AAYS_SF2_5_MIND_MEHR_FORCE_OK',done);
load('data_schreiben_fehler6_schulsprache_auslandsstudium_autonome_fahrzeuge.js?v=1','AAYS_SF2_6_SOURCE_FORCE_OK',done);
load('data_schreiben_fehler7_autonome_fahrzeuge_recherche_ebooks_praep_nvv.js?v=1','AAYS_SF2_7_SOURCE_FORCE_OK',done);
load('data_schreiben_fehler7_docx1_source_marker.js?v=1','AAYS_SF2_7_DOCX1_MARKER_FORCE_OK',done);
load('data_schreiben_fehler8_ebooks_massentourismus_alltag.js?v=1','AAYS_SF2_8_SOURCE_FORCE_OK',done);
load('data_schreiben_fehler9_fertiggerichte_online_studium_core.js?v=1','AAYS_SF2_9_CORE_FORCE_OK',done);
load('data_schreiben_fehler9_long1.js?v=1','AAYS_SF2_9_LONG1_FORCE_OK',done);
load('data_schreiben_fehler9_long2.js?v=1','AAYS_SF2_9_LONG2_FORCE_OK',done);
load('data_schreiben_fehler9_long3.js?v=1','AAYS_SF2_9_LONG3_FORCE_OK',done);
load('data_schreiben_fehler9_long4.js?v=1','AAYS_SF2_9_LONG4_FORCE_OK',done);
load('data_schreiben_fehler9_long5.js?v=1','AAYS_SF2_9_LONG5_FORCE_OK',done);
load('data_schreiben_fehler9_long6.js?v=1','AAYS_SF2_9_LONG6_FORCE_OK',done);
load('data_schreiben_fehler9_long7.js?v=1','AAYS_SF2_9_LONG7_FORCE_OK',done);
load('sf2_9_long8.js?v=1','AAYS_SF2_9_LONG8_FORCE_OK',done);
load('sf2_9_long9.js?v=1','AAYS_SF2_9_LONG9_FORCE_OK',done);
load('sf2_9_long10.js?v=1','AAYS_SF2_9_LONG10_FORCE_OK',done);
load('data_schreiben_fehler10_meinungsfreiheit_anonymitaet_vorbilder_zeitmanagement.js?v=1','AAYS_SF2_10_SOURCE_FORCE_OK',done);
load('data_schreiben_fehler11_freizeit_haustiere_hilfsprogramme_ki.js?v=1','AAYS_SF2_11_SOURCE_FORCE_OK',done);}
function openSf2(){patchCatOf();loadSf2(function(){patchCatOf();setTimeout(function(){try{renderTests('Schreiben Fehler 2');window.AAYS_SF2_RENDER_FORCED_OK=true;}catch(e){}},100);});}
function bind(){patchCatOf();var b=document.getElementById('catWrite2');if(b&&!b.__aaysSf2Fixed){b.__aaysSf2Fixed=true;b.onclick=function(ev){if(ev){ev.preventDefault();ev.stopPropagation();}openSf2();return false;};}}
var oldRender=window.renderTests;try{if(typeof renderTests==='function'){oldRender=renderTests;renderTests=function(cat){patchCatOf();return oldRender.apply(this,arguments);};window.renderTests=renderTests;}}catch(e){}
document.addEventListener('DOMContentLoaded',function(){patchCatOf();loadSf2(function(){window.AAYS_SF2_11_PRELOAD_FORCE_OK=true;});bind();setTimeout(bind,300);setTimeout(bind,1200);});
document.addEventListener('click',function(ev){var t=ev.target&&ev.target.closest&&ev.target.closest('#catWrite2');if(t){ev.preventDefault();ev.stopPropagation();openSf2();return false;}},true);
if(document.readyState!=='loading'){patchCatOf();loadSf2(function(){window.AAYS_SF2_11_PRELOAD_FORCE_OK=true;});bind();setTimeout(bind,300);}
})();