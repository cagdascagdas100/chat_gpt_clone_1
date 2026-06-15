(function(){
  window.DEUTSCH_TESTS=window.DEUTSCH_TESTS||{};
  window.DEUTSCH_LESSONS=window.DEUTSCH_LESSONS||{};
  window.LESSONS=window.LESSONS||{};
  function runUniqueLongGuard(){
    try{
      if(window.__uniqueLongNoRepeatGuard){ window.__uniqueLongNoRepeatGuard(); }
    }catch(e){ console.error('unique long guard failed', e); }
  }
  window.__ensureAllLongLessons1500=runUniqueLongGuard;
  runUniqueLongGuard();
  setTimeout(runUniqueLongGuard,700);
  setTimeout(runUniqueLongGuard,2200);
  setTimeout(runUniqueLongGuard,5200);
})();