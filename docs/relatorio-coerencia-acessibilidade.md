# Relatório: coerência entre as partes e acessibilidade

31/10/2026. Para o grupo ler e decidir junto. Eu só acrescentei a aba Instruções ao site (e o link no menu da página inicial). Nada do resto do site, do backend ou dos painéis foi alterado.

## Como foi medido

- 7 páginas (início, entrar, 3 painéis, mini curso, manual) em 8 modos: padrão, alto contraste, fonte para dislexia, protanopia, deuteranopia, tritanopia, acromatopsia e letra 150%.
- Contraste de todo texto visível, estrutura (idioma, título, landmarks, nomes de botões e links, textos alternativos), tamanho dos alvos de toque, rolagem horizontal em 320 px, tamanho de letra, comprimento de linha e de frase.
- Cores do site simuladas para os 3 tipos de daltonismo (matrizes de Machado, 2009) e comparadas par a par. Diferença de cor ΔE abaixo de 8 conta como "difícil de separar" (o mesmo limite do critério P1.3).
- **O que não foi feito:** teste com leitor de tela de verdade, teste com pessoas e a ferramenta axe (a rede do ambiente bloqueou o download). Recomendo rodar o Lighthouse (aba do Chrome, F12) em cada página antes da apresentação.

## O que já está bom

- Contraste de texto: **0 falhas nas 7 páginas, nos 8 modos** (só foram medidos textos sobre fundo liso; texto sobre foto não entra).
- Todas as páginas têm idioma, título, "pular para o conteúdo", barra de acessibilidade, um `main`, imagens com `alt`, botões e links com nome, sem `tabindex` positivo e sem IDs repetidos.
- Alvos de toque de pelo menos 24 px em todo o site.
- "Pausar animações" e "reduzir movimento do sistema" são respeitados.
- A senha de figurinhas tem nome (`aria-label`) em cada figurinha.

## 1. Incoerências entre as partes (o grupo decide)

| # | O que está diferente | Onde | Sugestão |
|---|---|---|---|
| C1 | **Três identidades visuais.** Site: Pixelify Sans, Atkinson Hyperlegible Next, Departure Mono, azul `#1F6FB2`, laranja `#A3401F`. Memória do projeto e backend: Lexend, Atkinson, azul `#1F5FBF`, âmbar `#C26A00`. O azul `#1F5FBF` ainda aparece no modo protanopia/deuteranopia do site. | `web/css/tokens.css`, `backend/adaptador/renderizador.py`, `CLAUDE.md` | Adotar a do site em tudo. Já fiz isso no manual (PDF) e na aba Instruções e atualizei o `CLAUDE.md`. Falta o `renderizador.py` (o material que a plataforma gera). |
| C2 | **Dois sistemas de código para as regras.** O site usa `R-DALT-01`, `R-TEA-01`; o manual usa `P1.1`, `P6.1`. O comentário de `js/dados.js` e o `web/README.md` mandam ler `docs/manual/regras.json`, que não existe mais (agora é `padroes.json`). | `web/js/dados.js`, `web/README.md` | Mostrar no site os códigos do manual (P1.1 etc.). O Frontend troca o nome do arquivo no comentário e no README. |
| C3 | **Etapas do fluxo com nomes diferentes.** Site: Perfil → Material → Adaptação → Guia → Mini-check (5). Manual: Enviar → Analisar → Transformar → Revisar → Publicar → Acompanhar (6). Backend: leitor → regras → HTML + fila de revisão. | `js/dados.js`, `padroes.json`, `backend/` | Escolher um só vocabulário. Sugiro o do manual no pitch e o do site na tela, com uma tabela "equivale a" no `README.md`. |
| C4 | **Promessa que o manual não sustenta.** O site diz "Cada regra do Manual vira uma automação". No manual, dos 51 critérios, 31 são automáticos, 18 são "IA + revisão do professor" e 2 são manuais. | texto da etapa 3 em `js/dados.js` | Trocar por algo como "A maioria das regras vira automação; o professor revisa o resto". Evita pergunta difícil da banca. |
| C5 | **A ficha do site não cumpre o P2.2 do manual.** O manual pede ≥ 14 pt (≈ 18,7 px) na versão padrão. A ficha padrão usa 14 px, a versão TEA usa 16 px e a rotina do TEA usa 13 px. O título da ficha original usa Georgia (com serifa), que o P2.3 proíbe. A versão baixa visão (24 px) cumpre o P2.2. | `web/css/ficha.css` | Subir as versões adaptadas para ≥ 18,7 px. A ficha "original" pode continuar ruim de propósito, mas rotulada como "antes". |
| C6 | **Fundo creme ou branco?** O site tem a regra "fundo sem brilho forte (creme)" marcada "a validar pela pesquisa". O backend usa branco puro. O manual não decide. | `js/dados.js` (R-DALT-07), `renderizador.py` | Decidir em grupo. Se o creme ficar, a pesquisa registra a fonte e o backend passa a usá-lo. |
| C7 | **O manual e o site não seguem os critérios do próprio manual.** P2.3 proíbe maiúsculas: os rótulos do site e das abas estão em maiúsculas. P2.2 pede ≥ 14 pt: há texto de 11 a 13,6 px. P3.1 pede ≤ 20 palavras por frase: o texto técnico tem várias maiores (início: 3, mini curso: 10, manual: cerca de 45, medido de forma aproximada). | site, aba, PDF | Escrever no manual o **escopo**: os critérios P2 e P3 valem para os materiais que a plataforma gera, e a interface segue o WCAG. Ou então reescrever os textos. Sem isso, um jurado atento nota a contradição. |
| C8 | **Os painéis (professor, aluno, família) têm cabeçalho só com a logo**, sem o menu e sem o rodapé da página inicial. | `web/painel/*.html` | Reaproveitar o mesmo cabeçalho. Fica para quando os painéis forem construídos. |

