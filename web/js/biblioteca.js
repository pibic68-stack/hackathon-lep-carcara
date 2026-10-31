/* Biblioteca da turma (aluno e família). Só aparece o que o professor aprovou (P10.1).
   Cada versão tem o nome do jeito de estudar ("Letras grandes", "Ouvir"), nunca de deficiência (P5.3).
   As versões que combinam com o perfil do aluno vêm primeiro, marcadas "do seu jeito".
   Aluno: avalia cada material com 1 a 5 estrelas e uma sugestão (até 150 palavras). As duas são opcionais
   e dá para pular. Família: pode tirar um material do painel do próprio aluno (a turma continua vendo). */
(function () {
  function el(tag, attrs, filhos) {
    var n = document.createElement(tag);
    Object.keys(attrs || {}).forEach(function (k) {
      if (k === "texto") n.textContent = attrs[k];
      else if (k === "classe") n.className = attrs[k];
      else if (k.indexOf("on") === 0) n.addEventListener(k.slice(2), attrs[k]);
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

  var MAX_PALAVRAS = 150;
  var NOMES = ["1 estrela", "2 estrelas", "3 estrelas", "4 estrelas", "5 estrelas"];
  var contador = 0;
  function palavras(t) { var m = t.trim().match(/\S+/g); return m ? m.length : 0; }

  /* 5 estrelas: acendem até onde está o mouse e ficam acesas no clique. Teclado: setas e Enter/Espaço. */
  function estrelas(inicial, aoMudar) {
    var valor = inicial || 0;
    var grupo = el("div", { classe: "estrelas", role: "radiogroup", "aria-label": "Quantas estrelas você dá para esta aula" });
    var botoes = NOMES.map(function (nome, i) {
      return el("button", { type: "button", classe: "estrela", role: "radio", "aria-label": nome, "data-n": String(i + 1), texto: "★" });
    });
    function pintar(ate) { botoes.forEach(function (b, i) { b.classList.toggle("acesa", i < ate); }); }
    function marcar(n, focar) {
      valor = n;
      botoes.forEach(function (b, i) {
        b.setAttribute("aria-checked", String(i + 1 === n));
        b.tabIndex = (n ? i + 1 === n : i === 0) ? 0 : -1;
      });
      pintar(n);
      if (focar && n) botoes[n - 1].focus();
      aoMudar(n);
    }
    botoes.forEach(function (b, i) {
      b.addEventListener("mouseenter", function () { pintar(i + 1); });
      b.addEventListener("focus", function () { pintar(Math.max(valor, 0) || 0); });
      b.addEventListener("click", function () { marcar(valor === i + 1 ? 0 : i + 1); });   // clicar de novo apaga
      b.addEventListener("keydown", function (e) {
        var k = e.key;
        if (k === "ArrowRight" || k === "ArrowUp") { e.preventDefault(); marcar(Math.min(5, (valor || 0) + 1), true); }
        else if (k === "ArrowLeft" || k === "ArrowDown") { e.preventDefault(); marcar(Math.max(1, (valor || 2) - 1), true); }
        else if (k === "Home") { e.preventDefault(); marcar(1, true); }
        else if (k === "End") { e.preventDefault(); marcar(5, true); }
      });
      grupo.appendChild(b);
    });
    grupo.addEventListener("mouseleave", function () { pintar(valor); });
    var legenda = el("span", { classe: "estrelas-valor", "aria-hidden": "true" });
    grupo.appendChild(legenda);
    var mudar = aoMudar;
    aoMudar = function (n) { legenda.textContent = n ? n + " de 5" : "sem nota"; mudar(n); };
    marcar(valor);
    return { no: grupo, valor: function () { return valor; } };
  }

  function caixaAvaliacao(m, aoTerminar) {
    var id = "sug-" + (++contador);
    var feito = m.avaliacao;
    var status = el("p", { classe: "status-avaliacao", role: "status", "aria-live": "polite" });
    var est = estrelas(feito && feito.estrelas, function () {});
    var area = el("textarea", { id: id, rows: "3", maxlength: "1500", "aria-describedby": id + "-conta " + id + "-dica" });
    area.value = (feito && feito.sugestao) || "";
    var conta = el("p", { id: id + "-conta", classe: "dica conta-palavras" });
    function contar() {
      var n = palavras(area.value);
      conta.textContent = n + " de " + MAX_PALAVRAS + " palavras";
      conta.classList.toggle("passou", n > MAX_PALAVRAS);
    }
    area.addEventListener("input", contar);
    contar();
    var enviar = el("button", { type: "submit", classe: "botao botao--pequeno" }, ["Enviar avaliação"]);
    var pular = el("button", { type: "button", classe: "botao botao--fantasma botao--pequeno", texto: "Pular avaliação" });
    var form = el("form", { classe: "avaliacao", novalidate: "" }, [
      el("div", { classe: "campo campo-sugestao" }, [
        el("label", { for: id, texto: "Sugestão:" }),
        el("p", { id: id + "-dica", classe: "dica", texto: "Conte o que ajudou ou o que pode melhorar. É opcional." }),
        area, conta
      ]),
      el("div", { classe: "acoes-avaliacao" }, [enviar, pular]),
      status
    ]);
    function mandar(dados, msg) {
      enviar.disabled = pular.disabled = true;
      Prisma.api.avaliar(m.id, dados).then(function (r) {
        m.avaliacao = r;
        status.textContent = msg(r);
        status.className = "status-avaliacao ok";
      }).catch(function (e) { status.textContent = e.message; status.className = "status-avaliacao erro"; })
        .then(function () { enviar.disabled = pular.disabled = false; });
    }
    form.addEventListener("submit", function (ev) {
      ev.preventDefault();
      var n = est.valor(), texto = area.value.trim();
      if (palavras(texto) > MAX_PALAVRAS) { status.textContent = "A sugestão pode ter até " + MAX_PALAVRAS + " palavras."; status.className = "status-avaliacao erro"; area.focus(); return; }
      if (!n && !texto) { status.textContent = "Escolha as estrelas, escreva uma sugestão ou pule a avaliação."; status.className = "status-avaliacao erro"; return; }
      mandar({ estrelas: n || null, sugestao: texto }, function (r) {
        return "Avaliação enviada. Obrigado!" + (r.estrelas ? " Você deu " + NOMES[r.estrelas - 1] + "." : "");
      });
    });
    pular.addEventListener("click", function () {
      mandar({ pular: true }, function () { return "Você pulou a avaliação. Se mudar de ideia, é só avaliar e enviar."; });
    });
    if (feito) status.textContent = feito.pulou ? "Você pulou a avaliação desta aula." : "Você já avaliou esta aula. Pode mudar e enviar de novo.";
    return { estrelas: est.no, form: form };
  }

  function cartaoMaterial(m, u, aoMudar) {
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
    var linha = el("div", { classe: "linha-material" }, [el("ul", { classe: "botoes-versoes" }, botoes)]);
    var partes = [
      el("h3", { texto: m.titulo || m.material }),
      el("p", { classe: "dica", texto: "Escolha o jeito que ajuda a estudar. Todas as versões têm o mesmo conteúdo." }),
      linha
    ];
    if (u.perfil === "aluno") {
      var av = caixaAvaliacao(m);
      linha.appendChild(el("div", { classe: "lado-estrelas" }, [el("span", { classe: "rotulo-estrelas", texto: "Avalie a aula:" }), av.estrelas]));
      partes.push(av.form);
    }
    if (u.perfil === "familia") {
      var tirar = el("button", { type: "button", classe: "botao botao--fantasma botao--pequeno", texto: "Tirar do painel de " + u.apelido });
      tirar.addEventListener("click", function () {
        tirar.disabled = true;
        Prisma.api.ocultar(m.id, true).then(aoMudar).catch(function (e) { tirar.disabled = false; alert(e.message); });
      });
      partes.push(el("div", { classe: "acoes-familia" }, [tirar,
        el("p", { classe: "dica", texto: "Some só do painel de " + u.apelido + ". A turma e a escola continuam vendo." })]));
    }
    return el("li", { classe: "cartao", "data-id": m.id }, partes);
  }

  document.addEventListener("prisma:painel", function (ev) {
    var u = ev.detail;
    if (u.perfil !== "aluno" && u.perfil !== "familia") return;
    if (u.perfil === "familia") montarFamilia(u);
    var area = document.getElementById("area-biblioteca");
    var estado = el("div", { role: "status", "aria-live": "polite" });
    var lista = el("ul", { classe: "lista-materiais" });
    var tirados = el("div", { classe: "tirados" });
    area.appendChild(el("h2", { texto: "Materiais da turma" }));
    area.appendChild(estado);
    area.appendChild(lista);
    area.appendChild(tirados);

    function carregar() {
      return Prisma.api.biblioteca().then(function (itens) {
        estado.textContent = ""; lista.textContent = ""; tirados.textContent = "";
        var visiveis = itens.filter(function (m) { return !m.oculto; });
        var ocultos = itens.filter(function (m) { return m.oculto; });
        if (!visiveis.length) {
          estado.appendChild(el("p", { classe: "dica", texto: itens.length
            ? "Nenhum material no painel agora."
            : "Ainda não há materiais. Quando a professora aprovar um, ele aparece aqui." }));
        }
        visiveis.forEach(function (m) { lista.appendChild(cartaoMaterial(m, u, carregar)); });
        if (u.perfil === "familia" && ocultos.length) {
          tirados.appendChild(el("details", {}, [
            el("summary", { texto: "Tirados do painel de " + u.apelido + " (" + ocultos.length + ")" }),
            el("ul", { classe: "lista-tirados" }, ocultos.map(function (m) {
              var volta = el("button", { type: "button", classe: "botao botao--secundario botao--pequeno", texto: "Devolver ao painel" });
              volta.addEventListener("click", function () { volta.disabled = true; Prisma.api.ocultar(m.id, false).then(carregar); });
              return el("li", {}, [el("strong", { texto: m.titulo || m.material }), " ", volta]);
            }))
          ]));
        }
      }).catch(function (e) { estado.appendChild(el("p", { classe: "erro", texto: e.message })); });
    }
    carregar();
  });
})();
