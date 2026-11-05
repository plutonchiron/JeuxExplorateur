#!/usr/bin/env python3
"""data/capitales.json : { code ISO3 du pays : capitale } pour le quiz « Capitales du monde » (page capitales.html).

Source : data/info-pays.json (capitales de Wikidata, voir scripts/build-info.py) ; on y applique des corrections et on écarte
les pays qui ne conviennent pas à un quiz pour enfants.
À relancer seulement si on change ces règles ou info-pays.json :   python3 scripts/build-capitales.py && npm run build
Python 3, aucune dépendance, hors ligne.
"""
import json, os

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
load = lambda p: json.load(open(os.path.join(ROOT, p), encoding='utf8'))
info, data = load('data/info-pays.json'), load('data/data.json')['countries']

# Pays à plusieurs capitales : on garde celle qu'on enseigne en premier.
CORRECTIONS = {'ZAF': 'Pretoria', 'SWZ': 'Mbabane'}
# Écartés : la capitale porte exactement le nom du pays (la réponse serait donnée), ou la capitale est disputée / double.
ECARTES = {
    'VAT': 'même nom', 'SGP': 'même nom', 'SMR': 'même nom', 'MCO': 'même nom', 'LUX': 'même nom',
    'KWT': 'même nom', 'DJI': 'même nom', 'GTM': 'même nom', 'PAN': 'même nom',
    'BOL': 'deux capitales (Sucre et La Paz)', 'ISR': 'capitale disputée',
}
out = {}
for code, c in data.items():
    if not c.get('t') or code in ECARTES: continue
    cap = CORRECTIONS.get(code) or info.get(code, {}).get('cap')
    if cap: out[code] = cap
json.dump(out, open(os.path.join(ROOT, 'data/capitales.json'), 'w', encoding='utf8'), ensure_ascii=False, separators=(',', ':'), sort_keys=True)
print('data/capitales.json :', len(out), 'capitales | écartés :', ', '.join(sorted(ECARTES)))
