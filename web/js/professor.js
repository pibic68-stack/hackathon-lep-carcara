/* Área do professor: enviar material, revisar o que foi adaptado, descrever imagens e aprovar.
   Fluxo do Manual: nada chega ao aluno sem aprovação (P10.1); imagem sem descrição bloqueia (P4.1).
   Todo texto vindo do servidor entra na página com textContent (nunca innerHTML): o conteúdo
   vem de arquivos de aula e não é confiável. */
(function () {
  // Necessidades como "jeito de aprender", nunca diagnóstico (P10.2). Chaves iguais às do backend.
  var NECESSIDADES = [
    ["baixa_visao", "Letras grandes e alto contraste"],
    ["daltonismo", "Cor sempre com símbolo"],
    ["instrucoes_em_etapas", "Instruções em etapas"],
    ["leitura_facil", "Texto mais direto (Leitura Fácil)"]
  ];
  var PREFERENCIAS = [["audio", "Ouvir o material"]];
  var ESTADOS = { rascunho: ["etiqueta--sol", "Aguardando sua aprovação"], publicado: ["etiqueta--ok", "Publicado para os alunos"] };

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
  var area, aviso, lista, estaOcupado = false;

  function avisar(texto, tipo) {
    aviso.textContent = "";
    if (!texto) return;
    aviso.appendChild(el("p", { classe: tipo === "erro" ? "erro" : "dica", texto: texto }));
  }

  function caixa(nome, valor, rotulo) {
    var id = "p-" + valor;
    return el("div", { classe: "lembrar" }, [
      el("input", { type: "checkbox", id: id, name: nome, value: valor }),
      el("label", { for: id, texto: rotulo })
    ]);
  }

  function formulario() {
    var arq = el("input", { type: "file", id: "arquivo", required: "", accept: ".pdf,.pptx,.txt,.md,.mp4,.mov,.mkv,.webm,.mp3,.wav,.m4a,.ogg", "aria-describedby": "dica-arquivo" });
    var botao = el("button", { type: "submit", classe: "botao" }, [icone("upload"), " Adaptar material"]);
    var f = el("form", { classe: "cartao form-envio", novalidate: "" }, [
      el("div", { classe: "campo" }, [
        el("label", { for: "arquivo", texto: "Material da aula" }), arq,
        el("p", { id: "dica-arquivo", classe: "dica", texto: "PDF, PowerPoint, texto, vídeo ou áudio. Use só materiais sem dados reais de alunos." })
      ]),
      el("fieldset", { classe: "campo" }, [
        el("legend", { texto: "Como o aluno aprende melhor (perfil fictício)" }),
        el("p", { classe: "dica", texto: "Marque o que ajuda. O PRISMA registra necessidades de aprendizagem, nunca diagnósticos." })
      ].concat(NECESSIDADES.map(function (n) { return caixa("necessidade", n[0], n[1]); }))
        .concat(PREFERENCIAS.map(function (n) { return caixa("preferencia", n[0], n[1]); }))),
      botao
    ]);
    f.addEventListener("submit", function (ev) {
      ev.preventDefault();
      if (estaOcupado) return;
      if (!arq.files.length) { avisar("Escolha o arquivo da aula primeiro.", "erro"); arq.focus(); return; }
      var perfil = {
        necessidades: Array.prototype.map.call(f.querySelectorAll('input[name="necessidade"]:checked'), function (i) { return i.value; }),
        preferencias: Array.prototype.map.call(f.querySelectorAll('input[name="preferencia"]:checked'), function (i) { return i.value; })
      };
      ocupar(botao, true, "Adaptando… vídeos e PDFs grandes podem levar alguns minutos.");
      Prisma.api.adaptar(arq.files[0], perfil).then(function (m) {
        f.reset();
        avisar("Pronto! O material está no fim da página, esperando a sua revisão.");
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

  function cartaoMaterial(m) {
    var est = ESTADOS[m.estado] || ["", m.estado];
    var titulo = el("h3", { tabindex: "-1", texto: m.material });
    var versoes = Object.keys(m.versoes).map(function (k) {
      var v = m.versoes[k];
      if (v.status !== "gerada") {
        return el("li", {}, [el("strong", { texto: v.nome + ": " }), "ainda não disponível (precisa de IA)."]);
      }
      return el("li", {}, [el("a", { href: Prisma.api.url(v.url), target: "_blank", rel: "noopener", texto: "Abrir versão " + v.nome }), " (abre em outra aba)"]);
    });
    var partes = [
      el("div", { classe: "painel-cab" }, [titulo, el("span", { classe: "etiqueta " + est[0], texto: est[1] })]),
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
    if (m.estado !== "publicado") partes.push(botaoAprovar(m));
    return el("li", { classe: "cartao", "data-id": m.id }, partes);
  }

  function formularioImagens(m, imagens) {
    var campos = imagens.map(function (img, i) {
      var id = "d-" + m.id + "-" + i;
      var area = el("textarea", { id: id, rows: "3", "data-imagem": img.arquivo });
      area.value = img.alt || "";
      var rotulo = img.origem === "ia"
        ? "Descrição da imagem " + (i + 1) + ", escrita pela IA. Confira e corrija se precisar"
        : "Descreva a imagem " + (i + 1) + " para quem não consegue vê-la";
      return el("div", { classe: "campo" }, [
        el("img", { src: Prisma.api.url("/api/previa/" + m.id + "/" + img.arquivo), alt: "", classe: "miniatura" }),
        el("label", { for: id, texto: rotulo }),
        area
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
      ? "Ao aprovar, os alunos e as famílias passam a ver este material."
      : "Ainda não dá para publicar: descreva todas as imagens." });
    if (!m.pode_publicar) { b.disabled = true; b.setAttribute("aria-describedby", nota.id); }
    b.addEventListener("click", function () {
      b.disabled = true;
      Prisma.api.aprovar(m.id).then(function () { avisar("Material publicado para os alunos."); return recarregar(m.id); })
        .catch(function (e) { avisar(e.message, "erro"); b.disabled = false; });
    });
    return el("div", {}, [b, nota]);
  }

  function recarregar(focoId) {
    return Prisma.api.materiais().then(function (resumos) {
      return Promise.all(resumos.map(function (r) { return Prisma.api.material(r.id); }));
    }).then(function (todos) {
      lista.textContent = "";
      if (!todos.length) { lista.appendChild(el("li", { classe: "dica", texto: "Nenhum material enviado ainda." })); return; }
      todos.forEach(function (m) { lista.appendChild(cartaoMaterial(m)); });
      if (focoId) {
        var c = lista.querySelector('[data-id="' + focoId + '"] h3');
        if (c) { c.scrollIntoView({ block: "center" }); c.focus(); }
      }
    }).catch(function (e) { avisar(e.message, "erro"); });
  }

  document.addEventListener("DOMContentLoaded", function () {
    area = document.getElementById("area-professor");
    if (!area) return;
    aviso = el("div", { role: "status", "aria-live": "polite" });
    lista = el("ul", { classe: "lista-materiais" });
    area.appendChild(el("h2", { texto: "Enviar material" }));
    area.appendChild(formulario());
    area.appendChild(aviso);
    area.appendChild(el("h2", { texto: "Seus materiais" }));
    area.appendChild(lista);
    recarregar();
  });
})();
