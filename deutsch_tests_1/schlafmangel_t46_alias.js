(function(){
'use strict';
if(window.AAYS_SCHLAFMANGEL_T46_ALIAS_OK)return;
var SOURCE='schlafmangel_studierende_ursachen_folgen_loesungen_c1c2';
var TARGET='t46';
function bind(){
  window.DEUTSCH_TESTS=window.DEUTSCH_TESTS||{};
  window.DEUTSCH_LESSONS=window.DEUTSCH_LESSONS||{};
  var src=window.DEUTSCH_TESTS[SOURCE];
  var lesson=window.DEUTSCH_LESSONS[SOURCE];
  if(src){
    src.category='Bevor Schreiben';
    src.title='Schlafmangel bei Studierenden - Ursachen / Folgen / Lösungen';
    window.DEUTSCH_TESTS[TARGET]=src;
  }
  if(lesson)window.DEUTSCH_LESSONS[TARGET]=lesson;
  window.AAYS_SCHLAFMANGEL_T46_READY=!!(window.DEUTSCH_TESTS[TARGET]&&window.DEUTSCH_LESSONS[TARGET]);
  return window.AAYS_SCHLAFMANGEL_T46_READY;
}
function dedupe(){
  var target=document.querySelector('input[name="tc"][value="'+TARGET+'"]');
  var source=document.querySelector('input[name="tc"][value="'+SOURCE+'"]');
  if(target&&source){var label=source.closest('label');if(label)label.remove();}
}
function wrapRender(){
  if(window.AAYS_SCHLAFMANGEL_RENDER_WRAPPED||typeof window.renderTests!=='function')return;
  var original=window.renderTests;
  window.renderTests=function(cat){
    bind();
    var out=original.apply(this,arguments);
    if(cat==='Bevor Schreiben')setTimeout(dedupe,0);
    return out;
  };
  window.AAYS_SCHLAFMANGEL_RENDER_WRAPPED=true;
}
function apply(){bind();wrapRender();dedupe();}
apply();
document.addEventListener('DOMContentLoaded',function(){setTimeout(apply,0);setTimeout(apply,200);setTimeout(apply,800)});
document.addEventListener('click',function(e){var n=e.target;while(n&&n!==document){if(n.id==='catBefore'){bind();setTimeout(function(){if(typeof window.renderTests==='function')window.renderTests('Bevor Schreiben')},30);break}n=n.parentNode}},true);
try{new MutationObserver(function(){bind();dedupe();wrapRender()}).observe(document.documentElement,{childList:true,subtree:true})}catch(e){}
setTimeout(apply,50);setTimeout(apply,500);setTimeout(apply,1500);
window.AAYS_SCHLAFMANGEL_T46_ALIAS_OK=true;
})();
