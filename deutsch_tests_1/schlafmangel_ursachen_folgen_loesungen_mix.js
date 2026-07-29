(function(){
'use strict';
if(window.AAYS_SCHLAFMANGEL_UFL_MIX_V1_OK)return;
var KEY="schlafmangel_studierende_ursachen_folgen_loesungen_c1c2";
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
function selectedKey(){var r=document.querySelector('input[name="tc"]:checked');return r?r.value:''}
function isActive(){return selectedKey()===KEY}
function ensureStyle(){if(E('sleep-ufl-style'))return;var s=document.createElement('style');s.id='sleep-ufl-style';s.textContent='.sleepMixGrid{display:grid;gap:12px}.sleepMixCard{border:1px solid #d8d3ca;border-radius:12px;padding:12px;background:#fffdf9}.sleepMixCard select{width:100%;padding:9px;border:1px solid #cfc9bf;border-radius:9px;margin-top:8px}.sleepMixCorrect{background:#ecfdf5!important;border-color:#86efac!important}.sleepMixWrong{background:#fff1f2!important;border-color:#fda4af!important}.sleepChain{font:14px Arial;color:#374151;margin-top:8px}';document.head.appendChild(s)}
function ensureUI(){
 ensureStyle();var controls=E('modeControls'),hang=E('btnHang');if(controls&&!E('btnUflMix')){var b=document.createElement('button');b.id='btnUflMix';b.className='ghost hide';b.textContent='Ursachen / Folgen / Lösungen karıştırma';if(hang&&hang.parentNode)hang.parentNode.insertBefore(b,hang.nextSibling);else controls.appendChild(b);b.addEventListener('click',openMix)}
 if(!E('uflMix')){var main=document.querySelector('main')||document.body,sec=document.createElement('div');sec.id='uflMix';sec.className='hide';sec.innerHTML='<section class="card"><h2>Schlafmangel bei Studierenden</h2><p class="muted">Altı ana parçayı karışık sıradan doğru yere yerleştir: iki Ursache, iki Folge ve iki Lösung.</p><div id="uflMixCards" class="sleepMixGrid"></div><p><button id="btnUflCheck">Prüfen</button><button class="sec" id="btnUflShuffle">Neu mischen</button><button class="ghost" id="btnUflBack">Menü</button></p><div id="uflMixResult"></div></section>';main.appendChild(sec);E('btnUflCheck').addEventListener('click',check);E('btnUflShuffle').addEventListener('click',render);E('btnUflBack').addEventListener('click',back)}
 sync();
}
function sync(){var b=E('btnUflMix');if(b)b.classList.toggle('hide',!isActive())}
function hideOthers(){['start','quiz','lesson','hang','shared','settingsWordCountPanel'].forEach(function(id){var x=E(id);if(x)x.classList.add('hide')})}
function openMix(){if(!isActive())return;hideOthers();E('uflMix').classList.remove('hide');render();window.scrollTo(0,0)}
function render(){var box=E('uflMixCards');if(!box)return;var order=shuffle(items);box.innerHTML=order.map(function(x,i){var opts='<option value="">Yer seç...</option>'+slots.map(function(s){return '<option value="'+esc(s)+'">'+esc(s)+'</option>'}).join('');return '<article class="sleepMixCard" data-answer="'+esc(x.slot)+'"><b>'+(i+1)+'. '+esc(x.title)+'</b><select aria-label="'+esc(x.title)+'">'+opts+'</select><div class="sleepChain hide">'+esc(x.chain)+'</div></article>'}).join('');E('uflMixResult').innerHTML='';}
function check(){var cards=[].slice.call(document.querySelectorAll('#uflMixCards .sleepMixCard')),score=0,used={};cards.forEach(function(c){c.classList.remove('sleepMixCorrect','sleepMixWrong');var s=c.querySelector('select'),ok=s.value===c.getAttribute('data-answer');if(ok){score++;c.classList.add('sleepMixCorrect')}else c.classList.add('sleepMixWrong');c.querySelector('.sleepChain').classList.remove('hide');if(s.value)used[s.value]=(used[s.value]||0)+1});var dup=Object.keys(used).filter(function(k){return used[k]>1});E('uflMixResult').innerHTML='<p><b>'+score+'/6 richtig</b></p>'+(dup.length?'<p class="dberr">Aynı yer birden fazla kullanıldı: '+esc(dup.join(', '))+'</p>':'<p class="muted">Her slot yalnızca bir kez kullanılmalıdır.</p>')}
function back(){var sec=E('uflMix');if(sec)sec.classList.add('hide');var start=E('start');if(start)start.classList.remove('hide');if(typeof window.renderTests==='function')window.renderTests('Bevor Schreiben');setTimeout(sync,30)}
document.addEventListener('change',function(e){if(e.target&&e.target.name==='tc')setTimeout(sync,0)},true);
document.addEventListener('click',function(){setTimeout(sync,80)},true);
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',ensureUI);else ensureUI();
setTimeout(ensureUI,300);setTimeout(ensureUI,1200);
window.AAYS_SCHLAFMANGEL_UFL_MIX_V1_OK=true;
})();
