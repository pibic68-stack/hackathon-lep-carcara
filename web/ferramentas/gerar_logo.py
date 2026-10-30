"""Gera o logo pixel do PRISMA: um prisma que recebe um feixe e solta um arco-íris
(um material entra, várias versões acessíveis saem).

Saída: assets/img/prisma-logo.svg e assets/img/favicon.png
Uso: python ferramentas/gerar_logo.py   (rodar dentro de web/)
"""
from pathlib import Path

from PIL import Image

W, H = 30, 18
TINTA, VIDRO, BRILHO, FEIXE = "#1E2235", "#CDEBFE", "#FFFFFF", "#8A8FA8"
ARCO = ["#E5533D", "#FFAD60", "#FFC93C", "#7BD389", "#57B3F9", "#B89AF0"]
px = {}


def p(x, y, cor):
    if 0 <= x < W and 0 <= y < H:
        px[(x, y)] = cor


# feixe de luz entrando pela esquerda
for x in range(0, 11):
    p(x, 10, FEIXE)
    p(x, 11, FEIXE)

# raios do arco-íris saindo pela direita, abrindo em leque (2 px de espessura)
for i, cor in enumerate(ARCO):
    ant = None
    for x in range(17, W):
        y = 7 + i + round((x - 17) * (i - 2.5) * 0.3)
        faixa = range(min(ant, y), max(ant, y) + 1) if ant is not None else [y]
        for yy in faixa:
            p(x, yy, cor)
        ant = y

# prisma: ápice (15,1), base de 7 a 23 na linha 16
for y in range(1, 17):
    meia = (y - 1) * 0.5
    x0, x1 = round(15 - meia), round(15 + meia)
    for x in range(x0, x1 + 1):
        borda = x in (x0, x1) or y == 16
        p(x, y, TINTA if borda else VIDRO)
# brilho no vidro
for y in range(5, 13):
    p(round(15 - (y - 1) * 0.5) + 2, y, BRILHO)

rects = "".join(f'<rect x="{x}" y="{y}" width="1" height="1" fill="{c}"/>' for (x, y), c in sorted(px.items()))
svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" shape-rendering="crispEdges">'
       f"<title>PRISMA</title>{rects}</svg>\n")
saida = Path(__file__).resolve().parent.parent / "assets" / "img"
(saida / "prisma-logo.svg").write_text(svg, encoding="utf-8")

img = Image.new("RGBA", (32, 32), (0, 0, 0, 0))
for (x, y), c in px.items():
    img.putpixel((x + 1, y + 7), tuple(int(c[i:i + 2], 16) for i in (1, 3, 5)) + (255,))
img.resize((64, 64), Image.NEAREST).save(saida / "favicon.png")
print("ok")
