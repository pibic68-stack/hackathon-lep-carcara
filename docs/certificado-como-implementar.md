# Certificado do mini curso: como ligar no site

Para: Szpigel. De: Ricardo (com o Claude). 31/10/2026.

O certificado já está pronto em `web/certificado/`. Falta só uma coisa: quando a pessoa termina o mini curso, aparecer um botão "Baixar certificado".
Este guia mostra onde mexer e o código para colar. Dá umas 30 linhas.

## 1. O que já existe

| Arquivo | O que faz |
|---|---|
| `web/certificado/modelo.html` | O certificado. A4 deitado, uma só página para as 3 trilhas. Lê o nome e a trilha do `#` do endereço. |
| `web/certificado/certificado.js` | `PrismaCertificado.abrir({ papel, nome })`: abre o certificado preenchido numa aba nova e já mostra "Salvar em PDF". |
| `web/certificado/gerar_pdf.py` | Opcional: gera o PDF no backend, para baixar direto sem a janela do navegador. |
| `web/certificado/exemplos/` | Os 3 PDFs de exemplo, para você ver como fica. |
| `web/certificado/LEIA-ME.md` | Detalhes do modelo (cores, textos, código do certificado). |

Abra `web/certificado/modelo.html` com duplo clique para brincar: tem uma barra em cima para digitar o nome e trocar a trilha.

A trilha usa os mesmos códigos do mini curso. Ninguém precisa traduzir nada:

| Botão no mini curso | `document.body.dataset.trilha` | Certificado |
|---|---|---|
| Sou professor(a) | `prof` | moldura azul, coruja |
| Sou da família | `fam` | moldura laranja-escuro, urso |
| Sou estudante | `est` | moldura verde, preguiça |

## 2. Onde mexer

Só em **`web/prisma-instrucoes/src/pagina.html`**. Nunca no `index.html` dessa pasta: ele é gerado.
Depois de editar, gere de novo:

```bash
python web/prisma-instrucoes/build.py
```

### Passo 1: carregar os dois scripts

Perto da linha 367, logo antes de `<script src="__BASE__js/icones.js"></script>`, coloque:

```html
<script src="__BASE__js/auth.js"></script>
<script src="__BASE__certificado/certificado.js"></script>
```

O `auth.js` serve para pegar o nome de quem está logado. Sem login ou sem backend, ele só devolve `null` e nada quebra.

### Passo 2: avisar quando o mini-check terminar

Na função `montaQuiz` (perto da linha 531), troque a primeira linha e o trecho do placar.

No começo da função, apague o certificado da trilha anterior (a função roda de novo quando a pessoa troca de trilha):

```js
function montaQuiz(){const t=document.body.dataset.trilha||"prof";const q=$("#quiz");q.innerHTML="";$("#cert")?.remove();let feitos=0,acertos=0;
```

E no clique da resposta, onde hoje está

```js
if(feitos===QUIZ[t].length)placar.textContent=`Você acertou ${acertos} de ${feitos}.`
```

passe a ser

```js
if(feitos===QUIZ[t].length){placar.textContent=`Você acertou ${acertos} de ${feitos}.`;mostraCertificado(t)}
```

### Passo 3: a caixa do certificado

Cole esta função logo depois de `montaQuiz`:

```js
/* ---------- certificado: aparece quando o mini-check termina ---------- */
function mostraCertificado(t){
  if($("#cert"))return;
  const c=document.createElement("div");c.id="cert";c.className="painel cert";
  c.innerHTML=`<h3 tabindex="-1">Você concluiu o mini curso</h3>
    <p>Baixe o seu certificado em PDF.</p>
    <label for="cert-nome">Nome que vai no certificado</label>
    <input id="cert-nome" type="text" autocomplete="name" maxlength="80">
    <p class="cert-erro" id="cert-erro" role="alert"></p>
    <button type="button" class="btn" id="cert-baixar">Baixar certificado</button>`;
  $("#quiz").after(c);
  // com login, o nome já vem preenchido (a pessoa pode corrigir)
  if(window.Prisma&&Prisma.auth)Prisma.auth.sessao().then(u=>{if(u&&u.perfil!=="familia"&&!$("#cert-nome").value)$("#cert-nome").value=u.nome});
  $("#cert-baixar").addEventListener("click",()=>{
    const nome=$("#cert-nome").value.trim();
    if(nome.length<2){$("#cert-erro").textContent="Digite o nome que vai no certificado.";$("#cert-nome").focus();return}
    $("#cert-erro").textContent="";
    PrismaCertificado.abrir({papel:t,nome});
  });
  c.querySelector("h3").focus();
}
```

