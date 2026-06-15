(function(){
  window.DEUTSCH_TESTS=window.DEUTSCH_TESTS||{};
  window.DEUTSCH_LESSONS=window.DEUTSCH_LESSONS||{};
  window.LESSONS=window.LESSONS||{};
  function loadV4(){
    try{
      if(window.__finalAntiRepeatLongGuard){ window.__finalAntiRepeatLongGuard(); return; }
      var s=document.createElement('script');
      s.src='lesson_unique_1400_no_repeat_guard_v4.js?v=1';
      s.onload=function(){ try{ if(window.__finalAntiRepeatLongGuard) window.__finalAntiRepeatLongGuard(); }catch(e){} };
      document.head.appendChild(s);
    }catch(e){ console.error('anti-repeat v4 load failed', e); }
  }
  function runUniqueLongGuard(){
    try{ if(window.__uniqueLongNoRepeatGuard){ window.__uniqueLongNoRepeatGuard(); } }catch(e){ console.error('unique long guard failed', e); }
    loadV4();
  }
  window.__ensureAllLongLessons1500=runUniqueLongGuard;
  runUniqueLongGuard();
  setTimeout(runUniqueLongGuard,700);
  setTimeout(runUniqueLongGuard,2200);
  setTimeout(runUniqueLongGuard,5200);
  setTimeout(runUniqueLongGuard,8200);
})();