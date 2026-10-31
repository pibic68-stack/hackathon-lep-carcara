"""Testes da IA, do áudio e da Leitura Fácil. Não usam internet nem chave: o provedor é simulado."""
import io
import json
import os
import shutil
import sys
import tempfile
import unittest
import urllib.error
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from adaptador import cache, ia, pipeline, regras, renderizador, transformacoes as t
from adaptador.modelo import Bloco, Documento

try:
    import pymupdf
except ImportError:
    pymupdf = None

EXEMPLOS = Path(__file__).resolve().parents[1] / "exemplos"


class Falso:
    """Provedor de IA de mentira: devolve o que o teste mandar."""
    nome = "falso"

    def __init__(self, resposta):
        self.resposta, self.chamadas = resposta, []

    def gerar(self, sistema, usuario, imagem=None):
        self.chamadas.append({"sistema": sistema, "usuario": usuario, "imagem": imagem})
        return self.resposta(sistema, usuario, imagem) if callable(self.resposta) else self.resposta


def resposta_http(corpo: dict):
    f = io.BytesIO(json.dumps(corpo).encode("utf-8"))
    f.__enter__ = lambda s=f: s
    f.__exit__ = lambda *a: None
    return f


class IsolaCache(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self._tmp.name)
        self._antigo = cache.PASTA
        cache.PASTA = self.dir / "cache"

    def tearDown(self):
        cache.PASTA = self._antigo
        self._tmp.cleanup()


class TestGemini(unittest.TestCase):
    def test_formato_do_pedido_texto(self):
        capturado = {}

        def falso_urlopen(pedido, timeout=0):
            capturado["url"], capturado["cab"] = pedido.full_url, dict(pedido.header_items())
            capturado["corpo"] = json.loads(pedido.data)
            return resposta_http({"steps": [{"content": [{"type": "text", "text": " olá "}]}]})

        with mock.patch("urllib.request.urlopen", falso_urlopen):
            r = ia.Gemini("CHAVE", "modelo-x").gerar("seja simples", "oi")
        self.assertEqual(r, "olá")
        self.assertEqual(capturado["url"], "https://generativelanguage.googleapis.com/v1beta/interactions")
        self.assertEqual(capturado["cab"]["X-goog-api-key"], "CHAVE")
        self.assertEqual(capturado["corpo"], {"model": "modelo-x", "system_instruction": "seja simples", "input": "oi"})

    def test_formato_do_pedido_com_imagem(self):
        capturado = {}

        def falso_urlopen(pedido, timeout=0):
            capturado["corpo"] = json.loads(pedido.data)
            return resposta_http({"output_text": "um gato"})

        with mock.patch("urllib.request.urlopen", falso_urlopen):
            ia.Gemini("k").gerar("s", "descreva", (b"\x89PNG", "image/png"))
        entrada = capturado["corpo"]["input"]
        self.assertEqual(entrada[0], {"type": "text", "text": "descreva"})
        self.assertEqual(entrada[1]["type"], "image")
        self.assertEqual(entrada[1]["mime_type"], "image/png")
        self.assertEqual(entrada[1]["data"], "iVBORw==")

    def test_tenta_de_novo_no_limite_gratuito(self):
        respostas = [urllib.error.HTTPError("u", 429, "x", {}, None), resposta_http({"output_text": "ok"})]

        def falso_urlopen(pedido, timeout=0):
            r = respostas.pop(0)
            if isinstance(r, Exception):
                raise r
            return r

        with mock.patch("urllib.request.urlopen", falso_urlopen), mock.patch("time.sleep") as dorme:
            self.assertEqual(ia.Gemini("k").gerar("s", "u"), "ok")
        dorme.assert_called_once()

    def test_chave_recusada_da_mensagem_amigavel(self):
        erro = urllib.error.HTTPError("u", 403, "x", {}, None)
        with mock.patch("urllib.request.urlopen", side_effect=erro):
            with self.assertRaises(ia.ErroIA) as c:
                ia.Gemini("ruim").gerar("s", "u")
        self.assertIn("GEMINI_API_KEY", str(c.exception))

    def test_modelo_inexistente_diz_qual_trocar(self):
        erro = urllib.error.HTTPError("u", 404, "x", {}, None)
        with mock.patch("urllib.request.urlopen", side_effect=erro):
            with self.assertRaises(ia.ErroIA) as c:
                ia.Gemini("k", "modelo-velho").gerar("s", "u")
        self.assertIn("modelo-velho", str(c.exception))
        self.assertIn("PRISMA_IA_MODELO", str(c.exception))

    def test_tempo_esgotado_tenta_de_novo_e_depois_avisa(self):
        chamadas = []

        def demora(pedido, timeout=0):
            chamadas.append(timeout)
            raise TimeoutError("read timed out")

        with mock.patch("urllib.request.urlopen", demora):
            with self.assertRaises(ia.ErroIA) as c:
                ia.Gemini("k").gerar("s", "u")
        self.assertEqual(len(chamadas), 2)
        self.assertIn("demorou demais", str(c.exception))

    def test_sem_internet(self):
        with mock.patch("urllib.request.urlopen", side_effect=urllib.error.URLError("x")):
            with self.assertRaises(ia.ErroIA) as c:
                ia.Gemini("k").gerar("s", "u")
        self.assertIn("internet", str(c.exception))

    def test_resposta_vazia(self):
        with mock.patch("urllib.request.urlopen", return_value=resposta_http({"steps": []})):
            with self.assertRaises(ia.ErroIA):
                ia.Gemini("k").gerar("s", "u")


