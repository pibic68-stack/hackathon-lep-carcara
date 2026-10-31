"""Uso: python -m adaptador material.pdf --perfil exemplos/perfil-exemplo.json"""
import argparse
import json
import sys
from pathlib import Path

from . import ia, pipeline


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")  # console do Windows usa cp1252 e quebra com ✓
    p =argparse.ArgumentParser(description="Adapta um material de aula conforme o perfil do aluno.")
    p.add_argument("material", type=Path, help=".pdf, .pptx, .txt, .mp4 ou .mp3")
    p.add_argument("--perfil", type=Path, help="JSON do perfil do aluno (fictício!)")
    p.add_argument("--saida", type=Path, default=pipeline.SAIDA_PADRAO)
    p.add_argument("--modelo-audio", default="small", help="tiny, base, small... (só para vídeo/áudio)")
    a = p.parse_args()

    perfil = json.loads(a.perfil.read_text(encoding="utf-8")) if a.perfil else None
    r = pipeline.adaptar(a.material, perfil, a.saida, ia.obter_provedor(), a.modelo_audio)

    print(f"Material: {r['material']}   Pasta: {r['pasta']}")
    for nome, v in r["versoes"].items():
        print(f"  - {nome}: {v['status']}" + (f" ({v['arquivo']})" if "arquivo" in v else ""))
    for x in r["transformacoes_aplicadas"]:
        print("  ✓", x)
    for x in r["pendencias_para_o_professor"]:
        print("  ! ", x)
    return 0


if __name__ == "__main__":
    sys.exit(main())
