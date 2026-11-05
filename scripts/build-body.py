#!/usr/bin/env python3
"""Dessine le corps du jeu « Les organes » (Python 3, aucune dépendance, hors ligne), style dessin animé comme le squelette
(`scripts/build-skeleton.py`) : un petit squelette sans les jambes sert de décor, et de gros organes colorés se détachent dedans.

  data/body-paths.frag : décor non cliquable (groupe .deco : silhouette, squelette) + un <path class="c organ o-xxx" data-c> par organe (forme cliquable),
                         chaque organe étant suivi d'un groupe .deco (reflets, plis…) que le jeu estompe au clic
  data/body.json       : { countries: {code: {n: nom avec article, r: groupe de difficulté A/B/C, a, t}}, zones, box }
                         (même structure que data/france.json : le jeu réutilise le moteur de la carte)
  src/styles.css       : les couleurs des organes (classes .o-*, entre les repères /*ORGANES*/) sont réécrites par ce script

À relancer après une retouche du dessin :   python3 scripts/build-body.py && npm run build
Repère : 400 × 560, centré sur x = 200 ; le dessin s'arrête au bassin (pas de jambes : plus de place pour les organes).
Groupes d'organes : A = Découverte, B = + Super, C = + Champion.
"""
import json, math, os, re

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
CREAM, LINE, TAN = '#F8E1C3', '#4B1E1E', '#D9B48C'      # os : même crème et même contour que le jeu du squelette

# ------------------------------------------------------------------ outils
def P(d, fill='none', stroke=None, w=3, op=None):
    s = '<path d="%s" fill="%s"' % (d, fill)
    if stroke: s += ' stroke="%s" stroke-width="%s" stroke-linecap="round" stroke-linejoin="round"' % (stroke, w)
    if op is not None: s += ' opacity="%s"' % op
    return s + '/>\n'
def E(cx, cy, rx, ry, fill, stroke=None, w=3, op=None, rot=None):
    s = '<ellipse cx="%s" cy="%s" rx="%s" ry="%s" fill="%s"' % (round(cx, 1), round(cy, 1), rx, ry, fill)
    if stroke: s += ' stroke="%s" stroke-width="%s"' % (stroke, w)
    if op is not None: s += ' opacity="%s"' % op
    if rot: s += ' transform="rotate(%s %s %s)"' % (rot, round(cx, 1), round(cy, 1))
    return s + '/>\n'
def D(d): return P(d, CREAM, LINE)
def mirror(d):
    """Symétrique par rapport à x = 200 (chemins absolus M L C Q Z)."""
    out, nums = [], 0
    for tok in re.findall(r'[MLCQZ]|-?\d+\.?\d*', d):
        if tok.isalpha(): out.append(tok); nums = 0
        else: out.append(('%g' % (400 - float(tok))) if nums % 2 == 0 else tok); nums += 1
    return ' '.join(out)
def sym(d): return [d, mirror(d)]
def poly(pts): return 'M' + ' L'.join('%.1f %.1f' % p for p in pts) + ' Z'
def bonec(c, shaft, e0, e1, n=60):
    """Os long à bouts ronds : courbe de Bézier c = [p0,p1,p2,p3], tige `shaft`, bouts de diamètre e0 / e1."""
    def at(t):
        u = 1 - t
        return (u**3 * c[0][0] + 3 * u * u * t * c[1][0] + 3 * u * t * t * c[2][0] + t**3 * c[3][0],
                u**3 * c[0][1] + 3 * u * u * t * c[1][1] + 3 * u * t * t * c[2][1] + t**3 * c[3][1])
    ts = [(1 - math.cos(math.pi * i / n)) / 2 for i in range(n + 1)]
    mid = [at(t) for t in ts]; cum = [0]
    for i in range(1, len(mid)): cum.append(cum[-1] + math.hypot(mid[i][0] - mid[i - 1][0], mid[i][1] - mid[i - 1][1]))
    tot = cum[-1]; L, Rr = [], []
    def knob(sd, d):
        r = d / 2
        return 2 * math.sqrt(max(0, r * r - (r - sd) ** 2)) if sd < 2 * r else 0
    for i, t in enumerate(ts):
        x, y = mid[i]; x2, y2 = at(min(1, t + .005)); x1, y1 = at(max(0, t - .005))
        dx, dy = x2 - x1, y2 - y1; ln = math.hypot(dx, dy) or 1; nx, ny = -dy / ln, dx / ln
        w = max(shaft * .999 if 0 < cum[i] < tot else 0, knob(cum[i], e0), knob(tot - cum[i], e1))
        L.append((x + nx * w / 2, y + ny * w / 2)); Rr.append((x - nx * w / 2, y - ny * w / 2))
    return poly(L + Rr[::-1])
