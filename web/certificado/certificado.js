/* =========================================================
   Certificado do mini curso PRISMA, para o site chamar.

   Uso (em qualquer página do site):
     <script src="../certificado/certificado.js"></script>
     PrismaCertificado.abrir({ papel: "prof", nome: "Ana Souza" });

   papel: "prof" | "fam" | "est"  (a trilha do mini curso usa esses mesmos códigos)
   nome:  nome de quem concluiu (vem do login)
   data:  "AAAA-MM-DD" (opcional, padrão hoje)

   Abre o modelo numa aba nova, já preenchido, e mostra a janela
   "Salvar em PDF" do navegador. Funciona sem internet e sem backend.
   Os dados vão depois do # da URL: não saem do computador.

   Com o backend ligado, dá para baixar o PDF direto (sem janela):
   ver gerar_pdf.py e LEIA-ME.md.
   ========================================================= */
(function () {
  "use strict";
  var script = document.currentScript;
  var PASTA = script ? new URL(".", script.src).href : "certificado/";

  function url(d, imprimir) {
    var p = new URLSearchParams();
    p.set("papel", d.papel || "prof");
    p.set("nome", (d.nome || "").trim());
    if (d.data) p.set("data", d.data);
    if (imprimir !== false) p.set("imprimir", "1");
    return PASTA + "modelo.html#" + p.toString();
  }

  window.PrismaCertificado = {
    /* endereço do modelo preenchido (útil para um link <a>) */
    url: url,
    /* abre o certificado numa aba nova e pede para salvar em PDF */
    abrir: function (d) {
      /* chame dentro de um clique, senão o navegador bloqueia a aba nova */
      var u = url(d, true), aba = window.open(u, "_blank");
      if (aba) { aba.opener = null; return true; }
      location.href = u; /* aba bloqueada: abre na mesma */
      return false;
    }
  };
})();
