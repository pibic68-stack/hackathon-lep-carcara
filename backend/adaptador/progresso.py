"""Acompanhar a produção de um material enquanto ela acontece (o professor vê no painel).

O site manda um código qualquer no cabeçalho `X-Prisma-Acompanhar` junto com o envio e, enquanto espera,
pergunta `GET /api/progresso/{codigo}` a cada segundo. Aqui ficam: a etapa atual, os passos (lote 3 de 7),
um diário curto do que aconteceu (IA ocupada, nova tentativa, troca de modelo) e números da IA.

Sem acompanhamento (testes, linha de comando), todas as funções simplesmente não fazem nada.
"""
from __future__ import annotations

import contextvars
import threading
import time

_atual: contextvars.ContextVar["Acompanhamento | None"] = contextvars.ContextVar("prisma_progresso", default=None)
_todos: dict[str, "Acompanhamento"] = {}
_trava = threading.Lock()
GUARDAR_POR = 3600          # segundos


class Acompanhamento:
    def __init__(self, codigo: str, dono: int | None):
        self.codigo, self.dono = codigo, dono
        self.inicio = time.time()
        self.fim: float | None = None
        self.etapa = "Começando"
        self.passo = 0
        self.passos = 0
        self.diario: list[dict] = []
        self.ia = {"pedidos": 0, "segundos": 0.0, "tentativas_extras": 0, "falhas": 0, "modelo": "", "guardadas": 0}
        self.erro: str | None = None

    def anotar(self, texto: str, tipo: str = "info") -> None:
        self.diario.append({"s": round(time.time() - self.inicio, 1), "texto": texto, "tipo": tipo})
        del self.diario[:-60]

    def para_dict(self) -> dict:
        agora = self.fim or time.time()
        ia = dict(self.ia)
        ia["media"] = round(ia["segundos"] / ia["pedidos"], 1) if ia["pedidos"] else None
        ia["segundos"] = round(ia["segundos"], 1)
        return {"codigo": self.codigo, "etapa": self.etapa, "passo": self.passo, "passos": self.passos,
                "segundos": round(agora - self.inicio, 1), "terminou": self.fim is not None,
                "erro": self.erro, "diario": self.diario[-25:], "ia": ia}


def comecar(codigo: str | None, dono: int | None = None) -> "Acompanhamento | None":
    if not codigo:
        _atual.set(None)
        return None
    codigo = codigo[:64]
    a = Acompanhamento(codigo, dono)
    with _trava:
        limite = time.time() - GUARDAR_POR
        for k in [k for k, v in _todos.items() if v.inicio < limite]:
            del _todos[k]
        _todos[codigo] = a
    _atual.set(a)
    return a


def terminar(erro: str | None = None) -> None:
    a = _atual.get()
    if a:
        a.fim = time.time()
        a.erro = erro
        a.etapa = "Deu errado" if erro else "Pronto"
        a.anotar(erro or "Pronto.", "erro" if erro else "ok")
        _atual.set(None)


def obter(codigo: str) -> "Acompanhamento | None":
    with _trava:
        return _todos.get(codigo)


def etapa(texto: str, passos: int = 0) -> None:
    a = _atual.get()
    if a:
        a.etapa, a.passo, a.passos = texto, 0, passos
        a.anotar(texto)


def passo(texto: str | None = None) -> None:
    a = _atual.get()
    if a:
        a.passo += 1
        if texto:
            a.anotar(texto)


def anotar(texto: str, tipo: str = "info") -> None:
    a = _atual.get()
    if a:
        a.anotar(texto, tipo)


def pedido_ia(segundos: float, modelo: str) -> None:
    a = _atual.get()
    if a:
        a.ia["pedidos"] += 1
        a.ia["segundos"] += segundos
        a.ia["modelo"] = modelo


def tentativa_extra_ia() -> None:
    a = _atual.get()
    if a:
        a.ia["tentativas_extras"] += 1


def falha_ia() -> None:
    a = _atual.get()
    if a:
        a.ia["falhas"] += 1


def resposta_guardada() -> None:
    a = _atual.get()
    if a:
        a.ia["guardadas"] += 1
