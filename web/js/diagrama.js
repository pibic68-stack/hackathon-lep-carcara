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
    afastarRotulos();
    pacote = svg.querySelector(".pacote");
    rastro = svg.querySelectorAll(".rastro rect");
    marcarAtivo();
    posicionarPacote(ang(ativo));
  }

  /* Rótulos de fora do anel não podem se encostar (nem nos botões das etapas), em nenhum tamanho
     de letra ou fonte. Mede as caixas de verdade e empurra cada rótulo pelo menor caminho (para o lado
     ou para cima/baixo). Se mesmo assim não couber (letra muito grande, tela estreita), os rótulos saem
     do desenho e aparecem como lista no caderno, ao lado: nenhuma informação se perde. */
  function afastarRotulos() {
    var caixa = raiz.querySelector(".externos");
    if (!caixa) return;
    raiz.classList.remove("radial--lista");
    if (!caixa.offsetWidth) return;
    var rotulos = Array.prototype.slice.call(caixa.querySelectorAll(".no-ext"));
    rotulos.forEach(function (r) { r.style.marginTop = "0px"; r.style.marginLeft = "0px"; });
    var base = caixa.getBoundingClientRect(), FOLGA = 6;
    var fixos = Array.prototype.map.call(raiz.querySelectorAll(".no, .centro-caixa"), function (n) { return n.getBoundingClientRect(); });
    function penetra(a, b) {
      var dx = Math.min(a.right, b.right) - Math.max(a.left, b.left) + FOLGA;
      var dy = Math.min(a.bottom, b.bottom) - Math.max(a.top, b.top) + FOLGA;
      return dx > 0 && dy > 0 ? { dx: dx, dy: dy } : null;
    }
    function mover(r, x, y) {
      var a = r.getBoundingClientRect();
      // não deixa sair do quadro
      x = Math.max(base.left + 2 - a.left, Math.min(x, base.right - 2 - a.right));
      y = Math.max(base.top + 2 - a.top, Math.min(y, base.bottom - 2 - a.bottom));
      r.style.marginLeft = (parseFloat(r.style.marginLeft) + x) + "px";
      r.style.marginTop = (parseFloat(r.style.marginTop) + y) + "px";
      return Math.abs(x) + Math.abs(y) >= 0.5;
    }
    function empurrar(r, a, b, p, sempre) {
      var cx = (a.left + a.right) / 2 - (b.left + b.right) / 2, cy = (a.top + a.bottom) / 2 - (b.top + b.bottom) / 2;
      if (p.dy <= p.dx) return mover(r, 0, (cy >= 0 ? 1 : -1) * p.dy * (sempre ? 1 : 0.5));
      return mover(r, (cx >= 0 ? 1 : -1) * p.dx * (sempre ? 1 : 0.5), 0);
    }
    var sobra = true;
    for (var volta = 0; volta < 80 && sobra; volta++) {
      sobra = false;
      rotulos.forEach(function (r, i) {
        fixos.forEach(function (b) {
          var a = r.getBoundingClientRect(), p = penetra(a, b);
          if (p) { sobra = true; empurrar(r, a, b, p, true); }
        });
        rotulos.forEach(function (o, j) {
          if (j <= i) return;
          var a = r.getBoundingClientRect(), b = o.getBoundingClientRect(), p = penetra(a, b);
          if (!p) return;
          sobra = true;
          // os dois se afastam pela metade, cada um para o seu lado
          empurrar(r, a, b, p, false);
          empurrar(o, b, r.getBoundingClientRect(), penetra(b, r.getBoundingClientRect()) || p, false);
        });
      });
    }
    // conferência final: sobrou algum encostando? então vira lista no caderno
    var caixas = rotulos.map(function (r) { return r.getBoundingClientRect(); });
    var ruim = caixas.some(function (a, i) {
      return caixas.some(function (b, j) { return j > i && penetra(a, b) && penetra(a, b).dx > FOLGA && penetra(a, b).dy > FOLGA; }) ||
        fixos.some(function (b) { var p = penetra(a, b); return p && p.dx > FOLGA && p.dy > FOLGA; });
    });
    if (ruim) raiz.classList.add("radial--lista");
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

    if ("ResizeObserver" in window) {
      var espera;
      new ResizeObserver(function () { clearTimeout(espera); espera = setTimeout(afastarRotulos, 60); }).observe(raiz);
    }
    if (document.fonts && document.fonts.ready) document.fonts.ready.then(afastarRotulos);
    new MutationObserver(function () { setTimeout(afastarRotulos, 30); })
      .observe(document.documentElement, { attributes: true, attributeFilter: ["data-fonte", "style", "data-contraste"] });

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

  /* O caderno guarda as 5 etapas empilhadas na mesma célula da grade e mostra só a ativa.
     Assim a caixa sempre tem a altura da etapa mais longa e os botões nunca mudam de lugar,
     em qualquer modo (daltonismo, dislexia, letra maior). */
  var necessidadeDesenhada = null;
  function atualizarCaderno() {
    var n = P.necessidadePorId(P.necessidadeAtual), e = P.ETAPAS[ativo];
    document.getElementById("caderno-aluno").textContent = n.aluno;
    document.getElementById("caderno-passo").textContent = "Etapa " + e.num + " de 5";
    var corpo = document.getElementById("caderno-corpo");
    if (necessidadeDesenhada !== P.necessidadeAtual || corpo.children.length !== P.ETAPAS.length) {
      necessidadeDesenhada = P.necessidadeAtual;
      corpo.innerHTML = P.ETAPAS.map(function (x, i) {
        return '<div class="caderno-etapa" data-etapa="' + i + '"><p class="rotulo">' + x.num + ".0 · " + x.nome + "</p><h3>" + x.titulo +
          "</h3><p>" + x.texto(n) + "</p>" + x.detalhe(n) +
          '<ul class="caderno-ligados" aria-label="Ligado a esta etapa">' + externosDe(i).map(function (t) { return "<li>" + t + "</li>"; }).join("") + "</ul></div>";
      }).join("");
      if (window.aplicarIcones) window.aplicarIcones(corpo);
    }
    Array.prototype.forEach.call(corpo.children, function (d, i) {
      var sim = i === ativo;
      d.classList.toggle("ativa", sim);
      if (sim) d.removeAttribute("aria-hidden"); else d.setAttribute("aria-hidden", "true");
    });
    var anuncio = document.getElementById("caderno-anuncio");
    if (anuncio) anuncio.textContent = "Etapa " + e.num + " de 5: " + e.nome + ". " + e.titulo;
  }

  document.addEventListener("DOMContentLoaded", montar);
})();
