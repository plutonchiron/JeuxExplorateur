#!/usr/bin/env python3
"""Relief du jeu « Eaux et montagnes » : VECTORISE la carte physique de référence (scripts/ref/carte-relief.png,
fournie par le propriétaire : vert < 200 m, beige 200-500 m, bruns 500-1000 / 1000-2000 m, brun foncé > 2000 m).
  1. l'image est lue (décodeur PNG maison, sans dépendance) et chaque pixel classé dans l'une des 5 couleurs de la légende ;
     textes, rivières et ombrages sont absorbés par un filtre de majorité ;
  2. la carte de l'image est recalée sur la carte de France du jeu (polynôme d'ordre 2 ajusté une fois pour toutes en
     maximisant le recouvrement des deux silhouettes : POLY ; Corse : transformation simple) ;
  3. pour chaque palier d'altitude, les contours sont tracés (suivi de bord), simplifiés puis lissés ;
  4. les massifs cliquables (Pyrénées, Alpes, Massif central, Vosges, Jura) sont les zones > 500 m de la référence.
Réécrit le bloc <!--RELIEF--> de data/eaux-paths.frag et le bloc /*RELIEF*/ de src/styles.css.
Relançable à volonté ; Python 3 sans dépendance, hors ligne."""
import re, os, zlib, struct
from collections import deque
root = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
FRAG = os.path.join(root, 'data', 'eaux-paths.frag'); CSS = os.path.join(root, 'src', 'styles.css')
REF = os.path.join(root, 'scripts', 'ref', 'carte-relief.png')

# --- lecture PNG (8 bits RVB, sans entrelacement) ---
def read_png(path):
    b = open(path, 'rb').read(); i = 8; idat = b''
    while i < len(b):
        n, t = struct.unpack('>I4s', b[i:i + 8]); d = b[i + 8:i + 8 + n]; i += 12 + n
        if t == b'IHDR': w, h, bd, ct, _, _, il = struct.unpack('>IIBBBBB', d)
        elif t == b'IDAT': idat += d
    assert bd == 8 and ct in (2, 6) and il == 0
    bpp = 3 if ct == 2 else 4; raw = zlib.decompress(idat); stride = w * bpp; rows = []; prev = bytearray(stride); p = 0
    for y in range(h):
        f = raw[p]; line = bytearray(raw[p + 1:p + 1 + stride]); p += 1 + stride
        for x in range(stride):
            a = line[x - bpp] if x >= bpp else 0; up = prev[x]; c = prev[x - bpp] if x >= bpp else 0
            if f == 1: line[x] = (line[x] + a) & 255
            elif f == 2: line[x] = (line[x] + up) & 255
            elif f == 3: line[x] = (line[x] + ((a + up) >> 1)) & 255
            elif f == 4:
                pa = abs(up - c); pb = abs(a - c); pc = abs(a + up - 2 * c)
                line[x] = (line[x] + (a if pa <= pb and pa <= pc else (up if pb <= pc else c))) & 255
        rows.append(line); prev = line
    return w, h, [[tuple(r[x * bpp:x * bpp + 3]) for x in range(w)] for r in rows]

# couleurs de la légende de la référence
PAL = [(190, 223, 134), (236, 182, 138), (172, 118, 92), (147, 97, 72), (75, 57, 33)]
HEX = ['#BEDF86', '#ECB68A', '#AC765C', '#936148', '#4B3921']
# recalage : (X, Y) du jeu -> (x, y) de l'image, u = X/1000, v = Y/1000 : a + b·u + c·v + d·u² + e·u·v + f·v²
POLY = [[-15.727, 675.560, -14.459, 0.229, 22.146, -0.204], [1.683, -0.601, 686.924, -5.095, -2.500, 3.928]]
STEP = 2                                          # pas de la grille de travail, en unités du jeu

# projection du fichier (vérifiée sur Annecy, Léman, Grand-Lieu, Thau) : (lon, lat) -> (x, y)
def P(lon, lat): return (748 + (lon - 6.17) * 65.4, 505 - (lat - 45.87) * 95)

W, H, px = read_png(REF)
def nearest(p):
    bd, k = 1e9, -1
    for i, c in enumerate(PAL):
        d = (p[0] - c[0]) ** 2 + (p[1] - c[1]) ** 2 + (p[2] - c[2]) ** 2
        if d < bd: bd, k = d, i
    return k if bd < 40 * 40 else -1
C = [[nearest(px[y][x]) for x in range(W)] for y in range(H)]