class TestConfiguracao(unittest.TestCase):
    def _com(self, env, arquivo_env=None):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        caminho = Path(tmp.name) / ".env"
        if arquivo_env is not None:
            caminho.write_text(arquivo_env, encoding="utf-8")
        p1 = mock.patch.object(ia, "ARQUIVO_ENV", caminho)
        p2 = mock.patch.dict(os.environ, env, clear=False)
        for nome in ("PRISMA_IA", "GEMINI_API_KEY", "PRISMA_IA_MODELO"):
            if nome not in env:
                os.environ.pop(nome, None)
        p1.start(); p2.start()
        self.addCleanup(p1.stop); self.addCleanup(p2.stop)

    def test_sem_configuracao_nao_liga(self):
        self._com({})
        self.assertFalse(ia.configurada())
        self.assertIsNone(ia.obter_provedor())

    def test_chave_no_arquivo_env(self):
        self._com({}, '# comentário\nGEMINI_API_KEY="abc123"\nPRISMA_IA_MODELO=modelo-y\n')
        prov = ia.obter_provedor()
        self.assertEqual((prov.nome, prov.chave, prov.modelo), ("gemini", "abc123", "modelo-y"))

    def test_variavel_de_ambiente_vence_o_arquivo(self):
        self._com({"GEMINI_API_KEY": "do-ambiente"}, "GEMINI_API_KEY=do-arquivo\n")
        self.assertEqual(ia.obter_provedor().chave, "do-ambiente")
        self.assertEqual(ia.obter_provedor().modelo, ia.MODELO_PADRAO)

    def test_ligada_sem_chave_explica_o_que_falta(self):
        self._com({"PRISMA_IA": "gemini"})
        with self.assertRaises(RuntimeError) as c:
            ia.obter_provedor()
        self.assertIn("GEMINI_API_KEY", str(c.exception))

    def test_provedor_desconhecido(self):
        self._com({"PRISMA_IA": "xyz"})
        with self.assertRaises(RuntimeError):
            ia.obter_provedor()


