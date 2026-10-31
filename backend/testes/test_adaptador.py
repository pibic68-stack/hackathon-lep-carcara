"""Rodar (de dentro de backend/):  python -m unittest discover -s testes -v"""
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from adaptador import cache, pipeline, regras, renderizador, transformacoes as t
from adaptador.modelo import Bloco, Documento

EXEMPLOS = Path(__file__).resolve().parents[1] / "exemplos"


class TestCorComSimbolo(unittest.TestCase):
    """Decisão do time (31/10): a legenda entra quando o material USA cor, não quando aparece a palavra."""

    def test_texto_colorido_ganha_legenda(self):
        # o leitor já marcou o trecho colorido com a forma da cor
        d = Documento("x", [Bloco("paragrafo", texto="As barras em vermelho (▲) são as meninas.")], cores=["vermelho"])
        r = t.cor_com_simbolo(d)
        self.assertEqual(r.blocos[0].tipo, "quadro")  # legenda no topo
        self.assertEqual(r.blocos[0].itens, ["▲ = trecho que no original estava em vermelho"])

    def test_palavra_de_cor_sem_cor_nao_ganha_legenda(self):
        d = Documento("x", [Bloco("paragrafo", texto="Pinte de azul e circule em vermelho.")])
        r = t.cor_com_simbolo(d)
        self.assertEqual(r.blocos, d.blocos)
        self.assertNotIn("(■)", r.blocos[0].texto)

    def test_imagem_colorida_vira_pendencia(self):
        d = Documento("x", [Bloco("imagem", arquivo="imagens/img-001.png")], figuras_coloridas=["imagens/img-001.png"])
        r = t.cor_com_simbolo(d)
        self.assertTrue(r.blocos[0].colorida)
        self.assertTrue(any(p.startswith("P1.2") for p in r.pendencias))

    def test_sem_cor_nao_muda_nada(self):
        d = Documento("x", [Bloco("paragrafo", texto="A água evapora.")])
        self.assertEqual(t.cor_com_simbolo(d).blocos, d.blocos)


class TestEtapas(unittest.TestCase):
    def test_quebra_instrucao_longa(self):
        d = Documento("x", [Bloco("paragrafo", texto=(
            "Leia o texto e depois responda às perguntas. Em seguida, desenhe o caminho da água "
            "e, por fim, mostre ao professor."))])
        r = t.instrucoes_em_etapas(d)
        self.assertEqual(r.blocos[0].tipo, "etapas")
        self.assertEqual(r.blocos[0].itens, [
            "Leia o texto", "Responda às perguntas",
            "Desenhe o caminho da água", "Mostre ao professor"])

    def test_virgula_antes_de_verbo_separa(self):
        d = Documento("x", [Bloco("paragrafo", texto=(
            "Desenhe o caminho da água, circule em vermelho o vapor e, por fim, mostre ao professor."))])
        self.assertEqual(t.instrucoes_em_etapas(d).blocos[0].itens, [
            "Desenhe o caminho da água", "Circule em vermelho o vapor", "Mostre ao professor"])

    def test_texto_informativo_nao_vira_etapa(self):
        d = Documento("x", [Bloco("paragrafo", texto="A água evapora e depois forma nuvens.")])
        self.assertEqual(t.instrucoes_em_etapas(d).blocos[0].tipo, "paragrafo")

    def test_hoje_vamos_respeita_o_maximo_do_manual(self):
        d = Documento("x", [Bloco("titulo", f"T{i}") for i in range(7)])
        r = t.quadro_hoje_vamos(d, regras.maximo_etapas_hoje_vamos(regras.carregar_manual()))
        self.assertEqual(len(r.blocos[0].itens), 5)
        self.assertTrue(any("P6.1" in p for p in r.pendencias))

    def test_hoje_vamos(self):
        d = Documento("x", [Bloco("titulo", "A"), Bloco("paragrafo", texto="..."), Bloco("titulo", "B")])
        r = t.quadro_hoje_vamos(d)
        self.assertEqual(r.blocos[0].itens, ["A", "B"])


class TestFigurado(unittest.TestCase):
    def test_expressao_dentro_de_passos_e_sinalizada(self):
        d = Documento("x", [Bloco("etapas", itens=["Leia o texto", "Não vale chover no molhado"])])
        self.assertTrue(any(p.startswith("P6.3") for p in t.sinalizar_linguagem_figurada(d).pendencias))


