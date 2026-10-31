"""Monta o vídeo final: intro + bloco 2 (time) + blocos 3 a 7 + legendas.

Antes: python narracao.py  e  sh render_tudo.sh
Depois: python montar.py
Saída em ../saida/: prisma-demo.mp4 (com legenda), prisma-demo-sem-legenda.mp4, prisma-demo.srt

Gravações (em ../gravacoes/), todas opcionais (se faltar, entra um marcador):
    intro.mp4 | intro.mov
    time-1.mp4 ... time-4.mp4, time-todos.mp4
"""
import json, re, subprocess
from pathlib import Path

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parent
SAIDA = RAIZ / "saida"
SEG = SAIDA / "segmentos"
GRAV = RAIZ / "gravacoes"
W, H, FPS = 1920, 1080, 30
INICIO_CLIPE = 1.5        # corta os 2 s parados do começo de cada vídeo do time (deixa 0,5 s)
FONTE_ARIAL = "C\\:/Windows/Fonts/arial.ttf"
VIDEO = ["-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p", "-r", str(FPS)]
AUDIO = ["-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2"]


def ff(*args):
    cmd = ["ffmpeg", "-y", "-v", "error", *map(str, args)]
    subprocess.run(cmd, check=True)


def duracao(arq):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(arq)],
                       capture_output=True, text=True)
    return float(r.stdout.strip())


def tem_audio(arq):
    r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "a", "-show_entries", "stream=index", "-of", "csv=p=0", str(arq)],
                       capture_output=True, text=True)
    return bool(r.stdout.strip())


def achar(nome):
    for ext in ("mp4", "mov", "MP4", "MOV", "m4v", "webm", "mkv"):
        p = GRAV / f"{nome}.{ext}"
        if p.exists():
            return p
    return None


def marcador(texto, dur, destino, cor="0x1F6FB2"):
    ff("-f", "lavfi", "-i", f"color=c={cor}:s={W}x{H}:r={FPS}:d={dur}",
       "-f", "lavfi", "-i", f"anullsrc=r=48000:cl=stereo", "-t", dur,
       "-vf", f"drawtext=fontfile='{FONTE_ARIAL}':text='{texto}':fontcolor=white:fontsize=80:x=(w-tw)/2:y=(h-th)/2",
       *VIDEO, *AUDIO, "-shortest", destino)
    return destino


def tempos_time():
    js = (RAIZ / "cenas" / "time.js").read_text(encoding="utf-8")
    m = re.search(r"TEMPOS_TIME\s*=\s*(\{.*?\});", js, re.S)
    t = json.loads(re.sub(r"(\w+):", r'"\1":', m.group(1)))
    t["palavras"] = re.findall(r'palavra:\s*"([^"]*)"', js)
    t["falas"] = [float(x) for x in re.findall(r'[{ ,]fala:\s*([\d.]+)', js)]
    return t, t["palavras"]


# ---------------- segmentos ----------------
def seg_intro():
    destino = SEG / "1-intro.mp4"
    origem = achar("intro")
    if not origem:
        print("  intro: faltando, usando marcador de 30 s")
        return marcador("intro (30 s)", 30, destino, "0x1E2235")
    entradas = ["-i", origem]
    mapa = ["-map", "0:v:0"]
    if tem_audio(origem):
        mapa += ["-map", "0:a:0"]
    else:
        entradas += ["-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo"]
        mapa += ["-map", "1:a:0", "-shortest"]
    ff(*entradas, *mapa, "-vf", f"scale={W}:{H}:force_original_aspect_ratio=decrease,pad={W}:{H}:(ow-iw)/2:(oh-ih)/2:color=0x1E2235,fps={FPS},setsar=1",
       *VIDEO, *AUDIO, destino)
    return destino


