#!/usr/bin/env python3
"""Gera a cena em pixel art do topo do site (360x216 px, exibida ampliada sem suavização).

Uso:  python3 gerar_cena.py            -> escreve hero.png ao lado deste arquivo
Requer: pip install pillow
Tudo é desenhado por código, então a cena é original e fácil de ajustar (cores, posições, semente).
"""
import math
import random
from pathlib import Path
from PIL import Image

W, H = 360, 216
PAPEL = (0xF5, 0xF4, 0xEF)  # tem de ser igual a --papel no CSS
rnd = random.Random(42)


def hx(s):
    s = s.lstrip('#')
    return tuple(int(s[i:i + 2], 16) for i in (0, 2, 4))


img = Image.new('RGB', (W, H), PAPEL)
P = img.load()


def put(x, y, c):
    if 0 <= x < W and 0 <= y < H:
        P[x, y] = c


def rect(x0, y0, x1, y1, c):
    for y in range(int(y0), int(y1)):
        for x in range(int(x0), int(x1)):
            put(x, y, c)


def disc(cx, cy, r, c, ry=None):
    ry = ry or r
    for y in range(int(cy - ry) - 1, int(cy + ry) + 2):
        for x in range(int(cx - r) - 1, int(cx + r) + 2):
            if ((x - cx) / r) ** 2 + ((y - cy) / ry) ** 2 <= 1:
                put(x, y, c)


