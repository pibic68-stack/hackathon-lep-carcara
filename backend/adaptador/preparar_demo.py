"""Prepara a apresentação: passa os materiais de teste pela IA com toda a paciência, ANTES da hora.

Cada resposta que a IA dá fica guardada em backend/cache/. Depois, na apresentação, quando o professor
enviar o mesmo arquivo, o PRISMA usa a resposta guardada: sai em segundos, mesmo com o Google ocupado
(erro 503) ou sem internet.

Uso:  python -m adaptador.preparar_demo [pasta]     (padrão: materiais-teste/ na raiz do projeto)
      ou dois cliques em materiais-teste/preparar-para-apresentacao.bat

Insiste por até 20 minutos: a cada rodada só refaz o que ainda faltou (o que deu certo já está guardado).
"""
from __future__ import annotations

import sys
import tempfile
import time
from pathlib import Path

from . import ia, pipeline

RAIZ = Path(__file__).resolve().parents[2]
EXTENSOES = {".pdf", ".pptx", ".txt", ".wav", ".mp3", ".m4a", ".mp4", ".webm", ".mov"}
# todas as versões e todos os ajustes de uma vez: o que a apresentação puder pedir já fica guardado
PERFIL = {"necessidades": ["daltonismo", "leitura_facil", "baixa_visao"], "preferencias": ["audio"]}
LIMITE = 20 * 60
ESPERA = 60


def faltando(r: dict) -> list[str]:
    """O que ainda depende da IA neste material."""
    falta = [f"{v}: {d.get('motivo', '')}" for v, d in r["versoes"].items() if d["status"] in ("falhou", "pendente_ia")]
    # "indisponível" = a IA não respondeu (vale tentar de novo); resposta ruim já guardada não muda ao repetir
    falta += [p for p in r["pendencias_para_o_professor"] if "indisponível" in p]
    falta += [f"imagem sem descrição: {i['arquivo']}" for i in r.get("imagens", []) if not i["alt"]]
    return falta


def main() -> int:
    pasta = Path(sys.argv[1]) if len(sys.argv) > 1 else RAIZ / "materiais-teste"
    arquivos = sorted(p for p in pasta.iterdir() if p.suffix.lower() in EXTENSOES)
    if not arquivos:
        print(f"Nenhum material em {pasta}.")
        return 1
    provedor = ia.obter_provedor()
    if not provedor:
        print("A IA está desligada: falta a chave do Gemini em backend/.env. Abra o publicar.bat uma vez e cole a chave.")
        return 1
    print(f"Preparando {len(arquivos)} material(is) com a IA ({provedor.modelo}).")
    print("Pode deixar rodando: se o Google estiver ocupado, eu espero e tento de novo.\n")

    inicio = time.time()
    pendentes = list(arquivos)
    rodada = 0
    with tempfile.TemporaryDirectory() as saida:
        while pendentes and time.time() - inicio < LIMITE:
            rodada += 1
            print(f"--- rodada {rodada} ---")
            ainda = []
            for arq in pendentes:
                t0 = time.time()
                try:
                    r = pipeline.adaptar(arq, PERFIL, Path(saida), provedor, nome_pasta=arq.stem)
                    falta = faltando(r)
                except Exception as erro:                       # transcrição falhou, arquivo estranho...
                    falta = [str(erro)]
                if falta:
                    ainda.append(arq)
                    print(f"  [faltou] {arq.name} ({time.time() - t0:.0f} s): {falta[0][:110]}")
                else:
                    print(f"  [pronto] {arq.name} ({time.time() - t0:.0f} s)")
            pendentes = ainda
            if pendentes and time.time() - inicio < LIMITE:
                print(f"\nO Google não respondeu tudo. Nova rodada em {ESPERA} s (só o que faltou)...\n")
                time.sleep(ESPERA)
    print()
    if pendentes:
        print("Não consegui tudo em 20 minutos. Faltou: " + ", ".join(p.name for p in pendentes))
        print("O que deu certo já está guardado. Rode de novo mais tarde para completar.")
        return 1
    print(f"Tudo pronto em {(time.time() - inicio) / 60:.1f} min. Na apresentação, envie estes mesmos arquivos:")
    print("as versões com IA vão sair em segundos.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
