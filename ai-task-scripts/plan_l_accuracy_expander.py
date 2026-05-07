# -*- coding: utf-8 -*-
from __future__ import annotations
import csv, json, os, re, sys
from collections import Counter, defaultdict
from datetime import datetime

BASE_DIR = os.environ.get('PLAN_L_BASE_DIR', r'D:\6 color parcells\plan_l_run01')
INPUT_DIR = os.path.join(BASE_DIR, 'input')
OUTPUT_DIR = os.path.join(BASE_DIR, 'output')
QA_DIR = os.path.join(OUTPUT_DIR, 'qa')
CSV_OUT = os.path.join(OUTPUT_DIR, 'london_6color.csv')
GEOJSON_OUT = os.path.join(OUTPUT_DIR, 'london_6color.geojson')
MARKET = os.path.join(INPUT_DIR, 'market_3110.csv')
VOA = os.path.join(INPUT_DIR, 'voa_london.csv')
REPORT_MD = os.path.join(QA_DIR, 'PLAN_L_ACCURACY_EXPANSION_REPORT.md')
REPORT_JSON = os.path.join(QA_DIR, 'plan_l_accuracy_expansion_report.json')

PRIORITY = ['Karma','Sanayi','Ofis','Perakende','Apartman','Müstakil']
KW = {
    'Sanayi': ['factory','industrial','warehouse','depot','workshop','plant','manufacturing','logistics','distribution'],
    'Perakende': ['retail','shop','store','supermarket','mall','shopping','showroom','restaurant','cafe','unit'],
    'Ofis': ['office','offices','business centre','business center','coworking','co-working','workspace','serviced office'],
    'Apartman': ['apartment','apartments','flat','flats','residential','block','maisonette','dwelling'],
    'Müstakil': ['detached','house','houses','semi-detached','semi detached','terrace','terraced','townhouse'],
}
MIX = ['mixed-use','mixed use','shop below','flats above','residential above','ground floor retail','upper floors residential']
COLS_EVIDENCE = ['parcel_ref','matched_inspire_id','current_class','confidence','sources','evidence_classes','evidence_strength','market_hits','voa_hits','reason']


def ensure(): os.makedirs(QA_DIR, exist_ok=True)

def norm(x): return '' if x is None else str(x).strip()

def read_csv(path):
    if not os.path.exists(path): return []
    with open(path, 'r', encoding='utf-8-sig', newline='') as f: return list(csv.DictReader(f))

def write_csv(path, rows, cols):
    with open(path, 'w', encoding='utf-8-sig', newline='') as f:
        w=csv.DictWriter(f, fieldnames=cols); w.writeheader(); w.writerows(rows)

def text(row): return ' | '.join(norm(v) for v in row.values() if norm(v))

def hit_classes(txt):
    low=(txt or '').lower()
    hits=defaultdict(list)
    for cls, words in KW.items():
        for w in words:
            if re.search(r'\b'+re.escape(w)+r'\b', low): hits[cls].append(w)
    retail=bool(hits.get('Perakende'))
    residential=bool(hits.get('Apartman') or hits.get('Müstakil'))
    if any(m in low for m in MIX) or (retail and residential and any(x in low for x in ['above','below','over','under','ground floor','upper floor'])):
        hits['Karma'].append('mixed/stacked-use phrase')
    return dict(hits)

def top_class(hits):
    if not hits: return ''
    for cls in PRIORITY:
        if cls in hits: return cls
    return ''

def index_rows(rows):
    by_ref=defaultdict(list); by_insp=defaultdict(list)
    for r in rows:
        ref=norm(r.get('matched_parcel_ref') or r.get('parcel_ref'))
        insp=norm(r.get('matched_inspire_id') or r.get('inspire_id'))
        if ref: by_ref[ref].append(r)
        if insp: by_insp[insp].append(r)
    return by_ref, by_insp