BAYER = [[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]


def dmix(x, y, a, b, t):
    return b if BAYER[y % 4][x % 4] / 16 < t else a


# ---------- Céu (degradê com pontilhado) ----------
SKY = [hx(c) for c in ['0B67C7', '1479DB', '2E93EA', '5AB0F2', '8ECFF7', 'BDE6FB']]
HORIZON = 142
for y in range(0, HORIZON + 12):
    f = min(1, (y / HORIZON) ** 1.7) * (len(SKY) - 1)
    i = min(int(f), len(SKY) - 2)
    t = f - i
    for x in range(W):
        put(x, y, dmix(x, y, SKY[i], SKY[i + 1], t))

# ---------- Nuvens ----------
CL1, CL2, CL3 = hx('FFFFFF'), hx('D3E9FB'), hx('A9D2F4')


def cloud(cx, cy, w, h, seed):
    r = random.Random(seed)
    mask = set()
    for _ in range(int(w / 6) + 3):
        ccx = cx + r.uniform(-w / 2, w / 2)
        rr = r.uniform(h * 0.35, h * 0.6)
        ccy = cy - (1 - abs(ccx - cx) / (w / 2)) * h * 0.35 + r.uniform(-1, 1)
        for y in range(int(ccy - rr), int(ccy + rr) + 1):
            for x in range(int(ccx - rr), int(ccx + rr) + 1):
                if (x - ccx) ** 2 + (y - ccy) ** 2 <= rr * rr and y <= cy + h * 0.18:
                    mask.add((x, y))
    cols = {}
    for (x, y) in mask:
        cols.setdefault(x, []).append(y)
    for x, ys in cols.items():
        bot = max(ys)
        for y in ys:
            d = bot - y
            put(x, y, CL3 if d <= 1 else CL2 if d <= 4 else CL1)


# Sem nuvens na zona do texto (canto superior esquerdo): o título é branco e precisa de céu azul.
for i, (cx, cy, w, h) in enumerate([(262, 46, 74, 24), (300, 112, 84, 28),
                                    (36, 130, 60, 20), (150, 134, 56, 16)]):
    cloud(cx, cy, w, h, 100 + i)

# ---------- Cidade ao longe ----------
BLD = [hx('7FA9D6'), hx('6F9CCB'), hx('92B7DF')]
WIN = hx('DCEEFB')
x = 200
while x < 284:
    bw = rnd.randint(6, 11)
    bh = rnd.randint(12, 32)
    c = rnd.choice(BLD)
    rect(x, 140 - bh, x + bw, 142, c)
    for wy in range(140 - bh + 3, 138, 4):
        for wx in range(x + 2, x + bw - 1, 3):
            if rnd.random() < 0.7:
                put(wx, wy, WIN)
    x += bw + rnd.randint(0, 2)
rect(263, 84, 267, 142, hx('86AED6'))  # torre
rect(264, 76, 266, 84, hx('86AED6'))
put(265, 74, hx('FFFFFF'))

# ---------- Colinas ----------
GRASS_FAR = [hx('78B65E'), hx('8FC968'), hx('64A552')]
GRASS_MID = [hx('4E9E48'), hx('67B554'), hx('3F8A3F')]
GRASS_NEAR = [hx('3A8A3C'), hx('4FA04A'), hx('2C7433')]


def hill(topfn, pal, x0=0, x1=W):
    base, light, dark = pal
    for x in range(x0, x1):
        top = int(topfn(x))
        for y in range(max(top, 0), H):
            r = rnd.random()
            c = base
            if y - top < 2:
                c = light
            elif r < 0.06:
                c = light
            elif r < 0.14:
                c = dark
            put(x, y, c)


hill(lambda x: 138 + 5 * math.sin(x / 45) + 3 * math.sin(x / 17), GRASS_FAR)


# ---------- Árvores ----------
def canopy(cx, cy, r, pal):
    for y in range(int(cy - r) - 1, int(cy + r) + 2):
        for x in range(int(cx - r) - 1, int(cx + r) + 2):
            dx, dy = (x - cx) / r, (y - cy) / r
            if dx * dx + dy * dy <= 1:
                lit = -0.6 * dx - 0.8 * dy + rnd.uniform(-0.25, 0.25)
                put(x, y, pal[0] if lit < -0.35 else pal[1] if lit < 0.25 else pal[2] if lit < 0.6 else pal[3])


LEAF = [hx('1F5A2D'), hx('2C6B34'), hx('3C8442'), hx('5BA14A')]
TRUNK = [hx('4A3222'), hx('6B4A32'), hx('8A6444')]


def tree(cx, base, r):
    th = int(r * 1.1)
    rect(cx - 1, base - th, cx + 2, base, TRUNK[1])
    rect(cx + 1, base - th, cx + 2, base, TRUNK[0])
    cy = base - th - r * 0.5
    canopy(cx, cy, r, LEAF)
    canopy(cx - r * 0.65, cy + r * 0.35, r * 0.7, LEAF)
    canopy(cx + r * 0.65, cy + r * 0.3, r * 0.72, LEAF)


# ---------- Escola ----------
def escola(x0, base):
    WALL, SHADE = hx('F2D27A'), hx('D9B45E')
    ROOF, ROOF2 = hx('B5452E'), hx('8E3322')
    rect(x0, base - 22, x0 + 50, base, WALL)
    rect(x0, base - 3, x0 + 50, base, SHADE)
    rect(x0 - 2, base - 26, x0 + 52, base - 22, ROOF)
    rect(x0 - 2, base - 23, x0 + 52, base - 22, ROOF2)
    for i in range(6):
        wx = x0 + 4 + i * 8
        if i == 3:
            continue
        rect(wx, base - 16, wx + 5, base - 9, hx('4D8FD6'))
        rect(wx, base - 12, wx + 5, base - 11, hx('2F6BB5'))
    rect(x0 + 21, base - 11, x0 + 29, base, hx('6B4A32'))
    rect(x0 + 24, base - 11, x0 + 25, base, hx('4A3222'))
    # torre
    rect(x0 + 19, base - 40, x0 + 31, base - 26, WALL)
    for i in range(7):
        rect(x0 + 18 + i, base - 41 - i, x0 + 32 - i, base - 40 - i, ROOF)
    disc(x0 + 25, base - 34, 3, hx('FFFFFF'))
    put(x0 + 25, base - 35, hx('333333'))
    put(x0 + 25, base - 34, hx('333333'))
    put(x0 + 26, base - 34, hx('333333'))
    rect(x0 + 25, base - 56, x0 + 26, base - 47, hx('555555'))
    rect(x0 + 26, base - 56, x0 + 31, base - 53, hx('FFD34D'))


tree(30, 150, 13)
tree(66, 145, 8)
escola(142, 142)
tree(122, 146, 9)
tree(198, 142, 6)

# ---------- Colina do meio ----------
hill(lambda x: 148 + 6 * math.sin(x / 38 + 1) + 2 * math.sin(x / 13), GRASS_MID)
# ---------- Colina da frente (some à esquerda, perto do rio) ----------
hill(lambda x: 170 + 5 * math.sin(x / 28) + max(0, 150 - x) * 1.3, GRASS_NEAR, 90, W)

# ---------- Rio ----------
WATER, WATER_L, WATER_D, BANK = hx('2F7FD6'), hx('8FD0FA'), hx('1F63B8'), hx('D9C58F')


def rio_cx(t):
    return 152 - t * 1.6 + 9 * math.sin(t / 12.0)


def rio_w(t):
    return 2 + t * 0.42


for y in range(144, H):
    t = y - 144
    cx, w = rio_cx(t), rio_w(t)
    for x in range(int(cx - w) - 1, int(cx + w) + 2):
        d = abs(x - cx)
        if d <= w:
            c = WATER
            if rnd.random() < 0.05:
                c = WATER_L
            elif rnd.random() < 0.08:
                c = WATER_D
            put(x, y, c)
        elif d <= w + 1.5:
            put(x, y, BANK)
for _ in range(90):  # brilhos horizontais
    y = rnd.randint(150, 205)
    t = y - 144
    x = int(rio_cx(t) + rnd.uniform(-rio_w(t) + 2, rio_w(t) - 3))
    for k in range(rnd.randint(2, 4)):
        put(x + k, y, WATER_L)

# ---------- Banco ----------
rect(40, 168, 58, 170, hx('8A6444'))
rect(40, 163, 58, 165, hx('8A6444'))
rect(41, 170, 43, 174, hx('4A3222'))
rect(55, 170, 57, 174, hx('4A3222'))
rect(41, 165, 43, 168, hx('4A3222'))
rect(55, 165, 57, 168, hx('4A3222'))

# ---------- Arbustos da frente (esquerda e base) ----------
BUSH = [hx('164A25'), hx('1F5E2D'), hx('2C7A38'), hx('5BA14A')]


def bush(cx, cy, r):
    for k in range(3):
        canopy(cx + (k - 1) * r * 0.8, cy + (k % 2) * 3, r, BUSH)


for bx in range(-10, 90, 17):
    bush(bx, 206, 11)
bush(150, 214, 12)
bush(120, 216, 12)

# ---------- Notebook computer (laptop) ----------
LX, LY = 224, 134
rect(LX, LY, LX + 62, LY + 42, hx('3A3D45'))
for y in range(LY + 2, LY + 40):
    f = (y - LY - 2) / 38
    for xx in range(LX + 2, LX + 60):
        put(xx, y, dmix(xx, y, hx('3E9DEB'), hx('9AD6F8'), f))
for cx, cy, w in [(LX + 14, LY + 12, 14), (LX + 44, LY + 9, 11)]:
    for y in range(cy - 3, cy + 3):
        rect(cx - w // 2, y, cx + w // 2, y + 1, hx('FFFFFF'))
    rect(cx - w // 2 + 2, cy - 4, cx + w // 2 - 2, cy - 3, hx('FFFFFF'))
# símbolos da Trama na tela
disc(LX + 14, LY + 28, 4, hx('FFFFFF'))
rect(LX + 22, LY + 24, LX + 30, LY + 32, hx('FFD34D'))
for i in range(5):
    rect(LX + 36 - i, LY + 24 + i * 2, LX + 38 + i + 1, LY + 26 + i * 2, hx('FF9A3D'))
for i in range(5):
    rect(LX + 50 - i, LY + 24 + i, LX + 52 + i, LY + 25 + i, hx('FF8FB8'))
    rect(LX + 50 - i, LY + 32 - i, LX + 52 + i, LY + 33 - i, hx('FF8FB8'))
rect(LX - 2, LY + 42, LX + 64, LY + 44, hx('2D2F36'))
for y in range(LY + 44, LY + 54):
    f = (y - LY - 44) / 10
    x0 = LX - 6 - int(f * 6)
    x1 = LX + 68 + int(f * 6)
    rect(x0, y, x1, y + 1, hx('A7ABB3') if y < LY + 52 else hx('6E727A'))
for y in range(LY + 45, LY + 50):
    for xx in range(LX + 4, LX + 58):
        put(xx, y, hx('4C4F57') if (xx + y) % 3 else hx('7A7E87'))
rect(LX - 14, LY + 54, LX + 76, LY + 57, hx('245C2B'))

# ---------- Notebook ----------
for y in range(191, 203):
    off = int((202 - y) * 0.55)
    rect(262 + off, y, 318 + off, y + 1, hx('5E4B34'))
for y in range(191, 195):
    off = int((202 - y) * 0.55)
    rect(264 + off, y, 316 + off, y + 1, hx('E9E3D2'))
for k in range(5):
    rect(262 + int(14 * 0.55) - 1 + k * 0, 193 + k * 2, 263 + int(11 * 0.55), 194 + k * 2, hx('A7ABB3'))
for k in range(26):
    put(282 + k, 198 - int(k * 0.33), hx('3B3F9A'))
    put(282 + k, 199 - int(k * 0.33), hx('3B3F9A'))
put(308, 190, hx('E7C58F'))
put(309, 190, hx('E7C58F'))

# ---------- Girassol ----------
SX, SB = 196, 197
rect(SX, SB - 36, SX + 2, SB, hx('2C6B34'))
rect(SX - 5, SB - 18, SX, SB - 15, hx('3C8442'))
rect(SX + 2, SB - 24, SX + 7, SB - 21, hx('3C8442'))
for a in range(0, 360, 30):
    px_ = SX + 1 + 7 * math.cos(math.radians(a))
    py_ = SB - 40 + 7 * math.sin(math.radians(a))
    disc(px_, py_, 2.6, hx('F2C230'))
disc(SX + 1, SB - 40, 4, hx('6B4A32'))
put(SX, SB - 41, hx('8A6444'))
put(SX + 2, SB - 39, hx('4A3222'))

# ---------- Árvore grande (direita) ----------
for y in range(60, 212):
    f = (y - 60) / 152
    l = int(322 - f * f * 18)
    r = int(344 + f * f * 22)
    for xx in range(l, r):
        c = TRUNK[1]
        if xx > r - 5:
            c = TRUNK[0]
        elif xx < l + 4:
            c = TRUNK[2]
        if rnd.random() < 0.06:
            c = TRUNK[0]
        put(xx, y, c)
for cx, cy, r in [(292, 34, 34), (330, 14, 40), (352, 58, 34), (310, 62, 28), (270, 8, 30), (340, 40, 34)]:
    canopy(cx, cy, r, LEAF)
for _ in range(500):
    x_, y_ = rnd.randint(262, 359), rnd.randint(0, 92)
    if P[x_, y_] in LEAF:
        put(x_, y_, rnd.choice(LEAF))

# ---------- Flores ----------
FL = [hx('D6342C'), hx('F2C230'), hx('FFFFFF'), hx('E58AB0')]
for _ in range(70):
    x_ = rnd.randint(228, 356)
    y_ = rnd.randint(172, 194)
    if 300 < x_ < 346 and y_ < 200:
        continue
    c = rnd.choice(FL)
    put(x_, y_, c)
    put(x_ + 1, y_, c)
    put(x_, y_ + 1, hx('2C6B34'))

# ---------- Borda que se dissolve em pixels ----------
for y in range(H - 12, H):
    p = ((y - (H - 12)) / 12) ** 1.4
    for x in range(0, W, 2):
        if rnd.random() < p:
            for dy in (0, 1):
                for dx in (0, 1):
                    put(x + dx, y + dy - (y % 2), PAPEL)
rect(0, H - 2, W, H, PAPEL)

saida = Path(__file__).with_name('hero.png')
img.save(saida, optimize=True)
print('ok', saida, img.size)
