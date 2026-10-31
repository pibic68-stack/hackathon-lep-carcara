"""P1.1 dentro das imagens: cada região de cor ganha um símbolo desenhado por cima, com legenda.

Um aluno daltônico não distingue, por exemplo, o verde das folhas do marrom do tronco.
Com um ● sobre o verde e um ◇ sobre o marrom, a imagem passa a ter forma além da cor.
Os símbolos são os mesmos da legenda de texto (transformacoes.SIMBOLOS).

Como funciona:
1. reduz a imagem e dá um nome de cor a cada ponto (cinza, branco e preto ficam de fora);
2. separa as regiões de cada cor (bolinhas próximas contam como um grupo);
3. região grande recebe símbolos numa grade em xadrez (um sim, um não), para não esconder o desenho;
   região pequena ou estreita (sol, tronco, grupo de bolinhas) recebe um símbolo no seu ponto mais central;
4. cada símbolo é preto com contorno branco, visível sobre qualquer cor.
Caixas de texto brancas e fundos acinzentados não recebem símbolo.
"""
from __future__ import annotations

import colorsys
import math
from collections import Counter
from pathlib import Path

LARGURA_ANALISE = 240        # pontos na largura da imagem reduzida
COLUNAS = 16                 # quadrados da grade na largura
PUREZA = 0.72                # fração mínima do quadrado com a mesma cor
AREA_MINIMA_REGIAO = 14      # pontos (na imagem reduzida) para uma região ganhar símbolo; menos que isso é ruído
ESPESSURA_MINIMA = 9         # menor lado da região (já com a folga): abaixo disso é linha ou faixa
MAX_CORES = 6


def _nome(r: int, g: int, b: int) -> str | None:
    """Nome da cor de um ponto. Mais exigente que o do texto: foto e JPEG têm ruído."""
    h, s, v = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)
    if v < 0.22 or s < 0.28 or (max(r, g, b) - min(r, g, b)) < 50:
        return None
    graus = h * 360
    if graus < 15 or graus >= 340:
        if v < 0.6:
            return "marrom"                   # vermelho escuro de JPEG (raiz, sombra) parece marrom
        return "rosa" if (v > 0.8 and s < 0.55) else "vermelho"
    if graus < 45:
        return "marrom" if v < 0.62 else "laranja"
    if graus < 70:
        return "marrom" if v < 0.45 else "amarelo"
    if graus < 165:
        return "verde"
    if graus < 255:
        return "azul"
    if graus < 290:
        return "roxo"
    return "rosa"


def _forma(desenho, simbolo: str, cx: float, cy: float, r: float) -> None:
    """Desenha o símbolo em preto com contorno branco largo."""
    contorno = max(2, int(r * 0.32))

    def poligono(pontos, cheio=True):
        desenho.polygon(pontos, fill="white", outline="white")
        desenho.line(pontos + [pontos[0]], fill="white", width=contorno * 2, joint="curve")
        if cheio:
            desenho.polygon(pontos, fill="black")
        else:
            desenho.line(pontos + [pontos[0]], fill="black", width=max(2, int(r * 0.3)), joint="curve")

    if simbolo in ("●", "○"):
        desenho.ellipse([cx - r - contorno, cy - r - contorno, cx + r + contorno, cy + r + contorno], fill="white")
        if simbolo == "●":
            desenho.ellipse([cx - r, cy - r, cx + r, cy + r], fill="black")
        else:
            desenho.ellipse([cx - r, cy - r, cx + r, cy + r], outline="black", width=max(2, int(r * 0.3)))
    elif simbolo == "■":
        poligono([(cx - r, cy - r), (cx + r, cy - r), (cx + r, cy + r), (cx - r, cy + r)])
    elif simbolo in ("▲", "▼"):
        s = -1 if simbolo == "▲" else 1
        poligono([(cx, cy + s * r * 1.1), (cx + r * 1.1, cy - s * r * 0.8), (cx - r * 1.1, cy - s * r * 0.8)])
    elif simbolo in ("◆", "◇"):
        poligono([(cx, cy - r * 1.2), (cx + r, cy), (cx, cy + r * 1.2), (cx - r, cy)], cheio=simbolo == "◆")
    elif simbolo == "★":
        pts = []
        for k in range(10):
            raio = r * 1.2 if k % 2 == 0 else r * 0.5
            ang = -math.pi / 2 + k * math.pi / 5
            pts.append((cx + raio * math.cos(ang), cy + raio * math.sin(ang)))
        poligono(pts)
    elif simbolo == "✚":
        a = r * 0.38
        poligono([(cx - a, cy - r), (cx + a, cy - r), (cx + a, cy - a), (cx + r, cy - a), (cx + r, cy + a),
                  (cx + a, cy + a), (cx + a, cy + r), (cx - a, cy + r), (cx - a, cy + a), (cx - r, cy + a),
                  (cx - r, cy - a), (cx - a, cy - a)])
    elif simbolo == "♥":
        pts = []
        for k in range(24):
            t = 2 * math.pi * k / 24
            x = 16 * math.sin(t) ** 3
            y = -(13 * math.cos(t) - 5 * math.cos(2 * t) - 2 * math.cos(3 * t) - math.cos(4 * t))
            pts.append((cx + x * r / 15, cy + y * r / 15))
        poligono(pts)
    else:                                          # ▬ e qualquer outro
        poligono([(cx - r, cy - r * 0.4), (cx + r, cy - r * 0.4), (cx + r, cy + r * 0.4), (cx - r, cy + r * 0.4)])


