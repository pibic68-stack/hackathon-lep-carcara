"""Leitor de PDF que entende matemática e cor.

Por que existe: o texto "puro" de um PDF perde a posição das letras. Um expoente vira "x2", uma fração
empilhada vira "3 2 3 1", a raiz perde a barra e o vetor F⃗ vira "F˜". Aqui o leitor olha cada letra,
o tamanho e a altura dela na linha e os traços desenhados na página (barra de fração, barra da raiz),
e remonta a expressão numa marcação curta, entre ⟦ ⟧, que o resto da plataforma entende:

    x⟦^{2}⟧            expoente             (vira <sup>)
    a⟦_{1}⟧            índice               (vira <sub>)
    ⟦\\frac{3}{2}⟧      fração               (vira MathML <mfrac>)
    ⟦\\sqrt{x^{2}+y^{2}}⟧ raiz              (vira MathML <msqrt>)
    ⟦\\vec{F}⟧          vetor                (vira MathML <mover>)

O leitor também anota o texto colorido (critério P1: cor nunca sozinha) e as imagens coloridas.

Funciona com PyMuPDF (o que o time instala) e, se ele não existir, com pdfminer.six. As duas bibliotecas
são traduzidas para o mesmo formato (`Pagina`, `Car`, `Barra`), e o resto do código não sabe qual foi usada.
Coordenadas sempre com a origem no canto de cima, à esquerda, em pontos.
"""
from __future__ import annotations

import io
import re
import statistics
import unicodedata
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path

ABRE, FECHA = "⟦", "⟧"


# ---------------------------------------------------------------- formato comum

@dataclass
class Car:
    c: str
    x0: float
    x1: float
    base: float          # altura da linha de base (y cresce para baixo)
    tam: float           # tamanho da letra em pontos
    fonte: str = ""
    cor: tuple = (0, 0, 0)
    negrito: bool = False
    usado: bool = False
    papel: str = ""      # "" | "sup" | "sub"

    @property
    def topo(self) -> float:
        return self.base - 0.72 * self.tam

    @property
    def fundo(self) -> float:
        return self.base + 0.22 * self.tam

    @property
    def cx(self) -> float:
        return (self.x0 + self.x1) / 2

    @property
    def meio(self) -> float:
        return self.base - 0.3 * self.tam


@dataclass
class Barra:
    """Traço horizontal fino (barra de fração ou da raiz)."""
    x0: float
    x1: float
    y: float


@dataclass
class Figura:
    x0: float
    y0: float
    x1: float
    y1: float
    dados: bytes
    ext: str


@dataclass
class Pagina:
    largura: float
    altura: float
    cars: list[Car] = field(default_factory=list)
    barras: list[Barra] = field(default_factory=list)
    imagens: list[Figura] = field(default_factory=list)
    desenhos_cor: list[tuple] = field(default_factory=list)   # cores de preenchimento de formas desenhadas


@dataclass
class Linha:
    texto: str
    tam: float
    negrito: bool
    x0: float
    x1: float
    topo: float
    fundo: float
    pagina: int
    cores: list[str] = field(default_factory=list)   # nomes das cores de texto colorido nesta linha


# ---------------------------------------------------------------- glifos de fontes TeX e afins

# fontes de matemática do TeX gravam alguns símbolos sem Unicode: "(cid:90)" etc.
CID_CMEX = {80: "∑", 88: "∑", 81: "∏", 89: "∏", 82: "∫", 90: "∫", 72: "∮", 73: "∮",
            112: "√", 113: "√", 114: "√", 115: "√", 116: "√"}
CID_CMSY = {0: "−", 1: "·", 2: "×", 3: "∗", 4: "÷", 6: "±", 20: "≤", 21: "≥", 33: "→", 49: "∞",
            50: "∈", 112: "√", 114: "∇", 115: "∫", 106: "|", 107: "‖"}
CID_CMMI = {126: "⃗"}   # acento de vetor do \vec
LETRA_CMSY = {"p": "√", "x": "§"}
ACENTO_VETOR = {"⃗", "⃑", "→", "⃗", "˜", "~", "⇀", "⟶"}
ACENTO_CHAPEU = {"^", "ˆ", "̂"}
ACENTO_BARRA = {"¯", "‾", "̄", "̅"}
OPERADOR_GRANDE = {"∫", "∮", "∑", "∏", "∬", "∭"}


