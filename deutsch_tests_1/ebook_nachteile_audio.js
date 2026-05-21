(function(){
  let chunks=[];
  let index=0;
  let speaking=false;
  let paused=false;
  let activeUtterance=null;
  let currentText='';
  let currentChar=0;
  let resumeOffset=0;

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
    const floating=clone.querySelector('#ebookFloatingAudioControls');
    if(floating)floating.remove();
    const nodes=[...clone.querySelectorAll('h3,h4,p,li,td')];
    let arr=nodes.map(n=>cleanText(n.textContent)).filter(t=>t.length>25);
    let out=[];
    arr.forEach(t=>{
      if(t.length>650){
        t.split(/(?<=[.!?])\s+/).forEach(x=>{x=cleanText(x);if(x.length>25)out.push(x)});
      }else out.push(t);
    });
    return out;
  }
  function getGermanVoice(){
    const voices=speechSynthesis.getVoices()||[];
    const score=v=>{
      const n=(v.name+' '+v.lang).toLowerCase();
      let s=0;
      if(/^de-de/i.test(v.lang))s+=100;
      else if(/^de/i.test(v.lang))s+=70;
      if(/natural|neural|online|premium|enhanced|wavenet/i.test(v.name))s+=60;
      if(/microsoft/i.test(v.name))s+=40;
      if(/google/i.test(v.name))s+=35;
      if(/katja|conrad|anna|amala|seraphina|florian|helena|heda|markus|stefan/i.test(n))s+=30;
      if(v.localService===false)s+=10;
      return s;
    };
    return voices.filter(v=>/^de/i.test(v.lang)).sort((a,b)=>score(b)-score(a))[0]||null;
  }
  function setStatus(txt){
    const s=document.getElementById('ebookAudioStatus');if(s)s.textContent=txt;
    const fs=document.getElementById('ebookFloatStatus');if(fs)fs.textContent=txt;
  }
  function setCounter(){
    const text=chunks.length?(index+1)+' / '+chunks.length:'0 / 0';
    const c=document.getElementById('ebookAudioCounter');if(c)c.textContent=text;
    const fc=document.getElementById('ebookFloatCounter');if(fc)fc.textContent=text;
  }
  function ensureFloatingControls(){
    if(document.getElementById('ebookFloatingAudioControls'))return;
    const div=document.createElement('div');
    div.id='ebookFloatingAudioControls';
    div.style.cssText='position:fixed;right:16px;bottom:16px;z-index:9999;background:#183642;color:#fff;border:2px solid #c4a484;border-radius:16px;padding:10px 12px;box-shadow:0 8px 24px #0006;font-family:Arial,sans-serif;display:none;max-width:260px';
    div.innerHTML='<div style="font-weight:700;margin-bottom:6px">🔊 E-Books Audio</div><div style="display:flex;gap:6px;flex-wrap:wrap"><button id="ebookFloatBack5" style="background:#fff;color:#183642;border:0;border-radius:10px;padding:8px 10px;font-weight:700">↶ 5 sn</button><button id="ebookFloatStop" style="background:#b91c1c;color:#fff;border:0;border-radius:10px;padding:8px 10px;font-weight:700">■ Durdur</button></div><div id="ebookFloatCounter" style="font-size:12px;margin-top:6px;opacity:.9">0 / 0</div><div id="ebookFloatStatus" style="font-size:11px;margin-top:3px;opacity:.85">Hazır</div>';
    document.body.appendChild(div);
    document.getElementById('ebookFloatStop').onclick=stop;
    document.getElementById('ebookFloatBack5').onclick=backFiveSeconds;
  }
  function showFloating(show){
    ensureFloatingControls();
    const el=document.getElementById('ebookFloatingAudioControls');
    if(el)el.style.display=show?'block':'none';
  }
  function stop(){
    if('speechSynthesis' in window)speechSynthesis.cancel();
    speaking=false; paused=false; activeUtterance=null; currentChar=0; resumeOffset=0;
    setStatus('Gestoppt'); setCounter(); showFloating(false);
  }
  function speakCurrent(fromChar){
    if(!('speechSynthesis' in window)){setStatus('Bu tarayıcı sesli okuma desteklemiyor.');return}
    chunks=chunks.length?chunks:collectChunks();
    if(!chunks.length){setStatus('Okunacak metin bulunamadı.');return}
    speechSynthesis.cancel();
    resumeOffset=Math.max(0,Number(fromChar||0));
    currentText=chunks[index]||'';
    const text=currentText.slice(resumeOffset).trim();
    if(!text){
      if(index<chunks.length-1){index++; resumeOffset=0; return speakCurrent(0)}
      speaking=false; setStatus('Bitti'); showFloating(false); return;
    }
    const u=new SpeechSynthesisUtterance(text);
    u.lang='de-DE';
    u.rate=Number(document.getElementById('ebookAudioRate')?.value||0.86);
    u.pitch=0.92;
    u.volume=1;
    const v=getGermanVoice();
    if(v)u.voice=v;
    activeUtterance=u; speaking=true; paused=false; showFloating(true);
    setStatus('Okunuyor'); setCounter();
    u.onboundary=function(e){
      if(typeof e.charIndex==='number')currentChar=resumeOffset+e.charIndex;
    };
    u.onend=function(){
      if(!speaking)return;
      currentChar=0; resumeOffset=0;
      if(index<chunks.length-1){index++; speakCurrent(0)}else{speaking=false; setStatus('Bitti'); setCounter(); showFloating(false)}
    };
    u.onerror=function(){speaking=false; setStatus('Sesli okuma durdu veya tarayıcı sesi engelledi.'); showFloating(false)};
    speechSynthesis.speak(u);
  }
  function play(){chunks=collectChunks(); if(!chunks.length)return setStatus('Okunacak metin bulunamadı.'); if(index>=chunks.length)index=0; speakCurrent(0)}
  function pause(){if(speechSynthesis.speaking&&!speechSynthesis.paused){speechSynthesis.pause(); paused=true; setStatus('Duraklatıldı')}}
  function resume(){if(speechSynthesis.paused){speechSynthesis.resume(); paused=false; setStatus('Devam ediyor')}}
  function prev(){chunks=collectChunks(); index=Math.max(0,index-1); currentChar=0; speakCurrent(0)}
  function next(){chunks=collectChunks(); index=Math.min((chunks.length||1)-1,index+1); currentChar=0; speakCurrent(0)}
  function backFiveSeconds(){
    chunks=chunks.length?chunks:collectChunks();
    if(!chunks.length)return;
    const charsBack=95;
    if(currentChar>charsBack){
      speakCurrent(currentChar-charsBack);
    }else if(index>0){
      index--;
      const prevText=chunks[index]||'';
      speakCurrent(Math.max(0,prevText.length-charsBack));
    }else{
      speakCurrent(0);
    }
  }
  function inject(){
    const content=document.getElementById('lessonContent');
    if(!content)return;
    ensureFloatingControls();
    if(document.getElementById('ebookAudioPanel')){
      const playBtn=document.querySelector('#ebookAudioPanel button[onclick="ebookAudioPlay()"]');
      chunks=collectChunks(); setCounter();
      return;
    }
    chunks=collectChunks(); index=0;
    const div=document.createElement('div');
    div.id='ebookAudioPanel';
    div.style.cssText='border:2px solid #8a5a44;border-radius:14px;padding:14px;margin:0 0 18px;background:#fff8ed;font-family:Arial,sans-serif';
    div.innerHTML='<h3 style="margin:0 0 8px;color:#183642">🔊 Almanca sesli konu anlatımı</h3><p style="margin:0 0 10px;color:#4b5563">Bu panel uzun konu anlatımını cihazındaki en doğal Almanca sesle okur. En iyi sonuç için Chrome/Edge ve Windows/Mac Almanca doğal seslerini kullan.</p><div style="display:flex;gap:8px;flex-wrap:wrap;align-items:center"><button id="ebookAudioPlay">▶ Başlat</button><button id="ebookAudioPause" class="sec">⏸ Duraklat</button><button id="ebookAudioResume" class="ghost">▶ Devam</button><button id="ebookAudioStop" class="danger">■ Durdur</button><button id="ebookAudioBack5" class="ghost">↶ 5 sn geri</button><button id="ebookAudioPrev" class="ghost">← Bölüm</button><button id="ebookAudioNext" class="ghost">Bölüm →</button><label>Hız <input id="ebookAudioRate" type="range" min="0.65" max="1.15" step="0.05" value="0.86" style="width:120px"></label><b id="ebookAudioCounter">0 / 0</b></div><p id="ebookAudioStatus" style="margin:10px 0 0;color:#374151">Hazır</p>';
    content.insertBefore(div,content.firstChild);
    document.getElementById('ebookAudioPlay').onclick=play;
    document.getElementById('ebookAudioPause').onclick=pause;
    document.getElementById('ebookAudioResume').onclick=resume;
    document.getElementById('ebookAudioStop').onclick=stop;
    document.getElementById('ebookAudioBack5').onclick=backFiveSeconds;
    document.getElementById('ebookAudioPrev').onclick=prev;
    document.getElementById('ebookAudioNext').onclick=next;
    document.getElementById('ebookAudioRate').oninput=function(){if(speaking&&!paused)speakCurrent(currentChar)};
    setCounter();
  }
  window.ebookAudioPlay=play;
  window.ebookAudioPause=pause;
  window.ebookAudioResume=resume;
  window.ebookAudioStop=stop;
  window.ebookAudioPrev=prev;
  window.ebookAudioNext=next;
  window.ebookAudioBack5=backFiveSeconds;
  document.addEventListener('DOMContentLoaded',function(){
    if('speechSynthesis' in window){speechSynthesis.getVoices(); speechSynthesis.onvoiceschanged=function(){speechSynthesis.getVoices()}}
    const old=window.startLesson;
    if(typeof old==='function'){
      window.startLesson=function(level){
        stop();
        old(level);
        setTimeout(function(){if(isTarget(level))inject()},120);
      };
    }
    document.addEventListener('click',function(){
      const lesson=document.getElementById('lesson');
      const visible=lesson&&!lesson.classList.contains('hide');
      if(visible&&window.selected==='t23'){
        const title=(document.getElementById('lessonTitle')||{}).textContent||'';
        if(/E-Books.*Nachteile/i.test(title))setTimeout(inject,160);
      }
    });
    window.addEventListener('beforeunload',stop);
  });
})();
