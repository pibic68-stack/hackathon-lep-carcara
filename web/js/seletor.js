/* Seletor de necessidade do aluno (fictício).
   Qualquer elemento com data-seletor-necessidade vira um grupo de chips.
   Todos os seletores da página ficam sincronizados.
   Para reagir à troca: document.addEventListener("prisma:necessidade", e => e.detail.id) */
(function () {
  var C = window.Prisma;
  C.necessidadeAtual = "protanopia";

  C.escolherNecessidade = function (id) {
    C.necessidadeAtual = id;
    document.querySelectorAll("[data-seletor-necessidade] [role=radio]").forEach(function (b) {
      var sel = b.dataset.id === id;
      b.setAttribute("aria-checked", sel);
      b.tabIndex = sel ? 0 : -1;
    });
    document.dispatchEvent(new CustomEvent("prisma:necessidade", { detail: { id: id, necessidade: C.necessidadePorId(id) } }));
  };

  function montar(alvo) {
    var grupos = [];
    C.NECESSIDADES.forEach(function (n) {
      var g = grupos.find(function (x) { return x.nome === n.grupo; });
      if (!g) grupos.push(g = { nome: n.grupo, itens: [] });
      g.itens.push(n);
    });
    var rotulo = alvo.dataset.rotulo || "Necessidade do aluno";
    alvo.innerHTML =
      '<p class="seletor-titulo" id="' + alvo.id + '-titulo">' + rotulo + "</p>" +
      '<div class="seletor-grupos" role="radiogroup" aria-labelledby="' + alvo.id + '-titulo">' +
      grupos.map(function (g) {
        return '<div class="seletor-grupo"><span class="seletor-grupo-nome" aria-hidden="true">' + g.nome + '</span><div class="chips">' +
          g.itens.map(function (n) {
            return '<button type="button" class="chip" role="radio" aria-checked="false" tabindex="-1" data-id="' + n.id + '"' +
              ' aria-label="' + (g.nome === "Daltonismo" ? "Daltonismo: " : "") + n.nome + '">' +
              '<span data-icone="' + n.icone + '"></span>' + n.nome + "</button>";
          }).join("") + "</div></div>";
      }).join("") + "</div>";
    if (window.aplicarIcones) window.aplicarIcones(alvo);

    alvo.addEventListener("click", function (e) {
      var b = e.target.closest("[role=radio]");
      if (b) C.escolherNecessidade(b.dataset.id);
    });
    // setas do teclado andam entre as opções (padrão de radiogroup)
    alvo.addEventListener("keydown", function (e) {
      var teclas = { ArrowRight: 1, ArrowDown: 1, ArrowLeft: -1, ArrowUp: -1 };
      if (!(e.key in teclas) && e.key !== "Home" && e.key !== "End") return;
      e.preventDefault();
      var botoes = Array.prototype.slice.call(alvo.querySelectorAll("[role=radio]"));
      var i = botoes.findIndex(function (b) { return b.dataset.id === C.necessidadeAtual; });
      if (e.key === "Home") i = 0; else if (e.key === "End") i = botoes.length - 1;
      else i = (i + teclas[e.key] + botoes.length) % botoes.length;
      C.escolherNecessidade(botoes[i].dataset.id);
      botoes[i].focus();
    });
  }

  document.addEventListener("DOMContentLoaded", function () {
    document.querySelectorAll("[data-seletor-necessidade]").forEach(montar);
    C.escolherNecessidade(C.necessidadeAtual);
  });
})();
