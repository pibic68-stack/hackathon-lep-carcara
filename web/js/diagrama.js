/* Diagrama radial "Como funciona" (inspirado no cofounder.co).
   Centro: PRISMA + mascote. Anel: as 5 etapas. Caixinhas de fora: detalhes de cada etapa.
   Um "pacotinho" de pixel percorre o anel na ordem 1 → 5 → 1, mostrando o ciclo. */
(function () {
  var P = window.Prisma;
  var W = 800, H = 620, CX = 400, CY = 310, R = 175, RO = 286, ABERTURA = 26;
  var PERMANENCIA = 3400, VIAGEM = 1000;

  var raiz, svg, pacote, rastro = [], ativo = 0, pausado = false, visivel = true;
  var fase = "parado", inicioFase = 0, quadro = null;

  function ang(i) { return (-90 + i * 72) * Math.PI / 180; }
  function ponto(a, r) { return { x: CX + Math.cos(a) * r, y: CY + Math.sin(a) * r }; }
  function pct(p) { return "left:" + (p.x / W * 100).toFixed(2) + "%;top:" + (p.y / H * 100).toFixed(2) + "%"; }
  function grade(v) { return Math.round(v / 6) * 6; } /* anda "em pixels" */

  function externosDe(i) {
    var e = P.ETAPAS[i];
    if (e.externos) return e.externos;
    return P.necessidadePorId(P.necessidadeAtual).adaptacoes.concat(["Manual de Acessibilidade"]);
  }

  function desenhar() {
    var linhas = "", externos = "";
    // anel
    linhas += '<circle class="l-anel" cx="' + CX + '" cy="' + CY + '" r="' + R + '"/>';
    P.ETAPAS.forEach(function (e, i) {
      var a = ang(i), pi = ponto(a, R), lista = externosDe(i);
      lista.forEach(function (txt, j) {
        var aj = a + (j - (lista.length - 1) / 2) * ABERTURA * Math.PI / 180;
        var po = ponto(aj, RO), meio = ponto(aj, RO - 34);
        linhas += '<polyline class="l-ext" data-i="' + i + '" points="' + pi.x.toFixed(1) + "," + pi.y.toFixed(1) + " " + meio.x.toFixed(1) + "," + meio.y.toFixed(1) + " " + po.x.toFixed(1) + "," + po.y.toFixed(1) + '"/>';
        var manual = txt === "Manual de Acessibilidade";
        externos += '<div class="no-ext' + (manual ? " no-ext--manual" : "") + '" data-i="' + i + '" style="' + pct(po) + '">' +
          (manual ? window.icone("script-text") : "") + txt + "</div>";
      });
      linhas += '<line class="l-raio" data-i="' + i + '" x1="' + CX + '" y1="' + CY + '" x2="' + pi.x.toFixed(1) + '" y2="' + pi.y.toFixed(1) + '"/>';
    });
    linhas += '<g class="rastro"><rect width="8" height="8" opacity=".25"/><rect width="8" height="8" opacity=".5"/></g><rect class="pacote" width="12" height="12"/>';
    svg.innerHTML = linhas;
    raiz.querySelector(".externos").innerHTML = externos;
    pacote = svg.querySelector(".pacote");
    rastro = svg.querySelectorAll(".rastro rect");
    marcarAtivo();
    posicionarPacote(ang(ativo));
  }

  function montar() {
    raiz = document.getElementById("radial");
    if (!raiz) return;
    var nos = P.ETAPAS.map(function (e, i) {
      return '<li style="' + pct(ponto(ang(i), R)) + '"><button type="button" class="no" data-i="' + i + '" aria-pressed="false">' +
        '<span class="no-num">' + e.num + "</span>" + window.icone(e.icone) + '<span class="no-nome">' + e.nome + "</span></button></li>";
    }).join("");
    raiz.innerHTML =
      '<svg class="radial-svg" viewBox="0 0 ' + W + " " + H + '" aria-hidden="true" focusable="false"></svg>' +
      '<div class="externos" aria-hidden="true"></div>' +
      '<div class="radial-centro"><img class="pixel" src="assets/img/carcara.png" alt="" width="78" height="90">' +
      '<div class="centro-caixa"><img class="pixel" src="assets/img/prisma-logo.svg" alt="" width="30" height="18">PRISMA</div></div>' +
      '<ol class="nos" aria-label="Etapas do ciclo">' + nos + "</ol>";
    svg = raiz.querySelector(".radial-svg");
    desenhar();

    raiz.addEventListener("click", function (e) {
      var b = e.target.closest(".no");
      if (!b) return;
      irPara(+b.dataset.i);
      pausar(true);
    });
    document.getElementById("etapa-proxima").addEventListener("click", function () { irPara((ativo + 1) % 5); pausar(true); });
    document.getElementById("etapa-anterior").addEventListener("click", function () { irPara((ativo + 4) % 5); pausar(true); });
    document.getElementById("etapa-pausa").addEventListener("click", function () { pausar(!pausado); });

    document.addEventListener("prisma:necessidade", function () { desenhar(); atualizarCaderno(); });
    document.addEventListener("prisma:movimento", function () { atualizarBotaoPausa(); });

    if ("IntersectionObserver" in window) {
      new IntersectionObserver(function (ents) { visivel = ents[0].isIntersecting; }, { threshold: 0.2 }).observe(raiz);
    }
    atualizarCaderno();
    atualizarBotaoPausa();
    inicioFase = performance.now();
    quadro = requestAnimationFrame(passo);
  }

  function parado() { return pausado || !visivel || (window.prismaMovimentoReduzido && window.prismaMovimentoReduzido()); }

  function pausar(v) {
    pausado = v;
    atualizarBotaoPausa();
    inicioFase = performance.now();
    if (fase === "viajando") { fase = "parado"; posicionarPacote(ang(ativo)); }
  }
  function atualizarBotaoPausa() {
    var b = document.getElementById("etapa-pausa");
    if (!b) return;
    var p = pausado || (window.prismaMovimentoReduzido && window.prismaMovimentoReduzido());
    b.setAttribute("aria-pressed", p);
    b.querySelector(".txt").textContent = p ? "Continuar" : "Pausar";
    b.querySelector("[data-icone]").innerHTML = window.icone(p ? "play" : "pause");
  }

  function irPara(i) {
    ativo = i; fase = "parado"; inicioFase = performance.now();
    marcarAtivo(); posicionarPacote(ang(ativo)); atualizarCaderno();
  }

  function marcarAtivo() {
    raiz.querySelectorAll(".no").forEach(function (b) {
      var s = +b.dataset.i === ativo;
      b.setAttribute("aria-pressed", s);
      b.classList.toggle("ativo", s);
    });
    svg.querySelectorAll("[data-i]").forEach(function (el) { el.classList.toggle("ativa", +el.dataset.i === ativo); });
    raiz.querySelectorAll(".no-ext").forEach(function (el) { el.classList.toggle("ativa", +el.dataset.i === ativo); });
  }

  function posicionarPacote(a, atrasos) {
    var p = ponto(a, R);
    pacote.setAttribute("x", grade(p.x) - 6); pacote.setAttribute("y", grade(p.y) - 6);
    rastro.forEach(function (r, k) {
      var q = atrasos ? ponto(a - (2 - k) * 0.07, R) : p;
      r.setAttribute("x", grade(q.x) - 4); r.setAttribute("y", grade(q.y) - 4);
      r.style.display = atrasos ? "" : "none";
    });
  }

  function passo(t) {
    quadro = requestAnimationFrame(passo);
    if (parado()) { inicioFase = t; return; }
    var dt = t - inicioFase;
    if (fase === "parado" && dt > PERMANENCIA) { fase = "viajando"; inicioFase = t; dt = 0; }
    if (fase === "viajando") {
      var k = Math.min(dt / VIAGEM, 1);
      var e = k < .5 ? 2 * k * k : 1 - Math.pow(-2 * k + 2, 2) / 2;
      posicionarPacote(ang(ativo) + e * 72 * Math.PI / 180, true);
      if (k >= 1) { irPara((ativo + 1) % 5); }
    }
  }

  function atualizarCaderno() {
    var n = P.necessidadePorId(P.necessidadeAtual), e = P.ETAPAS[ativo];
    document.getElementById("caderno-aluno").textContent = n.aluno;
    document.getElementById("caderno-passo").textContent = "Etapa " + e.num + " de 5";
    var corpo = document.getElementById("caderno-corpo");
    corpo.innerHTML = '<p class="rotulo">' + e.num + ".0 · " + e.nome + "</p><h3>" + e.titulo + "</h3><p>" + e.texto(n) + "</p>" + e.detalhe(n);
    if (window.aplicarIcones) window.aplicarIcones(corpo);
  }

  document.addEventListener("DOMContentLoaded", montar);
})();
