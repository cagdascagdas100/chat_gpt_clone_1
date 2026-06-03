# -*- coding: utf-8 -*-
from __future__ import annotations
import csv, json, os, sys, logging, re
from collections import Counter, defaultdict
from datetime import datetime

BASE_DIR = os.environ.get('PLAN_L_BASE_DIR', r'D:\6 color parcells\plan_l_run01')
INPUT_DIR = os.path.join(BASE_DIR, 'input')
OUTPUT_DIR = os.path.join(BASE_DIR, 'output')
QA_DIR = os.path.join(OUTPUT_DIR, 'qa')
LOG_DIR = os.path.join(BASE_DIR, 'logs')
LOG_PATH = os.path.join(LOG_DIR, 'deep_qa.log')
CSV_OUT = os.path.join(OUTPUT_DIR, 'london_6color.csv')
GEOJSON_OUT = os.path.join(OUTPUT_DIR, 'london_6color.geojson')
MARKET = os.path.join(INPUT_DIR, 'market_3110.csv')
VOA = os.path.join(INPUT_DIR, 'voa_london.csv')
REPORT_JSON = os.path.join(QA_DIR, 'plan_l_deep_qa_report.json')
REPORT_MD = os.path.join(QA_DIR, 'PLAN_L_DEEP_QA_REPORT.md')

CLASSES = ['Sanayi','Ofis','Perakende','Apartman','Müstakil','Karma']
EXPECTED_COLS = ['parcel_ref','use6_class','use6_color','use6_confidence','use6_sources']
KW = {
    'Sanayi': ['factory','industrial','warehouse','depot','workshop','plant','manufacturing','logistics','distribution'],
    'Perakende': ['retail','shop','store','supermarket','mall','shopping','showroom','restaurant','cafe'],
    'Ofis': ['office','business centre','business center','coworking','co-working','workspace'],
    'Apartman': ['apartment','apartments','flat','flats','residential','block','maisonette'],
    'Müstakil': ['detached','house','houses','semi-detached','semi detached','terrace','terraced','townhouse'],
}


def ensure():
    os.makedirs(QA_DIR, exist_ok=True); os.makedirs(LOG_DIR, exist_ok=True)
    logging.basicConfig(filename=LOG_PATH, level=logging.INFO, filemode='a', encoding='utf-8', format='%(asctime)s %(levelname)s %(message)s')


def read_csv(path):
    if not os.path.exists(path): return []
    with open(path, 'r', encoding='utf-8-sig', newline='') as f:
        return list(csv.DictReader(f))


def write_csv(path, rows, fields):
    with open(path, 'w', encoding='utf-8-sig', newline='') as f:
        w = csv.DictWriter(f, fieldnames=fields); w.writeheader(); w.writerows(rows)


def norm(x): return '' if x is None else str(x).strip()

def lower_join(row): return ' | '.join(norm(v).lower() for v in row.values() if norm(v))


def keyword_matrix(rows, source_name):
    matrix = []
    for cls, words in KW.items():
        cnt = 0
        examples = []
        for r in rows:
            txt = lower_join(r)
            if any(w in txt for w in words):
                cnt += 1
                if len(examples) < 3:
                    examples.append((norm(r.get('parcel_ref') or r.get('matched_parcel_ref') or r.get('matched_inspire_id') or r.get('title'))[:120]))
        matrix.append({'source': source_name, 'class': cls, 'keyword_row_hits': cnt, 'examples': '; '.join(examples)})
    return matrix


def safe_float(x):
    try: return float(str(x).replace(',',''))
    except Exception: return None