class TestImagem(unittest.TestCase):
    def test_imagem_sem_descricao_vira_pendencia(self):
        d = Documento("x", [Bloco("imagem", arquivo="imagens/a.png")])
        r = t.imagens_com_descricao(d)
        self.assertTrue(r.pendencias)
        self.assertFalse(r.blocos[0].alt)

    def test_ia_preenche_descricao(self):
        d = Documento("x", [Bloco("imagem", arquivo="imagens/a.png")])
        r = t.imagens_com_descricao(d, lambda caminho: "Um gato")
        self.assertEqual(r.blocos[0].alt, "Um gato")


class TestManual(unittest.TestCase):
    def test_parametros_vem_do_manual(self):
        p = regras.parametros_p2(regras.carregar_manual())
        self.assertEqual(p["caracteres_por_linha"], 60)
        self.assertEqual((p["pt_padrao"], p["pt_ampliada"]), (14, 18))
        self.assertEqual((p["contraste_padrao"], p["contraste_ampliada"]), (4.5, 7))
        self.assertEqual(p["espacamento_minimo"], 1.5)

    def test_contraste_das_cores_cumpre_o_manual(self):
        p = regras.parametros_p2(regras.carregar_manual())
        for estilo, minimo in (("padrao", p["contraste_padrao"]), ("ampliada", p["contraste_ampliada"])):
            c = renderizador.ESTILOS[estilo]
            self.assertGreaterEqual(renderizador.contraste(c["texto"], c["fundo"]), minimo, estilo)
            self.assertGreaterEqual(renderizador.contraste(c["destaque"], c["fundo"]), minimo, estilo)


class TestPipeline(unittest.TestCase):
    def setUp(self):  # o teste não deve sujar o cache de verdade
        self._tmp_cache = tempfile.TemporaryDirectory()
        self._antigo = cache.PASTA
        cache.PASTA = Path(self._tmp_cache.name)

    def tearDown(self):
        cache.PASTA = self._antigo
        self._tmp_cache.cleanup()

    def test_de_ponta_a_ponta_com_texto(self):
        perfil = json.loads((EXEMPLOS / "perfil-exemplo.json").read_text(encoding="utf-8"))
        with tempfile.TemporaryDirectory() as tmp:
            r = pipeline.adaptar(EXEMPLOS / "aula-ciclo-da-agua.txt", perfil, Path(tmp))
            pasta = Path(r["pasta"])
            self.assertEqual(r["versoes"]["universal"]["status"], "gerada")
            self.assertEqual(r["versoes"]["ampliada"]["status"], "gerada")
            self.assertEqual(r["versoes"]["audio"]["status"], "gerada")   # áudio não precisa de IA
            self.assertEqual(r["status"], "aguardando_aprovacao_do_professor")
            self.assertTrue(r["pode_publicar"])
            pagina = (pasta / "ampliada.html").read_text(encoding="utf-8")
            self.assertIn('lang="pt-BR"', pagina)
            self.assertIn("18.0pt", pagina)
            self.assertIn('data-tema="amarelo"', pagina)       # Ampliada abre em amarelo no preto
            self.assertNotIn("(■)", pagina)        # a palavra "azul" no texto não é cor de verdade
            self.assertIn('<ol class="etapas">', pagina)
            self.assertTrue((pasta / "revisao.json").exists())

    def test_imagem_sem_descricao_bloqueia_publicacao(self):
        d = Documento("x", [Bloco("imagem", arquivo="imagens/a.png")])
        d = t.imagens_com_descricao(d)
        self.assertTrue(any(p.startswith("P4.1") for p in d.pendencias))

    def test_formato_nao_suportado(self):
        with tempfile.TemporaryDirectory() as tmp:
            f = Path(tmp) / "a.xyz"
            f.write_text("x")
            with self.assertRaises(ValueError):
                pipeline.adaptar(f, None, Path(tmp) / "s")


if __name__ == "__main__":
    unittest.main()


