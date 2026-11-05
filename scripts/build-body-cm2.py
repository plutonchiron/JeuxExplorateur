#!/usr/bin/env python3
"""Dessine la planche d'anatomie du jeu « Situer les organes » (niveau CM2) : un tronc humain semi-réaliste, 16 organes,
avec dégradés, textures et petits vaisseaux (Python 3, aucune dépendance, hors ligne).

  data/body2-paths.frag : silhouette (groupe .deco) + un <path class="c organ2 o2-xxx" data-c> par organe (forme cliquable, dégradé),
                          chaque organe étant suivi d'un groupe .deco (textures, vaisseaux, reflets) que le jeu estompe au clic
  data/body2.json       : { countries: {code: {n: nom avec article, r, a, t}}, zones, box } (même structure que data/body.json)
  src/styles.css        : les fonds des organes (classes .o2-*, entre les repères /*ORGANES2*/) sont réécrits par ce script

À relancer après une retouche du dessin :   python3 scripts/build-body-cm2.py && npm run build
Repère : 400 × 560, tronc de face centré sur x = 200 (tête, cou, thorax, abdomen, bassin ; ni bras ni jambes).
Rien ne doit être dessiné autour des organes (demande du propriétaire) : les détails restent à l'intérieur de chaque organe.
"""
import json, math, os, random, re

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
R = random.Random(23)

defs = ''
def grad(i, stops, cx=.38, cy=.28, r=.95):
    global defs
    defs += '<radialGradient id="h-%s" cx="%s" cy="%s" r="%s">%s</radialGradient>\n' % (i, cx, cy, r, ''.join('<stop offset="%s" stop-color="%s"/>' % s for s in stops))
def clip(i, d):
    global defs
    defs += '<clipPath id="k2-%s"><path d="%s"/></clipPath>\n' % (i, d)
def pat(i, w, h, body, tr=''):
    global defs
    defs += '<pattern id="p2-%s" width="%s" height="%s" patternUnits="userSpaceOnUse"%s>%s</pattern>\n' % (i, w, h, (' patternTransform="%s"' % tr) if tr else '', body)

def P(d, fill='none', stroke=None, w=1.5, op=None):
    s = '<path d="%s" fill="%s"' % (d, fill)
    if stroke: s += ' stroke="%s" stroke-width="%s" stroke-linecap="round" stroke-linejoin="round"' % (stroke, w)
    if op is not None: s += ' opacity="%s"' % op
    return s + '/>\n'
def E(cx, cy, rx, ry, fill, stroke=None, w=1.5, op=None, rot=None):
    s = '<ellipse cx="%s" cy="%s" rx="%s" ry="%s" fill="%s"' % (round(cx, 1), round(cy, 1), rx, ry, fill)
    if stroke: s += ' stroke="%s" stroke-width="%s"' % (stroke, w)
    if op is not None: s += ' opacity="%s"' % op
    if rot: s += ' transform="rotate(%s %s %s)"' % (rot, round(cx, 1), round(cy, 1))
    return s + '/>\n'
def G(inner, cid=None): return '<g%s>\n%s</g>\n' % ((' clip-path="url(#k2-%s)"' % cid) if cid else '', inner)
def mirror(d):
    out, nums = [], 0
    for tok in re.findall(r'[MLCQZ]|-?\d+\.?\d*', d):
        if tok.isalpha(): out.append(tok); nums = 0
        else: out.append(('%g' % (400 - float(tok))) if nums % 2 == 0 else tok); nums += 1
    return ' '.join(out)
def sym(d): return [d, mirror(d)]
def scale(d, k, cx, cy):
    out, n = [], 0
    for tok in re.findall(r'[MLCQZ]|-?\d+\.?\d*', d):
        if tok.isalpha(): out.append(tok); n = 0
        else:
            v = float(tok); out.append('%.1f' % ((cx + (v - cx) * k) if n % 2 == 0 else (cy + (v - cy) * k))); n += 1
    return ' '.join(out)
