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
| `GET /api/biblioteca` · `GET /api/biblioteca/{id}/{arquivo}` | aluno e família | Só o que foi **publicado** (P10.1). Rascunho dá 404. |

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

## Como funciona

```
arquivo ──► leitores.py ──► Documento (blocos) ──► transformacoes.py ──► renderizador.py ──► HTML
 .pdf .pptx   texto, títulos,   lista de blocos      regras P1, P4, P6     CSS do padrão P2     + revisao.json
 .txt vídeo   imagens, áudio    (modelo.py)          (sem IA)              (fonte, contraste)
```

| Arquivo | Papel |
|---|---|
| `modelo.py` | Formato interno (`Documento`, `Bloco`). É o "contrato" entre as peças. |
| `leitores.py` | Um leitor por formato. Vídeo/áudio usa `faster-whisper` (roda no computador, sem internet). |
| `regras.py` | Lê os limites dos critérios do Manual (`docs/manual/padroes.json`: P2.1 contraste, P2.2 e P2.4 tamanho e linha, P6.1 etapas). Não ficam fixos no código. |
| `transformacoes.py` | Regras determinísticas: **P1.1** cor + símbolo, **P6.1/P6.2** "Hoje vamos" e passos numerados, **P6.3** avisa linguagem figurada, **P4.1** imagem sem descrição bloqueia a publicação. |
| `renderizador.py` | Gera o HTML acessível (idioma, pular para o conteúdo, foco visível, contraste conferido nos testes). |
| `cache.py` | Guarda o que é lento (transcrição, respostas da IA) em `backend/cache/`. Esta pasta **é versionada** de propósito, para a demo funcionar sem internet. |
| `ia.py` | Ponto de ligação da IA. **Ainda sem provedor.** |
| `pipeline.py` | Junta tudo e decide as versões pelo perfil (baixa visão ⇒ ampliada etc.). |

## O que já está feito e o que falta

- [x] Ler `.txt` · [x] critérios P1.1, P6.1 a P6.3 e P4.1 · [x] HTML padrão e ampliado · [x] fila de revisão · [x] cache
- [x] Ler PDF e PowerPoint (testado com arquivos criados nos testes) · [ ] testar com **PDFs e PowerPoints reais** de aula (layouts complicados, colunas, escaneados)
- [ ] Testar vídeo (precisa `faster-whisper`)
- [x] API para o site enviar arquivos (FastAPI, ver seção acima) · [ ] ligar o site (`web/js`) à API · [ ] login de verdade
- [ ] IA: simplificar texto (Leitura Fácil), descrever imagens, roteiro de áudio
- [ ] Mover `PEDE_VERSAO` (em `pipeline.py`, qual necessidade pede qual versão) para o `padroes.json`; versão `braille` ainda não tratada

## Limites conhecidos das regras sem IA

- **P1** reconhece palavras de cor, não cores dentro de imagens. "Rosa" (flor) pode ser marcado sem querer: o professor é avisado.
- **P6** reconhece instruções que começam com verbo de ordem (leia, desenhe, responda...). Lista de verbos em `transformacoes.py`.
- Imagens e gráficos não são adaptados; só ganham descrição quando a IA estiver ligada (ou o professor escrever).
- PDF escaneado (só imagem) não tem texto: precisa de OCR, e o sistema avisa.

## IA: do zero

1. **O que é**: um modelo de linguagem (LLM) é um serviço na internet. O código envia um texto (o *prompt*,
   com as instruções e o material) e recebe outro texto de volta. Não é preciso "treinar" nada.
2. **Como se liga**: o backend faz uma chamada HTTP autenticada por uma **chave de API**. A chave fica só no
   servidor (arquivo `.env`, já no `.gitignore`), nunca no HTML nem no GitHub.
3. **Onde entra aqui**: as três tarefas do manual que regra fixa não resolve: reescrever em Leitura Fácil (P3),
   descrever imagens (P4) e roteiro de áudio (P5). Tudo passa por `ia.py` e por `cache.com_cache()`,
   então cada pedido é pago/esperado uma vez só e a demo roda offline.
4. **Segurança**: o professor aprova tudo (P10); a IA nunca recebe nome real de aluno (LGPD).
