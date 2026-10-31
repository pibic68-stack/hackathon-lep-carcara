"""API HTTP do PRISMA: o mesmo servidor entrega o site (web/), a aba de instruções e a API.

Rodar (de dentro de backend/):   python -m adaptador.api      -> http://127.0.0.1:8000
Documentação interativa:         http://127.0.0.1:8000/docs

Quem pode o quê:
  - escola: cadastra-se com o código que passa aos professores; só VÊ professores, turmas, alunos e materiais;
  - professor: cria turmas e alunos fictícios, envia materiais, revisa, descreve imagens, aprova e lê os feedbacks;
  - aluno: vê os materiais PUBLICADOS da própria turma e avalia (estrelas e sugestão, as duas opcionais);
  - família: vê os mesmos materiais e pode tirar um material do painel do próprio aluno (não da turma).
Ciclo de vida (critério P10.1: nada chega ao aluno sem aprovação):
    POST /api/adaptar -> "rascunho" -> POST .../aprovar -> "publicado"
Imagem sem descrição bloqueia a aprovação (P4.1).

Segurança: sessão em cookie HttpOnly (SameSite=Lax); todo pedido que muda dados precisa do
cabeçalho "X-Prisma: 1" (impede que outro site faça pedidos em nome de quem está logado);
limite de tentativas de login e de envios por hora.
"""
from __future__ import annotations

import json
import re
import shutil
import time
import uuid
from collections import defaultdict, deque
from datetime import datetime, timezone
from pathlib import Path

from fastapi import FastAPI, Form, HTTPException, Request, Response, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from . import contas, ia, pipeline, regras
from .leitores import EXT_MIDIA, EXT_PDF, EXT_PPT, EXT_TEXTO

RAIZ = Path(__file__).resolve().parents[1]
SAIDA = RAIZ / "saida"
ENVIOS = RAIZ / "envios"
SITE = RAIZ.parent / "web"

LIMITE_BYTES = 300 * 1024 * 1024   # 300 MB (vídeos grandes devem ser comprimidos antes)
EXTENSOES = EXT_TEXTO | EXT_PDF | EXT_PPT | EXT_MIDIA
ID_VALIDO = re.compile(r"^[0-9a-f]{12}$")
COOKIE = "prisma_sessao"
ENVIOS_POR_HORA = 20               # por professor: protege a cota gratuita da IA

app = FastAPI(title="PRISMA – adaptador de material", version="0.2")
# CORS sem credenciais: outra origem até chama a API, mas nunca com o cookie de quem está logado.
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


@app.middleware("http")
async def protecoes(request: Request, chamar):
    if request.url.path.startswith("/api/") and request.method in ("POST", "PUT", "PATCH", "DELETE") \
            and request.headers.get("x-prisma") != "1":
        return JSONResponse({"detail": "Pedido recusado."}, status_code=403)
    resposta = await chamar(request)
    # o navegador sempre confere se o arquivo mudou (senão, depois de uma atualização, mostra CSS velho)
    resposta.headers.setdefault("Cache-Control", "no-cache")
    resposta.headers.setdefault("X-Content-Type-Options", "nosniff")
    resposta.headers.setdefault("Referrer-Policy", "same-origin")
    resposta.headers.setdefault("X-Frame-Options", "SAMEORIGIN")
    return resposta


@app.exception_handler(contas.ErroConta)
async def erro_conta(_: Request, erro: contas.ErroConta):
    return JSONResponse({"detail": {"erro": erro.texto, "campo": erro.campo}}, status_code=erro.status)


# ---------- quem está pedindo ----------

def _ip(request: Request) -> str:
    # atrás do túnel da Cloudflare todo pedido chega de 127.0.0.1; o IP real vem neste cabeçalho
    host = request.client.host if request.client else ""
    if host in ("127.0.0.1", "::1"):
        return request.headers.get("cf-connecting-ip", host)
    return host


def _https(request: Request) -> bool:
    return request.url.scheme == "https" or request.headers.get("x-forwarded-proto", "").lower() == "https"


def usuario(request: Request) -> dict | None:
    return contas.sessao(request.cookies.get(COOKIE))