def poly(pts): return 'M' + ' L'.join('%.1f %.1f' % p for p in pts) + ' Z'
def tube(c, w):
    """Tuyau plein à bouts ronds le long d'une Bézier cubique c (pour les gros vaisseaux cliquables)."""
    def at(t):
        u = 1 - t
        return (u**3 * c[0][0] + 3 * u * u * t * c[1][0] + 3 * u * t * t * c[2][0] + t**3 * c[3][0], u**3 * c[0][1] + 3 * u * u * t * c[1][1] + 3 * u * t * t * c[2][1] + t**3 * c[3][1])
    n = 36; L, Rr = [], []
    for i in range(n + 1):
        t = i / n; x, y = at(t); x2, y2 = at(min(1, t + .01)); x1, y1 = at(max(0, t - .01))
        dx, dy = x2 - x1, y2 - y1; ln = math.hypot(dx, dy) or 1; nx, ny = -dy / ln, dx / ln
        L.append((x + nx * w / 2, y + ny * w / 2)); Rr.append((x - nx * w / 2, y - ny * w / 2))
    return poly(L + Rr[::-1])
def wiggle(x, y, steps, ln, ang, turn):
    pts = [(x, y)]
    for _ in range(steps):
        ang += R.uniform(-turn, turn); x += math.cos(ang) * ln; y += math.sin(ang) * ln; pts.append((x, y))
    d = 'M%.1f %.1f' % pts[0]
    for i in range(1, len(pts) - 1):
        d += ' Q%.1f %.1f %.1f %.1f' % (pts[i][0], pts[i][1], (pts[i][0] + pts[i + 1][0]) / 2, (pts[i][1] + pts[i + 1][1]) / 2)
    return d
def branch(x, y, ang, ln, w, depth, out):
    x2, y2 = x + math.cos(math.radians(ang)) * ln, y + math.sin(math.radians(ang)) * ln
    out.append((x, y, x2, y2, w))
    if depth == 0: return
    for da in (-1, 1): branch(x2, y2, ang + da * R.uniform(22, 38), ln * R.uniform(.68, .8), w * .68, depth - 1, out)
    if depth > 2: branch(x2, y2, ang + R.uniform(-8, 8), ln * .7, w * .7, depth - 2, out)
def tree(x, y, ang, ln, w, depth):
    out = []; branch(x, y, ang, ln, w, depth, out); return out
def vessels(segs, color, k=.5, op=.85): return ''.join(P('M%.1f %.1f L%.1f %.1f' % s[:4], stroke=color, w=round(max(.5, s[4] * k), 2), op=op) for s in segs)
def tex(pid, cid): return G('<rect x="60" y="0" width="280" height="560" fill="url(#p2-%s)"/>\n' % pid, cid)
def rim(cid, ds, color, w=7, op=.3): return G(''.join(P(d, stroke=color, w=w, op=op) for d in ds), cid)
def shine(cx, cy, rx, ry, rot=-25, op=.07): return E(cx, cy, rx, ry, '#FFFFFF', op=op, rot=rot)
def dots(w, h, n, cols, rmin=.5, rmax=1.5):
    return ''.join(E(round(R.uniform(0, w), 1), round(R.uniform(0, h), 1), round(R.uniform(rmin, rmax), 1), round(R.uniform(rmin, rmax), 1), R.choice(cols), op=round(R.uniform(.2, .45), 2)) for _ in range(n))
def hexd(cx, cy, r): return 'M' + 'L'.join('%.1f,%.1f' % (cx + r * math.cos(math.radians(30 + 60 * k)), cy + r * math.sin(math.radians(30 + 60 * k))) for k in range(6)) + 'Z'

