# Certificado do mini curso PRISMA

Quem conclui o mini curso (aba Instruções) recebe um certificado em PDF com o seu nome.
A ideia do desenho vem da própria PRISMA: a logo (o prisma) fica no centro.
Um feixe cinza entra pela esquerda e sai pela direita em seis cores que se abrem em leque: uma aula entra, várias versões saem.
A moldura é pixel, com cantos em degrau e sombra sólida, como os cartões do site.
Pixelify Sans no título, Atkinson no nome e nos números, Departure Mono nos rótulos.

Há um modelo para cada trilha do mini curso. Mudam a cor da moldura e o mascote no canto de cima à esquerda.
O texto também diz a trilha (P1: cor nunca sozinha).

| Trilha | Código | Cor da moldura | Mascote (canto) | Exemplo |
|---|---|---|---|---|
| Professores | `prof` | céu escuro `#1F6FB2` | coruja | `gerar_pdf.py --exemplos` |
| Famílias | `fam` | laranja-escuro `#A3401F` | urso | `gerar_pdf.py --exemplos` |
| Estudantes | `est` | grama escura `#2E7D32` | preguiça | `gerar_pdf.py --exemplos` |

Os códigos `prof`, `fam` e `est` são os mesmos de `data-t` nos botões de trilha do mini curso.
Os nomes dos exemplos são fictícios.

## Arquivos

| Arquivo | O que é |
|---|---|
| `modelo.html` | O modelo (fonte única). Folha A4 deitada. Abre com duplo clique e tem uma barra para digitar o nome e salvar em PDF. A barra não sai no PDF. |
| `certificado.js` | Ajudante para o site: `PrismaCertificado.abrir({ papel, nome })`. |
| `gerar_pdf.py` | Gera o PDF pronto pelo Chrome ou Edge sem janela. Para o backend e para os exemplos. |

## Como preencher o modelo

Os dados vão depois do `#` do endereço. Essa parte não sai do computador.

```
modelo.html#papel=prof&nome=Ana%20Souza&data=2026-10-31&imprimir=1
```

- `papel`: `prof`, `fam` ou `est` (também aceita `professor`, `familia`, `aluno`, `estudante`).
- `nome`: nome de quem concluiu. Nome comprido diminui a letra e, se precisar, quebra em duas linhas.
- `data`: `AAAA-MM-DD`. Sem data, usa hoje. Sai por extenso: "31 de outubro de 2026".
- `imprimir=1`: abre a janela "Salvar em PDF" assim que a página carrega.

O rodapé mostra um código curto, como `prisma-prof-6a24-4c5e`.
Ele é sempre o mesmo para a mesma pessoa, trilha e data. Se um dia houver página de verificação, ela pode usar esse código.

## Como ligar no site (duas opções)


### 1. Sem backend: janela "Salvar em PDF" do navegador

Na aba Instruções, quando o mini-check terminar:

```html
<script src="../certificado/certificado.js"></script>
```

```js
// dentro do clique do botão "Baixar certificado"
PrismaCertificado.abrir({ papel: document.body.dataset.trilha, nome: nomeDoLogin });
```

Abre uma aba com o certificado preenchido e a janela de salvar já aberta.
O nome do arquivo sugerido vem do título: "Certificado PRISMA - professores - Ana Souza.pdf".
Funciona sem internet, inclusive com duplo clique no `index.html`.

### 2. Com backend: download direto do PDF

Esboço para `backend/adaptador/api.py` (adaptar à leitura de sessão que já existe lá):

```python
from fastapi.responses import Response
import sys; sys.path.append("web/certificado")
from gerar_pdf import gerar_pdf, nome_arquivo

@app.get("/api/certificado")
def certificado(usuario = Depends(sessao)):  # o nome vem da conta, não do pedido
    papel = {"professor": "prof", "familia": "fam", "aluno": "est"}[usuario.perfil]
    pdf = gerar_pdf(papel, usuario.nome)
    return Response(pdf, media_type="application/pdf",
                    headers={"Content-Disposition": f'attachment; filename="{nome_arquivo(papel, usuario.nome)}"'})
```

Precisa de Chrome ou Edge no PC que roda o backend (no PC do time já tem).
Para outro navegador, defina `PRISMA_NAVEGADOR` com o caminho do programa.
Cada PDF leva uns 2 segundos para sair.

## Onde mexer

| Quero mudar… | Onde, em `modelo.html` |
|---|---|
| Cor de uma trilha | `[data-papel="fam"] { --trilha }` |
| Texto da trilha ou mascote | objeto `PAPEIS` no script |
| Frase do rodapé | `<p class="faixa">` |
| Moldura | os `<polygon>` do SVG (sombra, tinta, cor da trilha, tinta, papel) |
| Feixe e raios de cor | o `<rect>` cinza e os `<g>` de cada cor no SVG: cada raio continua um raio da logo, em degraus de 1 pixel (2,4 mm), até a moldura |

Regras do Manual seguidas: letra mínima de 14 pt (P2.2), sem maiúsculas no texto corrido,
números nunca na fonte pixel, contraste conferido (texto branco sobre as 3 cores e as 3 cores sobre o papel passam de 4,5:1).
