# Memória do projeto (lida pelo Claude em toda sessão)

Time Carcará 3301 (4 alunos do IME) no hackathon da Liga de Empreendedorismo da Praia Vermelha. Tema: educação.

## Decisões já tomadas
- Ideia escolhida: adaptador de aula inclusiva. Mescla a trilha 1 (inclusão e acessibilidade) com a trilha 4 (aprendizagem individualizada).
- Fluxo: perfil de necessidades → material da aula → adaptações (regras do Manual) → guia para professor e família → mini-check para medir de novo.
- O Manual de Acessibilidade é a base de regras da ferramenta (`docs/manual/regras.json`), não um documento solto.
- Princípios: identificar barreiras, nunca diagnosticar; o professor aprova o que a IA gera; mesmo conteúdo para todos; alunos fictícios (LGPD); interface acessível.
- Divisão do time em 4 frentes: `docs/divisao-tarefas.md`.
- Site (`web/`): público é o ensino fundamental (1º ao 9º ano). Plataforma multidisciplinar: um mesmo tema visto por Matemática, Geografia, Ciências, História, Português e Música.
- Site: estilo inspirado no cofounder.co. Cena em pixel art no topo (gerada por `web/img/gerar_cena.py`), página em papel claro, logo em serifa fina, poucos blocos. Não poluir: menos seções e menos texto é melhor.
- Site: a ferramenta aponta a dificuldade do aluno (sinal para o professor), nunca laudo. Adapta o material para daltonismo, dislexia/leitura cansativa, baixa visão e excesso de informação. Necessidades descritas em palavras do dia a dia.
- Site: nome provisório "Trama". Tema da demo: "A água que usamos", aluno fictício A, 5º ano. HTML/CSS/JS puro, sem build, fontes locais (Atkinson Hyperlegible e Instrument Serif, licença OFL).
- Os códigos R-DISL-01, R-BVIS-01 e R-FOCO-01 na demo são provisórios; só R-DALT-01 vem de `docs/divisao-tarefas.md`. Alinhar com `docs/manual/regras.json` quando existir.

## Regras para o Claude
- Responder em português.
- Depois de uma compactação, ou se faltar contexto, reler `prompts/conversas/` e `docs/` antes de responder.
- Registrar aqui toda decisão nova importante do time.
- Toda conversa é exportada para `prompts/` pelos hooks em `.claude/settings.json`. Não remover.
- Nunca commitar segredos nem dados reais de alunos.
- Antes de mexer no site, ler `web/README.md`. Cor nunca sozinha (sempre com símbolo, padrão ou palavra), foco visível, navegação por teclado e contraste mínimo de 4,5:1 no texto.
- Trabalhar em branch e abrir Pull Request para a `main`. Não dar push direto na `main`.