def _limpar_glifo(c: str, fonte: str) -> str:
    f = fonte.lower()
    if len(c) == 1 and 0x1D400 <= ord(c) <= 0x1D7FF:      # 𝑥, 𝐅, 𝜌: letras "matemáticas" do Word e do Chrome
        return unicodedata.normalize("NFKC", c)
    m = re.fullmatch(r"\(cid:(\d+)\)", c)
    if m:
        n = int(m.group(1))
        if "cmex" in f:
            return CID_CMEX.get(n, "")
        if "cmsy" in f:
            return CID_CMSY.get(n, "")
        if "cmmi" in f:
            return CID_CMMI.get(n, "")
        return ""
    if "cmex" in f and len(c) == 1 and ord(c) in CID_CMEX:
        return CID_CMEX[ord(c)]
    if "cmsy" in f and c in LETRA_CMSY:
        return LETRA_CMSY[c]
    if len(c) == 1 and ord(c) < 32:
        return CID_CMSY.get(ord(c), "") if "cmsy" in f else ""
    return "" if c == "�" else c


# ---------------------------------------------------------------- leitura (duas bibliotecas)

def ler_paginas(caminho: Path) -> list[Pagina]:
    try:
        import pymupdf  # noqa: F401
        return _ler_pymupdf(caminho)
    except ImportError:
        pass
    try:
        import pdfminer  # noqa: F401
    except ImportError as erro:
        raise RuntimeError("Para ler PDF instale: pip install pymupdf") from erro
    return _ler_pdfminer(caminho)


def _rgb_int(n: int) -> tuple:
    return ((n >> 16) & 255) / 255, ((n >> 8) & 255) / 255, (n & 255) / 255


def _rgb_tupla(cor) -> tuple:
    """Cor do pdfminer (cinza, RGB ou CMYK, 0 a 1) para RGB."""
    if cor is None:
        return (0, 0, 0)
    if isinstance(cor, (int, float)):
        return (float(cor),) * 3
    cor = tuple(float(x) for x in cor if isinstance(x, (int, float)))
    if len(cor) == 1:
        return cor * 3
    if len(cor) == 3:
        return cor
    if len(cor) == 4:
        c, m, y, k = cor
        return ((1 - c) * (1 - k), (1 - m) * (1 - k), (1 - y) * (1 - k))
    return (0, 0, 0)


def _ler_pymupdf(caminho: Path) -> list[Pagina]:
    import pymupdf as fitz
    paginas = []
    with fitz.open(caminho) as pdf:
        for page in pdf:
            pg = Pagina(page.rect.width, page.rect.height)
            dados = page.get_text("rawdict")
            for b in dados["blocks"]:
                if b.get("type") != 0:
                    continue
                for linha in b["lines"]:
                    if abs(linha.get("dir", (1, 0))[1]) > 0.1:      # texto girado: fora
                        continue
                    for s in linha["spans"]:
                        negrito = bool(s["flags"] & 16) or "bold" in s["font"].lower()
                        for ch in s["chars"]:
                            c = _limpar_glifo(ch["c"], s["font"])
                            if not c:
                                continue
                            x0, _, x1, _ = ch["bbox"]
                            pg.cars.append(Car(c, x0, x1, ch["origin"][1], s["size"], s["font"],
                                               _rgb_int(s["color"]), negrito))
            # imagens, na ordem e no lugar em que aparecem
            for b in page.get_text("dict")["blocks"]:
                if b.get("type") == 1 and b.get("image"):
                    x0, y0, x1, y1 = b["bbox"]
                    pg.imagens.append(Figura(x0, y0, x1, y1, b["image"], b.get("ext", "png")))
            # traços horizontais finos (fração, raiz) e formas coloridas
            for d in page.get_drawings():
                for item in d.get("items", []):
                    if item[0] == "l":
                        p1, p2 = item[1], item[2]
                        if abs(p1.y - p2.y) < 0.8 and abs(p2.x - p1.x) > 2:
                            pg.barras.append(Barra(min(p1.x, p2.x), max(p1.x, p2.x), (p1.y + p2.y) / 2))
                    elif item[0] == "re":
                        r = item[1]
                        if r.height < 1.6 and r.width > 2:
                            pg.barras.append(Barra(r.x0, r.x1, (r.y0 + r.y1) / 2))
                cor = d.get("fill") or d.get("color")
                r = d.get("rect")
                if cor and r is not None and r.width * r.height > 30:
                    pg.desenhos_cor.append(tuple(cor[:3]) if len(cor) >= 3 else (cor[0],) * 3)
            paginas.append(pg)
    return paginas


