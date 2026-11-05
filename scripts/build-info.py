#!/usr/bin/env python3
"""Rassemble les fiches du mode exploration (données de Wikidata, en français) dans data/ :

  data/info-pays.json         : { code ISO3 : {cap: capitale, pop: habitants, area: km², lang: [langues], cur: [monnaies], nb: [codes ISO3 des voisins], fact: « Le savais-tu ? »} }
  data/info-departements.json : { code département : {pref: préfecture, reg: région, pop: habitants, area: km², nb: [codes des voisins], fact: …} }

Les phrases « Le savais-tu ? » sont écrites à la main dans data/faits-pays.json et data/faits-departements.json (non générés).
À relancer seulement pour actualiser les chiffres :   python3 scripts/build-info.py && npm run build
Nécessite Internet et Python 3 (aucun module). Les photos sont gérées par scripts/build-media.py.
"""
import json, os, sys, time, urllib.parse, urllib.request

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
UA = {'User-Agent': 'JeuxExplorateurs/1.0 (jeu educatif hors ligne; contact: plutonmail35@gmail.com)', 'Accept': 'application/sparql-results+json'}
load = lambda p: json.load(open(os.path.join(ROOT, p), encoding='utf8'))

def sparql(q, tries=4):
    url = 'https://query.wikidata.org/sparql?' + urllib.parse.urlencode({'query': q})
    for i in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=120) as r:
                return [{k: v['value'] for k, v in b.items()} for b in json.load(r)['results']['bindings']]
        except Exception as e:
            if i == tries - 1: raise
            time.sleep(5 + 5 * i)

FR = 'FILTER(lang(?%s)="fr")'

