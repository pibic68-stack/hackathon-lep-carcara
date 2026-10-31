"""Trilha original da intro PRISMA, sintetizada com numpy (sem amostras de terceiros).

96 BPM, fá maior, 12 compassos de 2,5 s. Lê saida/eventos.json (gerado por animacao.py)
para sincronizar palavras, montagem do prisma, raio, cores e corte.
Saída: saida/trilha.wav (48 kHz, estéreo, 16 bits).

    python trilha.py
"""
import json, os, wave
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "saida")
EV = json.load(open(os.path.join(OUT, "eventos.json"), encoding="utf-8"))
SR = 48000
DUR = 30.0
N = int(DUR * SR)
BEAT = 60 / 96
rng = np.random.default_rng(3)

mus = np.zeros((2, N))   # música (passa pelo reverb e é cortada no fim)
sfx = np.zeros((2, N))   # efeitos (whoosh final fica fora do corte)


def mtof(m):
    return 440.0 * 2 ** ((m - 69) / 12)


def add(buf, t0, sig, gain=1.0, pan=0.0):
    i0 = int(t0 * SR)
    if i0 >= N:
        return
    sig = sig[: N - i0]
    l, r = np.cos((pan + 1) * np.pi / 4), np.sin((pan + 1) * np.pi / 4)
    buf[0, i0:i0 + len(sig)] += sig * gain * l * 1.414
    buf[1, i0:i0 + len(sig)] += sig * gain * r * 1.414


def tt(d):
    return np.arange(int(d * SR)) / SR


def attack(t, a):
    return np.minimum(1, t / a)


# ---------------------------------------------------------------- instrumentos
def piano(m, dur, vel=1.0):
    f = mtof(m)
    d = dur + 1.6
    t = tt(d)
    s = np.zeros_like(t)
    for k in range(1, 9):
        fk = f * k * np.sqrt(1 + 0.0004 * k * k)
        if fk > 12000:
            break
        s += (1 / k ** 1.4) * np.exp(-t * (0.9 + 0.55 * k)) * np.sin(2 * np.pi * fk * t + rng.uniform(0, 6))
    rel = np.where(t > dur, np.exp(-(t - dur) * 7), 1)
    return s * attack(t, 0.004) * rel * vel * 0.5


def bell(m, dur=1.6, vel=1.0):
    """Celesta / caixinha de música."""
    f = mtof(m)
    t = tt(dur + 1.2)
    s = (np.sin(2 * np.pi * f * t) * np.exp(-t * 2.2)
         + 0.35 * np.sin(2 * np.pi * f * 2.0 * t) * np.exp(-t * 4)
         + 0.18 * np.sin(2 * np.pi * f * 2.76 * t) * np.exp(-t * 7)
         + 0.06 * np.sin(2 * np.pi * f * 5.4 * t) * np.exp(-t * 12))
    return s * attack(t, 0.002) * vel * 0.45


def marimba(m, vel=1.0):
    f = mtof(m)
    t = tt(1.4)
    s = (np.sin(2 * np.pi * f * t) * np.exp(-t * 4.2)
         + 0.28 * np.sin(2 * np.pi * f * 3.93 * t) * np.exp(-t * 13)
         + 0.08 * np.sin(2 * np.pi * f * 9.2 * t) * np.exp(-t * 30))
    return s * attack(t, 0.0015) * vel * 0.6


def pad(notes, dur, vel=1.0, a=0.7, r=1.0):
    t = tt(dur + r)
    s = np.zeros_like(t)
    for m in notes:
        f = mtof(m)
        for det in (-0.08, 0.0, 0.07):
            fd = f * 2 ** (det / 12)
            vib = 0.0025 * np.sin(2 * np.pi * 4.6 * t + rng.uniform(0, 6))
            for k in range(1, 6):
                s += (0.5 / k ** 1.6) * np.sin(2 * np.pi * fd * k * t * (1 + vib) + rng.uniform(0, 6))
    env = np.minimum(1, t / a) * np.where(t > dur, np.exp(-(t - dur) * 4 / r), 1)
    return s * env * vel * 0.06 / max(1, len(notes) ** 0.5)


def bass(m, dur, vel=1.0):
    f = mtof(m)
    t = tt(dur + 0.4)
    s = np.sin(2 * np.pi * f * t) + 0.25 * np.sin(2 * np.pi * 2 * f * t) + 0.08 * np.sin(2 * np.pi * 3 * f * t)
    env = attack(t, 0.01) * (0.55 + 0.45 * np.exp(-t * 3)) * np.where(t > dur, np.exp(-(t - dur) * 12), 1)
    return s * env * vel * 0.26


def noise(d):
    return rng.standard_normal(int(d * SR))


def lowpass(x, fc):
    """Passa-baixa de 1 polo; fc pode ser vetor (corte variável)."""
    fc = np.broadcast_to(np.asarray(fc, dtype=float), x.shape)
    a = 1 - np.exp(-2 * np.pi * fc / SR)
    y = np.empty_like(x)
    acc = 0.0
    for i in range(len(x)):
        acc += a[i] * (x[i] - acc)
        y[i] = acc
    return y


