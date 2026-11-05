#!/usr/bin/env python3
"""Dessine le squelette réaliste du jeu « Situer les os » (niveau 5ème) : squelette entier de face, 23 os à situer
(Python 3, aucune dépendance, hors ligne). Même esprit « imagerie médicale » que la planche des organes CM2.

  data/os5-paths.frag : un <path class="c bone5" data-c> par os (forme cliquable, dégradé d'ivoire) ; chaque os est suivi d'un
                        groupe .deco (texture, ombres de bord, détails) que le jeu estompe au clic
  data/os5.json       : { countries: {code: {n: nom avec article, r, a, t}}, zones, box } (même structure que data/body.json)
  src/styles.css      : fond sombre et apparence des os (classe .bone5, entre les repères /*OS5*/) réécrits par ce script

À relancer après une retouche du dessin :   python3 scripts/build-os-5e.py && npm run build
Repère : 400 × 800, squelette de face centré sur x = 200, dessiné côté gauche du dessin puis reflété (échelle ≈ 4,3 px par cm).
Les vertèbres dorsales sont cachées derrière le sternum et les côtes (comme sur un vrai squelette de face) : elles ne sont pas demandées.
"""
import json, math, os, random, re

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
R = random.Random(41)
defs = ''

def P(d, fill='none', stroke=None, w=1.0, op=None):
    s = '<path d="%s" fill="%s"' % (d, fill)
    if stroke: s += ' stroke="%s" stroke-width="%s" stroke-linecap="round" stroke-linejoin="round"' % (stroke, w)
    if op is not None: s += ' opacity="%s"' % op
    return s + '/>\n'
def E(cx, cy, rx, ry, fill, stroke=None, w=1.0, op=None):
    s = '<ellipse cx="%s" cy="%s" rx="%s" ry="%s" fill="%s"' % (round(cx, 1), round(cy, 1), rx, ry, fill)
    if stroke: s += ' stroke="%s" stroke-width="%s"' % (stroke, w)
    if op is not None: s += ' opacity="%s"' % op
    return s + '/>\n'
def mirror(d):
    out, n = [], 0
    for tok in re.findall(r'[MLCQZ]|-?\d+\.?\d*', d):
        if tok.isalpha(): out.append(tok); n = 0
        else: out.append(('%g' % (400 - float(tok))) if n % 2 == 0 else tok); n += 1
    return ' '.join(out)
def xform(d, sx, sy, cx, cy):
    out, n = [], 0
    for tok in re.findall(r'[MLCQZ]|-?\d+\.?\d*', d):
        if tok.isalpha(): out.append(tok); n = 0
        else: v = float(tok); out.append('%.1f' % ((cx + (v - cx) * sx) if n % 2 == 0 else (cy + (v - cy) * sy))); n += 1
    return ' '.join(out)
def poly(pts): return 'M' + ' L'.join('%.1f %.1f' % p for p in pts) + ' Z'
def ell(cx, cy, rx, ry):
    k = .5523
    return ('M%.1f %.1f C%.1f %.1f %.1f %.1f %.1f %.1f C%.1f %.1f %.1f %.1f %.1f %.1f C%.1f %.1f %.1f %.1f %.1f %.1f C%.1f %.1f %.1f %.1f %.1f %.1f Z'
            % (cx + rx, cy, cx + rx, cy + k * ry, cx + k * rx, cy + ry, cx, cy + ry, cx - k * rx, cy + ry, cx - rx, cy + k * ry, cx - rx, cy,
               cx - rx, cy - k * ry, cx - k * rx, cy - ry, cx, cy - ry, cx + k * rx, cy - ry, cx + rx, cy - k * ry, cx + rx, cy))