def exigir(request: Request, *perfis: str) -> dict:
    u = usuario(request)
    if not u:
        raise HTTPException(401, "Entre na sua conta para continuar.")
    if perfis and u["perfil"] not in perfis:
        raise HTTPException(403, "Esta área não é para o seu perfil.")
    return u


def _abrir_sessao(request: Request, resposta: Response, token: str, duracao: int, lembrar: bool, info: dict) -> dict:
    resposta.set_cookie(COOKIE, token, max_age=duracao if lembrar else None, httponly=True,
                        samesite="lax", secure=_https(request), path="/")
    return {"ok": True, **info, "destino": f"painel/{info['perfil']}.html"}


# ---------- utilidades de material ----------

def _pasta(id_: str) -> Path:
    if not ID_VALIDO.match(id_):
        raise HTTPException(404, "Material não encontrado.")
    pasta = SAIDA / id_
    if not (pasta / "estado.json").exists():
        raise HTTPException(404, "Material não encontrado.")
    return pasta


def _ler(pasta: Path, nome: str) -> dict:
    return json.loads((pasta / nome).read_text(encoding="utf-8"))


def _gravar(pasta: Path, nome: str, dados: dict) -> None:
    (pasta / nome).write_text(json.dumps(dados, ensure_ascii=False, indent=2), encoding="utf-8")


def _do_professor(id_: str, prof: dict) -> Path:
    pasta = _pasta(id_)
    if _ler(pasta, "estado.json").get("professor_id") != prof["id"]:
        raise HTTPException(404, "Material não encontrado.")      # não revela que existe
    return pasta


def _resumo(id_: str, pasta: Path) -> dict:
    estado, revisao = _ler(pasta, "estado.json"), _ler(pasta, "revisao.json")
    nomes = regras.versoes(regras.carregar_manual())
    return {
        "id": id_,
        "material": revisao["material"],
        "titulo": revisao.get("titulo") or revisao["material"],
        "estado": estado["estado"],
        "criado": estado["criado"],
        "turma_id": estado.get("turma_id"),
        "turma": estado.get("turma_nome"),
        "pode_publicar": revisao["pode_publicar"],
        "versoes": {
            nome: {**v, "nome": nomes.get(nome, {}).get("nome", nome),
                   "rotulo": nomes.get(nome, {}).get("rotulo_aluno", nome),   # P5.3: jeito de estudar, nunca deficiência
                   **({"url": f"/api/previa/{id_}/{v['arquivo']}"} if "arquivo" in v else {})}
            for nome, v in revisao["versoes"].items()
        },
    }


def _detalhe(id_: str, pasta: Path) -> dict:
    revisao = _ler(pasta, "revisao.json")
    return {
        **_resumo(id_, pasta),
        "transformacoes_aplicadas": revisao["transformacoes_aplicadas"],
        "pendencias_para_o_professor": revisao["pendencias_para_o_professor"],
        "bloqueios": revisao["bloqueios"],
        # origem: "pendente" (sem descrição), "ia" (escrita pela IA, conferir), "professor" ou "original"
        "imagens": revisao.get("imagens", []),
        "imagens_sem_descricao": [i["arquivo"] for i in revisao.get("imagens", []) if not i["alt"]],
    }


def _processar(id_: str, arquivo: Path, perfil: dict | None, descricoes: dict | None) -> dict:
    try:
        return pipeline.adaptar(arquivo, perfil, SAIDA, ia.obter_provedor(),
                                descricoes=descricoes, nome_pasta=id_)
    except ia.ErroIA as erro:                  # IA fora do ar, chave recusada, limite gratuito...
        raise HTTPException(502, str(erro))
    except ValueError as erro:                 # formato não suportado
        raise HTTPException(415, str(erro))
    except RuntimeError as erro:               # biblioteca opcional não instalada
        raise HTTPException(501, str(erro))
    except Exception:                          # arquivo corrompido, protegido etc.
        raise HTTPException(422, "Não consegui ler este arquivo. Ele pode estar corrompido ou protegido por senha.")


def _servir(pasta: Path, caminho: str) -> FileResponse:
    alvo = (pasta / caminho).resolve()
    if pasta.resolve() not in alvo.parents or not alvo.is_file() or alvo.name in ("estado.json", "revisao.json", "descricoes.json"):
        raise HTTPException(404, "Arquivo não encontrado.")
    return FileResponse(alvo)


