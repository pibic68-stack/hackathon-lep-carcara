/* Ficha de exemplo "O caminho da água" (Ciências, 5º ano) e suas versões adaptadas.
   Prisma.ficha(versao) devolve o HTML. versao = "original" ou o id de uma necessidade. */
(function () {
  var C = window.Prisma;

  /* estilo das 4 setas do ciclo em cada versão */
  var SETAS = ["evap", "cond", "prec", "esc"];
  var NOMES = { evap: "Evaporação", cond: "Condensação", prec: "Precipitação", esc: "Escoamento" };
  var SIMBOLOS = { evap: "▲", cond: "●", prec: "▼", esc: "◆" };
  var PADROES = { evap: "", cond: "10 6", prec: "2 6", esc: "14 5 3 5" };
  var PADRAO_NOME = { evap: "contínua", cond: "tracejada", prec: "pontilhada", esc: "traço e ponto" };

  var ESTILOS = {
    original: { cores: { evap: "#E53935", cond: "#43A047", prec: "#1E88E5", esc: "#FDD835" }, larg: 3, padrao: false, rotulos: false, simbolos: false, numeros: false, enfeites: true, fonte: 13 },
    protanopia: { cores: { evap: "#0072B2", cond: "#E69F00", prec: "#56B4E9", esc: "#1E2235" }, larg: 3.5, padrao: true, rotulos: true, simbolos: true, enfeites: true, fonte: 13 },
    deuteranopia: { cores: { evap: "#0072B2", cond: "#E69F00", prec: "#56B4E9", esc: "#1E2235" }, larg: 3.5, padrao: true, rotulos: true, simbolos: true, enfeites: true, fonte: 13 },
    tritanopia: { cores: { evap: "#D55E00", cond: "#1E2235", prec: "#8A8FA8", esc: "#CC79A7" }, larg: 3.5, padrao: true, rotulos: true, simbolos: true, enfeites: true, fonte: 13 },
    acromatopsia: { cores: { evap: "#1E2235", cond: "#1E2235", prec: "#5B6078", esc: "#1E2235" }, larg: 3.5, padrao: true, rotulos: true, simbolos: true, enfeites: false, cinza: true, fonte: 13 },
    "baixa-visao": { cores: { evap: "#0B3D91", cond: "#1E2235", prec: "#0B3D91", esc: "#1E2235" }, larg: 6, padrao: true, rotulos: true, simbolos: true, enfeites: false, fonte: 19, forte: true },
    tea: { cores: { evap: "#1F6FB2", cond: "#1F6FB2", prec: "#1F6FB2", esc: "#1F6FB2" }, larg: 3.5, padrao: false, rotulos: true, simbolos: false, numeros: true, enfeites: false, fonte: 13 }
  };

  /* geometria do ciclo (viewBox 400 x 250) */
  var GEO = {
    evap: { x1: 92, y1: 196, x2: 92, y2: 92, rx: 102, ry: 150, ancora: "start" },
    cond: { x1: 108, y1: 72, x2: 238, y2: 60, rx: 168, ry: 54, ancora: "middle" },
    prec: { x1: 314, y1: 92, x2: 314, y2: 166, rx: 304, ry: 146, ancora: "end" },
    esc: { x1: 290, y1: 222, x2: 196, y2: 222, rx: 244, ry: 242, ancora: "middle" }
  };

  function seta(id, e) {
    var g = GEO[id], cor = e.cores[id], w = e.larg;
    var ang = Math.atan2(g.y2 - g.y1, g.x2 - g.x1), cab = 8 + w * 1.6;
    // a linha para antes da ponta
    var lx = g.x2 - Math.cos(ang) * cab * 0.8, ly = g.y2 - Math.sin(ang) * cab * 0.8;
    var p1x = g.x2 - Math.cos(ang - 0.5) * cab, p1y = g.y2 - Math.sin(ang - 0.5) * cab;
    var p2x = g.x2 - Math.cos(ang + 0.5) * cab, p2y = g.y2 - Math.sin(ang + 0.5) * cab;
    var traco = e.padrao && PADROES[id] ? ' stroke-dasharray="' + PADROES[id].split(" ").map(function (n) { return n * (w / 3.5); }).join(" ") + '"' : "";
    var s = '<g class="seta seta-' + id + '">' +
      '<line x1="' + g.x1 + '" y1="' + g.y1 + '" x2="' + lx.toFixed(1) + '" y2="' + ly.toFixed(1) + '" stroke="' + cor + '" stroke-width="' + w + '"' + traco + "/>" +
      '<polygon points="' + g.x2 + "," + g.y2 + " " + p1x.toFixed(1) + "," + p1y.toFixed(1) + " " + p2x.toFixed(1) + "," + p2y.toFixed(1) + '" fill="' + cor + '"/>';
    if (e.rotulos || e.numeros) {
      var rot = (e.simbolos ? SIMBOLOS[id] + " " : "") + (e.numeros ? (SETAS.indexOf(id) + 2) + ". " : "") + NOMES[id];
      s += '<text x="' + g.rx + '" y="' + g.ry + '" text-anchor="' + g.ancora + '" font-size="' + e.fonte + '" font-weight="700" fill="#1E2235" stroke="#FFFFFF" stroke-width="' + (e.forte ? 5 : 4) + '" paint-order="stroke">' + rot + "</text>";
    }
    return s + "</g>";
  }

  function figura(versao) {
    var e = ESTILOS[versao] || ESTILOS.original;
    var cinza = e.cinza;
    var ceu = e.forte ? "#FFFFFF" : (cinza ? "#F4F1EA" : "#EAF6FF");
    var mar = cinza ? "#8A8FA8" : (e.forte ? "#5B8FD6" : "#7CC6FB");
    var morro = cinza ? "#C9C4B8" : "#B5D99C";
    var s = '<svg viewBox="0 0 400 250" role="img" aria-label="Ciclo da água: a água do mar evapora, forma nuvens, cai como chuva na montanha e escorre de volta para o mar.">';
    s += '<rect width="400" height="250" fill="' + ceu + '"/>';
    if (e.enfeites) {
      s += '<circle cx="40" cy="38" r="20" fill="' + (cinza ? "#D9D4C7" : "#FFC93C") + '"/>';
      for (var i = 0; i < 8; i++) {
        var a = i * Math.PI / 4;
        s += '<line x1="' + (40 + Math.cos(a) * 25).toFixed(1) + '" y1="' + (38 + Math.sin(a) * 25).toFixed(1) + '" x2="' + (40 + Math.cos(a) * 32).toFixed(1) + '" y2="' + (38 + Math.sin(a) * 32).toFixed(1) + '" stroke="' + (cinza ? "#D9D4C7" : "#FFC93C") + '" stroke-width="3"/>';
      }
      s += '<path d="M150 30 q8-10 16 0 q8-10 16 0" stroke="#5B6078" stroke-width="2" fill="none"/><path d="M190 20 q6-8 12 0 q6-8 12 0" stroke="#5B6078" stroke-width="2" fill="none"/>';
    }
    // montanha e rio
    s += '<polygon points="236,250 330,120 400,200 400,250" fill="' + morro + '" stroke="#1E2235" stroke-width="2"/>';
    // mar
    s += '<rect x="0" y="200" width="200" height="50" fill="' + mar + '" stroke="#1E2235" stroke-width="2"/>';
    if (e.enfeites) s += '<path d="M10 214 q10-8 20 0 t20 0 t20 0 M90 230 q10-8 20 0 t20 0 t20 0" stroke="#FFFFFF" stroke-width="2.5" fill="none"/>';
    // nuvem
    s += '<g fill="#FFFFFF" stroke="#1E2235" stroke-width="2"><ellipse cx="272" cy="64" rx="34" ry="22"/><ellipse cx="304" cy="56" rx="30" ry="26"/><ellipse cx="336" cy="68" rx="28" ry="20"/></g>' +
      '<rect x="250" y="66" width="104" height="18" fill="#FFFFFF"/><line x1="246" y1="86" x2="360" y2="86" stroke="#1E2235" stroke-width="2"/>';
    // gotas de chuva (enfeite)
    if (e.enfeites) s += '<g stroke="#5B6078" stroke-width="2"><line x1="290" y1="100" x2="286" y2="110"/><line x1="340" y1="100" x2="336" y2="110"/><line x1="300" y1="120" x2="296" y2="130"/></g>';
    SETAS.forEach(function (id) { s += seta(id, e); });
    return s + "</svg>";
  }

  function legenda(versao) {
    var e = ESTILOS[versao] || ESTILOS.original;
    if (versao === "original") {
      return '<div class="ficha-legenda" data-alvo="legenda"><strong>Legenda:</strong> ' + SETAS.map(function (id) {
        return '<span class="leg-item"><i style="background:' + e.cores[id] + '"></i>' + NOMES[id] + "</span>";
      }).join("") + "</div>";
    }
    if (versao === "tea") return "";
    return '<ul class="ficha-legenda ficha-legenda--lista" data-alvo="legenda" aria-label="Legenda">' + SETAS.map(function (id) {
      var dash = e.padrao && PADROES[id] ? ' stroke-dasharray="' + PADROES[id] + '"' : "";
      return '<li><svg viewBox="0 0 40 10" width="40" height="10" aria-hidden="true"><line x1="0" y1="5" x2="40" y2="5" stroke="' + e.cores[id] + '" stroke-width="' + Math.min(e.larg, 4) + '"' + dash + '/></svg>' +
        '<span aria-hidden="true">' + SIMBOLOS[id] + "</span> " + NOMES[id] + ' <span class="suave">(' + PADRAO_NOME[id] + ")</span></li>";
    }).join("") + "</ul>";
  }

  var TEXTO_ORIGINAL = "A água é uma grande viajante! Ela vive dando a volta ao mundo. Sobe para o céu, passeia nas nuvens e depois despenca de volta para a terra. Esse vaivém sem fim é o <strong>ciclo da água</strong>, e acontece o tempo todo, mesmo quando a gente nem percebe.";

  function cabecalho(extra) {
    return '<header class="ficha-cab"><span>Ciências · 5º ano</span><span>' + (extra || "Ficha 7") + "</span></header>" +
      '<h4 class="ficha-titulo">O caminho da água</h4>';
  }

  function opcoes(lista, tipo) {
    return '<ul class="ficha-opcoes" role="list">' + lista.map(function (o) {
      return '<li><span class="marcar ' + (tipo || "") + '" aria-hidden="true"></span>' + o + "</li>";
    }).join("") + "</ul>";
  }

  function fichaOriginal() {
    var e = ESTILOS.original;
    return '<article class="ficha ficha--original" aria-label="Ficha original">' + cabecalho() +
      '<p class="ficha-texto" data-alvo="texto">' + TEXTO_ORIGINAL + "</p>" +
      '<figure class="ficha-fig" data-alvo="figura">' + figura("original") + "</figure>" + legenda("original") +
      '<ol class="ficha-perguntas"><li data-alvo="q1">Qual é a cor da seta que mostra a água subindo?' +
      '<span class="bolinhas">' + SETAS.map(function (id) { return '<span class="bol" style="background:' + e.cores[id] + '"></span>'; }).join("") + "</span></li>" +
      "<li>Explique com suas palavras o que acontece na parte verde da figura.</li></ol></article>";
  }

  function fichaCor(versao) {
    return '<article class="ficha ficha--cor ficha--' + versao + '" aria-label="Ficha adaptada">' + cabecalho("Ficha 7 · adaptada") +
      '<p class="ficha-texto">' + TEXTO_ORIGINAL + "</p>" +
      '<figure class="ficha-fig">' + figura(versao) + "</figure>" + legenda(versao) +
      '<ol class="ficha-perguntas"><li>Qual seta mostra a água subindo? Marque o nome.' +
      opcoes(SETAS.map(function (id) { return '<span aria-hidden="true">' + SIMBOLOS[id] + "</span> " + NOMES[id]; })) + "</li>" +
      "<li>Explique com suas palavras o que acontece na seta <span aria-hidden=\"true\">●</span> Condensação.</li></ol></article>";
  }

  function fichaBaixaVisao() {
    return '<article class="ficha ficha--baixa-visao" aria-label="Ficha adaptada para baixa visão">' + cabecalho("Página 1 de 2") +
      '<div class="bv-pagina" data-pagina="1">' +
      '<p class="ficha-texto">A água é uma grande viajante. Ela sobe para o céu, forma nuvens e cai de volta. Isso é o <strong>ciclo da água</strong>.</p>' +
      '<figure class="ficha-fig">' + figura("baixa-visao") + "</figure>" +
      '<p class="bv-pergunta"><strong>Pergunta 1.</strong> Qual seta mostra a água subindo?</p>' +
      opcoes(["▲ Evaporação", "● Condensação", "▼ Precipitação", "◆ Escoamento"].map(function (t) { return t; })) +
      "</div>" +
      '<div class="bv-pagina" data-pagina="2" hidden>' +
      '<p class="bv-pergunta"><strong>Pergunta 2.</strong> Explique com suas palavras o que acontece na seta ● Condensação.</p>' +
      '<div class="bv-linhas" aria-hidden="true"><span></span><span></span><span></span></div></div>' +
      '<div class="bv-paginacao"><button type="button" class="botao botao--secundario botao--pequeno" data-bv="1" aria-pressed="true">Página 1</button>' +
      '<button type="button" class="botao botao--secundario botao--pequeno" data-bv="2" aria-pressed="false">Página 2</button></div>' +
      "</article>";
  }

  function fichaTea() {
    return '<article class="ficha ficha--tea" aria-label="Ficha adaptada com instruções em etapas">' + cabecalho("Tempo: 15 minutos") +
      '<ol class="tea-rotina" aria-label="Rotina da atividade">' +
      '<li class="agora"><span data-icone="book-open"></span><span>1. Ler</span><small>agora</small></li>' +
      '<li><span data-icone="eye"></span><span>2. Olhar a figura</span><small>depois</small></li>' +
      '<li><span data-icone="edit"></span><span>3. Responder</span><small>no fim</small></li></ol>' +
      '<ol class="tea-passos">' +
      "<li>O sol esquenta a água do mar.</li>" +
      "<li>A água sobe para o céu. Isso se chama <strong>evaporação</strong>.</li>" +
      "<li>No céu, a água forma as nuvens. Isso se chama <strong>condensação</strong>.</li>" +
      "<li>A água cai como chuva. Isso se chama <strong>precipitação</strong>.</li>" +
      "<li>A água da chuva escorre de volta para o mar. Isso se chama <strong>escoamento</strong>.</li></ol>" +
      '<figure class="ficha-fig">' + figura("tea") + "</figure>" +
      '<div class="tea-pergunta"><p><strong>Pergunta 1 de 2.</strong> Qual seta mostra a água subindo? <em>Marque 1 resposta.</em></p>' +
      opcoes(["2. Evaporação", "3. Condensação", "4. Precipitação", "5. Escoamento"], "quadrado") +
      '<p class="tea-fim"><span data-icone="human-handsup"></span> Quando terminar, levante a mão. Depois vem a pergunta 2.</p></div>' +
      "</article>";
  }

  C.ficha = function (versao) {
    if (versao === "original") return fichaOriginal();
    if (versao === "baixa-visao") return fichaBaixaVisao();
    if (versao === "tea") return fichaTea();
    return fichaCor(versao);
  };

  /* liga a paginação da ficha de baixa visão */
  C.ligarFicha = function (raiz) {
    raiz.querySelectorAll(".ficha--baixa-visao").forEach(function (f) {
      f.addEventListener("click", function (ev) {
        var b = ev.target.closest("[data-bv]");
        if (!b) return;
        f.querySelectorAll("[data-pagina]").forEach(function (p) { p.hidden = p.dataset.pagina !== b.dataset.bv; });
        f.querySelectorAll("[data-bv]").forEach(function (x) { x.setAttribute("aria-pressed", x === b); });
        f.querySelector(".ficha-cab span:last-child").textContent = "Página " + b.dataset.bv + " de 2";
      });
    });
    if (window.aplicarIcones) window.aplicarIcones(raiz);
  };
})();
