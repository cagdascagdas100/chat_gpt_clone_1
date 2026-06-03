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
  function renderIndividualitaet(level){
    var tests=window.DEUTSCH_TESTS||{};
    var lessons=window.DEUTSCH_LESSONS||{};
    var test=tests.t29||{};
    var lesson=lessons.t29&&lessons.t29[level];
    if(!lesson){
      lesson='<h3>Individualität – Nachteile</h3><p>Individualität kann persönliche Freiheit ermöglichen, kann aber problematisch werden, wenn sie zu Egoismus, sozialer Distanz, Leistungsdruck oder Anpassungsproblemen führt.</p>';
    }
    if(typeof hide==='function')hide();
    document.getElementById('lesson').classList.remove('hide');
    document.getElementById('lessonTitle').textContent='Konu anlatımı: '+(test.title||'Individualität – Nachteile · C1/C2 Nachteilsabsatz');
    document.getElementById('lessonMeta').textContent='Seviye: '+(level==='short'?'Kısa':level==='medium'?'Orta':'Uzun')+' · Word dosyasına göre tam konu anlatımı';
    var words=(test.words||[]).slice(0,level==='short'?8:level==='medium'?18:32).map(function(w){return '<li>'+safe(w)+'</li>';}).join('');
    document.getElementById('lessonContent').innerHTML='<section style="padding:14px;border:1px solid #d8d3ca;border-radius:14px;background:#fff;margin-bottom:18px"><h2>1. Genel bakış</h2><p><b>Thema:</b> '+safe(test.topic||'Individualität – Nachteile')+'</p>'+(words?'<h3>Öncelikli kavramlar</h3><ul>'+words+'</ul>':'')+'</section><section style="padding:14px;border:1px solid #d8d3ca;border-radius:14px;background:#fff;margin-bottom:18px"><h2>2. Konu açıklaması</h2>'+lesson+'</section>';
    document.getElementById('lesson').scrollIntoView({behavior:'smooth'});
  }
  function bind(){
    [['btnLessonShort','short'],['btnLessonMedium','medium'],['btnLessonLong','long']].forEach(function(pair){
      var btn=document.getElementById(pair[0]);
      if(!btn||btn.dataset.teamarbeitIndividualitaetForce==='1')return;
      btn.dataset.teamarbeitIndividualitaetForce='1';
      btn.addEventListener('click',function(ev){
        if(key()==='t28'){
          ev.preventDefault();
          ev.stopImmediatePropagation();
          render(pair[1]);
          return false;
        }
        if(key()==='t29'){
          ev.preventDefault();
          ev.stopImmediatePropagation();
          renderIndividualitaet(pair[1]);
          return false;
        }
      },true);
    });
  }
  function loadIndividualitaetData(){
    if((window.DEUTSCH_TESTS||{}).t29)return;
    if(document.querySelector('script[data-individualitaet-nachteile="1"]'))return;
    var s=document.createElement('script');
    s.src='data_bevor_individualitaet_nachteile.js?v=1';
    s.dataset.individualitaetNachteile='1';
    s.onload=function(){setTimeout(injectIndividualitaetOption,100);};
    document.head.appendChild(s);
  }
  function injectIndividualitaetOption(){
    var tests=window.DEUTSCH_TESTS||{};
    var t=tests.t29;
    if(!t)return;
    var list=document.getElementById('testList');
    if(!list||document.querySelector('input[name="tc"][value="t29"]'))return;
    var txt=list.textContent||'';
    if(txt.indexOf('Teamarbeit')<0&&txt.indexOf('Bevor Schreiben')<0&&txt.indexOf('Mindestlohn')<0)return;
    var label=document.createElement('label');
    label.className='opt';
    label.style.display='block';
    label.style.margin='8px 0';
    label.innerHTML='<input type="radio" name="tc" value="t29"> <b>'+safe(t.title)+'</b><br><span class="muted">'+safe(t.topic)+'</span>';
    var input=label.querySelector('input');
    input.addEventListener('change',function(){try{selected='t29'}catch(e){};var m=document.getElementById('modeControls');if(m)m.classList.remove('hide');});
    label.addEventListener('click',function(){input.checked=true;try{selected='t29'}catch(e){};var m=document.getElementById('modeControls');if(m)m.classList.remove('hide');});
    var team=document.querySelector('input[name="tc"][value="t28"]');
    if(team&&team.closest('label')) team.closest('label').after(label); else list.appendChild(label);
  }
  document.addEventListener('DOMContentLoaded',function(){bind();loadIndividualitaetData();setTimeout(injectIndividualitaetOption,500);});
  setInterval(function(){bind();loadIndividualitaetData();injectIndividualitaetOption();},700);
  window.forceTeamarbeitLesson=render;
  window.forceIndividualitaetLesson=renderIndividualitaet;
})();
