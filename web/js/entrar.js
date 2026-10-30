/* Tela de entrada: escolher perfil → formulário do perfil → Prisma.auth.entrar(). */
(function () {
  var FIGURAS = [
    { id: "coracao", nome: "Coração", icone: "heart", cor: "#F08BB4" },
    { id: "sol", nome: "Sol", icone: "sun", cor: "#FFC93C" },
    { id: "lua", nome: "Lua", icone: "moon", cor: "#B89AF0" },
    { id: "raio", nome: "Raio", icone: "zap", cor: "#FFAD60" },
    { id: "trofeu", nome: "Troféu", icone: "trophy", cor: "#FFE38A" },
    { id: "livro", nome: "Livro", icone: "book-open", cor: "#57B3F9" },
    { id: "lampada", nome: "Lâmpada", icone: "lightbulb", cor: "#FFE9A8" },
    { id: "carinha", nome: "Carinha feliz", icone: "mood-happy", cor: "#7BD389" },
    { id: "casa", nome: "Casa", icone: "home", cor: "#FFD3A6" }
  ];
  var PERFIS = {
    professor: { rotulo: "Professor(a)", ola: "Olá, professor(a)!", avatar: "professor.png", form: "form-email" },
    familia: { rotulo: "Família", ola: "Olá, família!", avatar: "familia.png", form: "form-email" },
    aluno: { rotulo: "Aluno(a)", ola: "Oi! Vamos estudar?", avatar: "aluno.png", form: "form-aluno" }
  };
  var perfil = null, figuras = [];
  function $(id) { return document.getElementById(id); }

  function mostrarPerfis() {
    perfil = null;
    $("passo-form").hidden = true;
    $("passo-perfil").hidden = false;
    history.replaceState(null, "", location.pathname);
    var b = document.querySelector(".perfil"); if (b) b.focus();
  }

  function escolher(p, focar) {
    if (!PERFIS[p]) return;
    perfil = p;
    var cfg = PERFIS[p];
    $("passo-perfil").hidden = true;
    $("passo-form").hidden = false;
    $("form-avatar").src = "assets/img/" + cfg.avatar;
    $("form-rotulo").textContent = cfg.rotulo;
    $("titulo-form").textContent = cfg.ola;
    ["form-email", "form-codigo", "form-aluno"].forEach(function (f) { $(f).hidden = f !== cfg.form; });
    $("abas-familia").hidden = p !== "familia";
    $("criar-conta").hidden = p !== "professor";
    limparErros();
    $("status").textContent = "";
    history.replaceState(null, "", "#" + p);
    if (focar !== false) $("titulo-form").focus();
  }

  function trocarAba(aba) {
    $("form-email").hidden = aba !== "email";
    $("form-codigo").hidden = aba !== "codigo";
    document.querySelectorAll("[data-aba]").forEach(function (t) { t.setAttribute("aria-selected", t.dataset.aba === aba); });
    var alvo = document.querySelector((aba === "email" ? "#form-email" : "#form-codigo") + ' [data-aba="' + aba + '"]');
    if (alvo) alvo.focus();
  }

  /* ---------- erros acessíveis ---------- */
  function limparErros() {
    document.querySelectorAll(".erro").forEach(function (e) { e.hidden = true; e.textContent = ""; });
    document.querySelectorAll("[aria-invalid]").forEach(function (e) { e.removeAttribute("aria-invalid"); });
  }
  function mostrarErro(erro) {
    var caixa = $("erro-" + erro.campo);
    caixa.innerHTML = window.icone("alert") + " " + erro.texto;
    caixa.hidden = false;
    var campo = $(erro.campo);
    if (campo) { campo.setAttribute("aria-invalid", "true"); campo.focus(); }
    else { var g = document.querySelector(".grade-figurinhas button"); if (g) g.focus(); }
  }

  /* ---------- senha de figurinhas ---------- */
  function montarFigurinhas() {
    $("grade-figurinhas").innerHTML = FIGURAS.map(function (f) {
      return '<button type="button" class="figurinha" data-id="' + f.id + '" style="--cor:' + f.cor + '" aria-label="' + f.nome + '">' +
        window.icone(f.icone) + '<span>' + f.nome + "</span></button>";
    }).join("");
    desenharSlots();
  }
  function desenharSlots() {
    var html = "";
    for (var i = 0; i < 3; i++) {
      var f = FIGURAS.find(function (x) { return x.id === figuras[i]; });
      html += f
        ? '<li class="cheio" style="--cor:' + f.cor + '">' + window.icone(f.icone) + '<span class="so-leitor">' + (i + 1) + "ª: " + f.nome + "</span></li>"
        : '<li><span class="so-leitor">' + (i + 1) + "ª: vazia</span>" + (i + 1) + "</li>";
    }
    $("senha-slots").innerHTML = html;
    document.querySelectorAll(".figurinha").forEach(function (b) { b.disabled = figuras.length >= 3; });
  }

  document.addEventListener("DOMContentLoaded", function () {
    montarFigurinhas();

    document.querySelectorAll(".perfil").forEach(function (b) {
      b.addEventListener("click", function () { escolher(b.dataset.perfil); });
    });
    $("trocar-perfil").addEventListener("click", mostrarPerfis);
    document.querySelectorAll("[data-aba]").forEach(function (t) {
      t.addEventListener("click", function () { trocarAba(t.dataset.aba); });
    });

    $("mostrar-senha").addEventListener("click", function () {
      var ver = $("senha").type === "password";
      $("senha").type = ver ? "text" : "password";
      this.setAttribute("aria-pressed", ver);
      this.innerHTML = window.icone(ver ? "eye-closed" : "eye") + (ver ? " Esconder" : " Mostrar");
    });

    $("grade-figurinhas").addEventListener("click", function (e) {
      var b = e.target.closest(".figurinha");
      if (!b || figuras.length >= 3) return;
      figuras.push(b.dataset.id);
      desenharSlots();
      if (figuras.length >= 3) $("limpar-figuras").focus();
    });
    $("limpar-figuras").addEventListener("click", function () {
      figuras = []; desenharSlots();
      document.querySelector(".figurinha").focus();
    });

    document.querySelectorAll("[data-em-breve]").forEach(function (a) {
      a.addEventListener("click", function (e) {
        e.preventDefault();
        $("status").textContent = "“" + a.textContent + "” ainda não existe neste protótipo.";
      });
    });

    function enviar(form, dados) {
      form.addEventListener("submit", function (e) {
        e.preventDefault();
        limparErros();
        var botao = form.querySelector("[type=submit]");
        botao.disabled = true;
        $("status").textContent = "Entrando…";
        Prisma.auth.entrar(perfil, dados()).then(function (r) {
          botao.disabled = false;
          if (!r.ok) { $("status").textContent = ""; mostrarErro(r.erro); return; }
          $("status").textContent = "Pronto, " + r.nome + "! Abrindo o seu painel…";
          setTimeout(function () { location.href = r.destino; }, 600);
        });
      });
    }
    enviar($("form-email"), function () { return { email: $("email").value.trim(), senha: $("senha").value }; });
    enviar($("form-codigo"), function () { return { codigo: $("codigo").value }; });
    enviar($("form-aluno"), function () { return { turma: $("turma").value, figuras: figuras.slice() }; });

    // index.html pode mandar direto para um perfil: entrar.html#aluno
    var inicial = location.hash.slice(1);
    if (PERFIS[inicial]) escolher(inicial, false);
  });
})();