def _componentes(mascara: list[list[bool]], w: int, h: int, folga: int):
    """Regiões ligadas da máscara. `folga` junta pedaços próximos (bolinhas de um mesmo grupo)."""
    if folga:
        dil = [[False] * w for _ in range(h)]
        for y in range(h):
            for x in range(w):
                if mascara[y][x]:
                    for yy in range(max(0, y - folga), min(h, y + folga + 1)):
                        linha = dil[yy]
                        for xx in range(max(0, x - folga), min(w, x + folga + 1)):
                            linha[xx] = True
    else:
        dil = mascara
    visto = [[False] * w for _ in range(h)]
    for y in range(h):
        for x in range(w):
            if dil[y][x] and not visto[y][x]:
                pilha, pontos = [(x, y)], []
                visto[y][x] = True
                while pilha:
                    cx, cy = pilha.pop()
                    pontos.append((cx, cy))
                    for nx, ny in ((cx + 1, cy), (cx - 1, cy), (cx, cy + 1), (cx, cy - 1)):
                        if 0 <= nx < w and 0 <= ny < h and dil[ny][nx] and not visto[ny][nx]:
                            visto[ny][nx] = True
                            pilha.append((nx, ny))
                yield pontos, dil


def _ponto_central(pontos, dil, w: int, h: int) -> tuple[int, int, int]:
    """Ponto mais "para dentro" da região (maior quadrado todo dentro dela), e o tamanho desse quadrado."""
    melhor = (pontos[0][0], pontos[0][1], 0)
    for x, y in pontos[:: max(1, len(pontos) // 1500)]:
        k = 0
        while k < 8:
            k1 = k + 1
            if x - k1 < 0 or y - k1 < 0 or x + k1 >= w or y + k1 >= h:
                break
            if not all(dil[yy][xx] for yy in range(y - k1, y + k1 + 1) for xx in (x - k1, x + k1)) or \
               not all(dil[yy][xx] for xx in range(x - k1, x + k1 + 1) for yy in (y - k1, y + k1)):
                break
            k = k1
        if k > melhor[2]:
            melhor = (x, y, k)
    return melhor


def marcar_cores(origem: Path, destino: Path) -> list[str]:
    """Grava em `destino` a imagem com símbolos e devolve as cores marcadas (da maior área para a menor).
    Lista vazia = nada marcado (e nada gravado)."""
    from PIL import Image, ImageDraw

    from .transformacoes import SIMBOLOS

    try:
        original = Image.open(origem).convert("RGB")
    except Exception:
        return []
    W, H = original.size
    if W < 80 or H < 80:
        return []
    escala = LARGURA_ANALISE / W
    pequena = original.resize((LARGURA_ANALISE, max(1, round(H * escala))), Image.BILINEAR)
    w, h = pequena.size
    px = pequena.load()
    nomes = [[_nome(*px[x, y]) for x in range(w)] for y in range(h)]
    total = Counter(n for linha in nomes for n in linha if n)

    passo = w / COLUNAS                              # lado do quadrado da grade (imagem reduzida)
    raio_grade = passo / escala * 0.26               # raio do símbolo na imagem original
    raio_min = max(9.0, W / 110)
    marcas: list[tuple[str, float, float, float]] = []
    ordem: list[str] = []

    aceitas: set[str] = set()                       # cores já marcadas (maior área primeiro)
    for cor, _ in total.most_common():
        if len(ordem) >= MAX_CORES:
            break
        mascara = [[n == cor for n in linha] for linha in nomes]

        def encostada(pontos) -> float:
            """Fração da região que fica ENTRE uma cor já marcada e outra coisa (fundo, outra cor): é a
            borda borrada de uma forma (o rosa na beira de uma seta vermelha), não uma região de verdade.
            Bolinha dentro de outra cor (água azul sobre o chão amarelo) só encosta numa cor: fica."""
            if not aceitas:
                return 0.0
            n = 0
            for x, y in pontos:
                vizinhos = {nomes[ny][nx] for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1))
                            if 0 <= nx < w and 0 <= ny < h} - {cor}
                if vizinhos & aceitas and len(vizinhos) >= 2:
                    n += 1
            return n / max(1, len(pontos))
        achou = False
        for pontos, dil in _componentes(mascara, w, h, folga=2):
            reais = sum(1 for x, y in pontos if mascara[y][x])
            if reais < AREA_MINIMA_REGIAO:
                continue
            xs, ys = [x for x, _ in pontos], [y for _, y in pontos]
            bw, bh = max(xs) - min(xs) + 1, max(ys) - min(ys) + 1
            densidade = reais / (bw * bh)
            if min(bw, bh) < ESPESSURA_MINIMA or densidade < 0.03 or (densidade < 0.07 and reais < 40):
                continue                     # faixa fina (borda de slide, contorno) ou pontos soltos de ruído
            reais_pts = [p for p in pontos if mascara[p[1]][p[0]]]
            if encostada(reais_pts) > 0.4:
                continue                     # borda borrada de uma forma de outra cor
            if (bw >= 0.8 * w or bh >= 0.8 * h) and densidade < 0.3:
                continue                     # degradê espalhado pela imagem toda (fundo), não é região
            # 1) regiões grandes: símbolos numa grade em xadrez, onde o quadrado é quase todo desta cor
            na_grade = 0
            dentro = set(pontos)
            for j in range(max(1, int(h / passo))):
                for i in range(COLUNAS):
                    if (i + j) % 2:
                        continue
                    x0, y0, x1, y1 = int(i * passo), int(j * passo), int((i + 1) * passo), int((j + 1) * passo)
                    cx, cy = (x0 + x1) // 2, (y0 + y1) // 2
                    if (cx, cy) not in dentro:
                        continue
                    caixa = [nomes[y][x] for y in range(y0, min(y1, h)) for x in range(x0, min(x1, w))]
                    if caixa and sum(1 for n in caixa if n == cor) / len(caixa) >= PUREZA:
                        marcas.append((cor, (x0 + x1) / 2 / escala, (y0 + y1) / 2 / escala, raio_grade))
                        na_grade += 1
            # 2) região pequena ou estreita (sol, tronco, grupo de bolinhas): um símbolo no ponto mais central
            if not na_grade:
                x, y, k = _ponto_central([p for p in pontos if mascara[p[1]][p[0]]] or pontos, mascara, w, h)
                raio = min(raio_grade, max(raio_min, (k + 0.5) / escala * 0.9))
                marcas.append((cor, (x + 0.5) / escala, (y + 0.5) / escala, raio))
            achou = True
        if achou:
            ordem.append(cor)
            aceitas.add(cor)

    if not marcas:
        return []
    desenho = ImageDraw.Draw(original)
    for cor, cx, cy, raio in marcas:
        if cor in ordem:
            _forma(desenho, SIMBOLOS.get(cor, "▬"), cx, cy, raio)
    destino.parent.mkdir(parents=True, exist_ok=True)
    original.save(destino, "PNG", optimize=True)
    return ordem
