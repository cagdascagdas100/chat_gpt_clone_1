(function(){
  var FULL_SCRIPT_SOURCES=[
    'teamarbeit_word_full_lesson.js?v=2',
    'teamarbeit_lesson_force.js?v=5',
    'individualitaet_final_fix.js?v=2',
    'individualitaet_super_override.js?v=2',
    'lebenslanges_lernen_final_fix.js?v=3',
    'lebenslanges_lernen_super_override.js?v=2',
    'werbung_nachteile_final_fix.js?v=3',
    'werbung_nachteile_long_full_override.js?v=2',
    'werbung_medien_nachteile_final_fix.js?v=2'
  ];
  var FULL_SIGNATURES={
    t28:['Teamarbeit','Vollständige Word-Version','Nachteil 4','Verantwortungsdiffusion','Übungen'],
    t29:['Individualität','Erweiterte vollständige Langversion','Nachteil 4','Kalıp Bankası','20 hazır Satzstarter'],
    t30:['Lebenslanges Lernen','Ziel dieses Arbeitsblattes','Nachteil 4','Kompakte C1/C2-Kopiervorlage','Musterlösung'],
    t31:['Werbung','Vollständige Word-Version','Manipulation','Reizüberflutung','Kompakte Kopiervorlage'],
    t32:['Medien','Vollständige Word-Version','Filterblasen','Fake News','Kopiervorlage']
  };
  var MIN_FULL_LENGTH={t28:4500,t29:4500,t30:4500,t31:3500,t32:3500};
  var canonical={};
  var loading={};
  var restoring=false;

  function currentKey(){
    var checked=document.querySelector('input[name="tc"]:checked');
    if(checked&&checked.value)return checked.value;
    try{if(typeof selected!=='undefined')return selected}catch(e){}
    return '';
  }
  function safe(v){
    return String(v||'').replace(/[&<>]/g,function(c){return {'&':'&amp;','<':'&lt;','>':'&gt;'}[c]});
  }
  function srcBase(src){return String(src||'').split('?')[0];}
  function scriptExists(src){
    var base=srcBase(src);
    return !!Array.prototype.slice.call(document.scripts).find(function(s){return (s.getAttribute('src')||'').indexOf(base)>=0;});
  }
  function loadScript(src){
    var base=srcBase(src);
    if(loading[base]||scriptExists(src))return;
    loading[base]=true;
    var s=document.createElement('script');
    s.src=src;
    s.dataset.longIntegrityDependency='1';
    s.onload=function(){setTimeout(function(){patchKnownFunctions();collectCanonicalLongs();restoreLessonObjects();},50);};
    document.head.appendChild(s);
  }
  function ensureFullScripts(){FULL_SCRIPT_SOURCES.forEach(loadScript);}
  function hasSignature(key,html){
    html=String(html||'');
    var sig=FULL_SIGNATURES[key];
    if(!sig)return html.length>=(MIN_FULL_LENGTH[key]||2500);
    return sig.every(function(x){return html.indexOf(x)!==-1;});
  }
  function isAcceptableLong(key,html){
    html=String(html||'');
    return html.length>=(MIN_FULL_LENGTH[key]||2500)&&hasSignature(key,html);
  }
  function storeCanonical(key,html,reason){
    html=String(html||'');
    if(!isAcceptableLong(key,html))return false;
    if(!canonical[key]||html.length>canonical[key].length){
      canonical[key]=html;
      try{sessionStorage.setItem('AAYS_CANONICAL_LONG_'+key,html);}catch(e){}
      try{console.info('[AAYS long lesson guard] canonical stored',key,html.length,reason||'');}catch(e){}
      return true;
    }
    return false;
  }
  function collectCanonicalLongs(){
    var lessons=window.DEUTSCH_LESSONS||{};
    Object.keys(lessons).forEach(function(key){
      var html=lessons[key]&&lessons[key].long;
      storeCanonical(key,html,'from-DEUTSCH_LESSONS');
    });
    Object.keys(FULL_SIGNATURES).forEach(function(key){
      if(!canonical[key]){
        try{
          var saved=sessionStorage.getItem('AAYS_CANONICAL_LONG_'+key)||'';
          if(isAcceptableLong(key,saved))canonical[key]=saved;
        }catch(e){}
      }
    });
  }
  function restoreLessonObjects(){
    window.DEUTSCH_LESSONS=window.DEUTSCH_LESSONS||{};
    Object.keys(canonical).forEach(function(key){
      window.DEUTSCH_LESSONS[key]=window.DEUTSCH_LESSONS[key]||{};
      var cur=String(window.DEUTSCH_LESSONS[key].long||'');
      if(!isAcceptableLong(key,cur)||cur.length+500<canonical[key].length){
        window.DEUTSCH_LESSONS[key].long=canonical[key];
        try{console.warn('[AAYS long lesson guard] restored lesson object',key,cur.length,'->',canonical[key].length);}catch(e){}
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
    if(typeof window.forceWerbungMedienLessonFinal==='function'){
      window.forceWerbungMedienLesson=window.forceWerbungMedienLessonFinal;
      window.forceWerbungMedienLessonFull=window.forceWerbungMedienLessonFinal;
    }
  }
  function renderLong(key){
    ensureFullScripts();
    patchKnownFunctions();
    collectCanonicalLongs();
    restoreLessonObjects();
    var tests=window.DEUTSCH_TESTS||{};
    var lessons=window.DEUTSCH_LESSONS||{};
    var test=tests[key]||{};
    var html=(lessons[key]&&lessons[key].long)||canonical[key]||'';
    if(!html)return false;
    if(canonical[key]&&(!isAcceptableLong(key,html)||html.length+500<canonical[key].length))html=canonical[key];
    var lesson=document.getElementById('lesson');
    var title=document.getElementById('lessonTitle');
    var meta=document.getElementById('lessonMeta');
    var content=document.getElementById('lessonContent');
    if(!lesson||!title||!meta||!content)return false;
    restoring=true;
    try{
      if(typeof hide==='function')hide();
      lesson.classList.remove('hide');
      title.textContent='Konu anlatımı: '+(test.title||key);
      meta.textContent='Seviye: Uzun · KANONİK kapsamlı içerik koruması aktif';
      var words=(test.words||[]).slice(0,70).map(function(w){return '<li>'+safe(w)+'</li>';}).join('');
      content.innerHTML='<section style="padding:14px;border:1px solid #d8d3ca;border-radius:14px;background:#fff;margin-bottom:18px"><h2>1. Genel bakış</h2><p><b>Thema:</b> '+safe(test.topic||'')+'</p>'+(words?'<h3>Öncelikli kavramlar</h3><ul>'+words+'</ul>':'')+'</section><section style="padding:14px;border:1px solid #d8d3ca;border-radius:14px;background:#fff;margin-bottom:18px"><h2>2. Konu açıklaması</h2>'+html+'</section>';
      lesson.scrollIntoView({behavior:'smooth'});
    }finally{
      setTimeout(function(){restoring=false;},50);
    }
    return true;
  }
  function verifyDom(){
    if(restoring)return;
    var key=currentKey();
    if(!key)return;
    var content=document.getElementById('lessonContent');
    var lesson=document.getElementById('lesson');
    if(!content||!lesson||lesson.classList.contains('hide'))return;
    var title=document.getElementById('lessonTitle');
    var meta=document.getElementById('lessonMeta');
    var appearsLong=meta&&String(meta.textContent||'').indexOf('Uzun')!==-1;
    if(!appearsLong&&title&&String(title.textContent||'').indexOf('Konu anlatımı')!==-1){
      var shown=content.innerHTML||'';
      if(canonical[key]&&shown.length+700<canonical[key].length)appearsLong=true;
    }
    if(!appearsLong)return;
    collectCanonicalLongs();
    restoreLessonObjects();
    var best=canonical[key]||((window.DEUTSCH_LESSONS||{})[key]&&window.DEUTSCH_LESSONS[key].long)||'';
    var shown=content.innerHTML||'';
    if(best&&isAcceptableLong(key,best)&&(shown.length+700<best.length||!hasSignature(key,shown))){
      try{console.warn('[AAYS long lesson guard] DOM shrink detected',key,shown.length,'->',best.length);}catch(e){}
      renderLong(key);
    }
  }
  function levelFromButton(el){
    if(!el)return null;
    if(el.id==='btnLessonShort')return 'short';
    if(el.id==='btnLessonMedium')return 'medium';
    if(el.id==='btnLessonLong')return 'long';
    return null;
  }
  function captureLessonClick(ev){
    var btn=ev.target&&ev.target.closest&&ev.target.closest('#btnLessonShort,#btnLessonMedium,#btnLessonLong');
    var level=levelFromButton(btn);
    if(!level)return;
    ensureFullScripts();
    patchKnownFunctions();
    collectCanonicalLongs();
    restoreLessonObjects();
    if(level==='long'){
      var key=currentKey();
      if(!key)return;
      ev.preventDefault();
      ev.stopPropagation();
      ev.stopImmediatePropagation();
      setTimeout(function(){renderLong(key);},120);
      return false;
    }
  }
  function installObserver(){
    var content=document.getElementById('lessonContent');
    if(!content||content.dataset.longIntegrityObserver==='1')return;
    content.dataset.longIntegrityObserver='1';
    var obs=new MutationObserver(function(){setTimeout(verifyDom,80);});
    obs.observe(content,{childList:true,subtree:true,characterData:true});
  }
  function boot(){
    ensureFullScripts();
    patchKnownFunctions();
    setTimeout(function(){collectCanonicalLongs();restoreLessonObjects();installObserver();},200);
    setTimeout(function(){collectCanonicalLongs();restoreLessonObjects();installObserver();verifyDom();},1000);
    setTimeout(function(){collectCanonicalLongs();restoreLessonObjects();installObserver();verifyDom();},2500);
  }
  document.addEventListener('pointerdown',captureLessonClick,true);
  document.addEventListener('mousedown',captureLessonClick,true);
  document.addEventListener('touchstart',captureLessonClick,true);
  document.addEventListener('click',captureLessonClick,true);
  document.addEventListener('DOMContentLoaded',boot);
  setInterval(function(){patchKnownFunctions();collectCanonicalLongs();restoreLessonObjects();installObserver();verifyDom();},1000);
  window.AAYS_LONG_LESSON_GUARD={
    version:'2.0-hard-canonical',
    ensureFullScripts:ensureFullScripts,
    collectCanonicalLongs:collectCanonicalLongs,
    restoreLessonObjects:restoreLessonObjects,
    renderLong:renderLong,
    verifyDom:verifyDom,
    canonical:canonical
  };
})();
