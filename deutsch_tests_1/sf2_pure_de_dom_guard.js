(function(){
'use strict';
var lastKey='';
var badWords=['Konu anlatımı','Seviye','Genel bakış','Öncelikli kavramlar','Konu açıklaması','Bu bölüm','Almancada','Türkçedeki','Yazmadan önce','Ezber formülü','doğru kullanım','örnek','KANONİK','kapsamlı içerik koruması'];
function el(id){return document.getElementById(id);}
function txt(id){var x=el(id);return x?(x.textContent||''):'';}
function visibleLesson(){var x=el('lesson');return !x||!/(^|\s)hide(\s|$)/.test(x.className||'');}
function hasBad(s){for(var i=0;i<badWords.length;i++){if(s.indexOf(badWords[i])>-1)return true;}return false;}
function noteIntent(s){
  s=s||'';
  if(s.indexOf('Schreibfehler 1')>-1||s.indexOf('Ausdrucksmuster')>-1)lastKey='sf2_1';
  if(s.indexOf('Schreibfehler 2')>-1||s.indexOf('Medien, Wirtschaft')>-1||s.indexOf('Globalisierung')>-1)lastKey='sf2_2';
}
function mode(){
  var t=txt('lessonTitle'),m=txt('lessonMeta'),c=txt('lessonContent'),all=t+' '+m+' '+c;
  noteIntent(all);
  if(t.indexOf('Schreibfehler 1')>-1||c.indexOf('almanca_kaliplar')>-1||c.indexOf('Schreiben fehlern 1')>-1||c.indexOf('Ausdrucksmuster')>-1)return 'sf2_1';
  if(t.indexOf('Schreibfehler 2')>-1||c.indexOf('Sprachtraining_C1_C2')>-1||c.indexOf('Schreiben fehlern 2')>-1||c.indexOf('Medien, Wirtschaft')>-1)return 'sf2_2';
  if(hasBad(all)&&lastKey)return lastKey;
  return '';
}
function render(k){
  var L=(window.DEUTSCH_LESSONS||{})[k];if(!L||!L.long)return false;
  var title=el('lessonTitle'),meta=el('lessonMeta'),content=el('lessonContent');if(!content)return false;
  if(k==='sf2_1'){
    if(title)title.textContent='Lektion: Schreibfehler 1 · Ausdrucksmuster, Präpositionen und Nomen-Verb-Verbindungen';
    if(meta)meta.textContent='Niveau: Ausführlich · C1/C2 · Deutsch';
    if(content.innerHTML!==L.long)content.innerHTML=L.long;
    window.AAYS_SF2_1_DOM_PURE_DE_OK=true;
    return true;
  }
  if(k==='sf2_2'){
    if(title)title.textContent='Lektion: Schreibfehler 2 · Medien, Wirtschaft, Präpositionen und Nomen-Verb-Verbindungen';
    if(meta)meta.textContent='Niveau: Ausführlich · C1/C2 · Deutsch';
    if(content.innerHTML!==L.long)content.innerHTML=L.long;
    window.AAYS_SF2_2_DOM_PURE_DE_OK=true;
    return true;
  }
  return false;
}
function apply(){
  if(!visibleLesson())return;
  var k=mode();
  if(!k)return;
  render(k);
}
document.addEventListener('click',function(e){noteIntent(((e.target||{}).textContent)||'');setTimeout(apply,40);setTimeout(apply,120);setTimeout(apply,300);setTimeout(apply,900);},true);
document.addEventListener('DOMContentLoaded',function(){setTimeout(apply,120);setTimeout(apply,500);});
try{new MutationObserver(function(){setTimeout(apply,30);}).observe(document.documentElement,{childList:true,subtree:true,characterData:true});}catch(e){}
setInterval(apply,250);
if(document.readyState!=='loading')setTimeout(apply,120);
window.AAYS_SF2_DOM_GUARD_V3_OK=true;
})();