# ---------- Pays ----------
def pays():
    targets = [k for k, v in load('data/data.json')['countries'].items() if v['t']]
    base = {r['iso3']: r for r in sparql('''SELECT ?iso3 (SAMPLE(?capL) AS ?cap) (SAMPLE(?pop) AS ?p) (SAMPLE(?ar) AS ?a) WHERE {
      ?c wdt:P31 wd:Q3624078; wdt:P298 ?iso3.
      OPTIONAL{?c wdt:P36 ?cp. ?cp rdfs:label ?capL. %s} OPTIONAL{?c wdt:P1082 ?pop} OPTIONAL{?c wdt:P2046 ?ar} } GROUP BY ?iso3''' % (FR % 'capL'))}
    def multi(prop, var):
        rows = sparql('''SELECT ?iso3 (GROUP_CONCAT(DISTINCT ?l; separator="|") AS ?ls) WHERE {
          ?c wdt:P31 wd:Q3624078; wdt:P298 ?iso3. ?c wdt:%s ?x. ?x rdfs:label ?l. %s } GROUP BY ?iso3''' % (prop, FR % 'l'))
        return {r['iso3']: [x for x in r['ls'].split('|') if x] for r in rows}
    mled = {c['cca3']: c for c in json.loads(urllib.request.urlopen(urllib.request.Request(
        'https://raw.githubusercontent.com/mledoze/countries/master/countries.json', headers=UA), timeout=60).read())}
    # Langues officielles et monnaies : codes de mledoze/countries (fiables, sans les territoires), noms français de Wikidata
    def labels(prop, codes):
        vals = ' '.join('"%s"' % c for c in sorted(codes))
        rows = sparql('SELECT ?code (SAMPLE(?l) AS ?lab) WHERE { VALUES ?code { %s } ?x wdt:%s ?code. ?x rdfs:label ?l. %s } GROUP BY ?code' % (vals, prop, FR % 'l'))
        return {r['code']: r['lab'] for r in rows}
    lcodes = {c for m in mled.values() for c in m.get('languages', {})}
    ccodes = {c for m in mled.values() for c in m.get('currencies', {})}
    llab, clab = labels('P220', lcodes), labels('P498', ccodes)
    faits = load('data/faits-pays.json') if os.path.exists(os.path.join(ROOT, 'data/faits-pays.json')) else {}
    over = load('data/corrections-pays.json') if os.path.exists(os.path.join(ROOT, 'data/corrections-pays.json')) else {}
    out, missing = {}, []
    for code in sorted(targets):
        b, m = base.get(code, {}), mled.get(code, {})
        e = {}
        if b.get('cap'): e['cap'] = b['cap']
        if b.get('p'): e['pop'] = int(float(b['p']))
        area = float(b['a']) if b.get('a') else m.get('area')
        if area: e['area'] = int(round(float(area)))
        if m.get('languages'): e['lang'] = [llab.get(c) or n for c, n in m['languages'].items()]
        if m.get('currencies'): e['cur'] = [clab.get(c) or v.get('name', c) for c, v in m['currencies'].items()]
        e['nb'] = [x for x in m.get('borders', []) if x in targets]
        if faits.get(code): e['fact'] = faits[code]
        e.update(over.get(code, {}))
        out[code] = e
        for k in ('cap', 'pop', 'area', 'lang', 'cur'):
            if k not in e: missing.append(code + ':' + k)
    json.dump(out, open(os.path.join(ROOT, 'data/info-pays.json'), 'w', encoding='utf8'), ensure_ascii=False, separators=(',', ':'))
    print('Pays :', len(out), '| manquants :', missing, '| data/info-pays.json', os.path.getsize(os.path.join(ROOT, 'data/info-pays.json')) // 1024, 'Ko')

# ---------- Départements ----------
def departements():
    rows = sparql('''SELECT ?code (SAMPLE(?prefL) AS ?pref) (SAMPLE(?regL) AS ?reg) (SAMPLE(?pop) AS ?p) (SAMPLE(?ar) AS ?a) WHERE {
      ?d wdt:P31 wd:Q6465; wdt:P2586 ?code. FILTER NOT EXISTS {?d wdt:P576 ?fin}
      OPTIONAL{?d wdt:P36 ?pf. ?pf rdfs:label ?prefL. %s}
      OPTIONAL{?d wdt:P131 ?rg. ?rg rdfs:label ?regL. %s}
      OPTIONAL{?d wdt:P1082 ?pop} OPTIONAL{?d wdt:P2046 ?ar} } GROUP BY ?code''' % (FR % 'prefL', FR % 'regL'))
    nbrows = sparql('''SELECT ?code (GROUP_CONCAT(DISTINCT ?c2; separator="|") AS ?nb) WHERE {
      ?d wdt:P31 wd:Q6465; wdt:P2586 ?code. FILTER NOT EXISTS {?d wdt:P576 ?fin}
      ?d wdt:P47 ?n. ?n wdt:P31 wd:Q6465; wdt:P2586 ?c2. } GROUP BY ?code''')
    nbs = {r['code']: [x for x in r['nb'].split('|') if x] for r in nbrows}
    targets = list(load('data/france.json')['countries'])
    faits = load('data/faits-departements.json') if os.path.exists(os.path.join(ROOT, 'data/faits-departements.json')) else {}
    over = load('data/corrections-departements.json') if os.path.exists(os.path.join(ROOT, 'data/corrections-departements.json')) else {}
    by = {r['code']: r for r in rows}
    out, missing = {}, []
    for code in sorted(targets):
        r = by.get(code, {}); e = {}
        if r.get('pref'): e['pref'] = r['pref']
        if r.get('reg'): e['reg'] = r['reg']
        if r.get('p'): e['pop'] = int(float(r['p']))
        if r.get('a'): e['area'] = int(round(float(r['a'])))
        e['nb'] = sorted(x for x in nbs.get(code, []) if x in targets)
        if faits.get(code): e['fact'] = faits[code]
        e.update(over.get(code, {}))
        out[code] = e
        for k in ('pref', 'reg', 'pop', 'area'):
            if k not in e: missing.append(code + ':' + k)
    for a, e in list(out.items()):                  # voisinage symétrique (Wikidata ne le renseigne pas toujours dans les deux sens)
        for b in e['nb']:
            if a not in out[b]['nb']: out[b]['nb'] = sorted(out[b]['nb'] + [a])
    json.dump(out, open(os.path.join(ROOT, 'data/info-departements.json'), 'w', encoding='utf8'), ensure_ascii=False, separators=(',', ':'))
    print('Départements :', len(out), '| manquants :', missing, '| data/info-departements.json', os.path.getsize(os.path.join(ROOT, 'data/info-departements.json')) // 1024, 'Ko')

if __name__ == '__main__':
    what = sys.argv[1:] or ['pays', 'departements']
    if 'pays' in what: pays()
    if 'departements' in what: departements()
