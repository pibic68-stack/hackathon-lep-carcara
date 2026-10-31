"""Cena da intro PRISMA: sala de aula voxel, personagens e quadro.

Roda dentro do Blender (MCP execute_blender_code):
    p = r"...\\video\\intro\\cena.py"
    ns = {"__file__": p}; exec(compile(open(p, encoding="utf-8").read(), p, "exec"), ns)

Apaga tudo e reconstrói. Plano em docs/video/plano-intro.md.
Convenção: personagens são montados olhando para +Y no espaço local.
"""
import bpy, bmesh, math, os, random, re
from mathutils import Vector, Matrix, Euler

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "saida")
FONTS = os.path.join(OUT, "fontes")
REPO = os.path.dirname(os.path.dirname(HERE))
IMG = os.path.join(REPO, "web", "assets", "img")
random.seed(7)


def lin(h, a=1.0):
    h = h.lstrip("#")
    c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    f = lambda x: x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4
    return (f(c[0]), f(c[1]), f(c[2]), a)


# ---------------------------------------------------------------- limpar
for o in list(bpy.data.objects):
    bpy.data.objects.remove(o, do_unlink=True)
for dc in (bpy.data.meshes, bpy.data.materials, bpy.data.curves, bpy.data.cameras,
           bpy.data.lights, bpy.data.images, bpy.data.actions, bpy.data.particles):
    for d in list(dc):
        dc.remove(d)
for c in list(bpy.data.collections):
    bpy.data.collections.remove(c)

sc = bpy.context.scene
sc.frame_start, sc.frame_end = 1, 720
sc.render.fps = 24


def coll(name):
    c = bpy.data.collections.new(name)
    sc.collection.children.link(c)
    return c


C_SALA, C_PERS, C_QUADRO, C_PAL, C_LUZ = (coll(n) for n in ("Sala", "Personagens", "Quadro", "Palavras", "Luzes"))


# ---------------------------------------------------------------- materiais
def new_mat(name):
    m = bpy.data.materials.new(name)
    if m.node_tree is None:
        m.use_nodes = True
    nt = m.node_tree
    bsdf = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
    return m, nt, bsdf


def mat_voxel():
    m, nt, b = new_mat("Voxel")
    at = nt.nodes.new("ShaderNodeAttribute")
    at.attribute_name, at.attribute_type = "Col", "GEOMETRY"
    nt.links.new(at.outputs["Color"], b.inputs["Base Color"])
    b.inputs["Roughness"].default_value = 0.62
    return m


def mat_fade(name, hexcol=None, emit=0.0, rough=0.5, use_attr=False):
    """Material com transparência pela cor do objeto (alpha) e brilho pelo canal R da cor do objeto
    quando emit < 0 (brilho animável)."""
    m, nt, b = new_mat(name)
    oi = nt.nodes.new("ShaderNodeObjectInfo")
    if use_attr:
        at = nt.nodes.new("ShaderNodeAttribute")
        at.attribute_name, at.attribute_type = "Col", "GEOMETRY"
        nt.links.new(at.outputs["Color"], b.inputs["Base Color"])
        nt.links.new(at.outputs["Color"], b.inputs["Emission Color"])
    else:
        b.inputs["Base Color"].default_value = lin(hexcol)
        b.inputs["Emission Color"].default_value = lin(hexcol)
    if emit < 0:  # força do brilho = R da cor do objeto
        sep = nt.nodes.new("ShaderNodeSeparateColor")
        nt.links.new(oi.outputs["Color"], sep.inputs["Color"])
        nt.links.new(sep.outputs[0], b.inputs["Emission Strength"])
    else:
        b.inputs["Emission Strength"].default_value = emit
    nt.links.new(oi.outputs["Alpha"], b.inputs["Alpha"])
    b.inputs["Roughness"].default_value = rough
    return m


VOX = mat_voxel()
M_PIXEL = mat_fade("Pixel", emit=-1, use_attr=True, rough=0.4)
M_TITULO = mat_fade("Titulo", "FBF7EE", emit=0.35)
M_PLACA = mat_fade("Placa", "1E2235", emit=0.0)
M_FEIXE = mat_fade("Feixe", "FFFFFF", emit=-1)


def mat_lousa():
    m, nt, b = new_mat("Lousa")
    tc = nt.nodes.new("ShaderNodeTexCoord")
    nz = nt.nodes.new("ShaderNodeTexNoise")
    nz.inputs["Scale"].default_value = 2.5
    nz.inputs["Detail"].default_value = 6
    nt.links.new(tc.outputs["Object"], nz.inputs["Vector"])
    cr = nt.nodes.new("ShaderNodeValToRGB")
    cr.color_ramp.elements[0].position, cr.color_ramp.elements[1].position = 0.35, 0.75
    cr.color_ramp.elements[0].color = lin("24392F")
    cr.color_ramp.elements[1].color = lin("31503F")
    nt.links.new(nz.outputs["Fac"], cr.inputs["Fac"])
    nt.links.new(cr.outputs["Color"], b.inputs["Base Color"])
    b.inputs["Roughness"].default_value = 0.92
    return m


def mat_giz():
    """Giz: grão de ruído + dissolução quando o alpha do objeto cai (ruído < alpha fica visível)."""
    m, nt, b = new_mat("Giz")
    tc = nt.nodes.new("ShaderNodeTexCoord")
    oi = nt.nodes.new("ShaderNodeObjectInfo")
    g = nt.nodes.new("ShaderNodeTexNoise")
    g.inputs["Scale"].default_value = 90
    nt.links.new(tc.outputs["Object"], g.inputs["Vector"])
    cr = nt.nodes.new("ShaderNodeValToRGB")
    cr.color_ramp.elements[0].position, cr.color_ramp.elements[1].position = 0.3, 0.7
    cr.color_ramp.elements[0].color = lin("C9CFC6")
    cr.color_ramp.elements[1].color = lin("F6F4EC")
    nt.links.new(g.outputs["Fac"], cr.inputs["Fac"])
    nt.links.new(cr.outputs["Color"], b.inputs["Base Color"])
    d = nt.nodes.new("ShaderNodeTexNoise")
    d.inputs["Scale"].default_value = 7
    d.inputs["Detail"].default_value = 4
    nt.links.new(tc.outputs["Object"], d.inputs["Vector"])
    # visível onde ruído*0.9+0.05 < alpha
    mul = nt.nodes.new("ShaderNodeMath"); mul.operation = "MULTIPLY_ADD"
    mul.inputs[1].default_value, mul.inputs[2].default_value = 0.9, 0.05
    nt.links.new(d.outputs["Fac"], mul.inputs[0])
    lt = nt.nodes.new("ShaderNodeMath"); lt.operation = "LESS_THAN"
    nt.links.new(mul.outputs[0], lt.inputs[0])
    nt.links.new(oi.outputs["Alpha"], lt.inputs[1])
    gr = nt.nodes.new("ShaderNodeMath"); gr.operation = "MULTIPLY"
    nt.links.new(lt.outputs[0], gr.inputs[0])
    nt.links.new(g.outputs["Fac"], gr.inputs[1])
    gr2 = nt.nodes.new("ShaderNodeMath"); gr2.operation = "MULTIPLY_ADD"  # grão no alpha: 0.6..1
    gr2.inputs[1].default_value, gr2.inputs[2].default_value = 0.5, 0.0
    nt.links.new(gr.outputs[0], gr2.inputs[0])
    add = nt.nodes.new("ShaderNodeMath"); add.operation = "MULTIPLY_ADD"
    add.inputs[1].default_value = 0.65
    nt.links.new(lt.outputs[0], add.inputs[0])
    nt.links.new(gr2.outputs[0], add.inputs[2])
    nt.links.new(add.outputs[0], b.inputs["Alpha"])
    b.inputs["Roughness"].default_value = 0.95
    b.inputs["Emission Color"].default_value = lin("F6F4EC")
    b.inputs["Emission Strength"].default_value = 0.08
    return m


