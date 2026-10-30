/* Seção "Antes e depois": ficha original → regras do Manual → ficha adaptada. */
(function () {
  var P = window.Prisma;

  function el(id) { return document.getElementById(id); }

  function atualizar() {
    var n = P.necessidadePorId(P.necessidadeAtual);

    // ficha original (sempre a mesma) só é desenhada uma vez
    if (!el("ficha-original").firstChild) {
      el("ficha-original").innerHTML = P.ficha("original");
    }
    el("ficha-adaptada").innerHTML = P.ficha(n.id);
    P.ligarFicha(el("ficha-adaptada"));

    el("regras").innerHTML =
      '<p class="regras-aluno"><img class="pixel" src="assets/img/aluno.png" alt="" width="36" height="36"><span><strong>' + n.aluno + "</strong><br>" + n.grupo + " · " + n.nome + "</span></p>" +
      '<p class="regras-resumo">' + n.resumo + "</p>" +
      '<ul class="lista-regras">' + n.regras.map(function (r) {
        return '<li><span class="etiqueta">' + r.id + "</span><span>" + r.texto + '<small class="fonte">' + r.fonte + "</small></span></li>";
      }).join("") + "</ul>";

    el("guia-familia").textContent = P.dicaFamilia(n);

    // simulação só faz sentido para necessidades de visão
    var podeSimular = !!n.filtro;
    el("alt-simular").hidden = !podeSimular;
    if (!podeSimular) el("simular").checked = false;
    aplicarSimulacao();
    aplicarBarreiras();
    reiniciarAprovacao();
  }

  function aplicarSimulacao() {
    var n = P.necessidadePorId(P.necessidadeAtual);
    var filtro = el("simular").checked && n.filtro ? n.filtro : "";
    document.querySelectorAll("#fluxo .ficha-moldura").forEach(function (m) {
      m.style.filter = filtro;
      m.classList.toggle("simulando", !!filtro);
      m.setAttribute("data-simulando", filtro ? "Como " + n.aluno.split(" · ")[0] + " enxerga" : "");
    });
  }

  function aplicarBarreiras() {
    var ligado = el("barreiras").checked;
    var ficha = el("ficha-original").querySelector(".ficha");
    var lista = el("lista-barreiras");
    ficha.querySelectorAll("[data-alvo]").forEach(function (a) { a.removeAttribute("data-barreira"); });
    ficha.classList.toggle("com-barreiras", ligado);
    lista.hidden = !ligado;
    if (!ligado) return;
    var barreiras = P.barreirasDe(P.necessidadeAtual);
    barreiras.forEach(function (b, i) {
      var alvo = ficha.querySelector('[data-alvo="' + b.alvo + '"]');
      if (alvo) alvo.setAttribute("data-barreira", i + 1);
    });
    lista.innerHTML = barreiras.map(function (b) { return "<li>" + b.texto + "</li>"; }).join("");
  }

  function reiniciarAprovacao() {
    var b = el("aprovar");
    b.disabled = false;
    b.innerHTML = window.icone("check") + " Aprovar";
  }

  document.addEventListener("DOMContentLoaded", function () {
    if (!el("fluxo")) return;
    el("simular").addEventListener("change", aplicarSimulacao);
    el("barreiras").addEventListener("change", aplicarBarreiras);
    el("aprovar").addEventListener("click", function () {
      this.innerHTML = window.icone("check-double") + " Aprovado!";
      this.disabled = true;
    });
    document.addEventListener("prisma:necessidade", atualizar);
    atualizar();
  });
})();
