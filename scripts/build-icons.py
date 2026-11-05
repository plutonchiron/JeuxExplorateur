#!/usr/bin/env python3
"""Icônes de l'appli installable (PWA) : un petit globe sur fond violet, dessiné pixel par pixel (Python 3 sans
dépendance, hors ligne). Écrit src/pwa/icon-192.png, icon-512.png, icon-maskable-512.png (globe plus petit : Android
rogne jusqu'à 20 % sur les bords) et apple-touch-icon.png (180). Relançable : python3 scripts/build-icons.py"""
import os, zlib, struct, math
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'src', 'pwa')

def write_png(path, n, px):
    raw = b''.join(b'\0' + b''.join(bytes(p) for p in row) for row in px)
    def ch(t, d): return struct.pack('>I', len(d)) + t + d + struct.pack('>I', zlib.crc32(t + d) & 0xffffffff)
    open(path, 'wb').write(b'\x89PNG\r\n\x1a\n' + ch(b'IHDR', struct.pack('>IIBBBBB', n, n, 8, 2, 0, 0, 0)) + ch(b'IDAT', zlib.compress(raw, 9)) + ch(b'IEND', b''))

def mix(a, b, t): return tuple(a[i] + (b[i] - a[i]) * t for i in range(3))
HEX = lambda h: tuple(int(h[i:i + 2], 16) for i in (1, 3, 5))
V1, V2, SEA1, SEA2, LAND, WHITE = HEX('#9B7BFF'), HEX('#5B3FD8'), HEX('#5CC0FF'), HEX('#1E6FC0'), HEX('#2DCB6A'), (255, 255, 255)
LANDS = [(-.30, -.30, .34, .22), (-.12, .0, .20, .32), (.40, .08, .28, .24), (.12, .52, .34, .14), (-.52, .34, .18, .12), (.05, -.70, .30, .10)]   # (x, y, rx, ry) en rayons de globe

def color(u, v, scale):
    cx = cy = .5; R = .5 * scale
    bg = mix(V1, V2, (u + v) / 2)                          # fond : dégradé violet en diagonale
    dx, dy = u - cx, v - cy
    if math.hypot(dx - .012, dy - .02) < R * 1.09: bg = mix(bg, (30, 10, 90), .35)       # ombre portée
    d = math.hypot(dx, dy)
    if d < R:
        x, y = dx / R, dy / R
        c = mix(SEA1, SEA2, (y + 1) / 2 * .8 + (x + 1) / 2 * .2)                            # océan
        for k, (lx, ly, rx, ry) in enumerate(LANDS):                                        # continents : ellipses au bord ondulé
            a = math.atan2((y - ly) / ry, (x - lx) / rx)
            if ((x - lx) / rx) ** 2 + ((y - ly) / ry) ** 2 < (1 + .22 * math.sin(3 * a + k * 2.1) + .12 * math.sin(5 * a + k)) ** 2:
                c = mix(LAND, (22, 140, 70), (y + 1) / 2); break
        if d > R * .86: c = mix(c, (10, 40, 110), (d / R - .86) / .14 * .45)                # bord sombre : effet de volume
        if math.hypot(x + .38, y + .45) < .22: c = mix(c, WHITE, .35 * (1 - math.hypot(x + .38, y + .45) / .22))   # reflet
        return c
    if d < R * 1.075: return WHITE                           # anneau blanc
    return bg

def render(n, scale):
    ss = 2; rows = []
    for j in range(n):
        row = []
        for i in range(n):
            acc = [0, 0, 0]
            for a in range(ss):
                for b in range(ss):
                    c = color((i + (a + .5) / ss) / n, (j + (b + .5) / ss) / n, scale)
                    for k in range(3): acc[k] += c[k]
            row.append(tuple(int(v / (ss * ss) + .5) for v in acc))
        rows.append(row)
    return rows

os.makedirs(OUT, exist_ok=True)
for name, n, sc in (('icon-512.png', 512, .80), ('icon-192.png', 192, .80), ('icon-maskable-512.png', 512, .58), ('apple-touch-icon.png', 180, .80)):
    write_png(os.path.join(OUT, name), n, render(n, sc)); print('OK', name)