M_LOUSA, M_GIZ = mat_lousa(), mat_giz()


def mat_img(name, path):
    m, nt, b = new_mat(name)
    tx = nt.nodes.new("ShaderNodeTexImage")
    tx.image = bpy.data.images.load(path, check_existing=True)
    tx.interpolation = "Closest"
    nt.links.new(tx.outputs["Color"], b.inputs["Base Color"])
    b.inputs["Roughness"].default_value = 0.8
    return m


def mat_ceu():
    m, nt, b = new_mat("Ceu")
    out = next(n for n in nt.nodes if n.type == "OUTPUT_MATERIAL")
    em = nt.nodes.new("ShaderNodeEmission")
    tc = nt.nodes.new("ShaderNodeTexCoord")
    sp = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(tc.outputs["Generated"], sp.inputs["Vector"])
    cr = nt.nodes.new("ShaderNodeValToRGB")
    cr.color_ramp.elements[0].color = lin("CFE8FA")
    cr.color_ramp.elements[1].color = lin("7DB8E8")
    nt.links.new(sp.outputs["Z"], cr.inputs["Fac"])
    nt.links.new(cr.outputs["Color"], em.inputs["Color"])
    em.inputs["Strength"].default_value = 1.6
    nt.links.new(em.outputs[0], out.inputs["Surface"])
    return m


# ---------------------------------------------------------------- construtor de malha
class MB:
    def __init__(s):
        s.bm = bmesh.new()
        s.cl = s.bm.loops.layers.float_color.new("Col")

    def _paint(s, verts, col, jit):
        k = 1 + random.uniform(-jit, jit) if jit else 1
        cc = tuple(min(1.0, x * k) for x in col[:3]) + (1.0,)
        for f in {f for v in verts for f in v.link_faces}:
            for l in f.loops:
                l[s.cl] = cc

    def box(s, c, sz, col, rot=(0, 0, 0), jit=0.0):
        M = Matrix.Translation(Vector(c)) @ Euler(rot).to_matrix().to_4x4() @ Matrix.Diagonal((sz[0], sz[1], sz[2], 1))
        s._paint(bmesh.ops.create_cube(s.bm, size=1.0, matrix=M)["verts"], col, jit)

    def cyl(s, c, r, depth, col, axis="X", seg=14):
        R = {"X": Euler((0, math.pi / 2, 0)), "Y": Euler((math.pi / 2, 0, 0)), "Z": Euler((0, 0, 0))}[axis]
        M = Matrix.Translation(Vector(c)) @ R.to_matrix().to_4x4()
        v = bmesh.ops.create_cone(s.bm, cap_ends=True, cap_tris=False, segments=seg,
                                  radius1=r, radius2=r, depth=depth, matrix=M)["verts"]
        s._paint(v, col, 0)

    def obj(s, name, collection, origin=(0, 0, 0), parent=None, parent_origin=(0, 0, 0), mat=None):
        o = Vector(origin)
        bmesh.ops.translate(s.bm, verts=s.bm.verts, vec=-o)
        me = bpy.data.meshes.new(name)
        s.bm.to_mesh(me)
        s.bm.free()
        me.materials.append(mat or VOX)
        ob = bpy.data.objects.new(name, me)
        collection.objects.link(ob)
        if parent:
            ob.parent = parent
        ob.location = o - Vector(parent_origin)
        return ob


def empty(name, collection, loc=(0, 0, 0), rotz=0.0, parent=None):
    e = bpy.data.objects.new(name, None)
    e.empty_display_size = 0.3
    collection.objects.link(e)
    e.parent = parent
    e.location = loc
    e.rotation_euler.z = rotz
    return e


# ---------------------------------------------------------------- paleta
P = {k: lin(v) for k, v in dict(
    tinta="1E2235", papel="FBF7EE", ceu="1F6FB2", branco="FFFFFF", piso1="EADFC8", piso2="D7C8AA",
    parede="F4EBDA", rodape="A9CBE6", faixa="E8A15A", teto="F7F3EA", madeira="D3A267", madeira2="8E5B32",
    metal="5D6B7A", prata="B8C0CC", boca="8A3B3B", bochecha="F2938C", verde_folha="5BAF5B",
    verde2="3E8E4A", vaso="C0643A", grama="7CC36A", tronco="7A5230",
    r1="E5533D", r2="FFAD60", r3="FFC93C", r4="7BD389", r5="57B3F9", r6="B89AF0").items()}
ARCO = [P[k] for k in ("r1", "r2", "r3", "r4", "r5", "r6")]

# ---------------------------------------------------------------- sala
W, D, H = 4.5, 4.0, 3.5          # meia-largura (x), meia-profundidade (y), altura
DOOR_Y = (-1.5, -0.5)            # abertura da porta na parede esquerda
DOOR_H = 2.5
WIN_Y = [(-3.0, -1.5), (-0.5, 1.0), (2.0, 3.5)]
WIN_Z = (1.0, 2.5)

b = MB()
for i in range(int(2 * W / 0.5)):
    for j in range(int(2 * D / 0.5)):
        x, y = -W + 0.25 + i * 0.5, -D + 0.25 + j * 0.5
        b.box((x, y, -0.05), (0.5, 0.5, 0.1), P["piso1"] if (i + j) % 2 else P["piso2"], jit=0.03)