def bone(p0, p1, shaft, e0, e1, bow=0):
    dx, dy = p1[0] - p0[0], p1[1] - p0[1]; ln = math.hypot(dx, dy); nx, ny = -dy / ln, dx / ln
    return bonec([p0, (p0[0] + dx / 3 + nx * bow, p0[1] + dy / 3 + ny * bow), (p0[0] + 2 * dx / 3 + nx * bow, p0[1] + 2 * dy / 3 + ny * bow), p1], shaft, e0, e1)
def caps(p0, p1, w):
    a = math.atan2(p1[1] - p0[1], p1[0] - p0[0]); r = w / 2; pts = []
    for k in range(9): pts.append((p1[0] + r * math.cos(a - math.pi / 2 + math.pi * k / 8), p1[1] + r * math.sin(a - math.pi / 2 + math.pi * k / 8)))
    for k in range(9): pts.append((p0[0] + r * math.cos(a + math.pi / 2 + math.pi * k / 8), p0[1] + r * math.sin(a + math.pi / 2 + math.pi * k / 8)))
    return poly(pts)
def hand(cx, cy, ang):
    s = ''; a = math.radians(ang); dx, dy = math.cos(a), math.sin(a); nx, ny = -dy, dx
    for off, ln in ((-9, 17), (-3, 20), (3, 19), (9, 15)):
        bx, by = cx + nx * off + dx * 8, cy + ny * off + dy * 8
        fa = a + math.radians(off * 1.6)
        s += D(caps((bx, by), (bx + math.cos(fa) * ln, by + math.sin(fa) * ln), 7.4))
    tb = (cx + nx * -13, cy + ny * -13)
    s += D(caps(tb, (tb[0] + math.cos(a - .9) * 13, tb[1] + math.sin(a - .9) * 13), 7.4))
    return s + E(cx, cy, 14, 12, CREAM, LINE, 3, rot=ang + 90)
def vert(y, w, h):
    return poly([(200 - w / 2 + 2, y), (200 + w / 2 - 2, y), (200 + w / 2 + 2, y + h * .3), (200 + w / 2 + 2, y + h * .7), (200 + w / 2 - 2, y + h), (200 - w / 2 + 2, y + h), (200 - w / 2 - 2, y + h * .7), (200 - w / 2 - 2, y + h * .3)])

# ------------------------------------------------------------------ décor : silhouette + petit squelette sans jambes
back = P('M122 212 C146 204 254 204 278 212 C296 250 300 330 292 392 C290 440 296 490 304 548 L96 548 C104 490 110 440 108 392 C100 330 104 250 122 212Z', '#F7FCFF', '#8FB4CC', 3, .75)
for d in (bone((106, 226), (56, 262), 16, 27, 30, bow=-3), bone((50, 256), (26, 198), 11, 19, 19, bow=2), bone((62, 262), (42, 202), 11, 21, 15, bow=-2),
          bone((294, 226), (330, 294), 16, 27, 30, bow=-2), bone((334, 300), (346, 380), 11, 19, 19, bow=1), bone((322, 300), (332, 380), 11, 21, 15, bow=-1)):
    back += D(d)
back += hand(32, 182, -112) + hand(348, 398, 96)
for yb, xm in ((232, 70), (252, 86), (272, 96), (292, 96), (312, 86)):                                 # côtes
    cx = 200 + xm * 1.3
    for d in sym(bonec([(196, yb), (cx, yb - 6), (cx, yb + 26), (196, yb + 16)], 14, 14, 14, n=40)): back += D(d)
for y in (188, 198, 208): back += D(vert(y, 22, 9))                                                  # cou
for d in sym(bonec([(207, 224), (176, 214), (140, 218), (108, 211)], 12, 20, 24)): back += D(d)       # clavicules
back += '<g transform="translate(-30 100.4) scale(1.15 1.1)">\n' + D('M118 346 C128 334 168 336 200 352 C232 336 272 334 282 346 C292 362 276 388 250 390 C230 392 214 382 200 372 C186 382 170 392 150 390 C124 388 108 362 118 346Z') \
        + E(158, 362, 15, 10, CREAM, LINE, 2.6, rot=-12) + E(242, 362, 15, 10, CREAM, LINE, 2.6, rot=12) + '</g>\n'     # bassin