def evidence_for(row, market_ref, market_insp, voa_ref, voa_insp):
    ref=norm(row.get('parcel_ref'))
    insp=norm(row.get('matched_inspire_id'))
    mrows=market_ref.get(ref, []) + market_insp.get(insp, [])
    vrows=voa_ref.get(ref, []) + voa_insp.get(insp, [])
    market_text=' | '.join(text(r) for r in mrows[:20])
    voa_text=' | '.join(text(r) for r in vrows[:20])
    mh=hit_classes(market_text); vh=hit_classes(voa_text)
    all_hits=defaultdict(list)
    for src_hits in (mh,vh):
        for k,vals in src_hits.items(): all_hits[k].extend(vals)
    ev_classes=[c for c in PRIORITY if c in all_hits]
    strength=0
    if mh: strength += 1
    if vh: strength += 1
    if len(ev_classes) >= 2: strength += 1
    if 'Karma' in ev_classes: strength += 1
    current=norm(row.get('use6_class'))
    suggested=top_class(all_hits)
    conf=norm(row.get('use6_confidence'))
    reason=[]
    if suggested and suggested != current: reason.append('class_conflict_suggested_' + suggested)
    if conf in ('1','2') and suggested: reason.append('low_confidence_with_external_evidence')
    if current == 'Karma' and 'Karma' not in ev_classes: reason.append('karma_without_external_mixed_phrase')
    return {
        'parcel_ref': ref,
        'matched_inspire_id': insp,
        'current_class': current,
        'confidence': conf,
        'sources': norm(row.get('use6_sources')),
        'evidence_classes': ';'.join(ev_classes),
        'evidence_strength': strength,
        'market_hits': ';'.join(k+':'+'/'.join(v[:5]) for k,v in mh.items()),
        'voa_hits': ';'.join(k+':'+'/'.join(v[:5]) for k,v in vh.items()),
        'reason': ';'.join(reason),
    }

def main():
    ensure()
    classified=read_csv(CSV_OUT); market=read_csv(MARKET); voa=read_csv(VOA)
    market_ref, market_insp=index_rows(market); voa_ref, voa_insp=index_rows(voa)
    evidence=[]; conflicts=[]; manual=[]
    for r in classified:
        ev=evidence_for(r, market_ref, market_insp, voa_ref, voa_insp)
        evidence.append(ev)
        if ev['reason']: conflicts.append(ev)
        if ev['reason'] or ev['confidence'] in ('1','2'):
            manual.append(ev)
    write_csv(os.path.join(QA_DIR,'qa_evidence_by_parcel_sample.csv'), evidence[:10000], COLS_EVIDENCE)
    write_csv(os.path.join(QA_DIR,'qa_conflict_candidates.csv'), conflicts[:10000], COLS_EVIDENCE)
    write_csv(os.path.join(QA_DIR,'qa_recommended_manual_review.csv'), manual[:10000], COLS_EVIDENCE)
    by_current=Counter(r.get('current_class','') for r in evidence)
    by_ev=Counter()
    for r in evidence:
        for c in r['evidence_classes'].split(';'):
            if c: by_ev[c]+=1
    metrics={
        'generated_at': datetime.utcnow().isoformat()+'Z',
        'classified_rows': len(classified),
        'market_rows': len(market),
        'voa_rows': len(voa),
        'evidence_rows': len(evidence),
        'conflict_candidates': len(conflicts),
        'manual_review_candidates': len(manual),
        'current_class_counts': dict(by_current),
        'external_evidence_class_counts': dict(by_ev),
        'outputs': ['qa_evidence_by_parcel_sample.csv','qa_conflict_candidates.csv','qa_recommended_manual_review.csv']
    }
    with open(REPORT_JSON,'w',encoding='utf-8') as f: json.dump(metrics,f,ensure_ascii=False,indent=2)
    lines=['# Plan L Accuracy Expansion Report','', 'Generated: '+metrics['generated_at'], '', '## Metrics']
    for k in ['classified_rows','market_rows','voa_rows','evidence_rows','conflict_candidates','manual_review_candidates']:
        lines.append('- %s: %s' % (k, metrics[k]))
    lines += ['', '## Current class counts']
    for k,v in sorted(by_current.items()): lines.append('- %s: %s' % (k,v))
    lines += ['', '## External evidence class counts']
    for k,v in sorted(by_ev.items()): lines.append('- %s: %s' % (k,v))
    lines += ['', '## Interpretation', '- Conflict candidates are not automatic overrides.', '- They are review targets for stronger matching rules or manual validation.', '- Broad VOA borough matching is intentionally not used.', '', 'NEXT_COMMAND=devam et']
    with open(REPORT_MD,'w',encoding='utf-8') as f: f.write('\n'.join(lines)+'\n')
    print('RESULT=ok')
    print('CONFLICT_CANDIDATES=%d' % len(conflicts))
    print('MANUAL_REVIEW_CANDIDATES=%d' % len(manual))
    print('REPORT_MD=' + REPORT_MD)

if __name__ == '__main__':
    try: main()
    except Exception as e:
        print('RESULT=failed')
        print('ERROR=' + str(e))
        sys.exit(1)
