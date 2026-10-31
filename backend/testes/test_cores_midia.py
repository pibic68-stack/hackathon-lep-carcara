"""Símbolos nas imagens coloridas (P1.1), transcrição pela IA e o botão "Gerar as versões de novo"."""
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from adaptador import cache, leitores, renderizador
from adaptador.modelo import Bloco, Documento
from adaptador.simbolos_imagem import marcar_cores

try:
    from PIL import Image, ImageDraw
except ImportError:  # pragma: no cover
    Image = None

try:
    from test_api import Base
except Exception:  # pragma: no cover
    Base = None


def figura(caminho: Path) -> None:
    """Fundo cinza claro, um retângulo verde grande, um sol amarelo pequeno e uma faixa vermelha fina na borda."""
    im = Image.new("RGB", (600, 400), (235, 235, 240))
    d = ImageDraw.Draw(im)
    d.rectangle([60, 150, 400, 360], fill=(40, 170, 50))
    d.ellipse([470, 40, 540, 110], fill=(250, 220, 20))
    d.rectangle([0, 0, 600, 3], fill=(220, 30, 30))             # enfeite de borda
    d.rectangle([420, 250, 560, 300], fill=(255, 255, 255))     # caixa de texto branca
    im.save(caminho)


@unittest.skipIf(Image is None, "Pillow não instalado")
class TestSimbolosNaImagem(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_marca_regioes_grandes_e_pequenas_e_ignora_borda(self):
        figura(self.dir / "f.png")
        cores = marcar_cores(self.dir / "f.png", self.dir / "f-cores.png")
        self.assertEqual(cores, ["verde", "amarelo"])           # maior área primeiro; a faixa vermelha fica de fora
        self.assertTrue((self.dir / "f-cores.png").exists())
        im = Image.open(self.dir / "f-cores.png").convert("RGB")
        b = im.tobytes()
        pretos = sum(1 for i in range(0, len(b), 3) if b[i:i + 3] == b"\x00\x00\x00")
        self.assertGreater(pretos, 300)                          # os símbolos foram desenhados

    def test_imagem_sem_cor_nao_gera_copia(self):
        Image.new("RGB", (300, 200), (200, 200, 200)).save(self.dir / "cinza.png")
        self.assertEqual(marcar_cores(self.dir / "cinza.png", self.dir / "x.png"), [])
        self.assertFalse((self.dir / "x.png").exists())

    def test_versao_mostra_imagem_com_simbolos_legenda_e_original(self):
        figura(self.dir / "f.png")
        marcar_cores(self.dir / "f.png", self.dir / "f-cores.png")
        doc = Documento("Teste", [Bloco("imagem", arquivo="f.png", alt="Árvore e sol.", colorida=True,
                                        arquivo_cores="f-cores.png", cores_imagem=["verde", "amarelo"])])
        partes = self._render(doc)
        self.assertIn('src="f-cores.png"', partes)
        self.assertIn("● verde", partes.replace('<span class="simbolo" aria-hidden="true">', "").replace("</span>", ""))
        self.assertIn("Ver a imagem sem os símbolos", partes)
        self.assertIn("círculo sobre o verde", partes)          # a versão Ouvir explica os símbolos

    def _render(self, doc):
        return renderizador.para_html(doc, "padrao", pasta_imagens=self.dir, pasta_saida=self.dir / "out", audio=True)


class Falso:
    nome = "falso"

    def __init__(self, resposta):
        self.resposta, self.chamadas = resposta, []

    def gerar(self, sistema, usuario, imagem=None):
        self.chamadas.append(imagem)
        return self.resposta


class TestTranscricaoPelaIA(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)
        self._antigo = cache.PASTA
        cache.PASTA = self.dir / "cache"
        (self.dir / "aula.mp3").write_bytes(b"ID3 audio de mentira")
        # finge que o faster-whisper não está instalado
        self._sem_whisper = mock.patch.dict(sys.modules, {"faster_whisper": None})
        self._sem_whisper.start()

    def tearDown(self):
        self._sem_whisper.stop()
        cache.PASTA = self._antigo
        self.tmp.cleanup()

    def test_sem_whisper_a_ia_transcreve(self):
        ia = Falso(json.dumps({"paragrafos": ["A água evapora.", "Depois vira chuva."], "na_tela": []}))
        doc = leitores.ler(self.dir / "aula.mp3", self.dir, ia=ia)
        self.assertEqual([b.texto for b in doc.blocos], ["A água evapora.", "Depois vira chuva."])
        dados, mime = ia.chamadas[0]
        self.assertEqual(mime, "audio/mp3")
        self.assertIn("transcrição feita pela IA", doc.pendencias[0])

    def test_video_traz_o_que_aparece_na_tela(self):
        (self.dir / "aula.mp4").write_bytes(b"video de mentira")
        ia = Falso(json.dumps({"paragrafos": ["Olá, turma."], "na_tela": ["Slide: Ciclo da água"]}))
        doc = leitores.ler(self.dir / "aula.mp4", self.dir, ia=ia)
        self.assertEqual(doc.blocos[1].texto, "O que aparece na tela")
        self.assertEqual(doc.blocos[2].itens, ["Slide: Ciclo da água"])

    def test_sem_whisper_e_sem_ia_explica_o_que_fazer(self):
        with self.assertRaises(RuntimeError) as erro:
            leitores.ler(self.dir / "aula.mp3", self.dir)
        self.assertIn("chave do Gemini", str(erro.exception))

    def test_sem_fala(self):
        with self.assertRaises(RuntimeError):
            leitores.ler(self.dir / "aula.mp3", self.dir, ia=Falso('{"paragrafos": [], "na_tela": []}'))


@unittest.skipIf(Base is None, "fastapi/httpx não instalados")
class TestRefazer(Base if Base else unittest.TestCase):
    def test_refazer_gera_de_novo_quando_a_ia_liga(self):
        c = self.professor()
        t, _ = self.turma_com_aluno(c, necessidades=("leitura_facil",))
        m = self.enviar_aula(c, t["id"]).json()
        pendentes = [k for k, v in m["versoes"].items() if v["status"] == "pendente_ia"]
        self.assertTrue(pendentes)
        r = c.post(f"/api/materiais/{m['id']}/refazer")
        self.assertEqual(r.status_code, 200, r.text)
        self.assertEqual(r.json()["id"], m["id"])

    def test_refazer_nao_mexe_em_publicado(self):
        c = self.professor()
        t, _ = self.turma_com_aluno(c)
        m = self.enviar_aula(c, t["id"]).json()
        c.post(f"/api/materiais/{m['id']}/aprovar")
        self.assertEqual(c.post(f"/api/materiais/{m['id']}/refazer").status_code, 409)


if __name__ == "__main__":
    unittest.main()


class TestLinhasDeResposta(unittest.TestCase):
    def test_pontilhado_vira_espaco_de_resposta_e_nao_vai_para_a_ia(self):
        from adaptador import transformacoes as t
        doc = Documento("Lista", [
            Bloco("titulo", texto="3.1 Análise Qualitativa: Ação do Sabão .", nivel=2),
            Bloco("paragrafo", texto="Explique por que o sabão tira a gordura."),
            Bloco("paragrafo", texto="." * 400),
            Bloco("lista", itens=["." * 60, "_" * 40]),
            Bloco("paragrafo", texto="Nome: ______________ Turma: ________"),
        ])
        novo = t.linhas_de_resposta(doc)
        self.assertEqual(novo.blocos[0].texto, "3.1 Análise Qualitativa: Ação do Sabão")
        self.assertEqual([b.tipo for b in novo.blocos], ["titulo", "paragrafo", "resposta", "paragrafo"])
        self.assertEqual(novo.blocos[2].nivel, 5 + 2)                     # 400 pontos ≈ 5 linhas + 2 itens
        self.assertEqual(novo.blocos[3].texto, "Nome: ______ Turma: ______")
        enviados = []

        def ia(textos, refazer=False):
            enviados.extend(textos)
            return (["."] + textos[1:], [])                               # a IA devolve só um ponto no 1º
        lf = t.leitura_facil(novo, "lf2", ia, 15)
        self.assertNotIn("." * 400, enviados)
        self.assertTrue(all(any(c.isalnum() for c in x) for x in enviados))
        textos = [b.texto for b in lf.blocos if b.tipo == "paragrafo"]
        self.assertIn("Explique por que o sabão tira a gordura.", textos)   # voltou o original, não "."
        self.assertFalse([x for x in textos if not any(c.isalnum() for c in x)])

    def test_pagina_mostra_pauta(self):
        doc = Documento("Lista", [Bloco("resposta", nivel=3)])
        html = renderizador.para_html(doc, "padrao", audio=True)
        self.assertIn('class="resposta"', html)
        self.assertIn("--linhas:3", html)
        self.assertIn("Espaço para escrever a resposta", html)


class TestSimbolosSoComDaltonismo(unittest.TestCase):
    def test_so_quando_a_turma_pede(self):
        from adaptador import pipeline
        self.assertFalse(pipeline.pede_simbolos(None))
        self.assertFalse(pipeline.pede_simbolos({"necessidades": ["baixa_visao"], "preferencias": ["audio"]}))
        self.assertTrue(pipeline.pede_simbolos({"necessidades": ["daltonismo"], "preferencias": []}))


class TestEstrutura(unittest.TestCase):
    def test_sumario_sai_subtitulos_e_marcadores(self):
        from adaptador import transformacoes as t
        doc = Documento("Relatório", [
            Bloco("titulo", texto="Sumário", nivel=2),
            Bloco("titulo", texto="1 Introdução 3", nivel=3),
            Bloco("paragrafo", texto="2.1 Materiais, reagentes e equipamentos ______ 4"),
            Bloco("titulo", texto="Referências Bibliográficas 9", nivel=3),
            Bloco("titulo", texto="1 Introdução", nivel=2),
            Bloco("paragrafo", texto="2.1 Materiais, reagentes e equipamentos"),
            Bloco("paragrafo", texto="• Vidrarias: tubos de ensaio."),
            Bloco("paragrafo", texto="• Indicador: Preto de Eriocromo T."),
            Bloco("paragrafo", texto="Cerca de 40 mL de água foram titulados até a viragem da água"),
            Bloco("paragrafo", texto="dura. Depois, lavamos tudo."),
            Bloco("paragrafo", texto="CaCO3(s) + CO2(g) −↽−−⇀− Ca2+(aq) (1)"),
        ])
        novo = t.arrumar_estrutura(doc)
        tipos = [(b.tipo, b.texto or b.itens) for b in novo.blocos]
        self.assertEqual(tipos[0], ("titulo", "1 Introdução"))
        self.assertEqual(tipos[1], ("titulo", "2.1 Materiais, reagentes e equipamentos"))
        self.assertEqual(tipos[2], ("lista", ["Vidrarias: tubos de ensaio.", "Indicador: Preto de Eriocromo T."]))
        self.assertEqual(tipos[3][1], "Cerca de 40 mL de água foram titulados até a viragem da água dura. Depois, lavamos tudo.")
        self.assertIn("⇌", tipos[4][1])
        self.assertTrue(any("sumário" in a for a in novo.aplicados))


@unittest.skipIf(Base is None, "fastapi/httpx não instalados")
class TestAcompanhar(Base if Base else unittest.TestCase):
    def test_progresso_do_envio_e_teste_da_ia(self):
        c = self.professor()
        t, _ = self.turma_com_aluno(c)
        with open(Path(__file__).resolve().parents[1] / "exemplos" / "aula-ciclo-da-agua.txt", "rb") as f:
            r = c.post("/api/adaptar", files={"arquivo": ("aula.txt", f, "text/plain")},
                       data={"turma_id": str(t["id"])}, headers={"X-Prisma-Acompanhar": "abc123"})
        self.assertEqual(r.status_code, 201, r.text)
        p = c.get("/api/progresso/abc123").json()
        self.assertTrue(p["terminou"])
        self.assertIsNone(p["erro"])
        self.assertTrue(any("Gerando a versão Padrão" in d["texto"] for d in p["diario"]))
        self.assertEqual(c.get("/api/progresso/nao-existe").json()["terminou"], False)
        teste = c.get("/api/ia/teste").json()        # nos testes a IA está desligada
        self.assertFalse(teste["ok"])
        self.assertIn("chave", teste["erro"])


@unittest.skipIf(Base is None, "fastapi/httpx não instalados")
class TestCompartilhar(Base if Base else unittest.TestCase):
    def test_contas_de_demo_so_no_proprio_computador(self):
        from adaptador import api, demo
        with mock.patch.object(demo, "ARQUIVO", Path(self.tmp.name) / "demo.json"), \
                mock.patch.object(api, "_do_proprio_computador", return_value=True):
            d = self.cliente().get("/api/compartilhar").json()
        self.assertTrue(d["local"])
        self.assertEqual(d["demo"]["professora"]["email"], demo.EMAIL_PROF)
        self.assertEqual(len(d["demo"]["turmas"][0]["alunos"]), 3)
        de_fora = self.cliente().get("/api/compartilhar", headers={"X-Forwarded-For": "1.2.3.4"}).json()
        self.assertFalse(de_fora["local"])
        self.assertIsNone(de_fora["demo"])


@unittest.skipIf(Base is None, "fastapi/httpx não instalados")
class TestDemoPublica(Base if Base else unittest.TestCase):
    def test_entrar_sem_senha_so_no_modo_publico(self):
        from adaptador import api, demo
        with mock.patch.object(demo, "ARQUIVO", Path(self.tmp.name) / "demo.json"):
            self.assertEqual(self.cliente().post("/api/demo/entrar", json={"perfil": "professor"}).status_code, 404)
            with mock.patch.object(api, "DEMO_PUBLICA", True):
                for perfil, destino in (("professor", "painel/professor.html"), ("aluno", "painel/aluno.html"),
                                        ("familia", "painel/familia.html"), ("escola", "painel/escola.html")):
                    c = self.cliente()
                    r = c.post("/api/demo/entrar", json={"perfil": perfil, "aluno": 1})
                    self.assertEqual(r.status_code, 200, r.text)
                    self.assertEqual(r.json()["destino"], destino)
                    self.assertEqual(c.get("/api/eu").json()["perfil"], perfil)
                self.assertTrue(self.cliente().get("/api/saude").json()["demo_publica"])


class TestEstadoNuvem(unittest.TestCase):
    def test_duas_copias_enxergam_a_mesma_pasta(self):
        from adaptador import estado_nuvem as e
        with tempfile.TemporaryDirectory() as d:
            d = Path(d)
            a, b = d / "a", d / "b"
            a.mkdir(); b.mkdir()
            with mock.patch.dict("os.environ", {"PRISMA_ESTADO_ARQUIVO": str(d / "estado.bin")}), \
                    mock.patch.object(e, "_armazem", None), mock.patch.object(e, "_versao_local", -1):
                (a / "prisma.db").write_text("contas da cópia A")
                e.subir(a)
                e._versao_local = -1            # outra cópia do servidor, que ainda não viu nada
                e.baixar(b)
                self.assertEqual((b / "prisma.db").read_text(), "contas da cópia A")
