(function(){
  function onReady(fn){
    if(document.readyState==='loading') document.addEventListener('DOMContentLoaded', fn); else fn();
  }
  function htmlToText(html){
    var d=document.createElement('div');
    d.innerHTML=String(html||'');
    return (d.textContent||d.innerText||'').replace(/\s+/g,' ').trim();
  }
  function wordCount(html){
    var text=htmlToText(html);
    if(!text) return 0;
    var m=text.match(/[\p{L}\p{N}]+(?:[-’'][\p{L}\p{N}]+)*/gu);
    return m ? m.length : 0;
  }
  function esc(s){
    return String(s==null?'':s).replace(/[&<>"']/g,function(c){return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c];});
  }
  function lessonFields(lesson){
    lesson=lesson||{};
    return {
      short: lesson.short || lesson.kisa || lesson.brief || '',
      medium: lesson.medium || lesson.orta || '',
      long: lesson.long || lesson.uzun || ''
    };
  }
  function topicTitle(key){
    var t=(window.DEUTSCH_TESTS&&window.DEUTSCH_TESTS[key])||{};
    return t.title || t.topic || key;
  }
  function isBevor(key){
    var t=(window.DEUTSCH_TESTS&&window.DEUTSCH_TESTS[key])||{};
    return t.category==='Bevor Schreiben' || /Bevor/i.test(t.category||'') || /Erörterung/i.test(t.topic||'');
  }
  function keyOrder(a,b){
    var na=parseInt(String(a).replace(/\D+/g,''),10), nb=parseInt(String(b).replace(/\D+/g,''),10);
    if(!isNaN(na)&&!isNaN(nb)) return na-nb;
    return String(a).localeCompare(String(b));
  }
  function buildReport(){
    var lessons=window.DEUTSCH_LESSONS||{};
    var keys=Object.keys(lessons).filter(isBevor).sort(keyOrder);
    var rows=[];
    var totalShort=0,totalMedium=0,totalLong=0,missing=0,belowLong=0;
    keys.forEach(function(k){
      var f=lessonFields(lessons[k]);
      var s=wordCount(f.short), m=wordCount(f.medium), l=wordCount(f.long);
      totalShort+=s; totalMedium+=m; totalLong+=l;
      var missingParts=[];
      if(!s) missingParts.push('kısa yok');
      if(!m) missingParts.push('orta yok');
      if(!l) missingParts.push('uzun yok');
      if(missingParts.length) missing++;
      var status='Tamam';
      var cls='okLine';
      if(missingParts.length){status=missingParts.join(', '); cls='badLine';}
      else if(l<2000){status='Uzun 2000 altı'; cls='warnLine'; belowLong++;}
      rows.push('<tr class="'+cls+'"><td>'+esc(k)+'</td><td>'+esc(topicTitle(k))+'</td><td>'+s+'</td><td>'+m+'</td><td>'+l+'</td><td>'+esc(status)+'</td></tr>');
    });
    if(!rows.length){
      rows.push('<tr><td colspan="6">Bevor Schreiben konu anlatımı verisi bulunamadı. Sayfa henüz tüm veri dosyalarını yüklememiş olabilir; 5 saniye bekleyip tekrar saydır.</td></tr>');
    }
    var now=new Date().toLocaleString('tr-TR');
    return '<div class="wcSummary">'+
      '<p><b>Canlı sayım zamanı:</b> '+esc(now)+'</p>'+
      '<p><b>Toplam konu:</b> '+keys.length+' · <b>Kısa toplam:</b> '+totalShort+' · <b>Orta toplam:</b> '+totalMedium+' · <b>Uzun toplam:</b> '+totalLong+'</p>'+
      '<p><b>Eksik kısa/orta/uzun:</b> '+missing+' · <b>Uzun 2000 altı:</b> '+belowLong+'</p>'+
      '<p class="muted">Bu tablo GitHub dosyasını değil, sayfanın o anda gerçekten yüklediği canlı konu anlatımı verisini sayar. Başlık kaybolursa ya da uzun metin kısalırsa burada hemen görünür.</p>'+
      '</div><div class="wcTableWrap"><table class="wcTable"><thead><tr><th>ID</th><th>Konu</th><th>Kısa</th><th>Orta</th><th>Uzun</th><th>Durum</th></tr></thead><tbody>'+rows.join('')+'</tbody></table></div>';
  }
  function copyReportText(){
    var box=document.getElementById('wordCountReport');
    if(!box) return;
    var text=box.innerText||'';
    if(navigator.clipboard&&navigator.clipboard.writeText){navigator.clipboard.writeText(text).catch(function(){});}
  }
  function install(){
    if(document.getElementById('btnSettingsWordCount')) return;
    var style=document.createElement('style');
    style.textContent='.settingsBtn{background:#5b4636!important}.settingsPanel{border:2px solid #c4a484}.wcTableWrap{overflow:auto;max-height:62vh;border:1px solid #ddd6ca;border-radius:12px}.wcTable{width:100%;border-collapse:collapse;font:14px Arial;background:#fff}.wcTable th{position:sticky;top:0;background:#183642;color:#fff;padding:8px;text-align:left}.wcTable td{border-bottom:1px solid #eee;padding:7px;vertical-align:top}.wcSummary{font-family:Arial}.okLine td{background:#f0fdf4}.warnLine td{background:#fffbeb}.badLine td{background:#fff1f2}.wcActions{display:flex;gap:8px;flex-wrap:wrap;margin:10px 0}';
    document.head.appendChild(style);
    var start=document.getElementById('start') || document.querySelector('main') || document.body;
    var btn=document.createElement('button');
    btn.id='btnSettingsWordCount';
    btn.className='settingsBtn';
    btn.textContent='Ayarlar · Kelime Sayımı';
    var p=start.querySelector('p') || start.firstChild;
    if(p && p.parentNode) p.parentNode.insertBefore(btn, p.nextSibling); else start.insertBefore(btn,start.firstChild);
    var panel=document.createElement('section');
    panel.id='settingsWordCountPanel';
    panel.className='card settingsPanel hide';
    panel.innerHTML='<h2>Ayarlar · Canlı Kelime Sayımı</h2><p class="muted">Bevor Schreiben konu anlatımlarının kısa, orta ve uzun metinleri canlı olarak sayılır.</p><div class="wcActions"><button id="btnRunWordCount">Kelime sayısını yenile</button><button class="ghost" id="btnCopyWordCount">Raporu kopyala</button><button class="ghost" id="btnCloseWordCount">Kapat</button></div><div id="wordCountReport"></div>';
    start.parentNode.insertBefore(panel,start.nextSibling);
    function run(){document.getElementById('wordCountReport').innerHTML=buildReport();}
    btn.addEventListener('click',function(){panel.classList.remove('hide');run();panel.scrollIntoView({behavior:'smooth',block:'start'});});
    document.getElementById('btnRunWordCount').addEventListener('click',run);
    document.getElementById('btnCopyWordCount').addEventListener('click',copyReportText);
    document.getElementById('btnCloseWordCount').addEventListener('click',function(){panel.classList.add('hide');});
  }
  onReady(function(){setTimeout(install,250);setTimeout(function(){if(!document.getElementById('btnSettingsWordCount')) install();},1500);});
})();

/* Ana menü düzeltmesi: ana sayfada yalnızca 5 ana kart kalır. */
(function(){
  var cards=[
    ['catTest','Test','C1/C2 Erörterung test sistemini aç.','./erorterung_tests.html?v=stable1',''],
    ['catGrammar','Genel Grammar','Satzbau, Kasus, Artikel, Pronomen, Negation ve doğru gramerle yazma.','','Genel Grammer'],
    ['catWrite','Schreiben Fehler','Kelime, kalıp, Präposition ve C1/C2 yazma hatası testleri.','','Schreiben Fehlern'],
    ['catNVV','NVV','Nomen-Verb-Verbindungen ve akademik yazma kalıpları.','','NVV'],
    ['catBefore','Bevor Schreiben / Bewerbungsschreiben','Selbstfahrende Autos: C1/C2 Vorteilsabsatz, Redemittel, NVV ve yazma hazırlığı dahil tüm Vorteile/Nachteile konu anlatımları burada.','','Bevor Schreiben']
  ];
  function e(s){return String(s||'').replace(/[&<>']/g,function(c){return {'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#039;'}[c];});}
  function render(){
    var list=document.getElementById('testList'); if(!list) return;
    try{selectedCategory=''; selected='';}catch(x){}
    try{ if(typeof setControls==='function') setControls(false); }catch(x){}
    var html='<h2>İlk olarak ana başlığı seç</h2><p class="muted">Ana menüde sadece 5 ana başlık gösterilir. Alt konu başlıkları kendi ana bölümünün içine girince görünür.</p><div id="strictMainGrid" style="display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:12px;margin-top:12px">';
    cards.forEach(function(c){
      var inner='<b>'+e(c[1])+'</b><br><span class="muted">'+e(c[2])+'</span>';
      html += c[3] ? '<a class="opt" id="'+c[0]+'" href="'+e(c[3])+'" style="text-align:left;display:block;text-decoration:none;color:inherit">'+inner+'</a>' : '<button class="opt" style="text-align:left" id="'+c[0]+'">'+inner+'</button>';
    });
    list.innerHTML=html+'</div>';
    cards.forEach(function(c){ if(!c[4]) return; var b=document.getElementById(c[0]); if(b) b.onclick=function(){ if(typeof renderTests==='function') renderTests(c[4]); }; });
  }
  window.renderCategoryChoice=render;
  document.addEventListener('DOMContentLoaded',function(){render(); setTimeout(render,400);});
  if(document.readyState!=='loading'){render(); setTimeout(render,400);}
})();
