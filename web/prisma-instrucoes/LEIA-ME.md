# Aba de instruções da PRISMA

Esta pasta é a aba **Instruções** do site, pronta para encaixar. Ela tem duas partes:

- **Mini curso**: 10 passos interativos, em três trilhas (professor, família, estudante).
- **Manual**: os 10 padrões, os 51 critérios, as necessidades, o mapa, o glossário, as referências e o botão para baixar o PDF.

## O que tem aqui

| Arquivo | Para que serve |
|---|---|
| `index.html` | A página inteira. Um arquivo só, sem dependências além das fontes do Google Fonts. |
| `manual-prisma-v1.pdf` | O PDF que o botão "Baixar o manual" entrega. |
| `padroes.json` | Os padrões e critérios em formato de dados. O backend pode ler daqui. |
| `src/pagina.html` | O modelo da página. Edite aqui, não no `index.html`. |
| `build.py` | Junta o modelo com os dados e gera o `index.html`. |

## Como encaixar no site (escolha uma)

**1. Pasta estática (mais simples).** Copie a pasta inteira para a pasta pública do site (`public/`, `static/` ou equivalente) e aponte a aba para `/prisma-instrucoes/`. O link `#manual` abre direto a aba Manual.

**2. Iframe.** Se o site já tem cabeçalho e menu próprios:

```html
<iframe src="/prisma-instrucoes/index.html" title="Instruções da PRISMA"
        style="width:100%;height:100vh;border:0"></iframe>
```

**3. Componente.** Em React, Vue ou similar, copie o `<style>`, o HTML e o `<script>` de `index.html` para um componente. O script não depende de biblioteca nenhuma.

## Como atualizar

Nunca edite `index.html` à mão: ele é gerado.

1. Mudou um padrão, critério, dado ou referência? Edite `docs/manual/padroes.json`.
2. Gere o PDF de novo: `python3 docs/manual/build_manual.py --fontes PASTA_DAS_FONTES`
3. Gere a página de novo: `python3 web/prisma-instrucoes/build.py`

## Para o backend

Cada critério em `padroes.json` tem `id`, `criterio`, `como_medir`, `limite` e `automacao`:

- `automatico`: o código verifica sozinho, com regra e limite.
- `ia_revisao`: a IA propõe e o professor confere.
- `manual`: uma pessoa faz.

Use o `id` (por exemplo, `P3.1`) no relatório de barreiras que vai para o professor. A ordem de verificação sugerida está na Parte 6 do PDF.

## Acessibilidade da própria página

A página segue os padrões que ensina: contraste ≥ 4,5:1 nos dois temas (claro e escuro), navegação por teclado, foco visível, gráficos com legenda escrita (nunca só cor), tabela alternativa nos gráficos de barras e respeito a "reduzir movimento".