### Passo 4: o visual da caixa

No fim de `web/prisma-instrucoes/src/estilo.css`:

```css
.cert{margin-top:18px}
.cert label{display:block;font-weight:700;margin:10px 0 6px}
.cert input{font:inherit;font-size:max(var(--letra-min),1.1rem);width:min(100%,28em);min-height:48px;padding:8px 12px;border:3px solid var(--cor-borda);background:var(--cor-superficie);color:var(--cor-texto)}
.cert input:focus-visible{outline:4px solid var(--cor-foco);outline-offset:2px}
.cert-erro{color:var(--cor-erro);font-weight:700;min-height:1.5em}
```

Rode o `build.py` e pronto.

## 3. Como testar

1. `python web/prisma-instrucoes/build.py`
2. Abra `web/prisma-instrucoes/index.html` com duplo clique.
3. Escolha uma trilha e responda as 4 perguntas do mini-check (passo 10).
4. Deve aparecer a caixa "Você concluiu o mini curso".
5. Clique em "Baixar certificado" sem nome: aparece o aviso e o cursor volta para o campo.
6. Digite um nome e clique de novo: abre uma aba com o certificado e a janela "Salvar em PDF".
7. Troque de trilha: a caixa some até terminar o mini-check da nova trilha.
8. Com o backend ligado e logado como professor, o nome já vem preenchido.

Na janela do navegador, escolha **Salvar como PDF**. O nome do arquivo já vem certo, por exemplo "Certificado PRISMA - professores - Ana Souza.pdf".

## 4. Opcional: baixar o PDF direto pelo backend

A opção acima mostra a janela do navegador. Para o PDF baixar direto, sem janela, use o `gerar_pdf.py` numa rota nova em `backend/adaptador/api.py`:

```python
import sys
sys.path.append(str(SITE / "certificado"))        # SITE já aponta para web/ no api.py
from gerar_pdf import gerar_pdf, nome_arquivo

class PedidoCertificado(BaseModel):
    papel: str        # prof | fam | est
    nome: str

@app.post("/api/certificado")
def certificado(corpo: PedidoCertificado, request: Request):
    pdf = gerar_pdf(corpo.papel, corpo.nome[:80])
    return Response(pdf, media_type="application/pdf",
                    headers={"Content-Disposition": f'attachment; filename="{nome_arquivo(corpo.papel, corpo.nome)}"'})
```

No site, o botão faz um `fetch` com o cabeçalho `X-Prisma: 1` (como os outros pedidos que mandam dados), pega o `blob()` e baixa.
Precisa de Chrome ou Edge no PC que roda o backend (o PC do time tem os dois). Cada PDF leva uns 2 segundos.

Minha sugestão: comece pela opção sem backend. Ela funciona com duplo clique e sem internet, que é como a demo roda.

## 5. Cuidados

- **Família**: o login da família guarda "Família de Lia", não o nome da pessoa. Por isso o código acima deixa o campo vazio para a família digitar.
- **Aluno**: o nome do login é o apelido fictício da turma. Ele vem preenchido, mas o aluno pode trocar.
- **Dados reais (LGPD)**: na demo, só nomes fictícios. O nome não vai para servidor nenhum na opção sem backend. Ele fica depois do `#` do endereço, que o navegador não envia.
- **Aba bloqueada**: `PrismaCertificado.abrir` precisa ser chamado dentro do clique. Se o navegador bloquear a aba nova, o certificado abre na mesma aba.
- **"Dez passos"**: o certificado diz "por concluir os dez passos e o mini-check". Hoje o site só sabe se o mini-check terminou. Se o time quiser exigir os 10 passos, é preciso guardar quais módulos a pessoa abriu. Ou então troque a frase no `modelo.html` (procure `motivo`).
- **Acessibilidade**: o campo tem rótulo, o aviso usa `role="alert"`, o botão tem 48 px de altura e o foco vai para o título da caixa quando ela aparece.

Qualquer dúvida, veja `web/certificado/LEIA-ME.md` ou me chame.
