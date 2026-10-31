"""Entrada do PRISMA na Vercel (a Vercel procura um `app` neste arquivo).

Na Vercel só a pasta /tmp aceita escrita e ela zera de tempos em tempos: contas e materiais de lá são
temporários. Serve como site público para experimentar (contas de demonstração, sem senha).
Para rodar no seu computador, use backend/ (README.md) ou o publicar.bat.
"""
import os
import sys
from pathlib import Path

os.environ.setdefault("PRISMA_DADOS", "/tmp/prisma")
os.environ.setdefault("PRISMA_DEMO_PUBLICA", "1")
Path(os.environ["PRISMA_DADOS"]).mkdir(parents=True, exist_ok=True)
sys.path.insert(0, str(Path(__file__).resolve().parent / "backend"))

from adaptador.api import app  # noqa: E402,F401
from adaptador import estado_nuvem  # noqa: E402

# Várias cópias do servidor na Vercel: contas e materiais ficam num Postgres (Storage › Neon) e todas enxergam igual.
estado_nuvem.instalar(app, Path(os.environ["PRISMA_DADOS"]))
