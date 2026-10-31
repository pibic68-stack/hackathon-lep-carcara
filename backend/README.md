# Backend: IA e Backend (Pessoa 2)

Recebe o material da aula + o perfil do aluno e devolve versões adaptadas em HTML acessível,
mais um arquivo `revisao.json` para o professor aprovar (critério P10.1 do Manual).

## Rodar agora

```bash
cd backend
python -m pip install -r requirements.txt      # só para PDF e PowerPoint
python -m adaptador exemplos/aula-ciclo-da-agua.txt --perfil exemplos/perfil-exemplo.json
```

Saída em `backend/saida/<material>/`: `universal.html`, `ampliada.html` e `revisao.json`.
Testes (não precisam instalar nada): `python -m unittest discover -s testes -v`

## API para o site

```bash
cd backend
python -m adaptador.api        # http://127.0.0.1:8000  (o mesmo servidor entrega o site de web/)
```

Documentação interativa (testar pelo navegador): http://127.0.0.1:8000/docs

| Rota | Quem usa | O que faz |
|---|---|---|
| `POST /api/adaptar` | professor | Envia o arquivo (`arquivo`) e o perfil (`perfil`, JSON opcional). Cria um **rascunho** e devolve versões, transformações, pendências e `pode_publicar`. |
| `GET /api/materiais` · `GET /api/materiais/{id}` | professor | Lista e detalha os materiais (fila de revisão). |
| `GET /api/previa/{id}/{arquivo}` | professor | Abre qualquer versão para revisar, publicada ou não. |
| `POST /api/materiais/{id}/descricoes` | professor | Escreve as descrições das imagens (`{"imagens": {"imagens/img-001.png": "texto"}}`). Gera as versões de novo. |
| `POST /api/materiais/{id}/aprovar` | professor | Publica. Recusa (409) se ainda há imagem sem descrição (P4.1). |
| `GET /api/biblioteca` · `GET /api/biblioteca/{id}/{arquivo}` | aluno e família | Só o que foi **publicado** (P10.1). Rascunho dá 404. Para o aluno, cada item traz a avaliação que ele já deu. |
| `POST /api/biblioteca/{id}/avaliacao` | aluno | `{"estrelas": 1..5 ou null, "sugestao": "até 150 palavras", "pular": false}`. As duas coisas são opcionais; `pular: true` registra que o aluno pulou. |
| `POST /api/biblioteca/{id}/ocultar` | família | `{"ocultar": true/false}`. Tira (ou devolve) o material só do painel do próprio aluno. A turma continua vendo. |
| `GET /api/feedbacks` | professor | Para cada material: média de estrelas, total e a lista (apelido do aluno, estrelas, sugestão). |
| `POST /api/contas/escola` | público | Cadastra a escola: nome, e-mail, senha do painel e o **código para os professores** (diferente da senha; guardado só como impressão digital). |
| `GET /api/escola` | escola | Só leitura: professores (com turmas e alunos) e materiais da escola. |
| `GET /api/eu` | todos | Quem está logado, ou `null` (sem erro 401). |

Exemplo (o que o JavaScript do site faz):

```js
const form = new FormData();
form.append("arquivo", inputArquivo.files[0]);
form.append("perfil", JSON.stringify({ necessidades: ["baixa_visao"] }));
const r = await fetch("http://127.0.0.1:8000/api/adaptar", { method: "POST", body: form });
const material = await r.json();   // material.versoes.universal.url -> abrir num <iframe> ou link
```

**Cuidados:** ainda **não há login**: qualquer um que alcance o servidor pode aprovar, então use só em rede local
na demo. Arquivos enviados ficam em `backend/envios/` e resultados em `backend/saida/` (ambos fora do Git).
Limite de 300 MB por arquivo. Vídeos longos podem levar minutos para transcrever (a requisição espera).

## Matemática e cor no PDF (`leitor_pdf.py`)

O texto "puro" de um PDF perde a posição das letras: x² vira "x2", uma fração empilhada vira "3 2 3 1".
O leitor olha cada letra (tamanho e altura na linha) e os traços desenhados (barra de fração e de raiz) e remonta:

| No PDF | Marcação interna | Na página | No Ouvir |
|---|---|---|---|
| x² | `x⟦^{2}⟧` | `<sup>` | "x ao quadrado" |
| a₁ | `a⟦_{1}⟧` | `<sub>` | "a índice 1" |
| 3 sobre 2 | `⟦\frac{3}{2}⟧` | MathML `<mfrac>` | "3 sobre 2" |
| √(x²+y²) | `⟦\sqrt{x⟦^{2}⟧+y⟦^{2}⟧}⟧` | MathML `<msqrt>` | "raiz quadrada de…" |
| F⃗ | `⟦\vec{F}⟧` | MathML `<mover>` | "vetor F" |
| ∫ com C embaixo | `∫⟦_{C}⟧` | `<sub>` | "integral índice C" |