# corredor atrás da porta
for i in range(5):
    for j in range(6):
        b.box((-W - 0.35 - i * 0.5, -2.75 + j * 0.5, -0.05), (0.5, 0.5, 0.1), lin("C9C2B4"), jit=0.03)


def wall_col(z):
    if z < 1.0:
        return P["rodape"]
    if z < 1.15:
        return P["faixa"]
    return P["parede"]


ZROWS = [(0.0, 0.5), (0.5, 1.0), (1.0, 1.15), (1.15, 1.6), (1.6, 2.05), (2.05, 2.5), (2.5, 3.0), (3.0, 3.5)]


def wall_blocks(axis, fixed, t0, t1, holes=()):
    """Parede em blocos de 0,5 m. axis='x' -> parede corre ao longo de y em x=fixed."""
    n = int(round((t1 - t0) / 0.5))
    for k in range(n):
        a = t0 + k * 0.5 + 0.25
        for z0, z1 in ZROWS:
            zc = (z0 + z1) / 2
            if any(h0 <= a <= h1 and hz0 <= zc <= hz1 for (h0, h1, hz0, hz1) in holes):
                continue
            if axis == "x":
                b.box((fixed, a, zc), (0.2, 0.5, z1 - z0), wall_col(zc), jit=0.025)
            else:
                b.box((a, fixed, zc), (0.5, 0.2, z1 - z0), wall_col(zc), jit=0.025)


wall_blocks("x", -W - 0.1, -D, D, holes=[(DOOR_Y[0], DOOR_Y[1], 0, DOOR_H)])
wall_blocks("x", W + 0.1, -D, D, holes=[(y0, y1, WIN_Z[0], WIN_Z[1]) for y0, y1 in WIN_Y])
wall_blocks("y", D + 0.1, -W - 0.2, W + 0.2)
wall_blocks("y", -D - 0.1, -W - 0.2, W + 0.2)
# teto
for i in range(9):
    for j in range(8):
        b.box((-W + 0.5 + i, -D + 0.5 + j, H + 0.05), (1.0, 1.0, 0.1), P["teto"], jit=0.015)
# luminárias (placas claras; a luz vem das area lights)
for x in (-2.0, 2.0):
    for y in (-2.4, 0.0, 2.4):
        b.box((x, y, H - 0.03), (1.3, 0.35, 0.05), lin("FFFDF4"))
# batentes da porta
b.box((-W - 0.1, DOOR_Y[0] - 0.06, DOOR_H / 2), (0.26, 0.12, DOOR_H), P["madeira2"])
b.box((-W - 0.1, DOOR_Y[1] + 0.06, DOOR_H / 2), (0.26, 0.12, DOOR_H), P["madeira2"])
b.box((-W - 0.1, (DOOR_Y[0] + DOOR_Y[1]) / 2, DOOR_H + 0.06), (0.26, 1.24, 0.12), P["madeira2"])
# rampinha na soleira
b.box((-W - 0.1, -1.0, 0.015), (0.5, 0.95, 0.03), lin("9AA3AF"))
# janelas: molduras e peitoris
for y0, y1 in WIN_Y:
    yc = (y0 + y1) / 2
    b.box((W + 0.02, yc, WIN_Z[0] - 0.04), (0.3, y1 - y0 + 0.1, 0.08), P["branco"])
    b.box((W + 0.02, yc, WIN_Z[1] + 0.04), (0.3, y1 - y0 + 0.1, 0.08), P["branco"])
    b.box((W + 0.02, y0, sum(WIN_Z) / 2), (0.3, 0.06, WIN_Z[1] - WIN_Z[0]), P["branco"])
    b.box((W + 0.02, y1, sum(WIN_Z) / 2), (0.3, 0.06, WIN_Z[1] - WIN_Z[0]), P["branco"])
    b.box((W + 0.1, yc, sum(WIN_Z) / 2), (0.05, 0.05, WIN_Z[1] - WIN_Z[0]), P["branco"])
    b.box((W + 0.1, yc, sum(WIN_Z) / 2), (0.05, y1 - y0, 0.05), P["branco"])
sala = b.obj("Sala_Estrutura", C_SALA)

# corredor: parede do fundo e lateral
b = MB()
for j in range(7):
    for z0, z1 in ZROWS:
        b.box((-W - 2.7, -2.75 + j * 0.5, (z0 + z1) / 2), (0.2, 0.5, z1 - z0), wall_col((z0 + z1) / 2), jit=0.03)
b.obj("Corredor", C_SALA)

# porta (pivô na dobradiça, abre para dentro)
b = MB()
b.box((0, 0.5, DOOR_H / 2 - 0.02), (0.05, 0.98, DOOR_H - 0.06), lin("4F86C6"))
b.box((0.04, 0.85, 1.05), (0.05, 0.1, 0.05), P["prata"])     # maçaneta
b.box((0.03, 0.5, 1.75), (0.02, 0.5, 0.5), lin("CFE8FA"))     # visor
b.obj("Porta", C_SALA, origin=(0, 0, 0)).location = (-W - 0.05, DOOR_Y[0] + 0.01, 0)

# ---------------------------------------------------------------- lá fora
b = MB()
b.box((W + 20, 0, -0.15), (40, 60, 0.1), P["grama"])
for k in range(14):
    x, y = random.uniform(W + 3, W + 12), random.uniform(-9, 9)
    hgt = random.uniform(1.6, 3.0)
    b.box((x, y, hgt / 2), (0.35, 0.35, hgt), P["tronco"])
    for _ in range(6):
        s = random.uniform(0.9, 1.6)
        b.box((x + random.uniform(-0.6, 0.6), y + random.uniform(-0.6, 0.6), hgt + random.uniform(0, 1.2)),
              (s, s, s), random.choice([P["verde_folha"], P["verde2"], lin("8BCB6B")]), jit=0.08)
b.obj("Fora_Arvores", C_SALA)
bpy.ops.mesh.primitive_plane_add(size=1)
ceu = bpy.context.active_object
ceu.name = "Ceu"
ceu.scale = (1, 70, 40)
ceu.location = (W + 16, 0, 8)
ceu.rotation_euler = (0, math.pi / 2, 0)
for c in ceu.users_collection:
    c.objects.unlink(ceu)
C_SALA.objects.link(ceu)
ceu.data.materials.append(mat_ceu())

# ---------------------------------------------------------------- mobília
ROWS_Y = [1.5, -0.3, -2.1]
COLS_X = [-2.7, -0.9, 0.9, 2.7]
GIRL_DESK = (COLS_X[0], ROWS_Y[0])
CHAIR_COLS = [P["r1"], P["r5"], P["r3"], P["r4"], lin("F28FB0"), P["r2"]]

