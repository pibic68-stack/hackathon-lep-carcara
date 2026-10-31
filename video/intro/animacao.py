"""Animação da intro PRISMA (rodar depois de cena.py). Grava keyframes de tudo e
escreve saida/eventos.json com os tempos que a trilha usa.

96 BPM: compasso = 2,5 s. Quadro f = round(t*24) + 1.
"""
import bpy, math, os, random, json
from mathutils import Vector, Euler

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "saida")
HELP = os.path.join(os.path.expanduser("~"), ".claude", "skills", "blender-3d-video", "scripts", "anim_helpers.py")
_h = {}
exec(compile(open(HELP, encoding="utf-8").read(), HELP, "exec"), _h)
put, ss, win, lerp = _h["put"], _h["ss"], _h["win"], _h["lerp"]

FPS, NF = 24, 708           # 708 = 29,5 s; o preto final entra na montagem
F = lambda t: int(round(t * FPS)) + 1
T = lambda f: (f - 1) / FPS
FR = range(1, NF + 1)
random.seed(11)
sc = bpy.context.scene
sc.frame_start, sc.frame_end = 1, NF
O = bpy.data.objects

for o in O:
    if o.animation_data:
        o.animation_data_clear()
    for c in list(o.constraints):
        o.constraints.remove(c)

EV = {}  # eventos para a música (segundos)


def unwrap(prev, a):
    while a - prev > math.pi:
        a -= 2 * math.pi
    while a - prev < -math.pi:
        a += 2 * math.pi
    return a


def yaw_to(src, dst):
    """Rotação em Z para olhar de src para dst (personagem montado olhando +Y)."""
    return math.atan2(-(dst[0] - src[0]), dst[1] - src[1])


def ease_back(u):
    u = min(1, max(0, u))
    c = 1.7
    return 1 + (c + 1) * (u - 1) ** 3 + c * (u - 1) ** 2


# ---------------------------------------------------------------- trajeto da aluna
def cr(P, u):
    i = min(int(u), len(P) - 2)
    s = u - i
    p0, p1, p2, p3 = P[max(i - 1, 0)], P[i], P[i + 1], P[min(i + 2, len(P) - 1)]
    return 0.5 * ((2 * p1) + (-p0 + p2) * s + (2 * p0 - 5 * p1 + 4 * p2 - p3) * s * s + (-p0 + 3 * p1 - 3 * p2 + p3) * s ** 3)


GP = [Vector(p) for p in [(-5.6, -1.0), (-4.7, -1.0), (-4.05, -0.82), (-3.78, -0.25), (-3.62, 0.25),
                          (-3.2, 0.5), (-2.82, 0.64), (-2.7, 0.9)]]
DENSE = [cr(GP, u * (len(GP) - 1) / 1200) for u in range(1201)]
CUM = [0.0]
for a, b in zip(DENSE, DENSE[1:]):
    CUM.append(CUM[-1] + (b - a).length)
GL = CUM[-1]
G_T0, G_T1 = 2.6, 7.35
EV["aluna_entra"] = G_T0


def girl_s(t):
    return GL * ss(G_T0, G_T1, t)


def girl_at(t):
    s = girl_s(t)
    j = 0
    while j < len(CUM) - 2 and CUM[j + 1] < s:
        j += 1
    u = (s - CUM[j]) / max(1e-9, CUM[j + 1] - CUM[j])
    p = DENSE[j].lerp(DENSE[j + 1], u)
    a, b = DENSE[max(j - 3, 0)], DENSE[min(j + 4, len(DENSE) - 1)]
    d = b - a
    return p, math.atan2(-d.x, d.y), s


gp = {}
prev = -math.pi / 2
G = {}
for f in FR:
    p, th, s = girl_at(T(f))
    th = unwrap(prev, th)
    prev = th
    G[f] = (p, th, s)
put(O["Aluna"], "location", {f: (G[f][0].x, G[f][0].y, 0) for f in FR})
put(O["Aluna"], "rotation_euler", {f: (0, 0, G[f][1]) for f in FR})
for side in "ED":
    put(O[f"Aluna_Roda{side}"], "rotation_euler", {f: (-G[f][2] / 0.3, 0, 0) for f in FR})
