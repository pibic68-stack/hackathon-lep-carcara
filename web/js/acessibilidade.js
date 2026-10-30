/* Barra de acessibilidade do site.
   Carregar no <head> (sem defer): aplica as preferências salvas antes de desenhar a página.
   Coloque <div id="barra-acessibilidade"></div> logo no começo do <body>. */
(function () {
  var raiz = document.documentElement;
  var CHAVE = "prisma-acessibilidade";
  var ESCALAS = [1, 1.15, 1.3, 1.5];

  function ler() {
    try { return JSON.parse(localStorage.getItem(CHAVE)) || {}; } catch (e) { return {}; }
  }
  function salvar(p) {
    try { localStorage.setItem(CHAVE, JSON.stringify(p)); } catch (e) { /* navegador sem armazenamento: segue sem salvar */ }
  }

  var pref = ler();
  var sistemaReduz = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  function aplicar() {
    raiz.style.setProperty("--escala", ESCALAS[pref.escala || 0]);
    pref.contraste ? raiz.setAttribute("data-contraste", "alto") : raiz.removeAttribute("data-contraste");
    pref.dislexia ? raiz.setAttribute("data-fonte", "dislexia") : raiz.removeAttribute("data-fonte");
    pref.daltonismo ? raiz.setAttribute("data-daltonismo", pref.daltonismo) : raiz.removeAttribute("data-daltonismo");
    var reduzir = pref.movimento === undefined ? sistemaReduz : pref.movimento;
    reduzir ? raiz.setAttribute("data-movimento", "reduzido") : raiz.removeAttribute("data-movimento");
    document.dispatchEvent(new CustomEvent("prisma:movimento", { detail: { reduzido: reduzir } }));
  }
  aplicar();

  /* outros scripts perguntam aqui se devem animar */
  window.prismaMovimentoReduzido = function () {
    return raiz.getAttribute("data-movimento") === "reduzido";
  };

  function montar() {
    var alvo = document.getElementById("barra-acessibilidade");
    if (!alvo) return;
    alvo.outerHTML =
      '<section class="barra-acess" aria-label="Acessibilidade">' +
      '<div class="conteiner">' +
      '<p class="titulo-barra"><span data-icone="human"></span> Acessibilidade</p>' +
      '<div class="grupo" role="group" aria-label="Tamanho da letra">' +
      '<button type="button" data-acao="menor" aria-label="Diminuir letra">A−</button>' +
      '<button type="button" data-acao="maior" aria-label="Aumentar letra">A+</button>' +
      "</div>" +
      '<div class="grupo">' +
      '<button type="button" data-acao="contraste" aria-pressed="false" aria-label="Alto contraste"><span data-icone="invert"></span> <span class="longo">Alto contraste</span><span class="curto">Contraste</span></button>' +
      '<button type="button" data-acao="dislexia" aria-pressed="false" aria-label="Fonte para dislexia"><span data-icone="text-add"></span> <span class="longo">Fonte para dislexia</span><span class="curto">Dislexia</span></button>' +
      '<label class="cores"><span data-icone="colors-swatch"></span> <span class="longo">Daltonismo</span><span class="curto">Cores</span>' +
      '<select data-acao="daltonismo" aria-label="Ajustar cores para daltonismo">' +
      '<option value="">Cores padrão</option>' +
      '<option value="protanopia">Protanopia</option>' +
      '<option value="deuteranopia">Deuteranopia</option>' +
      '<option value="tritanopia">Tritanopia</option>' +
      '<option value="acromatopsia">Acromatopsia</option>' +
      "</select></label>" +
      '<button type="button" data-acao="movimento" aria-pressed="false" aria-label="Pausar animações"><span data-icone="pause"></span> <span class="longo">Pausar animações</span><span class="curto">Pausar</span></button>' +
      "</div></div></section>";
    var barra = document.querySelector(".barra-acess");
    if (window.aplicarIcones) window.aplicarIcones(barra);

    function sincronizar() {
      barra.querySelector('[data-acao="contraste"]').setAttribute("aria-pressed", !!pref.contraste);
      barra.querySelector('[data-acao="dislexia"]').setAttribute("aria-pressed", !!pref.dislexia);
      barra.querySelector('[data-acao="movimento"]').setAttribute("aria-pressed", window.prismaMovimentoReduzido());
      barra.querySelector('[data-acao="daltonismo"]').value = pref.daltonismo || "";
      barra.querySelector('[data-acao="menor"]').disabled = !(pref.escala > 0);
      barra.querySelector('[data-acao="maior"]').disabled = (pref.escala || 0) >= ESCALAS.length - 1;
    }

    barra.addEventListener("click", function (e) {
      var b = e.target.closest("button[data-acao]");
      if (!b) return;
      var acao = b.dataset.acao;
      if (acao === "maior") pref.escala = Math.min((pref.escala || 0) + 1, ESCALAS.length - 1);
      if (acao === "menor") pref.escala = Math.max((pref.escala || 0) - 1, 0);
      if (acao === "contraste") pref.contraste = !pref.contraste;
      if (acao === "dislexia") pref.dislexia = !pref.dislexia;
      if (acao === "movimento") pref.movimento = !window.prismaMovimentoReduzido();
      salvar(pref); aplicar(); sincronizar();
      anunciar(b);
    });
    barra.querySelector('[data-acao="daltonismo"]').addEventListener("change", function (e) {
      pref.daltonismo = e.target.value || undefined;
      salvar(pref); aplicar(); sincronizar();
      var opcao = e.target.selectedOptions[0];
      anunciarTexto("Cores: " + opcao.textContent);
      // na página inicial, a demonstração mostra a ficha para o mesmo tipo
      if (pref.daltonismo && window.Prisma && Prisma.escolherNecessidade) Prisma.escolherNecessidade(pref.daltonismo);
    });
    sincronizar();
  }

  /* avisa o leitor de tela do que mudou */
  function anunciar(botao) {
    var estado = botao.hasAttribute("aria-pressed") ? (botao.getAttribute("aria-pressed") === "true" ? " ligado" : " desligado") : "";
    anunciarTexto((botao.getAttribute("aria-label") || botao.textContent.trim()) + estado);
  }
  function anunciarTexto(texto) {
    var vivo = document.getElementById("anuncio-acess");
    if (!vivo) {
      vivo = document.createElement("p");
      vivo.id = "anuncio-acess"; vivo.className = "so-leitor"; vivo.setAttribute("aria-live", "polite");
      document.body.appendChild(vivo);
    }
    vivo.textContent = texto;
  }

  /* menu do celular */
  function menuCelular() {
    var botao = document.querySelector(".menu-botao");
    var menu = document.getElementById("menu");
    if (!botao || !menu) return;
    botao.addEventListener("click", function () {
      var aberto = menu.classList.toggle("aberto");
      botao.setAttribute("aria-expanded", aberto);
    });
    menu.addEventListener("click", function (e) {
      if (e.target.closest("a")) { menu.classList.remove("aberto"); botao.setAttribute("aria-expanded", "false"); }
    });
  }

  document.addEventListener("DOMContentLoaded", function () { montar(); menuCelular(); });
})();
