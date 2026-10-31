# PRISMA · Plataforma de Recursos Inclusivos e Sala de Materiais Acessíveis

> **Uma aula entra e várias versões saem.** A Sala de Materiais é a biblioteca que os alunos acessam.

Time **Carcará 3301** · Hackathon LEPV (Educação)

> Time de alunos do IME no hackathon da Liga de Empreendedorismo da Praia Vermelha.
> **Trilhas:** 1 (Inclusão e acessibilidade) + 4 (Aprendizagem individualizada).

## Como rodar (tudo junto: site, manual, login e IA)

```bash
cd backend
python -m pip install -r requirements.txt
python -m adaptador.api          # abra http://127.0.0.1:8000
```

Um servidor só entrega o site (`web/`), a aba Instruções (mini curso e manual), o login e a API.
Configuração em `backend/.env` (modelo em `backend/.env.exemplo`, que nunca leva segredos):

- `GEMINI_API_KEY`: chave da IA. Sem ela tudo funciona, só a Leitura Fácil e a descrição automática ficam pendentes.
- `PRISMA_CODIGO_ESCOLA`: código que o professor digita para criar conta. Sem ele, o cadastro fica fechado.

**Link público para a banca:** rode `publicar.bat` (Windows). Ele liga o servidor e cria um endereço
`https://...trycloudflare.com` que qualquer pessoa abre. O link só aparece depois de testado pela internet,
já vem copiado (Ctrl+V) e fica em `link.txt`. Muda a cada vez e só funciona enquanto este computador
e a janela estiverem ligados. Se a rede bloquear o túnel, use o celular como roteador; no mesmo Wi-Fi,
o site também abre em `http://IP-do-computador:8000`. Detalhes em [`backend/README.md`](backend/README.md).

### Quem entra e como

| Perfil | Como entra | O que faz |
|---|---|---|
| Professor | e-mail e senha (cria a conta com o código da escola) | cria turmas e alunos fictícios, envia o material, revisa e aprova |
| Aluno | código da turma + senha de 3 figurinhas | abre os materiais publicados, com as versões do seu jeito primeiro |
| Família | código da família | vê como o aluno aprende melhor e os materiais da turma |

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
que a ferramenta aplica. A maioria das regras vira automação no código; as outras pedem IA com revisão
do professor ou uma pessoa (dos 51 critérios: 31 automáticos, 18 de IA com revisão, 2 manuais).

### O mesmo fluxo com outros nomes (item C3 do relatório)

| Site (5 etapas, na tela) | Manual (6 etapas, no pitch) | Backend (código) |
|---|---|---|
| Perfil | (antes de tudo) | turmas e alunos com necessidades (`contas.py`) |
| Material | Enviar | `POST /api/adaptar` |
| Adaptação | Analisar + Transformar | `leitores.py` + `transformacoes.py` + `ia.py` |
| Guia | Revisar + Publicar | fila de revisão, `aprovar`, biblioteca da turma |
| Mini-check | Acompanhar | ainda não construído |

## Princípios (não negociáveis)

- **Identificar barreiras, não diagnosticar.** A ferramenta não diz se a criança "tem autismo".
  Ela registra necessidades funcionais (por exemplo, "precisa de instruções em etapas") e, quando for o caso,
  orienta a família a procurar um profissional.
- **O professor revisa e aprova** tudo o que a IA gera antes de chegar ao aluno.
- **Mesmo conteúdo para todos**: muda a forma, não o objetivo de aprendizagem.
- **Dados de crianças são sensíveis (LGPD)**: na demo, usar só alunos fictícios.
- **A própria interface precisa ser acessível** (contraste, teclado, leitor de tela).

## Estrutura do repositório

| Pasta | Conteúdo | Responsável |
|---|---|---|
| `docs/manual/padroes.json` | **Fonte única**: 10 padrões, 51 critérios, necessidades, dados, glossário e referências | Pesquisa |
| `docs/manual/manual-prisma-v1.pdf` | Manual em PDF (gerado por `build_manual.py`) | Pesquisa |
| `docs/pesquisa/` | Catálogo de fontes, lacunas e matriz de barreiras | Pesquisa |
| `web/prisma-instrucoes/` | Aba **Instruções** do site: mini curso + manual + PDF. Ver o `LEIA-ME.md` da pasta | Pesquisa → Frontend |
| `backend/` | Python: leitura do material, critérios, IA | IA/Backend |
| `web/` | Demais telas do site | Frontend |
| `relatorios/` | Guia para família e perfis fictícios | Dados/Relatórios |
| `pitch/` | Roteiro da demo e slides | Produto/Pitch |
| `prompts/` | Registro das conversas com IA para os avaliadores | Todos (automático) |

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