# braços: empurram as rodas, depois aceno para a professora, depois mãos na mesa
WAVE_G = (7.55, 9.1)
for side, sx in (("E", -1), ("D", 1)):
    R = {}
    for f in FR:
        t = T(f)
        moving = win(t, G_T0 + 0.1, G_T1 - 0.15, 0.3)
        ph = 2 * math.pi * G[f][2] / 0.75
        push = (0.35 + 0.45 * math.sin(ph), 0.15 if sx < 0 else -0.15, 0)
        rest = (0.25, 0.12 if sx < 0 else -0.12, 0)
        desk = (math.radians(62), 0, 0)
        x = lerp(rest[0], push[0], moving)
        y = lerp(rest[1], push[1], moving)
        z = 0.0
        if side == "D":
            w = win(t, WAVE_G[0], WAVE_G[1], 0.3)
            x = lerp(x, 2.75, w)
            y = lerp(y, -0.15 + 0.3 * math.sin(2 * math.pi * 2.2 * t), w)
        k = ss(WAVE_G[1] - 0.1, WAVE_G[1] + 0.6, t)
        x, y = lerp(x, desk[0], k), lerp(y, desk[1], k)
        R[f] = (x, y, z)
    put(O[f"Aluna_Braco{side}"], "rotation_euler", R)
# cabeça: olha a turma ao entrar, depois a professora
H = {}
for f in FR:
    t = T(f)
    yaw = -0.45 * win(t, 4.3, 6.4, 0.5) + 0.25 * win(t, 6.6, 9.4, 0.4) + 0.06 * math.sin(t * 1.3)
    tilt = 0.06 * math.sin(t * 2.1) - 0.08 * win(t, 7.5, 9.2, 0.3)
    H[f] = (tilt, 0.08 * win(t, 7.5, 9.2, 0.3), yaw)
put(O["Aluna_Cabeca"], "rotation_euler", H)

# ---------------------------------------------------------------- porta
DOOR_T = (2.3, 3.05)
EV["porta"] = 2.5
put(O["Porta"], "rotation_euler", {f: (0, 0, -math.radians(95) * ease_back((T(f) - DOOR_T[0]) / (DOOR_T[1] - DOOR_T[0])))
                                    for f in FR})

# ---------------------------------------------------------------- professora
# Roteiro: aponta o PRISMA de giz para a turma -> olha a porta -> acena para a aluna ->
# anda até a frente do quadro -> conversa com a turma -> aponta o giz enquanto a câmera chega ->
# assiste a logo montar -> aponta a logo enquanto a câmera recua e mostra a cena.
P0 = Vector((-3.05, 3.15, 0))
P1 = Vector((-2.1, 3.4, 0))
WALK = (9.9, 11.8)
STEP = 0.25                                   # metros por passo
CHALK = Vector((0.0, 3.92, 1.77))             # centro do PRISMA de giz
LOGO = Vector((0.0, 3.9, 2.2))                # centro da logo
CAM_END = Vector((-0.65, 0.0, 2.15))       # alto, para não pegar a cabeça da 1ª fila
FACE0 = math.pi + 0.5                         # de frente para a turma, meio virada para o quadro
FACE1 = math.pi + 0.45


def t_pos(t):
    u = ss(*WALK, t)
    return P0.lerp(P1, u), u * (P1 - P0).length


def rz(v, a):
    c, s = math.cos(a), math.sin(a)
    return Vector((c * v.x - s * v.y, s * v.x + c * v.y, v.z))


def arm_to(root, th, side_x, target):
    """Euler (x, y, 0) que aponta o braço (pendurado em -Z, pivô no ombro) para o alvo."""
    sh = root + rz(Vector((side_x, 0, 1.43)), th)
    d = rz((target - sh).normalized(), -th)
    return (math.asin(max(-1, min(1, d.y))), math.atan2(-d.x, -d.z), 0.0)


