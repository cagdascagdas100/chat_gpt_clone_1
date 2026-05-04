function catOf(t){
  if(t && t.category==="Genel Grammer") return "Genel Grammer";
  if(t && t.category==="NVV") return "NVV";
  return "Schreiben Fehlern";
}
function renderCategoryChoice(){
  selectedCategory=""; selected=""; setControls(false);
  $("testList").innerHTML=`
    <h2>İlk olarak ana başlığı seç</h2>
    <p class="muted">Önce çalışma alanını seç. Sonra ilgili testleri, konu anlatımını veya harf kutucukları modunu açabilirsin.</p>
    <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:12px;margin-top:12px">
      <button class="opt" style="text-align:left" id="catGrammar"><b>Genel Grammer</b><br><span class="muted">Satzbau, Kasus, Artikel, Pronomen, Negation ve doğru gramerle yazma.</span></button>
      <button class="opt" style="text-align:left" id="catWrite"><b>Schreiben Fehlern</b><br><span class="muted">4–13 arası kelime, kalıp, Präposition ve C1/C2 yazma hatası testleri.</span></button>
      <button class="opt" style="text-align:left" id="catNVV"><b>NVV</b><br><span class="muted">Nomen-Verb-Verbindungen: Wirtschaft, Gesellschaft/Medien/Bildung, Umwelt/Innovation/Argumentation.</span></button>
    </div>`;
  $("catGrammar").onclick=()=>renderTests("Genel Grammer");
  $("catWrite").onclick=()=>renderTests("Schreiben Fehlern");
  $("catNVV").onclick=()=>renderTests("NVV");
}
document.addEventListener("DOMContentLoaded",function(){
  try{ renderCategoryChoice(); }catch(e){ console.error(e); }
});
