"""Renderiza quadros de checagem da câmera da cena: FRAMES = [...] definido antes do exec."""
import bpy, os

sc = bpy.context.scene
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "saida", "checagem")
os.makedirs(OUT, exist_ok=True)
sc.camera = bpy.data.objects["Cam"]
old = sc.render.resolution_percentage
sc.render.resolution_percentage = PCT if "PCT" in globals() else 40  # noqa: F821
files = []
last = 0
for f in sorted(FRAMES):  # noqa: F821
    if f > 480 and last < 480:   # partículas precisam andar quadro a quadro
        for k in range(470, f):
            sc.frame_set(k)
    sc.frame_set(f)
    last = f
    sc.render.filepath = os.path.join(OUT, f"q_{f:04d}.png")
    bpy.ops.render.render(write_still=True)
    files.append(sc.render.filepath)
sc.render.resolution_percentage = old
result = {"n": len(files)}
