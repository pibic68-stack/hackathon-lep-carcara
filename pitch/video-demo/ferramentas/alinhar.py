"""Usa a narração gravada num arquivo só (com tomadas repetidas) para montar os blocos 3 a 7.

1. Transcreve com tempo de cada palavra (faster-whisper) -> ../saida/audio/palavras.json
2. Acha cada frase do roteiro na transcrição; se uma frase foi gravada mais de uma vez, fica a ÚLTIMA tomada.
3. Corta cada frase do áudio (limpo e com volume nivelado) e junta com pausas iguais.
Saída: ../saida/audio/bloco-N.wav e tempos.json (o mesmo formato do narracao.py).

    python alinhar.py ../gravacoes/narracao-completa.mp4
"""
import difflib, json, re, subprocess, sys, unicodedata
from pathlib import Path
import numpy as np

import narracao as N

SR = 48000
# cortes conferidos de ouvido: início da frase (segundo na gravação), quando a pausa engana
INICIO_MANUAL = {"E se uma aula pudesse entrar": 49.04}
PAUSA = 0.5          # silêncio entre frases
ANTES, DEPOIS = 0.10, 0.22   # folga em volta de cada frase cortada
NUMEROS = {"2": "dois", "96": "noventa e seis", "%": "por cento", "35": "trinta e cinco", "10": "dez",
           "51": "cinquenta e um", "1": "um", "4": "quatro", "3": "tres", "5": "cinco"}


def norm(txt):
    txt = unicodedata.normalize("NFD", txt.lower())
    txt = "".join(c for c in txt if unicodedata.category(c) != "Mn")
    txt = re.sub(r"(\d+)\s*%", r"\1 %", txt)
    out = []
    for t in re.findall(r"[a-z]+|\d+|%", txt):
        out += NUMEROS.get(t, t).split()
    return out


def decodificar(arq):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(arq), "-af",
                          "highpass=f=80,afftdn=nf=-25,loudnorm=I=-16:TP=-1.5:LRA=11",
                          "-ac", "1", "-ar", str(SR), "-f", "s16le", "-"], capture_output=True).stdout
    return np.frombuffer(raw, np.int16).astype(np.float32) / 32768


def transcrever(audio):
    arq = N.SAIDA / "palavras.json"
    if arq.exists():
        return json.loads(arq.read_text(encoding="utf-8"))
    from faster_whisper import WhisperModel
    m = WhisperModel("small", device="cpu", compute_type="int8")
    a16 = audio[::3].copy()          # 48 kHz -> 16 kHz
    segs, _ = m.transcribe(a16, language="pt", word_timestamps=True, beam_size=5)
    ws = [{"w": w.word.strip(), "a": round(w.start, 2), "b": round(w.end, 2)} for s in segs for w in s.words]
    arq.write_text(json.dumps(ws, ensure_ascii=False), encoding="utf-8")
    return ws