def _ler_pdfminer(caminho: Path) -> list[Pagina]:
    from pdfminer.high_level import extract_pages
    from pdfminer.layout import LAParams, LTChar, LTCurve, LTFigure, LTImage, LTLine, LTRect

    paginas = []
    for page in extract_pages(str(caminho), laparams=LAParams()):
        H = page.height
        pg = Pagina(page.width, H)

        def andar(o):
            for x in getattr(o, "_objs", None) or []:
                yield x
                yield from andar(x)

        for o in andar(page):
            if isinstance(o, LTChar):
                if not o.upright:
                    continue
                c = _limpar_glifo(o.get_text(), o.fontname)
                if not c:
                    continue
                cor = getattr(o.graphicstate, "ncolor", None)
                pg.cars.append(Car(c, o.x0, o.x1, H - o.matrix[5], o.size, o.fontname, _rgb_tupla(cor),
                                   "bold" in o.fontname.lower()))
            elif isinstance(o, (LTLine, LTRect, LTCurve)):
                if o.height < 1.6 and o.width > 2:
                    pg.barras.append(Barra(o.x0, o.x1, H - (o.y0 + o.y1) / 2))
                elif getattr(o, "fill", False) and o.width * o.height > 30:
                    pg.desenhos_cor.append(_rgb_tupla(getattr(o, "non_stroking_color", None)))
            elif isinstance(o, LTImage):
                dados, ext = _bytes_imagem_pdfminer(o)
                if dados:
                    pg.imagens.append(Figura(o.x0, H - o.y1, o.x1, H - o.y0, dados, ext))
            elif isinstance(o, LTFigure):
                continue
        paginas.append(pg)
    return paginas


def _bytes_imagem_pdfminer(img) -> tuple[bytes, str]:
    """Imagem do pdfminer para bytes PNG/JPEG (usa Pillow quando o PDF guarda pixels crus)."""
    try:
        filtros = [str(f) for f in (img.stream.get_filters() or [])]
        bruto = img.stream.get_rawdata()
        if any("DCT" in f for f in filtros):
            return bruto, "jpeg"
        from PIL import Image
        dados = img.stream.get_data()
        w, h = img.srcsize
        cs = str(img.colorspace[0]) if img.colorspace else ""
        modo = "RGB" if "RGB" in cs else "L"
        if len(dados) < w * h * (3 if modo == "RGB" else 1):
            return b"", ""
        im = Image.frombytes(modo, (w, h), dados[: w * h * (3 if modo == "RGB" else 1)])
        saida = io.BytesIO()
        im.save(saida, "PNG")
        return saida.getvalue(), "png"
    except Exception:
        return b"", ""


# ---------------------------------------------------------------- cor (P1)

# cada cor ganha uma forma (mesma tabela da regra P1)
NOMES_COR = [
    ("vermelho", (0.85, 0.12, 0.12)), ("laranja", (0.95, 0.55, 0.1)), ("amarelo", (0.95, 0.85, 0.1)),
    ("verde", (0.15, 0.6, 0.2)), ("azul", (0.12, 0.35, 0.85)), ("roxo", (0.5, 0.2, 0.7)),
    ("rosa", (0.95, 0.45, 0.7)), ("marrom", (0.5, 0.3, 0.12)),
]


def nome_da_cor(rgb: tuple) -> str | None:
    """None para preto, branco e cinzas (cor que não carrega informação)."""
    r, g, b = (max(0.0, min(1.0, float(x))) for x in rgb[:3])
    mx, mn = max(r, g, b), min(r, g, b)
    if mx - mn < 0.18 or mx < 0.2:
        return None
    return min(NOMES_COR, key=lambda nc: sum((a - b) ** 2 for a, b in zip((r, g, b), nc[1])))[0]


def imagem_colorida(dados: bytes) -> bool:
    """Colorida de verdade (gráfico, mapa, desenho com legenda de cor)? Usa o índice de Hasler e Süsstrunk."""
    try:
        from PIL import Image
        im = Image.open(io.BytesIO(dados)).convert("RGB")
        im.thumbnail((160, 160))
        px = list(im.getdata())
    except Exception:
        return False
    if not px:
        return False
    rg = [r - g for r, g, b in px]
    yb = [(r + g) / 2 - b for r, g, b in px]
    desvio = (statistics.pstdev(rg) ** 2 + statistics.pstdev(yb) ** 2) ** 0.5
    media = (statistics.fmean(rg) ** 2 + statistics.fmean(yb) ** 2) ** 0.5
    return desvio + 0.3 * media > 25


# ---------------------------------------------------------------- matemática

def _sobrepoe(a0, a1, b0, b1) -> float:
    return max(0.0, min(a1, b1) - max(a0, b0))


def _corpo(cars: list[Car]) -> float:
    pesos = Counter(round(c.tam * 2) / 2 for c in cars if c.c.strip())
    return pesos.most_common(1)[0][0] if pesos else 11.0


