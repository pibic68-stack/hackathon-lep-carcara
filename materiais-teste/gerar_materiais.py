"""Gera os materiais de teste do PRISMA (tema: o ciclo da água, Ciências, 5º ano).

Todo o texto e todos os desenhos foram feitos pelo time para a demonstração: nada de terceiros,
nenhum dado real de aluno. Pode ir para a IA gratuita e para a apresentação.

Saída (nesta pasta):
  1-texto-leitura-facil.pdf     texto longo, sem imagem: testa a Leitura Fácil, as etapas e as linhas de resposta
  2-imagem-cores.pdf            desenho em que a cor carrega a informação: testa os símbolos sobre as cores (P1)
  roteiro-audio.txt             o que a voz do Windows fala no 3-audio-aula.wav
  slides/slide-1.png ... 4      quadros do vídeo; o roteiro de cada um está em roteiro-video.json

O áudio (3-audio-aula.wav) e o vídeo (4-video-aula.mp4) são feitos no Windows por
gerar-audio-e-video.bat, porque precisam da voz em português do próprio Windows.

Uso (precisa de Pillow e reportlab):  python materiais-teste/gerar_materiais.py
"""
from __future__ import annotations

import json
import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

AQUI = Path(__file__).resolve().parent
FONTES = AQUI.parent / "web" / "assets" / "fontes"

TINTA, PAPEL, CEU, LARANJA = (30, 34, 53), (251, 247, 238), (31, 111, 178), (163, 64, 31)


def fonte(peso: int, tamanho: int):
    try:
        return ImageFont.truetype(str(FONTES / f"atkinson-{peso}.woff2"), tamanho)
    except OSError:
        return ImageFont.truetype("DejaVuSans-Bold.ttf" if peso == 700 else "DejaVuSans.ttf", tamanho)


# ------------------------------------------------------------------ textos

TITULO = "O ciclo da água"

TEXTO_LONGO = [
    ("titulo", "O ciclo da água"),
    ("p", "Ciências – 5º ano. Nome: ______________________ Data: ____/____"),
    ("titulo2", "Para começar"),
    ("p", "A água que existe no nosso planeta não é criada nem destruída, mas está sempre mudando de lugar e de estado "
          "físico, passando dos rios, lagos e oceanos para o ar, do ar para as nuvens e das nuvens de volta para o chão, "
          "em um caminho contínuo que os cientistas chamam de ciclo da água, ou ciclo hidrológico, e que acontece todos "
          "os dias sem que a gente perceba."),
    ("titulo2", "As etapas do ciclo"),
    ("p", "Quando o Sol aquece a superfície dos rios, dos lagos e dos oceanos, uma parte da água líquida se transforma "
          "em vapor de água, que é invisível e sobe para a atmosfera junto com o ar quente; esse processo recebe o nome "
          "de evaporação e é a primeira etapa do ciclo."),
    ("p", "As plantas também participam do ciclo, porque retiram água do solo pelas raízes e liberam parte dela pelas "
          "folhas na forma de vapor, em um processo chamado transpiração, que em uma floresta grande como a Amazônia "
          "chega a formar verdadeiros rios voadores de umidade."),
    ("p", "Lá no alto, onde a temperatura é mais baixa, o vapor de água esfria e se transforma em gotinhas muito pequenas "
          "de água líquida, que se juntam e formam as nuvens; essa mudança do estado gasoso para o estado líquido "
          "chama-se condensação."),
    ("p", "Quando as gotinhas das nuvens se juntam e ficam pesadas demais para continuar flutuando no ar, elas caem de "
          "volta na forma de chuva, de neve ou de granizo, dependendo da temperatura, e a essa etapa damos o nome de "
          "precipitação. Às vezes chove canivetes e a rua vira um rio!"),
    ("p", "A água que cai pode escorrer pela superfície até chegar aos rios e ao mar, ou pode se infiltrar no solo e "
          "abastecer os lençóis freáticos, que são reservatórios de água subterrânea usados por poços e nascentes, e "
          "assim o ciclo recomeça."),
    ("titulo2", "Atividade"),
    ("p", "Pegue um copo transparente e coloque água até a metade. Depois, cubra o copo com plástico filme e deixe-o "
          "no sol por uma hora. Em seguida, observe o plástico e anote o que você viu."),
    ("titulo2", "Responda"),
    ("p", "1) O que se formou no plástico filme? Por quê?"),
    ("linhas", 3),
    ("p", "2) Escreva com as suas palavras o que é evaporação."),
    ("linhas", 3),
    ("p", "3) Por que é importante cuidar das florestas para o ciclo da água?"),
    ("linhas", 3),
]

