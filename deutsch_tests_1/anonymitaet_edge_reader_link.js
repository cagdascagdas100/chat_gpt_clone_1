(function(){
  var URL='reader_anonymitaet_vorteile.html';
  var BOX='<div style="border:1px solid #c5dfe3;background:#eef7f8;border-radius:12px;padding:12px;margin:12px 0;font-family:Arial,sans-serif"><b>Edge Sesli Oku / Okuma Modu:</b> Bu ana test sayfası JavaScript ile çalıştığı için Edge Reader bazen boş açılır. Sesli anlatım için <a href="'+URL+'" target="_blank" rel="noopener">statik okuma sayfasını aç</a>, sonra Edge’de <b>Sesli oku</b> veya <b>Okuma Modu</b> kullan.</div>';
  function add(){
    var L=window.DEUTSCH_LESSONS&&window.DEUTSCH_LESSONS.t39;
    if(!L){setTimeout(add,250);return;}
    ['short','lessonShort','contentShort','medium','lessonMedium','contentMedium','long','lessonLong','longLesson','contentLong'].forEach(function(k){
      if(typeof L[k]==='string' && L[k].indexOf(URL)<0){ L[k]=BOX+L[k]; }
    });
    try{ if(typeof renderTests==='function' && window.selectedCategory==='Bevor Schreiben') renderTests('Bevor Schreiben'); }catch(e){}
  }
  add(); setTimeout(add,700); setTimeout(add,2000); setTimeout(add,5000);
})();