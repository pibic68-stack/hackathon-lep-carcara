# Registro das conversas com IA

Esta pasta guarda **tudo que o time conversou com a IA** durante o hackathon, para os avaliadores verem como usamos a IA.

| Caminho | O que é |
|---|---|
| `conversas/sessao-XXXXXXXX.md` | Conversa completa de cada sessão, atualizada a cada resposta |
| `exportar_conversa.py` | Script que converte o histórico do Claude Code em Markdown |
| `hooks/salvar_conversa.sh` | Hook que exporta, faz commit e envia para o GitHub sozinho |

## Por que nada se perde na compactação

Quando a conversa fica longa, o Claude a **compacta** (resume) para economizar contexto.
O resumo fica no lugar da conversa *na memória do Claude*, mas o **arquivo de histórico (.jsonl)
continua com tudo**. O script sempre reexporta a partir desse arquivo.

## Como funciona

O arquivo `.claude/settings.json` deste repositório registra dois hooks:

- **Stop**: roda depois de cada resposta do Claude → atualiza `conversas/` e faz push.
- **PreCompact**: roda antes de compactar → guarda o snapshot e faz push.

## Para os outros membros do time

- **Usando Claude Code dentro deste repositório:** os hooks já funcionam sozinhos (o Claude Code pede para aprovar na primeira vez).
- **Usando o Claude no chat (claude.ai / app):** não há hooks. exporte o texto e salve em `conversas/`.
- **Exportar manualmente** qualquer sessão do Claude Code:
  ```bash
  python3 prompts/exportar_conversa.py ~/.claude/projects/<pasta>/<sessao>.jsonl
  ```

## Privacidade

O exportador remove avisos internos do sistema, raciocínio interno, saídas brutas de ferramentas, endereços de e-mail e chaves de API conhecidas (Google, Anthropic/OpenAI, GitHub).
Mesmo assim, **não colem chaves, senhas ou dados reais de alunos** na conversa.