b = MB()


def desk(x, y, w=0.8, h=0.75, rack=True):
    b.box((x, y, h - 0.02), (w, 0.55, 0.04), P["madeira"], jit=0.02)
    for sx in (-1, 1):
        for sy in (-1, 1):
            b.box((x + sx * (w / 2 - 0.04), y + sy * 0.23, (h - 0.04) / 2), (0.04, 0.04, h - 0.04), P["metal"])
    if rack:
        b.box((x, y + 0.03, h - 0.14), (w - 0.08, 0.42, 0.02), P["metal"])
    # caderno e lápis
    b.box((x + random.uniform(-0.15, 0.1), y - 0.05, h + 0.008), (0.26, 0.2, 0.012), random.choice(ARCO), rot=(0, 0, random.uniform(-0.2, 0.2)))
    b.box((x + 0.25, y - 0.02, h + 0.012), (0.02, 0.16, 0.02), P["r3"], rot=(0, 0, 0.4))


def chair(x, y, col):
    b.box((x, y, 0.42), (0.42, 0.4, 0.04), col, jit=0.03)
    b.box((x, y - 0.2, 0.7), (0.42, 0.04, 0.3), col, jit=0.03)
    for sx in (-1, 1):
        for sy in (-1, 1):
            b.box((x + sx * 0.18, y + sy * 0.17, 0.2), (0.035, 0.035, 0.4), P["metal"])
        b.box((x + sx * 0.18, y - 0.2, 0.5), (0.035, 0.035, 0.2), P["metal"])


SEATS = []
k = 0
for r, y in enumerate(ROWS_Y):
    for c, x in enumerate(COLS_X):
        if (x, y) == GIRL_DESK:
            desk(x, y, w=1.0, h=0.78, rack=False)     # mesa adaptada, sem cadeira
            continue
        desk(x, y)
        chair(x, y - 0.55, CHAIR_COLS[k % len(CHAIR_COLS)])
        SEATS.append((x, y - 0.55))
        k += 1

# mesa da professora
TX, TY = 3.0, 2.85
b.box((TX, TY, 0.76), (1.4, 0.7, 0.05), P["madeira2"], jit=0.02)
b.box((TX, TY + 0.3, 0.38), (1.36, 0.05, 0.72), P["madeira"])
for sx in (-1, 1):
    b.box((TX + sx * 0.66, TY, 0.38), (0.06, 0.66, 0.72), P["madeira"])
for i, c in enumerate([P["r5"], P["r1"], P["r4"]]):
    b.box((TX - 0.45, TY - 0.05, 0.81 + i * 0.05), (0.3, 0.22, 0.05), c, rot=(0, 0, 0.1 * i))
b.box((TX + 0.5, TY - 0.1, 0.83), (0.09, 0.09, 0.09), P["r1"])          # maçã
b.box((TX + 0.5, TY - 0.1, 0.89), (0.015, 0.015, 0.04), P["tronco"])
# estante na parede esquerda, perto do fundo
SX, SY = -W + 0.2, -3.0
b.box((SX, SY, 0.9), (0.4, 1.6, 1.8), P["madeira2"])
for z in (0.25, 0.75, 1.25):
    yy = SY - 0.7
    while yy < SY + 0.65:
        w = random.uniform(0.05, 0.1)
        hb = random.uniform(0.28, 0.4)
        b.box((SX + 0.12, yy + w / 2, z + hb / 2 + 0.02), (0.26, w, hb), random.choice(ARCO + [P["ceu"], P["papel"]]))
        yy += w + 0.008
# vasos de planta
for (px, py) in [(4.05, 3.55), (4.05, -3.6), (-4.05, 3.55)]:
    b.box((px, py, 0.22), (0.4, 0.4, 0.44), P["vaso"])
    for _ in range(9):
        s = random.uniform(0.18, 0.32)
        b.box((px + random.uniform(-0.2, 0.2), py + random.uniform(-0.2, 0.2), 0.5 + random.uniform(0, 0.7)),
              (s, s, s), random.choice([P["verde_folha"], P["verde2"]]), jit=0.1)
# bandeirinhas acima do quadro
b.box((0, D - 0.04, 3.2), (5.6, 0.02, 0.02), P["tinta"])
for i in range(15):
    x = -2.6 + i * (5.2 / 14)
    c = ARCO[i % 6]
    b.box((x, D - 0.05, 3.12), (0.22, 0.02, 0.08), c)
    b.box((x, D - 0.05, 3.04), (0.14, 0.02, 0.08), c)
    b.box((x, D - 0.05, 2.97), (0.06, 0.02, 0.06), c)
b.obj("Mobilia", C_SALA)

# cartazes com os mascotes (coruja = professor, preguiça = aluno, urso = família)
def poster(name, img, loc, rot, size=0.75):
    fb = MB()
    fb.box((0, 0, 0), (size + 0.08, 0.03, size + 0.08), P["madeira2"])
    fr = fb.obj(name + "_Moldura", C_SALA)
    fr.location, fr.rotation_euler = loc, rot
    bpy.ops.mesh.primitive_plane_add(size=size)
    pl = bpy.context.active_object
    pl.name = name
    for c in pl.users_collection:
        c.objects.unlink(pl)
    C_SALA.objects.link(pl)
    pl.parent = fr
    pl.location = (0, -0.017, 0)
    pl.rotation_euler = (math.pi / 2, 0, 0)
    pl.data.materials.append(mat_img("Img_" + name, os.path.join(IMG, img)))
    return fr


poster("Cartaz_Coruja", "professor.png", (-3.5, D - 0.02, 2.35), (0, 0, 0))
poster("Cartaz_Preguica", "aluno.png", (3.5, D - 0.02, 2.2), (0, 0, 0))
poster("Cartaz_Urso", "familia.png", (-W + 0.02, 1.7, 2.0), (0, 0, math.pi / 2))

# carcará voxel (pelúcia) na mesa da professora, a partir do pixel art do site
try:
    im = bpy.data.images.load(os.path.join(IMG, "carcara.png"), check_existing=True)
    w, h = im.size
    px = list(im.pixels)
    vs = 0.0055 * 2
    b = MB()
    for yy in range(0, h, 2):
        for xx in range(0, w, 2):
            i = (yy * w + xx) * 4
            r, g, bb, a = px[i:i + 4]
            if a > 0.5:
                tl = lambda v: v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4
                b.box(((xx - w / 2) * vs / 2, 0, yy * vs / 2), (vs, vs * 3, vs), (tl(r), tl(g), tl(bb), 1))
    cc = b.obj("Carcara", C_SALA)
    cc.location = (TX + 0.05, TY + 0.05, 0.785)
    cc.rotation_euler.z = math.radians(-20)
