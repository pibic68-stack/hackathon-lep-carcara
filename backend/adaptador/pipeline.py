"""Junta tudo: arquivo da aula + perfil do aluno -> versões adaptadas + fila de revisão."""
from __future__ import annotations

import json
import re
from pathlib import Path

from . import cache, leitores, regras, renderizador, transformacoes as t
from . import ia as ia_mod
from .modelo import Documento

SAIDA_PADRAO = Path(__file__).resolve().parents[1] / "saida"

# Qual necessidade/preferência do perfil pede qual versão do manual (ver "versoes_geradas").
# Quando o time quiser, isto pode migrar para o padroes.json.
PEDE_VERSAO = {
    "baixa_visao": "ampliada", "fonte_ampliada": "ampliada",
    "leitura_facil": "lf2", "alfabetizacao": "lf2",
    "audio": "audio",
}
PRECISA_IA = {"lf1", "lf2"}
ROTULO_VERSAO = {"lf1": "Leitura Fácil I", "lf2": "Leitura Fácil II"}


def versoes_do_perfil(perfil: dict | None) -> list[str]:
    pedidas = ["universal"]
    if perfil:
        for item in perfil.get("necessidades", []) + perfil.get("preferencias", []):
            v = PEDE_VERSAO.get(item)
            if v and v not in pedidas:
                pedidas.append(v)
    return pedidas


def pede_simbolos(perfil: dict | None) -> bool:
    """Símbolos desenhados por cima das imagens coloridas: só quando algum aluno da turma tem
    "Cor sempre com símbolo" (daltonismo). Decisão do time em 31/10: sem esse aluno, a imagem fica limpa."""
    return bool(perfil) and "daltonismo" in (perfil.get("necessidades") or []) + (perfil.get("preferencias") or [])


