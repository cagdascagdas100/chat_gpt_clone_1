(function(){
'use strict';
if(window.AAYS_SCHLAFMANGEL_RUNTIME_LOADER_V2_INSTALLED)return;
window.AAYS_SCHLAFMANGEL_RUNTIME_LOADER_V2_INSTALLED=true;
var KEY='schlafmangel_studierende_ursachen_folgen_loesungen_c1c2';
var files=[
'data_bevor_schlafmangel_00_base.js',
'data_bevor_schlafmangel_01_questions.js',
'data_bevor_schlafmangel_02_questions.js',
'data_bevor_schlafmangel_03_questions_lessons.js',
'data_bevor_schlafmangel_04_long.js',
'data_bevor_schlafmangel_05_long.js',
'data_bevor_schlafmangel_06_long.js',
'data_bevor_schlafmangel_07_finalize.js'
];
var running=false;
function ready(){var t=(window.DEUTSCH_TESTS||{})[KEY],l=(window.DEUTSCH_LESSONS||{})[KEY];return !!(t&&t.title&&t.fill&&t.mc&&t.tf&&t.wordMatch&&t.phraseMatch&&t.prep&&t.hang&&l&&l.short&&l.medium&&l.long)}
function redraw(){if(typeof window.renderTests==='function'){try{window.renderTests('Bevor Schreiben')}catch(e){console.error(e)}}}
function loadAt(i){
 if(i>=files.length){running=false;window.AAYS_SCHLAFMANGEL_RUNTIME_DATA_READY=ready();redraw();return}
 var src=files[i],existing=document.querySelector('script[data-sleep-runtime="'+src+'"]');
 if(existing){loadAt(i+1);return}
 var s=document.createElement('script');s.async=false;s.dataset.sleepRuntime=src;s.src=src+'?runtime=2';
 s.onload=function(){loadAt(i+1)};
 s.onerror=function(){console.error('Schlafmangel-Datei konnte nicht geladen werden:',src);loadAt(i+1)};
 (document.head||document.documentElement).appendChild(s);
}
function ensure(){if(ready()){window.AAYS_SCHLAFMANGEL_RUNTIME_DATA_READY=true;redraw();return}if(running)return;running=true;loadAt(0)}
document.addEventListener('click',function(e){var n=e.target;while(n&&n!==document){if(n.id==='catBefore'){setTimeout(ensure,0);setTimeout(ensure,300);break}n=n.parentNode}},true);
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',function(){setTimeout(ensure,50)});else setTimeout(ensure,50);
setTimeout(ensure,500);setTimeout(ensure,1500);
window.AAYS_ENSURE_SCHLAFMANGEL=ensure;
})();
