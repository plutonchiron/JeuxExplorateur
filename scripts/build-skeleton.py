#!/usr/bin/env python3
"""Dessine le squelette du jeu « Le squelette » (Python 3, aucune dépendance, hors ligne), style dessin animé :
gros crâne rond, grands yeux, sourire, contours épais brun foncé, aplats crème, un bras qui salue.

  data/skeleton-paths.frag : un <path class="c bone" data-c> par os (forme cliquable ; fond crème et contour réglés dans styles.css, `.c.bone`)
                             + des groupes .deco (yeux, sourire, mains, trous du bassin…) ; le groupe qui suit l'os cliqué est estompé par le jeu
  data/skeleton.json       : { countries: {code: {n: nom avec article, r: groupe de difficulté A/B/C, a, t}}, zones, box }
                             (même structure que data/body.json : le jeu réutilise le moteur de la carte)

À relancer après une retouche du dessin :   python3 scripts/build-skeleton.py && npm run build
Repère : 400 × 600, squelette centré sur x = 200. Les os pairs sont dessinés d'un côté puis reflétés ; les bras sont dessinés à la main (un bras salue).
Groupes d'os : A = Découverte, B = + Super, C = + Champion.
"""
import json, math, os, re

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
CREAM, LINE, TAN = '#F8E1C3', '#4B1E1E', '#D9B48C'     # même crème et même contour que `.c.bone` dans styles.css

def P(d, fill='none', stroke=None, w=2.8):
    s = '<path d="%s" fill="%s"' % (d, fill)
    if stroke: s += ' stroke="%s" stroke-width="%s" stroke-linecap="round" stroke-linejoin="round"' % (stroke, w)
    return s + '/>\n'
def E(cx, cy, rx, ry, fill, stroke=None, w=2.8, rot=None):
    s = '<ellipse cx="%s" cy="%s" rx="%s" ry="%s" fill="%s"' % (round(cx, 1), round(cy, 1), rx, ry, fill)
    if stroke: s += ' stroke="%s" stroke-width="%s"' % (stroke, w)
    if rot: s += ' transform="rotate(%s %s %s)"' % (rot, round(cx, 1), round(cy, 1))
    return s + '/>\n'
def D(d): return P(d, CREAM, LINE)                     # pièce de décor dessinée comme un os (mains)
def mirror(d):
    """Symétrique par rapport à x = 200 (chemins absolus M L C Q Z)."""
    out, nums = [], 0
    for tok in re.findall(r'[MLCQZ]|-?\d+\.?\d*', d):
        if tok.isalpha(): out.append(tok); nums = 0
        else: out.append(('%g' % (400 - float(tok))) if nums % 2 == 0 else tok); nums += 1
    return ' '.join(out)

def poly(pts): return 'M' + ' L'.join('%.1f %.1f' % p for p in pts) + ' Z'
def bonec(c, shaft, e0, e1, sig=None, n=60):
    """Os long de dessin animé : courbe de Bézier c = [p0,p1,p2,p3] ; tige de largeur `shaft`, bouts arrondis de diamètre e0 / e1."""
    def at(t):
        u = 1 - t
        return (u**3 * c[0][0] + 3 * u * u * t * c[1][0] + 3 * u * t * t * c[2][0] + t**3 * c[3][0],
                u**3 * c[0][1] + 3 * u * u * t * c[1][1] + 3 * u * t * t * c[2][1] + t**3 * c[3][1])
    ts = [(1 - math.cos(math.pi * i / n)) / 2 for i in range(n + 1)]       # échantillons plus serrés aux extrémités
    mid = [at(t) for t in ts]; cum = [0]
    for i in range(1, len(mid)): cum.append(cum[-1] + math.hypot(mid[i][0] - mid[i - 1][0], mid[i][1] - mid[i - 1][1]))
    tot = cum[-1]; L, Rr = [], []
    def knob(sd, d):                                                         # largeur d'un bout rond de diamètre d à la distance sd du bout
        r = d / 2
        return 2 * math.sqrt(max(0, r * r - (r - sd) ** 2)) if sd < 2 * r else 0
    for i, t in enumerate(ts):
        x, y = mid[i]; x2, y2 = at(min(1, t + .005)); x1, y1 = at(max(0, t - .005))
        dx, dy = x2 - x1, y2 - y1; ln = math.hypot(dx, dy) or 1; nx, ny = -dy / ln, dx / ln
        w = max(shaft if 0 < cum[i] < tot else 0, knob(cum[i], e0), knob(tot - cum[i], e1), shaft * .999 if 0 < cum[i] < tot else 0)
        L.append((x + nx * w / 2, y + ny * w / 2)); Rr.append((x - nx * w / 2, y - ny * w / 2))
    return poly(L + Rr[::-1])
