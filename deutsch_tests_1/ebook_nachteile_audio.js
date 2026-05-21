(function(){
  let chunks=[], index=0, speaking=false, paused=false, currentChar=0, resumeOffset=0;
  let realAudio=null, realAudioReady=false, realAudioChecked=false;
  let initialized=false;
  const MP3_SRC='ebook_nachteile_audio.mp3';

  function isTarget(level){try{return window.selected==='t23' && level==='long'}catch(e){return false}}
  function cleanText(s){return String(s||'').replace(/\s+/g,' ').replace(/\bKurz\b|\bMittel\b|\bLang\b/g,'').trim()}
  function collectChunks(){
    const content=document.getElementById('lessonContent'); if(!content)return [];
    const clone=content.cloneNode(true);
    ['#ebookAudioPanel','#ebookFloatingAudioControls'].forEach(sel=>{const x=clone.querySelector(sel); if(x)x.remove()});
    const nodes=[...clone.querySelectorAll('h3,h4,p,li,td')];
    let out=[];
    nodes.map(n=>cleanText(n.textContent)).filter(t=>t.length>25).forEach(t=>{
      if(t.length>650)t.split(/(?<=[.!?])\s+/).forEach(x=>{x=cleanText(x);if(x.length>25)out.push(x)}); else out.push(t);
    });
    return out;
  }
  function initRealAudio(){
    if(realAudioChecked)return realAudio;
    realAudioChecked=true;
    realAudio=new Audio(MP3_SRC+'?v=2');
    realAudio.preload='metadata';
    realAudio.oncanplay=function(){realAudioReady=true; setStatus('Gerçek MP3 hazır')};
    realAudio.onerror=function(){realAudioReady=false; setStatus('MP3 bulunamadı; Almanca tarayıcı sesi kullanılacak.')};
    realAudio.onended=function(){speaking=false; setStatus('Bitti'); showFloating(false)};
    realAudio.ontimeupdate=function(){setMp3Time()};
    return realAudio;
  }
  function getGermanVoice(){
    const voices=(window.speechSynthesis&&speechSynthesis.getVoices())||[];
    const score=v=>{
      const n=(v.name+' '+v.lang).toLowerCase(); let s=0;
      if(/^de-de/i.test(v.lang))s+=100; else if(/^de/i.test(v.lang))s+=70;
      if(/natural|neural|online|premium|enhanced|wavenet/i.test(v.name))s+=60;
      if(/microsoft/i.test(v.name))s+=40; if(/google/i.test(v.name))s+=35;
      if(/katja|conrad|anna|amala|seraphina|florian|helena|heda|markus|stefan/i.test(n))s+=30;
      if(v.localService===false)s+=10; return s;
    };
    return voices.filter(v=>/^de/i.test(v.lang)).sort((a,b)=>score(b)-score(a))[0]||null;
  }
  function setStatus(txt){
    const s=document.getElementById('ebookAudioStatus'); if(s)s.textContent=txt;
    const fs=document.getElementById('ebookFloatStatus'); if(fs)fs.textContent=txt;
  }
  function setCounter(){
    const text=chunks.length?(index+1)+' / '+chunks.length:'0 / 0';
    const c=document.getElementById('ebookAudioCounter'); if(c)c.textContent=text;
    const fc=document.getElementById('ebookFloatCounter'); if(fc)fc.textContent=text;
  }
  function setMp3Time(){
    if(!realAudio)return;
    const t=Math.floor(realAudio.currentTime||0), d=Math.floor(realAudio.duration||0);
    const fmt=x=>isFinite(x)?String(Math.floor(x/60)).padStart(2,'0')+':'+String(x%60).padStart(2,'0'):'--:--';
    const text=fmt(t)+' / '+fmt(d);
    const c=document.getElementById('ebookAudioCounter'); if(c)c.textContent=text;
    const fc=document.getElementById('ebookFloatCounter'); if(fc)fc.textContent=text;
  }
  function ensureFloatingControls(){
    if(document.getElementById('ebookFloatingAudioControls'))return;
    const div=document.createElement('div'); div.id='ebookFloatingAudioControls';
    div.style.cssText='position:fixed;right:16px;bottom:16px;z-index:9999;background:#183642;color:#fff;border:2px solid #c4a484;border-radius:16px;padding:10px 12px;box-shadow:0 8px 24px #0006;font-family:Arial,sans-serif;display:none;max-width:260px';
    div.innerHTML='<div style="font-weight:700;margin-bottom:6px">🔊 E-Books Audio</div><div style="display:flex;gap:6px;flex-wrap:wrap"><button id="ebookFloatBack5" style="background:#fff;color:#183642;border:0;border-radius:10px;padding:8px 10px;font-weight:700">↶ 5 sn</button><button id="ebookFloatStop" style="background:#b91c1c;color:#fff;border:0;border-radius:10px;padding:8px 10px;font-weight:700">■ Durdur</button></div><div id="ebookFloatCounter" style="font-size:12px;margin-top:6px;opacity:.9">0 / 0</div><div id="ebookFloatStatus" style="font-size:11px;margin-top:3px;opacity:.85">Hazır</div>';
    document.body.appendChild(div);
    document.getElementById('ebookFloatStop').onclick=stop;
    document.getElementById('ebookFloatBack5').onclick=backFiveSeconds;
  }
  function showFloating(show){ensureFloatingControls(); const el=document.getElementById('ebookFloatingAudioControls'); if(el)el.style.display=show?'block':'none'}
  function stop(){
    if('speechSynthesis' in window)speechSynthesis.cancel();
    if(realAudio){realAudio.pause(); realAudio.currentTime=0}
    speaking=false; paused=false; currentChar=0; resumeOffset=0;
    setStatus('Gestoppt'); setCounter(); showFloating(false);
  }
  function playRealAudio(){
    initRealAudio();
    if(!realAudioReady && realAudio.readyState<2){setStatus('MP3 kontrol ediliyor; yoksa tarayıcı sesi kullanılacak.'); setTimeout(()=>{if(realAudioReady)playRealAudio(); else playTTS()},450); return}
    if(!realAudioReady){playTTS(); return}
    if('speechSynthesis' in window)speechSynthesis.cancel();
    speaking=true; paused=false; showFloating(true); setStatus('Gerçek MP3 okunuyor');
    realAudio.playbackRate=Number(document.getElementById('ebookAudioRate')?.value||1);
    realAudio.play().catch(()=>{setStatus('MP3 oynatılamadı; Almanca tarayıcı sesi kullanılacak.'); playTTS()});
  }
  function speakCurrent(fromChar){
    if(!('speechSynthesis' in window)){setStatus('Bu tarayıcı sesli okuma desteklemiyor.');return}
    chunks=chunks.length?chunks:collectChunks(); if(!chunks.length){setStatus('Okunacak metin bulunamadı.');return}
    speechSynthesis.cancel(); resumeOffset=Math.max(0,Number(fromChar||0));
    const text=(chunks[index]||'').slice(resumeOffset).trim();
    if(!text){if(index<chunks.length-1){index++; return speakCurrent(0)} speaking=false; setStatus('Bitti'); showFloating(false); return}
    const u=new SpeechSynthesisUtterance(text); u.lang='de-DE'; u.rate=Number(document.getElementById('ebookAudioRate')?.value||0.86); u.pitch=0.92; u.volume=1;
    const v=getGermanVoice(); if(v)u.voice=v;
    speaking=true; paused=false; showFloating(true); setStatus('Almanca tarayıcı sesi okunuyor'); setCounter();
    u.onboundary=e=>{if(typeof e.charIndex==='number')currentChar=resumeOffset+e.charIndex};
    u.onend=function(){if(!speaking)return; currentChar=0; resumeOffset=0; if(index<chunks.length-1){index++; speakCurrent(0)}else{speaking=false; setStatus('Bitti'); setCounter(); showFloating(false)}};
    u.onerror=function(){speaking=false; setStatus('Sesli okuma durdu veya tarayıcı sesi engelledi.'); showFloating(false)};
    speechSynthesis.speak(u);
  }
  function playTTS(){chunks=collectChunks(); if(!chunks.length)return setStatus('Okunacak metin bulunamadı.'); if(index>=chunks.length)index=0; speakCurrent(0)}
  function play(){playRealAudio()}
  function pause(){if(realAudio&&!realAudio.paused){realAudio.pause(); paused=true; setStatus('Duraklatıldı');return} if(window.speechSynthesis&&speechSynthesis.speaking&&!speechSynthesis.paused){speechSynthesis.pause(); paused=true; setStatus('Duraklatıldı')}}
  function resume(){if(realAudio&&paused&&realAudioReady){realAudio.play(); paused=false; setStatus('Devam ediyor');return} if(window.speechSynthesis&&speechSynthesis.paused){speechSynthesis.resume(); paused=false; setStatus('Devam ediyor')}}
  function prev(){if(realAudioReady&&realAudio){realAudio.currentTime=0; setMp3Time(); return} chunks=collectChunks(); index=Math.max(0,index-1); currentChar=0; speakCurrent(0)}
  function next(){if(realAudioReady&&realAudio){realAudio.currentTime=Math.min(realAudio.duration||0,(realAudio.currentTime||0)+30); setMp3Time(); return} chunks=collectChunks(); index=Math.min((chunks.length||1)-1,index+1); currentChar=0; speakCurrent(0)}
  function backFiveSeconds(){
    if(realAudioReady&&realAudio){realAudio.currentTime=Math.max(0,(realAudio.currentTime||0)-5); setMp3Time(); return}
    chunks=chunks.length?chunks:collectChunks(); if(!chunks.length)return; const charsBack=95;
    if(currentChar>charsBack)speakCurrent(currentChar-charsBack); else if(index>0){index--; const prevText=chunks[index]||''; speakCurrent(Math.max(0,prevText.length-charsBack))} else speakCurrent(0);
  }
  function inject(){
    const lesson=document.getElementById('lesson');
    const content=document.getElementById('lessonContent');
    if(!lesson||lesson.classList.contains('hide')||!content)return;
    if(window.selected!=='t23')return;
    const title=(document.getElementById('lessonTitle')||{}).textContent||'';
    const text=(content.textContent||'').slice(0,300);
    if(!/E-Books|Nachteile/i.test(title+text))return;
    ensureFloatingControls(); initRealAudio();
    if(document.getElementById('ebookAudioPanel')){chunks=collectChunks(); setCounter(); return}
    chunks=collectChunks(); index=0;
    const div=document.createElement('div'); div.id='ebookAudioPanel'; div.style.cssText='border:2px solid #8a5a44;border-radius:14px;padding:14px;margin:0 0 18px;background:#fff8ed;font-family:Arial,sans-serif';
    div.innerHTML='<h3 style="margin:0 0 8px;color:#183642">🔊 Almanca sesli konu anlatımı</h3><p style="margin:0 0 10px;color:#4b5563">Öncelik gerçek MP3 dosyasındadır: <b>ebook_nachteile_audio.mp3</b>. Dosya yoksa en doğal Almanca tarayıcı sesi kullanılır.</p><div style="display:flex;gap:8px;flex-wrap:wrap;align-items:center"><button id="ebookAudioPlay">▶ Başlat</button><button id="ebookAudioPause" class="sec">⏸ Duraklat</button><button id="ebookAudioResume" class="ghost">▶ Devam</button><button id="ebookAudioStop" class="danger">■ Durdur</button><button id="ebookAudioBack5" class="ghost">↶ 5 sn geri</button><button id="ebookAudioPrev" class="ghost">← Başa</button><button id="ebookAudioNext" class="ghost">+30 sn</button><label>Hız <input id="ebookAudioRate" type="range" min="0.65" max="1.15" step="0.05" value="1" style="width:120px"></label><b id="ebookAudioCounter">0 / 0</b></div><p id="ebookAudioStatus" style="margin:10px 0 0;color:#374151">Hazır</p>';
    content.insertBefore(div,content.firstChild);
    document.getElementById('ebookAudioPlay').onclick=play; document.getElementById('ebookAudioPause').onclick=pause; document.getElementById('ebookAudioResume').onclick=resume; document.getElementById('ebookAudioStop').onclick=stop; document.getElementById('ebookAudioBack5').onclick=backFiveSeconds; document.getElementById('ebookAudioPrev').onclick=prev; document.getElementById('ebookAudioNext').onclick=next;
    document.getElementById('ebookAudioRate').oninput=function(){if(realAudioReady&&realAudio)realAudio.playbackRate=Number(this.value); else if(speaking&&!paused)speakCurrent(currentChar)};
    setCounter();
  }
  function patchStartLesson(){
    if(window.__ebookAudioPatched)return true;
    if(typeof window.startLesson!=='function')return false;
    const old=window.startLesson;
    window.startLesson=function(level){stop(); const r=old.apply(this,arguments); setTimeout(inject,120); setTimeout(inject,500); return r};
    window.__ebookAudioPatched=true;
    return true;
  }
  function init(){
    if(initialized)return; initialized=true;
    window.ebookAudioPlay=play; window.ebookAudioPause=pause; window.ebookAudioResume=resume; window.ebookAudioStop=stop; window.ebookAudioPrev=prev; window.ebookAudioNext=next; window.ebookAudioBack5=backFiveSeconds;
    if('speechSynthesis' in window){speechSynthesis.getVoices(); speechSynthesis.onvoiceschanged=function(){speechSynthesis.getVoices()}}
    patchStartLesson();
    let tries=0;
    const timer=setInterval(function(){tries++; patchStartLesson(); inject(); if(tries>30)clearInterval(timer)},300);
    document.addEventListener('click',function(){setTimeout(inject,150); setTimeout(inject,650)});
    window.addEventListener('beforeunload',stop);
  }
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',init); else init();
})();