# masque de la France dans l'image : pixels de couleur connue, fermés puis gardés s'ils touchent le gros morceau
def dil(m, r):
    rows = [[False] * W for _ in range(H)]
    for y in range(H):
        for x in range(W):
            if m[y][x]:
                for u in range(max(0, x - r), min(W, x + r + 1)): rows[y][u] = True
    o = [[False] * W for _ in range(H)]
    for y in range(H):
        for yy in range(max(0, y - r), min(H, y + r + 1)):
            ry = rows[yy]; oy = o[y]
            for x in range(W):
                if ry[x]: oy[x] = True
    return o
cl = dil([[v >= 0 for v in r] for r in C], 4)
cl = [[not v for v in r] for r in dil([[not v for v in r] for r in cl], 4)]
seen = [bytearray(W) for _ in range(H)]; comps = []
for y in range(H):
    for x in range(W):
        if cl[y][x] and not seen[y][x]:
            q = deque([(x, y)]); seen[y][x] = 1; pts = []
            while q:
                a, b = q.popleft(); pts.append((a, b))
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    u, v = a + dx, b + dy
                    if 0 <= u < W and 0 <= v < H and cl[v][u] and not seen[v][u]: seen[v][u] = 1; q.append((u, v))
            comps.append(pts)
comps.sort(key=len, reverse=True)
inside = [bytearray(W) for _ in range(H)]
for pts in comps:
    if len(pts) > 2000 and not (pts[0][0] < 100 and 300 < pts[0][1] < 450):          # métropole + Corse (pas la légende)
        for x, y in pts: inside[y][x] = 1

# un pixel brun foncé n'est un vrai sommet que s'il est entouré de relief (≥ 500 m) : sinon c'est une lettre noire de la carte
Ih = [[0] * (W + 1) for _ in range(H + 1)]
for y in range(H):
    t = 0
    for x in range(W):
        t += 1 if C[y][x] >= 2 else 0; Ih[y + 1][x + 1] = Ih[y][x + 1] + t
for y in range(H):
    for x in range(W):
        if C[y][x] >= 3:
            x0, x1, y0, y1 = max(0, x - 6), min(W, x + 7), max(0, y - 6), min(H, y + 7)
            if (Ih[y1][x1] - Ih[y0][x1] - Ih[y1][x0] + Ih[y0][x0]) * 100 < 35 * (x1 - x0) * (y1 - y0): C[y][x] = -1
# filtre de majorité (rayon 3) sur les pixels de couleur connue, puis propagation jusqu'aux bords du masque
R = 3
acc = []
for k in range(5):
    I = [[0] * (W + 1) for _ in range(H + 1)]
    for y in range(H):
        s = 0; Iy, Iu = I[y + 1], I[y]
        for x in range(W):
            if C[y][x] == k and inside[y][x]: s += 1
            Iy[x + 1] = Iu[x + 1] + s
    acc.append(I)
F = [[-1] * W for _ in range(H)]; q = deque()
for y in range(H):
    for x in range(W):
        if not inside[y][x]: continue
        x0, x1, y0, y1 = max(0, x - R), min(W, x + R + 1), max(0, y - R), min(H, y + R + 1)
        best, bn = -1, 0
        for k in range(5):
            I = acc[k]; n = I[y1][x1] - I[y0][x1] - I[y1][x0] + I[y0][x0]
            if n > bn: bn, best = n, k
        if best >= 0: F[y][x] = best; q.append((x, y))
while q:                                          # le reste (textes épais, bords) prend la classe du voisin le plus proche
    x, y = q.popleft()
    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        u, v = x + dx, y + dy
        if 0 <= u < W and 0 <= v < H and F[v][u] < 0: F[v][u] = F[y][x]; q.append((u, v))

# les petites taches sombres isolées sont des lettres (« Plateau lorrain », « Flandres »…), pas des sommets : elles reprennent la classe en dessous
def small_blobs(k, minpx):
    seen = [bytearray(W) for _ in range(H)]
    for y in range(H):
        for x in range(W):
            if F[y][x] >= k and not seen[y][x]:
                q = deque([(x, y)]); seen[y][x] = 1; pts = []
                while q:
                    a, b = q.popleft(); pts.append((a, b))
                    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        u, v = a + dx, b + dy
                        if 0 <= u < W and 0 <= v < H and F[v][u] >= k and not seen[v][u]: seen[v][u] = 1; q.append((u, v))
                if len(pts) < minpx:
                    for a, b in pts: F[b][a] = k - 1
small_blobs(4, 250); small_blobs(3, 120)

