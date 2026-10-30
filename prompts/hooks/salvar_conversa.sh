#!/usr/bin/env bash
# Hook do Claude Code: exporta a conversa para prompts/conversas/ e envia ao GitHub.
# Uso (chamado pelo Claude Code, que manda um JSON com "transcript_path" na entrada padrão):
#   salvar_conversa.sh            -> depois de cada resposta (Stop)
#   salvar_conversa.sh compactacao -> antes de compactar (PreCompact), guarda uma foto fixa
set -u
# Windows: "python3" costuma ser só um atalho da Microsoft Store; usa o primeiro Python que funcionar.
PY=""
for c in python3 python py; do
  if "$c" -c "import sys" >/dev/null 2>&1; then PY="$c"; break; fi
done
[ -n "$PY" ] || exit 0
ETIQUETA="${1:-}"
REPO="$(cd "$(dirname "$0")/../.." && pwd)"

ENTRADA="$(cat)"
TRANSCRIPT="$(printf '%s' "$ENTRADA" | "$PY" -c 'import json,sys; print(json.load(sys.stdin).get("transcript_path",""))' 2>/dev/null)"
[ -n "$TRANSCRIPT" ] && [ -f "$TRANSCRIPT" ] || exit 0

"$PY" "$REPO/prompts/exportar_conversa.py" "$TRANSCRIPT" ${ETIQUETA:+--etiqueta "$ETIQUETA"} || exit 0

cd "$REPO" || exit 0
git add prompts/conversas >/dev/null 2>&1
git diff --cached --quiet && exit 0
MSG="Atualiza registro da conversa com IA"
[ -n "$ETIQUETA" ] && MSG="Registro da conversa antes da compactação"
git commit -q -m "$MSG" >/dev/null 2>&1 || exit 0
# Envia sem travar a sessão; se falhar (sem internet), vai no próximo push.
( git pull -q --rebase origin main && git push -q origin HEAD:main ) >/dev/null 2>&1 || true
exit 0
