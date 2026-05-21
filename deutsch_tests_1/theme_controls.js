(function(){
  const KEY_MODE='dt_theme_mode';
  const KEY_BRIGHT='dt_theme_brightness';
  function css(){
    const style=document.createElement('style');
    style.id='themeControlsStyle';
    style.textContent=`
      :root{--dt-filter-brightness:1;--dt-bg:#f6f4ef;--dt-card:#ffffff;--dt-text:#1f2937;--dt-muted:#6b7280;--dt-border:#ddd6ca;--dt-header:#183642;--dt-accent:#8a5a44;}
      html.dt-dim{--dt-bg:#ece7dc;--dt-card:#f7f2e8;--dt-text:#17212b;--dt-muted:#515b68;--dt-border:#c8bda9;--dt-header:#142d36;--dt-accent:#7c513e;}
      html.dt-night{--dt-bg:#111827;--dt-card:#1f2937;--dt-text:#e5e7eb;--dt-muted:#cbd5e1;--dt-border:#334155;--dt-header:#0f172a;--dt-accent:#a8795f;}
      html.dt-night body,html.dt-dim body{background:var(--dt-bg)!important;color:var(--dt-text)!important;filter:brightness(var(--dt-filter-brightness));}
      html.dt-night .card,html.dt-dim .card{background:var(--dt-card)!important;border-color:var(--dt-border)!important;color:var(--dt-text)!important;box-shadow:none!important;}
      html.dt-night header,html.dt-dim header{background:var(--dt-header)!important;border-bottom-color:var(--dt-accent)!important;}
      html.dt-night .muted,html.dt-dim .muted{color:var(--dt-muted)!important;}
      html.dt-night .opt,html.dt-dim .opt{background:rgba(255,255,255,.035)!important;border-color:var(--dt-border)!important;color:var(--dt-text)!important;}
      html.dt-night .ghost,html.dt-dim .ghost{background:transparent!important;color:var(--dt-text)!important;border-color:var(--dt-border)!important;}
      html.dt-night input,html.dt-dim input{background:var(--dt-card)!important;color:var(--dt-text)!important;border-color:var(--dt-border)!important;}
      html.dt-night .mask,html.dt-dim .mask{background:rgba(255,255,255,.04)!important;color:var(--dt-text)!important;border-color:var(--dt-border)!important;}
      .theme-panel{position:sticky;top:0;z-index:1000;background:rgba(255,255,255,.92);backdrop-filter:blur(10px);border-bottom:1px solid #ddd6ca;padding:8px 12px;font-family:Arial,sans-serif;}
      html.dt-night .theme-panel{background:rgba(15,23,42,.94);border-color:#334155;color:#e5e7eb;}
      html.dt-dim .theme-panel{background:rgba(245,239,226,.94);border-color:#c8bda9;color:#17212b;}
      .theme-panel-inner{max-width:1080px;margin:auto;display:flex;gap:8px;align-items:center;flex-wrap:wrap;}
      .theme-panel strong{margin-right:4px;}
      .theme-panel button{padding:7px 10px;border-radius:999px;border:1px solid #c9c1b4;background:#fff;color:#183642;font-weight:700;cursor:pointer;}
      html.dt-night .theme-panel button{background:#1f2937;color:#e5e7eb;border-color:#475569;}
      .theme-panel button.active{background:#183642;color:#fff;border-color:#183642;}
      html.dt-night .theme-panel button.active{background:#a8795f;color:#111827;border-color:#a8795f;}
      .theme-panel input[type=range]{width:170px;accent-color:#8a5a44;}
      .theme-panel .theme-note{font-size:12px;opacity:.8;}
      @media(max-width:700px){.theme-panel-inner{gap:6px}.theme-panel input[type=range]{width:130px}.theme-panel button{padding:6px 8px}}
    `;
    document.head.appendChild(style);
  }
  function apply(mode,brightness){
    document.documentElement.classList.remove('dt-dim','dt-night');
    if(mode==='dim')document.documentElement.classList.add('dt-dim');
    if(mode==='night')document.documentElement.classList.add('dt-night');
    document.documentElement.style.setProperty('--dt-filter-brightness',String(brightness||1));
    localStorage.setItem(KEY_MODE,mode||'normal');
    localStorage.setItem(KEY_BRIGHT,String(brightness||1));
    document.querySelectorAll('[data-theme-mode]').forEach(b=>b.classList.toggle('active',b.dataset.themeMode===(mode||'normal')));
    const r=document.getElementById('themeBrightnessRange');
    const label=document.getElementById('themeBrightnessLabel');
    if(r)r.value=Math.round((brightness||1)*100);
    if(label)label.textContent=Math.round((brightness||1)*100)+'%';
  }
  function panel(){
    if(document.getElementById('themePanel'))return;
    const div=document.createElement('div');
    div.id='themePanel';
    div.className='theme-panel';
    div.innerHTML=`<div class="theme-panel-inner"><strong>Göz ayarı:</strong><button data-theme-mode="normal">Normal</button><button data-theme-mode="dim">Loş</button><button data-theme-mode="night">Gece</button><span>Parlaklık</span><input id="themeBrightnessRange" type="range" min="55" max="110" value="100"><span id="themeBrightnessLabel">100%</span><span class="theme-note">Gece çalışırken göz yormasın diye ayarlanır.</span></div>`;
    document.body.insertBefore(div,document.body.firstChild);
    div.querySelectorAll('[data-theme-mode]').forEach(btn=>btn.onclick=function(){apply(this.dataset.themeMode,Number(document.getElementById('themeBrightnessRange').value)/100)});
    document.getElementById('themeBrightnessRange').oninput=function(){apply(localStorage.getItem(KEY_MODE)||'normal',Number(this.value)/100)};
  }
  document.addEventListener('DOMContentLoaded',function(){
    css();
    panel();
    const mode=localStorage.getItem(KEY_MODE)||'normal';
    const brightness=Number(localStorage.getItem(KEY_BRIGHT)||'1');
    apply(mode,brightness);
  });
})();
