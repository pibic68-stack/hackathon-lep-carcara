/* Desenha animações Lottie em baixa resolução para parecerem pixel art.

   <canvas class="pixel anim" data-anim="livros" data-res="120"></canvas>

   1. O lottie-web desenha a animação num canvas escondido 2x maior que data-res.
   2. Cada bloco de 2x2 vira um pixel só: a cor da paleta que mais aparece no bloco
      (assim as bordas suavizadas não viram "sujeira" de cores soltas).
      Se menos da metade do bloco é opaca, o pixel fica transparente.
   3. O canvas visível tem esse mesmo tamanho pequeno; o CSS amplia sem suavizar (image-rendering: pixelated).
   4. Toca a ~12 quadros por segundo, como um sprite de jogo antigo.
   Com "Pausar animações" ligado, mostra um quadro parado. */
(function () {
  var PALETA = ["#1E2235", "#3A3F5C", "#8A8FA8", "#D9D4C7", "#FBF7EE", "#FFFFFF",
    "#1F4F86", "#1F6FB2", "#3E9BEA", "#57B3F9", "#A6DCFD", "#CDEBFE",
    "#B5762A", "#E9A23B", "#FFC93C", "#FFE38A",
    "#A3401F", "#C4552B", "#FFAD60", "#FFD3A6",
    "#2E7D32", "#4A9A4B", "#7BD389", "#CDEFD2"].map(function (h) {
    return [parseInt(h.slice(1, 3), 16), parseInt(h.slice(3, 5), 16), parseInt(h.slice(5, 7), 16)];
  });
  var S = 2; // amostras por lado em cada pixel final
  var cache = {};
  function maisProxima(r, g, b) { // devolve o índice da cor na paleta
    var k = (r >> 3) << 10 | (g >> 3) << 5 | (b >> 3);
    if (cache[k] !== undefined) return cache[k];
    var melhor = 0, dist = 1e9;
    for (var i = 0; i < PALETA.length; i++) {
      var p = PALETA[i], dr = p[0] - r, dg = p[1] - g, db = p[2] - b;
      var d = dr * dr * 2 + dg * dg * 4 + db * db * 3;
      if (d < dist) { dist = d; melhor = i; }
    }
    return (cache[k] = melhor);
  }

  function iniciar(canvas) {
    var dados = window.ANIMACOES && window.ANIMACOES[canvas.dataset.anim];
    if (!dados || !window.lottie) { canvas.hidden = true; return; }
    var largura = +canvas.dataset.res || 120;
    var altura = Math.round(largura * dados.h / dados.w);
    var fps = +canvas.dataset.fps || 12;

    // palco escondido onde o lottie desenha
    var palco = document.createElement("div");
    palco.setAttribute("aria-hidden", "true");
    palco.style.cssText = "position:absolute;left:-9999px;top:0;width:" + largura * S + "px;height:" + altura * S + "px;overflow:hidden;";
    document.body.appendChild(palco);
    var anim = window.lottie.loadAnimation({
      container: palco, renderer: "canvas", loop: true, autoplay: false,
      animationData: JSON.parse(JSON.stringify(dados)),
      rendererSettings: { dpr: 1, clearCanvas: true, preserveAspectRatio: "xMidYMid meet" }
    });

    canvas.width = largura; canvas.height = altura;

    // amplia só por números inteiros (2x, 3x...): ampliação quebrada deixa pixels de larguras diferentes
    function ajustarEscala() {
      var caixa = canvas.parentElement.clientWidth * 0.9;
      var n = Math.max(1, Math.floor(Math.min(caixa, 420) / largura));
      canvas.style.width = largura * n + "px";
    }
    ajustarEscala();
    if ("ResizeObserver" in window) new ResizeObserver(ajustarEscala).observe(canvas.parentElement);
    var ctx = canvas.getContext("2d");
    var trab = document.createElement("canvas"); // canvas de trabalho no tamanho grande
    trab.width = largura * S; trab.height = altura * S;
    var tctx = trab.getContext("2d", { willReadFrequently: true });
    var saida = ctx.createImageData(largura, altura);
    var contagem = new Uint8Array(PALETA.length);
    var quadro = 0, ultimo = 0, visivel = true, pronto = false;

    function desenhar() {
      var origem = palco.querySelector("canvas");
      if (!origem) return;
      tctx.clearRect(0, 0, trab.width, trab.height);
      tctx.drawImage(origem, 0, 0, trab.width, trab.height);
      var d;
      try { d = tctx.getImageData(0, 0, trab.width, trab.height).data; } catch (e) { return; }
      var o = saida.data, W = trab.width, metade = (S * S) / 2;
      for (var y = 0; y < altura; y++) {
        for (var x = 0; x < largura; x++) {
          contagem.fill(0);
          var opacos = 0, melhor = 0, vezes = 0;
          for (var sy = 0; sy < S; sy++) {
            for (var sx = 0; sx < S; sx++) {
              var i = ((y * S + sy) * W + x * S + sx) * 4;
              if (d[i + 3] < 110) continue;
              opacos++;
              var c = maisProxima(d[i], d[i + 1], d[i + 2]);
              if (++contagem[c] > vezes) { vezes = contagem[c]; melhor = c; }
            }
          }
          var j = (y * largura + x) * 4;
          if (opacos < metade) { o[j + 3] = 0; continue; }
          var p = PALETA[melhor];
          o[j] = p[0]; o[j + 1] = p[1]; o[j + 2] = p[2]; o[j + 3] = 255;
        }
      }
      ctx.putImageData(saida, 0, 0);
    }

    function mostrar(n) {
      anim.goToAndStop(n, true);
      desenhar();
    }

    function laco(t) {
      requestAnimationFrame(laco);
      if (!pronto || !visivel) return;
      if (window.prismaMovimentoReduzido && window.prismaMovimentoReduzido()) return;
      if (t - ultimo < 1000 / fps) return;
      ultimo = t;
      quadro = (quadro + anim.frameRate / fps) % anim.totalFrames;
      mostrar(Math.floor(quadro));
    }

    anim.addEventListener("DOMLoaded", function () {
      pronto = true;
      quadro = Math.floor(anim.totalFrames * 0.3);
      mostrar(quadro); // quadro parado inicial (também é o que aparece com animações pausadas)
    });
    if ("IntersectionObserver" in window) {
      new IntersectionObserver(function (e) { visivel = e[0].isIntersecting; }).observe(canvas);
    }
    requestAnimationFrame(laco);
  }

  document.addEventListener("DOMContentLoaded", function () {
    document.querySelectorAll("canvas.anim[data-anim]").forEach(iniciar);
  });
})();
