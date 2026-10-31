"""Leitores: transformam o arquivo da aula (.txt, .pdf, .pptx, vídeo/áudio) num `Documento`.

Bibliotecas externas só são importadas quando o tipo de arquivo aparece,
então dá para usar .txt sem instalar nada.
"""
from __future__ import annotations

import logging
import re
from collections import Counter
from pathlib import Path

from .modelo import Bloco, Documento

logging.getLogger("pdfminer").setLevel(logging.ERROR)   # avisos de fonte do pdfminer não interessam ao professor

EXT_TEXTO = {".txt", ".md"}
EXT_PDF = {".pdf"}
EXT_PPT = {".pptx"}
EXT_MIDIA = {".mp4", ".mkv", ".mov", ".webm", ".mp3", ".wav", ".m4a", ".ogg"}

MARCA_LISTA = re.compile(r"^\s*(?:[-•–*▪●○◦‣⁃■□➢✓])\s+(.*)$")
MARCA_NUMERO = re.compile(r"^\s*(?:\d{1,2}|[a-z])[.)]\s+(.*)$", re.I)
NOME_DE_ARQUIVO = re.compile(r".*\.(png|jpe?g|gif|bmp|tiff?|svg|emf|wmf|webp)$", re.I)


def ler(caminho: Path, pasta_trabalho: Path, modelo_audio: str = "small", ia=None) -> Documento:
    """Escolhe o leitor pela extensão. Imagens extraídas vão para pasta_trabalho/imagens."""
    caminho = Path(caminho)
    ext = caminho.suffix.lower()
    if ext in EXT_TEXTO:
        doc = _ler_texto(caminho)
    elif ext in EXT_PDF:
        doc = _ler_pdf(caminho, pasta_trabalho)
    elif ext in EXT_PPT:
        doc = _ler_pptx(caminho, pasta_trabalho)
    elif ext in EXT_MIDIA:
        doc = _ler_midia(caminho, modelo_audio, ia)
    else:
        raise ValueError(
            f"Formato não suportado: {ext}. Use .pdf, .pptx, .txt, .mp4 ou .mp3."
        )
    doc.origem = caminho.name
    return doc


# ---------- utilidades ----------

def _tirar_titulo(blocos: list[Bloco], padrao: str) -> tuple[str, list[Bloco]]:
    """O título principal (nível mais alto entre os 3 primeiros blocos) vira o título do documento.
    Cobre apostilas com cabeçalho pequeno antes do título ("Ciências - 5º ano")."""
    candidatos = [(b.nivel, i) for i, b in enumerate(blocos[:3]) if b.tipo == "titulo"]
    if not candidatos:
        return padrao, blocos
    _, i = min(candidatos)
    return blocos[i].texto, blocos[:i] + blocos[i + 1:]


def _bloco_de_linhas(linhas: list[str]) -> Bloco | None:
    """Decide se um grupo de linhas é lista, etapas ou parágrafo."""
    linhas = [l for l in (x.strip() for x in linhas) if l]
    if not linhas:
        return None
    if all(MARCA_NUMERO.match(l) for l in linhas) and len(linhas) >= 2:
        return Bloco("etapas", itens=[MARCA_NUMERO.match(l).group(1) for l in linhas])
    if all(MARCA_LISTA.match(l) for l in linhas):
        return Bloco("lista", itens=[MARCA_LISTA.match(l).group(1) for l in linhas])
    return Bloco("paragrafo", texto=" ".join(linhas))


def _parece_titulo(linha: str) -> bool:
    linha = linha.strip()
    return (
        0 < len(linha) <= 70
        and not linha.endswith((".", ":", ";", ",", "!", "?"))
        and not MARCA_LISTA.match(linha)
        and not MARCA_NUMERO.match(linha)
    )


# ---------- texto ----------