def _acentos(cars: list[Car]) -> None:
    """Acento solto em cima de uma letra (vetor, chapéu, barra) vira marcação na letra.
    A altura do acento não é confiável (cada fonte guarda de um jeito); vale a letra que ele cobre na horizontal."""
    todos = ACENTO_VETOR | ACENTO_CHAPEU | ACENTO_BARRA
    for a in cars:
        if a.usado or len(a.c) != 1 or not (a.c in todos or unicodedata.combining(a.c)):
            continue
        melhor, cobre = None, 0.0
        for L in cars:
            if L is a or L.usado or not L.c.isalnum() or abs(L.base - a.base) > 0.9 * L.tam:
                continue
            largura = min(L.x1 - L.x0, a.x1 - a.x0) or 1
            s = _sobrepoe(L.x0, L.x1, a.x0, a.x1) / largura
            if s > cobre:
                melhor, cobre = L, s
        if not melhor or cobre < 0.4:
            # "~" e "^" soltos no meio do texto são só caracteres
            if len(a.c) == 1 and unicodedata.combining(a.c):
                a.usado = True
            continue
        cmd = "vec" if a.c in ACENTO_VETOR else "hat" if a.c in ACENTO_CHAPEU else "bar"
        melhor.c = f"{ABRE}\\{cmd}{{{melhor.c}}}{FECHA}"
        a.usado = True


def _operadores_grandes(cars: list[Car]) -> None:
    """∫ e ∑ grandes ficam com a "linha de base" fora da linha do texto; encaixa na linha da expressão ao lado."""
    for op in cars:
        if op.c not in OPERADOR_GRANDE or op.usado:
            continue
        perto = [c for c in cars if c is not op and not c.usado and c.c.strip() and c.c not in OPERADOR_GRANDE
                 and -1 <= c.x0 - op.x1 <= 2.5 * op.tam and op.base - 0.6 * op.tam <= c.base <= op.base + 2.6 * op.tam
                 and c.tam >= 0.86 * op.tam]
        if perto:
            op.base = min(perto, key=lambda c: c.x0).base


def _token(texto: str, x0: float, x1: float, base: float, tam: float, modelo: Car) -> Car:
    return Car(texto, x0, x1, base, tam, modelo.fonte, (0, 0, 0), False)


def _raizes(cars: list[Car], barras: list[Barra], usadas: set[int], corpo: float) -> list[Car]:
    novos = []
    for r in cars:
        if r.usado or r.c != "√":
            continue
        barra = None
        for k, b in enumerate(barras):
            if k in usadas:
                continue
            if abs(b.x0 - r.x1) < 0.35 * r.tam + 1.5 and r.topo - 0.8 * r.tam < b.y < r.base:
                barra = k
                break
        if barra is not None:
            b = barras[barra]
            dentro = [c for c in cars if not c.usado and c is not r and b.x0 - 0.5 <= c.cx <= b.x1 + 0.5
                      and b.y < c.base < b.y + 2.0 * max(c.tam, corpo)]
        else:
            # sem barra desenhada: o radicando é o grupo grudado logo depois do símbolo
            seguintes = sorted((c for c in cars if not c.usado and c is not r and c.x0 >= r.x1 - 1
                                and abs(c.base - r.base) < 0.6 * r.tam), key=lambda c: c.x0)
            dentro, fim = [], r.x1
            for c in seguintes:
                if c.x0 - fim > 0.25 * c.tam or c.c in " +−-=<>,;":
                    break
                dentro.append(c)
                fim = c.x1
        if not dentro:
            continue
        usadas.add(barra) if barra is not None else None
        texto = _texto_de(dentro, corpo)
        for c in dentro:
            c.usado = True
        r.usado = True
        base = statistics.median(c.base for c in dentro if not c.papel) if any(not c.papel for c in dentro) else r.base
        x1 = barras[barra].x1 if barra is not None else max(c.x1 for c in dentro)
        novos.append(_token(f"{ABRE}\\sqrt{{{texto}}}{FECHA}", r.x0, x1, base, corpo, r))
    return novos