def bone(c, shaft, e0, e1, bumps=(), n=64):
    """Os long : Bézier cubique c, largeur `shaft`, bouts arrondis de diamètre e0 / e1, renflements gaussiens (t, amplitude, sigma)."""
    def at(t):
        u = 1 - t
        return (u**3 * c[0][0] + 3 * u * u * t * c[1][0] + 3 * u * t * t * c[2][0] + t**3 * c[3][0], u**3 * c[0][1] + 3 * u * u * t * c[1][1] + 3 * u * t * t * c[2][1] + t**3 * c[3][1])
    ts = [(1 - math.cos(math.pi * i / n)) / 2 for i in range(n + 1)]
    mid = [at(t) for t in ts]; cum = [0]
    for i in range(1, len(mid)): cum.append(cum[-1] + math.hypot(mid[i][0] - mid[i - 1][0], mid[i][1] - mid[i - 1][1]))
    tot = cum[-1]; L, Rr = [], []
    knob = lambda sd, d: (2 * math.sqrt(max(0, (d / 2) ** 2 - (d / 2 - sd) ** 2)) if sd < d else 0)
    for i, t in enumerate(ts):
        x, y = mid[i]; x2, y2 = at(min(1, t + .004)); x1, y1 = at(max(0, t - .004))
        dx, dy = x2 - x1, y2 - y1; ln = math.hypot(dx, dy) or 1; nx, ny = -dy / ln, dx / ln
        w = max(shaft * .999 if 0 < cum[i] < tot else 0, knob(cum[i], e0), knob(tot - cum[i], e1)) + sum(a * math.exp(-((t - tb) / sg) ** 2) for tb, a, sg in bumps)
        L.append((x + nx * w / 2, y + ny * w / 2)); Rr.append((x - nx * w / 2, y - ny * w / 2))
    return poly(L + Rr[::-1])
def seg(p0, p1, w0, w1=None, e=None):
    """Petit os droit (doigt, orteil, métacarpien) entre p0 et p1."""
    dx, dy = p1[0] - p0[0], p1[1] - p0[1]; m = (p0[0] + dx / 2, p0[1] + dy / 2)
    return bone([p0, (p0[0] + dx / 3, p0[1] + dy / 3), (p0[0] + 2 * dx / 3, p0[1] + 2 * dy / 3), p1], w0 * .72, w0, w1 or w0, n=14)
def vert(cx, y, w, h, wing=3):
    return poly([(cx - w / 2 + 2, y), (cx + w / 2 - 2, y), (cx + w / 2 + wing, y + h * .3), (cx + w / 2 + wing, y + h * .7), (cx + w / 2 - 2, y + h), (cx - w / 2 + 2, y + h), (cx - w / 2 - wing, y + h * .7), (cx - w / 2 - wing, y + h * .3)])

BONES = {}
def add(code, d): BONES.setdefault(code, []).append(d)
def pair(code, d): add(code, d); add(code, mirror(d))
def finger(code, base, ang, lens, ws):
    """Chaîne d'os (métacarpien + phalanges) à partir de base, dans la direction ang (degrés depuis « vers le bas »)."""
    x, y = base; a = math.radians(ang)
    for ln, w in zip(lens, ws):
        x2, y2 = x + math.sin(a) * ln, y + math.cos(a) * ln
        pair(code, seg((x, y), (x2, y2), w)); x, y = x2 + math.sin(a) * 1.2, y2 + math.cos(a) * 1.2

# ------------------------------------------------------------------ os (côté gauche du dessin, puis reflet)
# tête
add('crane', 'M200 6 C220 6 233 20 233 42 C233 56 229 66 224 72 L222 78 C214 82 186 82 178 78 L176 72 C171 66 167 56 167 42 C167 20 180 6 200 6Z')
add('mandibule', 'M172 50 L176 74 C178 88 190 96 200 96 C210 96 222 88 224 74 L228 50 L222 52 L219 72 C217 82 210 88 200 88 C190 88 183 82 181 72 L178 52Z')
# colonne : cervicales (7) sous la mâchoire, lombaires (5)
for i in range(7): add('cervicales', vert(200, 92 + i * 6.6, 17 + i * .9, 6, 3))
for i in range(5): add('lombaires', vert(200, 240 + i * 11.5, 30 + i * 1.4, 10, 6))
# thorax
add('sternum', 'M185 136 C191 132 209 132 215 136 L215 150 L209 156 L209 196 L204 212 L196 212 L191 196 L191 156 L185 150Z')
pair('clavicule', bone([(194, 140), (172, 148), (142, 122), (112, 134)], 8, 13, 15, bumps=((.5, 1.5, .3),)))
RIBS = ((28, 152), (40, 160), (50, 168), (56, 176), (60, 184), (62, 192), (62, 200), (58, 214), (52, 222), (44, 230), (34, None), (26, None))
for k, (xm, ys) in enumerate(RIBS):
    y0 = 140 + k * 10; xe, ye = 200 + xm * .86, y0 + 36
    pair('cotes', bone([(212, y0), (200 + xm * 1.25, y0 - 4), (200 + xm * 1.15, y0 + 22), (xe, ye)], 6.4, 6, 6, n=36))
    if ys is not None:
        xs = 209 if k < 7 else 209 + (k - 6) * 6
        pair('cotes', bone([(xe, ye), (xe - 8, ye + 2), (xs + 12, ys + 8), (xs, ys)], 5, 5, 5, n=24))