def _ler_texto(caminho: Path) -> Documento:
    texto = caminho.read_text(encoding="utf-8", errors="replace")
    grupos = re.split(r"\n\s*\n", texto.strip())
    blocos: list[Bloco] = []
    for grupo in grupos:
        linhas = grupo.splitlines()
        if len(linhas) == 1 and linhas[0].lstrip().startswith("#"):
            marcas = len(linhas[0]) - len(linhas[0].lstrip("#"))
            blocos.append(Bloco("titulo", linhas[0].lstrip("# ").strip(), nivel=min(marcas, 3)))
        elif len(linhas) == 1 and _parece_titulo(linhas[0]) and blocos is not None:
            blocos.append(Bloco("titulo", linhas[0].strip(), nivel=2))
        else:
            b = _bloco_de_linhas(linhas)
            if b:
                blocos.append(b)
    titulo, blocos = _tirar_titulo(blocos, caminho.stem.replace("-", " ").replace("_", " "))
    return Documento(titulo, blocos)


# ---------- PDF ----------

QUESTAO = re.compile(r"(?:(?<=\s)|^)(\d{1,2})\s*-?\s*\)\s*")
ITEM_LETRA = re.compile(r"(?:(?<=\s)|^)\(?([a-h])\)\s*")
COMECA_MARCA = re.compile(r"^\s*(?:\d{1,2}\s*-?\s*[).]|\(?[a-h]\)|[-•–*▪●○◦‣⁃■□➢✓]\s)", re.I)


def _cortes_em_sequencia(texto: str, padrao: re.Pattern, primeiro, proximo) -> list[int]:
    """Posições onde começa cada marcador de uma sequência (1, 2, 3... ou a, b, c...).
    Só conta se a sequência estiver em ordem: "(14 ; 5 )" não vira questão 5."""
    cortes, esperado = [], None
    for m in padrao.finditer(texto):
        valor = m.group(1)
        if esperado is None:
            if valor != primeiro(valor) and m.start() > 0:
                continue
            esperado = valor
        if valor == esperado:
            cortes.append(m.start())
            esperado = proximo(valor)
    return cortes


def dividir_questoes_e_itens(texto: str) -> list[Bloco]:
    """Uma linha com "1-) … a) … b) … 2-) …" vira questões separadas, e os itens a), b) viram lista."""
    blocos: list[Bloco] = []
    q = _cortes_em_sequencia(texto, QUESTAO, lambda v: v, lambda v: str(int(v) + 1))
    partes = [texto[a:b].strip() for a, b in zip([0] + q[1:], q[1:] + [len(texto)])] if len(q) >= 2 else [texto]
    if q and q[0] > 0 and len(q) >= 2:
        partes = [texto[:q[0]].strip()] + partes
    for parte in (p for p in partes if p):
        itens = _cortes_em_sequencia(parte, ITEM_LETRA, lambda v: "a", lambda v: chr(ord(v) + 1))
        if len(itens) >= 2:
            cabeca = parte[:itens[0]].strip()
            if cabeca:
                blocos.append(Bloco("paragrafo", texto=cabeca))
            blocos.append(Bloco("lista", itens=[parte[a:b].strip() for a, b in zip(itens, itens[1:] + [len(parte)])]))
        else:
            blocos.append(Bloco("paragrafo", texto=parte))
    return blocos


def _juntar_itens_de_letra(blocos: list[Bloco]) -> list[Bloco]:
    """Parágrafos seguidos que começam com (a), (b)... viram uma lista só."""
    saida: list[Bloco] = []
    for b in blocos:
        m = ITEM_LETRA.match(b.texto) if b.tipo == "paragrafo" else None
        if m and saida and saida[-1].tipo == "lista" and saida[-1].itens:
            ultimo = ITEM_LETRA.match(saida[-1].itens[-1])
            if ultimo and ord(m.group(1)) == ord(ultimo.group(1)) + 1:
                saida[-1].itens.append(b.texto)
                continue
        if m and m.group(1) == "a" and b.tipo == "paragrafo":
            saida.append(Bloco("lista", itens=[b.texto]))
            continue
        saida.append(b)
    # lista de um item só volta a ser parágrafo
    return [Bloco("paragrafo", texto=b.itens[0]) if b.tipo == "lista" and len(b.itens) == 1 and ITEM_LETRA.match(b.itens[0]) else b
            for b in saida]


