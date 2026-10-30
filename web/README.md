# Site do PRISMA (protótipo de interface)

**PRISMA**: Plataforma de Recursos Inclusivos e Sala de Materiais Acessíveis.
Só interface por enquanto: dados fictícios, sem backend, login falso.

## Como abrir

Dê **duplo clique em `index.html`**. Não precisa instalar nada nem ter internet:
fontes, ícones e a biblioteca de animação estão dentro da pasta.

Se preferir um servidor local (a partir da raiz do repositório):

```bash
python -m http.server 8765 --directory web
```

e abra http://localhost:8765.

## Páginas

| Arquivo | O que é |
|---|---|
| `index.html` | Página inicial: escola pixel, diagrama radial, antes e depois, públicos, princípios |
| `entrar.html` | Login: escolher perfil → formulário (professor, família, aluno com senha de figurinhas) |
| `painel/*.html` | Painel de cada perfil, ainda "em construção" |

## Onde mexer

| Quero mudar… | Arquivo |
|---|---|
| Cores, fontes, tamanhos | `css/tokens.css` |
| Botões, cartões, barra de acessibilidade | `css/componentes.css` |
| Necessidades do seletor, regras, alunos fictícios, textos das 5 etapas | `js/dados.js` |
| A ficha de exemplo e suas versões adaptadas | `js/material.js` + `css/ficha.css` |
| Diagrama radial | `js/diagrama.js` + `css/diagramas.css` |
| Diagrama antes e depois | `js/fluxo.js` + `index.html` (seção `#antes-depois`) |
| Login (formato dos dados, para o backend) | `js/auth.js` |

### Ligar ao backend depois

Só `js/auth.js` precisa mudar: troque o conteúdo de `Prisma.auth.entrar(perfil, dados)` por uma
chamada ao servidor. O formato de `dados` está documentado no topo do arquivo.
As regras de `js/dados.js` devem passar a vir de `docs/manual/regras.json`.

## Arte e animações (geradas por script)

Rodar dentro de `web/`, com Python e Pillow (`pip install pillow`):

| Script | Gera |
|---|---|
| `python ferramentas/gerar_logo.py` | Logo e favicon |
| `python ferramentas/gerar_icones.py` | `js/icones.js` a partir de `assets/icones/*.svg` |
| `python ferramentas/adaptar_animacoes.py` | Animações na paleta do site (`assets/anim/*.js`) a partir de `assets/anim/originais/` |

As animações ficam com cara de pixel art no navegador: `js/lottie-pixel.js` desenha em baixa resolução,
troca cada pixel pela cor da paleta que mais aparece em volta dele e amplia sem suavizar, sempre por um número
inteiro (2x, 3x) para todos os pixels terem o mesmo tamanho.

A escola do topo (`assets/img/escola.jpg`), os personagens (coruja = professor, preguiça = aluno,
urso = família) e o carcará (mascote do time) vieram das ilustrações do time e estão em `assets/img/`.

## Acessibilidade (a interface pratica o que o PRISMA prega)

- Barra no topo: aumentar letra, alto contraste, fonte para dislexia, daltonismo (protanopia, deuteranopia,
  tritanopia, acromatopsia) e pausar animações (fica salvo no navegador). As cores de cada modo ficam em `css/tokens.css`.
- Respeita "reduzir movimento" do sistema.
- Tudo navegável por teclado, com foco visível; o seletor de necessidade funciona com as setas.
- Cor nunca sozinha: todo status tem ícone ou palavra.

Licenças de fontes, ícones e biblioteca: [`assets/LICENCAS.md`](assets/LICENCAS.md).
