# Carcará 3301 · Hackathon LEP (Educação)

> Time de alunos do IME no hackathon da Liga de Empreendedorismo da Praia Vermelha.
> **Trilhas:** 1 (Inclusão e acessibilidade) + 4 (Aprendizagem individualizada).

## PRISMA

**Plataforma de Recursos Inclusivos e Sala de Materiais Acessíveis.**
Protótipo do site em [`web/`](web/README.md): abra `web/index.html` com duplo clique.

## A ideia em uma frase

**Ajudar o professor a fazer todos os alunos, inclusive os alunos PCD, aprenderem juntos o mesmo conteúdo**:
a ferramenta identifica as barreiras de cada aluno, adapta o material da aula e gera um guia prático para o professor e a família.

> Rascunho. Reescrevam esta frase até caber num tweet. Ela é a base do pitch.

## Como funciona (fluxo)

```
1. PERFIL       2. MATERIAL      3. ADAPTAÇÃO          4. GUIA / RELATÓRIO      5. MEDIR DE NOVO
necessidades -> aula original -> versões acessíveis -> para professor e      -> mini-check: todos
funcionais      (PDF, texto,     (regras do Manual)    família                   aprenderam?
do aluno        slide)                                                           ajusta o perfil
```

O **Manual de Acessibilidade** (`docs/manual/`) não é um entregável separado: ele é a **base de regras**
que a ferramenta aplica. Cada regra do manual vira uma automação no código.

## Princípios (não negociáveis)

- **Identificar barreiras, não diagnosticar.** A ferramenta não diz se a criança "tem autismo".
  Ela registra necessidades funcionais (ex.: "precisa de instruções em etapas") e, quando for o caso,
  orienta a família a procurar um profissional.
- **O professor revisa e aprova** tudo o que a IA gera antes de chegar ao aluno.
- **Mesmo conteúdo para todos**: muda a forma, não o objetivo de aprendizagem.
- **Dados de crianças são sensíveis (LGPD)**: na demo, usar só alunos fictícios.
- **A própria interface precisa ser acessível** (contraste, teclado, leitor de tela).

## Estrutura do repositório

| Pasta | Conteúdo | Responsável |
|---|---|---|
| `docs/pesquisa/` | Matriz de barreiras, fontes, dados para o pitch | Pesquisa |
| `docs/manual/` | Manual de acessibilidade (regras de adaptação) | Pesquisa + todos |
| `backend/` | Python: leitura do material, adaptações, IA | IA/Backend |
| `web/` | HTML/CSS/JS: telas do professor | Frontend |
| `relatorios/` | Modelo do guia/relatório (LaTeX → PDF) e perfis fictícios | Dados/Relatórios |
| `pitch/` | Roteiro da demo e slides | Produto/Pitch |

Divisão detalhada: [`docs/divisao-tarefas.md`](docs/divisao-tarefas.md)

## Como contribuir

1. `git pull` antes de começar.
2. Crie sua branch: `git checkout -b seu-nome/o-que-esta-fazendo`
3. Faça commits pequenos com mensagens claras.
4. `git push` e abra um **Pull Request** para a `main`. Alguém do time revisa.
5. **Nunca** suba chaves de API ou arquivos `.env`.

## Time

| Nome | Papel | GitHub |
|---|---|---|
| | Pesquisa e Manual | |
| | IA e Backend | |
| | Frontend e Acessibilidade | |
| | Relatórios, Dados e Pitch | |
