(function(){
  window.DEUTSCH_TESTS=window.DEUTSCH_TESTS||{};
  window.DEUTSCH_LESSONS=window.DEUTSCH_LESSONS||{};
  window.LESSONS=window.LESSONS||{};
  var WRITE_IDS={t4:1,t5:1,t6:1,t7:1,t8:1,t9:1,t10:1,t11:1,t12:1,t13:1};
  var GRAMMAR_IDS={t14:1,t15:1};
  var NVV_IDS={t16:1,t17:1,t18:1};
  var BEFORE_IDS={t19:1,t20:1,t21:1,t22:1,t23:1,t24:1,t25:1,t26:1,t27:1,t28:1,t29:1,t30:1,t31:1,t32:1,t33:1,t34:1,t35:1,t36:1,t37:1,t38:1,t39:1};
  function setCat(id,cat){ if(window.DEUTSCH_TESTS[id]) window.DEUTSCH_TESTS[id].category=cat; }
  function applyCats(){
    Object.keys(WRITE_IDS).forEach(function(id){setCat(id,'Schreiben Fehlern')});
    Object.keys(GRAMMAR_IDS).forEach(function(id){setCat(id,'Genel Grammer')});
    Object.keys(NVV_IDS).forEach(function(id){setCat(id,'NVV')});
    Object.keys(BEFORE_IDS).forEach(function(id){setCat(id,'Bevor Schreiben')});
  }
  function stripBad(html){
    var s=String(html||'');
    s=s.replace(/<section[^>]*(anti-repeat-v4|unique-source-expansion|unique-long-expansion|no-repeat-1400|completion-booster|auto-fill)[\s\S]*?<\/section>/gi,'');
    s=s.replace(/<h[1-6][^>]*>\s*(Benzersiz[^<]*|Quellennahe[^<]*|Ergänzende zweite Perspektive[^<]*|Zusätzliche[^<]*|C1\/C2-Prüfungsvertiefung[^<]*)[\s\S]*?(?=<h[1-6]|<section|$)/gi,'');
    s=s.replace(/<p[^>]*>\s*<b>[^<]*:<\/b>\s*Bu nokta,[\s\S]*?<\/p>/gi,'');
    s=s.replace(/<p[^>]*>[^<]*(?:Dieser Aspekt sollte im Aufsatz mit dem Kontext|Zunächst kann beschrieben werden, woran man|Danach folgt die Erklärung, warum dieser Punkt|Abschließend lässt sich zeigen, wie|So entsteht ein eigenständiger Abschnitt)[\s\S]*?<\/p>/gi,'');
    s=s.replace(/<p[^>]*>[^<]*(?:konkreter Prüfungsbezug|eigener Beispiel- und Bewertungssatz statt Standardformel|Bu bölüm kaynak dosyadaki ana hatları|yalnızca eksik kalan açıklama alanını tamamlar)[\s\S]*?<\/p>/gi,'');
    s=s.replace(/<table[^>]*class="source-table"[\s\S]*?<\/table>/gi,'');
    s=s.replace(/<h5[^>]*>\s*(Ayırt edici kavram haritası|Konuya özel açıklama|Prüfungsnaher Transfer)\s*<\/h5>/gi,'');
    return s;
  }
  function cleanLessons(){
    var ids=['t4','t5','t6','t7','t8','t9','t10','t11','t12','t13','t14','t15','t16','t17','t18','t20'];
    ids.forEach(function(id){
      [window.DEUTSCH_LESSONS[id],window.LESSONS[id]].forEach(function(o){
        if(!o) return;
        ['long','lessonLong','longLesson','contentLong'].forEach(function(k){ if(o[k]) o[k]=stripBad(o[k]); });
      });
    });
  }
  window.__uniqueLongNoRepeatGuard=function(){};
  window.__ensureUniqueLongLessons1400=function(){};
  window.__finalAntiRepeatLongGuard=function(){};
  window.__ensureAllLongLessons1500=function(){};
  window.__ensureAllLongLessons1500Final=function(){};
  window.catOf=function(t){
    if(t&&t.category==='Genel Grammer') return 'Genel Grammer';
    if(t&&t.category==='NVV') return 'NVV';
    if(t&&t.category==='Bevor Schreiben') return 'Bevor Schreiben';
    return 'Schreiben Fehlern';
  };
  function run(){
    applyCats();
    cleanLessons();
    try{ if(window.selectedCategory==='Schreiben Fehlern' && typeof window.renderTests==='function') window.renderTests('Schreiben Fehlern'); }catch(e){}
  }
  window.__finalSchreibenFehlernCleanup=run;
  run();
  [500,1500,3500,6500,9500].forEach(function(t){setTimeout(run,t)});
  if(document.addEventListener) document.addEventListener('DOMContentLoaded',function(){setTimeout(run,800);setTimeout(run,4200);});
})();