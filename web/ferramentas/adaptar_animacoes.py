"""Troca as cores das animações Lottie pela paleta do site e gera arquivos .js.

Entrada: web/assets/anim/originais/*.json (arquivos como vieram do LottieFiles)
Saída:   web/assets/anim/<nome>.js   (window.ANIMACOES.<nome> = {...})

Por que .js e não .json: assim o site abre com duplo clique (file://),
sem precisar de servidor para fazer fetch do JSON.

A pixelização em si acontece no navegador (js/lottie-pixel.js).
Uso: python ferramentas/adaptar_animacoes.py   (rodar dentro de web/)
"""
import base64
import colorsys
import io
import json
from pathlib import Path

from PIL import Image

PASTA = Path(__file__).resolve().parent.parent / "assets" / "anim"


def rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


# Rampas da paleta (do escuro para o claro)
RAMPAS = {
    "neutro": ["#1E2235", "#3A3F5C", "#8A8FA8", "#D9D4C7", "#FBF7EE"],
    "ceu": ["#1F4F86", "#1F6FB2", "#3E9BEA", "#57B3F9", "#A6DCFD", "#CDEBFE"],
    "sol": ["#B5762A", "#E9A23B", "#FFC93C", "#FFE38A"],
    "laranja": ["#A3401F", "#C4552B", "#FFAD60", "#FFD3A6"],
    "grama": ["#2E7D32", "#4A9A4B", "#7BD389", "#CDEFD2"],
}
RAMPAS = {k: [rgb(c) for c in v] for k, v in RAMPAS.items()}


def lum(c):
    r, g, b = (x / 255 for x in c)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def familia(c):
    h, s, v = colorsys.rgb_to_hsv(*(x / 255 for x in c))
    h *= 360
    if s < 0.18 or v < 0.12:
        return "neutro"
    if 30 <= h < 75:
        return "sol"
    if 75 <= h < 170:
        return "grama"
    if 170 <= h < 335:  # azuis e roxos viram céu
        return "ceu"
    return "laranja"


def mapear(c, troca=None):
    """Cor (0-255) -> cor da paleta com luminosidade mais próxima, na mesma família."""
    fam = familia(c)
    if troca and fam in troca:
        fam = troca[fam]
    rampa = RAMPAS[fam]
    return min(rampa, key=lambda p: abs(lum(p) - lum(c)))


def mapear_lottie(k, troca=None):
    c = tuple(round(x * 255) for x in k[:3])
    n = mapear(c, troca)
    return [round(x / 255, 4) for x in n] + list(k[3:])


def recolorir(o, troca=None):
    if isinstance(o, dict):
        if o.get("ty") in ("fl", "st") and "c" in o:
            o["c"].pop("x", None)  # remove expressões que apontam para uma camada "Controller" que não existe
            k = o["c"].get("k")
            if isinstance(k, list) and k and isinstance(k[0], (int, float)):
                o["c"]["k"] = mapear_lottie(k, troca)
            elif isinstance(k, list):  # cor animada
                for quadro in k:
                    if isinstance(quadro, dict) and "s" in quadro:
                        quadro["s"] = mapear_lottie(quadro["s"], troca)
        if o.get("ty") in ("gf", "gs") and "g" in o:
            p = o["g"]["p"]
            k = o["g"]["k"]
            if k.get("a") == 0:
                v = k["k"]
                for i in range(p):
                    v[i * 4 + 1:i * 4 + 4] = mapear_lottie(v[i * 4 + 1:i * 4 + 4], troca)
        for v in o.values():
            recolorir(v, troca)
    elif isinstance(o, list):
        for v in o:
            recolorir(v, troca)


def recolorir_imagens(d):
    """As imagens PNG embutidas (o laptop) também passam para a paleta, pixel a pixel."""
    for a in d.get("assets", []):
        p = a.get("p", "")
        if not p.startswith("data:image"):
            continue
        cab, b64 = p.split(",", 1)
        img = Image.open(io.BytesIO(base64.b64decode(b64))).convert("RGBA")
        px = img.load()
        cache = {}
        for y in range(img.height):
            for x in range(img.width):
                r, g, b, al = px[x, y]
                if al == 0:
                    continue
                chave = (r // 8, g // 8, b // 8)
                if chave not in cache:
                    cache[chave] = mapear((r, g, b))
                px[x, y] = cache[chave] + (255 if al > 96 else 0,)
        buf = io.BytesIO()
        img.save(buf, "PNG")
        a["p"] = "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()


def salvar(nome, d):
    js = "window.ANIMACOES = window.ANIMACOES || {};\nwindow.ANIMACOES[%s] = %s;\n" % (
        json.dumps(nome), json.dumps(d, separators=(",", ":")))
    (PASTA / f"{nome}.js").write_text(js, encoding="utf-8")
    print(nome, len(js) // 1024, "KB")


def main():
    # três livros pulando: o terceiro vira verde para variar
    d = json.loads((PASTA / "originais" / "livros.json").read_text(encoding="utf-8"))
    for i, camada in enumerate(d["layers"]):
        recolorir(camada, {"ceu": "grama"} if i == 2 else None)
    salvar("livros", d)

    # livro abrindo: capa azul e páginas no tom papel
    d = json.loads((PASTA / "originais" / "livro.json").read_text(encoding="utf-8"))
    recolorir(d)
    salvar("livro", d)

    # computador: imagens raster com degradê roxo
    d = json.loads((PASTA / "originais" / "computador.json").read_text(encoding="utf-8"))
    recolorir(d)
    recolorir_imagens(d)
    salvar("computador", d)


if __name__ == "__main__":
    main()