# ------------------------------------------------------------------ silhouette (décor, non cliquable)
grad('skin', [(0, '#C7D3E0'), (.7, '#98A9BD'), (1, '#6F829A')], cx=.5, cy=.3, r=.9)
BODY = 'M200 6 C234 6 254 30 254 62 C254 92 238 112 220 120 L220 140 C250 146 290 152 316 166 C328 190 322 250 312 300 C304 350 308 420 302 470 C300 500 306 524 312 556 L88 556 C94 524 100 500 98 470 C92 420 96 350 88 300 C78 250 72 190 84 166 C110 152 150 146 180 140 L180 120 C162 112 146 92 146 62 C146 30 166 6 200 6Z'
back = P(BODY, 'url(#h-skin)', '#A9BBD0', 1.6, .3)
# muscles : seulement quelques traits discrets (trapèzes, sterno-cléido-mastoïdiens, pectoraux)
for d in sym('M180 138 C160 148 128 156 100 172') + sym('M162 112 C170 130 186 156 198 178') + sym('M104 196 C130 224 170 226 196 204'):
    back += P(d, stroke='#A9BBD0', w=1.2, op=.3)
BONE, BONELINE = '#D9D3C0', '#8E8770'
# crâne (de face), sous le cerveau : cavités des yeux, nez, dents, mâchoire
SKULL = 'M200 10 C234 10 250 34 248 62 C247 80 240 92 232 100 L230 110 C220 116 180 116 170 110 L168 100 C160 92 153 80 152 62 C150 34 166 10 200 10Z'
back += P(SKULL, BONE, BONELINE, 1.2, .5)
back += E(181, 88, 11, 9, '#20242C', op=.75) + E(219, 88, 11, 9, '#20242C', op=.75) + P('M200 94 L194 108 C198 111 202 111 206 108Z', '#20242C', op=.75)
back += P('M180 110 L220 110', stroke='#6E604A', w=1, op=.5) + ''.join(P('M%d 106 L%d 112' % (x, x), stroke='#8A7A5E', w=.9, op=.7) for x in range(182, 220, 5))
back += P('M170 108 C172 128 188 136 200 136 C212 136 228 128 230 108 L222 112 C220 124 212 128 200 128 C188 128 180 124 178 112Z', BONE, BONELINE, 1.1, .5)
# squelette en retrait : colonne, côtes, sternum, clavicules, bassin (jamais cliquables)
BONE, BONELINE = '#D9D3C0', '#8E8770'
def bone(d): return P(d, BONE, BONELINE, 1.1, .4)
for i in range(24):
    if i < 7: y, h, w = 124 + i * 7.2, 6.4, 18 + i * .6
    elif i < 19: y, h, w = 175 + (i - 7) * 12.6, 11, 24 + (i - 7) * .5
    else: y, h, w = 327 + (i - 19) * 13.5, 12, 32 + (i - 19) * .8
    back += bone(poly([(200 - w / 2 + 2, y), (200 + w / 2 - 2, y), (200 + w / 2 + 2, y + h / 2), (200 + w / 2 - 2, y + h), (200 - w / 2 + 2, y + h), (200 - w / 2 - 2, y + h / 2)]))
for i, xm in enumerate((52, 64, 74, 80, 84, 86, 86, 82, 74, 64)):
    yb = 186 + i * 13; cx = 200 + xm * 1.3
    for d in sym(tube([(210, yb), (cx, yb - 8), (cx, yb + 36), (206, yb + 28)], 7.5)): back += bone(d)
for d in sym(tube([(204, 180), (182, 169), (140, 175), (96, 164)], 7)): back += bone(d)
back += bone('M190 178 C196 174 204 174 210 178 L210 190 L206 194 L206 290 L200 304 L194 290 L194 194 L190 190Z')
for d in sym('M192 440 C170 432 128 428 106 448 C94 468 104 504 132 528 C150 542 172 552 192 556 L192 520 C196 500 196 470 192 440Z'): back += bone(d)
back += bone('M184 440 L216 440 L208 500 L200 530 L192 500Z')

