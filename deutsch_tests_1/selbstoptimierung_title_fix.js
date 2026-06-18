(function(){
  var KEY='t40';
  var TITLE='Selbstoptimierung durch Vorbilder – Vorteile · C1/C2 Vorteilsabsatz';
  var TOPIC='Erörterung · Vorteile der Selbstoptimierung durch Vorbilder · Motivation · Zielorientierung · konkrete Beispiele · Selbstvertrauen · positive Gewohnheiten';
  var SOURCE='Selbstoptimierung_durch_Vorbilder_Vorteile_4_C1_C2_15_20(1).docx';
  function fix(){
    try{
      window.DEUTSCH_TESTS=window.DEUTSCH_TESTS||{};
      window.DEUTSCH_LESSONS=window.DEUTSCH_LESSONS||{};
      window.LESSONS=window.LESSONS||{};
      [window.DEUTSCH_TESTS[KEY], window.DEUTSCH_LESSONS[KEY], window.LESSONS[KEY]].forEach(function(o){
        if(!o)return;
        o.title=TITLE;
        o.name=TITLE;
        o.label=TITLE;
        o.buttonTitle=TITLE;
        o.displayTitle=TITLE;
        o.topic=TOPIC;
        o.meta=TOPIC;
        o.category='Bevor Schreiben';
        o.source=SOURCE;
        if(o.long && !/^\s*<h3[^>]*>\s*Selbstoptimierung durch Vorbilder/i.test(String(o.long))){
          o.long='<h3>'+TITLE+'</h3>'+o.long;
        }
        if(o.lessonLong && !/^\s*<h3[^>]*>\s*Selbstoptimierung durch Vorbilder/i.test(String(o.lessonLong))){
          o.lessonLong='<h3>'+TITLE+'</h3>'+o.lessonLong;
        }
        if(o.longLesson && !/^\s*<h3[^>]*>\s*Selbstoptimierung durch Vorbilder/i.test(String(o.longLesson))){
          o.longLesson='<h3>'+TITLE+'</h3>'+o.longLesson;
        }
        if(o.contentLong && !/^\s*<h3[^>]*>\s*Selbstoptimierung durch Vorbilder/i.test(String(o.contentLong))){
          o.contentLong='<h3>'+TITLE+'</h3>'+o.contentLong;
        }
      });
      if(window.DEUTSCH_TESTS[KEY]){
        window.DEUTSCH_TESTS[KEY].title=TITLE;
        window.DEUTSCH_TESTS[KEY].topic=TOPIC;
        window.DEUTSCH_TESTS[KEY].category='Bevor Schreiben';
      }
      var lc=document.getElementById('lessonContent');
      var lt=document.getElementById('lessonTitle');
      var lm=document.getElementById('lessonMeta');
      if(lc && /Selbstoptimierung durch Vorbilder/i.test(lc.innerHTML||'')){
        if(lt)lt.textContent=TITLE;
        if(lm)lm.textContent=TOPIC;
      }
      if(typeof renderTests==='function' && window.selectedCategory==='Bevor Schreiben')renderTests('Bevor Schreiben');
    }catch(e){console.error('selbstoptimierung title fix failed',e)}
  }
  window.__selbstoptimierungTitleFix=fix;
  fix();
  setTimeout(fix,300);setTimeout(fix,1000);setTimeout(fix,2500);setTimeout(fix,6000);
})();
