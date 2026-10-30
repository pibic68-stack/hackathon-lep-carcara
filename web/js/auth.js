/* "Contrato" do login. Hoje é FALSO: não envia nada para lugar nenhum.
   Quando o backend existir, só esta função muda (ex.: fetch("/api/entrar", ...)).

   Prisma.auth.entrar(perfil, dados) -> Promise<{ ok, nome, destino } | { ok: false, erro }>
     perfil: "professor" | "familia" | "aluno"
     dados:
       professor: { email, senha }
       familia:   { email, senha }  ou  { codigo }
       aluno:     { turma, figuras: ["sol", "lua", "coracao"] }
*/
window.Prisma = window.Prisma || {};
Prisma.auth = {
  entrar: function (perfil, dados) {
    return new Promise(function (resolver) {
      setTimeout(function () {
        var erro = Prisma.auth.validar(perfil, dados);
        if (erro) return resolver({ ok: false, erro: erro });
        var nomes = { professor: "Prof.ª Coruja", familia: "Família Urso", aluno: "Preguiça" };
        try { sessionStorage.setItem("prisma-sessao", JSON.stringify({ perfil: perfil, nome: nomes[perfil] })); } catch (e) { /* segue sem salvar */ }
        resolver({ ok: true, nome: nomes[perfil], destino: "painel/" + perfil + ".html" });
      }, 500);
    });
  },

  /* validação só do formato; a de verdade será no servidor */
  validar: function (perfil, d) {
    if (perfil === "aluno") {
      if (!d.turma || d.turma.trim().length < 3) return { campo: "turma", texto: "Digite o código da turma. Ele está no cartão que o professor entregou." };
      if (!d.figuras || d.figuras.length !== 3) return { campo: "figuras", texto: "Escolha 3 figurinhas, na ordem da sua senha." };
      return null;
    }
    if (perfil === "familia" && d.codigo !== undefined) {
      return d.codigo.trim().length >= 4 ? null : { campo: "codigo", texto: "Digite o código que a escola enviou." };
    }
    if (!d.email || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(d.email)) return { campo: "email", texto: "Digite um e-mail válido, como nome@escola.br." };
    if (!d.senha || d.senha.length < 6) return { campo: "senha", texto: "A senha precisa ter pelo menos 6 caracteres." };
    return null;
  },

  sessao: function () {
    try { return JSON.parse(sessionStorage.getItem("prisma-sessao")); } catch (e) { return null; }
  },
  sair: function () {
    try { sessionStorage.removeItem("prisma-sessao"); } catch (e) { /* nada */ }
  }
};
