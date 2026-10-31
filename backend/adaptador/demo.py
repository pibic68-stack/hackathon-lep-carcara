"""Contas de demonstração: uma escola, uma professora, uma turma e 3 alunos fictícios, prontos para a apresentação.

Criadas uma vez (o publicar.bat chama `python -m adaptador.demo`) e guardadas em backend/dados/demo.json,
que fica fora do Git. As senhas são sorteadas em cada computador: nunca vão para o GitHub nem para o chat.
A página compartilhar.html mostra estes acessos só para quem está no próprio computador do PRISMA.
"""
from __future__ import annotations

import json
import secrets
import sys

from . import contas

ARQUIVO = contas.BANCO.parent / "demo.json"
EMAIL_ESCOLA = "coordenacao@demo.prisma.br"
EMAIL_PROF = "professora@demo.prisma.br"
NOMES_FIGURAS = {"coracao": "Coração", "sol": "Sol", "lua": "Lua", "raio": "Raio", "trofeu": "Troféu",
                 "livro": "Livro", "lampada": "Lâmpada", "carinha": "Carinha feliz", "casa": "Casa"}
ALUNOS = [
    ("Bia (cores)", ["daltonismo"], []),
    ("Caio (texto direto)", ["leitura_facil"], ["audio"]),
    ("Duda (letra grande)", ["baixa_visao"], []),
]


def _ler() -> dict | None:
    try:
        return json.loads(ARQUIVO.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def _professor_id() -> int | None:
    with contas.conexao() as con:
        r = con.execute("SELECT id FROM professores WHERE email = ?", (EMAIL_PROF,)).fetchone()
        return r["id"] if r else None


def garantir() -> dict:
    """Cria as contas se ainda não existem e devolve os acessos (com turma e alunos atualizados)."""
    dados = _ler()
    pid = _professor_id()
    if not dados or not pid:
        senha_escola, senha_prof = secrets.token_urlsafe(9), secrets.token_urlsafe(9)
        codigo = "DEMO-" + secrets.token_hex(3).upper()
        with contas.conexao() as con:          # recomeça limpo se sobrou algo de uma tentativa anterior
            if pid:
                con.execute("DELETE FROM alunos WHERE turma_id IN (SELECT id FROM turmas WHERE professor_id = ?)", (pid,))
                con.execute("DELETE FROM turmas WHERE professor_id = ?", (pid,))
                con.execute("DELETE FROM professores WHERE id = ?", (pid,))
            con.execute("DELETE FROM escolas WHERE email = ?", (EMAIL_ESCOLA,))
        contas.criar_escola("Escola de Demonstração PRISMA", EMAIL_ESCOLA, senha_escola, codigo, "demo")
        contas.criar_professor("Professora Demonstração", EMAIL_PROF, senha_prof, codigo, "demo")
        pid = _professor_id()
        turma = contas.criar_turma(pid, "5º ano A (demonstração)")
        for apelido, nec, pref in ALUNOS:
            contas.criar_aluno(pid, turma["id"], apelido, nec, pref)
        dados = {"escola": {"email": EMAIL_ESCOLA, "senha": senha_escola, "codigo_professores": codigo},
                 "professora": {"email": EMAIL_PROF, "senha": senha_prof}}
        ARQUIVO.parent.mkdir(parents=True, exist_ok=True)
        ARQUIVO.write_text(json.dumps(dados, ensure_ascii=False, indent=2), encoding="utf-8")
    turmas = contas.turmas_do_professor(pid)
    dados["turmas"] = [{"nome": t["nome"], "codigo": t["codigo"],
                        "alunos": [{"apelido": a["apelido"], "figuras": [NOMES_FIGURAS.get(f, f) for f in a["figuras"]],
                                    "codigo_familia": a["codigo_familia"]} for a in t["alunos"]]}
                       for t in turmas]
    return dados


def main() -> int:
    d = garantir()
    print("  Contas de demonstração (fictícias; mostradas também em compartilhar.html neste computador):")
    print(f"    Professora: {d['professora']['email']}  senha {d['professora']['senha']}")
    for t in d["turmas"]:
        print(f"    Turma {t['nome']}: código {t['codigo']}")
        for a in t["alunos"]:
            print(f"      {a['apelido']}: figurinhas {', '.join(a['figuras'])}; família {a['codigo_familia']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
