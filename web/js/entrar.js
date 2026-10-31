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
    familia: { rotulo: "Família", ola: "Olá, família!", avatar: "familia.png", form: "form-codigo" },
    aluno: { rotulo: "Aluno(a)", ola: "Oi! Vamos estudar?", avatar: "aluno.png", form: "form-aluno" },
    escola: { rotulo: "Escola", ola: "Olá, coordenação!", avatar: "escola.jpg", form: "form-email" }
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
    ["form-email", "form-codigo", "form-aluno", "form-cadastro", "form-escola"].forEach(function (f) { $(f).hidden = f !== cfg.form; });
    $("criar-conta").hidden = p !== "professor";
    $("criar-escola").hidden = p !== "escola";
    limparErros();
    $("status").textContent = "";
    history.replaceState(null, "", "#" + p);
    if (focar !== false) $("titulo-form").focus();
  }

  function mostrarCadastro(sim) {
    var escola = perfil === "escola";
    var form = escola ? "form-escola" : "form-cadastro";
    limparErros();
    $("status").textContent = "";
    $("form-email").hidden = sim;
    $(form).hidden = !sim;
    $("titulo-form").textContent = sim ? (escola ? "Boas-vindas, escola!" : "Bem-vindo(a) ao PRISMA!") : PERFIS[perfil].ola;
    $(sim ? (escola ? "escola_nome" : "nome") : "email").focus();
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
    $("abrir-cadastro").addEventListener("click", function () { mostrarCadastro(true); });
    $("voltar-entrar").addEventListener("click", function () { mostrarCadastro(false); });
    $("abrir-cadastro-escola").addEventListener("click", function () { mostrarCadastro(true); });
    $("voltar-entrar-escola").addEventListener("click", function () { mostrarCadastro(false); });
    $("esqueci").addEventListener("click", function () {
      $("status").textContent = "Ainda não dá para trocar a senha sozinho. Peça ajuda à coordenação da escola.";
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

    function enviar(form, dados, acao) {
      form.addEventListener("submit", function (e) {
        e.preventDefault();
        limparErros();
        var botao = form.querySelector("[type=submit]");
        botao.disabled = true;
        $("status").textContent = "Entrando…";
        (acao || Prisma.auth.entrar)(perfil, dados()).then(function (r) {
          botao.disabled = false;
          if (!r.ok) { $("status").textContent = ""; mostrarErro(r.erro); return; }
          $("status").textContent = "Pronto, " + r.nome + "! Abrindo o seu painel…";
          setTimeout(function () { location.href = r.destino; }, 600);
        });
      });
    }
    enviar($("form-email"), function () { return { email: $("email").value.trim(), senha: $("senha").value, lembrar: $("lembrar").checked }; });
    enviar($("form-cadastro"), function () {
      return { nome: $("nome").value.trim(), email_novo: $("email_novo").value.trim(), senha_nova: $("senha_nova").value,
               codigo_escola: $("codigo_escola").value.trim(), lembrar: $("lembrar_novo").checked };
    }, function (_, d) { return Prisma.auth.cadastrar(d); });
    enviar($("form-escola"), function () {
      return { nome: $("escola_nome").value.trim(), email: $("escola_email").value.trim(), senha: $("escola_senha").value,
               codigo: $("escola_codigo").value.trim(), lembrar: $("lembrar_escola").checked };
    }, function (_, d) { return Prisma.auth.cadastrarEscola(d); });
    enviar($("form-codigo"), function () { return { codigo: $("codigo").value }; });
    enviar($("form-aluno"), function () { return { turma: $("turma").value, figuras: figuras.slice() }; });

    // index.html pode mandar direto para um perfil: entrar.html#aluno
    var inicial = location.hash.slice(1);
    if (PERFIS[inicial]) escolher(inicial, false);

    // quem já entrou pode ir direto para o painel
    Prisma.auth.sessao().then(function (u) {
      if (!u) return;
      var aviso = $("ja-entrou");
      aviso.textContent = "";
      aviso.appendChild(document.createTextNode("Você já entrou como " + u.nome + ". "));
      var link = document.createElement("a");
      link.href = "painel/" + u.perfil + ".html";
      link.textContent = "Ir para o meu painel";
      aviso.appendChild(link);
      aviso.hidden = false;
    });
  });
})();