# --- classe en chaque point de la grille du jeu ---
GW, GH = 490, 475                                 # 980 × 950 unités
def img_xy(X, Y):
    if X >= 900 and Y >= 770: return 528 + (X - 904.2) * .67, 506 + (Y - 778.4) * .655          # Corse (encadré de la carte)
    u, v = X / 1000, Y / 1000
    return (POLY[0][0] + POLY[0][1] * u + POLY[0][2] * v + POLY[0][3] * u * u + POLY[0][4] * u * v + POLY[0][5] * v * v,
            POLY[1][0] + POLY[1][1] * u + POLY[1][2] * v + POLY[1][3] * u * u + POLY[1][4] * u * v + POLY[1][5] * v * v)
G = [[0] * GW for _ in range(GH)]
for j in range(GH):
    for i in range(GW):
        x, y = img_xy(i * STEP + STEP / 2, j * STEP + STEP / 2)
        G[j][i] = F[min(H - 1, max(0, int(y)))][min(W - 1, max(0, int(x)))]

def blur_bin(B, r):                               # flou en boîte puis seuil à 50 % : arrondit les contours, efface les taches
    Ig = [[0] * (GW + 1) for _ in range(GH + 1)]
    for j in range(GH):
        s = 0
        for i in range(GW):
            s += B[j][i]; Ig[j + 1][i + 1] = Ig[j][i + 1] + s
    o = [[0] * GW for _ in range(GH)]
    for j in range(GH):
        for i in range(GW):
            x0, x1, y0, y1 = max(0, i - r), min(GW, i + r + 1), max(0, j - r), min(GH, j + r + 1)
            n = Ig[y1][x1] - Ig[y0][x1] - Ig[y1][x0] + Ig[y0][x0]
            o[j][i] = 1 if 2 * n > (x1 - x0) * (y1 - y0) else 0
    return o

def loops(B):                                     # contours d'une grille binaire (suivi de bord) : liste de boucles de sommets (i, j)
    nxt = {}
    for j in range(GH):
        for i in range(GW):
            if not B[j][i]: continue
            if j == 0 or not B[j - 1][i]: nxt.setdefault((i, j), []).append((i + 1, j))
            if i == GW - 1 or not B[j][i + 1]: nxt.setdefault((i + 1, j), []).append((i + 1, j + 1))
            if j == GH - 1 or not B[j + 1][i]: nxt.setdefault((i + 1, j + 1), []).append((i, j + 1))
            if i == 0 or not B[j][i - 1]: nxt.setdefault((i, j + 1), []).append((i, j))
    out = []
    while nxt:
        s = next(iter(nxt)); cur = s; pts = [s]
        while True:
            e = nxt[cur]; n = e.pop()
            if not e: del nxt[cur]
            cur = n
            if cur == s: break
            pts.append(cur)
            if cur not in nxt: break
        out.append(pts)
    return out

def dp(pts, eps):                                 # Douglas-Peucker sur une boucle
    def rec(a, b, keep):
        (x0, y0), (x1, y1) = pts[a], pts[b]; dx, dy = x1 - x0, y1 - y0; n = (dx * dx + dy * dy) ** .5 or 1; m, k = 0, -1
        for i in range(a + 1, b):
            d = abs((pts[i][0] - x0) * dy - (pts[i][1] - y0) * dx) / n
            if d > m: m, k = d, i
        if m > eps: keep.add(k); rec(a, k, keep); rec(k, b, keep)
    h = len(pts) // 2; keep = {0, h}; rec(0, h, keep); rec(h, len(pts) - 1, keep)
    return [pts[i] for i in sorted(keep)]

def area(pts): return sum(pts[i][0] * pts[(i + 1) % len(pts)][1] - pts[(i + 1) % len(pts)][0] * pts[i][1] for i in range(len(pts))) / 2

def path(B, minarea=12, eps=.8):                  # grille -> chemin SVG lissé (courbes passant par les milieux des segments)
    d = ''
    for pts in loops(B):
        if abs(area(pts)) < minarea or len(pts) < 4: continue
        pts = dp(pts, eps)
        if len(pts) < 3: continue
        xy = [(p[0] * STEP, p[1] * STEP) for p in pts]; n = len(xy)
        mid = [((xy[i][0] + xy[(i + 1) % n][0]) / 2, (xy[i][1] + xy[(i + 1) % n][1]) / 2) for i in range(n)]
        d += 'M%.1f,%.1f' % mid[-1]
        for i in range(n): d += 'Q%.1f,%.1f %.1f,%.1f' % (xy[i] + mid[i])
        d += 'Z'
    return d