def ocorrencias(frase, toks):
    """Todas as posições (i, j) em que a frase aparece na transcrição, com nota."""
    alvo = " ".join(frase)
    n = len(frase)
    achados = []
    for i in range(len(toks)):
        melhor = (0, None)
        for L in range(max(1, n - 3), n + 4):
            if i + L > len(toks):
                break
            nota = difflib.SequenceMatcher(None, alvo, " ".join(t for t, _ in toks[i:i + L])).ratio()
            if nota > melhor[0]:
                melhor = (nota, i + L)
        if melhor[0] >= 0.72:
            achados.append((melhor[0], i, melhor[1]))
    # fica só o melhor de cada grupo de posições vizinhas
    finais = []
    for a in sorted(achados, key=lambda x: -x[0]):
        if all(abs(a[1] - f[1]) > max(2, n // 2) for f in finais):
            finais.append(a)
    return sorted(finais, key=lambda x: x[1])


def mais_quieto(audio, de, ate):
    """Segundo mais silencioso (janela de 20 ms) entre 'de' e 'ate'."""
    de, ate = max(0.0, de), min(len(audio) / SR, ate)
    w = int(0.02 * SR)
    melhor, t_melhor = 9e9, de
    t = de
    while t + 0.02 <= ate:
        k = int(t * SR)
        e = float(np.mean(audio[k:k + w] ** 2))
        if e < melhor:
            melhor, t_melhor = e, t + 0.01
        t += 0.01
    return t_melhor


def pausas(audio):
    """Trechos de silêncio (início, fim) com pelo menos 0,1 s."""
    w = int(0.01 * SR)
    e = np.array([np.mean(audio[k:k + w] ** 2) for k in range(0, len(audio) - w, w)])
    db = 10 * np.log10(e + 1e-12)
    piso, topo = np.percentile(db, 8), np.percentile(db, 99)
    quieto = db < piso + 0.22 * (topo - piso)
    res, ini = [], None
    for k, q in enumerate(quieto):
        if q and ini is None:
            ini = k
        if not q and ini is not None:
            if k - ini >= 10:
                res.append((ini * 0.01, k * 0.01))
            ini = None
    return res


def maior_pausa(ps, de, ate):
    """A pausa mais longa que encosta na janela [de, ate]."""
    cand = [(min(b, ate) - max(a, de), a, b) for a, b in ps if b > de and a < ate]
    cand = [c for c in cand if c[0] > 0]
    if not cand:
        return None
    _, a, b = max(cand, key=lambda c: (c[2] - c[1]))
    return a, b


def main():
    arq = Path(sys.argv[1])
    audio = decodificar(arq)
    palavras = transcrever(audio)
    toks = []                         # (token normalizado, índice da palavra)
    for k, p in enumerate(palavras):
        for t in norm(p["w"]):
            toks.append((t, k))
    global PS
    PS = pausas(audio)
    blocos = N.frases_do_roteiro()
    ordem = [(b, f) for b in sorted(blocos) for f in blocos[b]]
    # de trás para frente: cada frase pega a última tomada antes da frase seguinte
    limite = len(toks)
    escolha = [None] * len(ordem)
    for idx in range(len(ordem) - 1, -1, -1):
        b, f = ordem[idx]
        occ = [o for o in ocorrencias(norm(f), toks) if o[2] <= limite]
        if not occ:
            raise SystemExit(f"não achei a frase: {f}")
        nota, i, j = occ[-1]
        escolha[idx] = (palavras[toks[i][1]]["a"], palavras[toks[j - 1][1]]["b"], nota)
        limite = i
    todos = {}
    for b in sorted(blocos):
        pedacos, tempos, t = [], [], 0.0
        for idx, (bb, f) in enumerate(ordem):
            if bb != b:
                continue
            a, z, nota = escolha[idx]
            # não invade a frase anterior/seguinte da gravação
            ant = escolha[idx - 1][1] if idx > 0 else 0.0
            seg = escolha[idx + 1][0] if idx + 1 < len(escolha) else len(audio) / SR
            pa = maior_pausa(PS, max(ant - 0.3, a - 1.2), a + 0.3)
            pz = maior_pausa(PS, z - 0.3, min(seg + 0.3, z + 1.2))
            a0 = pa[1] - 0.07 if pa else mais_quieto(audio, max(ant, a - 0.3), a + 0.06)
            z0 = pz[0] + 0.09 if pz else mais_quieto(audio, z - 0.06, min(seg, z + 0.4))
            for chave, seg_manual in INICIO_MANUAL.items():
                if f.startswith(chave):
                    a0 = seg_manual
            a, z = a0 + 0.07, z0 - 0.09
            pedaco = audio[int(a0 * SR):int(z0 * SR)].copy()
            r = int(0.02 * SR)
            pedaco[:r] *= np.linspace(0, 1, r); pedaco[-r:] *= np.linspace(1, 0, r)
            d = len(pedaco) / SR
            tempos.append({"t0": round(t + max(0, a - a0), 3), "t1": round(t + (z - a0), 3), "texto": N.legenda(f)})
            pedacos += [pedaco, np.zeros(int(PAUSA * SR), np.float32)]
            t += d + PAUSA
            print(f"  {b}  {a:6.2f}-{z:6.2f}  nota {nota:.2f}  {f}")
        pedacos.append(np.zeros(int((N.FOLGA_FIM - PAUSA) * SR), np.float32))
        bloco = np.concatenate(pedacos)
        destino = N.SAIDA / f"bloco-{b}.wav"
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "s16le", "-ar", str(SR), "-ac", "1", "-i", "-",
                        "-ac", "2", str(destino)], input=(bloco.clip(-1, 1) * 32767).astype(np.int16).tobytes(), check=True)
        todos[str(b)] = {"duracao": round(len(bloco) / SR, 3), "fonte": "gravação", "frases": tempos}
        print(f"bloco {b}: {todos[str(b)]['duracao']:.1f} s")
    (N.SAIDA / "tempos.json").write_text(json.dumps(todos, ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