pair('omoplate', 'M160 150 C150 146 134 148 124 154 L122 164 C126 176 130 194 132 208 C134 220 140 226 146 228 C152 216 158 196 162 176Z')
# bras
pair('humerus', bone([(112, 152), (102, 190), (88, 240), (72, 278)], 14, 25, 30, bumps=((.07, -6, .05), (.12, 5, .05), (.97, 5, .05))))
pair('radius', bone([(64, 284), (60, 320), (54, 356), (47, 392)], 9, 14, 19, bumps=((.06, 3, .06),)))
pair('cubitus', bone([(78, 282), (73, 318), (66, 354), (58, 390)], 9.5, 21, 11, bumps=((.04, 6, .06),)))
# main : poignet (8 carpiens), 5 métacarpiens, 14 phalanges
for cx, cy, rx, ry in ((40, 400, 6.5, 5), (49, 397, 6.5, 5.5), (58, 399, 6.5, 5), (66, 405, 6, 5), (40, 410, 5.5, 5), (48, 407, 6.5, 5), (57, 409, 6.5, 5), (47, 417, 6, 4.5)):
    pair('poignet', ell(cx, cy, rx, ry))
for base, ang, lm in (((37, 412), -38, 22), ((43, 419), -9, 30), ((50, 420), 0, 31), ((57, 419), 7, 28), ((64, 416), 15, 23)):
    finger('metacarpiens', base, ang, [lm], [7.5])
for base, ang, lens in (((29, 429), -38, (14, 11)), ((41, 449), -9, (17, 11, 9)), ((50, 451), 0, (19, 12, 10)), ((60, 446), 7, (17, 11, 9)), ((70, 437), 15, (13, 9, 8))):
    finger('phal_main', base, ang, lens, [6.2, 5.2, 4.4][:len(lens)])
# bassin
add('sacrum', 'M184 284 L216 284 L211 330 L205 348 C203 353 197 353 195 348 L189 330Z')
pair('coxal', xform('M184 286 C172 262 148 256 132 266 C122 274 118 288 120 300 C122 316 132 332 138 346 C140 356 142 366 148 376 C152 388 158 398 166 402 C176 406 186 400 192 392 L198 380 L198 360 C194 344 190 326 186 308Z M168 370 C160 372 156 384 160 394 C168 399 178 392 178 382 C178 376 174 372 168 370Z', .75, .8, 200, 270))
# jambes
pair('femur', bone([(160, 342), (140, 362), (150, 430), (168, 548)], 17, 30, 40, bumps=((.07, -6, .04), (.13, 8, .05))))
pair('tibia', bone([(168, 560), (170, 610), (172, 660), (173, 708)], 15, 36, 26, bumps=((.04, 8, .05),)))
pair('perone', bone([(146, 574), (148, 620), (154, 668), (156, 714)], 8, 13, 16))
pair('rotule', ell(169, 541, 11, 13))
for cx, cy, rx, ry in ((171, 723, 11, 9), (159, 738, 9.5, 14), (182, 738, 8.5, 6.5), (166, 752, 7.5, 7), (177, 752, 6, 6), (186, 751, 5.5, 5.5)):
    pair('tarse', ell(cx, cy, rx, ry))
for base, ang, lm in (((186, 758), 3, 22), ((178, 760), 0, 21), ((170, 760), -4, 20), ((162, 759), -8, 19), ((154, 757), -12, 18)):
    finger('metatarsiens', base, ang, [lm], [9 if base[0] == 186 else 6])
for base, ang, lens, ws in (((187, 782), 3, (12, 10), (9, 8)), ((178, 783), 0, (8, 6, 5), (5.5, 4.8, 4.2)), ((169, 782), -4, (8, 6, 5), (5.5, 4.8, 4.2)),
                            ((160, 779), -8, (7, 5, 5), (5.2, 4.6, 4)), ((151, 775), -12, (7, 5, 4), (5, 4.4, 3.8))):
    finger('phal_pied', base, ang, lens, ws)

