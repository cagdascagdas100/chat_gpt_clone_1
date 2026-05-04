function textKind(s){
  s=String(s||"").trim();
  const wc=s.split(/\s+/).filter(Boolean).length;
  const low=s.toLocaleLowerCase("de-DE");
  if(PREPS&&PREPS.includes(low))return"prep";
  if(/[.!?]$/.test(s)||wc>=7)return"sentence";
  if(/^(der|die|das|ein|eine|einen|einem|einer|des|den|dem)\b/i.test(s))return"noun";
  if(/\b(zu|zur|zum|auf|an|in|mit|von|für|gegen|bei|über|unter|nach|vor|aus)\b/.test(low)&&wc<=6)return"phrase";
  if(/(en|ern|eln)$/i.test(low)&&wc<=3)return"verb";
  return wc<=3?"short":"phrase";
}
function wc(s){return String(s||"").trim().split(/\s+/).filter(Boolean).length}
function badDistractor(s){
  s=String(s||"").toLocaleLowerCase("de-DE");
  return /\b(essen|trinken|tun|irgendwie|halt|sache|sachen|gut machen|macht gut|bekommen machen|manen)\b/.test(s);
}
function closeScore(a,b){
  const ka=textKind(a),kb=textKind(b);
  let score=0;
  if(ka===kb)score-=30;
  score+=Math.abs(String(a).length-String(b).length);
  score+=Math.abs(wc(a)-wc(b))*8;
  if(badDistractor(b))score+=80;
  return score;
}
function uniq(arr){
  const out=[],seen=new Set();
  (arr||[]).forEach(x=>{if(!x)return;let k=norm(x);if(k&&!seen.has(k)){seen.add(k);out.push(x)}});
  return out;
}
function smartOptions(ans,candidates,n){
  ans=String(ans||"");
  let cand=uniq(candidates||[]).filter(x=>norm(x)!==norm(ans)&&!badDistractor(x));
  const kind=textKind(ans);
  let preferred=cand.filter(x=>textKind(x)===kind);
  if(preferred.length<n-1)preferred=preferred.concat(cand.filter(x=>textKind(x)!==kind));
  preferred=uniq(preferred).sort((a,b)=>closeScore(ans,a)-closeScore(ans,b));
  let picked=preferred.slice(0,n-1);
  if(picked.length<n-1){
    let fallback=uniq(cand).filter(x=>!picked.some(y=>norm(y)===norm(x))).sort((a,b)=>closeScore(ans,a)-closeScore(ans,b));
    picked=picked.concat(fallback.slice(0,n-1-picked.length));
  }
  return sh([ans].concat(picked)).slice(0,n);
}
function completedPrep(x){return x&&x[0]?String(x[0]).replace("___",x[1]||""):""}
function fullPhrase(x){return x&&x[0]&&x[1]?String(x[0]+" "+x[1]).replace(/\s+/g," ").trim():""}
function collectCandidates(t){
  let c=[];
  (t.words||[]).forEach(x=>c.push(x));
  (t.hang||[]).forEach(x=>c.push(x));
  (t.fill||[]).forEach(x=>{c.push(x[1]);c.push(fillSentence(x))});
  (t.mc||[]).forEach(x=>{if(x&&x[1])c.push(x[1][x[2]])});
  (t.tf||[]).forEach(x=>{if(x&&x[1]===true)c.push(x[0])});
  (t.wordMatch||[]).forEach(x=>{c.push(x[0]);c.push(x[1])});
  (t.phraseMatch||[]).forEach(x=>{c.push(x[0]);c.push(x[1]);c.push(fullPhrase(x))});
  (t.prep||[]).forEach(x=>{c.push(x[1]);c.push(completedPrep(x))});
  return uniq(c);
}
function fillSentence(x){return x&&x[0]?String(x[0]).replace("____",x[1]||""):""}
function smartMCOptions(t,correct,original){
  const candidates=collectCandidates(t).concat((original||[]).filter(x=>!badDistractor(x)));
  return smartOptions(correct,candidates,5);
}
function opts(ans,p,n){return smartOptions(ans,p,n)}
function bank(t){
  let g={tf:[],fill:[],mc:[],wordMatch:[],phraseMatch:[],prep:[]},all=collectCandidates(t);
  (t.tf||[]).forEach(x=>g.tf.push({g:"tf",typ:"tf",sec:TIT.tf,q:x[0],a:x[1]?"Richtig":"Falsch",tag:x[2]}));
  (t.fill||[]).forEach(x=>{
    let answer=x[1];
    let sameType=(t.fill||[]).map(y=>y[1]).concat(all.filter(y=>textKind(y)===textKind(answer)));
    g.fill.push({g:"fill",typ:"r",sec:TIT.fill,q:x[0],a:answer,op:smartOptions(answer,sameType,6),tag:x[2]});
  });
  (t.mc||[]).forEach(x=>{
    let answer=x[1][x[2]];
    g.mc.push({g:"mc",typ:"r",sec:TIT.mc,q:x[0],a:answer,op:smartMCOptions(t,answer,x[1]),tag:x[3]});
  });
  let wm=t.wordMatch||[];
  wm.forEach((x,i)=>{
    let defs=wm.filter((_,j)=>j!==i).map(y=>y[1]);
    g.wordMatch.push({g:"wordMatch",typ:"r",sec:TIT.wordMatch,q:"Welche deutsche Bedeutung passt zu: „"+x[0]+"“?",a:x[1],op:smartOptions(x[1],defs,5),tag:"Bedeutung"});
  });
  let pm=t.phraseMatch||[];
  pm.forEach((x,i)=>{
    let comps=pm.filter((_,j)=>j!==i).map(y=>y[1]);
    g.phraseMatch.push({g:"phraseMatch",typ:"r",sec:TIT.phraseMatch,q:"Welche Ergänzung bildet eine korrekte Kollokation? „"+x[0]+" …“",a:x[1],op:smartOptions(x[1],comps,5),tag:"Kollokation"});
  });
  (t.prep||[]).forEach(x=>{
    let preps=(t.prep||[]).map(y=>y[1]).concat(PREPS);
    g.prep.push({g:"prep",typ:"r",sec:TIT.prep,q:x[0],a:x[1],op:smartOptions(x[1],preps,6),tag:x[2]||"Präposition"});
  });
  Object.keys(g).forEach(k=>g[k]=sh(g[k]));
  return g;
}