def _todos_materiais() -> list[tuple[str, Path]]:
    if not SAIDA.exists():
        return []
    return [(p.name, p) for p in SAIDA.glob("*") if ID_VALIDO.match(p.name) and (p / "estado.json").exists()]


_envios_recentes: dict[int, deque] = defaultdict(deque)


def _limitar_envios(professor_id: int) -> None:
    agora, fila = time.time(), _envios_recentes[professor_id]
    while fila and fila[0] < agora - 3600:
        fila.popleft()
    if len(fila) >= ENVIOS_POR_HORA:
        raise HTTPException(429, f"Limite de {ENVIOS_POR_HORA} materiais por hora atingido. Tente mais tarde.")
    fila.append(agora)


# ---------- rotas públicas ----------

@app.get("/api/saude")
def saude() -> dict:
    return {"ok": True, "ia_ligada": ia.configurada(), "cadastro_aberto": bool(contas.codigo_escola()) or contas.ha_escolas(),
            "formatos": sorted(EXTENSOES)}


@app.get("/api/opcoes")
def opcoes() -> dict:
    """Necessidades (lista fechada, P10.2) e figurinhas, para montar os formulários."""
    return {"necessidades": contas.NECESSIDADES, "preferencias": contas.PREFERENCIAS, "figuras": contas.FIGURAS}


# ---------- contas e sessão ----------

class NovoProfessor(BaseModel):
    nome: str
    email: str
    senha: str
    codigo_escola: str
    lembrar: bool = False


class NovaEscola(BaseModel):
    nome: str
    email: str
    senha: str
    codigo: str
    lembrar: bool = False


class Entrada(BaseModel):
    perfil: str
    email: str = ""
    senha: str = ""
    codigo: str = ""
    turma: str = ""
    figuras: list[str] = []
    lembrar: bool = False


@app.post("/api/contas/professor", status_code=201)
def cadastrar_professor(corpo: NovoProfessor, request: Request, resposta: Response) -> dict:
    token, duracao, info = contas.criar_professor(corpo.nome, corpo.email, corpo.senha, corpo.codigo_escola,
                                                  _ip(request), corpo.lembrar)
    return _abrir_sessao(request, resposta, token, duracao, corpo.lembrar, info)


@app.post("/api/contas/escola", status_code=201)
def cadastrar_escola(corpo: NovaEscola, request: Request, resposta: Response) -> dict:
    token, duracao, info = contas.criar_escola(corpo.nome, corpo.email, corpo.senha, corpo.codigo, _ip(request), corpo.lembrar)
    return _abrir_sessao(request, resposta, token, duracao, corpo.lembrar, info)


@app.post("/api/entrar")
def entrar(corpo: Entrada, request: Request, resposta: Response) -> dict:
    ip = _ip(request)
    if corpo.perfil == "professor":
        token, duracao, info = contas.entrar_professor(corpo.email, corpo.senha, ip, corpo.lembrar)
    elif corpo.perfil == "escola":
        token, duracao, info = contas.entrar_escola(corpo.email, corpo.senha, ip, corpo.lembrar)
    elif corpo.perfil == "aluno":
        token, duracao, info = contas.entrar_aluno(corpo.turma, corpo.figuras, ip, corpo.lembrar)
    elif corpo.perfil == "familia":
        token, duracao, info = contas.entrar_familia(corpo.codigo, ip, corpo.lembrar)
    else:
        raise HTTPException(400, "Perfil desconhecido.")
    return _abrir_sessao(request, resposta, token, duracao, corpo.lembrar, info)


@app.post("/api/sair")
def sair(request: Request, resposta: Response) -> dict:
    contas.sair(request.cookies.get(COOKIE))
    resposta.delete_cookie(COOKIE, path="/")
    return {"ok": True}


@app.get("/api/eu")
def eu(request: Request) -> dict:
    return exigir(request)


# ---------- turmas e alunos (professor) ----------

class NovaTurma(BaseModel):
    nome: str


class DadosAluno(BaseModel):
    apelido: str = ""
    necessidades: list[str] = []
    preferencias: list[str] = []


@app.get("/api/turmas")
def listar_turmas(request: Request) -> list[dict]:
    return contas.turmas_do_professor(exigir(request, "professor")["id"])