back += D('M200 12 C252 12 284 44 284 86 C284 112 270 132 250 142 L250 152 L150 152 L150 142 C130 132 116 112 116 86 C116 44 148 12 200 12Z')
back += E(164, 90, 18, 18, LINE) + E(236, 90, 18, 18, LINE) + P('M200 112 C192 112 189 125 196 131 L204 131 C211 125 208 112 200 112Z', LINE) + P('M124 104 C126 120 138 132 152 140 M276 104 C274 120 262 132 248 140', 'none', TAN, 3)
back += D('M154 148 L246 148 L244 168 C242 180 226 186 200 186 C174 186 158 180 156 168Z')
smile = P('M162 146 C178 160 222 160 238 146', 'none', LINE, 3.2)
for x in range(172, 232, 8): smile += P('M%d %.1f L%d %.1f' % (x, 146 + 10.5 * (1 - ((x - 200) / 38) ** 2) - 6, x, 146 + 10.5 * (1 - ((x - 200) / 38) ** 2) + 7), 'none', LINE, 2.6)
back += smile

# ------------------------------------------------------------------ organes : (code, nom, groupe, couleur, plus foncé, formes cliquables, détails)
def folds(color, ds, w=3): return ''.join(P(d, 'none', color, w) for d in ds)
def shine(cx, cy, rx, ry, rot=-25): return E(cx, cy, rx, ry, '#FFFFFF', op=.55, rot=rot)

LUNG_L = 'M168 222 C144 224 128 248 126 280 C124 306 132 328 150 334 C168 340 192 334 198 322 L198 246 C198 232 186 220 168 222Z'
LUNG_R = 'M232 222 C256 224 272 248 274 280 C276 306 268 328 250 334 C236 338 218 334 208 326 C202 316 208 300 206 286 C204 268 202 256 202 244 C202 230 216 220 232 222Z'
ORG = [
 ('gros', 'le gros intestin', 'C', '#E8AD76', '#B7733F',
  ['M150 424 C150 404 250 404 250 424 L258 470 C260 494 140 494 142 470 Z M172 436 C172 430 228 430 228 436 L231 466 C231 474 169 474 169 466Z'],
  ''.join(P('M%d 410 L%d 426' % (x, x), 'none', '#B7733F', 3, .8) for x in range(160, 245, 12))
  + ''.join(P('M154 %d L168 %d M246 %d L232 %d' % (y, y, y, y), 'none', '#B7733F', 3, .8) for y in (448, 460, 472))),
 ('intestins', 'l’intestin grêle', 'A', '#F9B3C4', '#DE7B96',
  ['M176 440 C188 430 214 430 224 440 C232 452 230 466 220 471 C206 477 192 477 182 471 C172 465 168 452 176 440Z'],
  ''.join(P(d, 'none', '#DE7B96', 4.6) + P(d, 'none', '#FFE0E8', 1.6) for d in ('M178 445 C190 438 208 452 224 444', 'M176 455 C190 449 208 461 226 454', 'M180 465 C192 459 208 470 222 464'))),
 ('reins', 'les reins', 'B', '#A55AA0', '#6E2F6B',
  sym('M138 384 C150 380 158 396 156 414 C154 430 140 432 134 420 C128 408 128 386 138 384Z'),
  ''.join(P(d, 'none', '#6E2F6B', 3) + P(h, 'none', '#FFFFFF', 3, .6) for d, h in zip(sym('M156 400 C148 404 148 412 154 416'), sym('M138 392 C142 392 145 396 145 400')))),
 ('foie', 'le foie', 'B', '#BE7248', '#7C3F1F',
  ['M126 352 C150 338 202 338 234 346 C242 368 234 392 212 400 C186 408 150 402 134 386 C124 376 122 362 126 352Z'],
  P('M178 346 C188 360 200 374 206 396', 'none', '#7C3F1F', 3.4) + P('M148 358 C160 350 176 348 190 350', 'none', '#FFFFFF', 4, .5) + shine(142, 372, 4, 8, 30)),
 ('estomac', 'l’estomac', 'A', '#F7AA5E', '#CC7022',
  ['M234 342 C258 334 282 350 280 376 C278 402 252 412 236 400 C224 392 226 382 236 378 C244 374 244 366 236 362 C228 356 226 348 234 342Z'],
  folds('#CC7022', ('M250 352 C262 358 266 370 260 384', 'M243 358 C252 364 254 376 249 388')) + shine(262, 358, 6, 10, -20)),
 ('rate', 'la rate', 'C', '#8F5AB8', '#5B3382',
  ['M276 340 C290 338 296 356 292 372 C288 384 278 384 276 374 C274 362 272 346 276 340Z'],
  P('M282 348 L282 366', 'none', '#FFFFFF', 3, .55)),
 ('pancreas', 'le pancréas', 'C', '#F4D663', '#C9A227',
  ['M178 402 C198 394 226 396 246 402 C252 410 242 418 222 418 C202 420 184 418 178 410Z'],
  ''.join(E(x, 409, 2.2, 2.2, '#C9A227', op=.85) for x in (190, 204, 218, 232)) + P('M186 400 C204 396 226 398 240 402', 'none', '#FFFFFF', 3, .55)),
 ('vessie', 'la vessie', 'B', '#FFE27A', '#D9A91C',
  ['M200 494 C184 502 182 522 200 528 C218 522 216 502 200 494Z'],
  shine(194, 508, 3.4, 7, 15)),
 ('poumons', 'les poumons', 'A', '#9ED9F2', '#4FA7CF',
  [LUNG_L, LUNG_R],
  ''.join(P(d, 'none', '#FFFFFF', 4, .9) for d in sym('M197 246 C189 262 177 272 165 284 M181 268 C187 280 189 292 187 304 M171 279 C163 285 159 295 159 305'))
  + ''.join(shine(x, 258, 5, 11, a) for x, a in ((150, 14), (250, -14)))),
 ('coeur', 'le cœur', 'A', '#EE4A57', '#A81D2E',
  [bonec([(218, 258), (216, 222), (248, 220), (246, 252)], 11, 11, 11, n=40),
   'M216 254 C208 238 182 242 184 268 C186 292 214 312 216 326 C218 312 246 292 248 268 C250 242 224 238 216 254Z'],
  P('M214 268 C220 284 228 298 232 310', 'none', '#A81D2E', 3) + shine(198, 262, 5, 11, 20) + P('M232 262 C238 266 240 272 238 280', 'none', '#FFB3B8', 3, .8)),
 ('cerveau', 'le cerveau', 'A', '#F7A6BF', '#C4637F',
  ['M162 44 C158 28 176 18 196 22 C208 14 232 18 240 32 C250 42 244 58 230 62 C218 68 186 68 176 62 C166 58 164 52 162 44Z'],
  folds('#C4637F', ('M200 22 C196 32 204 42 198 52 C196 58 198 62 200 66', 'M176 34 C184 38 186 46 182 52', 'M168 48 C176 50 180 56 177 60', 'M224 32 C216 38 214 46 218 52', 'M232 46 C224 48 220 54 223 60', 'M190 28 C194 32 193 36 190 38')) + shine(180, 32, 9, 4, -25)),
]
order = ['gros', 'intestins', 'reins', 'foie', 'estomac', 'rate', 'pancreas', 'vessie', 'poumons', 'coeur', 'cerveau']
byid = {o[0]: o for o in ORG}