# --- silhouette de la France (tous les départements) : un seul tracé pour découper le relief, sans raccords visibles ---
src = open(FRAG, encoding='utf8').read()
src = re.sub(r'<!--RELIEF-->.*?<!--/RELIEF-->\n?', '', src, flags=re.S)
src = re.sub(r'<path class="c mtn"[^\n]*\n', '', src)
src = re.sub(r'<defs>.*?</defs>\n?', '', src, count=1, flags=re.S)
polys = []
for m in re.finditer(r'<path class="land"(?: id="fr\d+")? d="([^"]+)"', src):
    polys.append([[tuple(map(float, a.split(','))) for a in re.findall(r'-?\d+\.?\d*,-?\d+\.?\d*', part)] for part in re.findall(r'M[^M]+', m.group(1))])
cross = {}
for sp in polys:
    for sub in sp:
        n = len(sub)
        for i in range(n):
            (x0, y0), (x1, y1) = sub[i], sub[(i + 1) % n]
            if y0 == y1: continue
            for j in range(max(0, int((min(y0, y1)) / STEP - .5) ), min(GH, int(max(y0, y1) / STEP + .5) + 1)):
                yy = j * STEP + STEP / 2
                if (y0 <= yy < y1) or (y1 <= yy < y0): cross.setdefault((j, id(sub)), []).append(x0 + (yy - y0) * (x1 - x0) / (y1 - y0))
SIL = [[0] * GW for _ in range(GH)]
for (j, _), xs in cross.items():
    xs.sort()
    for k in range(0, len(xs) - 1, 2):
        for i in range(max(0, int((xs[k] - STEP / 2) / STEP + .999)), min(GW, int((xs[k + 1] - STEP / 2) / STEP) + 1)): SIL[j][i] ^= 1
clip = '<clipPath id="frclip"><path d="%s"/></clipPath>' % path(SIL, 4, .5)

# --- paliers : ≥ 200 m, ≥ 500 m, ≥ 1000 m, ≥ 2000 m, empilés sur le vert des départements ---
SILD = [[1 if any(0 <= j + b < GH and 0 <= i + a < GW and SIL[j + b][i + a] for a in (-1, 0, 1) for b in (-1, 0, 1)) else 0 for i in range(GW)] for j in range(GH)]   # silhouette + 1 cellule
LV = [blur_bin([[1 if G[j][i] >= k else 0 for i in range(GW)] for j in range(GH)], 2) for k in range(1, 5)]
LV = [[[B[j][i] & SILD[j][i] for i in range(GW)] for j in range(GH)] for B in LV]                  # rien en mer
rel = '<!--RELIEF-->\n<defs>' + clip + '</defs>\n<g class="deco keep" clip-path="url(#frclip)">'
for k, B in enumerate(LV): rel += '<path fill="%s" d="%s"/>' % (HEX[k + 1], path(B, 14, .8))
rel += '</g>\n'

# --- massifs cliquables : la zone > 500 m de la référence qui contient le point de départ, élargie pour être facile à viser ---
SEEDS = {'pyrenees': ((0.5, 42.85), 'les Pyrénées'), 'alpes': ((6.9, 45.0), 'les Alpes'), 'massif-central': ((2.9, 45.3), 'le Massif central'),
         'vosges': ((7.0, 48.05), 'les Vosges'), 'jura': ((5.9, 46.7), 'le Jura')}
def lonlat(i, j): return 6.17 + (i * STEP + STEP / 2 - 748) / 65.4, 45.87 - (j * STEP + STEP / 2 - 505) / 95
def side(lon, lat): return (lat - 45.7) * 1.0 - (lon - 5.4) * .75               # > 0 : côté nord-ouest de la ligne Jura / Alpes
TERR = {                                        # territoire de chaque massif (la zone > 500 m s'arrête là : le Jura touche les Alpes)
  'pyrenees': lambda lo, la: -2.3 < lo < 3.4 and 42.2 < la < 43.5,
  'alpes': lambda lo, la: lo > 5.0 and la < 46.6 and side(lo, la) <= 0,
  'massif-central': lambda lo, la: 1.0 < lo < 4.7 and 43.5 < la < 46.4,
  'vosges': lambda lo, la: 6.2 < lo < 7.8 and 47.5 < la < 49.1,
  'jura': lambda lo, la: lo > 5.3 and la < 47.7 and side(lo, la) > 0}
