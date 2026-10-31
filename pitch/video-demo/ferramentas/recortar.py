"""Tira o fundo dos vídeos do time e põe o papel do site com a logo da PRISMA.

Entrada: ../gravacoes/whats-1.mp4 ... whats-4.mp4 (1 a 3: uma pessoa; 4: o grupo)
Saída:   ../gravacoes/time-1.mp4 ... time-4.mp4 (mesmo tamanho, com o som original)
"""
import re, subprocess, sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw

AQUI = Path(__file__).resolve().parent
GRAV = AQUI.parent / "gravacoes"
import os
WEB = Path(os.environ.get("PRISMA_WEB", AQUI.parent.parent.parent / "web"))
PAPEL = (0xFB, 0xF7, 0xEE)
# ajustes por vídeo: deslocamento horizontal (px) e escala da pessoa
DESLOCA = {}
ESCALA = {3: 1.18}


def sonda(arq):
    r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height,r_frame_rate",
                        "-of", "csv=p=0", str(arq)], capture_output=True, text=True).stdout.strip().split(",")
    n, d = r[2].split("/")
    return int(r[0]), int(r[1]), float(n) / float(d)


def fundo(w, h, unidade, x0, y0):
    img = Image.new("RGB", (w, h), PAPEL)
    dr = ImageDraw.Draw(img)
    passo = 16
    for y in range(passo // 2, h, passo):
        for x in range(passo // 2, w, passo):
            dr.rectangle([x, y, x + 1, y + 1], fill=(222, 219, 212))
    svg = (WEB / "assets" / "img" / "prisma-logo.svg").read_text(encoding="utf-8")
    for x, y, c in re.findall(r'<rect x="(\d+)" y="(\d+)" width="1" height="1" fill="(#\w+)"/>', svg):
        x, y = int(x), int(y)
        dr.rectangle([x0 + x * unidade, y0 + y * unidade, x0 + (x + 1) * unidade - 1, y0 + (y + 1) * unidade - 1], fill=c)
    return np.asarray(img).astype(np.float32)


def processar(i, sessao):
    from rembg import remove
    ent, sai = GRAV / f"whats-{i}.mp4", GRAV / f"time-{i}.mp4"
    w, h, fps = sonda(ent)
    grupo = i == 4
    escala = ESCALA.get(i, 0.84 if grupo else 0.92)
    unidade = 6 if grupo else 7
    x0 = (w - 30 * unidade) // 2 if grupo else 28
    y0 = 16 if grupo else 24
    base = fundo(w, h, unidade, x0, y0)
    leitor = subprocess.Popen(["ffmpeg", "-v", "error", "-i", str(ent), "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
    escritor = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{w}x{h}", "-r", str(fps), "-i", "-",
                                 "-i", str(ent), "-map", "0:v", "-map", "1:a", "-c:v", "libx264", "-crf", "16", "-pix_fmt", "yuv420p",
                                 "-c:a", "aac", "-b:a", "192k", "-shortest", str(sai)], stdin=subprocess.PIPE)
    n = 0
    sw, sh = int(w * escala), int(h * escala)
    while True:
        buf = leitor.stdout.read(w * h * 3)
        if len(buf) < w * h * 3:
            break
        quadro = Image.frombytes("RGB", (w, h), buf)
        alfa = remove(quadro, session=sessao, only_mask=True, post_process_mask=True)
        p = quadro.resize((sw, sh), Image.LANCZOS)
        a = alfa.resize((sw, sh), Image.LANCZOS)
        out = base.copy()
        px, py = (w - sw) // 2 + DESLOCA.get(i, 0), h - sh
        pa = np.asarray(a).astype(np.float32)[..., None] / 255.0
        pp = np.asarray(p).astype(np.float32)
        x0, x1 = max(0, px), min(w, px + sw)          # recorta o que sair da tela
        y0 = max(0, py)
        pa, pp = pa[y0 - py:, x0 - px:x1 - px], pp[y0 - py:, x0 - px:x1 - px]
        out[y0:h, x0:x1] = out[y0:h, x0:x1] * (1 - pa) + pp * pa
        escritor.stdin.write(out.clip(0, 255).astype(np.uint8).tobytes())
        n += 1
    escritor.stdin.close(); escritor.wait(); leitor.wait()
    print(f"time-{i}.mp4: {n} quadros")


if __name__ == "__main__":
    from rembg import new_session
    sessao = new_session("u2net_human_seg")
    for i in [int(x) for x in sys.argv[1:]] or [1, 2, 3, 4]:
        processar(i, sessao)
