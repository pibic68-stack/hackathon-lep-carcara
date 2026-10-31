"""Formato interno do material: uma lista de blocos.

Todo leitor (PDF, PowerPoint, vídeo, texto) devolve um `Documento`.
Toda regra do manual recebe um `Documento` e devolve outro. Assim, cada peça
é independente e dá para testar sozinha.
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Optional

# Tipos de bloco: titulo, paragrafo, lista, etapas, imagem, quadro
TIPOS = {"titulo", "paragrafo", "lista", "etapas", "imagem", "quadro"}


@dataclass
class Bloco:
    tipo: str
    texto: str = ""                      # titulo, paragrafo, quadro (título do quadro)
    itens: list[str] = field(default_factory=list)  # lista, etapas, quadro
    nivel: int = 2                       # nível do título (1 a 3)
    arquivo: str = ""                    # imagem: caminho relativo ao HTML
    alt: Optional[str] = None            # imagem: descrição; None = ainda não existe


@dataclass
class Documento:
    titulo: str
    blocos: list[Bloco] = field(default_factory=list)
    origem: str = ""                     # nome do arquivo original
    aplicados: list[str] = field(default_factory=list)   # o que foi mudado (para o professor)
    pendencias: list[str] = field(default_factory=list)  # o que exige revisão humana

    def para_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def de_dict(cls, d: dict) -> "Documento":
        blocos = [Bloco(**b) for b in d.get("blocos", [])]
        return cls(d["titulo"], blocos, d.get("origem", ""),
                   d.get("aplicados", []), d.get("pendencias", []))
