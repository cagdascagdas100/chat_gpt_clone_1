$ErrorActionPreference='Continue'
$TaskId='ty127-parcel-discovery-user-env-fixed'
$BridgeRoot='C:\AAYS1_GITHUB_BRIDGE\chat_gpt_clone_1'
$LegalRoot='E:\AAYS_DATA\legal'
$OutDir=Join-Path $BridgeRoot 'ai-results'
New-Item -ItemType Directory -Force -Path $OutDir,(Join-Path $LegalRoot 'reports') | Out-Null
function L($m){Write-Output ('['+(Get-Date -Format 's')+'] '+$m)}
foreach($k in @('DATABASE_URL','PGHOST','PGPORT','PGDATABASE','PGUSER','PGPASSWORD')){
  $cur=(Get-Item -Path ('Env:'+ $k) -ErrorAction SilentlyContinue).Value
  if([string]::IsNullOrWhiteSpace($cur)){
    $v=[Environment]::GetEnvironmentVariable($k,'User')
    if(-not [string]::IsNullOrWhiteSpace($v)){Set-Item -Path ('Env:'+ $k) -Value $v}
  }
}
$dbCreds=[bool]($env:DATABASE_URL -or ($env:PGHOST -and $env:PGDATABASE -and $env:PGUSER -and $env:PGPASSWORD))
$py=Join-Path $OutDir 'ty127_parcel_discovery.py'
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
if($dbCreds){$raw=(& python $py 2>&1 | Out-String);$exit=$LASTEXITCODE}else{$raw='{"ok":false,"error":"missing_db_credentials_after_user_env_import"}';$exit=3;Set-Content -Encoding UTF8 -Path (Join-Path $LegalRoot 'reports\blocked_by_missing_credential_parcel_discovery.json') -Value $raw}
try{$obj=$raw|ConvertFrom-Json}catch{$obj=[ordered]@{ok=$false;error='json_parse_failed';raw=$raw}}
$candidateCount=0
try{if($obj.ok -eq $true){$candidateCount=@($obj.candidates).Count}}catch{}
$progress=95
$next='Set User-level DB env and rerun. No secret values are written to GitHub.'
if($obj.ok -eq $true -and $candidateCount -gt 0){$progress=97;$next='Choose candidate table plus id/geom columns, then run matcher/export.'}
elseif($obj.ok -eq $true){$next='No parcel-like table found; import/create PostGIS parcel table, then rerun matcher.'}
$a=[ordered]@{task_id=$TaskId;status='completed';generated_at=(Get-Date).ToString('s');db_credentials_present_after_user_env_import=$dbCreds;python_exit_code=$exit;candidate_count=$candidateCount;discovery=$obj;plan_progress_percent=$progress;plan_percent_remaining=(100-$progress);next_action=$next}
$a|ConvertTo-Json -Depth 12|Set-Content -Encoding UTF8 -Path (Join-Path $OutDir 'ty127-parcel-discovery-user-env-fixed.audit.json')
$lines=@('# TY127 Parcel Discovery User Env Fixed','',('Plan completed: '+$progress+'%'),('Plan remaining: '+(100-$progress)+'%'),('DB credentials present after User env import: '+$dbCreds),('Python exit code: '+$exit),('Candidate count: '+$candidateCount),'','## Raw discovery',$raw,'','## Next Action',$next)
$lines|Set-Content -Encoding UTF8 -Path (Join-Path $OutDir 'ty127-parcel-discovery-user-env-fixed.report.md')
L('PLAN_PROGRESS_PERCENT='+$progress)
L('PLAN_PERCENT_REMAINING='+(100-$progress))
exit 0