# ------------------------------------------------------------------ organes : (code, nom, clair, moyen, foncé, formes cliquables)
LUNG_L = 'M168 176 C142 178 124 206 120 244 C118 276 124 296 140 304 C160 312 188 306 196 292 L198 214 C198 194 186 174 168 176Z'
LUNG_R = 'M232 176 C258 178 278 206 280 244 C282 276 276 296 260 304 C244 310 222 304 212 296 C202 286 210 270 208 254 C206 232 204 218 204 204 C204 188 216 174 232 176Z'
BRONCHI = 'M192 124 L208 124 L208 204 C220 208 232 216 244 232 L236 240 C226 230 216 224 200 222 C184 224 174 230 164 240 L156 232 C168 216 180 208 192 204Z'
ORG = [
 ('reins', 'les reins', '#9A4444', '#6B2326', '#3C1015', sym('M122 410 C136 406 146 424 144 446 C142 466 124 470 116 456 C108 442 110 412 122 410Z')),
 ('gros', 'le gros intestin', '#CDA074', '#A07446', '#6A4426',
  ['M154 436 C150 414 176 406 200 408 C224 406 250 414 246 436 L256 484 C258 506 232 508 200 508 C168 508 142 506 144 484Z M174 444 C174 436 226 436 226 444 L230 476 C230 486 170 486 170 476Z']),
 ('intestins', 'l’intestin grêle', '#E3AAA2', '#C07872', '#8A4B4A',
  ['M176 448 C190 436 214 436 224 448 C234 462 232 480 222 486 C206 492 192 492 182 486 C172 478 168 460 176 448Z']),
 ('vessie', 'la vessie', '#DDB097', '#B98568', '#7E5440', ['M200 498 C184 506 182 526 200 532 C218 526 216 506 200 498Z']),
 ('foie', 'le foie', '#94452F', '#652818', '#391409',
  ['M114 336 C140 322 196 322 236 332 C246 358 236 392 212 404 C186 414 150 408 130 390 C116 376 110 352 114 336Z']),
 ('vesicule', 'la vésicule biliaire', '#8DAE5C', '#5F8040', '#37512A', ['M170 396 C162 404 164 420 174 424 C186 422 190 408 184 398 C180 394 174 392 170 396Z']),
 ('estomac', 'l’estomac', '#DD9A88', '#B76A5C', '#7B3A33',
  ['M232 334 C258 326 286 342 284 372 C282 402 256 418 236 404 C224 394 226 382 238 378 C248 372 248 362 238 356 C228 348 224 340 232 334Z']),
 ('rate', 'la rate', '#85507A', '#5B3354', '#341A33', ['M282 330 C296 328 304 350 300 372 C296 388 284 388 282 376 C280 360 278 338 282 330Z']),
 ('pancreas', 'le pancréas', '#DEC585', '#B99C52', '#826E2E', ['M176 410 C196 400 228 402 254 410 C262 420 248 430 226 430 C204 432 184 430 176 420Z']),
 ('diaphragme', 'le diaphragme', '#B15A52', '#85403A', '#4F2220', ['M108 316 C124 296 176 290 200 306 C224 290 276 296 292 316 L292 332 C276 312 224 308 200 322 C176 308 124 312 108 332Z']),
 ('oesophage', 'l’œsophage', '#DE9187', '#B8655C', '#82413C', ['M210 126 L222 126 C222 200 228 260 238 310 L240 330 L228 332 L226 312 C216 262 212 200 210 126Z']),
 ('poumons', 'les poumons', '#E9C1B7', '#CC9188', '#94605F', [LUNG_L, LUNG_R]),
 ('trachee', 'la trachée', '#DCE3E8', '#A3B1BB', '#66757F', [BRONCHI]),
 ('thyroide', 'la thyroïde', '#C27289', '#93455D', '#5E2538', ['M200 152 C192 144 178 142 172 150 C168 160 178 168 192 166 L196 162 L204 162 L208 166 C222 168 232 160 228 150 C222 142 208 144 200 152Z']),
 ('coeur', 'le cœur', '#C23C52', '#8F1F33', '#4E0F1B',
  [tube([(214, 240), (216, 196), (254, 198), (252, 246)], 13), tube([(206, 242), (192, 216), (174, 214), (166, 228)], 11),
   'M200 232 C194 222 212 216 222 224 C234 218 252 224 250 244 C248 268 232 292 218 304 C210 310 202 300 196 288 C188 270 190 244 200 232Z']),
 ('cerveau', 'le cerveau', '#E1B5B0', '#BC8789', '#835258',
  [scale('M160 52 C156 32 176 16 198 20 C212 12 236 18 242 38 C250 52 244 74 228 80 C216 88 184 88 172 80 C162 74 160 62 160 52Z', .82, 200, 46),
   ]),
]
for code, n, a, b, c, ds in ORG:
    grad(code, [(0, a), (.55, b), (1, c)])
