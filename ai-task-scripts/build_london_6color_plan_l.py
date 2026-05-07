# -*- coding: utf-8 -*-
"""
Plan L London 6-color parcel classifier.
Windows target: D:\\6 color parcells\\plan_l_run01\\scripts\\build_london_6color.py
"""
from __future__ import annotations
import csv, json, logging, os, re, sys
from collections import Counter, defaultdict
from datetime import datetime

BASE_DIR = os.environ.get('PLAN_L_BASE_DIR', r'D:\6 color parcells\plan_l_run01')
INPUT_DIR = os.path.join(BASE_DIR, 'input')
OUTPUT_DIR = os.path.join(BASE_DIR, 'output')
LOG_DIR = os.path.join(BASE_DIR, 'logs')
GEOJSON_PATH = os.path.join(INPUT_DIR, 'london_parcels_geometry.geojson')
MARKET_PATH = os.path.join(INPUT_DIR, 'market_3110.csv')
VOA_PATH = os.path.join(INPUT_DIR, 'voa_london.csv')
OUT_GEOJSON = os.path.join(OUTPUT_DIR, 'london_6color.geojson')
OUT_CSV = os.path.join(OUTPUT_DIR, 'london_6color.csv')
OUT_SUMMARY = os.path.join(OUTPUT_DIR, 'london_6color_summary.csv')
OUT_CONF = os.path.join(OUTPUT_DIR, 'london_6color_confidence_summary.csv')
LOG_PATH = os.path.join(LOG_DIR, 'build.log')

CLASSES = {
    'Sanayi': '#F4C542',
    'Müstakil': '#A8E6A1',
    'Apartman': '#2E7D32',
    'Perakende': '#7FD3FF',
    'Ofis': '#1F4E9E',
    'Karma': '#8E44AD',
}
PRIORITY = ['Karma','Sanayi','Ofis','Perakende','Apartman','Müstakil']
KW = {
    'Sanayi': [r'\bfactory\b', r'\bindustrial\b', r'\bwarehouse\b', r'\bdepot\b', r'\bworkshop\b', r'\bplant\b', r'\bmanufactur(?:e|ing|er)\b', r'\blogistics\b', r'\bdistribution\b'],
    'Perakende': [r'\bretail\b', r'\bshop\b', r'\bshops\b', r'\bstore\b', r'\bsupermarket\b', r'\bmall\b', r'\bshopping\b', r'\bshowroom\b', r'\brestaurant\b', r'\bcafe\b'],
    'Ofis': [r'\boffice\b', r'\boffices\b', r'\bbusiness centre\b', r'\bbusiness center\b', r'\bcoworking\b', r'\bco-working\b', r'\bworkspace\b', r'\bstudio office\b'],
    'Apartman': [r'\bapartment\b', r'\bapartments\b', r'\bflat\b', r'\bflats\b', r'\bresidential\b', r'\bblock\b', r'\bmaisonette\b'],
    'Müstakil': [r'\bdetached\b', r'\bhouse\b', r'\bhouses\b', r'\bsemi-detached\b', r'\bsemi detached\b', r'\bterrace\b', r'\bterraced\b', r'\btownhouse\b'],
}
MIXED_STRONG = [
    r'\bshop(?:s)?\s+(?:below|beneath|under)\s+(?:flat|flats|residential|apartments)\b',
    r'\b(?:flat|flats|residential|apartments)\s+(?:above|over)\s+(?:shop|shops|retail|store)\b',
    r'\bresidential\s+(?:above|over)\s+retail\b',
    r'\bretail\s+(?:below|beneath|under)\s+residential\b',
    r'\bmixed[- ]use\s+(?:building|scheme|development|property|premises)\b',
    r'\bground\s+floor\s+(?:shop|retail|commercial).{0,80}\b(?:flat|flats|residential|apartment|apartments)\b',
]
RES_CLASSES = {'Apartman','Müstakil'}
MANUAL_FIELDS = {'manual_verified','manual_check','manual_validated','verified_manual','human_verified'}


def ensure_dirs():
    for p in (OUTPUT_DIR, LOG_DIR): os.makedirs(p, exist_ok=True)


def setup_logging():
    ensure_dirs()
    logging.basicConfig(filename=LOG_PATH, level=logging.INFO, filemode='a', format='%(asctime)s %(levelname)s %(message)s', encoding='utf-8')
    logging.getLogger().addHandler(logging.StreamHandler(sys.stdout))


def norm(v):
    if v is None: return ''
    if isinstance(v, float) and str(v) == 'nan': return ''
    return str(v).strip()


def text_of(*vals):
    return ' | '.join(norm(v) for v in vals if norm(v))


def find_col(cols, candidates):
    lower = {c.lower(): c for c in cols}
    for cand in candidates:
        if cand.lower() in lower: return lower[cand.lower()]
    for c in cols:
        lc = c.lower()
        for cand in candidates:
            if cand.lower() in lc: return c
    return None


