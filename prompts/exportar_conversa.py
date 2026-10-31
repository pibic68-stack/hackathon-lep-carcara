#!/usr/bin/env python3
"""Converte transcripts do Claude Code (.jsonl) em Markdown legível para os avaliadores.

Uso:
    python3 prompts/exportar_conversa.py <transcript.jsonl> [--saida prompts/conversas] [--etiqueta texto]

O que entra no Markdown:
  - mensagens do time (sem os avisos internos do sistema)
  - respostas do Claude (texto)
  - uma linha por ferramenta usada (o que foi feito, sem a saída completa)
  - resumos de compactação, marcados como tal

O que NÃO entra: raciocínio interno, saídas brutas de ferramentas, avisos do sistema, e-mails e chaves de API.

O transcript .jsonl guarda o histórico inteiro mesmo depois de uma compactação,
então reexportar a partir dele não perde nada do que foi conversado.
"""
import argparse
import json
import re
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

FUSO = timezone(timedelta(hours=-3))  # America/Sao_Paulo

BLOCOS_INTERNOS = re.compile(
    r"<(system-reminder|local-command-caveat|local-command-stdout|local-command-stderr|"
    r"command-name|command-message|command-args)>.*?</\1>",
    re.S,
)
EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
# chaves de API conhecidas (Google/Gemini, Anthropic/OpenAI "sk-", GitHub): nunca podem ir para o repositório
SEGREDO = re.compile(
    r"\b(?:AIza[0-9A-Za-z_-]{30,}|AQ\.[0-9A-Za-z_-]{20,}|sk-[A-Za-z0-9_-]{20,}|ghp_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{30,})"
)


def ocultar(texto: str) -> str:
    return SEGREDO.sub("[chave removida]", EMAIL.sub("[e-mail removido]", texto))


def limpar(texto: str) -> str:
    texto = BLOCOS_INTERNOS.sub("", texto)
    texto = ocultar(texto)
    return texto.strip()


def hora(registro: dict) -> str:
    ts = registro.get("timestamp")
    if not ts:
        return ""
    try:
        dt = datetime.fromisoformat(ts.replace("Z", "+00:00")).astimezone(FUSO)
        return dt.strftime("%d/%m %H:%M")
    except ValueError:
        return ""


def resumo_ferramenta(bloco: dict) -> str:
    nome = bloco.get("name", "ferramenta")
    entrada = bloco.get("input") or {}
    detalhe = (
        entrada.get("description")
        or entrada.get("subject")
        or entrada.get("file_path")
        or entrada.get("query")
        or entrada.get("url")
        or ""
    )
    nome = nome.replace("mcp__", "").replace("__", " / ")
    detalhe = ocultar(str(detalhe))
    return f"- 🔧 `{nome}`" + (f": {detalhe}" if detalhe else "")


def textos_usuario(conteudo) -> str:
    if isinstance(conteudo, str):
        return limpar(conteudo)
    partes = [b.get("text", "") for b in conteudo if b.get("type") == "text"]
    return limpar("\n\n".join(partes))


def exportar(caminho: Path) -> tuple[str, int]:
    linhas = []
    ferramentas_pendentes = []
    n_mensagens = 0
    inicio = None

    def despejar_ferramentas():
        if ferramentas_pendentes:
            linhas.append("<details><summary>Ações executadas pelo Claude ("
                          f"{len(ferramentas_pendentes)})</summary>\n")
            linhas.extend(ferramentas_pendentes)
            linhas.append("\n</details>\n")
            ferramentas_pendentes.clear()

    for bruta in caminho.read_text(encoding="utf-8").splitlines():
        try:
            reg = json.loads(bruta)
        except json.JSONDecodeError:
            continue
        tipo = reg.get("type")
        msg = reg.get("message") or {}
        conteudo = msg.get("content")
        if inicio is None and reg.get("timestamp"):
            inicio = hora(reg)

        if tipo == "user":
            if reg.get("isCompactSummary"):
                despejar_ferramentas()
                linhas.append(f"\n---\n\n### 🗜️ Resumo automático (conversa compactada) · {hora(reg)}\n")
                linhas.append(textos_usuario(conteudo) + "\n")
                continue
            if reg.get("isMeta") or conteudo is None:
                continue
            if isinstance(conteudo, list) and all(b.get("type") == "tool_result" for b in conteudo):
                continue
            texto = textos_usuario(conteudo)
            if not texto:
                continue
            despejar_ferramentas()
            n_mensagens += 1
            linhas.append(f"\n---\n\n## 🧑 Time · {hora(reg)}\n")
            linhas.append(texto + "\n")

        elif tipo == "assistant" and isinstance(conteudo, list):
            for bloco in conteudo:
                if bloco.get("type") == "text" and bloco.get("text", "").strip():
                    despejar_ferramentas()
                    linhas.append(f"\n## 🤖 Claude · {hora(reg)}\n")
                    linhas.append(ocultar(bloco["text"].strip()) + "\n")
                elif bloco.get("type") == "tool_use":
                    ferramentas_pendentes.append(resumo_ferramenta(bloco))

    despejar_ferramentas()
    cabecalho = [
        f"# Conversa com IA · sessão `{caminho.stem[:8]}`\n",
        f"- **Início:** {inicio or 'n/d'}",
        f"- **Mensagens do time:** {n_mensagens}",
        f"- **Exportado em:** {datetime.now(FUSO).strftime('%d/%m/%Y %H:%M')}",
        "- **Ferramenta:** Claude (Anthropic)\n",
        "> Exportação automática. Raciocínio interno e saídas brutas de ferramentas foram omitidos.\n",
    ]
    return "\n".join(cabecalho + linhas), n_mensagens


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("transcript", type=Path)
    p.add_argument("--saida", type=Path, default=Path(__file__).parent / "conversas")
    p.add_argument("--etiqueta", default="")
    a = p.parse_args()

    if not a.transcript.exists():
        print(f"transcript não encontrado: {a.transcript}", file=sys.stderr)
        return 1
    md, _ = exportar(a.transcript)
    a.saida.mkdir(parents=True, exist_ok=True)
    nome = f"sessao-{a.transcript.stem[:8]}"
    (a.saida / f"{nome}.md").write_text(md, encoding="utf-8")
    if a.etiqueta:  # foto fixa, ex.: antes de uma compactação
        carimbo = datetime.now(FUSO).strftime("%Y%m%d-%H%M")
        (a.saida / "snapshots").mkdir(exist_ok=True)
        (a.saida / "snapshots" / f"{nome}-{a.etiqueta}-{carimbo}.md").write_text(md, encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