def look_yaw(src, th, target, lim=1.1):
    return max(-lim, min(lim, unwrap(0, yaw_to(src, target) - th)))


girl_head_at = lambda t: Vector((girl_at(min(t, G_T1))[0].x, girl_at(min(t, G_T1))[0].y, 1.0))
CLASS = [Vector((-1.8, -1.2, 1.1)), Vector((1.2, -2.2, 1.1)), Vector((2.6, 0.2, 1.1)), Vector((0.0, -0.6, 1.1))]
DOOR = Vector((-4.5, -1.0, 1.4))
# sequência do olhar: (início, alvo)
LOOK = [(0.0, CLASS[3]), (0.75, CHALK), (1.6, CLASS[0]), (2.35, DOOR), (3.2, "aluna"), (9.6, "frente"),
        (12.0, CLASS[0]), (13.0, CLASS[1]), (14.0, CHALK), (15.1, CLASS[2]), (16.4, CHALK), (17.7, CLASS[3]),
        (18.7, CHALK), (24.95, CAM_END), (25.6, LOGO), (26.5, CAM_END)]


def look_target(spec, t, pos, th):
    if spec == "aluna":
        return girl_head_at(t)
    if spec == "frente":
        return pos + rz(Vector((0, 2.0, 1.6)), th)
    return spec


tw_yaw = yaw_to(P0, P1)
TR, TL, TA_E, TA_D, TH, TLEG = {}, {}, {}, {}, {}, {}
prev = FACE0
for f in FR:
    t = T(f)
    pos, s = t_pos(t)
    g = girl_head_at(t)
    # corpo
    girl_yaw = unwrap(prev, yaw_to(pos, g))
    th = FACE0 + 0.06 * math.sin(t * 0.9)
    th = lerp(th, lerp(math.pi, girl_yaw, 0.85), win(t, 2.7, 9.6, 0.8))
    late = FACE1 + 0.12 * math.sin(t * 0.75)
    th = lerp(th, late, ss(9.6, 11.2, t))
    th = lerp(th, unwrap(th, tw_yaw), win(t, WALK[0] - 0.4, WALK[1] + 0.35, 0.45))
    point_w = win(t, -1.0, 2.35, 0.4) + win(t, 14.0, 15.2, 0.35) + win(t, 16.3, 20.6, 0.5) + win(t, 25.8, 30.0, 0.8)
    th += 0.22 * point_w * (1 - win(t, WALK[0] - 0.4, WALK[1] + 0.35, 0.45))
    th = unwrap(prev, th)
    prev = th
    # passos
    walking = win(t, WALK[0], WALK[1], 0.25)
    ph = math.pi * s / STEP
    leg = 0.38 * math.sin(ph) * walking
    bob = 0.022 * abs(math.sin(ph)) * walking
    TR[f] = (0, 0, th)
    TL[f] = (pos.x, pos.y, bob)
    TLEG[f] = leg
    # braço esquerdo (ponteiro): repouso, apontando, balanço ao andar
    rest_e = (0.12 + 0.05 * math.sin(t * 1.3), 0.08, 0.0)
    if t < 8:      # lê o PRISMA da esquerda para a direita
        tgt = CHALK + Vector((lerp(-1.1, 1.1, ss(0.0, 2.2, t)), 0, 0.05 * math.sin(t * 2 * math.pi / 0.625)))
    elif t < 22:
        tgt = CHALK + Vector((lerp(-1.1, 1.1, ss(16.6, 19.6, t)) if t > 16 else 0.0, 0,
                              0.05 * math.sin((t - 7.5) * 2 * math.pi / 1.25)))
    else:
        tgt = LOGO + Vector((-0.35, 0, 0.04 * math.sin((t - 25) * 2 * math.pi / 1.25)))
    pe = arm_to(pos, th, -0.28, tgt)
    pw = min(1.0, point_w)
    ex = lerp(rest_e[0], pe[0], pw) - 0.28 * math.sin(ph) * walking
    ey = lerp(rest_e[1], pe[1], pw)
    TA_E[f] = (ex, ey, 0)
    # braço direito (livro): repouso, aceno para a aluna, gestos de explicação, "olha só" no final
    wv = win(t, 3.6, 6.3, 0.45)
    talk = win(t, 12.2, 16.2, 0.5) * (0.5 + 0.5 * math.sin(2 * math.pi * 0.8 * (t - 12.2) - 1.57))
    show = win(t, 25.4, 30.0, 0.8)
    dx = 0.42 + 0.28 * math.sin(ph) * walking + 0.45 * talk + 0.12 * show
    dy = -0.06 - 0.35 * talk - 0.55 * show
    dx = lerp(dx, 0.15, wv)
    dy = lerp(dy, -(2.55 + 0.3 * math.sin(2 * math.pi * 1.8 * t)), wv)
    TA_D[f] = (dx, dy, 0)
    # cabeça
    i = max(k for k in range(len(LOOK)) if LOOK[k][0] <= t)
    hp = pos + Vector((0, 0, 1.7))
    y0 = look_yaw(hp, th, look_target(LOOK[i][1], t, pos, th))
    yaw = y0
    tilt = 0.0
    if i + 1 < len(LOOK):
        y1 = look_yaw(hp, th, look_target(LOOK[i + 1][1], t, pos, th))
        yaw = lerp(y0, y1, ss(LOOK[i + 1][0] - 0.35, LOOK[i + 1][0], t))
    up = 0.18 * (win(t, 20.6, 24.95, 0.4) + win(t, 25.6, 26.5, 0.3))
    tilt = up + 0.04 * math.sin(t * 1.7) - 0.05 * win(t, 3.4, 7.0, 0.5)
    TH[f] = (tilt, 0.07 * win(t, 3.4, 7.0, 0.5) + 0.04 * math.sin(t * 1.1), yaw)
