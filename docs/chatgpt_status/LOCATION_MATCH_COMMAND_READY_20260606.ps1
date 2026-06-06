$ErrorActionPreference='Continue'
$MainRepo='C:\Users\cagda\Documents\GitHub\AAYS'
$Branch='feature/terrayield-aays-integration'
$Zip="$MainRepo\docs\chatgpt_status\sales_parcel_access_exports\sales_parcel_access_snapshot_20260606-041144.zip"
$Work='F:\chatgpt\AAYS_LOCATION_MATCH_WORK'
$Stamp=Get-Date -Format yyyyMMdd-HHmmss
$Extract="$Work\extract"
$Reports="$Work\reports_$Stamp"
New-Item -ItemType Directory -Force $Work,$Extract,$Reports | Out-Null
if(!(Test-Path $Zip)){ throw "Snapshot ZIP not found: $Zip" }
Expand-Archive -LiteralPath $Zip -DestinationPath $Extract -Force
$Py="$Work\match_$Stamp.py"
@'
import csv,json,re,sys,math
from pathlib import Path
from collections import defaultdict,Counter
root=Path(sys.argv[1]); out=Path(sys.argv[2]); out.mkdir(parents=True,exist_ok=True)
def nt(x):
 s=str(x or '').upper(); s=re.sub(r'[^A-Z0-9 ]+',' ',s); return re.sub(r'\s+',' ',s).strip()
def pc(x): return nt(x).replace(' ','')
def toks(x): return set(t for t in nt(x).split() if len(t)>1)
def rf(p):
 try:
  if p.suffix.lower()=='.json':
   d=json.loads(p.read_text(encoding='utf-8-sig',errors='replace'))
   if isinstance(d,dict):
    for k in ['rows','data','items','records','results']:
     if isinstance(d.get(k),list): return [r for r in d[k] if isinstance(r,dict)]
    return [d]
   return [r for r in d if isinstance(r,dict)] if isinstance(d,list) else []
  with p.open('r',encoding='utf-8-sig',errors='replace',newline='') as f: return list(csv.DictReader(f))[:300000]
 except Exception: return []
def cols(rows):
 c=set()
 for r in rows[:50]: c.update(map(str,r.keys()))
 return c
def fc(c,subs): return [x for x in c if any(s in x.lower() for s in subs)]
def fv(r,cc):
 for c in cc:
  v=r.get(c)
  if v not in [None,'']: return str(v)
 return ''
def addr(r,c): return ' '.join(str(r.get(x,'')) for x in fc(c,['address','paon','saon','street','locality','town','city','site','name']) if r.get(x))
def rid(r,c): return nt(fv(r,fc(c,['parcel_id','parcelid','id','gid','objectid','uprn','title']))) or str(abs(hash(str(r))))
files=[p for p in root.rglob('*') if p.suffix.lower() in ['.csv','.json'] and p.is_file()]
tables=[]
for p in files:
 rows=rf(p); c=cols(rows); tables.append((p,rows,c))
sales=[]; parcels=[]
for p,rows,c in tables:
 name=(str(p)+' '+' '.join(c)).lower()
 is_sale=any(x in name for x in ['sale','sold','transaction','price','paid','history'])
 is_parcel=any(x in name for x in ['parcel','candidate','staging','geometry','polygon','uprn'])
 for i,r in enumerate(rows):
  rec={'file':str(p.relative_to(root)),'row':i,'postcode':pc(fv(r,fc(c,['postcode','post_code','pcd']))),'address':nt(addr(r,c)),'tokens':toks(addr(r,c)),'uprn':nt(fv(r,fc(c,['uprn']))),'title':nt(fv(r,fc(c,['title','reference','ref']))),'raw':r}
  if is_sale: sales.append(rec)
  if is_parcel:
   rec['parcel_id']=rid(r,c); parcels.append(rec)
by_pc=defaultdict(list); by_u=defaultdict(list); by_t=defaultdict(list)
for p in parcels:
 if p['postcode']: by_pc[p['postcode']].append(p)
 if p['uprn']: by_u[p['uprn']].append(p)
 if p['title']: by_t[p['title']].append(p)
match=[]; mp=set(); ms=set(); methods=Counter()
for s in sales:
 cand=[]
 if s['uprn'] in by_u: cand += [(1.0,'uprn_exact',p) for p in by_u[s['uprn']]]
 if s['title'] in by_t: cand += [(0.95,'title_exact',p) for p in by_t[s['title']]]
 if s['postcode'] in by_pc:
  for p in by_pc[s['postcode']]:
   inter=len(s['tokens']&p['tokens']); union=max(1,len(s['tokens']|p['tokens'])); j=inter/union
   if j>=.45: cand.append((.75+min(j,.25),'postcode_address_tokens',p))
   elif inter>=2: cand.append((.65,'postcode_two_token_overlap',p))
 if cand:
  cand.sort(key=lambda x:x[0],reverse=True); sc,m,p=cand[0]
  if sc>=.65:
   ms.add((s['file'],s['row'])); mp.add(p['parcel_id']); methods[m]+=1
   match.append({'score':round(sc,3),'method':m,'sale_file':s['file'],'sale_row':s['row'],'sale_postcode':s['postcode'],'sale_address':s['address'][:180],'parcel_id':p['parcel_id'],'parcel_file':p['file'],'parcel_row':p['row'],'parcel_postcode':p['postcode'],'parcel_address':p['address'][:180]})
with (out/'LOCATION_MATCH_CANDIDATES.csv').open('w',encoding='utf-8',newline='') as f:
 w=csv.DictWriter(f,fieldnames=['score','method','sale_file','sale_row','sale_postcode','sale_address','parcel_id','parcel_file','parcel_row','parcel_postcode','parcel_address']); w.writeheader(); w.writerows(match[:20000])
summary={'status':'LOCATION_MATCH_ANALYSIS_COMPLETE','files_scanned':len(files),'sales_records_loaded':len(sales),'parcel_records_loaded':len(parcels),'matched_sales_rows_high_or_medium':len(ms),'matched_unique_parcel_count':len(mp),'method_counts':dict(methods),'label':'HUMAN_REVIEW_CANDIDATE_LOCATION_MATCH'}
(out/'LOCATION_MATCH_SUMMARY.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
(out/'LOCATION_MATCH_REPORT.txt').write_text('\n'.join([f'{k}={v}' for k,v in summary.items()])+'\n',encoding='utf-8')
print('LOCATION_MATCH_ANALYSIS_COMPLETE'); print('matched_unique_parcel_count='+str(len(mp)))
'@ | Set-Content -Encoding UTF8 $Py
python $Py $Extract $Reports
Write-Host "LOCAL_REPORT=$Reports\LOCATION_MATCH_REPORT.txt"
Write-Host "Bekleme suresi: 5-10 dakika"