def component(B, i0, j0, ok):
    best = None
    for r in range(0, 40):                        # cellule de zone la plus proche du point de départ
        for j in range(max(0, j0 - r), min(GH, j0 + r + 1)):
            for i in range(max(0, i0 - r), min(GW, i0 + r + 1)):
                if B[j][i] and ok(*lonlat(i, j)): best = (i, j); break
            if best: break
        if best: break
    if not best: return None
    q = deque([best]); comp = {best}
    while q:
        i, j = q.popleft()
        for di, dj in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            a, b = i + di, j + dj
            if 0 <= a < GW and 0 <= b < GH and B[b][a] and (a, b) not in comp and ok(*lonlat(a, b)): comp.add((a, b)); q.append((a, b))
    return comp
def grow(comp, r):
    out = set()
    for i, j in comp:
        for a in range(i - r, i + r + 1):
            for b in range(j - r, j + r + 1):
                if 0 <= a < GW and 0 <= b < GH: out.add((a, b))
    return out
mass = ''
for code, ((lon, lat), name) in SEEDS.items():
    X, Y = P(lon, lat); comp = component(LV[1], int(X / STEP), int(Y / STEP), TERR[code])
    if not comp: print('!! massif introuvable :', code); continue
    r = 0
    while True:                                   # assez large pour être cliquable : au moins ~ 30 unités de côté
        big = grow(comp, r) if r else comp
        xs = [c[0] for c in big]; ys = [c[1] for c in big]
        if min(max(xs) - min(xs), max(ys) - min(ys)) * STEP >= 30 or r >= 6: break
        r += 1
    B = [[0] * GW for _ in range(GH)]
    for i, j in big: B[j][i] = 1
    print('massif', code, 'cellules', len(comp), '→', len(big), 'élargi de', r)
    mass += '<path class="c mtn" data-c="%s" clip-path="url(#frclip)" d="%s"/>\n' % (code, path(blur_bin(B, 1), 8, .8))
rel += mass + '<!--/RELIEF-->\n'
i = [m.end() for m in re.finditer(r'<path class="land"[^\n]*\n', src)][-1]                # après le dernier département
src = src[:i] + rel + src[i:]
open(FRAG, 'w', encoding='utf8').write(src)

css = open(CSS, encoding='utf8').read()
RULES = [                                       # (sélecteur, déclarations) ; répétées sous le thème Halloween, dont la règle « .c » est plus spécifique
  ('.c.mtn', 'fill:rgba(255,255,255,.003);stroke:none'),
  ('.c.sea', 'fill:#D6EEFA;stroke:none'),
  ('.c.river', 'stroke:#3FA6F2;stroke-width:2px;pointer-events:none'),                                      # trait fin visible
  ('.c.lake', 'fill:#3FA6F2;stroke:#1E6FC0'),
  ('.c.rhit,.c.rhit.ok,.c.rhit.ko,.c.rhit.show', 'stroke:rgba(255,255,255,.001)'),                         # zone de clic large, invisible
  ('.c.river.show', 'stroke:#16c55a;stroke-width:6px;animation:pulseS .5s steps(1,end) infinite alternate'),                # erreur : la bonne rivière clignote en vert
  ('.c.rhit.show', 'stroke:#fff;stroke-width:13px'),                                                       # bonne réponse après une erreur : liseré blanc autour du vert
  ('.c.mtn.show,.c.lake.show,.c.sea.show', 'stroke:#fff;stroke-width:5px'),
  ('.c.rhit:hover', 'stroke:rgba(255,214,10,.8)!important'),                                                # survol : on voit ce qui est sélectionné
  ('.c.mtn:hover', 'fill:rgba(255,255,255,.4);stroke:#fff;stroke-width:3px'),
  ('.c.lake:hover', 'stroke:#FFD60A;stroke-width:4px'),
  ('.c.sea:hover', 'fill:#B6DDF3')]
H = 'html[data-theme="halloween"] '
blk = '/*RELIEF*/.land{fill:%s;stroke:%s}.land.nb{fill:#E6E2D6;stroke:#D3CDBC}' % (HEX[0], HEX[0])
for pre in ('', H): blk += ''.join('%s{%s}' % (','.join(pre + x for x in sel.split(',')), body) for sel, body in RULES)
blk += '@keyframes pulseS{from{stroke:#16c55a}to{stroke:#9af2b8}}/*/RELIEF*/'
css = re.sub(r'/\*RELIEF\*/.*?/\*/RELIEF\*/', lambda m: blk, css, flags=re.S)
open(CSS, 'w', encoding='utf8').write(css)
print('OK relief :', len(polys), 'départements,', len(SEEDS), 'massifs,', len(src) // 1024, 'Ko')
