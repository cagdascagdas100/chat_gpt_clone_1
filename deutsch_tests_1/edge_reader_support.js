(function(){
  'use strict';
  function txt(el){return (el&&el.textContent||'').replace(/\s+/g,' ').trim();}
  function markTables(root){
    root.querySelectorAll('table').forEach(function(t,i){
      if(!t.getAttribute('role')) t.setAttribute('role','table');
      if(!t.getAttribute('aria-label')) t.setAttribute('aria-label','Tabelle '+(i+1)+' der Konu anlatımı');
      t.querySelectorAll('th').forEach(function(th){ if(!th.getAttribute('scope')) th.setAttribute('scope','col'); });
    });
    root.querySelectorAll('ul,ol').forEach(function(l){ if(!l.getAttribute('role')) l.setAttribute('role','list'); });
    root.querySelectorAll('li').forEach(function(li){ if(!li.getAttribute('role')) li.setAttribute('role','listitem'); });
  }
  function enhanceLessonReader(){
    var lesson=document.getElementById('lesson');
    var title=document.getElementById('lessonTitle');
    var meta=document.getElementById('lessonMeta');
    var content=document.getElementById('lessonContent');
    if(!lesson||!content) return;
    var body=txt(content);
    if(!body || body.length<40) return;
    lesson.setAttribute('role','main');
    lesson.setAttribute('lang','de');
    if(title) title.setAttribute('data-reader-title','1');
    if(meta) meta.setAttribute('data-reader-meta','1');
    var article=content.querySelector(':scope > article.edge-reader-article');
    if(!article){
      article=document.createElement('article');
      article.className='edge-reader-article';
      article.setAttribute('lang','de');
      article.setAttribute('itemscope','');
      article.setAttribute('itemtype','https://schema.org/Article');
      article.setAttribute('role','article');
      article.setAttribute('aria-labelledby','lessonTitle');
      article.setAttribute('data-edge-reader-ready','1');
      var nodes=[];
      while(content.firstChild){ nodes.push(content.firstChild); article.appendChild(content.firstChild); }
      content.appendChild(article);
    }
    article.setAttribute('aria-label',txt(title)||'Deutsch Konu anlatımı');
    markTables(article);
  }
  function install(){
    enhanceLessonReader();
    var c=document.getElementById('lessonContent');
    if(c && !c.__edgeReaderObserver){
      c.__edgeReaderObserver=true;
      new MutationObserver(function(){setTimeout(enhanceLessonReader,0);}).observe(c,{childList:true,subtree:false});
    }
    ['btnLessonShort','btnLessonMedium','btnLessonLong'].forEach(function(id){
      var b=document.getElementById(id);
      if(b && !b.__edgeReaderClick){ b.__edgeReaderClick=true; b.addEventListener('click',function(){setTimeout(enhanceLessonReader,120);setTimeout(enhanceLessonReader,600);}); }
    });
  }
  window.__edgeReaderEnhanceLesson=enhanceLessonReader;
  if(document.readyState==='loading') document.addEventListener('DOMContentLoaded',install); else install();
  setTimeout(install,300);
  setTimeout(enhanceLessonReader,900);
  setTimeout(enhanceLessonReader,1800);
})();
