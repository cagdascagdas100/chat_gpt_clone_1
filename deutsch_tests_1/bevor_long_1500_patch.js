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
function levelName(level){return level==='short'?'Kısa':level==='medium'?'Orta':'Uzun';}
function buttonLevel(btn){
  if(!btn)return '';
  if(btn.id==='btnLessonShort')return 'short';
  if(btn.id==='btnLessonMedium')return 'medium';
  if(btn.id==='btnLessonLong')return 'long';
  return '';
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
function renderBevorSourceLesson(level){
  var key=currentBevorKey();
  var L=(window.DEUTSCH_LESSONS||{})[key]||{};
  var T=(window.DEUTSCH_TESTS||{})[key]||{};
  if(!isBevorSourceLocked(key)||!L[level])return false;
  clearBevorSourceCache(key);
  var lesson=document.getElementById('lesson');
  var title=document.getElementById('lessonTitle');
  var meta=document.getElementById('lessonMeta');
  var content=document.getElementById('lessonContent');
  if(!lesson||!title||!meta||!content)return false;
  try{if(typeof hide==='function')hide();}catch(e){}
  lesson.classList.remove('hide');
  title.textContent='Konu anlatımı: '+(T.title||key);
  meta.textContent='Seviye: '+levelName(level)+' · Word kaynaklı içerik';
  content.dataset.bevorSourceLevel=level;
  content.innerHTML='<section style="padding:14px;border:1px solid #d8d3ca;border-radius:14px;background:#fff;margin-bottom:18px"><h2>Konu açıklaması</h2>'+L[level]+'</section>';
  try{lesson.scrollIntoView({behavior:'smooth'});}catch(e){}
  return true;
}
function enforceBevorSourceRender(){
  cleanBevorGeneratedBlocks();
  var key=currentBevorKey();
  if(!isBevorSourceLocked(key))return;
  var content=document.getElementById('lessonContent');
  var lesson=document.getElementById('lesson');
  if(!content||!lesson||lesson.classList.contains('hide'))return;
  var level=content.dataset.bevorSourceLevel||window.AAYS_BEVOR_LAST_LEVEL||'long';
  var text=String(content.textContent||'');
  var bad=blockedHeadings.some(function(h){return text.indexOf(h)!==-1;});
  if(bad){renderBevorSourceLesson(level);}
}
function installBevorSourceLock(){patchGeneratedLessonExamples();cleanBevorGeneratedBlocks();enforceBevorSourceRender();}
document.addEventListener('click',function(ev){
  var btn=ev.target&&ev.target.closest&&ev.target.closest('#btnLessonShort,#btnLessonMedium,#btnLessonLong');
  var level=buttonLevel(btn);
  if(level&&isBevorSourceLocked(currentBevorKey())){
    window.AAYS_BEVOR_LAST_LEVEL=level;
    if(renderBevorSourceLesson(level)){
      ev.preventDefault();ev.stopPropagation();ev.stopImmediatePropagation();
      setTimeout(cleanBevorGeneratedBlocks,0);
      return false;
    }
  }
  setTimeout(installBevorSourceLock,0);setTimeout(installBevorSourceLock,150);setTimeout(installBevorSourceLock,600);
},true);
document.addEventListener('DOMContentLoaded',function(){installBevorSourceLock();setTimeout(installBevorSourceLock,100);setTimeout(installBevorSourceLock,700);});
setInterval(installBevorSourceLock,1000);
window.AAYS_BEVOR_SOURCE_LOCKED_GENERIC_EXAMPLES_DISABLED=true;
window.AAYS_BEVOR_SOURCE_CACHE_CLEANUP_OK=true;
window.AAYS_BEVOR_SOURCE_RENDER_OK=true;
})();