## 2. Acessibilidade: o que corrigir

Em ordem de importância.

1. **Números em Pixelify Sans são ambíguos.** O 5 parece S, o 3 parece B, o 0 parece 8. Ficou claro no meu primeiro teste: "2,5 mi" apareceu como "2,8 mi", e a questão 5 do simulador de daltonismo parecia "S". Para dados, anos e códigos, usar a fonte de texto. Na aba Instruções e no PDF já fiz isso. No site, vale para qualquer título ou número que use `--fonte-titulo`.
2. **Rolagem horizontal em celular (320 px).** `entrar.html` passa 24 px para fora da tela (`.entrar-arte` e `.entrar-painel`) e a página inicial passa 5 px (`ul.ficha-opcoes`). Como o `body` tem `overflow-x: hidden`, o conteúdo fica cortado e a pessoa não consegue rolar até ele. Na aba Instruções eu corrigi (0 px). Em letra 150% o site passa de 30 a 100 px; isso é extremo, mas vale olhar.
3. **Letras pequenas.** Na página inicial há texto de 11 px (`span`), 11,5 px (`.fonte`), 12 px (`.leg-item`, `li`) e 12,5 a 13 px (rótulos do seletor e do diagrama). Os rótulos em maiúsculas com Departure Mono a 12,8 px são os mais difíceis de ler. Sugestão: mínimo de 14 px.
4. **Modo acromatopsia:** `--ceu-escuro` (`#2B2B2B`) e `--laranja-escuro` (`#262626`) ficam quase iguais (ΔE 2,4). Tudo o que usa azul e laranja para dizer "dois estados" some. Sugestão: `--laranja-escuro` mais claro, por exemplo `#5A5A5A` (continua com contraste maior que 4,5:1 no fundo claro), ou sempre usar símbolo e padrão.
5. **Modos protanopia e deuteranopia:** o verde vira `#8DB4F0`, que fica quase igual ao `--ceu` (`#57B3F9`, ΔE 6,9) e ao fundo azul claro (`--grama-claro` e `--ceu-claro`: ΔE 1,2 a 2,3). O site ameniza com borda tracejada nas etiquetas "ok", mas diagramas que usam verde e azul juntos perdem a separação. Sugestão: nesses modos, trocar o verde por amarelo-âmbar e manter o símbolo ✓.
6. **Cores vivas no modo padrão:** `--ceu` e `--lilas` ficam muito parecidos para quem tem protanopia (ΔE 4,9). É o par "azul e roxo" que o nosso P1.3 lista como difícil. Se aparecerem lado a lado, acrescentar símbolo ou rótulo.
7. **Menu fixo translúcido.** Com o topo a 92% de opacidade, o texto da página aparece borrado atrás do menu, principalmente em alto contraste. Sugestão: fundo sólido no modo alto contraste.