put(O["Professora"], "rotation_euler", TR)
put(O["Professora"], "location", TL)
put(O["Professora_BracoE"], "rotation_euler", TA_E)
put(O["Professora_BracoD"], "rotation_euler", TA_D)
put(O["Professora_Cabeca"], "rotation_euler", TH)
put(O["Professora_PernaE"], "rotation_euler", {f: (TLEG[f], 0, 0) for f in FR})
put(O["Professora_PernaD"], "rotation_euler", {f: (-TLEG[f], 0, 0) for f in FR})
EV["professora_acena"] = 3.6
EV["professora_anda"] = WALK[0]


def teacher_head(t):
    p = TL[F(t)]
    return Vector((p[0], p[1], 1.7))


# ---------------------------------------------------------------- turma
students = sorted([o.name for o in O if o.name.startswith("Aluno") and o.type == "EMPTY"])
# mãos levantadas: (aluno, braço, início, fim)
HANDS = [("Aluno03", "E", 4.4, 6.0), ("Aluno00", "E", 6.6, 8.2), ("Aluno02", "D", 9.0, 11.2),
         ("Aluno06", "E", 10.8, 12.9), ("Aluno09", "D", 12.6, 14.6), ("Aluno01", "E", 14.3, 16.4),
         ("Aluno07", "D", 15.6, 17.6)]
CHAT = {"Aluno04": ("Aluno05", 10.6, 12.6), "Aluno05": ("Aluno04", 10.7, 12.5),
        "Aluno08": ("Aluno07", 13.4, 15.4),
        "Aluno07": ("Aluno08", 13.5, 15.3)}
