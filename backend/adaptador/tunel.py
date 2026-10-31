"""Cria o link público do PRISMA (Cloudflare, trycloudflare.com) e só o mostra quando ele FUNCIONA.

Uso (o publicar.bat chama sozinho):  python -m adaptador.tunel CAMINHO_DO_CLOUDFLARED

Por que existe: o link do Cloudflare aparece na tela antes de estar pronto. Quem abre cedo demais,
ou numa rede que bloqueia o túnel, vê o "Error 1033". Aqui:
1. espera o túnel se ligar à Cloudflare (se a rede bloquear, tenta o outro protocolo);
2. abre o próprio link pela internet até ele responder; só então mostra "LINK PRONTO";
3. copia o link (Ctrl+V cola) e grava em link.txt;
4. confere o link a cada 20 s; se cair, cria outro sozinho e avisa;
5. não deixa o computador dormir enquanto a janela estiver aberta;
6. mostra também o endereço na rede local (mesmo Wi-Fi), que funciona mesmo sem túnel.
"""
from __future__ import annotations

import os
import re
import socket
import subprocess
import sys
import threading
import time
import urllib.request
from pathlib import Path

LOCAL = "http://127.0.0.1:8000"
URL = re.compile(r"https://[a-z0-9-]+\.trycloudflare\.com")
RAIZ = Path(__file__).resolve().parents[2]
ARQUIVO_LINK = RAIZ / "link.txt"
ARQUIVO_COMPARTILHAR = RAIZ / "compartilhar.json"      # lido pela página compartilhar.html (QR code)


def anunciar(estado: str, link: str | None, rede: str | None) -> None:
    try:
        import json
        ARQUIVO_COMPARTILHAR.write_text(json.dumps({"estado": estado, "link": link, "rede": rede,
                                                    "quando": time.strftime("%H:%M")}), encoding="utf-8")
    except OSError:
        pass


def ip_na_rede() -> str | None:
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))           # não envia nada: só descobre qual placa de rede sai para a internet
            return s.getsockname()[0]
    except OSError:
        return None


def nao_dormir() -> None:
    """Windows: mantém o computador acordado enquanto este processo roda (sem mudar configuração nenhuma)."""
    if os.name == "nt":
        try:
            import ctypes
            ctypes.windll.kernel32.SetThreadExecutionState(0x80000000 | 0x00000001)   # CONTINUOUS | SYSTEM_REQUIRED
        except Exception:
            pass


def responde(url: str, tempo: float = 8) -> bool:
    try:
        pedido = urllib.request.Request(url + "/api/saude", headers={"User-Agent": "PRISMA-conferencia"})
        with urllib.request.urlopen(pedido, timeout=tempo) as r:
            return r.status == 200 and b'"ok"' in r.read(200)
    except Exception:
        return False


def copiar(texto: str) -> bool:
    if os.name != "nt":
        return False
    try:
        subprocess.run("clip", input=texto.encode("utf-16"), check=True, shell=True)
        return True
    except Exception:
        return False


def caixa(linhas: list[str]) -> None:
    largura = max(len(x) for x in linhas) + 4
    print()
    print("  " + "#" * largura)
    for x in linhas:
        print("  #  " + x.ljust(largura - 4) + "#")
    print("  " + "#" * largura)
    print()


class Tunel:
    def __init__(self, cloudflared: str, protocolo: str, comando: list[str] | None = None):
        self.url: str | None = None
        self.conectado = False
        self.erros: list[str] = []
        self.proc = subprocess.Popen(
            comando or [cloudflared, "tunnel", "--no-autoupdate", "--protocol", protocolo, "--url", LOCAL],
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding="utf-8", errors="replace")
        threading.Thread(target=self._ler, daemon=True).start()

    def _ler(self) -> None:
        for linha in self.proc.stdout:
            if not self.url and (m := URL.search(linha)) and "api.trycloudflare" not in m.group(0):
                self.url = m.group(0)
            if "Registered tunnel connection" in linha:
                self.conectado = True
            if " ERR " in linha or "failed to" in linha.lower():
                self.erros.append(linha.strip())

    def parar(self) -> None:
        if self.proc.poll() is None:
            self.proc.terminate()
            try:
                self.proc.wait(5)
            except subprocess.TimeoutExpired:
                self.proc.kill()