def _ler_pdf(caminho: Path, pasta_trabalho: Path) -> Documento:
    from . import leitor_pdf as lp

    paginas = lp.ler_paginas(caminho)
    linhas_pg = [lp.linhas_da_pagina(pg, n) for n, pg in enumerate(paginas)]

    # tamanho de letra mais comum = corpo do texto; maiores = títulos
    pesos: Counter = Counter()
    for linhas in linhas_pg:
        for L in linhas:
            pesos[round(L.tam)] += len(L.texto)
    corpo = pesos.most_common(1)[0][0] if pesos else 12

    pasta_img = pasta_trabalho / "imagens"
    n_img = 0
    blocos: list[Bloco] = []
    cores: list[str] = []
    figuras_coloridas: list[str] = []

    for n, (pg, linhas) in enumerate(zip(paginas, linhas_pg)):
        itens = [("linha", L.topo, L) for L in linhas]
        for f in pg.imagens:
            if min(f.x1 - f.x0, f.y1 - f.y0) < 40:
                continue                      # ícones e enfeites minúsculos
            itens.append(("imagem", f.y0, f))
        itens.sort(key=lambda x: x[1])

        grupo: list = []

        def fechar_grupo():
            if not grupo:
                return
            texto = " ".join(L.texto for L in grupo)
            texto = re.sub(r"(\w)- (?=[a-zà-ú])", r"\1", texto)            # palavra quebrada no fim da linha
            tam = max(L.tam for L in grupo)
            negrito = all(L.negrito for L in grupo)
            if re.fullmatch(r"\d{1,3}", texto.strip()):
                pass                                                          # número de página
            elif len(texto) <= 120 and tam >= corpo * 1.2:
                blocos.append(Bloco("titulo", lp.para_texto_simples(texto).strip() if lp.tem_matematica(texto) else texto,
                                    nivel=1 if tam >= corpo * 1.6 else 2))
            elif len(texto) <= 80 and negrito and not texto.endswith(".") and not COMECA_MARCA.match(texto):
                blocos.append(Bloco("titulo", texto, nivel=3))
            else:
                linhas_txt = [L.texto for L in grupo]
                if len(linhas_txt) >= 2 and all(MARCA_LISTA.match(l) for l in linhas_txt):
                    blocos.append(Bloco("lista", itens=[MARCA_LISTA.match(l).group(1) for l in linhas_txt]))
                else:
                    blocos.extend(dividir_questoes_e_itens(texto))
            for L in grupo:
                cores.extend(c for c in L.cores if c not in cores)
            grupo.clear()

        for tipo, _, x in itens:
            if tipo == "imagem":
                fechar_grupo()
                n_img += 1
                pasta_img.mkdir(parents=True, exist_ok=True)
                nome = f"img-{n_img:03d}.{x.ext}"
                (pasta_img / nome).write_bytes(x.dados)
                blocos.append(Bloco("imagem", arquivo=f"imagens/{nome}"))
                if lp.imagem_colorida(x.dados):
                    figuras_coloridas.append(f"imagens/{nome}")
                continue
            L = x
            if grupo:
                ant = grupo[-1]
                mesma = (L.topo - ant.fundo < 0.9 * L.tam and 0.85 <= L.tam / ant.tam <= 1.18
                         and L.negrito == ant.negrito and not COMECA_MARCA.match(L.texto))
                if not mesma:
                    fechar_grupo()
            grupo.append(L)
        fechar_grupo()
        # formas coloridas desenhadas no PDF (gráficos de barras, mapas feitos no Word)
        nomes = lp.desenho_informativo(pg)
        if nomes:
            figuras_coloridas.append(f"desenho na página {n + 1} ({', '.join(sorted(nomes))})")

    blocos = _juntar_itens_de_letra(blocos)
    titulo, blocos = _tirar_titulo(blocos, caminho.stem)
    doc = Documento(titulo, blocos, cores=cores, figuras_coloridas=figuras_coloridas)
    # escaneado = página sem nenhuma letra de verdade (um slide com só título e figura não é escaneado)
    letras = sum(1 for pg in paginas for c in pg.cars if c.c.strip())
    if letras < 20 and not any(b.tipo in ("paragrafo", "lista") for b in blocos):
        if letras == 0:
            doc.pendencias.append("Este PDF parece ser uma imagem escaneada (sem texto). É preciso aplicar OCR antes.")
        elif any(b.tipo == "imagem" for b in blocos):
            doc.pendencias.append(
                "Quase todo o conteúdo deste material está dentro de imagem. Na descrição, escreva também os textos "
                "que aparecem na figura: é o único jeito de eles chegarem à versão Ouvir e ao leitor de tela.")
    return doc


