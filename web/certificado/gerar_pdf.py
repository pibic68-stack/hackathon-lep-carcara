"""Gera o certificado do mini curso PRISMA em PDF, já com o nome da pessoa.

Usa o mesmo modelo do site (modelo.html) e o Chrome ou o Edge sem janela.
Não precisa instalar nada além de um desses navegadores.

Exemplos:
    python web/certificado/gerar_pdf.py --papel prof --nome "Ana Souza"
    python web/certificado/gerar_pdf.py --papel est --nome "Leo Lima" --data 2026-10-31 --saida leo.pdf
    python web/certificado/gerar_pdf.py --exemplos      # recria os 3 PDFs de exemplos/

No backend (FastAPI), basta chamar gerar_pdf(papel, nome, data) e devolver os bytes:
    from fastapi.responses import Response
    pdf = gerar_pdf("fam", usuario.nome)
    return Response(pdf, media_type="application/pdf",
                    headers={"Content-Disposition": 'attachment; filename="certificado-prisma.pdf"'})
"""
from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import tempfile
from datetime import date
from pathlib import Path
from urllib.parse import urlencode, quote

PASTA = Path(__file__).resolve().parent
MODELO = PASTA / "modelo.html"
PAPEIS = {"prof": "professor", "fam": "familia", "est": "aluno"}
APELIDOS = {"professor": "prof", "professora": "prof", "familia": "fam", "família": "fam",
            "aluno": "est", "aluna": "est", "estudante": "est"}

EXEMPLOS = [("prof", "Marina Duarte"), ("fam", "Carlos Pereira"), ("est", "Lia Santos")]  # nomes fictícios


def achar_navegador() -> str:
    """Procura Chrome, Edge ou Chromium. A variável PRISMA_NAVEGADOR tem prioridade."""
    candidatos = [os.environ.get("PRISMA_NAVEGADOR", "")]
    pf = [os.environ.get(k, "") for k in ("PROGRAMFILES", "PROGRAMFILES(X86)", "LOCALAPPDATA")]
    for base in filter(None, pf):
        candidatos += [rf"{base}\Google\Chrome\Application\chrome.exe",
                       rf"{base}\Microsoft\Edge\Application\msedge.exe"]
    candidatos += ["/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
                   "google-chrome", "chromium", "chromium-browser", "microsoft-edge"]
    for c in candidatos:
        if c and (Path(c).exists() or shutil.which(c)):
            return shutil.which(c) or c
    raise RuntimeError("Não achei Chrome nem Edge. Instale um deles ou defina PRISMA_NAVEGADOR.")


def gerar_pdf(papel: str, nome: str, data: str | None = None) -> bytes:
    """Devolve os bytes do PDF do certificado."""
    papel = APELIDOS.get(papel.lower(), papel.lower())
    if papel not in PAPEIS:
        raise ValueError(f"papel deve ser prof, fam ou est (veio {papel!r})")
    nome = " ".join(nome.split())
    if len(nome) < 2:
        raise ValueError("nome vazio")
    data = data or date.today().isoformat()

    # os dados vão depois do #: o modelo lê dali e nada sai do computador
    url = MODELO.as_uri() + "#" + urlencode({"papel": papel, "nome": nome, "data": data}, quote_via=quote)
    with tempfile.TemporaryDirectory() as tmp:
        saida = Path(tmp) / "certificado.pdf"
        cmd = [achar_navegador(), "--headless=new", "--disable-gpu", "--no-first-run",
               "--allow-file-access-from-files", f"--user-data-dir={Path(tmp) / 'perfil'}",
               "--no-pdf-header-footer", "--virtual-time-budget=4000",
               f"--print-to-pdf={saida}", url]
        subprocess.run(cmd, check=True, capture_output=True, timeout=60)
        if not saida.exists():
            raise RuntimeError("O navegador não gerou o PDF.")
        return saida.read_bytes()


def nome_arquivo(papel: str, nome: str) -> str:
    base = "".join(c if c.isalnum() else "-" for c in nome.lower()).strip("-")
    return f"certificado-prisma-{PAPEIS[papel]}-{base}.pdf"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--papel", help="prof, fam ou est")
    ap.add_argument("--nome", help="nome de quem recebe")
    ap.add_argument("--data", help="AAAA-MM-DD (padrão: hoje)")
    ap.add_argument("--saida", help="arquivo .pdf de saída")
    ap.add_argument("--exemplos", action="store_true", help="recria os 3 PDFs de exemplos/")
    a = ap.parse_args()

    if a.exemplos:
        (PASTA / "exemplos").mkdir(exist_ok=True)
        for papel, nome in EXEMPLOS:
            destino = PASTA / "exemplos" / f"certificado-{PAPEIS[papel]}.pdf"
            destino.write_bytes(gerar_pdf(papel, nome, a.data or "2026-10-31"))
            print("ok", destino.relative_to(PASTA.parent.parent))
        return 0
    if not (a.papel and a.nome):
        ap.error("use --papel e --nome (ou --exemplos)")
    papel = APELIDOS.get(a.papel.lower(), a.papel.lower())
    destino = Path(a.saida or nome_arquivo(papel, a.nome))
    destino.write_bytes(gerar_pdf(papel, a.nome, a.data))
    print("ok", destino)
    return 0


if __name__ == "__main__":
    sys.exit(main())
