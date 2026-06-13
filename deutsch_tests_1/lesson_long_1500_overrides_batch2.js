(function(){
  window.DEUTSCH_LESSONS = window.DEUTSCH_LESSONS || {};
  window.LESSONS = window.LESSONS || {};
  function applyLong(key, html){
    window.DEUTSCH_LESSONS[key] = window.DEUTSCH_LESSONS[key] || {};
    window.DEUTSCH_LESSONS[key].long = html;
    window.LESSONS[key] = window.LESSONS[key] || window.DEUTSCH_LESSONS[key];
    window.LESSONS[key].long = html;
  }
})();