Também separa "1-) … a) … b) … 2-) …" escritos na mesma linha em questões e itens, e marca o **texto colorido**
com a forma da cor (P1.1) e as **imagens coloridas** (P1.2: a descrição precisa dizer o que cada cor representa).
Usa PyMuPDF; sem ele, usa pdfminer.six (os testes rodam com qualquer um).

## Como funciona

```
arquivo ──► leitores.py ──► Documento (blocos) ──► transformacoes.py ──► renderizador.py ──► HTML
 .pdf .pptx   texto, títulos,   lista de blocos      regras P1, P4, P6     CSS do padrão P2     + revisao.json
 .txt vídeo   imagens, áudio    (modelo.py)          (sem IA)              (fonte, contraste)
```

| Arquivo | Papel |
|---|---|
| `modelo.py` | Formato interno (`Documento`, `Bloco`). É o "contrato" entre as peças. |
| `leitores.py` | Um leitor por formato. Vídeo/áudio usa `faster-whisper` se instalado; senão, a IA transcreve. |
| `simbolos_imagem.py` | P1.1 dentro de imagens coloridas: símbolo preto sobre cada região de cor + legenda (Pillow). |
| `regras.py` | Lê os limites dos critérios do Manual (`docs/manual/padroes.json`: P2.1 contraste, P2.2 e P2.4 tamanho e linha, P6.1 etapas). Não ficam fixos no código. |
| `transformacoes.py` | Regras determinísticas: **P1.1** cor + símbolo, **P6.1/P6.2** "Hoje vamos" e passos numerados, **P6.3** avisa linguagem figurada, **P4.1** imagem sem descrição bloqueia a publicação. |
| `renderizador.py` | Gera o HTML acessível (idioma, pular para o conteúdo, foco visível, contraste conferido nos testes). |
| `cache.py` | Guarda o que é lento (transcrição, respostas da IA) em `backend/cache/`. Esta pasta **é versionada** de propósito, para a demo funcionar sem internet. |
| `ia.py` | IA (Gemini): descrever imagens e Leitura Fácil. Pedidos e cache ficam aqui. Veja a seção IA. |
| `pipeline.py` | Junta tudo e decide as versões pelo perfil (baixa visão ⇒ ampliada etc.). |

## O que já está feito e o que falta

- [x] Ler `.txt` · [x] critérios P1.1, P6.1 a P6.3 e P4.1 · [x] HTML padrão e ampliado · [x] fila de revisão · [x] cache
- [x] Ler PDF e PowerPoint (testado com arquivos criados nos testes) · [ ] testar com **PDFs e PowerPoints reais** de aula (layouts complicados, colunas, escaneados)
- [x] Vídeo/áudio com `faster-whisper` (testado com arquivo sintético; falta áudio real de sala de aula)
- [x] API para o site enviar arquivos (FastAPI, ver seção acima) · [x] site ligado à API (`web/js/api.js`, `professor.js`, `biblioteca.js`) · [ ] login de verdade
- [x] IA (Gemini): descrever imagens e Leitura Fácil, **falta testar com a chave real** · [x] versão Ouvir (sem IA)
- [ ] Mover `PEDE_VERSAO` (em `pipeline.py`, qual necessidade pede qual versão) para o `padroes.json`; versão `braille` ainda não tratada

## Limites conhecidos das regras sem IA

- **P1** reconhece palavras de cor, não cores dentro de imagens. "Rosa" (flor) pode ser marcado sem querer: o professor é avisado.
- **P6** reconhece instruções que começam com verbo de ordem (leia, desenhe, responda...). Lista de verbos em `transformacoes.py`.
- Imagens e gráficos não são alterados; só ganham descrição (IA ou professor).
- PDF escaneado (só imagem) não tem texto: precisa de OCR, e o sistema avisa.

## IA (Gemini)

**Escolha do time:** Gemini (Google), pela chave **gratuita** do Google AI Studio (sem cartão), boa em português
e com leitura de imagens. O código não depende dele: todos os pedidos (prompts) ficam em `ia.py`, e trocar de
serviço (ex.: Claude) é escrever **uma** função `gerar(sistema, usuario, imagem)` numa nova classe.

### O que é uma IA aqui, do zero
Um modelo de linguagem é um serviço na internet. O código envia um texto (as instruções + o material) e recebe
outro texto de volta. Ninguém precisa treinar nada. O acesso é pago por uma **chave de API** (uma senha longa)
que fica só neste computador, no arquivo `.env`, nunca no site nem no GitHub.

### Ligar em 3 passos
1. Abra https://aistudio.google.com/apikey, entre com uma conta Google e clique em **Criar chave de API**.
2. Na pasta `backend/`, copie `.env.exemplo` para `.env`:
   ```bash
   cp .env.exemplo .env
   ```
3. Abra o `.env` e cole a chave depois de `GEMINI_API_KEY=`. Reinicie a API. Em `/api/saude` aparece `"ia_ligada": true`.