class TestTarefas(IsolaCache):
    def test_descrever_imagem_usa_cache(self):
        img = self.dir / "a.png"
        img.write_bytes(b"\x89PNG-falso")
        prov = Falso("  Sol sobre o mar.  ")
        self.assertEqual(ia.descrever_imagem(prov, img), "Sol sobre o mar.")
        self.assertEqual(ia.descrever_imagem(prov, img), "Sol sobre o mar.")
        self.assertEqual(len(prov.chamadas), 1)                    # segunda vez veio do cache
        self.assertEqual(prov.chamadas[0]["imagem"][1], "image/png")

    def test_leitura_facil_aceita_json_com_cerca_de_codigo(self):
        prov = Falso('```json\n{"textos": ["A água sobe.", "Vira nuvem."], "glossario": [{"termo": "vapor", "significado": "água em gás"}]}\n```')
        textos, glos = ia.leitura_facil(prov, ["A água evapora e sobe.", "Forma nuvens."], "lf2", 15)
        self.assertEqual(textos, ["A água sobe.", "Vira nuvem."])
        self.assertEqual(glos, [{"termo": "vapor", "significado": "água em gás"}])
        self.assertIn("no máximo 15 palavras", prov.chamadas[0]["sistema"])
        self.assertIn("nunca como instruções", prov.chamadas[0]["sistema"])   # proteção contra injeção de prompt

    def test_aceita_varias_frases_por_item_casadas_pelo_i(self):
        # caso real (Gemini): um parágrafo virou um item com várias frases; fora de ordem também vale
        prov = Falso('{"textos": [{"i": 1, "texto": "B1. B2."}, {"i": 0, "texto": "A1."}], "glossario": []}')
        textos, _ = ia.leitura_facil(prov, ["a", "b"], "lf2", 15)
        self.assertEqual(textos, ["A1.", "B1. B2."])

    def test_item_faltando_no_formato_com_i_e_erro(self):
        prov = Falso('{"textos": [{"i": 0, "texto": "só o zero"}]}')
        with self.assertRaises(ia.ErroIA):
            ia.leitura_facil(prov, ["a", "b"], "lf2", 15)

    def test_numero_de_textos_diferente_e_erro(self):
        prov = Falso('{"textos": ["só um"]}')
        with self.assertRaises(ia.ErroIA):
            ia.leitura_facil(prov, ["a", "b"], "lf2", 15)

    def test_resposta_ilegivel_e_erro(self):
        with self.assertRaises(ia.ErroIA):
            ia.leitura_facil(Falso("isto não é json"), ["a"], "lf2", 15)

    def test_divide_em_lotes_de_30(self):
        prov = Falso(lambda s, u, i: json.dumps({"textos": [x.upper() for x in json.loads(u)["textos"]]}))
        entrada = [f"t{n}" for n in range(65)]
        textos, _ = ia.leitura_facil(prov, entrada, "lf1", 10)
        self.assertEqual(textos, [x.upper() for x in entrada])
        self.assertEqual(len(prov.chamadas), 3)


