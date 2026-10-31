#!/usr/bin/env python3
"""Monta a aba de instruções da PRISMA a partir da fonte única.

Uso:  python3 web/prisma-instrucoes/build.py
Lê:   docs/manual/padroes.json  e  docs/manual/manual-prisma-v1.pdf
      web/prisma-instrucoes/src/pagina.html  (estrutura e código)  +  src/estilo.css (visual)
Gera: web/prisma-instrucoes/index.html          (página para o site: usa ../css, ../js e ../assets do próprio site)
      web/prisma-instrucoes/padroes.json        (cópia, para o backend ler)
      web/prisma-instrucoes/manual-prisma-v1.pdf (cópia, para o botão de download)
      web/prisma-instrucoes/_previa/            (só para ver a aba fora do site, na prévia do Claude; não vai para o Git)

O visual vem dos arquivos do site (css/tokens.css, css/base.css, css/componentes.css, js/acessibilidade.js).
Se o time mudar cores ou fontes em tokens.css, a aba acompanha sem precisar rodar este script de novo.
"""
import json
import shutil
from pathlib import Path

AQUI = Path(__file__).parent
WEB = AQUI.parent
RAIZ = WEB.parent
MANUAL = RAIZ / "docs" / "manual"

dados = json.loads((MANUAL / "padroes.json").read_text(encoding="utf-8"))
modelo = (AQUI / "src" / "pagina.html").read_text(encoding="utf-8")
estilo = (AQUI / "src" / "estilo.css").read_text(encoding="utf-8")
modelo = modelo.replace("__ESTILO__", estilo).replace("__DADOS__", json.dumps(dados, ensure_ascii=False))


def montar(base, index, entrar, download):
    return (modelo.replace("__BASE__", base).replace("__INDEX__", index)
            .replace("__ENTRAR__", entrar).replace("__DOWNLOAD_ATTR__", download))


# Página do site: fica em web/prisma-instrucoes/, então os arquivos do site estão um nível acima.
(AQUI / "index.html").write_text(montar("../", "../index.html", "../entrar.html", "download"), encoding="utf-8")

# Prévia fora do site (o visualizador do Claude bloqueia downloads e só serve arquivos da própria pasta):
# mesma página, com os arquivos do site copiados ao lado e os links do menu desativados.
previa = AQUI / "_previa"
if previa.exists():
    shutil.rmtree(previa)
for sub in ("css", "js", "assets/img", "assets/fontes"):
    (previa / sub).mkdir(parents=True)
for nome in ("tokens.css", "base.css", "componentes.css"):
    shutil.copy(WEB / "css" / nome, previa / "css" / nome)
for nome in ("acessibilidade.js", "icones.js"):
    shutil.copy(WEB / "js" / nome, previa / "js" / nome)
for nome in ("prisma-logo.svg", "favicon.png"):
    shutil.copy(WEB / "assets" / "img" / nome, previa / "assets" / "img" / nome)
for f in (WEB / "assets" / "fontes").glob("*.woff2"):
    shutil.copy(f, previa / "assets" / "fontes" / f.name)
(previa / "index.html").write_text(montar("", "#curso", "#curso", 'target="_blank" rel="noopener"'), encoding="utf-8")

shutil.copy(MANUAL / "padroes.json", AQUI / "padroes.json")
pdf = MANUAL / "manual-prisma-v1.pdf"
if pdf.exists():
    shutil.copy(pdf, AQUI / "manual-prisma-v1.pdf")
    shutil.copy(pdf, previa / "manual-prisma-v1.pdf")
print("ok:", AQUI / "index.html")
