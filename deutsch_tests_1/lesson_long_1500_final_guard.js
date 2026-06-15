(function(){
  window.DEUTSCH_TESTS=window.DEUTSCH_TESTS||{};
  window.DEUTSCH_LESSONS=window.DEUTSCH_LESSONS||{};
  window.LESSONS=window.LESSONS||{};
  function run(){
    try{ if(window.__uniqueLongNoRepeatGuard) window.__uniqueLongNoRepeatGuard(); }catch(e){ console.error('unique no-repeat guard failed',e); }
  }
  window.__ensureAllLongLessons1500Final=run;
  window.__forceLongLessons1500Final=run;
  run();
  setTimeout(run,300);setTimeout(run,1200);setTimeout(run,2600);setTimeout(run,5200);
  if(document.addEventListener)document.addEventListener('DOMContentLoaded',function(){setTimeout(run,500);setTimeout(run,1800);setTimeout(run,4200);});
  if(window.addEventListener)window.addEventListener('load',function(){setTimeout(run,500);setTimeout(run,1800);setTimeout(run,4200);});
})();