# ---------- PowerPoint ----------

def _ler_pptx(caminho: Path, pasta_trabalho: Path) -> Documento:
    try:
        from pptx import Presentation
        from pptx.enum.shapes import MSO_SHAPE_TYPE
    except ImportError as erro:
        raise RuntimeError("Para ler PowerPoint instale: pip install python-pptx") from erro

    apresentacao = Presentation(str(caminho))
    pasta_img = pasta_trabalho / "imagens"
    n_img = 0
    blocos: list[Bloco] = []
    cores: list[str] = []
    figuras_coloridas: list[str] = []
    for slide in apresentacao.slides:
        titulo_slide = slide.shapes.title
        if titulo_slide is not None and titulo_slide.text_frame.text.strip():
            blocos.append(Bloco("titulo", titulo_slide.text_frame.text.strip(), nivel=2))
        formas = sorted(slide.shapes, key=lambda s: (s.top or 0, s.left or 0))
        for forma in formas:
            if titulo_slide is not None and forma.shape_id == titulo_slide.shape_id:
                continue
            if forma.shape_type == MSO_SHAPE_TYPE.PICTURE:
                n_img += 1
                pasta_img.mkdir(parents=True, exist_ok=True)
                nome = f"img-{n_img:03d}.{forma.image.ext}"
                (pasta_img / nome).write_bytes(forma.image.blob)
                from .leitor_pdf import imagem_colorida
                if imagem_colorida(forma.image.blob):
                    figuras_coloridas.append(f"imagens/{nome}")
                alt = forma._element.xpath(".//p:cNvPr")[0].get("descr") or None
                if alt and NOME_DE_ARQUIVO.match(alt.strip()):
                    alt = None  # o PowerPoint às vezes grava o nome do arquivo como "descrição"
                blocos.append(Bloco("imagem", arquivo=f"imagens/{nome}", alt=alt))
            elif getattr(forma, "has_table", False) and forma.has_table:
                linhas = [" — ".join(c.text.strip() for c in l.cells) for l in forma.table.rows]
                blocos.append(Bloco("lista", itens=[l for l in linhas if l.strip(" —")]))
            elif forma.has_text_frame:
                paragrafos = [_texto_pptx_com_cor(p, cores) for p in forma.text_frame.paragraphs if p.text.strip()]
                if len(paragrafos) == 1:
                    blocos.append(Bloco("paragrafo", texto=paragrafos[0]))
                elif paragrafos:
                    b = _bloco_de_linhas(paragrafos)
                    # vários parágrafos no mesmo quadro de slide são tópicos, mesmo sem marcador
                    blocos.append(b if b and b.tipo != "paragrafo" else Bloco("lista", itens=paragrafos))
    primeiro = apresentacao.core_properties.title or caminho.stem
    return Documento(primeiro, blocos, cores=cores, figuras_coloridas=figuras_coloridas)