def main():
    ensure()
    out_rows = read_csv(CSV_OUT)
    market_rows = read_csv(MARKET)
    voa_rows = read_csv(VOA)
    report = {'generated_at': datetime.utcnow().isoformat() + 'Z', 'base_dir': BASE_DIR, 'files': {}, 'counts': {}, 'warnings': []}
    for name, path in [('classified_csv', CSV_OUT), ('classified_geojson', GEOJSON_OUT), ('market_3110', MARKET), ('voa_london', VOA)]:
        report['files'][name] = {'path': path, 'exists': os.path.exists(path), 'bytes': os.path.getsize(path) if os.path.exists(path) else 0}
    report['counts']['classified_rows'] = len(out_rows)
    report['counts']['market_rows'] = len(market_rows)
    report['counts']['voa_rows'] = len(voa_rows)
    if not out_rows:
        report['warnings'].append('classified output csv missing or empty')
    else:
        missing_cols = [c for c in EXPECTED_COLS if c not in out_rows[0]]
        if missing_cols: report['warnings'].append('missing expected columns: ' + ','.join(missing_cols))
    class_counts = Counter(r.get('use6_class','') for r in out_rows)
    conf_counts = Counter(r.get('use6_confidence','') for r in out_rows)
    source_counts = Counter(r.get('use6_sources','') for r in out_rows)
    write_csv(os.path.join(QA_DIR, 'qa_class_counts_recomputed.csv'), [{'class': k, 'count': v} for k,v in sorted(class_counts.items())], ['class','count'])
    write_csv(os.path.join(QA_DIR, 'qa_confidence_counts_recomputed.csv'), [{'confidence': k, 'count': v} for k,v in sorted(conf_counts.items())], ['confidence','count'])
    write_csv(os.path.join(QA_DIR, 'qa_source_counts.csv'), [{'source_signature': k, 'count': v} for k,v in source_counts.most_common()], ['source_signature','count'])
    low = [r for r in out_rows if str(r.get('use6_confidence','')).strip() in ('1','2')][:500]
    if out_rows:
        write_csv(os.path.join(QA_DIR, 'qa_low_confidence_sample.csv'), low, list(out_rows[0].keys()))
    by_la = defaultdict(Counter)
    for r in out_rows:
        by_la[r.get('local_authority','UNKNOWN')][r.get('use6_class','')] += 1
    la_rows = []
    for la, c in sorted(by_la.items()):
        total = sum(c.values())
        for cls in sorted(c): la_rows.append({'local_authority': la, 'class': cls, 'count': c[cls], 'share': round(c[cls]/total, 6) if total else 0})
    write_csv(os.path.join(QA_DIR, 'qa_local_authority_class_summary.csv'), la_rows, ['local_authority','class','count','share'])
    area = defaultdict(lambda: {'count':0,'area_sum':0.0,'area_known':0})
    for r in out_rows:
        cls = r.get('use6_class','')
        area[cls]['count'] += 1
        a = safe_float(r.get('area_m2'))
        if a is not None:
            area[cls]['area_sum'] += a; area[cls]['area_known'] += 1
    area_rows = [{'class': k, 'count': v['count'], 'area_known': v['area_known'], 'area_sum_m2': round(v['area_sum'],2), 'mean_area_m2': round(v['area_sum']/v['area_known'],2) if v['area_known'] else ''} for k,v in sorted(area.items())]
    write_csv(os.path.join(QA_DIR, 'qa_area_by_class_summary.csv'), area_rows, ['class','count','area_known','area_sum_m2','mean_area_m2'])
    key_stats = []
    for source_name, rows in [('classified',out_rows),('market_3110',market_rows),('voa_london',voa_rows)]:
        if rows:
            cols = rows[0].keys()
            for key in ['parcel_ref','matched_parcel_ref','matched_inspire_id','inspire_id','local_authority']:
                if key in cols:
                    vals = [norm(r.get(key)) for r in rows]
                    nonempty = sum(1 for v in vals if v)
                    key_stats.append({'source': source_name, 'key': key, 'rows': len(rows), 'nonempty': nonempty, 'share_nonempty': round(nonempty/len(rows), 6) if rows else 0, 'unique_nonempty': len(set(v for v in vals if v))})
    write_csv(os.path.join(QA_DIR, 'qa_key_coverage.csv'), key_stats, ['source','key','rows','nonempty','share_nonempty','unique_nonempty'])
    matrix = []
    matrix.extend(keyword_matrix(market_rows, 'market_3110'))
    matrix.extend(keyword_matrix(voa_rows, 'voa_london'))
    write_csv(os.path.join(QA_DIR, 'qa_keyword_hit_matrix.csv'), matrix, ['source','class','keyword_row_hits','examples'])
    suspicious = []
    for r in out_rows:
        if r.get('use6_class') == 'Karma':
            text = (r.get('use6_decision_reason','') + ' ' + r.get('use6_sources','')).lower()
            if 'mixed' not in text and 'retail' not in text:
                suspicious.append(r)
    if out_rows:
        write_csv(os.path.join(QA_DIR, 'qa_suspicious_karma_rows.csv'), suspicious[:1000], list(out_rows[0].keys()))
    if os.path.exists(GEOJSON_OUT):
        try:
            with open(GEOJSON_OUT, 'r', encoding='utf-8-sig') as f: gj = json.load(f)
            report['counts']['geojson_features'] = len(gj.get('features', []))
            if out_rows and len(gj.get('features', [])) != len(out_rows): report['warnings'].append('geojson feature count != csv rows')
        except Exception as e:
            report['warnings'].append('geojson parse error: ' + str(e))
    report['class_counts'] = dict(class_counts)
    report['confidence_counts'] = dict(conf_counts)
    report['source_counts_top'] = dict(source_counts.most_common(20))
    report['qa_outputs'] = sorted([x for x in os.listdir(QA_DIR) if x.endswith('.csv')])
    with open(REPORT_JSON, 'w', encoding='utf-8') as f: json.dump(report, f, ensure_ascii=False, indent=2)
    lines = ['# Plan L Deep QA Report','', 'Generated: ' + report['generated_at'], '', '## Counts']
    for k,v in report['counts'].items(): lines.append('- %s: %s' % (k,v))
    lines += ['', '## Class counts']
    for k,v in sorted(class_counts.items()): lines.append('- %s: %s' % (k,v))
    lines += ['', '## Confidence counts']
    for k,v in sorted(conf_counts.items()): lines.append('- %s: %s' % (k,v))
    lines += ['', '## Warnings']
    if report['warnings']:
        for w in report['warnings']: lines.append('- ' + w)
    else:
        lines.append('- none')
    lines += ['', 'NEXT_COMMAND=devam et']
    with open(REPORT_MD, 'w', encoding='utf-8') as f: f.write('\n'.join(lines) + '\n')
    print('RESULT=ok')
    print('QA_DIR=' + QA_DIR)
    print('REPORT_JSON=' + REPORT_JSON)
    print('REPORT_MD=' + REPORT_MD)

if __name__ == '__main__':
    try: main()
    except Exception as e:
        ensure(); logging.exception('deep qa failed')
        print('RESULT=failed')
        print('ERROR=' + str(e))
        sys.exit(1)