EV["maos"] = [h[2] for h in HANDS]
NOD_T0 = 7.5                                   # balançam a cabeça a cada 2 tempos (junto com as palavras)
for nm in students:
    root = O[nm]
    src = root.location
    delay = random.uniform(0, 0.45)
    ph = random.uniform(0, 6.28)
    nod_a = random.choice([0.0, 0.04, 0.06, 0.07])
    wr_ph = random.uniform(0, 6.28)
    write_on = [(a, a + random.uniform(1.5, 3.0)) for a in sorted(random.sample(range(9, 28, 2), 4))]
    Hh = {}
    Rt = {}
    for f in FR:
        t = T(f)
        g = G[f][0]
        a = max(-1.35, min(1.35, unwrap(0, yaw_to(src, g))))
        w = win(t, 2.9 + delay, 8.6 + delay, 0.5)
        tp = teacher_head(t)
        teach = 0.8 * max(-1.2, min(1.2, unwrap(0, yaw_to(src, tp))))
        board = 0.35 * yaw_to(src, (0.0, 3.9))
        att = lerp(teach, board, win(t, 16.5, 30, 0.6) * 0.6 + win(t, 14.0, 15.2, 0.3) * 0.6)
        yaw = lerp(att, a, w) + 0.05 * math.sin(t * 0.8 + ph)
        tilt = 0.05 * math.sin(t * 1.1 + ph) - 0.05
        tilt -= nod_a * (0.5 + 0.5 * math.cos(2 * math.pi * (t - NOD_T0) / 1.25)) * win(t, NOD_T0 - 0.3, 17.8, 0.6)
        if nm in CHAT:
            other, c0, c1 = CHAT[nm]
            cw = win(t, c0, c1, 0.35)
            yaw = lerp(yaw, max(-1.35, min(1.35, yaw_to(src, O[other].location))), cw)
            tilt += 0.05 * math.sin(2 * math.pi * 2.6 * t + ph) * cw
        Hh[f] = (tilt, 0.04 * math.sin(t * 0.6 + ph), yaw)
        Rt[f] = (0, 0.025 * math.sin(t * 0.6 + ph), 0.045 * math.sin(t * 0.45 + ph * 1.3))
    put(O[nm + "_Cabeca"], "rotation_euler", Hh)
    put(root, "rotation_euler", Rt)
    rest = math.radians(62)
    for side, sgn in (("E", 1), ("D", -1)):
        A = {}
        mine = [(a0, a1) for (n, sd, a0, a1) in HANDS if n == nm and sd == side]
        for f in FR:
            t = T(f)
            x, y = rest, 0.0
            if side == "D":      # escrevendo no caderno
                wr = sum(win(t, a0, a1, 0.3) for a0, a1 in write_on)
                x += wr * 0.06 * math.sin(2 * math.pi * 2.3 * t + wr_ph)
                y += wr * 0.07 * math.sin(2 * math.pi * 3.1 * t + wr_ph)
            for a0, a1 in mine:
                h = win(t, a0, a1, 0.35)
                x = lerp(x, 0.15, h)
                y = lerp(y, sgn * (2.5 + 0.18 * math.sin(2 * math.pi * 2.0 * t)), h)
            A[f] = (x, y, 0)
        put(O[f"{nm}_Braco{side}"], "rotation_euler", A)

# aluna: depois de chegar, acompanha a professora com o olhar e escreve
Hg = {}
for f in FR:
    t = T(f)
    p, th, _ = G[f]
    k = ss(9.0, 9.8, t)
    ty = max(-1.1, min(1.1, unwrap(0, yaw_to(p, teacher_head(t)) - th)))
    old = H[f]
    nod = -0.05 * (0.5 + 0.5 * math.cos(2 * math.pi * (t - NOD_T0) / 1.25)) * win(t, 9.5, 17.8, 0.6)
    Hg[f] = (lerp(old[0], 0.02 + nod, k), old[1] * (1 - k), lerp(old[2], ty, k))
put(O["Aluna_Cabeca"], "rotation_euler", Hg)

# ventiladores de teto
for k in range(2):
    fan = O[f"Ventilador{k}"]
    put(fan, "rotation_euler", {f: (0, 0, (k * 0.6) + (1 if k else -1) * 2 * math.pi * 0.7 * T(f)) for f in (1, NF)})

# piscar
for o in [o for o in O if o.name.endswith("_Olhos")]:
    S = {1: (1, 1, 1)}
    t = random.uniform(0.5, 2.5)
    while t < NF / FPS:
        f0 = F(t)
        S[f0 - 1] = (1, 1, 1)
        S[f0 + 1] = (1, 1, 0.12)
        S[f0 + 3] = (1, 1, 1)
        t += random.uniform(2.4, 4.6)
    S[NF] = (1, 1, 1)
    put(o, "scale", dict(sorted(S.items())))