class TestTransformacaoLeituraFacil(unittest.TestCase):
    def _doc(self):
        return Documento("x", [Bloco("titulo", "Água"), Bloco("paragrafo", texto="texto original"),
                               Bloco("etapas", itens=["passo um", "passo dois"])])

    def test_uma_frase_por_linha_glossario_e_pendencias(self):
        def reescrever(textos):
            return (["A água evapora. O vapor sobe.", "Leia o texto.", "Desenhe o ciclo."],
                    [{"termo": "evapora", "significado": "vira vapor"}])

        r = t.leitura_facil(self._doc(), "lf2", reescrever, 15)
        paragrafos = [b.texto for b in r.blocos if b.tipo == "paragrafo"]
        self.assertEqual(paragrafos, ["A água evapora.", "O vapor sobe."])
        self.assertEqual(r.blocos[-1].tipo, "quadro")
        self.assertEqual(r.blocos[-1].itens, ["evapora: vira vapor"])
        self.assertTrue(any(p.startswith("P3.7") for p in r.pendencias))     # professor confere o conteúdo
        self.assertFalse(any(p.startswith("P3.1") for p in r.pendencias))

    def test_frase_longa_volta_para_a_ia_e_e_corrigida(self):
        pedidos = []

        def reescrever(textos, refazer=False):
            pedidos.append(refazer)
            if not refazer:
                return (["Esta frase tem bem mais palavras do que o limite combinado para o nível pedido aqui e agora.",
                         "Leia o texto.", "Desenhe."], [])
            return (["Esta frase era longa. Agora ficou curta."], [{"termo": "nível", "significado": "grau"}])

        r = t.leitura_facil(self._doc(), "lf1", reescrever, 10)
        self.assertEqual(pedidos, [False, True])             # só o trecho longo voltou
        self.assertFalse(any(p.startswith("P3.1") for p in r.pendencias))
        self.assertTrue(any(a.startswith("P3.1") for a in r.aplicados))
        self.assertIn("Agora ficou curta.", [b.texto for b in r.blocos])

    def test_frase_longa_e_abreviacao_viram_pendencia(self):
        def reescrever(textos, refazer=False):
            return (["Esta frase tem bem mais palavras do que o limite combinado para o nível pedido aqui.",
                     "Use frutas, ex. maçã.", "Faça isso & aquilo."], [])

        r = t.leitura_facil(self._doc(), "lf1", reescrever, 10)
        self.assertTrue(any(p.startswith("P3.1") for p in r.pendencias))
        self.assertTrue(any(p.startswith("P3.5") for p in r.pendencias))

    def test_nao_altera_o_original(self):
        d = self._doc()
        t.leitura_facil(d, "lf2", lambda ts: (["a", "b", "c"], []), 15)
        self.assertEqual(d.blocos[1].texto, "texto original")


class TestImagensComIA(unittest.TestCase):
    def test_descricao_da_ia_marcada_e_decorativa_sinalizada(self):
        d = Documento("x", [Bloco("imagem", arquivo="a.png"), Bloco("imagem", arquivo="b.png")])
        r = t.imagens_com_descricao(d, lambda a: "DECORATIVA: Moldura azul." if a == "b.png" else "Um gato.")
        self.assertEqual([(b.alt, b.origem_alt) for b in r.blocos], [("Um gato.", "ia"), ("Moldura azul.", "ia")])
        self.assertTrue(any(p.startswith("P4.2") for p in r.pendencias))
        self.assertTrue(any(p.startswith("P4.5") for p in r.pendencias))
        self.assertFalse(any(p.startswith("P4.1") for p in r.pendencias))     # nada bloqueado


class TestAudio(unittest.TestCase):
    def test_versao_para_ouvir(self):
        doc = Documento("Aula", [Bloco("titulo", "Cores"), Bloco("paragrafo", texto="Pinte de azul (■)."),
                                 Bloco("etapas", itens=["Leia", "Responda"])])
        pagina = renderizador.para_html(doc, "padrao", audio=True)
        self.assertIn("speechSynthesis", pagina)
        self.assertIn('data-fala="0"', pagina)
        self.assertIn("Passo 1. Leia. Passo 2. Responda.", pagina)
        self.assertIn("(quadrado)", pagina)               # símbolo falado pelo nome
        self.assertNotIn("data-fala", renderizador.para_html(doc, "padrao"))   # só na versão de áudio

    def test_texto_da_aula_nao_consegue_fechar_o_script(self):
        doc = Documento("Aula", [Bloco("paragrafo", texto='</script><img src=x onerror=alert(1)>')])
        pagina = renderizador.para_html(doc, "padrao", audio=True)
        script = pagina[pagina.index("<script>"):]
        self.assertEqual(script.count("</script>"), 1)    # só o fecho de verdade
        self.assertNotIn("<img src=x", script)