def bone(p0, p1, shaft, e0, e1, bow=0, sig=.14):
    dx, dy = p1[0] - p0[0], p1[1] - p0[1]; ln = math.hypot(dx, dy); nx, ny = -dy / ln, dx / ln
    return bonec([p0, (p0[0] + dx / 3 + nx * bow, p0[1] + dy / 3 + ny * bow), (p0[0] + 2 * dx / 3 + nx * bow, p0[1] + 2 * dy / 3 + ny * bow), p1], shaft, e0, e1, sig)
def caps(p0, p1, w):
    """Capsule (doigt) : rectangle aux bouts ronds."""
    a = math.atan2(p1[1] - p0[1], p1[0] - p0[0]); r = w / 2; pts = []
    for k in range(9): pts.append((p1[0] + r * math.cos(a - math.pi / 2 + math.pi * k / 8), p1[1] + r * math.sin(a - math.pi / 2 + math.pi * k / 8)))
    for k in range(9): pts.append((p0[0] + r * math.cos(a + math.pi / 2 + math.pi * k / 8), p0[1] + r * math.sin(a + math.pi / 2 + math.pi * k / 8)))
    return poly(pts)
def hand(cx, cy, ang):
    """Main ouverte de dessin animé : 4 doigts + pouce + paume ; ang = direction des doigts (degrés, 0 = droite, 90 = bas)."""
    s = ''; a = math.radians(ang); dx, dy = math.cos(a), math.sin(a); nx, ny = -dy, dx
    for off, ln in ((-9, 17), (-3, 20), (3, 19), (9, 15)):
        bx, by = cx + nx * off + dx * 8, cy + ny * off + dy * 8
        fa = a + math.radians(off * 1.6)
        s += D(caps((bx, by), (bx + math.cos(fa) * ln, by + math.sin(fa) * ln), 7.4))
    tb = (cx + nx * -13, cy + ny * -13)
    s += D(caps(tb, (tb[0] + math.cos(a - .9) * 13, tb[1] + math.sin(a - .9) * 13), 7.4))
    s += E(cx, cy, 14, 12, CREAM, LINE, 2.8, rot=ang + 90)
    return s

# ------------------------------------------------------------------ os : code -> chemins cliquables
BONES = {}
def add(code, d): BONES.setdefault(code, []).append(d)
def add_pair(code, d): add(code, d); add(code, mirror(d))

# --- tête
add('crane', 'M200 12 C252 12 284 44 284 86 C284 112 270 132 250 142 L250 152 L150 152 L150 142 C130 132 116 112 116 86 C116 44 148 12 200 12Z')
add('machoire', 'M154 148 L246 148 L244 168 C242 180 226 186 200 186 C174 186 158 180 156 168Z')
# --- colonne vertébrale : 3 cervicales (sous la mâchoire), 6 dorsales (cachées derrière le sternum), 4 lombaires
def vert(y, w, h):
    return poly([(200 - w / 2 + 2, y), (200 + w / 2 - 2, y), (200 + w / 2 + 2, y + h * .3), (200 + w / 2 + 2, y + h * .7), (200 + w / 2 - 2, y + h), (200 - w / 2 + 2, y + h), (200 - w / 2 - 2, y + h * .7), (200 - w / 2 - 2, y + h * .3)])
for y in (188, 198, 208): add('colonne', vert(y, 22, 9))
for k in range(6): add('colonne', vert(216 + k * 14, 28, 12))
for k in range(4): add('colonne', vert(302 + k * 12, 30, 11))
# --- côtes : 4 paires de grosses côtes arrondies
for yb, xm in ((232, 44), (251, 54), (270, 56), (289, 48)):
    cx = 200 + xm * 1.3
    add_pair('cotes', bonec([(196, yb), (cx, yb - 6), (cx, yb + 26), (196, yb + 16)], 11.5, 12, 12, n=40))