def seg_time():
    """4 cartões; cada vídeo entra alinhado à sua palavra (nós, somos, a, PRISMA)."""
    destino = SEG / "2-time.mp4"
    T, _ = tempos_time()
    fim = T["fim"]
    fundo = SAIDA / "fotos" / "bloco-2-0.0.png"
    camada = SAIDA / "cenas" / "bloco-2.mov"
    POS = [(200, 15), (1040, 15), (200, 455), (1040, 455)]
    clipes = []
    for i in range(4):
        c = achar(f"time-{i + 1}")
        if not c:
            c = marcador(f"video {i + 1}", 6, SEG / f"marcador-time-{i + 1}.mp4", ["0x1F6FB2", "0xA3401F", "0x2E7D32", "0x8A5A2B"][i])
        clipes.append(c)
    entradas = ["-loop", "1", "-t", fim, "-i", fundo]
    for i, c in enumerate(clipes):
        ss = max(0.0, T["falas"][i] - T["antes_fala"]) if i < len(T["falas"]) else INICIO_CLIPE
        entradas += ["-ss", round(ss, 3), "-i", c]
    entradas += ["-i", camada]
    f = [f"[0:v]scale={W}:{H},fps={FPS},format=yuv420p[base0]"]
    ult = "base0"
    for i, (x, y) in enumerate(POS):
        t0 = T["cartoes"][i]
        f.append(f"[{i + 1}:v]scale=668:371:force_original_aspect_ratio=increase,crop=668:371,setsar=1,fps={FPS},"
                 f"tpad=stop_mode=clone:stop_duration=8,setpts=PTS-STARTPTS+{t0}/TB,fade=t=in:st={t0}:d=0.25[v{i}]")
        f.append(f"[{ult}][v{i}]overlay={x + 6}:{y + 6}:eof_action=repeat:enable='between(t,{t0},{T['logo'] + 0.4})'[b{i}]")
        ult = f"b{i}"
    f.append(f"[5:v]format=rgba[cam];[{ult}][cam]overlay=0:0:format=auto,format=yuv420p[vout]")
    # som: só o trecho da palavra de cada vídeo (tira o ruído da sala entre as falas)
    sons = []
    for i, c in enumerate(clipes):
        if not tem_audio(c):
            continue
        a = T["antes_fala"] - 0.12
        d = 0.75 if i < 3 else 0.95
        t = T["cartoes"][i] + a
        f.append(f"[{i + 1}:a]atrim={a}:{a + d},asetpts=PTS-STARTPTS,afade=t=in:d=0.04,afade=t=out:st={d - 0.15}:d=0.15,"
                 f"loudnorm=I=-16:TP=-1.5,aresample=48000,adelay={int(t * 1000)}:all=1[a{i}]")
        sons.append(f"[a{i}]")
    entradas += ["-f", "lavfi", "-i", "sine=frequency=1319:duration=0.25"]
    f.append(f"[6:a]volume=0.15,afade=t=out:st=0.05:d=0.2,adelay={int((T['logo'] + 0.3) * 1000)}:all=1[plim]")
    sons.append("[plim]")
    f.append("".join(sons) + f"amix=inputs={len(sons)}:normalize=0:duration=longest,apad=whole_dur={fim}[aout]")
    ff(*entradas, "-filter_complex", ";".join(f), "-map", "[vout]", "-map", "[aout]", "-t", fim, *VIDEO, *AUDIO, destino)
    return destino


def seg_bloco(n):
    destino = SEG / f"{n}-bloco.mp4"
    video = SAIDA / "cenas" / f"bloco-{n}.mp4"
    audio = SAIDA / "audio" / f"bloco-{n}.wav"
    d = duracao(video)
    ff("-i", video, "-i", audio, "-map", "0:v", "-map", "1:a", "-af", f"apad,atrim=0:{d}", "-t", d,
       *VIDEO, *AUDIO, destino)
    return destino


