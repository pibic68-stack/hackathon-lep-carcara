"""Junta os SVGs de assets/icones/ (Pixelarticons, licença MIT) em js/icones.js.

Os ícones viram texto dentro do JS para funcionarem abrindo o site com duplo clique
(o navegador bloqueia <use href="arquivo.svg#..."> em file://).
Uso: python ferramentas/gerar_icones.py   (rodar dentro de web/)
"""
import json
import re
from pathlib import Path

WEB = Path(__file__).resolve().parent.parent
icones = {}
for f in sorted((WEB / "assets" / "icones").glob("*.svg")):
    caminhos = re.findall(r'<path[^>]*\sd="([^"]+)"', f.read_text(encoding="utf-8"))
    icones[f.stem] = " ".join(caminhos)

js = """// Gerado por ferramentas/gerar_icones.py. Não editar à mão.
// Uso no HTML: <span data-icone="eye"></span>  (decorativo)
//              <span data-icone="eye" data-rotulo="Ver"></span>  (com nome para leitor de tela)
window.ICONES = %s;
window.icone = function (nome, rotulo) {
  var d = window.ICONES[nome] || "";
  var aria = rotulo ? 'role="img" aria-label="' + rotulo + '"' : 'aria-hidden="true" focusable="false"';
  return '<svg class="icone" viewBox="0 0 24 24" ' + aria + '><path fill="currentColor" d="' + d + '"/></svg>';
};
window.aplicarIcones = function (raiz) {
  (raiz || document).querySelectorAll("[data-icone]").forEach(function (el) {
    el.innerHTML = window.icone(el.dataset.icone, el.dataset.rotulo);
  });
};
document.addEventListener("DOMContentLoaded", function () { window.aplicarIcones(); });
""" % json.dumps(icones, indent=0, ensure_ascii=False)
(WEB / "js").mkdir(exist_ok=True)
(WEB / "js" / "icones.js").write_text(js, encoding="utf-8")
print(len(icones), "ícones")
