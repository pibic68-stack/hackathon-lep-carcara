"""Transforma um `Documento` em uma página HTML acessível (padrão P2: página limpa e legível).

Identidade visual do site (web/css/tokens.css): Atkinson Hyperlegible Next, tinta #1E2235,
fundo creme #FBF7EE (decisão do time em 31/10), bordas retas de pixel. A fonte vem do próprio
servidor (/assets/fontes); fora dele, cai para fontes do sistema sem serifa.
"""
from __future__ import annotations

import html
import json
import re
import shutil
from pathlib import Path

from . import leitor_pdf
from .modelo import Documento
from .regras import parametros_p2

FONTE = "'Atkinson Hyperlegible Next', 'Atkinson Hyperlegible', Verdana, Arial, sans-serif"
FONTES_SITE = """
@font-face { font-family: "Atkinson Hyperlegible Next"; src: url("/assets/fontes/atkinson-400.woff2") format("woff2"); font-weight: 400; font-display: swap; }
@font-face { font-family: "Atkinson Hyperlegible Next"; src: url("/assets/fontes/atkinson-700.woff2") format("woff2"); font-weight: 700; font-display: swap; }
"""

# Cores do site (tokens.css). Os testes conferem o contraste contra o manual (P2.1).
ESTILOS = {
    "padrao": {"texto": "#1E2235", "fundo": "#FBF7EE", "destaque": "#1F6FB2",
               "quadro_fundo": "#F3EDDF", "borda": "#1E2235"},
    "ampliada": {"texto": "#000000", "fundo": "#FBF7EE", "destaque": "#0E4A82",
                 "quadro_fundo": "#FFFFFF", "borda": "#000000"},
}

# Temas de leitura que o aluno escolhe na própria página (decisão do time, 31/10).
# A versão Ampliada abre em amarelo no preto, como o alto contraste do site. A preferência de cada pessoa
# com baixa visão varia (fundo escuro ofusca menos, mas há quem leia melhor no claro), então todos escolhem.
TEMAS = {
    "creme":   {"nome": "Creme (padrão)",   "texto": "#1E2235", "fundo": "#FBF7EE", "destaque": "#1F6FB2", "quadro": "#F3EDDF", "borda": "#1E2235", "link": "#1F6FB2"},
    "amarelo": {"nome": "Amarelo no preto", "texto": "#FFE600", "fundo": "#000000", "destaque": "#FFE600", "quadro": "#000000", "borda": "#FFE600", "link": "#FFFFFF"},
    "branco":  {"nome": "Branco no preto",  "texto": "#FFFFFF", "fundo": "#000000", "destaque": "#FFFFFF", "quadro": "#000000", "borda": "#FFFFFF", "link": "#FFE600"},
    "preto":   {"nome": "Preto no branco",  "texto": "#000000", "fundo": "#FFFFFF", "destaque": "#000000", "quadro": "#FFFFFF", "borda": "#000000", "link": "#0E4A82"},
}


def luminancia(hexcor: str) -> float:
    r, g, b = (int(hexcor[i:i + 2], 16) / 255 for i in (1, 3, 5))
    f = lambda c: c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    return 0.2126 * f(r) + 0.7152 * f(g) + 0.0722 * f(b)