def _texto_pptx_com_cor(paragrafo, cores: list[str]) -> str:
    """Trecho com cor própria (não preta nem cinza) ganha a forma da cor logo depois (P1)."""
    from .leitor_pdf import nome_da_cor
    from .transformacoes import SIMBOLOS
    partes = []
    for run in paragrafo.runs:
        texto = run.text
        nome = None
        try:
            if run.font.color is not None and run.font.color.type is not None and run.font.color.rgb is not None:
                rgb = run.font.color.rgb
                nome = nome_da_cor((rgb[0] / 255, rgb[1] / 255, rgb[2] / 255))
        except (AttributeError, TypeError, ValueError):
            nome = None
        if nome and texto.strip():
            if nome not in cores:
                cores.append(nome)
            texto = texto.rstrip() + f" ({SIMBOLOS.get(nome, '■')}) "
        partes.append(texto)
    return re.sub(r"\s+", " ", "".join(partes)).strip()


# ---------- vídeo e áudio ----------

def _ler_midia(caminho: Path, modelo: str, ia=None) -> Documento:
    """Transcreve o áudio. 1º faster-whisper (local, sem internet depois de baixar o modelo);
    se não estiver instalado, a IA (Gemini) ouve o arquivo; sem os dois, explica o que fazer."""
    try:
        from faster_whisper import WhisperModel
    except ImportError:
        if ia is not None:
            return _ler_midia_pela_ia(caminho, ia)
        raise RuntimeError(
            "Para transcrever vídeo ou áudio, ligue a IA: rode o publicar.bat e cole a chave do Gemini "
            "quando ele pedir (ou instale o transcritor local: pip install faster-whisper)."
        ) from None

    whisper = WhisperModel(modelo, device="cpu", compute_type="int8")
    segmentos, _ = whisper.transcribe(str(caminho), language="pt", vad_filter=True)

    # agrupa frases em parágrafos: nova pausa longa (>1,5 s) ou ~5 frases
    paragrafos, atual, fim_anterior = [], [], 0.0
    for seg in segmentos:
        if atual and (seg.start - fim_anterior > 1.5 or len(atual) >= 5):
            paragrafos.append(" ".join(atual))
            atual = []
        atual.append(seg.text.strip())
        fim_anterior = seg.end
    if atual:
        paragrafos.append(" ".join(atual))

    doc = Documento(caminho.stem, [Bloco("paragrafo", texto=p) for p in paragrafos])
    _pendencia_transcricao(doc)
    return doc


def _ler_midia_pela_ia(caminho: Path, ia) -> Documento:
    from . import ia as ia_mod
    try:
        dados = ia_mod.transcrever_midia(ia, caminho)
    except ia_mod.ErroIA as erro:
        raise RuntimeError(f"Não consegui transcrever o arquivo: {erro}") from None
    if not dados["paragrafos"]:
        raise RuntimeError("Não encontrei fala neste arquivo. Confira se o áudio está ligado.")
    blocos = [Bloco("paragrafo", texto=p) for p in dados["paragrafos"]]
    if dados["na_tela"]:
        blocos += [Bloco("titulo", texto="O que aparece na tela", nivel=2), Bloco("lista", itens=dados["na_tela"])]
    doc = Documento(caminho.stem, blocos)
    _pendencia_transcricao(doc, pela_ia=True)
    return doc


def _pendencia_transcricao(doc: Documento, pela_ia: bool = False) -> None:
    if pela_ia:
        doc.pendencias.append(
            "O texto veio da transcrição feita pela IA: o professor precisa conferir nomes, números e termos "
            "técnicos, e a lista \"O que aparece na tela\", antes de aprovar.")
        return
    doc.pendencias.append(
        "O texto veio da transcrição automática do áudio: o professor precisa conferir nomes, "
        "números e termos técnicos. Imagens e slides mostrados no vídeo não foram lidos."
    )
