/* Biblioteca da turma (aluno e família). Só aparece o que o professor aprovou (P10.1).
   Cada versão tem o nome do jeito de estudar ("Letras grandes", "Ouvir"), nunca de deficiência (P5.3).
   As versões que combinam com o perfil do aluno vêm primeiro, marcadas "do seu jeito". */
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

  function montarFamilia(u) {
    var area = document.getElementById("area-familia");
    if (!area) return;
    Prisma.api.opcoes().then(function (o) {
      var mapa = Object.assign({}, o.necessidades, o.preferencias);
      var itens = (u.necessidades || []).concat(u.preferencias || []);
      area.appendChild(el("h2", { texto: "Como " + u.apelido + " aprende melhor" }));
      area.appendChild(el("p", { texto: "A escola registrou o que ajuda nos estudos. Não é diagnóstico." }));
      area.appendChild(itens.length
        ? el("ul", {}, itens.map(function (k) { return el("li", { texto: mapa[k] || k }); }))
        : el("p", { classe: "dica", texto: "Nenhuma adaptação marcada ainda." }));
      area.appendChild(el("p", { texto: "Em casa, abra os materiais abaixo no jeito que mais ajuda." }));
    });
  }

  document.addEventListener("prisma:painel", function (ev) {
    var u = ev.detail;
    if (u.perfil !== "aluno" && u.perfil !== "familia") return;
    if (u.perfil === "familia") montarFamilia(u);
    var area = document.getElementById("area-biblioteca");
    var estado = el("div", { role: "status", "aria-live": "polite" });
    var lista = el("ul", { classe: "lista-materiais" });
    area.appendChild(el("h2", { texto: "Materiais da turma" }));
    area.appendChild(estado);
    area.appendChild(lista);

    Prisma.api.biblioteca().then(function (itens) {
      if (!itens.length) {
        estado.appendChild(el("p", { classe: "dica", texto: "Ainda não há materiais. Quando a professora aprovar um, ele aparece aqui." }));
        return;
      }
      itens.forEach(function (m) {
        var chaves = Object.keys(m.versoes).sort(function (a, b) {
          return (m.versoes[b].recomendada ? 1 : 0) - (m.versoes[a].recomendada ? 1 : 0);
        });
        var botoes = chaves.map(function (k) {
          var v = m.versoes[k];
          return el("li", {}, [el("a", {
            classe: "botao botao--pequeno " + (v.recomendada ? "" : "botao--secundario"), href: Prisma.api.url(v.url),
            target: "_blank", rel: "noopener", texto: v.recomendada ? "★ " + v.rotulo + " (do seu jeito)" : v.rotulo
          })]);
        });
        lista.appendChild(el("li", { classe: "cartao" }, [
          el("h3", { texto: m.titulo || m.material }),
          el("p", { classe: "dica", texto: "Escolha o jeito que ajuda a estudar. Todas as versões têm o mesmo conteúdo." }),
          el("ul", { classe: "botoes-versoes" }, botoes)
        ]));
      });
    }).catch(function (e) { estado.appendChild(el("p", { classe: "erro", texto: e.message })); });
  });
})();
