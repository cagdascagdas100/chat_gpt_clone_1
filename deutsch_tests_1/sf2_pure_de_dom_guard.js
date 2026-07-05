(function(){
'use strict';
function mode(){
  var t=(document.getElementById('lessonTitle')||{}).textContent||'';
  var c=(document.getElementById('lessonContent')||{}).textContent||'';
  if(t.indexOf('Schreibfehler 1')>-1||c.indexOf('almanca_kaliplar')>-1||c.indexOf('Schreiben fehlern 1')>-1)return 'sf2_1';
  if(t.indexOf('Schreibfehler 2')>-1||c.indexOf('Sprachtraining_C1_C2')>-1||c.indexOf('Schreiben fehlern 2')>-1)return 'sf2_2';
  return '';
}
function apply(){
  var k=mode();if(!k)return;
  var L=(window.DEUTSCH_LESSONS||{})[k];if(!L||!L.long)return;
  var title=document.getElementById('lessonTitle'),meta=document.getElementById('lessonMeta'),content=document.getElementById('lessonContent');if(!content)return;
  if(k==='sf2_1'){
    if(title)title.textContent='Lektion: Schreibfehler 1 · Ausdrucksmuster, Präpositionen und Nomen-Verb-Verbindungen';
    if(meta)meta.textContent='Niveau: Ausführlich · C1/C2 · Deutsch';
    content.innerHTML=L.long;
    window.AAYS_SF2_1_DOM_PURE_DE_OK=true;
  }
  if(k==='sf2_2'){
    if(title)title.textContent='Lektion: Schreibfehler 2 · Medien, Wirtschaft, Präpositionen und Nomen-Verb-Verbindungen';
    if(meta)meta.textContent='Niveau: Ausführlich · C1/C2 · Deutsch';
    content.innerHTML=L.long;
    window.AAYS_SF2_2_DOM_PURE_DE_OK=true;
  }
}
setInterval(apply,500);
document.addEventListener('click',function(){setTimeout(apply,80);setTimeout(apply,250);setTimeout(apply,800);},true);
document.addEventListener('DOMContentLoaded',function(){setTimeout(apply,500);});
if(document.readyState!=='loading')setTimeout(apply,500);
})();