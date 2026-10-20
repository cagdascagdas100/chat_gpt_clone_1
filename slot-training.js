/* SatzLab v2: Köşeli parantezlerdeki alanlar sabit ipucudur; değerlendirilmez. */
(function(){
"use strict";
const SLOTS=/\[[^\]]*\]/gu;
const isSlot=s=>/^\[[^\]]*\]$/u.test(s);
const splitParts=s=>{
  const parts=[];let at=0;
  for(const m of s.matchAll(/\[[^\]]*\][,.;:!?]?/gu)){
    if(m.index>at)parts.push({type:"text",value:s.slice(at,m.index)});
    parts.push({type:"slot",value:m[0]});at=m.index+m[0].length;
  }
  if(at<s.length)parts.push({type:"text",value:s.slice(at)});
  return parts;
};
const plain=s=>normalize(s.replace(/\[[^\]]*\][,.;:!?]?/gu," "));
const slots=s=>[...s.matchAll(SLOTS)].map(m=>m[0]);
const hintHtml=s=>{
  const hints=slots(s);
  if(!hints.length)return "";
  return '<aside class="fixed-hints"><div class="fixed-head">📌 Hazır verilen ifadeler — bunları yazma / ezberden bulma</div><div class="fixed-chip-row">'+hints.map(v=>'<span class="fixed-chip">'+escapeHtml(v)+'</span>').join("")+'</div></aside>';
};
const addHint=(box,s)=>{if(slots(s).length)box.insertAdjacentHTML("afterbegin",hintHtml(s))};
const answerFields=()=>[...document.querySelectorAll("#slotWriteArea .slot-answer")];
const originalFlash=flashView;
flashView=function(box){originalFlash(box);addHint(box,PATTERNS[current].text)};
const originalContinue=continueView;
continueView=function(box){originalContinue(box);addHint(box,PATTERNS[current].text)};
const originalMatch=matchView;
matchView=function(box){
  originalMatch(box);
  const idxs=[...document.querySelectorAll("#matchLeft .match-card")].map(b=>Number(b.dataset.idx));
  const texts=idxs.map(i=>PATTERNS[i].text);
  const available=texts.filter(s=>slots(s).length);
  if(available.length)box.insertAdjacentHTML("afterbegin",'<aside class="fixed-hints"><div class="fixed-head">📌 Bu sorudaki hazır verilen alanlar (eşleştirilmiyor)</div><div class="fixed-chip-row">'+available.flatMap(s=>slots(s)).map(v=>'<span class="fixed-chip">'+escapeHtml(v)+'</span>').join("")+'</div></aside>');
};
const originalReview=reviewView;
reviewView=function(box){
  originalReview(box);
  const due=PATTERNS.map((p,i)=>({i,due:allCard(i).due})).filter(x=>x.due<=Date.now()).sort((a,b)=>a.due-b.due);
  if(due.length)addHint(box,PATTERNS[due[0].i].text);
};
/* Devam seçimleri, eşleştirme ve sprint: ipucu olarak verilen [] alanları seçeneklerin parçası olmaz. */
halves=function(str){
  const words=tokens(plain(str));
  if(words.length<2)return[words.join(" "),"…"];
  const cut=Math.max(1,Math.min(words.length-1,Math.round(words.length*.48)));
  return[words.slice(0,cut).join(" "),words.slice(cut).join(" ")];
};
/* Yazma / baş harf / dinleyerek yazma: yalnızca normal metin bölümleri doldurulur. */
writingUI=function(box,{showCue=true,initialHint=false,listening=false}={}){
  currentHeader(box);
  const target=PATTERNS[current].text,parts=splitParts(target);
  addHTML(box,'<p class="helper">Köşeli parantezlerdeki ifadeler <b>hazır verilmiştir</b>. Bu alanları yazmana gerek yok. Yalnızca boş metin bölümlerini orijinal Almanca ifadelerle doldur.</p>');
  if(initialHint){
    const letters=parts.map(p=>p.type==="slot"?p.value:tokens(p.value).map(w=>w.charAt(0)+"·".repeat(Math.min(5,Math.max(0,w.length-1)))).join(" ")).join(" ");
    addHTML(box,'<div class="chunk-label">Baş harf ipuçları (köşeli parantezler sabit)</div><div class="demo-board"><div class="first-letters">'+escapeHtml(letters)+'</div></div>');
  }
  if(listening){
    addHTML(box,'<p class="helper">Yalnızca ezberlemen gereken Almanca metin okunur. Hazır verilen köşeli parantezler seslendirilmez.</p><div class="speech-controls"><button class="btn" id="speakBtn">▶ Almanca dinlet</button><button class="btn ghost" id="stopBtn">■ Durdur</button><label for="speed">Hız</label><select id="speed"><option value="0.8">Yavaş (0.8×)</option><option value="1" selected>Normal (1×)</option><option value="1.15">Hızlı (1.15×)</option></select></div><p class="small-note" id="speechNote">Ses özelliği cihaz ve tarayıcıya göre değişebilir.</p>');
  }
  addHTML(box,'<div class="field-label">Kalıbı tamamla — renkli alanlar hazır verilmiştir</div><div class="slot-composer" id="slotWriteArea"></div><div class="statusline"><div class="track"><div class="fill" id="typingFill"></div></div><span class="percent" id="typingPct">0%</span></div><div class="toolbar" id="writingActions"></div><div id="writingResult"></div>');
  const wrap=$('#slotWriteArea'),entries=[];let nth=0;
  parts.forEach(p=>{
    if(p.type==="slot"){wrap.append(el("span","locked-slot",p.value));return}
    if(!p.value.trim())return;
    const section=el("label","slot-write-section");
    const heading=el("span","slot-write-label",String(++nth)+". Almanca bölüm");
    const input=el("textarea","slot-answer");
    input.rows=p.value.length>110?4:p.value.length>60?3:2;
    input.setAttribute("aria-label",nth+". Almanca bölüm");
    input.setAttribute("spellcheck","false");
    input.setAttribute("autocapitalize","off");
    input.setAttribute("autocomplete","off");
    input.placeholder="Bu bölümü ezberden yaz…";
    section.append(heading,input);wrap.append(section);entries.push({part:p.value,input});
  });
  function progress(){
    const total=entries.reduce((n,x)=>n+normalize(x.part).length,0);
    const score=entries.reduce((n,x)=>n+textProgress(x.input.value,x.part)*normalize(x.part).length/100,0);
    const pc=total?Math.min(100,Math.round(score/total*100)):100;
    $('#typingFill').style.width=pc+"%";$('#typingPct').textContent=pc+"%";
  }
  entries.forEach(({input})=>input.addEventListener("input",progress));
  const actions=$('#writingActions');
  const givenInputs=()=>entries.map(e=>e.input.value);
  const isCorrect=()=>entries.every(e=>normalize(e.input.value)===normalize(e.part));
  function comparePanel(){
    const assembled=(()=>{let n=0;return parts.map(p=>p.type==="slot"?p.value:!p.value.trim()?p.value:(entries[n++]?.input.value||"")).join("")})();
    $('#writingResult').innerHTML='<div class="compare"><strong>ORİJİNAL KALIP — REFERANS</strong><p>'+formatted(target)+'</p><hr class="sep"><strong>SENİN CEVABIN (hazır alanlar otomatik eklendi)</strong><p class="muted">'+formatted(assembled)+'</p></div>';
  }
  actButton(actions,"Cevapları kontrol et",()=>{
    const good=isCorrect();record(good);
    entries.forEach(e=>e.input.classList.toggle("correct",normalize(e.input.value)===normalize(e.part)));
    entries.forEach(e=>e.input.classList.toggle("wrong",normalize(e.input.value)!==normalize(e.part)));
    feedback(good?"✓ Bütün yazılacak bölümler doğru. Köşeli parantezler puanlanmadı.":"Yalnızca Almanca bölümleri kontrol ettim. Yanlış bölümleri düzelt.",good?"good":"bad");
    if(!good)comparePanel();
  },"btn");
  actButton(actions,"Orijinali göster",comparePanel,"btn ghost");
  actButton(actions,"Tekrar başla",()=>{
    entries.forEach(e=>{e.input.value="";e.input.classList.remove("correct","wrong")});
    progress();$('#writingResult').replaceChildren();clearFeedback();
  },"btn ghost");
  if(listening){
    $('#speakBtn').onclick=()=>{
      if(!("speechSynthesis" in window)){feedback("Tarayıcında sesli okuma özelliği yok.","bad");return}
      try{
        speechSynthesis.cancel();
        const u=new SpeechSynthesisUtterance(plain(target));u.lang="de-DE";u.rate=Number($('#speed').value);
        u.onstart=()=>$('#speechNote').textContent="🔊 Almanca metin okunuyor…";
        u.onend=()=>$('#speechNote').textContent="Dinleme tamamlandı; istersen tekrar dinle.";
        u.onerror=()=>$('#speechNote').textContent="Ses açılamadı. Tarayıcı ayarlarını kontrol et.";
        speechSynthesis.speak(u);
      }catch(e){feedback("Ses özelliği çalıştırılamadı.","bad")}
    };
    $('#stopBtn').onclick=()=>{try{speechSynthesis.cancel()}catch(e){}};
  }
};
/* Sıralama: hazır alanlar sabit konumdadır; sadece Almanca kelime grupları sıralanır. */
orderView=function(box){
  currentHeader(box);
  addHTML(box,'<p class="helper">Yalnızca Almanca kelime gruplarını sırala. <b>[ ... ]</b> alanları daima görünür ve yerinden oynatılamaz.</p><div class="slot-order" id="orderWithSlots"></div><div class="toolbar" id="orderActions"></div>');
  const textParts=splitParts(PATTERNS[current].text);
  const groups=textParts.filter(p=>p.type==="text"&&p.value.trim()).map(p=>{
    const words=tokens(p.value),sz=Math.max(1,Math.ceil(words.length/Math.min(6,Math.max(2,Math.ceil(words.length/2)))));
    const pieces=[];for(let i=0;i<words.length;i+=sz)pieces.push(words.slice(i,i+sz).join(" "));
    let mix=shuffle(pieces.map((value,index)=>({value,index})));
    if(mix.length>1&&mix.every((v,i)=>v.index===i))mix.reverse();
    return {pieces,mix,selected:[]};
  });
  const host=$('#orderWithSlots');
  function draw(){
    host.replaceChildren();let gi=0;
    textParts.forEach(p=>{
      if(p.type==="slot"){host.append(el("div","locked-slot slot-order-locked",p.value));return}
      if(!p.value.trim())return;
      const g=groups[gi++],card=el("div","slot-order-group");
      const label=el("div","chunk-label","ALMANCA BÖLÜM "+gi+" — sırala");
      const chosen=el("div","chosen");
      if(!g.selected.length)chosen.append(el("span","sub","Parçaları sırayla seç…"));
      g.selected.forEach((k,j)=>{
        const b=el("button","tile",g.pieces[k]);b.type="button";b.title="Geri almak için dokun";
        b.onclick=()=>{g.selected.splice(j,1);draw()};chosen.append(b);
      });
      const tiles=el("div","tiles");
      g.mix.forEach(item=>{
        const b=el("button","tile",item.value);b.type="button";b.disabled=g.selected.includes(item.index);
        b.onclick=()=>{g.selected.push(item.index);draw()};tiles.append(b);
      });
      card.append(label,chosen,tiles);host.append(card);
    });
  }
  draw();const actions=$('#orderActions');
  actButton(actions,"Sıralamayı kontrol et",()=>{
    const good=groups.every(g=>g.selected.length===g.pieces.length&&g.selected.every((v,i)=>v===i));
    feedback(good?"✓ Almanca bölümler doğru sırada! Verilen alanlar puanlanmadı.":"Sıralama henüz tamamlanmadı veya yanlış. Hazır alanları değiştirmene gerek yok.",good?"good":"bad");
    if(good)record(true);
  },"btn");
  actButton(actions,"↶ Son parçayı geri al",()=>{
    const last=[...groups].reverse().find(g=>g.selected.length);if(last)last.selected.pop();draw();clearFeedback();
  },"btn secondary");
  actButton(actions,"Yeniden karıştır",()=>{
    groups.forEach(g=>{g.selected=[];g.mix=shuffle(g.mix)});draw();clearFeedback();
  },"btn ghost");
  actButton(actions,"Doğru sırayı göster",()=>{
    groups.forEach(g=>g.selected=g.pieces.map((_,i)=>i));draw();
    feedback("Doğru Almanca kelime sırası gösterildi. Köşeli parantezler hep sabitti.","info");
  },"btn ghost");
};
/* Devamını yaz: köşeli parantezler gösterilir, yalnızca Almanca devamı puanlanır. */
fullTailView=function(box){
  currentHeader(box);const text=PATTERNS[current].text,h=halves(text);
  addHTML(box,'<p class="helper">Kalıbın devamını yaz. <b>[ ... ]</b> ifadeleri hazır verilmiştir; bunları cevaba yazma.</p>'+hintHtml(text)+'<div class="full-label">Verilen başlangıç</div><div class="full-question" id="fullTailLead"></div><label class="field-label" for="fullTailAnswer">Yalnızca Almanca devamını yaz</label><textarea class="answer" id="fullTailAnswer" placeholder="Devam eden Almanca kısmı yaz…" spellcheck="false" autocapitalize="off"></textarea><div class="toolbar" id="fullTailActions"></div><div id="fullTailResult"></div>');
  $('#fullTailLead').textContent=h[0]+" …";const field=$('#fullTailAnswer');let done=false;
  actButton($('#fullTailActions'),"Yazdığımı kontrol et",()=>{
    if(done)return;done=true;const good=normalize(field.value)===normalize(h[1]);record(good);field.disabled=true;
    feedback(good?"✓ Almanca devam doğru. Köşeli parantezler değerlendirmeye alınmadı.":"Devam kısmını tekrar karşılaştır. Hazır alanları yazmana gerek yok.",good?"good":"bad");
    $('#fullTailResult').append(el("div","full-answer-details","DOĞRU ALMANCA DEVAM:\n"+h[1]+"\n\nSENİN YAZDIĞIN:\n"+(field.value||"(boş)")));
    actButton($('#fullTailActions'),"Sonraki kalıp →",()=>selectPattern(current+1),"btn secondary");
  },"btn");
  actButton($('#fullTailActions'),"Doğru metni göster",()=>{
    $('#fullTailResult').replaceChildren(el("div","full-answer-details","DOĞRU ALMANCA DEVAM:\n"+h[1]));
  },"btn ghost");
};
/* Karma sınav: her sorunun başında köşeli parantezler görünür. */
const originalExam=fullExamView;
fullExamView=function(box){
  originalExam(box);
  if(fullExam&&modeState.examRunning&&fullExam.pos<fullExam.items.length){
    const q=$('#fullExamQuestion'),p=PATTERNS[fullExam.items[fullExam.pos]];
    if(q)addHint(q,p.text);
  }
};
/* Sprintte soru yenilendikçe gerçek sabit alanlar da görünür. */
sprintView=function(box){
  addHTML(box,'<p class="helper">60 saniyede doğru devamı seç. Köşeli parantezler <b>hazır gösterilir</b> ve seçeneklerde sorulmaz.</p><div class="timer-bar"><div class="timer-inside" id="timerFill"></div></div><div class="sprint-metrics"><div class="sprint-num"><strong id="timeLeft">60</strong><span>Kalan saniye</span></div><div class="sprint-num"><strong id="sprintScore">0</strong><span>Doğru cevap</span></div><div class="sprint-num"><strong id="sprintCount">0</strong><span>Toplam soru</span></div></div><div class="demo-board" id="sprintBoard"><div class="hidden-message"><div class="giant">⏱</div><b>Hazır mısın?</b><span>Başlat’a dokununca süre akmaya başlar.</span></div></div><div class="toolbar" id="sprintActions"></div>');
  const actions=$('#sprintActions');let running=false,score=0,count=0,seconds=60;
  actButton(actions,"▶ 60 saniyeyi başlat",startSprint);
  function startSprint(){
    if(running)return;running=true;score=0;count=0;seconds=60;
    $('#timeLeft').textContent="60";$('#sprintScore').textContent="0";$('#sprintCount').textContent="0";$('#timerFill').style.width="100%";
    actions.replaceChildren();sprintQuestion();
    const tick=setInterval(()=>{
      if(mode!=="sprint"){clearInterval(tick);return}
      seconds--;$('#timeLeft').textContent=seconds;$('#timerFill').style.width=seconds/60*100+"%";
      if(seconds<=0){clearInterval(tick);running=false;
        $('#sprintBoard').innerHTML='<div class="hidden-message"><div class="giant">🏁</div><div class="bigcue">'+score+" / "+count+' doğru</div><div>Süre tamamlandı.</div></div>';
        actions.replaceChildren();actButton(actions,"Tekrar oyna",startSprint);
        feedback("Sprint sonucu: <b>"+score+"</b> doğru / "+count+" soru.","info");
      }
    },1000);intervals.push(tick);
  }
  function sprintQuestion(){
    if(!running||mode!=="sprint")return;
    const idx=Math.floor(Math.random()*PATTERNS.length);
    const h=halves(PATTERNS[idx].text),opts=choicesFor(idx),board=$('#sprintBoard');
    board.innerHTML='<div class="cue">DOĞRU ALMANCA DEVAMI SEÇ</div>'+hintHtml(PATTERNS[idx].text)+'<div class="prompt-panel">'+escapeHtml(h[0])+' …</div><div id="sprintOpts"></div>';
    opts.forEach((o,i)=>{
      const b=el("button","option","ABCD"[i]+") "+o.text);
      b.onclick=()=>{if(!running)return;count++;if(o.idx===idx){score++;b.classList.add("correct")}else b.classList.add("incorrect");
        $('#sprintScore').textContent=score;$('#sprintCount').textContent=count;
        document.querySelectorAll("#sprintOpts .option").forEach(x=>x.disabled=true);
        const t=setTimeout(()=>{if(running&&mode==="sprint")sprintQuestion()},220);intervals.push(t);
      };$('#sprintOpts').append(b);
    });
  }
};
})();