# ---------------------------------------------------------------- câmera
cam = O["Cam"]
cam.data.lens = 28


def hermite(keys, t):
    if t <= keys[0][0]:
        return keys[0][1].copy()
    if t >= keys[-1][0]:
        return keys[-1][1].copy()
    n = len(keys)

    def tan(i):
        if i == 0 or i == n - 1:
            return Vector((0, 0, 0))
        return (keys[i + 1][1] - keys[i - 1][1]) / (keys[i + 1][0] - keys[i - 1][0])

    for i in range(n - 1):
        t0, p0 = keys[i]
        t1, p1 = keys[i + 1]
        if t0 <= t <= t1:
            h = t1 - t0
            u = (t - t0) / h
            return (p0 * (2 * u ** 3 - 3 * u ** 2 + 1) + tan(i) * h * (u ** 3 - 2 * u ** 2 + u)
                    + p1 * (-2 * u ** 3 + 3 * u ** 2) + tan(i + 1) * h * (u ** 3 - u ** 2))


V = lambda *a: Vector(a)
CPOS = [(0.0, V(3.5, -3.75, 2.55)), (2.5, V(3.3, -3.55, 2.4)), (5.0, V(0.0, -2.6, 1.6)),
        (7.5, V(-1.8, -1.0, 1.45)), (10.0, V(1.1, -3.1, 2.4)), (12.5, V(2.9, -1.6, 2.45)),
        (15.0, V(2.2, -0.4, 2.3)), (17.5, V(0.65, -0.35, 2.0)), (20.0, V(0.0, 1.0, 1.75)), (24.9, V(0.0, 1.12, 1.75))]
# no slogan a câmera recua e mostra a professora apontando a logo
PULL = (24.9, 28.4)
CAM_TGT_END = V(-0.45, 3.92, 1.8)
BOARD_T = V(0.0, 3.92, 1.75)
CTGT_STATIC = [(0.0, V(-1.4, 0.4, 1.0)), (2.5, V(-3.6, -0.9, 1.2)), (9.0, V(-0.6, 1.2, 1.0)), (10.0, V(-0.7, 1.2, 1.0)),
               (12.5, V(-1.0, 1.6, 1.0)), (15.0, V(-0.8, 3.2, 1.45)), (17.5, V(0.0, 3.92, 1.8)), (20.0, BOARD_T),
               (29.5, BOARD_T)]


def girl_head(t):
    p = girl_at(t)[0]
    return Vector((p.x, p.y, 0.95))


def cam_pos(t):
    return hermite(CPOS, t).lerp(CAM_END, ss(*PULL, t))


def cam_tgt(t):
    st = hermite(CTGT_STATIC, t)
    w = win(t, 3.4, 9.2, 1.1)
    return st.lerp(girl_head(min(t, 7.6)), w).lerp(CAM_TGT_END, ss(*PULL, t))


Lc, Rc, prev = {}, {}, None
for f in FR:
    t = T(f)
    p, tg = cam_pos(t), cam_tgt(t)
    q = (tg - p).to_track_quat("-Z", "Y")
    e = q.to_euler("XYZ", prev) if prev else q.to_euler()
    prev = e
    Lc[f], Rc[f] = tuple(p), tuple(e)
put(cam, "location", Lc)
put(cam, "rotation_euler", Rc)

# folga entre câmera e cabeças
heads = [O[n].location + Vector((0, 0, 1.2)) for n in students]
clear = min((Vector(Lc[f]) - h).length for f in FR for h in heads)