# ---------------- legendas ----------------
def tempo_ass(s):
    h = int(s // 3600); m = int(s % 3600 // 60); sec = s % 60
    return f"{h}:{m:02d}:{sec:05.2f}"


def tempo_srt(s):
    ms = int(round(s * 1000))
    return f"{ms // 3600000:02d}:{ms // 60000 % 60:02d}:{ms // 1000 % 60:02d},{ms % 1000:03d}"


def fonte_ttf():
    from fontTools.ttLib import TTFont
    pasta = SAIDA / "fontes"
    pasta.mkdir(exist_ok=True)
    web = Path(__import__("os").environ.get("PRISMA_WEB", RAIZ.parent.parent / "web"))
    ttf = pasta / "atkinson-700.ttf"
    if not ttf.exists():
        f = TTFont(str(web / "assets" / "fontes" / "atkinson-700.woff2"))
        f.flavor = None
        f.save(str(ttf))
    return pasta


def legendas(inicios):
    T, _ = tempos_time()
    tempos = json.loads((SAIDA / "audio" / "tempos.json").read_text(encoding="utf-8"))
    falas = []
    b2 = inicios[2]
    ps = T["palavras"]
    for i in range(len(ps)):
        txt = " ".join(ps[:i + 1])
        txt = txt[0].upper() + txt[1:] + ("!" if i == len(ps) - 1 else "…")
        a = b2 + T["cartoes"][i] + T["antes_fala"]
        b = b2 + (T["cartoes"][i + 1] + T["antes_fala"] if i + 1 < len(ps) else T["logo"] + 1.5)
        falas.append((a, b, txt))
    for n in (3, 4, 5, 6, 7):
        for fr in tempos[str(n)]["frases"]:
            falas.append((inicios[n] + fr["t0"], inicios[n] + fr["t1"] + 0.3, fr["texto"]))
    # não deixa uma legenda passar por cima da próxima
    falas.sort()
    for i in range(len(falas) - 1):
        a, b, t = falas[i]
        falas[i] = (a, min(b, falas[i + 1][0] - 0.04), t)
    srt = "".join(f"{i + 1}\n{tempo_srt(a)} --> {tempo_srt(b)}\n{t}\n\n" for i, (a, b, t) in enumerate(falas))
    (SAIDA / "prisma-demo.srt").write_text(srt, encoding="utf-8")
    ass = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {W}
PlayResY: {H}
WrapStyle: 0

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Fala,Atkinson Hyperlegible Next,54,&H00EEF7FB,&H00EEF7FB,&H0035221E,&H0035221E,-1,0,0,0,100,100,0,0,3,16,0,2,280,280,46,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    ass += "".join(f"Dialogue: 0,{tempo_ass(a)},{tempo_ass(b)},Fala,,0,0,0,,{t}\n" for a, b, t in falas)
    (SAIDA / "legendas.ass").write_text(ass, encoding="utf-8")


def main():
    SEG.mkdir(parents=True, exist_ok=True)
    print("segmentos…")
    segs = {1: seg_intro(), 2: seg_time()}
    for n in (3, 4, 5, 6, 7):
        segs[n] = seg_bloco(n)
    inicios, t = {}, 0.0
    for n in sorted(segs):
        inicios[n] = t
        t += duracao(segs[n])
    print(f"duração total: {t:.1f} s ({int(round(t)) // 60} min {int(round(t)) % 60} s)")
    lista = SEG / "lista.txt"
    lista.write_text("".join(f"file '{segs[n].as_posix()}'\n" for n in sorted(segs)), encoding="utf-8")
    sem = SAIDA / "prisma-demo-sem-legenda.mp4"
    ff("-f", "concat", "-safe", 0, "-i", lista, "-c", "copy", sem)
    print("legendas…")
    legendas(inicios)
    fonte_ttf()
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", sem.name, "-vf", "ass=legendas.ass:fontsdir=fontes",
                    *VIDEO, "-c:a", "copy", "prisma-demo.mp4"], check=True, cwd=SAIDA)
    print(SAIDA / "prisma-demo.mp4")


if __name__ == "__main__":
    main()
