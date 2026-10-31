"""Faz o áudio e o vídeo de teste no Windows, com a voz em português do próprio Windows.

  3-audio-aula.wav   o roteiro-audio.txt falado
  4-video-aula.mp4   os slides de slides/ com a fala de cada um (roteiro-video.json)

Rodar com dois cliques em gerar-audio-e-video.bat (ou: python materiais-teste/montar_audio_video.py).
Precisa de internet só na primeira vez, para baixar o ffmpeg (pacote imageio-ffmpeg, ~30 MB).
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import wave
from pathlib import Path

AQUI = Path(__file__).resolve().parent

VOZ_PS = r"""
Add-Type -AssemblyName System.Speech
$s = New-Object System.Speech.Synthesis.SpeechSynthesizer
$pt = $s.GetInstalledVoices() | Where-Object { $_.Enabled -and $_.VoiceInfo.Culture.Name -like 'pt-*' } | Select-Object -First 1
if (-not $pt) { Write-Output 'SEM_VOZ_PT'; exit 3 }
$s.SelectVoice($pt.VoiceInfo.Name)
$s.Rate = -1
$texto = [IO.File]::ReadAllText($env:PRISMA_TEXTO, [Text.Encoding]::UTF8)
$s.SetOutputToWaveFile($env:PRISMA_SAIDA)
$s.Speak($texto)
$s.Dispose()
Write-Output ('VOZ=' + $pt.VoiceInfo.Name)
"""


def falar(texto: str, saida: Path) -> None:
    """Grava `texto` em `saida` (.wav) com a voz em português do Windows."""
    if os.environ.get("PRISMA_VOZ_FALSA"):            # testes fora do Windows: um tom no lugar da voz
        segundos = max(2.0, len(texto.split()) / 2.6)
        subprocess.run([ffmpeg(), "-y", "-loglevel", "error", "-f", "lavfi", "-i",
                        f"sine=frequency=440:duration={segundos:.1f}", str(saida)], check=True)
        return
    if os.name != "nt":
        sys.exit("Este script usa a voz do Windows. Rode no computador do time (Windows).")
    with tempfile.TemporaryDirectory() as tmp:
        arquivo = Path(tmp) / "texto.txt"
        arquivo.write_text(texto, encoding="utf-8")
        r = subprocess.run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", VOZ_PS],
                           capture_output=True, text=True,
                           env={**os.environ, "PRISMA_TEXTO": str(arquivo), "PRISMA_SAIDA": str(saida)})
    if "SEM_VOZ_PT" in r.stdout:
        sys.exit("O Windows não tem voz em português instalada.\n"
                 "Instale em: Configurações > Hora e idioma > Fala > Adicionar vozes > Português (Brasil).\n"
                 "Depois rode de novo.")
    if r.returncode != 0 or not saida.exists():
        sys.exit("Não consegui gerar a voz:\n" + (r.stderr or r.stdout))
    voz = [l for l in r.stdout.splitlines() if l.startswith("VOZ=")]
    if voz:
        print("   voz:", voz[0][4:])


def ffmpeg() -> str:
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except ImportError:
        pass
    if shutil.which("ffmpeg"):
        return shutil.which("ffmpeg")
    print("   Baixando o ffmpeg (só na primeira vez)...")
    subprocess.run([sys.executable, "-m", "pip", "install", "--disable-pip-version-check", "-q", "imageio-ffmpeg"], check=True)
    import imageio_ffmpeg
    return imageio_ffmpeg.get_ffmpeg_exe()


def duracao(wav: Path) -> float:
    try:
        with wave.open(str(wav)) as w:
            return w.getnframes() / float(w.getframerate())
    except wave.Error:                 # outro formato: pergunta ao ffmpeg
        r = subprocess.run([ffmpeg(), "-i", str(wav)], capture_output=True, text=True)
        import re
        m = re.search(r"Duration: (\d+):(\d+):([\d.]+)", r.stderr)
        return int(m[1]) * 3600 + int(m[2]) * 60 + float(m[3]) if m else 5.0


def main() -> None:
    ff = ffmpeg()
    print("1/2  Áudio da aula...")
    texto = (AQUI / "roteiro-audio.txt").read_text(encoding="utf-8").strip()
    falar(texto, AQUI / "3-audio-aula.wav")
    print(f"   pronto: 3-audio-aula.wav ({duracao(AQUI / '3-audio-aula.wav'):.0f} s)")

    print("2/2  Vídeo da aula...")
    roteiro = json.loads((AQUI / "roteiro-video.json").read_text(encoding="utf-8"))
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        partes = []
        for i, s in enumerate(roteiro, 1):
            fala = tmp / f"fala-{i}.wav"
            falar(s["fala"], fala)
            d = duracao(fala) + 0.8                     # respiro entre um slide e outro
            parte = tmp / f"parte-{i}.mp4"
            subprocess.run([ff, "-y", "-loglevel", "error", "-loop", "1", "-framerate", "25", "-i", str(AQUI / s["imagem"]),
                            "-i", str(fala), "-af", "apad", "-t", f"{d:.2f}",
                            "-c:v", "libx264", "-tune", "stillimage", "-pix_fmt", "yuv420p", "-r", "25",
                            "-c:a", "aac", "-ar", "44100", "-ac", "1", str(parte)], check=True)
            partes.append(parte)
            print(f"   slide {i}: {d:.0f} s")
        lista = tmp / "lista.txt"
        lista.write_text("".join(f"file '{p.as_posix()}'\n" for p in partes), encoding="utf-8")
        subprocess.run([ff, "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", str(lista),
                        "-c", "copy", "-movflags", "+faststart", str(AQUI / "4-video-aula.mp4")], check=True)
    print("   pronto: 4-video-aula.mp4")
    print()
    print("Feito! Os 4 materiais de teste estão na pasta materiais-teste.")


if __name__ == "__main__":
    main()