byid = {o[0]: o for o in ORG}
LUNGS = [LUNG_L, LUNG_R]

# textures répétées
pat('lung', 16, 16, dots(16, 16, 10, ['#A8504F', '#C97F7B', '#FFFFFF']))
pat('liver', 12, 20.78, ''.join(P(hexd(cx, cy, 6.93), stroke='#4A1C12', w=.7, op=.38) + E(cx, cy, .9, .9, '#3E160D', op=.35) for cx, cy in ((0, 0), (12, 0), (6, 10.39), (0, 20.78), (12, 20.78))))
pat('fiber', 5, 5, P('M0 0 L0 5', stroke='#7A0F20', w=1, op=.4) + P('M2.5 0 L2.5 5', stroke='#FF9AA2', w=.6, op=.3), 'rotate(-40)')
pat('stripe', 4, 4, P('M0 2 L4 2', stroke='#B84C3E', w=.8, op=.38), 'rotate(25)')
pat('ring', 4, 4, P('M0 0 L0 4', stroke='#B94E67', w=1.1, op=.4), 'rotate(75)')
pat('scale', 8, 8, P('M0 5 C2 1 6 1 8 5', stroke='#A8573A', w=.8, op=.4))
pat('grain', 10, 10, dots(10, 10, 7, ['#541616', '#E88B7E', '#FFFFFF']))
pat('muscle', 6, 6, P('M0 3 L6 3', stroke='#5A1A18', w=.9, op=.35), 'rotate(-60)')
for code, n, a, b, c, ds in ORG: clip(code, ' '.join(ds))

# ------------------------------------------------------------------ détails à l'intérieur de chaque organe
D = {}
def seg(code, s): D[code] = D.get(code, '') + s

# cerveau : circonvolutions, scissure, cervelet
br = ''.join(P(wiggle(R.uniform(170, 232), R.uniform(26, 74), 6, R.uniform(3.5, 6), R.uniform(0, 6.28), .9), stroke='#B95A76', w=2, op=.75) + P(wiggle(R.uniform(170, 232), R.uniform(26, 74), 4, 3, R.uniform(0, 6.28), 1.6), stroke='#D0435D', w=.8, op=.5) for _ in range(30))
br += P('M200 24 C196 36 205 48 199 60 C197 66 199 72 201 80', stroke='#A8466A', w=2.6) + shine(184, 36, 10, 4.5, -30)
br += ''
seg('cerveau', G(br, 'cerveau') + rim('cerveau', byid['cerveau'][5], '#A8466A', 7, .28))
# thyroïde
seg('thyroide', G(''.join(E(round(R.uniform(170, 232), 1), round(R.uniform(144, 168), 1), 1.2, 1.2, '#7A2E4C', op=.4) for _ in range(40)), 'thyroide') + rim('thyroide', byid['thyroide'][5], '#7A2E4C', 5, .35) + shine(186, 152, 7, 3, -10))
# trachée : anneaux de cartilage
seg('trachee', G(''.join(P('M192 %d L208 %d' % (y, y), stroke='#5F8AA3', w=1.6, op=.9) for y in range(128, 206, 6)) + P('M195 126 L195 202', stroke='#FFFFFF', w=2.2, op=.7), 'trachee') + rim('trachee', byid['trachee'][5], '#5F8AA3', 4, .4))
# œsophage
seg('oesophage', G(''.join(P('M%g 128 C%g 200 %g 262 %g 322' % (212 + k * 3, 214 + k * 3, 220 + k * 3, 230 + k * 2.5), stroke='#B55E56', w=1, op=.6) for k in range(3)) + P('M213 130 C214 200 220 262 229 318', stroke='#FFFFFF', w=2, op=.5), 'oesophage') + rim('oesophage', byid['oesophage'][5], '#A8524A', 4, .35))
# poumons : alvéoles, bronchioles, vaisseaux, ombres
lt = tex('lung', 'poumons')
lt += G(vessels(tree(162, 238, 112, 22, 5, 4), '#B7C8D6', .9, .95) + vessels(tree(238, 238, 68, 22, 5, 4), '#B7C8D6', .9, .95)
        + vessels(tree(170, 262, 100, 16, 3, 3), '#A82A3A', .5, .8) + vessels(tree(230, 262, 80, 16, 3, 3), '#3D52A0', .5, .8), 'poumons')
