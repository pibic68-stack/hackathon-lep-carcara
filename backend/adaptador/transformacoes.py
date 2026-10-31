"""Regras determinísticas do Manual. Não usam IA e sempre funcionam, mesmo sem internet.

Cada função recebe um `Documento` e devolve uma cópia nova com a regra aplicada.
O que mudou fica em `doc.aplicados` e o que precisa de gente fica em `doc.pendencias`
(é isso que o professor vê na fila de aprovação, critério P10.1).
"""
from __future__ import annotations

import copy
import re

from .modelo import Bloco, Documento

# ---------- P1: cor nunca sozinha ----------

# cada cor ganha uma forma diferente, que não depende de enxergar a cor
SIMBOLOS = {
    "vermelho": "▲", "verde": "●", "azul": "■", "amarelo": "◆",
    "laranja": "★", "roxo": "✚", "rosa": "♥", "preto": "▼",
    "branco": "○", "marrom": "◇", "cinza": "▬",
}
# toda forma escrita (feminino, plural) -> nome-base que tem símbolo
_FORMAS = {
    "vermelho": "vermelho", "vermelha": "vermelho", "vermelhos": "vermelho", "vermelhas": "vermelho",
    "verde": "verde", "verdes": "verde",
    "azul": "azul", "azuis": "azul",
    "amarelo": "amarelo", "amarela": "amarelo", "amarelos": "amarelo", "amarelas": "amarelo",
    "laranja": "laranja", "laranjas": "laranja",
    "roxo": "roxo", "roxa": "roxo", "roxos": "roxo", "roxas": "roxo",
    "rosa": "rosa", "rosas": "rosa",
    "preto": "preto", "preta": "preto", "pretos": "preto", "pretas": "preto",
    "branco": "branco", "branca": "branco", "brancos": "branco", "brancas": "branco",
    "marrom": "marrom", "marrons": "marrom",
    "cinza": "cinza", "cinzas": "cinza",
}
COR = re.compile(
    r"\b(" + "|".join(sorted(_FORMAS, key=len, reverse=True)) + r")\b(?!\s*\([▲●■◆★✚♥▼○◇▬]\))",
    re.I,
)


def _base(cor: str) -> str:
    return _FORMAS.get(cor.lower(), cor.lower())


def cor_com_simbolo(doc: Documento) -> Documento:
    novo = copy.deepcopy(doc)
    usadas: dict[str, str] = {}

    def marcar(m: re.Match) -> str:
        base = _base(m.group(1))
        simbolo = SIMBOLOS.get(base)
        if not simbolo:
            return m.group(0)
        usadas[base] = simbolo
        return f"{m.group(0)} ({simbolo})"

    for b in novo.blocos:
        if b.tipo in ("paragrafo", "titulo"):
            b.texto = COR.sub(marcar, b.texto)
        elif b.tipo in ("lista", "etapas", "quadro"):
            b.itens = [COR.sub(marcar, i) for i in b.itens]

    if usadas:
        legenda = Bloco("quadro", "Legenda das cores",
                        [f"{cor} = {simb}" for cor, simb in usadas.items()])
        novo.blocos.insert(0, legenda)
        novo.aplicados.append(
            f"P1.1 Cor nunca sozinha: {len(usadas)} cor(es) ganharam símbolo e uma legenda no topo."
        )
        novo.pendencias.append(
            "P1.1: confira se as palavras de cor marcadas realmente se referem a cores "
            "(ex.: \"rosa\" pode ser a flor)."
        )
    return novo


# ---------- P6: estrutura previsível ----------

IMPERATIVOS = (
    "abra|anote|apague|calcule|circule|compare|complete|copie|corrija|desenhe|discuta|"
    "escolha|escreva|explique|faça|identifique|ligue|leia|marque|meça|observe|ordene|"
    "pegue|pesquise|pinte|preencha|recorte|responda|resolva|separe|sublinhe|use|"
    "verifique|visite|junte|cole|conte|descreva|liste|monte|mostre|relacione|resuma"
)
INICIA_COM_ORDEM = re.compile(rf"^\W*(?:primeiro,?\s+)?({IMPERATIVOS})\b", re.I)
SEPARADOR = re.compile(
    r"\s*;\s*|[,.]?\s+(?:e,?\s+)?(?:depois|em seguida|a seguir|logo depois|por fim|finalmente|então)\b,?\s+"
    rf"|\s+e\s+(?=(?:{IMPERATIVOS})\b)|,\s+(?=(?:{IMPERATIVOS})\b)",
    re.I,
)


