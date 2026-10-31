"""Ponto de ligação da IA. Ainda NÃO há provedor escolhido pelo time.

A ideia: o resto do código só conhece a interface `Provedor`. Quando o time decidir
(Claude, Gemini, modelo local...), escreve-se uma classe aqui e nada mais muda.
Sem provedor, o sistema continua funcionando com as regras determinísticas e marca
como "pendente" tudo que exigiria IA.
"""
from __future__ import annotations

import os
from typing import Protocol

from . import cache


class Provedor(Protocol):
    nome: str

    def simplificar(self, texto: str, nivel: str) -> str:
        """Reescreve em Leitura Fácil (nivel 'lf2' ou 'lf1')."""

    def descrever_imagem(self, caminho_imagem: str) -> str:
        """Texto alternativo para a imagem."""

    def roteiro_audio(self, texto: str) -> str:
        """Texto pronto para ser lido em voz alta."""


def obter_provedor() -> Provedor | None:
    """Lê a variável PRISMA_IA. Por enquanto nenhum valor é reconhecido."""
    nome = os.environ.get("PRISMA_IA", "").strip().lower()
    if not nome:
        return None
    raise NotImplementedError(
        f"Provedor de IA '{nome}' ainda não implementado. Veja backend/README.md, seção IA."
    )


def com_cache(tarefa: str, entrada: str, produzir) -> str:
    """Só chama a IA se esse pedido exato nunca foi feito antes."""
    chave = cache.impressao_digital(tarefa, entrada)
    guardado = cache.ler("ia", chave)
    if guardado is not None:
        return guardado["resposta"]
    resposta = produzir()
    cache.gravar("ia", chave, {"tarefa": tarefa, "resposta": resposta})
    return resposta
