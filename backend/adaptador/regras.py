"""Lê as regras e os parâmetros do Manual em vez de deixar números fixos no código.

Fonte: docs/manual/padroes.json (e, quando existir, docs/manual/regras.json).
Se o manual mudar um número (ex.: 60 caracteres por linha), o backend acompanha.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
MANUAL = RAIZ / "docs" / "manual"


def _numero(texto: str, padrao: float) -> float:
    achou = re.search(r"\d+(?:[.,]\d+)?", str(texto))
    return float(achou.group().replace(",", ".")) if achou else padrao


def carregar_manual(pasta: Path = MANUAL) -> dict:
    manual = json.loads((pasta / "padroes.json").read_text(encoding="utf-8"))
    extra = pasta / "regras.json"
    manual["regras_extras"] = (
        json.loads(extra.read_text(encoding="utf-8")) if extra.exists() else []
    )
    return manual


def parametros_p2(manual: dict) -> dict:
    """Números do padrão P2 (página limpa e legível), já convertidos."""
    p2 = next(p for p in manual["padroes"] if p["id"] == "P2")["parametros"]
    return {
        "contraste_padrao": _numero(p2["contraste_texto_padrao"], 4.5),
        "contraste_ampliada": _numero(p2["contraste_versao_ampliada"], 7),
        "caracteres_por_linha": int(_numero(p2["caracteres_por_linha"], 60)),
        "pt_padrao": _numero(p2["corpo_do_texto_padrao"], 14),
        "pt_ampliada": _numero(p2["corpo_do_texto_ampliado"], 18),
    }


def versoes(manual: dict) -> dict:
    return {v["id"]: v for v in manual["versoes_geradas"]}
