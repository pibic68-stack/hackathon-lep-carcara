/* Cliente da API do PRISMA (backend em Python). Documentação das rotas: backend/README.md.

   O site é entregue pelo próprio servidor da API (mesmo endereço), então a sessão (cookie) funciona.
   Aberto por duplo clique (file://), tenta http://127.0.0.1:8000, mas o login não funciona assim.
   Todo pedido que muda dados leva o cabeçalho "X-Prisma: 1" (proteção contra outros sites).

   Todas as funções devolvem Promise e, em caso de erro, rejeitam com Error(mensagem em português). */
window.Prisma = window.Prisma || {};
Prisma.api = (function () {
  var forcado = null;
  try { forcado = new URLSearchParams(location.search).get("api"); } catch (e) { /* segue */ }
  var base = forcado !== null ? forcado.replace(/\/$/, "")
    : location.protocol === "file:" ? "http://127.0.0.1:8000" : "";

  function mensagemDeErro(resposta, corpo) {
    var d = corpo && corpo.detail;
    if (typeof d === "string") return d;
    if (d && d.erro) return d.erro + (d.bloqueios ? " " + d.bloqueios.join(" ") : "");
    if (resposta.status === 429) return "Muitos pedidos seguidos. Espere um pouco e tente de novo.";
    if (Array.isArray(d) && d[0] && d[0].msg) return "Dados inválidos: " + d[0].msg;
    return "Algo deu errado (código " + resposta.status + ").";
  }

  function chamar(caminho, opcoes) {
    opcoes = opcoes || {};
    opcoes.credentials = "same-origin";
    if (opcoes.method && opcoes.method !== "GET") {
      opcoes.headers = opcoes.headers || {};
      opcoes.headers["X-Prisma"] = "1";
    }
    return fetch(base + caminho, opcoes).then(function (r) {
      if (r.status === 401) {          // sessão acabou: volta para a tela de entrada
        location.href = (location.pathname.indexOf("/painel/") >= 0 ? "../" : "") + "entrar.html";
        return new Promise(function () {});
      }
      return r.json().catch(function () { return null; }).then(function (corpo) {
        if (!r.ok) throw new Error(mensagemDeErro(r, corpo));
        return corpo;
      });
    }, function () {
      throw new Error("Não consegui falar com o servidor do PRISMA. Confira a internet e tente de novo.");
    });
  }

  function json(metodo, corpo) {
    return { method: metodo, headers: { "Content-Type": "application/json" }, body: JSON.stringify(corpo) };
  }

  return {
    base: base,
    url: function (caminho) { return base + caminho; },
    saude: function () { return chamar("/api/saude"); },
    opcoes: function () { return chamar("/api/opcoes"); },
    turmas: function () { return chamar("/api/turmas"); },
    novaTurma: function (nome) { return chamar("/api/turmas", json("POST", { nome: nome })); },
    novoAluno: function (turmaId, dados) { return chamar("/api/turmas/" + turmaId + "/alunos", json("POST", dados)); },
    mudarAluno: function (alunoId, dados) { return chamar("/api/alunos/" + alunoId, json("PATCH", dados)); },
    apagarAluno: function (alunoId) { return chamar("/api/alunos/" + alunoId, { method: "DELETE" }); },
    apagarMaterial: function (id) { return chamar("/api/materiais/" + id, { method: "DELETE" }); },
    adaptar: function (arquivo, turmaId, perfil) {
      var f = new FormData();
      f.append("arquivo", arquivo);
      f.append("turma_id", String(turmaId));
      if (perfil) f.append("perfil", JSON.stringify(perfil));
      return chamar("/api/adaptar", { method: "POST", body: f });
    },
    materiais: function () { return chamar("/api/materiais"); },
    material: function (id) { return chamar("/api/materiais/" + id); },
    descrever: function (id, imagens) { return chamar("/api/materiais/" + id + "/descricoes", json("POST", { imagens: imagens })); },
    aprovar: function (id) { return chamar("/api/materiais/" + id + "/aprovar", { method: "POST" }); },
    biblioteca: function () { return chamar("/api/biblioteca"); },
    avaliar: function (id, dados) { return chamar("/api/biblioteca/" + id + "/avaliacao", json("POST", dados)); },
    ocultar: function (id, sim) { return chamar("/api/biblioteca/" + id + "/ocultar", json("POST", { ocultar: sim })); },
    feedbacks: function () { return chamar("/api/feedbacks"); },
    escola: function () { return chamar("/api/escola"); }
  };
})();
