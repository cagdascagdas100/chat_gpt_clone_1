(function(){
  var REQUIRED_FULL_SCRIPTS=[
    'teamarbeit_word_full_lesson.js?v=2',
    'teamarbeit_lesson_force.js?v=5',
    'individualitaet_final_fix.js?v=2',
    'individualitaet_super_override.js?v=2',
    'lebenslanges_lernen_final_fix.js?v=3',
    'lebenslanges_lernen_super_override.js?v=2',
    'werbung_nachteile_final_fix.js?v=2',
    'werbung_nachteile_long_full_override.js?v=2'
  ];
  var loaded={};
  var snapshots={};
  var MIN_LONG_CHARS=1800;

  function currentKey(){
    var checked=document.querySelector('input[name="tc"]:checked');
    if(checked&&checked.value)return checked.value;
    try{if(typeof selected!=='undefined')return selected}catch(e){}
    return '';
  }
  function levelFromButton(el){
    if(!el)return null;
    if(el.id==='btnLessonShort')return 'short';
    if(el.id==='btnLessonMedium')return 'medium';
    if(el.id==='btnLessonLong')return 'long';
    return null;
  }
  function safe(v){
    return String(v||'').replace(/[&<>]/g,function(c){return {'&':'&amp;','<':'&lt;','>':'&gt;'}[c]});
  }
  function scriptExists(base){
    var clean=String(base).split('?')[0];
    return !!Array.prototype.slice.call(document.scripts).find(function(s){return (s.getAttribute('src')||'').indexOf(clean)>=0;});
  }
  function loadScript(src){
    var clean=String(src).split('?')[0];
    if(loaded[clean]||scriptExists(clean)){loaded[clean]=true;return;}
    var s=document.createElement('script');
    s.src=src;
    s.dataset.longRestore='1';
    s.onload=function(){loaded[clean]=true;takeSnapshots();patchKnownFunctions();};
    document.head.appendChild(s);
  }
  function ensureFullScripts(){REQUIRED_FULL_SCRIPTS.forEach(loadScript);}

  function takeSnapshots(){
    var lessons=window.DEUTSCH_LESSONS||{};
    Object.keys(lessons).forEach(function(k){
      var l=lessons[k]&&lessons[k].long;
      if(typeof l==='string'&&l.length>=MIN_LONG_CHARS){
        if(!snapshots[k]||l.length>snapshots[k].length){
          snapshots[k]=l;
          try{localStorage.setItem('AAYS_LONG_LESSON_SNAPSHOT_'+k,l);}catch(e){}
        }
      }
    });
  }
  function restoreSnapshots(){
    window.DEUTSCH_LESSONS=window.DEUTSCH_LESSONS||{};
    Object.keys(window.DEUTSCH_LESSONS).forEach(function(k){
      var cur=(window.DEUTSCH_LESSONS[k]&&window.DEUTSCH_LESSONS[k].long)||'';
      var saved=snapshots[k];
      if(!saved){try{saved=localStorage.getItem('AAYS_LONG_LESSON_SNAPSHOT_'+k)||'';}catch(e){saved='';}}
      if(saved&&saved.length>cur.length+400){
        window.DEUTSCH_LESSONS[k]=window.DEUTSCH_LESSONS[k]||{};
        window.DEUTSCH_LESSONS[k].long=saved;
      }
    });
  }
  function patchKnownFunctions(){
    if(typeof window.forceIndividualitaetLessonFinal==='function'){
      window.forceIndividualitaetLesson=window.forceIndividualitaetLessonFinal;
      window.forceIndividualitaetLessonFull=window.forceIndividualitaetLessonFinal;
    }
    if(typeof window.forceLebenslangesLernenLesson==='function'){
      window.forceLebenslangesLernenLessonFull=window.forceLebenslangesLernenLesson;
    }
    if(typeof window.forceWerbungLessonFinal==='function'){
      window.forceWerbungLesson=window.forceWerbungLessonFinal;
      window.forceWerbungLessonFull=window.forceWerbungLessonFinal;
    }
  }
  function renderGeneric(key,level){
    var tests=window.DEUTSCH_TESTS||{};
    var lessons=window.DEUTSCH_LESSONS||{};
    var test=tests[key]||{};
    var block=lessons[key]&&lessons[key][level];
    if(!block&&level==='long')block=(snapshots[key]||'');
    if(!block)return false;
    if(typeof hide==='function')hide();
    var lesson=document.getElementById('lesson');
    var title=document.getElementById('lessonTitle');
    var meta=document.getElementById('lessonMeta');
    var content=document.getElementById('lessonContent');
    if(!lesson||!title||!meta||!content)return false;
    lesson.classList.remove('hide');
    title.textContent='Konu anlatımı: '+(test.title||key);
    meta.textContent='Seviye: '+(level==='short'?'Kısa':level==='medium'?'Orta':'Uzun')+' · uzun içerik koruma modu aktif';
    var words=((test.words||[]).slice(0,level==='short'?8:level==='medium'?22:60)).map(function(w){return '<li>'+safe(w)+'</li>';}).join('');
    content.innerHTML='<section style="padding:14px;border:1px solid #d8d3ca;border-radius:14px;background:#fff;margin-bottom:18px"><h2>1. Genel bakış</h2><p><b>Thema:</b> '+safe(test.topic||'')+'</p>'+(words?'<h3>Öncelikli kavramlar</h3><ul>'+words+'</ul>':'')+'</section><section style="padding:14px;border:1px solid #d8d3ca;border-radius:14px;background:#fff;margin-bottom:18px"><h2>2. Konu açıklaması</h2>'+block+'</section>';
    lesson.scrollIntoView({behavior:'smooth'});
    return true;
  }
  function renderKnownOrGeneric(key,level){
    ensureFullScripts();
    patchKnownFunctions();
    restoreSnapshots();
    if(key==='t29'&&typeof window.forceIndividualitaetLessonFinal==='function')return window.forceIndividualitaetLessonFinal(level||'long'),true;
    if(key==='t30'&&typeof window.forceLebenslangesLernenLesson==='function')return window.forceLebenslangesLernenLesson(level||'long'),true;
    if(key==='t31'&&typeof window.forceWerbungLessonFinal==='function')return window.forceWerbungLessonFinal(level||'long'),true;
    return renderGeneric(key,level||'long');
  }
  function inspectAfterRender(key){
    setTimeout(function(){
      restoreSnapshots();
      var content=document.getElementById('lessonContent');
      var shown=content?content.innerHTML:'';
      var best=(window.DEUTSCH_LESSONS&&window.DEUTSCH_LESSONS[key]&&window.DEUTSCH_LESSONS[key].long)||snapshots[key]||'';
      if(best&&shown.length+500<best.length){renderGeneric(key,'long');}
    },250);
  }
  function intercept(ev){
    var btn=ev.target&&ev.target.closest&&ev.target.closest('#btnLessonShort,#btnLessonMedium,#btnLessonLong');
    var level=levelFromButton(btn);
    if(!level)return;
    var key=currentKey();
    if(!key)return;
    if(level==='long'){
      ensureFullScripts();
      patchKnownFunctions();
      takeSnapshots();
      setTimeout(function(){renderKnownOrGeneric(key,'long');inspectAfterRender(key);},120);
    }else{
      ensureFullScripts();
      patchKnownFunctions();
    }
  }
  function boot(){
    ensureFullScripts();
    setTimeout(function(){patchKnownFunctions();takeSnapshots();restoreSnapshots();},300);
    setTimeout(function(){patchKnownFunctions();takeSnapshots();restoreSnapshots();},1200);
  }
  document.addEventListener('pointerdown',intercept,true);
  document.addEventListener('mousedown',intercept,true);
  document.addEventListener('touchstart',intercept,true);
  document.addEventListener('click',function(ev){
    var btn=ev.target&&ev.target.closest&&ev.target.closest('#btnLessonLong');
    if(!btn)return;
    var key=currentKey();
    if(!key)return;
    setTimeout(function(){renderKnownOrGeneric(key,'long');inspectAfterRender(key);},180);
  },true);
  document.addEventListener('DOMContentLoaded',boot);
  setInterval(function(){patchKnownFunctions();takeSnapshots();restoreSnapshots();},1000);
  window.AAYS_LONG_LESSON_GUARD={ensureFullScripts:ensureFullScripts,render:renderKnownOrGeneric,takeSnapshots:takeSnapshots,restoreSnapshots:restoreSnapshots};
})();
