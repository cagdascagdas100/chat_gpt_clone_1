(function(){
  var KEY='t33';
  function safe(v){return String(v||'').replace(/[&<>]/g,function(c){return {'&':'&amp;','<':'&lt;','>':'&gt;'}[c]});}
  function dataReady(){
    window.DEUTSCH_TESTS=window.DEUTSCH_TESTS||{};
    var t=window.DEUTSCH_TESTS[KEY];
    if(!t)return false;
    t.category='Bevor Schreiben';
    t.title='Fertiggerichte – Vorteile · C1/C2 Vorteilsabsatz';
    return true;
  }
  function checkedKey(){
    var c=document.querySelector('input[name="tc"]:checked');
    if(c&&c.value)return c.value;
    try{if(typeof selected!=='undefined')return selected}catch(e){}
    return '';
  }
  function isCategoryHome(){
    var box=document.getElementById('testList');
    if(!box)return false;
    if(box.querySelector('#catBefore')||box.querySelector('#catGrammar')||box.querySelector('#catWrite')||box.querySelector('#catNVV'))return true;
    var h=String((box.querySelector('h2')||{}).textContent||'').trim();
    return h.indexOf('İlk olarak ana başlığı seç')!==-1 || h.indexOf('Ilk olarak ana başlığı seç')!==-1;
  }
  function isBevorList(){
    var box=document.getElementById('testList');
    if(!box||isCategoryHome())return false;
    var h=String((box.querySelector('h2')||{}).textContent||'').trim();
    var hasBack=!!box.querySelector('#backCats');
    return hasBack && h==='Bevor Schreiben';
  }
  function labels(){return Array.prototype.slice.call(document.querySelectorAll('input[name="tc"][value="'+KEY+'']")).map(function(i){return i.closest('label');}).filter(Boolean);}
  function removeWrongPlace(){
    if(isBevorList())return;
    labels().forEach(function(l){l.remove();});
    var m=document.getElementById('modeControls');
    if(checkedKey()===KEY){
      try{selected=''}catch(e){}
      if(m)m.classList.add('hide');
    }
  }
  function choose(input){input.checked=true;try{selected=KEY}catch(e){}var m=document.getElementById('modeControls');if(m)m.classList.remove('hide');}
  function place(){
    var box=document.getElementById('testList');
    if(!box||!dataReady())return;
    if(!isBevorList()){
      removeWrongPlace();
      return;
    }
    var existing=labels();
    if(existing.length>1){existing.slice(1).forEach(function(l){l.remove();});}
    if(existing.length===1){existing[0].dataset.fertiggerichteFix='1';return;}
    var t=window.DEUTSCH_TESTS[KEY];
    var l=document.createElement('label');
    l.className='opt';
    l.style.display='block';
    l.style.margin='8px 0';
    l.dataset.fertiggerichteFix='1';
    l.innerHTML='<input type="radio" name="tc" value="'+KEY+'"> <b>'+safe(t.title)+'</b><br><span class="muted">'+safe(t.topic||'Fertiggerichte – Vorteile')+'</span>';
    var input=l.querySelector('input');
    input.addEventListener('change',function(){choose(input);});
    l.addEventListener('click',function(){choose(input);});
    var after=null, anchors=['t32','t31','t30','t29','t28','t27','t26','t25','t24'];
    for(var n=0;n<anchors.length;n++){var a=document.querySelector('input[name="tc"][value="'+anchors[n]+'"]');if(a&&a.closest('label')){after=a.closest('label');break;}}
    if(after)after.after(l);else box.appendChild(l);
  }
  function longClick(e){
    var b=e.target&&e.target.closest&&e.target.closest('#btnLessonLong');
    if(!b||checkedKey()!==KEY)return;
    if(typeof window.forceFertiggerichteVorteileWordFull==='function'){
      e.preventDefault();e.stopPropagation();e.stopImmediatePropagation();
      setTimeout(function(){window.forceFertiggerichteVorteileWordFull('long');},0);
      return false;
    }
  }
  document.addEventListener('click',longClick,true);
  document.addEventListener('DOMContentLoaded',function(){setTimeout(removeWrongPlace,50);setTimeout(place,250);setTimeout(removeWrongPlace,600);});
  setInterval(function(){removeWrongPlace();place();},350);
  window.AAYS_FERTIGGERICHTE_BEFORE_FIX={place:place,removeWrongPlace:removeWrongPlace,isBevorList:isBevorList,isCategoryHome:isCategoryHome};
})();