#!/bin/sh
# Renderiza todas as cenas (uso: sh render_tudo.sh [blocos...])
cd "$(dirname "$0")"
for b in ${@:-3 4 5 6 7}; do python render.py bloco-$b || exit 1; done
python render.py bloco-2 --alfa