## 3. O que eu fiz na aba Instruções

- A aba está em `web/prisma-instrucoes/index.html`, ligada ao menu **Instruções** da página inicial, com os dois subtítulos **Mini curso** e **Manual**.
- Visual do site: logo pixel (`prisma-logo.svg`), fontes, cores, borda pixel, barra de acessibilidade, menu e rodapé. Trocar uma cor em `tokens.css` muda a aba junto.
- Os 4 modos de daltonismo, o alto contraste, a fonte para dislexia e o tamanho da letra mudam a aba também (conferido nos 8 modos).
- Números, códigos e dados sempre na fonte do texto.
- PDF do manual: logo pixel na capa, fontes e cores do site, números na fonte do texto, sem depender de fontes fora do repositório.
- Problemas que achei na aba e já corrigi: rolagem horizontal no manual em celular, letras pequenas, linhas longas, cantos arredondados nos gráficos.

## 4. O que já foi corrigido (31/10, à noite)

Decisões do grupo: identidade do site em tudo, fundo creme no material gerado e **o site também segue P2 e P3**.

| Item | O que mudou |
|---|---|
| C1 | `renderizador.py` usa as fontes e cores do site. Contraste conferido nos testes. |
| C2 | O site mostra os critérios do manual (P1.1, P6.2...). Os 15 códigos antigos foram trocados. `regras.json` saiu dos comentários. |
| C3 | Tabela "equivale a" no `README.md`. |
| C4 | A frase virou "A maioria das regras do Manual vira automação. O professor revisa o resto." |
| C5 | Todas as fichas com letra de pelo menos 14 pt. A ficha "antes" continua com título serifado, de propósito. |
| C6 | Material gerado com fundo creme `#FBF7EE`. |
| C7 | O site segue P2 e P3: piso de 14 pt em todo `font-size` (`--letra-min`), nada em maiúsculas, linha de até 60 caracteres, sem itálico, frases de até 20 palavras e sem abreviações. Verificado em todas as páginas; só ficam de fora os exemplos de "antes" da aba Instruções. No manual, 24 frases foram divididas, sem mudar fatos nem números, e "&" virou "e" nas citações. |
| C8 | Os painéis têm o mesmo menu e rodapé da página inicial. |
| A1 | A fonte pixel só desenha letras; os números caem na Atkinson (`unicode-range`). |
| A2 | 0 px de rolagem lateral em 320 px nas páginas medidas. |
| A3 | Nenhum texto abaixo de 14 pt (fora os exemplos de "antes"). |
| A4 | Acromatopsia: `--laranja-escuro` passou a `#5A5A5A` (ΔE de 2,4 para 20,7). |
| A5 | Protanopia e deuteranopia: o verde virou amarelo `#E8D44D` (ΔE contra o azul céu acima de 100). |
| A6 | Céu e lilás só aparecem juntos nas figurinhas, que já têm ícone e nome. |
| A7 | Menu fixo com fundo sólido. O pontilhado atrás dos diagramas saiu (P2.7). |

Os ΔE foram medidos com as mesmas matrizes de Machado (2009) do relatório; o script reproduz os valores da tabela acima.

## 5. Para decidir em grupo (sugestão de ordem)

1. C1: aprovar a identidade do site para tudo, inclusive o material gerado.
2. C7: decidir o escopo dos critérios P2 e P3 (material gerado × interface).
3. C2 e C3: um vocabulário e um sistema de códigos só.
4. C4: corrigir a frase "cada regra vira automação" antes do pitch.
5. Acessibilidade 1 a 3 (números, celular, letras pequenas): são rápidas e aparecem na demo.
