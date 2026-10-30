#!/usr/bin/env python3
"""Monta a aba de instruções da PRISMA a partir da fonte única.

Uso:  python3 web/prisma-instrucoes/build.py
Lê:   docs/manual/padroes.json  e  docs/manual/manual-prisma-v1.pdf
Gera: web/prisma-instrucoes/index.html          (página completa, pronta para o site)
      web/prisma-instrucoes/padroes.json        (cópia, para o backend ler)
      web/prisma-instrucoes/manual-prisma-v1.pdf (cópia, para o botão de download)
      web/prisma-instrucoes/_previa_artifact.html (versão para a prévia no Claude)
"""
import json
import shutil
from pathlib import Path

AQUI = Path(__file__).parent
RAIZ = AQUI.parent.parent
MANUAL = RAIZ / "docs" / "manual"

dados = json.loads((MANUAL / "padroes.json").read_text(encoding="utf-8"))
modelo = (AQUI / "src" / "pagina.html").read_text(encoding="utf-8")
corpo = modelo.replace("__DADOS__", json.dumps(dados, ensure_ascii=False))

# Página completa para o site: o link baixa o PDF.
completa = ('<!doctype html>\n<html lang="pt-BR">\n<head>\n<meta charset="utf-8">\n'
            '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n'
            '<meta name="description" content="Instruções da PRISMA: mini curso e manual de padrões de acessibilidade.">\n'
            '</head>\n<body>\n' + corpo.replace("__DOWNLOAD_ATTR__", "download") + "\n</body>\n</html>\n")
(AQUI / "index.html").write_text(completa, encoding="utf-8")

# Prévia no Claude: o visualizador bloqueia downloads, então o link só abre o PDF.
(AQUI / "_previa_artifact.html").write_text(corpo.replace("__DOWNLOAD_ATTR__", 'target="_blank" rel="noopener"'), encoding="utf-8")

shutil.copy(MANUAL / "padroes.json", AQUI / "padroes.json")
pdf = MANUAL / "manual-prisma-v1.pdf"
if pdf.exists():
    shutil.copy(pdf, AQUI / "manual-prisma-v1.pdf")
print("ok:", AQUI / "index.html")