NAMES = {
 'crane': 'le crâne', 'mandibule': 'la mandibule', 'cervicales': 'les vertèbres cervicales', 'lombaires': 'les vertèbres lombaires', 'sacrum': 'le sacrum',
 'sternum': 'le sternum', 'cotes': 'les côtes', 'clavicule': 'la clavicule', 'omoplate': 'l’omoplate', 'humerus': 'l’humérus', 'radius': 'le radius',
 'cubitus': 'le cubitus', 'poignet': 'les os du poignet', 'metacarpiens': 'les métacarpiens', 'phal_main': 'les phalanges des doigts', 'coxal': 'l’os coxal',
 'femur': 'le fémur', 'rotule': 'la rotule', 'tibia': 'le tibia', 'perone': 'le péroné', 'tarse': 'les os du tarse', 'metatarsiens': 'les métatarsiens',
 'phal_pied': 'les phalanges des orteils',
}
# du fond vers le devant
ORDER = ['omoplate', 'cotes', 'lombaires', 'sternum', 'clavicule', 'humerus', 'radius', 'cubitus', 'poignet', 'metacarpiens', 'phal_main', 'sacrum', 'coxal', 'femur',
         'tibia', 'perone', 'tarse', 'metatarsiens', 'phal_pied', 'rotule', 'cervicales', 'crane', 'mandibule']

# ------------------------------------------------------------------ dégradés, textures, détails
defs += '<linearGradient id="b5" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#8F8870"/><stop offset=".3" stop-color="#E4DCC6"/><stop offset=".55" stop-color="#F3EEDD"/><stop offset="1" stop-color="#9A9279"/></linearGradient>\n'
defs += '<pattern id="p5" width="12" height="12" patternUnits="userSpaceOnUse">' + ''.join(E(round(R.uniform(0, 12), 1), round(R.uniform(0, 12), 1), round(R.uniform(.4, 1.2), 1), round(R.uniform(.4, 1.1), 1), R.choice(['#8A8068', '#FFFFFF', '#B8AC8E']), op=round(R.uniform(.2, .45), 2)) for _ in range(10)) + '</pattern>\n'
D = {}
def deco(code, s): D[code] = D.get(code, '') + s
deco('crane', E(186, 46, 8.5, 7.5, '#14181F', op=.9) + E(214, 46, 8.5, 7.5, '#14181F', op=.9) + P('M200 52 L194 66 C197 69 203 69 206 66Z', '#14181F', op=.9)
     + P('M172 56 C176 66 184 70 192 72 M228 56 C224 66 216 70 208 72', 'none', '#6F6650', 1.2, .8) + P('M176 24 C186 14 214 14 224 24 M200 8 L200 30', 'none', '#6F6650', .9, .6)
     + ''.join(P('M%d 74 L%d 81' % (x, x), 'none', '#6F6650', .8, .9) for x in range(180, 221, 4)) + P('M178 74 L222 74 L222 81 L178 81Z', 'none', '#6F6650', .8, .8))
deco('mandibule', ''.join(P('M%d 76 L%d 83' % (x, x), 'none', '#6F6650', .8, .9) for x in range(183, 218, 4)))
deco('sternum', P('M192 158 L208 158 M192 176 L208 176 M193 192 L207 192', 'none', '#7A725C', 1, .8) + P('M200 140 L200 208', 'none', '#FFFFFF', 1.4, .3))
deco('sacrum', ''.join(E(x, y, 2.2, 2.2, '#6F6650', op=.8) for x, y in ((194, 300), (206, 300), (196, 316), (204, 316))) + P('M187 292 L213 292 M190 308 L210 308 M193 324 L207 324', 'none', '#7A725C', 1, .7))
deco('coxal', ''.join(P(d, 'none', '#6F6650', 1.2, .6) for d in (xform('M126 284 C140 274 162 274 180 290 M122 296 C130 300 140 306 150 316', .75, .8, 200, 270), mirror(xform('M126 284 C140 274 162 274 180 290 M122 296 C130 300 140 306 150 316', .75, .8, 200, 270)))) + E(160, 342, 10, 10, 'none', '#6F6650', 1.3, .7) + E(240, 342, 10, 10, 'none', '#6F6650', 1.3, .7) + P('M199 352 L201 372', 'none', '#6F6650', 1.4, .8))
deco('lombaires', ''.join(E(200, 244 + i * 11.5 + 5, 3, 3.4, '#7A725C', op=.55) for i in range(5)))
deco('cervicales', ''.join(E(200, 95 + i * 6.6, 2, 1.8, '#7A725C', op=.6) for i in range(7)))
deco('femur', ''.join(E(x, 342, 2.6, 2.6, '#6F6650', op=.8) for x in (160, 240)))
deco('omoplate', P('M122 154 C134 162 148 168 160 170 M278 154 C266 162 252 168 240 170', 'none', '#6F6650', 1.2, .55))

