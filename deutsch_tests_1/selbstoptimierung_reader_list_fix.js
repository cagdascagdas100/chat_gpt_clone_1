(function(){
  var KEY='t40';
  var readerUrl='reader_selbstoptimierung_vorteile_edge_plain.html';
  function ulToReadable(html){
    if(!html)return html;
    return String(html).replace(/<ul>([\s\S]*?)<\/ul>/g,function(_,inner){
      var items=[];
      inner.replace(/<li>([\s\S]*?)<\/li>/g,function(__,li){
        var clean=li.replace(/<[^>]+>/g,'').replace(/\s+/g,' ').trim();
        if(clean)items.push('<p class="reader-bullet">• '+clean+'</p>');
      });
      return '<div class="reader-readable-list">'+items.join('')+'</div>';
    });
  }
  function ensureReaderLink(html){
    if(!html)return html;
    if(/reader_selbstoptimierung_vorteile_edge_plain\.html/.test(html))return html;
    var box='<div class="reader-note" style="border:1px solid #bfdbfe;background:#eff6ff;border-radius:12px;padding:12px;margin:12px 0"><b>Edge / Chrome sesli okuma:</b> Bu dinamik sayfada bazı liste maddeleri Okuma Modu tarafından atlanırsa <a href="'+readerUrl+'" target="_blank" rel="noopener">Selbstoptimierung için sade okuma sayfasını aç</a>. Bu bağlantıdaki metin JavaScript olmadan, doğrudan okunabilir HTML olarak hazırlanmıştır.</div>';
    return box+html;
  }
  function fixObj(o){
    if(!o)return;
    ['long','lessonLong','longLesson','contentLong'].forEach(function(k){
      if(o[k])o[k]=ensureReaderLink(ulToReadable(o[k]));
    });
  }
  function fixDom(){
    var lc=document.getElementById('lessonContent');
    if(!lc || !/Selbstoptimierung durch Vorbilder/i.test(lc.innerHTML||''))return;
    if(!lc.querySelector('.reader-note')){
      var d=document.createElement('div');
      d.className='reader-note';
      d.style.cssText='border:1px solid #bfdbfe;background:#eff6ff;border-radius:12px;padding:12px;margin:12px 0';
      d.innerHTML='<b>Edge / Chrome sesli okuma:</b> Eğer Okuma Modu maddeleri atlıyorsa <a href="'+readerUrl+'" target="_blank" rel="noopener">sade okuma sayfasını aç</a>.';
      lc.insertBefore(d,lc.firstChild);
    }
    Array.prototype.slice.call(lc.querySelectorAll('ul')).forEach(function(ul){
      if(ul.getAttribute('data-reader-fixed'))return;
      var div=document.createElement('div');
      div.className='reader-readable-list';
      Array.prototype.slice.call(ul.querySelectorAll('li')).forEach(function(li){
        var p=document.createElement('p');
        p.className='reader-bullet';
        p.textContent='• '+li.textContent.replace(/\s+/g,' ').trim();
        div.appendChild(p);
      });
      ul.parentNode.replaceChild(div,ul);
    });
  }
  function fix(){
    try{
      window.DEUTSCH_TESTS=window.DEUTSCH_TESTS||{};
      window.DEUTSCH_LESSONS=window.DEUTSCH_LESSONS||{};
      window.LESSONS=window.LESSONS||{};
      fixObj(window.DEUTSCH_TESTS[KEY]);
      fixObj(window.DEUTSCH_LESSONS[KEY]);
      fixObj(window.LESSONS[KEY]);
      fixDom();
    }catch(e){console.error('selbstoptimierung reader list fix failed',e)}
  }
  window.__selbstoptimierungReaderListFix=fix;
  fix();
  setTimeout(fix,300);setTimeout(fix,1000);setTimeout(fix,2500);setTimeout(fix,5000);setTimeout(fix,9000);
})();
