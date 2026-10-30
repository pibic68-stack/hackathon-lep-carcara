/* Dados de exemplo do protótipo. Todos os alunos são FICTÍCIOS (LGPD).
   Quando o backend existir, estes dados virão de lá e de docs/manual/regras.json. */
window.Prisma = window.Prisma || {};

/* ---------- necessidades do seletor ---------- */
Prisma.NECESSIDADES = [
  {
    id: "protanopia", grupo: "Daltonismo", nome: "Protanopia", icone: "colors-swatch",
    resumo: "Não percebe bem o vermelho. Vermelho e verde parecem a mesma cor.",
    aluno: "Aluno Fictício A · 5º ano",
    filtro: "url(#sim-protanopia)",
    adaptacoes: ["Cor + símbolo", "Paleta segura", "Linhas com padrão"],
    regras: [
      { id: "R-DALT-01", texto: "Toda informação em cor vem com símbolo ou palavra.", fonte: "WCAG 2.2 · 1.4.1" },
      { id: "R-DALT-02", texto: "Trocar vermelho e verde por azul e laranja (paleta Okabe-Ito).", fonte: "Okabe & Ito, 2008" },
      { id: "R-DALT-03", texto: "Diferenciar setas por padrão: contínua, tracejada, pontilhada.", fonte: "WCAG 2.2 · 1.4.1" },
      { id: "R-DALT-04", texto: "A pergunta não pede para reconhecer uma cor.", fonte: "DUA / CAST" }
    ]
  },
  {
    id: "deuteranopia", grupo: "Daltonismo", nome: "Deuteranopia", icone: "colors-swatch",
    resumo: "Não percebe bem o verde. É o tipo de daltonismo mais comum.",
    aluno: "Aluna Fictícia B · 5º ano",
    filtro: "url(#sim-deuteranopia)",
    adaptacoes: ["Cor + símbolo", "Paleta segura", "Linhas com padrão"],
    regras: [
      { id: "R-DALT-01", texto: "Toda informação em cor vem com símbolo ou palavra.", fonte: "WCAG 2.2 · 1.4.1" },
      { id: "R-DALT-02", texto: "Trocar vermelho e verde por azul e laranja (paleta Okabe-Ito).", fonte: "Okabe & Ito, 2008" },
      { id: "R-DALT-03", texto: "Diferenciar setas por padrão: contínua, tracejada, pontilhada.", fonte: "WCAG 2.2 · 1.4.1" },
      { id: "R-DALT-04", texto: "A pergunta não pede para reconhecer uma cor.", fonte: "DUA / CAST" }
    ]
  },
  {
    id: "tritanopia", grupo: "Daltonismo", nome: "Tritanopia", icone: "colors-swatch",
    resumo: "Confunde azul com verde e amarelo com rosa ou cinza.",
    aluno: "Aluno Fictício C · 5º ano",
    filtro: "url(#sim-tritanopia)",
    adaptacoes: ["Cor + símbolo", "Sem azul × amarelo", "Linhas com padrão"],
    regras: [
      { id: "R-DALT-01", texto: "Toda informação em cor vem com símbolo ou palavra.", fonte: "WCAG 2.2 · 1.4.1" },
      { id: "R-DALT-06", texto: "Evitar pares azul × verde e amarelo × rosa. Usar vermelho, preto e cinza.", fonte: "Okabe & Ito, 2008" },
      { id: "R-DALT-03", texto: "Diferenciar setas por padrão: contínua, tracejada, pontilhada.", fonte: "WCAG 2.2 · 1.4.1" },
      { id: "R-DALT-04", texto: "A pergunta não pede para reconhecer uma cor.", fonte: "DUA / CAST" }
    ]
  },
  {
    id: "acromatopsia", grupo: "Daltonismo", nome: "Acromatopsia", icone: "colors-swatch",
    resumo: "Não enxerga cores: vê tudo em tons de cinza. Costuma ter sensibilidade à luz.",
    aluno: "Aluna Fictícia D · 5º ano",
    filtro: "url(#sim-acromatopsia)",
    adaptacoes: ["Só formas e padrões", "Contraste de claro e escuro", "Rótulos em tudo"],
    regras: [
      { id: "R-DALT-01", texto: "Toda informação em cor vem com símbolo ou palavra.", fonte: "WCAG 2.2 · 1.4.1" },
      { id: "R-DALT-05", texto: "Elementos da figura com contraste de pelo menos 3:1 entre si.", fonte: "WCAG 2.2 · 1.4.11" },
      { id: "R-DALT-03", texto: "Diferenciar setas por padrão e espessura.", fonte: "WCAG 2.2 · 1.4.1" },
      { id: "R-DALT-07", texto: "Fundo sem brilho forte (creme no lugar de branco).", fonte: "a validar pela pesquisa" }
    ]
  },
  {
    id: "baixa-visao", grupo: "Visão", nome: "Baixa visão", icone: "zoom-in",
    resumo: "Enxerga pouco mesmo com óculos. Letra pequena e pouco contraste viram barreira.",
    aluno: "Aluno Fictício E · 5º ano",
    filtro: "url(#sim-baixa-visao)",
    adaptacoes: ["Fonte ≥ 24 px", "Alto contraste", "1 pergunta por página"],
    regras: [
      { id: "R-BV-01", texto: "Fonte sem serifa com pelo menos 24 px (18 pt).", fonte: "a validar pela pesquisa" },
      { id: "R-BV-02", texto: "Contraste de pelo menos 7:1 entre texto e fundo.", fonte: "WCAG 2.2 · 1.4.6" },
      { id: "R-BV-03", texto: "Menos elementos por página: uma pergunta de cada vez.", fonte: "a validar pela pesquisa" },
      { id: "R-BV-04", texto: "Figura ampliada, com setas grossas e rótulos grandes.", fonte: "WCAG 2.2 · 1.4.11" }
    ]
  },
  {
    id: "tea", grupo: "Aprendizagem", nome: "TEA", icone: "checklist",
    resumo: "Excesso de estímulos, instruções implícitas e linguagem figurada atrapalham.",
    aluno: "Aluna Fictícia F · 5º ano",
    filtro: null,
    adaptacoes: ["Instruções em etapas", "Linguagem literal", "Rotina visual"],
    regras: [
      { id: "R-TEA-01", texto: "Instruções em etapas numeradas, uma ação por frase.", fonte: "DUA / CAST" },
      { id: "R-TEA-02", texto: "Linguagem literal, sem metáforas nem expressões.", fonte: "a validar pela pesquisa" },
      { id: "R-TEA-03", texto: "Rotina visual: o que fazer agora, depois e quanto tempo leva.", fonte: "a validar pela pesquisa" },
      { id: "R-TEA-04", texto: "Página limpa, uma tarefa por vez.", fonte: "DUA / CAST" }
    ]
  }
];

