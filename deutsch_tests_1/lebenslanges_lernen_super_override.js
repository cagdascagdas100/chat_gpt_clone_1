(function(){
  function key(){
    var checked=document.querySelector('input[name="tc"]:checked');
    if(checked&&checked.value)return checked.value;
    try{if(typeof selected!=='undefined')return selected}catch(e){}
    return '';
  }
  function levelFrom(el){
    if(!el)return null;
    if(el.id==='btnLessonShort')return 'short';
    if(el.id==='btnLessonMedium')return 'medium';
    if(el.id==='btnLessonLong')return 'long';
    return null;
  }
  function ensure(){
    if(typeof window.forceLebenslangesLernenLesson==='function')return true;
    return false;
  }
  function render(level){
    if(!ensure())return false;
    window.forceLebenslangesLernenLesson(level||'long');
    return true;
  }
  function intercept(ev){
    var btn=ev.target&&ev.target.closest&&ev.target.closest('#btnLessonShort,#btnLessonMedium,#btnLessonLong');
    var level=levelFrom(btn);
    if(!level)return;
    if(key()!=='t30')return;
    ev.preventDefault();
    ev.stopPropagation();
    ev.stopImmediatePropagation();
    setTimeout(function(){render(level);},0);
    return false;
  }
  function preRender(ev){
    var btn=ev.target&&ev.target.closest&&ev.target.closest('#btnLessonShort,#btnLessonMedium,#btnLessonLong');
    var level=levelFrom(btn);
    if(!level)return;
    if(key()!=='t30')return;
    render(level);
  }
  function patch(){
    if(typeof window.forceLebenslangesLernenLesson==='function'){
      window.forceLebenslangesLernenLessonFull=window.forceLebenslangesLernenLesson;
    }
    if(!window.DEUTSCH_LESSONS)window.DEUTSCH_LESSONS={};
    if(window.DEUTSCH_LESSONS.t30&&window.DEUTSCH_LESSONS.t30.long){
      var l=window.DEUTSCH_LESSONS.t30.long;
      var required=['Ziel dieses Arbeitsblattes','Nachteil 1: Ständiger Leistungsdruck und Überforderung','Nachteil 2: Zeitmangel und Belastung des Privatlebens','Nachteil 3: Soziale Ungleichheit und ungleicher Zugang zu Weiterbildung','Nachteil 4: Orientierungslosigkeit, Zertifikatsdruck und Qualitätsprobleme','Kompakte C1/C2-Kopiervorlage','Übungsteil','Musterlösung'];
      window.LEBENSLANGES_LERNEN_WORD_LONG_OK=required.every(function(x){return l.indexOf(x)>=0;});
    }
  }
  document.addEventListener('pointerdown',preRender,true);
  document.addEventListener('mousedown',preRender,true);
  document.addEventListener('touchstart',preRender,true);
  document.addEventListener('click',intercept,true);
  document.addEventListener('DOMContentLoaded',patch);
  setInterval(patch,300);
})();