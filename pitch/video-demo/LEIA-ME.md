# Vídeo demo PRISMA

O roteiro para gravar está em `roteiro.md` (e `roteiro.pdf`).

## Como gerar o vídeo

1. Coloque as gravações em `gravacoes/` (nada disso vai para o Git):
   - `intro.mp4`: a intro já acelerada (a original de 30 s virou 24 s com `setpts=PTS/1.25` e `atempo=1.25`)
   - `whats-1.mp4` a `whats-4.mp4`: "nós", "somos", "a" e o grupo dizendo "PRISMA"
   - `narracao-3.m4a` a `narracao-7.m4a` (opcional: sem elas, entra a voz sintética)
2. Em `cenas/time.js`, confira as palavras e o segundo em que cada uma é falada no vídeo original.
3. Rode, dentro de `ferramentas/`:

```bash
python recortar.py
python narracao.py
sh render_tudo.sh
python montar.py
```

O `recortar.py` tira o fundo de cada `whats-N.mp4` e põe o papel do site com a logo, gerando `time-N.mp4`.
Ele só precisa rodar de novo se os vídeos do time mudarem.

O resultado fica em `saida/`:
- `prisma-demo.mp4`: com legenda
- `prisma-demo-sem-legenda.mp4`: sem legenda
- `prisma-demo.srt`: a legenda em arquivo, para o site

Se a narração mudar, rode os três comandos de novo, porque as cenas seguem o tempo de cada frase.

## Como funciona

- Cada bloco é uma página HTML em `cenas/`, com as cores e as fontes do site (`/web/css/tokens.css`).
- `render.py` abre a página no Chrome e grava quadro a quadro.
- Cada animação começa quando a sua frase começa. O tempo vem de `saida/audio/tempos.json`, gerado pelo `narracao.py`.
- Para conferir um momento sem gerar o vídeo: `python render.py bloco-5 --foto 12 30`.
- O site que as cenas usam vem de `../../web`. Para usar outra cópia, defina `PRISMA_WEB`.
- A legenda usa a Atkinson Hyperlegible Next, com no máximo 2 linhas e caixa escura.
