(function(){
'use strict';
if(window.AAYS_ARTIKEL_QUIZ_READY)return;
window.AAYS_ARTIKEL_QUIZ_READY=true;
var RAW=`Abbruch|der
Alltag|der
Angebot|das
Anteil|der
Arbeit|die
Armut|die
Art|die
Aspekt|der
Aufgabe|die
Aufsatz|der
Auge|das
Ausdruck|der
Ausgabe|die
Austausch|der
Bahn|die
Bedarf|der
Beispiel|das
Beitrag|der
Beruf|der
Beschwerde|die
Besuch|der
Betrieb|der
Bewusstsein|das
Bildschirm|der
Branche|die
Buch|das
Budget|das
Chance|die
Disziplin|die
Druck|der
Einblick|der
Einfluss|der
Einflussnahme|die
Einheimische|der/die
Einnahme|die
Einsatz|der
Einzelne|der/die
Ende|das
Erfolg|der
Fahrt|die
Fairness|die
Fastfood|das
Fokus|der
Folge|die
Form|die
Fortschritt|der
Freund|der
Fußball|der
Gebühr|die
Gefühl|das
Gehalt|das
Geld|das
Gerät|das
Gericht|das
Geschäft|das
Gespräch|das
Gewinn|der
Gleichgewicht|das
Grund|der
Gruppe|die
Halle|die
Handy|das
Haus|das
Heimweh|das
Hilfe|die
Hobby|das
Hotel|das
Idee|die
Internet|das
Jahr|das
Job|der
Jugendliche|der/die
Kamera|die
Kampagne|die
Kanal|der
Karriere|die
Kasse|die
Kauf|der
Kind|das
Komfort|der
Konflikt|der
Kontakt|der
Kontrolle|die
Kraft|die
Kümmern|das
Leid|das
Link|der
Lohn|der
Mail|die
Markt|der
Maß|das
Material|das
Menge|die
Mensch|der
Methode|die
Miete|die
Mikrofon|das
Mikrowelle|die
Minute|die
Mitglied|das
Mittel|das
Mode|die
Nachricht|die
Nachteil|der
Netz|das
Netzwerk|das
Niveau|das
Note|die
Notiz|die
Objekt|das
Ort|der
Pause|die
Pendeln|das
Person|die
Pflicht|die
Phase|die
Plattform|die
Platz|der
Praxis|die
Preis|der
Privatsphäre|die
Problem|das
Produkt|das
Profil|das
Programm|das
Projekt|das
Prozess|der
Quelle|die
Recht|das
Reife|die
Reise|die
Respekt|der
Ressource|die
Route|die
Rücksichtnahme|die
Ruhe|die
Salon|der
Salz|das
Satz|der
Schauspielern|das
Schmerz|der
Schule|die
Schutz|der
Schwäche|die
Seite|die
Sicht|die
Software|die
Spanne|die
Speise|die
Spielzeug|das
Sport|der
Spot|der
Sprache|die
Stadt|die
Stadtbild|das
Standard|der
Stelle|die
Stoff|der
Stress|der
Stuhl|der
Stunde|die
Supermarkt|der
System|das
Tag|der
Team|das
Teil|der
Termin|der
Übergewicht|das
Umfeld|das
Umlauf|der
Umsatz|der
Umwelt|die
Unfall|der
Unterricht|der
Unterschied|der
Verb|das
Verbrauch|der
Verkauf|der
Vielfalt|die
Volleyball|der
Vorbild|das
Vorschlag|der
Vorteil|der
Wahl|die
Wandel|der
Webseite|die
Weg|der
Weise|die
Weitergabe|die
Welt|die
Wert|der
Wettbewerb|der
Winkel|der
Zahl|die
Zeit|die
Ziel|das
Aufwachsen|das
Ausdauer|die
Ausland|das
Einkaufen|das
Erlernen|das
Ersparnis|die
Essen|das
Futter|das
Interesse|das
Kenntnis|die
Konsum|der
Kosten|die
Land|das
Leben|das
Lernen|das
Lesen|das
Papier|das
Raum|der
Reichtum|der
Restaurant|das
Schauen|das
Schreiben|das
Singen|das
Springen|das
Steuer|die
Tanzen|das
Tier|das
Unternehmen|das
Verfassen|das
Verhalten|das
Versagen|das
Vertrauen|das
Wetter|das
Wohlbefinden|das
Zimmer|das
Zutat|die`;
var QUESTIONS=RAW.split(/\n+/).map(function(line){var p=line.split('|');return {word:p[0],article:p[1],answers:p[1].split('/')};});
function esc(x){return String(x==null?'':x).replace(/[&<>]/g,function(c){return {'&':'&amp;','<':'&lt;','>':'&gt;'}[c];});}
function shuffle(a){for(var i=a.length-1;i>0;i--){var j=Math.floor(Math.random()*(i+1));var t=a[i];a[i]=a[j];a[j]=t;}return a;}
function hideMainAreas(){['start','quiz','lesson','modeControls'].forEach(function(id){var el=document.getElementById(id);if(el)el.classList.add('hide');});}
function showStart(){var s=document.getElementById('start');if(s)s.classList.remove('hide');var root=document.getElementById('artikelQuiz');if(root)root.classList.add('hide');}
function injectMenu(){
 var list=document.getElementById('testList')||document.querySelector('#start .card')||document.getElementById('start');
 if(!list||document.getElementById('artikelMenuCard'))return;
 var card=document.createElement('div');card.id='artikelMenuCard';card.className='card';card.style.marginTop='14px';
 card.innerHTML='<h2>Artikel</h2><p class="muted">der · die · das artikel testi. Doğru cevapta otomatik sonraki soruya geçer. Yanlışta doğru cevap gösterilmez; soru daha sonra tekrar karışık gelir.</p><button id="btnArtikelQuiz" class="sec">Artikel testini başlat</button>';
 list.appendChild(card);
 var btn=document.getElementById('btnArtikelQuiz');if(btn)btn.addEventListener('click',startQuiz);
}
function ensureRoot(){
 var root=document.getElementById('artikelQuiz');
 if(root)return root;
 root=document.createElement('section');root.id='artikelQuiz';root.className='card hide';root.style.margin='14px auto';root.style.maxWidth='1080px';
 var main=document.querySelector('main.wrap')||document.querySelector('main')||document.body;
 main.appendChild(root);return root;
}
var state={queue:[],current:null,total:0,done:0,correct:0,wrongStats:{},answered:false};
function startQuiz(){
 state={queue:shuffle(QUESTIONS.slice()),current:null,total:QUESTIONS.length,done:0,correct:0,wrongStats:{},answered:false};
 hideMainAreas();
 var root=ensureRoot();root.classList.remove('hide');
 nextQuestion();
}
function nextQuestion(){
 state.answered=false;
 while(state.queue.length&&state.queue[0].done)state.queue.shift();
 if(!state.queue.length){finishQuiz();return;}
 state.current=state.queue.shift();
 renderQuestion();
}
function wrongListHtml(){
 var keys=Object.keys(state.wrongStats).filter(function(k){return !state.wrongStats[k].fixed;});
 if(!keys.length)return '<p class="muted">Henüz tekrar gelecek yanlış soru yok.</p>';
 return '<ul>'+keys.map(function(k){return '<li>'+esc(k)+'</li>';}).join('')+'</ul>';
}
function renderQuestion(){
 var q=state.current,root=ensureRoot();
 var progress=state.done+' / '+state.total;
 root.innerHTML='<h2>Artikel testi</h2><p class="muted">Doğru yapılan soru tekrar gelmez. Yanlış yapılan soru doğru cevap gösterilmeden karışık şekilde tekrar gelir; sonra doğru yapılırsa test bitene kadar tekrar çıkmaz.</p><div class="bar" style="margin:10px 0"><div style="width:'+(state.done/state.total*100)+'%"></div></div><p><b>İlerleme:</b> '+progress+' · <b>Doğru:</b> '+state.correct+' · <b>Tekrar gelecek yanlış:</b> '+Object.keys(state.wrongStats).filter(function(k){return !state.wrongStats[k].fixed;}).length+'</p><div style="font-size:34px;font-weight:bold;margin:18px 0">'+esc(q.word)+'</div><div id="artikelOpts"></div><p id="artikelFeedback" style="min-height:28px;font-weight:bold"></p><button id="artikelNext" class="ghost hide">Sonraki</button><button id="artikelBack" class="ghost" style="margin-left:8px">Ana menü</button><h3>Yanlış yapılanlar</h3><div id="artikelWrongList">'+wrongListHtml()+'</div>';
 var opts=document.getElementById('artikelOpts');
 ['der','die','das'].forEach(function(a){var b=document.createElement('button');b.textContent=a;b.dataset.article=a;b.style.margin='4px';b.addEventListener('click',answer);opts.appendChild(b);});
 document.getElementById('artikelNext').addEventListener('click',nextQuestion);
 document.getElementById('artikelBack').addEventListener('click',showStart);
}
function answer(ev){
 if(state.answered)return;
 state.answered=true;
 var q=state.current,ans=ev.currentTarget.dataset.article;
 var buttons=[].slice.call(document.querySelectorAll('#artikelOpts button'));
 var ok=q.answers.indexOf(ans)!==-1;
 buttons.forEach(function(b){b.disabled=true;});
 if(ok){
  ev.currentTarget.style.background='#16a34a';ev.currentTarget.style.color='#fff';
  state.done++;state.correct++;q.done=true;
  if(state.wrongStats[q.word])state.wrongStats[q.word].fixed=true;
  document.getElementById('artikelFeedback').textContent='Doğru';
  setTimeout(nextQuestion,280);
 }else{
  ev.currentTarget.style.background='#dc2626';ev.currentTarget.style.color='#fff';
  if(!state.wrongStats[q.word])state.wrongStats[q.word]={article:q.article,count:0,fixed:false};
  state.wrongStats[q.word].count++;
  var pos=Math.min(state.queue.length,Math.max(2,Math.floor(Math.random()*8)+2));
  state.queue.splice(pos,0,q);
  document.getElementById('artikelFeedback').textContent='Yanlış. Doğru cevap gösterilmeyecek; bu soru tekrar gelecek.';
  document.getElementById('artikelWrongList').innerHTML=wrongListHtml();
  document.getElementById('artikelNext').classList.remove('hide');
 }
}
function finishQuiz(){
 var root=ensureRoot();
 var wrong=Object.keys(state.wrongStats).sort().map(function(k){var x=state.wrongStats[k];return {word:k,article:x.article,count:x.count};});
 var copy=wrong.length?wrong.map(function(x){return x.word+'\t'+x.article+'\t'+x.count+' kez yanlış';}).join('\n'):'Yanlış yok.';
 root.innerHTML='<h2>Artikel testi bitti</h2><p><b>Toplam soru:</b> '+state.total+' · <b>Doğru tamamlanan:</b> '+state.correct+' · <b>Yanlış yapılan farklı soru:</b> '+wrong.length+'</p><h3>Yanlış yapılanlar ve doğru cevapları</h3><textarea id="artikelCopy" style="width:100%;min-height:220px;font:15px monospace">'+esc(copy)+'</textarea><p><button id="artikelCopyBtn" class="sec">Listeyi kopyala</button><button id="artikelRestart" style="margin-left:8px">Yeniden başlat</button><button id="artikelBack" class="ghost" style="margin-left:8px">Ana menü</button></p>';
 document.getElementById('artikelCopyBtn').addEventListener('click',function(){var ta=document.getElementById('artikelCopy');ta.select();document.execCommand('copy');});
 document.getElementById('artikelRestart').addEventListener('click',startQuiz);
 document.getElementById('artikelBack').addEventListener('click',showStart);
}
function boot(){injectMenu();setTimeout(injectMenu,400);setTimeout(injectMenu,1200);}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',boot);else boot();
setInterval(injectMenu,2000);
window.AAYS_ARTIKEL_QUIZ_COUNT=QUESTIONS.length;
window.AAYS_ARTIKEL_QUIZ_MENU_OK=true;
window.AAYS_ARTIKEL_QUIZ_AUTO_NEXT_CORRECT_OK=true;
window.AAYS_ARTIKEL_QUIZ_NO_ANSWER_REVEAL_OK=true;
})();