# ---------------------------------------------------------------- palavras flutuantes
WORD_T0, WORD_DT, LIFE = 7.5, 1.25, 2.4
EV["palavras"] = []
for i in range(8):
    t0 = WORD_T0 + i * WORD_DT
    EV["palavras"].append(t0)
    txt = O[f"Palavra_{i}"]
    pl = O[f"Sombra_{i}"]
    side = -1 if i % 2 == 0 else 1
    k = min(1.0, 0.9 / max(0.01, txt.dimensions.x / max(1e-6, txt.scale.x)))
    c = txt.constraints.new("TRACK_TO")
    c.target, c.track_axis, c.up_axis = cam, "TRACK_Z", "UP_Y"
    L, S, A = {}, {}, {}
    for f in range(max(1, F(t0) - 2), min(NF, F(t0 + LIFE) + 2) + 1):
        t = T(f)
        u = (t - t0) / LIFE
        p, tg = cam_pos(t), cam_tgt(t)
        fwd = (tg - p).normalized()
        right = fwd.cross(Vector((0, 0, 1))).normalized()
        up = right.cross(fwd)
        a = ss(t0, t0 + 0.35, t) * (1 - ss(t0 + LIFE - 0.5, t0 + LIFE, t))
        L[f] = tuple(p + fwd * 1.9 + right * (side * 0.47) + up * ((0.3 if side < 0 else -0.05) + 0.14 * u))
        sc_ = k * (0.55 + 0.45 * ease_back((t - t0) / 0.4))
        if f < F(t0) or f > F(t0 + LIFE):
            sc_ = 0.0
        S[f] = (sc_, sc_, sc_)
        A[f] = (1, 1, 1, a)
    put(txt, "location", L)
    put(txt, "scale", S)
    put(txt, "color", A)
    put(pl, "color", A)

# ---------------------------------------------------------------- quadro
T_GIZ = 20.0
EV["giz_some"] = T_GIZ
giz = O["Giz_PRISMA"]
put(giz, "color", {F(T_GIZ) - 1: (1, 1, 1, 1), F(T_GIZ + 1.1): (1, 1, 1, 0)})

# poeira de giz: partículas emitidas da forma das letras
for n in ("Giz_Emissor", "Poeira"):
    if n in O:
        bpy.data.objects.remove(O[n], do_unlink=True)
dg = bpy.context.evaluated_depsgraph_get()
me = bpy.data.meshes.new_from_object(giz.evaluated_get(dg))
em = bpy.data.objects.new("Giz_Emissor", me)
giz.users_collection[0].objects.link(em)
em.matrix_world = giz.matrix_world.copy()
em.show_instancer_for_render = False
em.show_instancer_for_viewport = False
dust_me = bpy.data.meshes.new("Poeira")
import bmesh
bm = bmesh.new()
bmesh.ops.create_cube(bm, size=1.0)
bm.to_mesh(dust_me)
bm.free()
dm = bpy.data.materials.get("PoeiraMat") or bpy.data.materials.new("PoeiraMat")
if dm.node_tree is None:
    dm.use_nodes = True
