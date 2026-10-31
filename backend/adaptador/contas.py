"""Contas, turmas e sessões do PRISMA (SQLite local em backend/dados/, fora do Git).

Quem entra e como:
  - escola:    cria a conta com nome, e-mail, senha e o CÓDIGO que vai passar aos professores; entra com e-mail e senha.
               Vê (só vê) as listas de professores, turmas, alunos e materiais dela;
  - professor: cria a conta com o código da escola (de uma escola cadastrada ou o PRISMA_CODIGO_ESCOLA do .env)
               e entra com e-mail e senha;
  - aluno:     código da turma + senha de 3 figurinhas (gerada pelo professor);
  - família:   código da família (gerado pelo professor para cada aluno).

LGPD (critérios P10.2 e P10.6): só apelido fictício e necessidades de aprendizagem. Nenhum diagnóstico,
nenhum nome real, nenhum dado de saúde.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import os
import re
import secrets
import sqlite3
import time
from contextlib import contextmanager
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
# PRISMA_BANCO permite um banco separado (testes, demonstração)
# PRISMA_DADOS: pasta de dados (na nuvem, o volume persistente; ex.: /data)
BANCO = Path(os.environ.get("PRISMA_BANCO")
             or (Path(os.environ["PRISMA_DADOS"]) / "prisma.db" if os.environ.get("PRISMA_DADOS") else RAIZ / "dados" / "prisma.db"))

FIGURAS = ["coracao", "sol", "lua", "raio", "trofeu", "livro", "lampada", "carinha", "casa"]
PALAVRAS_TURMA = ["SOL", "LUA", "MAR", "RIO", "IPE", "ARARA", "ONCA", "CAJU", "PITANGA", "SABIA", "TUCANO", "BOTO"]
ALFABETO = "ABCDEFGHJKMNPQRSTUVWXYZ23456789"     # sem 0/O, 1/I/L: fáceis de confundir

# Lista fechada de necessidades (P10.2: nada de diagnóstico). As chaves batem com o pipeline.
NECESSIDADES = {
    "baixa_visao": "Letras grandes e alto contraste",
    "daltonismo": "Cor sempre com símbolo",
    "instrucoes_em_etapas": "Instruções em etapas",
    "leitura_facil": "Texto mais direto",
}
PREFERENCIAS = {"audio": "Ouvir o material"}

SESSAO_CURTA = 12 * 3600          # sem "lembrar de mim"
SESSAO_LONGA = 30 * 24 * 3600     # com "lembrar de mim"
MAX_FALHAS = 8                    # tentativas erradas por janela, por IP e por alvo
JANELA_FALHAS = 15 * 60


class ErroConta(Exception):
    """Erro com mensagem para a pessoa e o campo do formulário a destacar."""

    def __init__(self, texto: str, campo: str = "", status: int = 400):
        super().__init__(texto)
        self.texto, self.campo, self.status = texto, campo, status


# ---------- banco ----------

ESQUEMA = """
CREATE TABLE IF NOT EXISTS professores (
  id INTEGER PRIMARY KEY, nome TEXT NOT NULL, email TEXT NOT NULL UNIQUE,
  senha TEXT NOT NULL, criado REAL NOT NULL);
CREATE TABLE IF NOT EXISTS turmas (
  id INTEGER PRIMARY KEY, nome TEXT NOT NULL, codigo TEXT NOT NULL UNIQUE,
  professor_id INTEGER NOT NULL REFERENCES professores(id), criado REAL NOT NULL);
CREATE TABLE IF NOT EXISTS alunos (
  id INTEGER PRIMARY KEY, apelido TEXT NOT NULL, turma_id INTEGER NOT NULL REFERENCES turmas(id),
  figuras TEXT NOT NULL, codigo_familia TEXT NOT NULL UNIQUE,
  necessidades TEXT NOT NULL DEFAULT '[]', preferencias TEXT NOT NULL DEFAULT '[]', criado REAL NOT NULL,
  UNIQUE (turma_id, figuras));
CREATE TABLE IF NOT EXISTS sessoes (
  token_hash TEXT PRIMARY KEY, perfil TEXT NOT NULL, ref_id INTEGER NOT NULL, expira REAL NOT NULL);
