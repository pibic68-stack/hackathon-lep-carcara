"""Junta tudo: arquivo da aula + perfil do aluno -> versões adaptadas + fila de revisão."""
from __future__ import annotations

import json
import re
from pathlib import Path

from . import cache, leitores, regras, renderizador, transformacoes as t
from .modelo import Documento

SAIDA_PADRAO = Path(__file__).resolve().parents[1] / "saida"

# Qual necessidade/preferência do perfil pede qual versão do manual (ver "versoes_geradas").
# Quando regras.json existir, isto deve migrar para lá.
PEDE_VERSAO = {
    "baixa_visao": "ampliada", "fonte_ampliada": "ampliada",
    "leitura_facil": "lf2", "alfabetizacao": "lf2",
    "audio": "audio",
}
PRECISA_IA = {"lf1", "lf2", "audio"}


def versoes_do_perfil(perfil: dict | None) -> list[str]:
    pedidas = ["universal"]
    if perfil:
        for item in perfil.get("necessidades", []) + perfil.get("preferencias", []):
            v = PEDE_VERSAO.get(item)
            if v and v not in pedidas:
                pedidas.append(v)
    return pedidas


def _identificador(nome: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", nome.lower()).strip("-") or "material"


def preparar(caminho: Path, manual: dict, ia=None, modelo_audio: str = "small") -> tuple[Documento, Path]:
    """Lê o arquivo (usando o cache se já foi lido) e aplica as regras comuns a todos."""
    chave = cache.arquivo(caminho, extras=modelo_audio)
    pasta = cache.pasta_de(chave)
    guardado = cache.ler(chave, "documento")
    if guardado:
        doc = Documento.de_dict(guardado)
    else:
        doc = leitores.ler(caminho, pasta, modelo_audio)
        cache.gravar(chave, "documento", doc.para_dict())

    doc = t.cor_com_simbolo(doc)                      # P1
    doc = t.instrucoes_em_etapas(doc)                 # P6
    doc = t.sinalizar_linguagem_figurada(doc)         # P6 (só avisa)
    doc = t.imagens_com_descricao(doc, ia.descrever_imagem if ia else None)  # P4
    doc = t.quadro_hoje_vamos(doc, regras.maximo_etapas_hoje_vamos(manual))  # P6.1
    return doc, pasta


def adaptar(caminho: Path, perfil: dict | None = None, saida: Path = SAIDA_PADRAO,
            ia=None, modelo_audio: str = "small") -> dict:
    caminho = Path(caminho)
    manual = regras.carregar_manual()
    doc, pasta_trabalho = preparar(caminho, manual, ia, modelo_audio)

    pasta = Path(saida) / _identificador(caminho.stem)
    pasta.mkdir(parents=True, exist_ok=True)

    versoes: dict[str, dict] = {}
    for v in versoes_do_perfil(perfil):
        if v in PRECISA_IA:
            versoes[v] = {"status": "pendente_ia",
                          "motivo": "Esta versão precisa de IA, que ainda não está ligada."}
            continue
        estilo = "ampliada" if v == "ampliada" else "padrao"
        html = renderizador.para_html(doc, estilo, manual, pasta_trabalho, pasta)
        (pasta / f"{v}.html").write_text(html, encoding="utf-8")
        versoes[v] = {"status": "gerada", "arquivo": f"{v}.html"}

    # P4.1: imagem sem descrição bloqueia a publicação
    bloqueios = [p for p in doc.pendencias if p.startswith("P4.1")]
    revisao = {
        "material": doc.origem,
        "aluno": (perfil or {}).get("aluno"),
        "status": "aguardando_aprovacao_do_professor",   # P10.1: nada chega ao aluno sem aprovar
        "pode_publicar": not bloqueios,
        "bloqueios": bloqueios,
        "versoes": versoes,
        "transformacoes_aplicadas": doc.aplicados,
        "pendencias_para_o_professor": doc.pendencias,
    }
    (pasta / "revisao.json").write_text(
        json.dumps(revisao, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    revisao["pasta"] = str(pasta)
    return revisao