@app.post("/api/turmas", status_code=201)
def nova_turma(corpo: NovaTurma, request: Request) -> dict:
    return contas.criar_turma(exigir(request, "professor")["id"], corpo.nome)


@app.post("/api/turmas/{turma_id}/alunos", status_code=201)
def novo_aluno(turma_id: int, corpo: DadosAluno, request: Request) -> dict:
    prof = exigir(request, "professor")
    return contas.criar_aluno(prof["id"], turma_id, corpo.apelido, corpo.necessidades, corpo.preferencias)


@app.patch("/api/alunos/{aluno_id}")
def mudar_aluno(aluno_id: int, corpo: DadosAluno, request: Request) -> dict:
    prof = exigir(request, "professor")
    return contas.atualizar_aluno(prof["id"], aluno_id, corpo.necessidades, corpo.preferencias)


@app.delete("/api/alunos/{aluno_id}")
def apagar_aluno(aluno_id: int, request: Request) -> dict:
    contas.remover_aluno(exigir(request, "professor")["id"], aluno_id)
    return {"ok": True}


# ---------- materiais (professor) ----------

@app.post("/api/adaptar", status_code=201)
def adaptar(request: Request, arquivo: UploadFile, turma_id: int = Form(...), perfil: str | None = Form(None)) -> dict:
    """Recebe o material e a turma. As versões saem conforme as necessidades dos alunos da turma
    (mais as marcadas em `perfil`, se houver). Cria um rascunho."""
    prof = exigir(request, "professor")
    perfil_turma = contas.perfil_da_turma(prof["id"], turma_id)
    nome = Path(arquivo.filename or "material").name
    ext = Path(nome).suffix.lower()
    if ext not in EXTENSOES:
        raise HTTPException(415, f"Formato {ext or 'desconhecido'} não suportado. Use: {', '.join(sorted(EXTENSOES))}.")
    try:
        extra = json.loads(perfil) if perfil else {}
        if not isinstance(extra, dict):
            raise ValueError
    except ValueError:
        raise HTTPException(422, "O perfil precisa ser um JSON de objeto.")
    perfil_final = {
        "necessidades": sorted(set(perfil_turma["necessidades"]) | set(extra.get("necessidades") or [])),
        "preferencias": sorted(set(perfil_turma["preferencias"]) | set(extra.get("preferencias") or [])),
    }
    _limitar_envios(prof["id"])

    id_ = uuid.uuid4().hex[:12]
    pasta_envio = ENVIOS / id_
    pasta_envio.mkdir(parents=True)
    seguro = re.sub(r"[^\w.-]+", "-", Path(nome).stem, flags=re.UNICODE).strip("-") or "material"
    caminho = pasta_envio / f"{seguro}{ext}"

    total = 0
    with caminho.open("wb") as saida:
        while bloco := arquivo.file.read(1024 * 1024):
            total += len(bloco)
            if total > LIMITE_BYTES:
                saida.close()
                shutil.rmtree(pasta_envio, ignore_errors=True)
                raise HTTPException(413, f"Arquivo maior que {LIMITE_BYTES // (1024 * 1024)} MB.")
            saida.write(bloco)

    try:
        _processar(id_, caminho, perfil_final, None)
    except HTTPException:
        shutil.rmtree(pasta_envio, ignore_errors=True)
        shutil.rmtree(SAIDA / id_, ignore_errors=True)
        raise
    pasta = SAIDA / id_
    _gravar(pasta, "estado.json", {
        "estado": "rascunho", "criado": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "envio": f"{id_}/{caminho.name}", "perfil": perfil_final,
        "professor_id": prof["id"], "turma_id": turma_id, "turma_nome": perfil_turma["turma"],
    })
    return _detalhe(id_, pasta)


@app.get("/api/materiais")
def listar_materiais(request: Request) -> list[dict]:
    """Visão do professor: os próprios materiais, mais recentes primeiro."""
    prof = exigir(request, "professor")
    itens = [_resumo(i, p) for i, p in _todos_materiais() if _ler(p, "estado.json").get("professor_id") == prof["id"]]
    return sorted(itens, key=lambda i: i["criado"], reverse=True)


@app.get("/api/materiais/{id_}")
def ver_material(id_: str, request: Request) -> dict:
    return _detalhe(id_, _do_professor(id_, exigir(request, "professor")))


