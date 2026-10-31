# Aba de instruções da PRISMA

Esta pasta é a aba **Instruções** do site. Ela já está ligada ao menu da página inicial e usa o mesmo visual do resto do site (logo pixel, fontes, cores e barra de acessibilidade). Tem duas partes:

- **Mini curso**: 10 passos interativos, em três trilhas (professor, família, estudante).
- **Manual**: os 10 padrões, os 51 critérios, as necessidades, o mapa, o glossário, as referências e o botão para baixar o PDF.

## Como abrir

Abra `web/prisma-instrucoes/index.html` com duplo clique, ou pelo menu **Instruções** da página inicial. Não precisa de internet. Os endereços `index.html#curso` e `index.html#manual` abrem cada aba direto.

## O que tem aqui

| Arquivo | Para que serve |
|---|---|
| `index.html` | A página pronta. **Gerada**, não edite à mão. Usa `../css/`, `../js/` e `../assets/` do site. |
| `manual-prisma-v1.pdf` | O PDF que o botão "Baixar o manual" entrega. |
| `src/pagina.html` | Estrutura e código da página. Edite aqui. |
| `src/estilo.css` | O visual próprio da aba. Só usa as cores e fontes do site (`web/css/tokens.css`). |
| `build.py` | Junta modelo, estilo e dados e gera o `index.html`. |
| `_previa/` | Cópia para ver a aba fora do site (não vai para o Git). |

## Como o visual acompanha o site

A aba carrega `../css/tokens.css`, `../css/base.css`, `../css/componentes.css` e `../js/acessibilidade.js`. Por isso:

- se o time mudar uma cor ou fonte em `tokens.css`, a aba muda junto, sem rodar nada;
- a barra de acessibilidade do topo (letra maior, alto contraste, fonte para dislexia, 4 modos de daltonismo, pausar animações) vale para a aba também;
- o menu e o rodapé são os mesmos da página inicial. Se mudarem lá, copie a mudança para `src/pagina.html`.

Exceção de propósito: o simulador de daltonismo do passo 2 usa vermelho e verde fixos, porque precisa mostrar a confusão de verdade.

## Como atualizar

Nunca edite `index.html` nem o PDF à mão: eles são gerados.

1. Mudou um padrão, critério, dado ou referência? Edite `docs/manual/padroes.json`.
2. Gere o PDF de novo: `python3 docs/manual/build_manual.py` (as fontes vêm de `web/assets/fontes`, não precisa de nada além do Python e do Playwright).
3. Gere a página de novo: `python3 web/prisma-instrucoes/build.py`

## Para o backend

Cada critério em `padroes.json` tem `id`, `criterio`, `como_medir`, `limite` e `automacao`:

- `automatico`: o código verifica sozinho, com regra e limite.
- `ia_revisao`: a IA propõe e o professor confere.
- `manual`: uma pessoa faz.

Use o `id` (por exemplo, `P3.1`) no relatório de barreiras que vai para o professor. A ordem de verificação sugerida está na Parte 6 do PDF.

## Acessibilidade da própria página

Contraste de texto conferido em 8 modos (padrão, alto contraste, dislexia, 4 de daltonismo e letra 150%): 0 falhas. Navegação por teclado, foco visível, gráficos com legenda escrita (nunca só cor), tabela alternativa nos gráficos de barras, alvos de toque de 44 px, linhas de até 60 caracteres, sem rolagem horizontal em 320 px e respeito a "reduzir movimento". As partes técnicas do mini curso e do manual ainda têm frases com mais de 20 palavras: o critério P3.1 vale para os materiais que a plataforma gera, não para este texto técnico (ver `docs/relatorio-coerencia-acessibilidade.md`).
