(function(){
  function safe(v){return String(v||'').replace(/[&<>]/g,function(c){return {'&':'&amp;','<':'&lt;','>':'&gt;'}[c]});}
  function ensureData(){
    window.DEUTSCH_TESTS=window.DEUTSCH_TESTS||{};
    window.DEUTSCH_LESSONS=window.DEUTSCH_LESSONS||{};
    if(!window.DEUTSCH_TESTS.t30){
      window.DEUTSCH_TESTS.t30={category:'Bevor Schreiben',slug:'lebenslanges_lernen_nachteile_c1_c2',title:'Lebenslanges Lernen – Nachteile · C1/C2 Nachteilsabsatz',topic:'Nachteile des lebenslangen Lernens: Leistungsdruck, Zeitmangel, soziale Ungleichheit, Orientierungslosigkeit',words:['das lebenslange Lernen','der Leistungsdruck','die Überforderung','die Doppelbelastung','die Work-Life-Balance','die soziale Ungleichheit','die digitale Spaltung','der Zertifikatsdruck','die Orientierungslosigkeit']};
    }
    window.DEUTSCH_TESTS.t30.category='Bevor Schreiben';
    window.DEUTSCH_TESTS.t30.title='Lebenslanges Lernen – Nachteile · C1/C2 Nachteilsabsatz';
    if(!window.DEUTSCH_LESSONS.t30){
      window.DEUTSCH_LESSONS.t30={
        short:'<h3>Lebenslanges Lernen – Nachteile · Kurz</h3><p><b>Grundthese:</b> Lebenslanges Lernen kann berufliche Anpassung ermöglichen, aber auch Leistungsdruck, Zeitmangel, soziale Ungleichheit und Orientierungslosigkeit erzeugen.</p>',
        medium:'<h3>Lebenslanges Lernen – Nachteile · Mittel</h3><p>Die wichtigsten Nachteile sind dauerhafter Leistungsdruck, Doppelbelastung durch Beruf und Lernen, ungleicher Zugang zu Weiterbildung sowie Zertifikatsdruck und Orientierungslosigkeit.</p>',
        long:'<h3>Lebenslanges Lernen – Nachteile · Lang</h3><p>Die lange Word-Version konnte nicht vollständig geladen werden. Bitte Seite neu öffnen.</p>'
      };
    }
  }
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
  function injectButton(){
    ensureData();
    var list=document.getElementById('testList');
    if(!list||document.querySelector('input[name="tc"][value="t30"]'))return;
    var t=window.DEUTSCH_TESTS.t30;
    var label=document.createElement('label');
    label.className='opt';
    label.style.display='block';
    label.style.margin='8px 0';
    label.innerHTML='<input type="radio" name="tc" value="t30"> <b>'+safe(t.title)+'</b><br><span class="muted">'+safe(t.topic)+'</span>';
    var input=label.querySelector('input');
    function choose(){input.checked=true;try{selected='t30'}catch(e){};var m=document.getElementById('modeControls');if(m)m.classList.remove('hide');}
    input.addEventListener('change',choose);
    label.addEventListener('click',choose);
    var ind=document.querySelector('input[name="tc"][value="t29"]');
    var team=document.querySelector('input[name="tc"][value="t28"]');
    if(ind&&ind.closest('label'))ind.closest('label').after(label);
    else if(team&&team.closest('label'))team.closest('label').after(label);
    else list.appendChild(label);
  }
  function render(level){
    ensureData();
    var tests=window.DEUTSCH_TESTS||{};
    var lessons=window.DEUTSCH_LESSONS||{};
    var test=tests.t30||{};
    var lesson=lessons.t30&&lessons.t30[level];
    if(!lesson)return false;
    if(typeof hide==='function')hide();
    document.getElementById('lesson').classList.remove('hide');
    document.getElementById('lessonTitle').textContent='Konu anlatımı: '+(test.title||'Lebenslanges Lernen – Nachteile · C1/C2 Nachteilsabsatz');
    document.getElementById('lessonMeta').textContent='Seviye: '+(level==='short'?'Kısa':level==='medium'?'Orta':'Uzun')+' · Word dosyasına göre tam konu anlatımı';
    var words=(test.words||[]).slice(0,level==='short'?8:level==='medium'?18:44).map(function(w){return '<li>'+safe(w)+'</li>';}).join('');
    document.getElementById('lessonContent').innerHTML='<section style="padding:14px;border:1px solid #d8d3ca;border-radius:14px;background:#fff;margin-bottom:18px"><h2>1. Genel bakış</h2><p><b>Thema:</b> '+safe(test.topic||'Lebenslanges Lernen – Nachteile')+'</p>'+(words?'<h3>Öncelikli kavramlar</h3><ul>'+words+'</ul>':'')+'</section><section style="padding:14px;border:1px solid #d8d3ca;border-radius:14px;background:#fff;margin-bottom:18px"><h2>2. Konu açıklaması</h2>'+lesson+'</section>';
    document.getElementById('lesson').scrollIntoView({behavior:'smooth'});
    return true;
  }
  document.addEventListener('click',function(ev){
    var btn=ev.target&&ev.target.closest&&ev.target.closest('#btnLessonShort,#btnLessonMedium,#btnLessonLong');
    var level=levelFromButton(btn);
    if(!level)return;
    if(currentKey()!=='t30')return;
    ev.preventDefault();
    ev.stopPropagation();
    ev.stopImmediatePropagation();
    setTimeout(function(){render(level);},0);
    return false;
  },true);
  document.addEventListener('DOMContentLoaded',function(){ensureData();injectButton();});
  setInterval(function(){ensureData();injectButton();},700);
  window.forceLebenslangesLernenLesson=render;
})();