except Exception as e:
    print("carcara:", e)

# ---------------------------------------------------------------- quadro
BX, BY, BZ, BW, BH = 0.0, D - 0.05, 1.75, 4.8, 2.2
BFRONT = BY - 0.03
b = MB()
b.box((0, 0, 0), (BW, 0.06, BH), P["tinta"])
lousa = b.obj("Lousa", C_QUADRO, mat=M_LOUSA)
lousa.location = (BX, BY, BZ)
b = MB()
for sz, c in [((BW + 0.2, 0.1, 0.1), (0, -0.02, BH / 2 + 0.05)), ((BW + 0.2, 0.1, 0.1), (0, -0.02, -BH / 2 - 0.05)),
              ((0.1, 0.1, BH), (BW / 2 + 0.05, -0.02, 0)), ((0.1, 0.1, BH), (-BW / 2 - 0.05, -0.02, 0))]:
    b.box(c, sz, P["madeira2"], jit=0.03)
b.box((0, -0.1, -BH / 2 - 0.08), (BW, 0.14, 0.04), P["madeira2"])                      # canaleta
for i, c in enumerate([P["papel"], P["r3"], P["r5"], P["papel"]]):
    b.box((-1.6 + i * 0.12, -0.1, -BH / 2 - 0.045), (0.08, 0.025, 0.025), c, rot=(0, 0, 0.2 * i))
b.box((1.4, -0.1, -BH / 2 - 0.04), (0.22, 0.08, 0.05), lin("3D4A6B"))                   # apagador
b.box((1.4, -0.1, -BH / 2 - 0.01), (0.22, 0.08, 0.015), lin("D9D2C3"))
b.box((-0.6, -0.1, -BH / 2 - 0.05), (0.7, 0.02, 0.02), P["tronco"], rot=(0, 0, 0.05))    # ponteira
mold = b.obj("Lousa_Moldura", C_QUADRO)
mold.location = (BX, BY, BZ)


def font(n):
    return bpy.data.fonts.load(os.path.join(FONTS, n + ".ttf"), check_existing=True)


F_PIX, F_ATK = font("pixelify-700"), font("atkinson-700")


def text(name, body, fnt, size, loc, mat, collection, extrude=0.0, rot=(math.pi / 2, 0, 0)):
    cu = bpy.data.curves.new(name, "FONT")
    cu.body = body
    cu.font = fnt
    cu.size = size
    cu.align_x, cu.align_y = "CENTER", "CENTER"
    cu.extrude = extrude
    o = bpy.data.objects.new(name, cu)
    collection.objects.link(o)
    o.location, o.rotation_euler = loc, rot
    cu.materials.append(mat)
    return o


giz = text("Giz_PRISMA", "PRISMA", F_PIX, 0.78, (0, BFRONT - 0.002, BZ + 0.02), M_GIZ, C_QUADRO)
titulo = text("Titulo_PRISMA", "PRISMA", F_PIX, 0.46, (0, BFRONT - 0.004, 1.30), M_TITULO, C_QUADRO, extrude=0.004)
slogan = text("Slogan", "uma aula entra, várias versões saem.", F_ATK, 0.155, (0, BFRONT - 0.004, 0.94),
              M_TITULO, C_QUADRO, extrude=0.003)

# logo em pixels (de web/assets/img/prisma-logo.svg)
svg = open(os.path.join(IMG, "prisma-logo.svg"), encoding="utf-8").read()
rects = [(int(x), int(y), c.upper()) for x, y, c in
         re.findall(r'<rect x="(\d+)" y="(\d+)" width="1" height="1" fill="#([0-9A-Fa-f]{6})"', svg)]
PX = 0.056
LOGO_C = (0.0, 2.2)  # centro (x, z) no quadro
GROUP = {"1E2235": "corpo", "CDEBFE": "corpo", "FFFFFF": "corpo", "8A8FA8": "feixe",
         "E5533D": "c1", "FFAD60": "c2", "FFC93C": "c3", "7BD389": "c4", "57B3F9": "c5", "B89AF0": "c6"}
logo_root = empty("Logo", C_QUADRO, (LOGO_C[0], BFRONT - 0.016, LOGO_C[1]))
pix_info = []
for x, y, c in rects:
    b = MB()
    b.box((0, 0, 0), (PX * 0.94, 0.03, PX * 0.94), lin(c))
    o = b.obj(f"Px_{GROUP[c]}_{x:02d}_{y:02d}", C_QUADRO, mat=M_PIXEL)
    o.parent = logo_root
    o.location = ((x - 14.5) * PX, 0, (8.5 - y) * PX)
    o.color = (0.0, 0, 0, 1)
    pix_info.append((o.name, GROUP[c], x, y))

# feixe de luz (barra branca que viaja da borda do quadro até o prisma)
b = MB()
b.box((0.5, 0, 0), (1.0, 0.035, PX * 2.2), P["branco"])
feixe = b.obj("Feixe_Luz", C_QUADRO, mat=M_FEIXE)
feixe.location = (-BW / 2 + 0.05, BFRONT - 0.03, LOGO_C[1] + (8.5 - 10.5) * PX)
feixe.color = (6.0, 0, 0, 0)

# ---------------------------------------------------------------- palavras flutuantes
PALAVRAS = ["inclusão", "acessibilidade", "aprender", "ver", "ouvir", "ler", "autonomia", "para todos"]
for i, wd in enumerate(PALAVRAS):
    col = ["E5533D", "FFAD60", "FFC93C", "7BD389", "57B3F9", "B89AF0", "FFAD60", "7BD389"][i]
    m = mat_fade(f"Palavra_{i}", col, emit=0.9)
    t = text(f"Palavra_{i}", wd, F_PIX, 0.24, (0, 0, -10), m, C_PAL, extrude=0.012, rot=(0, 0, 0))
    # sem placa: só uma sombra fina deslocada, para a palavra continuar legível em parede clara
    sh = text(f"Sombra_{i}", wd, F_PIX, 0.24, (0, 0, 0), M_PLACA, C_PAL, extrude=0.012, rot=(0, 0, 0))
    sh.parent = t
    sh.location = (0.016, -0.016, -0.014)
    t.color = (1, 1, 1, 0)
    sh.color = (1, 1, 1, 0)

# ---------------------------------------------------------------- personagens
SKIN = [lin(h) for h in ("F2C9A5", "E0AC80", "C68B59", "8D5524", "6B3F1F", "F5D3B8", "D9A06E")]
HAIR = [lin(h) for h in ("1E1B1A", "4A2C1A", "7B4B2A", "E3C16F", "2B1D16", "B5461E")]