lt += rim('poumons', LUNGS, '#B35F5E', 9, .3) + G(E(160, 296, 28, 12, '#A85658', op=.22) + E(240, 292, 28, 12, '#A85658', op=.22), 'poumons')
lt += ''.join(P(d, stroke='#B35F5E', w=2, op=.6) for d in ('M124 252 C144 256 170 266 192 288', 'M276 252 C256 256 232 266 212 290')) + P('M136 190 C128 214 126 244 130 272', stroke='#fff', w=5, op=.3) + P('M266 190 C274 214 276 244 272 272', stroke='#fff', w=5, op=.3)
seg('poumons', lt)
# cœur : fibres, sillon, coronaires, graisse
hc = tex('fiber', 'coeur') + rim('coeur', byid['coeur'][5], '#5E0A18', 7, .4)
hc += G(P('M216 232 C216 256 224 280 230 298', stroke='#7A0F20', w=3, op=.8)
        + ''.join(P(wiggle(x, y, 5, 5, a, .5), stroke='#9E101F', w=1.8, op=.9) + P(wiggle(x, y, 5, 5, a, .5), stroke='#FF8A92', w=.6, op=.6) for x, y, a in ((214, 228, 1.4), (226, 232, 1.2), (204, 238, 1.8)))
        + ''.join(P(wiggle(x, y, 4, 5, a, .6), stroke='#3D52A0', w=1.4, op=.85) for x, y, a in ((198, 244, 1.6), (222, 230, 1.5)))
        + ''.join(E(round(R.uniform(204, 244), 1), round(R.uniform(226, 236), 1), R.uniform(2, 3.4), R.uniform(1.4, 2.4), '#DCC58A', op=.85) for _ in range(9))
        + shine(204, 244, 6, 11, 15) + E(232, 262, 3, 9, '#fff', op=.22, rot=-18), 'coeur')
seg('coeur', hc)
# diaphragme : fibres rayonnant depuis le centre tendineux
dg = tex('muscle', 'diaphragme') + rim('diaphragme', byid['diaphragme'][5], '#5A1A18', 6, .35)
dg += G(''.join(P('M%d 314 C%d %d %d %d %d %d' % (200 + k * 4, 200 + k * 30, 306 - abs(k) * 2, 200 + k * 60, 310 - abs(k), 200 + k * 90, 322 - abs(k)), stroke='#7A2E2A', w=1.1, op=.6) for k in range(-3, 4))
        + P('M176 310 C190 304 210 304 224 310 L224 318 C210 314 190 314 176 318Z', '#F3E3D0', '#C9A98A', 1, .85), 'diaphragme')
