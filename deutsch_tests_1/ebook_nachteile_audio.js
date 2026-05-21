(function(){
  let chunks=[];
  let index=0;
  let speaking=false;
  let paused=false;
  let activeUtterance=null;
  function isTarget(level){
    try{return window.selected==='t23' && level==='long'}catch(e){return false}
  }
  function cleanText(s){return String(s||'').replace(/\s+/g,' ').replace(/\bKurz\b|\bMittel\b|\bLang\b/g,'').trim()}
  function collectChunks(){
    const content=document.getElementById('lessonContent');
    if(!content)return [];
    const clone=content.cloneNode(true);
    const old=clone.querySelector('#ebookAudioPanel');
    if(old)old.remove();
    const nodes=[...clone.querySelectorAll('h3,h4,p,li,td')];
    let arr=nodes.map(n=>cleanText(n.textContent)).filter(t=>t.length>25);
    let out=[];
    arr.forEach(t=>{
      if(t.length>900){
        t.split(/(?<=[.!?])\s+/).forEach(x=>{x=cleanText(x);if(x.length>25)out.push(x)});
      }else out.push(t);
    });
    return out;
  }
  function getGermanVoice(){
    const voices=speechSynthesis.getVoices()||[];
    return voices.find(v=>/de-DE/i.test(v.lang)&&/Google|Microsoft|Natural|Online|Anna|Katja|Amala|Conrad/i.test(v.name))||voices.find(v=>/^de/i.test(v.lang))||null;
  }
  function setStatus(txt){const s=document.getElementById('ebookAudioStatus');if(s)s.textContent=txt}
  function setCounter(){const c=document.getElementById('ebookAudioCounter');if(c)c.textContent=chunks.length?(index+1)+' / '+chunks.length:'0 / 0'}
  function stop(){
    speechSynthesis.cancel(); speaking=false; paused=false; activeUtterance=null; setStatus('Gestoppt'); setCounter();
  }
  function speakCurrent(){
    if(!('speechSynthesis' in window)){setStatus('Bu tarayıcı sesli okuma desteklemiyor.');return}
    chunks=chunks.length?chunks:collectChunks();
    if(!chunks.length){setStatus('Okunacak metin bulunamadı.');return}
    speechSynthesis.cancel();
    const u=new SpeechSynthesisUtterance(chunks[index]);
    u.lang='de-DE';
    u.rate=Number(document.getElementById('ebookAudioRate')?.value||0.88);
    u.pitch=0.96;
    u.volume=1;
    const v=getGermanVoice();
    if(v)u.voice=v;
    activeUtterance=u; speaking=true; paused=false;
    setStatus('Okunuyor: '+chunks[index].slice(0,90)+(chunks[index].length>90?'...':''));
    setCounter();
    u.onend=function(){
      if(!speaking)return;
      if(index<chunks.length-1){index++; speakCurrent()}else{speaking=false; setStatus('Bitti'); setCounter()}
    };
    u.onerror=function(){speaking=false; setStatus('Sesli okuma durdu veya tarayıcı sesi engelledi.')};
    speechSynthesis.speak(u);
  }
  function play(){chunks=collectChunks(); if(!chunks.length)return setStatus('Okunacak metin bulunamadı.'); if(index>=chunks.length)index=0; speakCurrent()}
  function pause(){if(speechSynthesis.speaking&&!speechSynthesis.paused){speechSynthesis.pause(); paused=true; setStatus('Duraklatıldı')}}
  function resume(){if(speechSynthesis.paused){speechSynthesis.resume(); paused=false; setStatus('Devam ediyor')}}
  function prev(){chunks=collectChunks(); index=Math.max(0,index-1); speakCurrent()}
  function next(){chunks=collectChunks(); index=Math.min((chunks.length||1)-1,index+1); speakCurrent()}
  function inject(){
    const content=document.getElementById('lessonContent');
    if(!content||document.getElementById('ebookAudioPanel'))return;
    chunks=collectChunks(); index=0;
    const div=document.createElement('div');
    div.id='ebookAudioPanel';
    div.style.cssText='border:2px solid #8a5a44;border-radius:14px;padding:14px;margin:0 0 18px;background:#fff8ed;font-family:Arial,sans-serif';
    div.innerHTML='<h3 style="margin:0 0 8px;color:#183642">🔊 Almanca sesli konu anlatımı</h3><p style="margin:0 0 10px;color:#4b5563">Bu panel uzun konu anlatımını Almanca tarayıcı sesiyle okur. Ses kalitesi cihazındaki Almanca sese bağlıdır.</p><div style="display:flex;gap:8px;flex-wrap:wrap;align-items:center"><button id="ebookAudioPlay">▶ Başlat</button><button id="ebookAudioPause" class="sec">⏸ Duraklat</button><button id="ebookAudioResume" class="ghost">▶ Devam</button><button id="ebookAudioStop" class="danger">■ Durdur</button><button id="ebookAudioPrev" class="ghost">← Geri</button><button id="ebookAudioNext" class="ghost">İleri →</button><label>Hız <input id="ebookAudioRate" type="range" min="0.65" max="1.15" step="0.05" value="0.88" style="width:120px"></label><b id="ebookAudioCounter">0 / 0</b></div><p id="ebookAudioStatus" style="margin:10px 0 0;color:#374151">Hazır</p>';
    content.insertBefore(div,content.firstChild);
    document.getElementById('ebookAudioPlay').onclick=play;
    document.getElementById('ebookAudioPause').onclick=pause;
    document.getElementById('ebookAudioResume').onclick=resume;
    document.getElementById('ebookAudioStop').onclick=stop;
    document.getElementById('ebookAudioPrev').onclick=prev;
    document.getElementById('ebookAudioNext').onclick=next;
    document.getElementById('ebookAudioRate').oninput=function(){if(speaking&&!paused)speakCurrent()};
    setCounter();
  }
  document.addEventListener('DOMContentLoaded',function(){
    if('speechSynthesis' in window){speechSynthesis.getVoices(); speechSynthesis.onvoiceschanged=function(){speechSynthesis.getVoices()}}
    const old=window.startLesson;
    if(typeof old==='function'){
      window.startLesson=function(level){
        stop();
        old(level);
        setTimeout(function(){if(isTarget(level))inject()},80);
      };
    }
    document.addEventListener('click',function(){
      const lesson=document.getElementById('lesson');
      const visible=lesson&&!lesson.classList.contains('hide');
      if(visible&&window.selected==='t23'&&!document.getElementById('ebookAudioPanel')){
        const title=(document.getElementById('lessonTitle')||{}).textContent||'';
        if(/E-Books.*Nachteile/i.test(title)&&/Lang|Uzun/i.test(document.body.textContent))setTimeout(inject,120);
      }
    });
    window.addEventListener('beforeunload',stop);
  });
})();
