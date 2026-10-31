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
    """P1.1 (decisão do time, 31/10): a legenda entra quando o material USA cor para passar informação,
    não quando aparece a palavra "vermelho". O leitor já marcou cada trecho de texto colorido com a forma
    da cor (ex.: "as barras em vermelho (▲)") e listou as figuras coloridas. Aqui entram a legenda e os avisos."""
    novo = copy.deepcopy(doc)
    if novo.cores:
        legenda = Bloco("quadro", "Legenda das cores",
                        [f"{SIMBOLOS.get(c, '■')} = trecho que no original estava em {c}" for c in novo.cores])
        novo.blocos.insert(0, legenda)
        novo.aplicados.append(
            f"P1.1 Cor nunca sozinha: {len(novo.cores)} cor(es) de texto ganharam símbolo e uma legenda no topo."
        )
    imagens = [f for f in novo.figuras_coloridas if f.startswith("imagens/")]
    desenhos = [f for f in novo.figuras_coloridas if not f.startswith("imagens/")]
    if imagens:
        novo.pendencias.append(
            f"P1.2: {len(imagens)} imagem(ns) colorida(s). Na descrição de cada uma, diga o que cada cor representa "
            "(por exemplo: \"barras vermelhas: meninas\"). É assim que o aluno daltônico e a versão Ouvir entendem o desenho."
        )
        for b in novo.blocos:
            if b.tipo == "imagem" and b.arquivo in imagens:
                b.colorida = True
    if desenhos:
        novo.pendencias.append(
            "P1.2: o material tem desenho colorido feito no próprio arquivo (" + "; ".join(desenhos) + "). "
            "Ele não vira imagem: confira se o texto explica o que cada cor significa."
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
        # conta e expressão não se dividem em passos: "mmc (20 ; 30)" tem ";" mas não é lista de ações
        com_conta = "⟦" in b.texto or re.search(r"\([^)]*;[^)]*\)", b.texto)
        if b.tipo == "paragrafo" and not com_conta and INICIA_COM_ORDEM.match(b.texto):
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
    # olha também dentro de listas e passos (a instrução costuma virar passos antes desta regra)
    textos = [b.texto for b in novo.blocos if b.texto] + [i for b in novo.blocos for i in b.itens]
    achadas = sorted({e for x in textos for e in expressoes if e in x.lower()})
    if achadas:
        novo.pendencias.append(
            "P6.3: expressões de sentido figurado encontradas (" + ", ".join(achadas)
            + "). Considere trocar por linguagem literal."
        )
    return novo


# ---------- P4: imagem com descrição ----------

def imagens_com_descricao(doc: Documento, descrever=None) -> Documento:
    """`descrever(caminho_da_imagem) -> str|None` é a IA (opcional). Sem ela, vira pendência (P4.1)."""
    novo = copy.deepcopy(doc)
    sem = por_ia = decorativas = 0
    for b in novo.blocos:
        if b.tipo == "imagem" and not b.alt:
            texto = descrever(b.arquivo) if descrever else None
            if texto:
                if texto.upper().startswith("DECORATIVA:"):      # P4.5: a IA acha que é só enfeite
                    texto = texto[len("DECORATIVA:"):].strip()
                    decorativas += 1
                b.alt, b.origem_alt = texto, "ia"
                por_ia += 1
            else:
                sem += 1
    if por_ia:
        novo.aplicados.append(f"P4.2: {por_ia} descrição(ões) de imagem escrita(s) por IA.")
        novo.pendencias.append(
            f"P4.2: {por_ia} descrição(ões) de imagem foram escritas por IA. Confira e corrija antes de aprovar."
        )
    if decorativas:
        novo.pendencias.append(
            f"P4.5: {decorativas} imagem(ns) parece(m) só decorativa(s). Decida se ficam no material."
        )
    if sem:
        novo.pendencias.append(
            f"P4.1: {sem} imagem(ns) sem descrição. O professor precisa escrever o texto alternativo."
        )
    return novo


# ---------- P3: Leitura Fácil (usa IA; o código confere os limites do manual) ----------

ABREVIACAO = re.compile(r"\b(?:ex|etc|obs|p\.ex|cf|aprox)\.|[\\&<§#]", re.I)


def _frases(texto: str) -> list[str]:
    return [f.strip() for f in re.split(r"(?<=[.!?])\s+", texto.strip()) if f.strip()]


def _palavras(frase: str) -> int:
    # fórmula (⟦…⟧) conta como uma palavra só
    return len(re.findall(r"\w+", re.sub(r"⟦(?:[^⟦⟧]|⟦[^⟧]*⟧)*⟧", " F ", frase)))


def leitura_facil(doc: Documento, nivel: str, reescrever, max_palavras: int) -> Documento:
    """`reescrever(textos) -> (textos, glossario)` é a IA. Aplica P3.2, P3.4 e confere P3.1 e P3.5."""
    novo = copy.deepcopy(doc)
    alvos = []  # (bloco, índice do item ou None, texto)
    for b in novo.blocos:
        if b.tipo == "paragrafo":
            alvos.append((b, None, b.texto))
        elif b.tipo in ("lista", "etapas"):
            alvos.extend((b, i, x) for i, x in enumerate(b.itens))
    if not alvos:
        return novo

    resultado = reescrever([a[2] for a in alvos])
    textos, glossario = resultado[0], resultado[1]
    avisos = list(resultado[2]) if len(resultado) > 2 else []

    # P3.1: trecho com frase longa volta para a IA uma vez, com a instrução reforçada
    refazer = [k for k, t in enumerate(textos) if any(_palavras(f) > max_palavras for f in _frases(t))]
    if refazer:
        segundo = reescrever([textos[k] for k in refazer], refazer=True)
        novos, glos2 = segundo[0], segundo[1]
        avisos += list(segundo[2]) if len(segundo) > 2 else []
        for k, t in zip(refazer, novos):
            antes = sum(_palavras(f) > max_palavras for f in _frases(textos[k]))
            if sum(_palavras(f) > max_palavras for f in _frases(t)) < antes:
                textos[k] = t
        nomes = {g["termo"] for g in glossario}
        glossario = glossario + [g for g in glos2 if g["termo"] not in nomes]
        novo.aplicados.append(f"P3.1: {len(refazer)} trecho(s) com frase longa voltaram para a IA reescrever.")

    for (b, i, _), texto in zip(alvos, textos):
        if i is None:
            b.texto = texto
        else:
            b.itens[i] = texto

    # P3.2: uma frase por linha
    saida: list[Bloco] = []
    for b in novo.blocos:
        if b.tipo == "paragrafo":
            saida.extend(Bloco("paragrafo", texto=f) for f in (_frases(b.texto) or [b.texto]))
        else:
            saida.append(b)
    novo.blocos = saida

    # P3.4: glossário
    if glossario:
        novo.blocos.append(Bloco("quadro", "Palavras difíceis", [f"{g['termo']}: {g['significado']}" for g in glossario]))

    # P3.1 e P3.5: conferência automática do que a IA devolveu
    todas = [f for b in novo.blocos if b.tipo in ("paragrafo", "lista", "etapas")
             for f in (_frases(b.texto) if b.tipo == "paragrafo" else b.itens)]
    longas = [f for f in todas if _palavras(f) > max_palavras]
    sujas = [f for f in todas if ABREVIACAO.search(re.sub(r"⟦(?:[^⟦⟧]|⟦[^⟧]*⟧)*⟧", " ", f))]
    rotulo = {"lf2": "Leitura Fácil II", "lf1": "Leitura Fácil I"}.get(nivel, nivel)
    novo.pendencias.extend(avisos)
    novo.aplicados.append(f"P3 ({rotulo}): {len(textos)} texto(s) reescrito(s) por IA, uma frase por linha.")
    novo.pendencias.append(
        f"P3.7 ({rotulo}): a IA reescreveu o texto. Confira se todos os conceitos da aula foram conservados."
    )
    if longas:
        novo.pendencias.append(f"P3.1 ({rotulo}): {len(longas)} frase(s) ainda passam de {max_palavras} palavras. "
                               f"Por exemplo: \"{longas[0][:80]}\"")
    if sujas:
        novo.pendencias.append(f"P3.5 ({rotulo}): {len(sujas)} frase(s) com abreviação ou caractere especial.")
    return novo