CREATE TABLE IF NOT EXISTS falhas (chave TEXT NOT NULL, quando REAL NOT NULL);
CREATE TABLE IF NOT EXISTS escolas (
  id INTEGER PRIMARY KEY, nome TEXT NOT NULL, email TEXT NOT NULL UNIQUE, senha TEXT NOT NULL,
  codigo_hash TEXT NOT NULL UNIQUE, criado REAL NOT NULL);
CREATE TABLE IF NOT EXISTS avaliacoes (
  aluno_id INTEGER NOT NULL REFERENCES alunos(id) ON DELETE CASCADE, material_id TEXT NOT NULL,
  estrelas INTEGER, sugestao TEXT NOT NULL DEFAULT '', pulou INTEGER NOT NULL DEFAULT 0, quando REAL NOT NULL,
  PRIMARY KEY (aluno_id, material_id));
CREATE TABLE IF NOT EXISTS ocultos (
  aluno_id INTEGER NOT NULL REFERENCES alunos(id) ON DELETE CASCADE, material_id TEXT NOT NULL, quando REAL NOT NULL,
  PRIMARY KEY (aluno_id, material_id));
"""


def _migrar(con) -> None:
    """Bancos criados antes das escolas: o professor ganha a coluna escola_id (vazia = código do .env)."""
    colunas = {r["name"] for r in con.execute("PRAGMA table_info(professores)")}
    if "escola_id" not in colunas:
        con.execute("ALTER TABLE professores ADD COLUMN escola_id INTEGER REFERENCES escolas(id)")


@contextmanager
def conexao():
    BANCO.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(BANCO)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys = ON")
    try:
        con.executescript(ESQUEMA)
        _migrar(con)
        yield con
        con.commit()
    except ErroConta:
        con.commit()          # guarda a tentativa errada registrada antes do erro
        raise
    finally:
        con.close()


# ---------- senhas e códigos ----------

def _hash_senha(senha: str, sal: bytes | None = None) -> str:
    sal = sal or secrets.token_bytes(16)
    h = hashlib.scrypt(senha.encode("utf-8"), salt=sal, n=2 ** 14, r=8, p=1, dklen=32)
    return sal.hex() + "$" + h.hex()


def _confere_senha(senha: str, guardada: str) -> bool:
    sal, _ = guardada.split("$", 1)
    return hmac.compare_digest(_hash_senha(senha, bytes.fromhex(sal)), guardada)


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def _codigo(n: int) -> str:
    return "".join(secrets.choice(ALFABETO) for _ in range(n))


def normalizar_codigo(texto: str) -> str:
    return re.sub(r"[^A-Z0-9]", "", (texto or "").upper())


def _hash_codigo(codigo: str) -> str:
    """O código da escola fica guardado só como impressão digital (quem lê o banco não descobre o código)."""
    return hashlib.sha256(("prisma-escola:" + normalizar_codigo(codigo)).encode()).hexdigest()


def codigo_escola() -> str:
    """Lido do ambiente ou de backend/.env. Vazio = cadastro de professor fechado."""
    from . import ia
    return os.environ.get("PRISMA_CODIGO_ESCOLA") or ia._env().get("PRISMA_CODIGO_ESCOLA", "")


# ---------- limite de tentativas ----------

def _limitar(con, chave: str) -> None:
    agora = time.time()
    con.execute("DELETE FROM falhas WHERE quando < ?", (agora - JANELA_FALHAS,))
    n = con.execute("SELECT COUNT(*) FROM falhas WHERE chave = ?", (chave,)).fetchone()[0]
    if n >= MAX_FALHAS:
        raise ErroConta("Muitas tentativas erradas. Espere 15 minutos e tente de novo.", status=429)


def _falhou(con, chave: str) -> None:
    con.execute("INSERT INTO falhas (chave, quando) VALUES (?, ?)", (chave, time.time()))


# ---------- sessões ----------

def _abrir_sessao(con, perfil: str, ref_id: int, lembrar: bool) -> tuple[str, int]:
    token = secrets.token_urlsafe(32)
    duracao = SESSAO_LONGA if lembrar else SESSAO_CURTA
    con.execute("INSERT INTO sessoes VALUES (?, ?, ?, ?)", (_hash_token(token), perfil, ref_id, time.time() + duracao))
    return token, duracao


def sessao(token: str | None) -> dict | None:
    """Quem é o dono do token, ou None. Devolve {perfil, id, nome, ...}."""
    if not token:
        return None
    with conexao() as con:
        con.execute("DELETE FROM sessoes WHERE expira < ?", (time.time(),))
        s = con.execute("SELECT * FROM sessoes WHERE token_hash = ?", (_hash_token(token),)).fetchone()
        if not s:
            return None
        if s["perfil"] == "escola":
            e = con.execute("SELECT id, nome, email FROM escolas WHERE id = ?", (s["ref_id"],)).fetchone()
            return e and {"perfil": "escola", "id": e["id"], "nome": e["nome"], "email": e["email"]}
        if s["perfil"] == "professor":
            p = con.execute("""SELECT p.id, p.nome, p.email, p.escola_id, e.nome AS escola FROM professores p
                               LEFT JOIN escolas e ON e.id = p.escola_id WHERE p.id = ?""", (s["ref_id"],)).fetchone()
            return p and {"perfil": "professor", "id": p["id"], "nome": p["nome"], "email": p["email"],
                          "escola_id": p["escola_id"], "escola": p["escola"]}
        a = con.execute("""SELECT a.*, t.nome AS turma_nome, t.codigo AS turma_codigo
                           FROM alunos a JOIN turmas t ON t.id = a.turma_id WHERE a.id = ?""", (s["ref_id"],)).fetchone()
        if not a:
            return None
        base = {"aluno_id": a["id"], "turma_id": a["turma_id"], "turma": a["turma_nome"],
                "necessidades": json.loads(a["necessidades"]), "preferencias": json.loads(a["preferencias"])}
        if s["perfil"] == "aluno":
            return {"perfil": "aluno", "id": a["id"], "nome": a["apelido"], **base}
        return {"perfil": "familia", "id": a["id"], "nome": "Família de " + a["apelido"], "apelido": a["apelido"], **base}


def sair(token: str | None) -> None:
    if token:
        with conexao() as con:
            con.execute("DELETE FROM sessoes WHERE token_hash = ?", (_hash_token(token),))


# ---------- professor ----------

EMAIL_VALIDO = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")


def criar_professor(nome: str, email: str, senha: str, codigo: str, ip: str, lembrar: bool = False):
    nome, email = (nome or "").strip(), (email or "").strip().lower()
    esperado = codigo_escola()
    with conexao() as con:
        _limitar(con, f"escola:{ip}")
        escolas = con.execute("SELECT COUNT(*) FROM escolas").fetchone()[0]
        if not esperado and not escolas:
            raise ErroConta("O cadastro de professores está fechado: nenhuma escola foi cadastrada ainda.", "codigo_escola", 403)
        escola = con.execute("SELECT id, nome FROM escolas WHERE codigo_hash = ?", (_hash_codigo(codigo),)).fetchone() \
            if normalizar_codigo(codigo) else None
        legado = bool(esperado) and hmac.compare_digest(normalizar_codigo(codigo), normalizar_codigo(esperado))
        if not escola and not legado:
            _falhou(con, f"escola:{ip}")
            raise ErroConta("Código da escola errado. Peça o código à coordenação.", "codigo_escola", 403)
        if len(nome) < 2:
            raise ErroConta("Digite o seu nome.", "nome")
        if not EMAIL_VALIDO.match(email):
            raise ErroConta("Digite um e-mail válido, como nome@escola.br.", "email_novo")
        if len(senha or "") < 8:
            raise ErroConta("A senha precisa ter pelo menos 8 caracteres.", "senha_nova")
        if _email_usado(con, email):
            raise ErroConta("Já existe uma conta com esse e-mail. Use Entrar.", "email_novo", 409)
        cur = con.execute("INSERT INTO professores (nome, email, senha, criado, escola_id) VALUES (?, ?, ?, ?, ?)",
                          (nome, email, _hash_senha(senha), time.time(), escola["id"] if escola else None))
        token, duracao = _abrir_sessao(con, "professor", cur.lastrowid, lembrar)
    return token, duracao, {"perfil": "professor", "nome": nome}


def _email_usado(con, email: str) -> bool:
    """Um e-mail serve para uma conta só (de escola ou de professor): o login não precisa adivinhar o perfil."""
    return bool(con.execute("SELECT 1 FROM professores WHERE email = ? UNION SELECT 1 FROM escolas WHERE email = ?",
                            (email, email)).fetchone())


# ---------- escola ----------

def criar_escola(nome: str, email: str, senha: str, codigo: str, ip: str, lembrar: bool = False):
    """A escola escolhe o código que vai passar aos professores. Ele é diferente da senha do painel."""
    nome, email, cod = (nome or "").strip(), (email or "").strip().lower(), normalizar_codigo(codigo)
    with conexao() as con:
        _limitar(con, f"nova-escola:{ip}")
        if not 3 <= len(nome) <= 120:
            raise ErroConta("Digite o nome da escola.", "escola_nome")
        if not EMAIL_VALIDO.match(email):
            raise ErroConta("Digite um e-mail válido, como coordenacao@escola.br.", "escola_email")
        if len(senha or "") < 8:
            raise ErroConta("A senha precisa ter pelo menos 8 caracteres.", "escola_senha")
        if len(cod) < 6:
            raise ErroConta("O código para os professores precisa ter pelo menos 6 letras ou números.", "escola_codigo")
        if cod == normalizar_codigo(senha):
            raise ErroConta("Use um código diferente da senha: o código vai para os professores.", "escola_codigo")
        if _email_usado(con, email):
            _falhou(con, f"nova-escola:{ip}")
            raise ErroConta("Já existe uma conta com esse e-mail. Use Entrar.", "escola_email", 409)
        legado = codigo_escola()
        if con.execute("SELECT 1 FROM escolas WHERE codigo_hash = ?", (_hash_codigo(cod),)).fetchone() \
                or (legado and cod == normalizar_codigo(legado)):
            _falhou(con, f"nova-escola:{ip}")
            raise ErroConta("Esse código já está em uso. Escolha outro.", "escola_codigo", 409)
        cur = con.execute("INSERT INTO escolas (nome, email, senha, codigo_hash, criado) VALUES (?, ?, ?, ?, ?)",
                          (nome, email, _hash_senha(senha), _hash_codigo(cod), time.time()))
        token, duracao = _abrir_sessao(con, "escola", cur.lastrowid, lembrar)
    return token, duracao, {"perfil": "escola", "nome": nome}


def entrar_escola(email: str, senha: str, ip: str, lembrar: bool = False):
    email = (email or "").strip().lower()
    with conexao() as con:
        _limitar(con, f"escola-login:{ip}")
        e = con.execute("SELECT * FROM escolas WHERE email = ?", (email,)).fetchone()
        if not e or not _confere_senha(senha or "", e["senha"]):
            _falhou(con, f"escola-login:{ip}")
            raise ErroConta("E-mail ou senha não conferem.", "senha", 401)
        token, duracao = _abrir_sessao(con, "escola", e["id"], lembrar)
    return token, duracao, {"perfil": "escola", "nome": e["nome"]}


def resumo_da_escola(escola_id: int) -> dict:
    """O que a escola vê: professores, turmas e alunos (apelidos fictícios). Os materiais vêm da API."""
    with conexao() as con:
        profs = []
        for p in con.execute("SELECT id, nome, email FROM professores WHERE escola_id = ? ORDER BY nome", (escola_id,)):
            turmas = []
            for t in con.execute("SELECT id, nome FROM turmas WHERE professor_id = ? ORDER BY criado", (p["id"],)):
                alunos = [a["apelido"] for a in con.execute("SELECT apelido FROM alunos WHERE turma_id = ? ORDER BY criado", (t["id"],))]
                turmas.append({"id": t["id"], "nome": t["nome"], "alunos": alunos})
            profs.append({"id": p["id"], "nome": p["nome"], "email": p["email"], "turmas": turmas})
        return {"professores": profs}


def ha_escolas() -> bool:
    with conexao() as con:
        return bool(con.execute("SELECT 1 FROM escolas LIMIT 1").fetchone())


def professores_da_escola(escola_id: int) -> dict[int, str]:
    with conexao() as con:
        return {r["id"]: r["nome"] for r in con.execute("SELECT id, nome FROM professores WHERE escola_id = ?", (escola_id,))}


def entrar_professor(email: str, senha: str, ip: str, lembrar: bool = False):
    email = (email or "").strip().lower()
    with conexao() as con:
        _limitar(con, f"prof:{ip}")
        p = con.execute("SELECT * FROM professores WHERE email = ?", (email,)).fetchone()
        if not p or not _confere_senha(senha or "", p["senha"]):
            _falhou(con, f"prof:{ip}")
            raise ErroConta("E-mail ou senha não conferem.", "senha", 401)
        token, duracao = _abrir_sessao(con, "professor", p["id"], lembrar)
    return token, duracao, {"perfil": "professor", "nome": p["nome"]}


# ---------- aluno e família ----------

def entrar_aluno(codigo_turma: str, figuras: list[str], ip: str, lembrar: bool = False):
    cod = normalizar_codigo(codigo_turma)
    with conexao() as con:
        _limitar(con, f"turma:{cod}:{ip}")
        _limitar(con, f"turma:{cod}")           # também por turma, de qualquer lugar (senha curta)
        t = con.execute("SELECT id FROM turmas WHERE REPLACE(codigo, '-', '') = ?", (cod,)).fetchone()
        if not t:
            _falhou(con, f"turma:{cod}:{ip}")
            raise ErroConta("Não achei essa turma. Confira o código no cartão.", "turma", 401)
        a = con.execute("SELECT * FROM alunos WHERE turma_id = ? AND figuras = ?",
                        (t["id"], ",".join(figuras or []))).fetchone()
        if not a:
            _falhou(con, f"turma:{cod}:{ip}")
            _falhou(con, f"turma:{cod}")
            raise ErroConta("As figurinhas não conferem. Tente de novo, na ordem do cartão.", "figuras", 401)
        token, duracao = _abrir_sessao(con, "aluno", a["id"], lembrar)
    return token, duracao, {"perfil": "aluno", "nome": a["apelido"]}


def entrar_familia(codigo: str, ip: str, lembrar: bool = False):
    cod = normalizar_codigo(codigo)
    with conexao() as con:
        _limitar(con, f"familia:{ip}")
        a = con.execute("SELECT * FROM alunos WHERE REPLACE(codigo_familia, '-', '') = ?", (cod,)).fetchone()
        if not a:
            _falhou(con, f"familia:{ip}")
            raise ErroConta("Código não encontrado. Confira o bilhete da escola.", "codigo", 401)
        token, duracao = _abrir_sessao(con, "familia", a["id"], lembrar)
    return token, duracao, {"perfil": "familia", "nome": "Família de " + a["apelido"]}


# ---------- turmas e alunos (só o professor dono) ----------

def _turma_do_professor(con, turma_id: int, professor_id: int):
    t = con.execute("SELECT * FROM turmas WHERE id = ? AND professor_id = ?", (turma_id, professor_id)).fetchone()
    if not t:
        raise ErroConta("Turma não encontrada.", status=404)
    return t


def criar_turma(professor_id: int, nome: str) -> dict:
    nome = (nome or "").strip()
    if not 2 <= len(nome) <= 60:
        raise ErroConta("Dê um nome à turma, como 5º ano A.", "nome_turma")
    with conexao() as con:
        for _ in range(50):
            codigo = f"{secrets.choice(PALAVRAS_TURMA)}-{secrets.randbelow(9000) + 1000}"
            if not con.execute("SELECT 1 FROM turmas WHERE codigo = ?", (codigo,)).fetchone():
                break
        cur = con.execute("INSERT INTO turmas (nome, codigo, professor_id, criado) VALUES (?, ?, ?, ?)",
                          (nome, codigo, professor_id, time.time()))
        return {"id": cur.lastrowid, "nome": nome, "codigo": codigo, "alunos": []}


def _validar_lista(itens, permitidos: dict, campo: str) -> list[str]:
    itens = list(dict.fromkeys(itens or []))
    if any(i not in permitidos for i in itens):
        raise ErroConta("Escolha só opções da lista.", campo)
    return itens


def criar_aluno(professor_id: int, turma_id: int, apelido: str, necessidades, preferencias) -> dict:
    apelido = (apelido or "").strip()
    if not 2 <= len(apelido) <= 30:
        raise ErroConta("Dê um apelido fictício ao aluno, como Aluno A.", "apelido")
    nec = _validar_lista(necessidades, NECESSIDADES, "necessidades")
    pref = _validar_lista(preferencias, PREFERENCIAS, "preferencias")
    with conexao() as con:
        _turma_do_professor(con, turma_id, professor_id)
        usadas = {r["figuras"] for r in con.execute("SELECT figuras FROM alunos WHERE turma_id = ?", (turma_id,))}
        livres = [f"{a},{b},{c}" for a in FIGURAS for b in FIGURAS for c in FIGURAS
                  if len({a, b, c}) == 3 and f"{a},{b},{c}" not in usadas]
        if not livres:
            raise ErroConta("Esta turma já tem o máximo de alunos.", "apelido")
        figuras = secrets.choice(livres)
        while True:
            codigo = f"{_codigo(4)}-{_codigo(4)}"
            if not con.execute("SELECT 1 FROM alunos WHERE codigo_familia = ?", (codigo,)).fetchone():
                break
        cur = con.execute("""INSERT INTO alunos (apelido, turma_id, figuras, codigo_familia, necessidades, preferencias, criado)
                             VALUES (?, ?, ?, ?, ?, ?, ?)""",
                          (apelido, turma_id, figuras, codigo, json.dumps(nec), json.dumps(pref), time.time()))
        return _aluno_dict(con.execute("SELECT * FROM alunos WHERE id = ?", (cur.lastrowid,)).fetchone())


def atualizar_aluno(professor_id: int, aluno_id: int, necessidades, preferencias) -> dict:
    nec = _validar_lista(necessidades, NECESSIDADES, "necessidades")
    pref = _validar_lista(preferencias, PREFERENCIAS, "preferencias")
    with conexao() as con:
        a = con.execute("SELECT * FROM alunos WHERE id = ?", (aluno_id,)).fetchone()
        if not a:
            raise ErroConta("Aluno não encontrado.", status=404)
        _turma_do_professor(con, a["turma_id"], professor_id)
        con.execute("UPDATE alunos SET necessidades = ?, preferencias = ? WHERE id = ?",
                    (json.dumps(nec), json.dumps(pref), aluno_id))
        return _aluno_dict(con.execute("SELECT * FROM alunos WHERE id = ?", (aluno_id,)).fetchone())


def remover_aluno(professor_id: int, aluno_id: int) -> None:
    with conexao() as con:
        a = con.execute("SELECT * FROM alunos WHERE id = ?", (aluno_id,)).fetchone()
        if not a:
            raise ErroConta("Aluno não encontrado.", status=404)
        _turma_do_professor(con, a["turma_id"], professor_id)
        con.execute("DELETE FROM sessoes WHERE perfil IN ('aluno', 'familia') AND ref_id = ?", (aluno_id,))
        con.execute("DELETE FROM alunos WHERE id = ?", (aluno_id,))


def _aluno_dict(a) -> dict:
    return {"id": a["id"], "apelido": a["apelido"], "figuras": a["figuras"].split(","),
            "codigo_familia": a["codigo_familia"], "necessidades": json.loads(a["necessidades"]),
            "preferencias": json.loads(a["preferencias"])}


def turmas_do_professor(professor_id: int) -> list[dict]:
    with conexao() as con:
        saida = []
        for t in con.execute("SELECT * FROM turmas WHERE professor_id = ? ORDER BY criado", (professor_id,)):
            alunos = [_aluno_dict(a) for a in con.execute("SELECT * FROM alunos WHERE turma_id = ? ORDER BY criado", (t["id"],))]
            saida.append({"id": t["id"], "nome": t["nome"], "codigo": t["codigo"], "alunos": alunos})
        return saida


def perfil_da_turma(professor_id: int, turma_id: int) -> dict:
    """União das necessidades da turma: o material sai com todas as versões que alguém da turma precisa."""
    with conexao() as con:
        t = _turma_do_professor(con, turma_id, professor_id)
        nec, pref = [], []
        for a in con.execute("SELECT necessidades, preferencias FROM alunos WHERE turma_id = ?", (turma_id,)):
            nec += json.loads(a["necessidades"])
            pref += json.loads(a["preferencias"])
        return {"turma": t["nome"], "necessidades": sorted(set(nec)), "preferencias": sorted(set(pref))}


# ---------- avaliação do material (aluno) e feedbacks (professor) ----------

MAX_PALAVRAS_SUGESTAO = 150


def avaliar(aluno_id: int, material_id: str, estrelas, sugestao: str, pular: bool) -> dict:
    """O aluno dá de 1 a 5 estrelas e/ou uma sugestão (as duas são opcionais) ou pula a avaliação."""
    sugestao = re.sub(r"\s+", " ", (sugestao or "")).strip()
    if pular:
        estrelas, sugestao = None, ""
    else:
        if estrelas is not None and (not isinstance(estrelas, int) or not 1 <= estrelas <= 5):
            raise ErroConta("Escolha de 1 a 5 estrelas.", "estrelas")
        if len(sugestao.split()) > MAX_PALAVRAS_SUGESTAO or len(sugestao) > 1500:
            raise ErroConta(f"A sugestão pode ter até {MAX_PALAVRAS_SUGESTAO} palavras.", "sugestao")
        if estrelas is None and not sugestao:
            raise ErroConta("Escolha as estrelas, escreva uma sugestão ou pule a avaliação.", "estrelas")
    with conexao() as con:
        con.execute("""INSERT INTO avaliacoes (aluno_id, material_id, estrelas, sugestao, pulou, quando) VALUES (?, ?, ?, ?, ?, ?)
                       ON CONFLICT (aluno_id, material_id) DO UPDATE SET estrelas = excluded.estrelas,
                       sugestao = excluded.sugestao, pulou = excluded.pulou, quando = excluded.quando""",
                    (aluno_id, material_id, estrelas, sugestao, 1 if pular else 0, time.time()))
    return {"estrelas": estrelas, "sugestao": sugestao, "pulou": bool(pular)}


def avaliacoes_do_aluno(aluno_id: int) -> dict[str, dict]:
    with conexao() as con:
        return {r["material_id"]: {"estrelas": r["estrelas"], "sugestao": r["sugestao"], "pulou": bool(r["pulou"])}
                for r in con.execute("SELECT * FROM avaliacoes WHERE aluno_id = ?", (aluno_id,))}


def avaliacoes_do_material(material_id: str) -> list[dict]:
    """Para o professor: nome (apelido) de quem avaliou, estrelas e sugestão. Quem pulou não aparece."""
    with conexao() as con:
        return [{"aluno": r["apelido"], "estrelas": r["estrelas"], "sugestao": r["sugestao"], "quando": r["quando"]}
                for r in con.execute("""SELECT a.apelido, v.* FROM avaliacoes v JOIN alunos a ON a.id = v.aluno_id
                                        WHERE v.material_id = ? AND v.pulou = 0 ORDER BY v.quando DESC""", (material_id,))]


def apagar_avaliacoes(material_id: str) -> None:
    with conexao() as con:
        con.execute("DELETE FROM avaliacoes WHERE material_id = ?", (material_id,))
        con.execute("DELETE FROM ocultos WHERE material_id = ?", (material_id,))


# ---------- família: tirar um material só do painel do próprio aluno ----------

def ocultar(aluno_id: int, material_id: str, sim: bool = True) -> None:
    with conexao() as con:
        if sim:
            con.execute("INSERT OR IGNORE INTO ocultos (aluno_id, material_id, quando) VALUES (?, ?, ?)",
                        (aluno_id, material_id, time.time()))
        else:
            con.execute("DELETE FROM ocultos WHERE aluno_id = ? AND material_id = ?", (aluno_id, material_id))


def ocultos_do_aluno(aluno_id: int) -> set[str]:
    with conexao() as con:
        return {r["material_id"] for r in con.execute("SELECT material_id FROM ocultos WHERE aluno_id = ?", (aluno_id,))}