ROTEIRO_AUDIO = (
    "Olá, turma! Hoje vamos falar sobre o ciclo da água. "
    "A água do planeta não some e não aparece do nada. Ela muda de lugar e de estado o tempo todo. "
    "Primeiro, o Sol aquece os rios, os lagos e o mar. Uma parte da água vira vapor e sobe. Isso é a evaporação. "
    "As plantas também soltam vapor pelas folhas. Isso se chama transpiração. "
    "Lá no alto, o ar é frio. O vapor esfria e vira gotinhas, que formam as nuvens. Isso é a condensação. "
    "Quando as gotinhas ficam pesadas, elas caem como chuva. Isso é a precipitação. "
    "A chuva corre para os rios ou entra no solo, e o ciclo começa de novo. "
    "Para a próxima aula, observe o céu e anote se havia nuvens. Até lá!"
)

SLIDES = [
    {"titulo": "O ciclo da água", "linhas": ["Ciências – 5º ano", "A água muda de lugar e de estado o tempo todo."],
     "fala": "Olá! Neste vídeo vamos ver o ciclo da água. A água do planeta muda de lugar e de estado o tempo todo."},
    {"titulo": "1. Evaporação", "linhas": ["O Sol aquece rios, lagos e o mar.", "A água vira vapor e sobe."],
     "fala": "Primeiro vem a evaporação. O Sol aquece os rios, os lagos e o mar, e uma parte da água vira vapor e sobe."},
    {"titulo": "2. Condensação", "linhas": ["Lá no alto, o ar é frio.", "O vapor vira gotinhas: as nuvens."],
     "fala": "Depois vem a condensação. Lá no alto o ar é frio, e o vapor vira gotinhas que formam as nuvens."},
    {"titulo": "3. Precipitação", "linhas": ["Gotinhas pesadas caem.", "Chuva, neve ou granizo."],
     "fala": "Por fim, a precipitação. Quando as gotinhas ficam pesadas, elas caem como chuva. E o ciclo recomeça."},
]


# ------------------------------------------------------------------ desenho do ciclo (cor carrega a informação)

