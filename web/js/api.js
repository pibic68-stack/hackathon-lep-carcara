/* Cliente da API do PRISMA (backend em Python). Documentação das rotas: backend/README.md.

   Onde está o servidor?
     - página aberta pelo próprio servidor (porta 8000)  -> mesmo endereço ("")
     - página aberta por duplo clique (file://) ou outro servidor -> http://127.0.0.1:8000
     - para forçar outro endereço: abrir a página com ?api=http://endereco:porta

   Todas as funções devolvem Promise e, em caso de erro, rejeitam com Error(mensagem em português). */
window.Prisma = window.Prisma || {};
Prisma.api = (function () {
  var forcado = null;
  try { forcado = new URLSearchParams(location.search).get("api"); } catch (e) { /* segue */ }
  var base = forcado !== null ? forcado.replace(/\/$/, "")
    : (location.protocol.indexOf("http") === 0 && location.port === "8000") ? "" : "http://127.0.0.1:8000";

  function mensagemDeErro(resposta, corpo) {
    var d = corpo && corpo.detail;
    if (typeof d === "string") return d;
    if (d && d.erro) return d.erro + (d.bloqueios ? " " + d.bloqueios.join(" ") : "");
    if (Array.isArray(d) && d[0] && d[0].msg) return "Dados inválidos: " + d[0].msg;
    return "Algo deu errado (código " + resposta.status + ").";
  }

  function chamar(caminho, opcoes) {
    return fetch(base + caminho, opcoes).then(function (r) {
      return r.json().catch(function () { return null; }).then(function (corpo) {
        if (!r.ok) throw new Error(mensagemDeErro(r, corpo));
        return corpo;
      });
    }, function () {
      throw new Error("Não consegui falar com o servidor do PRISMA. Ele está ligado? (No computador do time: python -m adaptador.api)");
    });
  }

  function json(metodo, corpo) {
    return { method: metodo, headers: { "Content-Type": "application/json" }, body: JSON.stringify(corpo) };
  }

  return {
    base: base,
    url: function (caminho) { return base + caminho; },
    saude: function () { return chamar("/api/saude"); },
    adaptar: function (arquivo, perfil) {
      var f = new FormData();
      f.append("arquivo", arquivo);
      if (perfil) f.append("perfil", JSON.stringify(perfil));
      return chamar("/api/adaptar", { method: "POST", body: f });
    },
    materiais: function () { return chamar("/api/materiais"); },
    material: function (id) { return chamar("/api/materiais/" + id); },
    descrever: function (id, imagens) { return chamar("/api/materiais/" + id + "/descricoes", json("POST", { imagens: imagens })); },
    aprovar: function (id) { return chamar("/api/materiais/" + id + "/aprovar", { method: "POST" }); },
    biblioteca: function () { return chamar("/api/biblioteca"); }
  };
})();
