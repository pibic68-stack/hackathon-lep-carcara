/* Painel de cada perfil. Ainda é só a "casca": mostra o que vai existir.
   O perfil vem de <body data-perfil="professor|familia|aluno">. */
(function () {
  var PAINEIS = {
    professor: {
      nome: "Prof.ª Coruja", avatar: "professor.png", ola: "Boa aula, Prof.ª Coruja!",
      cartoes: [
        ["users", "Minhas turmas", "5º ano A e 5º ano B. Perfis dos alunos (fictícios)."],
        ["upload", "Enviar material", "PDF, texto ou slide para adaptar."],
        ["check-double", "Aprovações", "Versões adaptadas esperando a sua revisão."],
        ["chart-bar", "Mini-checks", "Resultado das últimas aulas, por aluno."]
      ]
    },
    familia: {
      nome: "Família Urso", avatar: "familia.png", ola: "Olá, Família Urso!",
      cartoes: [
        ["book-open", "Guias da semana", "O que foi estudado e como ajudar em casa."],
        ["chat", "Recados da escola", "Mensagens da professora."],
        ["calendar", "Agenda", "Atividades e datas importantes."],
        ["heart", "Como meu filho aprende", "O perfil escrito pela escola, em linguagem simples."]
      ]
    },
    aluno: {
      nome: "Preguiça", avatar: "aluno.png", ola: "Oi, Preguiça! Bora estudar?",
      cartoes: [
        ["book-open", "Atividade de hoje", "O caminho da água · Ciências."],
        ["sliders", "Do meu jeito", "Letra maior, áudio ou passo a passo."],
        ["checklist", "Mini-check", "3 perguntinhas no fim da aula."],
        ["trophy", "Minhas conquistas", "Figurinhas por cada atividade feita."]
      ]
    }
  };

  document.addEventListener("DOMContentLoaded", function () {
    var p = PAINEIS[document.body.dataset.perfil];
    var alvo = document.getElementById("painel");
    if (!p || !alvo) return;
    alvo.innerHTML =
      '<div class="painel-cab"><img class="pixel" src="../assets/img/' + p.avatar + '" alt="">' +
      '<div><p class="rotulo">Painel · em construção</p><h1 tabindex="-1">' + p.ola + "</h1></div>" +
      '<a class="botao botao--secundario botao--pequeno" href="../entrar.html" id="sair">' + window.icone("login") + " Sair</a></div>" +
      '<p class="aviso">' + window.icone("info-box") + " <span><strong>Protótipo:</strong> estas áreas ainda vão ser construídas. O login de verdade entra aqui depois.</span></p><br>" +
      '<ul class="painel-grade">' + p.cartoes.map(function (c) {
        return '<li class="cartao"><h2>' + window.icone(c[0]) + c[1] + "</h2><p>" + c[2] + '</p><span class="etiqueta etiqueta--sol em-breve">em breve</span></li>';
      }).join("") + "</ul>";
    document.getElementById("sair").addEventListener("click", function () { Prisma.auth.sair(); });
  });
})();