def desenho_ciclo(caminho: Path, largura: int = 1200, altura: int = 760) -> None:
    """A legenda é SÓ de cor, de propósito: é o caso que atrapalha o aluno daltônico.
    Setas vermelhas = evaporação; setas verdes = transpiração; gotas azuis = chuva; laranja = Sol."""
    im = Image.new("RGB", (largura, altura), (236, 242, 248))
    d = ImageDraw.Draw(im)
    # céu e chão
    d.rectangle([0, 520, largura, altura], fill=(128, 84, 46))                  # solo marrom
    d.polygon([(0, 560), (520, 520), (560, altura), (0, altura)], fill=(30, 110, 200))   # mar azul
    # Sol laranja
    d.ellipse([60, 50, 200, 190], fill=(245, 140, 30))
    for k in range(12):
        a = k * math.pi / 6
        d.line([(130 + 85 * math.cos(a), 120 + 85 * math.sin(a)), (130 + 115 * math.cos(a), 120 + 115 * math.sin(a))],
               fill=(245, 140, 30), width=8)
    # nuvem (cinza: não carrega informação)
    for x, y, r in [(640, 150, 60), (710, 120, 75), (790, 150, 60), (720, 170, 55)]:
        d.ellipse([x - r, y - r, x + r, y + r], fill=(205, 210, 220))
    # árvores verdes (transpiração)
    for x in (880, 1010):
        d.rectangle([x - 12, 430, x + 12, 525], fill=(110, 70, 35))
        d.ellipse([x - 70, 330, x + 70, 460], fill=(40, 150, 60))
    # setas vermelhas: evaporação (do mar para a nuvem)
    def seta(x0, y0, x1, y1, cor):
        d.line([(x0, y0), (x1, y1)], fill=cor, width=12)
        ang = math.atan2(y1 - y0, x1 - x0)
        p = [(x1 + 26 * math.cos(ang), y1 + 26 * math.sin(ang)),
             (x1 + 22 * math.cos(ang + 2.4), y1 + 22 * math.sin(ang + 2.4)),
             (x1 + 22 * math.cos(ang - 2.4), y1 + 22 * math.sin(ang - 2.4))]
        d.polygon(p, fill=cor)
    for x in (250, 340, 430):
        seta(x, 500, x + 150, 270, (215, 40, 40))
    # setas verdes: transpiração (das árvores para a nuvem)
    seta(880, 320, 800, 230, (40, 150, 60))
    seta(1010, 320, 860, 215, (40, 150, 60))
    # gotas azuis: chuva
    for x, y in [(650, 260), (700, 300), (750, 255), (800, 300), (680, 350), (760, 350)]:
        d.polygon([(x, y - 22), (x + 12, y), (x, y + 12), (x - 12, y)], fill=(30, 110, 200))
        d.ellipse([x - 12, y - 6, x + 12, y + 16], fill=(30, 110, 200))
    # legenda só com cor
    f = fonte(700, 26)
    d.rectangle([700, 560, 1180, 745], fill=(255, 255, 255), outline=TINTA, width=3)
    itens = [((215, 40, 40), "evaporação"), ((40, 150, 60), "transpiração"), ((30, 110, 200), "chuva")]
    for i, (cor, nome) in enumerate(itens):
        y = 585 + i * 52
        d.rectangle([725, y, 765, y + 34], fill=cor)
        d.text((785, y + 2), nome, font=f, fill=TINTA)
    im.save(caminho)


# ------------------------------------------------------------------ slides do vídeo

def slide(n: int, s: dict, caminho: Path) -> None:
    im = Image.new("RGB", (1280, 720), PAPEL)
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, 1280, 18], fill=CEU)
    d.text((80, 90), s["titulo"], font=fonte(700, 76), fill=CEU)
    for i, linha in enumerate(s["linhas"]):
        d.text((80, 240 + i * 80), linha, font=fonte(400, 48), fill=TINTA)
    # ícone simples por etapa
    cx, cy = 1050, 470
    if n == 1:                                   # gota
        d.polygon([(cx, cy - 150), (cx + 95, cy + 10), (cx - 95, cy + 10)], fill=(31, 111, 178))
        d.ellipse([cx - 100, cy - 60, cx + 100, cy + 130], fill=(31, 111, 178))
    elif n == 2:                                 # Sol e vapor subindo
        d.ellipse([cx - 60, cy - 170, cx + 60, cy - 50], fill=(163, 64, 31))
        for x in (cx - 80, cx, cx + 80):
            d.line([(x, cy + 140), (x, cy + 10)], fill=(31, 111, 178), width=12)
            d.polygon([(x - 22, cy + 20), (x + 22, cy + 20), (x, cy - 15)], fill=(31, 111, 178))
    elif n == 3:
        for x, y, r in [(cx - 70, cy, 60), (cx, cy - 30, 75), (cx + 70, cy, 60)]:
            d.ellipse([x - r, y - r, x + r, y + r], fill=(160, 170, 185))
    else:
        for x, y, r in [(cx - 70, cy - 60, 55), (cx, cy - 90, 70), (cx + 70, cy - 60, 55)]:
            d.ellipse([x - r, y - r, x + r, y + r], fill=(160, 170, 185))
        for x in (cx - 60, cx, cx + 60):
            d.line([(x, cy + 10), (x - 15, cy + 70)], fill=(31, 111, 178), width=10)
    d.text((80, 640), "PRISMA · material de teste feito pelo time", font=fonte(400, 26), fill=(90, 95, 110))
    im.save(caminho)