@app.delete("/api/materiais/{id_}")
def apagar_material(id_: str, request: Request) -> dict:
    pasta = _do_professor(id_, exigir(request, "professor"))
    shutil.rmtree(pasta, ignore_errors=True)
    shutil.rmtree(ENVIOS / id_, ignore_errors=True)
    contas.apagar_avaliacoes(id_)
    return {"ok": True}


class Descricoes(BaseModel):
    imagens: dict[str, str]   # {"imagens/img-001.png": "Texto alternativo"}


@app.post("/api/materiais/{id_}/descricoes")
def escrever_descricoes(id_: str, corpo: Descricoes, request: Request) -> dict:
    """O professor escreve (ou corrige) as descrições das imagens; as versões são geradas de novo."""
    pasta = _do_professor(id_, exigir(request, "professor"))
    estado = _ler(pasta, "estado.json")
    if estado["estado"] == "publicado":
        raise HTTPException(409, "Material já publicado. Envie de novo para alterar.")
    anteriores = _ler(pasta, "descricoes.json") if (pasta / "descricoes.json").exists() else {}
    todas = {**anteriores, **{k: v.strip()[:1000] for k, v in corpo.imagens.items() if v.strip()}}
    _gravar(pasta, "descricoes.json", todas)
    _processar(id_, ENVIOS / estado["envio"], estado.get("perfil"), todas)
    return _detalhe(id_, pasta)


@app.post("/api/materiais/{id_}/aprovar")
def aprovar(id_: str, request: Request) -> dict:
    """Aprovação do professor: publica o material para a turma."""
    pasta = _do_professor(id_, exigir(request, "professor"))
    revisao = _ler(pasta, "revisao.json")
    if not revisao["pode_publicar"]:
        raise HTTPException(409, {"erro": "Há pendências que bloqueiam a publicação.", "bloqueios": revisao["bloqueios"]})
    estado = _ler(pasta, "estado.json")
    estado.update(estado="publicado", publicado=datetime.now(timezone.utc).isoformat(timespec="seconds"))
    _gravar(pasta, "estado.json", estado)
    return _detalhe(id_, pasta)


@app.get("/api/previa/{id_}/{caminho:path}")
def previa(id_: str, caminho: str, request: Request) -> FileResponse:
    """Para o professor dono revisar qualquer versão, publicada ou não."""
    return _servir(_do_professor(id_, exigir(request, "professor")), caminho)


# ---------- feedbacks dos alunos (professor) ----------

@app.get("/api/feedbacks")
def feedbacks(request: Request) -> list[dict]:
    """Para cada material do professor: média, quantos avaliaram e a lista (apelido, estrelas, sugestão)."""
    prof = exigir(request, "professor")
    saida = []
    for id_, pasta in _todos_materiais():
        estado = _ler(pasta, "estado.json")
        if estado.get("professor_id") != prof["id"]:
            continue
        lista = contas.avaliacoes_do_material(id_)
        notas = [a["estrelas"] for a in lista if a["estrelas"]]
        saida.append({"id": id_, "titulo": _resumo(id_, pasta)["titulo"], "turma": estado.get("turma_nome"),
                      "estado": estado["estado"], "publicado": estado.get("publicado"),
                      "media": round(sum(notas) / len(notas), 1) if notas else None,
                      "total": len(lista), "avaliacoes": lista})
    return sorted(saida, key=lambda m: m.get("publicado") or "", reverse=True)


# ---------- painel da escola (só leitura) ----------

@app.get("/api/escola")
def painel_escola(request: Request) -> dict:
    escola = exigir(request, "escola")
    dados = contas.resumo_da_escola(escola["id"])
    nomes = {p["id"]: p["nome"] for p in dados["professores"]}
    materiais = []
    for id_, pasta in _todos_materiais():
        estado = _ler(pasta, "estado.json")
        if estado.get("professor_id") not in nomes:
            continue
        materiais.append({"titulo": _resumo(id_, pasta)["titulo"], "professor": nomes[estado["professor_id"]],
                          "turma": estado.get("turma_nome"), "estado": estado["estado"],
                          "criado": estado.get("criado"), "publicado": estado.get("publicado")})
    dados["materiais"] = sorted(materiais, key=lambda m: m.get("criado") or "", reverse=True)
    dados["escola"] = escola["nome"]
    return dados


