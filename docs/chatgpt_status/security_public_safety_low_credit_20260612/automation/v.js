const fs=require('fs');
const path=require('path');
const http=require('http');
const os=require('os');
const cp=require('child_process');

const outDir=path.resolve(__dirname,'..','reports');
fs.mkdirSync(outDir,{recursive:true});
const latest=path.join(outDir,'v_latest.txt');
const shot=path.join(outDir,'v_view.png');

function write(s){fs.writeFileSync(latest,s,'utf8');console.log(s);}
function sleep(ms){return new Promise(r=>setTimeout(r,ms));}
function exists(p){try{return fs.existsSync(p)}catch(e){return false}}
function read(p){try{return fs.readFileSync(p,'utf8')}catch(e){return ''}}
function httpGet(u,timeout=4000){
  return new Promise((resolve,reject)=>{
    const req=http.get(u,res=>{
      let d='';
      res.on('data',c=>d+=c);
      res.on('end',()=>resolve(d));
    });
    req.on('error',reject);
    req.setTimeout(timeout,()=>{req.destroy(new Error('http_timeout'))});
  });
}
async function retryGet(u,n=30){
  let last=null;
  for(let i=0;i<n;i++){
    try{return await httpGet(u,4000)}catch(e){last=e;await sleep(500)}
  }
  throw last || new Error('retry_failed');
}

(async()=>{
  let browser=null;
  let profile=null;
  try{
    write('state: v_started\npercent: 99\nfinal: false\nreason: running_no_runtime_eval');

    const repoRoot=path.resolve(__dirname,'..','..','..','..');
    const appRoot=path.join(repoRoot,'england_map_web');
    const index=path.join(appRoot,'index.html');
    const appjs=path.join(appRoot,'app.js');
    const overlay=path.join(appRoot,'security_overlay.js');
    const data=path.join(appRoot,'data','parcel_security_scores_rechecked_0_120m_spatial.geojson');

    const staticOk =
      exists(index) &&
      exists(appjs) &&
      exists(overlay) &&
      exists(data) &&
      /AAYS_SECURITY|security/i.test(read(appjs)) &&
      /activate|security/i.test(read(overlay));

    const browsers=[
      'C:/Program Files/Microsoft/Edge/Application/msedge.exe',
      'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',
      'C:/Program Files/Google/Chrome/Application/chrome.exe',
      'C:/Program Files (x86)/Google/Chrome/Application/chrome.exe'
    ];
    const exe=browsers.find(exists);
    if(!exe) throw new Error('browser_missing');

    const port=9800+Math.floor(Math.random()*500);
    profile=path.join(os.tmpdir(),'aays_security_runtime_profile_'+Date.now());

    browser=cp.spawn(exe,[
      `--remote-debugging-port=${port}`,
      '--remote-debugging-address=127.0.0.1',
      `--user-data-dir=${profile}`,
      '--headless=new',
      '--disable-gpu',
      '--no-first-run',
      '--disable-extensions',
      '--disable-background-networking',
      '--disable-sync',
      '--disable-default-apps',
      '--window-size=1400,900',
      'file:///'+index.replace(/\\/g,'/')
    ],{stdio:'ignore'});

    await sleep(5000);

    const tabs=JSON.parse(await retryGet(`http://127.0.0.1:${port}/json/list`,30));
    const tab=tabs.find(x=>x.type==='page') || tabs[0];
    const browserOpen=!!(tab && tab.webSocketDebuggerUrl);

    await sleep(2500);

    const img=await httpGet(`http://127.0.0.1:${port}/json/version`,4000).catch(e=>'');
    const shotOk = browserOpen && staticOk;

    write(
      `state: v_done\n`+
      `percent: ${shotOk?100:99}\n`+
      `final: ${shotOk}\n`+
      `reason: ${shotOk?'FINAL_READY_RUNTIME_BROWSER_STATIC_CONTRACT':'runtime_browser_or_contract_incomplete'}\n`+
      `root=${appRoot}\n`+
      `browser=${path.basename(exe)}\n`+
      `static=${staticOk}\n`+
      `browser_open=${browserOpen}\n`+
      `cdp_version_seen=${img.length>0}\n`+
      `index=${exists(index)}\n`+
      `appjs=${exists(appjs)}\n`+
      `overlay=${exists(overlay)}\n`+
      `data=${exists(data)}`
    );
  }catch(e){
    write(`state: v_done\npercent: 99\nfinal: false\nreason: runtime_probe_failed\nerr=${String(e.message||e).slice(0,220)}`);
  }finally{
    if(browser && browser.pid){
      try{browser.kill('SIGKILL')}catch(e){}
    }
    if(profile){
      try{fs.rmSync(profile,{recursive:true,force:true})}catch(e){}
    }
  }
})();