def contraste(a: str, b: str) -> float:
    la, lb = sorted((luminancia(a), luminancia(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)


def _css_temas() -> str:
    linhas = []
    for chave, t in TEMAS.items():
        linhas.append(f':root[data-tema="{chave}"] {{ --texto:{t["texto"]}; --fundo:{t["fundo"]}; --destaque:{t["destaque"]}; '
                      f'--quadro:{t["quadro"]}; --borda:{t["borda"]}; --link:{t["link"]}; }}')
    return "\n".join(linhas)


def _css(estilo: str, params: dict) -> str:
    cor = ESTILOS[estilo]
    pt = params["pt_ampliada"] if estilo == "ampliada" else params["pt_padrao"]
    return FONTES_SITE + f"""
:root {{ --texto:{cor['texto']}; --fundo:{cor['fundo']}; --destaque:{cor['destaque']};
         --quadro:{cor['quadro_fundo']}; --borda:{cor['borda']}; --link:{cor['destaque']}; --escala:1; }}
{_css_temas()}
* {{ box-sizing: border-box; }}
html {{ background:var(--fundo); }}
body {{ margin:0; background:var(--fundo); color:var(--texto); font-family:{FONTE};
        font-size:calc({pt}pt * var(--escala)); line-height:{max(params['espacamento_minimo'], 1.8 if estilo == 'ampliada' else 1.6)};
        text-align:left; hyphens:none; font-style:normal; {"font-weight:700; letter-spacing:.01em;" if estilo == "ampliada" else ""} }}
a {{ color:var(--link); text-decoration-thickness:2px; text-underline-offset:3px; }}
/* fórmulas (MathML): mesma cor do texto, fonte de matemática do sistema */
math {{ font-family:"Cambria Math","STIX Two Math","Latin Modern Math",math; font-size:1.1em; color:inherit; math-style:normal; }}
mfrac {{ padding:0 .1em; }}
sup, sub {{ font-size:.75em; line-height:0; }}
ul.itens {{ list-style:none; padding-left:0; }}
ul.itens li {{ padding-left:2.2em; text-indent:-2.2em; }}
/* barra de ajustes de leitura */
.ajustes {{ display:flex; flex-wrap:wrap; gap:.6rem 1rem; align-items:center; margin:0 0 1.2rem; padding:.6rem .8rem;
  border:3px solid var(--borda); background:var(--quadro); font-size:max(14pt, .8em); font-weight:400; }}
.ajustes label {{ font-weight:700; }}
.ajustes select, .ajustes button {{ font:inherit; font-weight:700; min-height:44px; padding:.2rem .7rem; color:var(--texto);
  background:var(--fundo); border:3px solid var(--borda); border-radius:0; cursor:pointer; }}
.ajustes .grupo {{ display:inline-flex; gap:.4rem; align-items:center; }}
figure img {{ border:3px solid var(--borda); background:#fff; }}
.cor-aviso {{ font-size:.9em; }}

main {{ max-width:{params['caracteres_por_linha']}ch; margin:0 auto; padding:1.5rem 1rem 4rem; }}
h1, h2, h3 {{ line-height:1.25; color:var(--destaque); }}
h1 {{ font-size:1.7em; }} h2 {{ font-size:1.35em; margin-top:2rem; }} h3 {{ font-size:1.15em; }}
p, li {{ margin:.6em 0; }}
ol.etapas {{ padding-left:1.6em; }}
ol.etapas li {{ margin:.9em 0; padding-left:.3em; }}
ol.etapas li::marker {{ font-weight:700; color:var(--destaque); }}
aside.quadro {{ background:var(--quadro); border:3px solid var(--borda); border-radius:0;
                padding:.6rem 1.2rem; margin:1.2rem 0; }}
aside.quadro h2 {{ margin:.4rem 0; font-size:1.1em; }}
figure {{ margin:1.2rem 0; }} img {{ max-width:100%; height:auto; }}
.pendente {{ border:2px dashed var(--borda); padding:.5rem; }}
.pular {{ position:absolute; left:-999px; }} .pular:focus {{ left:1rem; top:1rem; background:#fff; padding:.5rem; }}
:focus-visible {{ outline:4px solid var(--destaque); outline-offset:2px; }}
@media print {{ section.pagina {{ break-before:page; }} }}
"""


FALA_SIMBOLOS = {"▲": "triângulo", "●": "círculo", "■": "quadrado", "◆": "losango", "★": "estrela",
                 "✚": "cruz", "♥": "coração", "▼": "triângulo para baixo", "○": "círculo vazio",
                 "◇": "losango vazio", "▬": "barra"}

CSS_AUDIO = """
.barra-audio { position:sticky; top:0; z-index:5; display:flex; flex-wrap:wrap; gap:.6rem; align-items:center;
  background:var(--quadro); border:3px solid var(--borda); padding:.6rem .8rem; margin:1rem 0; }
.barra-audio button, .barra-audio select { font:inherit; font-size:max(14pt, .8em); font-weight:700; min-height:44px; padding:.3rem .9rem;
  color:var(--texto); background:var(--fundo); border:3px solid var(--borda); cursor:pointer; }
.barra-audio p { margin:0; flex-basis:100%; }
.lendo { outline:5px solid var(--destaque); outline-offset:6px; border-left:10px solid var(--destaque); padding-left:.6rem; }
"""

BARRA_AUDIO = """<div class="barra-audio" role="group" aria-label="Ouvir o material">
<button type="button" id="ouvir">Ouvir</button>
<button type="button" id="pausar">Pausar</button>
<button type="button" id="parar">Parar</button>
<label>Velocidade <select id="vel"><option value="0.8">Devagar</option><option value="1" selected>Normal</option><option value="1.25">Rápido</option></select></label>
<p id="aviso-audio" role="status"></p>
</div>"""

SCRIPT_AUDIO = r"""<script>
(function () {
  var falas = __FALAS__;
  var itens = document.querySelectorAll("[data-fala]");
  var aviso = document.getElementById("aviso-audio");
  if (!("speechSynthesis" in window)) { aviso.textContent = "Este navegador não sabe ler em voz alta. Tente o Chrome ou o Edge."; return; }
  var atual = 0, tocando = false, rodada = 0;
  function limpar() { itens.forEach(function (e) { e.classList.remove("lendo"); }); }
  function destacar(i) {
    limpar();
    var e = document.querySelector('[data-fala="' + i + '"]');
    if (e) { e.classList.add("lendo"); e.scrollIntoView({ block: "center" }); }
  }
  function ler(i) {
    if (!tocando) return;
    if (i >= falas.length) { parar(); return; }
    var id = ++rodada;
    atual = i; destacar(i);
    var u = new SpeechSynthesisUtterance(falas[i]);
    u.lang = "pt-BR"; u.rate = parseFloat(document.getElementById("vel").value);
    u.onend = function () { if (tocando && id === rodada) ler(i + 1); };
    speechSynthesis.speak(u);
  }
  function parar() { tocando = false; rodada++; speechSynthesis.cancel(); limpar(); atual = 0; aviso.textContent = ""; }
  document.getElementById("ouvir").addEventListener("click", function () {
    if (speechSynthesis.paused) { speechSynthesis.resume(); aviso.textContent = ""; return; }
    if (!tocando) { tocando = true; aviso.textContent = "Lendo em voz alta…"; ler(atual); }
  });
  document.getElementById("pausar").addEventListener("click", function () { speechSynthesis.pause(); aviso.textContent = "Pausado."; });
  document.getElementById("parar").addEventListener("click", parar);
  document.getElementById("vel").addEventListener("change", function () { if (tocando) { speechSynthesis.cancel(); ler(atual); } });
  window.addEventListener("pagehide", function () { speechSynthesis.cancel(); });
})();
</script>"""


def _fala(texto: str) -> str:
    """Texto como deve ser falado: fórmulas viram palavras ("x ao quadrado"), símbolos viram o nome da forma."""
    texto = leitor_pdf.para_fala(texto)
    for simbolo, nome in FALA_SIMBOLOS.items():
        texto = texto.replace(f"({simbolo})", f"({nome})").replace(f"{simbolo} =", f"{nome}:")
    return texto


def _barra_ajustes(estilo: str) -> str:
    opcoes = "".join(f'<option value="{k}">{_esc(t["nome"])}</option>' for k, t in TEMAS.items())
    return (f'<div class="ajustes" role="group" aria-label="Ajustes de leitura">'
            f'<span class="grupo"><label for="tema">Cores da página</label><select id="tema">{opcoes}</select></span>'
            f'<span class="grupo" role="group" aria-label="Tamanho da letra">'
            f'<button type="button" id="letra-menor" aria-label="Diminuir a letra">A−</button>'
            f'<button type="button" id="letra-maior" aria-label="Aumentar a letra">A+</button></span></div>')


SCRIPT_AJUSTES = r"""<script>
(function () {
  var CHAVE = "prisma-leitura-__VERSAO__", ESCALAS = [1, 1.15, 1.3, 1.5, 1.75];
  var raiz = document.documentElement, pref = {};
  try { pref = JSON.parse(localStorage.getItem(CHAVE)) || {}; } catch (e) { pref = {}; }
  function aplicar() {
    raiz.setAttribute("data-tema", pref.tema || "__TEMA__");
    raiz.style.setProperty("--escala", ESCALAS[pref.escala || 0]);
    document.getElementById("tema").value = pref.tema || "__TEMA__";
    document.getElementById("letra-menor").disabled = !(pref.escala > 0);
    document.getElementById("letra-maior").disabled = (pref.escala || 0) >= ESCALAS.length - 1;
  }
  function salvar() { try { localStorage.setItem(CHAVE, JSON.stringify(pref)); } catch (e) { /* segue sem salvar */ } aplicar(); }
  document.getElementById("tema").addEventListener("change", function (e) { pref.tema = e.target.value; salvar(); });
  document.getElementById("letra-maior").addEventListener("click", function () { pref.escala = Math.min((pref.escala || 0) + 1, ESCALAS.length - 1); salvar(); });
  document.getElementById("letra-menor").addEventListener("click", function () { pref.escala = Math.max((pref.escala || 0) - 1, 0); salvar(); });
  aplicar();
})();
</script>"""


def _esc(t: str) -> str:
    return html.escape(t, quote=True)


def _html(t: str) -> str:
    """Texto do material para HTML: escapa tudo e transforma a marcação de fórmula em <sup>, <sub> ou MathML."""
    return leitor_pdf.para_html(t)


ITEM_LETRA = re.compile(r"^\(?[a-h]\)\s")


def para_html(doc: Documento, estilo: str = "padrao", manual: dict | None = None,
              pasta_imagens: Path | None = None, pasta_saida: Path | None = None,
              audio: bool = False, versao: str = "") -> str:
    if manual is None:
        from .regras import carregar_manual
        manual = carregar_manual()
    params = parametros_p2(manual)

    falas: list[str] = []

    def marca(fala: str) -> str:
        """Só na versão de áudio: liga o elemento ao trecho que será falado."""
        if not audio:
            return ""
        falas.append(_fala(fala))
        return f' data-fala="{len(falas) - 1}"'

    partes: list[str] = []
    abertura = False
    for i, b in enumerate(doc.blocos):
        if b.tipo == "titulo" and b.nivel <= 2:
            if abertura:
                partes.append("</section>")
            partes.append('<section class="pagina">')
            abertura = True
        elif not abertura:
            partes.append('<section class="pagina">')
            abertura = True

        if b.tipo == "titulo":
            n = min(max(b.nivel, 1), 3) + 1  # h1 é o título do documento
            partes.append(f"<h{n}{marca(b.texto)}>{_html(b.texto)}</h{n}>")
        elif b.tipo == "paragrafo":
            partes.append(f"<p{marca(b.texto)}>{_html(b.texto)}</p>")
        elif b.tipo == "lista":
            letras = all(ITEM_LETRA.match(x) for x in b.itens)
            partes.append(f"<ul{' class=\"itens\"' if letras else ''}{marca(('' if letras else 'Lista. ') + '. '.join(b.itens))}>"
                          + "".join(f"<li>{_html(x)}</li>" for x in b.itens) + "</ul>")
        elif b.tipo == "etapas":
            falado = " ".join(f"Passo {k}. {x}." for k, x in enumerate(b.itens, 1))
            partes.append(f'<ol class="etapas"{marca(falado)}>' + "".join(f"<li>{_html(x)}</li>" for x in b.itens) + "</ol>")
        elif b.tipo == "quadro":
            rotulo = f"quadro-{i}"
            partes.append(
                f'<aside class="quadro" aria-labelledby="{rotulo}"{marca(b.texto + ". " + ". ".join(b.itens))}><h2 id="{rotulo}">{_esc(b.texto)}</h2>'
                + "<ul>" + "".join(f"<li>{_html(x)}</li>" for x in b.itens) + "</ul></aside>"
            )
        elif b.tipo == "imagem":
            if b.alt:
                partes.append(f'<figure{marca("Imagem: " + b.alt)}><img src="{_esc(b.arquivo)}" alt="{_esc(b.alt)}">'
                              f"<figcaption>{_esc(b.alt)}</figcaption></figure>")
            else:
                partes.append(f'<figure{marca("Imagem sem descrição.")}><img src="{_esc(b.arquivo)}" alt="">'
                              '<p class="pendente">Descrição da imagem pendente: aguarda o professor.</p></figure>')
            if pasta_imagens and pasta_saida:
                destino = pasta_saida / b.arquivo
                destino.parent.mkdir(parents=True, exist_ok=True)
                if (pasta_imagens / b.arquivo).exists():
                    shutil.copyfile(pasta_imagens / b.arquivo, destino)
    if abertura:
        partes.append("</section>")

    # o texto da aula entra dentro de <script>: o "<" é trocado por um código, para ninguém fechar a tag
    falas_json = json.dumps(falas, ensure_ascii=False).replace("<", chr(92) + "u003c")

    tema = "amarelo" if estilo == "ampliada" else "creme"
    return f"""<!doctype html>
<html lang="pt-BR" data-tema="{tema}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{_esc(doc.titulo)}</title>
<style>{_css(estilo, params)}{CSS_AUDIO if audio else ""}</style>
</head>
<body>
<a class="pular" href="#conteudo">Pular para o conteúdo</a>
<main id="conteudo">
{_barra_ajustes(estilo)}
<h1>{_html(doc.titulo)}</h1>
{BARRA_AUDIO if audio else ""}
{chr(10).join(partes)}
</main>
{SCRIPT_AJUSTES.replace("__VERSAO__", versao or estilo).replace("__TEMA__", tema)}
{SCRIPT_AUDIO.replace("__FALAS__", falas_json) if audio else ""}
</body>
</html>
"""