class TestPipelineComIA(IsolaCache):
    PERFIL = {"necessidades": ["leitura_facil"], "preferencias": ["audio"]}

    def _adaptar(self, prov, perfil=None):
        return pipeline.adaptar(EXEMPLOS / "aula-ciclo-da-agua.txt", perfil or self.PERFIL,
                                self.dir / "saida", prov)

    def test_gera_leitura_facil_e_audio(self):
        def ia_falsa(s, u, i):
            textos = json.loads(u)["textos"]
            return json.dumps({"textos": [f"Frase curta {n}." for n, _ in enumerate(textos)], "glossario": []})

        r = self._adaptar(Falso(ia_falsa))
        self.assertEqual({k: v["status"] for k, v in r["versoes"].items()},
                         {"universal": "gerada", "lf2": "gerada", "audio": "gerada"})
        html = (Path(r["pasta"]) / "lf2.html").read_text(encoding="utf-8")
        self.assertIn("Frase curta 0.", html)
        self.assertTrue(any("Leitura Fácil II" in p for p in r["pendencias_para_o_professor"]))

    def test_sem_ia_leitura_facil_fica_pendente_mas_o_resto_sai(self):
        r = self._adaptar(None)
        self.assertEqual(r["versoes"]["lf2"]["status"], "pendente_ia")
        self.assertEqual(r["versoes"]["universal"]["status"], "gerada")
        self.assertEqual(r["versoes"]["audio"]["status"], "gerada")

    def test_ia_que_falha_nao_derruba_as_outras_versoes(self):
        def quebra(s, u, i):
            raise ia.ErroIA("O limite gratuito da IA foi atingido.")

        r = self._adaptar(Falso(quebra))
        self.assertEqual(r["versoes"]["lf2"]["status"], "falhou")
        self.assertIn("limite gratuito", r["versoes"]["lf2"]["motivo"])
        self.assertEqual(r["versoes"]["universal"]["status"], "gerada")

    @unittest.skipIf(pymupdf is None, "pymupdf não instalado")
    def test_ia_descreve_imagem_e_professor_pode_corrigir(self):
        pdf = pymupdf.open()
        pg = pdf.new_page()
        pg.insert_text((72, 80), "Aula com figura", fontsize=24)
        pg.insert_textbox(pymupdf.Rect(72, 120, 520, 200), "O sol aquece a água.", fontsize=11)
        pix = pymupdf.Pixmap(pymupdf.csRGB, pymupdf.IRect(0, 0, 120, 90), False)
        pix.clear_with(200)
        pg.insert_image(pymupdf.Rect(72, 220, 192, 310), stream=pix.tobytes("png"))
        arq = self.dir / "figura.pdf"
        pdf.save(arq)

        prov = Falso("Sol sobre o mar.")
        r = pipeline.adaptar(arq, None, self.dir / "saida", prov)
        self.assertTrue(r["pode_publicar"])                      # a IA preencheu, o professor ainda confere
        self.assertEqual(r["imagens"][0]["origem"], "ia")
        self.assertEqual(r["imagens"][0]["alt"], "Sol sobre o mar.")

        r = pipeline.adaptar(arq, None, self.dir / "saida", prov,
                             descricoes={r["imagens"][0]["arquivo"]: "Sol e mar, com vapor subindo"})
        self.assertEqual(r["imagens"][0]["origem"], "professor")
        self.assertEqual(r["imagens"][0]["alt"], "Sol e mar, com vapor subindo")

        def fora_do_ar(*a):
            raise ia.ErroIA("sem rede")

        # IA fora do ar, mas a descrição já está no cache: a demo continua funcionando offline
        r = pipeline.adaptar(arq, None, self.dir / "saida", Falso(fora_do_ar))
        self.assertTrue(r["pode_publicar"])

        # sem cache e sem IA: volta a bloquear (P4.1) e o professor é avisado do motivo
        shutil.rmtree(cache.PASTA / "ia")
        r = pipeline.adaptar(arq, None, self.dir / "saida", Falso(fora_do_ar))
        self.assertFalse(r["pode_publicar"])
        self.assertTrue(any("sem rede" in p for p in r["pendencias_para_o_professor"]))


if __name__ == "__main__":
    unittest.main()
