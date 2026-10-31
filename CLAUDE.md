# Memória do projeto (lida pelo Claude em toda sessão)

Time Carcará 3301 (4 alunos do IME) no hackathon da Liga de Empreendedorismo da Praia Vermelha. Tema: educação.

## Decisões já tomadas
- Nome do projeto (30/10): **PRISMA**, sigla de Plataforma de Recursos Inclusivos e Sala de Materiais Acessíveis. A ideia por trás: uma aula entra e sai em várias versões, para todos. Ainda falta ver se o @ e o domínio estão livres.
- Ideia escolhida: adaptador de aula inclusiva. Mescla a trilha 1 (inclusão e acessibilidade) com a trilha 4 (aprendizagem individualizada).
- Fluxo: perfil de necessidades → material da aula → adaptações (regras do Manual) → guia para professor e família → mini-check para medir de novo.
- O Manual de Acessibilidade é a base de regras da ferramenta (`docs/manual/padroes.json`), não um documento solto.
- Princípios: identificar barreiras, nunca diagnosticar; o professor aprova o que a IA gera; mesmo conteúdo para todos; alunos fictícios (LGPD); interface acessível.
- Divisão do time em 4 frentes: `docs/divisao-tarefas.md`.
- O carcará é o mascote do time (aparece no site como mascote, não como nome do produto).
- Site (protótipo de interface) em `web/`: HTML/CSS/JS puro, abre com duplo clique, sem internet. Estilo pixel inspirado no cofounder.co. Plano em `docs/plano-site.md`, guia em `web/README.md`.
- Personagens: coruja = professor, preguiça = aluno, urso = família. A escola do topo é a imagem do time (`web/assets/img/escola.jpg`).
- Seletor de necessidades da demo: daltonismo (protanopia, deuteranopia, tritanopia, acromatopsia), baixa visão e TEA, cada um com sua versão da ficha "O caminho da água" (`web/js/dados.js` e `web/js/material.js`). A barra de acessibilidade do site também tem esses 4 modos de daltonismo, que trocam a paleta do próprio site.
- Login ainda é falso; o backend entra só em `web/js/auth.js`. Adler é o responsável pela pesquisa.
- Plataforma: o professor envia o material → a plataforma transforma → o professor aprova → o material fica salvo e listado numa biblioteca que os alunos acessam. As versões servem para todos, não só para alunos PCD.
- Manual PRISMA v1.0 (30/10, noite): 10 padrões (P1 cor, P2 página limpa, P3 Linguagem Simples em níveis, P4 imagem descrita, P5 mais de um caminho, P6 estrutura previsível, P7 do concreto ao abstrato, P8 conexões entre disciplinas, P9 material vivo, P10 professor no comando) e 51 critérios verificáveis com código (P3.1 etc.), limite e quem verifica (automatico / ia_revisao / manual). Fonte única: `docs/manual/padroes.json` (também tem necessidades, dados dos gráficos, glossário e referências). `docs/manual/build_manual.py` gera o PDF; `web/prisma-instrucoes/build.py` gera a aba Instruções do site (ligada ao menu da home; usa o CSS e a barra de acessibilidade do site). Nunca editar `index.html` ou o PDF à mão.
- P7, P8 e P9 vieram da colega professora do grupo: material concreto (letras móveis, material dourado, Cuisenaire) para TDAH/DI; integração entre disciplinas; o material se constrói durante o processo de ensino.
- O nome antigo `regras.json` foi substituído por `padroes.json` em todo o repositório.
- Identidade visual (31/10): a do site, em `web/css/tokens.css`: Pixelify Sans (títulos curtos), Atkinson Hyperlegible Next (texto e TODOS os números, porque o 5 do Pixelify parece S), Departure Mono (rótulos); céu #1F6FB2 e laranja-escuro #A3401F para texto e gráficos; papel #FBF7EE e tinta #1E2235. A logo é `web/assets/img/prisma-logo.svg` (prisma pixelado). Manual em PDF e aba Instruções já seguem isso. O gerador de HTML do backend (`renderizador.py`) ainda usa a identidade antiga (Lexend, #1F5FBF, #C26A00): decisão pendente do time.
- Fontes lidas e lacunas: `docs/pesquisa/fontes.md` e `docs/pesquisa/lacunas.md`.
- Backend (30/10): pacote Python `backend/adaptador/` (guia em `backend/README.md`). Fluxo: leitor por formato (.txt/.pdf/.pptx/vídeo) → `Documento` (lista de blocos) → regras determinísticas P1.1, P4.1, P6.1 a P6.3 → HTML acessível (P2) + `revisao.json` (P10.1). Parâmetros numéricos vêm de `padroes.json`. Não existe uma linguagem que adapte tudo: são bibliotecas por formato (PyMuPDF, python-pptx, faster-whisper). A IA só entra em Leitura Fácil (P3) e descrição de imagens (P4), via `ia.py`. IA escolhida (30/10): Gemini, pela chave gratuita do Google AI Studio (sem cartão); troca de serviço = uma função `gerar()`. Plano gratuito pode treinar com o conteúdo: só material de domínio público e alunos fictícios. A versão Ouvir (P5) usa a voz do navegador, sem IA. Chave em `backend/.env` (fora do Git, modelo em `.env.exemplo`; nunca colar a chave no chat). Testado ao vivo em 30/10: modelo padrão `gemini-3.1-flash-lite` (o 2.5 estava desativado e o 3.8 não respondeu). Cache em `backend/cache/` é versionado de propósito (demo offline). API FastAPI em `backend/adaptador/api.py` (`python -m adaptador.api`, também serve o `web/`): `POST /api/adaptar` cria rascunho; o professor descreve imagens e aprova (`/aprovar`); só publicado aparece em `/api/biblioteca` (P10.1). Sem login ainda.
- Relatório de coerência e acessibilidade entre as partes do time (31/10): `docs/relatorio-coerencia-acessibilidade.md`. Itens para o grupo decidir juntos; nada do site foi alterado além do link Instruções no menu.

## Regras para o Claude
- Responder em português.
- Depois de uma compactação, ou se faltar contexto, reler `prompts/conversas/` e `docs/` antes de responder.
- A cada mensagem do Adler: `git fetch` e revisar o que os colegas subiram (commits, arquivos fora do lugar, conflitos) e manter o repositório organizado.
- Registrar aqui toda decisão nova importante do time.
- Toda conversa é exportada para `prompts/` pelos hooks em `.claude/settings.json`. Não remover.
- Nunca commitar segredos nem dados reais de alunos.
