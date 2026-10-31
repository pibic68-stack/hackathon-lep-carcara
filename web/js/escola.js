/* Painel da escola: só leitura. Lista os professores que entraram com o código da escola,
   as turmas e os alunos (apelidos fictícios) e os materiais enviados. A escola não muda nada. */
(function () {
  var ESTADOS = { rascunho: ["etiqueta--sol", "Esperando aprovação"], publicado: ["etiqueta--ok", "Publicado"] };

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
  function data(iso) {
    if (!iso) return "";
    try { return new Date(iso).toLocaleDateString("pt-BR"); } catch (e) { return ""; }
  }
  function plural(n, um, varios) { return n + " " + (n === 1 ? um : varios); }

  document.addEventListener("prisma:painel", function (ev) {
    if (ev.detail.perfil !== "escola") return;
    var area = document.getElementById("area-escola");
    var estado = el("div", { role: "status", "aria-live": "polite" });
    area.appendChild(estado);
    estado.appendChild(el("p", { classe: "dica", texto: "Carregando as listas da escola…" }));

    Prisma.api.escola().then(function (d) {
      estado.textContent = "";
      var turmas = 0, alunos = 0;
      d.professores.forEach(function (p) { turmas += p.turmas.length; p.turmas.forEach(function (t) { alunos += t.alunos.length; }); });

      area.appendChild(el("ul", { classe: "numeros-escola", "aria-label": "Resumo" }, [
        el("li", {}, [el("strong", { texto: String(d.professores.length) }), el("span", { texto: d.professores.length === 1 ? " professor" : " professores" })]),
        el("li", {}, [el("strong", { texto: String(turmas) }), el("span", { texto: turmas === 1 ? " turma" : " turmas" })]),
        el("li", {}, [el("strong", { texto: String(alunos) }), el("span", { texto: alunos === 1 ? " aluno" : " alunos" })]),
        el("li", {}, [el("strong", { texto: String(d.materiais.length) }), el("span", { texto: d.materiais.length === 1 ? " material" : " materiais" })])
      ]));
      if (d.assinatura) {
        var a = d.assinatura;
        area.appendChild(el("section", { classe: "cartao assinatura", "aria-labelledby": "titulo-assinatura" }, [
          el("h2", { id: "titulo-assinatura", texto: "Assinatura" }),
          el("p", {}, [el("strong", { texto: "Plano " + a.plano_nome }), " (até " + a.alunos.toLocaleString("pt-BR") + " alunos) · " +
            a.periodo_nome + ": R$ " + a.valor.toLocaleString("pt-BR") + (a.periodo === "anual" ? " por ano" : " por semestre")]),
          el("p", {}, [el("strong", { texto: "Forma de pagamento: " }), a.pagamento_nome + ". ",
            el("span", { classe: "etiqueta etiqueta--sol", texto: "Pagamento em breve" })]),
          el("p", { classe: "dica", texto: "A conta da escola está ativa e pode ser usada agora. A cobrança ainda não foi ligada ao PRISMA: os dados de pagamento chegam em breve." })
        ]));
      }
      area.appendChild(el("p", { classe: "dica", texto: "O código para os professores foi criado no cadastro. Por segurança, o PRISMA guarda só uma impressão dele e não consegue mostrá-lo de novo." }));

      // professores
      area.appendChild(el("h2", { texto: "Professores" }));
      if (!d.professores.length) {
        area.appendChild(el("p", { classe: "dica", texto: "Nenhum professor ainda. Passe o código da escola para eles criarem a conta em Entrar." }));
      } else {
        area.appendChild(el("ul", { classe: "lista-turmas" }, d.professores.map(function (p) {
          return el("li", { classe: "cartao" }, [
            el("h3", { texto: p.nome }),
            el("p", { classe: "dica", texto: p.email + " · " + plural(p.turmas.length, "turma", "turmas") }),
            p.turmas.length ? el("ul", { classe: "turmas-escola" }, p.turmas.map(function (t) {
              return el("li", {}, [
                el("strong", { texto: t.nome }), " · " + plural(t.alunos.length, "aluno", "alunos"),
                t.alunos.length ? el("p", { classe: "apelidos", texto: t.alunos.join(", ") }) : null
              ]);
            })) : null
          ]);
        })));
      }

      // materiais
      area.appendChild(el("h2", { texto: "Materiais" }));
      if (!d.materiais.length) {
        area.appendChild(el("p", { classe: "dica", texto: "Nenhum material enviado ainda." }));
        return;
      }
      var tabela = el("table", { classe: "tabela-escola" }, [
        el("caption", { classe: "so-leitor", texto: "Materiais enviados pelos professores da escola" }),
        el("thead", {}, [el("tr", {}, ["Material", "Professor", "Turma", "Situação", "Enviado em"].map(function (c) { return el("th", { scope: "col", texto: c }); }))]),
        el("tbody", {}, d.materiais.map(function (m) {
          var e = ESTADOS[m.estado] || ["", m.estado];
          return el("tr", {}, [
            el("th", { scope: "row", texto: m.titulo }), el("td", { texto: m.professor }), el("td", { texto: m.turma || "" }),
            el("td", {}, [el("span", { classe: "etiqueta " + e[0], texto: e[1] })]), el("td", { texto: data(m.criado) })
          ]);
        }))
      ]);
      area.appendChild(el("div", { classe: "rolagem-tabela" }, [tabela]));
    }).catch(function (e) { estado.textContent = ""; estado.appendChild(el("p", { classe: "erro", texto: e.message })); });
  });
})();
