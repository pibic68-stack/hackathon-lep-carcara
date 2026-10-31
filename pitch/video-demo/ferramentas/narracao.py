"""Monta a narração de cada bloco e o tempo de cada frase.

Lê o texto de ../roteiro.md (blocos 3 a 7, uma frase por linha).
- Se existir ../gravacoes/narracao-N.(m4a|mp3|wav|ogg|aac), usa a gravação do time
  e acha as frases pelas pausas (silêncio de 0,5 s ou mais).
- Se não existir, gera uma voz sintética provisória (edge-tts, pt-BR).

Saída em ../saida/audio/: bloco-N.wav e tempos.json
    python narracao.py            (tudo)
    python narracao.py 3 5        (só alguns blocos)
"""
import asyncio, json, re, subprocess, sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parent
SAIDA = RAIZ / "saida" / "audio"
VOZ = "pt-BR-FranciscaNeural"
PAUSA = 0.55       # silêncio entre frases (voz sintética)
FOLGA_FIM = 0.8    # silêncio no fim de cada bloco

# como a legenda mostra o que a voz fala por extenso
LEGENDA = [
    ("dois milhões e meio", "2,5 milhões"),
    ("noventa e seis por cento", "96%"),
    ("trinta e cinco", "35"),
    ("dez padrões", "10 padrões"),
    ("cinquenta e um critérios", "51 critérios"),
    ("um em cada quatro", "1 em cada 4"),
]


def frases_do_roteiro():
    texto = (RAIZ / "roteiro.md").read_text(encoding="utf-8")
    texto = texto.split("## Texto da narração", 1)[1].split("## Fontes", 1)[0]
    blocos = {}
    for parte in re.split(r"^### ", texto, flags=re.M)[1:]:
        n = int(re.match(r"Bloco (\d+)", parte).group(1))
        linhas = [l.strip() for l in parte.splitlines()[1:]]
        blocos[n] = [l for l in linhas if l and not l.startswith("---")]
    return blocos


def legenda(frase):
    for falado, escrito in LEGENDA:
        frase = frase.replace(falado, escrito)
    return frase


def duracao(arq):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(arq)],
                       capture_output=True, text=True)
    return float(r.stdout.strip())


def ff(*args):
    subprocess.run(["ffmpeg", "-y", "-v", "error", *map(str, args)], check=True)


async def sintetizar(frase, destino):
    import edge_tts
    await edge_tts.Communicate(frase, VOZ, rate="-4%").save(str(destino))


def bloco_sintetico(n, frases):
    pasta = SAIDA / f"tmp-{n}"
    pasta.mkdir(parents=True, exist_ok=True)
    pedacos, tempos, t = [], [], 0.0
    for i, f in enumerate(frases):
        mp3 = pasta / f"f{i:02d}.mp3"
        if not mp3.exists():
            asyncio.run(sintetizar(f, mp3))
        wav = pasta / f"f{i:02d}.wav"
        # tira o silêncio das pontas e põe a pausa padrão no fim
        ff("-i", mp3, "-af", f"silenceremove=start_periods=1:start_threshold=-45dB,areverse,"
           f"silenceremove=start_periods=1:start_threshold=-45dB,areverse,apad=pad_dur={PAUSA}",
           "-ar", 48000, "-ac", 2, wav)
        d = duracao(wav)
        tempos.append({"t0": round(t, 3), "t1": round(t + d - PAUSA, 3), "texto": legenda(f)})
        pedacos.append(wav)
        t += d
    lista = pasta / "lista.txt"
    lista.write_text("".join(f"file '{p.as_posix()}'\n" for p in pedacos), encoding="utf-8")
    final = SAIDA / f"bloco-{n}.wav"
    ff("-f", "concat", "-safe", 0, "-i", lista, "-af", f"apad=pad_dur={FOLGA_FIM}", final)
    return final, tempos


def bloco_gravado(n, frases, arq):
    final = SAIDA / f"bloco-{n}.wav"
    # limpa ruído leve, nivela o volume e corta silêncio longo das pontas
    ff("-i", arq, "-af", "highpass=f=80,afftdn=nf=-25,"
       "silenceremove=start_periods=1:start_threshold=-40dB,areverse,"
       "silenceremove=start_periods=1:start_threshold=-40dB,areverse,"
       f"loudnorm=I=-16:TP=-1.5:LRA=11,apad=pad_dur={FOLGA_FIM}",
       "-ar", 48000, "-ac", 2, final)
    total = duracao(final) - FOLGA_FIM
    r = subprocess.run(["ffmpeg", "-v", "info", "-i", str(final), "-af", "silencedetect=n=-35dB:d=0.45", "-f", "null", "-"],
                       capture_output=True, text=True)
    ini = [float(x) for x in re.findall(r"silence_start: ([\d.]+)", r.stderr)]
    fim = [float(x) for x in re.findall(r"silence_end: ([\d.]+)", r.stderr)]
    falas, t = [], 0.0
    for a, b in zip(ini, fim):
        if a > t + 0.2:
            falas.append((t, a))
        t = b
    if t < total - 0.2:
        falas.append((t, total))
    if len(falas) == len(frases):
        tempos = [{"t0": round(a, 3), "t1": round(b, 3), "texto": legenda(f)} for (a, b), f in zip(falas, frases)]
    else:
        # não bateu: divide o tempo pelo tamanho de cada frase
        print(f"  bloco {n}: {len(falas)} trechos para {len(frases)} frases, dividindo pelo tamanho do texto")
        tam = [len(f) for f in frases]
        tempos, t = [], 0.0
        for f, c in zip(frases, tam):
            d = total * c / sum(tam)
            tempos.append({"t0": round(t, 3), "t1": round(t + d - 0.3, 3), "texto": legenda(f)})
            t += d
    return final, tempos


def main():
    SAIDA.mkdir(parents=True, exist_ok=True)
    blocos = frases_do_roteiro()
    quais = [int(x) for x in sys.argv[1:]] or sorted(blocos)
    arq_tempos = SAIDA / "tempos.json"
    todos = json.loads(arq_tempos.read_text(encoding="utf-8")) if arq_tempos.exists() else {}
    for n in quais:
        gravado = next((p for p in sorted((RAIZ / "gravacoes").glob(f"narracao-{n}.*"))), None) if (RAIZ / "gravacoes").exists() else None
        if gravado:
            final, tempos = bloco_gravado(n, blocos[n], gravado)
            fonte = "gravação"
        else:
            final, tempos = bloco_sintetico(n, blocos[n])
            fonte = "voz sintética"
        todos[str(n)] = {"duracao": round(duracao(final), 3), "fonte": fonte, "frases": tempos}
        print(f"bloco {n}: {todos[str(n)]['duracao']:.1f} s ({fonte})")
    arq_tempos.write_text(json.dumps(todos, ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
