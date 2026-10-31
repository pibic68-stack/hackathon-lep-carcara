/* Área do professor: turmas e alunos (fictícios), envio de material, revisão e aprovação.
   Fluxo do Manual: nada chega ao aluno sem aprovação (P10.1); imagem sem descrição bloqueia (P4.1);
   perfil por necessidades de uma lista fechada, nunca diagnóstico (P10.2).
   Todo texto vindo do servidor entra com textContent (nunca innerHTML). */
(function () {
  var FIGURAS = {
    coracao: ["Coração", "heart"], sol: ["Sol", "sun"], lua: ["Lua", "moon"], raio: ["Raio", "zap"],
    trofeu: ["Troféu", "trophy"], livro: ["Livro", "book-open"], lampada: ["Lâmpada", "lightbulb"],
    carinha: ["Carinha feliz", "mood-happy"], casa: ["Casa", "home"]
  };
  var ESTADOS = { rascunho: ["etiqueta--sol", "Esperando a sua aprovação"], publicado: ["etiqueta--ok", "Publicado para a turma"] };
  var opcoes = { necessidades: {}, preferencias: {} };
  var turmas = [];
  var aviso, listaTurmas, listaMateriais, seletorTurma, estaOcupado = false;

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
  // window.icone() devolve o SVG pronto (texto fixo do próprio site, não vem do servidor)
  function icone(nome) { var s = document.createElement("span"); s.innerHTML = window.icone(nome); return s; }

  function avisar(texto, tipo) {
    aviso.textContent = "";
    if (texto) aviso.appendChild(el("p", { classe: tipo === "erro" ? "erro" : "dica", texto: texto }));
  }

  var contador = 0;
  function caixas(nome, mapa, marcadas) {
    return Object.keys(mapa).map(function (chave) {
      var id = "c" + (++contador);
      var input = el("input", { type: "checkbox", id: id, name: nome, value: chave });
      input.checked = (marcadas || []).indexOf(chave) >= 0;
      return el("div", { classe: "lembrar" }, [input, el("label", { for: id, texto: mapa[chave] })]);
    });
  }
  function marcadas(form, nome) {
    return Array.prototype.map.call(form.querySelectorAll('input[name="' + nome + '"]:checked'), function (i) { return i.value; });
  }
  function rotulos(lista, mapa) {
    return lista.length ? lista.map(function (k) { return mapa[k] || k; }).join(", ") : "nenhuma marcada";
  }

  /* ---------------- turmas e alunos ---------------- */

  function cartaoAluno(a) {
    var figuras = el("ol", { classe: "figuras-cartao", "aria-label": "Senha de figurinhas, em ordem" },
      a.figuras.map(function (f, i) {
        var info = FIGURAS[f] || [f, "heart"];
        return el("li", {}, [icone(info[1]), el("span", { texto: (i + 1) + "ª " + info[0] })]);
      }));
    var editar = el("details", {}, [el("summary", { texto: "Mudar necessidades" })]);
    var form = el("form", { classe: "form-aluno-editar" },
      caixas("necessidade", opcoes.necessidades, a.necessidades).concat(caixas("preferencia", opcoes.preferencias, a.preferencias)));
    form.appendChild(el("button", { type: "submit", classe: "botao botao--secundario botao--pequeno", texto: "Salvar" }));
    form.addEventListener("submit", function (ev) {
      ev.preventDefault();
      Prisma.api.mudarAluno(a.id, { necessidades: marcadas(form, "necessidade"), preferencias: marcadas(form, "preferencia") })
        .then(function () { avisar("Necessidades de " + a.apelido + " salvas."); return carregarTurmas(); })
        .catch(function (e) { avisar(e.message, "erro"); });
    });
    editar.appendChild(form);
    var remover = el("button", { type: "button", classe: "botao botao--fantasma botao--pequeno", texto: "Remover aluno" });
    remover.addEventListener("click", function () {
      if (!confirm("Remover " + a.apelido + "? O cartão e o código da família deixam de funcionar.")) return;
      Prisma.api.apagarAluno(a.id).then(function () { avisar(a.apelido + " foi removido."); return carregarTurmas(); })
        .catch(function (e) { avisar(e.message, "erro"); });
    });
    return el("li", { classe: "cartao cartao-aluno" }, [
      el("h4", { texto: a.apelido }),
      el("p", {}, [el("strong", { texto: "Aprende melhor com: " }), rotulos(a.necessidades.concat(a.preferencias),
        Object.assign({}, opcoes.necessidades, opcoes.preferencias))]),
      el("p", { texto: "Senha de figurinhas do aluno:" }), figuras,
      el("p", {}, [el("strong", { texto: "Código da família: " }), el("span", { classe: "codigo", texto: a.codigo_familia })]),
      editar, remover
    ]);
  }

  function formNovoAluno(t) {
    var id = "apelido-" + t.id;
    var form = el("form", { classe: "form-novo-aluno" }, [
      el("div", { classe: "campo" }, [
        el("label", { for: id, texto: "Apelido fictício do aluno" }),
        el("p", { classe: "dica", texto: "Nunca use o nome real. Por exemplo: Aluno A." }),
        el("input", { type: "text", id: id, maxlength: "30", autocomplete: "off" })
      ]),
      el("fieldset", { classe: "campo" }, [el("legend", { texto: "Como ele aprende melhor" })]
        .concat(caixas("necessidade", opcoes.necessidades)).concat(caixas("preferencia", opcoes.preferencias))),
      el("button", { type: "submit", classe: "botao botao--secundario" }, [icone("plus"), " Adicionar aluno"])
    ]);
    form.addEventListener("submit", function (ev) {
      ev.preventDefault();
      var apelido = form.querySelector("#" + id).value.trim();
      Prisma.api.novoAluno(t.id, { apelido: apelido, necessidades: marcadas(form, "necessidade"), preferencias: marcadas(form, "preferencia") })
        .then(function (a) { avisar(a.apelido + " entrou na turma. Entregue o cartão com a senha e o código."); return carregarTurmas(); })
        .catch(function (e) { avisar(e.message, "erro"); });
    });
    return form;
  }

  function desenharTurmas() {
    listaTurmas.textContent = "";
    if (!turmas.length) listaTurmas.appendChild(el("li", { classe: "dica", texto: "Você ainda não tem turmas. Crie a primeira abaixo." }));
    turmas.forEach(function (t) {
      listaTurmas.appendChild(el("li", { classe: "cartao turma" }, [
        el("h3", { texto: t.nome }),
        el("p", {}, [el("strong", { texto: "Código da turma: " }), el("span", { classe: "codigo", texto: t.codigo })]),
        el("p", { classe: "dica", texto: "O aluno entra com este código e com a senha de figurinhas dele." }),
        el("ul", { classe: "lista-alunos" }, t.alunos.map(cartaoAluno)),
        el("details", {}, [el("summary", { texto: "Adicionar aluno nesta turma" }), formNovoAluno(t)])
      ]));
    });
    // seletor de turma do envio de material
    seletorTurma.textContent = "";
    if (!turmas.length) seletorTurma.appendChild(el("option", { value: "", texto: "Crie uma turma primeiro" }));
    turmas.forEach(function (t) { seletorTurma.appendChild(el("option", { value: String(t.id), texto: t.nome + " (" + t.alunos.length + (t.alunos.length === 1 ? " aluno)" : " alunos)") })); });
  }

  function carregarTurmas() {
    return Prisma.api.turmas().then(function (lista) { turmas = lista; desenharTurmas(); })
      .catch(function (e) { avisar(e.message, "erro"); });
  }

  function montarTurmas(area) {
    listaTurmas = el("ul", { classe: "lista-turmas" });
    var nomeId = "nome_turma";
    var form = el("form", { classe: "cartao form-nova-turma" }, [
      el("div", { classe: "campo" }, [el("label", { for: nomeId, texto: "Nome da nova turma" }),
        el("input", { type: "text", id: nomeId, maxlength: "60", placeholder: "5º ano A" })]),
      el("button", { type: "submit", classe: "botao botao--secundario" }, [icone("plus"), " Criar turma"])
    ]);
    form.addEventListener("submit", function (ev) {
      ev.preventDefault();
      Prisma.api.novaTurma(form.querySelector("#" + nomeId).value).then(function (t) {
        form.reset();
        avisar("Turma criada. O código dela é " + t.codigo + ".");
        return carregarTurmas();
      }).catch(function (e) { avisar(e.message, "erro"); });
    });
    area.appendChild(el("h2", { texto: "Minhas turmas" }));
    area.appendChild(listaTurmas);
    area.appendChild(form);
  }

  /* ---------------- envio de material ---------------- */

  function formulario() {
    var arq = el("input", { type: "file", id: "arquivo", required: "", accept: ".pdf,.pptx,.txt,.md,.mp4,.mov,.mkv,.webm,.mp3,.wav,.m4a,.ogg", "aria-describedby": "dica-arquivo" });
    seletorTurma = el("select", { id: "turma-envio", "aria-describedby": "dica-turma-envio" });
    var botao = el("button", { type: "submit", classe: "botao" }, [icone("upload"), " Adaptar material"]);
    var f = el("form", { classe: "cartao form-envio", novalidate: "" }, [
      el("div", { classe: "campo" }, [
        el("label", { for: "arquivo", texto: "Material da aula" }), arq,
        el("p", { id: "dica-arquivo", classe: "dica", texto: "Pode ser PDF, PowerPoint, texto, vídeo ou áudio. Use só materiais sem dados reais de alunos." })
      ]),
      el("div", { classe: "campo" }, [
        el("label", { for: "turma-envio", texto: "Para qual turma" }), seletorTurma,
        el("p", { id: "dica-turma-envio", classe: "dica", texto: "As versões saem conforme as necessidades dos alunos dessa turma." })
      ]),
      botao
    ]);
    f.addEventListener("submit", function (ev) {
      ev.preventDefault();
      if (estaOcupado) return;
      if (!arq.files.length) { avisar("Escolha o arquivo da aula primeiro.", "erro"); arq.focus(); return; }
      if (!seletorTurma.value) { avisar("Crie uma turma antes de enviar o material.", "erro"); return; }
      ocupar(botao, true, "Adaptando… PDFs grandes e vídeos podem levar alguns minutos.");
      Prisma.api.adaptar(arq.files[0], seletorTurma.value).then(function (m) {
        f.reset();
        avisar("Pronto! O material está em Seus materiais, esperando a sua revisão.");
        return recarregar(m.id);
      }).catch(function (e) { avisar(e.message, "erro"); })
        .then(function () { ocupar(botao, false); });
    });
    return f;
  }

  function ocupar(botao, sim, msg) {
    estaOcupado = sim;
    botao.disabled = sim;
    botao.setAttribute("aria-busy", sim ? "true" : "false");
    if (sim) avisar(msg);
  }

  /* ---------------- revisão ---------------- */

  function cartaoMaterial(m) {
    var est = ESTADOS[m.estado] || ["", m.estado];
    var titulo = el("h3", { tabindex: "-1", texto: m.titulo || m.material });
    var versoes = Object.keys(m.versoes).map(function (k) {
      var v = m.versoes[k];
      if (v.status === "pendente_ia") return el("li", {}, [el("strong", { texto: v.nome + ": " }), "precisa da IA, que está desligada."]);
      if (v.status === "falhou") return el("li", {}, [el("strong", { texto: v.nome + ": " }), "não saiu. " + (v.motivo || "")]);
      return el("li", {}, [el("a", { href: Prisma.api.url(v.url), target: "_blank", rel: "noopener", texto: "Abrir a versão " + v.nome }), " (abre em outra aba)"]);
    });
    var partes = [
      el("div", { classe: "painel-cab" }, [titulo, el("span", { classe: "etiqueta " + est[0], texto: est[1] })]),
      el("p", { classe: "dica", texto: "Arquivo: " + m.material + (m.turma ? ". Turma: " + m.turma + "." : ".") }),
      el("ul", {}, versoes)
    ];
    if (m.transformacoes_aplicadas && m.transformacoes_aplicadas.length) {
      partes.push(el("details", {}, [el("summary", { texto: "O que o PRISMA mudou (" + m.transformacoes_aplicadas.length + ")" }),
        el("ul", {}, m.transformacoes_aplicadas.map(function (t) { return el("li", { texto: t }); }))]));
    }
    var pend = (m.pendencias_para_o_professor || []);
    if (pend.length) {
      partes.push(el("details", { open: "" }, [el("summary", { texto: "Para você conferir (" + pend.length + ")" }),
        el("ul", {}, pend.map(function (t) { return el("li", { texto: t }); }))]));
    }
    // sem descrição, ou descrita pela IA (o professor confere e corrige)
    var imagens = (m.imagens || []).filter(function (i) { return !i.alt || i.origem === "ia"; });
    if (imagens.length && m.estado !== "publicado") partes.push(formularioImagens(m, imagens));
    var acoes = el("div", { classe: "acoes-material" });
    if (m.estado !== "publicado") acoes.appendChild(botaoAprovar(m));
    var apagar = el("button", { type: "button", classe: "botao botao--fantasma botao--pequeno", texto: "Apagar material" });
    apagar.addEventListener("click", function () {
      if (!confirm("Apagar " + (m.titulo || m.material) + "? A turma deixa de ver este material.")) return;
      Prisma.api.apagarMaterial(m.id).then(function () { avisar("Material apagado."); return recarregar(); })
        .catch(function (e) { avisar(e.message, "erro"); });
    });
    acoes.appendChild(apagar);
    partes.push(acoes);
    return el("li", { classe: "cartao", "data-id": m.id }, partes);
  }

  function formularioImagens(m, imagens) {
    var campos = imagens.map(function (img, i) {
      var id = "d-" + m.id + "-" + i;
      var area = el("textarea", { id: id, rows: "3", "data-imagem": img.arquivo });
      area.value = img.alt || "";
      var rotulo = img.origem === "ia"
        ? "Imagem " + (i + 1) + ": a IA escreveu esta descrição. Confira e corrija se precisar."
        : "Imagem " + (i + 1) + ": descreva para quem não consegue ver.";
      return el("div", { classe: "campo" }, [
        el("img", { src: Prisma.api.url("/api/previa/" + m.id + "/" + img.arquivo), alt: "", classe: "miniatura" }),
        el("label", { for: id, texto: rotulo }), area
      ]);
    });
    var salvar = el("button", { type: "submit", classe: "botao botao--secundario" }, ["Salvar descrições"]);
    var f = el("form", { classe: "descricoes" }, [
      el("h4", { texto: "Descrições das imagens" }),
      el("p", { classe: "dica", texto: "Toda imagem precisa de descrição para o material ser publicado. Salvar confirma o texto." })
    ].concat(campos, [salvar]));
    f.addEventListener("submit", function (ev) {
      ev.preventDefault();
      var mapa = {};
      Array.prototype.forEach.call(f.querySelectorAll("textarea"), function (t) { if (t.value.trim()) mapa[t.dataset.imagem] = t.value.trim(); });
      if (!Object.keys(mapa).length) { avisar("Escreva pelo menos uma descrição.", "erro"); return; }
      salvar.disabled = true;
      Prisma.api.descrever(m.id, mapa).then(function () { avisar("Descrições salvas."); return recarregar(m.id); })
        .catch(function (e) { avisar(e.message, "erro"); salvar.disabled = false; });
    });
    return f;
  }

  function botaoAprovar(m) {
    var b = el("button", { type: "button", classe: "botao" }, [icone("check-double"), " Aprovar e publicar"]);
    var nota = el("p", { classe: "dica", id: "nota-" + m.id, texto: m.pode_publicar
      ? "Ao aprovar, os alunos e as famílias da turma passam a ver este material."
      : "Ainda não dá para publicar. Descreva todas as imagens primeiro." });
    if (!m.pode_publicar) { b.disabled = true; b.setAttribute("aria-describedby", nota.id); }
    b.addEventListener("click", function () {
      b.disabled = true;
      Prisma.api.aprovar(m.id).then(function () { avisar("Material publicado para a turma."); return recarregar(m.id); })
        .catch(function (e) { avisar(e.message, "erro"); b.disabled = false; });
    });
    return el("div", {}, [b, nota]);
  }

  function recarregar(focoId) {
    return Prisma.api.materiais().then(function (resumos) {
      return Promise.all(resumos.map(function (r) { return Prisma.api.material(r.id); }));
    }).then(function (todos) {
      listaMateriais.textContent = "";
      if (!todos.length) { listaMateriais.appendChild(el("li", { classe: "dica", texto: "Nenhum material enviado ainda." })); return; }
      todos.forEach(function (m) { listaMateriais.appendChild(cartaoMaterial(m)); });
      if (focoId) {
        var c = listaMateriais.querySelector('[data-id="' + focoId + '"] h3');
        if (c) { c.scrollIntoView({ block: "center" }); c.focus(); }
      }
    }).catch(function (e) { avisar(e.message, "erro"); });
  }

  /* ---------------- feedbacks dos alunos ---------------- */

  function estrelasTexto(media) {
    var cheias = Math.round(media || 0), s = "";
    for (var i = 1; i <= 5; i++) s += i <= cheias ? "★" : "☆";
    return s;
  }

  function montarFeedbacks(area) {
    var lista = el("ul", { classe: "lista-feedbacks" });
    var estado = el("div", { role: "status", "aria-live": "polite" });
    var atualizar = el("button", { type: "button", classe: "botao botao--secundario botao--pequeno" }, [icone("reload"), " Atualizar"]);
    area.appendChild(el("div", { classe: "painel-cab" }, [el("h2", { texto: "Feedbacks dos alunos" }), atualizar]));
    area.appendChild(el("p", { classe: "dica", texto: "Cada aluno pode dar de 1 a 5 estrelas e deixar uma sugestão. As duas são opcionais. Quem pulou não aparece." }));
    area.appendChild(estado);
    area.appendChild(lista);
    function carregar() {
      estado.textContent = "";
      return Prisma.api.feedbacks().then(function (mats) {
        lista.textContent = "";
        var publicados = mats.filter(function (m) { return m.estado === "publicado"; });
        if (!publicados.length) { lista.appendChild(el("li", { classe: "dica", texto: "Quando você publicar um material, as avaliações da turma aparecem aqui." })); return; }
        publicados.forEach(function (m) {
          var corpo = m.total
            ? el("ul", { classe: "avaliacoes-alunos" }, m.avaliacoes.map(function (a) {
                return el("li", {}, [
                  el("span", { classe: "quem", texto: a.aluno }),
                  a.estrelas ? el("span", { classe: "media-estrelas", "aria-label": a.estrelas + " de 5 estrelas" }, [" " + estrelasTexto(a.estrelas)]) : el("span", { classe: "dica", texto: " sem estrelas" }),
                  a.sugestao ? el("blockquote", { texto: a.sugestao }) : null
                ]);
              }))
            : el("p", { classe: "dica", texto: "Ninguém avaliou ainda." });
          lista.appendChild(el("li", { classe: "cartao" }, [
            el("h3", { texto: m.titulo }),
            el("p", { classe: "dica", texto: (m.turma ? "Turma " + m.turma + ". " : "") + m.total + (m.total === 1 ? " avaliação." : " avaliações.") }),
            m.media ? el("p", { classe: "media-estrelas", "aria-label": "Média " + String(m.media).replace(".", ",") + " de 5" },
              [estrelasTexto(m.media), el("strong", { texto: "média " + String(m.media).replace(".", ",") + " de 5" })]) : null,
            corpo
          ]));
        });
      }).catch(function (e) { estado.appendChild(el("p", { classe: "erro", texto: e.message })); });
    }
    atualizar.addEventListener("click", carregar);
    carregar();
  }

  document.addEventListener("prisma:painel", function (ev) {
    if (ev.detail.perfil !== "professor") return;
    var areaTurmas = document.getElementById("area-turmas");
    var area = document.getElementById("area-professor");
    aviso = el("div", { role: "status", "aria-live": "polite", classe: "aviso-fixo" });
    listaMateriais = el("ul", { classe: "lista-materiais" });
    area.appendChild(el("h2", { texto: "Enviar material" }));
    area.appendChild(formulario());
    area.appendChild(el("h2", { texto: "Seus materiais" }));
    area.appendChild(listaMateriais);
    document.getElementById("painel").insertBefore(aviso, areaTurmas);
    montarFeedbacks(document.getElementById("area-feedbacks"));

    Prisma.api.opcoes().then(function (o) {
      opcoes = o;
      montarTurmas(areaTurmas);
      return carregarTurmas();
    }).then(function () { return recarregar(); });
  });
})();
