(function(){
  let audio=null;
  let audioReady=false;
  let audioChecked=false;
  let initialized=false;
  const MP3_SRC='ebook_nachteile_audio.mp3';

  function isTargetLesson(){
    const lesson=document.getElementById('lesson');
    const content=document.getElementById('lessonContent');
    if(!lesson||lesson.classList.contains('hide')||!content)return false;
    if(window.selected!=='t23')return false;
    const title=(document.getElementById('lessonTitle')||{}).textContent||'';
    const text=(content.textContent||'').slice(0,600);
    return /E-Books/i.test(title+text)&&/Nachteile/i.test(title+text);
  }

  function fmt(x){
    if(!isFinite(x))return '--:--';
    x=Math.max(0,Math.floor(x));
    return String(Math.floor(x/60)).padStart(2,'0')+':'+String(x%60).padStart(2,'0');
  }

  function setStatus(txt){
    const s=document.getElementById('ebookAudioStatus'); if(s)s.textContent=txt;
    const fs=document.getElementById('ebookFloatStatus'); if(fs)fs.textContent=txt;
  }

  function setTime(){
    const t=audio?fmt(audio.currentTime):'00:00';
    const d=audio?fmt(audio.duration):'--:--';
    const label=t+' / '+d;
    const c=document.getElementById('ebookAudioCounter'); if(c)c.textContent=label;
    const fc=document.getElementById('ebookFloatCounter'); if(fc)fc.textContent=label;
  }

  function ensureAudio(){
    if(audioChecked)return audio;
    audioChecked=true;
    audio=new Audio(MP3_SRC+'?v=chatgpt-audio-1');
    audio.preload='metadata';
    audio.oncanplay=function(){audioReady=true; setStatus('MP3 hazır'); setTime();};
    audio.onerror=function(){audioReady=false; setStatus('MP3 dosyası bulunamadı. Tarayıcı sesi kapalıdır; sadece MP3 çalınır.');};
    audio.onended=function(){setStatus('Bitti'); showFloating(false); setTime();};
    audio.ontimeupdate=setTime;
    return audio;
  }

  function ensureFloating(){
    let el=document.getElementById('ebookFloatingAudioControls');
    if(el)return el;
    el=document.createElement('div');
    el.id='ebookFloatingAudioControls';
    el.style.cssText='position:fixed;right:16px;bottom:16px;z-index:99999;background:#183642;color:#fff;border:2px solid #c4a484;border-radius:16px;padding:10px 12px;box-shadow:0 8px 24px rgba(0,0,0,.45);font-family:Arial,sans-serif;display:none;max-width:255px';
    el.innerHTML='<div style="font-weight:700;margin-bottom:6px">🔊 MP3 Audio</div><div style="display:flex;gap:6px;flex-wrap:wrap"><button id="ebookFloatBack5" style="background:#fff;color:#183642;border:0;border-radius:10px;padding:8px 10px;font-weight:700">↶ 5 sn</button><button id="ebookFloatStop" style="background:#b91c1c;color:#fff;border:0;border-radius:10px;padding:8px 10px;font-weight:700">■ Durdur</button></div><div id="ebookFloatCounter" style="font-size:12px;margin-top:6px;opacity:.9">00:00 / --:--</div><div id="ebookFloatStatus" style="font-size:11px;margin-top:3px;opacity:.85">Hazır</div>';
    document.body.appendChild(el);
    document.getElementById('ebookFloatBack5').onclick=backFive;
    document.getElementById('ebookFloatStop').onclick=stop;
    return el;
  }

  function showFloating(force){
    const el=ensureFloating();
    const should=force || (isTargetLesson() && window.scrollY>450 && audio && !audio.paused);
    el.style.display=should?'block':'none';
  }

  function play(){
    ensureAudio();
    if(!audioReady && audio.readyState<2){
      setStatus('MP3 kontrol ediliyor...');
      setTimeout(function(){
        if(audioReady)play();
        else setStatus('MP3 bulunamadı. Lütfen deutsch_tests_1/ebook_nachteile_audio.mp3 dosyasını üretip yükle.');
      },500);
      return;
    }
    if(!audioReady){
      setStatus('MP3 yok. Site içi tarayıcı seslendirmesi kaldırıldı.');
      return;
    }
    audio.playbackRate=Number(document.getElementById('ebookAudioRate')?.value||1);
    audio.play().then(function(){setStatus('MP3 çalıyor'); showFloating(true); setTime();}).catch(function(){setStatus('Tarayıcı MP3 çalmayı engelledi; Başlat düğmesine tekrar bas.');});
  }

  function pause(){
    ensureAudio();
    if(audio){audio.pause(); setStatus('Duraklatıldı'); setTime(); showFloating(false);}
  }

  function resume(){
    ensureAudio();
    if(audioReady&&audio){audio.play(); setStatus('Devam ediyor'); showFloating(true); setTime();}
    else setStatus('MP3 yok.');
  }

  function stop(){
    ensureAudio();
    if(audio){audio.pause(); audio.currentTime=0;}
    setStatus('Durduruldu'); setTime(); showFloating(false);
  }

  function backFive(){
    ensureAudio();
    if(audioReady&&audio){audio.currentTime=Math.max(0,(audio.currentTime||0)-5); setStatus('5 saniye geri alındı'); setTime(); showFloating(!audio.paused);}
    else setStatus('MP3 yok.');
  }

  function forwardThirty(){
    ensureAudio();
    if(audioReady&&audio){audio.currentTime=Math.min(audio.duration||0,(audio.currentTime||0)+30); setStatus('30 saniye ileri alındı'); setTime();}
    else setStatus('MP3 yok.');
  }

  function restart(){
    ensureAudio();
    if(audioReady&&audio){audio.currentTime=0; setTime(); setStatus('Başa alındı');}
    else setStatus('MP3 yok.');
  }

  function inject(){
    const content=document.getElementById('lessonContent');
    if(!isTargetLesson()||!content)return;
    ensureAudio(); ensureFloating();
    if(document.getElementById('ebookAudioPanel')){setTime(); return;}
    const div=document.createElement('div');
    div.id='ebookAudioPanel';
    div.style.cssText='border:2px solid #8a5a44;border-radius:14px;padding:14px;margin:0 0 18px;background:#fff8ed;font-family:Arial,sans-serif';
    div.innerHTML='<h3 style="margin:0 0 8px;color:#183642">🔊 ChatGPT/OpenAI Almanca MP3 seslendirme</h3><p style="margin:0 0 10px;color:#4b5563">Bu bölüm yalnızca gerçek MP3 dosyasını çalar: <b>ebook_nachteile_audio.mp3</b>. Site içi tarayıcı seslendirmesi kaldırıldı; MP3 yoksa ses çalmaz.</p><div style="display:flex;gap:8px;flex-wrap:wrap;align-items:center"><button id="ebookAudioPlay">▶ Başlat</button><button id="ebookAudioPause" class="sec">⏸ Duraklat</button><button id="ebookAudioResume" class="ghost">▶ Devam</button><button id="ebookAudioStop" class="danger">■ Durdur</button><button id="ebookAudioBack5" class="ghost">↶ 5 sn geri</button><button id="ebookAudioRestart" class="ghost">← Başa</button><button id="ebookAudioForward" class="ghost">+30 sn</button><label>Hız <input id="ebookAudioRate" type="range" min="0.75" max="1.15" step="0.05" value="1" style="width:120px"></label><b id="ebookAudioCounter">00:00 / --:--</b></div><p id="ebookAudioStatus" style="margin:10px 0 0;color:#374151">Hazır</p>';
    content.insertBefore(div,content.firstChild);
    document.getElementById('ebookAudioPlay').onclick=play;
    document.getElementById('ebookAudioPause').onclick=pause;
    document.getElementById('ebookAudioResume').onclick=resume;
    document.getElementById('ebookAudioStop').onclick=stop;
    document.getElementById('ebookAudioBack5').onclick=backFive;
    document.getElementById('ebookAudioRestart').onclick=restart;
    document.getElementById('ebookAudioForward').onclick=forwardThirty;
    document.getElementById('ebookAudioRate').oninput=function(){if(audio)audio.playbackRate=Number(this.value)};
    setTime();
  }

  function patchStartLesson(){
    if(window.__ebookAudioMp3OnlyPatched)return true;
    if(typeof window.startLesson!=='function')return false;
    const old=window.startLesson;
    window.startLesson=function(){
      stop();
      const r=old.apply(this,arguments);
      setTimeout(inject,120);
      setTimeout(inject,600);
      return r;
    };
    window.__ebookAudioMp3OnlyPatched=true;
    return true;
  }

  function updateFloating(){showFloating(false);}

  function init(){
    if(initialized)return; initialized=true;
    window.ebookAudioPlay=play;
    window.ebookAudioPause=pause;
    window.ebookAudioResume=resume;
    window.ebookAudioStop=stop;
    window.ebookAudioBack5=backFive;
    window.ebookAudioPrev=restart;
    window.ebookAudioNext=forwardThirty;
    patchStartLesson();
    let tries=0;
    const timer=setInterval(function(){tries++; patchStartLesson(); inject(); updateFloating(); if(tries>30)clearInterval(timer)},300);
    document.addEventListener('click',function(){setTimeout(inject,150);setTimeout(updateFloating,300);});
    document.addEventListener('scroll',updateFloating,{passive:true});
    window.addEventListener('beforeunload',stop);
  }
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',init); else init();
})();
