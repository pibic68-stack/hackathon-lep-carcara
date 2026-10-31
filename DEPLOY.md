# Site público fixo (Vercel)

## Vercel (o mais rápido: uns 5 minutos)

O repositório já tem `app.py`, `requirements.txt` e `vercel.json` na raiz.

1. Em **vercel.com**, entre com o GitHub › **Add New… › Project** › importe `hackathon-lep-carcara`.
2. Deixe tudo como a Vercel sugerir (ela reconhece o FastAPI sozinha). Em **Environment Variables**, crie
   `GEMINI_API_KEY` (de preferência uma chave de outra conta do Google, para não dividir o limite com o PC).
3. **Deploy**. O link fixo é o `…vercel.app` que aparece no fim. Coloque no `README.md` e no portal.
3b. **Obrigatório para o login funcionar:** no projeto, aba **Storage › Create Database › Neon (Postgres)** › plano grátis ›
   **Connect** a este projeto. A Vercel cria sozinha a variável `DATABASE_URL`. Depois, **Deployments › Redeploy**.
   Sem isso, cada pedido pode cair numa cópia diferente do servidor e a pessoa entra no painel e volta para a tela
   de entrada. Com o Postgres, todas as cópias guardam e leem as mesmas contas e materiais (`backend/adaptador/estado_nuvem.py`).
4. Abra o link › **Entrar** › **Experimentar sem cadastro**.

Como a Vercel funciona e o que muda lá:
- Não há disco fixo: sem o Postgres do passo 3b, contas e materiais ficam numa pasta temporária que **zera**.
  No primeiro clique em "Experimentar sem cadastro", o PRISMA recria as contas e publica os 2 PDFs de teste
  (em segundos, sem IA): Padrão, Letras grandes, Ouvir e o desenho com símbolos.
- Áudio e vídeo de teste: entre como Professora e envie `materiais-teste/3-audio-aula.wav` e `4-video-aula.mp4`
  (a IA transcreve na hora). A Vercel aceita envios de **até 4,5 MB**; arquivos maiores, só no PC.
- Cada pedido pode durar até 5 minutos (`maxDuration` no `vercel.json`): suficiente para a IA com as novas tentativas.
- Cada `git push` na `main` atualiza a Vercel sozinho.
- O projeto que vale é o **`hackathon-lep-carcara-backend`**, com Root Directory vazio (a raiz do repositório).
  O `hackathon-lep-carcara` tinha Root Directory = `backend` e falhava em todo push (lá não há `app.py`, o
  `requirements.txt` traz o faster-whisper e o site `web/` fica de fora). Ele foi desconectado do Git em 31/10.

## Outro serviço com Docker

O `Dockerfile` da raiz roda o PRISMA em qualquer serviço que aceite Docker (servidor único, com disco):
variável `GEMINI_API_KEY`, volume em `/data` e a porta na variável `PORT`. Lá os 4 materiais de teste são
publicados sozinhos ao ligar, com a IA, inclusive áudio e vídeo.