def _fracoes(cars: list[Car], barras: list[Barra], usadas: set[int], corpo: float, largura_pagina: float) -> list[Car]:
    """Barra com algo em cima e algo embaixo, alinhados com ela, é fração. As menores primeiro (frações dentro de frações)."""
    novos: list[Car] = []
    ordem = sorted((k for k in range(len(barras)) if k not in usadas), key=lambda k: barras[k].x1 - barras[k].x0)
    for k in ordem:
        b = barras[k]
        if b.x1 - b.x0 > 0.45 * largura_pagina:
            continue           # linha de tabela, sublinhado longo
        todos = [c for c in cars + novos if not c.usado and b.x0 - 1 <= c.cx <= b.x1 + 1]
        # medido em PDFs do Word e do LaTeX: o numerador fica com a base 0,2 a 0,6 letra acima da barra;
        # o denominador, com a base 0,7 a 1,1 letra abaixo
        cima = [c for c in todos if b.y - 0.85 * c.tam < c.base < b.y + 0.05 * c.tam]
        baixo = [c for c in todos if b.y + 0.45 * c.tam < c.base < b.y + 1.35 * c.tam]
        if not cima or not baixo:
            continue
        # o numerador e o denominador cabem na barra (sobra pouco para os lados)
        if min(c.x0 for c in cima + baixo) < b.x0 - 3 or max(c.x1 for c in cima + baixo) > b.x1 + 3:
            continue
        num, den = _texto_de(cima, corpo), _texto_de(baixo, corpo)
        for c in cima + baixo:
            c.usado = True
        usadas.add(k)
        tam = max(c.tam for c in cima + baixo)
        novos.append(_token(f"{ABRE}\\frac{{{num}}}{{{den}}}{FECHA}", b.x0, b.x1, b.y + 0.3 * tam, max(tam, corpo * 0.9), cima[0]))
    return novos


def _linhas_de_base(cars: list[Car]) -> list[list[Car]]:
    """Agrupa letras do mesmo tamanho que estão na mesma linha de base."""
    linhas: list[list[Car]] = []
    for c in sorted(cars, key=lambda c: (round(c.base, 1), c.x0)):
        for L in linhas:
            ref = L[0]
            if abs(c.base - ref.base) <= 0.3 * min(c.tam, ref.tam) and 0.8 <= c.tam / ref.tam <= 1.25:
                L.append(c)
                break
        else:
            linhas.append([c])
    return linhas


def _texto_de(cars: list[Car], corpo: float) -> str:
    """Texto de um grupo pequeno (numerador, radicando): já com expoentes e índices."""
    linhas = _montar_linhas(cars, corpo)
    return " ".join(t for t, *_ in linhas).strip()


def _montar_linhas(cars: list[Car], corpo: float):
    """Devolve [(texto, cars_principais)] por linha visual, com expoentes e índices presos à letra certa."""
    if not cars:
        return []
    for c in cars:
        c.papel = ""
    grupos = _linhas_de_base(cars)
    # linhas "principais": tamanho de texto normal para a vizinhança
    principais = [g for g in grupos if statistics.median(c.tam for c in g) >= 0.86 * corpo or len(grupos) == 1]
    if not principais:
        principais = [max(grupos, key=len)]
    pequenos = [g for g in grupos if g not in principais]
    for g in pequenos:
        resto = []
        for s in g:
            dono, papel = None, ""
            for P in principais:
                ref = statistics.median(c.tam for c in P)
                pbase = statistics.median(c.base for c in P)
                # limite embaixo ou em cima de operador grande (∫ com C embaixo)
                grande = [c for c in P if c.c in OPERADOR_GRANDE and c.x0 - 2 <= s.cx <= c.x1 + 0.5 * ref]
                if grande and abs(s.base - pbase) < 2.2 * ref:
                    dono, papel = P, ("sub" if s.base > pbase else "sup")
                    break
                vizinho = any(-0.2 * ref <= s.x0 - c.x1 <= 0.6 * ref for c in P) or any(c.x0 <= s.cx <= c.x1 for c in P)
                if vizinho and abs(s.base - pbase) < 0.75 * ref and abs(s.base - pbase) > 0.12 * ref:
                    dono, papel = P, ("sup" if s.base < pbase else "sub")
                    break
            if dono:
                s.papel = papel
                dono.append(s)
            else:
                resto.append(s)
        g[:] = resto
    linhas = [g for g in principais] + [g for g in pequenos if g]
    saida = []
    for g in linhas:
        g.sort(key=lambda c: (c.x0, c.papel != ""))
        saida.append((_texto_linha(g), g))
    saida.sort(key=lambda t: min(c.base for c in t[1] if not c.papel) if any(not c.papel for c in t[1]) else t[1][0].base)
    return saida


def _texto_linha(g: list[Car]) -> str:
    partes: list[str] = []
    atual_papel, buffer = "", []
    anterior = None

    def fechar():
        nonlocal buffer
        if buffer:
            corpo = "".join(buffer).strip()
            if corpo:
                partes.append(f"{ABRE}{'^' if atual_papel == 'sup' else '_'}{{{corpo}}}{FECHA}")
        buffer = []

    for c in g:
        if c.papel != atual_papel:
            fechar()
            atual_papel = c.papel
        if anterior is not None and c.c != " " and anterior.c != " ":
            folga = c.x0 - anterior.x1
            # perto de sinal de conta o espaço é menor (o PDF aperta "x² + y²")
            limite = 0.12 if (c.c in "+−-=<>×÷·" or anterior.c in "+−-=<>×÷·" or c.papel != anterior.papel) else 0.22
            if folga > limite * min(c.tam, anterior.tam) and (c.papel == anterior.papel or (not c.papel and anterior.papel)):
                (buffer if c.papel else partes).append(" ")
        (buffer if c.papel else partes).append(c.c)
        anterior = c
    fechar()
    return re.sub(r"[ \t]+", " ", "".join(partes)).strip()