def head_build(h, NZ, HS, spec):
    """Cabeça com cabelo, boca, bochechas e óculos (olhos ficam em objeto separado)."""
    skin, hair = spec["skin"], spec["hair"]
    top = NZ + HS
    fy = HS / 2
    h.box((0, 0, NZ + HS / 2), (HS, HS, HS), skin)
    mo = P["boca"]
    h.box((0, fy + 0.006, NZ + 0.085), (0.08, 0.012, 0.025), mo)
    for sx in (-1, 1):
        h.box((sx * 0.05, fy + 0.006, NZ + 0.1), (0.025, 0.012, 0.03), mo)
        h.box((sx * 0.115, fy + 0.004, NZ + 0.115), (0.05, 0.01, 0.03), P["bochecha"])
    st = spec.get("style", "short")
    big = st in ("curly", "afro")
    pad = 0.1 if big else 0.04
    h.box((0, -0.01, top + (0.06 if big else 0.035)), (HS + pad, HS + pad, 0.14 if big else 0.07), hair, jit=0.04)
    if st != "buzz":
        h.box((0, fy + 0.01, top - 0.04), (HS + 0.04, 0.04, 0.08), hair)          # franja
    back = {"short": 0.24, "buzz": 0.12, "long": 0.55, "bun": 0.3, "braids": 0.3, "curly": 0.3,
            "afro": 0.32, "wavy": 0.44, "pony": 0.25}[st]
    side = {"short": 0.15, "buzz": 0.06, "long": 0.36, "bun": 0.2, "braids": 0.2, "curly": 0.26,
            "afro": 0.3, "wavy": 0.34, "pony": 0.16}[st]
    bt = 0.08 if big else 0.04
    h.box((0, -fy - bt / 2, top - back / 2), (HS + pad, bt, back), hair, jit=0.04)
    for sx in (-1, 1):
        h.box((sx * (HS / 2 + bt / 2), -0.03, top - side / 2), (bt, HS - 0.04, side), hair, jit=0.04)
    if st == "bun":
        h.box((0, -0.07, top + 0.13), (0.18, 0.18, 0.16), hair, jit=0.05)
    if st == "pony":
        h.box((0, -fy - 0.08, top - 0.12), (0.1, 0.1, 0.24), hair)
    if st == "braids":
        for sx in (-1, 1):
            for j in range(4):
                h.box((sx * 0.15, -0.1, top - 0.25 - j * 0.09), (0.07, 0.07, 0.08), hair)
    if st in ("curly", "afro"):
        for _ in range(10):
            a = random.uniform(0, 2 * math.pi)
            h.box((math.cos(a) * 0.2, math.sin(a) * 0.2 - 0.02, top + random.uniform(-0.02, 0.1)),
                  (0.1, 0.1, 0.1), hair, jit=0.08)
    if st == "wavy":
        for sx in (-1, 1):
            for j in range(3):
                h.box((sx * (HS / 2 + 0.05), -0.02 - j * 0.04, top - 0.12 - j * 0.11), (0.06, 0.16, 0.1), hair, jit=0.06)
        for j in range(3):
            h.box((0, -fy - 0.05, top - 0.2 - j * 0.12), (HS + 0.06, 0.05, 0.1), hair, jit=0.05)
    ez = NZ + 0.19 * HS / 0.36
    if spec.get("glasses"):
        g = P["tinta"]
        for sx in (-1, 1):
            cx = sx * 0.078
            h.box((cx, fy + 0.02, ez + 0.055), (0.11, 0.012, 0.016), g)
            h.box((cx, fy + 0.02, ez - 0.055), (0.11, 0.012, 0.016), g)
            h.box((cx - 0.055, fy + 0.02, ez), (0.016, 0.012, 0.11), g)
            h.box((cx + 0.055, fy + 0.02, ez), (0.016, 0.012, 0.11), g)
            h.box((sx * (HS / 2 + 0.01), 0.05, ez + 0.05), (0.012, 0.26, 0.014), g)
        h.box((0, fy + 0.02, ez + 0.02), (0.05, 0.012, 0.014), g)
    if spec.get("aid"):
        h.box((HS / 2 + bt + 0.012, -0.02, ez - 0.03), (0.03, 0.07, 0.09), lin("2BB3A3"))
    return ez


def eyes_build(name, NZ, HS, ez, head, head_origin):
    e = MB()
    fy = HS / 2
    for sx in (-1, 1):
        e.box((sx * 0.078, fy + 0.008, ez), (0.05, 0.016, 0.075), P["tinta"])
        e.box((sx * 0.078 + 0.012, fy + 0.017, ez + 0.018), (0.016, 0.004, 0.016), P["branco"])
    return e.obj(name + "_Olhos", C_PERS, origin=(0, fy, ez), parent=head, parent_origin=head_origin)


def seated(name, spec, root, S=0.44, shin=None):
    """Criança sentada: corpo, braços, cabeça, olhos. Origem no chão sob o assento."""
    skin, shirt, pants = spec["skin"], spec["shirt"], spec["pants"]
    shoes = spec.get("shoes", P["tinta"])
    b = MB()
    b.box((0, 0.12, S + 0.07), (0.32, 0.44, 0.14), pants)
    sh = shin or S
    for sx in (-0.085, 0.085):
        b.box((sx, 0.3, S + 0.07 - (sh + 0.07) / 2), (0.13, 0.13, sh + 0.07), pants)
        b.box((sx, 0.34, S - sh + 0.035), (0.14, 0.21, 0.07), shoes)
    T0, TH = S + 0.13, 0.42
    b.box((0, -0.02, T0 + TH / 2), (0.36, 0.22, TH), shirt)
    if spec.get("inner"):
        b.box((0, 0.095, T0 + TH / 2 + 0.02), (0.12, 0.012, TH - 0.06), spec["inner"])
    b.box((0, -0.02, T0 + TH + 0.02), (0.13, 0.12, 0.05), skin)
    b.obj(name + "_Corpo", C_PERS, parent=root)
    SH = T0 + TH - 0.05
    arms = {}
    for side, sx in (("E", -1), ("D", 1)):
        a = MB()
        x = sx * 0.235
        a.box((x, -0.02, SH - 0.17), (0.11, 0.12, 0.36), spec.get("sleeve", shirt))
        a.box((x, -0.02, SH - 0.39), (0.1, 0.11, 0.08), skin)
        arms[side] = a.obj(f"{name}_Braco{side}", C_PERS, origin=(x, -0.02, SH), parent=root)
    NZ, HS = T0 + TH + 0.04, 0.36
    h = MB()
    ez = head_build(h, NZ, HS, spec)
    ho = (0, -0.02, NZ)
    head = h.obj(name + "_Cabeca", C_PERS, origin=ho, parent=root)
    eyes_build(name, NZ, HS, ez, head, ho)
    return arms, head


