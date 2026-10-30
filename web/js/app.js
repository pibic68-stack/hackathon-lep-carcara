/* Trama · demonstração interativa
   Tudo aqui é conteúdo de exemplo (alunos fictícios). Na versão final, as adaptações vêm do backend
   a partir das regras de docs/manual/regras.json, e o professor aprova antes de chegar ao aluno. */
(() => {
  'use strict';

  /* ---------- Símbolos (cor sempre com símbolo ou palavra) ---------- */
  const FORMAS = {
    circulo: '<circle cx="10" cy="10" r="8"/>',
    quadrado: '<rect x="2" y="2" width="16" height="16" rx="2"/>',
    triangulo: '<path d="M10 2 L18.5 17.5 H1.5 Z"/>',
    losango: '<path d="M10 1 L19 10 L10 19 L1 10 Z"/>',
    hexagono: '<path d="M5.5 2 H14.5 L19 10 L14.5 18 H5.5 L1 10 Z"/>',
    cruz: '<path d="M7 2 h6 v5 h5 v6 h-5 v5 H7 v-5 H2 V7 h5 z"/>',
    estrela: '<path d="M10 1.5 L12.4 7.3 L18.6 7.7 L13.8 11.7 L15.4 17.8 L10 14.5 L4.6 17.8 L6.2 11.7 L1.4 7.7 L7.6 7.3 Z"/>',
    anel: '<circle cx="10" cy="10" r="6.5" fill="none" stroke="currentColor" stroke-width="3"/>'
  };
  const forma = (nome, cor) =>
    `<svg class="forma" viewBox="0 0 20 20" aria-hidden="true" focusable="false"${cor ? ` style="color:${cor}"` : ''}>${FORMAS[nome]}</svg>`;
  const selo = (conteudo) => `<span class="selo">${conteudo}</span>`;

  /* ---------- Necessidades (palavras do dia a dia, nunca diagnóstico) ---------- */
  const NECESSIDADES = [
    { id: 'cores', titulo: 'Cores difíceis de distinguir' },
    { id: 'leitura', titulo: 'Leitura cansativa' },
    { id: 'letra', titulo: 'Letra pequena cansa' },
    { id: 'foco', titulo: 'Muita coisa na página' }
  ];
  const REGRAS = {
    cores: ['R-DALT-01', 'Cor sempre com símbolo, padrão ou palavra'],
    leitura: ['R-DISL-01', 'Frases curtas, fonte sem serifa e espaçamento maior'],
    letra: ['R-BVIS-01', 'Letra ampliada e alto contraste'],
    foco: ['R-FOCO-01', 'Uma etapa por vez, com a ordem marcada']
  };
  const BARREIRAS = {
    cores: { txt: 'a resposta dependia só da cor, que nem todos os alunos distinguem.', btn: 'Aplicar “cores difíceis de distinguir”' },
    leitura: { txt: 'o texto estava longo e denso para ler.', btn: 'Aplicar “leitura cansativa”' },
    foco: { txt: 'havia várias informações juntas e a ordem não estava marcada.', btn: 'Aplicar “muita coisa na página”' }
  };

  /* ---------- Disciplinas do tema “A água que usamos” ---------- */
  const DISCIPLINAS = [
    {
      id: 'mat', nome: 'Matemática', forma: 'circulo', cor: '#0072B2', visual: 'barras', bar: 'cores',
      titulo: 'Quantos litros por dia?',
      texto: 'Uma família gasta, em média, uma quantidade de água que varia conforme os hábitos de cada casa. Ao comparar o consumo diário de três famílias, podemos perceber quem economiza mais e quanto a diferença representa.',
      curto: ['Cada casa gasta uma quantidade de água.', 'O gasto muda com os hábitos da família.', 'Aqui estão três famílias.', 'Vamos comparar quanto cada uma usa por dia.'],
      ativ: 'Compare a barra vermelha com a verde. Quantos litros por dia a família da barra verde usa a menos?',
      ativAd: 'Compare a barra com listras com a barra lisa. Quantos litros por dia a família da barra lisa usa a menos?',
      opcoes: [{ t: '70 litros', ok: true }, { t: '30 litros' }, { t: '150 litros' }]
    },
    {
      id: 'geo', nome: 'Geografia', forma: 'quadrado', cor: '#009E73', visual: 'mapa', bar: 'cores',
      titulo: 'Para onde vai a chuva?',
      texto: 'Quando chove, a água escorre pelo terreno até chegar ao rio. Em áreas de mata, boa parte dela entra no solo; em áreas muito construídas, ela corre rápido e pode causar enchentes.',
      curto: ['A chuva cai no terreno.', 'Parte da água entra no solo.', 'Outra parte escorre até o rio.', 'Na cidade, a água escorre mais rápido.'],
      ativ: 'Olhe as áreas verdes do mapa. Em qual tipo de área a água da chuva entra melhor no solo?',
      ativAd: 'Olhe as áreas marcadas com M no mapa. Em qual tipo de área a água da chuva entra melhor no solo?',
      opcoes: [{ t: 'Mata', ok: true }, { t: 'Cidade' }, { t: 'Plantação' }]
    },
    {
      id: 'cie', nome: 'Ciências', forma: 'triangulo', cor: '#D55E00', visual: 'ciclo', bar: 'foco',
      titulo: 'O caminho da água',
      texto: 'A água dos rios e do mar esquenta com o calor do Sol e sobe como vapor. No alto, o vapor esfria, vira gotas e forma as nuvens. Depois, as gotas caem como chuva e o ciclo recomeça.',
      curto: ['O Sol esquenta a água.', 'A água sobe como vapor.', 'No alto, o vapor esfria e forma nuvens.', 'A chuva cai e o ciclo recomeça.'],
      ativ: 'Em qual fase o vapor esfria e vira gotinhas de água?',
      opcoes: [{ t: 'Condensação', ok: true }, { t: 'Evaporação' }, { t: 'Precipitação' }]
    },
    {
      id: 'his', nome: 'História', forma: 'losango', cor: '#E69F00', visual: 'pares', bar: 'cores',
      titulo: 'Rios e as primeiras cidades',
      texto: 'Muitas das primeiras grandes civilizações surgiram perto de rios, porque a água permitia plantar, beber e transportar pessoas e mercadorias. O Nilo, no Egito, e o Tigre e o Eufrates, na Mesopotâmia, são exemplos.',
      curto: ['Muitas civilizações nasceram perto de rios.', 'A água servia para beber e plantar.', 'Também servia para transportar coisas.', 'O rio Nilo ficava no Egito.'],
      ativ: 'Cada rio tem a mesma cor da civilização que nasceu perto dele. Qual civilização nasceu perto do rio Nilo?',
      ativAd: 'Cada rio tem o mesmo símbolo da civilização que nasceu perto dele. Qual civilização nasceu perto do rio Nilo?',
      opcoes: [{ t: 'Egito', ok: true }, { t: 'Mesopotâmia' }, { t: 'Vale do Indo' }]
    },
    {
      id: 'por', nome: 'Português', forma: 'hexagono', cor: '#CC79A7', visual: 'frase', bar: 'leitura',
      titulo: 'Lendo uma frase sobre a chuva',
      texto: 'Na gramática, cada palavra de uma frase tem uma função: os substantivos nomeiam seres e coisas, os verbos indicam ações e os advérbios dizem como a ação acontece.',
      curto: ['Cada palavra tem uma função na frase.', 'O substantivo dá nome às coisas.', 'O verbo mostra uma ação.', 'O advérbio diz como a ação acontece.'],
      ativ: 'Qual palavra está em vermelho? Ela mostra uma ação.',
      ativAd: 'Qual palavra está marcada com V? Ela mostra uma ação.',
      opcoes: [{ t: 'enche', ok: true }, { t: 'chuva' }, { t: 'devagar' }]
    },
    {
      id: 'mus', nome: 'Música', forma: 'cruz', cor: '#56B4E9', visual: 'tempos', bar: 'cores',
      titulo: 'O ritmo da chuva',
      texto: 'A chuva fraca e a chuva forte têm ritmos diferentes. Na música, chamamos de pulso a batida regular que sentimos, e alguns tempos são mais fortes do que outros.',
      curto: ['A chuva tem ritmo.', 'O pulso é a batida regular.', 'Alguns tempos são fortes.', 'Outros tempos são fracos.'],
      ativ: 'Bata palmas nos tempos vermelhos e estale os dedos nos verdes. Em quais números você bateu palmas?',
      ativAd: 'Bata palmas nos tempos altos (●) e estale os dedos nos baixos (○). Em quais números você bateu palmas?',
      opcoes: [{ t: '1 e 5', ok: true }, { t: 'Em todos' }, { t: 'Só no 8' }]
    }
  ];

  /* ---------- Visuais ---------- */
  const NIVEIS = {
    alta: { cor: '#D6342C', pad: 'listras', f: 'triangulo', palavra: 'gasto alto' },
    media: { cor: '#E8B800', pad: 'pontos', f: 'quadrado', palavra: 'gasto médio' },
    baixa: { cor: '#1E9E52', pad: 'liso', f: 'circulo', palavra: 'gasto baixo' }
  };
  function legendaNiveis(a) {
    return `<ul class="legenda">${Object.values(NIVEIS).map((n) =>
      `<li><span class="amostra ${a.cores ? 'pad-' + n.pad : ''}" style="background-color:${n.cor}"></span>${a.cores ? selo(forma(n.f)) : ''}${n.palavra}</li>`).join('')}</ul>`;
  }
  function visualBarras(a) {
    const H = 170, MAX = 150;
    const itens = [['Família A', 150, 'alta'], ['Família B', 80, 'baixa'], ['Família C', 110, 'media']];
    const cols = itens.map(([nome, v, nivel]) => {
      const n = NIVEIS[nivel];
      const dentro = a.cores ? `${selo(forma(n.f))}${selo(v + ' L')}` : '';
      return `<div class="barra-col"><div class="pilha"><div class="barra ${a.cores ? 'pad-' + n.pad : ''}" style="height:${Math.round(v / MAX * H)}px;background-color:${n.cor}">${dentro}</div></div><span class="nome">${nome}</span>${a.cores ? `<small>${n.palavra}</small>` : ''}</div>`;
    }).join('');
    return `<div><div class="grafico" role="img" aria-label="Gráfico de barras: consumo diário de água de três famílias, em litros"><div class="eixo" aria-hidden="true"><span>150</span><span>100</span><span>50</span><span>0</span></div><div class="barras">${cols}</div></div>${legendaNiveis(a)}</div>`;
  }

  const USOS = {
    M: { nome: 'mata', cor: '#1E9E52', pad: 'pontos' },
    C: { nome: 'cidade', cor: '#D6342C', pad: 'xadrez' },
    P: { nome: 'plantação', cor: '#E8B800', pad: 'listras' },
    R: { nome: 'rio', cor: '#2F6BDB', pad: 'ondas' }
  };
  const MAPA = ['MMRP', 'MRRP', 'CRCP', 'CCRP'];
  function visualMapa(a) {
    const celulas = MAPA.join('').split('').map((k) => {
      const u = USOS[k];
      return `<div class="celula ${a.cores ? 'pad-' + u.pad : ''}" style="background-color:${u.cor}">${a.cores ? selo(k) : ''}</div>`;
    }).join('');
    const leg = Object.entries(USOS).map(([k, u]) =>
      `<li><span class="amostra ${a.cores ? 'pad-' + u.pad : ''}" style="background-color:${u.cor}"></span>${a.cores ? selo(k) : ''}${u.nome}</li>`).join('');
    return `<div><div class="mapa" role="img" aria-label="Mapa de quatro por quatro quadrados com mata, cidade, plantação e um rio">${celulas}</div><ul class="legenda">${leg}</ul></div>`;
  }

  const FASES = [
    { n: 'Evaporação', cor: '#F7C873', f: 'triangulo' },
    { n: 'Condensação', cor: '#A8C7F0', f: 'quadrado' },
    { n: 'Precipitação', cor: '#7FD0F0', f: 'circulo' },
    { n: 'Escoamento', cor: '#A5DEC4', f: 'losango' }
  ];
  function visualCiclo(a) {
    const partes = FASES.map((f, i) => {
      const num = a.foco ? selo(i + 1) : '';
      const sim = a.cores ? selo(forma(f.f)) : '';
      const seta = a.foco && i < FASES.length - 1 ? '<span class="seta" aria-hidden="true">›</span>' : '';
      return `<span class="fase" style="background-color:${f.cor}">${num}${sim}${f.n}</span>${seta}`;
    }).join('');
    return `<div class="fluxo" role="group" aria-label="Fases do ciclo da água">${partes}</div>`;
  }

  const PARES = {
    rios: [
      { n: 'Nilo', cor: '#E69F00', f: 'triangulo' },
      { n: 'Tigre e Eufrates', cor: '#CC79A7', f: 'quadrado' },
      { n: 'Indo', cor: '#009E73', f: 'circulo' }
    ],
    civs: [
      { n: 'Mesopotâmia', cor: '#CC79A7', f: 'quadrado' },
      { n: 'Vale do Indo', cor: '#009E73', f: 'circulo' },
      { n: 'Egito', cor: '#E69F00', f: 'triangulo' }
    ]
  };
  function visualPares(a) {
    const col = (titulo, lista) => `<div><p class="col-titulo">${titulo}</p><ul>${lista.map((p) =>
      `<li class="item-par" style="background-color:${p.cor}">${a.cores ? selo(forma(p.f)) : ''}${p.n}</li>`).join('')}</ul></div>`;
    return `<div class="pares">${col('Rios', PARES.rios)}${col('Civilizações', PARES.civs)}</div>`;
  }

  const PALAVRAS = [
    ['A', 'art', ''], ['chuva', 'subst', 'S'], ['enche', 'verbo', 'V'],
    ['o', 'art', ''], ['rio', 'subst', 'S'], ['devagar', 'adv', 'Adv']
  ];
  const SUBLINHA = { subst: 'sub-solido', verbo: 'sub-onda', adv: 'sub-ponto', art: '' };
  function visualFrase(a) {
    const frase = PALAVRAS.map(([p, tipo, tag]) =>
      `<span class="palavra"><span class="tp-${tipo} ${a.cores ? SUBLINHA[tipo] : ''}">${p}</span><small>${a.cores ? tag : ''}</small></span>`).join('');
    const leg = a.cores
      ? `<ul class="legenda"><li>${selo('S')}substantivo (linha reta)</li><li>${selo('V')}verbo (linha ondulada)</li><li>${selo('Adv')}advérbio (linha pontilhada)</li></ul>`
      : `<ul class="legenda"><li class="tp-subst">substantivo</li><li class="tp-verbo">verbo</li><li class="tp-adv">advérbio</li></ul>`;
    return `<div><p class="frase" aria-label="A chuva enche o rio devagar.">${frase}</p>${leg}</div>`;
  }

  function visualTempos(a) {
    const caixas = Array.from({ length: 8 }, (_, i) => {
      const forte = i % 4 === 0;
      const cor = forte ? '#D6342C' : '#1E9E52';
      const alt = a.cores ? (forte ? 96 : 48) : 60;
      const pad = a.cores ? (forte ? 'pad-listras' : 'pad-pontos') : '';
      const marca = a.cores ? selo(forma(forte ? 'circulo' : 'anel')) : '';
      return `<div class="tempo"><div class="caixa-tempo ${pad}" style="height:${alt}px;background-color:${cor}">${marca}</div><span class="n">${i + 1}</span></div>`;
    }).join('');
    const leg = a.cores
      ? `<ul class="legenda"><li>${selo(forma('circulo'))}tempo forte (alto)</li><li>${selo(forma('anel'))}tempo fraco (baixo)</li></ul>`
      : `<ul class="legenda"><li><span class="amostra" style="background-color:#D6342C"></span>tempo forte</li><li><span class="amostra" style="background-color:#1E9E52"></span>tempo fraco</li></ul>`;
    return `<div><div class="tempos" role="img" aria-label="Oito tempos numerados de 1 a 8, com tempo forte no 1 e no 5">${caixas}</div>${leg}</div>`;
  }
  const VISUAIS = { barras: visualBarras, mapa: visualMapa, ciclo: visualCiclo, pares: visualPares, frase: visualFrase, tempos: visualTempos };

  /* ---------- Estado ---------- */
  const estado = {
    aba: 'mat', perfil: new Set(['cores', 'leitura']), modo: 'adaptado',
    simular: false, aprovado: false, passo: 0, resp: null, msg: ''
  };
  const ativos = () => {
    const a = { cores: false, leitura: false, letra: false, foco: false };
    if (estado.modo === 'adaptado') estado.perfil.forEach((k) => { a[k] = true; });
    return a;
  };
  const disciplinaAtual = () => DISCIPLINAS.find((d) => d.id === estado.aba);

  const janela = document.getElementById('janela');
  const elPerfil = document.getElementById('perfil');
  const elRegras = document.getElementById('regras');
  const elAbas = document.getElementById('abas');
  const elPalco = document.getElementById('palco');
  const elRodape = document.getElementById('rodape-janela');
  const anuncio = document.createElement('div');
  anuncio.className = 'so-leitor';
  anuncio.setAttribute('aria-live', 'polite');
  janela.appendChild(anuncio);
  const avisar = (t) => { anuncio.textContent = ''; setTimeout(() => { anuncio.textContent = t; }, 40); };

  /* ---------- Renderização ---------- */
  function montarPerfil() {
    elPerfil.innerHTML = NECESSIDADES.map((n) =>
      `<button type="button" class="necessidade" data-acao="neces" data-id="${n.id}" data-foco="n-${n.id}" aria-pressed="false">
        <span class="caixa"><svg viewBox="0 0 16 16" aria-hidden="true"><path d="M3 8.5 L6.5 12 L13 4.5"/></svg></span>
        <strong>${n.titulo}</strong>
      </button>`).join('');
  }
  function atualizarPerfil() {
    elPerfil.querySelectorAll('.necessidade').forEach((b) => {
      b.setAttribute('aria-pressed', String(estado.perfil.has(b.dataset.id)));
    });
  }
  function renderRegras() {
    const a = ativos();
    const lista = Object.keys(REGRAS).filter((k) => a[k]);
    elRegras.innerHTML = (lista.length
      ? lista.map((k) => `<li><b>${REGRAS[k][0]}</b>${REGRAS[k][1]}</li>`).join('')
      : '<li class="vazio">Nenhuma regra aplicada.</li>');
  }
  function renderAbas() {
    elAbas.innerHTML = DISCIPLINAS.map((d) => {
      const sel = d.id === estado.aba;
      return `<button type="button" class="aba" role="tab" id="aba-${d.id}" aria-selected="${sel}" aria-controls="palco" tabindex="${sel ? 0 : -1}" data-acao="aba" data-id="${d.id}" data-foco="aba-${d.id}">${forma(d.forma, d.cor)}${d.nome}</button>`;
    }).join('');
    elPalco.setAttribute('aria-labelledby', 'aba-' + estado.aba);
  }
  function blocoTexto(d, a) {
    if (a.leitura) return `<div class="texto-leitura">${d.curto.map((s) => `<p>${s}</p>`).join('')}</div>`;
    return `<p class="texto texto-original">${d.texto}</p>`;
  }
  function retorno(d, a) {
    if (estado.msg) return `<div class="retorno ok"><strong>${estado.msg}</strong></div>`;
    if (estado.resp === null) return '';
    if (d.opcoes[estado.resp].ok) {
      return '<div class="retorno ok"><strong>Resposta esperada.</strong>Nenhum sinal de barreira nesta atividade.</div>';
    }
    const b = BARREIRAS[d.bar];
    const extra = a[d.bar]
      ? ' Essa adaptação já está aplicada, então o professor pode investigar outras causas.'
      : `<br><button type="button" class="btn-mini" data-acao="aplicar" data-foco="aplicar">${b.btn}</button>`;
    return `<div class="retorno dif"><strong>Resposta diferente da esperada.</strong>É um sinal para o professor, não um diagnóstico: ${b.txt}${extra}</div>`;
  }
  function blocoAtividade(d, a) {
    const txt = a.cores && d.ativAd ? d.ativAd : d.ativ;
    return `<div class="atividade"><p class="pergunta">${txt}</p>
      <div class="opcoes" role="group" aria-label="Opções de resposta">${d.opcoes.map((o, i) =>
        `<button type="button" class="opcao" data-acao="resp" data-i="${i}" data-foco="op-${i}" aria-pressed="${estado.resp === i}">${o.t}</button>`).join('')}</div>
      ${retorno(d, a)}</div>`;
  }
  const ETAPAS = ['Leia', 'Observe', 'Responda'];
  function renderPalco() {
    const d = disciplinaAtual();
    const a = ativos();
    const blocos = [blocoTexto(d, a), `<div class="visual">${VISUAIS[d.visual](a)}</div>`, blocoAtividade(d, a)];
    let html = `<h3>${d.titulo}</h3>`;
    if (a.foco) {
      const i = estado.passo;
      html += `<div class="etapa-barra"><p>Etapa ${i + 1} de 3: ${ETAPAS[i]}</p><div>
        <button type="button" class="btn-mini fantasma" data-acao="voltar" data-foco="voltar" ${i === 0 ? 'disabled' : ''}>Voltar</button>
        <button type="button" class="btn-mini" data-acao="proxima" data-foco="proxima" ${i === 2 ? 'disabled' : ''}>Próxima etapa</button></div></div>`;
      html += blocos[i];
    } else {
      html += blocos.join('');
    }
    elPalco.innerHTML = html;
    elPalco.classList.toggle('simulando', estado.simular);
  }
  function renderRodape() {
    const a = ativos();
    const temPerfil = estado.perfil.size > 0;
    let status;
    if (estado.modo === 'original') status = '<span class="selo-estado">Material original, sem adaptação</span>';
    else if (!temPerfil) status = '<span class="selo-estado">Nenhuma necessidade marcada</span>';
    else if (estado.aprovado) status = '<span class="selo-estado"><svg viewBox="0 0 16 16" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M3 8.5 L6.5 12 L13 4.5"/></svg>Aprovado pelo professor</span>';
    else status = '<span class="selo-estado">Aguardando aprovação do professor</span><button type="button" class="btn-mini" data-acao="aprovar" data-foco="aprovar">Aprovar para o aluno</button>';
    elRodape.innerHTML = `
      <div class="segmento" role="group" aria-label="Versão do material">
        <button type="button" data-acao="modo" data-m="original" data-foco="m-original" aria-pressed="${estado.modo === 'original'}">Material original</button>
        <button type="button" data-acao="modo" data-m="adaptado" data-foco="m-adaptado" aria-pressed="${estado.modo === 'adaptado'}">Material adaptado</button>
      </div>
      <label class="troca"><input type="checkbox" data-acao="simular" data-foco="simular" ${estado.simular ? 'checked' : ''}>Ver como alguém com daltonismo vê</label>
      <div class="estado">${status}</div>`;
    janela.classList.toggle('contraste', a.letra);
    janela.style.setProperty('--esc', a.letra ? '1.3' : '1');
  }
  function render() {
    const foco = document.activeElement && document.activeElement.dataset ? document.activeElement.dataset.foco : null;
    atualizarPerfil(); renderRegras(); renderAbas(); renderPalco(); renderRodape();
    if (foco) {
      const alvo = janela.querySelector(`[data-foco="${foco}"]:not([disabled])`);
      if (alvo) alvo.focus({ preventScroll: true });
    }
  }
  const zerarAprovacao = () => { estado.aprovado = false; };

  /* ---------- Eventos da janela ---------- */
  function mudarAba(id) {
    estado.aba = id; estado.passo = 0; estado.resp = null; estado.msg = ''; zerarAprovacao();
    elPalco.style.animation = 'none'; void elPalco.offsetWidth; elPalco.style.animation = '';
    render();
  }
  janela.addEventListener('click', (e) => {
    const el = e.target.closest('[data-acao]');
    if (!el) return;
    switch (el.dataset.acao) {
      case 'aba': mudarAba(el.dataset.id); break;
      case 'neces': {
        const id = el.dataset.id;
        if (estado.perfil.has(id)) estado.perfil.delete(id); else estado.perfil.add(id);
        if (estado.modo === 'original') estado.modo = 'adaptado';
        estado.passo = 0; estado.msg = ''; zerarAprovacao(); render();
        break;
      }
      case 'modo': estado.modo = el.dataset.m; estado.passo = 0; estado.msg = ''; zerarAprovacao(); render(); break;
      case 'simular': estado.simular = el.checked; render(); break;
      case 'aprovar': estado.aprovado = true; render(); avisar('Material aprovado pelo professor.'); break;
      case 'resp': {
        estado.resp = Number(el.dataset.i); estado.msg = ''; render();
        const d = disciplinaAtual();
        avisar(d.opcoes[estado.resp].ok ? 'Resposta esperada.' : 'Resposta diferente da esperada. Há um sinal para o professor.');
        break;
      }
      case 'aplicar': {
        estado.perfil.add(disciplinaAtual().bar); estado.modo = 'adaptado'; estado.passo = 0;
        estado.resp = null; estado.msg = 'Adaptação aplicada. Tente a atividade de novo.'; zerarAprovacao(); render();
        avisar(estado.msg);
        break;
      }
      case 'proxima': estado.passo = Math.min(2, estado.passo + 1); render(); break;
      case 'voltar': estado.passo = Math.max(0, estado.passo - 1); render(); break;
      default: break;
    }
  });
  elAbas.addEventListener('keydown', (e) => {
    const ids = DISCIPLINAS.map((d) => d.id);
    let i = ids.indexOf(estado.aba);
    if (e.key === 'ArrowRight') i = (i + 1) % ids.length;
    else if (e.key === 'ArrowLeft') i = (i - 1 + ids.length) % ids.length;
    else if (e.key === 'Home') i = 0;
    else if (e.key === 'End') i = ids.length - 1;
    else return;
    e.preventDefault();
    mudarAba(ids[i]);
    const alvo = document.getElementById('aba-' + ids[i]);
    if (alvo) alvo.focus();
  });

  montarPerfil();
  render();
})();