def _cores_da_linha(g: list[Car], corpo: float) -> tuple[str, list[str]]:
    """Marca trechos de texto colorido com a forma da cor (P1). Devolve (texto marcado, cores).
    Título colorido é estilo, não informação: fica de fora."""
    from .transformacoes import SIMBOLOS
    principais = [c for c in g if not c.papel and c.c.strip()]
    if principais and statistics.median(c.tam for c in principais) >= 1.15 * corpo:
        return _texto_linha(g), []
    usadas = []
    for c in g:
        if c.papel or not c.c.strip():
            continue
        nome = nome_da_cor(c.cor)
        if nome and nome not in usadas:
            usadas.append(nome)
    if not usadas:
        return _texto_linha(g), []
    # coloca o símbolo logo depois de cada trecho colorido
    marcado: list[Car] = []
    ativo = None
    for c in g:
        nome = nome_da_cor(c.cor) if c.c.strip() and not c.papel else ativo
        if ativo and nome != ativo:
            marcado.append(Car(f" ({SIMBOLOS.get(ativo, '■')}) ", c.x0, c.x0, c.base, c.tam))
        ativo = nome
        marcado.append(c)
    if ativo:
        u = g[-1]
        marcado.append(Car(f" ({SIMBOLOS.get(ativo, '■')})", u.x1, u.x1, u.base, u.tam))
    return _texto_linha(marcado), usadas


def linhas_da_pagina(pg: Pagina, n: int) -> list[Linha]:
    cars = [c for c in pg.cars if c.c]
    if not cars:
        return []
    corpo = _corpo(cars)
    _acentos(cars)
    _operadores_grandes(cars)
    usadas: set[int] = set()
    novos = _raizes(cars, pg.barras, usadas, corpo)
    novos += _fracoes(cars, pg.barras, usadas, corpo, pg.largura)
    vivos = [c for c in cars if not c.usado] + novos
    saida = []
    for texto, g in _montar_linhas(vivos, corpo):
        principais = [c for c in g if not c.papel] or g
        texto_cor, cores = _cores_da_linha(g, corpo)
        if not texto_cor.strip():
            continue
        saida.append(Linha(
            texto_cor, statistics.median(c.tam for c in principais),
            sum(c.negrito for c in principais) > len(principais) / 2,
            min(c.x0 for c in g), max(c.x1 for c in g),
            min(c.topo for c in g), max(c.fundo for c in g), n, cores))
    saida.sort(key=lambda L: (L.topo, L.x0))
    # linhas que se sobrepõem na vertical e estão lado a lado (ex.: "a)" e a fração) viram uma só
    juntas: list[Linha] = []
    for L in saida:
        if juntas:
            J = juntas[-1]
            if _sobrepoe(J.topo, J.fundo, L.topo, L.fundo) > 0.45 * min(J.fundo - J.topo, L.fundo - L.topo):
                esq, dir_ = (J, L) if J.x0 <= L.x0 else (L, J)
                juntas[-1] = Linha(esq.texto + " " + dir_.texto, max(J.tam, L.tam), J.negrito and L.negrito,
                                   min(J.x0, L.x0), max(J.x1, L.x1), min(J.topo, L.topo), max(J.fundo, L.fundo),
                                   n, J.cores + [c for c in L.cores if c not in J.cores])
                continue
        juntas.append(L)
    return juntas


# ---------------------------------------------------------------- da marcação para HTML, MathML e fala

_SIMPLES = re.compile(r"⟦([\^_])\{((?:[^{}⟦⟧]|⟦[^⟧]*⟧)*)\}⟧")


def tem_matematica(texto: str) -> bool:
    return ABRE in texto


def _ler_grupo(s: str, i: int) -> tuple[str, int]:
    """Lê {…} balanceado a partir de s[i] == '{'. Devolve (conteúdo, posição depois de '}')."""
    if i >= len(s) or s[i] != "{":
        return "", i
    nivel, j = 0, i
    while j < len(s):
        if s[j] == "{":
            nivel += 1
        elif s[j] == "}":
            nivel -= 1
            if nivel == 0:
                return s[i + 1:j], j + 1
        j += 1
    return s[i + 1:], len(s)