def _limpar_passo(texto: str) -> str:
    texto = re.sub(r"^\W*(?:primeiro|depois|em seguida|por fim)\b,?\s*", "", texto, flags=re.I)
    texto = re.sub(r"\s+e$", "", texto.strip(" ,;."))  # sobra de "…, e por fim,"
    texto = texto.strip(" ,;.")
    return texto[:1].upper() + texto[1:] if texto else texto


def _passos(paragrafo: str) -> list[str]:
    passos = []
    for frase in re.split(r"(?<=[.!?])\s+", paragrafo.strip()):
        passos.extend(_limpar_passo(p) for p in SEPARADOR.split(frase) if p and p.strip())
    return [p for p in passos if p]


def instrucoes_em_etapas(doc: Documento) -> Documento:
    novo = copy.deepcopy(doc)
    saida: list[Bloco] = []
    convertidos = 0
    for b in novo.blocos:
        if b.tipo == "paragrafo" and INICIA_COM_ORDEM.match(b.texto):
            passos = _passos(b.texto)
            if len(passos) >= 2:
                saida.append(Bloco("etapas", itens=passos))
                convertidos += 1
                continue
        saida.append(b)
    novo.blocos = saida
    if convertidos:
        novo.aplicados.append(
            f"P6.2 Estrutura previsível: {convertidos} instrução(ões) viraram passos numerados, um por ação."
        )
    return novo


def quadro_hoje_vamos(doc: Documento, maximo: int = 5) -> Documento:
    """P6.1: abre o material dizendo o que vai acontecer (usa os títulos da aula; até `maximo` etapas)."""
    novo = copy.deepcopy(doc)
    titulos = [b.texto for b in novo.blocos if b.tipo == "titulo" and b.nivel <= 2]
    if len(titulos) >= 2:
        # fica depois da legenda de cores (se houver), mas antes do conteúdo
        pos = sum(1 for b in novo.blocos[:1] if b.tipo == "quadro")
        novo.blocos.insert(pos, Bloco("quadro", "Hoje vamos", titulos[:maximo]))
        novo.aplicados.append("P6.1: quadro \"Hoje vamos\" acrescentado no começo, com os assuntos da aula.")
        if len(titulos) > maximo:
            novo.pendencias.append(
                f"P6.1: a aula tem {len(titulos)} assuntos e o quadro aceita no máximo {maximo}. "
                "Escolha quais mostrar ou divida a aula."
            )
    return novo


def sinalizar_linguagem_figurada(doc: Documento) -> Documento:
    """Só avisa o professor; não reescreve (reescrever exige revisão humana)."""
    novo = copy.deepcopy(doc)
    expressoes = ["chover no molhado", "pagar o pato", "de cabeça", "pisar na bola",
                  "um mar de", "quebrar a cabeça", "ficar de olho", "dar uma mão"]
    achadas = sorted({e for b in novo.blocos if b.texto for e in expressoes if e in b.texto.lower()})
    if achadas:
        novo.pendencias.append(
            "P6.3: expressões de sentido figurado encontradas (" + ", ".join(achadas)
            + "). Considere trocar por linguagem literal."
        )
    return novo


# ---------- P4: imagem com descrição ----------

def imagens_com_descricao(doc: Documento, descrever=None) -> Documento:
    """`descrever(bytes_caminho) -> str|None` é a IA (opcional). Sem ela, vira pendência."""
    novo = copy.deepcopy(doc)
    sem = 0
    for b in novo.blocos:
        if b.tipo == "imagem" and not b.alt:
            texto = descrever(b.arquivo) if descrever else None
            if texto:
                b.alt = texto
                novo.aplicados.append(f"P4.2: descrição gerada por IA para {b.arquivo} (precisa de revisão).")
            else:
                sem += 1
    if sem:
        novo.pendencias.append(
            f"P4.1: {sem} imagem(ns) sem descrição. O professor precisa escrever o texto alternativo."
        )
    return novo
