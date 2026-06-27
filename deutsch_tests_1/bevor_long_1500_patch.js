(function(){
'use strict';
window.DEUTSCH_LESSONS=window.DEUTSCH_LESSONS||{};
window.DEUTSCH_TESTS=window.DEUTSCH_TESTS||{};
if(!window.DEUTSCH_PATCH_8106C1F_LOADED){
  window.DEUTSCH_PATCH_8106C1F_LOADED=true;
  document.write('<script src="https://rawcdn.githack.com/cagdascagdas100/chat_gpt_clone_1/8106c1f58b83d7f6e69b3e152fe351b5bce3e51f/deutsch_tests_1/bevor_long_1500_patch.js"><\/script>');
}
function currentBevorKey(){
  var checked=document.querySelector('input[name="tc"]:checked');
  if(checked&&checked.value)return checked.value;
  try{if(typeof selected!=='undefined'&&selected)return selected;}catch(e){}
  try{if(window.selected)return window.selected;}catch(e){}
  return '';
}
function isBevorSourceLocked(key){
  var T=(window.DEUTSCH_TESTS||{})[key]||{};
  var L=(window.DEUTSCH_LESSONS||{})[key]||{};
  return !!(key&&T.category==='Bevor Schreiben'&&(T.source||L.source||L.longSourceDocx||L.longSourceVerified));
}
function clearBevorSourceCache(key){
  if(!key)return;
  try{localStorage.removeItem('AAYS_CANONICAL_LONG_V3_'+key);}catch(e){}
}
var blockedHeadings=[
  'Mini paragraf örnekleri',
  'Ezberlenecek kalıplar',
  'Gramer ve Rektion',
  'C1/C2 örnek cümleler',
  'Hata uyarıları',
  'Yazma görevi'
];
function patchGeneratedLessonExamples(){
  if(typeof window.appendGeneratedLessonExamples!=='function')return;
  if(window.appendGeneratedLessonExamples.__bevorSourceLockedDisabled)return;
  var original=window.appendGeneratedLessonExamples;
  var wrapped=function(level){
    var key=currentBevorKey();
    if(isBevorSourceLocked(key)){clearBevorSourceCache(key);return false;}
    return original.apply(this,arguments);
  };
  wrapped.__bevorSourceLockedDisabled=true;
  wrapped.__original=original;
  window.appendGeneratedLessonExamples=wrapped;
}
function cleanBevorGeneratedBlocks(){
  var key=currentBevorKey();
  if(!isBevorSourceLocked(key))return;
  clearBevorSourceCache(key);
  var root=document.getElementById('lessonContent');
  if(!root)return;
  Array.prototype.slice.call(root.querySelectorAll('section')).forEach(function(sec){
    var text=String(sec.textContent||'');
    if(blockedHeadings.some(function(h){return text.indexOf(h)!==-1;})){sec.remove();}
  });
}
function installBevorSourceLock(){patchGeneratedLessonExamples();cleanBevorGeneratedBlocks();}
document.addEventListener('DOMContentLoaded',function(){installBevorSourceLock();setTimeout(installBevorSourceLock,100);setTimeout(installBevorSourceLock,700);});
document.addEventListener('click',function(){setTimeout(installBevorSourceLock,0);setTimeout(installBevorSourceLock,150);setTimeout(installBevorSourceLock,600);},true);
setInterval(installBevorSourceLock,1000);
window.AAYS_BEVOR_SOURCE_LOCKED_GENERIC_EXAMPLES_DISABLED=true;
window.AAYS_BEVOR_SOURCE_CACHE_CLEANUP_OK=true;
})();