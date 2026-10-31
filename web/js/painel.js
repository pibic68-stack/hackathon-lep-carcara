/* Painel de cada perfil. O perfil vem de <body data-perfil="professor|familia|aluno">.
   Só abre para quem entrou com esse perfil (Prisma.auth.exigir). As áreas que já funcionam
   são montadas por professor.js e biblioteca.js; o resto aparece como "em breve". */
(function () {
  var PAINEIS = {
    escola: {
      avatar: "escola.jpg", ola: function (n) { return n; },
      areas: ["area-escola"],
      breve: [["users", "Convidar professores", "Enviar o código da escola por e-mail."]]
    },
    professor: {
      avatar: "professor.png", ola: function (n) { return "Boa aula, " + n + "!"; },
      areas: ["area-turmas", "area-professor", "area-feedbacks"],
      breve: [["calendar", "Agenda da turma", "Datas das aulas e entregas."]]
    },
    familia: {
      avatar: "familia.png", ola: function (n) { return "Olá, " + n + "!"; },
      areas: ["area-familia", "area-biblioteca"],
      breve: [["chat", "Recados da escola", "Mensagens da professora."],
              ["calendar", "Agenda", "Atividades e datas importantes."]]
    },
    aluno: {
      avatar: "aluno.png", ola: function (n) { return "Oi, " + n + "! Bora estudar?"; },
      areas: ["area-biblioteca"],
      breve: [["trophy", "Minhas conquistas", "Figurinhas por cada atividade feita."]]
    }
  };

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
  function icone(nome) { var s = document.createElement("span"); s.innerHTML = window.icone(nome); return s; }

  document.addEventListener("DOMContentLoaded", function () {
    var perfil = document.body.dataset.perfil;
    var p = PAINEIS[perfil];
    var alvo = document.getElementById("painel");
    if (!p || !alvo) return;
    alvo.appendChild(el("p", { classe: "dica", role: "status", texto: "Abrindo o seu painel…" }));

    Prisma.auth.exigir(perfil).then(function (u) {
      Prisma.usuario = u;
      alvo.textContent = "";
      var sair = el("button", { type: "button", classe: "botao botao--secundario botao--pequeno" }, [icone("login"), " Sair"]);
      sair.addEventListener("click", function () {
        sair.disabled = true;
        Prisma.auth.sair().then(function () { location.href = "../entrar.html"; });
      });
      var titulo = el("h1", { tabindex: "-1", texto: p.ola(u.nome) });
      alvo.appendChild(el("div", { classe: "painel-cab" }, [
        el("img", { classe: "pixel", src: "../assets/img/" + p.avatar, alt: "" }),
        el("div", {}, [el("p", { classe: "rotulo", texto: u.turma ? "Turma " + u.turma : (perfil === "escola" ? "Painel da escola" : (u.escola ? u.escola : "Painel")) }), titulo]),
        sair
      ]));
      alvo.appendChild(el("p", { classe: "aviso" }, [icone("info-box"),
        el("span", {}, [el("strong", { texto: "Demonstração: " }), "use só nomes e dados fictícios."])]));
      p.areas.forEach(function (id) { alvo.appendChild(el("section", { id: id, classe: "area-painel" })); });
      alvo.appendChild(el("h2", { classe: "mais-em-breve", texto: "Em breve" }));
      alvo.appendChild(el("ul", { classe: "painel-grade" }, p.breve.map(function (c) {
        return el("li", { classe: "cartao" }, [el("h3", {}, [icone(c[0]), c[1]]), el("p", { texto: c[2] }),
          el("span", { classe: "etiqueta etiqueta--sol em-breve", texto: "em breve" })]);
      })));
      document.dispatchEvent(new CustomEvent("prisma:painel", { detail: u }));
    });
  });
})();