# ------------------------------------------------------------------ PDFs

def _pdf_fontes():
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    pdfmetrics.registerFont(TTFont("Texto", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"))
    pdfmetrics.registerFont(TTFont("Texto-Negrito", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"))


def _quebrar(c, texto: str, fonte_nome: str, tam: int, largura: float) -> list[str]:
    palavras, linhas, atual = texto.split(), [], ""
    for p in palavras:
        teste = (atual + " " + p).strip()
        if c.stringWidth(teste, fonte_nome, tam) <= largura:
            atual = teste
        else:
            linhas.append(atual)
            atual = p
    if atual:
        linhas.append(atual)
    return linhas


def pdf_texto(caminho: Path) -> None:
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas
    c = canvas.Canvas(str(caminho), pagesize=A4)
    c.setTitle(TITULO)
    L, A = A4
    m, y = 60, A - 70
    for tipo, valor in TEXTO_LONGO:
        if y < 110:
            c.showPage()
            y = A - 70
        if tipo == "titulo":
            c.setFont("Texto-Negrito", 22); c.drawString(m, y, valor); y -= 34
        elif tipo == "titulo2":
            y -= 8; c.setFont("Texto-Negrito", 15); c.drawString(m, y, valor); y -= 24
        elif tipo == "linhas":
            for _ in range(valor):
                c.setFont("Texto", 12); c.drawString(m, y, "." * 110); y -= 22
            y -= 6
        else:
            c.setFont("Texto", 12)
            for linha in _quebrar(c, valor, "Texto", 12, L - 2 * m):
                c.drawString(m, y, linha); y -= 17
            y -= 8
    c.save()


def pdf_imagem(caminho: Path, figura: Path) -> None:
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas
    c = canvas.Canvas(str(caminho), pagesize=A4)
    c.setTitle("O ciclo da água em desenho")
    L, A = A4
    m = 60
    c.setFont("Texto-Negrito", 22); c.drawString(m, A - 70, "O ciclo da água em desenho")
    c.setFont("Texto", 12)
    y = A - 100
    for linha in _quebrar(c, "Observe o desenho. Cada cor mostra uma etapa do ciclo da água. "
                              "Use a legenda para descobrir o que cada seta e cada gota representam.",
                          "Texto", 12, L - 2 * m):
        c.drawString(m, y, linha); y -= 17
    larg = L - 2 * m
    alt = larg * 760 / 1200
    c.drawImage(str(figura), m, y - alt - 10, larg, alt)
    y = y - alt - 40
    c.setFont("Texto-Negrito", 14); c.drawString(m, y, "Responda"); y -= 22
    c.setFont("Texto", 12)
    for q in ["1) De que cor são as setas que mostram a evaporação?",
              "2) O que as gotas representam?",
              "3) Por que as árvores também têm setas?"]:
        c.drawString(m, y, q); y -= 20
        c.drawString(m, y, "_" * 70); y -= 26
    c.save()


def main() -> None:
    _pdf_fontes()
    (AQUI / "slides").mkdir(exist_ok=True)
    figura = AQUI / "slides" / "desenho-ciclo.png"
    desenho_ciclo(figura)
    pdf_texto(AQUI / "1-texto-leitura-facil.pdf")
    pdf_imagem(AQUI / "2-imagem-cores.pdf", figura)
    for n, s in enumerate(SLIDES, 1):
        slide(n, s, AQUI / "slides" / f"slide-{n}.png")
    (AQUI / "roteiro-audio.txt").write_text(ROTEIRO_AUDIO + "\n", encoding="utf-8")
    (AQUI / "roteiro-video.json").write_text(
        json.dumps([{"imagem": f"slides/slide-{n}.png", "fala": s["fala"]} for n, s in enumerate(SLIDES, 1)],
                   ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("ok: materiais gerados em", AQUI)


if __name__ == "__main__":
    main()