bs = next(n for n in dm.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
bs.inputs["Base Color"].default_value = (0.92, 0.92, 0.88, 1)
bs.inputs["Emission Color"].default_value = (0.92, 0.92, 0.88, 1)
bs.inputs["Emission Strength"].default_value = 0.25
dust_me.materials.append(dm)
dust = bpy.data.objects.new("Poeira", dust_me)
giz.users_collection[0].objects.link(dust)
dust.location = (0, 0, -20)
mod = em.modifiers.new("Poeira", "PARTICLE_SYSTEM")
pst = em.particle_systems[0].settings
pst.count = 1400
pst.frame_start, pst.frame_end = F(T_GIZ), F(T_GIZ + 0.9)
pst.lifetime, pst.lifetime_random = 34, 0.7
pst.emit_from = "FACE"
pst.normal_factor, pst.factor_random = 0.35, 0.45
pst.effector_weights.gravity = 0.12
pst.brownian_factor = 0.15
pst.render_type = "OBJECT"
pst.instance_object = dust
pst.particle_size, pst.size_random = 0.013, 0.6
pst.use_rotations, pst.rotation_factor_random = True, 1.0

# pixels do prisma
pix = []
for o in O:
    if o.name.startswith("Px_"):
        _, grp, x, y = o.name.split("_")
        pix.append((o, grp, int(x), int(y)))
T_BODY = 20.65
T_BEAM = 22.5
T_HIT = T_BEAM + 0.3125                       # meia batida a 96 BPM
T_RAY = [23.125 + 0.3125 * k for k in range(6)]  # uma cor por colcheia
EV.update(prisma_monta=T_BODY, feixe=T_BEAM, feixe_bate=T_HIT, cores=T_RAY,
          linhas=[T_BODY + (16 - y) / 15 * 1.25 for y in range(16, 0, -1)])


def pop(o, t0, glow_peak, glow_rest, t_glow=None, glow_spike=None):
    f0 = F(t0)
    put(o, "scale", {f0 - 1: (0, 0, 0), f0 + 3: (1.22, 1.22, 1.22), f0 + 6: (0.95, 0.95, 0.95), f0 + 8: (1, 1, 1)})
    put(o, "location", {f0 - 1: (o.location.x, -0.25, o.location.z), f0 + 5: (o.location.x, 0, o.location.z)})
    C = {f0 - 1: (glow_peak, 0, 0, 1), f0 + 10: (glow_rest, 0, 0, 1)}
    if t_glow:
        g = F(t_glow)
        C[g] = (glow_rest, 0, 0, 1)
        C[g + 5] = (glow_spike, 0, 0, 1)
        C[g + 20] = (glow_rest * 2.2, 0, 0, 1)
    put(o, "color", dict(sorted(C.items())))


end_x = O["Logo"].location.x + (10 - 14.5) * 0.056
for o, grp, x, y in pix:
    if grp == "corpo":
        d = (16 - y) / 15 * 1.25 + (x % 3) * 0.035 + random.uniform(0, 0.08)
        pop(o, T_BODY + d, 0.9, 0.12, t_glow=T_HIT + abs(x - 14) * 0.012, glow_spike=1.1)
    elif grp == "feixe":
        xw = O["Logo"].location.x + (x - 14.5) * 0.056
        pop(o, T_BEAM + (xw - O["Feixe_Luz"].location.x) / (end_x - O["Feixe_Luz"].location.x) * (T_HIT - T_BEAM) - 0.04, 3.0, 0.7)
    else:
        k = int(grp[1]) - 1
        pop(o, T_RAY[k] + max(0, x - 21) / 8 * 0.24, 3.2, 1.0)

fx = O["Feixe_Luz"]
L0 = fx.location.copy()
full = end_x - L0.x
put(fx, "scale", {F(T_BEAM) - 1: (0.001, 1, 1), F(T_HIT): (full, 1, 1), F(T_HIT + 1.2): (full, 1, 1)})
put(fx, "color", {F(T_BEAM) - 1: (6, 0, 0, 0), F(T_BEAM) + 2: (6, 0, 0, 1), F(T_HIT + 0.15): (6, 0, 0, 1),
                  F(T_HIT + 1.2): (2, 0, 0, 0)})

# título e slogan
T_TIT, T_SLO = 25.0, 25.55
EV.update(titulo=T_TIT, slogan=T_SLO, corte=29.5)
for nm, t0, z in (("Titulo_PRISMA", T_TIT, 1.30), ("Slogan", T_SLO, 0.94)):
    o = O[nm]
    put(o, "color", {F(t0) - 1: (1, 1, 1, 0), F(t0 + 0.6): (1, 1, 1, 1)})
    put(o, "scale", {F(t0) - 2: (0, 0, 0), F(t0) - 1: (1, 1, 1)})
    put(o, "location", {F(t0) - 1: (o.location.x, o.location.y, z - 0.06), F(t0 + 0.7): (o.location.x, o.location.y, z)})

sc.frame_set(1)
with open(os.path.join(OUT, "eventos.json"), "w", encoding="utf-8") as fh:
    json.dump(EV, fh, indent=1)
bpy.ops.wm.save_mainfile()
result = {"girl_len": round(GL, 2), "cam_head_clearance": round(clear, 2), "pix": len(pix), "events": EV}