def read_csv_rows(path):
    if not os.path.exists(path): return []
    try:
        try:
            import pandas as pd
        except Exception as e:
            raise RuntimeError('pandas gerekli. Kurulum: py -m pip install pandas') from e
        df = pd.read_csv(path, dtype=str, encoding='utf-8-sig').fillna('')
        return df.to_dict('records')
    except Exception:
        logging.exception('CSV okunamadı: %s', path)
        raise


def keyword_hits(txt):
    t = (txt or '').lower()
    hits = defaultdict(list)
    for cls, pats in KW.items():
        for pat in pats:
            if re.search(pat, t, flags=re.I): hits[cls].append(pat)
    return dict(hits)


def has_mixed_phrase(txt):
    t = (txt or '').lower()
    return any(re.search(p, t, flags=re.I | re.S) for p in MIXED_STRONG)


def source_signal(name, txt):
    hits = keyword_hits(txt)
    cats = set(hits)
    retail = 'Perakende' in cats
    residential = bool(cats & RES_CLASSES)
    mixed = has_mixed_phrase(txt) or (retail and residential and re.search(r'\b(above|over|below|beneath|under|ground floor|upper floor|mixed[- ]use)\b', (txt or '').lower()))
    strength = 'strong' if cats or mixed else 'none'
    if name == 'market' and re.search(r'\b(address|road|street|avenue|lane)\b', (txt or '').lower()) and len(cats) == 1:
        strength = 'weak'
    return {'source': name, 'categories': cats, 'retail': retail, 'residential': residential, 'mixed': bool(mixed), 'strength': strength, 'text_len': len(txt or '')}


def group_market(rows):
    by_ref, by_inspire = defaultdict(list), defaultdict(list)
    if not rows: return by_ref, by_inspire
    cols = list(rows[0].keys())
    ref_col = find_col(cols, ['matched_parcel_ref','parcel_ref'])
    insp_col = find_col(cols, ['matched_inspire_id','inspire_id'])
    txt_cols = [c for c in ['title','address_text','listing_status','description','summary'] if c in cols]
    for r in rows:
        txt = text_of(*(r.get(c,'') for c in txt_cols))
        if ref_col and norm(r.get(ref_col)): by_ref[norm(r.get(ref_col))].append(txt)
        if insp_col and norm(r.get(insp_col)): by_inspire[norm(r.get(insp_col))].append(txt)
    return by_ref, by_inspire


def group_voa(rows):
    by_ref, by_inspire = defaultdict(list), defaultdict(list)
    meta = {'loaded': bool(rows), 'matched_by': []}
    if not rows: return by_ref, by_inspire, meta
    cols = list(rows[0].keys())
    ref_col = find_col(cols, ['matched_parcel_ref','parcel_ref'])
    insp_col = find_col(cols, ['matched_inspire_id','inspire_id'])
    text_like = [c for c in cols if any(k in c.lower() for k in ['desc','description','business','trade','category','use','class','text','name'])]
    if not text_like: text_like = cols[:8]
    for r in rows:
        txt = text_of(*(r.get(c,'') for c in text_like))
        if ref_col and norm(r.get(ref_col)):
            by_ref[norm(r.get(ref_col))].append(txt); meta['matched_by'].append(ref_col)
        if insp_col and norm(r.get(insp_col)):
            by_inspire[norm(r.get(insp_col))].append(txt); meta['matched_by'].append(insp_col)
    meta['matched_by'] = sorted(set(meta['matched_by']))
    return by_ref, by_inspire, meta


def choose_class(signals):
    retail_sources = {s['source'] for s in signals if s['retail']}
    res_sources = {s['source'] for s in signals if s['residential']}
    explicit_mixed = any(s['mixed'] for s in signals)
    cats_by_source = defaultdict(set)
    for s in signals:
        for c in s['categories']: cats_by_source[c].add(s['source'])
    if explicit_mixed or (retail_sources and res_sources and len(retail_sources | res_sources) >= 2):
        return 'Karma', 'mixed: residential + retail signal'
    for c in PRIORITY[1:]:
        if cats_by_source.get(c): return c, c + ' signal'
    return 'Müstakil', 'fallback'


def confidence(chosen, signals, props):
    for k in MANUAL_FIELDS:
        if norm(props.get(k)).lower() in {'1','true','yes','y','manual','verified'}:
            return 6, 'manual verified flag'
    if not signals or all(s['strength'] == 'none' for s in signals):
        return 1, 'sadece fallback'
    supportive = []
    for s in signals:
        if chosen == 'Karma':
            ok = s['mixed'] or s['retail'] or s['residential']
        else:
            ok = chosen in s['categories']
        if ok and s['strength'] != 'none': supportive.append(s)
    independent = {s['source'] for s in supportive}
    strong = any(s['strength'] == 'strong' for s in supportive)
    if len(independent) >= 3: return 5, 'üç+ kaynak uyumlu'
    if len(independent) >= 2: return 4, 'iki bağımsız kaynak uyumlu'
    if strong: return 3, 'tek güçlü sinyal'
    return 2, 'tek zayıf sinyal'