def shaker(vel=1.0):
    x = noise(0.07)
    x = x - lowpass(x, 5000)
    t = tt(0.07)
    return x * np.exp(-t * 60) * attack(t, 0.003) * vel * 0.25


def kick(vel=1.0):
    t = tt(0.35)
    f = 48 + 70 * np.exp(-t * 30)
    ph = 2 * np.pi * np.cumsum(f) / SR
    return np.sin(ph) * np.exp(-t * 9) * attack(t, 0.002) * vel


def whoosh(d, f0, f1, peak_at=0.7, vel=1.0):
    t = tt(d)
    u = t / d
    fc = f0 * (f1 / f0) ** np.minimum(1, u / peak_at) * np.where(u > peak_at, np.exp(-(u - peak_at) * 4), 1)
    x = lowpass(noise(d), fc)
    x = x - lowpass(x, fc * 0.15)
    env = np.where(u < peak_at, (u / peak_at) ** 2, np.exp(-(u - peak_at) / (1 - peak_at) * 4))
    return x * env * vel


# ---------------------------------------------------------------- harmonia (compasso -> acorde)
def bar(n):
    return (n - 1) * 2.5


CH = {1: [53, 57, 60, 64], 2: [53, 57, 60, 65], 3: [50, 53, 57, 60], 4: [58, 62, 65, 69], 5: [60, 64, 67, 72],
      6: [57, 60, 64, 67], 7: [62, 65, 69, 72], 9: [60, 65, 67, 72], 10: [58, 62, 65, 72]}
BASS = {2: 41, 3: 38, 4: 34, 5: 36, 6: 33, 7: 38, 9: 36, 10: 34}
for n, notes in CH.items():
    add(mus, bar(n), pad(notes, 2.5, vel=0.8 if n > 1 else 0.9, a=1.4 if n == 1 else 0.5), pan=0.0)
for n, m in BASS.items():
    add(mus, bar(n), bass(m, 2.3, 0.9 if n != 9 else 0.6))
# compasso 8: Bb -> C com subida
add(mus, bar(8), pad([58, 62, 65, 70], 1.25, 0.85, a=0.3, r=0.4))
add(mus, bar(8) + 1.25, pad([60, 64, 67, 72], 1.25, 0.95, a=0.2, r=0.6))
add(mus, bar(8), bass(34, 1.2))
add(mus, bar(8) + 1.25, bass(36, 1.2))
# final: fá com nona, compassos 11-12
add(mus, bar(11), pad([53, 57, 60, 67, 69], 4.5, 1.0, a=0.15, r=1.5))
add(mus, bar(11), bass(29, 4.4, 1.0))
for i, m in enumerate([41, 53, 60, 65, 69, 72, 77]):
    add(mus, bar(11) + i * 0.025, piano(m, 3.6, 0.55), pan=-0.1 + i * 0.03)

# compasso 1: motivo de caixinha de música
for b_, m, d in [(0, 84, .5), (.5, 81, .5), (1, 77, .5), (1.5, 79, .5), (2, 81, 1), (3, 84, 1)]:
    add(mus, 0.3 + b_ * BEAT, bell(m, 1.4, 0.7), pan=0.25)
# compassos 2-3: piano
for b_, m, d in [(4, 69, 1), (5, 72, 1), (6, 77, 1.5), (7.5, 76, .5), (8, 74, 1), (9, 77, 1), (10, 81, 1.5), (11.5, 79, .5)]:
    add(mus, b_ * BEAT, piano(m, d * BEAT, 0.8), pan=-0.15)
for n in (2, 3):
    for m in CH[n][:3]:
        add(mus, bar(n), piano(m - 12, 2.4, 0.28), pan=-0.2)

# compassos 4-7: marimba, uma nota por palavra (+ ecos suaves)
WORD_NOTES = [77, 74, 76, 79, 81, 84, 86, 81]
FILL = [70, 74, 72, 76, 76, 79, 81, 77]
for i, t0 in enumerate(EV["palavras"]):
    add(mus, t0, marimba(WORD_NOTES[i], 1.0), pan=-0.35 if i % 2 == 0 else 0.35)
    add(mus, t0 + BEAT, marimba(FILL[i], 0.42), pan=0.2 if i % 2 == 0 else -0.2)
    add(mus, t0 + 1.5 * BEAT, marimba(FILL[i] - 5, 0.3), pan=0.0)
for n in (4, 5, 6, 7):
    for m in CH[n][:3]:
        add(mus, bar(n), piano(m - 12, 2.4, 0.22), pan=-0.2)
# percussão leve (compassos 4-8)
t = bar(4)
k = 0
while t < bar(9) - 0.01:
    add(mus, t, shaker(1.0 if k % 2 == 0 else 0.55), pan=0.3)
    if k % 4 == 0 and t >= bar(5):
        add(mus, t, kick(0.35))
    t += BEAT / 2
    k += 1
# compasso 8: escala subindo até a chegada no quadro
run = [72, 74, 76, 77, 79, 81, 82, 84]
for i, m in enumerate(run):
    add(mus, bar(8) + 1.25 + i * BEAT / 4, piano(m, BEAT / 4, 0.45 + 0.04 * i), pan=0.1)