# --- sternum et clavicules
add('sternum', 'M190 224 C190 214 210 214 210 224 L210 294 C210 308 190 308 190 294Z')
add_pair('clavicule', bonec([(207, 224), (182, 214), (156, 218), (128, 209)], 12, 20, 24))
# --- bras qui salue (côté gauche du dessin) : humérus, avant-bras (radius + cubitus) levé
add('humerus', bone((126, 224), (72, 258), 16, 27, 30, bow=-3))
add('radius', bone((69, 254), (38, 192), 11, 19, 19, bow=2))
add('cubitus', bone((76, 262), (56, 198), 11, 21, 15, bow=-2))
# --- bras qui pend (côté droit du dessin)
add('humerus', bone((276, 226), (298, 292), 16, 27, 30, bow=-2))
add('radius', bone((304, 296), (316, 376), 11, 19, 19, bow=1))
add('cubitus', bone((292, 298), (300, 376), 11, 21, 15, bow=-1))
# --- bassin (deux trous dessinés par-dessus)
add('bassin', 'M118 346 C128 334 168 336 200 352 C232 336 272 334 282 346 C292 362 276 388 250 390 C230 392 214 382 200 372 C186 382 170 392 150 390 C124 388 108 362 118 346Z')
# --- jambes (jambe gauche du dessin, puis reflet)
add_pair('femur', bone((160, 382), (149, 462), 17, 31, 32, bow=-3))
add_pair('tibia', bone((150, 466), (151, 552), 16, 29, 29, bow=0))
add_pair('perone', bone((132, 474), (133, 548), 9, 16, 16, bow=0))
add_pair('rotule', 'M150 448 C138 448 136 470 150 474 C164 470 162 448 150 448Z')
add_pair('pied', 'M122 554 C122 541 166 540 176 554 L184 576 C185 586 176 590 166 590 L126 590 C117 590 114 580 120 572Z')

NAMES = {
 'crane': ('le crâne', 'A'), 'colonne': ('la colonne vertébrale', 'A'), 'cotes': ('les côtes', 'A'), 'bassin': ('le bassin', 'A'),
 'humerus': ('l’humérus', 'A'), 'femur': ('le fémur', 'A'),
 'clavicule': ('la clavicule', 'B'), 'rotule': ('la rotule', 'B'), 'tibia': ('le tibia', 'B'), 'cubitus': ('le cubitus', 'B'),
 'radius': ('le radius', 'C'), 'perone': ('le péroné', 'C'), 'sternum': ('le sternum', 'C'), 'machoire': ('la mâchoire', 'C'), 'pied': ('les os du pied', 'C'),
}
# ordre de superposition (du fond vers le devant)
ORDER = ['cotes', 'humerus', 'radius', 'cubitus', 'femur', 'tibia', 'perone', 'pied', 'colonne', 'bassin', 'sternum', 'clavicule', 'crane', 'machoire', 'rotule']

# ------------------------------------------------------------------ décor : traits dessinés par-dessus certains os
smile = P('M162 146 C178 160 222 160 238 146', 'none', LINE, 3.2)
for x in range(172, 232, 8): smile += P('M%d %.1f L%d %.1f' % (x, 146 + 10.5 * (1 - ((x - 200) / 38) ** 2) - 6, x, 146 + 10.5 * (1 - ((x - 200) / 38) ** 2) + 7), 'none', LINE, 2.6)
DECO = {
    'crane': E(164, 88, 18, 18, LINE) + E(236, 88, 18, 18, LINE) + P('M200 110 C192 110 189 123 196 129 L204 129 C211 123 208 110 200 110Z', LINE)
             + P('M124 102 C126 118 138 130 152 138 M276 102 C274 118 262 130 248 138', 'none', TAN, 3),
    'machoire': smile,
    'bassin': E(158, 362, 15, 10, CREAM, LINE, 2.8, rot=-12) + E(242, 362, 15, 10, CREAM, LINE, 2.8, rot=12),
    'sternum': P('M200 226 L200 292', 'none', TAN, 3) + P('M193 244 L207 244 M193 262 L207 262 M193 280 L207 280', 'none', TAN, 2.6),
    'pied': ''.join(P('M%d 580 L%d 590' % (x, x), 'none', LINE, 2.4) for x in (134, 144, 154, 164, 266, 256, 246, 236)),
}
AFTER = {'cubitus': hand(38, 178, -112) + hand(318, 396, 96)}      # mains : groupe à part, jamais estompé

# ------------------------------------------------------------------ assemblage
frag = ''
countries = {}
for code in ORDER:
    name, grp = NAMES[code]
    countries[code] = {'n': name, 'r': grp, 'a': 1000, 't': 1}
    for d in BONES[code]: frag += '<path class="c bone" data-c="%s" d="%s"/>\n' % (code, d)
    frag += '<g class="deco">\n' + DECO.get(code, '') + '</g>\n'
    if code in AFTER: frag += '<g class="deco keep">\n' + AFTER[code] + '</g>\n'
open(os.path.join(ROOT, 'data/skeleton-paths.frag'), 'w', encoding='utf8').write(frag)
zb = [10, 0, 390, 598]
json.dump({'countries': countries, 'zones': {k: zb for k in ('tous',)}, 'box': [0, 0, 400, 610]},
          open(os.path.join(ROOT, 'data/skeleton.json'), 'w', encoding='utf8'), ensure_ascii=False, separators=(',', ':'))
print('data/skeleton-paths.frag', len(frag) // 1024, 'Ko |', len(countries), 'os')
