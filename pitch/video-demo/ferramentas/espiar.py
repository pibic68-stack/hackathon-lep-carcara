"""Tira foto de páginas do site (1600x900) para escolher o que entra no vídeo."""
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright
import render
porta = render.ligar_servidor()
out = render.RAIZ / "saida" / "fotos"; out.mkdir(parents=True, exist_ok=True)
with sync_playwright() as pw:
    nav = pw.chromium.launch(channel="chrome")
    pag = nav.new_page(viewport={"width": 1600, "height": 900})
    for url in sys.argv[1:]:
        try:
            pag.goto(f"http://127.0.0.1:{porta}/web/{url}", wait_until="networkidle", timeout=15000)
        except Exception as e:
            print("erro", url, e)
        pag.wait_for_timeout(800)
        arq = out / ("site-" + url.replace("/", "_").replace("?", "_") + ".png")
        pag.screenshot(path=str(arq)); print(arq.name, pag.url)
    nav.close()
