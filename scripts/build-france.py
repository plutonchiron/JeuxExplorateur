#!/usr/bin/env python3
"""Génère les données de la carte « Villes de France » (96 départements de métropole).

  data/france-paths.frag : un <path class="c {zone}" data-c="{code département}" d="…"/> par département
  data/france.json       : { countries: {code: {n: département, r: zone, a: surface en px², t: 1}},
                             zones: {zone: [x0, y0, x1, y1]}, box: [x0, y0, x1, y1] }
  (même structure que data/data.json : le jeu réutilise tout le code de Géo Explorateurs)

Source des contours : https://github.com/gregoiredavid/france-geojson (données IGN, Licence Ouverte Etalab).
À relancer seulement si on change la carte, les villes ou les zones :   python3 scripts/build-france.py && npm run build
Nécessite Internet (téléchargement du fichier des départements) et Python 3, sans module à installer.
"""
import json, math, os, sys, urllib.request

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
URL = 'https://raw.githubusercontent.com/gregoiredavid/france-geojson/master/departements-version-simplifiee.geojson'
K = 95            # pixels du repère SVG par degré de latitude
TOL = 0.45        # tolérance de simplification (px)
MINPOLY = 0.4     # surface minimale (px²) d'un îlot dessiné

# Codes des 96 départements de métropole
CODES = '01 02 03 04 05 06 07 08 09 10 11 12 13 14 15 16 17 18 19 21 22 23 24 25 26 27 28 29 2A 2B 30 31 32 33 34 35 36 37 38 39 40 41 42 43 44 45 46 47 48 49 50 51 52 53 54 55 56 57 58 59 60 61 62 63 64 65 66 67 68 69 70 71 72 73 74 75 76 77 78 79 80 81 82 83 84 85 86 87 88 89 90 91 92 93 94 95'.split()
# Couleur des départements (regroupement des 13 régions en 4 quarts de la France) ; la lettre est la classe CSS (E violet, A jaune, F orange, M vert)
ZONES = {
 'E': '22 29 35 56 14 27 50 61 76 44 49 53 72 85 18 28 36 37 41 45',                      # Nord-Ouest
 'A': '02 59 60 62 80 75 77 78 91 92 93 94 95 08 10 51 52 54 55 57 67 68 88 21 25 39 58 70 71 89 90',   # Nord-Est
 'F': '16 17 19 23 24 33 40 47 64 79 86 87 09 11 12 30 31 32 34 46 48 65 66 81 82',       # Sud-Ouest
 'M': '01 03 07 15 26 38 42 43 63 69 73 74 04 05 06 13 83 84 2A 2B',                      # Sud-Est
}
ZONE_OF = {c: z for z, cs in ZONES.items() for c in cs.split()}

def project(lon, lat):
    return ((lon + 5.3) * math.cos(math.radians(46.6)) * K, (51.2 - lat) * K)

def rdp(pts, tol):
    if len(pts) < 3: return pts
    keep = [False] * len(pts); keep[0] = keep[-1] = True
    stack = [(0, len(pts) - 1)]
    while stack:
        a, b = stack.pop()
        (x1, y1), (x2, y2) = pts[a], pts[b]
        dx, dy = x2 - x1, y2 - y1; n = math.hypot(dx, dy) or 1e-9
        best, bi = 0, -1
        for i in range(a + 1, b):
            d = abs(dy * pts[i][0] - dx * pts[i][1] + x2 * y1 - y2 * x1) / n
            if d > best: best, bi = d, i
        if best > tol and bi > 0:
            keep[bi] = True; stack += [(a, bi), (bi, b)]
    return [p for p, k in zip(pts, keep) if k]

def area(ring):
    return abs(sum(ring[i][0] * ring[(i + 1) % len(ring)][1] - ring[(i + 1) % len(ring)][0] * ring[i][1] for i in range(len(ring)))) / 2

def main():
    with urllib.request.urlopen(URL, timeout=60) as r: geo = json.load(r)
    feats = {f['properties']['code']: f for f in geo['features'] if f['properties']['code'] in CODES}
    missing = sorted(set(CODES) - set(feats))
    if missing: sys.exit('Départements absents du fichier : ' + ', '.join(missing))
    countries, paths, boxes = {}, '', {}
    for code in sorted(CODES):
        f = feats[code]
        polys = f['geometry']['coordinates'] if f['geometry']['type'] == 'MultiPolygon' else [f['geometry']['coordinates']]
        proj = [[[project(lo, la) for lo, la in ring[:-1]] for ring in poly] for poly in polys]   # [polygone][anneau][point]
        biggest = max(area(p[0]) for p in proj)
        d, total, xs, ys = '', 0, [], []
        for poly in proj:
            a = area(poly[0])
            if a < MINPOLY and a != biggest: continue
            total += a - sum(area(h) for h in poly[1:])
            for ring in poly:
                m = max(range(len(ring)), key=lambda i: math.hypot(ring[i][0] - ring[0][0], ring[i][1] - ring[0][1]))   # anneau fermé : on le coupe en deux
                s = rdp(ring[:m + 1], TOL)[:-1] + rdp(ring[m:] + [ring[0]], TOL)[:-1]
                if len(s) < 3: continue
                d += 'M' + 'L'.join('%.1f,%.1f' % p for p in s) + 'Z'
                xs += [p[0] for p in s]; ys += [p[1] for p in s]
        z = ZONE_OF[code]
        countries[code] = {'n': f['properties']['nom'], 'r': z, 'a': round(total, 2), 't': 1}
        boxes[code] = (min(xs), min(ys), max(xs), max(ys))
        paths += '<path class="c %s" data-c="%s" d="%s" fill-rule="evenodd"/>\n' % (z, code, d)
    def bbox(codes):
        b = [boxes[c] for c in codes]
        return [round(v, 1) for v in (min(x[0] for x in b), min(x[1] for x in b), max(x[2] for x in b), max(x[3] for x in b))]
    zones = {'france': bbox(CODES)}                  # on joue toujours sur toute la carte
    box = bbox(CODES)
    # Contrôle des noms et codes avec la liste officielle (API Géo de l'État, d'après le COG de l'INSEE)
    try:
        with urllib.request.urlopen('https://geo.api.gouv.fr/departements?fields=nom,code', timeout=30) as r:
            off = {d['code']: d['nom'] for d in json.load(r)}
        for code, c in countries.items():
            if off.get(code) != c['n']: print('! nom différent de la source officielle pour', code, ':', c['n'], '≠', off.get(code))
        print('Noms comparés à geo.api.gouv.fr :', sum(1 for c, v in countries.items() if off.get(c) == v['n']), '/', len(countries), 'identiques')
    except Exception as e:
        print('(contrôle des noms ignoré :', e, ')')
    with open(os.path.join(ROOT, 'data/france-paths.frag'), 'w', encoding='utf8') as fh: fh.write(paths)
    with open(os.path.join(ROOT, 'data/france.json'), 'w', encoding='utf8') as fh:
        json.dump({'countries': countries, 'zones': zones, 'box': box}, fh, ensure_ascii=False, separators=(',', ':'))
    print('Départements :', len(countries), '| data/france-paths.frag :', len(paths) // 1024, 'Ko | zone France :', zones['france'])

main()
