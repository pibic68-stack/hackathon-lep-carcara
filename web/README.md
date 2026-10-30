# Site da Trama

HTML, CSS e JavaScript puros. Não precisa instalar nada.

## Como abrir

```bash
cd web
python -m http.server 8000
```

Depois abra http://localhost:8000. Também funciona abrindo `index.html` direto no navegador.

## Arquivos

| Arquivo | O que tem |
|---|---|
| `index.html` | Estrutura da página e textos fixos |
| `css/style.css` | Cores, tipografia e layout. Os valores estão no começo, em `:root` |
| `js/app.js` | Demonstração: disciplinas, adaptações, perfil do aluno e seletor de ano |
| `img/hero.png` | Cena em pixel art do topo (360x216, exibida ampliada sem suavização) |
| `img/gerar_cena.py` | Script que desenha a cena (`pip install pillow`, depois `python gerar_cena.py`) |
| `fonts/` | Atkinson Hyperlegible (texto) e Instrument Serif (logo), licença OFL |

## Como a demonstração funciona

- As **abas** são as disciplinas. Para incluir uma, adicione um item em `DISCIPLINAS` (em `app.js`) e um visual em `VISUAIS`.
- Cada **necessidade** do perfil liga uma adaptação: `cores` (símbolo, padrão e palavra junto da cor), `leitura` (frases curtas e espaçamento), `letra` (letra maior e alto contraste) e `foco` (uma etapa por vez).
- O botão **Ver como alguém com daltonismo vê** aplica um filtro de cor só para quem está avaliando a página. Ele não é parte da adaptação.
- Os conteúdos são exemplos escritos à mão. Na versão final, o backend gera as adaptações a partir de `docs/manual/regras.json`.

## Regras do time para este site

- Só alunos fictícios.
- Cor nunca sozinha: sempre com símbolo, padrão ou palavra.
- Se mudar a cor de fundo (`--papel` no CSS), mude também `PAPEL` em `img/gerar_cena.py` e gere a cena de novo.
- Antes de subir mudanças, teste com o teclado (Tab, setas nas abas) e confira o contraste.
