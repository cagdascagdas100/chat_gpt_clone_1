$ErrorActionPreference='Continue'
$Repo='C:\Users\cagda\Documents\GitHub\AAYS'
$Remote='https://github.com/cagdascagdas100/chat_gpt_clone_1.git'
$Branch='feature/terrayield-aays-integration'
$Stamp=Get-Date -Format yyyyMMdd-HHmmss
$Root=$null
foreach($d in @('E:\chatgpt','D:\chatgpt','C:\Temp\chatgpt')){ if(Test-Path (Split-Path $d -Qualifier)){ $Root=$d; break } }
if(!$Root){ $Root='C:\Temp\chatgpt' }
$Work=Join-Path $Root 'AAYS_FULL_DB_ADDRESS_MATCH_V2'
$Reports=Join-Path $Work "reports_$Stamp"
New-Item -ItemType Directory -Force $Work,$Reports | Out-Null
$Py=Join-Path $Work "full_db_address_match_v2_$Stamp.py"
@'
import csv, json, os, re, sys, subprocess, math, tempfile
from pathlib import Path
from collections import defaultdict, Counter
work=Path(sys.argv[1]); reports=Path(sys.argv[2]); reports.mkdir(parents=True,exist_ok=True)
def run(cmd, timeout=120):
    p=subprocess.run(cmd,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,errors='replace',timeout=timeout)
    return p.returncode,p.stdout,p.stderr
def norm(x):
    x='' if x is None else str(x).upper()
    x=re.sub(r'[^A-Z0-9 ]+',' ',x); x=re.sub(r'\s+',' ',x).strip(); return x
def pc(x): return norm(x).replace(' ','')
def toks(x): return set(t for t in norm(x).split() if len(t)>1 and t not in {'THE','AND','OF','ROAD','STREET','LTD','LIMITED'})
def choose(cols, pats):
    lc={c.lower():c for c in cols}
    for p in pats:
        for c in cols:
            if c.lower()==p: return c
    for p in pats:
        for c in cols:
            if p in c.lower(): return c
    return None
def qident(s): return '"'+s.replace('"','""')+'"'
# docker/postgres discovery
code,out,err=run(['docker','ps','--format','{{.ID}}|{{.Image}}|{{.Names}}'])
containers=[l.split('|') for l in out.splitlines() if re.search('postgres|postgis',l,re.I)]
if not containers:
    raise SystemExit('NO_POSTGRES_CONTAINER_FOUND')
cid=containers[0][0]
code,envout,err=run(['docker','inspect','-f','{{range .Config.Env}}{{println .}}{{end}}',cid])
env=dict([tuple(x.split('=',1)) for x in envout.splitlines() if '=' in x])
user=env.get('POSTGRES_USER','postgres'); default_db=env.get('POSTGRES_DB','postgres')
def psql(db, sql, timeout=240):
    return run(['docker','exec',cid,'psql','-U',user,'-d',db,'-At','-c',sql], timeout=timeout)
def psql_csv(db, sql, path, timeout=900):
    cmd=['docker','exec',cid,'psql','-U',user,'-d',db,'-c',"\\copy ("+sql+") TO STDOUT WITH CSV HEADER"]
    p=subprocess.run(cmd,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,errors='replace',timeout=timeout)
    path.write_text(p.stdout,encoding='utf-8',errors='replace')
    return p.returncode,p.stderr
code,dbout,err=psql(default_db,"select datname from pg_database where datistemplate=false order by 1")
dbs=[x.strip() for x in dbout.splitlines() if x.strip()] or [default_db]
chosen=None; tx_table=None
for db in dbs:
    code,tout,err=psql(db,"select table_schema||'.'||table_name from information_schema.tables where table_type='BASE TABLE' and table_name ilike '%transactions_price_paid%' limit 5")
    if tout.strip(): chosen=db; tx_table=tout.splitlines()[0].strip(); break
if not chosen:
    raise SystemExit('transactions_price_paid table not found in visible postgres databases')
