/* Motor das cenas: liga cada animação à frase da narração.

   Na cena:  <script>window.BLOCO = 3; window.SOBRA = 0.6;</script>
   Num elemento:  data-f="2"        a animação começa quando a frase 2 começa
                  data-f="2+0.4"    0,4 s depois do início da frase 2
                  data-f="2>"       quando a frase 2 termina
                  data-f="@12.5"    no segundo 12,5 da cena
                  data-f="1, 4"     duas animações (entra na frase 1, sai na frase 4)
   window.aoTempo(t) é chamado a cada quadro (para contadores etc.).
   Sem tempos.json, usa tempos de reserva (3 s por frase). */
(function () {
  function frases() {
    var b = window.TEMPOS && window.TEMPOS[String(window.BLOCO)];
    return b ? b.frases : null;
  }
  window.F = function (i) {
    var fr = frases();
    if (!fr) return i * 3;
    return fr[Math.min(i, fr.length - 1)].t0;
  };
  window.FIM = function (i) {
    var fr = frases();
    if (!fr) return i * 3 + 2.5;
    return fr[Math.min(i, fr.length - 1)].t1;
  };
  function quando(txt) {
    txt = txt.trim();
    if (txt[0] === "@") return parseFloat(txt.slice(1));
    var m = txt.match(/^(\d+)(>)?([+-][\d.]+)?$/);
    if (!m) return 0;
    var base = m[2] ? window.FIM(+m[1]) : window.F(+m[1]);
    return base + (m[3] ? parseFloat(m[3]) : 0);
  }
  window.quando = quando;
  window.pronto = function () {
    var b = window.TEMPOS && window.TEMPOS[String(window.BLOCO)];
    window.DURACAO = window.DURACAO || ((b ? b.duracao : 30) + (window.SOBRA || 0.5));
    document.querySelectorAll("[data-f]").forEach(function (el) {
      el.style.animationDelay = el.dataset.f.split(",").map(function (p) { return quando(p) + "s"; }).join(", ");
    });
    if (window.montar) window.montar();
  };
  if (window.ALFA) document.documentElement.classList.add("alfa");
})();

/* contador: escreve no elemento o número de a até b entre t0 e t1 */
function contar(el, t, t0, t1, a, b, fmt) {
  var p = Math.max(0, Math.min(1, (t - t0) / (t1 - t0)));
  p = 1 - Math.pow(1 - p, 3);
  el.textContent = fmt(a + (b - a) * p);
}
