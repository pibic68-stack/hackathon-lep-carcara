/* Login de verdade: fala com a API do PRISMA (backend/adaptador/api.py).
   A sessão fica num cookie protegido (HttpOnly): o JavaScript nunca vê o "token".

   Prisma.auth.entrar(perfil, dados)   -> Promise<{ ok, nome, destino } | { ok: false, erro: { campo, texto } }>
     professor: { email, senha, lembrar }
     familia:   { codigo }
     aluno:     { turma, figuras: ["sol", "lua", "coracao"] }
   Prisma.auth.cadastrar(dados)        -> igual, para criar conta de professor
     { nome, email_novo, senha_nova, codigo_escola, lembrar }
   Prisma.auth.sessao()                -> Promise<usuário | null>
   Prisma.auth.exigir("professor")     -> Promise<usuário>; sem login, volta para a tela de entrada
   Prisma.auth.sair()                  -> Promise
*/
window.Prisma = window.Prisma || {};
Prisma.auth = (function () {
  var base = location.protocol === "file:" ? "http://127.0.0.1:8000" : "";

  function pedir(caminho, corpo) {
    return fetch(base + caminho, {
      method: corpo ? "POST" : "GET",
      credentials: "same-origin",
      headers: corpo ? { "Content-Type": "application/json", "X-Prisma": "1" } : {},
      body: corpo ? JSON.stringify(corpo) : undefined
    });
  }

  // Resposta da API -> formato que a tela de entrada entende.
  function traduzir(promessa, campoPadrao) {
    return promessa.then(function (r) {
      return r.json().catch(function () { return {}; }).then(function (corpo) {
        if (r.ok) return { ok: true, nome: corpo.nome, destino: corpo.destino };
        var d = corpo.detail || {};
        var texto = typeof d === "string" ? d : (d.erro || "Não deu certo. Tente de novo.");
        return { ok: false, erro: { campo: d.campo || campoPadrao, texto: texto } };
      });
    }, function () {
      return { ok: false, erro: { campo: campoPadrao, texto: "O servidor do PRISMA não respondeu. Confira a internet." } };
    });
  }

  var CAMPO_PADRAO = { professor: "senha", escola: "senha", familia: "codigo", aluno: "figuras" };

  return {
    entrar: function (perfil, dados) {
      var erro = Prisma.auth.validar(perfil, dados);
      if (erro) return Promise.resolve({ ok: false, erro: erro });
      if (location.protocol === "file:") {
        return Promise.resolve({ ok: false, erro: { campo: CAMPO_PADRAO[perfil], texto: "Para entrar, abra o site pelo servidor do PRISMA, não pelo arquivo." } });
      }
      var corpo = { perfil: perfil, lembrar: !!dados.lembrar };
      Object.keys(dados).forEach(function (k) { corpo[k] = dados[k]; });
      return traduzir(pedir("/api/entrar", corpo), CAMPO_PADRAO[perfil]);
    },

    cadastrar: function (d) {
      if (!d.nome || d.nome.trim().length < 2) return Promise.resolve({ ok: false, erro: { campo: "nome", texto: "Digite o seu nome." } });
      if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(d.email_novo || "")) return Promise.resolve({ ok: false, erro: { campo: "email_novo", texto: "Digite um e-mail válido, como nome@escola.br." } });
      if (!d.senha_nova || d.senha_nova.length < 8) return Promise.resolve({ ok: false, erro: { campo: "senha_nova", texto: "A senha precisa ter pelo menos 8 caracteres." } });
      if (!d.codigo_escola || !d.codigo_escola.trim()) return Promise.resolve({ ok: false, erro: { campo: "codigo_escola", texto: "Digite o código da escola. A coordenação tem esse código." } });
      return traduzir(pedir("/api/contas/professor", {
        nome: d.nome, email: d.email_novo, senha: d.senha_nova, codigo_escola: d.codigo_escola, lembrar: !!d.lembrar
      }), "codigo_escola");
    },

    cadastrarEscola: function (d) {
      if (!d.nome || d.nome.trim().length < 3) return Promise.resolve({ ok: false, erro: { campo: "escola_nome", texto: "Digite o nome da escola." } });
      if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(d.email || "")) return Promise.resolve({ ok: false, erro: { campo: "escola_email", texto: "Digite um e-mail válido, como coordenacao@escola.br." } });
      if (!d.senha || d.senha.length < 8) return Promise.resolve({ ok: false, erro: { campo: "escola_senha", texto: "A senha precisa ter pelo menos 8 caracteres." } });
      var cod = (d.codigo || "").replace(/[^A-Za-z0-9]/g, "");
      if (cod.length < 6) return Promise.resolve({ ok: false, erro: { campo: "escola_codigo", texto: "O código para os professores precisa ter pelo menos 6 letras ou números." } });
      if (location.protocol === "file:") return Promise.resolve({ ok: false, erro: { campo: "escola_nome", texto: "Para cadastrar, abra o site pelo servidor do PRISMA, não pelo arquivo." } });
      return traduzir(pedir("/api/contas/escola", d), "escola_codigo");
    },

    /* validação só do formato; a de verdade é no servidor */
    validar: function (perfil, d) {
      if (perfil === "aluno") {
        if (!d.turma || d.turma.trim().length < 3) return { campo: "turma", texto: "Digite o código da turma. Ele está no cartão que o professor entregou." };
        if (!d.figuras || d.figuras.length !== 3) return { campo: "figuras", texto: "Escolha 3 figurinhas, na ordem da sua senha." };
        return null;
      }
      if (perfil === "familia") {
        return d.codigo && d.codigo.trim().length >= 4 ? null : { campo: "codigo", texto: "Digite o código que a escola enviou." };
      }
      if (!d.email || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(d.email)) return { campo: "email", texto: "Digite um e-mail válido, como nome@escola.br." };
      if (!d.senha) return { campo: "senha", texto: "Digite a sua senha." };
      return null;
    },

    sessao: function () {
      return pedir("/api/eu").then(function (r) { return r.ok ? r.json().catch(function () { return null; }) : null; }, function () { return null; });
    },

    exigir: function (perfil) {
      return Prisma.auth.sessao().then(function (u) {
        if (!u || (perfil && u.perfil !== perfil)) {
          location.replace("../entrar.html#" + (perfil || ""));
          return new Promise(function () {});   // a página está saindo
        }
        return u;
      });
    },

    sair: function () {
      return pedir("/api/sair", {}).catch(function () {});
    }
  };
})();