def _identificador(nome: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", nome.lower()).strip("-") or "material"


def preparar(caminho: Path, manual: dict, ia=None, modelo_audio: str = "small",
             descricoes: dict | None = None, perfil: dict | None = None) -> tuple[Documento, Path]:
    """Lê o arquivo (usando o cache se já foi lido) e aplica as regras comuns a todos."""
    # "leitor-v2": leitor de PDF com matemática e cor (31/10). Mudou o leitor, o cache antigo não serve mais.
    chave = cache.arquivo(caminho, extras=modelo_audio + "|leitor-v2")
    pasta = cache.pasta_de(chave)
    guardado = cache.ler(chave, "documento")
    if guardado:
        doc = Documento.de_dict(guardado)
    else:
        doc = leitores.ler(caminho, pasta, modelo_audio, ia)
        cache.gravar(chave, "documento", doc.para_dict())

    # descrições escritas pelo professor (chave = caminho da imagem, ex.: "imagens/img-001.png")
    for b in doc.blocos:
        if b.tipo == "imagem" and descricoes and descricoes.get(b.arquivo, "").strip():
            b.alt, b.origem_alt = descricoes[b.arquivo].strip(), "professor"

    # P4: se a IA falhar (sem internet, limite...), a imagem fica "sem descrição" e o professor é avisado
    erros_ia: list[str] = []

    def descrever(arquivo: str) -> str | None:
        if not ia:
            return None
        try:
            return ia_mod.descrever_imagem(ia, pasta / arquivo, colorida=arquivo in doc.figuras_coloridas)
        except ia_mod.ErroIA as erro:
            if str(erro) not in erros_ia:
                erros_ia.append(str(erro))
            return None

    doc = t.linhas_de_resposta(doc)                   # pontilhado vira espaço de resposta (antes da IA)
    doc = t.cor_com_simbolo(doc)                      # P1
    if pede_simbolos(perfil):
        _simbolos_nas_imagens(doc, pasta)             # P1.1 dentro das imagens: só se a turma marcou "Cor sempre com símbolo"
    doc = t.instrucoes_em_etapas(doc)                 # P6
    doc = t.sinalizar_linguagem_figurada(doc)         # P6 (só avisa)
    doc = t.imagens_com_descricao(doc, descrever)     # P4
    doc = t.quadro_hoje_vamos(doc, regras.maximo_etapas_hoje_vamos(manual))  # P6.1
    for erro in erros_ia:
        doc.pendencias.append(f"IA indisponível para descrever imagens: {erro}")
    return doc, pasta


def _simbolos_nas_imagens(doc, pasta: Path) -> None:
    """Imagem colorida ganha uma cópia com símbolos sobre cada cor e a legenda (P1.1)."""
    from .simbolos_imagem import marcar_cores
    marcadas = 0
    for b in doc.blocos:
        if b.tipo != "imagem" or not b.colorida or not (pasta / b.arquivo).exists():
            continue
        destino = Path(b.arquivo).with_name(Path(b.arquivo).stem + "-cores.png").as_posix()
        try:
            cores = marcar_cores(pasta / b.arquivo, pasta / destino)
        except Exception:                       # imagem estranha: fica sem símbolos, o professor já foi avisado (P1.2)
            cores = []
        if cores:
            b.arquivo_cores, b.cores_imagem = destino, cores
            marcadas += 1
    if marcadas:
        doc.aplicados.append(
            f"P1.1 Cor nunca sozinha: {marcadas} imagem(ns) colorida(s) ganharam símbolos sobre cada cor e uma legenda.")


def _origem_imagem(b) -> str:
    if not b.alt:
        return "pendente"
    return b.origem_alt or "original"


def adaptar(caminho: Path, perfil: dict | None = None, saida: Path = SAIDA_PADRAO,
            ia=None, modelo_audio: str = "small", descricoes: dict | None = None,
            nome_pasta: str | None = None) -> dict:
    caminho = Path(caminho)
    manual = regras.carregar_manual()
    doc, pasta_trabalho = preparar(caminho, manual, ia, modelo_audio, descricoes, perfil)

    pasta = Path(saida) / (nome_pasta or _identificador(caminho.stem))
    pasta.mkdir(parents=True, exist_ok=True)

    versoes: dict[str, dict] = {}
    extra_aplicados: list[str] = []
    extra_pendencias: list[str] = []
    limites_p31 = regras.limites(manual, "P3.1")          # [20, 15, 10]: todos, nível II, nível I

    for v in versoes_do_perfil(perfil):
        if v in PRECISA_IA:
            if not ia:
                versoes[v] = {"status": "pendente_ia",
                              "motivo": "Esta versão precisa da IA, e a chave do Gemini não foi colocada neste computador."}
                continue
            maximo = int(limites_p31[1] if v == "lf2" else limites_p31[2])
            try:
                versao_doc = t.leitura_facil(
                    doc, v, lambda textos, refazer=False, v=v, m=maximo: ia_mod.leitura_facil(ia, textos, v, m, refazer), maximo)
            except ia_mod.ErroIA as erro:
                versoes[v] = {"status": "falhou", "motivo": str(erro)}
                continue
            extra_aplicados += versao_doc.aplicados[len(doc.aplicados):]
            extra_pendencias += versao_doc.pendencias[len(doc.pendencias):]
            html = renderizador.para_html(versao_doc, "padrao", manual, pasta_trabalho, pasta, versao=v)
        elif v == "audio":
            html = renderizador.para_html(doc, "padrao", manual, pasta_trabalho, pasta, audio=True, versao=v)
            extra_aplicados.append("P5: versão para ouvir criada (lê o texto em voz alta pelo navegador).")
        else:
            html = renderizador.para_html(doc, "ampliada" if v == "ampliada" else "padrao",
                                          manual, pasta_trabalho, pasta, versao=v)
        (pasta / f"{v}.html").write_text(html, encoding="utf-8")
        versoes[v] = {"status": "gerada", "arquivo": f"{v}.html"}

    aplicados = doc.aplicados + extra_aplicados
    pendencias = doc.pendencias + extra_pendencias
    # P4.1: imagem sem descrição bloqueia a publicação
    bloqueios = [p for p in pendencias if p.startswith("P4.1")]
    revisao = {
        "material": doc.origem,
        "titulo": doc.titulo,
        "aluno": (perfil or {}).get("aluno"),
        "status": "aguardando_aprovacao_do_professor",   # P10.1: nada chega ao aluno sem aprovar
        "pode_publicar": not bloqueios,
        "bloqueios": bloqueios,
        "versoes": versoes,
        "imagens": [{"arquivo": b.arquivo, "alt": b.alt or "", "origem": _origem_imagem(b)}
                    for b in doc.blocos if b.tipo == "imagem"],
        "transformacoes_aplicadas": aplicados,
        "pendencias_para_o_professor": pendencias,
    }
    (pasta / "revisao.json").write_text(
        json.dumps(revisao, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    revisao["pasta"] = str(pasta)
    return revisao