Prisma.necessidadePorId = function (id) {
  return Prisma.NECESSIDADES.find(function (n) { return n.id === id; }) || Prisma.NECESSIDADES[0];
};

/* ---------- barreiras que a ferramenta marca na ficha original ---------- */
Prisma.BARREIRAS = {
  cor: [
    { alvo: "legenda", texto: "A legenda usa só cor: sem símbolo ou palavra na seta." },
    { alvo: "q1", texto: "A pergunta 1 pede para reconhecer uma cor." },
    { alvo: "figura", texto: "Setas vermelha e verde com a mesma espessura e o mesmo traço." }
  ],
  "baixa-visao": [
    { alvo: "texto", texto: "Letra pequena (14 px) e texto corrido." },
    { alvo: "figura", texto: "Figura pequena, setas finas, sem rótulo." },
    { alvo: "q1", texto: "Duas perguntas e a figura dividem a mesma página." }
  ],
  tea: [
    { alvo: "texto", texto: "Linguagem figurada: “grande viajante”, “despenca”, “vaivém”." },
    { alvo: "q1", texto: "Instruções implícitas: não diz quantas respostas marcar." },
    { alvo: "figura", texto: "Página cheia: sol, ondas e enfeites competem com o que importa." }
  ]
};
Prisma.barreirasDe = function (id) {
  if (id === "baixa-visao" || id === "tea") return Prisma.BARREIRAS[id];
  return Prisma.BARREIRAS.cor;
};

