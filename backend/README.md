# Backend: IA e Backend (Pessoa 2)

Recebe o material da aula + o perfil do aluno e devolve versões adaptadas em HTML acessível,
mais um arquivo `revisao.json` para o professor aprovar (padrão P7 do Manual).

## Rodar agora

```bash
cd backend
python -m pip install -r requirements.txt      # só para PDF e PowerPoint
python -m adaptador exemplos/aula-ciclo-da-agua.txt --perfil exemplos/perfil-exemplo.json
```

Saída em `backend/saida/<material>/`: `universal.html`, `ampliada.html` e `revisao.json`.
Testes (não precisam instalar nada): `python -m unittest discover -s testes -v`

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
| `regras.py` | Lê números do Manual (`docs/manual/padroes.json`: 60 caracteres, 14/18 pt, contraste). Não ficam fixos no código. |
| `transformacoes.py` | Regras determinísticas: **P1** cor + símbolo, **P6** passos numerados e "Hoje vamos", **P4** imagem sem descrição vira pendência. |
| `renderizador.py` | Gera o HTML acessível (idioma, pular para o conteúdo, foco visível, contraste conferido nos testes). |
| `cache.py` | Guarda o que é lento (transcrição, respostas da IA) em `backend/cache/`. Esta pasta **é versionada** de propósito, para a demo funcionar sem internet. |
| `ia.py` | Ponto de ligação da IA. **Ainda sem provedor.** |
| `pipeline.py` | Junta tudo e decide as versões pelo perfil (baixa visão ⇒ ampliada etc.). |

## O que já está feito e o que falta

- [x] Ler `.txt` · [x] regras P1, P6, P4 (pendência) · [x] HTML padrão e ampliado · [x] fila de revisão · [x] cache
- [ ] Testar PDF e PowerPoint com materiais reais (código escrito, **ainda não executado**)
- [ ] Testar vídeo (precisa `faster-whisper`)
- [ ] API para o site enviar arquivos (FastAPI)
- [ ] IA: simplificar texto (Leitura Fácil), descrever imagens, roteiro de áudio
- [ ] Migrar `PEDE_VERSAO` (em `pipeline.py`) para `docs/manual/regras.json` quando a Pessoa 1 entregar

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
4. **Segurança**: o professor aprova tudo (P7); a IA nunca recebe nome real de aluno (LGPD).