def ligar(cloudflared: str, espera: float = 40, comando: list[str] | None = None) -> Tunel | None:
    for protocolo in ("http2", "quic"):
        print(f"  Abrindo o túnel ({protocolo})...")
        t = Tunel(cloudflared, protocolo, comando)
        limite = time.time() + espera
        while time.time() < limite and not (t.url and t.conectado) and t.proc.poll() is None:
            time.sleep(0.5)
        if not (t.url and t.conectado):
            t.parar()
            print("  A rede não deixou o túnel se ligar por este caminho.")
            continue
        print("  Túnel ligado. Conferindo se o link já abre pela internet (até 1 minuto)...")
        limite = time.time() + 75
        while time.time() < limite:
            if responde(t.url):
                return t
            time.sleep(3)
        print("  O link não respondeu a tempo. Tentando de novo...")
        t.parar()
    return None


def testar_ia() -> None:
    """Antes da apresentação: a IA está respondendo? Em quanto tempo? (pergunta curtinha, sem cache)"""
    try:
        from . import ia
        provedor = ia.obter_provedor()
    except Exception as erro:          # configuração incompleta
        print(f"  IA: {erro}")
        return
    if not provedor:
        print("  IA: desligada (sem chave). Leitura Fácil e descrição de imagens não vão sair.")
        return
    print("  Testando a IA...")
    inicio = time.time()
    try:
        provedor.gerar("Responda só com a palavra: ok", "Teste de conexão do PRISMA.")
        print(f"  IA: respondendo em {time.time() - inicio:.1f} s (modelo {provedor.modelo}).")
    except Exception as erro:
        print(f"  [AVISO] IA não respondeu agora: {erro}")
        print("          O site funciona; as versões com IA podem demorar ou falhar. No painel use \"Testar a IA agora\".")


def main() -> int:
    if len(sys.argv) < 2:
        print("Uso: python -m adaptador.tunel CAMINHO_DO_CLOUDFLARED")
        return 2
    cloudflared = sys.argv[1]
    nao_dormir()
    ip = ip_na_rede()
    na_rede = f"http://{ip}:8000" if ip else None
    if not responde(LOCAL, 3):
        print("  [ERRO] O servidor do PRISMA não está respondendo. Abra o publicar.bat de novo.")
        return 1
    testar_ia()
    try:
        from . import demo
        demo.main()
    except Exception as erro:
        print(f"  (contas de demonstração: {erro})")
    anunciar("criando", None, na_rede)
    print("  A página com o QR code está aberta no navegador: " + LOCAL + "/compartilhar.html")

    tentativas = 0
    while True:
        tentativas += 1
        t = ligar(cloudflared)
        if not t:
            linhas = ["NAO CONSEGUI CRIAR O LINK PUBLICO.",
                      "Esta rede bloqueia o tunel (comum em escola e universidade).",
                      "Saidas: 1) use o celular como roteador (4G) e abra de novo;",
                      "        2) apresente neste computador: " + LOCAL]
            if na_rede:
                linhas.append("        3) outro aparelho no MESMO Wi-Fi: " + na_rede)
            caixa(linhas)
            anunciar("bloqueado", None, na_rede)
            if tentativas >= 3:
                return 1
            print("  Tentando de novo em 20 segundos (Ctrl+C para parar)...")
            time.sleep(20)
            continue

        anunciar("pronto", t.url, na_rede)
        copiou = copiar(t.url)
        try:
            ARQUIVO_LINK.write_text(t.url + "\n", encoding="utf-8")
        except OSError:
            pass
        linhas = ["LINK PRONTO (testado agora pela internet):", "", "   " + t.url, ""]
        if copiou:
            linhas.append("Ja esta copiado: e so colar (Ctrl+V) no WhatsApp ou e-mail.")
        linhas += ["Tambem gravado em link.txt, na pasta do PRISMA.",
                   "Funciona enquanto ESTA janela e o computador estiverem ligados."]
        if na_rede:
            linhas.append("No mesmo Wi-Fi, tambem abre em: " + na_rede)
        caixa(linhas)

        falhas = 0
        while t.proc.poll() is None:
            time.sleep(20)
            if responde(t.url):
                if falhas:
                    print(time.strftime("  %H:%M") + "  O link voltou a responder.")
                falhas = 0
                continue
            falhas += 1
            print(time.strftime("  %H:%M") + f"  O link não respondeu ({falhas}/3).")
            if falhas >= 3:
                break
        t.parar()
        anunciar("caiu", None, na_rede)
        print()
        print("  O LINK CAIU. Criando um novo... (o endereço vai MUDAR: mande o novo para quem for abrir)")


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        sys.exit(0)
