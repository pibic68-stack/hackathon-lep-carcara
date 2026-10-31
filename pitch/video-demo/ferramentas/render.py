"""Transforma uma cena HTML em vídeo, quadro a quadro (Chrome sem janela + ffmpeg).

    python render.py bloco-3            -> ../saida/cenas/bloco-3.mp4
    python render.py bloco-3 --foto 12  -> ../saida/fotos/bloco-3-12.0.png (um quadro, para conferir)
    python render.py bloco-2 --alfa     -> .mov com transparência (para pôr por cima de vídeo)

A cena fica em ../cenas/<nome>.html. O servidor local serve:
    /cenas/  -> ../cenas
    /web/    -> o site (variável PRISMA_WEB ou ../../../web)
    /saida/  -> ../saida
A cena recebe window.TEMPOS (de ../saida/audio/tempos.json) antes de carregar.
"""
import argparse, functools, http.server, json, os, subprocess, threading
from pathlib import Path

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parent
WEB = Path(os.environ.get("PRISMA_WEB", RAIZ.parent.parent / "web"))
FPS = 30
W, H = 1920, 1080


class Servidor(http.server.SimpleHTTPRequestHandler):
    mapas = {"/cenas/": RAIZ / "cenas", "/web/": WEB, "/saida/": RAIZ / "saida"}

    def translate_path(self, path):
        path = path.split("?", 1)[0].split("#", 1)[0]
        from urllib.parse import unquote
        path = unquote(path)
        for pre, pasta in self.mapas.items():
            if path.startswith(pre):
                return str(pasta / path[len(pre):])
        return str(RAIZ / path.lstrip("/"))

    def log_message(self, *a):
        pass


def ligar_servidor():
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Servidor)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv.server_address[1]


SEEK = """(t) => {
  const ms = t * 1000;
  const docs = [document, ...[...document.querySelectorAll('iframe')].map(f => { try { return f.contentDocument } catch (e) { return null } }).filter(Boolean)];
  for (const d of docs) for (const a of d.getAnimations()) { a.pause(); a.currentTime = ms; }
  if (window.aoTempo) window.aoTempo(t);
}"""


def abrir(pw, nome, alfa):
    porta = ligar_servidor()
    nav = pw.chromium.launch(channel="chrome", args=["--force-color-profile=srgb", "--hide-scrollbars"])
    pag = nav.new_page(viewport={"width": W, "height": H}, device_scale_factor=1)
    tempos = RAIZ / "saida" / "audio" / "tempos.json"
    pag.add_init_script("window.TEMPOS = " + (tempos.read_text(encoding="utf-8") if tempos.exists() else "{}") + ";"
                        + ("window.ALFA = true;" if alfa else ""))
    pag.goto(f"http://127.0.0.1:{porta}/cenas/{nome}.html", wait_until="networkidle")
    pag.evaluate("document.fonts.ready")
    pag.evaluate("window.pronto ? window.pronto() : null")
    pag.wait_for_timeout(400)
    dur = pag.evaluate("window.DURACAO || 5")
    return nav, pag, dur


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("nome")
    ap.add_argument("--foto", type=float, nargs="*")
    ap.add_argument("--alfa", action="store_true")
    ap.add_argument("--fps", type=int, default=FPS)
    a = ap.parse_args()
    from playwright.sync_api import sync_playwright
    with sync_playwright() as pw:
        nav, pag, dur = abrir(pw, a.nome, a.alfa)
        if a.foto is not None:
            pasta = RAIZ / "saida" / "fotos"
            pasta.mkdir(parents=True, exist_ok=True)
            for t in a.foto:
                pag.evaluate(SEEK, t)
                pag.wait_for_timeout(60)
                arq = pasta / f"{a.nome}-{t:.1f}.png"
                pag.screenshot(path=str(arq))
                print(arq)
            nav.close()
            return
        pasta = RAIZ / "saida" / "cenas"
        pasta.mkdir(parents=True, exist_ok=True)
        n = int(round(dur * a.fps))
        if a.alfa:
            destino = pasta / f"{a.nome}.mov"
            cod = ["-c:v", "qtrle"]
            fmt = "png"
        else:
            destino = pasta / f"{a.nome}.mp4"
            cod = ["-c:v", "libx264", "-preset", "medium", "-crf", "16", "-pix_fmt", "yuv420p"]
            fmt = "jpeg"
        ff = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "image2pipe", "-framerate", str(a.fps),
                               "-i", "-", *cod, str(destino)], stdin=subprocess.PIPE)
        for i in range(n):
            pag.evaluate(SEEK, i / a.fps)
            if fmt == "png":
                img = pag.screenshot(type="png", omit_background=True)
            else:
                img = pag.screenshot(type="jpeg", quality=93)
            ff.stdin.write(img)
            if i % (a.fps * 5) == 0:
                print(f"  {a.nome}: {i / a.fps:.0f}/{dur:.0f} s", flush=True)
        ff.stdin.close()
        ff.wait()
        nav.close()
        print(destino)


if __name__ == "__main__":
    main()