# columns
schema,table=tx_table.split('.',1)
col_sql=f"select column_name from information_schema.columns where table_schema='{schema}' and table_name='{table}' order by ordinal_position"
code,colout,err=psql(chosen,col_sql)
tx_cols=[x.strip() for x in colout.splitlines() if x.strip()]
fields={
 'postcode':choose(tx_cols,['postcode','post_code','post code','pcd']),
 'paon':choose(tx_cols,['paon','primary_addressable_object_name','house_number','building_number']),
 'saon':choose(tx_cols,['saon','secondary_addressable_object_name','flat','unit']),
 'street':choose(tx_cols,['street','thoroughfare','road']),
 'town':choose(tx_cols,['town','city','post_town','locality']),
 'uprn':choose(tx_cols,['uprn']),
 'title':choose(tx_cols,['title_number','title_no','title','transaction_unique_identifier','transaction_id']),
 'price':choose(tx_cols,['price','sale_price','amount']),
 'date':choose(tx_cols,['date_of_transfer','transfer_date','sale_date','date'])
}
def expr(col, alias): return (f"coalesce({qident(col)}::text,'') as {alias}" if col else f"'' as {alias}")
tx_select=', '.join([expr(fields[k],k) for k in ['postcode','paon','saon','street','town','uprn','title','price','date']])
tx_csv=reports/'transactions_price_paid_v2_export.csv'
psql_csv(chosen, f"select {tx_select} from {qident(schema)}.{qident(table)}", tx_csv)
# parcel table candidates
cand_sql="""
select table_schema||'.'||table_name
from information_schema.columns
where lower(column_name) similar to '%(parcel|postcode|post_code|uprn|title|address|street|paon|saon|geom|geometry|wkb_geometry)%'
and table_schema not in ('pg_catalog','information_schema')
group by table_schema,table_name
having count(*)>=2
order by table_schema,table_name
"""
code,pout,err=psql(chosen,cand_sql)
parcel_tables=[x.strip() for x in pout.splitlines() if x.strip() and x.strip()!=tx_table]
parcel_csvs=[]; inv=[]
for full in parcel_tables[:80]:
    s,t=full.split('.',1)
    code,cout,err=psql(chosen,f"select column_name from information_schema.columns where table_schema='{s}' and table_name='{t}' order by ordinal_position")
    cols=[x.strip() for x in cout.splitlines() if x.strip()]
    flds={
      'parcel_id':choose(cols,['parcel_id','parcelid','id','gid','objectid','uprn','title_number']),
      'postcode':choose(cols,['postcode','post_code','post code','pcd']),
      'paon':choose(cols,['paon','primary_addressable_object_name','house_number','building_number']),
      'saon':choose(cols,['saon','secondary_addressable_object_name','flat','unit']),
      'street':choose(cols,['street','thoroughfare','road','address']),
      'town':choose(cols,['town','city','post_town','locality']),
      'uprn':choose(cols,['uprn']),
      'title':choose(cols,['title_number','title_no','title'])
    }
    if not any(flds.values()): continue
    sel=', '.join([expr(flds[k],k) for k in ['parcel_id','postcode','paon','saon','street','town','uprn','title']])
    safe=re.sub('[^A-Za-z0-9_]+','_',full)
    outp=reports/f'parcel_candidate_{safe}.csv'
    psql_csv(chosen, f"select {sel} from {qident(s)}.{qident(t)} limit 1000000", outp)
    parcel_csvs.append(outp); inv.append({'table':full,'columns':cols,'mapped':flds,'export':outp.name})
# load CSV
def rows(path):
    with path.open('r',encoding='utf-8-sig',errors='replace',newline='') as f:
        for r in csv.DictReader(f): yield r
sales=[]
for i,r in enumerate(rows(tx_csv)):
    addr=' '.join([r.get('paon',''),r.get('saon',''),r.get('street',''),r.get('town','')])
    sales.append({'i':i,'pc':pc(r.get('postcode')),'paon':norm(r.get('paon')),'street':norm(r.get('street')),'addr':norm(addr),'tok':toks(addr),'uprn':norm(r.get('uprn')),'title':norm(r.get('title'))})
parcels=[]
for pth in parcel_csvs:
    for i,r in enumerate(rows(pth)):
        addr=' '.join([r.get('paon',''),r.get('saon',''),r.get('street',''),r.get('town','')])
        pid=norm(r.get('parcel_id')) or f'{pth.name}:{i}'
        parcels.append({'pid':pid,'file':pth.name,'row':i,'pc':pc(r.get('postcode')),'paon':norm(r.get('paon')),'street':norm(r.get('street')),'addr':norm(addr),'tok':toks(addr),'uprn':norm(r.get('uprn')),'title':norm(r.get('title'))})
by_pc=defaultdict(list); by_uprn=defaultdict(list); by_title=defaultdict(list)
for p in parcels:
    if p['pc']: by_pc[p['pc']].append(p)
    if p['uprn']: by_uprn[p['uprn']].append(p)
    if p['title']: by_title[p['title']].append(p)
