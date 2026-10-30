# Plano do site inicial (protótipo de interface)

> Status: **implementado** em `web/` (ver [`web/README.md`](../web/README.md)).
> Escopo desta fase: só interface e design, com dados fictícios. Sem backend, sem login real.
>
> **Decisões tomadas depois deste plano:**
> - Nome oficial: **PRISMA** (Plataforma de Recursos Inclusivos e Sala de Materiais Acessíveis). Logo: um prisma pixel que transforma um feixe em arco-íris (um material, várias versões). O carcará virou mascote do time.
> - Ilustrações enviadas pelo time: coruja (professor), preguiça (aluno), urso (família), carcará e a escola com o Pão de Açúcar e o bondinho (`web/assets/img/escola.jpg`). O texto do topo fica numa placa clara por cima da imagem.
> - Os dois diagramas foram feitos.
> - O seletor tem: protanopia, deuteranopia, tritanopia, acromatopsia, baixa visão e TEA. Cada um gera uma versão diferente da ficha de exemplo, com as regras do Manual aplicadas, simulação de como o aluno enxerga e marcação de barreiras na original.
> - As perguntas da seção 10 abaixo já foram respondidas.

## 1. Objetivo

Um site que apresente a ferramenta (adaptador de aula inclusiva) para jurados, professores e famílias,
com a cara de uma plataforma escolar amigável para crianças do ensino fundamental.
Inspirado no estilo pixel do [cofounder.co](https://cofounder.co/), mas com identidade própria.

O site também precisa **praticar o que a ferramenta prega**: ser acessível (contraste, teclado,
leitor de tela, menos animação para quem precisa).

## 2. O que eu vi no cofounder.co e o que vamos aproveitar

| No cofounder | No nosso site |
|---|---|
| Hero com cenário pixel (árvore, laptop, céu) | Cenário pixel de escola: pátio, lousa, carteiras, árvore, sol |
| Fundo creme (`#F5F5F2`), texto quase preto, muito espaço vazio | Fundo "papel de caderno" (`#FBF7EE`) com mais cor (céu, sol, grama) |
| Fonte de títulos fina e elegante + rótulos em fonte mono pixel (Departure Mono) | Títulos em fonte pixel legível + texto em fonte feita para baixa visão + rótulos em Departure Mono |
| Diagrama radial: "Cofounder" no centro com girassol pixel, departamentos em volta, linhas tracejadas, círculo | Mesmo conceito, mas com o **ciclo da aula** no centro (detalhes na seção 5) |
| Diagrama de fluxo com grade pontilhada e setas tracejadas entre cartões | Seção "Antes e depois": material original virando versões adaptadas |
| Seções numeradas "1.0 — LAUNCH" com lista sanfona "1.1, 1.2…" | Seções "1.0 — PERFIL", "2.0 — MATERIAL"… com sanfona e uma prévia ao lado |
| Botões escuros arredondados, discretos | Botões pixel com "degrau" de sombra e efeito de apertar (mais infantil) |

O que vamos fazer **diferente** (item 4 do pedido):
- **Mascote**: um carcará pixel (nome do time) no lugar do girassol, que pisca e acena.
- **Barra de acessibilidade** fixa: aumentar letra, alto contraste, fonte para dislexia, pausar animações.
  O próprio site vira uma demonstração das adaptações.
- **Animações "pixelizadas"**: os modelos Lottie são desenhados em baixa resolução e ampliados sem
  suavização, com as cores trocadas pela nossa paleta (seção 6).
- **Login com "senha de figurinhas"** para o aluno (seção 7).
- **Linhas do diagrama com "pacotinhos" de pixel** andando de uma etapa para a outra, mostrando o ciclo.

## 3. Tecnologia

- **HTML + CSS + JavaScript puro**, sem framework e sem etapa de build. Combina com a divisão do time
  (`web/` é HTML/CSS/JS) e qualquer pessoa consegue editar.
- Biblioteca única: **lottie-web** (para as animações), copiada para `web/vendor/` para a demo
  funcionar **sem internet**. Fontes também ficam locais.
- As animações JSON viram arquivos `.js` (`window.ANIM_LIVROS = {...}`), para o site abrir com
  **duplo clique no `index.html`**, sem precisar de servidor.

### Estrutura de pastas

```
web/
  index.html              página inicial
  entrar.html             escolha de perfil e login (protótipo)
  painel/
    professor.html        "em construção" (placeholder para o login futuro)
    familia.html
    aluno.html
  css/
    tokens.css            cores, fontes, tamanhos, sombras (variáveis)
    base.css              reset, tipografia, foco visível
    componentes.css       botões, cartões, sanfona, barra de acessibilidade
    diagrama.css
    paginas.css
  js/
    acessibilidade.js     barra de acessibilidade (salva preferências)
    diagrama.js           diagrama radial animado
    fluxo.js              diagrama "antes e depois"
    lottie-pixel.js       desenha Lottie em baixa resolução + troca de paleta
    entrar.js             troca de formulário por perfil, senha de figurinhas
    auth.js               "contrato" do login (falso por enquanto)
  assets/
    fontes/  icones/  img/  anim/
  vendor/lottie.min.js
  README.md               como abrir e editar
```

## 4. Identidade visual

### Paleta (contrastes já conferidos, todos passam no WCAG AA)

| Nome | Cor | Uso | Contraste |
|---|---|---|---|
| papel | `#FBF7EE` | fundo | — |
| tinta | `#1E2235` | texto, bordas pixel | 14,7 : 1 sobre papel |
| céu | `#57B3F9` | preenchimentos, destaques | tinta sobre céu 6,9 : 1 |
| céu escuro | `#1F6FB2` | links | 4,9 : 1 |
| sol | `#FFC93C` | botão principal | tinta sobre sol 10,2 : 1 |
| laranja | `#FFAD60` | etiquetas, livros | 8,5 : 1 |
| grama | `#7BD389` / `#2E7D32` | sucesso, "aprovado" | 8,6 / 4,8 : 1 |
| carcará | `#8A5A2B` | mascote, detalhes | 5,5 : 1 |
| lousa | `#2F4F3E` | seções escuras (texto papel) | 8,5 : 1 |

Regra do nosso próprio Manual: **cor nunca sozinha**. Todo status tem ícone ou palavra junto
(ex.: ✓ "Aprovado", não só verde).

### Fontes (todas gratuitas, licença aberta)

| Papel | Fonte | Por quê |
|---|---|---|
| Títulos | **Pixelify Sans** (Google Fonts) | Pixel, mas legível (a Press Start 2P cansa a leitura) |
| Texto | **Atkinson Hyperlegible Next** (Google Fonts) | Criada para pessoas com baixa visão. Ótimo argumento no pitch |
| Rótulos e números | **Departure Mono** | A mesma que o cofounder usa nos rótulos |
| Modo dislexia | **OpenDyslexic** | Ativada pela barra de acessibilidade |

Tamanhos: texto 18px (mínimo 16px), títulos 40–56px, rótulos 13–14px em maiúsculas.

### Componentes (eu faço em CSS, não precisa de imagem)

**Botão principal**
- Altura mínima 48px (alvo de toque), padding 12px × 24px, texto 18px Pixelify Sans
- Fundo sol, borda tinta de 3px, **cantos "recortados" em degrau** de 3px (efeito pixel, sem arredondar)
- Sombra sólida 4px para baixo (sem desfoque). Ao clicar, o botão desce 4px e a sombra some ("aperta")
- Foco do teclado: contorno céu de 3px com 3px de distância

**Botão secundário**: fundo papel, mesma borda e sombra. **Botão fantasma**: só texto sublinhado.

**Cartão**: fundo branco, borda tinta 3px, cantos em degrau, sombra sólida 6px na diagonal.

**Ícones**: [Pixelarticons](https://pixelarticons.com/) (licença MIT, 24×24, SVG).
Uso: livro, lápis, olho, volume, usuário, usuários, cadeado, check, gráfico, casa, e-mail, estrela.

**Grade pontilhada** de fundo nos diagramas (como no cofounder), em CSS puro.

## 5. Página inicial (`index.html`), seção por seção

1. **Barra de acessibilidade** (topo, recolhível): A+ / A− · Alto contraste · Fonte dislexia · Pausar animações.
   Respeita `prefers-reduced-motion` e salva a escolha no navegador.
2. **Menu**: logo · Como funciona · Professores · Famílias · Princípios · botão **Entrar**.
3. **Hero**: cenário pixel de escola em tela cheia (ilustração, ver seção 8). Título:
   "Uma aula. Todos os alunos aprendendo juntos." + subtítulo da frase do README +
   botões "Ver como funciona" e "Entrar". Animação: nuvens andando devagar, mascote piscando.
4. **Diagrama radial "Como funciona"** (pedido 3), dentro de um cartão grande com grade pontilhada:
   - **Centro**: nome da ferramenta, com o mascote carcará pixel em cima (no lugar do girassol).
   - **Anel interno, 5 nós**: 1 Perfil · 2 Material · 3 Adaptação · 4 Guia · 5 Mini-check.
   - **Nós externos (caixinhas cinza, como no cofounder)**: detalhes de cada etapa. Ex.: em volta de
     "Adaptação": Fonte ampliada, Alto contraste, Cor + símbolo, Instruções em etapas, Áudio.
     Ligado a "Adaptação" fica o nó "Manual de Acessibilidade (regras)".
   - **Linhas**: tracejadas em pixel (quadradinhos). Um "pacotinho" de pixel sai do centro e percorre
     1 → 2 → 3 → 4 → 5 → volta ao 1, mostrando que é um ciclo. O nó ativo acende.
   - **Painel ao lado** (como o chat do cofounder, mas em estilo "caderno"): mostra o que acontece na
     etapa ativa com um aluno fictício. Ex.: "Aluno Fictício A, 5º ano. Precisa de fonte ampliada e
     instruções em etapas."
   - **Seletor de aluno fictício** no topo do cartão (baixa visão · daltonismo · TEA): muda quais
     adaptações acendem no diagrama.
   - **Acessível**: cada nó é um botão, dá para navegar com Tab e setas; o painel é lido pelo leitor
     de tela; com "pausar animações" o ciclo para.
   - **Celular**: vira uma linha do tempo vertical com as mesmas 5 etapas.
   - Feito em **SVG + JS próprio** (sem biblioteca), fácil de mudar os textos num único objeto de dados.
5. **"Antes e depois"** (o segundo diagrama do cofounder): cartões ligados por setas tracejadas
   sobre grade pontilhada. "Texto original" → "Regras do Manual" → 4 versões adaptadas →
   "Professor aprova ✓" → "Guia da família". Os cartões aparecem em sequência ao rolar a página.
6. **Seções numeradas por público** (sanfona à esquerda, prévia à direita):
   - **1.0 Professores**: 1.1 Cadastrar necessidades · 1.2 Enviar o material · 1.3 Revisar e aprovar · 1.4 Mini-check.
     Animação: computador (Programming Computer pixelizado).
   - **2.0 Famílias**: 2.1 Guia em linguagem simples · 2.2 O que fazer em casa · 2.3 Quando procurar um profissional.
     Animação: livro abrindo (Book pixelizado).
   - **3.0 Alunos**: 3.1 Mesmo conteúdo, do seu jeito · 3.2 Escolher como ler (áudio, letra maior) · 3.3 Mini-check divertido.
     Animação: três livros pulando (Books pixelizado).
7. **Princípios** (5 cartões com ícone): Identificar barreiras, nunca diagnosticar · O professor aprova ·
   Mesmo conteúdo para todos · Alunos fictícios (LGPD) · Interface acessível.
8. **Chamada final**: "Comece pela sua turma" + botão Entrar.
9. **Rodapé**: grama pixel, Time Carcará 3301 · IME · Hackathon LEP, link do GitHub.

Textos: tirados do README e da divisão de tarefas. **Nenhum número de estatística** entra antes de a
pesquisa confirmar a fonte; onde precisar, fica `[dado a confirmar]`.

## 6. Adaptação das animações JSON (pedido 4)

O que encontrei nos 3 arquivos:

| Arquivo | O que é | Detalhe técnico |
|---|---|---|
| `Books.json` | 3 livros isométricos pulando em sequência | 1000×1000, 30 fps, 4 s. Cores azul `#57B3F9`, laranja `#FFAD60`, cinza escuro |
| `Book.json` | Livro aberto virando páginas | 512×512, 60 fps, 3 s, 48 camadas, tons de azul. Arquivo pesado (470 KB) |
| `Programming Computer.json` | Laptop isométrico com porta-lápis | 600×450. **Usa 5 imagens PNG embutidas** com degradê roxo, não vetores |

Como vou adaptar:
1. **Trocar as cores** de cada camada pela nossa paleta (script Python que reescreve o JSON).
   Os livros ficam céu, sol e laranja; o contorno vira tinta.
2. **Pixelizar na hora**: a animação é desenhada num canvas pequeno (ex.: 96×96) e ampliada 4–6× sem
   suavização. Isso transforma qualquer animação em pixel art, **inclusive as imagens PNG do laptop**.
3. **Reduzir as cores** (opcional): cada pixel vai para a cor mais próxima da paleta, para ficar com
   cara de jogo antigo.
4. **Animação "em passos"**: tocar a ~12 quadros por segundo, como um sprite, em vez de 60.
5. Com "pausar animações" ligado, mostra só um quadro parado.

Risco: o laptop roxo pode ficar estranho mesmo pixelizado. Plano B: trocar as 5 imagens PNG dele por
versões redesenhadas na nossa paleta (eu consigo gerar em baixa resolução).

## 7. Aba de login (pedido 5), `entrar.html`

Só interface. Nada é enviado a lugar nenhum.

1. **Passo 1, "Quem é você?"**: 3 cartões grandes com personagem pixel: Professor(a) · Família · Aluno(a).
2. **Passo 2, formulário de cada perfil**:
   - **Professor(a)**: e-mail + senha, "Esqueci a senha", "Criar conta da escola".
   - **Família**: e-mail + senha **ou** "Tenho um código da escola".
   - **Aluno(a)**: código da turma (ex.: `SOL-42`) + **senha de figurinhas**: escolher 3 figuras pixel
     em ordem (🍎 ⭐ 🐱). Não exige leitura nem digitação, bom para alunos pequenos ou com dificuldade motora.
3. Um aviso "Protótipo: os dados não são salvos".
4. `js/auth.js` define o "contrato" que o backend vai cumprir depois:
   `entrar(perfil, dados)` → por enquanto finge que deu certo e vai para `painel/<perfil>.html`
   ("em construção"). Quando o backend existir, só essa função muda.
5. Formulários com rótulos, mensagens de erro lidas pelo leitor de tela e tudo navegável por teclado.

## 8. O que eu preciso de vocês (pedido 2)

Botões, cartões, ícones, grade, diagramas e a barra de acessibilidade **eu faço em código**.
O que faz diferença vir de vocês são as **ilustrações pixel**:

| # | Peça | Tamanho em pixels (desenho) | Detalhes | Prioridade |
|---|---|---|---|---|
| 1 | **Cenário do hero** (pátio ou sala de aula) | 480×270 (eu amplio 4×, fica Full HD) | Lousa, carteiras, árvore, céu. Céu e nuvens numa camada separada para eu animar. Deixar a área de cima à esquerda mais "vazia" para o título | Alta |
| 2 | **Mascote carcará** | 32×32, de frente | 2 a 4 quadros (parado, piscando, acenando) em uma tira PNG (sprite sheet) | Alta |
| 3 | **Logo / nome** | — | Primeiro precisamos decidir o nome (ver perguntas) | Alta |
| 4 | **3 personagens do login** | 48×48 cada | Professor(a), família (adulto + criança), aluno(a). Diversos, sem estereótipo | Média |
| 5 | **Figurinhas da senha do aluno** | 16×16, 9 a 12 figuras | Maçã, estrela, gato, sol, bola, flor, peixe, lápis, foguete… | Média |
| 6 | **Enfeites** | 16×16 | Flor, joaninha, lápis, maçã (para espalhar como no cofounder) | Baixa |

Regras para todas as ilustrações:
- PNG com fundo transparente, **sem suavização** (anti-aliasing desligado), 1 pixel do desenho = 1 pixel do arquivo.
- Usar só as cores da paleta acima (mais 2 ou 3 tons de cada, se precisar).
- Ferramentas grátis: [Piskel](https://www.piskelapp.com/) (navegador) ou LibreSprite. Aseprite é pago.

**Se vocês não tiverem tempo**, eu faço versões provisórias de todas essas peças (SVG/CSS pixel)
para o protótipo funcionar, e vocês trocam depois sem mexer no código.

## 9. Etapas de implementação

| # | Etapa | Resultado |
|---|---|---|
| 1 | Base: pastas, `tokens.css`, fontes locais, botões, cartões, barra de acessibilidade | Uma página de "catálogo" com todos os componentes |
| 2 | Página inicial: menu, hero (provisório), seções, princípios, rodapé | Página navegável do começo ao fim |
| 3 | Diagrama radial animado + painel + seletor de aluno + versão celular | Seção "Como funciona" pronta |
| 4 | Diagrama "Antes e depois" | Seção pronta |
| 5 | Script de troca de cores + `lottie-pixel.js` + as 3 animações no lugar | Animações no estilo pixel |
| 6 | `entrar.html` + `auth.js` + painéis "em construção" | Aba de login pronta |
| 7 | Revisão de acessibilidade (teclado, leitor de tela, contraste, celular) e capturas de tela | Lista do que passou e do que falta |

Tudo em uma branch `ricardo/site-inicial`, com um Pull Request para o time revisar.

## 10. Perguntas para decidir antes de começar

1. **Nome da ferramenta.** Ainda não temos. Sugestões: *Turma Toda*, *Todo Mundo Aprende*, *Ponte*, *Carcará*.
   Posso usar "Turma Toda" provisoriamente.
2. **Ilustrações**: vocês vão desenhar (seção 8) ou eu faço as provisórias?
3. **Paleta**: aprova as cores acima ou quer outra cor principal?
4. **Diagramas**: fazer os dois (radial + antes e depois) ou só o radial nesta primeira versão?