def existing_confidence_boost(score, props):
    raw = norm(props.get('confidence_level_1_4') or props.get('confidence') or props.get('confidence_score'))
    try: old = int(float(raw))
    except Exception: return score
    if old >= 4 and score < 3: return 3
    if old >= 3 and score < 2: return 2
    return score


def main():
    setup_logging()
    logging.info('PLAN_L_BASE_DIR=%s', BASE_DIR)
    if not os.path.exists(GEOJSON_PATH): raise FileNotFoundError(GEOJSON_PATH)
    if not os.path.exists(MARKET_PATH): raise FileNotFoundError(MARKET_PATH)
    market_rows = read_csv_rows(MARKET_PATH)
    voa_rows = read_csv_rows(VOA_PATH) if os.path.exists(VOA_PATH) else []
    if not voa_rows: logging.info('VOA yok veya boş; atlanıyor: %s', VOA_PATH)
    market_by_ref, market_by_inspire = group_market(market_rows)
    voa_by_ref, voa_by_inspire, voa_meta = group_voa(voa_rows)
    with open(GEOJSON_PATH, 'r', encoding='utf-8-sig') as f: gj = json.load(f)
    features = gj.get('features', [])
    rows = []
    class_counts, conf_counts = Counter(), Counter()
    for idx, feat in enumerate(features):
        props = feat.setdefault('properties', {})
        parcel_ref = norm(props.get('parcel_ref') or props.get('matched_parcel_ref') or props.get('id'))
        inspire = norm(props.get('inspire_id') or props.get('matched_inspire_id') or props.get('INSPIREID'))
        geo_txt = text_of(props.get('recommended_class'), props.get('recommended_use6'), props.get('use'), props.get('class'), props.get('description'), props.get('local_authority'))
        signals = []
        sg = source_signal('geojson', geo_txt)
        if sg['strength'] != 'none': signals.append(sg)
        market_txt = text_of(*market_by_ref.get(parcel_ref, []), *market_by_inspire.get(inspire, []))
        sm = source_signal('market_3110', market_txt)
        if sm['strength'] != 'none': signals.append(sm)
        voa_txt = text_of(*voa_by_ref.get(parcel_ref, []), *voa_by_inspire.get(inspire, []))
        sv = source_signal('voa_london', voa_txt)
        if sv['strength'] != 'none': signals.append(sv)
        chosen, reason = choose_class(signals)
        score, score_reason = confidence(chosen, signals, props)
        score = existing_confidence_boost(score, props)
        color = CLASSES[chosen]
        source_names = sorted({s['source'] for s in signals})
        props['use6_class'] = chosen
        props['use6_color'] = color
        props['use6_confidence'] = int(score)
        props['use6_confidence_reason'] = score_reason
        props['use6_decision_reason'] = reason
        props['use6_sources'] = ';'.join(source_names) if source_names else 'fallback'
        props['use6_generated_at'] = datetime.utcnow().isoformat(timespec='seconds') + 'Z'
        class_counts[chosen] += 1; conf_counts[int(score)] += 1
        rows.append({
            'row_index': idx,
            'parcel_ref': parcel_ref,
            'matched_inspire_id': inspire,
            'local_authority': norm(props.get('local_authority')),
            'area_m2': norm(props.get('area_m2')),
            'use6_class': chosen,
            'use6_color': color,
            'use6_confidence': int(score),
            'use6_sources': props['use6_sources'],
            'use6_decision_reason': reason,
            'use6_confidence_reason': score_reason,
        })
    ensure_dirs()
    with open(OUT_GEOJSON, 'w', encoding='utf-8') as f: json.dump(gj, f, ensure_ascii=False, separators=(',', ':'))
    fieldnames = list(rows[0].keys()) if rows else ['row_index','parcel_ref','use6_class','use6_color','use6_confidence']
    with open(OUT_CSV, 'w', encoding='utf-8-sig', newline='') as f:
        w = csv.DictWriter(f, fieldnames=fieldnames); w.writeheader(); w.writerows(rows)
    with open(OUT_SUMMARY, 'w', encoding='utf-8-sig', newline='') as f:
        w = csv.DictWriter(f, fieldnames=['class','color','count']); w.writeheader()
        for c in PRIORITY: w.writerow({'class': c, 'color': CLASSES[c], 'count': class_counts.get(c,0)})
    with open(OUT_CONF, 'w', encoding='utf-8-sig', newline='') as f:
        w = csv.DictWriter(f, fieldnames=['confidence','count']); w.writeheader()
        for k in range(1,7): w.writerow({'confidence': k, 'count': conf_counts.get(k,0)})
    logging.info('DONE features=%s classes=%s confidence=%s voa_meta=%s', len(features), dict(class_counts), dict(conf_counts), voa_meta)
    print('RESULT=ok')
    print('FEATURES=%d' % len(features))
    print('SUMMARY=%s' % OUT_SUMMARY)
    print('CONFIDENCE_SUMMARY=%s' % OUT_CONF)

if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        ensure_dirs(); setup_logging(); logging.exception('FAILED')
        print('RESULT=failed')
        print('ERROR=' + str(e))
        sys.exit(1)
