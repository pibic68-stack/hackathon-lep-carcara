"""Estado compartilhado na Vercel: todas as cópias do site enxergam as mesmas contas e materiais.

Por que existe: na Vercel cada pedido pode cair numa cópia diferente do servidor, cada uma com a sua pasta /tmp.
Sem isto, a pessoa entra (cópia A) e o painel pergunta "quem sou eu?" para a cópia B, que não conhece a
sessão: volta para a tela de entrada.

Como funciona (simples, feito para a demonstração):
- a pasta de dados inteira (banco SQLite, materiais, respostas da IA) vira um .tar.gz guardado num Postgres;
- antes de cada pedido, a cópia confere a versão guardada; se for mais nova que a dela, baixa e abre;
- depois de um pedido que mudou algum arquivo, ela sobe a pasta de novo com versão + 1.
Ligado só quando há DATABASE_URL (ou POSTGRES_URL): a Vercel cria essa variável ao ligar um Postgres (Neon)
em Storage. Sem ela, nada muda.
"""
from __future__ import annotations

import io
import os
import shutil
import tarfile
import threading
from pathlib import Path

_trava = threading.Lock()
_versao_local = -1


def url() -> str:
    return os.environ.get("DATABASE_URL") or os.environ.get("POSTGRES_URL") or ""


def ligado() -> bool:
    return bool(url()) or bool(os.environ.get("PRISMA_ESTADO_ARQUIVO"))


class _Postgres:
    def __init__(self, endereco: str):
        import psycopg
        self.con = psycopg.connect(endereco, autocommit=True, connect_timeout=10)
        self.con.execute("CREATE TABLE IF NOT EXISTS prisma_estado (id INTEGER PRIMARY KEY, versao BIGINT NOT NULL, "
                         "dados BYTEA NOT NULL)")

    def versao(self) -> int:
        r = self.con.execute("SELECT versao FROM prisma_estado WHERE id = 1").fetchone()
        return r[0] if r else 0

    def dados(self) -> tuple[int, bytes] | None:
        r = self.con.execute("SELECT versao, dados FROM prisma_estado WHERE id = 1").fetchone()
        return (r[0], bytes(r[1])) if r else None

    def guardar(self, dados: bytes) -> int:
        r = self.con.execute("INSERT INTO prisma_estado (id, versao, dados) VALUES (1, 1, %s) "
                             "ON CONFLICT (id) DO UPDATE SET versao = prisma_estado.versao + 1, dados = EXCLUDED.dados "
                             "RETURNING versao", (dados,)).fetchone()
        return r[0]


class _Arquivo:
    """Para os testes: o "banco" é um arquivo local."""
    def __init__(self, caminho: str):
        self.caminho = Path(caminho)

    def versao(self) -> int:
        d = self.dados()
        return d[0] if d else 0

    def dados(self) -> tuple[int, bytes] | None:
        if not self.caminho.exists():
            return None
        bruto = self.caminho.read_bytes()
        return int.from_bytes(bruto[:8], "big"), bruto[8:]

    def guardar(self, dados: bytes) -> int:
        v = self.versao() + 1
        self.caminho.write_bytes(v.to_bytes(8, "big") + dados)
        return v


_armazem = None


def _abrir():
    global _armazem
    if _armazem is None:
        _armazem = _Arquivo(os.environ["PRISMA_ESTADO_ARQUIVO"]) if os.environ.get("PRISMA_ESTADO_ARQUIVO") \
            else _Postgres(url())
    return _armazem


def foto(pasta: Path) -> tuple:
    """Assinatura rápida da pasta (nome, tamanho, data de cada arquivo): diz se algo mudou."""
    itens = []
    for raiz, _, arquivos in os.walk(pasta):
        for a in arquivos:
            p = os.path.join(raiz, a)
            try:
                st = os.stat(p)
            except OSError:
                continue
            itens.append((p, st.st_size, st.st_mtime_ns))
    return tuple(sorted(itens))


def baixar(pasta: Path) -> None:
    """Se o estado guardado é mais novo que o desta cópia, troca a pasta pelo guardado."""
    global _versao_local
    with _trava:
        try:
            arm = _abrir()
            v = arm.versao()
            if v <= _versao_local:
                return
            d = arm.dados()
        except Exception as erro:              # banco fora do ar: segue com o que tem
            print(f"[estado] não consegui ler o estado guardado: {erro}", flush=True)
            return
        if not d:
            return
        versao, dados = d
        if pasta.exists():
            shutil.rmtree(pasta, ignore_errors=True)
        pasta.mkdir(parents=True, exist_ok=True)
        with tarfile.open(fileobj=io.BytesIO(dados), mode="r:gz") as tar:
            tar.extractall(pasta, filter="data")
        _versao_local = versao


def subir(pasta: Path) -> None:
    """Guarda a pasta inteira como a versão mais nova."""
    global _versao_local
    with _trava:
        buf = io.BytesIO()
        with tarfile.open(fileobj=buf, mode="w:gz", compresslevel=3) as tar:
            tar.add(pasta, arcname=".")
        try:
            _versao_local = _abrir().guardar(buf.getvalue())
        except Exception as erro:
            print(f"[estado] não consegui guardar o estado: {erro}", flush=True)


def instalar(app, pasta: Path) -> None:
    """Liga a sincronização em volta de cada pedido do FastAPI."""
    if not ligado():
        return

    @app.middleware("http")
    async def sincronizar(request, chamar):
        caminho = request.url.path
        if not caminho.startswith("/api/"):           # páginas e arquivos do site não mexem nos dados
            return await chamar(request)
        baixar(pasta)
        antes = foto(pasta)
        resposta = await chamar(request)
        if foto(pasta) != antes:
            subir(pasta)
        return resposta
