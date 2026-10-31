"""Lê as regras e os parâmetros do Manual em vez de deixar números fixos no código.

Fonte: docs/manual/padroes.json. Cada padrão tem `criterios` com `id` (P2.1...), `limite`
e `automacao`. Se o time mudar um limite no manual (ex.: 60 caracteres por linha),
o backend acompanha sem mexer no código.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
MANUAL = RAIZ / "docs" / "manual"


def carregar_manual(pasta: Path = MANUAL) -> dict:
    return json.loads((pasta / "padroes.json").read_text(encoding="utf-8"))


def criterio(manual: dict, codigo: str) -> dict:
    """Busca um critério pelo código, ex.: criterio(manual, "P2.4")."""
    padrao = codigo.split(".")[0]
    for p in manual["padroes"]:
        if p["id"] == padrao:
            for c in p.get("criterios", []):
                if c["id"] == codigo:
                    return c
    raise KeyError(f"Critério {codigo} não existe em padroes.json")


def limites(manual: dict, codigo: str) -> list[float]:
    """Números que vêm depois de ≥ ou ≤ no limite do critério (ex.: '≥ 4,5:1 ...; ≥ 7:1' -> [4.5, 7])."""
    texto = criterio(manual, codigo)["limite"]
    return [float(n.replace(",", ".")) for n in re.findall(r"[≥≤]\s*(\d+(?:[.,]\d+)?)", texto)]


def parametros_p2(manual: dict) -> dict:
    """Números do padrão P2 (página limpa e legível), já convertidos."""
    contraste = limites(manual, "P2.1")
    corpo = limites(manual, "P2.2")
    return {
        "contraste_padrao": contraste[0],
        "contraste_ampliada": contraste[1],
        "pt_padrao": corpo[0],
        "pt_ampliada": corpo[1],
        "caracteres_por_linha": int(limites(manual, "P2.4")[0]),
        "espacamento_minimo": limites(manual, "P2.6")[0],
    }


def maximo_etapas_hoje_vamos(manual: dict) -> int:
    return int(limites(manual, "P6.1")[0])


def versoes(manual: dict) -> dict:
    return {v["id"]: v for v in manual["versoes_geradas"]}