seg('diaphragme', dg)
# foie : lobules, ligament, vaisseaux
lv = tex('liver', 'foie') + rim('foie', byid['foie'][5], '#3E160D', 10, .3)
lv += G(vessels(tree(190, 360, 170, 22, 6, 4), '#34408F', .7, .8) + vessels(tree(192, 362, 10, 22, 6, 4), '#34408F', .7, .8) + vessels(tree(190, 358, 190, 20, 4, 3), '#A82A3A', .6, .85), 'foie')
lv += P('M186 326 C190 348 196 372 206 402', stroke='#552016', w=2.6) + shine(150, 346, 16, 5, -10)
seg('foie', lv)
seg('vesicule', rim('vesicule', byid['vesicule'][5], '#3E7228', 4, .4) + shine(172, 408, 3, 8, 15) + P('M184 398 C192 396 198 392 204 388', stroke='#6FA64B', w=2.4, op=.9))
# estomac : plis, muscle, vaisseaux
sv = ''.join(vessels(tree(x, y, a, 9, 2.4, 3), '#A02A22', .7, .8) for x, y, a in ((282, 360, 180), (278, 380, 195), (272, 398, 215), (252, 334, 90), (262, 336, 100)))
seg('estomac', tex('stripe', 'estomac') + rim('estomac', byid['estomac'][5], '#A0443A', 8, .32) + G(sv, 'estomac')
    + ''.join(P(d, stroke='#C25E50', w=2.2, op=.75) for d in ('M258 340 C272 346 278 360 272 378', 'M250 346 C262 352 266 366 260 384', 'M240 344 C250 350 252 360 246 372')) + shine(262, 346, 10, 4, -20))
seg('rate', tex('grain', 'rate') + rim('rate', byid['rate'][5], '#4A1F44', 5, .45) + shine(288, 346, 3, 9, 8) + G(vessels(tree(284, 360, 180, 7, 2.4, 3), '#3D52A0', .9), 'rate'))
seg('pancreas', G(''.join(E(round(R.uniform(176, 256), 1), round(R.uniform(402, 432), 1), R.uniform(1, 2.2), R.uniform(1, 1.8), '#B09030', op=round(R.uniform(.25, .5), 2)) for _ in range(70)), 'pancreas') + rim('pancreas', byid['pancreas'][5], '#B09030', 6, .4) + P('M184 418 C204 414 232 416 252 420', stroke='#FFF3CE', w=1.6, op=.8))
# intestin grêle : anses
sm = tex('ring', 'intestins') + rim('intestins', byid['intestins'][5], '#B9605E', 8, .4)
for k, y in enumerate((454, 463, 472, 481)):
    x0, x1 = (178, 224) if k % 2 == 0 else (224, 178); mx = (x0 + x1) / 2
    d = 'M%d %d C%d %d %d %d %d %d' % (x0, y, x0 + (x1 - x0) / 3, y - 5, x0 + 2 * (x1 - x0) / 3, y + 5, x1, y)
    sm += G(P(d, stroke='#B9605E', w=8.6) + P(d, stroke='#F8B4AC', w=6.4) + P(d, stroke='#FFE6E2', w=1.4, op=.8), 'intestins')
