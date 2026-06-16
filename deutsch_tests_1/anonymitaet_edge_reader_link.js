(function(){
  var URL='reader_anonymitaet_vorteile_edge_plain.html';
  var BOX='<div style="border:2px solid #0f3d48;background:#eef7f8;border-radius:12px;padding:14px;margin:14px 0;font-family:Arial,sans-serif"><b>Edge Sesli Oku / Okuma Modu:</b> Test sayfası JavaScript ile çalıştığı için Edge Reader bazen boş açılır. Sesli anlatım için <a href="'+URL+'" target="_blank" rel="noopener" style="font-weight:700;color:#0f3d48;text-decoration:underline">sade statik okuma sayfasını aç</a>. Açılan sayfada Edge’de <b>Sesli oku</b> veya <b>Okuma Modu</b> kullan.</div>';
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
