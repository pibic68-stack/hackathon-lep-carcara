"""Gera ../roteiro.pdf a partir de ../roteiro.md, com as fontes e cores do site."""
import markdown
from playwright.sync_api import sync_playwright
import render
md = (render.RAIZ / "roteiro.md").read_text(encoding="utf-8")
corpo = markdown.markdown(md, extensions=["tables"])
html = """<!doctype html><html lang="pt-BR"><head><meta charset="utf-8"><title>Roteiro do vídeo PRISMA</title>
<link rel="stylesheet" href="/web/css/tokens.css"><style>
@page { size: A4; margin: 18mm 16mm; }
body { font-family: var(--fonte-texto); color: var(--tinta); font-size: 13pt; line-height: 1.5; background: #fff; }
h1 { font-family: var(--fonte-titulo); color: var(--ceu-escuro); font-size: 26pt; margin: 0 0 8pt; }
h2 { font-family: var(--fonte-titulo); font-size: 18pt; border-bottom: 3px solid var(--tinta); padding-bottom: 4pt; margin-top: 20pt; }
h3 { font-size: 14pt; color: var(--laranja-escuro); margin: 16pt 0 6pt; }
table { border-collapse: collapse; width: 100%; font-size: 11.5pt; margin: 8pt 0; }
th, td { border: 2px solid var(--tinta); padding: 5pt 7pt; text-align: left; vertical-align: top; }
th { background: var(--ceu-claro); }
blockquote { border-left: 6px solid var(--sol); background: var(--sol-claro); margin: 10pt 0; padding: 6pt 12pt; }
code { font-family: var(--fonte-mono); font-size: 11pt; background: var(--papel-2); padding: 0 4pt; }
hr { border: 0; border-top: 2px dashed var(--tinta-3); margin: 18pt 0; }
h3 + p, h3 ~ p { font-size: 14pt; }
</style></head><body>""" + corpo + "</body></html>"
(render.RAIZ / "saida").mkdir(exist_ok=True)
tmp = render.RAIZ / "saida" / "roteiro.html"; tmp.write_text(html, encoding="utf-8")
porta = render.ligar_servidor()
with sync_playwright() as pw:
    nav = pw.chromium.launch(channel="chrome"); pag = nav.new_page()
    pag.goto(f"http://127.0.0.1:{porta}/saida/roteiro.html", wait_until="networkidle")
    pag.evaluate("document.fonts.ready")
    pag.pdf(path=str(render.RAIZ / "roteiro.pdf"), format="A4", print_background=True,
            margin={"top": "18mm", "bottom": "18mm", "left": "16mm", "right": "16mm"})
    nav.close()
print("ok")
