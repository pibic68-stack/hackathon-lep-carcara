"""Rodar (de dentro de backend/):  python -m unittest discover -s testes -v"""
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from adaptador import cache, pipeline, regras, renderizador, transformacoes as t
from adaptador.modelo import Bloco, Documento

EXEMPLOS = Path(__file__).resolve().parents[1] / "exemplos"


class TestCorComSimbolo(unittest.TestCase):
    def test_cor_ganha_simbolo_e_legenda(self):
        d = Documento("x", [Bloco("paragrafo", texto="Pinte de azul e circule em vermelho.")])
        r = t.cor_com_simbolo(d)
        self.assertIn("azul (■)", r.blocos[1].texto)
        self.assertIn("vermelho (▲)", r.blocos[1].texto)
        self.assertEqual(r.blocos[0].tipo, "quadro")  # legenda no topo

    def test_nao_duplica_e_respeita_plural(self):
        d = Documento("x", [Bloco("paragrafo", texto="As nuvens azuis e a cor azul (■).")])
        txt = t.cor_com_simbolo(d).blocos[1].texto
        self.assertIn("azuis (■)", txt)
        self.assertEqual(txt.count("(■)"), 2)  # a segunda já tinha símbolo

    def test_sem_cor_nao_muda_nada(self):
        d = Documento("x", [Bloco("paragrafo", texto="A água evapora.")])
        self.assertEqual(t.cor_com_simbolo(d).blocos, d.blocos)

    def test_nao_altera_o_original(self):
        d = Documento("x", [Bloco("paragrafo", texto="Use o verde.")])
        t.cor_com_simbolo(d)
        self.assertEqual(d.blocos[0].texto, "Use o verde.")


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

    def test_hoje_vamos(self):
        d = Documento("x", [Bloco("titulo", "A"), Bloco("paragrafo", texto="..."), Bloco("titulo", "B")])
        r = t.quadro_hoje_vamos(d)
        self.assertEqual(r.blocos[0].itens, ["A", "B"])


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
            self.assertEqual(r["versoes"]["audio"]["status"], "pendente_ia")
            self.assertEqual(r["status"], "aguardando_aprovacao_do_professor")
            pagina = (pasta / "ampliada.html").read_text(encoding="utf-8")
            self.assertIn('lang="pt-BR"', pagina)
            self.assertIn("font-size:18.0pt", pagina)
            self.assertIn("azul (■)", pagina)
            self.assertIn('<ol class="etapas">', pagina)
            self.assertTrue((pasta / "revisao.json").exists())

    def test_formato_nao_suportado(self):
        with tempfile.TemporaryDirectory() as tmp:
            f = Path(tmp) / "a.xyz"
            f.write_text("x")
            with self.assertRaises(ValueError):
                pipeline.adaptar(f, None, Path(tmp) / "s")


if __name__ == "__main__":
    unittest.main()
