(function(){
'use strict';
if(window.AAYS_SCHLAFMANGEL_T46_MIX_V3_OK)return;
var KEY='t46';
var items=[
 {slot:'Ursache 1',title:'Leistungs- und Zeitdruck durch Studium, Nebenjob und mangelnde Planung',chain:'Mehrere Verpflichtungen → längere Arbeitszeiten → spätes Schlafengehen → zu wenig Erholung'},
 {slot:'Ursache 2',title:'Nächtliche Mediennutzung und unregelmäßige Alltagsgewohnheiten',chain:'Digitale Ablenkung → Verlust des Zeitgefühls → späterer Schlafbeginn → instabiler Rhythmus'},
 {slot:'Folge 1',title:'Nachlassende Konzentrations-, Lern- und Studienleistung',chain:'Zu wenig Schlaf → geringere Aufmerksamkeit → mehr Fehler → zusätzlicher Leistungsdruck'},
 {slot:'Folge 2',title:'Körperliche, psychische und soziale Belastungen',chain:'Schlafdefizit → Erschöpfung → Gereiztheit und Rückzug → weniger Unterstützung'},
 {slot:'Lösung 1',title:'Realistisches Zeitmanagement und eine feste Schlafroutine',chain:'Frühzeitige Planung → kleinere Arbeitsschritte → feste Schlusszeit → ausreichende Nachtruhe'},
 {slot:'Lösung 2',title:'Bewusster Medienumgang und Unterstützung durch Hochschulen',chain:'Klare Offline-Zeit + Beratung → weniger Ablenkung und Belastung → stabilerer Studienalltag'}
];
var slots=items.map(function(x){return x.slot});
function E(id){return document.getElementById(id)}
function esc(s){return String(s||'').replace(/[&<>']/g,function(c){return {'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#039;'}[c]})}
function shuffle(a){a=a.slice();for(var i=a.length-1;i>0;i--){var j=Math.floor(Math.random()*(i+1)),t=a[i];a[i]=a[j];a[j]=t}return a}
function selected(){var r=document.querySelector('input[name="tc"]:checked');return r?r.value:''}
function active(){return selected()===KEY}
function style(){if(E('sleep-t46-mix-style'))return;var s=document.createElement('style');s.id='sleep-t46-mix-style';s.textContent='.sleepMixGrid{display:grid;gap:12px}.sleepMixCard{border:1px solid #d8d3ca;border-radius:12px;padding:12px;background:#fffdf9}.sleepMixCard select{width:100%;padding:9px;border:1px solid #cfc9bf;border-radius:9px;margin-top:8px}.sleepMixCorrect{background:#ecfdf5!important;border-color:#86efac!important}.sleepMixWrong{background:#fff1f2!important;border-color:#fda4af!important}.sleepChain{font:14px Arial;color:#374151;margin-top:8px}';document.head.appendChild(s)}
function ensureButton(){
  var controls=E('modeControls'),hang=E('btnHang');if(!controls||!hang)return;
  var b=E('btnSleepT46Mix');
  if(!b){b=document.createElement('button');b.id='btnSleepT46Mix';b.className='ghost';b.textContent='Ursachen / Folgen / Lösungen karıştırma';hang.parentNode.insertBefore(b,hang.nextSibling);b.onclick=openMix;}
  b.style.display=active()?'inline-block':'none';
}
function ensurePanel(){
  var p=E('sleepT46MixPanel');if(p)return p;
  p=document.createElement('section');p.id='sleepT46MixPanel';p.className='card hide';
  var main=document.querySelector('main.wrap')||document.body;main.appendChild(p);return p;
}
function renderMix(){
  style();var p=ensurePanel(),rows=shuffle(items),opts=['<option value="">Bitte zuordnen</option>'].concat(slots.map(function(s){return '<option value="'+esc(s)+'">'+esc(s)+'</option>'})).join('');
  p.innerHTML='<h2>Schlafmangel bei Studierenden · Ursachen / Folgen / Lösungen</h2><p class="muted">Ordne genau zwei Ursachen, zwei Folgen und zwei Lösungen zu.</p><div class="sleepMixGrid">'+rows.map(function(x,i){return '<div class="sleepMixCard" data-answer="'+esc(x.slot)+'"><b>'+(i+1)+'. '+esc(x.title)+'</b><div class="sleepChain">'+esc(x.chain)+'</div><select>'+opts+'</select></div>'}).join('')+'</div><p><button id="btnSleepT46Check">Auswerten</button><button class="sec" id="btnSleepT46Reset">Neu mischen</button><button class="ghost" id="btnSleepT46Back">Menü</button></p><div id="sleepT46Result"></div>';
  E('btnSleepT46Check').onclick=check;E('btnSleepT46Reset').onclick=renderMix;E('btnSleepT46Back').onclick=closeMix;
}
function openMix(){if(!active())return;['quiz','hang','lesson','shared'].forEach(function(id){var x=E(id);if(x)x.classList.add('hide')});var st=E('start');if(st)st.classList.add('hide');renderMix();ensurePanel().classList.remove('hide')}
function closeMix(){var p=ensurePanel();p.classList.add('hide');var st=E('start');if(st)st.classList.remove('hide');if(typeof window.renderTests==='function')window.renderTests('Bevor Schreiben')}
function check(){var cards=ensurePanel().querySelectorAll('.sleepMixCard'),score=0;cards.forEach(function(c){var ok=c.querySelector('select').value===c.getAttribute('data-answer');c.classList.remove('sleepMixCorrect','sleepMixWrong');c.classList.add(ok?'sleepMixCorrect':'sleepMixWrong');if(ok)score++});E('sleepT46Result').innerHTML='<p><b>'+score+'/6 richtig</b></p>'}
function sync(){ensureButton()}
document.addEventListener('change',function(e){if(e.target&&e.target.name==='tc')setTimeout(sync,0)},true);
document.addEventListener('click',function(){setTimeout(sync,30)},true);
document.addEventListener('DOMContentLoaded',function(){setTimeout(sync,100);setTimeout(sync,600)});
try{new MutationObserver(function(){sync()}).observe(document.documentElement,{childList:true,subtree:true})}catch(e){}
setInterval(sync,700);
window.AAYS_SCHLAFMANGEL_T46_MIX_V3_OK=true;
})();