STUDENTS = [
    dict(skin=SKIN[3], hair=HAIR[0], shirt=lin("F2F2F2"), pants=lin("2F4E7A"), style="afro"),
    dict(skin=SKIN[0], hair=HAIR[3], shirt=lin("F28FB0"), pants=lin("3B4A6B"), style="pony", glasses=True),
    dict(skin=SKIN[2], hair=HAIR[1], shirt=lin("7BD389"), pants=lin("2F4E7A"), style="short"),
    dict(skin=SKIN[5], hair=HAIR[2], shirt=lin("FFC93C"), pants=lin("4A4F63"), style="long", aid=True),
    dict(skin=SKIN[4], hair=HAIR[4], shirt=lin("57B3F9"), pants=lin("2B2F3F"), style="braids"),
    dict(skin=SKIN[1], hair=HAIR[0], shirt=lin("E5533D"), pants=lin("2F4E7A"), style="buzz"),
    dict(skin=SKIN[6], hair=HAIR[1], shirt=lin("B89AF0"), pants=lin("3B4A6B"), style="curly", glasses=True),
    dict(skin=SKIN[0], hair=HAIR[5], shirt=lin("FFAD60"), pants=lin("2B2F3F"), style="short"),
    dict(skin=SKIN[2], hair=HAIR[0], shirt=lin("2BB3A3"), pants=lin("4A4F63"), style="bun"),
    dict(skin=SKIN[3], hair=HAIR[4], shirt=lin("F4EBDA"), pants=lin("2F4E7A"), style="short", glasses=True),
    dict(skin=SKIN[5], hair=HAIR[3], shirt=lin("E5533D"), pants=lin("3B4A6B"), style="wavy"),
]
STUDENT_NAMES = []
for i, (x, y) in enumerate(SEATS):
    nm = f"Aluno{i:02d}"
    root = empty(nm, C_PERS, (x, y, 0))
    arms, head = seated(nm, STUDENTS[i % len(STUDENTS)], root)
    for a in arms.values():
        a.rotation_euler.x = math.radians(62)
    STUDENT_NAMES.append(nm)

# aluna cadeirante (inspirada na referência: cabelo ruivo ondulado, jaqueta azul, blusa roxa)
GIRL = dict(skin=lin("F5D3B8"), hair=lin("D9662B"), shirt=lin("4F7FD6"), inner=lin("A46BD1"),
            pants=lin("8A4B32"), shoes=lin("57B3F9"), style="wavy")
groot = empty("Aluna", C_PERS, (-W - 1.8, -1.0, 0), rotz=-math.pi / 2)
garms, ghead = seated("Aluna", GIRL, groot, S=0.53, shin=0.36)
b = MB()
dark, mid = lin("2E3440"), lin("3B4252")
b.box((0, 0.02, 0.5), (0.44, 0.44, 0.05), dark)
b.box((0, -0.21, 0.76), (0.42, 0.04, 0.44), mid)
for sx in (-1, 1):
    b.box((sx * 0.2, -0.27, 0.98), (0.03, 0.12, 0.03), P["tinta"])
    b.box((sx * 0.235, 0.02, 0.46), (0.025, 0.5, 0.025), P["prata"])
    b.box((sx * 0.215, -0.21, 0.72), (0.025, 0.025, 0.55), P["prata"])
    b.box((sx * 0.17, 0.26, 0.3), (0.025, 0.025, 0.34), P["prata"])
    b.cyl((sx * 0.17, 0.27, 0.06), 0.06, 0.03, P["tinta"], axis="X", seg=10)
b.box((0, 0.34, 0.12), (0.36, 0.14, 0.025), mid)
b.obj("Aluna_Cadeira", C_PERS, parent=groot)
for side, sx in (("E", -1), ("D", 1)):
    w = MB()
    c = (sx * 0.29, -0.06, 0.3)
    w.cyl(c, 0.3, 0.04, lin("222222"), axis="X", seg=20)
    w.cyl(c, 0.255, 0.05, lin("9AA3AF"), axis="X", seg=20)
    w.box((c[0], c[1], c[2]), (0.056, 0.48, 0.05), P["branco"])
    w.box((c[0], c[1], c[2]), (0.056, 0.05, 0.48), P["branco"])
    w.cyl(c, 0.06, 0.07, P["r5"], axis="X", seg=10)
    w.cyl((c[0] + sx * 0.03, c[1], c[2]), 0.28, 0.01, P["prata"], axis="X", seg=20)
    w.obj(f"Aluna_Roda{side}", C_PERS, origin=c, parent=groot)

# professora (mistura das duas referências: coque ruivo, óculos, colete verde, saia cáqui, livro azul)
TEACH = dict(skin=lin("F2C9A5"), hair=lin("B5582A"), style="bun", glasses=True)
troot = empty("Professora", C_PERS, (-3.05, 3.15, 0), rotz=math.pi)
for side, sx in (("E", -0.09), ("D", 0.09)):       # pernas separadas (pivô no quadril) para andar
    lg = MB()
    lg.box((sx, 0, 0.27), (0.12, 0.13, 0.5), TEACH["skin"])
    lg.box((sx, 0.03, 0.035), (0.14, 0.22, 0.07), lin("5B3A29"))
    lg.obj(f"Professora_Perna{side}", C_PERS, origin=(sx, 0, 0.5), parent=troot)
b = MB()
b.box((0, 0, 0.72), (0.44, 0.3, 0.46), lin("A88B6A"))
b.box((0, 0, 1.2), (0.44, 0.25, 0.52), lin("5E9C8F"))
b.box((0, 0.128, 1.33), (0.14, 0.012, 0.26), P["branco"])
for sx in (-1, 1):
    b.box((sx * 0.06, 0.13, 1.44), (0.1, 0.02, 0.06), P["branco"])
for z in (1.0, 1.08, 1.16):
    b.box((0, 0.13, z), (0.03, 0.012, 0.03), lin("C8662E"))