### O que a IA faz (e o que o código confere)
| Tarefa | Critério | Como funciona |
|---|---|---|
| Descrever imagens | P4.2, P4.5 | A IA escreve; o professor **confere e corrige** no painel antes de aprovar. Se achar que é só enfeite, avisa. |
| Leitura Fácil I e II | P3.1 a P3.5 | A IA reescreve com os limites do manual (palavras por frase vêm de `padroes.json`). Feito para o Gemini Flash Lite gratuito, que guarda pouco contexto: **lotes de até 6 trechos**, fórmulas trocadas por `[M1]` antes de ir para a IA, e **cada resposta é conferida** (fórmula perdida, frase longa, texto parecido demais com o original, nível I que não encurtou). O que voltou com problema vai de novo, **um trecho por vez**, com a instrução reforçada. Se ainda falhar, o trecho fica só com as frases divididas e o professor recebe um aviso: a versão nunca sai pela metade. |

A versão **Ouvir** (P5) **não usa IA**: usa a voz do navegador (Chrome e Edge têm voz em português), sem internet.
Ela lê o texto na tela e não gera arquivo de áudio.

### Cuidados
- **Privacidade:** no plano gratuito o Google pode usar o conteúdo enviado para melhorar os produtos dele.
  Use só material de domínio público ou criado pelo time, **nunca dados reais de alunos**. Para uso real, o plano pago
  não usa o conteúdo desse jeito.
- **Limites gratuitos:** ao passar do limite, o sistema espera e tenta de novo; se não der, avisa o professor.
  Tudo que a IA responde fica em `backend/cache/`, então **rode a demo antes**: depois disso ela funciona sem internet.
- **Sem IA, nada quebra:** as versões Padrão, Ampliada e Ouvir continuam saindo. Leitura Fácil fica "pendente".
- **Revisão obrigatória:** a IA erra. Nada chega ao aluno sem o professor aprovar (P10.1).
- **Testado ao vivo (30/10/2026)** com uma chave gratuita: descreveu corretamente um gráfico de colunas (cores e
  posições) e reescreveu uma aula em Leitura Fácil II com frases curtas e glossário. Cada chamada leva uns 7 segundos.
  Só foram testados 2 materiais pequenos; falta experimentar aulas reais e mais longas.
- **Modelo:** padrão `gemini-3.1-flash-lite`. Nesse teste o `gemini-2.5-flash` estava desativado para contas novas e o
  `gemini-3.8-flash` não respondeu em 60 s. Os modelos mudam rápido: se der erro de modelo, troque `PRISMA_IA_MODELO=` no `.env`.
- **Chave:** cada pessoa usa a própria no `.env` dela (ou o time combina por canal privado). **Nunca cole a chave no chat
  nem no `.env.exemplo`**: o chat é publicado em `prompts/` (o exportador esconde chaves conhecidas, mas não confie só nisso)
  e o `.env.exemplo` vai para o GitHub. Se uma chave vazar, apague-a em https://aistudio.google.com/apikey e crie outra.

## Acompanhar a produção e a IA

- `GET /api/ia/teste` (professor): pergunta curtinha, sem cache. Diz se a IA respondeu, em quantos segundos e com qual modelo.
- `GET /api/progresso/{codigo}`: o site manda o cabeçalho `X-Prisma-Acompanhar: codigo` em `/api/adaptar`, `/refazer` e
  `/descricoes` e pergunta este endereço a cada segundo (etapa, passos, diário, pedidos à IA, novas tentativas, modelo).
- Erro 503 do Google (modelo sobrecarregado): o PRISMA tenta de novo, troca de caminho da API e depois usa os modelos
  reserva (`PRISMA_IA_RESERVA` no `.env`). Só desiste quando todos falham, e diz isso ao professor.

## Vídeo e áudio

Dois caminhos, nesta ordem (31/10):
1. **`faster-whisper` instalado** (`pip install faster-whisper`): transcreve no próprio computador, sem internet depois de baixar o modelo.
2. **Sem ele, a IA (Gemini) ouve o arquivo** (`ia.transcrever_midia`): até 15 MB vai junto no pedido; acima disso sobe pela
   Files API do Google (apagado por ele em 48 h). Em vídeo, a IA também lista "O que aparece na tela" (slide, fórmula no quadro).
   O professor confere antes de aprovar. É o caminho do `publicar.bat`, que não instala o `faster-whisper` (pesado).
Sem nenhum dos dois, a plataforma explica como ligar a IA.

`pip install -r requirements.txt` já inclui o `faster-whisper`. Na primeira vez ele baixa o modelo de voz
(`small`, ~460 MB). Testado com um `.mp4` e um `.wav` em português: transcrição correta e, na segunda vez, 1 segundo (cache).
O modelo `tiny` (`--modelo-audio tiny`, ~75 MB) é rápido, mas erra palavras. Áudio de sala de aula real,
com ruído e vários falando, será pior que o de teste: o professor precisa conferir a transcrição.
