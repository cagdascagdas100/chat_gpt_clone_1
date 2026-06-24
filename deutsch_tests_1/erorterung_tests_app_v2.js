let currentTestIndex=0;
function esc(s){return String(s).replace(/[&<>]/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;"}[c]));}
function renderTabs(){
  document.getElementById("tabs").innerHTML=tests.map((t,i)=>`<button class="tab ${i===currentTestIndex?"active":""}" onclick="switchTest(${i})">${esc(t.title.split(" – ")[0])}</button>`).join("");
}
function renderTest(){
  const t=tests[currentTestIndex];
  document.getElementById("app").innerHTML=
    `<div class="panel-head"><h2>${esc(t.title)}</h2><p class="desc">${esc(t.description)} · ${t.questions.length} Aufgaben</p><div class="tools"><button class="action" onclick="checkAnswers()">Auswertung</button><button class="action secondary" onclick="resetTest()">Zurücksetzen</button><span class="score" id="score"></span></div></div>`+
    `<div class="questions">${t.questions.map((qq,qi)=>renderQuestion(qq,qi)).join("")}</div>`+
    `<div class="wrong-box"><h2>Falsche / offene Fragen als kopierbarer Text</h2><p class="muted">Nach der Auswertung erscheinen hier nur die falsch beantworteten oder offenen Aufgaben.</p><textarea id="wrongText" placeholder="Bitte zuerst Auswertung drücken."></textarea><div class="tools"><button class="action" onclick="copyWrongText()">Text kopieren</button><span class="muted" id="copyStatus"></span></div></div>`;
}
function renderQuestion(qq,qi){
  return `<article class="question" id="q-${qi}"><div class="q-title">${qi+1}. ${esc(qq.q)}</div>`+
    qq.options.map((op,oi)=>`<label class="option"><input type="radio" name="q${qi}" value="${oi}"> <span><b>${letters[oi]})</b> ${esc(op)}</span></label>`).join("")+
    `<div class="feedback" id="fb-${qi}"></div></article>`;
}
function selectedValue(i){
  const input=document.querySelector(`input[name="q${i}"]:checked`);
  return input?Number(input.value):null;
}
function checkAnswers(){
  const t=tests[currentTestIndex];
  let correct=0;
  const wrong=[];
  t.questions.forEach((qq,i)=>{
    const selected=selectedValue(i);
    const card=document.getElementById(`q-${i}`);
    const fb=document.getElementById(`fb-${i}`);
    card.classList.remove("correct","wrong");
    fb.className="feedback";
    if(selected===qq.answer){
      correct++;
      card.classList.add("correct");
      fb.classList.add("ok");
      fb.textContent="Richtig.";
    }else{
      card.classList.add("wrong");
      fb.classList.add("no");
      fb.textContent=selected===null?"Nicht beantwortet.":"Falsch.";
      wrong.push({number:i+1,question:qq,selected});
    }
  });
  document.getElementById("score").textContent=`${correct} / ${t.questions.length} richtig`;
  document.getElementById("wrongText").value=wrong.length?createWrongText(t,wrong):`Test: ${t.title}\n\nAlle Aufgaben wurden richtig beantwortet. Bitte erstelle mir zur Wiederholung fünf neue C1/C2-Beispielsätze zu denselben Regeln.`;
  document.getElementById("copyStatus").textContent="Kontrolle abgeschlossen.";
  document.getElementById("wrongText").scrollIntoView({behavior:"smooth",block:"nearest"});
}
function createWrongText(t,wrong){
  const out=[`Test: ${t.title}`,"","Bitte erkläre mir die richtigen Lösungen zu den folgenden falsch oder nicht beantworteten Aufgaben. Erkläre jede Aufgabe mit Kasus, Signalwort, Satzstellung, Redemittel-Funktion und einer kurzen Merkregel für C1/C2-Erörterungen.",""];
  wrong.forEach(item=>{
    const qq=item.question;
    out.push(`Aufgabe ${item.number}: ${qq.q}`);
    out.push(`Meine Antwort: ${item.selected===null?"nicht beantwortet":letters[item.selected]+") "+qq.options[item.selected]}`);
    out.push(`Richtige Antwort: ${letters[qq.answer]}) ${qq.options[qq.answer]}`);
    out.push(`Regel: ${qq.rule}`);
    out.push("Optionen:");
    qq.options.forEach((op,i)=>out.push(`${letters[i]}) ${op}`));
    out.push("");
  });
  return out.join("\n");
}
function resetTest(){
  document.querySelectorAll("input[type=radio]").forEach(x=>x.checked=false);
  document.querySelectorAll(".question").forEach(x=>x.classList.remove("correct","wrong"));
  document.querySelectorAll(".feedback").forEach(x=>{x.textContent="";x.className="feedback";});
  document.getElementById("score").textContent="";
  document.getElementById("wrongText").value="";
  document.getElementById("copyStatus").textContent="";
}
function copyWrongText(){
  const textarea=document.getElementById("wrongText");
  textarea.select();
  textarea.setSelectionRange(0, textarea.value.length);
  try{
    navigator.clipboard && navigator.clipboard.writeText(textarea.value);
    document.getElementById("copyStatus").textContent="Kopyalandı.";
  }catch(e){
    document.execCommand("copy");
    document.getElementById("copyStatus").textContent="Kopyalandı.";
  }
}
function switchTest(index){
  currentTestIndex=index;
  renderTabs();
  renderTest();
  window.scrollTo({top:0,behavior:"smooth"});
}
renderTabs();
renderTest();
