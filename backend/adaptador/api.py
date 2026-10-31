"""API HTTP do PRISMA: o site envia o material e recebe as versões adaptadas.

Rodar (de dentro de backend/):   python -m adaptador.api      -> http://127.0.0.1:8000
Documentação interativa:         http://127.0.0.1:8000/docs

Ciclo de vida de um material (critério P10.1 do Manual: nada chega ao aluno sem aprovação):
    POST /api/adaptar  ->  estado "rascunho"  ->  POST .../aprovar  ->  estado "publicado"
Só materiais publicados aparecem na biblioteca dos alunos.
Imagem sem descrição bloqueia a aprovação (P4.1) até o professor escrever o texto.

AINDA NÃO HÁ LOGIN: qualquer um que alcance o servidor pode aprovar. Use só em rede local na demo.
"""
from __future__ import annotations

import json
import re
import shutil
import uuid
from datetime import datetime, timezone
from pathlib import Path

from fastapi import FastAPI, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from . import ia, pipeline
from .leitores import EXT_MIDIA, EXT_PDF, EXT_PPT, EXT_TEXTO

RAIZ = Path(__file__).resolve().parents[1]
SAIDA = RAIZ / "saida"
ENVIOS = RAIZ / "envios"
SITE = RAIZ.parent / "web"

LIMITE_BYTES = 300 * 1024 * 1024   # 300 MB (vídeos grandes devem ser comprimidos antes)
EXTENSOES = EXT_TEXTO | EXT_PDF | EXT_PPT | EXT_MIDIA
ID_VALIDO = re.compile(r"^[0-9a-f]{12}$")

app = FastAPI(title="PRISMA – adaptador de material", version="0.1")
# O site abre por duplo clique (origem "null"), então precisa de CORS aberto. Sem cookies/credenciais.
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


# ---------- utilidades ----------

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


def _resumo(id_: str, pasta: Path) -> dict:
    estado, revisao = _ler(pasta, "estado.json"), _ler(pasta, "revisao.json")
    return {
        "id": id_,
        "material": revisao["material"],
        "estado": estado["estado"],
        "criado": estado["criado"],
        "pode_publicar": revisao["pode_publicar"],
        "versoes": {
            nome: {**v, **({"url": f"/api/previa/{id_}/{v['arquivo']}"} if "arquivo" in v else {})}
            for nome, v in revisao["versoes"].items()
        },
    }


def _detalhe(id_: str, pasta: Path) -> dict:
    revisao = _ler(pasta, "revisao.json")
    return {
        **_resumo(id_, pasta),
        "aluno": revisao.get("aluno"),
        "transformacoes_aplicadas": revisao["transformacoes_aplicadas"],
        "pendencias_para_o_professor": revisao["pendencias_para_o_professor"],
        "bloqueios": revisao["bloqueios"],
        "imagens_sem_descricao": _imagens_pendentes(pasta),
    }


def _imagens_pendentes(pasta: Path) -> list[str]:
    """Caminhos das imagens sem descrição, lidos do HTML gerado (cada <img alt=""> é uma pendência)."""
    achadas: set[str] = set()
    for html in pasta.glob("*.html"):
        achadas.update(re.findall(r'<img src="([^"]+)" alt="">', html.read_text(encoding="utf-8")))
    return sorted(achadas)


def _processar(id_: str, arquivo: Path, perfil: dict | None, descricoes: dict | None) -> dict:
    try:
        return pipeline.adaptar(arquivo, perfil, SAIDA, ia.obter_provedor(),
                                descricoes=descricoes, nome_pasta=id_)
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


# ---------- rotas ----------

@app.get("/api/saude")
def saude() -> dict:
    return {"ok": True, "ia_ligada": ia.obter_provedor() is not None, "formatos": sorted(EXTENSOES)}


