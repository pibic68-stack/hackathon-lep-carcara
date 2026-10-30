# Memória do projeto (lida pelo Claude em toda sessão)

Time Carcará 3301 (4 alunos do IME) no hackathon da Liga de Empreendedorismo da Praia Vermelha. Tema: educação.

## Decisões já tomadas
- Ideia escolhida: adaptador de aula inclusiva. Mescla a trilha 1 (inclusão e acessibilidade) com a trilha 4 (aprendizagem individualizada).
- Fluxo: perfil de necessidades → material da aula → adaptações (regras do Manual) → guia para professor e família → mini-check para medir de novo.
- O Manual de Acessibilidade é a base de regras da ferramenta (`docs/manual/regras.json`), não um documento solto.
- Princípios: identificar barreiras, nunca diagnosticar; o professor aprova o que a IA gera; mesmo conteúdo para todos; alunos fictícios (LGPD); interface acessível.
- Divisão do time em 4 frentes: `docs/divisao-tarefas.md`.

## Regras para o Claude
- Responder em português.
- Depois de uma compactação, ou se faltar contexto, reler `prompts/conversas/` e `docs/` antes de responder.
- Registrar aqui toda decisão nova importante do time.
- Toda conversa é exportada para `prompts/` pelos hooks em `.claude/settings.json`. Não remover.
- Nunca commitar segredos nem dados reais de alunos.
