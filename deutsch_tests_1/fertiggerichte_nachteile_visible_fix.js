(function(){
  var KEY='t34';
  function ready(){
    window.DEUTSCH_TESTS=window.DEUTSCH_TESTS||{};
    window.DEUTSCH_LESSONS=window.DEUTSCH_LESSONS||{};
    var t=window.DEUTSCH_TESTS[KEY];
    if(!t)return false;
    t.category='Bevor Schreiben';
    t.slug='fertiggerichte_nachteile_c1_c2';
    t.title='Fertiggerichte – Nachteile · C1/C2 Nachteilsabsatz';
    t.topic=t.topic||'Erörterung · Nachteile von Fertiggerichten · Gesundheit · Kochkompetenz · Umwelt · Transparenz · industrielle Ernährung';
    return true;
  }
  function esc(s){return String(s||'').replace(/[&<>]/g,function(c){return {'&':'&amp;','<':'&lt;','>':'&gt;'}[c];});}
  function isBevorList(){
    var box=document.getElementById('testList');
    if(!box)return false;
    var h=String((box.querySelector('h2')||{}).textContent||'').trim();
    return h==='Bevor Schreiben';
  }
  function choose(input){
    input.checked=true;
    try{ selected=KEY; }catch(e){}
    var m=document.getElementById('modeControls');
    if(m)m.classList.remove('hide');
  }
  function place(){
    if(!ready()||!isBevorList())return;
    var box=document.getElementById('testList');
    if(!box)return;
    var existing=box.querySelector('input[name="tc"][value="'+KEY+'"]');
    if(existing){
      var lab=existing.closest('label');
      if(lab){ lab.style.display='block'; lab.dataset.fertiggerichteNachteileVisible='1'; }
      return;
    }
    var t=window.DEUTSCH_TESTS[KEY];
    var lab=document.createElement('label');
    lab.className='opt';
    lab.style.display='block';
    lab.dataset.fertiggerichteNachteileVisible='1';
    lab.innerHTML='<input type="radio" name="tc" value="'+KEY+'"> <b>'+esc(t.title)+'</b><br><span class="muted">'+esc(t.topic)+'</span>';
    var input=lab.querySelector('input');
    input.addEventListener('change',function(){choose(input);});
    lab.addEventListener('click',function(){choose(input);});
    var after=null;
    var vorteil=box.querySelector('input[name="tc"][value="t33"]');
    if(vorteil&&vorteil.closest('label'))after=vorteil.closest('label');
    if(after)after.after(lab);else box.appendChild(lab);
  }
  document.addEventListener('click',function(){setTimeout(place,60);},true);
  document.addEventListener('DOMContentLoaded',function(){setTimeout(place,200);});
  window.AAYS_FERTIGGERICHTE_NACHTEILE_VISIBLE={place:place};
})();