b.box((0, 0, 1.49), (0.13, 0.12, 0.06), TEACH["skin"])
b.obj("Professora_Corpo", C_PERS, parent=troot)
tarms = {}
for side, sx in (("E", -1), ("D", 1)):
    a = MB()
    x = sx * 0.28
    a.box((x, 0, 1.43 - 0.15), (0.12, 0.13, 0.3), P["branco"])
    a.box((x, 0, 1.43 - 0.38), (0.11, 0.12, 0.18), TEACH["skin"])
    a.box((x, 0, 1.43 - 0.5), (0.1, 0.11, 0.07), TEACH["skin"])
    if side == "D":   # livro azul-esverdeado na mão direita
        a.box((x - 0.07, 0.12, 0.98), (0.05, 0.24, 0.3), lin("6EC1C8"))
        a.box((x - 0.045, 0.12, 0.98), (0.012, 0.2, 0.26), P["papel"])
    else:             # ponteiro na mão esquerda, na linha do braço
        a.box((x, 0.07, 1.43 - 0.5 - 0.3), (0.025, 0.025, 0.66), P["madeira2"])
        a.box((x, 0.07, 1.43 - 0.5 - 0.64), (0.035, 0.035, 0.05), P["r1"])
    tarms[side] = a.obj(f"Professora_Braco{side}", C_PERS, origin=(x, 0, 1.43), parent=troot)
NZ, HS = 1.52, 0.38
h = MB()
ez = head_build(h, NZ, HS, TEACH)
thead = h.obj("Professora_Cabeca", C_PERS, origin=(0, 0, NZ), parent=troot)
eyes_build("Professora", NZ, HS, ez, thead, (0, 0, NZ))

# ventiladores de teto (giram na animação)
for k, (fx_, fy_) in enumerate([(0.0, -1.2), (0.0, 1.6)]):
    b = MB()
    b.box((0, 0, H - 0.2), (0.04, 0.04, 0.4), P["metal"])
    b.obj(f"Ventilador{k}_Haste", C_SALA).location = (fx_, fy_, 0)
    b = MB()
    b.cyl((0, 0, 0), 0.13, 0.12, P["branco"], axis="Z", seg=12)
    b.cyl((0, 0, -0.07), 0.07, 0.04, P["prata"], axis="Z", seg=10)
    for j in range(4):
        a = j * math.pi / 2
        b.box((math.cos(a) * 0.42, math.sin(a) * 0.42, 0.0), (0.62, 0.15, 0.018), lin("F4EBDA"), rot=(0, 0, a))
    fan = b.obj(f"Ventilador{k}", C_SALA)
    fan.location = (fx_, fy_, H - 0.42)

# ---------------------------------------------------------------- luzes e mundo
def light(name, kind, loc, energy, color="FFFFFF", rot=(0, 0, 0), size=1.0, size_y=None):
    ld = bpy.data.lights.new(name, kind)
    ld.energy = energy
    ld.color = lin(color)[:3]
    if kind == "AREA":
        ld.shape = "RECTANGLE"
        ld.size, ld.size_y = size, size_y or size
    if kind == "SUN":
        ld.angle = math.radians(3)
    o = bpy.data.objects.new(name, ld)
    C_LUZ.objects.link(o)
    o.location, o.rotation_euler = loc, rot
    return o


for x in (-2.0, 2.0):
    for y in (-2.4, 0.0, 2.4):
        light(f"Teto_{x}_{y}", "AREA", (x, y, H - 0.08), 110, "FFF6E8", size=1.3, size_y=0.35)
light("Sol", "SUN", (0, 0, 10), 3.2, "FFE6BE", rot=(math.radians(-15), math.radians(52), math.radians(8)))
light("Preenchimento_Quadro", "AREA", (0, 1.2, 3.2), 90, "FFFFFF", rot=(math.radians(-60), 0, 0), size=4, size_y=1)
light("Corredor_Luz", "AREA", (-W - 1.5, -1.0, H - 0.2), 60, "FFF6E8", size=1.5)

wd = bpy.data.worlds.get("World") or bpy.data.worlds.new("World")
sc.world = wd
if wd.node_tree is None:
    wd.use_nodes = True
bg = next(n for n in wd.node_tree.nodes if n.type == "BACKGROUND")
bg.inputs["Color"].default_value = lin("BFDDF5")
bg.inputs["Strength"].default_value = 0.7

# câmera
cd = bpy.data.cameras.new("Cam")
cd.lens, cd.clip_start, cd.clip_end = 28, 0.05, 200
cam = bpy.data.objects.new("Cam", cd)
sc.collection.objects.link(cam)
sc.camera = cam
cam.location = (3.4, -3.6, 2.5)
cam.rotation_euler = (math.radians(70), 0, math.radians(40))

# render
sc.render.engine = "BLENDER_EEVEE"
sc.render.resolution_x, sc.render.resolution_y = 1920, 1080
sc.render.resolution_percentage = 50
sc.eevee.taa_render_samples = 16
sc.view_settings.view_transform = "AgX"
try:
    sc.view_settings.look = "AgX - Medium High Contrast"
except Exception:
    pass

# brilho suave (bloom) no compositor, para o raio e as cores
try:
    for g in [g for g in bpy.data.node_groups if g.name.startswith("Composicao")]:
        bpy.data.node_groups.remove(g)
    ng = bpy.data.node_groups.new("Composicao", "CompositorNodeTree")
    ng.interface.new_socket("Image", in_out="OUTPUT", socket_type="NodeSocketColor")
    rl = ng.nodes.new("CompositorNodeRLayers")
    gl = ng.nodes.new("CompositorNodeGlare")
    gl.inputs["Type"].default_value = "Bloom"
    gl.inputs["Threshold"].default_value = 1.2
    gl.inputs["Strength"].default_value = 0.6
    gl.inputs["Size"].default_value = 0.5
    go = ng.nodes.new("NodeGroupOutput")
    ng.links.new(rl.outputs["Image"], gl.inputs["Image"])
    ng.links.new(gl.outputs["Image"], go.inputs[0])
    sc.compositing_node_group = ng
except Exception as e:
    print("compositor:", e)

for o in bpy.data.objects:
    if o.name.startswith(("Titulo", "Slogan", "Palavra_", "Sombra_", "Feixe")):
        o.visible_shadow = False

bpy.app.driver_namespace["prisma"] = dict(
    seats=SEATS, students=STUDENT_NAMES, pix=pix_info, girl_desk=GIRL_DESK, rows=ROWS_Y, cols=COLS_X,
    board=(BX, BY, BZ, BW, BH, BFRONT), logo_c=LOGO_C, px=PX, words=PALAVRAS, door_y=DOOR_Y, W=W, D=D)

os.makedirs(OUT, exist_ok=True)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, "intro_prisma.blend"))
result = {"objects": len(bpy.data.objects), "pixels": len(pix_info), "seats": len(SEATS),
          "giz_dim": tuple(round(v, 2) for v in giz.dimensions), "slogan_dim": tuple(round(v, 2) for v in slogan.dimensions),
          "titulo_dim": tuple(round(v, 2) for v in titulo.dimensions)}
