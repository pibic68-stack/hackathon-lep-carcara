"""Transforma um `Documento` em uma página HTML acessível (padrão P2: página limpa e legível).

O HTML não depende de internet: as fontes têm alternativas do sistema.
"""
from __future__ import annotations

import html
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
        font-size:{pt}pt; line-height:{1.8 if estilo == 'ampliada' else 1.6}; }}
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
.pendente {{ border:2px dashed var(--borda); padding:.5rem; font-style:italic; }}
.pular {{ position:absolute; left:-999px; }} .pular:focus {{ left:1rem; top:1rem; background:#fff; padding:.5rem; }}
:focus-visible {{ outline:4px solid var(--destaque); outline-offset:2px; }}
@media print {{ section.pagina {{ break-before:page; }} }}
"""


def _esc(t: str) -> str:
    return html.escape(t, quote=True)


def para_html(doc: Documento, estilo: str = "padrao", manual: dict | None = None,
              pasta_imagens: Path | None = None, pasta_saida: Path | None = None) -> str:
    if manual is None:
        from .regras import carregar_manual
        manual = carregar_manual()
    params = parametros_p2(manual)

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
            partes.append(f"<h{n}>{_esc(b.texto)}</h{n}>")
        elif b.tipo == "paragrafo":
            partes.append(f"<p>{_esc(b.texto)}</p>")
        elif b.tipo == "lista":
            partes.append("<ul>" + "".join(f"<li>{_esc(x)}</li>" for x in b.itens) + "</ul>")
        elif b.tipo == "etapas":
            partes.append('<ol class="etapas">' + "".join(f"<li>{_esc(x)}</li>" for x in b.itens) + "</ol>")
        elif b.tipo == "quadro":
            rotulo = f"quadro-{i}"
            partes.append(
                f'<aside class="quadro" aria-labelledby="{rotulo}"><h2 id="{rotulo}">{_esc(b.texto)}</h2>'
                + "<ul>" + "".join(f"<li>{_esc(x)}</li>" for x in b.itens) + "</ul></aside>"
            )
        elif b.tipo == "imagem":
            if b.alt:
                partes.append(f'<figure><img src="{_esc(b.arquivo)}" alt="{_esc(b.alt)}">'
                              f"<figcaption>{_esc(b.alt)}</figcaption></figure>")
            else:
                partes.append(f'<figure><img src="{_esc(b.arquivo)}" alt="">'
                              '<p class="pendente">Descrição da imagem pendente: aguarda o professor.</p></figure>')
            if pasta_imagens and pasta_saida:
                destino = pasta_saida / b.arquivo
                destino.parent.mkdir(parents=True, exist_ok=True)
                if (pasta_imagens / b.arquivo).exists():
                    shutil.copyfile(pasta_imagens / b.arquivo, destino)
    if abertura:
        partes.append("</section>")

    return f"""<!doctype html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{_esc(doc.titulo)}</title>
<style>{_css(estilo, params)}</style>
</head>
<body>
<a class="pular" href="#conteudo">Pular para o conteúdo</a>
<main id="conteudo">
<h1>{_esc(doc.titulo)}</h1>
{chr(10).join(partes)}
</main>
</body>
</html>
"""
