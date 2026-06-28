(function(){
'use strict';
window.DEUTSCH_LESSONS=window.DEUTSCH_LESSONS||{};
window.DEUTSCH_TESTS=window.DEUTSCH_TESTS||{};
if(!window.DEUTSCH_PATCH_8106C1F_LOADED){
  window.DEUTSCH_PATCH_8106C1F_LOADED=true;
  document.write('<script src="https://rawcdn.githack.com/cagdascagdas100/chat_gpt_clone_1/8106c1f58b83d7f6e69b3e152fe351b5bce3e51f/deutsch_tests_1/bevor_long_1500_patch.js"><\/script>');
}
var forcedSourceLocks={t21:true,t22:true,t23:true,t24:true,t25:true,t26:true,t47:true};
function currentBevorKey(){
  var checked=document.querySelector('input[name="tc"]:checked');
  if(checked&&checked.value)return checked.value;
  try{if(typeof selected!=='undefined'&&selected)return selected;}catch(e){}
  try{if(window.selected)return window.selected;}catch(e){}
  return '';
}
function knownSourceLockedTopic(key,T,L){
  var text=[key,T.slug,T.title,T.topic,T.source,L.source,L.longSourceDocx].join(' ').toLowerCase();
  return !!(forcedSourceLocks[key]||(text.indexOf('massentourismus')>-1&&text.indexOf('nachteile')>-1)||(text.indexOf('haustiere')>-1&&text.indexOf('nachteile')>-1));
}
function isBevorSourceLocked(key){
  var T=(window.DEUTSCH_TESTS||{})[key]||{};
  var L=(window.DEUTSCH_LESSONS||{})[key]||{};
  return !!(key&&T.category==='Bevor Schreiben'&&(T.source||L.source||L.longSourceDocx||L.longSourceVerified||knownSourceLockedTopic(key,T,L)));
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
function esc(x){return String(x==null?'':x).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');}
function textWords(html){var t=String(html||'').replace(/<[^>]+>/g,' ').replace(/\s+/g,' ').trim();return t?t.split(' ').length:0;}
function list(arr){return '<ul>'+arr.filter(Boolean).map(function(x){return '<li>'+x+'</li>';}).join('')+'</ul>';}
function pairList(arr){return '<ul>'+(arr||[]).filter(Boolean).map(function(x){return '<li>'+esc(x&&x[0]||'')+(x&&x[1]?' → '+esc(x[1]):'')+'</li>';}).join('')+'</ul>';}
function fillList(T){return '<ul>'+(T.fill||[]).map(function(x){return '<li>'+esc(String(x&&x[0]||'').replace('____',x&&x[1]||''))+'</li>';}).join('')+'</ul>';}
function mcList(T){return '<ul>'+(T.mc||[]).map(function(x){var opts=(x&&x[1])||[],right=opts[x&&x[2]||0]||'';return '<li><b>'+esc(right)+'</b><br><span class="muted">Ausgangspunkt: '+esc(x&&x[0]||'')+'</span></li>';}).join('')+'</ul>';}
function tfList(T){return '<ul>'+(T.tf||[]).map(function(x){return '<li>'+esc(x&&x[0]||'')+' <span class="muted">('+((x&&x[1])?'richtig':'falsch')+')</span></li>';}).join('')+'</ul>';}
function prepList(T){return '<ul>'+(T.prep||[]).map(function(x){var s=esc(String(x&&x[0]||'')).replace('___','<b>'+esc(x&&x[1]||'')+'</b>');return '<li>'+s+'</li>';}).join('')+'</ul>';}
function sourceLong1500(key,heading,orderText){
  var T=(window.DEUTSCH_TESTS||{})[key],L=(window.DEUTSCH_LESSONS||{})[key];
  if(!T||T.category!=='Bevor Schreiben')return;
  if(!L){L={};window.DEUTSCH_LESSONS[key]=L;}
  if(L.__aaysSourceLong1500)return;
  var base=[L.long,L.medium,L.short].filter(Boolean).join('');
  var html='<h3>'+esc(heading)+' · ausführliche Quellenfassung</h3>'+
  '<p><b>Prinzip:</b> Diese lange Fassung nutzt nur die im Repository vorhandenen Quellen zu '+esc(key)+'. Die Informationen werden nicht als technische Übungsliste angezeigt, sondern als geordnetes Material für eine flüssige C1/C2-Konu anlatımı. Fremde Beispiele und erfundene Zusatzinformationen werden nicht ergänzt.</p>'+
  '<section>'+base+'</section>'+
  '<h4>Zentraler Wortschatz aus der Quelle</h4>'+list((T.words||[]).map(esc))+
  '<h4>Satzbausteine aus dem Quellenmaterial</h4>'+fillList(T)+
  '<h4>Kernformulierungen für die Argumentation</h4>'+mcList(T)+
  '<h4>Inhaltliche Grenzen und stilistische Kontrolle</h4>'+tfList(T)+
  '<h4>Begriffe und Bedeutungen</h4>'+pairList(T.wordMatch)+
  '<h4>Feste Verbindungen für einen natürlichen Stil</h4>'+pairList(T.phraseMatch)+
  '<h4>Präpositionen und Satzanschlüsse</h4>'+prepList(T)+
  '<h4>Formulierungen, die im Absatz wiederverwendet werden können</h4>'+list((T.hang||[]).map(esc))+
  '<h4>Schreiblogik ohne Wiederholung und ohne Erfindung</h4><p>'+esc(orderText)+'</p>';
  L.long=html;L.source=T.source||L.source||key+' source arrays';L.longSourceVerified=true;L.__aaysSourceLong1500=true;L.__aaysSourceLongWordCount=textWords(html);
}
function applyT21SourceLong1500(){
  sourceLong1500('t21','Massentourismus · C1/C2 Vorteilsabsatz','Für den langen Vorteilsabsatz werden die Quellenbausteine in eine klare Reihenfolge gebracht: zuerst Grundverständnis und Grundthese, danach der wirtschaftliche Nutzen, anschließend Beschäftigungsmöglichkeiten und Infrastruktur, danach Zugang zu Reisen, kulturelle Begegnungen, Horizonterweiterung, Weltoffenheit, Toleranz und internationale Verständigung. Jede Formulierung muss sich auf einen vorhandenen Quellenbaustein zurückführen lassen.');
}
function applyT22SourceLong1500(){
  sourceLong1500('t22','Massentourismus-Nachteile · C1/C2 Nachteile-Absatz','Für den langen Nachteile-Absatz werden die Quellenbausteine in eine klare Reihenfolge gebracht: zuerst Grundverständnis und Leitthese, danach Umweltbelastung und Ressourcenverbrauch, anschließend Belastung der Einheimischen und sinkende Lebensqualität, danach kulturelle Authentizität, Kommerzialisierung, wirtschaftliche Abhängigkeit und unsichere Arbeitsbedingungen. Jede Formulierung muss sich auf einen vorhandenen Quellenbaustein zurückführen lassen.');
}
function applyT23SourceLong1500(){
  sourceLong1500('t23','t23 · C1/C2 Nachteilsabsatz','Für den langen Absatz werden ausschließlich die geladenen Quellenbausteine von t23 vollständig geordnet: vorhandene Lektion, Wortschatz, Satzbausteine, Kernformulierungen, inhaltliche Kontrolle, Begriffe, feste Verbindungen, Satzanschlüsse und Formulierungsregister. Jede Formulierung muss sich auf einen vorhandenen Quellenbaustein zurückführen lassen.');
}
function applyT24SourceLong1500(){
  sourceLong1500('t24','t24 · C1/C2 Nachteilsabsatz','Für den langen Absatz werden ausschließlich die geladenen Quellenbausteine von t24 vollständig geordnet: vorhandene Lektion, Wortschatz, Satzbausteine, Kernformulierungen, inhaltliche Kontrolle, Begriffe, feste Verbindungen, Satzanschlüsse und Formulierungsregister. Jede Formulierung muss sich auf einen vorhandenen Quellenbaustein zurückführen lassen.');
}
function applyT25SourceLong1500(){
  sourceLong1500('t25','Studium im Ausland – Nachteile · C1/C2 Nachteilsabsatz','Für den langen Absatz werden ausschließlich die geladenen Quellenbausteine von t25 vollständig geordnet: Titel, Thema, Wortschatz, Satzbausteine, Kernformulierungen, inhaltliche Kontrolle, Begriffe, feste Verbindungen, Satzanschlüsse und Formulierungsregister. Jede Formulierung muss sich auf einen vorhandenen Quellenbaustein zurückführen lassen.');
}
function applyT26SourceLong1500(){
  sourceLong1500('t26','Das mehrsprachige Aufwachsen von Kindern – Nachteile · C1/C2 Nachteilsabsatz','Für den langen Absatz werden ausschließlich die geladenen Quellenbausteine von t26 vollständig geordnet: Titel, Thema, Wortschatz, Satzbausteine, Kernformulierungen, inhaltliche Kontrolle, Begriffe, feste Verbindungen, Satzanschlüsse und Formulierungsregister. Jede Formulierung muss sich auf einen vorhandenen Quellenbaustein zurückführen lassen.');
}
function applySourceLong1500(){applyT21SourceLong1500();applyT22SourceLong1500();applyT23SourceLong1500();applyT24SourceLong1500();applyT25SourceLong1500();applyT26SourceLong1500();}
function wrapGeneratedLessonExamples(original){
  if(typeof original!=='function')return original;
  if(original.__bevorSourceLockedDisabled)return original;
  var wrapped=function(level){
    var key=currentBevorKey();
    if(isBevorSourceLocked(key)){clearBevorSourceCache(key);return false;}
    return original.apply(this,arguments);
  };
  wrapped.__bevorSourceLockedDisabled=true;
  wrapped.__original=original;
  return wrapped;
}
function installGeneratedLessonExamplesTrap(){
  if(window.__AAYS_APPEND_EXAMPLES_TRAP_INSTALLED){
    if(typeof window.appendGeneratedLessonExamples==='function')window.appendGeneratedLessonExamples=wrapGeneratedLessonExamples(window.appendGeneratedLessonExamples);
    return;
  }
  try{
    var stored=wrapGeneratedLessonExamples(window.appendGeneratedLessonExamples);
    Object.defineProperty(window,'appendGeneratedLessonExamples',{configurable:true,enumerable:true,get:function(){return stored;},set:function(fn){stored=wrapGeneratedLessonExamples(fn);}});
    window.__AAYS_APPEND_EXAMPLES_TRAP_INSTALLED=true;
  }catch(e){
    if(typeof window.appendGeneratedLessonExamples==='function')window.appendGeneratedLessonExamples=wrapGeneratedLessonExamples(window.appendGeneratedLessonExamples);
  }
}
function patchGeneratedLessonExamples(){installGeneratedLessonExamplesTrap();}
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
  applySourceLong1500();
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
  applySourceLong1500();
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
function installBevorSourceLock(){applySourceLong1500();patchGeneratedLessonExamples();cleanBevorGeneratedBlocks();enforceBevorSourceRender();}
applySourceLong1500();
installGeneratedLessonExamplesTrap();
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
window.AAYS_APPEND_EXAMPLES_TRAP_OK=true;
window.AAYS_FORCED_SOURCE_LOCKS_OK=true;
window.AAYS_T21_SOURCE_LONG_1500_OK=true;
window.AAYS_T22_SOURCE_LONG_1500_OK=true;
window.AAYS_T23_SOURCE_LONG_1500_OK=true;
window.AAYS_T24_SOURCE_LONG_1500_OK=true;
window.AAYS_T25_SOURCE_LONG_1500_OK=true;
window.AAYS_T26_SOURCE_LONG_1500_OK=true;
window.AAYS_SOURCE_LONG_FLUENT_LABELS_OK=true;
})();