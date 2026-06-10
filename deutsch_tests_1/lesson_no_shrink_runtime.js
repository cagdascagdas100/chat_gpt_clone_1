(function(){
  var VERSION='1.0-no-shrink-runtime';
  var MIN_SAVE_CHARS=1200;
  var DROP_RATIO=0.78;
  var canon={};
  var protectedKeys={};
  var rendering=false;

  function now(){return new Date().toISOString();}
  function safe(v){return String(v||'').replace(/[&<>]/g,function(c){return {'&':'&amp;','<':'&lt;','>':'&gt;'}[c]});}
  function logEvent(type,key,fromLen,toLen,detail){
    var e={time:now(),type:type,key:key,from:fromLen||0,to:toLen||0,detail:detail||''};
    try{
      var arr=JSON.parse(localStorage.getItem('AAYS_LONG_SHRINK_EVENTS')||'[]');
      arr.push(e); if(arr.length>80)arr=arr.slice(arr.length-80);
      localStorage.setItem('AAYS_LONG_SHRINK_EVENTS',JSON.stringify(arr));
    }catch(_){ }
    try{console.warn('[AAYS no-shrink]',e);}catch(_){ }
  }
  function storageKey(key){return 'AAYS_CANONICAL_LONG_V3_'+key;}
  function currentKey(){
    var checked=document.querySelector('input[name="tc"]:checked');
    if(checked&&checked.value)return checked.value;
    try{if(typeof selected!=='undefined')return selected}catch(e){}
    return '';
  }
  function currentLevelLooksLong(){
    var meta=document.getElementById('lessonMeta');
    var title=document.getElementById('lessonTitle');
    var m=String(meta&&meta.textContent||'');
    var t=String(title&&title.textContent||'');
    return m.indexOf('Uzun')!==-1 || m.indexOf('Long')!==-1 || t.indexOf('Konu anlatımı')!==-1;
  }
  function isStrongLong(html){
    html=String(html||'');
    if(html.length<MIN_SAVE_CHARS)return false;
    var hits=0;
    ['Nachteil','Musterabsatz','C1/C2','Wortschatz','Übung','Kopiervorlage','Beispiele','Erklärung','Redemittel','Satzbausteine','Nomen-Verb'].forEach(function(s){if(html.indexOf(s)!==-1)hits++;});
    return html.length>2500 || hits>=2;
  }
  function saveCanon(key,html,why){
    html=String(html||'');
    if(!key||!isStrongLong(html))return false;
    var old=canon[key]||'';
    try{var stored=localStorage.getItem(storageKey(key))||''; if(stored.length>old.length)old=stored;}catch(_){ }
    if(html.length>old.length){
      canon[key]=html;
      try{localStorage.setItem(storageKey(key),html);}catch(_){ }
      logEvent('canonical_saved',key,old.length,html.length,why||'');
      return true;
    }
    if(!canon[key]&&old){canon[key]=old;}
    return false;
  }
  function loadCanon(key){
    if(canon[key])return canon[key];
    try{var s=localStorage.getItem(storageKey(key))||''; if(isStrongLong(s))canon[key]=s;}catch(_){ }
    return canon[key]||'';
  }
  function shouldRejectShorter(key,oldVal,newVal){
    oldVal=String(oldVal||''); newVal=String(newVal||'');
    var best=canon[key]||loadCanon(key)||oldVal;
    if(!isStrongLong(best))return false;
    return newVal.length>0 && newVal.length < best.length*DROP_RATIO;
  }
  function protectLessonObject(key){
    var lessons=window.DEUTSCH_LESSONS||{};
    var obj=lessons[key];
    if(!obj||protectedKeys[key]===obj)return;
    var cur=String(obj.long||'');
    if(isStrongLong(cur))saveCanon(key,cur,'initial-protect');
    var value=canon[key]||loadCanon(key)||cur;
    if(value && (!cur || cur.length<value.length)) obj.long=value;
    try{
      Object.defineProperty(obj,'long',{
        configurable:true,
        enumerable:true,
        get:function(){return value;},
        set:function(v){
          v=String(v||'');
          if(shouldRejectShorter(key,value,v)){
            logEvent('blocked_short_assignment',key,value.length,v.length,'setter');
            return;
          }
          if(isStrongLong(v)&&v.length>String(value||'').length){saveCanon(key,v,'setter-longer');}
          value=(canon[key]&&canon[key].length>v.length)?canon[key]:v;
        }
      });
      protectedKeys[key]=obj;
    }catch(e){ }
  }
  function protectAll(){
    window.DEUTSCH_LESSONS=window.DEUTSCH_LESSONS||{};
    Object.keys(window.DEUTSCH_LESSONS).forEach(function(key){protectLessonObject(key);});
  }
  function restoreAll(){
    var lessons=window.DEUTSCH_LESSONS||{};
    Object.keys(lessons).forEach(function(key){
      var best=loadCanon(key);
      if(best&&lessons[key]){
        var cur=String(lessons[key].long||'');
        if(cur.length<best.length*DROP_RATIO){
          lessons[key].long=best;
          logEvent('restored_lesson_object',key,cur.length,best.length,'periodic');
        }
      }
    });
  }
  function renderCanonical(key){
    var lessons=window.DEUTSCH_LESSONS||{};
    var tests=window.DEUTSCH_TESTS||{};
    var html=(lessons[key]&&lessons[key].long)||loadCanon(key)||'';
    if(!isStrongLong(html))return false;
    var lesson=document.getElementById('lesson');
    var title=document.getElementById('lessonTitle');
    var meta=document.getElementById('lessonMeta');
    var content=document.getElementById('lessonContent');
    if(!lesson||!title||!meta||!content)return false;
    rendering=true;
    try{
      if(typeof hide==='function')hide();
      lesson.classList.remove('hide');
      title.textContent='Konu anlatımı: '+((tests[key]&&tests[key].title)||key);
      meta.textContent='Seviye: Uzun · eksilme engellendi / kapsamlı içerik geri yüklendi';
      var words=((tests[key]&&tests[key].words)||[]).slice(0,70).map(function(w){return '<li>'+safe(w)+'</li>';}).join('');
      content.innerHTML='<section style="padding:14px;border:1px solid #d8d3ca;border-radius:14px;background:#fff;margin-bottom:18px"><h2>1. Genel bakış</h2><p><b>Thema:</b> '+safe((tests[key]&&tests[key].topic)||'')+'</p>'+(words?'<h3>Öncelikli kavramlar</h3><ul>'+words+'</ul>':'')+'</section><section style="padding:14px;border:1px solid #d8d3ca;border-radius:14px;background:#fff;margin-bottom:18px"><h2>2. Konu açıklaması</h2>'+html+'</section>';
    }finally{setTimeout(function(){rendering=false;},80);}
    return true;
  }
  function verifyDom(){
    if(rendering)return;
    var key=currentKey();
    if(!key||!currentLevelLooksLong())return;
    var content=document.getElementById('lessonContent');
    if(!content)return;
    var shown=String(content.innerHTML||'');
    var best=((window.DEUTSCH_LESSONS||{})[key]&&window.DEUTSCH_LESSONS[key].long)||loadCanon(key)||'';
    if(isStrongLong(best)&&shown.length<best.length*DROP_RATIO){
      logEvent('dom_shrink_detected',key,best.length,shown.length,'mutation-or-delay');
      renderCanonical(key);
    }
  }
  function installObserver(){
    var content=document.getElementById('lessonContent');
    if(!content||content.dataset.noShrinkObserver==='1')return;
    content.dataset.noShrinkObserver='1';
    new MutationObserver(function(){setTimeout(verifyDom,100);}).observe(content,{childList:true,subtree:true,characterData:true});
  }
  function onLessonClick(ev){
    var btn=ev.target&&ev.target.closest&&ev.target.closest('#btnLessonLong');
    if(!btn)return;
    protectAll(); restoreAll();
    var key=currentKey();
    setTimeout(function(){protectAll(); restoreAll(); if(key)verifyDom();},200);
    setTimeout(function(){if(key)renderCanonical(key);},700);
  }
  function boot(){
    protectAll(); restoreAll(); installObserver();
    setTimeout(function(){protectAll(); restoreAll(); installObserver(); verifyDom();},600);
    setTimeout(function(){protectAll(); restoreAll(); installObserver(); verifyDom();},1800);
  }
  document.addEventListener('pointerdown',onLessonClick,true);
  document.addEventListener('click',onLessonClick,true);
  document.addEventListener('DOMContentLoaded',boot);
  setInterval(function(){protectAll(); restoreAll(); installObserver(); verifyDom();},1200);
  window.AAYS_LONG_NO_SHRINK={version:VERSION,protectAll:protectAll,restoreAll:restoreAll,renderCanonical:renderCanonical,report:function(){try{return JSON.parse(localStorage.getItem('AAYS_LONG_SHRINK_EVENTS')||'[]');}catch(e){return [];}},canonical:canon};
})();
