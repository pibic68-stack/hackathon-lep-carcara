# Memória do projeto (lida pelo Claude em toda sessão)

Time Carcará 3301 (4 alunos do IME) no hackathon da Liga de Empreendedorismo da Praia Vermelha. Tema: educação.

## Decisões já tomadas
- Nome do projeto (30/10): **PRISMA**, sigla de Plataforma de Recursos Inclusivos e Sala de Materiais Acessíveis. A ideia por trás: uma aula entra e sai em várias versões, para todos. Ainda falta ver se o @ e o domínio estão livres.
- Ideia escolhida: adaptador de aula inclusiva. Mescla a trilha 1 (inclusão e acessibilidade) com a trilha 4 (aprendizagem individualizada).
- Fluxo: perfil de necessidades → material da aula → adaptações (regras do Manual) → guia para professor e família → mini-check para medir de novo.
- O Manual de Acessibilidade é a base de regras da ferramenta (`docs/manual/regras.json`), não um documento solto.
- Princípios: identificar barreiras, nunca diagnosticar; o professor aprova o que a IA gera; mesmo conteúdo para todos; alunos fictícios (LGPD); interface acessível.
- Divisão do time em 4 frentes: `docs/divisao-tarefas.md`.
- O carcará é o mascote do time (aparece no site como mascote, não como nome do produto).
- Site (protótipo de interface) em `web/`: HTML/CSS/JS puro, abre com duplo clique, sem internet. Estilo pixel inspirado no cofounder.co. Plano em `docs/plano-site.md`, guia em `web/README.md`.
- Personagens: coruja = professor, preguiça = aluno, urso = família. A escola do topo é a imagem do time (`web/assets/img/escola.jpg`).
- Seletor de necessidades da demo: daltonismo (protanopia, deuteranopia, tritanopia, acromatopsia), baixa visão e TEA, cada um com sua versão da ficha "O caminho da água" (`web/js/dados.js` e `web/js/material.js`). A barra de acessibilidade do site também tem esses 4 modos de daltonismo, que trocam a paleta do próprio site.
- Login ainda é falso; o backend entra só em `web/js/auth.js`. Adler é o responsável pela pesquisa.
- Plataforma: o professor envia o material → a plataforma transforma → o professor aprova → o material fica salvo e listado numa biblioteca que os alunos acessam. As versões servem para todos, não só para alunos PCD.
- Manual v0.1 (30/10): 7 padrões de transformação P1 a P7. A fonte única é `docs/manual/padroes.json`; `build_manual.py` gera o PDF. O manual também vai ser uma aba do site, com um mini curso interativo em 3 trilhas (professor/técnica, família/orientadora, estudante/Leitura Fácil). Protótipo em `web/minicurso/index.html`, aguardando o sinal verde do Adler.
- Identidade visual: Lexend (títulos), Atkinson Hyperlegible (texto), IBM Plex Mono (códigos); azul #1F5FBF e âmbar #C26A00, validados para daltonismo.
- Fontes lidas e lacunas: `docs/pesquisa/fontes.md` e `docs/pesquisa/lacunas.md`.

## Regras para o Claude
- Responder em português.
- Depois de uma compactação, ou se faltar contexto, reler `prompts/conversas/` e `docs/` antes de responder.
- Registrar aqui toda decisão nova importante do time.
- Toda conversa é exportada para `prompts/` pelos hooks em `.claude/settings.json`. Não remover.
- Nunca commitar segredos nem dados reais de alunos.