# ------------------------------------------------------------------ assemblage
# Chaque forme est écrite deux fois seulement : une copie dans <defs> (id « s5-n »), réutilisée par <use> pour l'ombre, le masque de
# texture et l'ombre de bord ; et la forme cliquable elle-même.
zb = [30, 0, 370, 800]
ids = {}
n = 0
shapes = ''
for code in ORDER:
    ids[code] = []
    for d in BONES[code]:
        ids[code].append('s5-%d' % n); shapes += '<path id="s5-%d" d="%s" fill-rule="evenodd"/>\n' % (n, d); n += 1
frag = '<defs>\n' + defs + shapes
for code in ORDER:
    frag += '<clipPath id="k5-%s">%s</clipPath>\n' % (code, ''.join('<use href="#%s"/>' % i for i in ids[code]))
frag += '</defs>\n'
countries = {}
for code in ORDER:
    countries[code] = {'n': NAMES[code], 'r': 'A', 'a': 1000, 't': 1}
    frag += '<g class="deco">\n' + ''.join('<use href="#%s" transform="translate(2 3)" fill="#000" opacity=".4"/>\n' % i for i in ids[code]) + '</g>\n'
    for d in BONES[code]: frag += '<path class="c bone5" data-c="%s" d="%s" fill-rule="evenodd"/>\n' % (code, d)
    fx = '<g clip-path="url(#k5-%s)"><rect x="0" y="0" width="400" height="800" fill="url(#p5)"/>' % code
    fx += ''.join('<use href="#%s" fill="none" stroke="#4A4330" stroke-width="5" opacity=".28"/>' % i for i in ids[code]) + '</g>\n'
    frag += '<g class="deco">\n' + fx + D.get(code, '') + '</g>\n'
open(os.path.join(ROOT, 'data/os5-paths.frag'), 'w', encoding='utf8').write(frag)
json.dump({'countries': countries, 'zones': {'tous': zb}, 'box': [0, 0, 400, 810]}, open(os.path.join(ROOT, 'data/os5.json'), 'w', encoding='utf8'), ensure_ascii=False, separators=(',', ':'))
css = ('.c.bone5,html[data-theme="halloween"] .c.bone5{fill:url(#b5);stroke:rgba(25,20,10,.8);stroke-width:.9px}'
       'body[data-page="os5"] .mapwrap{background:radial-gradient(ellipse at 50% 40%,#2E3A4A,#121921 88%);box-shadow:inset 0 0 0 2px #3C4A5C,inset 0 0 60px rgba(0,0,0,.45),var(--shadow)}'
       'html[data-theme="halloween"] body[data-page="os5"] .mapwrap{background:radial-gradient(ellipse at 50% 40%,#2E3347,#101320 88%);box-shadow:inset 0 0 0 2px #4a3a6a,inset 0 0 60px rgba(0,0,0,.45),var(--shadow)}')
p = os.path.join(ROOT, 'src/styles.css'); s = open(p, encoding='utf8').read()
block = '/*OS5*/' + css + '/*/OS5*/'
s = re.sub(r'/\*OS5\*/.*?/\*/OS5\*/', lambda m: block, s) if '/*OS5*/' in s else s.rstrip('\n') + '\n\n/* Squelette réaliste (jeu « Situer les os », 5ème) */\n' + block + '\n'
open(p, 'w', encoding='utf8').write(s)
print('data/os5-paths.frag', len(frag) // 1024, 'Ko |', len(countries), 'os |', sum(len(v) for v in BONES.values()), 'formes')
