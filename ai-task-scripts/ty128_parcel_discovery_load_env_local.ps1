$ErrorActionPreference='Continue'
$TaskId='ty128-parcel-discovery-load-env-local'
$BridgeRoot='C:\AAYS1_GITHUB_BRIDGE\chat_gpt_clone_1'
$ProjectRoot='C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence'
$LegalRoot='E:\AAYS_DATA\legal'
$OutDir=Join-Path $BridgeRoot 'ai-results'
New-Item -ItemType Directory -Force -Path $OutDir,(Join-Path $LegalRoot 'reports') | Out-Null
function L($m){Write-Output ('['+(Get-Date -Format 's')+'] '+$m)}
function Import-DotEnv($path){
  if(!(Test-Path $path)){return $false}
  Get-Content $path | ForEach-Object {
    $line=$_.Trim()
    if(!$line -or $line.StartsWith('#')){return}
    $idx=$line.IndexOf('=')
    if($idx -lt 1){return}
    $key=$line.Substring(0,$idx).Trim()
    $val=$line.Substring($idx+1).Trim()
    if(($val.StartsWith('"') -and $val.EndsWith('"')) -or ($val.StartsWith("'") -and $val.EndsWith("'"))){$val=$val.Substring(1,$val.Length-2)}
    if($key -match '^(DATABASE_URL|PGHOST|PGPORT|PGDATABASE|PGUSER|PGPASSWORD|AAYS_PARCEL_TABLE|AAYS_PARCEL_ID_COL|AAYS_PARCEL_GEOM_COL)$'){
      Set-Item -Path ('Env:'+ $key) -Value $val
    }
  }
  return $true
}
$envFile=Join-Path $ProjectRoot '.env.local'
$loadedEnvLocal=Import-DotEnv $envFile
foreach($k in @('DATABASE_URL','PGHOST','PGPORT','PGDATABASE','PGUSER','PGPASSWORD')){
  $cur=(Get-Item -Path ('Env:'+ $k) -ErrorAction SilentlyContinue).Value
  if([string]::IsNullOrWhiteSpace($cur)){
    $v=[Environment]::GetEnvironmentVariable($k,'User')
    if(-not [string]::IsNullOrWhiteSpace($v)){Set-Item -Path ('Env:'+ $k) -Value $v}
  }
}
$dbCreds=[bool]($env:DATABASE_URL -or ($env:PGHOST -and $env:PGDATABASE -and $env:PGUSER -and $env:PGPASSWORD))
$py=Join-Path $OutDir 'ty128_parcel_discovery.py'
@'
import os, json, sys
try:
    import psycopg
    from psycopg.rows import dict_row
except Exception as e:
    print(json.dumps({'ok': False, 'error': 'psycopg_import_failed', 'detail': str(e)}))
    sys.exit(2)
conninfo=os.environ.get('DATABASE_URL')
if not conninfo:
    parts={'host':os.environ.get('PGHOST'),'port':os.environ.get('PGPORT','5432'),'dbname':os.environ.get('PGDATABASE'),'user':os.environ.get('PGUSER'),'password':os.environ.get('PGPASSWORD')}
    conninfo=' '.join(f'{k}={v}' for k,v in parts.items() if v)
if not conninfo.strip():
    print(json.dumps({'ok': False, 'error': 'missing_db_credentials'}))
    sys.exit(3)
out=[]
try:
    with psycopg.connect(conninfo,row_factory=dict_row) as conn:
        with conn.cursor() as cur:
            cur.execute("""
            select table_schema, table_name
            from information_schema.tables
            where table_type='BASE TABLE'
              and (lower(table_name) like '%parcel%' or lower(table_name) like '%land%' or lower(table_name) like '%site%' or lower(table_name) like '%property%')
            order by table_schema, table_name
            """)
            tables=cur.fetchall()
            for t in tables:
                schema=t['table_schema']; table=t['table_name']
                cur.execute("""
                select column_name, data_type, udt_name
                from information_schema.columns
                where table_schema=%s and table_name=%s
                order by ordinal_position
                """, (schema, table))
                cols=cur.fetchall()
                col_names=[c['column_name'] for c in cols]
                geom=[c['column_name'] for c in cols if str(c.get('udt_name','')).lower() in ('geometry','geography') or c['column_name'].lower() in ('geom','geometry','wkb_geometry','the_geom')]
                ids=[c for c in col_names if c.lower() in ('parcel_id','id','gid','uprn','title_number','objectid') or 'parcel' in c.lower()]
                out.append({'table':f'{schema}.{table}','id_candidates':ids,'geom_candidates':geom,'columns':col_names[:80]})
    print(json.dumps({'ok': True, 'candidates': out}, ensure_ascii=False))
except Exception as e:
    print(json.dumps({'ok': False, 'error': 'db_query_failed', 'detail': str(e)}, ensure_ascii=False))
    sys.exit(4)
'@ | Set-Content -Encoding UTF8 -Path $py
$raw=''
$exit=0
if($dbCreds){$raw=(& python $py 2>&1 | Out-String);$exit=$LASTEXITCODE}else{$raw='{"ok":false,"error":"missing_db_credentials_after_env_local_import"}';$exit=3}
try{$obj=$raw|ConvertFrom-Json}catch{$obj=[ordered]@{ok=$false;error='json_parse_failed';raw=$raw}}
$candidateCount=0
try{if($obj.ok -eq $true){$candidateCount=@($obj.candidates).Count}}catch{}
$progress=95
$next='Fix local .env.local / DATABASE_URL / PG* credentials, then rerun. No secret values are written to GitHub.'
if($obj.ok -eq $true -and $candidateCount -gt 0){$progress=97;$next='Choose candidate table plus id/geom columns, then run matcher/export.'}
elseif($obj.ok -eq $true){$next='No parcel-like table found; import/create PostGIS parcel table, then rerun matcher.'}
$a=[ordered]@{task_id=$TaskId;status='completed';generated_at=(Get-Date).ToString('s');loaded_env_local=$loadedEnvLocal;db_credentials_present=$dbCreds;python_exit_code=$exit;candidate_count=$candidateCount;discovery=$obj;plan_progress_percent=$progress;plan_percent_remaining=(100-$progress);next_action=$next}
$a|ConvertTo-Json -Depth 12|Set-Content -Encoding UTF8 -Path (Join-Path $OutDir 'ty128-parcel-discovery-load-env-local.audit.json')
$lines=@('# TY128 Parcel Discovery Load Env Local','',('Plan completed: '+$progress+'%'),('Plan remaining: '+(100-$progress)+'%'),('Loaded .env.local: '+$loadedEnvLocal),('DB credentials present: '+$dbCreds),('Python exit code: '+$exit),('Candidate count: '+$candidateCount),'','## Raw discovery',$raw,'','## Next Action',$next)
$lines|Set-Content -Encoding UTF8 -Path (Join-Path $OutDir 'ty128-parcel-discovery-load-env-local.report.md')
L('PLAN_PROGRESS_PERCENT='+$progress)
L('PLAN_PERCENT_REMAINING='+(100-$progress))
exit 0
