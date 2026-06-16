(function(){
  var blocked=['lesson_unique_1400_no_repeat_guard_v4.js','lesson_long_1500_completion_booster.js'];
  function bad(src){src=String(src||'');return blocked.some(function(x){return src.indexOf(x)>=0});}
  var oldAppend=Element.prototype.appendChild;
  Element.prototype.appendChild=function(n){
    try{if(n&&String(n.tagName).toLowerCase()==='script'&&bad(n.src)){setTimeout(function(){if(n.onload)n.onload()},0);return n;}}catch(e){}
    return oldAppend.call(this,n);
  };
  function noop(){}
  function disable(){
    window.__uniqueLongNoRepeatGuard=noop;
    window.__ensureUniqueLongLessons1400=noop;
    window.__finalAntiRepeatLongGuard=noop;
    window.__ensureAllLongLessons1500=noop;
    window.__ensureAllLongLessons1500Final=noop;
  }
  function plain(s){return String(s||'').replace(/<[^>]+>/g,' ').replace(/&[^;]+;/g,' ')}
  function strip(html){
    var s=String(html||'');
    s=s.replace(/<section[^>]*(anti-repeat-v4|unique-source-expansion|unique-long-expansion|no-repeat-1400|completion-booster|auto-fill)[\s\S]*?<\/section>/gi,'');
    s=s.replace(/<table[^>]*class=["']?source-table["']?[\s\S]*?<\/table>/gi,'');
    s=s.replace(/<p[^>]*>[\s\S]*?(Bu nokta,|konkreter Prüfungsbezug|eigener Beispiel- und Bewertungssatz|Dieser Aspekt sollte im Aufsatz mit dem Kontext|Zunächst kann beschrieben werden, woran man|Danach folgt die Erklärung, warum dieser Punkt|Abschließend lässt sich zeigen, wie|So entsteht ein eigenständiger Abschnitt)[\s\S]*?<\/p>/gi,'');
    s=s.replace(/<h[1-6][^>]*>\s*(Benzersiz|Quellennahe|Ergänzende zweite Perspektive|Zusätzliche|C1\/C2-Prüfungsvertiefung)[\s\S]*?(?=<h[1-6]|<section|$)/gi,'');
    return s;
  }
  function dedupe(html){
    var seen={};
    return String(html||'').replace(/<p[^>]*>([\s\S]*?)<\/p>/gi,function(m,inner){var k=plain(inner).toLowerCase().replace(/\s+/g,' ').trim(); if(k.length>80){var key=k.slice(0,220); if(seen[key])return ''; seen[key]=1;} return m;});
  }
  function clean(){
    disable();
    ['t4','t5','t6','t7','t8','t9','t10','t11','t12','t13','t14','t15','t16','t17','t18','t20'].forEach(function(id){
      [window.DEUTSCH_LESSONS&&window.DEUTSCH_LESSONS[id],window.LESSONS&&window.LESSONS[id]].forEach(function(o){
        if(!o)return; ['long','lessonLong','longLesson','contentLong'].forEach(function(k){if(o[k])o[k]=dedupe(strip(o[k]));});
      });
    });
  }
  window.__noGenericFillersCleanup=clean;
  clean();
  [300,900,1800,3600,6200,9000].forEach(function(t){setTimeout(clean,t)});
})();
