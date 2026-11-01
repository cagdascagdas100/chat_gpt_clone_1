"use strict";
const PHRASES=[
 {title:"Önemli avantaj / etki",text:"Ein besonders wichtige [Vorteil / Nachteil / Wirkung / Grenze / Ursache / Folge / Maßnahme] von [THEMA / PROBLEM] besteht in [NOMINALISIERUNG], da …"},
 {title:"Bir diğer önemli boyut",text:"Eine weitere bedeutsame [Vorteil / Nachteil / Wirkung / Grenze / Ursache / Folge / Maßnahme] von [THEMA / PROBLEM] zeigt sich in [NOMINALISIERUNG], da …"},
 {title:"Göz ardı edilmemesi gereken",text:"Eine nicht zu unterschätzende [Vorteil / Nachteil / Wirkung / Grenze / Ursache / Folge / Maßnahme] von [THEMA / PROBLEM] ist in [NOMINALISIERUNG] zu sehen, da …"},
 {title:"Problem açıklama",text:"Dies ist problematisch, weil …"},
 {title:"Destekleyici argüman",text:"Dafür spricht vor allem, dass …"},
 {title:"Geniş kapsamlı etkiler",text:"Dies kann insofern weitreichende Auswirkungen auf [X] haben, als …"},
 {title:"İlişki kurma",text:"Zunächst ist zu klären, wie [A] mit [B] zusammenhängt. Entscheidend ist dabei, dass …"},
 {title:"Anstatt … zu …",text:"Anstatt [Handlung 1] zu [Verb], neigt [SUBJEKT] dazu, [Handlung 2] zu [Verb]."},
 {title:"Etki karşılaştırması",text:"Auch wenn der Einfluss von B nicht an den von A heranreicht, ist er insofern keineswegs zu unterschätzen, als ... [B’nin etkisi A’nınkine ulaşmasa da, şu bakımdan kesinlikle küçümsenmemelidir: ...]"},
 {title:"Olumlu / olumsuz etkiler",text:"[Einflussfaktor] kann sich insofern positiv / förderlich / negativ / begrenzend auf [Person/Gruppe/Objekt] auswirken, als [Person/Gruppe] dazu neigt, [Handlung] zu + Infinitiv."},
 {title:"Sowohl … als auch …",text:"sowohl dazu führen, dass …, als auch dazu, dass … [hem a hem b]"},
 {title:"Anstelle von …",text:"Anstelle von … setzt man zunehmend auf … [a yerine b]"},
 {title:"Gelişmekte olan ülkeler",text:"in Entwicklungs- und Schwellenländern"},
 {title:"Somut örnek",text:"Ein besonders anschauliches Beispiel hierfür zeigt, welche / Gerade in meinem eigenen Umfeld lässt sich beobachten, welche / Ein besonders anschauliches Beispiel aus dem Alltag  im Bereich [X] zeigt, welche [FÖRDERLICHE / BEGRENZTE / PROBLEMATISCHE / BEDEUTSAME] Wirkung entfalten kann, wenn [KONKRETES BEISPIEL]"},
 {title:"Doğrudan ve dolaylı etkiler",text:"Daraus wird ersichtlich, welche unmittelbaren Auswirkungen dies auf [positiven/negativen Aspekt 1] hat. Dies ist vor allem darauf zurückzuführen, dass [Grund 1]. Darüber hinaus können sich daraus mittelbare Folgen für [positiven/negativen Aspekt 2] ergeben, was sich insbesondere dadurch erklären lässt, dass [Grund 2]."},
 {title:"Kısa etki değerlendirmesi",text:"Daraus wird ersichtlich, welche unmittelbaren Auswirkungen dies auf [positiven/negativen Aspekt 1] hat und welche mittelbaren Folgen sich daraus für [positiven/negativen Aspekt 2] ergeben können."},
 {title:"Kısa ve uzun vadeli etkiler",text:"Zunächst kann [KURZZEITWIRKUNG] entstehen, / Zunächst kann es dazu kommen, dass [Satz]. Infolgedessen könnte sich langfristig auch [LANGZEITWIRKUNG] einstellen, zumal [ERKLÄRUNG]."},
 {title:"Sınırlama / önlem",text:"Bei aller Bedeutung der genannten [Vorteile / Wirkungen] sollte jedoch nicht außer Acht gelassen werden, dass [Thema] für [betroffene Gruppe] zugleich mit gewissen [Nachteilen / Begrenzungen] verbunden ist. / zugleich geeignete [Lösungen / Maßnahmen] erfordert."},
 {title:"Giriş paragrafı",text:"[Thema] gewinnt heutzutage zunehmend an Bedeutung und betrifft insbesondere [betroffene Gruppe / Zielgruppe]. Besonders relevant ist das Thema, weil [Grund, warum das Thema wichtig ist] und dabei verschiedene [Vorteil / Nachteil / Wirkung / Grenze / Ursache / Folge / Maßnahme] eine wichtige Rolle spielen. Vor diesem Hintergrund stellt sich die Frage: [Prüfungsfrage]?"},
 {title:"Sonuç paragrafı",text:"Zusammenfassend lässt sich festhalten, dass [Thema] sowohl [Vorteil / positiver Aspekt] als auch [Nachteil / negativer Aspekt] mit sich bringt. Wägt man beide Seiten gegeneinander ab, so zeigt sich meines Erachtens, dass [Vorteil / positiver Aspekt] stärker ins Gewicht fällt, da [Begründung]. Aus diesem Grund erscheint es mir sinnvoll, [Maßnahme / Empfehlung], damit [Ziel / gewünschte Folge]."}
];
const LEVELS={
 easy:{name:"Kolay",ratio:0.27,mult:1,base:100,perLetter:3.6,max:360},
 medium:{name:"Orta",ratio:0.48,mult:2,base:80,perLetter:2.5,max:330},
 hard:{name:"Zor",ratio:0.72,mult:3,base:60,perLetter:1.8,max:300}
};
const $=id=>document.getElementById(id);
const letterPattern=/^\p{L}$/u;
const sameLetter=(a,b)=>String(a).normalize("NFC").toLocaleLowerCase("de-DE")===String(b).normalize("NFC").toLocaleLowerCase("de-DE");
const shuffle=arr=>{const out=[...arr];for(let i=out.length-1;i>0;i--){const n=Math.floor(Math.random()*(i+1));[out[i],out[n]]=[out[n],out[i]]}return out};
const lex=s=>[...s.matchAll(/\[[^\]]*\]|(?:\.{3}|…)|\p{L}+(?:['’]\p{L}+)*|\p{N}+|[\s\S]/gu)].map(x=>x[0]);
const isWord=s=>/^\p{L}+(?:['’]\p{L}+)*$/u.test(s)&&!["A","B","X"].includes(s);
let session=null,clockJob=null,round=null;
const setFeedback=(text,kind="info")=>{const area=$("feedback");area.textContent=text;area.className="feedback "+kind};
const stopClock=()=>{if(clockJob!==null){clearInterval(clockJob);clockJob=null}};
const secsFormat=n=>{const s=Math.max(0,Math.ceil(n));return String(Math.floor(s/60)).padStart(2,"0")+":"+String(s%60).padStart(2,"0")};
function startGame(level="easy"){
 stopClock();$("finishModal").hidden=true;const config=LEVELS[level];if(!config)return;
 session={level,queue:shuffle(PHRASES.map((_,i)=>i)),position:0,score:0,won:0,skipped:0};
 document.querySelectorAll("[data-level]").forEach(btn=>{const active=btn.dataset.level===level;btn.classList.toggle("active",active);btn.setAttribute("aria-pressed",String(active))});
 $("levelDisplay").textContent=config.name;$("scoreDisplay").textContent="0";startRound();
}
function buildRoundTokens(text,level){
 const parts=lex(text);const eligible=parts.map((v,i)=>isWord(v)?i:null).filter(x=>x!==null);
 const count=Math.max(1,Math.min(eligible.length,Math.round(eligible.length*LEVELS[level].ratio)));
 const picked=new Set(shuffle(eligible).slice(0,count));
 return {parts,picked};
}
function getFirstEditable(){return round?.inputs.find(el=>!el.disabled&&el.value==="")||round?.inputs.find(el=>!el.disabled)}
function focusFirst(){
 if(window.matchMedia("(pointer:coarse)").matches)return;
 const el=getFirstEditable();if(el)el.focus({preventScroll:true});
}
function startRound(){
 stopClock();if(!session)return;
 if(session.position>=session.queue.length){finishSession();return}
 const idx=session.queue[session.position],item=PHRASES[idx],config=LEVELS[session.level];
 const {parts,picked}=buildRoundTokens(item.text,session.level);
 round={idx,done:false,inputs:[],groups:[],hintCount:0,parts,picked,remaining:0,secondsTotal:0,deadline:0};
 $("phraseTitle").textContent=(idx+1)+". "+item.title;
 $("roundDisplay").textContent=(session.position+1)+" / "+PHRASES.length;
 $("wordsProgress").textContent="0 / "+picked.size+" kelime";
 $("roundMeta").textContent="Hazır alanlar hep görünür • Her kutu bir harf • "+config.name+" seviye";
 $("wordsBar").style.width="0%";
 $("sentence").replaceChildren();
 $("checkBtn").hidden=false;$("hintBtn").hidden=false;$("skipBtn").hidden=false;$("nextBtn").hidden=true;
 $("answerPanel").hidden=true;$("timerCard").classList.remove("danger");$("timerTrack").classList.remove("danger");
 setFeedback("","info");
 let tokenNo=0;
 parts.forEach((part,pos)=>{
   if(part.startsWith("[")&&part.endsWith("]")){
     const span=document.createElement("span");span.className="fixed-bracket";span.textContent=part;$("sentence").append(span);return;
   }
   if(picked.has(pos)){
     const group=document.createElement("span");group.className="word-group";group.setAttribute("role","group");group.setAttribute("aria-label","Eksik kelime "+(++tokenNo));
     const chars=[...part.normalize("NFC")];const cells=[];
     chars.forEach((char,j)=>{
       if(!letterPattern.test(char)){
         const fixed=document.createElement("span");fixed.className="punctuation";fixed.textContent=char;group.append(fixed);return;
       }
       const input=document.createElement("input");input.type="text";input.maxLength=1;input.autocomplete="off";input.autocorrect="off";input.autocapitalize="off";input.spellcheck=false;
       input.className="letter-box";input.setAttribute("aria-label","Kelime "+tokenNo+", harf "+(j+1));
       input.inputMode="text";input.dataset.expected=char;input.addEventListener("input",onLetterInput);
       input.addEventListener("keydown",onLetterKeydown);input.addEventListener("paste",onPaste);
       input.addEventListener("focus",()=>{if(!round?.done)input.select()});
       group.append(input);round.inputs.push(input);cells.push(input);
     });
     round.groups.push({group,cells,word:part});
     $("sentence").append(group);
   }else{
     const span=document.createElement("span");span.className=isWord(part)?"text-word":"punctuation";span.textContent=part;$("sentence").append(span);
   }
 });
 const hiddenLetters=round.inputs.length;
 round.secondsTotal=Math.min(config.max,Math.ceil(config.base+hiddenLetters*config.perLetter));
 round.deadline=Date.now()+round.secondsTotal*1000;round.remaining=round.secondsTotal;
 updateClock();updateProgress();
 clockJob=setInterval(updateClock,250);
 window.requestAnimationFrame(focusFirst);
}
function onLetterInput(event){
 if(!round||round.done)return;const input=event.currentTarget;
 const chars=[...input.value.normalize("NFC")].filter(x=>letterPattern.test(x));
 if(!chars.length){input.value="";updateProgress();return}
 const at=round.inputs.indexOf(input);
 writeCharacters(at,chars);
}
function writeCharacters(start,chars){
 if(!round||round.done)return;
 let last=start;
 for(const letter of chars){
   if(last>=round.inputs.length)break;
   const el=round.inputs[last];el.value=letter;el.classList.remove("wrong");el.closest(".word-group")?.classList.remove("wrong");last++;
 }
 updateProgress();
 if(last<round.inputs.length)round.inputs[last].focus({preventScroll:true});
 else round.inputs[round.inputs.length-1]?.blur();
}
function onPaste(e){
 if(round?.done)return;
 e.preventDefault();
 const chars=[...(e.clipboardData?.getData("text/plain")||"").normalize("NFC")].filter(x=>letterPattern.test(x));
 if(chars.length)writeCharacters(round.inputs.indexOf(e.currentTarget),chars);
}
function onLetterKeydown(e){
 if(round?.done)return;
 const i=round.inputs.indexOf(e.currentTarget);
 if(e.key==="Backspace"){
   e.preventDefault();
   const current=round.inputs[i];
   if(current.value){current.value="";current.classList.remove("wrong")}
   else if(i>0){const prev=round.inputs[i-1];prev.value="";prev.classList.remove("wrong");prev.focus({preventScroll:true})}
   updateProgress();return;
 }
 if(e.key==="ArrowLeft"&&i>0){e.preventDefault();round.inputs[i-1].focus({preventScroll:true});return}
 if(e.key==="ArrowRight"&&i<round.inputs.length-1){e.preventDefault();round.inputs[i+1].focus({preventScroll:true});return}
 if(e.key==="Enter"){e.preventDefault();checkAnswers();return}
 if(e.key===" "){e.preventDefault();if(i<round.inputs.length-1)round.inputs[i+1].focus({preventScroll:true})}
}
function groupCorrect(g){return g.cells.every(c=>sameLetter(c.value,c.dataset.expected))}
function updateProgress(){
 if(!round)return;
 const correct=round.groups.filter(groupCorrect).length;
 $("wordsProgress").textContent=correct+" / "+round.groups.length+" kelime";
 $("wordsBar").style.width=(round.groups.length?correct/round.groups.length*100:100)+"%";
}
function updateClock(){
 if(!round||round.done)return;
 round.remaining=Math.max(0,(round.deadline-Date.now())/1000);
 $("timerDisplay").textContent=secsFormat(round.remaining);
 const percent=Math.max(0,round.remaining/round.secondsTotal*100);
 $("timeBar").style.width=percent+"%";$("timerTrack").setAttribute("aria-valuenow",String(Math.round(percent)));
 const danger=round.remaining<=20;$("timerCard").classList.toggle("danger",danger);$("timerTrack").classList.toggle("danger",danger);
 if(round.remaining<=0){endRound("time")}
}
function checkAnswers(){
 if(!round||round.done)return;
 updateClock();if(round.done)return;
 const empty=round.inputs.filter(input=>!input.value).length;
 if(empty){setFeedback("Önce "+empty+" boş harfi tamamla. Yanlış harfleri dilediğin gibi düzeltebilirsin.","info");getFirstEditable()?.focus({preventScroll:true});return}
 const wrong=round.groups.filter(g=>!groupCorrect(g));
 round.groups.forEach(g=>{
   const ok=groupCorrect(g);g.group.classList.toggle("good",ok);g.group.classList.toggle("wrong",!ok);
   g.cells.forEach(c=>{c.classList.toggle("wrong",!sameLetter(c.value,c.dataset.expected));c.classList.toggle("good",ok)});
 });
 if(wrong.length){
   setFeedback(wrong.length+" kelimede hata var. Kırmızı harfleri silip düzelt; süre devam ediyor.","bad");
   const bad=wrong[0].cells.find(c=>!sameLetter(c.value,c.dataset.expected));
   bad?.focus({preventScroll:true});return;
 }
 endRound("success");
}
function giveHint(){
 if(!round||round.done)return;
 const input=round.inputs.find(c=>!sameLetter(c.value,c.dataset.expected));
 if(!input){setFeedback("Bütün harfler dolu ve doğru. Kontrol et düğmesine bas!","ok");return}
 const at=round.inputs.indexOf(input);input.value=input.dataset.expected;input.readOnly=true;input.classList.add("locked");round.hintCount++;
 input.closest(".word-group")?.classList.remove("wrong");updateProgress();
 setFeedback("Bir harf gösterildi. Bu turun puanından 20 puan düşecek.","info");
 const next=round.inputs.find((v,i)=>i>at&&!v.readOnly&&!sameLetter(v.value,v.dataset.expected))||round.inputs.find(v=>!v.readOnly&&!sameLetter(v.value,v.dataset.expected));
 next?.focus({preventScroll:true});
}
function endRound(reason){
 if(!round||round.done)return;round.done=true;stopClock();
 const settings=LEVELS[session.level],left=Math.max(0,Math.floor(round.remaining));
 if(reason==="success"){
  session.won++;
  const earned=Math.max(0,round.groups.length*20*settings.mult+Math.ceil(left/3)-round.hintCount*20);
  session.score+=earned;$("scoreDisplay").textContent=String(session.score);
  setFeedback("🎉 Doğru! "+round.groups.length+" kelimeyi tamamladın. +"+earned+" puan kazandın.","ok");
 }else{
  session.skipped++;
  setFeedback(reason==="time"?"⏳ Süre doldu. Kalıbın doğru hâlini aşağıda incele.":"Kalıbı geçtin. Doğru cevap aşağıda; tekrar çalışabilirsin.","bad");
 }
 round.inputs.forEach(input=>{if(reason!=="success")input.value=input.dataset.expected;input.disabled=true;input.readOnly=true;input.classList.add("locked");input.classList.remove("wrong")});
 round.groups.forEach(g=>g.group.classList.remove("wrong"));
 $("answerPanel").hidden=false;$("correctSentence").textContent=PHRASES[round.idx].text;
 $("checkBtn").hidden=true;$("hintBtn").hidden=true;$("skipBtn").hidden=true;$("nextBtn").hidden=false;
 $("nextBtn").textContent=session.position===PHRASES.length-1?"Sonuçları gör →":"Sonraki kalıp →";
 updateProgress();
}
function nextRound(){if(!round?.done)return;session.position++;startRound()}
function finishSession(){
 stopClock();const level=LEVELS[session.level].name;
 $("finishTitle").textContent="20 kalıp tamamlandı!";
 $("finishText").textContent=level+" seviyesinde "+session.won+" kalıbı süre içinde tamamladın, "+session.skipped+" kalıbı geçtin veya süre doldu.";
 $("finishScore").textContent=session.score.toLocaleString("tr-TR")+" puan";
 $("finishModal").hidden=false;
 try{
   const key="satzlab_word_arena_best_v1_"+session.level, old=Number(localStorage.getItem(key)||"0");
   if(session.score>old)localStorage.setItem(key,String(session.score));
 }catch(e){}
}
$("difficulty").addEventListener("click",e=>{
 const btn=e.target.closest("[data-level]");
 if(!btn||btn.dataset.level===session?.level)return;
 startGame(btn.dataset.level);
});
$("shuffleBtn").addEventListener("click",()=>startGame(session?.level||"easy"));
$("checkBtn").addEventListener("click",checkAnswers);
$("hintBtn").addEventListener("click",giveHint);
$("skipBtn").addEventListener("click",()=>endRound("skip"));
$("nextBtn").addEventListener("click",nextRound);
$("playAgain").addEventListener("click",()=>startGame(session?.level||"easy"));
document.addEventListener("visibilitychange",()=>{if(!document.hidden)updateClock()});
startGame("easy");
