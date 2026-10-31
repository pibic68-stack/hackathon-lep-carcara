"""Transforma um `Documento` em uma página HTML acessível (padrão P2: página limpa e legível).

O HTML não depende de internet: as fontes têm alternativas do sistema.
"""
from __future__ import annotations

import html
import json
import shutil
from pathlib import Path

from .modelo import Documento
from .regras import parametros_p2

FONTE = "'Atkinson Hyperlegible', 'Lexend', Verdana, Arial, sans-serif"

# Cores da identidade (CLAUDE.md). Os testes conferem o contraste contra o manual.
ESTILOS = {
    "padrao": {"texto": "#1A1A1A", "fundo": "#FFFFFF", "destaque": "#1F5FBF",
               "quadro_fundo": "#EEF3FB", "borda": "#C26A00"},
    "ampliada": {"texto": "#000000", "fundo": "#FFFFFF", "destaque": "#0B3A8F",
                 "quadro_fundo": "#FFF4D6", "borda": "#000000"},
}


def luminancia(hexcor: str) -> float:
    r, g, b = (int(hexcor[i:i + 2], 16) / 255 for i in (1, 3, 5))
    f = lambda c: c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    return 0.2126 * f(r) + 0.7152 * f(g) + 0.0722 * f(b)


def contraste(a: str, b: str) -> float:
    la, lb = sorted((luminancia(a), luminancia(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)


def _css(estilo: str, params: dict) -> str:
    cor = ESTILOS[estilo]
    pt = params["pt_ampliada"] if estilo == "ampliada" else params["pt_padrao"]
    return f"""
:root {{ --texto:{cor['texto']}; --fundo:{cor['fundo']}; --destaque:{cor['destaque']};
         --quadro:{cor['quadro_fundo']}; --borda:{cor['borda']}; }}
* {{ box-sizing: border-box; }}
body {{ margin:0; background:var(--fundo); color:var(--texto); font-family:{FONTE};
        font-size:{pt}pt; line-height:{max(params['espacamento_minimo'], 1.8 if estilo == 'ampliada' else 1.6)};
        text-align:left; hyphens:none; font-style:normal; }}
main {{ max-width:{params['caracteres_por_linha']}ch; margin:0 auto; padding:1.5rem 1rem 4rem; }}
h1, h2, h3 {{ line-height:1.25; color:var(--destaque); }}
h1 {{ font-size:1.7em; }} h2 {{ font-size:1.35em; margin-top:2rem; }} h3 {{ font-size:1.15em; }}
p, li {{ margin:.6em 0; }}
ol.etapas {{ padding-left:1.6em; }}
ol.etapas li {{ margin:.9em 0; padding-left:.3em; }}
ol.etapas li::marker {{ font-weight:700; color:var(--destaque); }}
aside.quadro {{ background:var(--quadro); border:3px solid var(--borda); border-radius:6px;
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
.barra-audio button, .barra-audio select { font:inherit; font-size:1rem; min-height:44px; padding:.3rem .9rem;
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
    """Texto como deve ser falado: símbolos viram o nome da forma."""
    for simbolo, nome in FALA_SIMBOLOS.items():
        texto = texto.replace(f"({simbolo})", f"({nome})")
    return texto


def _esc(t: str) -> str:
    return html.escape(t, quote=True)


def para_html(doc: Documento, estilo: str = "padrao", manual: dict | None = None,
              pasta_imagens: Path | None = None, pasta_saida: Path | None = None,
              audio: bool = False) -> str:
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
            partes.append(f"<h{n}{marca(b.texto)}>{_esc(b.texto)}</h{n}>")
        elif b.tipo == "paragrafo":
            partes.append(f"<p{marca(b.texto)}>{_esc(b.texto)}</p>")
        elif b.tipo == "lista":
            partes.append(f"<ul{marca('Lista. ' + '. '.join(b.itens))}>" + "".join(f"<li>{_esc(x)}</li>" for x in b.itens) + "</ul>")
        elif b.tipo == "etapas":
            falado = " ".join(f"Passo {k}. {x}." for k, x in enumerate(b.itens, 1))
            partes.append(f'<ol class="etapas"{marca(falado)}>' + "".join(f"<li>{_esc(x)}</li>" for x in b.itens) + "</ol>")
        elif b.tipo == "quadro":
            rotulo = f"quadro-{i}"
            partes.append(
                f'<aside class="quadro" aria-labelledby="{rotulo}"{marca(b.texto + ". " + ". ".join(b.itens))}><h2 id="{rotulo}">{_esc(b.texto)}</h2>'
                + "<ul>" + "".join(f"<li>{_esc(x)}</li>" for x in b.itens) + "</ul></aside>"
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

    return f"""<!doctype html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{_esc(doc.titulo)}</title>
<style>{_css(estilo, params)}{CSS_AUDIO if audio else ""}</style>
</head>
<body>
<a class="pular" href="#conteudo">Pular para o conteúdo</a>
<main id="conteudo">
<h1>{_esc(doc.titulo)}</h1>
{BARRA_AUDIO if audio else ""}
{chr(10).join(partes)}
</main>
{SCRIPT_AUDIO.replace("__FALAS__", falas_json) if audio else ""}
</body>
</html>
"""