matched_p=set(); matched_s=set(); out=[]; methods=Counter()
for s in sales:
    cands=[]
    if s['uprn'] in by_uprn: cands += [(0.99,'uprn_exact',p) for p in by_uprn[s['uprn']]]
    if s['title'] in by_title: cands += [(0.96,'title_exact',p) for p in by_title[s['title']]]
    for p in by_pc.get(s['pc'],[])[:5000]:
        score=0.42; method='postcode_only'
        if s['paon'] and p['paon'] and s['paon']==p['paon']:
            score+=0.28; method='postcode_paon'
        if s['street'] and p['street'] and (s['street'] in p['street'] or p['street'] in s['street']):
            score+=0.18; method += '_street'
        inter=len(s['tok'] & p['tok']); union=max(1,len(s['tok']|p['tok']))
        j=inter/union
        if j>=0.35:
            score=max(score,0.66+min(j,0.25)); method='postcode_address_token'
        if score>=0.65: cands.append((score,method,p))
    if cands:
        cands.sort(key=lambda x:x[0], reverse=True)
        sc,m,p=cands[0]
        matched_p.add(p['pid']); matched_s.add(s['i']); methods[m]+=1
        if len(out)<50000:
            out.append({'score':round(sc,3),'method':m,'sale_row':s['i'],'sale_pc':s['pc'],'sale_addr':s['addr'][:180],'parcel_id':p['pid'],'parcel_file':p['file'],'parcel_row':p['row'],'parcel_pc':p['pc'],'parcel_addr':p['addr'][:180]})
with (reports/'FULL_DB_ADDRESS_MATCH_V2_MATCHES.csv').open('w',encoding='utf-8',newline='') as f:
    w=csv.DictWriter(f,fieldnames=['score','method','sale_row','sale_pc','sale_addr','parcel_id','parcel_file','parcel_row','parcel_pc','parcel_addr']); w.writeheader(); w.writerows(out)
summary={'status':'FULL_DB_ADDRESS_MATCH_V2_COMPLETE','database':chosen,'transactions_table':tx_table,'transaction_rows_loaded':len(sales),'parcel_tables_detected':len(parcel_tables),'parcel_tables_exported':len(parcel_csvs),'parcel_rows_loaded':len(parcels),'matched_sales_rows_v2':len(matched_s),'matched_unique_parcel_count_v2':len(matched_p),'method_counts':dict(methods),'verification_label':'HUMAN_REVIEW_CANDIDATE_ADDRESS_MATCH_V2','db_write':False,'production_deploy':False,'verified_auto_publish':False}
(reports/'FULL_DB_ADDRESS_MATCH_V2_SUMMARY.json').write_text(json.dumps(summary,indent=2,ensure_ascii=False),encoding='utf-8')
(reports/'FULL_DB_ADDRESS_MATCH_V2_INVENTORY.json').write_text(json.dumps(inv,indent=2,ensure_ascii=False),encoding='utf-8')
lines=[f'{k}={v}' for k,v in summary.items() if k!='method_counts']; lines.append('method_counts='+json.dumps(dict(methods),ensure_ascii=False))
(reports/'FULL_DB_ADDRESS_MATCH_V2_REPORT.txt').write_text('\n'.join(lines)+'\n',encoding='utf-8')
print('FULL_DB_ADDRESS_MATCH_V2_COMPLETE')
print('matched_unique_parcel_count_v2='+str(len(matched_p)))
print('matched_sales_rows_v2='+str(len(matched_s)))
print('report='+str(reports/'FULL_DB_ADDRESS_MATCH_V2_REPORT.txt'))
'@ | Set-Content -Encoding UTF8 $Py
python $Py $Work $Reports
$DestRel='docs/chatgpt_status/sales_parcel_access_exports/full_db_address_match_v2_20260606'
$Clean=Join-Path $Work "repo_push_$Stamp"
if(Test-Path $Clean){ Remove-Item $Clean -Recurse -Force }
git clone --depth 1 --branch $Branch --filter=blob:none --sparse $Remote $Clean
git -C $Clean sparse-checkout set docs/chatgpt_status/sales_parcel_access_exports docs/chatgpt_status
$Dest=Join-Path $Clean $DestRel
New-Item -ItemType Directory -Force $Dest | Out-Null
Copy-Item "$Reports\*" $Dest -Recurse -Force
git -C $Clean add $DestRel
if(git -C $Clean status --porcelain){ git -C $Clean commit -m 'docs: add full db address match v2 report'; git -C $Clean pull --rebase origin $Branch; git -C $Clean push origin $Branch }
Write-Host 'STATUS=FULL_DB_ADDRESS_MATCH_V2_DONE'
Write-Host "LOCAL_REPORT=$Reports\FULL_DB_ADDRESS_MATCH_V2_REPORT.txt"
Write-Host 'Bekleme suresi: 10-25 dakika'