add(mus, bar(8), whoosh(2.5, 200, 2500, peak_at=0.98, vel=0.05), pan=0.0)
add(mus, bar(9), bell(84, 2.0, 0.6), pan=0.0)

# compasso 9: pó de giz (brilhinhos) e montagem do prisma (uma nota por linha de pixels)
for _ in range(26):
    add(sfx, EV["giz_some"] + rng.uniform(0, 1.1), bell(int(rng.choice([96, 98, 101, 103, 105])), 0.3, rng.uniform(0.08, 0.18)),
        pan=rng.uniform(-0.7, 0.7))
add(sfx, EV["giz_some"], lowpass(noise(1.2), 2500) * np.exp(-tt(1.2) * 3) * 0.03, pan=0.0)
PENTA = [65, 67, 69, 72, 74, 77, 79, 81, 84, 86, 89, 91, 93, 96, 98, 101]
for i, t0 in enumerate(EV["linhas"]):
    add(sfx, t0, marimba(PENTA[i], 0.32 - 0.008 * i), pan=-0.3 + 0.04 * i)

# compasso 10: raio de luz e as seis cores
add(sfx, EV["feixe"] - 0.05, whoosh(0.5, 400, 6000, peak_at=0.72, vel=0.11), pan=-0.6)
for m in (77, 84, 89):
    add(mus, EV["feixe_bate"], bell(m, 2.2, 0.35), pan=0.0)
add(mus, EV["feixe_bate"], kick(0.25))
for i, (t0, m) in enumerate(zip(EV["cores"], [77, 81, 84, 89, 93, 96])):
    add(mus, t0, bell(m, 1.8, 0.75), pan=-0.2 + 0.1 * i)
    add(mus, t0, marimba(m - 12, 0.35), pan=0.2 - 0.1 * i)
# compasso 11: o motivo volta, suave, sob o slogan
for b_, m in [(0, 84), (.5, 81), (1, 77), (1.5, 79), (2, 81), (3, 77)]:
    add(mus, EV["slogan"] + 0.2 + b_ * BEAT, bell(m, 1.6, 0.42), pan=0.25)

# ---------------------------------------------------------------- porta e passos da professora (bem baixinho)
add(sfx, EV["porta"] - 0.15, lowpass(noise(0.05), 3000) * np.exp(-tt(0.05) * 80) * 0.25, pan=-0.5)
for k, t0 in enumerate(EV["passos"]):
    d = 0.09
    step = lowpass(noise(d), 900) * np.exp(-tt(d) * 45) + 0.5 * np.sin(2 * np.pi * 95 * tt(d)) * np.exp(-tt(d) * 60)
    add(sfx, t0, step * rng.uniform(0.09, 0.12), pan=-0.4 if t0 < EV["professora_anda"] else -0.15)

# ---------------------------------------------------------------- reverb e mixagem
def reverb(x, secs=1.8, mix=0.22):
    t = tt(secs)
    out = np.empty_like(x)
    for c in range(2):
        ir = rng.standard_normal(len(t)) * np.exp(-t / 0.42)
        ir = lowpass(ir, 6000)
        ir /= np.sqrt(np.sum(ir ** 2))
        n = 1 << int(np.ceil(np.log2(x.shape[1] + len(ir))))
        wet = np.fft.irfft(np.fft.rfft(x[c], n) * np.fft.rfft(ir, n), n)[: x.shape[1]]
        out[c] = x[c] * (1 - mix) + wet * mix * 1.6
    return out


mus = reverb(mus)
sfx = reverb(sfx, mix=0.15)
mix = mus + sfx
# entrada suave e corte seco em 29,5 s
tm = np.arange(N) / SR
cut = EV["corte"]
mix *= np.minimum(1, tm / 0.25)
mix *= np.clip((cut + 0.04 - tm) / 0.08, 0, 1)
# whoosh do corte (fica depois do corte)
w = whoosh(1.0, 250, 5000, peak_at=0.5, vel=0.75)
wl = len(w)
pan = np.linspace(-0.8, 0.8, wl)
i0 = int((cut - 0.5) * SR)
mix[0, i0:i0 + wl] += w[: N - i0] * np.cos((pan[: N - i0] + 1) * np.pi / 4) * 1.414
mix[1, i0:i0 + wl] += w[: N - i0] * np.sin((pan[: N - i0] + 1) * np.pi / 4) * 1.414

peak = np.max(np.abs(mix))
mix *= 10 ** (-1.5 / 20) / peak
rms = 20 * np.log10(np.sqrt(np.mean(mix ** 2)) + 1e-12)
pcm = (np.clip(mix, -1, 1).T * 32767).astype("<i2")
with wave.open(os.path.join(OUT, "trilha.wav"), "wb") as wf:
    wf.setnchannels(2)
    wf.setsampwidth(2)
    wf.setframerate(SR)
    wf.writeframes(pcm.tobytes())
print(f"ok: {DUR}s, pico -1.5 dBFS, RMS {rms:.1f} dBFS")
