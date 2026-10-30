# Memória do projeto (lida pelo Claude em toda sessão)

Time Carcará 3301 (4 alunos do IME) no hackathon da Liga de Empreendedorismo da Praia Vermelha. Tema: educação.

## Decisões já tomadas
- Nome do projeto (30/10): **PRISMA**, sigla de Plataforma de Recursos Inclusivos e Sala de Materiais Acessíveis. A ideia por trás: uma aula entra e sai em várias versões, para todos. Ainda falta ver se o @ e o domínio estão livres.
- Ideia escolhida: adaptador de aula inclusiva. Mescla a trilha 1 (inclusão e acessibilidade) com a trilha 4 (aprendizagem individualizada).
- Fluxo: perfil de necessidades → material da aula → adaptações (regras do Manual) → guia para professor e família → mini-check para medir de novo.
- O Manual de Acessibilidade é a base de regras da ferramenta (`docs/manual/padroes.json`), não um documento solto.
- Princípios: identificar barreiras, nunca diagnosticar; o professor aprova o que a IA gera; mesmo conteúdo para todos; alunos fictícios (LGPD); interface acessível.
- Divisão do time em 4 frentes: `docs/divisao-tarefas.md`. Adler é o responsável pela pesquisa.
- Plataforma: o professor envia o material → a plataforma transforma → o professor aprova → o material fica salvo e listado numa biblioteca que os alunos acessam. As versões servem para todos, não só para alunos PCD.
- Manual PRISMA v1.0 (30/10, noite): 10 padrões (P1 cor, P2 página limpa, P3 Linguagem Simples em níveis, P4 imagem descrita, P5 mais de um caminho, P6 estrutura previsível, P7 do concreto ao abstrato, P8 conexões entre disciplinas, P9 material vivo, P10 professor no comando) e 51 critérios verificáveis com código (P3.1 etc.), limite e quem verifica (automatico / ia_revisao / manual). Fonte única: `docs/manual/padroes.json` (também tem necessidades, dados dos gráficos, glossário e referências). `docs/manual/build_manual.py` gera o PDF; `web/prisma-instrucoes/build.py` gera a aba Instruções do site. Nunca editar `index.html` ou o PDF à mão.
- P7, P8 e P9 vieram da colega professora do grupo: material concreto (letras móveis, material dourado, Cuisenaire) para TDAH/DI; integração entre disciplinas; o material se constrói durante o processo de ensino.
- O nome antigo `regras.json` foi substituído por `padroes.json` em todo o repositório.
- Identidade visual: Lexend (títulos), Atkinson Hyperlegible (texto), IBM Plex Mono (códigos); azul #1F5FBF e âmbar #C26A00, validados para daltonismo.
- Fontes lidas e lacunas: `docs/pesquisa/fontes.md` e `docs/pesquisa/lacunas.md`.

## Regras para o Claude
- Responder em português.
- Depois de uma compactação, ou se faltar contexto, reler `prompts/conversas/` e `docs/` antes de responder.
- A cada mensagem do Adler: `git fetch` e revisar o que os colegas subiram (commits, arquivos fora do lugar, conflitos) e manter o repositório organizado.
- Registrar aqui toda decisão nova importante do time.
- Toda conversa é exportada para `prompts/` pelos hooks em `.claude/settings.json`. Não remover.
- Nunca commitar segredos nem dados reais de alunos.
