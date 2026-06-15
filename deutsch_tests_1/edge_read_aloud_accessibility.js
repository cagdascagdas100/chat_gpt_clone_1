(function(){
  'use strict';
  var STYLE_ID='edge-reader-style';
  function addStyle(){
    if(document.getElementById(STYLE_ID)) return;
    var s=document.createElement('style');
    s.id=STYLE_ID;
    s.textContent='\n.edge-reader-only{position:absolute!important;left:-10000px!important;top:auto!important;width:1px!important;height:1px!important;overflow:hidden!important;white-space:normal!important}\n.edge-reader-toggle{margin:10px 0 12px 0;padding:10px 13px;border-radius:10px;border:1px solid #183642;background:#fff;color:#183642;font-weight:bold;cursor:pointer}\n.edge-reader-visible{position:static!important;width:auto!important;height:auto!important;overflow:visible!important;left:auto!important;border:1px solid #d8d3ca;border-radius:14px;background:#fffaf0;padding:14px;margin:14px 0;white-space:normal!important}\n.edge-reader-visible h2{margin-top:0}\n';
    document.head.appendChild(s);
  }
  function text(x){return String(x||'').replace(/\s+/g,' ').trim();}
  function esc(x){return String(x||'').replace(/[&<>]/g,function(c){return c==='&'?'&amp;':c==='<'?'&lt;':'&gt;';});}
  function tableToSpeech(tbl,idx){
    var rows=[].slice.call(tbl.rows||[]).map(function(r){return [].slice.call(r.cells||[]).map(function(c){return text(c.innerText);}).filter(Boolean);}).filter(function(r){return r.length;});
    if(!rows.length) return '';
    var out=['<section><h3>Tabelle '+idx+'</h3>'];
    var head=rows[0];
    if(head.length>1) out.push('<p>Spalten: '+esc(head.join('; '))+'.</p>');
    rows.slice(1).forEach(function(r,i){
      var bits=r.map(function(v,j){return (head[j]&&head.length>1?head[j]+': ':'')+v;});
      out.push('<p>Zeile '+(i+1)+': '+esc(bits.join('. '))+'.</p>');
    });
    if(rows.length===1) out.push('<p>'+esc(rows[0].join('. '))+'.</p>');
    out.push('</section>');
    return out.join('');
  }
  function nodeToSpeech(root){
    var clone=root.cloneNode(true);
    clone.querySelectorAll('script,style,button,input,select,textarea,.edge-reader-toggle,#edgeReaderMirror').forEach(function(n){n.remove();});
    var tableIndex=1;
    clone.querySelectorAll('table').forEach(function(t){
      var html=tableToSpeech(t,tableIndex++);
      var wrap=document.createElement('div'); wrap.innerHTML=html;
      t.replaceWith(wrap);
    });
    clone.querySelectorAll('li').forEach(function(li){
      if(!/^Punkt[:.]/i.test(text(li.textContent))) li.insertAdjacentText('afterbegin','Punkt: ');
    });
    clone.querySelectorAll('h1,h2,h3,h4,h5,h6,p,li,td,th,div').forEach(function(n){
      if(n.childNodes.length===1 && n.firstChild && n.firstChild.nodeType===3){ n.textContent=text(n.textContent); }
    });
    return clone.innerHTML;
  }
  function currentTitle(){
    var h=document.getElementById('lessonTitle');
    return text(h&&h.textContent)||'Konu anlatımı';
  }
  function buildMirror(){
    addStyle();
    var lesson=document.getElementById('lesson');
    var root=document.getElementById('lessonContent');
    if(!lesson||!root||lesson.classList.contains('hide')||!text(root.innerText)) return;
    lesson.setAttribute('role','main');
    root.setAttribute('role','article');
    root.setAttribute('itemprop','articleBody');
    root.setAttribute('lang','de');
    root.setAttribute('tabindex','0');
    var old=document.getElementById('edgeReaderMirror'); if(old) old.remove();
    var btn=document.getElementById('edgeReaderToggle'); if(btn) btn.remove();
    var mirror=document.createElement('article');
    mirror.id='edgeReaderMirror';
    mirror.className='edge-reader-only';
    mirror.lang='de';
    mirror.setAttribute('role','article');
    mirror.setAttribute('aria-label','Edge sesli okuma için semantik konu anlatımı');
    mirror.innerHTML='<h1>'+esc(currentTitle())+'</h1><p>Bu bölüm Edge sesli okuma ve Copilot sayfa okuma modu için hazırlanmış semantik metin aynasıdır. Tablolar satır satır okunur; maddeler Punkt ifadesiyle başlar.</p>'+nodeToSpeech(root);
    var toggle=document.createElement('button');
    toggle.id='edgeReaderToggle';
    toggle.className='edge-reader-toggle';
    toggle.type='button';
    toggle.textContent='Sesli okuma metnini göster / gizle';
    toggle.onclick=function(){mirror.classList.toggle('edge-reader-only');mirror.classList.toggle('edge-reader-visible');};
    root.parentNode.insertBefore(toggle,root.nextSibling);
    toggle.parentNode.insertBefore(mirror,toggle.nextSibling);
  }
  function schedule(){setTimeout(buildMirror,80);setTimeout(buildMirror,500);setTimeout(buildMirror,1400);}
  var oldStart=window.startLesson;
  if(typeof oldStart==='function' && !oldStart.__edgeReaderWrapped){
    var wrapped=function(level){var r=oldStart.apply(this,arguments);schedule();return r;};
    wrapped.__edgeReaderWrapped=true; window.startLesson=wrapped;
  }
  document.addEventListener('click',function(e){
    var id=e.target&&e.target.id;
    if(id==='btnLessonShort'||id==='btnLessonMedium'||id==='btnLessonLong') schedule();
  },true);
  document.addEventListener('DOMContentLoaded',schedule);
  new MutationObserver(function(){schedule();}).observe(document.documentElement,{childList:true,subtree:true});
  schedule();
})();
