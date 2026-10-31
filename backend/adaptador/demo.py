"""Contas de demonstração: uma escola, uma professora, uma turma e 3 alunos fictícios, prontos para a apresentação.

Criadas uma vez (o publicar.bat chama `python -m adaptador.demo`) e guardadas em backend/dados/demo.json,
que fica fora do Git. As senhas são sorteadas em cada computador: nunca vão para o GitHub nem para o chat.
A página compartilhar.html mostra estes acessos só para quem está no próprio computador do PRISMA.
"""
from __future__ import annotations

import json
import secrets
import sys
import threading
import time
from pathlib import Path

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


def abrir_sessao(perfil: str, aluno: int = 0) -> tuple[str, int, dict]:
    """Entra numa conta de demonstração sem senha e sem o limite de tentativas
    (alguém errando a senha da turma de propósito não pode trancar a demonstração da banca)."""
    garantir()
    pid = _professor_id()
    with contas.conexao() as con:
        if perfil == "professor":
            token, duracao = contas._abrir_sessao(con, "professor", pid, False)
            return token, duracao, {"perfil": "professor", "nome": "Professora Demonstração"}
        if perfil == "escola":
            e = con.execute("SELECT id, nome FROM escolas WHERE email = ?", (EMAIL_ESCOLA,)).fetchone()
            token, duracao = contas._abrir_sessao(con, "escola", e["id"], False)
            return token, duracao, {"perfil": "escola", "nome": e["nome"]}
        alunos = con.execute("""SELECT a.id, a.apelido FROM alunos a JOIN turmas t ON t.id = a.turma_id
                                WHERE t.professor_id = ? ORDER BY a.criado""", (pid,)).fetchall()
        a = alunos[max(0, min(aluno, len(alunos) - 1))]
        if perfil == "aluno":
            token, duracao = contas._abrir_sessao(con, "aluno", a["id"], False)
            return token, duracao, {"perfil": "aluno", "nome": a["apelido"]}
        token, duracao = contas._abrir_sessao(con, "familia", a["id"], False)
        return token, duracao, {"perfil": "familia", "nome": "Família de " + a["apelido"]}


def turma_crua() -> dict:
    """A turma de demonstração com os nomes internos das figurinhas (para entrar como aluno)."""
    garantir()
    return contas.turmas_do_professor(_professor_id())[0]


# ---------- materiais de teste já publicados no site público ----------

MATERIAIS = Path(__file__).resolve().parents[2] / "materiais-teste"
EXTENSOES = {".pdf", ".wav", ".mp4"}
# descrição escrita pelo time (o desenho é nosso): o material publica mesmo se a IA estiver ocupada
DESCRICOES = {
    "2-imagem-cores.pdf": "Desenho do ciclo da água. À esquerda, o Sol laranja e o mar azul. Do mar saem três setas "
                          "vermelhas que sobem até a nuvem: é a evaporação. De duas árvores, à direita, saem setas "
                          "verdes até a nuvem: é a transpiração. Da nuvem caem gotas azuis: é a chuva. A legenda diz: "
                          "vermelho, evaporação; verde, transpiração; azul, chuva.",
}
# nome que a turma vê (o título de áudio e vídeo vem do nome do arquivo)
NOMES = {"3-audio-aula.wav": "Aula falada sobre o ciclo da água.wav",
         "4-video-aula.mp4": "Vídeo sobre o ciclo da água.mp4"}
_trava = threading.Lock()


def _registro() -> dict:
    return (_ler() or {}).get("materiais", {})


def _guardar_registro(reg: dict) -> None:
    d = _ler() or {}
    d["materiais"] = reg
    ARQUIVO.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")


def _publicar_um(arquivo: Path, tentativa: int) -> str | None:
    """Cria, descreve e publica um material de teste. Devolve o id publicado (ou None: tentar depois)."""
    from . import api
    garantir()
    pid = _professor_id()
    turma = contas.turmas_do_professor(pid)[0]
    perfil = contas.perfil_da_turma(pid, turma["id"])
    perfil_final = {"necessidades": perfil["necessidades"], "preferencias": perfil["preferencias"]}
    nome = NOMES.get(arquivo.name, arquivo.name)
    with arquivo.open("rb") as f:
        m = api.criar_material(pid, turma["id"], perfil, perfil_final, nome, f)
    pasta = api.SAIDA / m["id"]
    faltou_ia = [v for v in m["versoes"].values() if v["status"] in ("falhou", "pendente_ia")]
    if faltou_ia and tentativa < 8:            # IA ocupada: tenta de novo mais tarde (o que deu certo fica guardado)
        api.shutil.rmtree(pasta, ignore_errors=True)
        api.shutil.rmtree(api.ENVIOS / m["id"], ignore_errors=True)
        return None
    texto = DESCRICOES.get(arquivo.name)
    sem = [i["arquivo"] for i in m.get("imagens", []) if not i["alt"] or i["origem"] == "ia"]
    if texto and sem:
        descricoes = {k: texto for k in sem}
        api._gravar(pasta, "descricoes.json", descricoes)
        estado = api._ler(pasta, "estado.json")
        api._processar(m["id"], api.ENVIOS / estado["envio"], estado.get("perfil"), descricoes)
    revisao = api._ler(pasta, "revisao.json")
    if not revisao["pode_publicar"]:
        return None
    estado = api._ler(pasta, "estado.json")
    estado.update(estado="publicado", publicado=api.datetime.now(api.timezone.utc).isoformat(timespec="seconds"))
    api._gravar(pasta, "estado.json", estado)
    return m["id"]


def semear() -> None:
    """Publica os materiais de teste para a turma de demonstração, com paciência (a IA gratuita pode estar ocupada)."""
    if not MATERIAIS.exists():
        return
    with _trava:
        for rodada in range(12):
            reg = _registro()
            from . import api
            pendentes = [a for a in sorted(MATERIAIS.iterdir())
                         if a.suffix.lower() in EXTENSOES and not (reg.get(a.name) and (api.SAIDA / reg[a.name]).exists())]
            if not pendentes:
                return
            for arquivo in pendentes:
                try:
                    novo = _publicar_um(arquivo, rodada)
                    if novo:
                        reg = _registro()
                        reg[arquivo.name] = novo
                        _guardar_registro(reg)
                        print(f"[demo] publicado: {arquivo.name}", flush=True)
                    else:
                        print(f"[demo] {arquivo.name}: IA ocupada, tento de novo depois", flush=True)
                except Exception as erro:          # nunca derruba o site
                    print(f"[demo] {arquivo.name}: {erro}", flush=True)
            time.sleep(90)


def semear_em_segundo_plano() -> None:
    threading.Thread(target=semear, name="prisma-demo", daemon=True).start()


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