seg('intestins', sm)
# gros intestin : haustrations, bandelette
cg = ''.join(P('M%d 410 L%d 432' % (160 + i * 10, 160 + i * 10), stroke='#8F5632', w=2.2, op=.5) for i in range(10))
cg += ''.join(P('M146 %d L170 %d M254 %d L230 %d' % (y, y, y, y), stroke='#8F5632', w=2.2, op=.5) for y in range(446, 496, 12))
seg('gros', tex('scale', 'gros') + rim('gros', byid['gros'][5], '#8F5632', 8, .35) + G(cg + P('M152 500 L150 440 C150 416 250 416 250 440 L248 500', stroke='#FFEBD8', w=1.8, op=.6), 'gros'))
# reins : cortex, hile, vaisseaux
kv = ''.join(vessels(tree(x, y, a, 7, 2.2, 3), '#A02A22', .8, .8) for x, y, a in ((144, 430, 0), (256, 430, 180)))
seg('reins', tex('grain', 'reins') + rim('reins', byid['reins'][5], '#5A1A1C', 7, .4) + G(kv, 'reins') + ''.join(P(d, stroke='#5A1A1C', w=2.4) for d in sym('M144 428 C136 432 136 442 142 446')) + ''.join(shine(x, 420, 3, 7, 15) for x in (122, 278)))
# vessie : parois musculaires et veines
seg('vessie', tex('stripe', 'vessie') + rim('vessie', byid['vessie'][5], '#B87654', 6, .4) + G(''.join(P(wiggle(x, 502, 4, 4, a, .7), stroke='#7A6CC4', w=.9, op=.55) for x, a in ((192, 1.4), (200, 1.5), (208, 1.7))), 'vessie') + shine(193, 512, 3, 7, 15))

# ------------------------------------------------------------------ assemblage
order = ['reins', 'gros', 'intestins', 'vessie', 'foie', 'vesicule', 'estomac', 'rate', 'pancreas', 'diaphragme', 'oesophage', 'poumons', 'trachee', 'thyroide', 'coeur', 'cerveau']
frag = '<defs>\n' + defs + '</defs>\n<g class="deco">\n' + back + '</g>\n'
css = ''
for code in order:
    _, n, a, b, c, ds = byid[code]
    frag += '<g class="deco">\n' + ''.join('<path d="%s" transform="translate(3 4.5)" fill="#000" opacity=".38" fill-rule="evenodd"/>\n' % d for d in ds) + '</g>\n'
    for d in ds: frag += '<path class="c organ2 o2-%s" data-c="%s" d="%s" fill-rule="evenodd"/>\n' % (code, code, d)
    frag += '<g class="deco">\n' + D.get(code, '') + '</g>\n'
    css += '.o2-%s{fill:url(#h-%s)}' % (code, code)
css += '.c.organ2,html[data-theme="halloween"] .c.organ2{stroke:rgba(20,8,8,.7);stroke-width:.8px}'
css += 'body[data-page="cm2"] .mapwrap{background:radial-gradient(ellipse at 50% 36%,#2E3A4A,#121921 88%);box-shadow:inset 0 0 0 2px #3C4A5C,inset 0 0 60px rgba(0,0,0,.45),var(--shadow)}'
css += 'html[data-theme="halloween"] body[data-page="cm2"] .mapwrap{background:radial-gradient(ellipse at 50% 36%,#2E3347,#101320 88%);box-shadow:inset 0 0 0 2px #4a3a6a,inset 0 0 60px rgba(0,0,0,.45),var(--shadow)}'
open(os.path.join(ROOT, 'data/body2-paths.frag'), 'w', encoding='utf8').write(frag)
zb = [60, 0, 340, 556]
json.dump({'countries': {c: {'n': n, 'r': 'A', 'a': 1000, 't': 1} for c, n, _, _, _, _ in ORG},
           'zones': {'tous': zb}, 'box': [0, 0, 400, 560]},
          open(os.path.join(ROOT, 'data/body2.json'), 'w', encoding='utf8'), ensure_ascii=False, separators=(',', ':'))
p = os.path.join(ROOT, 'src/styles.css'); s = open(p, encoding='utf8').read()
block = '/*ORGANES2*/' + css + '/*/ORGANES2*/'
s = re.sub(r'/\*ORGANES2\*/.*?/\*/ORGANES2\*/', lambda m: block, s) if '/*ORGANES2*/' in s else s.rstrip('\n') + '\n\n/* Planche d\'anatomie (jeu « Situer les organes », CM2) */\n' + block + '\n'
open(p, 'w', encoding='utf8').write(s)
print('data/body2-paths.frag', len(frag) // 1024, 'Ko |', len(ORG), 'organes')