class TestMatematica(unittest.TestCase):
    """Marcação de fórmulas (⟦…⟧) do leitor de PDF para HTML, MathML e fala."""

    def test_expoente_e_indice_viram_sup_e_sub(self):
        from adaptador import leitor_pdf as lp
        self.assertEqual(lp.para_html("x⟦^{2}⟧ + a⟦_{1}⟧"), "x<sup>2</sup> + a<sub>1</sub>")

    def test_fracao_raiz_e_vetor_viram_mathml(self):
        from adaptador import leitor_pdf as lp
        h = lp.para_html("z = ⟦\\sqrt{x⟦^{2}⟧+ y⟦^{2}⟧}⟧ e ⟦\\frac{3}{2}⟧ e ⟦\\vec{F}⟧")
        self.assertIn("<msqrt>", h)
        self.assertIn("<msup><mi>x</mi><mrow><mn>2</mn></mrow></msup>", h)
        self.assertIn("<mfrac><mrow><mn>3</mn></mrow><mrow><mn>2</mn></mrow></mfrac>", h)
        self.assertIn('<mover accent="true">', h)
        self.assertIn('aria-label="', h)                      # leitor de tela lê a fórmula por extenso

    def test_fala_por_extenso(self):
        from adaptador import leitor_pdf as lp
        self.assertEqual(lp.para_fala("x⟦^{2}⟧ + ⟦\\frac{3}{2}⟧"), "x ao quadrado mais 3 sobre 2")

    def test_texto_comum_e_escapado(self):
        from adaptador import leitor_pdf as lp
        self.assertEqual(lp.para_html("<b>oi</b> & ⟦^{2}⟧"), "&lt;b&gt;oi&lt;/b&gt; &amp; <sup>2</sup>")

    def test_questoes_e_itens_na_mesma_linha_viram_lista(self):
        from adaptador import leitores
        blocos = leitores.dividir_questoes_e_itens(
            "1-) Calcule: a) mmc (20 ;30) = b) mmc (15 ; 20) = c) mmc (14 ; 5 ) = 2-) Calcule as frações:")
        self.assertEqual([b.tipo for b in blocos], ["paragrafo", "lista", "paragrafo"])
        self.assertEqual(blocos[1].itens, ["a) mmc (20 ;30) =", "b) mmc (15 ; 20) =", "c) mmc (14 ; 5 ) ="])
        self.assertEqual(blocos[2].texto, "2-) Calcule as frações:")


@unittest.skipUnless(shutil.which("pdflatex"), "pdflatex não instalado")
class TestPdfComMatematica(unittest.TestCase):
    """PDF de verdade (LaTeX) com frações empilhadas, expoentes, raiz, integral com limite e vetores."""

    def _pdf(self, corpo: str) -> Path:
        tmp = Path(tempfile.mkdtemp())
        (tmp / "a.tex").write_text("\\documentclass{article}\\usepackage{amsmath}\\pagestyle{empty}\\begin{document}"
                                   + corpo + "\\end{document}", encoding="utf-8")
        subprocess.run(["pdflatex", "-interaction=nonstopmode", "a.tex"], cwd=tmp, capture_output=True, timeout=120)
        return tmp / "a.pdf"

    def test_lista_de_fracoes(self):
        from adaptador import leitores
        pdf = self._pdf("a) $\\dfrac{3}{2} + \\dfrac{3}{1} =$\n\nb) $\\dfrac{7}{5} - \\dfrac{7}{2} =$")
        doc = leitores.ler(pdf, pdf.parent)
        itens = [i for b in doc.blocos for i in (b.itens or [b.texto])]
        self.assertIn("a) ⟦\\frac{3}{2}⟧ + ⟦\\frac{3}{1}⟧ =", itens)
        self.assertIn("b) ⟦\\frac{7}{5}⟧ − ⟦\\frac{7}{2}⟧ =", itens)

    def test_expoente_raiz_integral_e_vetor(self):
        from adaptador import leitores
        pdf = self._pdf("Seja $z = \\sqrt{x^2 + y^2}$ e $\\vec{F} = (y^2, x)$. Calcule $\\int_C \\vec{F} \\cdot d\\vec{r}$.")
        texto = " ".join(b.texto for b in leitores.ler(pdf, pdf.parent).blocos)
        self.assertIn("⟦\\sqrt{x⟦^{2}⟧", texto)
        self.assertIn("⟦\\vec{F}⟧", texto)
        self.assertIn("∫⟦_{C}⟧", texto)
        self.assertIn("d⟦\\vec{r}⟧", texto)
