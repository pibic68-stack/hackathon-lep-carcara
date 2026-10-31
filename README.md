# PRISMA · Plataforma de Recursos Inclusivos e Sala de Materiais Acessíveis

> **Uma aula entra e várias versões saem, para todos.** O professor envia o material, o PRISMA cria versões
> acessíveis, o professor aprova e a turma estuda do jeito que aprende melhor.

Time **Carcará 3301** (alunos do IME) · Hackathon da Liga de Empreendedorismo da Praia Vermelha (**LEPV**), tema Educação.
Trilhas 1 (inclusão e acessibilidade) e 4 (aprendizagem individualizada).

## Entregas

| Entrega | Onde |
|---|---|
| 1. Vídeo demo (2 min 57 s) | [`pitch/video-demo/prisma-demo.mp4`](pitch/video-demo/prisma-demo.mp4) · roteiro em [`pitch/video-demo/roteiro.md`](pitch/video-demo/roteiro.md) |
| 2. Plano de negócio | [slides 16:9](pitch/plano-negocio/plano-de-negocio-prisma.pdf) · [documento A4](pitch/plano-negocio/plano-de-negocio-prisma-A4.pdf) · números em [`modelo.py`](pitch/plano-negocio/modelo.py) |
| 3. Site no ar, sem senha | **[hackathon-lep-carcara-backend.vercel.app](https://hackathon-lep-carcara-backend.vercel.app/)** · em **Entrar › Experimentar sem cadastro** |
| 4. Repositório e sessões de IA | este repositório · conversas em [`prompts/`](prompts/) · decisões em [`CLAUDE.md`](CLAUDE.md) |

## Experimente em 1 minuto (site no ar)

1. Abra [o site](https://hackathon-lep-carcara-backend.vercel.app/) › **Entrar** › **Experimentar sem cadastro**. Não precisa de conta: todas são fictícias.
2. **Aluna Bia (cores)**: abre os materiais publicados e escolhe a versão (Padrão, Letras grandes, Ouvir).
   O desenho do ciclo da água tem um símbolo sobre cada cor, para quem não distingue cores. Avalie com estrelas.
3. **Professora**: envie um arquivo de [`materiais-teste/`](materiais-teste/) (PDF, áudio ou vídeo), acompanhe a
   produção ao vivo, confira as versões e aprove. Os feedbacks dos alunos aparecem no painel.
4. **Escola** e **Família**: veja os painéis de cada papel. O cadastro de escola mostra os planos de assinatura.

## O que o PRISMA faz

- **Lê o material como ele é**: PDF (inclusive fórmulas: expoente, fração, raiz, integral, vetor), PowerPoint,
  texto, áudio e vídeo (a IA transcreve e lista o que aparece na tela).
- **Cria versões a partir do Manual PRISMA** (`docs/manual/padroes.json`, 10 padrões e 51 critérios verificáveis):
  - **Padrão** acessível para todos: página limpa, instruções em passos, linhas de resposta, quadro "Hoje vamos".
  - **Letras grandes e alto contraste** (amarelo no preto, com troca de cores e tamanho pelo aluno).
  - **Ouvir**: lê em voz alta, inclusive fórmulas e a legenda das cores.
  - **Leitura Fácil** (IA): frases curtas, fórmulas protegidas, conferência de cada resposta e plano B sem IA.
  - **Cor sempre com símbolo** (daltonismo): símbolos desenhados sobre as cores das imagens, com legenda.
- **O professor está no comando**: nada chega ao aluno sem aprovação; descrições de imagem da IA são conferidas.
- **Papéis**: escola (vê professores, turmas e materiais; assinatura), professor (turmas, envio, revisão,
  feedbacks), aluno (biblioteca e avaliação de 1 a 5 estrelas), família (vê e pode tirar um material do painel do filho).
- **Interface acessível**: barra de acessibilidade (letra, alto contraste, fonte para dislexia, 4 modos de daltonismo).
- **Mini curso e manual** na aba Instruções, com teste final e certificado.

## Como rodar do zero

Precisa de Python 3.10 ou mais novo.

```bash
git clone https://github.com/pibic68-stack/hackathon-lep-carcara.git
cd hackathon-lep-carcara/backend
python -m pip install -r requirements-nuvem.txt
cp .env.exemplo .env              # cole a chave gratuita do Gemini em GEMINI_API_KEY= (sem ela, só a IA fica pendente)
python -m adaptador.api           # abra http://127.0.0.1:8000
python -m pytest testes           # opcional: os testes automáticos
```

- **Windows, sem terminal:** dois cliques em `publicar.bat`. Ele instala o que faltar, pede a chave da IA, abre o site
  e cria um link público com QR code e contas de demonstração (página Compartilhar).
- **Docker:** `docker build -t prisma . && docker run -p 8000:8000 -e GEMINI_API_KEY=... prisma`.
- **Vercel** (site no ar): veja [`DEPLOY.md`](DEPLOY.md).
- **Antes de uma apresentação:** [`materiais-teste/LEIA-ME.md`](materiais-teste/LEIA-ME.md) deixa as respostas da IA guardadas.

## Estrutura do repositório

| Pasta | Conteúdo |
|---|---|
| `backend/adaptador/` | Servidor (FastAPI): leitores por formato, regras do Manual, IA (Gemini), contas, painéis. Guia: [`backend/README.md`](backend/README.md) |
| `web/` | Site (HTML, CSS e JS puros), painéis e aba Instruções. Guia: [`web/README.md`](web/README.md) |
| `docs/manual/` | Manual PRISMA: `padroes.json` (fonte única das regras) e o PDF |
| `docs/pesquisa/` | Fontes lidas, lacunas e matriz de barreiras |
| `pitch/` | Vídeo demo e plano de negócio |
| `materiais-teste/` | Materiais do time para testar e demonstrar (ciclo da água, 5º ano) |
| `prompts/` | Todas as sessões com a IA, exportadas automaticamente |
| `CLAUDE.md` | Memória do projeto: cada decisão do time, com data |

## Princípios

- **Identificar barreiras, nunca diagnosticar**: o perfil registra necessidades ("letra grande"), não doenças.
- **O professor revisa e aprova** tudo o que a IA gera.
- **Mesmo conteúdo para todos**: muda a forma, não o objetivo de aprendizagem.
- **LGPD**: só alunos fictícios; nenhum dado real vai para a IA gratuita.
- **A própria interface é acessível**.
