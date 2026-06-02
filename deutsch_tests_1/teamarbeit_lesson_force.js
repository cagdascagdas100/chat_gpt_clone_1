(function(){
  function key(){
    var checked=document.querySelector('input[name="tc"]:checked');
    if(checked&&checked.value)return checked.value;
    try{if(typeof selected!=='undefined')return selected}catch(e){}
    return '';
  }
  function safe(v){return String(v||'').replace(/[&<>]/g,function(c){return {'&':'&amp;','<':'&lt;','>':'&gt;'}[c]});}
  function render(level){
    var tests=window.DEUTSCH_TESTS||{};
    var lessons=window.DEUTSCH_LESSONS||{};
    var test=tests.t28||{};
    var lesson=lessons.t28&&lessons.t28[level];
    if(!lesson){
      lesson='<h3>Teamarbeit – Nachteile</h3><p>Teamarbeit kann zwar kreative Prozesse fördern, führt jedoch häufig zu Konflikten, Zeitverlust, ungleicher Arbeitsverteilung und verwässerter Verantwortlichkeit.</p>';
    }
    if(typeof hide==='function')hide();
    document.getElementById('lesson').classList.remove('hide');
    document.getElementById('lessonTitle').textContent='Konu anlatımı: '+(test.title||'Teamarbeit – Nachteile · C1/C2 Nachteilsabsatz');
    document.getElementById('lessonMeta').textContent='Seviye: '+(level==='short'?'Kısa':level==='medium'?'Orta':'Uzun')+' · C1/C2 Nachteilsabsatz';
    var words=(test.words||[]).slice(0,level==='short'?8:level==='medium'?16:28).map(function(w){return '<li>'+safe(w)+'</li>';}).join('');
    document.getElementById('lessonContent').innerHTML='<section style="padding:14px;border:1px solid #d8d3ca;border-radius:14px;background:#fff;margin-bottom:18px"><h2>1. Genel bakış</h2><p><b>Thema:</b> '+safe(test.topic||'Teamarbeit – Nachteile')+'</p>'+(words?'<h3>Öncelikli kavramlar</h3><ul>'+words+'</ul>':'')+'</section><section style="padding:14px;border:1px solid #d8d3ca;border-radius:14px;background:#fff;margin-bottom:18px"><h2>2. Konu açıklaması</h2>'+lesson+'</section>';
    document.getElementById('lesson').scrollIntoView({behavior:'smooth'});
  }
  function bind(){
    [['btnLessonShort','short'],['btnLessonMedium','medium'],['btnLessonLong','long']].forEach(function(pair){
      var btn=document.getElementById(pair[0]);
      if(!btn||btn.dataset.teamarbeitForce==='1')return;
      btn.dataset.teamarbeitForce='1';
      btn.addEventListener('click',function(ev){
        if(key()!=='t28')return;
        ev.preventDefault();
        ev.stopImmediatePropagation();
        render(pair[1]);
        return false;
      },true);
    });
  }
  document.addEventListener('DOMContentLoaded',bind);
  setInterval(bind,500);
  window.forceTeamarbeitLesson=render;
})();
