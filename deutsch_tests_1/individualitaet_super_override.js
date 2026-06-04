(function(){
  function patch(){
    if(typeof window.forceIndividualitaetLessonFinal==='function'){
      window.forceIndividualitaetLesson=window.forceIndividualitaetLessonFinal;
      window.forceIndividualitaetLessonFull=window.forceIndividualitaetLessonFinal;
    }
  }
  patch();
  document.addEventListener('DOMContentLoaded',patch);
  setInterval(patch,200);
})();