/* ---------- dica do guia da família (texto de exemplo) ---------- */
Prisma.dicaFamilia = function (n) {
  return {
    tea: "Em casa, mostre a rotina da tarefa antes de começar: “primeiro ler, depois olhar a figura, depois responder”.",
    "baixa-visao": "Em casa, estude num lugar bem iluminado e deixe a criança aproximar a folha o quanto precisar.",
    acromatopsia: "Em casa, prefira luz indireta e não peça para a criança dizer o nome das cores."
  }[n.id] || "Em casa, peça para a criança dizer o nome das setas, não a cor delas.";
};

/* ---------- as 5 etapas do diagrama ---------- */
Prisma.ETAPAS = [
  {
    id: "perfil", num: "1", nome: "Perfil", icone: "user",
    externos: ["Necessidades funcionais", "Preferências", "Observações"],
    titulo: "O professor descreve como o aluno aprende",
    texto: function (n) {
      return "Sem diagnóstico: só necessidades funcionais. Para " + n.aluno.split(" · ")[0] + ", o professor marcou: “" + n.resumo + "”";
    },
    detalhe: function (n) {
      return '<ul class="lista-check"><li>' + n.nome + "</li><li>Prefere atividades curtas</li><li>Observação: “senta na frente”</li></ul>";
    }
  },
  {
    id: "material", num: "2", nome: "Material", icone: "upload",
    externos: ["PDF ou texto", "Slide"],
    titulo: "Envia a aula como ela é",
    texto: function () { return "A ficha de Ciências “O caminho da água” entra do jeito que o professor já usa: PDF, texto ou slide."; },
    detalhe: function () {
      return '<p class="arquivo"><span data-icone="file"></span> ciclo-da-agua-5ano.pdf <span class="etiqueta etiqueta--ok"><span data-icone="check"></span> enviado</span></p>';
    }
  },
  {
    id: "adaptacao", num: "3", nome: "Adaptação", icone: "zap",
    externos: null, /* vem da necessidade escolhida */
    titulo: "Aplica as regras do Manual de Acessibilidade",
    texto: function (n) { return "Cada regra do Manual vira uma automação. Para " + n.nome.toLowerCase() + ", o PRISMA aplicou " + n.regras.length + " regras:"; },
    detalhe: function (n) {
      return '<ul class="lista-regras">' + n.regras.map(function (r) {
        return '<li><span class="etiqueta">' + r.id + "</span> " + r.texto + "</li>";
      }).join("") + "</ul>";
    }
  },
  {
    id: "guia", num: "4", nome: "Guia", icone: "book-open",
    externos: ["Guia do professor", "Guia da família"],
    titulo: "O professor aprova e o guia sai pronto",
    texto: function () { return "Nada chega ao aluno sem o OK do professor. Depois, a família recebe orientações em linguagem simples."; },
    detalhe: function (n) {
      return '<p class="balao"><strong>Guia da família:</strong> ' + Prisma.dicaFamilia(n) + '</p><p><span class="etiqueta etiqueta--ok"><span data-icone="check"></span> Aprovado pelo professor</span></p>';
    }
  },
  {
    id: "minicheck", num: "5", nome: "Mini-check", icone: "checklist",
    externos: ["3 perguntas", "Ajusta o perfil"],
    titulo: "Mede de novo: todo mundo aprendeu?",
    texto: function () { return "Três perguntas rápidas no fim da aula. Se o aluno ainda tropeçar, o perfil é ajustado e o ciclo recomeça."; },
    detalhe: function () {
      return '<div class="minicheck"><span class="mc ok">✓ 1</span><span class="mc ok">✓ 2</span><span class="mc nao">✗ 3</span></div><p class="suave">2 de 3 certas · sugestão: manter a adaptação e revisar “condensação”.</p>';
    }
  }
];
