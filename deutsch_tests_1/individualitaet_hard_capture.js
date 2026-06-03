(function(){
  function currentKey(){
    var checked=document.querySelector('input[name="tc"]:checked');
    if(checked&&checked.value)return checked.value;
    try{if(typeof selected!=='undefined')return selected}catch(e){}
    return '';
  }
  function levelFromButton(el){
    if(!el)return null;
    var id=el.id||'';
    if(id==='btnLessonShort')return 'short';
    if(id==='btnLessonMedium')return 'medium';
    if(id==='btnLessonLong')return 'long';
    return null;
  }
  function render(level){
    if(typeof window.forceIndividualitaetLesson==='function'){
      window.forceIndividualitaetLesson(level);
      return true;
    }
    var lessons=window.DEUTSCH_LESSONS||{};
    var tests=window.DEUTSCH_TESTS||{};
    var lesson=lessons.t29&&lessons.t29[level];
    var test=tests.t29||{};
    if(!lesson)return false;
    function safe(v){return String(v||'').replace(/[&<>]/g,function(c){return {'&':'&amp;','<':'&lt;','>':'&gt;'}[c]});}
    if(typeof hide==='function')hide();
    document.getElementById('lesson').classList.remove('hide');
    document.getElementById('lessonTitle').textContent='Konu anlatımı: '+(test.title||'Individualität – Nachteile · C1/C2 Nachteilsabsatz');
    document.getElementById('lessonMeta').textContent='Seviye: '+(level==='short'?'Kısa':level==='medium'?'Orta':'Uzun')+' · tam Word yapısı';
    var words=(test.words||[]).slice(0,level==='short'?8:level==='medium'?18:32).map(function(w){return '<li>'+safe(w)+'</li>';}).join('');
    document.getElementById('lessonContent').innerHTML='<section style="padding:14px;border:1px solid #d8d3ca;border-radius:14px;background:#fff;margin-bottom:18px"><h2>1. Genel bakış</h2><p><b>Thema:</b> '+safe(test.topic||'Individualität – Nachteile')+'</p>'+(words?'<h3>Öncelikli kavramlar</h3><ul>'+words+'</ul>':'')+'</section><section style="padding:14px;border:1px solid #d8d3ca;border-radius:14px;background:#fff;margin-bottom:18px"><h2>2. Konu açıklaması</h2>'+lesson+'</section>';
    document.getElementById('lesson').scrollIntoView({behavior:'smooth'});
    return true;
  }
  document.addEventListener('click',function(ev){
    var btn=ev.target&&ev.target.closest&&ev.target.closest('#btnLessonShort,#btnLessonMedium,#btnLessonLong');
    var level=levelFromButton(btn);
    if(!level)return;
    if(currentKey()!=='t29')return;
    ev.preventDefault();
    ev.stopPropagation();
    ev.stopImmediatePropagation();
    setTimeout(function(){render(level);},0);
    return false;
  },true);
  document.addEventListener('DOMContentLoaded',function(){
    if(!window.DEUTSCH_TESTS||!window.DEUTSCH_TESTS.t29){
      var s=document.createElement('script');
      s.src='data_bevor_individualitaet_nachteile.js?v=2';
      document.head.appendChild(s);
    }
  });
})();
