"""Junta os quadros renderizados com a trilha num MP4.

    python montar.py previa     -> saida/intro_prisma_previa.mp4
    python montar.py final      -> saida/intro_prisma_final_1080p.mp4

Entrada suave do preto (0,8 s) e corte seco para preto em 29,5 s (12 quadros pretos até 30 s).
"""
import os, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "saida")
modo = sys.argv[1] if len(sys.argv) > 1 else "previa"
src = os.path.join(OUT, modo, "f_%04d.png")
dst = os.path.join(OUT, "intro_prisma_previa.mp4" if modo == "previa" else "intro_prisma_final_1080p.mp4")
vf = "fade=t=in:st=0:d=0.8,tpad=stop_mode=add:stop_duration=0.5:color=black,format=yuv420p"
if modo == "previa":
    vf = "scale=1920:1080:flags=lanczos," + vf
cmd = ["ffmpeg", "-y", "-loglevel", "error", "-framerate", "24", "-i", src, "-i", os.path.join(OUT, "trilha.wav"),
       "-vf", vf, "-c:v", "libx264", "-preset", "slow", "-crf", "18", "-c:a", "aac", "-b:a", "192k",
       "-t", "30", "-movflags", "+faststart", dst]
subprocess.run(cmd, check=True)
print(dst)
