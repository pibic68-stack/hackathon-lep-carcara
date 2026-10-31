"""Cache em disco: a demo não pode depender da internet nem de esperar a IA.

Tudo que é lento ou caro (transcrição de vídeo, respostas da IA) é guardado em
backend/cache/ e reaproveitado. A chave é a "impressão digital" (sha256) do conteúdo:
se o arquivo ou o pedido mudar, o cache não é usado.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path

PASTA = (Path(os.environ["PRISMA_DADOS"]) / "cache" if os.environ.get("PRISMA_DADOS")
         else Path(__file__).resolve().parents[1] / "cache")


def impressao_digital(*partes: bytes | str) -> str:
    h = hashlib.sha256()
    for p in partes:
        h.update(p if isinstance(p, bytes) else p.encode("utf-8"))
        h.update(b"\x00")
    return h.hexdigest()[:16]


def arquivo(caminho: Path, extras: str = "") -> str:
    return impressao_digital(Path(caminho).read_bytes(), extras)


def pasta_de(chave: str) -> Path:
    p = PASTA / chave
    p.mkdir(parents=True, exist_ok=True)
    return p


def ler(chave: str, nome: str):
    f = PASTA / chave / f"{nome}.json"
    return json.loads(f.read_text(encoding="utf-8")) if f.exists() else None


def gravar(chave: str, nome: str, dados) -> None:
    (pasta_de(chave) / f"{nome}.json").write_text(
        json.dumps(dados, ensure_ascii=False, indent=2), encoding="utf-8"
    )