# ------------------------------------------------------------------ assemblage
frag = '<g class="deco">\n' + back + '</g>\n'
css = ''
for code in order:
    _, n, r, col, dark, ds, detail = byid[code]
    for d in ds: frag += '<path class="c organ o-%s" data-c="%s" d="%s" fill-rule="evenodd"/>\n' % (code, code, d)
    frag += '<g class="deco">\n' + detail + '</g>\n'
    css += '.o-%s{fill:%s}' % (code, col)
css += '.c.organ,html[data-theme="halloween"] .c.organ{stroke:#4B1E1E;stroke-width:3px}'
open(os.path.join(ROOT, 'data/body-paths.frag'), 'w', encoding='utf8').write(frag)
zb = [0, 0, 400, 545]
json.dump({'countries': {c: {'n': n, 'r': r, 'a': 1000, 't': 1} for c, n, r, _, _, _, _ in ORG},
           'zones': {k: zb for k in ('tous',)}, 'box': [0, 0, 400, 560]},
          open(os.path.join(ROOT, 'data/body.json'), 'w', encoding='utf8'), ensure_ascii=False, separators=(',', ':'))
p = os.path.join(ROOT, 'src/styles.css'); s = open(p, encoding='utf8').read()
s = re.sub(r'/\*ORGANES\*/.*?/\*/ORGANES\*/', lambda m: '/*ORGANES*/' + css + '/*/ORGANES*/', s)
open(p, 'w', encoding='utf8').write(s)
print('data/body-paths.frag', len(frag) // 1024, 'Ko |', len(ORG), 'organes')
