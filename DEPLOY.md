# Site público fixo (Vercel, Railway ou Render)

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

## Railway ou Render (servidor de verdade, com o `Dockerfile`)

Use se quiser disco fixo e materiais publicados sozinhos com IA (inclusive áudio e vídeo).
No Render: **New › Blueprint** › este repositório (usa o `render.yaml`; plano grátis dorme após 15 min sem uso
e zera os dados ao acordar). No Railway, siga abaixo.

# Railway

O site do PC (`publicar.bat`) continua igual: é o da apresentação, com controle total.
Este guia cria **outra cópia, na nuvem, com endereço fixo**, para a banca e qualquer pessoa usarem sem senha.
As duas usam o mesmo código: cada `git push` na `main` atualiza a nuvem sozinho.

O repositório já tem tudo o que o Railway precisa: `Dockerfile`, `railway.json` e `backend/requirements-nuvem.txt`.

## Passo a passo (uns 10 minutos, uma vez só)

1. Entre em **railway.com** com a conta do GitHub (o teste grátis dá um crédito inicial, sem cartão).
2. **New Project › Deploy from GitHub repo** e escolha `hackathon-lep-carcara`.
   Se ele não aparecer, autorize o Railway a ver o repositório (ele é privado).
3. Abra o serviço criado › **Variables** › **New Variable**:
   - `GEMINI_API_KEY` = a chave do Gemini. **Dica:** crie uma chave nova, de outra conta do Google,
     para a nuvem não dividir o limite gratuito com o PC da apresentação.
   - (opcional) `PRISMA_CODIGO_ESCOLA` = um código para professores de verdade criarem conta.
4. **Volume** (para não perder contas e materiais a cada atualização): no serviço, clique com o botão direito
   › **Attach Volume** (ou **Settings › Volumes**) e use o caminho **`/data`**.
5. **Settings › Networking › Generate Domain**. Esse é o link fixo (`algo.up.railway.app`).
   Coloque-o no topo do `README.md` e na entrega do portal.
6. Espere o primeiro deploy (2 a 5 minutos). Abra o link › **Entrar** › **Experimentar sem cadastro**.

## O que acontece sozinho na nuvem

- Cria a escola, a professora e a turma de demonstração (3 alunos fictícios), com senhas sorteadas.
- Publica os 4 materiais de `materiais-teste/` para a turma. Isso usa a IA e tem a mesma paciência do PC:
  se o Google estiver ocupado (erro 503), tenta de novo a cada 90 segundos. Nos **Logs** do Railway aparece
  `[demo] publicado: ...` para cada um. Pode levar alguns minutos depois do deploy.
- A caixa "Experimentar sem cadastro" só existe no site da nuvem (`PRISMA_DEMO_PUBLICA=1`, já no `Dockerfile`).
  No PC ela não aparece.

## Se algo der errado

- **Deploy falhou:** aba **Deployments › View logs**. O teste de saúde é `/api/saude`.
- **Materiais não aparecem:** veja os Logs. "IA ocupada, tento de novo depois" é normal; espere.
  Se aparecer "chave", confira a variável `GEMINI_API_KEY`.
- **Contas sumiram depois de um deploy:** falta o volume em `/data` (passo 4).