# ---------- biblioteca (aluno e família) ----------

def _recomendadas(u: dict) -> set[str]:
    return set(pipeline.versoes_do_perfil({"necessidades": u.get("necessidades", []),
                                           "preferencias": u.get("preferencias", [])})) - {"universal"}


@app.get("/api/biblioteca")
def biblioteca(request: Request) -> list[dict]:
    """Só o que foi publicado para a turma de quem está logado.
    O aluno não vê o que a família tirou do painel dele; a família vê esses itens marcados como "oculto"
    (para poder devolver). Para o aluno, cada item traz a avaliação que ele já deu."""
    u = exigir(request, "aluno", "familia")
    recomendadas = _recomendadas(u)
    ocultos = contas.ocultos_do_aluno(u["aluno_id"])
    avaliacoes = contas.avaliacoes_do_aluno(u["aluno_id"]) if u["perfil"] == "aluno" else {}
    saida = []
    for id_, pasta in _todos_materiais():
        estado = _ler(pasta, "estado.json")
        if estado["estado"] != "publicado" or estado.get("turma_id") != u["turma_id"]:
            continue
        if id_ in ocultos and u["perfil"] == "aluno":
            continue
        item = _resumo(id_, pasta)
        saida.append({
            "id": id_, "material": item["material"], "titulo": item["titulo"], "publicado": estado.get("publicado"),
            "oculto": id_ in ocultos,
            **({"avaliacao": avaliacoes.get(id_)} if u["perfil"] == "aluno" else {}),
            "versoes": {n: {"url": f"/api/biblioteca/{id_}/{v['arquivo']}", "rotulo": v["rotulo"],
                            "recomendada": n in recomendadas}
                        for n, v in item["versoes"].items() if v["status"] == "gerada"},
        })
    return sorted(saida, key=lambda i: i.get("publicado") or "", reverse=True)


def _publicado_da_turma(id_: str, u: dict) -> Path:
    pasta = _pasta(id_)
    estado = _ler(pasta, "estado.json")
    if estado["estado"] != "publicado" or estado.get("turma_id") != u.get("turma_id"):
        raise HTTPException(404, "Material não encontrado.")
    return pasta


class Avaliacao(BaseModel):
    estrelas: int | None = None
    sugestao: str = ""
    pular: bool = False


@app.post("/api/biblioteca/{id_}/avaliacao")
def avaliar(id_: str, corpo: Avaliacao, request: Request) -> dict:
    """Só o aluno avalia. Estrelas (1 a 5) e sugestão (até 150 palavras) são opcionais; dá para pular."""
    u = exigir(request, "aluno")
    _publicado_da_turma(id_, u)
    return contas.avaliar(u["aluno_id"], id_, corpo.estrelas, corpo.sugestao, corpo.pular)


class Ocultar(BaseModel):
    ocultar: bool = True


@app.post("/api/biblioteca/{id_}/ocultar")
def ocultar(id_: str, corpo: Ocultar, request: Request) -> dict:
    """A família tira (ou devolve) um material do painel do próprio aluno. A turma continua vendo."""
    u = exigir(request, "familia")
    _publicado_da_turma(id_, u)
    contas.ocultar(u["aluno_id"], id_, corpo.ocultar)
    return {"ok": True, "oculto": corpo.ocultar}


@app.get("/api/biblioteca/{id_}/{caminho:path}")
def arquivo_publicado(id_: str, caminho: str, request: Request) -> FileResponse:
    u = exigir(request)
    pasta = _pasta(id_)
    estado = _ler(pasta, "estado.json")
    dono = u["perfil"] == "professor" and estado.get("professor_id") == u["id"]
    da_turma = u["perfil"] in ("aluno", "familia") and estado.get("turma_id") == u.get("turma_id")
    if estado["estado"] != "publicado" or not (dono or da_turma):
        raise HTTPException(404, "Material não encontrado.")   # rascunho e outra turma não vazam
    return _servir(pasta, caminho)


# O mesmo servidor entrega o site: um endereço só, sem problema de CORS nem de cookie.
if SITE.exists():
    app.mount("/", StaticFiles(directory=SITE, html=True), name="site")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000, proxy_headers=True, forwarded_allow_ips="127.0.0.1")
