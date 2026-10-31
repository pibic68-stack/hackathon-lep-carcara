# Site público fixo no Railway

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