@app.post("/api/adaptar", status_code=201)
def adaptar(arquivo: UploadFile, perfil: str | None = Form(None)) -> dict:
    """Recebe o material (.pdf, .pptx, .txt, .mp4, .mp3...) e o perfil (JSON, opcional). Cria um rascunho."""
    nome = Path(arquivo.filename or "material").name
    ext = Path(nome).suffix.lower()
    if ext not in EXTENSOES:
        raise HTTPException(415, f"Formato {ext or 'desconhecido'} não suportado. Use: {', '.join(sorted(EXTENSOES))}.")
    try:
        perfil_dict = json.loads(perfil) if perfil else None
        if perfil_dict is not None and not isinstance(perfil_dict, dict):
            raise ValueError
    except ValueError:
        raise HTTPException(422, "O perfil precisa ser um JSON de objeto, ex.: {\"necessidades\": [\"baixa_visao\"]}.")

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
                shutil.rmtree(pasta_envio, ignore_errors=True)
                raise HTTPException(413, f"Arquivo maior que {LIMITE_BYTES // (1024 * 1024)} MB.")
            saida.write(bloco)

    try:
        _processar(id_, caminho, perfil_dict, None)
    except HTTPException:
        shutil.rmtree(pasta_envio, ignore_errors=True)
        raise
    pasta = SAIDA / id_
    _gravar(pasta, "estado.json", {
        "estado": "rascunho", "criado": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "envio": f"{id_}/{caminho.name}", "perfil": perfil_dict,
    })
    return _detalhe(id_, pasta)


@app.get("/api/materiais")
def listar_materiais() -> list[dict]:
    """Visão do professor: todos os materiais, mais recentes primeiro."""
    itens = [_resumo(p.name, p) for p in SAIDA.glob("*") if ID_VALIDO.match(p.name) and (p / "estado.json").exists()] if SAIDA.exists() else []
    return sorted(itens, key=lambda i: i["criado"], reverse=True)


@app.get("/api/materiais/{id_}")
def ver_material(id_: str) -> dict:
    return _detalhe(id_, _pasta(id_))


class Descricoes(BaseModel):
    imagens: dict[str, str]   # {"imagens/img-001.png": "Texto alternativo"}


@app.post("/api/materiais/{id_}/descricoes")
def escrever_descricoes(id_: str, corpo: Descricoes) -> dict:
    """O professor escreve (ou corrige) as descrições das imagens; as versões são geradas de novo."""
    pasta = _pasta(id_)
    estado = _ler(pasta, "estado.json")
    if estado["estado"] == "publicado":
        raise HTTPException(409, "Material já publicado. Crie um novo rascunho para alterar.")
    anteriores = _ler(pasta, "descricoes.json") if (pasta / "descricoes.json").exists() else {}
    todas = {**anteriores, **{k: v for k, v in corpo.imagens.items() if v.strip()}}
    _gravar(pasta, "descricoes.json", todas)
    _processar(id_, ENVIOS / estado["envio"], estado.get("perfil"), todas)
    return _detalhe(id_, pasta)


@app.post("/api/materiais/{id_}/aprovar")
def aprovar(id_: str) -> dict:
    """Aprovação do professor: publica o material na biblioteca dos alunos."""
    pasta = _pasta(id_)
    revisao = _ler(pasta, "revisao.json")
    if not revisao["pode_publicar"]:
        raise HTTPException(409, {"erro": "Há pendências que bloqueiam a publicação.", "bloqueios": revisao["bloqueios"]})
    estado = _ler(pasta, "estado.json")
    estado.update(estado="publicado", publicado=datetime.now(timezone.utc).isoformat(timespec="seconds"))
    _gravar(pasta, "estado.json", estado)
    return _detalhe(id_, pasta)


@app.get("/api/previa/{id_}/{caminho:path}")
def previa(id_: str, caminho: str) -> FileResponse:
    """Para o professor revisar qualquer versão, publicada ou não."""
    return _servir(_pasta(id_), caminho)


@app.get("/api/biblioteca")
def biblioteca() -> list[dict]:
    """Visão do aluno e da família: só o que foi publicado."""
    saida = []
    for item in listar_materiais():
        if item["estado"] != "publicado":
            continue
        saida.append({
            "id": item["id"], "material": item["material"],
            "versoes": {n: {"url": f"/api/biblioteca/{item['id']}/{v['arquivo']}"}
                        for n, v in item["versoes"].items() if v["status"] == "gerada"},
        })
    return saida


@app.get("/api/biblioteca/{id_}/{caminho:path}")
def arquivo_publicado(id_: str, caminho: str) -> FileResponse:
    pasta = _pasta(id_)
    if _ler(pasta, "estado.json")["estado"] != "publicado":
        raise HTTPException(404, "Material não encontrado.")   # rascunho não vaza para o aluno
    return _servir(pasta, caminho)


# O mesmo servidor entrega o site: assim a demo é um comando só e não há problema de CORS.
if SITE.exists():
    app.mount("/", StaticFiles(directory=SITE, html=True), name="site")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
