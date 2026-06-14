(function(){
  var KEY='t35';
  window.DEUTSCH_TESTS=window.DEUTSCH_TESTS||{};
  window.DEUTSCH_LESSONS=window.DEUTSCH_LESSONS||{};
  window.LESSONS=window.LESSONS||{};

  if(window.DEUTSCH_TESTS[KEY]){
    window.DEUTSCH_TESTS[KEY].cat='Bevor Schreiben';
    window.DEUTSCH_TESTS[KEY].category='Bevor Schreiben';
    window.DEUTSCH_TESTS[KEY].slug='online_studium_vorteile_c1_c2';
    window.DEUTSCH_TESTS[KEY].title='Online-Studium – Vorteile · C1/C2 Vorteilsabsatz';
  }

  if(window.LESSONS[KEY] && window.LESSONS[KEY].long){
    window.DEUTSCH_LESSONS[KEY]=window.DEUTSCH_LESSONS[KEY]||{};
    window.DEUTSCH_LESSONS[KEY].long=window.LESSONS[KEY].long;
  }
  if(window.DEUTSCH_LESSONS[KEY] && window.DEUTSCH_LESSONS[KEY].long){
    window.LESSONS[KEY]=window.LESSONS[KEY]||{};
    window.LESSONS[KEY].long=window.DEUTSCH_LESSONS[KEY].long;
  }

  function esc(s){return String(s||'').replace(/[&<>']/g,function(c){return {'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#039;'}[c]});}
  function catOfLocal(t){return (t&&((t.cat||t.category)==='Bevor Schreiben'||t.category==='Bevor Schreiben'))?'Bevor Schreiben':(t&&t.category)||'Schreiben Fehlern';}
  function buildFallbackMenu(){
    var list=document.getElementById('testList');
    if(!list)return;
    var tests=window.DEUTSCH_TESTS||{};
    var entries=Object.entries(tests).filter(function(pair){return catOfLocal(pair[1])==='Bevor Schreiben';});
    if(!entries.length)return;
    list.innerHTML='<p><button class="ghost" id="backCats">← Ana başlıklara dön</button></p><h2>Bevor Schreiben</h2><p class="muted">Bu ana başlık altındaki testi seç. Ardından konu anlatımı, test uzunluğu veya harf kutucukları modunu aç.</p>'+entries.map(function(pair,i){var k=pair[0],t=pair[1];return '<label class="opt"><input type="radio" name="tc" value="'+k+'" '+(i===0?'checked':'')+'> <b>'+esc(t.title)+'</b><br><span class="muted">'+esc(t.topic||'')+'</span></label>';}).join('');
    window.selected=entries[0][0];
    var mc=document.getElementById('modeControls'); if(mc)mc.classList.remove('hide');
    Array.prototype.forEach.call(document.querySelectorAll('input[name="tc"]'),function(e){e.onchange=function(){window.selected=e.value;};});
    var back=document.getElementById('backCats'); if(back && typeof window.renderCategoryChoice==='function') back.onclick=function(){try{window.renderCategoryChoice();}catch(e){}};
  }
  function rescue(){
    var header=document.querySelector('header'); if(header){header.style.display='block';header.classList.remove('hide');}
    var main=document.querySelector('main'); if(main){main.style.display='block';main.classList.remove('hide');}
    var start=document.getElementById('start'); if(start){start.style.display='block';start.classList.remove('hide');}
    var list=document.getElementById('testList');
    var empty=!list||!String(list.textContent||'').trim()||/Testliste wird geladen/i.test(list.textContent||'');
    if(empty){
      if(typeof window.renderCategoryChoice==='function'){
        try{window.renderCategoryChoice();}catch(e){buildFallbackMenu();}
      }else{
        buildFallbackMenu();
      }
    }
  }
  if(document.readyState==='loading'){
    document.addEventListener('DOMContentLoaded',function(){setTimeout(rescue,100);setTimeout(rescue,900);});
  }else{
    setTimeout(rescue,100);setTimeout(rescue,900);
  }
})();
