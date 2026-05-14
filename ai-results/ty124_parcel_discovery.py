import os, json, sys
try:
    import psycopg
    from psycopg.rows import dict_row
except Exception as e:
    print(json.dumps({"ok": False, "error": "psycopg_import_failed", "detail": str(e)}))
    sys.exit(2)
conninfo=os.environ.get("DATABASE_URL")
if not conninfo:
    parts={"host":os.environ.get("PGHOST"),"port":os.environ.get("PGPORT","5432"),"dbname":os.environ.get("PGDATABASE"),"user":os.environ.get("PGUSER"),"password":os.environ.get("PGPASSWORD")}
    conninfo=" ".join(f"{k}={v}" for k,v in parts.items() if v)
if not conninfo.strip():
    print(json.dumps({"ok": False, "error": "missing_db_credentials"}))
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
                out.append({'table':f'{schema}.{table}','id_candidates':ids,'geom_candidates':geom,'columns':col_names})
    print(json.dumps({'ok': True, 'candidates': out}, ensure_ascii=False))
except Exception as e:
    print(json.dumps({'ok': False, 'error': 'db_query_failed', 'detail': str(e)}, ensure_ascii=False))
    sys.exit(4)
