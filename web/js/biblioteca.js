/* Biblioteca de materiais publicados (aluno e família). Só aparece o que o professor aprovou (P10.1).
   Cada versão tem o nome do jeito de estudar ("Letras grandes", "Ouvir"), nunca de deficiência (P5.3). */
(function () {
  function el(tag, attrs, filhos) {
    var n = document.createElement(tag);
    Object.keys(attrs || {}).forEach(function (k) {
      if (k === "texto") n.textContent = attrs[k];
      else if (k === "classe") n.className = attrs[k];
      else n.setAttribute(k, attrs[k]);
    });
    (filhos || []).forEach(function (f) { if (f) n.appendChild(typeof f === "string" ? document.createTextNode(f) : f); });
    return n;
  }

  document.addEventListener("DOMContentLoaded", function () {
    var area = document.getElementById("area-biblioteca");
    if (!area) return;
    var estado = el("div", { role: "status", "aria-live": "polite" });
    var lista = el("ul", { classe: "lista-materiais" });
    area.appendChild(el("h2", { texto: "Materiais da turma" }));
    area.appendChild(estado);
    area.appendChild(lista);

    Prisma.api.biblioteca().then(function (itens) {
      if (!itens.length) {
        estado.appendChild(el("p", { classe: "dica", texto: "Ainda não há materiais publicados. Quando a professora aprovar um, ele aparece aqui." }));
        return;
      }
      itens.forEach(function (m) {
        var botoes = Object.keys(m.versoes).map(function (k) {
          return el("li", {}, [el("a", {
            classe: "botao botao--secundario botao--pequeno", href: Prisma.api.url(m.versoes[k].url),
            target: "_blank", rel: "noopener", texto: m.versoes[k].rotulo
          })]);
        });
        lista.appendChild(el("li", { classe: "cartao" }, [
          el("h3", { texto: m.material }),
          el("p", { classe: "dica", texto: "Escolha o jeito que ajuda você a estudar:" }),
          el("ul", { classe: "botoes-versoes" }, botoes)
        ]));
      });
    }).catch(function (e) { estado.appendChild(el("p", { classe: "erro", texto: e.message })); });
  });
})();
