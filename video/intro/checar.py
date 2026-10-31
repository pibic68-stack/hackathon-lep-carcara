"""Renders de checagem com câmera livre: VIEWS = [(nome, pos, alvo, lente), ...] definido antes do exec."""
import bpy, os
from mathutils import Vector

sc = bpy.context.scene
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "saida", "checagem")
os.makedirs(OUT, exist_ok=True)
cd = bpy.data.cameras.get("CamChk") or bpy.data.cameras.new("CamChk")
cam = bpy.data.objects.get("CamChk") or bpy.data.objects.new("CamChk", cd)
if cam.name not in sc.collection.objects:
    sc.collection.objects.link(cam)
old = sc.camera
sc.camera = cam
files = []
for name, pos, tgt, lens in VIEWS:  # noqa: F821
    cd.lens, cd.clip_start = lens, 0.05
    cam.location = pos
    cam.rotation_euler = (Vector(tgt) - Vector(pos)).to_track_quat("-Z", "Y").to_euler()
    sc.render.filepath = os.path.join(OUT, name + ".png")
    bpy.ops.render.render(write_still=True)
    files.append(sc.render.filepath)
sc.camera = old
result = {"files": files}