def _partes(texto: str):
    """Divide em ("texto", s) e ("mat", conteúdo de ⟦…⟧), respeitando ⟦ ⟧ dentro de ⟦ ⟧."""
    i, inicio, nivel = 0, 0, 0
    while i < len(texto):
        ch = texto[i]
        if ch == ABRE:
            if nivel == 0 and i > inicio:
                yield "texto", texto[inicio:i]
            if nivel == 0:
                inicio = i + 1
            nivel += 1
        elif ch == FECHA and nivel:
            nivel -= 1
            if nivel == 0:
                yield "mat", texto[inicio:i]
                inicio = i + 1
        i += 1
    if inicio < len(texto):
        yield ("mat" if nivel else "texto"), texto[inicio:]


def _esc(t: str) -> str:
    return t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def _mathml_conteudo(s: str) -> str:
    """Mini-LaTeX (só o que o leitor produz) para MathML Core."""
    out: list[str] = []
    i = 0
    while i < len(s):
        ch = s[i]
        if ch == ABRE:          # marcação aninhada: ⟦^{2}⟧ dentro de fração etc.
            j, nivel = i, 0
            while j < len(s):
                if s[j] == ABRE:
                    nivel += 1
                elif s[j] == FECHA:
                    nivel -= 1
                    if nivel == 0:
                        break
                j += 1
            interno = s[i + 1:j]
            if interno[:1] in "^_" and out:
                grupo, _ = _ler_grupo(interno, 1)
                base = out.pop()
                tag = "msup" if interno[0] == "^" else "msub"
                out.append(f"<{tag}>{base}<mrow>{_mathml_conteudo(grupo)}</mrow></{tag}>")
            else:
                out.append(_mathml_conteudo(interno))
            i = j + 1
            continue
        if ch == "\\":
            m = re.match(r"\\([a-z]+)", s[i:])
            cmd = m.group(1) if m else ""
            j = i + 1 + len(cmd)
            if cmd == "frac":
                a, j = _ler_grupo(s, j)
                b, j = _ler_grupo(s, j)
                out.append(f"<mfrac><mrow>{_mathml_conteudo(a)}</mrow><mrow>{_mathml_conteudo(b)}</mrow></mfrac>")
            elif cmd == "sqrt":
                a, j = _ler_grupo(s, j)
                out.append(f"<msqrt><mrow>{_mathml_conteudo(a)}</mrow></msqrt>")
            elif cmd in ("vec", "hat", "bar"):
                a, j = _ler_grupo(s, j)
                acento = {"vec": "→", "hat": "^", "bar": "¯"}[cmd]
                out.append(f'<mover accent="true"><mrow>{_mathml_conteudo(a)}</mrow><mo>{acento}</mo></mover>')
            else:
                out.append(f"<mi>{_esc(cmd)}</mi>")
            i = j
            continue
        if ch in "^_" and i + 1 < len(s) and s[i + 1] == "{" and out:
            grupo, j = _ler_grupo(s, i + 1)
            base = out.pop()
            tag = "msup" if ch == "^" else "msub"
            out.append(f"<{tag}>{base}<mrow>{_mathml_conteudo(grupo)}</mrow></{tag}>")
            i = j
            continue
        if ch.isspace():
            i += 1
            continue
        if ch.isdigit() or (ch in ",." and out and out[-1].startswith("<mn>")):
            m = re.match(r"\d+(?:[.,]\d+)?", s[i:])
            out.append(f"<mn>{m.group(0)}</mn>")
            i += len(m.group(0))
            continue
        if ch.isalpha():
            m = re.match(r"[^\W\d_]+", s[i:])
            palavra = m.group(0)
            if len(palavra) > 1 and palavra.lower() in ("sen", "sin", "cos", "tg", "tan", "log", "ln", "lim", "mmc", "mdc"):
                out.append(f"<mi>{_esc(palavra)}</mi>")
                i += len(palavra)
            elif len(palavra) > 2:
                out.append(f"<mtext>{_esc(palavra)}</mtext>")
                i += len(palavra)
            else:
                out.append(f"<mi>{_esc(ch)}</mi>")
                i += 1
            continue
        out.append(f"<mo>{_esc(ch)}</mo>")
        i += 1
    return "".join(out)


