function render(){
  let h="",num=1;
  ORDER.forEach(k=>{
    let qs=current.filter(q=>q.g===k);
    if(!qs.length)return;
    h+='<section style="border:1px solid #e5ded4;border-radius:14px;padding:12px;margin:14px 0;background:#fffdf9"><h3>'+esc(TIT[k])+' <span class="muted">('+qs.length+')</span></h3>';
    qs.forEach(q=>{
      q.id="q_"+(num-1);
      h+='<div class="q"><div class="qt">'+num+'. '+esc(q.q)+'</div>';
      if(q.typ==="tf"){
        h+='<label class="opt"><input type="radio" name="'+q.id+'" value="true"> Richtig</label><label class="opt"><input type="radio" name="'+q.id+'" value="false"> Falsch</label>';
      }else{
        h+=q.op.map((o,j)=>'<label class="opt"><input type="radio" name="'+q.id+'" value="'+j+'"> '+String.fromCharCode(65+j)+') '+esc(o)+'</label>').join("");
      }
      h+='<div id="fb_'+q.id+'"></div></div>';
      num++;
    });
    h+='</section>';
  });
  $("qs").innerHTML=h;
  document.querySelectorAll("#qs input").forEach(e=>e.onchange=()=>{let q=current.find(x=>x.id===e.name);if(q)instant(q);progress()});
}

function catOf(t){
  if(t&&t.category==="Genel Grammer")return"Genel Grammer";
  if(t&&t.category==="NVV")return"NVV";
  return"Schreiben Fehlern";
}

function renderCategoryChoice(){
  selectedCategory="";selected="";setControls(false);
  $("testList").innerHTML=`
    <h2>İlk olarak ana başlığı seç</h2>
    <p class="muted">Önce çalışma alanını seç. Sonra ilgili testleri, konu anlatımını veya harf kutucukları modunu açabilirsin.</p>
    <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:12px;margin-top:12px">
      <button class="opt" style="text-align:left" id="catGrammar"><b>Genel Grammer</b><br><span class="muted">Satzbau, Kasus, Artikel, Pronomen, Negation.</span></button>
      <button class="opt" style="text-align:left" id="catWrite"><b>Schreiben Fehlern</b><br><span class="muted">Kelime, kalıp, Präposition ve C1/C2 yazma hataları.</span></button>
      <button class="opt" style="text-align:left" id="catNVV"><b>NVV</b><br><span class="muted">Nomen-Verb-Verbindungen: ekonomi, toplum, medya, çevre, akademik argümantasyon.</span></button>
    </div>`;
  $("catGrammar").onclick=()=>renderTests("Genel Grammer");
  $("catWrite").onclick=()=>renderTests("Schreiben Fehlern");
  $("catNVV").onclick=()=>renderTests("NVV");
}

document.addEventListener("DOMContentLoaded",function(){try{renderCategoryChoice()}catch(e){console.error(e)}});