def _fala_conteudo(s: str) -> str:
    """Como a expressão deve ser lida em voz alta (versão Ouvir)."""
    def troca(texto: str) -> str:
        texto = re.sub(r"\\frac", " FRAC ", texto)
        return texto
    out = []
    i = 0
    while i < len(s):
        ch = s[i]
        if ch == ABRE:
            j, nivel = i, 0
            while j < len(s):
                if s[j] == ABRE:
                    nivel += 1
                elif s[j] == FECHA:
                    nivel -= 1
                    if nivel == 0:
                        break
                j += 1
            out.append(_fala_conteudo(s[i + 1:j]))
            i = j + 1
            continue
        if ch == "\\":
            m = re.match(r"\\([a-z]+)", s[i:])
            cmd = m.group(1) if m else ""
            j = i + 1 + len(cmd)
            if cmd == "frac":
                a, j = _ler_grupo(s, j)
                b, j = _ler_grupo(s, j)
                out.append(f" {_fala_conteudo(a)} sobre {_fala_conteudo(b)} ")
            elif cmd == "sqrt":
                a, j = _ler_grupo(s, j)
                out.append(f" raiz quadrada de {_fala_conteudo(a)}, ")
            elif cmd == "vec":
                a, j = _ler_grupo(s, j)
                out.append(f" vetor {_fala_conteudo(a)} ")
            elif cmd in ("hat", "bar"):
                a, j = _ler_grupo(s, j)
                out.append(f" {_fala_conteudo(a)} {'chapéu' if cmd == 'hat' else 'barra'} ")
            i = j
            continue
        if ch in "^_" and i + 1 < len(s) and s[i + 1] == "{":
            grupo, j = _ler_grupo(s, i + 1)
            g = _fala_conteudo(grupo).strip()
            if ch == "^":
                out.append(" ao quadrado " if g == "2" else " ao cubo " if g == "3" else f" elevado a {g} ")
            else:
                out.append(f" índice {g} ")
            i = j
            continue
        out.append({"−": " menos ", "-": " menos ", "+": " mais ", "=": " igual a ", "·": " vezes ", "×": " vezes ",
                    "÷": " dividido por ", "∫": " integral ", "∑": " somatório ", "≤": " menor ou igual a ",
                    "≥": " maior ou igual a ", "<": " menor que ", ">": " maior que ", "ρ": " rô ",
                    "π": " pi ", "θ": " teta ", "α": " alfa ", "β": " beta ", "∇": " nabla ", "∞": " infinito "}.get(ch, ch))
        i += 1
    return re.sub(r"\s+", " ", "".join(out))


def para_html(texto: str) -> str:
    """Texto com marcação ⟦…⟧ para HTML seguro (o resto é escapado)."""
    saida = []
    for tipo, parte in _partes(texto):
        if tipo == "texto":
            saida.append(_esc(parte))
            continue
        simples = re.fullmatch(r"([\^_])\{(.*)\}", parte, flags=re.S)
        if simples and "\\" not in simples.group(2) and ABRE not in simples.group(2):
            tag = "sup" if simples.group(1) == "^" else "sub"
            saida.append(f"<{tag}>{_esc(simples.group(2))}</{tag}>")
        else:
            fala = _esc(_fala_conteudo(parte).strip())
            saida.append(f'<math aria-label="{fala}"><mrow>{_mathml_conteudo(parte)}</mrow></math>')
    return "".join(saida)


FALA_OPERADOR = {"+": " mais ", "=": " igual a ", "−": " menos ", "×": " vezes ", "÷": " dividido por ",
                 "≤": " menor ou igual a ", "≥": " maior ou igual a ", "∫": " integral ", "·": " vezes ", "√": " raiz de "}


def para_fala(texto: str) -> str:
    saida = []
    for tipo, parte in _partes(texto):
        if tipo == "texto":
            # símbolos de conta fora da marcação também são lidos ("x² + y²")
            parte = "".join(FALA_OPERADOR.get(ch, ch) for ch in parte) if ABRE in texto or re.search(r"\d\s*[+=−×÷]\s*\d", parte) else parte
            saida.append(parte)
        else:
            saida.append(_fala_conteudo(parte))
    return re.sub(r"\s+", " ", "".join(saida)).strip()


def para_texto_simples(texto: str) -> str:
    """Sem marcação, para contar palavras e mandar para conferências (x^2 vira x2)."""
    return re.sub(r"[⟦⟧{}\\^_]|frac|sqrt|vec", " ", texto)


# ---------------------------------------------------------------- proteção para a IA

def proteger(texto: str) -> tuple[str, list[str]]:
    """Troca cada ⟦…⟧ por [M1], [M2]... antes de mandar para a IA; `restaurar` põe de volta."""
    guardados: list[str] = []
    saida = []
    for tipo, parte in _partes(texto):
        if tipo == "texto":
            saida.append(parte)
        else:
            guardados.append(f"{ABRE}{parte}{FECHA}")
            saida.append(f"[M{len(guardados)}]")
    return "".join(saida), guardados


def restaurar(texto: str, guardados: list[str]) -> str:
    def troca(m):
        k = int(m.group(1)) - 1
        return guardados[k] if 0 <= k < len(guardados) else m.group(0)
    return re.sub(r"\[M(\d+)\]", troca, texto)
